# Section 14 — System Design

## 14.1 Monolith vs Microservices

```
MONOLITH (Start here for most products)

Advantages:
  - Simple to develop, test, and deploy (one codebase)
  - No network latency between components
  - Easier debugging (one process, one log stream)
  - Simpler transactions (ACID within one DB)

Disadvantages:
  - Scales as a unit — can't scale one component independently
  - Long CI/CD cycles as codebase grows
  - Technology lock-in
  - Blast radius of any bug = entire application

When to STAY monolith:
  - Team < 10 engineers
  - Domain model not yet well-understood
  - Less than 100k users

When to MOVE to microservices:
  - Clear bounded domains that evolve independently
  - Teams stepping on each other in one codebase
  - Scaling needs differ per service (e.g. ML inference vs CRUD API)
  - Different reliability requirements (payments vs search)
```

---

## 14.2 SaaS Architecture Patterns

### Multi-Tenant Architecture Models

```
Model 1: Silo (One stack per customer)
  Customer A → own DB + own K8s namespace + own infra
  Customer B → own DB + own K8s namespace + own infra
  
  Pro: Full isolation, easier compliance (SOC2, HIPAA, data residency)
  Con: High operational cost, complex management
  Use: Enterprise/government customers, very large deployments
  FDE workload: High — deploy and maintain independently per customer

Model 2: Pool (Shared everything, isolated by tenant_id)
  All customers → shared DB (row-level tenant isolation) + shared pods
  
  Pro: Low cost, simple operations
  Con: Noisy-neighbour risk, harder compliance, data isolation concerns
  Use: SMB SaaS, developer tools, low-compliance domains
  FDE workload: Low — deploy once, onboard customers with config

Model 3: Bridge (Shared control plane, isolated data plane)
  Control plane: shared (auth, billing, config API)
  Data plane: per-customer (DB, compute, storage)
  
  Pro: Best balance of cost and isolation
  Con: Complex architecture, harder to debug
  Use: Enterprise SaaS at scale (Snowflake, Datadog model)
  FDE workload: Medium — configure data plane, shared control plane is vendor-managed
```

### Bridge Model Implementation
```
           ┌──────────────────────────────────────────┐
           │         CONTROL PLANE (Shared)            │
           │  Auth Service │ Billing │ Config API      │
           └────────────────┬─────────────────────────┘
                            │ API calls
         ┌──────────────────┼──────────────────┐
         │                  │                  │
┌────────▼────────┐ ┌───────▼────────┐ ┌──────▼──────────┐
│  CUSTOMER A     │ │  CUSTOMER B    │ │  CUSTOMER C     │
│  DATA PLANE     │ │  DATA PLANE    │ │  DATA PLANE     │
│  ─────────────  │ │  ────────────  │ │  ────────────   │
│  App pods       │ │  App pods      │ │  App pods       │
│  PostgreSQL     │ │  PostgreSQL    │ │  PostgreSQL     │
│  Redis          │ │  Redis         │ │  Redis          │
│  us-east-1      │ │  eu-west-1     │ │  ap-south-1     │
└─────────────────┘ └────────────────┘ └─────────────────┘
```

---

## 14.3 System Design Case Study: URL Shortener

### Requirements
```
Functional:
  - Create short URL from long URL
  - Redirect short URL to long URL
  - Custom aliases
  - Expiry

Non-functional:
  - 100M URLs created/day (write)
  - 10B redirects/day (read) — read-heavy 100:1 ratio
  - Redirect latency < 10ms p99
  - 99.99% availability
```

### Capacity Estimation
```
Write:  100M / 86,400 = ~1,160 writes/sec
Read:   10B / 86,400  = ~115,700 reads/sec

Storage per URL: ~200 bytes (short key + long URL + metadata)
  100M URLs/day × 200B = 20GB/day
  5 years = 36TB total

Read traffic (redirects):
  115,700 req/sec → cache hit rate must be >99% to stay on fast path
```

### Architecture
```
Write path:
  Client → API → URL Service → PostgreSQL (write)
                             → Cache (invalidate)
                             → Return short URL

Read path (redirect):
  Client → CDN (cache short→long map) → Cache miss?
        → Redis (100M hot URLs cached) → Cache miss?
        → PostgreSQL (cold path)
  
Short key generation:
  Option A: Base62 encode a distributed counter (Snowflake ID → base62)
  Option B: MD5 of long URL, take first 7 chars, check collision
  Use Option A: no collisions, no DB read on write
```

```sql
CREATE TABLE urls (
    short_key   CHAR(7)     PRIMARY KEY,
    long_url    TEXT        NOT NULL,
    user_id     UUID,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at  TIMESTAMPTZ,
    click_count BIGINT      NOT NULL DEFAULT 0
);

CREATE INDEX CONCURRENTLY idx_urls_user_id ON urls(user_id);
CREATE INDEX CONCURRENTLY idx_urls_expires ON urls(expires_at)
    WHERE expires_at IS NOT NULL;
```

---

## 14.4 System Design Case Study: Deployment Orchestration Service

### Requirements
```
Functional:
  - Accept deployment job (image, config, target cluster)
  - Execute deployment steps (provision, deploy, validate)
  - Stream real-time logs to caller
  - Allow cancel/rollback
  - Retry on transient failures

Non-functional:
  - 1,000 concurrent deployments
  - Job queue durability (no jobs lost on crash)
  - Step execution idempotent (safe to retry)
  - Full audit log
```

### Architecture
```
                    ┌─────────────┐
Client ────HTTP────►│  API Server  │
                    └──────┬──────┘
                           │ Enqueue
                    ┌──────▼──────┐
                    │  Job Queue  │ (Kafka / BullMQ)
                    └──────┬──────┘
                           │ Consume
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──┐    ┌──────▼──┐    ┌──────▼──┐
     │ Worker 1 │    │ Worker 2 │    │ Worker N │
     └──────┬──┘    └──────┬──┘    └──────┬──┘
            │              │              │
            └──────────────▼──────────────┘
                           │ State persistence
                    ┌──────▼──────┐
                    │ PostgreSQL  │
                    └─────────────┘
                           │ Pub/Sub
                    ┌──────▼──────┐
                    │   Redis     │◄─── WebSocket streaming to client
                    └─────────────┘
```

```sql
CREATE TABLE deployment_jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status      VARCHAR(20) NOT NULL DEFAULT 'queued',
    config      JSONB NOT NULL,
    steps       JSONB NOT NULL DEFAULT '[]',
    current_step INT NOT NULL DEFAULT 0,
    attempts    INT NOT NULL DEFAULT 0,
    error       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    idempotency_key VARCHAR(64) UNIQUE  -- Prevent duplicate submissions
);
```

---

## 14.5 CAP Theorem Applied to Design Decisions

| System | CAP Choice | Reasoning |
|--------|-----------|-----------|
| Financial transaction service | CP | Never serve stale balance data |
| User session store | AP | Stale session data acceptable; never lock out users |
| Deployment state | CP | Correct deployment status required |
| Feature flags | AP | Slightly stale flag = acceptable |
| Distributed lock | CP | Must be consistent to prevent double-processing |
| Search index | AP | Stale search results acceptable |

---

## 14.6 Event-Driven Architecture

```
Event-Driven vs Request-Response:

Request-Response:          Event-Driven:
User ──────────────────►   User ──► API ──► Event Bus
     ◄── response ────         ↓
                          Consumers react asynchronously:
                            - Email service
                            - Audit log
                            - Analytics
                            - Billing

Benefits of event-driven:
  - Decoupled producers and consumers
  - Consumers can be added without changing producer
  - Resilient: if consumer is down, events queue up
  
Challenges:
  - Eventual consistency (harder to reason about)
  - Event schema evolution (breaking changes)
  - Debugging is harder (distributed trace needed)
  - Order guarantees limited to single partition

FDE event-driven deployment decisions:
  - Deployment notifications (Slack, email, PagerDuty) → Async events ✅
  - Deployment status query → Synchronous REST ✅
  - Audit log → Async event ✅
  - Authorization check → Synchronous (can't be eventually consistent) ✅
```
