# Section 20 — Resources

## 20.1 Essential Books

### Infrastructure & Operations
| Title | Author | Why Read It |
|-------|--------|-------------|
| The Phoenix Project | Kim, Behr, Spafford | DevOps narrative; transforms how you think about deployments |
| The Unicorn Project | Gene Kim | Developer perspective on DevOps transformation |
| Site Reliability Engineering | Google SRE Team | Production engineering Bible; every FDE should read this |
| The SRE Workbook | Google SRE Team | Practical exercises to accompany SRE book |
| Accelerate | Forsgren, Humble, Kim | DORA research: what makes software delivery perform |
| Infrastructure as Code | Kief Morris | Terraform, automation, and cloud architecture patterns |

### Distributed Systems
| Title | Author | Why Read It |
|-------|--------|-------------|
| Designing Data-Intensive Applications | Martin Kleppmann | The single most important book for any FDE |
| Understanding Distributed Systems | Roberto Vitillo | Accessible intro to consensus, replication, fault tolerance |
| Database Internals | Alex Petrov | Deep PostgreSQL and storage engine understanding |
| Kafka: The Definitive Guide | Neha Narkhede et al. | Complete Kafka reference for event streaming |

### Software Engineering
| Title | Author | Why Read It |
|-------|--------|-------------|
| Clean Code | Robert C. Martin | Code quality principles (know them even if you debate them) |
| Refactoring | Martin Fowler | How to safely change production code |
| A Philosophy of Software Design | John Ousterhout | Complexity management in large systems |
| System Design Interview (Vol 1 & 2) | Alex Xu | Interview prep + real-world design examples |

### Leadership & Communication
| Title | Author | Why Read It |
|-------|--------|-------------|
| The Manager's Path | Camille Fournier | Engineering leadership progression |
| Turn the Ship Around | L. David Marquet | Ownership mindset (critical for FDE customer relationships) |
| Crucial Conversations | Patterson, Grenny | Customer escalation + difficult conversations |

---

## 20.2 Online Courses

### Kubernetes & Containers
```
KodeKloud: Certified Kubernetes Administrator (CKA)
  → Best hands-on K8s training available
  → Labs run in real clusters (not videos only)
  → Recommended for: K8s from basics to production
  
KodeKloud: Certified Kubernetes Application Developer (CKAD)
  → Deployment, configuration, multi-container patterns
  
Linux Foundation: LFS458 Kubernetes Fundamentals
  → Official LF course aligned with CKA exam

Killer.sh: CKA/CKAD Exam Simulator
  → Two full simulation exams included with CKA registration
  → Harder than the real exam
```

### Cloud (AWS)
```
A Cloud Guru (Pluralsight): AWS Certified Solutions Architect Associate
  → Covers all core AWS services with hands-on labs
  
Adrian Cantrill: AWS Certified Solutions Architect Professional
  → Best SAP course on the market (very in-depth)
  
Stephane Maarek: AWS courses on Udemy
  → SAA, SAP, Developer, SysOps tracks
  → Excellent for exam prep
```

### Infrastructure as Code
```
HashiCorp Learn (developer.hashicorp.com):
  → Official Terraform tutorials (free, interactive)
  → Vault, Nomad, Consul tutorials
  
FreeCodeCamp: Terraform on YouTube
  → 4-hour comprehensive course (free)
  
Udemy: Terraform for the Absolute Beginner (Mumshad Mannambeth)
  → Good ramp for beginners
```

### CI/CD & DevOps
```
GitHub Learning Lab (skills.github.com):
  → Interactive GitHub Actions training (free)
  → CI/CD, Docker integration, deployment workflows

Linux Foundation: LFS261 DevOps and SRE Fundamentals
  → DevOps toolchain, SRE principles, SLOs

Coursera: Google SRE course series
  → Based on Google SRE book practices
  → Available free to audit
```

### Observability
```
Grafana University (grafana.com/tutorials/):
  → Free Grafana Labs courses: Prometheus, Loki, Tempo, Grafana
  → Hands-on with Grafana Play sandbox

Udemy: Prometheus and Grafana the Real Talk
  → Production alerting, PromQL mastery

OpenTelemetry (opentelemetry.io/docs/):
  → Official getting started guides (free)
  → Collector configuration, instrumentation guides
```

---

## 20.3 GitHub Repositories to Study

### Kubernetes
```
kubernetes/kubernetes
  → Read: Deployment controller source code
  → Read: HPA controller source code
  → Understand: How Kubernetes actually works

kubernetes/examples
  → Production-grade YAML examples
  → Reference for manifest best practices

helm/charts (deprecated but study)
  → Historical reference for Helm chart structure

bitnami/charts
  → Industry-standard Helm charts
  → Study: values.yaml structure, named templates
```

### Infrastructure as Code
```
terraform-aws-modules (github.com/terraform-aws-modules)
  → Official AWS Terraform modules
  → Study the module interfaces and variable design

gruntwork-io/terragrunt
  → DRY Terraform at scale
  → Multi-account AWS deployments

infracost/infracost
  → Cost estimation in CI/CD
  → Use on every Terraform PR
```

### Observability
```
prometheus/prometheus
  → Read: alerting rule syntax
  → Read: recording rule best practices
  
grafana/loki
  → LogQL query examples
  → Label design for log shipping

open-telemetry/opentelemetry-demo
  → Full reference microservices app with OTEL instrumentation
  → Study: how traces connect services
```

### Security
```
OWASP/CheatSheetSeries
  → Every OWASP cheat sheet in one repo
  → Bookmark and reference constantly

aquasecurity/trivy
  → Container and IaC vulnerability scanning
  → Run on all Dockerfiles and Terraform

bridgecrewio/checkov
  → Terraform security policy scanner
  → Use in every CI pipeline
```

---

## 20.4 YouTube Channels

| Channel | Focus | Best Series |
|---------|-------|-------------|
| TechWorld with Nana | K8s, Docker, CI/CD | Kubernetes Tutorial for Beginners |
| NetworkChuck | Networking, Linux | CCNA series (free) |
| Fireship | Modern frameworks | Tech overviews in 100 seconds |
| Hussein Nasser | Distributed systems, DB | Backend Engineering Masterclass |
| Anton Babenko | Terraform, AWS | Terraform Thursdays |
| That DevOps Guy | DevOps toolchain | Kubernetes, ArgoCD, GitOps |
| KubeSimplify | Kubernetes | CKA prep, Helm deep dives |
| Dreams of Code | Systems programming | Advanced Rust, Go |

---

## 20.5 Engineering Blogs

### Company Engineering Blogs
```
Netflix Technology Blog (netflixtechblog.com)
  → Chaos engineering, microservices, streaming at scale
  → Must-read: "Fault Tolerance in a High Volume, Distributed System"

Uber Engineering (eng.uber.com)
  → Geospatial systems, real-time data, ML platform
  → Must-read: "Building Reliable Reprocessing and Dead Letter Queues"

Meta Engineering (engineering.fb.com)
  → Social graph, distributed systems at extreme scale
  → Must-read: "How Facebook Encodes your Videos"

Shopify Engineering (shopify.engineering)
  → Rails at scale, database sharding, SRE practices
  → Must-read: "Handling Large Data Migrations at Shopify"

Stripe Engineering (stripe.com/blog/engineering)
  → API design, reliability, payments infrastructure
  → Must-read: "The Secret Life of DNS"

Cloudflare Blog (blog.cloudflare.com)
  → Network engineering, DDoS, Rust, eBPF
  → Must-read: "How Cloudflare was not impacted by the Facebook outage"

GitHub Engineering (github.blog/engineering)
  → DevEx, Copilot, large-scale systems
  → Must-read: "How we found and fixed a rare race condition in our session handling"

Datadog Engineering (datadoghq.com/blog/engineering/)
  → Observability infrastructure, distributed tracing
  → Must-read: "The Architecture of Datadog's Observability Pipelines Worker"
```

### Aggregator & Newsletter
```
SRE Weekly (sreweekly.com)         → Curated SRE/production content
High Scalability (highscalability.com) → Architecture case studies
TLDR Newsletter (tldr.tech)        → Daily tech news digest
The Pragmatic Engineer (blog.pragmaticengineer.com) → Engineering career + systems
Architecture Notes (architecturenotes.co) → Deep system design breakdowns
```

---

## 20.6 Certifications (Priority Order)

```
Priority 1 — Most valuable for FDE:
  ★★★★★  AWS Certified Solutions Architect – Associate (SAA-C03)
           → Baseline cloud credibility. Get this first.
  
  ★★★★★  Certified Kubernetes Administrator (CKA)
           → Hands-on K8s. Gold standard for FDEs.

Priority 2 — Deepen expertise:
  ★★★★☆  HashiCorp Terraform Associate
           → Validates IaC skills. Respected by customers.
  
  ★★★★☆  AWS Certified Solutions Architect – Professional (SAP-C02)
           → Advanced architecture patterns. 2+ years experience required.
  
  ★★★☆☆  Certified Kubernetes Security Specialist (CKS)
           → Valuable for security-focused deployments.

Priority 3 — Specialist:
  ★★★☆☆  AWS Certified DevOps Engineer – Professional
  ★★★☆☆  CKAD (Kubernetes Application Developer)
  ★★☆☆☆  GCP Professional Cloud Architect / Azure Solutions Architect
```

---

## 20.7 Practice Platforms

| Platform | What You Practice | Cost |
|----------|------------------|----|
| Killercoda (killercoda.com) | K8s, Linux, Docker — browser-based | Free tier |
| KodeKloud (kodekloud.com) | CKA, CKAD, Terraform, Ansible | Paid |
| Linux Foundation Sandbox | CKA practice scenarios | With registration |
| AWS Free Tier (aws.amazon.com) | Real AWS — costs if exceeded | Free tier limited |
| LocalStack (localstack.cloud) | AWS services locally | Free/Paid |
| Minikube / k3d | Local K8s cluster | Free |
| Play with Docker (labs.play-with-docker.com) | Docker browser environment | Free |
| LeetCode (leetcode.com) | Coding algorithms | Free/Paid |
| Excalidraw (excalidraw.com) | System design diagrams | Free |

---

## 20.8 Communities

```
Kubernetes Slack (slack.k8s.io)
  → #kubernetes-users, #sig-node, #helm-users
  → Ask real questions, get real answers

CNCF Slack (slack.cncf.io)
  → #opentelemetry, #argo, #prometheus, #grafana
  → Direct access to project maintainers

HashiCorp Discuss (discuss.hashicorp.com)
  → Terraform, Vault community forums

Reddit
  → r/kubernetes, r/devops, r/sre, r/aws

Discord
  → DevOps Lounge, Kubernetes Discord
  → Real-time chat with practitioners

LinkedIn
  → Follow: Kelsey Hightower, Charity Majors, Martin Kleppmann
  → Join: Site Reliability Engineering, Kubernetes/Containers, DevOps groups
```
