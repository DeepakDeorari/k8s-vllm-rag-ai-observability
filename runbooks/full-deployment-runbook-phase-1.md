# Full Deployment Runbook

## Overview

This runbook documents the deployment of a complete GPU-enabled AI platform on AWS using:

- MicroK8s
- NVIDIA GPU Operator
- vLLM
- Open WebUI
- Qdrant
- FastAPI RAG Application
- Prometheus
- Grafana
- Loki
- Promtail
- Tempo
- OpenTelemetry Collector

Infrastructure:

```text
AWS EC2 g5.xlarge
Ubuntu 24.04 LTS
NVIDIA A10G GPU
4 vCPU
16 GB Memory
```

---

# Phase 1 - Host Validation

Verify OS:

```bash
cat /etc/os-release
```

Verify GPU:

```bash
lspci | grep -i nvidia

lspci | grep -i '3d controller\|vga'
```

Verify driver:

```bash
nvidia-smi
```

Verify kernel modules:

```bash
lsmod | grep nvidia
```

---

# Phase 2 - Install MicroK8s

Install:

```bash
snap install microk8s --classic --channel=1.35/stable
```

Wait for readiness:

```bash
microk8s status --wait-ready
```

Create alias:

```bash
echo "alias k='microk8s kubectl'" >> ~/.bashrc

source ~/.bashrc
```

Verify:

```bash
k get nodes

k get pods -A
```

---

# Phase 3 - Enable MicroK8s Addons

```bash
microk8s enable hostpath-storage

microk8s enable ingress

microk8s enable metrics-server

microk8s enable helm3
```

Validate:

```bash
k get pods -A
```

---

# Phase 4 - Enable GPU Operator

```bash
microk8s enable gpu
```

Validate:

```bash
k get pods -n gpu-operator-resources

k get runtimeclass
```

Verify GPU allocation:

```bash
k describe node | grep nvidia.com/gpu
```

---

# Phase 5 - CUDA Validation

Deploy CUDA test:

```bash
k apply -f manifests/gpu/cuda-test.yaml
```

Watch:

```bash
k get pod cuda-test -w
```

Check logs:

```bash
k logs cuda-test
```

Expected:

```text
Test PASSED
Done
```

---

# Phase 6 - Deploy vLLM

Create namespace:

```bash
k create namespace vllm
```

Create Hugging Face secret:

```bash
k -n vllm create secret generic hf-token \
  --from-literal=HF_TOKEN=<HF_TOKEN>
```

Deploy:

```bash
k apply -f manifests/vllm/vllm-pvc.yaml

k apply -f manifests/vllm/vllm.yaml
```

Validate:

```bash
k -n vllm get pods

k -n vllm get pvc

k -n vllm logs deploy/vllm
```

Watch startup:

```bash
k -n vllm logs -f deploy/vllm
```

---

# Phase 7 - Validate vLLM

Port-forward:

```bash
k -n vllm port-forward svc/vllm 8000:8000
```

List models:

```bash
curl -s http://127.0.0.1:8000/v1/models | jq .
```

Test inference:

```bash
curl -s http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model":"Qwen/Qwen2.5-1.5B-Instruct",
    "messages":[
      {
        "role":"user",
        "content":"What is Kubernetes?"
      }
    ],
    "max_tokens":100
  }' | jq .
```

---

# Phase 8 - Deploy Open WebUI

Add repo:

```bash
microk8s helm3 repo add open-webui \
https://open-webui.github.io/helm-charts

microk8s helm3 repo update
```

Create namespace:

```bash
k create namespace open-webui
```

Deploy:

```bash
microk8s helm3 upgrade --install open-webui \
open-webui/open-webui \
-n open-webui \
-f manifests/openwebui/open-webui-values.yaml
```

Validate:

```bash
k -n open-webui get pods

k -n open-webui get svc
```

Port-forward:

```bash
k -n open-webui port-forward svc/open-webui 8080:80
```

---

# Phase 9 - Validate Open WebUI

Verify connectivity:

```bash
k -n open-webui exec open-webui-0 -- env | grep OPENAI
```

Validate model discovery:

```bash
k -n open-webui exec open-webui-0 -- wget -qO- \
http://vllm.vllm.svc.cluster.local:8000/v1/models
```

Login to Open WebUI and verify:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

appears in the model list.

---

# Phase 10 - Deploy Qdrant

Add repository:

```bash
microk8s helm3 repo add qdrant \
https://qdrant.github.io/qdrant-helm

microk8s helm3 repo update
```

Create namespace:

```bash
k create namespace qdrant
```

Deploy:

```bash
microk8s helm3 upgrade --install qdrant \
qdrant/qdrant \
-n qdrant \
-f manifests/qdrant/qdrant-values.yaml
```

Validate:

```bash
k -n qdrant get all

k -n qdrant get pvc

k -n qdrant get endpoints
```

Health check:

```bash
k -n qdrant port-forward svc/qdrant 6333:6333

curl http://127.0.0.1:6333/healthz
```

---

# Phase 11 - Build RAG Application

Navigate:

```bash
cd applications/rag-app
```

Build image:

```bash
docker build -t rag-app:local .
```

Import image:

```bash
docker save rag-app:local | microk8s ctr image import -
```

Verify:

```bash
microk8s ctr images ls | grep rag-app
```

---

# Phase 12 - Deploy RAG Application

Create namespace:

```bash
k create namespace rag
```

Deploy:

```bash
k apply -f manifests/rag-app/rag-app.yaml
```

Validate:

```bash
k -n rag get pods

k -n rag logs deploy/rag-app
```

---

# Phase 13 - Validate RAG Application

Port-forward:

```bash
k -n rag port-forward svc/rag-app 8081:8080
```

Health endpoint:

```bash
curl http://127.0.0.1:8081/health
```

Ingest sample data:

```bash
curl -s http://127.0.0.1:8081/ingest \
-H "Content-Type: application/json" \
-d '{
  "texts":[
    "MicroK8s is a lightweight Kubernetes distribution.",
    "vLLM provides OpenAI compatible inference APIs.",
    "Qdrant is a vector database used for retrieval augmented generation."
  ]
}' | jq .
```

Query:

```bash
curl -s http://127.0.0.1:8081/query \
-H "Content-Type: application/json" \
-d '{
  "question":"What is Qdrant used for?"
}' | jq .
```

---

# Phase 14 - Deploy Prometheus and Grafana

Add repositories:

```bash
microk8s helm3 repo add prometheus-community \
https://prometheus-community.github.io/helm-charts

microk8s helm3 repo add grafana \
https://grafana.github.io/helm-charts

microk8s helm3 repo update
```

Create namespace:

```bash
k create namespace observability
```

Deploy:

```bash
microk8s helm3 upgrade --install kube-prometheus-stack \
prometheus-community/kube-prometheus-stack \
-n observability \
-f manifests/observability/kube-prometheus-stack-values.yaml
```

Validate:

```bash
k -n observability get pods
```

Access Grafana:

```bash
k -n observability port-forward \
svc/kube-prometheus-stack-grafana 3000:80
```

---

# Phase 15 - Deploy Loki

Deploy:

```bash
microk8s helm3 upgrade --install loki \
grafana/loki \
-n observability \
-f manifests/observability/loki-values.yaml
```

Validate:

```bash
k -n observability get pods | grep loki

k -n observability get svc | grep loki
```

---

# Phase 16 - Deploy Promtail

Deploy:

```bash
microk8s helm3 upgrade --install promtail \
grafana/promtail \
-n observability \
-f manifests/observability/promtail-values.yaml
```

Validate:

```bash
k -n observability get pods | grep promtail
```

Verify logs in Grafana Explore.

---

# Phase 17 - Deploy Tempo

Deploy:

```bash
microk8s helm3 upgrade --install tempo \
grafana/tempo \
-n observability \
-f manifests/observability/tempo-values.yaml
```

Validate:

```bash
k -n observability get svc | grep tempo
```

Add Tempo datasource in Grafana.

---

# Phase 18 - Deploy OpenTelemetry Collector

Add repository:

```bash
microk8s helm3 repo add open-telemetry \
https://open-telemetry.github.io/opentelemetry-helm-charts

microk8s helm3 repo update
```

Deploy:

```bash
microk8s helm3 upgrade --install otel-collector \
open-telemetry/opentelemetry-collector \
-n observability \
-f manifests/observability/otel-collector-values.yaml
```

Validate:

```bash
k -n observability get pods | grep otel

k -n observability logs \
deploy/otel-collector-opentelemetry-collector
```

---

# Phase 19 - Validate Tracing

Verify OTEL env variables:

```bash
k -n rag get deploy rag-app -o yaml | grep -A20 OTEL
```

Generate traffic:

```bash
for i in {1..10}; do
  curl -s http://127.0.0.1:8081/query \
    -H "Content-Type: application/json" \
    -d '{"question":"What is Qdrant used for?"}' >/dev/null
done
```

Verify traces:

```text
Grafana
→ Explore
→ Tempo
→ service.name = rag-app
```

---

# Phase 20 - Resource Validation

Node usage:

```bash
k top node
```

Pod usage:

```bash
k top pod -A
```

Allocated resources:

```bash
k describe node | grep -A20 Allocated
```

Cluster state:

```bash
k get pods -A
```

---

# Useful Port Forward Commands

### vLLM

```bash
k -n vllm port-forward svc/vllm 8000:8000
```

### Open WebUI

```bash
k -n open-webui port-forward svc/open-webui 8080:80
```

### Qdrant

```bash
k -n qdrant port-forward svc/qdrant 6333:6333
```

### RAG

```bash
k -n rag port-forward svc/rag-app 8081:8080
```

### Grafana

```bash
k -n observability port-forward \
svc/kube-prometheus-stack-grafana 3000:80
```

### Prometheus

```bash
k -n observability port-forward \
svc/kube-prometheus-stack-prometheus 9090:9090
```

### Loki

```bash
k -n observability port-forward svc/loki 3100:3100
```

### Tempo

```bash
k -n observability port-forward svc/tempo 3200:3200
```

---

# Successful Outcome

Validated:

- GPU Scheduling
- CUDA Workloads
- vLLM Inference
- Open WebUI
- Qdrant
- RAG Queries
- Prometheus Metrics
- Loki Logs
- Tempo Traces
- OpenTelemetry Collector

Final platform status:

```text
SUCCESS
```
