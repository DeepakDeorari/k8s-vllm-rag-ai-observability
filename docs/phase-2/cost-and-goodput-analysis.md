# Phase 2.13 - Cost and Goodput Analysis

## Overview

Phase 2.13 evaluates the cost efficiency and useful serving capacity of the GPU-backed AI inference platform.

Previous phases measured:

- Single-GPU inference performance
- Dual-GPU horizontal scaling
- End-to-end latency
- Request throughput
- Queueing behavior
- Reliability under extreme concurrency
- Pod and node recovery behavior
- RAG retrieval and answer quality

This phase combines infrastructure cost, benchmark performance, and Service Level Objectives to answer the following questions:

1. What is the cost of running the platform?
2. How many successful requests are processed per dollar?
3. How does cost efficiency change from one GPU to two GPUs?
4. Does horizontal scaling preserve cost efficiency?
5. What is the difference between raw throughput and SLO-compliant goodput?
6. Which configuration provides the best operating point?

---

## Objectives

The objectives of this phase were to:

1. Establish an hourly infrastructure cost model.
2. Calculate the cost per successful request.
3. Calculate successful requests per dollar.
4. Compare single-GPU and dual-GPU cost efficiency.
5. Calculate horizontal scaling efficiency.
6. Separate overload throughput from SLO-compliant goodput.
7. Identify the recommended configuration for normal and extreme load.
8. Document limitations in the available benchmark data.

---

# Definitions

## Throughput

Throughput represents the total number of completed requests per second.

```text
Throughput = Completed Requests / Test Duration
```

Throughput includes all successfully completed requests, regardless of whether those requests satisfied latency objectives.

---

## Successful Throughput

Successful throughput represents requests that completed without an HTTP or inference failure.

```text
Successful Throughput =
Successful Requests / Test Duration
```

All measured single-GPU and dual-GPU benchmark runs completed with:

```text
0 failures
100% request success rate
```

Therefore, raw throughput and successful throughput were equal for the measured tests.

---

## Goodput

Goodput represents useful requests that satisfy the applicable service objectives.

For the current platform, a request contributes toward request-level goodput when:

- The HTTP request succeeds.
- A valid model response is returned.
- End-to-end response time is below the applicable latency limit.

Goodput is represented as:

```text
Goodput =
Successful Requests Satisfying the Latency Objective
/
Measurement Duration
```

---

## SLO Window Compliance

Some objectives are evaluated over a complete measurement window rather than per request.

The documented normal-load SLOs include:

```text
P95 end-to-end latency < 2 seconds
P99 end-to-end latency < 3 seconds
P95 TTFT < 1 second
P95 TPOT < 100 milliseconds
P95 queue time < 500 milliseconds
Error rate < 1%
```

These objectives apply only to the normal operating region:

```text
1-32 concurrent users
```

A benchmark window is SLO-compliant only when all measured applicable objectives pass.

---

## Cost-Normalized Throughput

Cost-normalized throughput measures the number of completed requests processed for each dollar of infrastructure cost.

```text
Requests per Dollar =
Requests per Hour / Hourly Infrastructure Cost
```

---

## Cost per 1,000 Requests

```text
Cost per 1,000 Requests =
Hourly Infrastructure Cost
/
Requests per Hour
× 1,000
```

---

## Horizontal Scaling Efficiency

Horizontal scaling efficiency compares the measured performance increase with the infrastructure increase.

```text
Scaling Efficiency =
Measured Throughput Scaling
/
Infrastructure Scaling
× 100
```

---

# Infrastructure Cost Model

## Pricing Model

The analysis uses the following AWS reference pricing:

```text
Instance Type: g5.xlarge
Operating System: Linux
Pricing Model: On-Demand
Hourly Cost: $1.006
```

The cost is an infrastructure reference cost and does not include:

- EBS volume charges
- Data-transfer charges
- Public IPv4 charges
- CloudWatch charges
- Operational labor
- Backup storage
- Software licensing
- Support plans
- Taxes
- Discounts from Savings Plans or Reserved Instances

---

## Single-GPU Configuration

```text
Instances: 1
GPU Count: 1 NVIDIA A10G
Hourly Cost: 1 × $1.006
Total Cost: $1.006/hour
```

---

## Dual-GPU Configuration

```text
Instances: 2
GPU Count: 2 NVIDIA A10Gs
Hourly Cost: 2 × $1.006
Total Cost: $2.012/hour
```

---

# Benchmark Inputs

## Single-GPU Extreme-Load Benchmark

The single-GPU benchmark used:

```text
Concurrent Users: 1,024
Instances: 1
GPUs: 1
Model: Qwen/Qwen2.5-1.5B-Instruct
```

Measured results:

| Metric | Value |
|---|---:|
| Completed Requests | 12,152 |
| Failures | 0 |
| Success Rate | 100% |
| Throughput | 67.52 req/s |
| Average Latency | 14.493 s |
| Median Latency | 15.0 s |
| P95 Latency | 16.0 s |
| P99 Latency | 16.0 s |
| Maximum Latency | 17.9 s |
| Active Requests | Approximately 254 |
| Waiting Requests | Approximately 767 |

---

## Dual-GPU Extreme-Load Benchmark

The dual-GPU benchmark used:

```text
Concurrent Users: 1,024
Instances: 2
GPUs: 2
Model Replicas: 2
Model: Qwen/Qwen2.5-1.5B-Instruct
```

Measured results:

| Metric | Value |
|---|---:|
| Completed Requests | 24,414 |
| Failures | 0 |
| Success Rate | 100% |
| Throughput | 135.63 req/s |
| Average Latency | 7.370 s |
| Median Latency | 7.5 s |
| P95 Latency | 8.5 s |
| P99 Latency | 8.8 s |
| Maximum Latency | 9.248 s |
| Active Requests | Approximately 510 |
| Waiting Requests | Approximately 496-507 |

---

## Single-GPU Normal-Load Benchmark

The single-GPU normal-load benchmark used:

```text
Concurrent Users: 32
Instances: 1
GPUs: 1
Model: Qwen/Qwen2.5-1.5B-Instruct
```

Measured results:

| Metric | Value |
|---|---:|
| Completed Requests | 5,792 |
| Failures | 0 |
| Success Rate | 100% |
| Throughput | 32.22 req/s |
| Average Latency | 0.990 s |
| Median Latency | 1.0 s |
| P95 Latency | 1.2 s |
| P99 Latency | 1.3 s |
| Maximum Latency | 1.322 s |

This benchmark is within the documented normal operating region.

---

# Extreme-Load Cost Efficiency

The 1,024-user benchmarks are used to compare cost efficiency under identical extreme-load conditions.

These results are not used for formal normal-load SLO compliance because 1,024 concurrent users are outside the documented 1 to 32-user SLO scope.

---

## Single-GPU Requests per Hour

Measured throughput:

```text
67.52 requests/second
```

Calculation:

```text
67.52 × 3,600
= 243,072 requests/hour
```

Result:

```text
243,072 requests/hour
```

---

## Single-GPU Cost per Request

Calculation:

```text
$1.006 / 243,072
= $0.000004138 per request
```

Result:

```text
Approximately $0.00000414 per request
```

---

## Single-GPU Cost per 1,000 Requests

Calculation:

```text
$1.006 / 243,072 × 1,000
= $0.004138
```

Result:

```text
Approximately $0.00414 per 1,000 requests
```

---

## Single-GPU Requests per Dollar

Calculation:

```text
243,072 / $1.006
= 241,622 requests per dollar
```

Result:

```text
Approximately 241,622 successful requests per dollar
```

---

## Dual-GPU Requests per Hour

Measured throughput:

```text
135.63 requests/second
```

Calculation:

```text
135.63 × 3,600
= 488,268 requests/hour
```

Result:

```text
488,268 requests/hour
```

---

## Dual-GPU Cost per Request

Calculation:

```text
$2.012 / 488,268
= $0.000004121 per request
```

Result:

```text
Approximately $0.00000412 per request
```

---

## Dual-GPU Cost per 1,000 Requests

Calculation:

```text
$2.012 / 488,268 × 1,000
= $0.004121
```

Result:

```text
Approximately $0.00412 per 1,000 requests
```

---

## Dual-GPU Requests per Dollar

Calculation:

```text
488,268 / $2.012
= 242,678 requests per dollar
```

Result:

```text
Approximately 242,678 successful requests per dollar
```

---

# Extreme-Load Cost Comparison

| Metric | Single GPU | Dual GPU | Change |
|---|---:|---:|---:|
| Instance Count | 1 | 2 | 2.0x |
| GPU Count | 1 | 2 | 2.0x |
| Hourly Cost | $1.006 | $2.012 | 2.0x |
| Throughput | 67.52 req/s | 135.63 req/s | 2.01x |
| Requests per Hour | 243,072 | 488,268 | 2.01x |
| Cost per 1,000 Requests | $0.00414 | $0.00412 | Approximately 0.4% lower |
| Requests per Dollar | 241,622 | 242,678 | Approximately 0.44% higher |
| Average Latency | 14.493 s | 7.370 s | 49.1% lower |
| P95 Latency | 16.0 s | 8.5 s | 46.9% lower |
| P99 Latency | 16.0 s | 8.8 s | 45% lower |
| Success Rate | 100% | 100% | Maintained |

---

# Horizontal Scaling Efficiency

## Throughput Scaling

Calculation:

```text
135.63 / 67.52
= 2.0087
```

Result:

```text
Approximately 2.01x throughput scaling
```

---

## Infrastructure Scaling

Calculation:

```text
2 GPUs / 1 GPU
= 2.0x infrastructure scaling
```

---

## Scaling Efficiency

Calculation:

```text
2.0087 / 2.0 × 100
= 100.44%
```

Result:

```text
Approximately 100% horizontal scaling efficiency
```

The measured value slightly above 100% is attributed to normal benchmark variation and should not be interpreted as sustained superlinear scaling.

---

# Incremental Cost Analysis

Adding the second GPU node increased hourly cost by:

```text
$2.012 - $1.006
= $1.006/hour
```

Additional throughput:

```text
135.63 - 67.52
= 68.11 requests/second
```

Additional hourly capacity:

```text
68.11 × 3,600
= 245,196 requests/hour
```

Incremental requests per additional dollar:

```text
245,196 / $1.006
= approximately 243,734 requests
```

The second instance therefore delivered approximately the same cost-normalized request capacity as the first instance.

---

# Normal-Load SLO Analysis

The documented end-to-end latency SLO applies to:

```text
1-32 concurrent users
```

The single-GPU 32-user benchmark measured:

```text
Average latency: 0.990 seconds
P95 latency: 1.2 seconds
P99 latency: 1.3 seconds
Error rate: 0%
```

The applicable targets were:

```text
P95 latency < 2 seconds
P99 latency < 3 seconds
Error rate < 1%
```

Result:

```text
P95 end-to-end latency: PASS
P99 end-to-end latency: PASS
Error rate: PASS
```

---

## Single-GPU Normal-Load Requests per Hour

Calculation:

```text
32.22 × 3,600
= 115,992 requests/hour
```

Result:

```text
115,992 requests/hour
```

---

## Single-GPU Normal-Load Cost per 1,000 Requests

Calculation:

```text
$1.006 / 115,992 × 1,000
= $0.008673
```

Result:

```text
Approximately $0.00867 per 1,000 requests
```

---

## Single-GPU Normal-Load Requests per Dollar

Calculation:

```text
115,992 / $1.006
= approximately 115,300 requests per dollar
```

Result:

```text
Approximately 115,300 requests per dollar
```

---

# Goodput Interpretation

## Aggregate Compliance

The 32-user benchmark passed the measured end-to-end latency and error-rate objectives.

Therefore, the observed throughput can be treated as an aggregate SLO-window compliant throughput baseline for:

```text
P95 end-to-end latency
P99 end-to-end latency
Error rate
```

Baseline:

```text
32.22 requests/second
```

---

## Formal Per-Request Goodput Limitation

Formal goodput requires counting each request that completed within the two-second latency threshold.

The available summary reported:

```text
P99 latency: 1.3 seconds
Maximum latency: 1.322 seconds
Failures: 0
```

Because the observed maximum latency was below two seconds, all recorded requests in that benchmark met the two-second end-to-end request-latency threshold.

Therefore:

```text
Request-level latency goodput: 32.22 requests/second
```

for the measured 32-user run.

However, full SLO-window compliance also requires TTFT, TPOT, and queue-time measurements from the same benchmark window.

Those metrics were not preserved as benchmark artifacts for the original 32-user single-GPU run.

The result must therefore be described as:

```text
End-to-end latency and error-rate compliant goodput
```

rather than:

```text
Fully SLO-compliant goodput
```

---

# Extreme-Load Goodput Interpretation

The 1,024-user tests intentionally operated outside the documented normal operating region.

Therefore:

```text
Single-GPU 1024-user throughput
and
Dual-GPU 1024-user throughput
```

are classified as:

```text
Successful overload throughput
```

and not:

```text
Normal-load SLO goodput
```

The overload tests remain useful for:

- Capacity analysis
- Horizontal scaling analysis
- Queue behavior
- Cost per successful request
- Latency reduction
- Cost-normalized successful throughput

---

# Cost and Goodput Summary

| Operating Point | Cost/Hour | Throughput | Cost per 1,000 Requests | Requests per Dollar | Classification |
|---|---:|---:|---:|---:|---|
| Single GPU, 32 users | $1.006 | 32.22 req/s | $0.00867 | 115,300 | End-to-end latency and error-rate compliant |
| Single GPU, 1024 users | $1.006 | 67.52 req/s | $0.00414 | 241,622 | Extreme-load successful throughput |
| Dual GPU, 1024 users | $2.012 | 135.63 req/s | $0.00412 | 242,678 | Extreme-load successful throughput |

---

# Key Findings

## Finding 1: Horizontal Scaling Preserved Cost Efficiency

The dual-GPU configuration doubled infrastructure cost and delivered approximately double the request throughput.

```text
Cost increase:       2.0x
Throughput increase: 2.01x
```

As a result, cost per successful request remained essentially unchanged.

---

## Finding 2: The Second GPU Delivered Near-Linear Incremental Value

The additional g5.xlarge instance added:

```text
68.11 requests/second
245,196 requests/hour
```

for an additional:

```text
$1.006/hour
```

The incremental request capacity per dollar was similar to the original node.

---

## Finding 3: Dual-GPU Scaling Improved Latency Significantly

Under the same 1,024-user workload:

```text
Average latency:
14.493 seconds → 7.370 seconds

P95 latency:
16.0 seconds → 8.5 seconds

P99 latency:
16.0 seconds → 8.8 seconds
```

The dual-GPU deployment delivered both additional throughput and improved user experience under overload.

---

## Finding 4: Maximum Throughput Does Not Equal Goodput

The 1,024-user tests produced the highest successful throughput, but those workloads were outside the defined normal SLO operating region.

The platform must distinguish:

```text
Successful throughput
```

from:

```text
SLO-compliant goodput
```

when making production capacity decisions.

---

## Finding 5: Lower Concurrency Has a Higher Cost per Request

At 32 concurrent users, the single-GPU platform processed:

```text
32.22 requests/second
```

At 1,024 concurrent users, the same GPU processed:

```text
67.52 requests/second
```

Continuous batching improved GPU utilization at high concurrency, reducing cost per request.

However, overload latency increased significantly.

This demonstrates the core latency-versus-efficiency trade-off:

```text
Higher concurrency
→ Better hardware utilization
→ Lower cost per request
→ Higher queueing and latency
```

---

## Finding 6: The Best Configuration Depends on the Objective

For strict interactive latency:

```text
Single GPU at or below 32 concurrent users
```

provided the measured normal-load baseline.

For maximum successful throughput:

```text
Dual GPU at high concurrency
```

provided the strongest capacity.

For node-level model availability:

```text
Additional replicated GPU capacity
```

would still be required because the current multi-model architecture assigns one model to each GPU node.

---

# Recommended Operating Points

## Interactive Workload Operating Point

Recommended baseline:

```text
Concurrency: 32 users or fewer
Configuration: 1 GPU minimum
```

Observed:

```text
P95 latency: 1.2 seconds
P99 latency: 1.3 seconds
Error rate: 0%
```

This operating point passed the measured end-to-end latency and error-rate objectives.

---

## High-Throughput Operating Point

Recommended architecture:

```text
2 × g5.xlarge
2 × NVIDIA A10G
2 × Qwen vLLM replicas
```

Observed under 1,024 users:

```text
Throughput: 135.63 requests/second
Success rate: 100%
Cost per 1,000 requests: approximately $0.00412
```

This configuration provided the best measured overload throughput while preserving nearly linear cost efficiency.

---

## Multi-Model Operating Point

Current architecture:

```text
Node 1 GPU:
Qwen/Qwen2.5-1.5B-Instruct

Node 2 GPU:
microsoft/Phi-3-mini-4k-instruct
```

This configuration optimizes for:

- Model diversity
- Explicit model routing
- Independent model lifecycle management
- One model per GPU

It does not provide two-replica throughput scaling for one model because each GPU serves a different model.

---

# Capacity Planning Implications

The benchmark results support the following planning guidance.

## Scale Out When

- Queue depth grows continuously.
- P95 queue time approaches the operational threshold.
- TTFT begins violating its target.
- End-to-end latency approaches two seconds in the normal operating region.
- Request demand remains above the sustainable per-GPU operating point.
- Additional model redundancy is required.

---

## Do Not Scale Based Only on CPU

The inference bottleneck is GPU and scheduler capacity.

Preferred scaling signals include:

```text
vllm:num_requests_waiting
vllm:request_queue_time_seconds
vllm:time_to_first_token_seconds
vllm:num_requests_running
Generation tokens per second
```

CPU utilization alone does not represent inference saturation accurately.

---

# Token-Economics Limitation

The current benchmark artifacts preserved:

- Request counts
- Request throughput
- Latency percentiles
- Failures
- Prompt-token rate dashboards
- Generation-token rate dashboards

However, the benchmark result files did not preserve complete prompt-token and generation-token totals for each matched test window.

Therefore, this report does not claim:

```text
Cost per one million prompt tokens
Cost per one million generated tokens
Cost per one million total tokens
```

Those calculations require controlled benchmark runs that record exact token totals over the same measurement interval.

---

# Recommended Token-Cost Methodology

Future benchmark runs should collect:

```text
Prompt tokens generated during the test
Output tokens generated during the test
Total successful requests
Test duration
Infrastructure hourly cost
```

The following calculations can then be used.

## Prompt Token Cost

```text
Cost per 1M Prompt Tokens =
Test Infrastructure Cost
/
Prompt Tokens
× 1,000,000
```

## Generation Token Cost

```text
Cost per 1M Generated Tokens =
Test Infrastructure Cost
/
Generated Tokens
× 1,000,000
```

## Total Token Cost

```text
Cost per 1M Total Tokens =
Test Infrastructure Cost
/
(Prompt Tokens + Generated Tokens)
× 1,000,000
```

## Token Goodput

```text
Token Goodput =
Tokens Generated by Requests Meeting the SLO
/
Measurement Duration
```

---

# Limitations

The Phase 2.13 analysis has the following limitations:

1. AWS pricing excludes storage, transfer, monitoring, and operational costs.
2. The hourly price is a reference On-Demand Linux price.
3. Spot, Reserved Instance, and Savings Plan pricing were not evaluated.
4. Energy consumption was not measured.
5. Exact token totals were not preserved for the matched benchmark windows.
6. Dual-GPU 32-user normal-load goodput was not measured before moving to multi-model mode.
7. The single-GPU and dual-GPU 1,024-user tests were overload tests, not normal-load SLO tests.
8. TTFT, TPOT, and queue-time measurements were not preserved for the original 32-user benchmark window.
9. Benchmark clients consumed host CPU and memory resources within the Kubernetes cluster.
10. Model quality differences were not included in cost comparisons.
11. Cost calculations assume continuous utilization for one hour.
12. Startup, idle, and scale-transition costs were not modeled.

---

# Future Enhancements

Future cost and goodput analysis should include:

- Exact prompt-token counts
- Exact generation-token counts
- Cost per million tokens
- SLO-compliant token goodput
- GPU utilization over each test window
- GPU power consumption
- Idle-versus-active cost
- Spot Instance comparison
- Savings Plan comparison
- Model quality-adjusted cost
- RAG answer-quality-adjusted goodput
- Cost per grounded answer
- Cost per correct answer
- Comparison between vLLM and SGLang
- Automated benchmark and cost-report generation

---

# Exit Criteria

Phase 2.13 used the following exit criteria:

- Infrastructure cost model documented.
- Single-GPU hourly cost calculated.
- Dual-GPU hourly cost calculated.
- Requests per hour calculated.
- Cost per 1,000 successful requests calculated.
- Successful requests per dollar calculated.
- Horizontal scaling efficiency calculated.
- Goodput methodology defined.
- Normal-load SLO scope respected.
- Overload throughput separated from SLO goodput.
- Recommended operating points identified.
- Analysis limitations documented.

---

# Exit-Criteria Validation

| Exit Criterion | Status |
|---|---|
| Infrastructure cost model documented | Pass |
| Single-GPU cost efficiency calculated | Pass |
| Dual-GPU cost efficiency calculated | Pass |
| Throughput scaling efficiency calculated | Pass |
| Cost per successful request calculated | Pass |
| Requests per dollar calculated | Pass |
| Goodput methodology documented | Pass |
| SLO scope applied correctly | Pass |
| Normal-load and overload results separated | Pass |
| Recommended operating points documented | Pass |
| Token-cost limitation documented | Pass |

---

# Conclusion

The Phase 2.13 analysis demonstrated that the platform scaled horizontally with nearly linear cost efficiency.

Increasing from one g5.xlarge instance to two g5.xlarge instances produced:

```text
Infrastructure cost: 2.0x
Request throughput: 2.01x
Active scheduler capacity: approximately 2.0x
Average latency under overload: approximately 49% lower
P95 latency under overload: approximately 47% lower
```

Cost per 1,000 successful overload requests remained nearly unchanged:

```text
Single GPU: approximately $0.00414
Dual GPU:   approximately $0.00412
```

Successful requests per dollar were also nearly identical:

```text
Single GPU: approximately 241,622 requests per dollar
Dual GPU:   approximately 242,678 requests per dollar
```

This demonstrates that the second GPU node delivered proportional performance for proportional infrastructure cost.

The 32-user single-GPU benchmark established an end-to-end latency and error-rate compliant normal-load baseline:

```text
Throughput: 32.22 requests/second
P95 latency: 1.2 seconds
P99 latency: 1.3 seconds
Error rate: 0%
```

The primary engineering conclusion is that cost efficiency remained stable during horizontal expansion, while throughput and overload latency improved substantially.

For interactive workloads, the platform should operate within the validated normal-load region.

For high-throughput workloads, the dual-GPU architecture provides the best measured capacity and latency while maintaining effectively unchanged cost per successful request.

---

# Phase Status

```text
Phase 2.13 - Cost and Goodput Analysis

Status: COMPLETE
```

---

# Next Phase

```text
Phase 2.14 - Optional vLLM vs SGLang Comparison
```

Phase 2.14 may compare:

- Throughput
- TTFT
- TPOT
- P95 latency
- P99 latency
- GPU memory usage
- Queue behavior
- Startup time
- Cost per successful request
- Cost per million tokens
- SLO-compliant goodput
