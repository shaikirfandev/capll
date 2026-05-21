# Section 18 — Case Studies

## Case Study 1: Production Database Outage at Scale

**Company Type:** Enterprise SaaS (fintech customer, 500k end users)  
**Duration:** 47 minutes total impact  
**Severity:** SEV-1

### What Happened
```
Timeline:
  14:23  — Scheduled Postgres maintenance: vacuum + reindex on production DB
  14:24  — Autovacuum lock conflict: VACUUM FULL blocked by long-running transaction
  14:31  — Table bloat growing, query planner choosing sequential scans
  14:35  — Application latency spikes (p99: 45ms → 4,200ms)
  14:37  — Health checks failing → Kubernetes starts killing pods (unhealthy)
  14:38  — SEV-1 declared: 503s across all endpoints
  14:40  — FDE on-call paged
  14:43  — FDE identifies cause: VACUUM FULL holding AccessShareLock
  14:45  — Decision: kill VACUUM FULL + long-running transaction
  14:47  — Locks released, query planner back to index scans
  14:52  — Latency returns to normal (p99: 48ms)
  15:10  — Incident declared resolved
```

### Root Cause
A scheduled `VACUUM FULL` ran during business hours. An existing 23-minute-old transaction (batch analytics job) held an `AccessShareLock` that conflicted with `VACUUM FULL`'s `AccessExclusiveLock`. As VACUUM FULL waited, subsequent queries were queued behind it — PostgreSQL lock queue is FIFO, causing a pile-up.

### What Should Have Been Done Differently
```
1. VACUUM FULL should NEVER run during business hours.
   Use: VACUUM (not FULL) for routine maintenance — it doesn't lock.
   Use: VACUUM FULL only during scheduled maintenance windows.

2. Long-running transactions must be monitored.
   Alert: "Transaction running > 5 minutes" should fire.
   The 23-min analytics job had no timeout configured.

3. Maintenance jobs should kill long-running transactions first.
   SET lock_timeout = '5s'; on maintenance sessions.
   Fail fast rather than pile up locks.

4. Health check should have been smarter.
   Kubernetes restarted pods (making it worse by killing established connections)
   because health check measured response time, not DB health.
   Better: readinessProbe checks DB connection directly.
```

### Corrective Actions
```
Immediate:
  ✅ Documented that VACUUM FULL is prohibited during business hours
  ✅ Removed VACUUM FULL from cron job (replaced with VACUUM ANALYZE)

Short-term:
  ✅ Alert: pg_stat_activity transaction age > 5 minutes
  ✅ Alert: pg_stat_activity query age > 30 seconds
  ✅ Set statement_timeout = 60000 (60s) for analytics service

Long-term:
  ✅ Implemented pg_cron for maintenance jobs with time-window restrictions
  ✅ Analytics batch job refactored to run outside business hours
  ✅ Runbook: "Database lock pile-up" added to internal playbooks
```

---

## Case Study 2: Kubernetes Deployment Gone Wrong

**Company Type:** DevTools SaaS  
**Duration:** 34-minute rollout → 20-minute rollback  
**Severity:** SEV-2

### What Happened
```
Context:
  Release v3.4.0 included a database migration: added NOT NULL column without default.
  The migration ran on 1 schema, but code v3.4.0 required the column to exist.
  
Timeline:
  09:00  — v3.4.0 deployed to production via Helm rolling update
  09:02  — First pod running v3.4.0 starts serving traffic
  09:02  — Errors begin: "column 'owner_id' of table 'deployments' does not exist"
  09:04  — 50% of pods running v3.4.0 (rolling update progress)
  09:05  — Error rate reaches 45%
  09:06  — FDE on-call investigates
  09:08  — Root cause identified: migration not run before deployment
  09:09  — Decision: rollback code (not run reverse migration — too risky)
  09:11  — helm rollback myapp 1 executed
  09:15  — All pods back to v3.3.2
  09:16  — Error rate drops to 0%
  09:18  — Incident resolved
  09:30  — Emergency migration run on DB
  10:00  — v3.4.0 redeployed successfully
```

### Root Cause
Deployment process required running database migration BEFORE deploying new code. This step was manual — and was skipped. The rolling update meant v3.3.2 (old code) and v3.4.0 (new code) ran simultaneously, with v3.4.0 requiring a column that didn't exist.

### What Should Have Been Done Differently
```
1. Migrations must run as part of the deployment, not manually.
   Kubernetes init container pattern:
   
   initContainers:
     - name: run-migrations
       image: myapp:3.4.0
       command: ["npm", "run", "db:migrate"]
       env: [DB credentials]
   
   containers:
     - name: app
       image: myapp:3.4.0
   
   Init container runs migration before any app pod starts.
   If migration fails, deployment stops — no broken state.

2. Backward-compatible migrations for rolling deployments.
   Deploy in 2 phases:
     Phase 1: Add column as nullable (no default required)
     Phase 2: Backfill data → add NOT NULL constraint → deploy v3.4.0
   
   Old code ignores new column.
   New code requires new column — but it exists.

3. CI/CD should validate migration compatibility.
   Test: does old code run with new schema? (run both versions against migrated DB)
   Test: does migration run cleanly on production-sized dataset?
```

---

## Case Study 3: Memory Leak in Production Node.js Service

**Company Type:** Cloud infrastructure company  
**Impact:** 15% performance degradation, 2 restarts over 72 hours  
**Severity:** SEV-3 escalated to SEV-2

### What Happened
```
Symptoms observed:
  - Deployment service memory usage growing from 512MB at startup
    to 2.1GB over 8 hours, then OOMKilled
  - After each OOMKill + restart: memory grows again
  - No corresponding increase in request rate

Investigation:
  1. Enabled --expose-gc and heapsnapshot
  2. Captured heap snapshot at startup (512MB): 12k live objects
  3. Captured heap snapshot after 6 hours (1.8GB): 890k live objects
  
  Heap comparison showed:
    - EventEmitter instances: 842k objects (vs 120 at startup)
    - Most retained by: "deploymentWorker" module
  
  Code inspection revealed:
    async function watchDeployment(id: string) {
        const worker = new Worker(id);
        worker.on("log", (line) => logBuffer.push(line));  // ← added listener
        worker.on("completed", () => {
            // worker finished — but listener never removed!
        });
    }
    // Each deployment adds 2 listeners to 'worker' EventEmitter
    // Workers are cached in a Map — never garbage collected
    // Over thousands of deployments: thousands of listeners
```

### Root Cause
Event listeners added to Worker instances were never removed when deployments completed. The Worker cache retained references to workers, preventing GC. Each deployment added 2 listeners; after 10,000 deployments, 20,000 listeners accumulated.

### Fix
```typescript
async function watchDeployment(id: string) {
    const worker = new Worker(id);
    
    const onLog = (line: string) => logBuffer.push(line);
    const onCompleted = () => {
        // Remove listeners to allow GC
        worker.off("log", onLog);
        worker.off("completed", onCompleted);
        worker.off("error", onError);
        
        // If caching, check if still needed
        if (!workerCache.has(id)) {
            worker.destroy();
        }
    };
    const onError = (err: Error) => {
        worker.off("log", onLog);
        worker.off("completed", onCompleted);
        worker.off("error", onError);
        log.error("Worker error", { deploymentId: id, error: err.message });
    };
    
    worker.on("log",       onLog);
    worker.on("completed", onCompleted);
    worker.on("error",     onError);
    
    // Also: set max listeners to avoid Node.js warning
    worker.setMaxListeners(10);
}

// Add memory monitoring
setInterval(() => {
    const { heapUsed, heapTotal } = process.memoryUsage();
    metrics.gauge("memory.heap_used_bytes", heapUsed);
    
    if (heapUsed > 1.5 * 1024 * 1024 * 1024) {  // 1.5GB
        log.warn("High memory usage", { 
            heap_used_gb: (heapUsed / 1e9).toFixed(2) 
        });
    }
}, 30_000);
```

---

## Case Study 4: Failed Multi-Region Deployment

**Company Type:** Government defence contractor (on-prem Kubernetes)  
**Impact:** 6-hour deployment delay (no user impact — staging environment)  
**Lesson:** Pre-flight validation saves deployment day

### What Happened
```
Context:
  Deploying platform to customer's air-gapped on-premise Kubernetes cluster.
  No internet access — all images must be pre-loaded.
  
Failure sequence:
  Day 1 - 09:00: Begin deployment
  Day 1 - 09:15: Helm install fails: ImagePullBackOff
    → Container registry not accessible from air-gapped environment
    → Images were not pre-loaded (assumed the previous FDE did it)
    
  Day 1 - 09:30: Begin loading images manually
    → docker save → scp to bastion → docker load
    → 12 images × 2GB average = 24GB transfer at 50MB/s = 8 minutes each
    → Total: ~2 hours
    
  Day 1 - 11:30: Images loaded, redeploy
  Day 1 - 11:45: New failure: PersistentVolumeClaim pending
    → Storage class "gp2" not available in customer cluster
    → Customer uses "local-storage" only
    
  Day 1 - 12:30: Storage class corrected in values.yaml, redeploy
  Day 1 - 13:00: New failure: ServiceAccount creation forbidden
    → ClusterRoleBinding required FDE to have cluster-admin
    → Customer security policy: no cluster-admin during business hours
    
  Day 1 - 15:00: Cluster-admin granted (after customer approval process)
  Day 1 - 15:30: Deployment successful
```

### What Should Have Been Done Differently
```
Pre-flight checklist (every air-gapped/on-prem deployment):

Infrastructure:
  □ Container registry reachable from cluster? (test with kubectl run)
  □ All container images pre-loaded and tagged correctly?
  □ Required storage class exists? kubectl get storageclass
  □ Sufficient PV provisioned? kubectl get pv
  □ Node resource capacity sufficient? kubectl top nodes

Permissions:
  □ FDE credentials have required RBAC permissions? kubectl auth can-i
  □ ServiceAccount creation permitted?
  □ ClusterRoleBinding creation permitted?
  □ PersistentVolumeClaim creation permitted?

Network:
  □ DNS resolution working inside cluster?
  □ Required outbound ports open (if not fully air-gapped)?
  □ Certificate authorities loaded?

Time:
  □ Node time synchronised (NTP/PTP)? — critical for JWT, Kafka, TLS

Lesson: Build and run a pre-flight validation script BEFORE the deployment window.
If anything fails in pre-flight, reschedule — don't try to fix under pressure.
```

---

## Case Study 5: AWS Cost Explosion

**Company Type:** AI startup (customer-managed AWS)  
**Impact:** $84,000 unexpected AWS bill in 30 days  
**Root Cause:** Misconfigured autoscaler + GPU instances

### What Happened
```
Customer deployed ML inference workload.
FDE configured HPA (Horizontal Pod Autoscaler) with:
  - minReplicas: 1
  - maxReplicas: 50  ← No upper cost limit agreed
  - CPU target: 70%

Cluster autoscaler was also enabled:
  - Added new g5.12xlarge instances ($16.29/hour) when pods couldn't schedule

Traffic spike (marketing campaign) caused:
  Day 1:  3 GPU instances     $39/hour    = $936/day
  Day 7:  12 GPU instances    $196/hour   = $4,700/day
  Day 14: 30 GPU instances    $489/hour   = $11,700/day
  Day 30: Bill arrives: $84,000

No cost alerts were configured.
No max node count was set on cluster autoscaler.
No budget threshold notification.
```

### Lessons for FDEs
```
Before deploying any autoscaling:
  □ Set realistic maxReplicas (not 50 unless agreed)
  □ Set cluster autoscaler max-nodes per node group
  □ Configure AWS Cost Anomaly Detection alerts
  □ Create AWS Budget with monthly threshold + email alert
  □ Run cost estimate: "If HPA scales to max, cost = $X/day"
  □ Present cost scenarios to customer before go-live
  □ Set up weekly cost report to customer

AWS Cost Guardrails:
  aws budgets create-budget --account-id $ACCOUNT_ID --budget '{
    "BudgetName": "myapp-monthly",
    "BudgetLimit": {"Amount": "5000", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{
      "SubscriptionType": "EMAIL",
      "Address": "fde-team@company.com"
    }]
  }]'
```
