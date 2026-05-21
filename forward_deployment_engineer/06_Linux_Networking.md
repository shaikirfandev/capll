# Section 06 — Linux Administration & Networking

## 6.1 Linux Administration

Every FDE lives in the Linux command line. You will SSH into customer servers, debug running processes, investigate disk issues, and manage services.

### Essential Commands (Production Context)

```bash
# --- PROCESS MANAGEMENT ---
ps aux | sort -k3 -rn | head -20          # Top CPU consumers
ps aux | sort -k4 -rn | head -20          # Top memory consumers
top -b -n1 | head -30                     # One-shot top output
htop                                       # Interactive (if installed)

# Find and kill process
lsof -i :8080                             # What's using port 8080?
kill -15 <pid>                            # Graceful shutdown (SIGTERM)
kill -9  <pid>                            # Force kill (SIGKILL) — last resort

# --- FILE SYSTEM ---
df -h                                     # Disk usage per mount point
du -sh /var/log/* | sort -rh | head -20  # Largest log directories
du -sh /proc/*/fd 2>/dev/null | sort -rh # Open file descriptors per process

# Find large files (>100MB) modified in last 7 days
find / -type f -size +100M -mtime -7 -not -path "/proc/*" 2>/dev/null

# --- LOGS (most important FDE skill) ---
journalctl -u myapp.service -n 100 --no-pager       # systemd service logs
journalctl -u myapp.service -f                       # Follow live
journalctl -u myapp.service --since "1 hour ago"     # Time-bounded
journalctl --disk-usage                              # How much journal disk?
journalctl --vacuum-time=7d                          # Clean logs > 7 days

tail -f /var/log/nginx/access.log                    # Live nginx logs
grep "ERROR" /var/log/app/app.log | tail -100        # Last 100 errors

# --- NETWORK ---
ss -tlnp                                 # TCP listening sockets + process
ss -s                                    # Socket statistics
netstat -an | grep ESTABLISHED | wc -l  # Active connections count
ip addr show                            # IP addresses
ip route show                           # Routing table
curl -v -o /dev/null https://api.example.com  # Verbose HTTP request trace
```

### systemd Service Management
```bash
# Service lifecycle
systemctl start   myapp
systemctl stop    myapp
systemctl restart myapp
systemctl reload  myapp      # Reload config without restart (if supported)
systemctl enable  myapp      # Auto-start on boot
systemctl disable myapp

# Status and diagnostics
systemctl status  myapp -l   # Detailed status with recent logs
systemctl cat     myapp      # Show service unit file

# Create a systemd service (common for FDE-deployed services)
cat > /etc/systemd/system/myapp.service << 'EOF'
[Unit]
Description=My Application Service
After=network.target postgresql.service
Requires=network.target

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
EnvironmentFile=/etc/myapp/environment
ExecStart=/opt/myapp/bin/myapp serve --config /etc/myapp/config.yaml
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/myapp /var/log/myapp

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now myapp
```

---

## 6.2 Shell Scripting for FDE Operations

### Text Processing (Critical for Log Analysis)
```bash
# Parse nginx access log — extract slowest requests
# Log format: 127.0.0.1 - - [15/Nov/2024:10:23:45 +0000] "GET /api/deployments HTTP/1.1" 200 1234 "-" "-" "0.543"
# Last field = response time in seconds

awk '{print $NF, $7}' /var/log/nginx/access.log | \
    sort -k1 -rn | \
    head -20

# Count errors by status code in last hour
awk -v cutoff="$(date -d '1 hour ago' +'%d/%b/%Y:%H:%M:%S')" \
    '$4 > "["cutoff {print $9}' /var/log/nginx/access.log | \
    sort | uniq -c | sort -rn

# Find IP addresses making most requests
awk '{print $1}' /var/log/nginx/access.log | \
    sort | uniq -c | sort -rn | head -20

# Extract JSON log fields with jq
cat /var/log/app/app.log | \
    jq -r 'select(.level == "error") | [.timestamp, .message, .error] | @tsv' | \
    sort | tail -50

# Monitor log file for errors and alert
tail -F /var/log/app/app.log | while read -r line; do
    if echo "$line" | grep -qE '"level":"error"|"level":"fatal"'; then
        echo "$(date): ALERT - $(echo "$line" | jq -r '.message')" | \
            tee -a /var/log/alert.log
        # curl -X POST "$SLACK_WEBHOOK" -d "{\"text\":\"ERROR: $(echo "$line" | jq -r '.message')\"}"
    fi
done
```

---

## 6.3 Nginx Configuration

Nginx is the most common web server/reverse proxy in FDE deployments.

```nginx
# Production nginx config — complete template

user  nginx;
worker_processes  auto;   # One per CPU core

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;

events {
    worker_connections  4096;    # Connections per worker
    use epoll;                   # Efficient on Linux
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format json_combined escape=json
        '{"time":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"method":"$request_method",'
        '"uri":"$uri",'
        '"status":$status,'
        '"bytes_sent":$bytes_sent,'
        '"request_time":$request_time,'
        '"upstream_time":"$upstream_response_time",'
        '"user_agent":"$http_user_agent"}';
    
    access_log /var/log/nginx/access.log json_combined;
    
    # Performance
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout 65;
    client_max_body_size 10m;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    
    # Rate limiting zones
    limit_req_zone $binary_remote_addr zone=global:10m rate=60r/m;
    
    # Upstream backend
    upstream app_backend {
        least_conn;
        server app-1:3000;
        server app-2:3000;
        server app-3:3000;
        keepalive 16;
    }
    
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name myapp.example.com;
        
        ssl_certificate     /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 10m;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header Content-Security-Policy "default-src 'self'" always;
        
        location / {
            limit_req zone=global burst=30 nodelay;
            
            proxy_pass http://app_backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_set_header Host              $host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout  5s;
            proxy_send_timeout     60s;
            proxy_read_timeout     60s;
            
            # Buffer settings
            proxy_buffer_size       4k;
            proxy_buffers          16 4k;
        }
        
        location /health {
            access_log off;
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## 6.4 DNS

FDEs configure DNS for every customer deployment.

```bash
# DNS lookup tools
dig api.example.com              # Full DNS resolution trace
dig api.example.com +short       # Just the IP
dig api.example.com MX           # Mail records
dig api.example.com TXT          # TXT records (SPF, DKIM, verification)
dig @8.8.8.8 api.example.com    # Query specific DNS server
nslookup api.example.com         # Windows-compatible alternative

# Reverse lookup (IP → hostname)
dig -x 192.168.1.1

# Check DNS propagation globally
# Use: https://dnschecker.org
```

### Common DNS Record Types
| Type | Purpose | FDE Use Case |
|------|---------|-------------|
| A | hostname → IPv4 | Point domain to server IP |
| AAAA | hostname → IPv6 | IPv6 endpoint |
| CNAME | alias → hostname | `api` → load balancer hostname |
| MX | mail exchange | Email routing |
| TXT | arbitrary text | SSO verification, SPF, DKIM |
| NS | name server | Delegation |
| SRV | service location | gRPC service discovery |
| PTR | reverse DNS | IP → hostname |

### Common DNS Issues FDEs Diagnose
```
Issue: SSO not working after config change
Check: TXT record for SAML/OIDC verification token present?

Issue: App unreachable after deployment
Check: A record pointing to new IP? TTL expired?
  dig +trace api.myapp.com  →  shows full resolution path

Issue: SSL certificate error after domain change
Check: Does cert's CN/SAN match the new hostname?
  openssl s_client -connect api.myapp.com:443 | openssl x509 -noout -subject -dates

Issue: Emails going to spam after migration
Check: SPF/DKIM/DMARC TXT records configured for new mail server?
```

---

## 6.5 HTTP/HTTPS Deep Dive

### HTTP Status Codes (FDE Production Diagnostic Reference)
```
1xx — Informational
  100 Continue: Client should send body
  101 Switching Protocols: WebSocket upgrade

2xx — Success
  200 OK
  201 Created
  204 No Content

3xx — Redirect
  301 Moved Permanently: Update bookmarks/links
  302 Found: Temporary redirect
  304 Not Modified: Client cache valid (ETag match)

4xx — Client Error (customer's request is wrong)
  400 Bad Request:   Malformed input — log the request body
  401 Unauthorized:  Token missing/expired — check auth
  403 Forbidden:     Authenticated but no permission — check RBAC
  404 Not Found:     Resource missing — or route not configured
  409 Conflict:      Race condition (duplicate create)
  422 Unprocessable: Validation failed
  429 Too Many Req:  Rate limited — check headers for retry-after

5xx — Server Error (your problem)
  500 Internal Server Error: Uncaught exception — check logs immediately
  502 Bad Gateway:           Upstream app not responding — is the app running?
  503 Service Unavailable:   App overloaded/maintenance — check resources
  504 Gateway Timeout:       Upstream too slow — check DB/external calls
```

### TLS Certificate Management
```bash
# Check certificate expiry (critical for FDE — expired certs = production outage)
openssl s_client -connect api.example.com:443 -servername api.example.com 2>/dev/null | \
    openssl x509 -noout -dates

# Check all certs in a bundle
openssl x509 -in /etc/ssl/certs/myapp.crt -noout -text | grep -E "Subject:|Not After"

# Generate CSR for customer-provided cert
openssl req -new -newkey rsa:2048 -nodes \
    -keyout server.key \
    -out server.csr \
    -subj "/C=US/ST=California/L=San Francisco/O=Acme Corp/CN=api.acme.com"

# Verify cert matches private key
openssl x509 -noout -modulus -in server.crt | openssl md5
openssl rsa  -noout -modulus -in server.key | openssl md5
# These must match — if not, cert/key mismatch = HTTPS broken

# Test with Let's Encrypt
certbot certonly --nginx -d api.example.com -d www.example.com
```

---

## 6.6 TCP/IP & Network Debugging

```bash
# --- CONNECTIVITY DEBUGGING ---
ping -c 4 192.168.1.1                    # Basic connectivity
traceroute api.example.com              # Path to destination
mtr --report api.example.com            # Continuous traceroute with stats

# Port connectivity
nc -zv api.example.com 443              # Is port 443 open?
nc -zv db-server.internal 5432          # Can I reach the database port?

# Capture packets (essential for deep debugging)
tcpdump -i eth0 -nn port 80             # Capture HTTP traffic
tcpdump -i eth0 -nn host 10.0.1.50     # Traffic to/from specific host
tcpdump -i eth0 -nn port 5432 -w /tmp/db.pcap  # Save to file for Wireshark

# --- BANDWIDTH & LATENCY ---
iperf3 -s                               # Start server mode
iperf3 -c server-ip -t 10              # Test bandwidth for 10 seconds
iperf3 -c server-ip -u -b 100M        # UDP bandwidth test

# --- FIREWALL (iptables / nftables) ---
iptables -L -n -v                       # List all rules
iptables -L INPUT -n -v | grep DROP    # See what's being dropped

# Common firewall — allow specific port from specific subnet
iptables -A INPUT -p tcp --dport 5432 -s 10.0.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 5432 -j DROP  # Block from everywhere else
```

### Load Balancing

```
Load Balancing Algorithms:

Round Robin:
  Request 1 → Server A
  Request 2 → Server B
  Request 3 → Server C
  Request 4 → Server A  (repeat)
  Use: Uniform, stateless requests

Least Connections:
  New request → Server with fewest active connections
  Use: Requests with variable processing time

IP Hash:
  hash(client_IP) % num_servers = server index
  Same client always hits same server
  Use: Session affinity (sticky sessions)

Weighted:
  Server A weight=3, Server B weight=1
  Server A gets 75% of traffic
  Use: Heterogeneous server sizes

Health Check + Passive Failover:
  Load balancer pings /health every 10s
  Server with 3 consecutive failures → removed from pool
  Automatically re-added when health check passes
```
