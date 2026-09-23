# Phase 2 Summary - Production-Grade AI Inference Platform

## Overview

Phase 2 evolved the project from a functional single-node AI application into a measurable, observable, multi-node, multi-GPU, and multi-model inference platform.

The work covered:

- vLLM inference observability
- Single-GPU performance benchmarking
- Service Level Objectives and error budgets
- API security and ingress design
- Overload-handling strategy
- Autoscaling and capacity-planning strategy
- Two-node MicroK8s expansion
- Dual-GPU horizontal scaling
- Multi-model serving
- Failure engineering
- RAG quality evaluation
- Cost and goodput analysis

The platform was tested through controlled load generation, node expansion, pod deletion, node maintenance, EC2 interruption, model-specific routing, retrieval evaluation, and cost analysis.

---

# Phase 2 Objectives

The primary objectives were to:

1. Preserve the stable Phase 1 baseline.
2. Expose inference-specific operational metrics.
3. Establish a reproducible single-GPU performance baseline.
4. Define reliability and latency objectives.
5. Document production ingress and security requirements.
6. Define overload and admission-control behavior.
7. Define scaling signals for stateless and GPU workloads.
8. Expand the cluster to two GPU nodes.
9. Validate horizontal inference scaling.
10. Serve different models on separate GPUs.
11. Measure failure detection and recovery behavior.
12. Evaluate RAG retrieval and answer quality.
13. Quantify infrastructure cost and useful serving capacity.

---

# Final Platform Architecture

## Infrastructure

```text
AWS VPC
│
├── Node 1: g5.xlarge
│   ├── Ubuntu 24.04
│   ├── MicroK8s v1.35.6
│   ├── NVIDIA A10G
│   ├── MicroK8s control plane
│   ├── Qwen inference workload
│   ├── RAG API
│   ├── Qdrant
│   ├── Open WebUI
│   └── Observability stack
│
└── Node 2: g5.xlarge
    ├── Ubuntu 24.04
    ├── MicroK8s v1.35.6
    ├── NVIDIA A10G
    ├── MicroK8s worker
    └── Phi-3 or secondary Qwen inference workload
```

## Platform Services

```text
Open WebUI
    │
    ├── Custom RAG API
    │       │
    │       ├── SentenceTransformer embeddings
    │       ├── Qdrant vector search
    │       └── Qwen generation backend
    │
    ├── vllm-qwen Service
    │       └── Qwen/Qwen2.5-1.5B-Instruct
    │
    └── vllm-phi3 Service
            └── microsoft/Phi-3-mini-4k-instruct
```

## Observability

```text
vLLM Metrics
Kubernetes Metrics
Node Metrics
GPU Metrics
Application Logs
Distributed Traces
        │
        ├── Prometheus
        ├── Grafana
        ├── Loki
        ├── Tempo
        └── OpenTelemetry Collector
```

---

# Phase Completion Summary

| Phase | Capability | Status | Evidence Type |
|---|---|---|---|
| 2.0 | Freeze and reproduce Phase 1 | Complete | Baseline and documentation |
| 2.1 | Inference metrics and dashboard | Practically complete | Runtime validation |
| 2.2 | Single-node performance baseline | Practically complete | Locust benchmarks |
| 2.3 | SLOs and error budget | Complete | Engineering definitions |
| 2.4 | Production API entry point | Design complete | Architecture documentation |
| 2.5 | Overload handling | Design complete | Strategy documentation |
| 2.6 | Stateless HPA | Design complete | Autoscaling strategy |
| 2.7 | KEDA and GPU constraint demo | Partially validated | GPU constraint demonstrated |
| 2.8 | Add second g5.xlarge | Practically complete | Two Ready GPU nodes |
| 2.9 | Two-replica vLLM | Practically complete | Dual-GPU benchmark |
| 2.10 | Multi-model serving | Practically complete | One model per GPU |
| 2.11 | Failure engineering | Practically complete | Measured failure tests |
| 2.12 | RAG quality evaluation | Practically complete | Quality metrics |
| 2.13 | Cost and goodput | Complete | Cost and capacity analysis |

---

# Phase 2.0 - Baseline Protection

## Objective

Preserve the stable Phase 1 implementation before introducing production-oriented changes.

## Outcome

The Phase 1 platform was preserved in the repository and backed up before beginning Phase 2 changes.

Phase 2 work was performed using the existing EC2 environment, with the intent to commit the completed Phase 2 state to a dedicated Git branch.

## Evidence

- Stable Phase 1 code preserved
- Existing manifests retained
- Phase 2 documentation organized under `docs/phase-2`
- Benchmark artifacts preserved separately

---

# Phase 2.1 - Inference Metrics and Dashboard

## Objective

Expose and visualize AI inference metrics beyond standard Kubernetes infrastructure metrics.

## Metrics Validated

The vLLM endpoint exposed:

```text
vllm:num_requests_running
vllm:num_requests_waiting
vllm:request_success_total
vllm:time_to_first_token_seconds
vllm:inter_token_latency_seconds
vllm:e2e_request_latency_seconds
vllm:request_queue_time_seconds
vllm:request_prompt_tokens
vllm:request_generation_tokens
vllm:kv_cache_usage_perc
vllm:prefix_cache_hits_total
vllm:prefix_cache_queries_total
```

## Prometheus Integration Issue

The vLLM metrics endpoint worked directly, but Prometheus initially returned:

```text
Empty query result
```

Root cause:

```text
The vLLM Service had no metadata labels.
```

The ServiceMonitor expected:

```yaml
selector:
  matchLabels:
    app: vllm
```

but the Service did not have:

```yaml
metadata:
  labels:
    app: vllm
```

After adding the Service label and naming the Service port `http`, Prometheus discovered the target and Grafana displayed inference metrics.

## Outcome

A Grafana dashboard was created with:

- Running requests
- Waiting requests
- Requests per second
- P95 TTFT
- P95 TPOT
- P95 end-to-end latency
- Prompt-token throughput
- Generation-token throughput
- Queue time
- KV-cache utilization
- Prefix-cache hit ratio

## Status

```text
Practically complete
```

---

# Phase 2.2 - Single-GPU Performance Baseline

## Objective

Measure the latency, throughput, reliability, and scheduler behavior of a single A10G-backed vLLM replica.

## Benchmark Configuration

```text
Instance: AWS g5.xlarge
GPU: NVIDIA A10G
Model: Qwen/Qwen2.5-1.5B-Instruct
Load Generator: Locust 2.46.5
Max Output Tokens: 128
Artificial Think Time: 0
```

## Normal-to-Moderate Load Results

| Concurrency | Average Latency | P95 | P99 | Throughput |
|---:|---:|---:|---:|---:|
| 1 | 827 ms | 1.0 s | 1.1 s | 0.43 req/s |
| 2 | 835 ms | 1.1 s | 1.1 s | 2.39 req/s |
| 4 | 838 ms | 1.1 s | 1.1 s | 4.76 req/s |
| 8 | 858 ms | 1.1 s | 1.1 s | 9.30 req/s |
| 16 | 883 ms | 1.1 s | 1.2 s | 18.05 req/s |
| 32 | 990 ms | 1.2 s | 1.3 s | 32.22 req/s |

## Extreme-Load Result

At 1,024 concurrent users:

```text
Completed Requests: 12,152
Failures: 0
Success Rate: 100%
Throughput: 67.52 req/s
Average Latency: 14.493 s
Median Latency: 15.0 s
P95 Latency: 16.0 s
P99 Latency: 16.0 s
Maximum Latency: 17.9 s
```

Observed scheduler behavior:

```text
Running Requests: approximately 254
Waiting Requests: approximately 767
```

## Key Finding

The single-GPU platform did not crash under extreme load.

Instead, vLLM limited active execution and queued excess requests. The service degraded through controlled scheduler backpressure rather than request loss.

## Status

```text
Practically complete
```

---

# Phase 2.3 - SLOs and Error Budget

## Objective

Define measurable service-quality targets based on the Phase 2.2 benchmark.

## Normal Operating Region

```text
1-32 concurrent users
```

## Defined SLOs

```text
P95 End-to-End Latency: < 2 seconds
P99 End-to-End Latency: < 3 seconds
P95 TTFT: < 1 second
P95 TPOT: < 100 milliseconds
P95 Queue Time: < 500 milliseconds
Error Rate: < 1%
```

## Goodput Definition

Goodput was defined as successful requests that return a valid answer and satisfy the applicable latency objective.

## Outcome

The 32-user benchmark passed the measured end-to-end latency and error-rate objectives:

```text
P95: 1.2 seconds
P99: 1.3 seconds
Error Rate: 0%
```

## Status

```text
Complete
```

---

# Phase 2.4 - Production API Entry Point

## Objective

Define a controlled production entry point using Traefik, authentication, rate limits, request limits, and timeouts.

## Completed Design Work

The following were documented:

- Current service-exposure model
- Traefik ingress-controller role
- Internal-only ClusterIP services
- Kubernetes Secret usage
- Observability-service isolation
- Future TLS and authentication requirements

## Current Security Posture

The following services remain internal:

```text
vLLM
RAG API
Qdrant
Prometheus
Grafana
Loki
Tempo
OpenTelemetry Collector
```

The Hugging Face token is stored in:

```text
Kubernetes Secret: vllm/hf-token
```

## Deferred Implementation

The following roadmap items were documented but not fully implemented:

- Public TLS endpoint
- API-key enforcement
- Rate limiting
- Request-size limits
- Production proxy timeouts
- External DNS
- OAuth or OIDC

## Status

```text
Design complete
Implementation deferred
```

---

# Phase 2.5 - Overload Handling

## Objective

Define bounded admission and predictable overload behavior.

## Practical Evidence

Phase 2.2 demonstrated scheduler-level backpressure:

```text
Approximately 254 active requests
Approximately 767 waiting requests
0 failures
```

## Completed Design Work

The overload strategy documented:

- Queue depth thresholds
- Queue-time thresholds
- TTFT thresholds
- End-to-end latency thresholds
- Future request rejection using HTTP 429 or 503
- Admission-control requirements
- Preference for fast rejection over uncontrolled latency growth

## Deferred Implementation

The following were not implemented:

- Bounded gateway queue
- Maximum in-flight request enforcement
- HTTP 429 admission response
- HTTP 503 overload response
- Queue timeout
- Request deadline and cancellation

## Status

```text
Design complete
Implementation deferred
```

---

# Phase 2.6 - Stateless HPA

## Objective

Demonstrate scale-up and scale-down of stateless platform services.

## Completed Design Work

The autoscaling strategy defined:

- Queue-depth scaling signals
- Queue-time scaling signals
- TTFT scaling signals
- GPU-utilization considerations
- Scale-out and scale-in conditions
- Separation between CPU workload scaling and GPU workload scaling

## Key Design Conclusion

AI inference workloads should not scale only on CPU utilization.

Preferred signals include:

```text
vllm:num_requests_waiting
vllm:request_queue_time_seconds
vllm:time_to_first_token_seconds
vllm:num_requests_running
Token throughput
```

## Deferred Implementation

A practical HPA scale-up and scale-down experiment for the RAG API or API gateway was not executed.

## Status

```text
Design complete
Implementation deferred
```

---

# Phase 2.7 - KEDA and GPU Constraint Demonstration

## Objective

Use Prometheus-driven scaling and demonstrate the physical GPU scheduling constraint.

## Practical GPU Constraint Evidence

When the original vLLM Deployment was scaled from one replica to two replicas, the second pod remained Pending.

Scheduler result:

```text
0/2 nodes are available:

1 Insufficient nvidia.com/gpu
1 node did not match PersistentVolume node affinity
```

This proved:

- Each vLLM replica requested one full GPU.
- A second replica could not fit on a single-GPU node.
- The existing hostpath PVC was tied to Node 1.
- Additional GPU capacity and separate node-local storage were required.

## Completed Design Work

Prometheus-based scaling triggers and GPU-capacity limitations were documented.

## Deferred Implementation

The following were not executed:

- KEDA installation
- KEDA `ScaledObject`
- Prometheus-triggered RAG scaling
- KEDA activation and cooldown validation

## Status

```text
GPU constraint practically demonstrated
KEDA implementation deferred
```

---

# Phase 2.8 - Add Second g5.xlarge

## Objective

Expand the MicroK8s cluster to two Ready GPU nodes.

## Worker Configuration

```text
Instance Type: g5.xlarge
OS: Ubuntu 24.04.5 LTS
Private IP: 172.31.6.36
GPU: NVIDIA A10G
NVIDIA Driver: 595.91.07
CUDA Compatibility: 13.2
MicroK8s: v1.35.6
Role: Worker
```

## Primary Configuration

```text
Instance Type: g5.xlarge
Private IP: 172.31.7.23
GPU: NVIDIA A10G
NVIDIA Driver: 595.84
CUDA Compatibility: 13.2
MicroK8s: v1.35.6
Role: Control Plane and Worker
```

## Validation

Both nodes reported:

```text
STATUS: Ready
nvidia.com/gpu: 1
```

Total cluster GPU capacity:

```text
2 NVIDIA A10G GPUs
```

GPU Operator automatically deployed and validated the required components on the second node:

- NVIDIA Container Toolkit
- NVIDIA Device Plugin
- GPU Feature Discovery
- DCGM Exporter
- Operator Validator
- CUDA Validator

## Status

```text
Practically complete
```

---

# Phase 2.9 - Two-Replica vLLM

## Objective

Run one Qwen vLLM replica on each GPU and validate routed traffic and horizontal scaling.

## Storage Constraint

The original shared `hf-cache` PVC used MicroK8s hostpath storage and was bound to Node 1.

A second replica could not mount the same node-local PVC on Node 2.

## Solution

Separate deployments and PVCs were created:

```text
Primary Qwen
├── Deployment: vllm
├── Node: ip-172-31-7-23
└── PVC: hf-cache

Secondary Qwen
├── Deployment: vllm-secondary
├── Node: ip-172-31-6-36
└── PVC: hf-cache-secondary
```

## Routing Validation

Before the routing test:

```text
Primary completed requests: 9,842
Secondary completed requests: 0
```

After the routing test:

```text
Primary completed requests: 10,646
Secondary completed requests: 836
```

Requests handled during the test:

```text
Primary: 804
Secondary: 836
```

Approximate split:

```text
Primary: 49%
Secondary: 51%
```

## Dual-GPU 1,024-User Benchmark

```text
Completed Requests: 24,414
Failures: 0
Success Rate: 100%
Throughput: 135.63 req/s
Average Latency: 7.370 s
Median Latency: 7.5 s
P95 Latency: 8.5 s
P99 Latency: 8.8 s
Maximum Latency: 9.248 s
```

Observed active scheduler capacity:

```text
Primary Replica: approximately 254-256 active requests
Secondary Replica: approximately 251-256 active requests
Total: approximately 510 active requests
```

## Single-GPU Versus Dual-GPU

| Metric | Single GPU | Dual GPU | Change |
|---|---:|---:|---:|
| Throughput | 67.52 req/s | 135.63 req/s | 2.01x |
| Average Latency | 14.493 s | 7.370 s | 49.1% lower |
| Median Latency | 15.0 s | 7.5 s | 50% lower |
| P95 Latency | 16.0 s | 8.5 s | 46.9% lower |
| P99 Latency | 16.0 s | 8.8 s | 45% lower |
| Active Requests | Approximately 254 | Approximately 510 | Approximately 2x |
| Failures | 0 | 0 | Maintained |

## Key Finding

The second A10G produced approximately linear horizontal scaling while preserving a 100% request success rate.

## Status

```text
Practically complete
```

---

# Phase 2.10 - Multi-Model Serving

## Objective

Serve a different model on each GPU and provide explicit model-specific routing.

## Final Model Placement

```text
Node 1:
Qwen/Qwen2.5-1.5B-Instruct
Service: vllm-qwen
Maximum Context: 8,192 tokens

Node 2:
microsoft/Phi-3-mini-4k-instruct
Service: vllm-phi3
Maximum Context: 4,096 tokens
```

## Phi-3 Compatibility Issue

The Phi-3 deployment initially failed because it inherited:

```text
--max-model-len 8192
```

The model supports:

```text
4,096 tokens
```

The deployment was corrected to:

```text
--max-model-len 4096
```

Qwen-specific tool-parser arguments were also removed from the Phi-3 configuration.

## Dedicated Services

```text
vllm-qwen
└── Qwen pod only

vllm-phi3
└── Phi-3 pod only
```

## Model Validation

The Qwen endpoint returned:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

The Phi-3 endpoint returned:

```text
microsoft/Phi-3-mini-4k-instruct
```

Both models generated valid responses from their dedicated Services.

## Open WebUI

Open WebUI was configured with both OpenAI-compatible backend URLs.

Open WebUI connectivity to both backends was validated from inside the pod.

The UI continued to display only the existing Qwen model entry, but backend multi-model routing was fully functional.

## Status

```text
Practically complete
```

---

# Phase 2.11 - Failure Engineering

## Objective

Measure Kubernetes self-healing, worker-node failure detection, and GPU-model recovery behavior.

## Test 1: Qwen Pod Deletion

```text
Recovery Type: Automatic
Time to Ready: 112 seconds
Manual Intervention: None
```

## Test 2: Phi-3 Pod Deletion

```text
Recovery Type: Automatic
Time to Ready: 103 seconds
Manual Intervention: None
```

## Test 3: Worker Node Drain

The worker node was drained using:

```text
--ignore-daemonsets
--delete-emptydir-data
```

Observed:

```text
Node cordoned
Phi-3 pod evicted
Replacement pod created
Replacement remained Pending
```

Reason:

```text
Node 1 did not match the Phi-3 node selector.
Node 2 was SchedulingDisabled.
```

After uncordoning Node 2:

```text
Phi-3 recovery time: 102 seconds
```

## Test 4: Worker EC2 Node Loss

The worker EC2 instance was stopped.

Measured:

```text
Node failure detection: 43 seconds
Node Ready after restart: 29 seconds
Phi-3 service recovery after start: approximately 225 seconds
```

## Failure Summary

| Scenario | Recovery Type | Recovery Time |
|---|---|---:|
| Qwen pod deletion | Automatic | 112 s |
| Phi-3 pod deletion | Automatic | 103 s |
| Worker drain | Manual uncordon required | 102 s after uncordon |
| Worker node loss | Node restart required | 225 s |

## Key Finding

The platform provides:

```text
Pod-level self-healing
```

but not:

```text
Node-level model high availability
```

The limitation is caused by:

- One GPU per model
- Explicit node selectors
- Node-local hostpath storage
- No redundant GPU capacity for each model

## Status

```text
Practically complete
```

---

# Phase 2.12 - RAG Quality Evaluation

## Objective

Measure retrieval effectiveness, answer correctness, groundedness, refusal behavior, and hallucination resistance.

## Corpus

Initial Qdrant points:

```text
4
```

The corpus was expanded with platform architecture, benchmark, failure, and operations facts.

The 30-item expansion dataset was accidentally ingested twice, resulting in:

```text
64 total Qdrant points
```

The duplicate vectors reduced retrieval diversity but did not prevent evaluation.

## Evaluation Dataset

Ten controlled questions were executed:

```text
5 exact factual questions
3 paraphrased questions
2 unsupported questions
```

## Results

| Metric | Result |
|---|---:|
| Retrieval Accuracy | 87.5% |
| Answer Accuracy | 80% |
| Groundedness | 90% |
| Correct Refusal Rate | 100% |
| Unsupported-Question Hallucination Rate | 0% |
| Context-Contradiction Rate | 10% |

## Retrieval Failure

Question:

```text
Which model is deployed on Node 2?
```

The relevant Phi-3 source was not retrieved in the Top-3 context, and the model correctly responded that the information was unavailable.

## Grounding Failure

Question:

```text
Does the platform currently provide node-level high availability?
```

The correct negative source was retrieved, but the model answered affirmatively.

This demonstrated a generation-grounding failure rather than a retrieval failure.

## Key Finding

The RAG pipeline performed strongly for:

- Quantitative facts
- Explicit platform facts
- Unsupported-question refusal

The primary improvement areas are:

- Deduplicated ingestion
- Improved retrieval diversity
- Stronger grounding instructions
- Automated evaluation
- Similarity-score reporting
- Larger question sets

## Status

```text
Practically complete
```

---

# Phase 2.13 - Cost and Goodput Analysis

## Objective

Compare infrastructure cost, successful throughput, and SLO-aware serving capacity.

## Cost Model

```text
AWS g5.xlarge On-Demand Linux:
$1.006 per instance-hour
```

## Extreme-Load Cost Comparison

| Metric | Single GPU | Dual GPU |
|---|---:|---:|
| Hourly Cost | $1.006 | $2.012 |
| Throughput | 67.52 req/s | 135.63 req/s |
| Requests per Hour | 243,072 | 488,268 |
| Cost per 1,000 Requests | $0.00414 | $0.00412 |
| Requests per Dollar | 241,622 | 242,678 |
| Success Rate | 100% | 100% |

## Scaling Efficiency

```text
Throughput Scaling: 2.01x
Infrastructure Scaling: 2.0x
Scaling Efficiency: approximately 100%
```

## Normal-Load Goodput Baseline

At 32 users on one GPU:

```text
Throughput: 32.22 req/s
Average Latency: 0.990 s
P95 Latency: 1.2 s
P99 Latency: 1.3 s
Failures: 0
```

This passed the measured end-to-end latency and error-rate objectives.

## Key Finding

The second GPU doubled infrastructure cost and delivered approximately double throughput.

As a result:

```text
Cost per successful request remained essentially unchanged.
```

At the same time, the dual-GPU configuration reduced overload latency by approximately half.

## Status

```text
Complete
```

---

# Major Engineering Findings

## 1. vLLM Degraded Gracefully Under Overload

At 1,024 single-GPU users:

```text
Approximately 254 requests were active.
Approximately 767 requests waited.
No requests failed.
```

The engine protected stability through scheduler backpressure.

---

## 2. A Second GPU Produced Nearly Linear Scaling

Moving from one A10G to two A10Gs produced:

```text
2.01x throughput
Approximately 49% lower average latency
Approximately 47% lower P95 latency
Approximately 2x active scheduler capacity
```

---

## 3. Cost Efficiency Remained Stable

```text
Single GPU:
$0.00414 per 1,000 successful overload requests

Dual GPU:
$0.00412 per 1,000 successful overload requests
```

Horizontal expansion delivered proportional capacity for proportional cost.

---

## 4. Node-Local Storage Affected Multi-Node Scheduling

MicroK8s hostpath PVCs were tied to the provisioning node.

This required:

```text
One cache PVC per vLLM deployment
```

and prevented automatic model relocation during worker-node failure.

---

## 5. Pod Recovery Was Automatic but Slow

GPU inference workloads recovered in approximately:

```text
103-112 seconds
```

The primary delay came from:

- Container startup
- Model-weight loading
- CUDA initialization
- KV-cache allocation
- CUDA-graph capture
- Readiness probe completion

---

## 6. Node-Level HA Requires Redundant GPU Capacity

The platform provides Kubernetes pod self-healing but cannot relocate a model when:

- The only eligible GPU node fails.
- The deployment is pinned to a specific node.
- The model cache uses node-local storage.

True model-level high availability requires at least two eligible GPU nodes per model.

---

## 7. Retrieval Success Did Not Guarantee Grounded Generation

The RAG evaluation demonstrated that relevant context may be retrieved while the generation model still contradicts the context.

Platform-quality evaluation must therefore measure:

```text
Retrieval
Answer correctness
Groundedness
Refusal behavior
```

rather than retrieval alone.

---

# Operational Metrics Established

The platform now exposes or measures:

## Inference Metrics

- Time to First Token
- Time per Output Token
- End-to-end latency
- Queue time
- Running requests
- Waiting requests
- Request success rate
- Prompt-token throughput
- Generation-token throughput
- KV-cache utilization
- Prefix-cache hit ratio

## Reliability Metrics

- Pod recovery time
- Node failure-detection time
- Node Ready recovery time
- Model service restoration time
- Scheduling failure reason

## Quality Metrics

- Retrieval accuracy
- Answer accuracy
- Groundedness
- Correct-refusal rate
- Hallucination rate
- Context-contradiction rate

## Cost Metrics

- Hourly infrastructure cost
- Requests per hour
- Requests per dollar
- Cost per 1,000 requests
- Horizontal scaling efficiency

---

# Repository Evidence

Phase 2 documentation includes:

```text
docs/phase-2/
├── api-security.md
├── autoscaling-strategy.md
├── bounded-queue-overload-handling.md
├── capacity-planning.md
├── cost-and-goodput-analysis.md
├── dual-gpu-scaling-validation.md
├── error-budget.md
├── failure-engineering.md
├── ingress-architecture.md
├── load-balancing-strategy.md
├── multi-model-serving.md
├── multi-replica-routing.md
├── phase2-performance-baseline.md
├── phase2-rag-dataset.json
├── rag-quality-evaluation.md
├── scaling-thresholds.md
├── scaling-triggers.md
├── slos.md
├── benchmarks/
└── images/
```

Supporting manifests include:

```text
manifests/
├── load-testing/
├── observability/
├── openwebui/
├── qdrant/
├── rag-app/
└── vllm/
```

---

# Deferred Work

The following items were intentionally deferred or left optional:

## Production Ingress Implementation

- TLS certificates
- External DNS
- API-key enforcement
- Rate limiting
- Request-size limits
- Production timeout policies

## Admission Control

- Bounded queues
- Maximum in-flight request controls
- Predictable HTTP 429 or 503 responses
- Queue deadlines
- Request cancellation

## Autoscaling Implementation

- Stateless RAG HPA
- KEDA installation
- Prometheus `ScaledObject`
- KEDA cooldown testing
- Automated GPU capacity expansion

## High Availability

- Redundant control plane
- Shared or replicated model storage
- Multiple eligible GPU nodes per model
- Automated model relocation
- Node-level model failover

## Evaluation Automation

- Automated RAG scoring
- Retrieval-score thresholds
- Reranking
- Idempotent ingestion
- Model-quality regression gates

## Optional Engine Comparison

- vLLM versus SGLang
- Controlled engine benchmark
- Engine-specific cost comparison
- Engine-specific SLO goodput

---

# Recommended Production Improvements

## Short-Term

1. Make RAG ingestion idempotent.
2. Restrict the original `vllm` Service to the primary Qwen deployment.
3. Add explicit model labels to every model deployment.
4. Add model-specific Grafana variables.
5. Add alerts for queue depth and TTFT.
6. Preserve exact token totals during future benchmarks.
7. Pin tested image versions instead of using `latest`.

## Medium-Term

1. Add a production AI gateway.
2. Implement authentication and rate limits.
3. Add bounded request admission.
4. Add HPA for stateless services.
5. Add KEDA for Prometheus-driven scaling.
6. Introduce shared or replicated model storage.
7. Add redundant GPU capacity for critical models.
8. Automate RAG quality evaluation.

## Long-Term

1. Implement multi-tenant quotas.
2. Add model onboarding workflows.
3. Add canary model deployments.
4. Add quality-adjusted goodput.
5. Add cost per correct and grounded answer.
6. Compare inference engines.
7. Introduce GitOps and policy enforcement.
8. Add production control-plane high availability.

---

# Portfolio Outcomes

Phase 2 demonstrates practical experience with:

- Kubernetes GPU scheduling
- Multi-node MicroK8s operations
- NVIDIA GPU Operator
- vLLM inference serving
- Multi-replica routing
- Multi-model deployment
- Qdrant-backed RAG
- Open WebUI
- Prometheus and Grafana
- Loki and Tempo
- OpenTelemetry
- Locust load testing
- SLOs and error budgets
- Failure engineering
- Capacity planning
- RAG quality evaluation
- Cost-efficiency analysis

---

# Key Quantitative Outcomes

```text
Single-GPU Throughput:
67.52 requests/second at 1,024 users

Dual-GPU Throughput:
135.63 requests/second at 1,024 users

Throughput Scaling:
2.01x

Average Latency Improvement:
Approximately 49%

P95 Latency Improvement:
Approximately 47%

Pod Recovery:
103-112 seconds

Worker Failure Detection:
43 seconds

Worker-Outage Service Recovery:
Approximately 225 seconds after restart

RAG Retrieval Accuracy:
87.5%

RAG Answer Accuracy:
80%

RAG Groundedness:
90%

Unsupported-Question Hallucination Rate:
0%

Single-GPU Cost per 1,000 Requests:
Approximately $0.00414

Dual-GPU Cost per 1,000 Requests:
Approximately $0.00412
```

---

# Phase 2 Exit Criteria

Phase 2 is considered complete when:

- Stable Phase 1 baseline is preserved.
- Inference metrics are observable.
- Single-GPU performance is benchmarked.
- SLOs and error budgets are defined.
- Production API requirements are documented.
- Overload behavior is measured or designed.
- Scaling signals are defined.
- Two GPU nodes are schedulable.
- Two vLLM replicas route traffic.
- Multi-model serving is validated.
- Failure recovery is measured.
- RAG quality metrics are recorded.
- Cost and goodput are analyzed.
- Findings and limitations are documented.

---

# Exit-Criteria Validation

| Exit Criterion | Status |
|---|---|
| Phase 1 baseline preserved | Pass |
| vLLM inference metrics visible | Pass |
| Grafana inference dashboard functional | Pass |
| Single-GPU baseline completed | Pass |
| Extreme-load behavior measured | Pass |
| SLOs and error budget documented | Pass |
| API security and ingress design documented | Pass |
| Overload strategy documented | Pass |
| Scaling triggers documented | Pass |
| Second GPU node added | Pass |
| Two GPUs schedulable | Pass |
| Two-replica routing validated | Pass |
| Dual-GPU benchmark completed | Pass |
| Multi-model serving validated | Pass |
| Pod recovery measured | Pass |
| Worker-node failure measured | Pass |
| RAG quality evaluated | Pass |
| Cost efficiency calculated | Pass |
| Platform limitations documented | Pass |

---

# Final Phase Status

```text
Phase 2 - Production-Grade AI Inference Platform

Status: COMPLETE
```

---

# Final Conclusion

Phase 2 transformed the project from a functional single-node AI application into a measured and operationally validated AI inference platform.

The completed platform demonstrated:

- Multi-node GPU orchestration
- Approximately linear dual-GPU scaling
- Controlled overload behavior
- Multi-model serving
- Kubernetes pod self-healing
- Measured worker-node recovery
- Observable inference characteristics
- Quantified RAG quality
- Stable cost per successful request during horizontal scaling

The strongest result was the dual-GPU benchmark:

```text
Throughput increased from 67.52 to 135.63 requests per second.
Average overload latency decreased from 14.493 to 7.370 seconds.
P95 overload latency decreased from 16.0 to 8.5 seconds.
No request failures occurred.
```

The most important reliability finding was that pod-level recovery worked automatically, while node-level model high availability remained limited by dedicated GPU placement and node-local storage.

The most important quality finding was that retrieval performance was strong, but relevant retrieval did not always guarantee grounded generation.

The most important cost finding was that the second GPU delivered proportional performance for proportional cost, preserving cost efficiency while significantly improving throughput and latency.

Phase 2 therefore established a strong technical foundation for future work in production access control, admission control, autoscaling, multi-tenancy, GitOps, model governance, and quality-aware serving.
