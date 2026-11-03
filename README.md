# Production-Grade GPU AI Platform on MicroK8s

A production-style AI inference platform built on AWS EC2 and MicroK8s with NVIDIA A10G GPUs, vLLM, multi-model serving, Retrieval-Augmented Generation, Open WebUI, Qdrant, and a complete LGTM observability stack.

The project evolved from a single-node GPU environment into a two-node, dual-GPU AI platform with performance benchmarking, Service Level Objectives, failure engineering, RAG quality evaluation, and cost-efficiency analysis.

---

## Project Status

```text
Phase 1: COMPLETE
Phase 2: COMPLETE
```
---

## Project Overview

This project demonstrates the design, deployment, operation, scaling, observability, reliability testing, and cost analysis of a production-style AI inference platform running on Kubernetes.

The platform started as a single-node deployment with:

- One NVIDIA A10G GPU
- One vLLM inference replica
- Qwen2.5-1.5B-Instruct
- Open WebUI
- Qdrant
- A custom FastAPI RAG application
- Prometheus, Grafana, Loki, Tempo, and OpenTelemetry

Phase 2 expanded the platform into:

- A two-node MicroK8s cluster
- Two NVIDIA A10G GPUs
- Dual-GPU horizontal inference scaling
- Multi-model serving
- Model-specific Kubernetes Services
- Failure detection and recovery testing
- RAG quality measurement
- SLO and error-budget engineering
- Cost and goodput analysis

---

## Phase 2 Highlights

Phase 2 transformed the platform from a single-node AI deployment into a measurable, multi-node, production-style AI inference platform.

Key achievements:

- Expanded the MicroK8s cluster from one node to two nodes
- Added a second AWS g5.xlarge GPU instance
- Registered two schedulable NVIDIA A10G GPUs
- Deployed one vLLM replica per GPU
- Achieved approximately 2.01x throughput scaling
- Reduced average overload latency by approximately 49%
- Reduced P95 overload latency by approximately 47%
- Maintained a 100% success rate in 1,024-user stress tests
- Implemented Qwen and Phi-3 multi-model serving
- Added explicit model-specific Kubernetes Services
- Validated Kubernetes pod self-healing
- Measured worker-node failure detection and recovery
- Evaluated RAG retrieval accuracy and groundedness
- Calculated cost per request and requests per dollar
- Established SLOs, error budgets, and capacity thresholds

---

## Architecture

```text
                                  Users
                                    │
                                    ▼
                              Open WebUI
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
       Custom RAG API          vllm-qwen              vllm-phi3
             │                      │                      │
             │                      │                      │
             ▼                      ▼                      ▼
     SentenceTransformer    Qwen2.5-1.5B-Instruct   Phi-3-mini-4k
         Embeddings           Node 1 / GPU 1         Node 2 / GPU 2
             │
             ▼
          Qdrant
       Vector Database
             │
             └─────────────── Retrieved Context
```

### Observability Architecture

```text
Application Metrics
vLLM Metrics
Kubernetes Metrics
GPU Metrics
Logs
Traces
        │
        ├── Prometheus
        ├── Grafana
        ├── Loki
        ├── Promtail
        ├── Tempo
        └── OpenTelemetry Collector
```

---

## Infrastructure

### Cloud Platform

- AWS EC2
- Private VPC networking
- Shared security group for cluster communication
- On-Demand Linux instances

### Kubernetes Platform

- MicroK8s v1.35.6
- Kubernetes
- Containerd
- Helm
- Calico networking
- MicroK8s hostpath storage

### GPU Infrastructure

- Two NVIDIA A10G GPUs
- NVIDIA GPU Operator
- NVIDIA Container Toolkit
- NVIDIA Device Plugin
- GPU Feature Discovery
- DCGM Exporter
- CUDA validation workloads

---

## Cluster Topology

### Node 1

```text
Hostname: ip-172-31-7-23
Instance Type: AWS g5.xlarge
Operating System: Ubuntu 24.04 LTS
GPU: NVIDIA A10G
GPU Memory: Approximately 24 GB
Role: MicroK8s Control Plane and Worker
```

Primary workloads:

- Qwen vLLM inference service
- Custom RAG API
- Qdrant
- Open WebUI
- Redis
- Prometheus
- Grafana
- Loki
- Tempo
- OpenTelemetry Collector

### Node 2

```text
Hostname: ip-172-31-6-36
Instance Type: AWS g5.xlarge
Operating System: Ubuntu 24.04 LTS
GPU: NVIDIA A10G
GPU Memory: Approximately 24 GB
Role: MicroK8s Worker
```

Primary workloads:

- Secondary Qwen replica during dual-GPU testing
- Microsoft Phi-3 during multi-model serving
- GPU Operator node components
- Node Exporter
- Promtail
- DCGM Exporter

### Total Cluster Capacity

```text
Nodes: 2
vCPUs: 8
System Memory: Approximately 32 GB
GPUs: 2 NVIDIA A10Gs
Total GPU Memory: Approximately 48 GB
```

---

## Technology Stack

### Infrastructure

- AWS EC2
- Ubuntu 24.04 LTS
- NVIDIA A10G
- AWS VPC networking

### Container Platform

- Kubernetes
- MicroK8s
- Containerd
- Helm
- Calico

### AI and LLM Components

- vLLM
- Qwen/Qwen2.5-1.5B-Instruct
- microsoft/Phi-3-mini-4k-instruct
- Open WebUI
- FastAPI
- Qdrant
- SentenceTransformers
- OpenAI-compatible APIs

### Observability

- Prometheus
- Grafana
- Loki
- Promtail
- Tempo
- OpenTelemetry Collector
- NVIDIA DCGM Exporter
- Kubernetes Metrics Server

### Performance and Reliability

- Locust
- PromQL
- Kubernetes readiness probes
- Kubernetes liveness probes
- SLOs
- Error budgets
- Failure engineering

---

## AI Inference Services

### Qwen Service

Model:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

Deployment:

```text
vllm
```

Dedicated Service:

```text
vllm-qwen
```

Placement:

```text
Node 1
NVIDIA A10G GPU 1
```

Maximum model length:

```text
8,192 tokens
```

### Phi-3 Service

Model:

```text
microsoft/Phi-3-mini-4k-instruct
```

Deployment:

```text
vllm-secondary
```

Dedicated Service:

```text
vllm-phi3
```

Placement:

```text
Node 2
NVIDIA A10G GPU 2
```

Maximum model length:

```text
4,096 tokens
```

### Model-Specific Routing

```text
vllm-qwen
└── Qwen only

vllm-phi3
└── Phi-3 only
```

Model-specific routing prevents requests for one model from being sent to the other model.

---

## Retrieval-Augmented Generation

The platform includes a custom FastAPI-based RAG application.

### RAG Data Flow

```text
User Question
      │
      ▼
FastAPI RAG Service
      │
      ▼
SentenceTransformer Embedding
      │
      ▼
Qdrant Similarity Search
      │
      ▼
Top-3 Retrieved Context Chunks
      │
      ▼
Qwen Generation Backend
      │
      ▼
Grounded Answer and Sources
```

### Embedding Model

```text
sentence-transformers/all-MiniLM-L6-v2
```

### Vector Database

```text
Qdrant
```

### Qdrant Collection

```text
docs
```

### RAG Endpoints

```text
GET  /health
POST /ingest
POST /query
GET  /v1/models
POST /v1/chat/completions
```

### Sample Query

Request:

```json
{
  "question": "What is Deepak secret validation code?"
}
```

Response:

```json
{
  "answer": "RAG-DEMO-2026-XYZ.",
  "sources": [
    {
      "text": "The Deepak secret validation code is RAG-DEMO-2026-XYZ."
    }
  ]
}
```

---

## Open WebUI

Open WebUI provides the user-facing chat interface.

Configured OpenAI-compatible backends:

```text
http://vllm-qwen.vllm.svc.cluster.local:8000/v1
http://vllm-phi3.vllm.svc.cluster.local:8000/v1
```

Open WebUI connectivity to both model services was validated from inside the Open WebUI pod.

The current Open WebUI release continued to display the existing Qwen model entry in the interface, while both model backends remained independently accessible and functional.

---

## Observability

### Prometheus Metrics

The platform exposes:

- Kubernetes metrics
- Node metrics
- Container metrics
- GPU Operator metrics
- DCGM GPU metrics
- vLLM inference metrics
- RAG service metrics

### Inference Metrics

Key vLLM metrics include:

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

### Grafana Dashboard Panels

The inference dashboard includes:

- Running requests
- Waiting requests
- Requests per second
- P95 Time to First Token
- P95 Time per Output Token
- P95 end-to-end latency
- P95 queue time
- Prompt tokens per second
- Generation tokens per second
- KV-cache utilization
- Prefix-cache hit ratio
- Per-pod request distribution

### Logs

Logs are collected using:

```text
Promtail
↓
Loki
↓
Grafana Explore
```

### Traces

Traces are collected using:

```text
OpenTelemetry Collector
↓
Tempo
↓
Grafana
```

---

## Single-GPU Performance Baseline

The initial performance baseline used:

```text
Instance: AWS g5.xlarge
GPU: NVIDIA A10G
Model: Qwen/Qwen2.5-1.5B-Instruct
Load Generator: Locust 2.46.5
```

### Baseline Results

| Concurrency | Average Latency | P95 | P99 | Throughput |
|---:|---:|---:|---:|---:|
| 1 | 827 ms | 1.0 s | 1.1 s | 0.43 req/s |
| 2 | 835 ms | 1.1 s | 1.1 s | 2.39 req/s |
| 4 | 838 ms | 1.1 s | 1.1 s | 4.76 req/s |
| 8 | 858 ms | 1.1 s | 1.1 s | 9.30 req/s |
| 16 | 883 ms | 1.1 s | 1.2 s | 18.05 req/s |
| 32 | 990 ms | 1.2 s | 1.3 s | 32.22 req/s |

### Single-GPU Extreme Load

At 1,024 concurrent users:

```text
Completed Requests: 12,152
Failures: 0
Success Rate: 100%
Throughput: 67.52 requests/second
Average Latency: 14.493 seconds
Median Latency: 15.0 seconds
P95 Latency: 16.0 seconds
P99 Latency: 16.0 seconds
Maximum Latency: 17.9 seconds
```

Observed scheduler state:

```text
Running Requests: approximately 254
Waiting Requests: approximately 767
```

The platform degraded through controlled queueing instead of request loss or service instability.

---

## Dual-GPU Scaling Validation

A second Qwen replica was deployed on Node 2 for the dual-GPU benchmark.

### Request Distribution

During routing validation:

```text
Primary Replica Requests: 804
Secondary Replica Requests: 836
```

Approximate distribution:

```text
Primary: 49%
Secondary: 51%
```

### Dual-GPU Extreme Load

At 1,024 concurrent users:

```text
Completed Requests: 24,414
Failures: 0
Success Rate: 100%
Throughput: 135.63 requests/second
Average Latency: 7.370 seconds
Median Latency: 7.5 seconds
P95 Latency: 8.5 seconds
P99 Latency: 8.8 seconds
Maximum Latency: 9.248 seconds
```

Observed scheduler state:

```text
Active Requests: approximately 510
Waiting Requests: approximately 496 to 507
```

### Single-GPU Versus Dual-GPU

| Metric | Single GPU | Dual GPU | Improvement |
|---|---:|---:|---:|
| Throughput | 67.52 req/s | 135.63 req/s | 2.01x |
| Average Latency | 14.493 s | 7.370 s | 49.1% lower |
| Median Latency | 15.0 s | 7.5 s | 50% lower |
| P95 Latency | 16.0 s | 8.5 s | 46.9% lower |
| P99 Latency | 16.0 s | 8.8 s | 45% lower |
| Active Requests | Approximately 254 | Approximately 510 | Approximately 2x |
| Failures | 0 | 0 | Maintained |

The second A10G produced almost perfectly linear horizontal scaling.

---

## SLOs and Error Budget

### Normal Operating Region

```text
1 to 32 concurrent users
```

### Service-Level Objectives

```text
P95 End-to-End Latency: less than 2 seconds
P99 End-to-End Latency: less than 3 seconds
P95 Time to First Token: less than 1 second
P95 Time per Output Token: less than 100 milliseconds
P95 Queue Time: less than 500 milliseconds
Error Rate: less than 1%
```

### Normal-Load Validation

At 32 concurrent users:

```text
Throughput: 32.22 req/s
Average Latency: 990 ms
P95 Latency: 1.2 seconds
P99 Latency: 1.3 seconds
Error Rate: 0%
```

The 32-user run passed the measured end-to-end latency and error-rate objectives.

### Goodput Definition

Goodput is defined as requests that:

- Return successfully
- Produce a valid response
- Satisfy applicable latency objectives

---

## Failure Engineering

Controlled failure tests were performed against GPU-backed model workloads.

### Qwen Pod Failure

```text
Failure: Primary Qwen pod deleted
Recovery Type: Automatic
Time to Ready: 112 seconds
Manual Intervention: None
```

### Phi-3 Pod Failure

```text
Failure: Secondary Phi-3 pod deleted
Recovery Type: Automatic
Time to Ready: 103 seconds
Manual Intervention: None
```

### Worker Node Drain

```text
Failure: Worker node drained
Result: Phi-3 pod evicted
Replacement: Created automatically
Scheduling Result: Pending
Recovery: Manual uncordon required
Time to Ready after uncordon: 102 seconds
```

### Worker Node Loss

```text
Failure: Worker EC2 instance stopped
Node Failure Detection: Approximately 43 seconds
Node Ready after Restart: Approximately 29 seconds
Model Service Recovery: Approximately 225 seconds
```

### Failure Engineering Conclusion

The platform provides:

```text
Pod-level self-healing
```

The platform does not currently provide:

```text
Node-level model high availability
```

The limitation is caused by:

- One GPU per model
- Explicit node placement
- Local hostpath storage
- No redundant GPU capacity per model

---

## RAG Quality Evaluation

### Corpus

Initial knowledge base:

```text
4 points
```

Expanded knowledge base:

```text
64 stored points
```

The 30-item expansion dataset was accidentally ingested twice, creating duplicate vectors.

### Evaluation Dataset

```text
10 controlled questions
```

Question categories:

- Exact factual retrieval
- Paraphrased retrieval
- Unsupported questions

### Results

| Metric | Result |
|---|---:|
| Retrieval Accuracy | 87.5% |
| Answer Accuracy | 80% |
| Groundedness | 90% |
| Correct Refusal Rate | 100% |
| Unsupported-Question Hallucination Rate | 0% |
| Context-Contradiction Rate | 10% |

### Key Quality Findings

The RAG system performed well for:

- Quantitative facts
- Explicit platform facts
- Operational metrics
- Unsupported-question refusal

Improvement areas include:

- Idempotent ingestion
- Duplicate-vector removal
- Retrieval diversity
- Stronger grounding instructions
- Automated evaluation
- Retrieval-score reporting

---

## Cost and Goodput Analysis

### Reference Cost

```text
AWS g5.xlarge On-Demand Linux
$1.006 per instance-hour
```

### Single-GPU Cost Efficiency

```text
Hourly Cost: $1.006
Throughput: 67.52 req/s
Requests per Hour: 243,072
Requests per Dollar: approximately 241,622
Cost per 1,000 Requests: approximately $0.00414
```

### Dual-GPU Cost Efficiency

```text
Hourly Cost: $2.012
Throughput: 135.63 req/s
Requests per Hour: 488,268
Requests per Dollar: approximately 242,678
Cost per 1,000 Requests: approximately $0.00412
```

### Cost Conclusion

```text
Infrastructure Cost Increase: 2.0x
Throughput Increase: 2.01x
Scaling Efficiency: approximately 100%
```

Horizontal expansion delivered proportional performance for proportional cost.

The second GPU significantly improved throughput and overload latency without increasing cost per successful request.

---

## Challenges Solved

### Prometheus Did Not Discover vLLM

Issue:

```text
ServiceMonitor showed 0/0 targets.
```

Root cause:

```text
The vLLM Service did not have the app=vllm metadata label.
```

Solution:

- Added the Service label
- Added the named `http` Service port
- Preserved numeric `targetPort: 8000`

### Multi-Node PVC Scheduling Failure

Issue:

```text
The second vLLM replica remained Pending.
```

Root cause:

```text
The MicroK8s hostpath PVC was bound to Node 1.
```

Solution:

- Created a second node-local PVC
- Created a separate secondary deployment
- Assigned one cache PVC per model deployment

### Port-Forward Bypassed Service Load Balancing

Issue:

```text
All locally generated requests reached one replica.
```

Root cause:

```text
kubectl port-forward selected one backend pod.
```

Solution:

- Deployed Locust inside Kubernetes
- Targeted the ClusterIP Service
- Verified per-pod request counters through Prometheus

### Phi-3 Context-Length Failure

Issue:

```text
Phi-3 failed to start with max-model-len 8192.
```

Root cause:

```text
Phi-3 Mini 4K supports a maximum context length of 4096.
```

Solution:

```text
--max-model-len 4096
```

### Node-Level Failover Limitation

Issue:

```text
A replacement Phi-3 pod remained Pending after worker failure.
```

Root cause:

- Node selector pinned Phi-3 to Node 2
- Node 2 was unavailable
- Node-local model cache could not move
- No second eligible GPU existed

Conclusion:

```text
Pod self-healing exists.
Node-level model HA requires redundant GPU capacity.
```

### RAG Grounding Failure

Issue:

The model answered that node-level high availability existed even though the retrieved source stated that node-level high availability did not exist.

Conclusion:

```text
Successful retrieval does not guarantee grounded generation.
```

Recommended improvement:

- Strengthen grounding instructions
- Enforce attention to negation
- Automate RAG regression evaluation

---

## Repository Structure

```text
.
├── README.md
│
├── applications/
│   └── rag-app/
│       ├── Dockerfile
│       ├── main.py
│       └── requirements.txt
│
├── architecture/
│
├── docs/
│   └── phase-2/
│       ├── api-security.md
│       ├── autoscaling-strategy.md
│       ├── bounded-queue-overload-handling.md
│       ├── capacity-planning.md
│       ├── cost-and-goodput-analysis.md
│       ├── dual-gpu-scaling-validation.md
│       ├── error-budget.md
│       ├── failure-engineering.md
│       ├── ingress-architecture.md
│       ├── load-balancing-strategy.md
│       ├── multi-model-serving.md
│       ├── multi-replica-routing.md
│       ├── phase-2-summary.md
│       ├── phase2-performance-baseline.md
│       ├── phase2-rag-dataset.json
│       ├── rag-quality-evaluation.md
│       ├── scaling-thresholds.md
│       ├── scaling-triggers.md
│       ├── slos.md
│       ├── benchmarks/
│       └── images/
│
├── load-testing/
│
├── manifests/
│   ├── load-testing/
│   ├── observability/
│   ├── openwebui/
│   ├── qdrant/
│   ├── rag-app/
│   └── vllm/
│
├── runbooks/
│
├── screenshots/
│
└── scripts/
```

---

## Phase 2 Documentation

Detailed Phase 2 evidence is stored under:

```text
docs/phase-2/
```

Primary documents include:

- `phase-2-summary.md`
- `phase2-performance-baseline.md`
- `dual-gpu-scaling-validation.md`
- `multi-model-serving.md`
- `failure-engineering.md`
- `rag-quality-evaluation.md`
- `cost-and-goodput-analysis.md`
- `slos.md`
- `error-budget.md`

---

## Roadmap Status

| Phase | Capability | Status |
|---|---|---|
| 2.0 | Freeze and reproduce Phase 1 | Complete |
| 2.1 | Inference metrics and dashboard | Complete |
| 2.2 | Single-node performance baseline | Complete |
| 2.3 | SLOs and error budget | Complete |
| 2.4 | Production API entry-point design | Design complete |
| 2.5 | Overload-handling design | Design complete |
| 2.6 | Stateless autoscaling strategy | Design complete |
| 2.7 | GPU scheduling constraint demonstration | Partially complete |
| 2.8 | Add second g5.xlarge | Complete |
| 2.9 | Two-replica vLLM | Complete |
| 2.10 | Multi-model serving | Complete |
| 2.11 | Failure engineering | Complete |
| 2.12 | RAG quality evaluation | Complete |
| 2.13 | Cost and goodput | Complete |

---

## Deferred Production Enhancements

The following capabilities are documented but remain future implementation work:

- TLS termination
- External DNS
- API-key enforcement
- OAuth or OIDC
- Rate limiting
- Request-size limits
- Bounded admission queues
- HTTP 429 and 503 overload responses
- Stateless HPA validation
- KEDA installation
- Prometheus-driven scaling
- Shared or replicated model storage
- Redundant GPU capacity
