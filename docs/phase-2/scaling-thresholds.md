# Phase 2.7 - Scaling Thresholds

## Objective

Define measurable thresholds that indicate when additional capacity is required.

---

# Threshold 1

Metric:

vllm:num_requests_waiting

Warning:

100

Critical:

250

---

# Threshold 2

Metric:

P95 Queue Time

Warning:

1 second

Critical:

5 seconds

---

# Threshold 3

Metric:

P95 TTFT

Warning:

2 seconds

Critical:

10 seconds

---

# Threshold 4

Metric:

P95 End-to-End Latency

Warning:

2 seconds

Critical:

15 seconds

---

# Threshold 5

Metric:

Request Throughput

Benchmark Maximum:

67.52 req/s

Scaling Evaluation:

>80% of benchmark maximum

---

# Scaling Actions

Warning Threshold:

- Review traffic patterns
- Monitor queue growth

Critical Threshold:

- Add GPU capacity
- Add vLLM replicas
- Introduce load balancing
