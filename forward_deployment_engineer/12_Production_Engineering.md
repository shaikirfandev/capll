# Section 12 — Production Engineering

## 12.1 Root Cause Analysis (RCA)

RCA is the most critical skill for a senior FDE. When production breaks, your job is to find the true cause — not just the symptom — and prevent recurrence.

### The 5-Why Method
```
Incident: Customer reports API returning 503 for 12 minutes

Why 1: Why 503 errors?
  → Application pods were crashing (CrashLoopBackOff)

Why 2: Why were pods crashing?
  → OOMKilled: container memory exceeded its limit (256Mi)

Why 3: Why was memory exceeded?
  → Large payload processing job ran without streaming → loaded 800MB into RAM

Why 4: Why did a large payload arrive?
  → Customer uploaded a 50MB CSV; our code tried to parse it entirely in memory

Why 5: Why was there no protection?
  → No input size validation on the upload endpoint; memory limits not reviewed since launch

Root cause: Missing input validation + memory limits set 6 months ago when payloads were small.

Corrective actions:
  1. Immediate: Increase memory limit to 1Gi (unblocks customer)
  2. Short-term: Add 10MB file size limit on upload endpoint
  3. Long-term: Refactor file processing to use streaming (never load full file)
  4. Process: Add memory utilisation alerts at 70% threshold
```

### Fishbone Diagram (Ishikawa) for Complex Incidents
```
Categories to investigate:
  People:   Wrong deployment by human error? Training gap?
  Process:  Missing review step? Change management failure?
  Technology: Bug in code? Infrastructure misconfiguration?
  Environment: External dependency failure? Cloud provider issue?
  Data:     Unexpected data shape? Volume spike?
  Measurement: Monitoring gap that delayed detection?
```

---

## 12.2 Postmortem Documentation

A postmortem is not a blame document. It is a learning document. The most important cultural rule: **blameless postmortems**.

```markdown
# Postmortem: API 503 Errors — 2024-11-15 10:21–10:33 UTC

## Summary
The Deployment API returned 503 errors for 12 minutes affecting 100% of requests
to the /api/v1/deployments endpoint. 3 customer environments were unable to
initiate deployments during this window.

## Impact
- Duration: 12 minutes (10:21 UTC – 10:33 UTC)
- Customers affected: 3 enterprise customers
- Failed requests: ~1,440 (est. 2 req/sec × 12 min × 3 environments)
- Revenue impact: None (no SLA breach — 12 min within 30-min threshold)

## Timeline
| Time (UTC) | Event |
|------------|-------|
| 10:15      | Customer Acme Corp uploads 48MB CSV file |
| 10:21      | First 503 alert fires (5xx rate > 5%) |
| 10:22      | On-call engineer paged |
| 10:24      | Engineer identifies OOMKilled pods |
| 10:25      | Decision: restart pods + increase memory limit |
| 10:28      | Memory limit updated to 1Gi, pods restarting |
| 10:33      | All pods healthy, error rate returns to 0% |
| 10:45      | Incident declared resolved |
| 11:00      | Root cause investigation complete |

## Root Cause
Memory limit on deployment-service (256Mi) was insufficient to process
large CSV file payloads. The upload handler loaded the entire file into
memory as a Buffer before processing, causing OOMKill when a 48MB file
was uploaded.

## Contributing Factors
1. No file size limit on the upload endpoint
2. Memory limits not reviewed after CSV processing feature was added
3. No memory utilisation alert at staging — issue wasn't caught pre-production

## Corrective Actions
| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| Add 10MB upload size limit | @alice | 2024-11-17 | P0 |
| Refactor to streaming CSV parse | @bob | 2024-11-22 | P1 |
| Add memory alert at 70% | @carol | 2024-11-17 | P1 |
| Update staging memory limits to match production | @alice | 2024-11-17 | P1 |
| Load test with large files before next release | @team | Ongoing | P2 |

## What Went Well
- Alert fired within 1 minute of first error
- On-call engineer identified root cause within 4 minutes
- Mitigation was applied and working within 7 minutes of alert

## What Went Poorly
- No validation on file upload size
- Staging environment had different resource limits than production
```

---

## 12.3 Rollback Procedures

Having a documented, tested rollback plan is non-negotiable for production deployments.

```bash
#!/usr/bin/env bash
# Rollback runbook — FDE production procedure

set -euo pipefail

NAMESPACE="${1:?Usage: $0 <namespace> <previous_version>}"
VERSION="${2:?Usage: $0 <namespace> <previous_version>}"
RELEASE_NAME="myapp"

echo "=== ROLLBACK PROCEDURE ==="
echo "Namespace: $NAMESPACE"
echo "Rolling back to: $VERSION"
echo ""

# Step 1: Confirm current state
echo "--- Current State ---"
kubectl get pods -n "$NAMESPACE" -l app=myapp
helm history "$RELEASE_NAME" -n "$NAMESPACE" --max 5

# Step 2: Confirm with operator
read -p "Confirm rollback to $VERSION? [y/N]: " CONFIRM
[[ "$CONFIRM" != "y" ]] && { echo "Rollback cancelled."; exit 1; }

# Step 3: Execute rollback
echo "--- Executing Rollback ---"
helm rollback "$RELEASE_NAME" 0 -n "$NAMESPACE" --wait --timeout 5m
# Note: revision 0 = previous revision in Helm

# Step 4: Verify pods are healthy
echo "--- Verifying Deployment ---"
kubectl rollout status deployment/myapp -n "$NAMESPACE" --timeout=120s

# Step 5: Smoke test
echo "--- Smoke Testing ---"
ENDPOINT=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}')
for i in {1..5}; do
    STATUS=$(curl -sS -o /dev/null -w "%{http_code}" "https://$ENDPOINT/health")
    echo "Attempt $i: HTTP $STATUS"
    [[ "$STATUS" == "200" ]] || { echo "SMOKE TEST FAILED"; exit 1; }
    sleep 2
done

echo ""
echo "✓ Rollback complete. Service healthy."
echo "  Please update the incident channel and create a ticket for follow-up."
```

---

## 12.4 Live Debugging

When production is broken and you have seconds to diagnose:

```bash
# === KUBERNETES LIVE DEBUGGING ===

# 1. What's happening right now?
kubectl get pods -n myapp-production -o wide
kubectl get events -n myapp-production --sort-by=.lastTimestamp | tail -20

# 2. Why is a pod failing?
kubectl describe pod myapp-xyz-123 -n myapp-production
# Look for: Events section, OOMKilled, CrashLoopBackOff, ImagePullBackOff

# 3. What does the pod say?
kubectl logs myapp-xyz-123 -n myapp-production --tail=100
kubectl logs myapp-xyz-123 -n myapp-production --previous  # Last crashed container

# 4. Get inside a running pod
kubectl exec -it myapp-xyz-123 -n myapp-production -- /bin/sh

# 5. Debug a failing pod without disrupting traffic
kubectl debug pod/myapp-xyz-123 -n myapp-production \
    --image=busybox \
    --copy-to=debug-pod

# 6. Port-forward to test directly (bypass ingress)
kubectl port-forward svc/myapp 8080:80 -n myapp-production
curl http://localhost:8080/health

# === NODE / PROCESS DEBUGGING ===

# High CPU — which process?
top -b -n 3 -d 1 | grep -E "^( |[0-9])" | sort -k9 -rn | head -10

# What syscalls is a process making?
strace -p <pid> -e trace=network,file -s 500 2>&1 | head -50

# Open files and connections
lsof -p <pid>
lsof -i :5432    # Who's connecting to postgres?

# Memory — what's in RAM?
cat /proc/<pid>/status | grep -i vm
cat /proc/<pid>/smaps_rollup

# Network — where are packets going?
ss -tnp | grep <pid>
tcpdump -i any -nn port 5432 -c 100

# === DATABASE DEBUGGING ===
# Active queries (PostgreSQL)
SELECT pid, now() - query_start AS duration, state, query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < now() - interval '5 seconds'
ORDER BY duration DESC;

# Locks
SELECT l.pid, a.query, l.mode, l.granted
FROM pg_locks l
JOIN pg_stat_activity a ON a.pid = l.pid
WHERE NOT l.granted;

# Table sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;
```

---

## 12.5 Performance Analysis

### Application Performance Profiling
```python
# Python: Profile CPU bottleneck
import cProfile
import pstats
import io

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(20)  # Top 20 functions
    print(stream.getvalue())
    return result

# Line profiler (pip install line_profiler)
from line_profiler import LineProfiler

@profile  # Add @profile decorator to any function
def process_data(records):
    # Line-by-line timing output
    result = []
    for r in records:
        result.append(transform(r))
    return result
```

### Load Testing
```python
# Locust — Python load testing (used at Stripe, etc.)
from locust import HttpUser, task, between

class DeploymentAPIUser(HttpUser):
    wait_time = between(1, 3)  # Think time between requests
    
    def on_start(self):
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
    
    @task(3)  # 3x more frequent than other tasks
    def list_deployments(self):
        self.client.get("/api/v1/deployments",
                        headers={"Authorization": f"Bearer {self.token}"})
    
    @task(1)
    def get_deployment_detail(self):
        self.client.get("/api/v1/deployments/dep-12345",
                        headers={"Authorization": f"Bearer {self.token}"})
    
    @task(1)
    def create_deployment(self):
        self.client.post("/api/v1/deployments",
                         headers={"Authorization": f"Bearer {self.token}"},
                         json={"name": "test-deploy", "version": "1.0.0", 
                               "environment": "staging"})

# Run: locust -f locustfile.py --host=https://staging.myapp.com
#       Open http://localhost:8089 → set users=100, ramp=10/s
```

---

## 12.6 Capacity Planning

```
Before deploying to a customer:

1. Baseline metrics
   - Current QPS: 50 req/sec
   - p99 latency: 120ms
   - CPU per request: ~2ms CPU time
   - Memory per connection: ~8MB

2. Forecast
   - Customer expects: 500 req/sec peak (10x current)
   - Expected growth in 12 months: 200%

3. Calculate resources needed
   CPU:
     500 req/sec × 2ms CPU = 1 CPU second/second = 1 vCPU
     With 70% utilisation target → 1.43 vCPU → 2 vCPUs minimum
     For 3-pod redundancy → 3 × 2 vCPU pods = 6 vCPU total
   
   Memory:
     500 connections × 8MB = 4GB
     Plus application heap (~512MB) → 5GB
     With 3 pods → 2GB per pod

4. Plan for failure
   Design for 2x expected peak (traffic spikes, slow dependencies)
   Configure HPA: scale up at 70% CPU, scale down at 30%
   Set minReplicas=3 (for AZ redundancy)

5. Cost estimate
   3 × {2 vCPU, 4GB RAM} ECS Fargate: ~$200/month
   RDS db.t3.large (2 vCPU, 8GB): ~$120/month
   Total: ~$320/month → present to customer with margin
```
