# Section 01 — Introduction to Forward Deployment Engineering

## 1.1 What Is a Forward Deployment Engineer?

A **Forward Deployment Engineer (FDE)** is a senior technical role that sits at the intersection of software engineering, infrastructure, architecture, and customer success. FDEs are deployed directly into customer environments — on-site or remotely — to implement, customise, integrate, and operate enterprise software platforms.

The term was popularised by **Palantir Technologies**, where FDEs ("Forward Deployed Engineers") embedded with government agencies, financial institutions, and defence contractors to build production data infrastructure systems directly within client networks.

Today the concept has spread across the industry. At different companies it goes by different names:

| Company | Title Used |
|---------|-----------|
| Palantir | Forward Deployed Engineer (FDE) |
| Stripe | Deployment Engineer / Integration Engineer |
| Datadog | Solutions Engineer / Deployment Engineer |
| Snowflake | Field Engineer / Deployment Architect |
| OpenAI | Forward Deployment Engineer |
| Vercel | Solutions Engineer |
| Google | Customer Engineer / Field Engineer |
| AWS | Solutions Architect (implementation-focused) |

---

## 1.2 Core Responsibilities

### Technical Delivery
- **Deploy** software platforms into customer infrastructure (cloud, on-prem, hybrid)
- **Integrate** with customer data sources, authentication systems, APIs, and workflows
- **Customise** platform behaviour through configuration, scripting, and code
- **Build** customer-specific features, dashboards, pipelines, and automations
- **Maintain** and upgrade deployed systems with zero production downtime

### Customer Engineering
- Lead **architecture discussions** with customer engineering and IT teams
- Translate vague business requirements into **technical specifications**
- Present deployment architectures to CTOs, VPs of Engineering, and CISOs
- Run **technical workshops** and training sessions for customer developers
- Produce deployment documentation and runbooks for customer teams

### Operations
- Own **production incidents** end-to-end — detect, triage, resolve, document
- Build and maintain **monitoring and alerting** for deployed systems
- Conduct **performance optimisation** and capacity planning
- Execute **rollback procedures** when deployments go wrong
- Manage **SLA commitments** through proactive operational oversight

---

## 1.3 Role Comparison Matrix

Understanding where FDE sits relative to adjacent roles is critical for positioning yourself and knowing when to escalate or delegate.

| Dimension | Software Engineer | DevOps Engineer | SRE | Solutions Architect | Platform Engineer | FDE |
|-----------|-----------------|----------------|-----|--------------------|--------------------|-----|
| **Primary focus** | Feature development | CI/CD pipelines | Reliability | Pre-sales design | Internal tooling | Customer delivery |
| **Codes?** | Always | Sometimes | Sometimes | Rarely | Always | Always |
| **Deploys?** | To dev/staging | To all envs | To prod | Designs only | Internal infra | To customer prod |
| **Customer-facing?** | Rarely | No | No | Yes (pre-sales) | No | Daily |
| **Incidents?** | Escalates | Fixes infra | Owns all | Not involved | Escalates | Owns in customer env |
| **Architecture?** | Component-level | Infra-level | Service-level | Full system | Platform-level | Customer system |
| **Writes runbooks?** | No | Yes | Yes | No | Yes | Yes (for customers) |
| **On-call?** | Sometimes | Yes | Yes | No | Sometimes | Yes (customer SLA) |

### SRE vs FDE (Key Distinction)
```
SRE: "How do we keep our platform reliable for all customers?"
FDE: "How do we keep THIS customer's deployment of our platform reliable right now?"

SRE works inward (platform health).
FDE works outward (customer deployment health).
```

### Solutions Architect vs FDE (Key Distinction)
```
Solutions Architect: Designs the blueprint, hands it off, moves to next customer.
FDE: Designs the blueprint, builds it, deploys it, maintains it, owns its outcome.

SA = architecture at 30,000 feet.
FDE = architecture at ground level with a keyboard in hand.
```

---

## 1.4 Real-World Deployment Lifecycle

A typical FDE engagement follows this lifecycle from first contact to steady-state operations:

```
PHASE 1: DISCOVERY (Week 1-2)
├── Customer kickoff meeting
├── Requirements gathering sessions
├── Existing architecture audit
├── Integration landscape mapping
├── Security and compliance review (SSO, network, data residency)
└── Delivery: Technical Discovery Document

PHASE 2: DESIGN (Week 2-3)
├── Reference architecture selection
├── Customisation requirements list
├── Integration API design
├── Data model mapping
├── Infrastructure sizing and capacity planning
└── Delivery: Architecture Design Document (ADD)

PHASE 3: STAGING DEPLOYMENT (Week 3-5)
├── Infrastructure provisioning (Terraform / CloudFormation)
├── Kubernetes namespace and RBAC setup
├── Application deployment (Helm charts)
├── SSO / IdP integration (SAML/OIDC)
├── Data source connectivity (DB, APIs, S3)
├── End-to-end integration testing
└── Delivery: Staging environment + test report

PHASE 4: PRODUCTION DEPLOYMENT (Week 5-6)
├── Change management documentation
├── Customer sign-off on staging
├── Production provisioning
├── Data migration / cutover execution
├── Smoke tests and validation
├── Rollback plan standby
└── Delivery: Production-ready system

PHASE 5: HANDOVER & STEADY STATE (Ongoing)
├── Customer team training
├── Runbook documentation
├── Monitoring and alerting setup
├── SLA agreement and escalation paths
├── Regular cadence: weekly check-ins
└── Delivery: Operational runbook + SLA SLOs
```

---

## 1.5 The Customer Engineering Relationship

Working with enterprise clients is fundamentally different from internal software development. As an FDE, you interact with:

### Stakeholder Tiers You Will Face

| Stakeholder | Role | What They Care About |
|------------|------|---------------------|
| CTO / VP Engineering | Executive | Strategic alignment, timeline, risk |
| Principal / Staff Engineer | Technical lead | Architecture quality, technical risk |
| DevOps / SRE team | Operators | Runbooks, monitoring, handover quality |
| Data Engineer | Integration | API contracts, data format, performance |
| Security / CISO team | Compliance | SSO, data residency, vulnerability posture |
| Business Analyst | Requirements | Feature parity, reporting, UX |

### Communication Rules for FDE Customer Engagement
1. **Never say "that's not possible" in the first meeting** — explore the constraint, propose alternatives
2. **Translate technical risk into business impact** — "latency of 500ms means 2% conversion drop" not "the API is slow"
3. **Document everything** — every decision made verbally becomes a ticket or ADR (Architecture Decision Record)
4. **Set expectations with specificity** — "the integration will be complete by EOD Friday" not "soon"
5. **Own production issues in front of the customer** — never blame the platform, always present with a resolution path
6. **Over-communicate during incidents** — status update every 15 minutes even if "still investigating"

---

## 1.6 FDE Competency Levels

### Level 1 — Associate FDE (0-2 years in role)
- Deploys pre-built configurations under supervision
- Handles Tier 1/2 support issues
- Writes basic integration scripts
- Participates in customer calls as technical support

### Level 2 — FDE (2-4 years in role)
- Independently leads customer deployments end-to-end
- Architects integrations with minimal guidance
- Handles production incidents with confidence
- Leads technical portions of customer calls

### Level 3 — Senior FDE (4-7 years in role)
- Manages multiple concurrent customer engagements
- Defines deployment patterns and reusable playbooks
- Mentors junior FDEs
- Presents at executive level (C-suite, board)
- Identifies product gaps and feeds engineering roadmap

### Level 4 — Principal / Staff FDE
- Defines the company's deployment methodology
- Architects solutions for the company's largest / most complex customers
- Builds internal tooling and automation for the FDE team
- Bridges product, engineering, and go-to-market
- Seen externally as a thought leader
