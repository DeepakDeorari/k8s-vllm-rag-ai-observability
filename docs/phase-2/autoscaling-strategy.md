# Phase 2.6 - Autoscaling Strategy

## Overview

This document defines the autoscaling approach for the AI platform.

The current deployment operates on a single GPU and does not yet support horizontal inference scaling.

Future phases introducing additional GPU nodes will enable autoscaling.

---

# Scaling Dimensions

## Vertical Scaling

Increase:

- GPU memory
- GPU compute capacity
- Model size support

Examples:

- A10G → L4
- A10G → A100

---

## Horizontal Scaling

Increase:

- Number of vLLM replicas
- Number of GPU nodes
- Request processing capacity

Examples:

- 1 replica → 2 replicas
- 1 GPU → 2 GPUs

---

# Current Limitation

Current Environment:

- Single Node
- Single GPU
- Single vLLM Replica

Because only one GPU exists, scaling beyond a single vLLM replica is not currently possible.

---

# Future Architecture

```text
              Load Balancer
                     │
         ┌───────────┴───────────┐
         │                       │
    vLLM Replica 1         vLLM Replica 2
         │                       │
         └───────────┬───────────┘
                     │
                GPU Nodes
```

---

# Autoscaling Goals

The platform should scale before queue growth becomes excessive.

Target:

- Maintain latency SLOs
- Reduce queue time
- Prevent scheduler saturation
- Preserve user experience

---

# Benchmark Findings

Phase 2.2 identified:

- ~254 active requests
- ~767 queued requests
- No failures

This indicates queue buildup occurs before service instability.

Autoscaling should react before queue depth reaches these levels.
