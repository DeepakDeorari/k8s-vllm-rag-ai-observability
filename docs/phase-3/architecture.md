# Phase 3 Architecture: Distributed AI SRE Agent Platform

## 1. Overview

Phase 3 extends the Kubernetes-based AI platform into a distributed, read-only AI SRE investigation system.

The platform combines:

- FastAPI for the public investigation API
- LangGraph for workflow orchestration and state transitions
- Qwen served through vLLM for intent classification and guarded analysis
- Prometheus for infrastructure and application metrics
- Kubernetes APIs for workload diagnostics
- Qdrant for operational runbook retrieval
- MiniLM for semantic embeddings
- Ray and KubeRay for distributed diagnostic execution
- Prometheus instrumentation for measuring agent behavior
- Deterministic validation and fallback logic for safe responses

The architecture intentionally separates workflow control, distributed execution, and infrastructure scheduling:

```text
LangGraph
→ Determines what the investigation should do next

Ray
→ Determines where and how eligible Python workloads execute

Kubernetes
→ Manages the containers and infrastructure on which Ray runs
```

The platform is designed for investigation and decision support. It does not perform autonomous remediation or mutate Kubernetes resources.

---

## 2. Phase 3 Objectives

Phase 3 was designed around the following engineering goals:

1. Build a practical AI SRE investigation workflow.
2. Support multiple diagnostic routes through a single API.
3. Keep Kubernetes access read-only.
4. Ground LLM output in real operational evidence.
5. Reject speculative or unsafe analysis.
6. Preserve deterministic fallback behavior.
7. Instrument the AI agent using Prometheus.
8. Evaluate where distributed execution improves the system.
9. Deploy Ray across multiple Kubernetes nodes.
10. Validate task and Actor recovery after worker failure.
11. Preserve existing API behavior while adding distributed investigations.
12. Produce a portfolio-ready AI Infrastructure and LLMOps project.

---

## 3. Final Architecture

```text
                           Client
                             │
                             ▼
                    FastAPI /investigate
                             │
                             ▼
                         LangGraph
                             │
             ┌───────────────┴────────────────┐
             │                                │
             ▼                                ▼
     Lightweight routes                 BROAD route
     CPU / Health / K8s                       │
             │                                ▼
             │                           Ray Client
             │                                │
             │                                ▼
             │                         KubeRay Head Pod
             │                       Kubernetes Node 1
             │                                │
             │                                ▼
             │                        Ray Worker Pod
             │                       Kubernetes Node 2
             │             ┌──────────────────┼──────────────────┐
             │             ▼                  ▼                  ▼
             │        Prometheus         Kubernetes       KnowledgeActor
             │        diagnostics        diagnostics            │
             │        - targets          - pod health          MiniLM
             │        - node CPU         - restarts              │
             │                                                Qdrant
             │             └──────────────────┼──────────────────┘
             │                                ▼
             │                         Evidence bundle
             │                                │
             └────────────────────────────────┘
                                              │
                                              ▼
                                         LangGraph
                                              │
                                              ▼
                                      Deterministic report
                                              │
                                              ▼
                                           FastAPI
                                              │
                                              ▼
                                    Prometheus instrumentation
```

---

## 4. Kubernetes Deployment Topology

Phase 3 runs on a two-node MicroK8s cluster.

### 4.1 Kubernetes Node 1

```text
Node:
ip-172-31-7-23

Workloads:
- AI SRE Agent
- Ray Head
- Primary Qwen/vLLM workload
- GPU-backed inference components
```

The Ray Head provides the Ray control services and Ray Client endpoint.

The Ray Head advertises zero normal task CPUs. This prevents general Ray diagnostic tasks from competing with the AI SRE Agent and primary inference workloads on Node 1.

### 4.2 Kubernetes Node 2

```text
Node:
ip-172-31-6-36

Workloads:
- Ray Worker
- Secondary vLLM workload
- Distributed CPU diagnostic execution
```

The Ray Worker advertises two logical Ray CPUs and executes the distributed diagnostic workload.

### 4.3 GPU Isolation

Both Kubernetes nodes have NVIDIA GPUs allocated to vLLM workloads.

The Ray cluster is intentionally CPU-only.

The Ray Head and Ray Worker do not request:

```yaml
nvidia.com/gpu
```

This ensures that Ray diagnostics do not compete with LLM inference for GPU resources.

---

## 5. FastAPI Application

The AI SRE Agent exposes a FastAPI service.

### 5.1 Deployed image

```text
ai-sre-agent:0.1.3
```

### 5.2 Endpoints

```text
GET  /health
GET  /metrics
GET  /capabilities
POST /investigate
```

### 5.3 Health endpoint

```text
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "service": "ai-sre-langgraph-api"
}
```

### 5.4 Capabilities endpoint

```text
GET /capabilities
```

The implemented routes are:

```text
cpu
health
kubernetes
broad
unsupported
```

The Kubernetes route supports:

```text
restarts
unhealthy
```

### 5.5 Investigation endpoint

```text
POST /investigate
```

Example request:

```json
{
  "question": "Investigate overall Kubernetes and monitoring platform health."
}
```

The API response contract includes:

```text
question
route
kubernetes_intent
answer
analysis_valid
analysis_validation_errors
retrieved_documents
duration_ms
```

---

## 6. LangGraph Workflow

LangGraph owns the investigation workflow and shared state.

LangGraph is responsible for:

- Primary intent classification
- Kubernetes intent classification
- Workflow routing
- Diagnostic evidence state
- Qdrant retrieval workflow
- Qwen analysis workflow
- Deterministic analysis validation
- Safe fallback behavior
- Final response formatting

### 6.1 Primary routes

```text
CPU
HEALTH
KUBERNETES
BROAD
UNSUPPORTED
```

### 6.2 Existing lightweight routes

```text
CPU
  ↓
collect_cpu_metrics
  ↓
format_cpu_response
  ↓
END
```

```text
HEALTH
  ↓
collect_health_metrics
  ↓
format_health_response
  ↓
END
```

```text
KUBERNETES
  ↓
classify_kubernetes_intent
  ├── restarts
  ├── unhealthy
  └── unsupported
```

### 6.3 Kubernetes restart route

```text
collect_restart_metrics
        ↓
build_restart_retrieval_query
        ↓
retrieve_restart_knowledge
        ↓
analyze_restart_evidence
        ↓
validate_restart_analysis
        ↓
format_restart_response
        ↓
END
```

### 6.4 Broad distributed route

Phase 3 adds the following route:

```text
classify_primary_intent
        ↓
route = broad
        ↓
collect_ray_evidence
        ↓
format_ray_response
        ↓
END
```

The broad route collects evidence across multiple operational systems through Ray.

---

## 7. Qwen and vLLM

Qwen is served through vLLM.

Qwen is used for:

- Primary intent classification
- Kubernetes intent classification
- Grounded restart analysis

The configured model is:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

### 7.1 Classification

The primary classifier chooses one of:

```text
CPU
HEALTH
KUBERNETES
BROAD
UNSUPPORTED
```

Normalization uses an explicit allowlist.

Unknown or unrecognized outputs fail closed to:

```text
unsupported
```

### 7.2 Guarded analysis

The restart-analysis path allows Qwen to analyze:

- Kubernetes restart evidence
- Retrieved operational knowledge
- Workload identifiers
- Namespace information
- Restart counts

The model output is never trusted directly.

It is passed through a deterministic validator before being included in the final response.

---

## 8. Analysis Validation and Safe Fallback

The validator checks Qwen output for:

- Unsupported workload identifiers
- Claims that are not grounded in Kubernetes evidence
- Claims that are not grounded in retrieved documents
- Speculative causal statements
- Missing required evidence
- Invalid response structure

If validation succeeds:

```text
Qwen analysis
→ accepted
→ included in final answer
```

If validation fails:

```text
Qwen analysis
→ rejected
→ deterministic safe fallback
```

The fallback is built from actual Kubernetes and retrieved runbook evidence.

This keeps the LLM in an advisory role rather than allowing unsupported operational conclusions.

---

## 9. Prometheus Diagnostics

The platform queries Prometheus for:

- Prometheus scrape-target health
- Kubernetes node CPU utilization
- Agent request metrics
- Agent route metrics
- Investigation duration
- Knowledge retrieval counts
- Validator decisions
- Fallback usage

### 9.1 Prometheus target-health schema

```text
total_target_count
up_target_count
down_target_count
targets
```

### 9.2 Node CPU schema

```text
node_count
nodes
query
```

Example CPU evidence:

```json
{
  "node_count": 2,
  "nodes": [
    {
      "instance": "172.31.7.23:9100",
      "cpu_utilization_percent": 15.38
    },
    {
      "instance": "172.31.6.36:9100",
      "cpu_utilization_percent": 3.77
    }
  ]
}
```

---

## 10. Kubernetes Diagnostics

The platform uses in-cluster Kubernetes authentication and read-only RBAC.

Supported diagnostic evidence includes:

- Total pod count
- Current unhealthy pod count
- Pod waiting reasons
- Container readiness
- Historical container restart counts
- Namespace information
- Pod identifiers
- Workload health evidence

### 10.1 Kubernetes health schema

```text
config_source
total_pod_count
unhealthy_pod_count
unhealthy_pods
```

### 10.2 Kubernetes restart schema

```text
config_source
total_pod_count
restarting_pod_count
restarting_pods
```

---

## 11. Qdrant and MiniLM

Qdrant stores operational knowledge and runbook content.

MiniLM generates semantic embeddings using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embedding dimensions:

```text
384
```

The embedding model is packaged inside the container images.

The model was validated with networking disabled:

```text
OFFLINE_MINILM_OK
```

This prevents runtime dependency on Hugging Face availability.

---

## 12. Ray and KubeRay Architecture

KubeRay manages a RayCluster containing one head and one worker.

### 12.1 KubeRay operator

```text
Namespace:
ray-system

Version:
1.7.0
```

### 12.2 RayCluster

```text
Namespace:
ray-cluster

Name:
ai-sre-ray

Status:
ready
```

### 12.3 Ray Head

```text
Node:
ip-172-31-7-23

Image:
ai-sre-ray:0.1.1

Normal task CPUs:
0
```

### 12.4 Ray Worker

```text
Node:
ip-172-31-6-36

Image:
ai-sre-ray:0.1.1

Logical Ray CPUs:
2
```

The head advertises no normal task CPU capacity, ensuring the diagnostic tasks execute on the Ray Worker.

---

## 13. Custom CPU-Only Ray Image

The custom Ray image contains:

- Ray 2.59.0
- CPU-only PyTorch
- Kubernetes Python client
- Requests
- Qdrant client
- Sentence Transformers
- Transformers
- Local MiniLM model
- Project SRE diagnostic tools
- Ray SRE evidence collector

### 13.1 CPU-only validation

```text
Torch version:
2.14.1+cpu

CUDA available:
False

Torch CUDA version:
None
```

### 13.2 Image size optimization

Full agent image content size:

```text
3.62 GB
```

Dedicated Ray image content size:

```text
1.48 GB
```

Approximate reduction:

```text
59%
```

This reduces image-transfer and startup overhead across Ray nodes.

---

## 14. Distributed Broad Investigation

The broad route collects five independent evidence sources:

```text
1. Prometheus target health
2. Prometheus node CPU
3. Kubernetes workload health
4. Kubernetes restart history
5. Qdrant operational knowledge
```

### 14.1 Stateless Ray Tasks

The Prometheus and Kubernetes collectors use fractional CPU allocations:

```text
Prometheus target health:
0.25 CPU

Prometheus node CPU:
0.25 CPU

Kubernetes workload health:
0.25 CPU

Kubernetes restart history:
0.25 CPU
```

These operations are mostly network and API I/O.

Fractional CPU reservations allow them to execute concurrently on a two-CPU Ray Worker.

### 14.2 KnowledgeActor

The KnowledgeActor requests:

```text
0.5 CPU
```

The Actor retains:

- MiniLM model
- Qdrant client
- Process identity
- Retrieval counter
- Reconstructable runtime state

The Actor does not own durable incident or workflow state.

### 14.3 Named detached Actor

```text
Actor name:
ai-sre-knowledge-v1

Namespace:
ai-sre-platform
```

The detached named Actor survives individual Ray Client requests and reuses MiniLM across investigations.

---

## 15. Distributed Evidence Collector

The FastAPI/LangGraph process connects to the existing Ray cluster using:

```text
RAY_ADDRESS=
ray://ai-sre-ray-head-svc.ray-cluster.svc.cluster.local:10001
```

Additional configuration:

```text
RAY_NAMESPACE=ai-sre-platform

RAY_KNOWLEDGE_ACTOR_NAME=
ai-sre-knowledge-v1
```

The collector:

1. Connects explicitly to the existing KubeRay cluster.
2. Refuses to create a silent local Ray runtime.
3. Gets or creates the named KnowledgeActor.
4. Submits all diagnostic operations before waiting.
5. Collects each result independently.
6. Preserves partial evidence when one source fails.
7. Returns execution metadata for each source.
8. Returns Qdrant documents to LangGraph state.

---

## 16. Security Architecture

The platform uses dedicated Kubernetes identities.

### 16.1 AI SRE Agent identity

```text
Namespace:
agent-platform

ServiceAccount:
ai-sre-agent

ClusterRole:
ai-sre-agent-readonly
```

### 16.2 Ray identity

```text
Namespace:
ray-cluster

ServiceAccount:
ai-sre-ray

ClusterRoleBinding:
ai-sre-ray-readonly

ClusterRole:
ai-sre-agent-readonly
```

### 16.3 Allowed operations

```text
get
list
watch
```

### 16.4 Denied operations

```text
create
update
patch
delete
```

Validated examples:

```text
List pods across namespaces:
yes

Read nodes:
yes

Delete pods:
no

Patch deployments:
no

Create secrets:
no
```

The platform performs diagnosis only.

It cannot perform autonomous remediation or modify Kubernetes resources.

---

## 17. Agent Observability

The FastAPI service exposes Prometheus metrics at:

```text
GET /metrics
```

Metrics include:

```text
ai_sre_investigations_total

ai_sre_route_total{
  route,
  kubernetes_intent
}

ai_sre_investigation_duration_seconds{
  route
}

ai_sre_analysis_validation_total{
  result
}

ai_sre_fallback_total

ai_sre_retrieved_documents
```

A ServiceMonitor in the `observability` namespace discovers the agent Service in the `agent-platform` namespace.

### 17.1 Broad-route metrics

The deployed broad route was observed in Prometheus:

```text
ai_sre_route_total{
  route="broad",
  kubernetes_intent="none"
}
```

Latency was observed through:

```text
ai_sre_investigation_duration_seconds_count{
  route="broad"
}
```

---

## 18. Failure Model

### 18.1 Ray Task failure

A retryable task was started on the Ray Worker.

The active worker Pod was deleted while the task was running.

Observed recovery:

1. Ray detected the worker failure.
2. KubeRay created a replacement worker.
3. The replacement worker joined the Ray cluster.
4. The task became schedulable again.
5. Ray retried the task.
6. The task completed on the replacement worker.

The task restarted from the beginning.

The task did not resume from its interrupted execution point.

### 18.2 Ray Actor failure

A stateful Actor method was running when the Ray Worker Pod was deleted.

Observed recovery:

1. The Actor process disappeared.
2. KubeRay restored the worker infrastructure.
3. Ray reconstructed the Actor.
4. The Actor constructor executed again.
5. In-memory Actor state reset.
6. The interrupted Actor method was retried.
7. The method completed on the replacement worker.

This demonstrated that:

```text
Actor memory
→ reconstructable runtime state

External persistence
→ durable application state
```

---

## 19. Final Deployed Versions

```text
AI SRE Agent:
ai-sre-agent:0.1.3

Ray Head:
ai-sre-ray:0.1.1

Ray Worker:
ai-sre-ray:0.1.1

Ray:
2.59.0

KubeRay Operator:
1.7.0
```

---

## 20. Production Validation

The following validation completed successfully:

```text
FastAPI contract tests:
12/12 passed

Broad route normalization:
passed

Full broad LangGraph invocation:
passed

Distributed collector sources:
5/5 passed

Qdrant documents:
3 retrieved

Deployed broad investigations:
5/5 passed

Prometheus broad-route observation:
passed

Persistent KnowledgeActor:
passed

Ray Worker recovery:
passed

Ray task retry:
passed

Ray Actor reconstruction:
passed
```

---

## 21. Key Architecture Decision

Ray is not used for every diagnostic route.

Benchmarking demonstrated that tiny warmed diagnostic calls were faster sequentially than through Ray.

The final execution strategy is:

```text
Small, inexpensive diagnostics
→ direct sequential execution

Broad multi-source investigations
→ Ray distributed fan-out

Expensive reusable model state
→ persistent Ray Actor

Durable workflow state
→ LangGraph or external persistence
```

This keeps the architecture evidence-based rather than applying distributed execution indiscriminately.

---

## 22. Technical Debt

The following technical-debt items remain:

1. Align Python patch versions across the FastAPI Ray Client and Ray runtime.

   ```text
   FastAPI Ray Client:
   Python 3.12.3

   Ray runtime:
   Python 3.12.14
   ```

2. Investigate removing the unused `cupy-cuda12x` package from the CPU-only Ray image.

3. Consider lazy-loading the host-side Qdrant retriever to reduce application startup time.

4. Gather more broad-route latency samples before treating histogram p95 as statistically meaningful.

5. Refine broad-route histogram buckets around the observed latency range.

6. Add external durable checkpointing if future Actors own workflow state.

---

## 23. Final Phase 3 Outcome

Phase 3 delivers a distributed, observable, read-only AI SRE investigation platform.

The completed platform demonstrates:

- AI application orchestration
- Kubernetes operations
- Distributed Python execution
- LLM inference through vLLM
- Retrieval-augmented generation
- Prometheus observability
- Least-privilege security
- Deterministic LLM guardrails
- Performance benchmarking
- Worker failure recovery
- Actor reconstruction
- Evidence-based architectural decision-making

The Phase 3 architecture is now frozen.
