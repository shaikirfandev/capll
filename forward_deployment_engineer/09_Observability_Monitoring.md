# Section 09 — Observability & Monitoring

## 9.1 The Three Pillars of Observability

```
Observability = Metrics + Logs + Traces

Metrics: Numeric measurements over time
  "CPU usage is 87%, latency p99 is 450ms, error rate is 0.3%"
  
Logs: Structured event records
  "2024-11-15T10:23:45Z WARN deployment dep-123 failed: connection timeout"
  
Traces: Request path across distributed services
  User request → API Gateway (12ms) → Auth Service (5ms) → DB query (280ms)
  
A system is observable if you can ask ANY question about its behaviour
using only external signals — without deploying new code.
```

---

## 9.2 Prometheus — Metrics Collection

Prometheus is the most common monitoring system in cloud-native environments.

### Instrument Your Application
```typescript
// Node.js application — expose /metrics for Prometheus scraping
import { Registry, Counter, Histogram, Gauge } from "prom-client";

const register = new Registry();

// Counter — monotonically increasing (requests, errors, deployments)
const httpRequests = new Counter({
    name: "http_requests_total",
    help: "Total HTTP requests",
    labelNames: ["method", "path", "status_code"],
    registers: [register],
});

// Histogram — observe distributions (latency, payload sizes)
const httpDuration = new Histogram({
    name: "http_request_duration_seconds",
    help: "HTTP request duration in seconds",
    labelNames: ["method", "path", "status_code"],
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
    registers: [register],
});

// Gauge — current value (active connections, queue depth)
const activeDeployments = new Gauge({
    name: "active_deployments",
    help: "Number of currently running deployments",
    labelNames: ["environment"],
    registers: [register],
});

// Middleware to instrument all routes
function metricsMiddleware(req: Request, res: Response, next: NextFunction) {
    const end = httpDuration.startTimer({
        method: req.method,
        path:   req.route?.path ?? req.path,
    });
    
    res.on("finish", () => {
        httpRequests.inc({
            method:      req.method,
            path:        req.route?.path ?? req.path,
            status_code: String(res.statusCode),
        });
        end({ status_code: String(res.statusCode) });
    });
    
    next();
}

// Expose metrics endpoint
app.get("/metrics", async (req, res) => {
    res.set("Content-Type", register.contentType);
    res.end(await register.metrics());
});
```

### Prometheus Query Language (PromQL)
```promql
# --- REQUEST RATE ---
# Requests per second over 5-minute window
rate(http_requests_total[5m])

# Error rate (5xx responses as % of total)
rate(http_requests_total{status_code=~"5.."}[5m])
/
rate(http_requests_total[5m])
* 100

# --- LATENCY ---
# p50, p95, p99 latency
histogram_quantile(0.99, 
  rate(http_request_duration_seconds_bucket[5m])
)

# Slow endpoints (average latency > 500ms)
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])
> 0.5

# --- RESOURCE ---
# CPU usage per pod
rate(container_cpu_usage_seconds_total{namespace="myapp-production"}[5m]) * 100

# Memory usage %
container_memory_working_set_bytes{namespace="myapp-production"}
/
container_spec_memory_limit_bytes{namespace="myapp-production"}
* 100

# --- AVAILABILITY ---
# Uptime % (no 5xx errors in last 30 days)
1 - (
  sum(rate(http_requests_total{status_code=~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
)
```

---

## 9.3 Grafana — Dashboards

### Dashboard Design Principles for FDEs

```
Dashboard Hierarchy:
  Level 1 — Executive Dashboard (5 metrics on one screen)
    - Uptime / Availability
    - Request rate
    - Error rate
    - p99 latency
    - Active deployments
    
  Level 2 — Service Overview Dashboard
    - Per-endpoint latency
    - Error breakdown by type
    - Database connection pool usage
    - Memory / CPU
    - Active alerts
    
  Level 3 — Debug Dashboard
    - Per-pod resource usage
    - Database query performance
    - External API call latency
    - Queue depths
    - Cache hit/miss rates
```

```json
// Grafana dashboard panel — key configuration for FDE
{
  "title": "HTTP Error Rate",
  "type": "stat",
  "targets": [{
    "expr": "sum(rate(http_requests_total{status_code=~\"5..\",namespace=\"myapp-production\"}[5m])) / sum(rate(http_requests_total{namespace=\"myapp-production\"}[5m])) * 100",
    "legendFormat": "Error Rate %"
  }],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "thresholds": {
        "steps": [
          { "value": 0,   "color": "green" },
          { "value": 0.1, "color": "yellow" },
          { "value": 1.0, "color": "red" }
        ]
      }
    }
  }
}
```

---

## 9.4 Alerting Rules

```yaml
# Prometheus alert rules — production-grade
groups:
  - name: slo_alerts
    rules:
      # Error budget burn rate
      - alert: HighErrorRate
        expr: |
          (
            rate(http_requests_total{status_code=~"5..",namespace="myapp-production"}[5m])
            /
            rate(http_requests_total{namespace="myapp-production"}[5m])
          ) > 0.01
        for: 5m
        labels:
          severity: critical
          team:     platform
        annotations:
          summary:     "High error rate on {{ $labels.namespace }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 1%)"
          runbook:      "https://runbooks.internal/high-error-rate"

      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.99,
            rate(http_request_duration_seconds_bucket{namespace="myapp-production"}[5m])
          ) > 2.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary:     "High p99 latency: {{ $value }}s"
          description: "p99 latency exceeds 2 seconds"
          runbook:      "https://runbooks.internal/high-latency"

      - alert: PodCrashLooping
        expr: |
          rate(kube_pod_container_status_restarts_total{namespace="myapp-production"}[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod {{ $labels.pod }} is crash-looping"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.15
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 15% on {{ $labels.instance }}"
```

---

## 9.5 Distributed Tracing with OpenTelemetry

OpenTelemetry is the industry standard (adopted by Datadog, Honeycomb, Jaeger, Tempo).

```typescript
// Setup OpenTelemetry in Node.js
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";

const sdk = new NodeSDK({
    serviceName:    "deployment-service",
    traceExporter:  new OTLPTraceExporter({
        url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
    }),
    instrumentations: [
        getNodeAutoInstrumentations({
            "@opentelemetry/instrumentation-http":       { enabled: true },
            "@opentelemetry/instrumentation-express":    { enabled: true },
            "@opentelemetry/instrumentation-pg":         { enabled: true },
            "@opentelemetry/instrumentation-ioredis":    { enabled: true },
        }),
    ],
});
sdk.start();

// Manual spans for business operations
import { trace, context, SpanStatusCode } from "@opentelemetry/api";
const tracer = trace.getTracer("deployment-service");

async function deployApplication(config: DeploymentConfig): Promise<Deployment> {
    const span = tracer.startSpan("deploy_application", {
        attributes: {
            "deployment.environment": config.environment,
            "deployment.version":     config.version,
            "deployment.customer":    config.customerId,
        },
    });
    
    return context.with(trace.setSpan(context.active(), span), async () => {
        try {
            const result = await performDeployment(config);
            span.setStatus({ code: SpanStatusCode.OK });
            return result;
        } catch (err) {
            span.setStatus({ code: SpanStatusCode.ERROR, message: err.message });
            span.recordException(err);
            throw err;
        } finally {
            span.end();
        }
    });
}
```

### Trace Analysis Workflow
```
When investigating a slow request:

1. Find the trace by request_id in Jaeger/Tempo/Datadog
2. Look at the waterfall chart:
   ┌─────────────────────────────────────────────────────┐
   │ API Gateway                              1,245ms     │
   │  ├─ Auth middleware                       12ms       │
   │  ├─ Request validation                    3ms        │
   │  └─ deployment-service                   1,228ms     │
   │       ├─ redis GET (cache check)          2ms        │
   │       ├─ postgres query                   850ms ◄── SLOW
   │       └─ external API call               370ms ◄── SLOW
   └─────────────────────────────────────────────────────┘
   
3. Postgres query = 850ms → Go to DB dashboard, find the query, EXPLAIN ANALYZE
4. External API = 370ms → Is this third-party? What's their SLA?
```

---

## 9.6 Log Management (ELK Stack)

```
ELK Architecture:
  Applications → Filebeat (log shipper) → Logstash (parse/transform) → Elasticsearch → Kibana
  
Fluent Bit variant (lighter weight, preferred for Kubernetes):
  Pod logs → Fluent Bit DaemonSet → Elasticsearch/S3 → Kibana/OpenSearch Dashboards
```

### Structured Logging (Critical for searchability)
```typescript
// Use structured JSON logging — never use console.log in production
import winston from "winston";

const logger = winston.createLogger({
    level: process.env.LOG_LEVEL ?? "info",
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: {
        service: "deployment-service",
        version: process.env.APP_VERSION,
    },
    transports: [
        new winston.transports.Console(),
    ],
});

// Every log entry should have correlation IDs
function requestLogger(req: Request, res: Response, next: NextFunction) {
    const requestId = req.headers["x-request-id"] ?? crypto.randomUUID();
    req.log = logger.child({
        request_id: requestId,
        user_id:    req.user?.id,
        tenant_id:  req.user?.tenantId,
    });
    res.setHeader("X-Request-Id", requestId);
    next();
}

// Log meaningful events
async function handleDeployment(req: Request, res: Response) {
    req.log.info("deployment_started", {
        deployment_id: req.params.id,
        environment:   req.body.environment,
        version:       req.body.version,
    });
    
    try {
        const result = await deployService.run(req.params.id);
        req.log.info("deployment_completed", {
            deployment_id: req.params.id,
            duration_ms:   result.durationMs,
        });
        res.json(result);
    } catch (err) {
        req.log.error("deployment_failed", {
            deployment_id: req.params.id,
            error:         err.message,
            stack:         err.stack,
        });
        res.status(500).json({ error: "Deployment failed" });
    }
}
```

---

## 9.7 SLO/SLA/SLI Definitions

Every FDE must define and measure service levels before signing a contract with a customer.

```
SLI (Service Level Indicator):
  A measurement of service behaviour.
  Example: "% of requests returning HTTP 200 within 500ms"

SLO (Service Level Objective):
  A target for an SLI.
  Example: "99.9% of requests return HTTP 200 within 500ms, measured monthly"

SLA (Service Level Agreement):
  A contract with financial consequences for missing an SLO.
  Example: "If uptime < 99.9% in any calendar month, customer receives 10% credit"

Error Budget:
  SLO = 99.9% → Error budget = 0.1% of time = 43.8 minutes/month
  If you've used 40 of 43.8 minutes → freeze risky deployments
```

| SLO Level | Monthly Downtime | Use Case |
|-----------|----------------|----------|
| 99% | 7.3 hours | Internal tools |
| 99.5% | 3.65 hours | Business apps |
| 99.9% | 43.8 minutes | Standard SaaS |
| 99.95% | 21.9 minutes | Premium SaaS |
| 99.99% | 4.4 minutes | Critical financial |
| 99.999% | 26 seconds | Payments, emergency services |

---

## 9.8 Incident Response

```
Incident Severity Levels:

SEV-1 (Critical):
  - Production completely down
  - Data loss occurring
  - Security breach active
  Action: Page on-call immediately, incident bridge in 5 min
  
SEV-2 (High):
  - Partial production outage
  - Degraded performance affecting >20% users
  Action: Alert on-call, bridge within 15 min
  
SEV-3 (Medium):
  - Minor degradation, workaround exists
  - Single customer affected
  Action: Notify team, respond within 2 hours
  
SEV-4 (Low):
  - Cosmetic issue, no impact
  Action: Create ticket, next business day

Incident Response Playbook:
  1. DETECT:    Alert fires / customer reports issue
  2. ASSESS:    Determine severity
  3. MOBILISE:  Create incident channel (#incident-2024-1115-api-down)
  4. MITIGATE:  Restore service (rollback, scale up, failover)
  5. RESOLVE:   Confirm service restored
  6. DOCUMENT:  Postmortem within 48 hours

Communication template (every 15 minutes):
  "[11:32] Update: We are investigating elevated error rates on the
   Deployment API (affecting ~30% of requests). Root cause suspected
   to be database connection pool exhaustion. ETA for resolution: 15 minutes.
   Mitigation: increased pool size deployed to 2/3 regions."
```
