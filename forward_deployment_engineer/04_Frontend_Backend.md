# Section 04 — Frontend, Backend & API Engineering

## 4.1 React — Production-Grade Frontend

FDEs often need to build internal dashboards, customer-facing configuration UIs, and integration management consoles.

### Component Architecture
```jsx
// Production React: separation of concerns
// File: components/DeploymentStatus/index.tsx

import { useReducer, useEffect, useCallback } from "react";

// State management with useReducer (better than useState for complex state)
type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; deployments: Deployment[] }
  | { status: "error"; message: string };

type Action =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: Deployment[] }
  | { type: "FETCH_ERROR"; message: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "FETCH_START":   return { status: "loading" };
    case "FETCH_SUCCESS": return { status: "success", deployments: action.payload };
    case "FETCH_ERROR":   return { status: "error", message: action.message };
    default: return state;
  }
}

// Custom hook — encapsulates data fetching logic
function useDeployments(environmentId: string) {
  const [state, dispatch] = useReducer(reducer, { status: "idle" });
  
  const refresh = useCallback(async () => {
    dispatch({ type: "FETCH_START" });
    try {
      const data = await fetchDeployments(environmentId);
      dispatch({ type: "FETCH_SUCCESS", payload: data });
    } catch (err) {
      dispatch({ type: "FETCH_ERROR", message: err.message });
    }
  }, [environmentId]);
  
  useEffect(() => { refresh(); }, [refresh]);
  
  return { state, refresh };
}

// Component is now pure rendering logic
export function DeploymentStatus({ environmentId }: { environmentId: string }) {
  const { state, refresh } = useDeployments(environmentId);
  
  if (state.status === "loading") return <Spinner />;
  if (state.status === "error")   return <ErrorBanner message={state.message} onRetry={refresh} />;
  if (state.status === "idle")    return null;
  
  return (
    <div className="deployment-grid">
      {state.deployments.map(d => (
        <DeploymentCard key={d.id} deployment={d} />
      ))}
    </div>
  );
}
```

### React Query (TanStack Query) — Standard for FDE Dashboards
```tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

function useDeployments(envId: string) {
  return useQuery({
    queryKey: ["deployments", envId],
    queryFn: () => api.getDeployments(envId),
    staleTime: 30_000,       // Cache for 30s
    refetchInterval: 60_000, // Poll every 60s
  });
}

function useCreateDeployment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createDeployment,
    onSuccess: (_, vars) => {
      // Invalidate cache so list refreshes
      queryClient.invalidateQueries({ queryKey: ["deployments", vars.envId] });
    },
  });
}
```

---

## 4.2 Next.js — Full-Stack FDE Applications

Next.js is the standard for FDE-built portals and internal tools at companies like Vercel, Stripe, and Linear.

```typescript
// app/api/deployments/route.ts — Server-side API route
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { getServerSession } from "next-auth";

const CreateDeploymentSchema = z.object({
  name:        z.string().min(1),
  environment: z.enum(["staging", "production"]),
  version:     z.string().regex(/^v\d+\.\d+\.\d+$/),
});

export async function POST(req: NextRequest) {
  // Auth check
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  
  // Input validation
  const body = await req.json();
  const result = CreateDeploymentSchema.safeParse(body);
  if (!result.success) {
    return NextResponse.json({ error: result.error.flatten() }, { status: 422 });
  }
  
  const deployment = await deploymentService.create({
    ...result.data,
    createdBy: session.user.email,
  });
  
  return NextResponse.json(deployment, { status: 201 });
}
```

---

## 4.3 REST API Design & Implementation

### Designing APIs for Enterprise Customers

```
Principles for FDE API Design:
1. Predictability — consistent naming, consistent error format
2. Versioning — always from day 1
3. Pagination — never return unbounded lists
4. Filtering — customers need to query subsets
5. Idempotency — POST with idempotency-key for retries
6. Rate limiting — protect the platform
```

**Standard Error Response Format**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Request validation failed",
    "details": [
      {
        "field": "replicas",
        "message": "Must be between 1 and 50"
      }
    ],
    "request_id": "req_01HV3K9XZQM7YBP",
    "timestamp": "2024-11-15T10:23:45Z"
  }
}
```

**Idempotency Pattern (Stripe-style)**
```typescript
// Client sends idempotency key — safe to retry on network failure
// POST /deployments
// Idempotency-Key: a1b2c3d4-e5f6-7890-abcd-ef1234567890

app.post("/deployments", async (req, res) => {
  const idempotencyKey = req.headers["idempotency-key"];
  
  if (idempotencyKey) {
    const cached = await cache.get(`idem:${idempotencyKey}`);
    if (cached) return res.json(JSON.parse(cached)); // Return cached result
  }
  
  const deployment = await createDeployment(req.body);
  
  if (idempotencyKey) {
    await cache.set(`idem:${idempotencyKey}`, JSON.stringify(deployment), {
      EX: 86400 // 24 hours
    });
  }
  
  res.status(201).json(deployment);
});
```

---

## 4.4 GraphQL

GraphQL is used at Meta, GitHub, Shopify, and many enterprise platforms. FDEs at these companies build customer integrations against GraphQL APIs.

```graphql
# Schema design
type Deployment {
  id:          ID!
  name:        String!
  status:      DeploymentStatus!
  environment: Environment!
  createdAt:   DateTime!
  logs(last: Int = 100): [LogEntry!]!
}

enum DeploymentStatus {
  PENDING
  RUNNING
  COMPLETED
  FAILED
  ROLLED_BACK
}

type Query {
  deployment(id: ID!): Deployment
  deployments(
    environment: String
    status: DeploymentStatus
    first: Int = 20
    after: String         # Cursor-based pagination
  ): DeploymentConnection!
}

type Mutation {
  createDeployment(input: CreateDeploymentInput!): CreateDeploymentPayload!
  rollbackDeployment(id: ID!): RollbackPayload!
}

type Subscription {
  deploymentStatusChanged(id: ID!): Deployment!
}
```

```typescript
// Apollo Server resolver
const resolvers = {
  Query: {
    deployment: async (_, { id }, ctx) => {
      if (!ctx.user) throw new GraphQLError("Unauthorized", { 
        extensions: { code: "UNAUTHENTICATED" } 
      });
      return deploymentService.getById(id);
    },
  },
  
  Deployment: {
    // Field-level resolver — only loads logs if requested
    logs: async (parent, { last }) => {
      return logService.getForDeployment(parent.id, { limit: last });
    },
  },
  
  Subscription: {
    deploymentStatusChanged: {
      subscribe: (_, { id }) => pubsub.asyncIterator(`DEPLOYMENT:${id}`),
    },
  },
};
```

---

## 4.5 gRPC — High-Performance Internal APIs

gRPC is used at Google, Netflix, Uber, and Lyft for internal microservice communication. FDEs building integrations with these platforms need gRPC fluency.

```protobuf
// deployment.proto
syntax = "proto3";
package deployment.v1;

import "google/protobuf/timestamp.proto";

service DeploymentService {
  rpc GetDeployment (GetDeploymentRequest) returns (Deployment);
  rpc CreateDeployment (CreateDeploymentRequest) returns (Deployment);
  rpc WatchDeployment (WatchDeploymentRequest) returns (stream DeploymentEvent);
}

message Deployment {
  string id     = 1;
  string name   = 2;
  string status = 3;
  google.protobuf.Timestamp created_at = 4;
}

message DeploymentEvent {
  string deployment_id = 1;
  string event_type    = 2;  // "status_changed", "log_line", "completed"
  string payload       = 3;
  google.protobuf.Timestamp timestamp = 4;
}
```

```python
# gRPC client usage
import grpc
from deployment.v1 import deployment_pb2, deployment_pb2_grpc

channel = grpc.secure_channel("deployments.internal:443", 
                               grpc.ssl_channel_credentials())
stub = deployment_pb2_grpc.DeploymentServiceStub(channel)

# Streaming — watch deployment progress in real-time
for event in stub.WatchDeployment(deployment_pb2.WatchDeploymentRequest(id="dep-123")):
    print(f"[{event.timestamp.seconds}] {event.event_type}: {event.payload}")
    if event.event_type == "completed":
        break
```

---

## 4.6 WebSockets & Real-Time Systems

```typescript
// Server — Socket.io for deployment status dashboard
import { Server } from "socket.io";

const io = new Server(httpServer, {
  cors: { origin: process.env.FRONTEND_URL },
});

io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  const user = await verifyJWT(token);
  if (!user) return next(new Error("Authentication failed"));
  socket.data.user = user;
  next();
});

io.on("connection", (socket) => {
  socket.on("subscribe:deployment", async (deploymentId) => {
    const hasAccess = await checkDeploymentAccess(socket.data.user, deploymentId);
    if (!hasAccess) {
      socket.emit("error", { message: "Access denied" });
      return;
    }
    socket.join(`deployment:${deploymentId}`);
  });
});

// Emit from anywhere in the application
function broadcastDeploymentUpdate(deploymentId: string, update: DeploymentUpdate) {
  io.to(`deployment:${deploymentId}`).emit("deployment:updated", update);
}
```

---

## 4.7 Authentication & Authorization

FDE deployments always involve configuring auth. You must understand every common auth pattern.

### JWT Authentication Flow
```
Client                  API Gateway              Auth Service
  │                           │                        │
  │── POST /auth/login ──────►│── verify credentials ─►│
  │                           │◄── JWT (access+refresh)─│
  │◄── tokens ────────────────│                        │
  │                           │                        │
  │── GET /api/data ─────────►│── verify JWT locally ──│ (no network call!)
  │                           │                        │
  │◄── data ──────────────────│                        │
```

```typescript
// JWT verification middleware
import { verify, JwtPayload } from "jsonwebtoken";

interface AuthPayload extends JwtPayload {
  sub:    string;
  email:  string;
  roles:  string[];
  tenant: string;  // Multi-tenant: which customer?
}

function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const header = req.headers.authorization;
  if (!header?.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing token" });
  }
  
  const token = header.slice(7);
  try {
    const payload = verify(token, process.env.JWT_SECRET!) as AuthPayload;
    req.user = payload;
    next();
  } catch {
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}
```

### SAML/OIDC SSO (You configure this for every enterprise customer)
```
SAML 2.0 Flow:
  1. User hits your app → app checks if authenticated
  2. Redirect to customer IdP (Okta, Azure AD, Ping)
  3. User authenticates against corporate IdP
  4. IdP issues SAML assertion (XML signed with IdP private key)
  5. Browser POSTs assertion to your ACS (Assertion Consumer Service) URL
  6. App verifies signature using IdP's public certificate
  7. App creates session, maps SAML attributes to app roles
  8. User is logged in

OIDC Flow:
  1. Redirect to IdP /authorize endpoint with client_id, scope, redirect_uri
  2. User authenticates, IdP redirects back with auth code
  3. App exchanges code for tokens at /token endpoint (server-side, never browser)
  4. App receives id_token (user identity) + access_token + refresh_token
  5. Verify id_token signature against IdP's JWKS endpoint
```

**Configuration checklist for enterprise SSO deployment:**
```
□ Obtain customer IdP metadata URL or XML file
□ Register your ACS URL with customer IdP admin
□ Map IdP groups/roles to your platform roles
□ Configure session timeout to match customer security policy
□ Test SP-initiated and IdP-initiated login flows
□ Test logout (single logout if SAML, or token revocation if OIDC)
□ Verify attribute mapping (email, name, employee ID if needed)
□ Test with both admin and regular user accounts
□ Document the configuration in customer runbook
```

---

## 4.8 API Gateway Patterns

```
API Gateway — sits in front of all backend services:

[Client]
   │
   ▼
[API Gateway] ─── Authentication & JWT validation
   │           ─── Rate limiting (per API key, per tenant)
   │           ─── Request routing
   │           ─── Response caching
   │           ─── Request/response transformation
   │           ─── Logging & tracing
   ├──► [Service A: /users]
   ├──► [Service B: /deployments]
   └──► [Service C: /billing]
```

Common API Gateways you will configure as an FDE:
- **Kong** — self-hosted, plugin ecosystem, used at Netflix/Nasdaq
- **AWS API Gateway** — serverless, integrates with Lambda and ECS
- **Nginx** — high-performance reverse proxy, often the inner layer
- **Envoy** — service mesh data plane (Istio uses Envoy)

```nginx
# nginx.conf — API gateway with rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api_per_ip:10m rate=100r/m;
    limit_req_zone $http_x_tenant_id   zone=api_per_tenant:10m rate=1000r/m;
    
    upstream backend {
        least_conn;
        server backend-1:3000 weight=3;
        server backend-2:3000 weight=3;
        server backend-3:3000 weight=3;
        keepalive 32;
    }
    
    server {
        listen 443 ssl http2;
        ssl_certificate     /etc/ssl/certs/tls.crt;
        ssl_certificate_key /etc/ssl/private/tls.key;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         HIGH:!aNULL:!MD5;
        
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header Strict-Transport-Security "max-age=31536000" always;
        
        location /api/ {
            limit_req zone=api_per_ip    burst=20 nodelay;
            limit_req zone=api_per_tenant burst=100 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host              $host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 5s;
            proxy_send_timeout    30s;
            proxy_read_timeout    30s;
        }
    }
}
```

---

## 4.9 Microservices Architecture

```
Microservices vs Monolith Decision:

Monolith first if:
  - Team < 10 engineers
  - Domain not yet understood
  - Early stage product

Move to microservices when:
  - Independent deployment velocity blocked by coupling
  - Teams stepping on each other in same codebase
  - Specific services need different scaling profiles
  - Different SLA requirements per service

Common FDE microservices pattern:
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                          │
└──────────┬──────────┬──────────┬────────────────────────┘
           │          │          │
    ┌──────▼──┐  ┌────▼────┐  ┌──▼──────┐
    │  Auth   │  │ Deploy  │  │ Monitor │
    │ Service │  │ Service │  │ Service │
    └──────┬──┘  └────┬────┘  └──┬──────┘
           │          │          │
           └──────────▼──────────┘
                   Event Bus
                  (Kafka/NATS)
                      │
             ┌────────▼────────┐
             │   Audit Service  │
             │  (compliance log)│
             └─────────────────┘
```

**Service communication patterns:**
```
Synchronous (REST/gRPC): Use when caller needs immediate response
  User requests deployment → Get deployment status

Asynchronous (Kafka/NATS): Use when decoupling is more important than immediacy
  Deployment completed → Multiple consumers (notification, billing, audit)
  
Rule: Never use synchronous calls for fire-and-forget operations.
Rule: Never use async for operations where the user waits for the result.
```
