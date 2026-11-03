# Phase 2.2 - Performance Baseline Report

## Overview

This phase establishes the performance baseline of the single-node AI inference platform before introducing additional complexity such as multi-node deployment, autoscaling, routing, or multi-model serving.

The objective was to measure the behavior of a single NVIDIA A10G GPU running vLLM serving the Qwen/Qwen2.5-1.5B-Instruct model under increasing concurrency levels.

---

# Environment

## Infrastructure

- AWS EC2 g5.xlarge
- NVIDIA A10G GPU
- Ubuntu Linux
- MicroK8s Kubernetes Cluster
- Single Node Deployment

## AI Stack

- vLLM
- Qwen/Qwen2.5-1.5B-Instruct
- Open WebUI
- Qdrant
- Custom FastAPI RAG Service

## Observability Stack

- Prometheus
- Grafana
- Loki
- Tempo
- OpenTelemetry Collector

## Benchmark Tool

- Locust 2.46.5

---

# Test Methodology

The benchmark targeted the OpenAI-compatible vLLM endpoint.

Endpoint:

```text
/v1/chat/completions
```

Prompt:

```text
Explain Kubernetes in five concise bullet points.
```

Model:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

Max Tokens:

```text
128
```

Each concurrency level was executed for approximately 3 minutes under continuous load.

---

# Benchmark Results

| Concurrency | Avg Latency (ms) | P95 (ms) | P99 (ms) | Req/s |
|-------------|------------------|----------|----------|--------|
| 1           | 827              | 1000     | 1100     | 0.43   |
| 2           | 835              | 1100     | 1100     | 2.39   |
| 4           | 838              | 1100     | 1100     | 4.76   |
| 8           | 858              | 1100     | 1100     | 9.30   |
| 16          | 883              | 1100     | 1200     | 18.05  |
| 32          | 990              | 1200     | 1300     | 32.22  |

---

# Scaling Analysis

## Throughput Scaling

Throughput increased nearly linearly as concurrency increased.

```text
Concurrency 1    -> 0.43 req/s
Concurrency 2    -> 2.39 req/s
Concurrency 4    -> 4.76 req/s
Concurrency 8    -> 9.30 req/s
Concurrency 16   -> 18.05 req/s
Concurrency 32   -> 32.22 req/s
```

The platform demonstrated efficient utilization of the GPU and inference scheduler across the tested concurrency levels.

## Latency Growth

Latency remained relatively stable throughout the benchmark range.

```text
Average Latency
827 ms -> 990 ms
```

while throughput increased substantially.

This indicates that the platform had not yet reached a hard saturation point within the 1–32 concurrency range.

## Reliability

Across all benchmark runs:

```text
Failures: 0
Success Rate: 100%
```

No API failures, pod restarts, OOM events, or GPU-related instability were observed.

---

# Extreme Load Test (1024 Concurrent Users)

An additional stress test was executed using 1024 concurrent Locust users to understand scheduler behavior under heavy overload conditions.

## Results

| Metric | Value |
|----------|----------|
| Concurrent Users | 1024 |
| Requests Processed | 12,152 |
| Success Rate | 100% |
| Failures | 0 |
| Throughput | 67.52 req/s |
| Average Latency | 14.49 sec |
| Median Latency | 15 sec |
| P95 Latency | 16 sec |
| Maximum Latency | 17.9 sec |

---

# Queue Saturation Behavior

During the 1024-user test, Grafana dashboards showed:

| Metric | Value |
|----------|----------|
| Running Requests | ~254 |
| Waiting Requests | ~767 |
| P95 TTFT | ~19.2 sec |
| P95 E2E Latency | ~19.2 sec |
| P95 Queue Time | ~14.6 sec |
| Prefix Cache Hit Ratio | ~84% |

The scheduler consistently maintained approximately 250 active requests while placing excess requests into the waiting queue.

This behavior remained stable throughout the test duration.

---

# High-Concurrency Behavior Analysis

Under a 1024-user synthetic workload, the platform maintained 100% successful request completion with no pod failures or GPU-related instability.

vLLM limited active execution to approximately 250 requests while queuing approximately 750 additional requests.

Rather than rejecting requests or crashing, the scheduler applied backpressure and processed requests as execution slots became available.

This demonstrates graceful degradation behavior under extreme load.

## Engineering Observation

The primary bottleneck during the 1024-user workload was queueing delay.

Most latency growth was caused by:

```text
Request Queue Time
```

rather than:

```text
GPU Compute Time
```

The system remained operational and responsive while latency increased in a predictable manner.

---

# Queue Saturation Visualization

Screenshot:

```text
docs/phase-2/images/1024-user-queue-saturation.png
```

Observed Dashboard Metrics:

```text
Running Requests : ~254
Waiting Requests : ~767
P95 TTFT         : ~19.2 sec
P95 Queue Time   : ~14.6 sec
Request Rate     : ~58-67 req/sec
```

This visualization captures the scheduler saturation point where incoming demand exceeded active execution capacity and excess requests were buffered in the scheduler queue.

---

# Key Findings

## Finding 1

The platform successfully handled all tested workloads without request failures.

```text
Success Rate = 100%
```

for all benchmark executions.

## Finding 2

Throughput scaled efficiently up to at least:

```text
32 concurrent users
```

with only modest latency growth.

## Finding 3

The platform did not fail at:

```text
1024 concurrent users
```

instead transitioning into controlled queueing behavior.

## Finding 4

vLLM scheduler backpressure prevented instability by limiting active execution while maintaining queued request processing.

## Finding 5

The primary bottleneck at extreme load was queue depth rather than model inference execution.

## Finding 6

No pod crashes, GPU failures, OOM events, or Kubernetes instability were observed during testing.

---

# Conclusions

The single-node MicroK8s AI platform demonstrated strong performance characteristics under both normal and extreme load conditions.

The benchmark established:

- Throughput baseline
- Latency baseline
- Queueing baseline
- Scheduler saturation behavior
- Reliability baseline

The platform remained stable under heavy load and exhibited predictable degradation characteristics through scheduler-based backpressure rather than request loss.

These benchmark results provide the official performance baseline for future comparisons during:

- Phase 2.3 - SLOs and Error Budgets
- Phase 2.6 - Autoscaling
- Phase 2.8 - Two-Node Deployment
- Phase 2.9 - Multi-Replica vLLM Routing
- Phase 2.13 - Cost and Goodput Analysis

---

# Phase Status

```text
Phase 2.2 - Performance Baseline

Status: COMPLETE ✅
```
