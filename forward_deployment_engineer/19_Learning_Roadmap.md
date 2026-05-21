# Section 19 — Learning Roadmap

## 19.1 Assessment: Where Are You Now?

Before starting the roadmap, honestly assess your current level:

```
□ Beginner (< 2 years):     Can code, but haven't deployed production systems
□ Intermediate (2-4 years): Deployed apps, basic Docker/K8s, some cloud
□ Advanced (4-7 years):     Led deployments, designed architectures, handled incidents
□ Senior (7+ years):        Multiple production environments, customer-facing work
```

This roadmap is calibrated for the **Intermediate → FDE-Ready** transition (someone with 2–5 years of software development experience).

---

## 19.2 30-Day Kickstart Plan

**Goal:** Cover fundamentals, build first working deployment

| Week | Focus | Deliverable |
|------|-------|-------------|
| 1 | Linux, Docker, Bash | Dockerise an existing app; write 5 bash scripts |
| 2 | Kubernetes fundamentals | Deploy app to local K8s (k3d); configure HPA |
| 3 | Cloud foundations | Provision AWS VPC + ECS service via Terraform |
| 4 | CI/CD | GitHub Actions pipeline: test → build → deploy |

### Week 1 Daily Schedule
```
Day 1:  Linux admin — process management, logs, networking (Section 06)
Day 2:  Dockerfile best practices — write and optimise a Dockerfile
Day 3:  Docker Compose — multi-service local stack
Day 4:  Bash scripting — write deployment + health-check script
Day 5:  Nginx config — reverse proxy + TLS + rate limiting
Day 6:  Project: Dockerise a Node.js/Python app with Nginx + DB
Day 7:  Review + documentation practice
```

### Week 2 Daily Schedule
```
Day 8:  K8s concepts — pods, deployments, services, ingress
Day 9:  Write deployment.yaml, service.yaml, configmap.yaml
Day 10: Deploy to k3d local cluster
Day 11: Add liveness/readiness probes + resource limits
Day 12: Configure HPA + test scaling with locust
Day 13: Helm — convert manifests to Helm chart
Day 14: Project: Full app on local K8s with HPA
```

### Week 3 Daily Schedule
```
Day 15: AWS — VPC, subnets, security groups, IAM roles
Day 16: Terraform basics — init, plan, apply, state
Day 17: Terraform VPC module + ECS task definition
Day 18: RDS PostgreSQL + connection pooling
Day 19: ALB + Route 53 + ACM certificate
Day 20: Full Terraform deploy: VPC + ECS + RDS + ALB
Day 21: Review + cost analysis
```

### Week 4 Daily Schedule
```
Day 22: GitHub Actions — CI pipeline (lint, test, build)
Day 23: OIDC to AWS — no long-lived access keys
Day 24: Docker image build + ECR push in CI
Day 25: ECS service deployment in CD
Day 26: Rollback strategy + testing
Day 27: Slack notifications + deployment status badges
Day 28: Add staging → production gates (environment protection rules)
Day 29: Full end-to-end test: push code → deploys to staging → promote to prod
Day 30: Retrospective + documentation
```

---

## 19.3 90-Day FDE Foundation Plan

**Goal:** Production-ready skills across all FDE domains

```
MONTH 1 (Days 1-30): Infrastructure & Deployment
  ✓ Linux, Docker, K8s, Terraform, CI/CD (as above)

MONTH 2 (Days 31-60): Production Engineering
  Days 31-35:  PostgreSQL — schema, indexes, query optimisation, replication
  Days 36-40:  Redis — caching, rate limiting, Pub/Sub, distributed locks
  Days 41-45:  Observability — Prometheus, Grafana, Alertmanager, alerting rules
  Days 46-50:  Distributed tracing — OpenTelemetry, Jaeger/Tempo
  Days 51-55:  Security — OWASP Top 10, JWT, RBAC, secrets management
  Days 56-60:  Production incident simulation — break things and fix them

MONTH 3 (Days 61-90): Enterprise & Customer Skills
  Days 61-65:  System design practice (3 designs/week)
  Days 66-70:  API design — REST, GraphQL, gRPC, WebSockets
  Days 71-75:  Kafka + event-driven architecture project
  Days 76-80:  Customer deployment simulation (full 5-phase engagement)
  Days 81-85:  Interview preparation (technical + behavioural)
  Days 86-90:  Portfolio project completion + documentation
```

---

## 19.4 6-Month Expert Trajectory

| Month | Domain | Milestone |
|-------|--------|-----------|
| 1 | Infrastructure | Deploy multi-region app via Terraform |
| 2 | Production Ops | Build full observability stack + run RCA on simulated incident |
| 3 | Enterprise | Complete simulated customer engagement end-to-end |
| 4 | Distributed Systems | Build Kafka-based event pipeline + write system design doc |
| 5 | Security | Pass OWASP checklist on existing project; implement mTLS |
| 6 | AI/Modern | Deploy LLM inference with RAG + monitoring |

### Month-by-Month Projects
```
Month 1 → Deploy: Multi-service app on EKS with Terraform + GitHub Actions
  
Month 2 → Observe: Full Prometheus + Grafana + Alertmanager stack
           Simulate incidents: OOMKill, connection pool saturation, DB lock
  
Month 3 → Engage: Write a technical discovery doc for a fictional customer.
           Design architecture. Produce Helm chart. Deploy to staging.
  
Month 4 → Event-Driven: Customer notification system using Kafka.
           Producer: deployment service. Consumers: Slack, email, billing.
  
Month 5 → Security audit: Run trivy, OWASP ZAP, checkov on existing projects.
           Fix all HIGH/CRITICAL findings. Document security posture.
  
Month 6 → AI deployment: vLLM on GPU Kubernetes + RAG system + observability.
```

---

## 19.5 1-Year Mastery Path

```
QUARTER 1 (Days 1-90):   Technical foundation (sections 2-12)
QUARTER 2 (Days 91-180): Enterprise skills + customer-facing (sections 13-16)
QUARTER 3 (Days 181-270): Interview + portfolio + real projects
QUARTER 4 (Days 271-365): Land FDE role + first 90 days on the job

YEAR-END SKILLS CHECKLIST:
  Infrastructure:
    □ Terraform for multi-region AWS infrastructure (VPC, ECS, RDS, ALB)
    □ Kubernetes: deploy, scale, debug, upgrade production cluster
    □ Helm: create charts, manage releases, rollbacks
    □ Docker: multi-stage builds, layer optimisation, security hardening
  
  Programming:
    □ Python: automation scripts, FastAPI backend, data pipeline
    □ TypeScript: Node.js service with full test coverage
    □ Go: at least one production utility
    □ Bash: deployment scripts, log analysis, health checks
  
  Databases:
    □ PostgreSQL: schema design, query optimisation, replication
    □ Redis: caching, rate limiting, distributed lock
    □ Elasticsearch: indexing strategy, complex queries
  
  Observability:
    □ Prometheus + Grafana: custom dashboards, alert rules
    □ OpenTelemetry: instrumented multi-service app with traces
    □ ELK stack: structured logs, Kibana dashboards
  
  Security:
    □ Passed OWASP Top 10 review on a real project
    □ Configured SSO (SAML or OIDC) in a real deployment
    □ Secrets management with Vault or AWS Secrets Manager
  
  Enterprise:
    □ Completed 2+ customer deployment simulations end-to-end
    □ Written 3+ architecture decision records
    □ Written 2+ postmortems
    □ Presented architecture to simulated executive audience
  
  AI (optional, high-value):
    □ Deployed LLM inference endpoint (vLLM)
    □ Built RAG system with vector database
    □ Instrumented AI system with observability
```

---

## 19.6 Daily Practice Schedule

```
OPTIMAL DAILY SCHEDULE FOR FDE LEARNING (2 hours/day)

[30 min] Theory & Reading
  → One section from this handbook
  → One blog post from DORA, SRE Weekly, High Scalability

[60 min] Hands-On Practice
  → Build the current week's project
  → Break something and fix it
  → Run a simulated incident

[30 min] Documentation
  → Write a postmortem for what you broke
  → Write a runbook for how you fixed it
  → Document architecture decision you made

WEEKLY REVIEW (Sunday, 1 hour):
  → What did I deploy this week?
  → What broke and what did I learn?
  → What am I weakest at? → prioritise next week

MONTHLY PORTFOLIO REVIEW:
  → Add project to portfolio
  → Update skills checklist
  → Practice one system design question end-to-end
```

---

## 19.7 Mindset Milestones

```
Level 1 → "I can deploy this application"
  Milestone: Deploy a given Helm chart to a Kubernetes cluster.

Level 2 → "I can deploy this application reliably"
  Milestone: Zero-downtime deployment with rollback capability.

Level 3 → "I can deploy this application reliably at scale"
  Milestone: Multi-region, HA, autoscaling, full observability.

Level 4 → "I can deploy any application reliably at scale"
  Milestone: Terraform any cloud infrastructure from scratch.
  New stack? Day 1 production-ready.

Level 5 → "I can architect, deploy, and operationalise anything for anyone"
  Milestone: Walk into a customer's office, understand their environment,
  design a solution, build it, deploy it, hand it off.
  This is the FDE.
```
