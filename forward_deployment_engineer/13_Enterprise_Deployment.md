# Section 13 — Enterprise Deployment Playbook

## 13.1 Customer Onboarding Workflow

The FDE customer onboarding process is a repeatable workflow. Document it, standardise it, and execute it consistently across every engagement.

```
FULL ENTERPRISE ONBOARDING TIMELINE (Typical 6-Week Engagement)

Week 1: DISCOVERY
  Day 1-2: Kickoff + requirements gathering
  Day 3-4: Architecture review + integration landscape
  Day 5:   Security/compliance review
  Deliverable: Technical Discovery Document

Week 2: DESIGN
  Day 6-7:  Architecture design document (ADD)
  Day 8:    Customer review + approval
  Day 9-10: Infrastructure sizing + IaC design
  Deliverable: ADD + Terraform plan

Week 3: STAGING BUILD
  Day 11-12: Infrastructure provisioning (Terraform apply)
  Day 13:    Platform deployment (Helm install)
  Day 14:    SSO/IdP integration
  Day 15:    Initial connectivity tests
  Deliverable: Staging environment accessible

Week 4: STAGING VALIDATION
  Day 16-17: Integration testing with customer systems
  Day 18:    Data pipeline validation
  Day 19:    Performance testing (baseline load)
  Day 20:    Customer UAT sign-off
  Deliverable: Signed UAT acceptance

Week 5: PRODUCTION BUILD
  Day 21-22: Production infrastructure (Terraform)
  Day 23:    Production deployment + configuration
  Day 24:    Data migration (if applicable)
  Day 25:    Smoke tests + validation
  Deliverable: Production environment live

Week 6: HANDOVER
  Day 26-27: Customer team training
  Day 28:    Monitoring + alerting setup
  Day 29:    Runbook review with customer ops
  Day 30:    Go-live + hypercare period begins
  Deliverable: Operations runbook + SLA start
```

---

## 13.2 Technical Discovery Document Template

```markdown
# Technical Discovery Document
**Customer:** Acme Corp  
**Date:** 2024-11-15  
**FDE:** [Your Name]  
**Version:** 1.2

---

## 1. Executive Summary
Brief description of the customer's technical environment and deployment goals.

## 2. Current Environment

### Infrastructure
| Component | Technology | Version | Location |
|-----------|-----------|---------|----------|
| Kubernetes | EKS | 1.28 | AWS us-east-1 |
| Database | PostgreSQL | 14.5 | RDS Multi-AZ |
| Identity | Okta | — | SaaS |
| CI/CD | GitHub Actions | — | SaaS |
| Monitoring | Datadog | — | SaaS |

### Network Architecture
- VPC CIDR: 10.100.0.0/16
- Outbound internet: via NAT Gateway
- Inbound: Only through ALB (no direct ingress)
- Corporate VPN to AWS: Site-to-site VPN (10.200.0.0/16 → AWS)

### Data Sources to Integrate
| Source | Type | Protocol | Volume |
|--------|------|----------|--------|
| PostgreSQL prod DB | Relational | JDBC | 500GB |
| Salesforce CRM | API | REST | 50k records |
| S3 data lake | Object | S3 API | 2TB |

## 3. Security & Compliance Requirements
- Data must remain in AWS us-east-1 (data residency)
- SSO via Okta (OIDC)
- All traffic encrypted in transit (TLS 1.2+)
- Audit logging to Splunk (customer SIEM)
- SOC 2 Type II required before production access

## 4. Integration Requirements
- [x] SSO/OIDC via Okta
- [x] PostgreSQL read replica integration
- [x] Salesforce CRM connector
- [ ] Custom webhook for deployment notifications (Slack + PagerDuty)

## 5. Open Questions
| # | Question | Owner | Due |
|---|----------|-------|-----|
| 1 | What is the Salesforce API rate limit in production? | Customer | 2024-11-17 |
| 2 | Is Kubernetes 1.29 upgrade planned before go-live? | Customer infra | 2024-11-17 |

## 6. Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Salesforce API throttling | Medium | High | Implement rate-limited queue |
| Okta OIDC config delay | Low | High | Start config in Week 1 |
```

---

## 13.3 Architecture Decision Records (ADRs)

ADRs document every technical decision made during an engagement.

```markdown
# ADR-001: Database Integration Strategy

**Date:** 2024-11-12  
**Status:** Accepted  
**Deciders:** FDE team + Customer Infra Lead

## Context
The platform needs to read data from the customer's PostgreSQL production database.
Direct queries to the primary would impact production performance.

## Decision
Use a **dedicated read replica** for all platform queries.
- Replica will be tagged with `purpose=platform-read`
- Platform credentials will have SELECT-only permissions on specific schemas
- Connection pooling via PgBouncer (pool_size=10, transaction mode)

## Rationale
- Isolates platform load from production write traffic
- SELECT-only permissions limit blast radius of credential compromise
- PgBouncer prevents connection exhaustion

## Consequences
- Read replica lag: up to 100ms (acceptable per business requirements)
- Customer must provision replica (est. 2 hours of customer infra work)
- If replica falls behind >30s, platform switches to degraded mode with alert
```

---

## 13.4 SLA Management

### SLA Tier Structure
```
Enterprise SLA Tiers (typical structure):

Tier 1 — Business Critical:
  Uptime SLO:      99.9% monthly
  P1 response:     15 minutes
  P1 resolution:   4 hours
  Maintenance:     Scheduled 48h notice, weekends 2–4am

Tier 2 — Standard:
  Uptime SLO:      99.5% monthly
  P1 response:     1 hour
  P1 resolution:   8 hours
  Maintenance:     Scheduled 24h notice

Tier 3 — Developer:
  Uptime SLO:      99.0% monthly
  P1 response:     4 hours
  P1 resolution:   Next business day
```

### SLA Reporting Dashboard (Monthly)
```
Monthly SLA Report: Acme Corp — November 2024

Uptime: 99.94% (SLO: 99.9% ✅)
  Total minutes in period: 43,200
  Downtime: 26 minutes
  Incidents: 1 (SEV-2, 2024-11-15 10:21–10:33, +13 min post-incident monitoring)

Performance:
  p50 latency: 45ms  (SLO: <200ms ✅)
  p95 latency: 120ms (SLO: <500ms ✅)
  p99 latency: 280ms (SLO: <1000ms ✅)

Error Rate: 0.02% (SLO: <0.1% ✅)

Credits: None (no SLA breach)
```

---

## 13.5 Change Management

Enterprise customers require change management processes. Never deploy without following this.

```
Change Management Checklist:

□ CHANGE REQUEST CREATED
  - Change ID: CHG-2024-1115-001
  - Description: Upgrade deployment-service from v2.0 to v2.1
  - Risk level: Low (minor feature release, backward compatible)
  - Rollback plan documented and tested in staging
  - Affected services: deployment-service only
  - Customer communication: Not required for low-risk change

□ PRE-CHANGE VALIDATION
  - Staging deployment: ✅ completed 2024-11-14
  - Staging smoke tests: ✅ all 47 tests passing
  - Customer-impacting features: ✅ tested in staging with customer data copy
  - DB migration: ✅ migration tested on staging, backward compatible

□ CHANGE WINDOW
  - Scheduled: Saturday 2024-11-16 02:00–04:00 UTC
  - Duration: 30 minutes estimated
  - On-call: [FDE name] + [backup]
  
□ EXECUTION
  - Verify staging still healthy before starting
  - Helm upgrade with --atomic flag
  - Smoke test after each region
  - Monitor error rate for 15 minutes post-deployment

□ POST-CHANGE VALIDATION
  - Smoke test: pass/fail
  - Error rate: <0.1%
  - P99 latency: <500ms
  - Notify: Customer Slack channel
```

---

## 13.6 Customer Communication Templates

```
===== NEW INCIDENT — Immediate Notification =====

Subject: [INCIDENT] Deployment API — Elevated Error Rates

Hi [Customer Name] Team,

We are currently investigating elevated error rates affecting the Deployment API
for your environment.

Impact:    API requests returning 503 errors
Started:   2024-11-15 10:21 UTC
Affected:  POST /api/v1/deployments endpoints

We have identified the issue and are implementing a fix.
Next update: 15 minutes (10:48 UTC)

Incident channel: #incident-acme-2024-1115

— [FDE Name], Platform Engineering

=====

===== INCIDENT RESOLVED =====

Subject: [RESOLVED] Deployment API — Incident 2024-1115

Hi [Customer Name] Team,

The incident affecting the Deployment API has been resolved.

Timeline:
  10:21 UTC — Incident start (elevated 503 errors)
  10:24 UTC — Root cause identified (memory limit exceeded)
  10:33 UTC — Service restored (memory limit increased, pods healthy)
  Duration: 12 minutes

Impact:
  Approximately 1,440 requests affected.
  No data loss. No deployments were in progress during the incident.

Root Cause:
  A large file upload (48MB CSV) exceeded the container memory limit.
  The container was OOMKilled and took ~2 minutes to restart.

Actions Taken:
  Immediate: Memory limit increased from 256Mi to 1Gi.
  Permanent fix: File size validation (10MB limit) deploying Monday.

Full postmortem available at: https://status.myapp.com/incidents/2024-1115

— [FDE Name], Platform Engineering
```
