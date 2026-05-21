# Section 02 — Software Development Foundations

## 2.1 Data Structures & Algorithms (FDE Context)

An FDE needs DSA not for competitive programming, but for writing performant integration code, optimising data pipelines, and diagnosing algorithmic complexity in production systems.

### Data Structures You Use Daily as an FDE

| Structure | Where You Use It in Production |
|-----------|-------------------------------|
| Hash Map | Cache lookups, config stores, deduplication |
| Sorted Set | Leaderboards, priority queues, time-window rate limiting |
| Trie | Autocomplete, IP prefix routing |
| B-Tree | Database indexes (PostgreSQL, MySQL) |
| Graph | Service dependency mapping, infrastructure topology |
| Ring Buffer | Log streams, Kafka consumer offsets |
| Bloom Filter | Probabilistic deduplication (cache miss reduction) |
| Heap | Priority-based job scheduling, top-N queries |

### Complexity Reference (Production Relevance)

```
O(1)   → Hash lookup, array index access, Redis GET
O(log n) → Binary search, B-tree index lookup (DB query with index)
O(n)   → Linear scan (table scan without index — FIX THIS)
O(n log n) → Sorting a result set (ORDER BY on unindexed column)
O(n²)  → Nested loops — never acceptable in production data paths
```

**Rule:** If a production data path has > 10,000 records flowing through it, every O(n²) operation is a production incident waiting to happen.

---

## 2.2 System Design Fundamentals

### The 5-Step System Design Framework (FDE Interview Standard)

```
Step 1: CLARIFY REQUIREMENTS (5 min)
  ├─ Functional requirements (what it must do)
  └─ Non-functional: QPS, latency SLO, availability, data volume

Step 2: CAPACITY ESTIMATION (5 min)
  ├─ Reads/writes per second
  ├─ Storage needed (3 years)
  └─ Bandwidth requirements

Step 3: HIGH-LEVEL ARCHITECTURE (10 min)
  ├─ Draw components: clients, load balancers, app servers, DBs, caches
  └─ Show data flow arrows

Step 4: DEEP DIVE (15 min)
  ├─ Database schema design
  ├─ API design
  ├─ Caching strategy
  └─ Bottleneck identification

Step 5: SCALABILITY & FAILURE (5 min)
  ├─ Single points of failure
  ├─ Horizontal scaling strategy
  └─ Monitoring and alerting
```

### Numbers Every FDE Must Know
```
Latency Reference:
  L1 cache access:     0.5 ns
  L2 cache access:     7 ns
  RAM access:          100 ns
  SSD sequential read: 150 µs
  HDD sequential read: 1 ms
  Network round trip (same DC): 0.5 ms
  Network round trip (cross-continent): 150 ms
  DNS lookup:          10-100 ms

Throughput Reference:
  Single PostgreSQL node:    ~10,000 TPS (simple queries)
  Redis:                     ~100,000 ops/sec
  Kafka:                     ~1,000,000 msgs/sec (single partition)
  HTTP server (nginx):       ~50,000 req/sec (static)
  HTTP server (Node.js app): ~5,000-20,000 req/sec
```

---

## 2.3 Object-Oriented Programming

### The 4 OOP Pillars (Applied to FDE Work)

**Encapsulation**
```python
# Bad: Exposed internals
class DatabaseConnection:
    host = "prod-db.internal"
    password = "secret123"
    
# Good: Encapsulated with controlled access
class DatabaseConnection:
    def __init__(self):
        self._host = os.getenv("DB_HOST")      # Never hardcode
        self._password = os.getenv("DB_PASS")  # Read from secrets

    def connect(self) -> Connection:
        return psycopg2.connect(host=self._host, password=self._password)
```

**Inheritance + Composition**
```python
# Prefer composition over inheritance for FDE integrations
class BaseIntegration:
    def validate_config(self, config: dict) -> bool:
        raise NotImplementedError

class SlackIntegration(BaseIntegration):
    def __init__(self, notifier: Notifier, logger: Logger):
        self._notifier = notifier  # composition
        self._logger = logger      # composition
    
    def validate_config(self, config: dict) -> bool:
        return "webhook_url" in config and "channel" in config
```

---

## 2.4 Design Patterns (Most Used by FDEs)

### Creational Patterns

**Singleton — Config Manager**
```python
class ConfigManager:
    _instance = None
    
    @classmethod
    def get(cls) -> "ConfigManager":
        if not cls._instance:
            cls._instance = cls._load_config()
        return cls._instance
    
    @staticmethod
    def _load_config() -> "ConfigManager":
        # Load from env, Vault, or SSM
        ...
```

**Factory — Multi-Cloud Storage**
```python
def storage_factory(provider: str) -> StorageBackend:
    match provider:
        case "s3":    return S3Backend(os.getenv("AWS_BUCKET"))
        case "gcs":   return GCSBackend(os.getenv("GCS_BUCKET"))
        case "azure": return AzureBlob(os.getenv("AZURE_CONTAINER"))
        case _:       raise ValueError(f"Unknown provider: {provider}")
```

### Structural Patterns

**Adapter — Third-Party API Integration**
```python
# Customer uses their own UserService interface
# You need to adapt your platform's API to match

class CustomerUserServiceAdapter:
    def __init__(self, platform_api: PlatformAPI):
        self._api = platform_api
    
    # Customer expects this interface
    def get_user_by_email(self, email: str) -> CustomerUser:
        # Translate to platform API call
        raw = self._api.users.fetch(filter={"email": email})
        return CustomerUser(id=raw["id"], name=raw["display_name"])
```

**Decorator — Request Middleware / Retry Logic**
```python
import functools, time

def with_retry(max_attempts: int = 3, backoff: float = 1.0):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (ConnectionError, TimeoutError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(backoff * (2 ** attempt))  # Exponential backoff
        return wrapper
    return decorator

@with_retry(max_attempts=3, backoff=0.5)
def call_external_api(endpoint: str) -> dict:
    response = requests.get(endpoint, timeout=5)
    response.raise_for_status()
    return response.json()
```

### Behavioural Patterns

**Observer — Event-Driven Integration**
```python
class DeploymentEventBus:
    def __init__(self):
        self._handlers: dict[str, list] = {}
    
    def subscribe(self, event: str, handler: callable):
        self._handlers.setdefault(event, []).append(handler)
    
    def publish(self, event: str, payload: dict):
        for handler in self._handlers.get(event, []):
            handler(payload)

bus = DeploymentEventBus()
bus.subscribe("deployment.completed", send_slack_notification)
bus.subscribe("deployment.completed", update_status_page)
bus.subscribe("deployment.failed",    trigger_rollback)
```

**Circuit Breaker — Fault Isolation**
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failures = 0
        self.threshold = failure_threshold
        self.timeout = timeout
        self.state = "CLOSED"  # CLOSED=normal, OPEN=broken, HALF_OPEN=testing
        self.opened_at: float = 0
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.opened_at > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise RuntimeError("Circuit breaker OPEN — service unavailable")
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failures = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "OPEN"
            self.opened_at = time.time()
```

---

## 2.5 Clean Architecture

```
Clean Architecture Layers (Outermost → Innermost):

[Frameworks & Drivers]  → HTTP frameworks, databases, external APIs
        ↓ depends on
[Interface Adapters]    → Controllers, presenters, gateways
        ↓ depends on
[Application Use Cases] → Business logic orchestration
        ↓ depends on
[Domain Entities]       → Core business rules (no framework dependencies)
```

**FDE Rule:** Keep customer-specific integration code in the outermost layer only. Core business logic should never know about a specific customer's infrastructure.

---

## 2.6 API Design Principles

### REST API Best Practices

```
Resource naming:
  GET    /v1/deployments          → List all deployments
  GET    /v1/deployments/{id}     → Get specific deployment
  POST   /v1/deployments          → Create new deployment
  PATCH  /v1/deployments/{id}     → Update (partial)
  DELETE /v1/deployments/{id}     → Delete

Status codes:
  200 OK           → Success
  201 Created      → Resource created
  204 No Content   → Success, no body (DELETE)
  400 Bad Request  → Invalid input
  401 Unauthorized → Missing/invalid auth
  403 Forbidden    → Authenticated but no permission
  404 Not Found    → Resource doesn't exist
  409 Conflict     → Duplicate resource
  422 Unprocessable → Validation failed
  429 Too Many Requests → Rate limited
  500 Internal Server Error → Never expose stack traces
  503 Service Unavailable  → Maintenance / overload
```

### API Versioning Strategy
```
URL versioning:    /v1/users  →  /v2/users
Header versioning: Accept: application/vnd.api+json;version=2
Query param:       /users?version=2  (least preferred)
```

**FDE Rule:** Always version APIs before deploying to a customer. Breaking API changes without versioning have caused production incidents at every major company.

---

## 2.7 Software Development Lifecycle (SDLC) in FDE Context

```
Classical SDLC:
Requirements → Design → Development → Testing → Deployment → Maintenance

FDE Adapted SDLC:
Customer Discovery → Architecture Design → Integration Development →
Staging Validation → Production Deployment → Monitoring → Iteration
```

The key difference: in classical SDLC, "customers" are internal stakeholders. In FDE work, the customer is physically present or on the call during every phase.

---

## 2.8 Agile & Scrum in Customer Deployments

### How FDEs Adapt Agile

| Agile Concept | Standard Team | FDE Adaptation |
|--------------|--------------|----------------|
| Sprint | 2-week internal | 1-week customer-facing delivery cycles |
| Backlog | Product manager owns | Co-owned with customer technical lead |
| Stand-up | Internal team | May include customer engineers |
| Definition of Done | PR merged + tests pass | Deployed + customer acceptance sign-off |
| Retrospective | Internal | Joint retrospective with customer after go-live |
| Sprint goal | Feature release | Deployment milestone (staging, prod, UAT) |

### Ticket Writing for FDE Deployments
```
Title: [CUSTOMER-ABC] Configure SAML SSO with Okta tenant

Description:
  Customer: Acme Corp
  Environment: Production (AWS us-east-1)
  
  Context:
    Customer requires SSO via Okta before production go-live.
    Their Okta admin is available Thursday for joint configuration session.
  
  Acceptance Criteria:
    □ SAML metadata imported from Okta
    □ Test user can log in via SSO flow
    □ Role mapping configured (admin → platform-admin group)
    □ Session timeout = 8 hours per customer security policy
  
  Dependencies:
    - Customer Okta admin provides metadata URL
    - Platform SSO module v2.3+ deployed (ticket INFRA-445)
  
  Estimate: 3 hours
  Owner: [FDE engineer name]
```
