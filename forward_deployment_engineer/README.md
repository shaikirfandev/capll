# Forward Deployment Engineer — Enterprise Mastery Handbook

> **Audience:** Engineers with 5+ years of software development experience transitioning into  
> a Forward Deployment Engineer (FDE) role at companies like Palantir, OpenAI, Stripe,  
> Datadog, Snowflake, Vercel, Netflix, Uber, Amazon, Google, or Microsoft.
>
> **Philosophy:** An FDE is not a DevOps engineer who also talks to customers.  
> An FDE is a software architect who deploys with precision, debugs under pressure,  
> communicates at the executive level, and treats production as a living system.

---

## Folder Structure

```
forward_deployment_engineer/
├── README.md                          ← This file
├── 01_Introduction.md                 ← Role, responsibilities, FDE vs SRE vs SA
├── 02_Software_Foundations.md         ← DSA, system design, SDLC, patterns
├── 03_Programming_Skills.md           ← JS, TS, Python, Go, Bash, async, perf
├── 04_Frontend_Backend.md             ← React, Next.js, APIs, auth, microservices
├── 05_Databases.md                    ← SQL, NoSQL, Redis, Elasticsearch, tuning
├── 06_Linux_Networking.md             ← Linux admin, SSH, Nginx, DNS, TCP/IP
├── 07_Cloud_Infrastructure.md         ← AWS, Azure, GCP, IAM, VPC, HA
├── 08_DevOps_Deployment.md            ← Docker, K8s, Helm, Terraform, CI/CD
├── 09_Observability_Monitoring.md     ← Grafana, Prometheus, Datadog, OTel
├── 10_Distributed_Systems.md          ← CAP, Kafka, patterns, fault tolerance
├── 11_Security_Engineering.md         ← OWASP, RBAC, secrets, TLS, scanning
├── 12_Production_Engineering.md       ← RCA, postmortems, rollback, live debug
├── 13_Enterprise_Deployment.md        ← Customer workflow, onboarding, SLAs
├── 14_System_Design.md                ← Architecture patterns, case studies
├── 15_AI_Modern_Systems.md            ← LLMs, vector DBs, MLOps, GPU deployments
├── 16_Hands_On_Projects.md            ← 9 complete production-grade projects
├── 17_Interview_Prep.md               ← 150+ Q&A, STAR, system design rounds
├── 18_Case_Studies.md                 ← Real production outages + RCA walkthroughs
├── 19_Learning_Roadmap.md             ← 30/90-day, 6-month, 1-year plan
├── 20_Resources.md                    ← Books, repos, courses, blogs, platforms
└── 21_Cheat_Sheets.md                 ← Linux, Docker, K8s, Git, Terraform refs
```

---

## Quick Reference — Top Skills by Tier

### Tier 1 — Non-Negotiable (Day 1 Competency)
- Linux command line mastery + SSH + process debugging
- Docker: build, run, compose, multi-stage builds
- Git: branching, rebasing, conflict resolution, hooks
- REST API design + debugging (curl, Postman, Insomnia)
- Kubernetes: pods, deployments, services, ConfigMaps, ingress
- Python or Go scripting for automation
- PostgreSQL: schema design, query optimisation, EXPLAIN

### Tier 2 — Required (90 Days)
- Terraform: state management, modules, workspaces
- CI/CD: GitHub Actions or GitLab CI full pipelines
- Observability: Prometheus + Grafana + structured logging
- Kafka / message queue architecture
- AWS or GCP core services (EC2, S3, IAM, VPC, RDS)
- Helm chart authoring
- JWT + OAuth2 + OIDC authentication flows

### Tier 3 — Differentiator (6 Months)
- EKF sensor fusion / distributed tracing (OpenTelemetry)
- Multi-region deployment + failover
- LLM API deployment and prompt infrastructure
- Security: zero-trust, secrets rotation, CVE triage
- Customer architecture presentations (executive level)
- Cost optimisation across cloud spend

---

## The FDE Mindset

```
"You are the last line between the customer's production system
 and failure. You wrote the code, you deployed the stack, you
 own the incident, you close the loop."
                                    — Palantir FDE philosophy
```

| Situation | SWE Response | FDE Response |
|-----------|-------------|-------------|
| Deployment fails at 2am | Escalate to on-call | You ARE on-call. Diagnose and fix. |
| Customer says "it's slow" | File a ticket | SSH in, run profiler, identify bottleneck, fix in session |
| Requirement unclear | Ask PM | Lead architecture discussion with the customer directly |
| New feature request | Sprint planning | Rapid prototype + deploy to staging within 24h |
| Post-deployment issue | Monitor Jira | Live postmortem with customer engineering team |
