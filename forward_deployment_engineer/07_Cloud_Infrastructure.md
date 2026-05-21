# Section 07 — Cloud Infrastructure

## 7.1 AWS — The FDE Primary Cloud Platform

FDEs deploy into customer AWS environments daily. You must be fluent in the core services.

### Core AWS Services Reference

| Service | Category | FDE Use Case |
|---------|----------|-------------|
| EC2 | Compute | Application servers, jump hosts |
| ECS/EKS | Container | Container orchestration |
| Lambda | Serverless | Automation, webhooks, event processing |
| S3 | Storage | Backups, artifacts, static assets |
| RDS | Database | PostgreSQL, MySQL managed instances |
| ElastiCache | Cache | Redis, Memcached |
| ALB/NLB | Load Balancing | Traffic distribution, SSL termination |
| Route 53 | DNS | Domain management, health-check routing |
| VPC | Networking | Network isolation, subnets, security groups |
| IAM | Identity | Permissions, roles, policies |
| Secrets Manager | Secrets | Database credentials, API keys |
| CloudWatch | Monitoring | Metrics, logs, alarms |
| CloudTrail | Audit | API call logging (compliance) |
| KMS | Encryption | Key management for encryption at rest |
| ACM | Certificates | Free TLS certificates for AWS resources |

---

## 7.2 IAM — The Most Important AWS Service for FDEs

Incorrectly configured IAM is the source of most cloud security incidents. Master it.

### IAM Principles for FDE Deployments
```
Principle of Least Privilege:
  Grant only the exact permissions required — nothing more.
  
Identity types:
  IAM User:   Human with long-term credentials (avoid — prefer SSO + roles)
  IAM Role:   Assumed by services, Lambda, EC2, ECS tasks
  IAM Group:  Collection of users sharing a policy
  IAM Policy: JSON document defining permissions

Permission evaluation:
  1. Explicit DENY always wins
  2. Explicit ALLOW required (no implicit allow)
  3. Everything is implicitly denied by default
```

```json
// Example: ECS task role — minimal permissions for an application
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadAppSecrets",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:123456789:secret:myapp/production/*"
      ]
    },
    {
      "Sid": "WriteToS3Bucket",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::myapp-production-assets/*"
    },
    {
      "Sid": "ReadS3BucketList",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::myapp-production-assets"
    }
  ]
}
```

---

## 7.3 VPC Design

Every enterprise customer deployment needs a well-designed VPC.

```
Production VPC Architecture:

VPC CIDR: 10.0.0.0/16 (65,534 IPs)

Availability Zones:    us-east-1a        us-east-1b        us-east-1c

Public subnets:        10.0.1.0/24       10.0.2.0/24       10.0.3.0/24
  (internet-facing)    [ALB, NAT GW]     [ALB, NAT GW]     [ALB, NAT GW]

Private App subnets:   10.0.11.0/24      10.0.12.0/24      10.0.13.0/24
  (no direct internet) [ECS tasks, EC2]  [ECS tasks, EC2]  [ECS tasks, EC2]

Private Data subnets:  10.0.21.0/24      10.0.22.0/24      10.0.23.0/24
  (database tier)      [RDS, ElastiCache] [RDS replica]    [ElastiCache]

Security Groups:
  sg-alb:       Allow 443/80 from 0.0.0.0/0
  sg-app:       Allow 3000 from sg-alb only
  sg-database:  Allow 5432 from sg-app only
  sg-cache:     Allow 6379 from sg-app only
```

```bash
# Terraform — VPC module (IaC for FDE deployments)
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "myapp-production"
  cidr = "10.0.0.0/16"

  azs              = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets  = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
  database_subnets = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false   # One per AZ for HA
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Environment = "production"
    Customer    = "acme-corp"
    ManagedBy   = "terraform"
  }
}
```

---

## 7.4 Terraform — Infrastructure as Code

Terraform is the most important infrastructure tool for FDEs. Every deployment should be codified.

### Project Structure
```
infra/
├── environments/
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   └── production/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
├── modules/
│   ├── app/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   └── networking/
└── shared/
    └── backend.tf    # S3 state backend
```

```hcl
# modules/app/main.tf — ECS application module
resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${var.app_name}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = var.app_name
    image = "${var.ecr_repo}:${var.app_version}"
    
    environment = [
      { name = "APP_ENV", value = var.environment }
    ]
    
    secrets = [
      { name = "DB_PASSWORD", valueFrom = "${aws_secretsmanager_secret.db_password.arn}" }
    ]
    
    portMappings = [{ containerPort = 3000, protocol = "tcp" }]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.app_name}/${var.environment}"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "app"
      }
    }
    
    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:3000/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

resource "aws_ecs_service" "app" {
  name            = var.app_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 100  # Zero-downtime deployment
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = var.app_name
    container_port   = 3000
  }

  lifecycle {
    ignore_changes = [desired_count]  # Allow autoscaler to manage count
  }
}
```

### Terraform Workflow for FDE Deployments
```bash
# Initialize
terraform init -backend-config="environments/production/backend.hcl"

# Plan — always review before apply
terraform plan -var-file="environments/production/terraform.tfvars" \
               -out="plan.tfplan"

# Review the plan output — look for:
# - Unexpected resource replacements (means downtime!)
# - Security group changes (means traffic disruption!)
# - IAM changes (means permission changes!)

# Apply
terraform apply "plan.tfplan"

# State management
terraform state list                          # All managed resources
terraform state show aws_ecs_service.app     # Specific resource state
terraform import aws_s3_bucket.assets arn:aws:s3:::my-bucket  # Import existing

# Destroy (use with extreme caution in customer environments)
terraform destroy -target=aws_ecs_service.app  # Targeted destroy only
```

---

## 7.5 AWS EKS — Managed Kubernetes

```bash
# Connect to EKS cluster
aws eks update-kubeconfig --name my-cluster --region us-east-1

# Verify cluster access
kubectl get nodes
kubectl get pods -A

# Create IAM role for EKS node group (IRSA pattern — pods get specific IAM role)
eksctl create iamserviceaccount \
    --cluster=my-cluster \
    --namespace=myapp \
    --name=myapp-service-account \
    --attach-policy-arn=arn:aws:iam::123456789:policy/MyAppPolicy \
    --override-existing-serviceaccounts \
    --approve
```

---

## 7.6 Azure — Key Differences for FDEs

Many enterprise customers (government, banks) run Azure. Key equivalents:

| AWS | Azure | Purpose |
|-----|-------|---------|
| EC2 | Virtual Machine | Compute |
| EKS | AKS | Kubernetes |
| Lambda | Azure Functions | Serverless |
| S3 | Blob Storage | Object storage |
| RDS | Azure Database | Managed PostgreSQL |
| ElastiCache | Azure Cache for Redis | Redis |
| IAM | Azure AD + RBAC | Identity |
| VPC | Virtual Network (VNet) | Network isolation |
| CloudWatch | Azure Monitor | Observability |
| Secrets Manager | Azure Key Vault | Secrets |

```bash
# Azure CLI common operations
az login
az account list --output table
az account set --subscription "Acme Corp Production"

# Create resource group
az group create --name myapp-prod --location eastus

# Get AKS credentials
az aks get-credentials --resource-group myapp-prod --name myapp-cluster

# List Key Vault secrets (important for FDE config management)
az keyvault secret list --vault-name myapp-keyvault --output table
az keyvault secret show --vault-name myapp-keyvault --name db-password --query "value" -o tsv
```

---

## 7.7 GCP — Key Services for FDEs

| AWS | GCP | Purpose |
|-----|-----|---------|
| EC2 | Compute Engine | Compute |
| EKS | GKE | Kubernetes |
| S3 | Cloud Storage | Object storage |
| RDS | Cloud SQL | Managed database |
| IAM | Cloud IAM + Workload Identity | Identity |
| CloudWatch | Cloud Monitoring | Observability |
| VPC | VPC | Networking |

---

## 7.8 High Availability Architecture

```
Multi-AZ Active-Active Architecture:

         Internet
            │
       ┌────▼────┐
       │  Route  │
       │   53    │
       └────┬────┘
            │ (latency-based routing)
     ┌──────┴──────┐
     │             │
┌────▼────┐   ┌────▼────┐
│  ALB    │   │  ALB    │
│ us-e-1a │   │ us-e-1b │
└────┬────┘   └────┬────┘
     │             │
┌────▼────┐   ┌────▼────┐
│  ECS    │   │  ECS    │
│ Tasks   │   │ Tasks   │
│  AZ-a   │   │  AZ-b   │
└────┬────┘   └────┬────┘
     │             │
     └──────┬──────┘
            │
     ┌──────▼──────┐
     │  RDS Multi- │
     │  AZ Primary │◄──sync replication──► RDS Standby
     └─────────────┘                       (AZ-b)
```

**Availability math every FDE must know:**
```
Single server uptime:               99.9%  = 8.7 hours downtime/year
Two servers (either one can fail):  99.99% = 52 minutes downtime/year
Three servers:                      99.999% = 5 minutes downtime/year

AWS SLAs:
  EC2:            99.99%
  RDS Multi-AZ:   99.95%
  S3:             99.99%
  ALB:            99.99%
  Route 53:       100%
```
