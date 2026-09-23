# Phase 2.6 - Scaling Triggers

## Overview

This document defines future autoscaling triggers.

Values are based on Phase 2.2 benchmark observations.

---

# Trigger 1 - Queue Depth

Metric:

```text
vllm:num_requests_waiting
```

Scale Out Threshold:

```text
> 100 requests waiting
```

Reason:

Queue growth was the first observable sign of saturation.

---

# Trigger 2 - Queue Time

Metric:

```text
vllm:request_queue_time_seconds
```

Scale Out Threshold:

```text
P95 Queue Time > 1 second
```

Reason:

Queue latency directly impacts TTFT and end-user experience.

---

# Trigger 3 - TTFT

Metric:

```text
vllm:time_to_first_token_seconds
```

Scale Out Threshold:

```text
P95 TTFT > 2 seconds
```

Reason:

TTFT is highly visible to users.

---

# Trigger 4 - Throughput Saturation

Metric:

```text
Requests per second
```

Scale Out Threshold:

Capacity approaching benchmark maximum.

---

# Trigger 5 - GPU Utilization

Metric:

```text
DCGM GPU Utilization
```

Target:

```text
70-85%
```

Scale Out Threshold:

```text
>90%
```

for sustained periods.

---

# Scale In Conditions

Scale-in should be conservative.

Requirements:

- Low queue depth
- Stable TTFT
- Stable latency

---

# Priority Order

1. Queue Depth
2. Queue Time
3. TTFT
4. GPU Utilization
5. Throughput
