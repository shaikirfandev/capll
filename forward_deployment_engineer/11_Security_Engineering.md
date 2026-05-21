# Section 11 — Security Engineering

## 11.1 OWASP Top 10 (FDE Perspective)

Every FDE deploys software into enterprise customer environments. You own the security posture of that deployment. Know every OWASP Top 10 category and its fix.

### A01 — Broken Access Control
```
Attack: User A accesses User B's data by changing an ID in the URL
  GET /api/deployments/12345  →  GET /api/deployments/12346

Fix: Always enforce ownership/permission checks in the backend
```
```typescript
// WRONG — trusts client-provided ID
app.get("/api/deployments/:id", async (req, res) => {
    const deployment = await db.findById(req.params.id);
    res.json(deployment);
});

// CORRECT — verifies caller owns the resource
app.get("/api/deployments/:id", requireAuth, async (req, res) => {
    const deployment = await db.findById(req.params.id);
    if (!deployment) return res.status(404).json({ error: "Not found" });
    
    // Authorization check
    if (deployment.tenantId !== req.user.tenantId) {
        return res.status(403).json({ error: "Access denied" });
    }
    res.json(deployment);
});
```

### A02 — Cryptographic Failures
```
Violations:
  ❌ Storing passwords in plaintext or MD5
  ❌ Sensitive data in URLs (logged by proxies/servers)
  ❌ HTTP instead of HTTPS
  ❌ Weak TLS (TLS 1.0/1.1, weak cipher suites)

Fixes:
  ✅ bcrypt/argon2 for passwords (never MD5/SHA1)
  ✅ TLS 1.2+ with ECDHE ciphers
  ✅ Secrets in environment variables / Vault / AWS Secrets Manager
  ✅ Encrypt sensitive DB columns at rest (pgcrypto, application-level AES)
```

```python
# Correct password hashing
import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    # bcrypt.checkpw is timing-safe — no timing attacks
```

### A03 — Injection (SQL, Command, LDAP)
```typescript
// SQL injection — WRONG
const query = `SELECT * FROM users WHERE email = '${req.body.email}'`;
// Attacker sends: email = "'; DROP TABLE users; --"

// CORRECT — parameterised queries always
const user = await db.query(
    "SELECT * FROM users WHERE email = $1",
    [req.body.email]  // Parameter binding — safe from injection
);

// Command injection — WRONG
exec(`ping ${req.query.host}`);  // host = "8.8.8.8; rm -rf /data"

// CORRECT — never pass user input to shell
const host = req.query.host;
if (!/^[\w.-]+$/.test(host)) return res.status(400).json({ error: "Invalid host" });
execFile("ping", ["-c", "1", host]); // Array args — no shell interpolation
```

### A04 — Insecure Design
```
FDE Checklist:
  □ Threat modelled the deployment before coding
  □ Authentication required on ALL endpoints (no accidental public routes)
  □ Sensitive operations require re-authentication or MFA
  □ Rate limiting on auth endpoints (prevent brute force)
  □ Account lockout after N failed attempts
```

### A05 — Security Misconfiguration
```
Common FDE misconfiguration incidents:
  ❌ S3 bucket left public
  ❌ Debug endpoints exposed in production (/debug, /_profiler, /swagger)
  ❌ Default admin credentials not changed
  ❌ Verbose error messages exposing stack traces to users
  ❌ CORS set to * in production

Fixes:
  ✅ Infrastructure-as-Code with policy checks (terraform + checkov)
  ✅ Disable debug routes in production environments
  ✅ Generic error messages to users, detailed errors to logs only
  ✅ CORS whitelist specific domains
```

```typescript
// WRONG — expose stack traces to client
app.use((err: Error, req: Request, res: Response) => {
    res.status(500).json({ error: err.message, stack: err.stack });
});

// CORRECT — sanitise errors
app.use((err: Error, req: Request, res: Response) => {
    req.log.error("Unhandled error", { error: err.message, stack: err.stack });
    
    if (err instanceof ValidationError) {
        return res.status(422).json({ error: err.message, fields: err.fields });
    }
    // Never expose internal error details
    res.status(500).json({ error: "Internal server error", request_id: req.id });
});
```

### A06 — Vulnerable and Outdated Components
```bash
# Audit dependencies for known CVEs
npm audit
npm audit --audit-level=moderate

# Python
pip-audit
safety check

# Container image scanning
trivy image myapp:2.1.0
grype myapp:2.1.0

# Set up automated scanning in CI
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: '${{ env.IMAGE }}'
    severity: 'CRITICAL,HIGH'
    exit-code: '1'  # Fail CI on critical/high CVEs
```

### A07 — Authentication and Identification Failures
```typescript
// JWT best practices
import { sign, verify } from "jsonwebtoken";

const ACCESS_TOKEN_EXPIRY  = "15m";   // Short-lived — 15 minutes
const REFRESH_TOKEN_EXPIRY = "7d";    // Longer-lived

function issueTokenPair(userId: string, tenantId: string) {
    const accessToken = sign(
        { sub: userId, tenantId, type: "access" },
        process.env.JWT_SECRET!,
        { expiresIn: ACCESS_TOKEN_EXPIRY, algorithm: "HS256" }
    );
    
    const refreshToken = sign(
        { sub: userId, tenantId, type: "refresh", jti: crypto.randomUUID() },
        process.env.JWT_REFRESH_SECRET!,
        { expiresIn: REFRESH_TOKEN_EXPIRY, algorithm: "HS256" }
    );
    
    // Store refresh token hash in DB (for revocation)
    await storeRefreshTokenHash(userId, hashToken(refreshToken));
    
    return { accessToken, refreshToken };
}
```

### A08 — Software and Data Integrity Failures
```bash
# Verify container image signatures (Cosign)
cosign sign --key cosign.key myregistry/myapp:2.1.0
cosign verify --key cosign.pub myregistry/myapp:2.1.0

# Verify Helm chart integrity
helm pull myrepo/myapp --verify

# GitHub Actions: pin actions to SHA (not tag — tags can be changed)
# WRONG:
uses: actions/checkout@v4
# CORRECT:
uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

### A09 — Security Logging and Monitoring Failures
```typescript
// Log all security-relevant events with sufficient detail
function logSecurityEvent(event: SecurityEvent): void {
    auditLogger.info("security_event", {
        event_type:  event.type,         // "login", "login_failed", "permission_denied"
        user_id:     event.userId,
        tenant_id:   event.tenantId,
        ip_address:  event.ipAddress,
        user_agent:  event.userAgent,
        resource:    event.resource,     // What was accessed/attempted
        outcome:     event.outcome,      // "success" | "failure"
        timestamp:   new Date().toISOString(),
        request_id:  event.requestId,
    });
}

// Alert on suspicious patterns
// - >5 failed logins in 5 minutes from same IP
// - Login from new country for existing user
// - Excessive API calls (>10x normal rate)
// - Access to admin endpoints by non-admin user
```

### A10 — Server-Side Request Forgery (SSRF)
```
Attack: Attacker tricks server into making requests to internal services
  POST /api/fetch-url
  { "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/" }
  (AWS instance metadata endpoint → steal IAM credentials)

Fix: Validate and restrict URLs
```
```typescript
import { URL } from "url";
import dns from "dns/promises";
import ipRangeCheck from "ip-range-check";

const BLOCKED_RANGES = [
    "10.0.0.0/8",       // Private
    "172.16.0.0/12",    // Private
    "192.168.0.0/16",   // Private
    "127.0.0.0/8",      // Loopback
    "169.254.0.0/16",   // Link-local (AWS metadata)
    "::1/128",          // IPv6 loopback
];

async function validateSafeUrl(rawUrl: string): Promise<string> {
    let parsed: URL;
    try {
        parsed = new URL(rawUrl);
    } catch {
        throw new ValidationError("Invalid URL format");
    }
    
    if (!["http:", "https:"].includes(parsed.protocol)) {
        throw new ValidationError("Only HTTP(S) URLs allowed");
    }
    
    // Resolve hostname and check IP
    const addresses = await dns.lookup(parsed.hostname, { all: true });
    for (const { address } of addresses) {
        if (ipRangeCheck(address, BLOCKED_RANGES)) {
            throw new ValidationError("URL resolves to private network address");
        }
    }
    
    return parsed.toString();
}
```

---

## 11.2 RBAC — Role-Based Access Control

```typescript
// RBAC implementation for multi-tenant FDE platform
const PERMISSIONS = {
    "deployments:read":   "View deployments",
    "deployments:create": "Create deployments",
    "deployments:delete": "Delete deployments",
    "admin:users:manage": "Manage users",
    "admin:settings":     "Modify platform settings",
} as const;

type Permission = keyof typeof PERMISSIONS;

const ROLES: Record<string, Permission[]> = {
    "viewer":  ["deployments:read"],
    "editor":  ["deployments:read", "deployments:create"],
    "operator":["deployments:read", "deployments:create", "deployments:delete"],
    "admin":   Object.keys(PERMISSIONS) as Permission[],
};

function requirePermission(permission: Permission) {
    return (req: Request, res: Response, next: NextFunction) => {
        const userRoles = req.user.roles as string[];
        const userPermissions = userRoles.flatMap(r => ROLES[r] ?? []);
        
        if (!userPermissions.includes(permission)) {
            log.warn("permission_denied", {
                user_id:    req.user.id,
                permission,
                user_roles: userRoles,
            });
            return res.status(403).json({ error: "Insufficient permissions" });
        }
        next();
    };
}

// Usage
app.post("/deployments",
    requireAuth,
    requirePermission("deployments:create"),
    createDeploymentHandler
);
```

---

## 11.3 Secrets Management

```bash
# AWS Secrets Manager — production standard
# Store secret
aws secretsmanager create-secret \
    --name "myapp/production/db-password" \
    --secret-string "$(openssl rand -base64 32)"

# Rotate secret (automated rotation)
aws secretsmanager rotate-secret \
    --secret-id "myapp/production/db-password" \
    --rotation-lambda-arn arn:aws:lambda:us-east-1:123:function:rotation

# In application — fetch at startup, not hardcoded
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]

DB_PASSWORD = get_secret("myapp/production/db-password")

# HashiCorp Vault — common in on-prem enterprise deployments
vault kv put secret/myapp/db password=supersecret
vault kv get -field=password secret/myapp/db

# Kubernetes secrets (base64 encoded — NOT encrypted by default!)
kubectl create secret generic myapp-secrets \
    --from-literal=db_password="$(openssl rand -base64 32)" \
    --namespace myapp-production

# Enable envelope encryption for Kubernetes secrets with KMS
# aws-encryption-provider or azure Key Vault CSI driver
```

---

## 11.4 TLS Certificate Automation

```bash
# Let's Encrypt with cert-manager on Kubernetes
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# ClusterIssuer — ACME via DNS challenge (no public port 80 required)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@mycompany.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - dns01:
          route53:
            region: us-east-1
            hostedZoneID: Z1234567890
EOF

# Ingress — cert-manager auto-provisions cert
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts: [api.myapp.com]
      secretName: myapp-tls
  rules:
    - host: api.myapp.com
      ...
```
