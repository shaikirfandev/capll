# Section 05 — Databases

## 5.1 PostgreSQL — The FDE Default Database

PostgreSQL is the most common database FDEs encounter. Master it completely.

### Schema Design
```sql
-- Production schema: always use explicit types, constraints, and indexes
CREATE TABLE deployments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(63) NOT NULL CHECK (name ~ '^[a-z0-9-]+$'),
    environment_id  UUID NOT NULL REFERENCES environments(id),
    version         VARCHAR(50) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','running','completed','failed','rolled_back')),
    config          JSONB NOT NULL DEFAULT '{}',
    created_by      VARCHAR(255) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    
    CONSTRAINT valid_completion CHECK (
        (status IN ('completed','failed','rolled_back')) = (completed_at IS NOT NULL)
    )
);

-- Indexes: every query path needs an index
CREATE INDEX CONCURRENTLY idx_deployments_env_status
    ON deployments(environment_id, status) WHERE status != 'completed';

CREATE INDEX CONCURRENTLY idx_deployments_created_at
    ON deployments(created_at DESC);

-- JSONB index for querying config fields
CREATE INDEX CONCURRENTLY idx_deployments_config_gin
    ON deployments USING GIN (config);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_deployments_updated_at
    BEFORE UPDATE ON deployments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### Query Optimisation
```sql
-- EXPLAIN ANALYZE — your first tool when a query is slow
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT d.id, d.name, d.status, e.name AS environment
FROM   deployments d
JOIN   environments e ON e.id = d.environment_id
WHERE  d.status = 'running'
  AND  d.created_at > NOW() - INTERVAL '24 hours'
ORDER BY d.created_at DESC;

-- Read the output:
-- "Seq Scan" on a large table = missing index
-- "Hash Join" vs "Nested Loop" — hash better for large datasets
-- Rows with "Rows Removed by Filter" = predicate not using index

-- Common slow query patterns and fixes:
-- 1. N+1 query problem — use JOIN or WITH
-- Bad:
SELECT id FROM deployments;
-- Then for each ID: SELECT * FROM logs WHERE deployment_id = $1

-- Good: Single query with lateral join
SELECT d.id, d.name, recent_logs.data
FROM   deployments d
LEFT   JOIN LATERAL (
    SELECT json_agg(l ORDER BY l.created_at DESC) AS data
    FROM   logs l
    WHERE  l.deployment_id = d.id
    LIMIT  10
) recent_logs ON true
WHERE d.status = 'running';

-- 2. Pagination — OFFSET is O(n), use cursor-based for large datasets
-- Bad (offset gets slower as page increases):
SELECT * FROM events ORDER BY id LIMIT 20 OFFSET 100000;

-- Good (cursor-based — always O(log n) with index):
SELECT * FROM events WHERE id > :last_seen_id ORDER BY id LIMIT 20;
```

### Connection Pooling
```
Direct connections vs PgBouncer:

Without pooling:
  100 app instances × 10 connections each = 1,000 PostgreSQL connections
  PostgreSQL spawns a process per connection = memory exhausted

With PgBouncer (transaction mode):
  100 app instances × 10 "connections" → PgBouncer pool of 20 real connections
  
PgBouncer config:
  pool_mode = transaction
  max_client_conn = 1000
  default_pool_size = 20
  server_idle_timeout = 600

Rule: Always deploy PgBouncer in front of PostgreSQL in production.
Never let applications connect directly at scale.
```

---

## 5.2 MySQL

MySQL differences you must know when a customer runs it instead of Postgres:

| Feature | PostgreSQL | MySQL |
|---------|-----------|-------|
| JSONB support | Native, indexed | JSON (slower) |
| Window functions | Full support | MySQL 8+ only |
| Upsert | `INSERT ... ON CONFLICT DO UPDATE` | `INSERT ... ON DUPLICATE KEY UPDATE` |
| Sequences | `SEQUENCE` objects | `AUTO_INCREMENT` |
| Partial indexes | Yes | No (workaround: generated columns) |
| Concurrent index build | `CREATE INDEX CONCURRENTLY` | Online DDL (row lock risk) |

---

## 5.3 MongoDB

FDEs encounter MongoDB at startups and in document-heavy use cases (logs, events, config stores).

```javascript
// Aggregation pipeline — MongoDB's power feature
const deploymentSummary = await db.collection("deployments").aggregate([
  // Stage 1: Filter
  { $match: { status: "completed", createdAt: { $gte: new Date(Date.now() - 86400000) } } },
  
  // Stage 2: Group by environment + count
  { $group: {
    _id: "$environmentId",
    total:    { $sum: 1 },
    avgDuration: { $avg: { $subtract: ["$completedAt", "$createdAt"] } },
    failures: { $sum: { $cond: [{ $eq: ["$status", "failed"] }, 1, 0] } }
  }},
  
  // Stage 3: Lookup environment name
  { $lookup: {
    from:         "environments",
    localField:   "_id",
    foreignField: "_id",
    as:           "environment"
  }},
  
  // Stage 4: Unwind and project
  { $unwind: "$environment" },
  { $project: {
    environmentName: "$environment.name",
    total:           1,
    avgDurationMs:   { $round: ["$avgDuration", 0] },
    failureRate:     { $divide: ["$failures", "$total"] }
  }},
  
  { $sort: { total: -1 } }
]).toArray();

// Indexing strategy
await db.collection("deployments").createIndexes([
  { key: { environmentId: 1, status: 1 } },
  { key: { createdAt: -1 } },
  { key: { "metadata.tags": 1 }, sparse: true },
]);
```

**MongoDB Schema Design Rules:**
```
Embed when:
  - Data always accessed together
  - One-to-few relationship (e.g. deployment + its 5 config values)
  - Sub-document < 16MB

Reference when:
  - Data accessed independently
  - One-to-many (e.g. deployment → thousands of log lines)
  - Many-to-many
```

---

## 5.4 Redis

Redis is the most versatile tool in the FDE toolkit. Uses:

```
Caching          → Store expensive query results (TTL-based)
Session store    → JWT session data, SSO state
Rate limiting    → Token bucket / sliding window counters
Job queue        → Background task scheduling (BullMQ)
Pub/Sub          → Real-time event broadcasting
Distributed lock → Prevent duplicate deployments
Leaderboard      → ZADD/ZRANGE for sorted scoring
```

### Rate Limiting with Redis
```typescript
// Sliding window rate limiter using sorted sets
async function isRateLimited(key: string, limit: number, windowMs: number): Promise<boolean> {
    const now = Date.now();
    const windowStart = now - windowMs;
    
    const pipeline = redis.pipeline();
    pipeline.zremrangebyscore(key, 0, windowStart);      // Remove old entries
    pipeline.zadd(key, now, `${now}`);                    // Add current request
    pipeline.zcard(key);                                  // Count requests in window
    pipeline.expire(key, Math.ceil(windowMs / 1000));     // Cleanup TTL
    
    const results = await pipeline.exec();
    const count = results[2][1] as number;
    return count > limit;
}
```

### Distributed Lock (Critical for FDE deployments)
```typescript
// Prevent two concurrent deployments to same environment
async function acquireDeploymentLock(envId: string, ttlMs = 300_000): Promise<string | null> {
    const lockKey = `lock:deployment:${envId}`;
    const lockValue = crypto.randomUUID();
    
    // NX = only set if not exists, PX = expire in milliseconds
    const result = await redis.set(lockKey, lockValue, "NX", "PX", ttlMs);
    return result === "OK" ? lockValue : null;
}

async function releaseDeploymentLock(envId: string, lockValue: string): Promise<void> {
    // Lua script: only delete if we own the lock (atomic check-and-delete)
    const script = `
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
    `;
    await redis.eval(script, 1, `lock:deployment:${envId}`, lockValue);
}
```

---

## 5.5 Elasticsearch

Used for log search and full-text search in FDE monitoring platforms (ELK stack).

```json
// Create index with proper mappings
PUT /deployments-2024-11
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "5s"
  },
  "mappings": {
    "properties": {
      "timestamp":     { "type": "date" },
      "deployment_id": { "type": "keyword" },
      "environment":   { "type": "keyword" },
      "status":        { "type": "keyword" },
      "log_line":      { "type": "text", "analyzer": "standard" },
      "duration_ms":   { "type": "long" }
    }
  }
}
```

```json
// Query — find failed deployments with specific error in last 24h
GET /deployments-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "log_line": "connection refused" } },
        { "term":  { "status": "failed" } },
        { "range": { "timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "by_environment": {
      "terms": { "field": "environment", "size": 10 },
      "aggs": {
        "failure_timeline": {
          "date_histogram": { "field": "timestamp", "calendar_interval": "1h" }
        }
      }
    }
  },
  "sort": [{ "timestamp": "desc" }],
  "size": 50
}
```

---

## 5.6 Database Replication & High Availability

```
PostgreSQL Streaming Replication:

Primary  ──WAL stream──►  Standby 1 (sync replica)
                      ──WAL stream──►  Standby 2 (async replica)

Write:  Always to primary
Read:   Can route to standbys (read replicas)
Failover: Patroni + etcd handles automatic failover

Recovery Time Objective (RTO) with Patroni: ~30 seconds
Recovery Point Objective (RPO): 0 (with synchronous replica)
```

```
Multi-Region Database Setup:
                                                        
  Region: us-east-1 (Primary)     Region: eu-west-1 (DR)
  ┌─────────────────────────┐     ┌────────────────────────────┐
  │  Primary DB (R/W)        │────►│  Read Replica (R only)     │
  │  PgBouncer pool          │     │  PgBouncer pool            │
  │  Connection: 5432        │     │  Lag: ~50-100ms            │
  └─────────────────────────┘     └────────────────────────────┘
```

---

## 5.7 Backup & Recovery Strategy

```bash
#!/usr/bin/env bash
# PostgreSQL backup to S3 with encryption

set -euo pipefail

DB_HOST="${DB_HOST:?}"
DB_NAME="${DB_NAME:?}"
S3_BUCKET="${S3_BUCKET:?}"
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backup_${DB_NAME}_${BACKUP_DATE}.dump"

# Create encrypted compressed backup
pg_dump \
    --host="$DB_HOST" \
    --username="$DB_USER" \
    --format=custom \
    --compress=9 \
    --no-password \
    "$DB_NAME" | \
gpg --batch --symmetric --cipher-algo AES256 \
    --passphrase-file /run/secrets/backup_key \
    --output - | \
aws s3 cp - "s3://${S3_BUCKET}/backups/${BACKUP_FILE}.gpg" \
    --storage-class STANDARD_IA

echo "Backup complete: ${BACKUP_FILE}.gpg"

# Verify backup is restorable (test restore to temp DB)
if [[ "${VERIFY_BACKUP:-false}" == "true" ]]; then
    TEMP_DB="verify_restore_$(date +%s)"
    createdb "$TEMP_DB"
    aws s3 cp "s3://${S3_BUCKET}/backups/${BACKUP_FILE}.gpg" - | \
    gpg --batch --decrypt --passphrase-file /run/secrets/backup_key | \
    pg_restore --host="$DB_HOST" --dbname="$TEMP_DB" --no-owner
    dropdb "$TEMP_DB"
    echo "Backup verified successfully"
fi
```

**Backup Testing Rule:** A backup that has never been tested is not a backup. Schedule monthly restore drills.

---

## 5.8 Database Sharding

When a single node cannot handle load:

```
Horizontal Sharding Strategies:

Range sharding:
  Shard 1: customer_id 1–10,000
  Shard 2: customer_id 10,001–20,000
  Pro: Range queries are efficient
  Con: Hot spots if new customers come in batches

Hash sharding:
  Shard = hash(customer_id) % num_shards
  Pro: Even distribution
  Con: Range queries cross all shards

Directory sharding:
  Lookup table: customer_id → shard_id
  Pro: Flexible routing
  Con: Lookup table becomes bottleneck

FDE rule: For most enterprise customers, vertical scaling (bigger machine)
+ read replicas handles 99% of cases without sharding complexity.
Reach for sharding only after exhausting single-node options.
```
