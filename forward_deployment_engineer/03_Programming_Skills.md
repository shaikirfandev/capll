# Section 03 — Programming Skills

## 3.1 JavaScript — From Beginner to Production-Grade

### Core Language Mechanics
```javascript
// Event loop — critical to understand for Node.js FDE work
console.log("1");                          // Synchronous
setTimeout(() => console.log("2"), 0);    // Macro-task queue
Promise.resolve().then(() => console.log("3")); // Micro-task queue
console.log("4");
// Output: 1, 4, 3, 2  (micro-tasks before macro-tasks)

// Closures — used heavily in middleware and callbacks
function createRateLimiter(maxRPS) {
    let count = 0;
    setInterval(() => count = 0, 1000); // Reset every second
    
    return function check() {
        if (count >= maxRPS) throw new Error("Rate limit exceeded");
        count++;
        return true;
    };
}
const limiter = createRateLimiter(100);

// Destructuring + spread — common in API response handling
const { data: { users, total }, meta: { page } } = apiResponse;
const merged = { ...defaultConfig, ...userConfig };         // shallow merge
const allUsers = [...usersFromCache, ...usersFromDB];       // array merge
```

### Async Patterns
```javascript
// Pattern 1: async/await with proper error handling
async function deployService(config) {
    try {
        const validated = await validateConfig(config);
        const result    = await provisionInfra(validated);
        await updateDNS(result.endpoint);
        return { status: "deployed", endpoint: result.endpoint };
    } catch (err) {
        await rollback(config.serviceId);
        throw new DeploymentError(`Deployment failed: ${err.message}`, err);
    }
}

// Pattern 2: Parallel execution — don't await sequentially when independent
async function healthCheckAll(services) {
    const checks = services.map(s => checkHealth(s).catch(e => ({ service: s, error: e })));
    const results = await Promise.allSettled(checks);
    return results.map((r, i) => ({
        service: services[i],
        healthy: r.status === "fulfilled" && r.value.ok
    }));
}

// Pattern 3: Async generator for streaming responses (LLM, logs)
async function* streamLogs(deploymentId) {
    const response = await fetch(`/api/deployments/${deploymentId}/logs`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        yield decoder.decode(value);
    }
}
```

---

## 3.2 TypeScript — Production-Grade Typing

```typescript
// Discriminated unions — model API states without null checks
type DeploymentState =
    | { status: "pending";   createdAt: Date }
    | { status: "running";   startedAt: Date; progress: number }
    | { status: "completed"; startedAt: Date; completedAt: Date; endpoint: string }
    | { status: "failed";    error: string;   rollbackAt?: Date };

function handleDeployment(state: DeploymentState): string {
    switch (state.status) {
        case "running":    return `Progress: ${state.progress}%`;
        case "completed":  return `Live at: ${state.endpoint}`;
        case "failed":     return `Error: ${state.error}`;
        default:           return "Pending...";
    }
}

// Generic utility types — config management
type Required<T> = { [K in keyof T]-?: T[K] };
type Partial<T>  = { [K in keyof T]?: T[K] };

interface DeploymentConfig {
    name:         string;
    image:        string;
    replicas:     number;
    env?:         Record<string, string>;
    resources?:   { cpu: string; memory: string };
}

// Use Zod for runtime validation (critical for FDE — customer configs are untrusted)
import { z } from "zod";

const DeploymentConfigSchema = z.object({
    name:     z.string().min(1).max(63).regex(/^[a-z0-9-]+$/),
    image:    z.string().includes(":"),
    replicas: z.number().int().min(1).max(50),
    env:      z.record(z.string()).optional(),
});

function parseCustomerConfig(raw: unknown): DeploymentConfig {
    return DeploymentConfigSchema.parse(raw); // throws ZodError if invalid
}
```

---

## 3.3 Python — The FDE Automation Language

Python is the primary scripting language for FDEs. You will use it for: data migration scripts, automation, API integrations, monitoring utilities, and quick prototypes.

### Production Python Patterns

```python
# Config management with Pydantic (type-safe, validated)
from pydantic import BaseSettings, validator
from typing import Optional

class Settings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_name: str
    db_password: str  # Loaded from env — never hardcoded
    
    kafka_brokers: list[str]
    kafka_topic: str
    
    max_retries: int = 3
    request_timeout_s: float = 30.0
    
    @validator("kafka_brokers", pre=True)
    def parse_brokers(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v
    
    class Config:
        env_file = ".env"

settings = Settings()  # reads from environment variables

# Context manager — resource cleanup critical in FDE scripts
class ManagedDBConnection:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._conn = None
    
    def __enter__(self):
        self._conn = psycopg2.connect(self._dsn)
        return self._conn.cursor()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            if exc_type:
                self._conn.rollback()
            else:
                self._conn.commit()
            self._conn.close()

with ManagedDBConnection(settings.db_dsn) as cursor:
    cursor.execute("SELECT COUNT(*) FROM users WHERE migrated = false")
    pending = cursor.fetchone()[0]
    print(f"Pending migration: {pending} records")

# Concurrent data migration with thread pool
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

def migrate_batch(batch: list[dict], worker_id: int) -> dict:
    success = failure = 0
    for record in batch:
        try:
            transform_and_insert(record)
            success += 1
        except Exception as e:
            failure += 1
            log.warning(f"Worker {worker_id}: failed record {record['id']}: {e}")
    return {"success": success, "failure": failure}

def run_migration(records: list[dict], workers: int = 8):
    batches = [records[i::workers] for i in range(workers)]
    totals = {"success": 0, "failure": 0}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(migrate_batch, b, i): i 
                   for i, b in enumerate(batches)}
        for future in as_completed(futures):
            result = future.result()
            totals["success"] += result["success"]
            totals["failure"] += result["failure"]
    
    print(f"Migration complete: {totals['success']} success, {totals['failure']} failed")
```

### Python Async (FastAPI / aiohttp — common FDE backend pattern)
```python
import asyncio
import aiohttp
from fastapi import FastAPI, HTTPException

app = FastAPI()

async def fetch_service_health(session: aiohttp.ClientSession, url: str) -> dict:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            return {"url": url, "status": resp.status, "ok": resp.status == 200}
    except asyncio.TimeoutError:
        return {"url": url, "status": 0, "ok": False, "error": "timeout"}

@app.get("/health/all")
async def check_all_services():
    services = ["http://svc-a/health", "http://svc-b/health", "http://svc-c/health"]
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_service_health(session, url) for url in services]
        results = await asyncio.gather(*tasks)
    return {"services": results, "all_healthy": all(r["ok"] for r in results)}
```

---

## 3.4 Go — High-Performance FDE Services

Go is used at Stripe, Datadog, Uber, and Google. FDEs often write small, high-performance integration services and CLI tools in Go.

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "sync"
    "time"
)

// Idiomatic Go: struct with methods, explicit error handling
type DeploymentClient struct {
    baseURL    string
    httpClient *http.Client
    apiKey     string
}

func NewDeploymentClient(baseURL, apiKey string) *DeploymentClient {
    return &DeploymentClient{
        baseURL: baseURL,
        apiKey:  apiKey,
        httpClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

type Deployment struct {
    ID       string    `json:"id"`
    Name     string    `json:"name"`
    Status   string    `json:"status"`
    Created  time.Time `json:"created_at"`
}

func (c *DeploymentClient) GetDeployment(ctx context.Context, id string) (*Deployment, error) {
    req, err := http.NewRequestWithContext(ctx, "GET",
        fmt.Sprintf("%s/deployments/%s", c.baseURL, id), nil)
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }
    req.Header.Set("Authorization", "Bearer "+c.apiKey)
    
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("execute request: %w", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
    }
    
    var dep Deployment
    if err := json.NewDecoder(resp.Body).Decode(&dep); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }
    return &dep, nil
}

// Goroutines for concurrent health checks
func checkServicesHealth(services []string) map[string]bool {
    results := make(map[string]bool)
    var mu sync.Mutex
    var wg sync.WaitGroup
    
    for _, svc := range services {
        wg.Add(1)
        go func(s string) {
            defer wg.Done()
            ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
            defer cancel()
            
            req, _ := http.NewRequestWithContext(ctx, "GET", s+"/health", nil)
            resp, err := http.DefaultClient.Do(req)
            healthy := err == nil && resp.StatusCode == 200
            
            mu.Lock()
            results[s] = healthy
            mu.Unlock()
        }(svc)
    }
    wg.Wait()
    return results
}
```

---

## 3.5 Bash Scripting

Bash is your Swiss Army knife as an FDE. You will write deployment scripts, health checks, data validation scripts, and automation helpers.

```bash
#!/usr/bin/env bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures
IFS=$'\n\t'        # Safe IFS

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/deploy.log"
readonly TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Logging
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
error() { log "ERROR: $*" >&2; exit 1; }
warn()  { log "WARN:  $*" >&2; }

# Dependency check
check_deps() {
    local deps=("kubectl" "helm" "terraform" "jq" "aws")
    for dep in "${deps[@]}"; do
        command -v "$dep" >/dev/null 2>&1 || error "Required tool not found: $dep"
    done
    log "All dependencies present"
}

# Wait for Kubernetes deployment
wait_for_deployment() {
    local namespace="$1"
    local deployment="$2"
    local timeout="${3:-300}"
    
    log "Waiting for deployment ${namespace}/${deployment} (timeout: ${timeout}s)"
    if ! kubectl rollout status deployment/"$deployment" \
        -n "$namespace" \
        --timeout="${timeout}s"; then
        error "Deployment ${deployment} did not become ready within ${timeout}s"
    fi
    log "Deployment ${deployment} is ready"
}

# Smoke test with retry
smoke_test() {
    local url="$1"
    local expected_code="${2:-200}"
    local max_attempts=10
    local wait_seconds=5
    
    for ((i=1; i<=max_attempts; i++)); do
        local code
        code=$(curl -sS -o /dev/null -w "%{http_code}" \
               --max-time 5 "$url" 2>/dev/null || echo "000")
        
        if [[ "$code" == "$expected_code" ]]; then
            log "Smoke test passed: $url returned $code"
            return 0
        fi
        warn "Attempt $i/$max_attempts: got $code, expected $expected_code. Retrying..."
        sleep "$wait_seconds"
    done
    error "Smoke test failed: $url did not return $expected_code after $max_attempts attempts"
}

# Rollback on failure
rollback() {
    local release="$1"
    local namespace="$2"
    warn "Rolling back Helm release ${release} in ${namespace}"
    helm rollback "$release" 0 -n "$namespace" --wait
    log "Rollback complete"
}

# Trap for cleanup
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Script failed with exit code $exit_code. Check $LOG_FILE"
    fi
}
trap cleanup EXIT

# Main
main() {
    local environment="${1:?Usage: $0 <environment> <version>}"
    local version="${2:?Usage: $0 <environment> <version>}"
    
    check_deps
    log "Starting deployment: env=${environment} version=${version}"
    
    helm upgrade --install "myapp-${environment}" ./charts/myapp \
        --namespace "myapp-${environment}" \
        --create-namespace \
        --set image.tag="$version" \
        --set environment="$environment" \
        --values "./environments/${environment}/values.yaml" \
        --atomic \
        --timeout 5m
    
    wait_for_deployment "myapp-${environment}" "myapp" 300
    smoke_test "https://myapp-${environment}.example.com/health"
    
    log "Deployment successful: ${environment} running ${version}"
}

main "$@"
```

---

## 3.6 Memory Optimisation & Performance Tuning

### Python Memory Profiling
```python
# Use generators instead of lists for large datasets
def stream_records(db_cursor, batch_size=1000):
    """Memory-efficient record streaming — never loads all at once"""
    offset = 0
    while True:
        db_cursor.execute(
            "SELECT * FROM events WHERE processed=false ORDER BY id LIMIT %s OFFSET %s",
            (batch_size, offset)
        )
        batch = db_cursor.fetchall()
        if not batch:
            break
        yield from batch
        offset += batch_size

# Profile memory usage
from memory_profiler import profile

@profile
def process_large_dataset(records):
    # Memory profiler annotates each line with memory delta
    ...

# Use __slots__ for high-frequency objects
class LogEvent:
    __slots__ = ['timestamp', 'level', 'message', 'service']
    
    def __init__(self, timestamp, level, message, service):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.service = service
    # __slots__ reduces memory 40-50% vs __dict__ for thousands of instances
```

### Node.js Performance
```javascript
// Avoid blocking the event loop — offload CPU work to worker threads
const { Worker, isMainThread, workerData, parentPort } = require('worker_threads');

if (isMainThread) {
    function processInWorker(data) {
        return new Promise((resolve, reject) => {
            const worker = new Worker(__filename, { workerData: data });
            worker.on('message', resolve);
            worker.on('error', reject);
        });
    }
    // Main thread stays responsive to HTTP requests
} else {
    // Heavy CPU computation in worker thread
    const result = heavyDataTransformation(workerData);
    parentPort.postMessage(result);
}

// Stream large API responses instead of buffering
app.get('/export/large-dataset', async (req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.write('[');
    
    const stream = db.query('SELECT * FROM large_table').stream();
    let first = true;
    
    stream.on('data', (row) => {
        if (!first) res.write(',');
        res.write(JSON.stringify(row));
        first = false;
    });
    
    stream.on('end', () => {
        res.write(']');
        res.end();
    });
});
```
