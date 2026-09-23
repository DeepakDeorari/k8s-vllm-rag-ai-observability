# Phase 2.11 - Failure Engineering

## Overview

This phase evaluated platform resilience under controlled failure conditions.

The goal was to validate:

- Kubernetes self-healing behavior
- Recovery characteristics
- Failure detection times
- GPU workload recovery
- Node failure handling

All tests were executed against the production-like two-node inference platform.

---

# Environment

## Cluster

| Component | Value |
|------------|------------|
| Kubernetes | MicroK8s v1.35.6 |
| Worker Nodes | 2 |
| GPUs | 2x NVIDIA A10G |
| Inference Engine | vLLM |
| Models | Qwen 2.5 1.5B, Phi-3 Mini 4K |

---

# Platform Topology

```text
Node 1
├── Qwen
├── Open WebUI
├── RAG API
├── Qdrant
└── Observability Stack

Node 2
└── Phi-3
```

---

# Failure Scenarios

## Test 1 - Primary Qwen Pod Failure

### Failure Injected

```bash
kubectl delete pod -n vllm \
-l app.kubernetes.io/instance=primary
```

### Observations

Replacement pod was automatically created.

Timeline:

```text
Running (0/1 Ready) : 93 sec
Ready (1/1)         : 112 sec
```

### Recovery Time

```text
112 seconds
```

### Result

```text
PASS
```

No manual intervention required.

---

## Test 2 - Secondary Phi-3 Pod Failure

### Failure Injected

```bash
kubectl delete pod -n vllm \
-l app.kubernetes.io/instance=secondary
```

### Observations

Replacement pod was automatically created.

Timeline:

```text
Running (0/1 Ready) : 12 sec
Ready (1/1)         : 103 sec
```

### Recovery Time

```text
103 seconds
```

### Result

```text
PASS
```

No manual intervention required.

---

## Test 3 - Worker Node Drain

### Failure Injected

```bash
kubectl drain ip-172-31-6-36 \
  --ignore-daemonsets \
  --delete-emptydir-data
```

### Observations

Node was successfully cordoned and drained.

The Phi-3 pod was evicted.

Kubernetes created a replacement pod:

```text
vllm-secondary-xxxxx
```

The replacement remained:

```text
Pending
```

### Scheduler Events

```text
0/2 nodes are available:

1 node(s) didn't match Pod's node affinity/selector

1 node(s) were unschedulable
```

### Root Cause

Phi-3 is pinned to Node 2:

```yaml
nodeSelector:
  kubernetes.io/hostname: ip-172-31-6-36
```

After drain:

```text
Node 2 = SchedulingDisabled
Node 1 = Selector mismatch
```

### Recovery

```bash
kubectl uncordon ip-172-31-6-36
```

Recovery completed in:

```text
102 seconds
```

### Result

```text
PARTIAL PASS
```

Automatic recreation occurred but manual node recovery was required.

---

## Test 4 - Worker Node Loss

### Failure Injected

Worker EC2 instance was stopped.

### Timeline

#### Node Failure Detection

```text
Stop Initiated : 09:54:56 UTC

Node NotReady  : 09:55:39 UTC
```

Detection Time:

```text
43 seconds
```

---

### Kubernetes Reaction

Existing Phi-3 pod entered:

```text
Terminating
```

Kubernetes created a replacement pod:

```text
vllm-secondary-xxxxx
```

The replacement remained:

```text
Pending
```

### Scheduler Events

```text
0/2 nodes are available:

1 node(s) didn't match Pod's node affinity/selector

1 node(s) had untolerated taints
```

### Result

```text
No automatic workload recovery
```

---

### Node Recovery

#### Node Start Initiated

```text
10:04:18 UTC
```

#### Node Ready

```text
10:04:47 UTC
```

Node Recovery Time:

```text
29 seconds
```

---

### Phi-3 Service Recovery

Replacement pod transitioned:

```text
Pending
↓
ContainerCreating
↓
Running
↓
Ready
```

Service Restored:

```text
10:08:03 UTC
```

Recovery Time:

```text
225 seconds
```

---

# Failure Recovery Summary

| Failure Scenario | Recovery Type | Recovery Time |
|-----------------|---------------|---------------|
| Qwen Pod Failure | Automatic | 112 sec |
| Phi-3 Pod Failure | Automatic | 103 sec |
| Worker Node Drain | Manual uncordon required | 102 sec |
| Worker Node Loss | Node restore required | 225 sec |

---

# Key Findings

## Finding 1

The platform provides strong pod-level resilience.

Measured recovery:

```text
103-112 seconds
```

without operator intervention.

---

## Finding 2

Kubernetes correctly detects worker-node failure.

Observed detection time:

```text
43 seconds
```

---

## Finding 3

The Deployment controller correctly recreates failed workloads.

Replacement pods were created automatically in all scenarios.

---

## Finding 4

The platform currently does not provide node-level high availability.

Reason:

```text
Model workloads are intentionally pinned
to specific GPU nodes.
```

via:

```yaml
nodeSelector
```

and local storage affinity.

---

## Finding 5

Recovery is limited by model initialization.

Recovery time is dominated by:

- GPU initialization
- Weight loading
- KV cache creation
- CUDA graph capture
- Readiness probes

rather than scheduler latency.

---

# Architectural Assessment

Current platform resilience:

| Capability | Status |
|------------|---------|
| Pod Self-Healing | ✅ |
| Deployment Recovery | ✅ |
| Worker Failure Detection | ✅ |
| Automatic Node Failover | ❌ |
| Multi-Node GPU Redundancy | ❌ |

---

# Conclusion

The platform successfully demonstrated Kubernetes self-healing behavior for GPU-backed inference workloads.

Pod failures recovered automatically within approximately two minutes.

Worker-node failure was detected within 43 seconds and recovery proceeded correctly after node restoration.

The primary resilience limitation is intentional node pinning and local storage affinity, which prevent automatic failover of model-specific workloads to alternate nodes.

The platform therefore provides robust pod-level recovery but does not yet provide node-level high availability.

---

# Phase Status

```text
Phase 2.11 - Failure Engineering

Status: COMPLETE ✅
```
