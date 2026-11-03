# Phase 2.9 - Load Balancing Strategy

## Overview

This document defines how requests will be distributed between vLLM replicas.

---

# Current State

Inference replicas:

```text
1
```

Load balancing:

```text
Not required
```

---

# Future State

Inference replicas:

```text
2+
```

Load balancing:

```text
Required
```

---

# Strategy

Use Kubernetes Service-based load balancing.

Example:

```text
Client Request
       ↓
 Service
       ↓

Replica A
Replica B
Replica C
```

---

# Scaling Goals

Goals:

- Reduce queue depth
- Reduce TTFT
- Reduce latency
- Increase throughput

---

# Scaling Trigger Integration

Scale-out decisions should be informed by:

- Waiting Requests
- Queue Time
- TTFT
- Throughput

defined in Phase 2.6.

---

# Benchmark Alignment

Phase 2.2 findings:

```text
~254 active requests
~767 waiting requests
```

indicate horizontal scaling will likely be more effective than further queue expansion.

---

# Future Enhancements

Potential future capabilities:

- Weighted routing
- Model-aware routing
- Canary deployments
- Blue/Green deployments
- Cost-aware routing
- Multi-model routing

---

## Relationship To Phase 2.2

Phase 2.2 demonstrated that vLLM maintained approximately 250 active requests while queuing additional traffic.

This indicates that future performance improvements are more likely to come from horizontal expansion than increased queue depth.

Multi-replica routing is therefore considered the primary future scaling mechanism.
