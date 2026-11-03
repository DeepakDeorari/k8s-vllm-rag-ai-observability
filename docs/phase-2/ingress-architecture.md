# Phase 2.4 - Ingress Architecture

## Overview

This document describes the network exposure model for the AI Platform during Phase 2.

The platform uses Traefik as the Kubernetes ingress controller while application services remain internal-only.

---

# Current Architecture

```text
Internet
    │
    ▼
Traefik Ingress Controller
    │
    ▼
Open WebUI
    │
    ▼
RAG API
    │
    ▼
vLLM
    │
    ▼
Qdrant
```

---

# Kubernetes Service Model

## Traefik

Namespace:

```text
ingress
```

Service Type:

```text
LoadBalancer
```

Purpose:

```text
Primary ingress controller
```

---

## Open WebUI

Namespace:

```text
open-webui
```

Service Type:

```text
ClusterIP
```

Purpose:

```text
User-facing AI interface
```

Exposure:

```text
Internal only
```

---

## RAG API

Namespace:

```text
rag
```

Service Type:

```text
ClusterIP
```

Purpose:

```text
Retrieval-Augmented Generation service
```

Exposure:

```text
Internal only
```

---

## vLLM

Namespace:

```text
vllm
```

Service Type:

```text
ClusterIP
```

Purpose:

```text
LLM Inference Engine
```

Exposure:

```text
Internal only
```

---

## Qdrant

Namespace:

```text
qdrant
```

Service Type:

```text
ClusterIP
```

Purpose:

```text
Vector database
```

Exposure:

```text
Internal only
```

---

# Observability Services

The following services remain internal-only.

```text
Grafana
Prometheus
Loki
Tempo
OTel Collector
```

All observability access is performed through controlled methods such as:

```text
kubectl port-forward
```

---

# Current Ingress Status

Current ingress resources:

```text
None
```

Traefik is installed and operational but no public routes are currently defined.

This intentionally minimizes external exposure during development and benchmarking phases.

---

# Security Model

Only the ingress controller is designed for external access.

Application workloads remain isolated behind Kubernetes ClusterIP services.

This prevents direct external access to:

- vLLM
- Qdrant
- Prometheus
- Grafana
- Loki
- Tempo

---

# Future Direction

Future phases may introduce:

- Public Open WebUI access
- HTTPS termination
- Authentication
- Rate limiting
- External DNS

These features are intentionally deferred until after performance, scaling, and multi-node objectives are completed.
