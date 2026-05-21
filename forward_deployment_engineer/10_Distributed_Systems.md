# Section 10 — Distributed Systems

## 10.1 Fundamental Concepts

### CAP Theorem
```
Any distributed data store can guarantee only 2 of 3:

C — Consistency:   Every read receives the most recent write
A — Availability:  Every request receives a response
P — Partition Tolerance: System continues despite network splits

Since network partitions are unavoidable in distributed systems,
you choose between CP and AP:

CP (Consistency + Partition Tolerance):
  - Returns an error when network partition occurs
  - Examples: HBase, Zookeeper, Redis Cluster (with writes disabled)
  - Use: Financial data, inventory counts, distributed locks
  
AP (Availability + Partition Tolerance):
  - Returns potentially stale data but never errors
  - Examples: CouchDB, Cassandra, DynamoDB (eventually consistent)
  - Use: Social feeds, recommendation systems, session data

PACELC (extends CAP):
  "Even without partition, there is a tradeoff between Latency and Consistency"
```

### ACID vs BASE
```
ACID (Traditional databases — PostgreSQL, MySQL):
  Atomicity:   Transaction fully succeeds or fully fails
  Consistency: DB moves from valid state to valid state
  Isolation:   Concurrent transactions behave as if sequential
  Durability:  Committed data survives failures

BASE (Distributed NoSQL — Cassandra, DynamoDB):
  Basically Available:  System is available most of the time
  Soft state:           State may change over time even without input
  Eventual consistency: Data will become consistent "eventually"
  
FDE Decision Guide:
  Financial transactions → ACID (PostgreSQL)
  User sessions, preferences → BASE (DynamoDB/Redis)
  Analytics events → BASE (Cassandra/ClickHouse)
  Audit logs → ACID (append-only PostgreSQL)
```

---

## 10.2 Message Queues — Apache Kafka

Kafka is the backbone of event-driven architecture at Netflix, Uber, LinkedIn, and Confluent.

```
Kafka Architecture:
  
  Producers → Topics → Consumer Groups
  
  Topic "deployment-events":
    Partition 0: [msg1, msg4, msg7, ...]
    Partition 1: [msg2, msg5, msg8, ...]
    Partition 2: [msg3, msg6, msg9, ...]
    
  Consumer Group "monitoring-service":
    Consumer A: reads Partition 0
    Consumer B: reads Partition 1
    Consumer C: reads Partition 2
    (Each partition consumed by exactly one consumer in a group)
  
  Consumer Group "billing-service":
    Consumer D: reads all partitions
    (Different groups → same messages, different offsets)

Key guarantees:
  - Messages within a partition: ordered
  - Messages across partitions: not ordered
  - At-least-once delivery (default)
  - Exactly-once (with transactions)
  - Messages retained configurable duration (default 7 days)
```

```python
# Kafka producer — structured event publishing
from confluent_kafka import Producer
from dataclasses import dataclass, asdict
import json, uuid
from datetime import datetime, timezone

@dataclass
class DeploymentEvent:
    event_id:       str
    event_type:     str   # "deployment.started" | "deployment.completed" | "deployment.failed"
    deployment_id:  str
    environment:    str
    version:        str
    customer_id:    str
    timestamp:      str
    metadata:       dict

class DeploymentEventPublisher:
    def __init__(self, brokers: str):
        self._producer = Producer({
            "bootstrap.servers": brokers,
            "enable.idempotence": True,    # Exactly-once semantics
            "acks": "all",                  # All replicas must acknowledge
            "retries": 5,
            "retry.backoff.ms": 1000,
        })
    
    def publish(self, event: DeploymentEvent):
        self._producer.produce(
            topic="deployment-events",
            key=event.deployment_id.encode("utf-8"),  # Partition by deployment_id
            value=json.dumps(asdict(event)).encode("utf-8"),
            headers={"event_type": event.event_type},
            on_delivery=self._delivery_callback,
        )
        self._producer.poll(0)  # Trigger callbacks
    
    def flush(self, timeout: float = 10.0):
        self._producer.flush(timeout)
    
    @staticmethod
    def _delivery_callback(err, msg):
        if err:
            log.error("Message delivery failed", error=str(err))
        else:
            log.debug("Message delivered", 
                      partition=msg.partition(), 
                      offset=msg.offset())

# Kafka consumer — idempotent event processing
from confluent_kafka import Consumer, KafkaError

class DeploymentEventConsumer:
    def __init__(self, brokers: str, group_id: str):
        self._consumer = Consumer({
            "bootstrap.servers":     brokers,
            "group.id":              group_id,
            "auto.offset.reset":     "earliest",
            "enable.auto.commit":    False,   # Manual commit for at-least-once
            "max.poll.interval.ms":  300_000,
        })
        self._consumer.subscribe(["deployment-events"])
    
    def run(self, handler: callable, stop_event):
        try:
            while not stop_event.is_set():
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaError(msg.error())
                
                event = DeploymentEvent(**json.loads(msg.value()))
                
                try:
                    handler(event)
                    self._consumer.commit(message=msg)  # Commit after success
                except Exception as e:
                    log.error("Handler failed — not committing", error=str(e))
                    # Message will be redelivered on next poll
        finally:
            self._consumer.close()
```

---

## 10.3 RabbitMQ

RabbitMQ is simpler than Kafka. Used for task queues, RPC patterns, and workloads that need complex routing.

```
Kafka vs RabbitMQ Decision:
  
  Use Kafka when:
    - High throughput (>100k msg/sec)
    - Message replay needed
    - Stream processing
    - Multiple independent consumers
    
  Use RabbitMQ when:
    - Task distribution (worker queue)
    - Complex routing (exchange patterns)
    - Request-reply RPC patterns
    - Lower throughput with higher routing flexibility
    - Older enterprise integration (AMQP requirement)
```

---

## 10.4 Rate Limiting

Rate limiting protects your platform from overload and abuse.

### Token Bucket Algorithm
```python
import time
import threading

class TokenBucket:
    """
    Tokens replenish at `rate` per second up to `capacity`.
    One token consumed per request.
    """
    def __init__(self, capacity: float, rate: float):
        self.capacity  = capacity
        self.rate      = rate
        self.tokens    = capacity
        self.last_time = time.monotonic()
        self._lock     = threading.Lock()
    
    def consume(self, tokens: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.last_time = now
            
            # Refill tokens
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True  # Allowed
            return False  # Rate limited
```

### Distributed Rate Limiting (Redis-based — production standard)
```lua
-- Redis Lua script — sliding window rate limiter
-- KEYS[1] = rate limit key, ARGV[1] = limit, ARGV[2] = window_ms, ARGV[3] = now_ms
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local window_start = now - window

redis.call("ZREMRANGEBYSCORE", key, 0, window_start)
local count = redis.call("ZCARD", key)

if count < limit then
    redis.call("ZADD", key, now, now .. math.random())
    redis.call("EXPIRE", key, math.ceil(window / 1000))
    return {1, limit - count - 1}  -- {allowed, remaining}
else
    return {0, 0}  -- {blocked, remaining}
end
```

---

## 10.5 Caching Strategies

```
Cache Hit/Miss Pattern:
  
  READ (cache-aside):
    1. Check cache for key
    2. Hit  → Return cached value
    3. Miss → Query DB → Store in cache with TTL → Return value
    
  WRITE strategies:
    Write-through:  Write to cache AND DB simultaneously
                    Pro: Cache always consistent
                    Con: Write latency = DB latency
    
    Write-behind:   Write to cache, asynchronously write to DB
                    Pro: Low write latency
                    Con: Risk of data loss if cache fails
    
    Write-around:   Write directly to DB, skip cache
                    Pro: Avoids polluting cache with infrequently-read data
                    Con: Cache miss on next read
```

```typescript
class CacheService {
    constructor(
        private redis: Redis,
        private db: DatabaseService
    ) {}
    
    async get<T>(
        key: string,
        fetchFn: () => Promise<T>,
        ttlSeconds: number = 300
    ): Promise<T> {
        // Try cache first
        const cached = await this.redis.get(key);
        if (cached !== null) {
            return JSON.parse(cached) as T;
        }
        
        // Cache miss — fetch from DB
        const value = await fetchFn();
        
        // Store in cache with TTL
        await this.redis.setex(key, ttlSeconds, JSON.stringify(value));
        
        return value;
    }
    
    async invalidate(pattern: string): Promise<void> {
        // Pattern-based invalidation (use with care — expensive on large keyspaces)
        const keys = await this.redis.keys(pattern);
        if (keys.length > 0) {
            await this.redis.del(...keys);
        }
    }
    
    async invalidateKey(key: string): Promise<void> {
        await this.redis.del(key);
    }
}

// Cache stampede protection (dogpile prevention)
// Multiple concurrent requests on the same cache miss → only one DB query
class SingleFlightCache extends CacheService {
    private _inFlight = new Map<string, Promise<unknown>>();
    
    async get<T>(key: string, fetchFn: () => Promise<T>, ttl = 300): Promise<T> {
        const cached = await this.redis.get(key);
        if (cached !== null) return JSON.parse(cached);
        
        // If another request is already fetching this key, wait for it
        if (this._inFlight.has(key)) {
            return this._inFlight.get(key) as Promise<T>;
        }
        
        const promise = fetchFn().then(async value => {
            await this.redis.setex(key, ttl, JSON.stringify(value));
            this._inFlight.delete(key);
            return value;
        });
        
        this._inFlight.set(key, promise);
        return promise;
    }
}
```

---

## 10.6 Saga Pattern — Distributed Transactions

When a business operation spans multiple services, use Sagas instead of 2-phase commit.

```
Example: Customer deployment involves 4 services

Saga steps (orchestration pattern):
  1. Deployment Service: reserve slot       → SUCCESS
  2. Billing Service:    charge customer    → SUCCESS
  3. Infra Service:      provision cloud    → FAILED ← rollback from here
  
Compensating transactions (rollback):
  3. Infra Service:      [no rollback needed — failed before provisioning]
  2. Billing Service:    reverse charge
  1. Deployment Service: release slot
```

```typescript
class DeploymentSaga {
    private completedSteps: string[] = [];
    
    async execute(config: DeploymentConfig): Promise<void> {
        try {
            await this.reserveDeploymentSlot(config);
            this.completedSteps.push("reserve_slot");
            
            await this.chargeCustomer(config);
            this.completedSteps.push("charge_customer");
            
            await this.provisionInfrastructure(config);
            this.completedSteps.push("provision_infra");
            
            await this.deployApplication(config);
            this.completedSteps.push("deploy_app");
            
        } catch (error) {
            log.error("Saga step failed — executing compensation", {
                error: error.message,
                completed_steps: this.completedSteps
            });
            await this.compensate(config);
            throw error;
        }
    }
    
    private async compensate(config: DeploymentConfig): Promise<void> {
        // Compensate in reverse order
        for (const step of [...this.completedSteps].reverse()) {
            try {
                switch (step) {
                    case "deploy_app":      await this.rollbackDeployment(config);   break;
                    case "provision_infra": await this.deprovisionInfra(config);     break;
                    case "charge_customer": await this.refundCustomer(config);       break;
                    case "reserve_slot":    await this.releaseSlot(config);          break;
                }
            } catch (compError) {
                // Log compensation failure — needs manual intervention
                log.error("Compensation failed — MANUAL ACTION REQUIRED", {
                    step, error: compError.message
                });
            }
        }
    }
}
```

---

## 10.7 Consistent Hashing

Used in distributed caches (Redis Cluster), load balancers, and CDNs to minimise remapping when nodes are added/removed.

```
Traditional hashing: server = hash(key) % num_servers
  Add 1 server of 3: 67% of keys remapped → massive cache miss storm

Consistent hashing: keys and servers on a ring 0..2^32
  Add 1 server of 3: only ~33% of keys remapped (keys between new and prev node)
  
FDE use cases:
  - Redis Cluster routes keys to shards using consistent hashing
  - Cassandra partitions data across nodes with consistent hashing
  - HAProxy / Nginx can use consistent hashing for session affinity
```
