# Phase 2.9 - Multi-Replica vLLM Routing

## Overview

This document defines the future request routing strategy for multiple vLLM replicas.

Current deployment uses a single vLLM instance.

Future deployments will support multiple inference replicas across multiple GPU nodes.

---

# Current Architecture

```text
Open WebUI
    ↓
RAG API
    ↓
vLLM
```

Single point of inference.

---

# Target Architecture

```text
Open WebUI
     ↓
RAG API
     ↓
Inference Service
     ↓

┌──────────┬──────────┬──────────┐
│          │          │
vLLM-1   vLLM-2   vLLM-3
```

---

# Routing Goals

- Increase throughput
- Reduce queue growth
- Reduce TTFT
- Improve availability
- Distribute inference load

---

# Replica Responsibilities

Each replica:

- Hosts identical model version
- Uses identical inference settings
- Processes independent requests

---

# Traffic Flow

Incoming requests:

```text
Client
    ↓
Open WebUI
    ↓
RAG API
    ↓
Kubernetes Service
    ↓
Available vLLM Replica
```

---

# Future Routing Options

Option 1:

Kubernetes Service Load Balancing

Benefits:

- Simple
- Native Kubernetes
- Low operational complexity

---

Option 2:

Traefik Weighted Routing

Benefits:

- Advanced traffic control
- Canary deployments
- Gradual rollouts

---

Option 3:

Dedicated AI Gateway

Examples:

- Envoy
- KGateway
- AI Gateway solutions

Benefits:

- Advanced routing
- Request policies
- Multi-model support

---

# Recommended Approach

Phase 2:

Native Kubernetes Service load balancing.

Future phases:

Evaluate advanced traffic shaping and AI gateways.
``
