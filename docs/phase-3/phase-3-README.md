# Phase 3: Distributed AI SRE Agent Platform

## Status

```text
Phase 3 technical implementation: COMPLETE
Architecture status: FROZEN
API contract tests: 12/12 passed
Deployed broad investigations: 5/5 passed
```

## Overview

Phase 3 extends the Kubernetes AI platform into a distributed, observable, and read-only AI SRE investigation system.

The platform combines:

- FastAPI for the public investigation API
- LangGraph for workflow orchestration and state transitions
- Qwen served through vLLM for classification and guarded analysis
- Prometheus for platform metrics and agent observability
- Kubernetes APIs for workload diagnostics
- Qdrant for operational runbook retrieval
- MiniLM for semantic embeddings
- Ray and KubeRay for distributed diagnostic execution
- Deterministic validation and safe fallback behavior

The system diagnoses infrastructure but does not perform autonomous remediation.

## Final Architecture

```text
                           Client
                             |
                             v
                    FastAPI /investigate
                             |
                             v
                         LangGraph
                             |
              +--------------+--------------+
              |                             |
              v                             v
     Lightweight routes                BROAD route
     CPU / Health / K8s                     |
              |                             v
              |                         Ray Client
              |                             |
              |                             v
              |                      KubeRay Head Pod
              |                    Kubernetes Node 1
              |                             |
              |                             v
              |                     Ray Worker Pod
              |                    Kubernetes Node 2
              |          +------------------+------------------+
              |          |                  |                  |
              |          v                  v                  v
              |     Prometheus         Kubernetes       KnowledgeActor
              |     diagnostics        diagnostics            |
              |     - targets          - pod health          MiniLM
              |     - node CPU         - restarts              |
              |                                             Qdrant
              |          +------------------+------------------+
              |                             |
              |                             v
              |                       Evidence bundle
              |                             |
              +-----------------------------+
                                            |
                                            v
                                        LangGraph
                                            |
                                            v
                                    Deterministic response
                                            |
                                            v
                                         FastAPI
                                            |
                                            v
                                  Prometheus instrumentation
```

## Kubernetes Topology

### Node 1

```text
Node: ip-172-31-7-23

Workloads:
- AI SRE Agent
- Ray Head
- Primary Qwen/vLLM workload
```

### Node 2

```text
Node: ip-172-31-6-36

Workloads:
- Ray Worker
- Secondary vLLM workload
- Distributed CPU diagnostic execution
```

The Ray runtime is CPU-only and does not request NVIDIA GPU resources.

## Final Runtime Versions

```text
AI SRE Agent:
ai-sre-agent:0.1.3

Ray Head and Worker:
ai-sre-ray:0.1.1

Ray:
2.59.0

KubeRay Operator:
1.7.0
```

## API Endpoints

```text
GET  /health
GET  /metrics
GET  /capabilities
POST /investigate
```

## Supported Routes

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

## Example Broad Investigation

Port-forward the API:

```bash
kubectl -n agent-platform port-forward \
  svc/ai-sre-agent \
  8082:8082
```

Submit an investigation:

```bash
curl -sS -X POST \
  http://127.0.0.1:8082/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Investigate overall Kubernetes and monitoring platform health."
  }' \
  | python -m json.tool
```

Expected high-level response:

```text
route: broad
kubernetes_intent: null
retrieved_documents: 3
```

The answer includes:

- Prometheus target health
- Kubernetes workload health
- Node CPU utilization
- Historical restart evidence
- Relevant operational knowledge

## LangGraph Workflow

LangGraph owns:

- Primary intent classification
- Kubernetes intent classification
- Workflow routing
- Evidence state
- Retrieval flow
- Guarded Qwen analysis
- Deterministic validation
- Safe fallback behavior
- Final response formatting

The broad route is:

```text
classify_primary_intent
        |
        v
route = broad
        |
        v
collect_ray_evidence
        |
        v
format_ray_response
        |
        v
END
```

Existing CPU, health, Kubernetes restart, unhealthy, validation, and fallback routes remain intact.

## Distributed Broad Investigation

The broad route collects five evidence sources:

```text
1. Prometheus target health
2. Prometheus node CPU
3. Kubernetes workload health
4. Kubernetes restart history
5. Qdrant operational knowledge
```

Stateless collectors request fractional Ray CPU resources:

```text
Prometheus target health: 0.25 CPU
Prometheus node CPU:      0.25 CPU
Kubernetes health:        0.25 CPU
Kubernetes restarts:      0.25 CPU
```

The persistent KnowledgeActor requests:

```text
0.5 CPU
```

This allows short, I/O-heavy diagnostic Tasks to execute concurrently while retaining MiniLM and the Qdrant client in a long-lived Actor.

## KnowledgeActor

The named detached Actor is:

```text
Name: ai-sre-knowledge-v1
Namespace: ai-sre-platform
```

The Actor retains reconstructable runtime state:

- MiniLM model
- Qdrant client
- Process identity
- Temporary runtime state
- Retrieval counter

The Actor does not own durable incident or workflow state.

Final recorded state included:

```text
status: ready
hostname: ai-sre-ray-cpu-workers-worker-2n56d
pod_ip: 10.1.227.32
pid: 160
initialization_seconds: 16.5236
retrieval_count: 3
```

## Read-Only Security

The AI SRE Agent and Ray runtime use dedicated Kubernetes ServiceAccounts.

Allowed operations:

```text
get
list
watch
```

Denied operations:

```text
create
update
patch
delete
```

Validated examples:

```text
List Pods:        yes
Get Nodes:        yes
Delete Pods:      no
Patch Deployment: no
Create Secret:    no
```

The LLM remains advisory. The platform cannot autonomously alter cluster state.

## Guarded LLM Analysis

Qwen output is validated before it is accepted.

The deterministic validator checks for:

- Unsupported workload identifiers
- Claims not grounded in Kubernetes evidence
- Claims not grounded in retrieved documents
- Speculative causal statements
- Missing evidence
- Invalid response structure

When validation fails, the model output is rejected and replaced with a deterministic safe response.

## Agent Observability

The API exports Prometheus metrics at:

```text
GET /metrics
```

Metric families include:

```text
ai_sre_investigations_total
ai_sre_route_total
ai_sre_investigation_duration_seconds
ai_sre_analysis_validation_total
ai_sre_fallback_total
ai_sre_retrieved_documents
```

A ServiceMonitor discovers the agent Service across namespaces.

## Benchmark Summary

### Synthetic parallelism

```text
Sequential: 6.00 seconds
Ray:        2.24 seconds
Speedup:    2.68x
```

### Tiny warmed SRE workload

```text
Sequential Python:   14.84 investigations/second
ThreadPoolExecutor:   8.00 investigations/second
Ray:                  5.39 investigations/second
```

The result demonstrated that Ray should not be used indiscriminately.

The final strategy is:

```text
Small inexpensive diagnostics:
direct sequential execution

Broad multi-source investigations:
Ray distributed fan-out

Expensive reusable model state:
persistent Ray Actor

Durable workflow state:
LangGraph or external persistence
```

## Failure Engineering

### Task recovery

A long-running Ray Task was interrupted by deleting the active worker Pod.

Observed sequence:

```text
Task starts
Worker Pod is deleted
Ray detects node loss
KubeRay creates a replacement worker
Ray retries the Task
Task completes on the replacement worker
```

The Task restarted from the beginning. It did not resume from its interrupted instruction.

### Actor recovery

A long-running Actor method was interrupted by deleting its worker Pod.

Observed sequence:

```text
Actor method starts
Worker Pod is deleted
Actor process is lost
KubeRay recreates worker capacity
Ray reconstructs the Actor
Actor constructor runs again
Actor method is retried
Method completes on replacement worker
```

Actor in-memory state reset during reconstruction. This proved that Actor memory is runtime state, not durable application state.

## Image Optimization

The dedicated CPU-only Ray image reduced content size from approximately:

```text
Full agent image: 3.62 GB
Ray SRE image:    1.48 GB
```

Approximate reduction:

```text
59 percent
```

CPU-only PyTorch validation:

```text
Torch:              2.14.1+cpu
CUDA available:     False
Torch CUDA version: None
```

MiniLM was also validated with networking disabled.

## Final Deployment Validation

API contract tests:

```text
12/12 passed
```

Full broad graph invocation:

```text
PASS
```

Five deployed broad investigations:

```text
Request 1: 1848.49 ms
Request 2:  251.11 ms
Request 3:  255.34 ms
Request 4: 1167.31 ms
Request 5: 2144.99 ms
```

All five returned:

```text
route = broad
retrieved documents = 3
```

Prometheus recorded:

```text
Broad samples:     6
Average latency:   3.10753 seconds
p50 estimate:      1.50 seconds
p95 estimate:      approximately 17 seconds
```

The p95 estimate is low confidence because only six histogram samples existed and the buckets were coarse. The directly observed final requests ranged from approximately 0.251 seconds to 2.145 seconds.

## Key Engineering Lessons

1. Benchmark before distributing a workload.
2. Distributed execution is not automatically faster.
3. Dependency boundaries strongly affect worker startup cost.
4. Persistent Actors are useful for expensive model and client initialization.
5. Actor memory is not durable state.
6. Retries imply possible duplicate execution.
7. Retryable side-effecting operations require idempotency protection.
8. Kubernetes schedules Pods, while Ray schedules Python Tasks and Actors.
9. Failure recovery must be tested rather than assumed.
10. Least-privilege read-only access is the correct boundary for an advisory AI SRE system.

## Documentation

- [Phase 3 Architecture](architecture.md)
- [Ray Benchmarks and Failure Engineering](ray-benchmarks-and-failure-engineering.md)
- [Operations Runbook](operations-runbook.md)

## Technical Debt

Accepted technical debt:

```text
1. Align Python patch versions between the FastAPI Ray Client and Ray runtime.
2. Investigate removing inherited cupy-cuda12x from the CPU-only Ray image.
3. Consider lazy-loading the host-side Qdrant retriever.
4. Collect more broad-route latency samples.
5. Refine Prometheus histogram buckets around the observed latency range.
6. Add durable checkpointing before storing workflow-critical state in Actors.
```

Observed Python versions:

```text
FastAPI Ray Client: Python 3.12.3
Ray Runtime:        Python 3.12.14
```

## Completion Criteria

Phase 3 is complete because:

```text
Kubernetes Nodes are Ready
AI SRE Agent is 1/1 Running
/health returns HTTP 200
/capabilities includes broad
/metrics is scraped
RayCluster status is ready
Ray Worker is available
KnowledgeActor status is ready
Broad investigation succeeds
Prometheus broad route counter increments
Read-only RBAC remains enforced
API tests report 12 passed
```

## Final Outcome

Phase 3 delivers a distributed, observable, read-only AI SRE investigation platform.

The final architecture combines:

```text
FastAPI
LangGraph
Qwen and vLLM
Prometheus
Kubernetes
Qdrant
MiniLM
Ray
KubeRay
```

The architecture is frozen for Phase 3.

Future capabilities should be developed as a new phase rather than continuously expanding this implementation.
