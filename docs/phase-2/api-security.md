# Phase 2.4 - API Security

## Overview

This document describes the current API security posture of the AI Platform.

The focus during Phase 2 is minimizing attack surface while maintaining platform functionality.

---

# Security Principles

The platform follows four primary principles:

1. Least Exposure
2. Internal Service Communication
3. Secret-Based Authentication
4. Controlled Administrative Access

---

# Secret Management

## Hugging Face Token

Namespace:

```text
vllm
```

Secret:

```text
hf-token
```

Purpose:

```text
Model download and authentication
```

Storage Method:

```text
Kubernetes Secret
```

The Hugging Face token is not stored directly inside application manifests.

---

# Internal Services

The following services are intentionally not exposed publicly.

## vLLM

```text
Namespace: vllm
Service Type: ClusterIP
```

## Qdrant

```text
Namespace: qdrant
Service Type: ClusterIP
```

## RAG API

```text
Namespace: rag
Service Type: ClusterIP
```

## Prometheus

```text
Namespace: observability
Service Type: ClusterIP
```

## Grafana

```text
Namespace: observability
Service Type: ClusterIP
```

## Loki

```text
Namespace: observability
Service Type: ClusterIP
```

## Tempo

```text
Namespace: observability
Service Type: ClusterIP
```

---

# Ingress Security

Current ingress exposure:

```text
None
```

Traefik is deployed but no ingress resources currently expose application services.

This reduces risk while platform engineering activities are in progress.

---

# Administrative Access

Administrative access is performed through:

```text
kubectl
kubectl port-forward
SSH access
```

No public management interfaces are exposed.

---

# Observability Access

Grafana access is currently performed using:

```text
kubectl port-forward
```

Prometheus access is currently performed using:

```text
kubectl port-forward
```

This prevents accidental exposure of monitoring systems.

---

# Security Benefits

Current design provides:

- Minimal external attack surface
- Internal-only service communication
- Secret-based credential storage
- Isolation of observability components
- Protection of the vector database
- Protection of the inference engine

---

# Known Limitations

The current platform does not yet implement:

- OAuth/OIDC
- JWT Authentication
- API Keys
- TLS Certificates
- Certificate Rotation
- External DNS
- Web Application Firewall

These capabilities may be introduced in future production-focused phases.

---

# Phase 2 Security Status

The platform currently operates with:

```text
Single ingress controller
Internal-only services
Kubernetes Secret management
Restricted administrative access
```

This security posture is considered appropriate for the Phase 2 engineering environment.
