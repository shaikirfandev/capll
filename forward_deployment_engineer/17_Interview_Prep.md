# Section 17 — Interview Preparation

## 17.1 FDE Technical Interview Format

Companies like Palantir, OpenAI, Datadog, and Stripe typically structure FDE interviews in 4–5 rounds:

| Round | Format | Duration | What They Evaluate |
|-------|--------|----------|--------------------|
| 1 | Technical Screen | 45 min | Coding + problem solving |
| 2 | System Design | 60 min | Architecture thinking |
| 3 | Production Engineering | 60 min | Debugging, ops, incident response |
| 4 | Deployment Scenario | 60 min | Customer scenario + delivery |
| 5 | Behavioural / Culture | 45 min | Communication, ownership, judgment |

---

## 17.2 Coding Questions (FDE Focus)

Unlike pure SWE roles, FDE coding questions skew towards real-world utilities and data processing.

### Q1: Implement a rate limiter
```python
# Design and implement a thread-safe rate limiter with sliding window

from collections import deque
import threading
import time

class RateLimiter:
    """
    Sliding window rate limiter.
    Allows at most `limit` requests per `window_seconds` seconds.
    """
    def __init__(self, limit: int, window_seconds: float):
        self._limit = limit
        self._window = window_seconds
        self._requests = deque()
        self._lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        now = time.monotonic()
        cutoff = now - self._window
        
        with self._lock:
            # Remove expired entries
            while self._requests and self._requests[0] < cutoff:
                self._requests.popleft()
            
            if len(self._requests) < self._limit:
                self._requests.append(now)
                return True
            return False

# Test
limiter = RateLimiter(limit=3, window_seconds=1.0)
for i in range(5):
    result = limiter.is_allowed()
    print(f"Request {i+1}: {'ALLOWED' if result else 'BLOCKED'}")
# Expected: ALLOWED ALLOWED ALLOWED BLOCKED BLOCKED
```

### Q2: Parse and aggregate log file
```python
# Given a log file, find the top 5 endpoints by error rate
# Log format: timestamp method path status_code response_time_ms

from collections import defaultdict
import re

def analyse_logs(filepath: str) -> list[dict]:
    pattern = re.compile(
        r'(\S+) (GET|POST|PUT|DELETE|PATCH) (\S+) (\d{3}) (\d+)'
    )
    
    stats = defaultdict(lambda: {"total": 0, "errors": 0})
    
    with open(filepath) as f:
        for line in f:
            m = pattern.search(line)
            if not m:
                continue
            _, method, path, status, _ = m.groups()
            key = f"{method} {path}"
            stats[key]["total"] += 1
            if int(status) >= 500:
                stats[key]["errors"] += 1
    
    results = [
        {
            "endpoint":   k,
            "total":      v["total"],
            "errors":     v["errors"],
            "error_rate": v["errors"] / v["total"] if v["total"] else 0,
        }
        for k, v in stats.items()
        if v["total"] >= 10  # Minimum sample size
    ]
    
    return sorted(results, key=lambda x: x["error_rate"], reverse=True)[:5]
```

### Q3: Implement circuit breaker
```python
# See Section 02 — Design Patterns for full implementation
# Interview tip: explain state machine (CLOSED → OPEN → HALF_OPEN → CLOSED)
# and when each transition occurs
```

### Q4: Kubernetes pod scheduler (simplified)
```python
# Given nodes with available CPU/memory and pods with requirements,
# assign pods to nodes using bin-packing

from dataclasses import dataclass
from typing import Optional

@dataclass
class Node:
    name:       str
    cpu_milli:  int
    memory_mb:  int

@dataclass
class Pod:
    name:       str
    cpu_req:    int
    memory_req: int

def schedule_pods(nodes: list[Node], pods: list[Pod]) -> dict[str, str]:
    """
    First-fit decreasing bin packing.
    Returns: {pod_name: node_name}
    """
    available = {n.name: {"cpu": n.cpu_milli, "mem": n.memory_mb} for n in nodes}
    assignment = {}
    
    # Sort pods by resource requirement (largest first)
    sorted_pods = sorted(pods, key=lambda p: p.cpu_req + p.memory_req, reverse=True)
    
    for pod in sorted_pods:
        placed = False
        for node_name, res in available.items():
            if res["cpu"] >= pod.cpu_req and res["mem"] >= pod.memory_req:
                res["cpu"] -= pod.cpu_req
                res["mem"] -= pod.memory_req
                assignment[pod.name] = node_name
                placed = True
                break
        if not placed:
            assignment[pod.name] = None  # Unschedulable
    
    return assignment
```

---

## 17.3 System Design Questions

### Q: Design a deployment platform for 10,000 enterprise customers

**Framework Answer:**
```
Step 1: Clarify requirements
  - How many concurrent deployments? ~10,000/day, ~100/hour peak
  - Average deployment duration? 5 minutes
  - Cloud targets? AWS, Azure, GCP, on-prem
  - Deployment methods? Kubernetes (Helm), Docker Compose, direct VMs
  - Customer isolation requirement? High — SOC2 Type II

Step 2: High-level design
  API Layer → Queue → Worker Pool → Target Infrastructure
  Control plane (shared) + Data plane (per customer)

Step 3: Key components
  - API Server: auth, rate limiting, job submission
  - Job Queue: Kafka (durability, replay, fan-out)
  - Workers: one pool per cloud target
  - State Store: PostgreSQL (job state, audit log)
  - Real-time: WebSocket (log streaming to user)
  - Secrets: Vault (per-customer cloud credentials)

Step 4: Scale
  100 concurrent deployments × 5 min = 500 pod-minutes/day
  Worker pool: 50 workers, each handling 2 concurrent deployments
  Queue: Kafka with 10 partitions, 10 consumer group members

Step 5: Failure modes
  - Worker crash: job requeued (Kafka consumer group rebalance)
  - Queue down: Kafka 3-node cluster, RF=3
  - Database down: Patroni automatic failover
  - Cloud provider outage: jobs queued, timeout alerts to customer
```

### Q: Design a multi-tenant secrets manager

```
Key decisions:
  - Per-tenant encryption keys (KMS key per tenant)
  - Hierarchical access: tenant admin → team → service
  - Audit log: every read/write/delete
  - Secret rotation: automated + manual trigger
  - Versioning: keep previous 5 versions
  
Schema:
  tenants(id, name, kms_key_arn)
  secrets(id, tenant_id, name, encrypted_value, version, created_at)
  access_policies(id, secret_id, principal_type, principal_id, actions)
  audit_log(id, secret_id, principal_id, action, ip, timestamp)
```

---

## 17.4 Production Engineering Questions

### Q: A customer reports the API has been returning errors for 30 minutes. What do you do?

```
Model Answer (STAR format + structured approach):

1. ASSESS SEVERITY (2 minutes)
   - "What percentage of requests are failing?" 
   - "Is it all endpoints or specific ones?"
   - "What does the monitoring show?"
   → Check: Datadog/Grafana error rate dashboard

2. IMMEDIATE COMMUNICATION (1 minute)
   - Open incident channel
   - Send first status update to customer

3. IDENTIFY IMPACT (3 minutes)
   - Check pods: kubectl get pods -n <namespace>
   - Check recent events: kubectl get events --sort-by=.lastTimestamp
   - Check metrics: error rate, latency, resource usage

4. HYPOTHESISE ROOT CAUSE
   - Recent deployment? (check helm history)
   - Infrastructure change? (check CloudTrail)
   - Traffic spike? (check request rate)
   - External dependency? (check outbound API health)

5. MITIGATE FIRST (don't wait for root cause)
   - If deployment: rollback with helm rollback
   - If pods OOMKilled: increase memory limit
   - If DB saturated: kill long-running queries, increase connections

6. VERIFY RESOLUTION
   - Error rate returns to baseline?
   - Smoke test 5 endpoints

7. ROOT CAUSE ANALYSIS (post-incident)
   - 5 whys
   - Write postmortem within 48h
```

### Q: Memory usage is growing without bound in production. Diagnose it.

```
Memory leak investigation:

1. Confirm: is it a leak or a load increase?
   kubectl top pods -n myapp  →  steady growth = leak

2. What's using memory?
   kubectl exec -it pod/myapp-xyz -- /bin/sh
   cat /proc/1/status | grep VmRSS
   node -e "console.log(process.memoryUsage())"

3. Language-specific:
   Node.js:
     - Enable heap dump: kill -USR2 <pid>  (if clinic.js or heapdump installed)
     - Check: closures holding large data, event listener leaks, cache without TTL
   Python:
     - tracemalloc.start(), take snapshot before/after
     - Check: circular references, unbounded lists, global caches

4. Common causes:
   - Unbounded in-memory cache (never evicted)
   - Event listeners registered but never removed
   - Database connection objects leaked (not closed)
   - Node.js streams not properly destroyed
   - Circular reference preventing GC

5. Quick mitigation:
   - Add memory alert at 80% and restart before OOM
   - Set --max-old-space-size for Node.js
   - Configure resource limits + livenessProbe to restart unhealthy pods
```

---

## 17.5 Behavioural Questions (STAR Format)

### Q: Tell me about a time you prevented a production incident.

**Structure:**
```
Situation: Context (company, system, scale)
Task:       What was your responsibility?
Action:     Specific steps you took (technical detail)
Result:     Measurable outcome

Example:
S: We were upgrading the customer's Kubernetes version from 1.25 → 1.28.
   This is a 3-version jump, affecting 500 customer pods.

T: I was the lead FDE responsible for coordinating the upgrade
   across 3 environments with zero downtime.

A: - Read all deprecation notices between 1.25 and 1.28
   - Ran pluto (deprecation scanner) against all manifests — found 12 deprecated APIs
   - Updated all manifests (PodDisruptionBudgets, HPA) to use new API versions
   - Staged upgrade: dev → staging → prod, with 48h observation window per stage
   - Created rollback runbook + tested it on dev
   - Scheduled maintenance window with customer and executed upgrade
     with cordon/drain/uncordon pattern per node

R: Upgrade completed with zero downtime.
   0 incidents.
   Customer security team praised the thoroughness of the change doc.
   Created internal playbook adopted by 4 other FDEs.
```

### Q: Tell me about a time you had a difficult conversation with a customer.

```
Example answer framework:
  - Customer expectations were out of sync with what was technically feasible
  - You had to deliver bad news (delay, limitation, or cost increase)
  - How you prepared, how you delivered it with empathy + data
  - What the outcome was (they accepted the honest trade-off)

Key principles to demonstrate:
  - Honesty over people-pleasing
  - Data-driven communication
  - Alternative proposal ready
  - Customer's business outcome at the centre
```

---

## 17.6 150 Quick-Fire Q&A

### Infrastructure
```
Q: What is the difference between RTO and RPO?
A: RTO (Recovery Time Objective) = how fast you must restore service after failure.
   RPO (Recovery Point Objective) = how much data loss is acceptable.
   Example: RTO=1hr, RPO=5min → restore within 1 hour, lose at most 5 min of data.

Q: What is the purpose of a bastion host?
A: A hardened jump server in the public subnet that allows SSH access
   to instances in private subnets. Limits attack surface — SSH to private
   instances only via the bastion.

Q: What is VPC peering vs VPN vs Transit Gateway?
A: VPC Peering: private, direct connection between 2 VPCs (same or different accounts)
   Site-to-site VPN: encrypted tunnel over internet to customer on-prem network
   Transit Gateway: hub-and-spoke, connects many VPCs + on-prem networks centrally

Q: What is the difference between horizontal and vertical scaling?
A: Vertical: add more CPU/RAM to existing machine (scale up)
   Horizontal: add more machines (scale out)
   Horizontal preferred: no downtime, fault tolerant, cheaper at scale.
```

### Kubernetes
```
Q: What is the difference between Deployment and StatefulSet?
A: Deployment: stateless pods, random names, any-order scheduling
   StatefulSet: stateful pods, stable network identity (pod-0, pod-1),
   ordered startup/shutdown, persistent volume per pod.
   Use StatefulSet for databases, Kafka, Zookeeper.

Q: What is a PodDisruptionBudget?
A: Limits number of pods that can be simultaneously unavailable during voluntary
   disruptions (node drain, cluster upgrade). Protects availability during maintenance.

Q: What happens when a pod is OOMKilled?
A: Container's memory usage exceeded its limit → kernel kills the process.
   Pod status shows "OOMKilled" in last state.
   Fix: increase memory limit or find memory leak.

Q: Explain Kubernetes readiness vs liveness probe.
A: Readiness: "Is pod ready to receive traffic?" → removes pod from Service if failing
   Liveness:  "Is pod alive?" → restarts pod if failing
   Use readiness to take pods out of rotation during cold start.
   Use liveness to recover from deadlocks.
```

### Databases
```
Q: What is a deadlock in PostgreSQL? How do you resolve it?
A: Two transactions waiting for locks held by each other — both block indefinitely.
   PostgreSQL detects and kills one transaction automatically.
   Resolution: always acquire locks in consistent order across transactions.
   Investigate: SELECT * FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid;

Q: What is the difference between TRUNCATE and DELETE?
A: DELETE: row-by-row, triggers fire, can be rolled back, slow for large tables
   TRUNCATE: deallocates pages, no triggers, faster, minimal logging
   Use TRUNCATE when clearing large tables in maintenance windows.

Q: Explain connection pooling. Why do you need it?
A: Databases have a limit on concurrent connections (typically 100–200 for Postgres).
   Each application instance connects multiple times.
   Without pooling: N instances × M connections = thousands of DB connections.
   With PgBouncer: N instances × M connections → 10-20 real connections.
   Transaction mode: connection returned to pool after each transaction.
```

### Security
```
Q: What is the difference between authentication and authorisation?
A: Authentication: verifying identity (who are you?)
   Authorisation: verifying permission (what are you allowed to do?)
   JWT verifies authentication. RBAC policy enforces authorisation.

Q: What is SSRF?
A: Server-Side Request Forgery: attacker tricks server into making HTTP requests
   to internal services (AWS metadata, internal APIs).
   Prevention: whitelist allowed domains, reject private IP ranges.

Q: Explain certificate pinning.
A: App accepts only a specific certificate (or its public key) for a domain.
   Prevents man-in-the-middle even with a valid CA-signed cert.
   Used in mobile apps and high-security API clients.

Q: What is the difference between symmetric and asymmetric encryption?
A: Symmetric: same key for encrypt and decrypt (AES). Fast. Key distribution problem.
   Asymmetric: public key encrypts, private key decrypts (RSA, ECDH). Slower.
   TLS uses asymmetric for key exchange, then symmetric (AES) for data.
```

### Networking
```
Q: What happens when you type "google.com" in a browser?
A: 1. Browser checks local cache / OS cache for DNS
   2. DNS resolver queries root → TLD → google.com nameservers
   3. Returns A record (IP address)
   4. Browser establishes TCP connection (3-way handshake)
   5. TLS handshake (negotiate cipher, verify certificate)
   6. HTTP GET /
   7. Server responds with HTML
   8. Browser parses HTML, fetches CSS/JS/images
   9. Page renders

Q: What is a subnet mask?
A: Defines which part of an IP is network vs host.
   10.0.1.0/24: /24 means 24 bits network (10.0.1), 8 bits host (0-255)
   Gives 254 usable hosts.

Q: Explain the TCP handshake.
A: SYN → (client initiates)
   SYN-ACK → (server responds)
   ACK → (client confirms)
   3 steps to establish connection.
   FIN / FIN-ACK / ACK to close.
```
