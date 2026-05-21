# Section 08 — DevOps & Deployment Engineering

## 8.1 Docker — Production Container Management

### Dockerfile Best Practices
```dockerfile
# Production-grade Node.js Dockerfile

# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependency files first (cache layer)
COPY package*.json ./
RUN npm ci --only=production

# Copy source and build
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# Stage 2: Production image (minimal attack surface)
FROM node:20-alpine AS production

# Security: run as non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser  -u 1001 -S appuser -G appgroup

WORKDIR /app

# Copy only what's needed from builder
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/dist         ./dist

# Security: read-only filesystem (app writes to /tmp if needed)
USER appuser

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

ENTRYPOINT ["node", "dist/server.js"]
```

### Docker Compose for Local Development
```yaml
# docker-compose.yml — local development stack
version: "3.9"

services:
  app:
    build:
      context: .
      target: builder        # Use development stage
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DB_HOST=postgres
      - REDIS_HOST=redis
    env_file:
      - .env.local
    volumes:
      - ./src:/app/src:ro    # Live reload
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB:       myapp_dev
      POSTGRES_USER:     dev
      POSTGRES_PASSWORD: devpassword  # Local dev only — never in production
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev -d myapp_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  redis_data:
```

---

## 8.2 Kubernetes — Production Orchestration

### Kubernetes Architecture
```
Control Plane:
  API Server    → Single entry point for all K8s operations
  etcd          → Cluster state database
  Scheduler     → Assigns pods to nodes
  Controller    → Ensures desired state matches actual state

Worker Nodes:
  kubelet       → Manages pods on the node
  kube-proxy    → Network proxy for services
  Container runtime (containerd/Docker)

Key objects:
  Pod           → Smallest deployable unit (1+ containers)
  Deployment    → Manages pod replicas and rollouts
  Service       → Stable network endpoint for pods
  ConfigMap     → Non-secret configuration
  Secret        → Sensitive configuration
  Ingress       → HTTP routing to services
  Namespace     → Logical cluster isolation
  HPA           → Horizontal Pod Autoscaler
  PVC/PV        → Persistent storage
```

### Production Kubernetes Manifests
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: myapp-production
  labels:
    app: myapp
    version: "2.1.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0     # Never take a pod down before new one is ready
      maxSurge:       1     # Create one extra pod during update
  template:
    metadata:
      labels:
        app: myapp
        version: "2.1.0"
    spec:
      serviceAccountName: myapp-sa
      
      # Security context — run as non-root
      securityContext:
        runAsNonRoot: true
        runAsUser:    1001
        fsGroup:      1001
        seccompProfile:
          type: RuntimeDefault

      # Graceful termination
      terminationGracePeriodSeconds: 60

      containers:
        - name: myapp
          image: 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:2.1.0
          imagePullPolicy: Always
          ports:
            - containerPort: 3000
          
          env:
            - name: APP_ENV
              value: production
            - name: DB_HOST
              valueFrom:
                configMapKeyRef:
                  name: myapp-config
                  key: db_host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: myapp-secrets
                  key: db_password
          
          # Resource limits — prevents noisy-neighbour problems
          resources:
            requests:
              cpu:    "250m"
              memory: "256Mi"
            limits:
              cpu:    "1000m"
              memory: "512Mi"
          
          # Probes — critical for zero-downtime deployments
          startupProbe:
            httpGet:
              path: /health
              port: 3000
            failureThreshold: 30    # Allow 30 × 5s = 150s to start
            periodSeconds: 5
          
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 15
            failureThreshold: 3
          
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
            periodSeconds: 5
            failureThreshold: 2     # Remove from load balancer after 10s
          
          # Security context at container level
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem:   true
            capabilities:
              drop: ["ALL"]
          
          volumeMounts:
            - name: tmp
              mountPath: /tmp   # Writable /tmp even with readOnlyRootFilesystem
      
      volumes:
        - name: tmp
          emptyDir: {}
      
      # Pod anti-affinity — spread pods across nodes
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                topologyKey: kubernetes.io/hostname
                labelSelector:
                  matchLabels:
                    app: myapp
```

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp
  namespace: myapp-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type:               Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type:               Utilization
          averageUtilization: 80
```

---

## 8.3 Helm — Kubernetes Package Management

```
Helm concepts:
  Chart     → Package of Kubernetes manifests + templates
  Release   → Deployed instance of a chart
  Values    → Configuration injected into templates
  Repository → Collection of charts

Chart structure:
  mychart/
  ├── Chart.yaml          # Chart metadata
  ├── values.yaml         # Default values
  ├── values/
  │   ├── staging.yaml
  │   └── production.yaml
  └── templates/
      ├── deployment.yaml
      ├── service.yaml
      ├── ingress.yaml
      ├── configmap.yaml
      ├── secret.yaml
      └── hpa.yaml
```

```bash
# Helm operations
helm repo add myrepo https://charts.example.com
helm repo update

# Install
helm install myapp myrepo/myapp \
    --namespace myapp-production \
    --create-namespace \
    --values values/production.yaml \
    --set image.tag="2.1.0" \
    --set replicas=3

# Upgrade
helm upgrade myapp myrepo/myapp \
    --namespace myapp-production \
    --values values/production.yaml \
    --set image.tag="2.2.0" \
    --atomic \         # Roll back automatically if upgrade fails
    --timeout 5m

# Rollback
helm rollback myapp 1 --namespace myapp-production

# Inspect
helm status   myapp -n myapp-production
helm history  myapp -n myapp-production
helm get values myapp -n myapp-production
```

---

## 8.4 CI/CD Pipelines

### GitHub Actions — Production Pipeline
```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]
    tags:
      - "v*.*.*"

permissions:
  contents: read
  id-token: write    # For OIDC to AWS

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm run test:unit -- --coverage
      - uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials (OIDC — no long-lived keys)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: us-east-1
      
      - name: Login to ECR
        id: ecr_login
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ steps.ecr_login.outputs.registry }}/myapp:${{ github.sha }}
            ${{ steps.ecr_login.outputs.registry }}/myapp:latest
          cache-from: type=gha
          cache-to:   type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
          aws-region: us-east-1
      
      - name: Deploy to staging
        run: |
          aws ecs update-service \
            --cluster myapp-staging \
            --service myapp \
            --force-new-deployment
          
          aws ecs wait services-stable \
            --cluster myapp-staging \
            --services myapp

      - name: Run smoke tests
        run: |
          curl -f https://staging.myapp.com/health || exit 1

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.com
    # Manual approval gate for production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to production
        run: |
          helm upgrade myapp ./charts/myapp \
            --namespace myapp-production \
            --set image.tag="${{ github.sha }}" \
            --atomic \
            --timeout 10m
```

---

## 8.5 Deployment Strategies

### Blue-Green Deployment
```
Traffic: 100% → Blue (current)

Step 1: Deploy new version to Green (no traffic)
  Blue: v1.0 ← 100% traffic
  Green: v2.0 ← 0% traffic

Step 2: Run smoke tests on Green
  curl https://green.myapp.com/health

Step 3: Switch traffic
  Blue: v1.0 ← 0% traffic
  Green: v2.0 ← 100% traffic

Step 4: Monitor Green for 15 minutes
  If issue: switch back to Blue instantly

Step 5: Terminate Blue (or keep for quick rollback)

Pros: Instant rollback, zero downtime
Cons: Double infrastructure cost during transition
Use: High-risk releases, database migrations
```

### Canary Deployment
```
Step 1: Deploy v2.0 to 1 of 10 pods (10% traffic)
  v1.0: 9 pods ← 90% traffic
  v2.0: 1 pod  ←  10% traffic

Step 2: Monitor error rates, latency for 30 minutes
  Baseline: v1.0 error rate = 0.1%
  Canary:   v2.0 error rate = 0.1%  ← good, continue

Step 3: Increase canary to 50%
  v1.0: 5 pods ← 50%
  v2.0: 5 pods ← 50%

Step 4: Monitor, then promote to 100%

Pros: Gradual exposure, data-driven rollout
Cons: Runs two versions simultaneously, complex routing
Use: Standard production releases with A/B capability

Kubernetes + Nginx Ingress canary:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"   # 10% traffic
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp-v2
                port:
                  number: 80
```

### Rolling Update
```
10 pods of v1.0 → rolling update to v2.0

t=0:  [v1,v1,v1,v1,v1,v1,v1,v1,v1,v1]  (10 × v1.0)
t=1:  [v2,v1,v1,v1,v1,v1,v1,v1,v1,v1]  (1 new pod ready, 1 old terminated)
t=2:  [v2,v2,v1,v1,v1,v1,v1,v1,v1,v1]
...
t=10: [v2,v2,v2,v2,v2,v2,v2,v2,v2,v2]  (all v2.0)

Rollback: kubectl rollout undo deployment/myapp
Kubernetes ensures maxUnavailable=0 → zero downtime

Pros: Simple, built-in to Kubernetes
Cons: Two versions live simultaneously, harder rollback
Use: Standard daily releases
```

---

## 8.6 GitOps with ArgoCD

ArgoCD is the standard GitOps tool in Kubernetes environments (Palantir, Datadog, Stripe-scale deployments).

```yaml
# ArgoCD Application definition
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-production
  namespace: argocd
spec:
  project: production
  
  source:
    repoURL: https://github.com/acme/myapp-helm-charts
    targetRevision: HEAD
    path: charts/myapp
    helm:
      valueFiles:
        - values/production.yaml
  
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp-production
  
  syncPolicy:
    automated:
      prune:    true    # Delete resources removed from Git
      selfHeal: true    # Revert manual kubectl changes
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

**GitOps workflow:**
```
Developer pushes code → CI builds image + updates Helm chart version in Git
→ ArgoCD detects Git diff → ArgoCD applies to cluster
→ Cluster state matches Git state always

"If it's not in Git, it doesn't exist in production"
```
