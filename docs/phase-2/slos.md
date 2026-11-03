# Phase 2.3 - Service Level Objectives (SLOs)

## Overview

This document defines performance and reliability objectives for the AI inference platform based on measurements collected during Phase 2.2 benchmarking.

These values represent engineering targets rather than hard platform guarantees.

---

# Service Scope

Covered Services:

- vLLM
- RAG API
- Open WebUI API Path
- Qdrant Retrieval Path

Excluded:

- EC2 infrastructure failures
- AWS networking failures
- Planned maintenance windows

---

# Availability SLO

## API Availability

Target:

```text
99.5%
```

Definition:

Successful HTTP response returned by the inference API.

Measurement:

```text
successful_requests / total_requests
```

---

# Request Success SLO

Target:

```text
99%
```

Requirements:

- HTTP 200 response
- Valid model output
- No inference error

---

# Latency SLO

## Interactive Workloads

P95 End-to-End Latency:

```text
< 2 seconds
```

P99 End-to-End Latency:

```text
< 3 seconds
```

Applies to:

```text
Normal operating region
(<=32 concurrent users)
```

---

# TTFT SLO

P95 Time-To-First-Token:

```text
< 1 second
```

Target User Experience:

First token should appear within one second during normal operating conditions.

---

# TPOT SLO

P95 Time Per Output Token:

```text
< 100 ms
```

---

# Queue Time SLO

P95 Queue Time:

```text
< 500 ms
```

Normal Load:

```text
<100 ms preferred
```

---

# Error Rate SLO

Target:

```text
< 1%
```

Definition:

Failed requests divided by total requests.

---

# Goodput Definition

Goodput is defined as:

Successful requests satisfying:

- HTTP 200
- Valid response
- P95 latency SLO satisfied

Requests violating SLOs are excluded.

---

# Load Regions

## Region 1 - Normal Operation

Concurrency:

```text
1-32 users
```

Expected:

- SLOs met
- No queue buildup

---

## Region 2 - High Load

Concurrency:

```text
64-256 users
```

Expected:

- Platform healthy
- Elevated queue time
- Reduced latency margin

---

## Region 3 - Overload

Concurrency:

```text
512-1024 users
```

Expected:

- Queue growth
- TTFT increase
- Backpressure behavior

SLO violations allowed.

Platform should remain available.

---

# Graceful Degradation Policy

When platform capacity is exceeded:

Expected behavior:

- Queue requests
- Maintain availability
- Avoid crashes
- Avoid request loss

Observed in Phase 2.2 benchmark:

- ~254 running requests
- ~767 waiting requests
- 0 request failures

---

# SLO Review

SLOs will be revisited after:

- Phase 2.8 Two Node Deployment
- Phase 2.9 Multi-Replica vLLM
- Phase 2.13 Cost and Goodput Analysis
