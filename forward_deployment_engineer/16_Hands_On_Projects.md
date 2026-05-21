# Section 16 — Hands-On Projects

## Project 1: Dockerised MERN Stack with Nginx

**Goal:** Deploy a full-stack application with proper containerisation, environment separation, and production config.

**Stack:** MongoDB, Express, React, Node.js, Nginx, Docker Compose

```
Project Structure:
mern-docker/
├── frontend/           ← React app
├── backend/            ← Express API
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

**Key Skills Practised:**
- Multi-stage Dockerfiles
- Nginx as reverse proxy for React + API
- MongoDB with volume persistence
- Environment variable management
- Health checks

```yaml
# docker-compose.prod.yml
version: "3.9"
services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on: [frontend, backend]

  frontend:
    build: { context: ./frontend, target: production }
    environment: [NODE_ENV=production]

  backend:
    build: { context: ./backend, target: production }
    environment:
      - NODE_ENV=production
      - MONGO_URI=mongodb://mongo:27017/myapp
    depends_on:
      mongo:
        condition: service_healthy

  mongo:
    image: mongo:7
    volumes: [mongo_data:/data/db]
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      retries: 5

volumes:
  mongo_data:
```

**Completion Checklist:**
```
□ React app serves correctly at /
□ API accessible at /api/ via nginx proxy
□ MongoDB data persists across container restarts
□ docker-compose up -d starts all services
□ Health checks all pass
□ Production build uses minified assets
```

---

## Project 2: Kubernetes Production Cluster

**Goal:** Deploy a stateful application to Kubernetes with full production-grade configuration.

**Stack:** Kubernetes (minikube or k3s locally), PostgreSQL (Helm), Redis, Node.js app

```bash
# Local K8s cluster setup
k3d cluster create myapp \
    --port "8080:80@loadbalancer" \
    --agents 2

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager --create-namespace \
    --set installCRDs=true

# Install PostgreSQL via Helm
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgres bitnami/postgresql \
    --namespace myapp --create-namespace \
    --set auth.postgresPassword=<from-secrets> \
    --set primary.persistence.size=10Gi

# Deploy application
kubectl apply -f manifests/
kubectl rollout status deployment/myapp -n myapp
```

**Completion Checklist:**
```
□ Application accessible through ingress
□ Database persistent across pod restarts
□ HPA scales pods under load
□ Rolling update with zero downtime
□ Rollback with helm rollback works
□ Resource limits set on all containers
□ Liveness + readiness probes configured
□ Secrets stored in Kubernetes Secrets (not ConfigMaps)
```

---

## Project 3: CI/CD Pipeline with GitHub Actions

**Goal:** Build a complete CI/CD pipeline from commit to production.

```yaml
# .github/workflows/main.yml
name: CI/CD Pipeline
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm }
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --coverage --forceExit
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/test_db

  build-push:
    needs: test
    permissions: { id-token: write, contents: read }
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      - uses: aws-actions/amazon-ecr-login@v2
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ secrets.ECR_REGISTRY }}/myapp:${{ github.sha }}

  deploy:
    needs: build-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: |
          helm upgrade myapp ./charts/myapp \
            --set image.tag=${{ github.sha }} \
            --atomic --timeout 5m
```

**Completion Checklist:**
```
□ PR builds run tests automatically
□ Main branch pushes build + push Docker image
□ Tagged releases deploy to production
□ Broken tests block the pipeline
□ Secrets managed via GitHub Secrets (not in code)
□ OIDC to AWS (no long-lived access keys)
```

---

## Project 4: Monitoring Dashboard

**Goal:** Set up Prometheus + Grafana with custom application metrics.

```bash
# Deploy monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace \
    --values monitoring/values.yaml

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
# Default: admin / prom-operator
```

```yaml
# monitoring/values.yaml
grafana:
  adminPassword: "${GRAFANA_PASSWORD}"
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: default
          folder: ""
          type: file
          options:
            path: /var/lib/grafana/dashboards/default
  dashboards:
    default:
      myapp:
        json: |
          { ... dashboard JSON ... }

prometheus:
  prometheusSpec:
    additionalScrapeConfigs:
      - job_name: myapp
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: myapp
```

**Completion Checklist:**
```
□ Grafana accessible with dashboards
□ Application metrics scraped by Prometheus
□ Alert rules configured (error rate, latency)
□ PagerDuty/Slack alertmanager webhook working
□ Dashboard shows: RPS, latency p99, error rate, CPU, memory
```

---

## Project 5: SaaS Backend API

**Goal:** Build a production-grade multi-tenant REST API.

**Features:**
- JWT authentication + refresh tokens
- RBAC (viewer, editor, admin roles)
- Multi-tenancy (tenant isolation by tenant_id)
- Rate limiting (per tenant, per user)
- Paginated list endpoints
- Comprehensive error handling
- OpenAPI documentation
- Integration test suite

```typescript
// Multi-tenant middleware — inject tenant context
function tenantMiddleware(req: Request, res: Response, next: NextFunction) {
    const tenant = req.user?.tenantId;
    if (!tenant) return res.status(401).json({ error: "Tenant not identified" });
    
    // All subsequent DB queries filtered by tenant
    req.db = db.withTenant(tenant);
    next();
}

// Paginated endpoint with cursor
app.get("/api/v1/deployments", requireAuth, tenantMiddleware, async (req, res) => {
    const { limit = 20, cursor, status, environment } = req.query;
    
    const result = await req.db.deployments.findMany({
        where:  { status, environmentId: environment },
        take:   Math.min(Number(limit), 100),
        cursor: cursor ? { id: cursor as string } : undefined,
        skip:   cursor ? 1 : 0,
        orderBy: { createdAt: "desc" },
    });
    
    res.json({
        data:       result,
        nextCursor: result.length === Number(limit) ? result.at(-1)?.id : null,
    });
});
```

**Completion Checklist:**
```
□ JWT auth working (login, refresh, logout)
□ RBAC enforced on all routes
□ Multi-tenant data isolation verified (User A cannot see User B's data)
□ Rate limiting active
□ All endpoints paginated
□ OpenAPI spec at /docs
□ Integration test suite passing
□ Load test: 100 concurrent users, p99 < 200ms
```

---

## Project 6: Multi-Service Microservices System

**Goal:** Build 3 communicating microservices with async messaging.

**Services:**
- `auth-service`: JWT issuance, user management
- `deployment-service`: Core deployment logic
- `notification-service`: Async notifications (Slack, email)

**Communication:**
- auth-service ↔ deployment-service: REST (synchronous auth checks)
- deployment-service → notification-service: Kafka events (async)

```yaml
# docker-compose.yml for local development
services:
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_NODE_ID: 1
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092

  auth-service:
    build: ./services/auth
    ports: ["3001:3001"]

  deployment-service:
    build: ./services/deployment
    ports: ["3002:3002"]
    environment:
      AUTH_SERVICE_URL: http://auth-service:3001
      KAFKA_BROKERS: kafka:9092

  notification-service:
    build: ./services/notification
    environment:
      KAFKA_BROKERS: kafka:9092
      SLACK_WEBHOOK: ${SLACK_WEBHOOK}
```

---

## Project 7: Real-Time Chat with WebSockets

**Goal:** Build a real-time collaboration tool (live deployment logs viewer).

```typescript
// Server: broadcast log lines to subscribers
io.on("connection", (socket) => {
    socket.on("subscribe:logs", async (deploymentId: string) => {
        if (!await canAccessDeployment(socket.data.user, deploymentId)) {
            socket.emit("error", "Access denied");
            return;
        }
        socket.join(`logs:${deploymentId}`);
        
        // Send last 100 lines on subscribe
        const history = await getRecentLogs(deploymentId, 100);
        socket.emit("logs:history", history);
    });
});

// Worker publishes log lines as they arrive
deploymentWorker.on("log", (deploymentId: string, line: string) => {
    io.to(`logs:${deploymentId}`).emit("logs:line", { line, timestamp: Date.now() });
});
```

---

## Project 8: AI-Powered API

**Goal:** Build a RAG-enabled API that answers questions about a document corpus.

```
Features:
  - Document ingestion endpoint (PDF, Markdown)
  - Chunking + embedding pipeline
  - Semantic search endpoint
  - Q&A endpoint (RAG)
  - Streaming responses
  - Conversation history
  - Citation of source documents

Stack: FastAPI + LangChain + pgvector + OpenAI
```

---

## Project 9: Log Aggregation Pipeline

**Goal:** Build a complete observability stack for a multi-service application.

```
Pipeline:
  App logs (JSON) → Fluent Bit → Elasticsearch → Kibana
  App metrics → Prometheus → Grafana
  App traces → OTEL Collector → Tempo → Grafana

Components to deploy:
  1. Fluent Bit DaemonSet on Kubernetes
  2. Elasticsearch 8.x (single node for local)
  3. Kibana with saved searches + dashboards
  4. OpenTelemetry Collector
  5. Grafana Tempo for distributed traces
  6. Grafana with all datasources configured
```

**Completion Checklist:**
```
□ Application logs appear in Kibana within 10 seconds
□ Kibana dashboard shows error rate from logs
□ Grafana dashboard shows application metrics
□ Distributed trace visible end-to-end (API → DB)
□ Alert rule: error rate > 1% sends Slack notification
□ All infrastructure deployed via docker-compose or Helm
```
