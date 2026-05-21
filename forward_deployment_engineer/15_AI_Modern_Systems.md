# Section 15 — AI & Modern Systems

## 15.1 LLM Deployment Architecture

AI is now a core part of FDE work. Companies like OpenAI, Anthropic, Cohere, and enterprise customers deploying AI workloads need FDEs who understand this stack.

### LLM Serving Architecture
```
Production LLM Serving Stack:

[Client Applications]
        │
[API Gateway + Auth + Rate Limiting]
        │
[LLM Router / Load Balancer]
  ├── Route by model type
  ├── Route by customer tier
  └── Fallback routing
        │
    ┌───┴───────────────┐
    │                   │
[GPU Instance A]   [GPU Instance B]
 vLLM / TGI          vLLM / TGI
 GPT-4 / Claude     Llama 3
        │
[Response Cache]  ← Cache identical prompts (deterministic only)
        │
[Streaming Response]  ← SSE / WebSockets to client
```

### vLLM Deployment on Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference
  namespace: ai-production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: llm-inference
  template:
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          command:
            - "python"
            - "-m"
            - "vllm.entrypoints.openai.api_server"
            - "--model"
            - "meta-llama/Llama-3.1-8B-Instruct"
            - "--tensor-parallel-size"
            - "1"
            - "--max-model-len"
            - "8192"
          resources:
            requests:
              nvidia.com/gpu: "1"
              memory: "16Gi"
            limits:
              nvidia.com/gpu: "1"
              memory: "24Gi"
          env:
            - name: HUGGING_FACE_HUB_TOKEN
              valueFrom:
                secretKeyRef:
                  name: ai-secrets
                  key: hf_token
      nodeSelector:
        node.kubernetes.io/instance-type: g5.xlarge  # NVIDIA A10G GPU
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
```

---

## 15.2 RAG — Retrieval-Augmented Generation

RAG is the most common pattern for enterprise AI deployments. It grounds LLM responses in customer data.

```
RAG Architecture:

                    ┌───────────────────────────────┐
                    │        INDEXING PIPELINE        │
                    │                                 │
Customer Docs       │  PDF/Docs → Chunk → Embed       │
     │              │                     │           │
     └──────────────►         Vector DB ◄─┘           │
                    │      (Pinecone/Qdrant/Weaviate)  │
                    └───────────────────────────────┘
                    
                    ┌───────────────────────────────┐
                    │          QUERY PIPELINE         │
                    │                                 │
User Question ─────►│  Embed question → Vector search │
                    │  → Top-k relevant chunks        │
                    │  → Inject into LLM prompt       │
                    │  → Stream response to user      │
                    └───────────────────────────────┘
```

```python
# RAG implementation with LangChain
from langchain.document_loaders import PDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# Step 1: Load and chunk documents
loader = DirectoryLoader("/customer-docs/", glob="**/*.pdf", loader_cls=PDFLoader)
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)
chunks = splitter.split_documents(documents)

# Step 2: Embed and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(
    chunks,
    embeddings,
    url="http://qdrant:6333",
    collection_name="customer_docs",
)

# Step 3: Query
llm = ChatOpenAI(model="gpt-4o", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
)

result = qa_chain.invoke({"query": "What is the deployment procedure for production?"})
print(result["result"])
print("Sources:", [doc.metadata["source"] for doc in result["source_documents"]])
```

---

## 15.3 Vector Databases

| Database | Deployment | Best For |
|----------|-----------|----------|
| Qdrant | Self-hosted / Cloud | High performance, Rust-based |
| Pinecone | Managed SaaS | Fully managed, no ops |
| Weaviate | Self-hosted / Cloud | GraphQL API, multi-modal |
| pgvector | PostgreSQL extension | Simple use cases, existing Postgres |
| Chroma | Local / server | Development, prototyping |
| Milvus | Self-hosted | Very large scale (billions of vectors) |

```sql
-- pgvector — simplest option for FDE deployments with existing Postgres
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    content     TEXT NOT NULL,
    embedding   vector(1536),  -- OpenAI text-embedding-3-small
    metadata    JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- IVFFlat index — approximate nearest neighbour search
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);  -- sqrt(num_rows) is a good starting point

-- Semantic search query
SELECT id, content, metadata,
       1 - (embedding <=> $1::vector) AS similarity
FROM   document_chunks
WHERE  document_id = $2
ORDER BY embedding <=> $1::vector
LIMIT  5;
```

---

## 15.4 MLOps — Model Lifecycle Management

```
MLOps Lifecycle:

[Data] → [Training] → [Evaluation] → [Registry] → [Serving] → [Monitoring]
          │                              │               │
          └─── MLflow / W&B ────────────►│               │
                                         │               │
                                  Model artifacts   Inference API
                                  versioned +       (vLLM / TorchServe)
                                  tagged            │
                                                    ▼
                                              Performance metrics
                                              Drift detection
                                              A/B test results
```

```python
# MLflow experiment tracking
import mlflow

mlflow.set_experiment("deployment-classifier")

with mlflow.start_run(run_name="gradient-boost-v3"):
    mlflow.log_params({
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.01,
    })
    
    # ... train model ...
    
    mlflow.log_metrics({
        "accuracy": 0.94,
        "f1_score": 0.93,
        "inference_latency_ms": 12,
    })
    
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        registered_model_name="deployment-classifier",
        signature=infer_signature(X_train, y_train),
    )

# Promote to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="deployment-classifier",
    version=3,
    stage="Production",
)
```

---

## 15.5 AI Observability

```
Standard AI metrics to monitor:

Model Performance:
  - Request latency (p50/p95/p99)
  - Tokens per second (throughput)
  - GPU utilisation
  - Token cache hit rate (for KV cache)
  
Quality Metrics:
  - User feedback (thumbs up/down)
  - Hallucination rate (where measurable)
  - Retrieval quality score (RAG: were relevant docs retrieved?)
  - Answer length distribution

Business Metrics:
  - Cost per query (tokens × price/token)
  - Queries per second per GPU
  - Model error rate (rate limiting, context length exceeded)
```

```python
# Log LLM invocations for observability
from opentelemetry import trace
import tiktoken

tracer = trace.getTracer("llm-service")
encoder = tiktoken.encoding_for_model("gpt-4o")

async def invoke_llm(prompt: str, user_id: str) -> str:
    input_tokens = len(encoder.encode(prompt))
    
    with tracer.start_as_current_span("llm.invoke") as span:
        span.set_attributes({
            "llm.model":          "gpt-4o",
            "llm.input_tokens":   input_tokens,
            "llm.user_id":        user_id,
            "llm.prompt_preview": prompt[:100],
        })
        
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.000005) + (output_tokens * 0.000015)
            
            span.set_attributes({
                "llm.output_tokens":  output_tokens,
                "llm.total_tokens":   response.usage.total_tokens,
                "llm.cost_usd":       cost,
                "llm.finish_reason":  response.choices[0].finish_reason,
            })
            
            return response.choices[0].message.content
            
        except Exception as e:
            span.record_exception(e)
            raise
```

---

## 15.6 GPU Infrastructure

```
GPU Instance Types (AWS):

p4d.24xlarge:  8x A100 80GB — LLM training, large models
g5.xlarge:     1x A10G 24GB — LLM inference (7B–13B models)
g5.12xlarge:   4x A10G      — Multi-GPU inference
inf2.xlarge:   AWS Inferentia — Cost-optimised inference
g4dn.xlarge:   1x T4 16GB   — Budget inference

Key GPU metrics:
  GPU Utilisation:  Should be >80% for efficient inference
  GPU Memory:       Monitor for OOM (model too large for GPU)
  SM Efficiency:    Streaming multiprocessor efficiency
  Power usage:      Affects data centre billing
```

---

## 15.7 AI API Integration Patterns

```typescript
// Streaming LLM responses to users (critical for good UX)
app.post("/api/chat", requireAuth, async (req: Request, res: Response) => {
    const { message, conversationId } = req.body;
    
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    
    const stream = await openai.chat.completions.create({
        model:    "gpt-4o",
        messages: await buildMessageHistory(conversationId, message),
        stream:   true,
        max_tokens: 2048,
    });
    
    let fullResponse = "";
    
    for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta?.content;
        if (delta) {
            fullResponse += delta;
            res.write(`data: ${JSON.stringify({ delta })}\n\n`);
        }
    }
    
    res.write("data: [DONE]\n\n");
    res.end();
    
    // Store full response for conversation history
    await saveMessage(conversationId, "assistant", fullResponse);
});

// Retry with exponential backoff for rate limits
async function callWithRetry<T>(
    fn: () => Promise<T>,
    maxRetries = 3
): Promise<T> {
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            return await fn();
        } catch (err: any) {
            if (err?.status === 429 && attempt < maxRetries - 1) {
                const retryAfter = parseInt(err.headers?.["retry-after"] ?? "10");
                await new Promise(r => setTimeout(r, retryAfter * 1000));
                continue;
            }
            throw err;
        }
    }
    throw new Error("Max retries exceeded");
}
```
