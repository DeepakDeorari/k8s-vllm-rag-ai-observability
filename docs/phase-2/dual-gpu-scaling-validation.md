# Phase 2.8 & 2.9 - Dual-GPU Scaling Validation

## Overview

This phase expanded the platform from a single-node deployment to a dual-node GPU-enabled Kubernetes cluster and validated horizontal inference scaling.

The objective was to determine whether adding a second NVIDIA A10G GPU and a second vLLM replica would improve throughput, reduce latency, and reduce queueing behavior under heavy concurrent workloads.

---

# Objectives

## Phase 2.8

Expand the platform from:

```text
1 Node
1 GPU
1 vLLM Replica
```

to:

```text
2 Nodes
2 GPUs
```

while maintaining platform stability.

---

## Phase 2.9

Validate:

- Multi-replica vLLM deployment
- Service-based request routing
- Cross-node GPU scheduling
- Throughput scaling
- Latency improvements
- Queue reduction

---

# Environment

## Infrastructure

| Component | Value |
|------------|------------|
| Cloud | AWS |
| Instance Type | g5.xlarge |
| Node Count | 2 |
| GPU Type | NVIDIA A10G |
| Total GPUs | 2 |
| Kubernetes | MicroK8s v1.35.6 |
| Runtime | containerd |

---

# Cluster Topology

## Node 1

```text
Hostname: ip-172-31-7-23
Role: Control Plane + Worker
GPU: NVIDIA A10G
```

Workloads:

```text
Primary vLLM Replica
RAG API
Qdrant
Open WebUI
Observability Stack
```

---

## Node 2

```text
Hostname: ip-172-31-6-36
Role: Worker
GPU: NVIDIA A10G
```

Workloads:

```text
Secondary vLLM Replica
Locust Benchmark Pod
```

---

# GPU Validation

Both nodes successfully advertised GPU resources.

```text
Node 1:
nvidia.com/gpu = 1

Node 2:
nvidia.com/gpu = 1
```

GPU Operator automatically deployed:

```text
nvidia-device-plugin
nvidia-dcgm-exporter
nvidia-container-toolkit
gpu-feature-discovery
operator-validator
```

to the new worker node.

---

# Storage Challenge Encountered

Initial attempt:

```yaml
replicas: 2
```

failed.

Error:

```text
0/2 nodes are available:

1 Insufficient nvidia.com/gpu
1 node(s) didn't match PersistentVolume's node affinity
```

Root Cause:

```text
hf-cache PVC
```

used:

```text
microk8s-hostpath
```

storage.

The PVC had node affinity:

```text
ip-172-31-7-23
```

and could not be mounted from Node 2.

---

# Solution

A second deployment was created.

## Primary Replica

```text
Deployment: vllm
PVC: hf-cache
Node: ip-172-31-7-23
```

## Secondary Replica

```text
Deployment: vllm-secondary
PVC: hf-cache-secondary
Node: ip-172-31-6-36
```

Each replica maintains an independent Hugging Face cache.

---

# Traffic Routing Validation

A Kubernetes Service exposed both replicas.

Validated endpoints:

```text
10.1.17.85:8000
10.1.227.11:8000
```

Traffic distribution was verified using Prometheus metrics.

---

## Validation Before Test

```text
vllm-primary     = 9842 completed requests
vllm-secondary   = 0 completed requests
```

---

## Validation After Test

```text
vllm-primary     = 10646 completed requests
vllm-secondary   = 836 completed requests
```

Request growth:

```text
Primary    +804
Secondary  +836
```

Approximate distribution:

```text
Primary    49%
Secondary  51%
```

Result:

```text
Load balancing confirmed.
```

---

# Benchmark Results

## Single-GPU Baseline

Phase 2.2

### 1024 Concurrent Users

| Metric | Value |
|----------|----------|
| Throughput | 67.52 req/sec |
| Avg Latency | 14.49 sec |
| Median Latency | 15.0 sec |
| P95 Latency | 16.0 sec |
| P99 Latency | 16.0 sec |
| Failures | 0 |
| Success Rate | 100% |

Observed Scheduler State:

```text
Running Requests ≈ 254
Waiting Requests ≈ 767
```

---

## Dual-GPU Benchmark

### 512 Concurrent Users

| Metric | Value |
|----------|----------|
| Throughput | 134.8 req/sec |
| Avg Latency | 3.75 sec |
| P95 Latency | 4.7 sec |
| P99 Latency | 5.0 sec |
| Failures | 0 |
| Success Rate | 100% |

Observed Dashboard Metrics:

```text
Running Requests:
254
256

Total ≈ 510
```

```text
Waiting Requests:
21
8

Total ≈ 29
```

---

### 1024 Concurrent Users

| Metric | Value |
|----------|----------|
| Throughput | 135.63 req/sec |
| Avg Latency | 7.37 sec |
| Median Latency | 7.5 sec |
| P95 Latency | 8.5 sec |
| P99 Latency | 8.8 sec |
| Maximum Latency | 9.25 sec |
| Failures | 0 |
| Success Rate | 100% |

Observed Dashboard Metrics:

```text
Running Requests:
256
251

Total ≈ 507
```

```text
Waiting Requests:
236
260

Total ≈ 496
```

Observed Runtime Metrics:

```text
P95 TTFT ≈ 4.84 sec
P95 TPOT ≈ 0.048 sec
P95 E2E Latency ≈ 9.68 sec
P95 Queue Time ≈ 4.84 sec
```

---

# Single-GPU vs Dual-GPU Comparison

| Metric | Single GPU | Dual GPU | Change |
|----------|----------|----------|----------|
| Users | 1024 | 1024 | Same |
| Throughput | 67.52 req/sec | 135.63 req/sec | 2.01x |
| Average Latency | 14.49 sec | 7.37 sec | -49% |
| Median Latency | 15.0 sec | 7.5 sec | -50% |
| P95 Latency | 16.0 sec | 8.5 sec | -47% |
| P99 Latency | 16.0 sec | 8.8 sec | -45% |
| Running Requests | ~254 | ~510 | ~2x |
| Waiting Requests | ~767 | ~496 | Reduced |
| Failures | 0 | 0 | No Change |
| Success Rate | 100% | 100% | Maintained |

---

# Scaling Efficiency

## Throughput Scaling

Calculation:

```text
135.63 / 67.52
= 2.0087
```

Result:

```text
≈ 2.01x throughput scaling
```

Scaling efficiency:

```text
≈ 100%
```

The second A10G GPU delivered nearly linear horizontal scaling.

---

# Engineering Findings

## Finding 1

Adding a second GPU approximately doubled active execution capacity.

```text
Single GPU:
~254 active requests

Dual GPU:
~510 active requests
```

---

## Finding 2

Throughput scaled almost perfectly.

```text
67.52 req/sec
→
135.63 req/sec
```

---

## Finding 3

Average latency was reduced by approximately:

```text
49%
```

under the same 1024-user workload.

---

## Finding 4

P95 latency improved from:

```text
16 seconds
```

to:

```text
8.5 seconds
```

---

## Finding 5

The platform maintained:

```text
100% success rate
0 failures
```

under extreme load.

---

## Finding 6

The platform degraded through predictable queueing behavior rather than request loss.

---

# Architectural Discussion

The benchmark confirms:

```text
Horizontal GPU scaling
```

is significantly more effective than:

```text
Increasing queue depth
```

for improving user experience.

Future scaling should focus on:

```text
Additional GPUs
Additional vLLM replicas
Queue-aware load balancing
```

rather than allowing request queues to grow indefinitely.

---

# Conclusion

The dual-node, dual-GPU MicroK8s deployment successfully validated horizontal scaling for vLLM inference workloads.

Adding a second NVIDIA A10G GPU:

- Increased throughput by approximately 2x
- Reduced average latency by approximately 49%
- Reduced P95 latency by approximately 47%
- Doubled active scheduler capacity
- Reduced queue pressure
- Maintained 100% request success rate

This phase demonstrates that the platform can scale horizontally through additional GPU-backed vLLM replicas while preserving reliability and significantly improving performance under heavy concurrent workloads.

---

# Phase Status

```text
Phase 2.8 - Two Node Expansion
Status: COMPLETE ✅

Phase 2.9 - Multi-Replica vLLM Routing & Scaling Validation
Status: COMPLETE ✅
```
