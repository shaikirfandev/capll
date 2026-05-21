# Section 21 — Cheat Sheets

## 21.1 Linux Command Reference

### File System
```bash
ls -lahF                    # Long list with human sizes + type indicators
ls -lt                      # Sort by modification time (newest first)
find / -name "*.log" -mtime -1  # Files modified in last 1 day
find . -size +100M          # Files larger than 100MB
du -sh /*                   # Directory sizes
df -hT                      # Disk free + filesystem type
stat file.txt               # File metadata (size, permissions, timestamps)
chmod 644 file.txt          # rw-r--r--
chmod 755 dir/              # rwxr-xr-x
chown user:group file       # Change owner
ln -s /etc/nginx/sites-available/app /etc/nginx/sites-enabled/app  # Symlink
```

### Process Management
```bash
ps aux                      # All running processes
ps aux | grep nginx         # Filter by process name
top                         # Real-time process monitor
htop                        # Interactive process monitor (better top)
kill -9 <pid>               # Force kill process
kill -15 <pid>              # Graceful kill (SIGTERM)
pkill nginx                 # Kill by name
nohup ./app &               # Run in background, survive logout
jobs                        # List background jobs
fg %1                       # Bring job 1 to foreground
lsof -i :8080               # What process is using port 8080?
lsof -p <pid>               # Files opened by process
strace -p <pid>             # Trace system calls of running process
```

### Log Analysis
```bash
tail -f /var/log/app.log            # Follow log in real time
tail -n 200 /var/log/app.log        # Last 200 lines
grep "ERROR" app.log                # Lines containing ERROR
grep -n "ERROR" app.log             # With line numbers
grep -v "health" app.log            # Exclude health check lines
grep -E "ERROR|WARN" app.log        # Multiple patterns
cat app.log | awk '{print $4}' | sort | uniq -c | sort -rn  # Top IPs
journalctl -u nginx -f              # Systemd service logs (follow)
journalctl --since "1 hour ago"     # Recent journal entries
journalctl -p err                   # Only error-level logs
```

### Network
```bash
curl -vI https://api.example.com    # Verbose HTTP headers only
curl -w "\n%{http_code}" https://...  # Print status code
wget -O - https://example.com       # Fetch and print to stdout
nc -zv 10.0.0.5 5432                # Test TCP connection to host:port
netstat -tulpn                      # Open ports + listening services
ss -tulpn                           # Modern netstat equivalent
ping -c 4 10.0.0.5                  # Send 4 ICMP pings
traceroute 8.8.8.8                  # Trace network path
nslookup api.example.com            # DNS lookup
dig api.example.com                 # Detailed DNS lookup
dig +short api.example.com          # Just the IP
host api.example.com                # Simple forward lookup
iptables -L -n -v                   # List firewall rules
tcpdump -i eth0 port 5432           # Capture DB traffic
tcpdump -i eth0 -w /tmp/cap.pcap    # Write capture to file
```

### System Info
```bash
uname -a                    # Kernel version + architecture
cat /etc/os-release         # Linux distribution info
uptime                      # System uptime + load average
free -m                     # Memory usage in MB
vmstat 1 5                  # System stats every 1s, 5 times
iostat -x 1 5               # Disk I/O stats
sar -u 1 5                  # CPU utilisation history
dmesg | tail -20            # Kernel messages
cat /proc/cpuinfo           # CPU details
cat /proc/meminfo           # Memory details
sysctl -a | grep vm.swappiness  # Kernel tuning parameters
```

---

## 21.2 Docker Command Reference

### Images
```bash
docker build -t myapp:1.0.0 .           # Build from Dockerfile in current dir
docker build --no-cache -t myapp .      # Build without cache
docker build -f Dockerfile.prod .       # Specify Dockerfile
docker images                            # List local images
docker image ls --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker pull nginx:alpine                 # Pull from registry
docker push registry.example.com/myapp:1.0.0
docker tag myapp:latest registry/myapp:1.0.0  # Retag
docker rmi myapp:old                     # Remove image
docker image prune -a                    # Remove unused images
docker save myapp:1.0.0 | gzip > myapp.tar.gz  # Export image
docker load < myapp.tar.gz              # Import image
docker inspect myapp:1.0.0             # Full image metadata
docker history myapp:1.0.0             # Layer history
```

### Containers
```bash
docker run -d -p 8080:80 --name webapp nginx    # Detached with port mapping
docker run -it ubuntu:22.04 /bin/bash           # Interactive shell
docker run --rm -v $(pwd):/data alpine ls /data # Mount current dir + remove on exit
docker run -e DATABASE_URL=postgres://... myapp # Environment variables
docker run --memory 512m --cpus 0.5 myapp       # Resource limits
docker ps                                        # Running containers
docker ps -a                                     # All containers
docker logs webapp -f --tail 100                # Follow last 100 lines
docker exec -it webapp /bin/sh                  # Shell into running container
docker exec webapp env                           # Print env vars
docker stop webapp && docker rm webapp          # Stop and remove
docker stats                                     # Live resource usage
docker inspect webapp                            # Container metadata
docker cp webapp:/etc/nginx/nginx.conf ./       # Copy file from container
```

### Compose
```bash
docker compose up -d                    # Start all services detached
docker compose up --build               # Build then start
docker compose down                     # Stop and remove containers
docker compose down -v                  # Also remove volumes
docker compose ps                       # Service status
docker compose logs -f app             # Follow service logs
docker compose exec db psql -U postgres # Run command in service
docker compose pull                     # Pull latest images
docker compose config                   # Validate and print config
```

### Cleanup
```bash
docker system prune -f                  # Remove stopped containers + dangling images
docker system prune -af                 # Include all unused images
docker volume ls                        # List volumes
docker volume prune                     # Remove unused volumes
docker network ls                       # List networks
```

---

## 21.3 Kubernetes (kubectl) Reference

### Context & Cluster
```bash
kubectl config get-contexts             # List all contexts
kubectl config use-context prod-cluster # Switch context
kubectl config current-context          # Show active context
kubectl cluster-info                    # API server URL
kubectl api-resources                   # All resource types
kubectl explain deployment.spec.template  # Field documentation
```

### Pods
```bash
kubectl get pods -n myapp               # List pods in namespace
kubectl get pods -A                     # All namespaces
kubectl get pods -o wide                # With node + IP
kubectl describe pod myapp-xyz          # Detailed info + events
kubectl logs myapp-xyz -f               # Follow logs
kubectl logs myapp-xyz -c init-migrate  # Specific container logs
kubectl logs myapp-xyz --previous       # Crashed container logs
kubectl exec -it myapp-xyz -- /bin/sh   # Shell into pod
kubectl exec myapp-xyz -- env           # Print env vars
kubectl delete pod myapp-xyz            # Delete (will restart if Deployment)
kubectl top pod -n myapp                # CPU + memory usage
```

### Deployments
```bash
kubectl get deployments -n myapp
kubectl describe deployment myapp
kubectl rollout status deployment/myapp
kubectl rollout history deployment/myapp
kubectl rollout undo deployment/myapp          # Rollback to previous
kubectl rollout undo deployment/myapp --to-revision=3  # Rollback to revision 3
kubectl scale deployment myapp --replicas=5
kubectl set image deployment/myapp app=myapp:2.0.0  # Update image
kubectl get events --sort-by=.lastTimestamp -n myapp
```

### Services & Ingress
```bash
kubectl get services -n myapp
kubectl describe service myapp-svc
kubectl get ingress -n myapp
kubectl port-forward svc/myapp-svc 8080:80   # Local port forward
kubectl port-forward pod/myapp-xyz 8080:8080
```

### Config & Secrets
```bash
kubectl get configmaps -n myapp
kubectl describe configmap app-config
kubectl create configmap app-config --from-file=config.yaml
kubectl get secrets -n myapp
kubectl describe secret app-secrets
kubectl create secret generic db-creds \
  --from-literal=password=supersecret
```

### Nodes
```bash
kubectl get nodes                        # Node list
kubectl describe node ip-10-0-0-5
kubectl top node                         # CPU + memory per node
kubectl cordon node-1                    # Mark unschedulable
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data
kubectl uncordon node-1                 # Re-enable scheduling
```

### Helm
```bash
helm repo add stable https://charts.helm.sh/stable
helm repo update
helm search repo nginx
helm install myapp ./charts/myapp -n myapp --create-namespace
helm install myapp ./charts/myapp -f custom-values.yaml
helm upgrade myapp ./charts/myapp --set image.tag=2.0.0
helm rollback myapp 1
helm uninstall myapp -n myapp
helm list -n myapp
helm history myapp
helm template myapp ./charts/myapp -f values.yaml  # Dry-run render
helm lint ./charts/myapp
```

---

## 21.4 Git Command Reference

### Daily Operations
```bash
git status                              # Show working tree status
git diff                                # Unstaged changes
git diff --staged                       # Staged changes (before commit)
git add .                               # Stage all changes
git add -p                              # Stage interactively (patch mode)
git commit -m "feat: add rate limiter"
git commit --amend --no-edit            # Amend last commit (don't push!)
git log --oneline -20                   # Recent 20 commits
git log --oneline --graph --all         # Branch graph
git stash                               # Temporarily stash changes
git stash pop                           # Restore stashed changes
git stash list                          # List stashes
```

### Branches
```bash
git checkout -b feature/new-feature     # Create + switch branch
git checkout main
git merge feature/new-feature
git merge --squash feature/new-feature  # Squash to single commit
git rebase main                         # Rebase onto main
git rebase -i HEAD~3                    # Interactive rebase last 3 commits
git branch -d feature/done             # Delete local branch
git push origin --delete feature/done  # Delete remote branch
git fetch --prune                       # Remove stale remote tracking branches
```

### Remote
```bash
git remote -v                           # Show remotes
git push origin main
git push --force-with-lease             # Safe force push (not --force)
git pull --rebase                       # Pull + rebase (cleaner history)
git fetch origin                        # Fetch without merging
git cherry-pick abc1234                 # Apply specific commit
```

### Debugging
```bash
git blame file.py                       # Who wrote each line?
git log --all --follow file.py          # Full history of file
git bisect start                        # Binary search for bug commit
git bisect good HEAD~20
git bisect bad HEAD
git show abc1234                        # Show commit details
git diff HEAD~3..HEAD -- file.py       # Changes to file in last 3 commits
```

---

## 21.5 Terraform Reference

```bash
# Workflow
terraform init                          # Download providers + modules
terraform fmt -recursive               # Format all .tf files
terraform validate                      # Validate syntax + logic
terraform plan -out=tfplan             # Preview changes, save plan
terraform apply tfplan                  # Apply saved plan
terraform apply -auto-approve           # Apply without confirmation (CI only)
terraform destroy                       # Destroy all resources
terraform destroy -target=module.rds   # Destroy specific resource

# State
terraform state list                    # All resources in state
terraform state show aws_instance.web  # Details of resource
terraform state mv aws_s3_bucket.old aws_s3_bucket.new  # Rename
terraform state rm aws_instance.legacy # Remove from state (does NOT delete resource)
terraform import aws_s3_bucket.my-bucket my-bucket-name  # Import existing

# Variables
terraform apply -var="environment=prod"
terraform apply -var-file="prod.tfvars"
TF_VAR_db_password=secret terraform apply  # Environment variable

# Workspaces
terraform workspace list
terraform workspace new staging
terraform workspace select prod
terraform workspace show

# Debugging
TF_LOG=DEBUG terraform plan
terraform console                       # Interactive expression evaluation
terraform output                        # Print output values
terraform output db_endpoint            # Specific output
```

---

## 21.6 GitHub Actions Quick Reference

```yaml
# Trigger patterns
on:
  push:
    branches: [main, "release/*"]
    paths:   ["src/**", "Dockerfile"]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 9 * * 1-5"            # 9am Mon-Fri UTC
  workflow_dispatch:                   # Manual trigger

# Common steps
- uses: actions/checkout@v4
- uses: actions/setup-node@v4
  with: { node-version: "20" }
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- uses: docker/setup-buildx-action@v3

# Cache
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: ${{ runner.os }}-node-

# AWS OIDC (no access keys)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/github-actions
    aws-region: us-east-1

# Secrets + env
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
  APP_ENV: production

# Conditional steps
- if: github.ref == 'refs/heads/main'
  run: echo "Only on main"
- if: failure()
  run: echo "Previous step failed"

# Matrix strategy
strategy:
  matrix:
    node: [18, 20]
    os: [ubuntu-latest, macos-latest]
runs-on: ${{ matrix.os }}

# Job dependencies
jobs:
  test: ...
  deploy:
    needs: test
    if: success()
```

---

## 21.7 Networking Quick Reference

### curl Flags
```bash
curl -v                     # Verbose (request + response headers)
curl -I                     # HEAD request (headers only)
curl -L                     # Follow redirects
curl -s                     # Silent (no progress)
curl -o /dev/null           # Discard body
curl -w "%{http_code}"      # Print status code
curl -X POST                # Method
curl -d '{"key":"val"}'     # Request body
curl -H "Authorization: Bearer TOKEN"  # Header
curl --connect-timeout 5    # Connection timeout (seconds)
curl --max-time 30          # Total timeout
curl -k                     # Skip TLS verification (development only)
curl --cert client.pem      # Client certificate
curl -u user:pass           # Basic auth
```

### netcat (nc)
```bash
nc -zv hostname 5432            # Test TCP port
nc -zv hostname 5432-5440       # Test port range
nc -l 8080                      # Listen on port 8080
echo "ping" | nc hostname 8080  # Send data
nc -u hostname 53               # UDP mode
```

### openssl
```bash
openssl s_client -connect api.example.com:443    # TLS handshake info
openssl x509 -in cert.pem -text -noout          # Decode certificate
openssl x509 -in cert.pem -enddate -noout        # Certificate expiry
openssl req -newkey rsa:2048 -keyout key.pem -out csr.pem  # Generate CSR
openssl verify -CAfile ca.pem cert.pem           # Verify cert chain
```

### iptables
```bash
iptables -L -n -v                               # List all rules
iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # Allow port 443
iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT       # Allow CIDR
iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT # Insert at position 1
iptables -D INPUT 2                              # Delete rule 2
iptables -F                                      # Flush all rules (danger!)
iptables-save > /etc/iptables.rules              # Persist rules
iptables-restore < /etc/iptables.rules           # Restore rules
```

---

## 21.8 CI/CD Concepts Glossary

| Term | Definition |
|------|-----------|
| Continuous Integration | Automatically build and test every code commit |
| Continuous Delivery | Every commit is deployable; deployment is a manual decision |
| Continuous Deployment | Every passing commit is automatically deployed to production |
| Artifact | Build output stored in a registry (Docker image, JAR, npm package) |
| Pipeline | Automated sequence of stages (build → test → deploy) |
| Gate | Manual approval or automated check that must pass before next stage |
| Canary | Gradual traffic shift to new version (1% → 10% → 100%) |
| Blue/Green | Two identical environments; switch DNS/LB to swap versions instantly |
| Rolling Update | Replace pods one by one with new version |
| Feature Flag | Toggle features at runtime without deploying new code |
| DORA Metrics | Deployment Frequency, Lead Time, Change Failure Rate, MTTR |
| MTTR | Mean Time To Restore — how quickly you recover from failures |
| MTTD | Mean Time To Detect — how quickly you discover problems |
| Idempotent Deploy | Running the same deploy twice produces the same result |
| GitOps | Git is the single source of truth; deployments driven by git state |
| ArgoCD | GitOps controller: reconciles cluster state to match Git |
| Helm Release | A deployed instance of a Helm chart in a cluster |
| Revision | A numbered version of a Helm release (used for rollbacks) |
| immutable infrastructure | Never patch running servers; replace with new image |
| Drift | Difference between actual infrastructure and IaC definition |
| Blast Radius | How many users/services are affected if a change goes wrong |
| Rollback | Reverting to a previous known-good version |
| Smoke Test | Minimal post-deployment verification that critical paths work |
| SLO | Service Level Objective — internal reliability target (99.9% uptime) |
| SLA | Service Level Agreement — contractual commitment to customers |
| SLI | Service Level Indicator — measurable metric (request success rate) |
| Error Budget | Allowed downtime/failures before SLO is violated |
| Toil | Manual, repetitive operational work that should be automated |

---

## 21.9 Kubernetes Object Reference

| Object | Purpose | Key Fields |
|--------|---------|-----------|
| Pod | Smallest deployable unit | containers, volumes, restartPolicy |
| Deployment | Manages ReplicaSets for stateless apps | replicas, selector, template, strategy |
| StatefulSet | Ordered pods with stable network identity | serviceName, volumeClaimTemplates |
| DaemonSet | One pod per node (logging, monitoring agents) | selector, template |
| Job | Run to completion | completions, parallelism, backoffLimit |
| CronJob | Scheduled jobs | schedule (cron syntax), jobTemplate |
| Service | Stable network endpoint for pods | type (ClusterIP/NodePort/LoadBalancer), selector, ports |
| Ingress | HTTP/HTTPS routing to Services | rules (host/path), tls, annotations |
| ConfigMap | Non-secret configuration | data (key-value or file content) |
| Secret | Sensitive configuration | data (base64 encoded), type |
| PersistentVolume | Cluster storage resource | capacity, accessModes, storageClassName |
| PersistentVolumeClaim | Request for storage | resources.requests.storage, storageClassName |
| HorizontalPodAutoscaler | Auto-scale deployment based on metrics | minReplicas, maxReplicas, metrics |
| ServiceAccount | Identity for pods to call K8s API | automountServiceAccountToken |
| ClusterRole | Cluster-wide permissions | rules (apiGroups, resources, verbs) |
| ClusterRoleBinding | Bind ClusterRole to user/SA | subjects, roleRef |
| Namespace | Virtual cluster isolation | name, labels |
| ResourceQuota | Limit resource consumption in namespace | hard (pods, requests.cpu, limits.memory) |
| NetworkPolicy | Firewall rules between pods | podSelector, ingress/egress rules |
| PodDisruptionBudget | Minimum available pods during disruptions | minAvailable or maxUnavailable |

---

## 21.10 Production Debugging Quick Reference

```bash
# Application is slow
1. kubectl top pods → check CPU/memory saturation
2. kubectl describe pod → check events (OOMKills, restarts)
3. Check database: SELECT * FROM pg_stat_activity WHERE state='active';
4. Check slow queries: SELECT query, total_time FROM pg_stat_statements ORDER BY total_time DESC;
5. Check external HTTP calls: grep "external_request" app.log | jq .duration | sort -n | tail

# Pod won't start
1. kubectl get events --sort-by=.lastTimestamp
2. kubectl describe pod <pod-name> → look at Events section
3. kubectl logs <pod-name> --previous → logs from crashed container
4. Image pull failure? Check: kubectl get secret regcred
5. OOMKilled? Increase memory limit in deployment

# Service unreachable
1. kubectl get endpoints <service-name> → are pods selected?
2. kubectl exec debug -- curl http://<service-name>.<namespace>.svc.cluster.local
3. Check NetworkPolicy: kubectl get networkpolicy
4. Check Ingress: kubectl describe ingress <name>
5. Check TLS cert: kubectl describe certificate <name>

# Database connection failures
1. Test from pod: kubectl exec -it app -- nc -zv db-service 5432
2. Check pool exhaustion: SELECT count(*) FROM pg_stat_activity;
3. Check locks: SELECT * FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid;
4. Check password: kubectl get secret db-creds -o jsonpath='{.data.password}' | base64 -d

# High error rate
1. Prometheus query: rate(http_requests_total{status=~"5.."}[5m])
2. Check logs: kubectl logs deployment/app | grep -i error | tail -50
3. Recent deployment? kubectl rollout history deployment/app
4. Roll back: kubectl rollout undo deployment/app
```
