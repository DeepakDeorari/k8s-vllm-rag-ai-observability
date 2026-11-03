# Phase 3 Operations Runbook

## 1. Purpose

This runbook covers operation, validation, troubleshooting, recovery, and rollback for the Phase 3 distributed AI SRE Agent platform.

The platform is intentionally read-only. It diagnoses infrastructure and returns operational evidence, but it does not autonomously modify Kubernetes resources.

## 2. Deployed Versions

```text
AI SRE Agent: ai-sre-agent:0.1.3
Ray Runtime: ai-sre-ray:0.1.1
Ray: 2.59.0
KubeRay Operator: 1.7.0
```

## 3. Namespaces

```text
agent-platform
ray-cluster
ray-system
observability
vllm
qdrant
```

## 4. Node Placement

```text
Node 1: ip-172-31-7-23
- AI SRE Agent
- Ray Head
- Primary vLLM workload

Node 2: ip-172-31-6-36
- Ray Worker
- Secondary vLLM workload
```

The Ray runtime is CPU-only and does not request GPU resources.

## 5. Quick Health Check

```bash
kubectl get nodes -o wide
kubectl -n agent-platform get deployment,pod,svc -o wide
kubectl -n ray-cluster get raycluster,pod,svc -o wide
kubectl -n ray-system get deployment,pod -o wide
```

Expected state:

```text
Kubernetes Nodes: Ready
AI SRE Agent: 1/1 Running
RayCluster: ready
Ray Workers: 1/1 available
KubeRay Operator: 1/1 Running
```

## 6. Capture Current Pod Names

```bash
AGENT_POD=$(kubectl -n agent-platform get pods -l app.kubernetes.io/name=ai-sre-agent -o jsonpath='{.items[0].metadata.name}')
HEAD_POD=$(kubectl -n ray-cluster get pods -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}')
WORKER_POD=$(kubectl -n ray-cluster get pods -l ray.io/node-type=worker -o jsonpath='{.items[0].metadata.name}')

echo "AGENT_POD=$AGENT_POD"
echo "HEAD_POD=$HEAD_POD"
echo "WORKER_POD=$WORKER_POD"
```

## 7. Validate Running Images

```bash
kubectl -n agent-platform get pod "$AGENT_POD" -o jsonpath='{.spec.containers[0].image}{"\n"}'
kubectl -n ray-cluster get pods -o jsonpath='{range .items[*]}{.metadata.name}{"  "}{.spec.nodeName}{"  "}{.spec.containers[0].image}{"\n"}{end}'
```

Expected:

```text
AI SRE Agent: ai-sre-agent:0.1.3
Ray Head: ai-sre-ray:0.1.1
Ray Worker: ai-sre-ray:0.1.1
```

## 8. Validate Agent Environment

```bash
kubectl -n agent-platform exec "$AGENT_POD" -- env | grep -E '^(QWEN_|PROMETHEUS_URL|QDRANT_URL|RAY_|EMBEDDING_MODEL|TRANSFORMERS_OFFLINE|HF_HUB_OFFLINE)'
```

Expected Ray settings:

```text
RAY_ADDRESS=ray://ai-sre-ray-head-svc.ray-cluster.svc.cluster.local:10001
RAY_NAMESPACE=ai-sre-platform
RAY_KNOWLEDGE_ACTOR_NAME=ai-sre-knowledge-v1
```

## 9. API Port Forward

Run in a dedicated terminal:

```bash
kubectl -n agent-platform port-forward svc/ai-sre-agent 8082:8082
```

## 10. Health Endpoint

```bash
curl -sS http://127.0.0.1:8082/health | python -m json.tool
```

Expected:

```json
{
  "status": "healthy",
  "service": "ai-sre-langgraph-api"
}
```

## 11. Capabilities Endpoint

```bash
curl -sS http://127.0.0.1:8082/capabilities | python -m json.tool
```

Expected public routes:

```text
cpu
health
kubernetes
broad
```

Expected Kubernetes intents:

```text
restarts
unhealthy
```

The API should report `read_only: true`.

## 12. Metrics Endpoint

```bash
curl -sS http://127.0.0.1:8082/metrics | grep '^ai_sre_'
```

Expected metric families:

```text
ai_sre_investigations_total
ai_sre_route_total
ai_sre_investigation_duration_seconds
ai_sre_analysis_validation_total
ai_sre_fallback_total
ai_sre_retrieved_documents
```

## 13. CPU Investigation

```bash
curl -sS -X POST http://127.0.0.1:8082/investigate \
  -H "Content-Type: application/json" \
  -d '{"question":"Show the current Kubernetes node CPU utilization."}' \
  | python -m json.tool
```

Expected route: `cpu`.

## 14. Prometheus Health Investigation

```bash
curl -sS -X POST http://127.0.0.1:8082/investigate \
  -H "Content-Type: application/json" \
  -d '{"question":"Are all Prometheus scrape targets healthy?"}' \
  | python -m json.tool
```

Expected route: `health`.

## 15. Kubernetes Unhealthy Workload Investigation

```bash
curl -sS -X POST http://127.0.0.1:8082/investigate \
  -H "Content-Type: application/json" \
  -d '{"question":"Are any Kubernetes pods unhealthy now?"}' \
  | python -m json.tool
```

Expected:

```text
route: kubernetes
kubernetes_intent: unhealthy
```

## 16. Kubernetes Restart Investigation

```bash
curl -sS -X POST http://127.0.0.1:8082/investigate \
  -H "Content-Type: application/json" \
  -d '{"question":"Show the workloads with the highest historical restart counts."}' \
  | python -m json.tool
```

Expected:

```text
route: kubernetes
kubernetes_intent: restarts
```

## 17. Broad Distributed Investigation

```bash
curl -sS -X POST http://127.0.0.1:8082/investigate \
  -H "Content-Type: application/json" \
  -d '{"question":"Investigate overall Kubernetes and monitoring platform health."}' \
  | python -m json.tool
```

Expected:

```text
route: broad
kubernetes_intent: null
retrieved_documents: 3
```

The answer should include Prometheus target health, Kubernetes workload health, node CPU utilization, and relevant platform knowledge.

## 18. Repeated Broad Validation

```bash
for i in $(seq 1 5); do
  echo "Broad investigation $i/5"
  curl -sS -X POST http://127.0.0.1:8082/investigate \
    -H "Content-Type: application/json" \
    -d '{"question":"Investigate overall Kubernetes and monitoring platform health."}' \
    | python -c 'import json,sys; r=json.load(sys.stdin); print("route=",r["route"],"duration_ms=",r["duration_ms"],"documents=",len(r["retrieved_documents"]))'
done
```

Final recorded samples:

```text
1848.49 ms
251.11 ms
255.34 ms
1167.31 ms
2144.99 ms
```

## 19. Agent Logs

```bash
kubectl -n agent-platform logs "$AGENT_POD" --timestamps --tail=300
kubectl -n agent-platform logs "$AGENT_POD" --timestamps -f
kubectl -n agent-platform logs "$AGENT_POD" --previous --timestamps --tail=300
```

## 20. Agent Startup Troubleshooting

Observed application import time was approximately 10.71 seconds. During startup the Pod can temporarily show `Running` but `0/1 Ready`.

Inspect events:

```bash
kubectl -n agent-platform describe pod "$AGENT_POD" | sed -n '/Events:/,$p'
```

Check PID 1:

```bash
kubectl -n agent-platform exec "$AGENT_POD" -- sh -c 'tr "\0" " " < /proc/1/cmdline; echo'
```

Expected process includes:

```text
uvicorn app.langgraph_main:app --host 0.0.0.0 --port 8082
```

## 21. Internal Health Test

```bash
kubectl -n agent-platform exec -i "$AGENT_POD" -- python - <<'PY'
import urllib.request
with urllib.request.urlopen("http://127.0.0.1:8082/health", timeout=5) as response:
    print("status:", response.status)
    print("body:", response.read().decode())
PY
```

Expected status: `200`.

## 22. Agent Resource Usage

```bash
kubectl top pod -n agent-platform "$AGENT_POD" --containers
```

Observed Phase 3 memory usage was approximately 646 MiB. The configured memory limit is 4 GiB.

## 23. RayCluster Health

```bash
kubectl -n ray-cluster get raycluster ai-sre-ray
kubectl -n ray-cluster get pods -o wide
```

Expected:

```text
Desired workers: 1
Available workers: 1
GPU: 0
Status: ready
```

## 24. Ray Cluster Resources

```bash
kubectl -n ray-cluster exec -i "$HEAD_POD" -- python - <<'PY'
import ray
ray.init(address="auto")
print("Cluster resources:", ray.cluster_resources())
print("Available resources:", ray.available_resources())
ray.shutdown()
PY
```

Expected total task CPU: `2`. GPU should be zero or absent.

## 25. Ray Status and State Inspection

```bash
kubectl -n ray-cluster exec "$HEAD_POD" -- ray status
kubectl -n ray-cluster exec "$HEAD_POD" -- ray list tasks --detail
kubectl -n ray-cluster exec "$HEAD_POD" -- ray list nodes --detail
kubectl -n ray-cluster exec "$HEAD_POD" -- ray list actors --detail
```

## 26. KnowledgeActor Health

```bash
kubectl -n ray-cluster exec -i "$HEAD_POD" -- python - <<'PY'
import ray
ray.init(address="auto", namespace="ai-sre-platform")
actor = ray.get_actor("ai-sre-knowledge-v1")
print(ray.get(actor.health.remote()))
ray.shutdown()
PY
```

Expected status: `ready`.

Final recorded state included:

```text
hostname: ai-sre-ray-cpu-workers-worker-2n56d
pod_ip: 10.1.227.32
pid: 160
initialization_seconds: 16.5236
retrieval_count: 3
```

## 27. Prometheus Broad Route Metrics

Broad route counter:

```bash
curl -sG "http://10.152.183.49:9090/api/v1/query" \
  --data-urlencode 'query=ai_sre_route_total{route="broad"}' \
  | python -m json.tool
```

Broad sample count:

```bash
curl -sG "http://10.152.183.49:9090/api/v1/query" \
  --data-urlencode 'query=ai_sre_investigation_duration_seconds_count{route="broad"}' \
  | python -m json.tool
```

Final sample count: `6`.

Broad average latency:

```bash
curl -sG "http://10.152.183.49:9090/api/v1/query" \
  --data-urlencode 'query=sum(ai_sre_investigation_duration_seconds_sum{route="broad"}) / sum(ai_sre_investigation_duration_seconds_count{route="broad"})' \
  | python -m json.tool
```

Recorded value: `3.10753 seconds`.

Broad p50:

```bash
curl -sG "http://10.152.183.49:9090/api/v1/query" \
  --data-urlencode 'query=histogram_quantile(0.50, sum by (le) (ai_sre_investigation_duration_seconds_bucket{route="broad"}))' \
  | python -m json.tool
```

Recorded estimate: `1.50 seconds`.

Broad p95:

```bash
curl -sG "http://10.152.183.49:9090/api/v1/query" \
  --data-urlencode 'query=histogram_quantile(0.95, sum by (le) (ai_sre_investigation_duration_seconds_bucket{route="broad"}))' \
  | python -m json.tool
```

Recorded estimate: approximately 17 seconds. This is not an exact observed request duration because only six samples existed and histogram buckets were coarse. Directly observed final requests ranged from approximately 0.251 seconds to 2.145 seconds.

## 28. AI SRE Agent RBAC

```bash
AGENT_SA="system:serviceaccount:agent-platform:ai-sre-agent"

kubectl auth can-i list pods --all-namespaces --as="$AGENT_SA"
kubectl auth can-i get nodes --as="$AGENT_SA"
kubectl auth can-i delete pods --all-namespaces --as="$AGENT_SA"
```

Expected:

```text
list pods: yes
get nodes: yes
delete pods: no
```

## 29. Ray RBAC

```bash
RAY_SA="system:serviceaccount:ray-cluster:ai-sre-ray"

kubectl auth can-i list pods --all-namespaces --as="$RAY_SA"
kubectl auth can-i get nodes --as="$RAY_SA"
kubectl auth can-i delete pods --all-namespaces --as="$RAY_SA"
kubectl auth can-i patch deployments --all-namespaces --as="$RAY_SA"
kubectl auth can-i create secrets -n ray-cluster --as="$RAY_SA"
```

Expected:

```text
list pods: yes
get nodes: yes
delete pods: no
patch deployments: no
create secrets: no
```

## 30. Validate Kubernetes Access from Ray Worker

```bash
kubectl -n ray-cluster exec -i "$WORKER_POD" -- python - <<'PY'
from tools.kubernetes_pods import get_unhealthy_pods
result = get_unhealthy_pods()
print("RAY_KUBERNETES_ACCESS_OK")
print("Total pods:", result.get("total_pod_count"))
print("Unhealthy pods:", result.get("unhealthy_pod_count"))
PY
```

## 31. Validate CPU-Only PyTorch

```bash
docker run --rm -i ai-sre-ray:0.1.1 python - <<'PY'
import torch
print("Torch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
print("Torch CUDA version:", torch.version.cuda)
PY
```

Expected:

```text
Torch: 2.14.1+cpu
CUDA available: False
Torch CUDA version: None
```

## 32. Validate Offline MiniLM

```bash
docker run --rm -i --network none ai-sre-ray:0.1.1 python - <<'PY'
import os
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(os.environ["EMBEDDING_MODEL"])
embedding = model.encode("Kubernetes pod restart investigation")
print("Embedding dimensions:", len(embedding))
print("OFFLINE_MINILM_OK")
PY
```

Expected:

```text
Embedding dimensions: 384
OFFLINE_MINILM_OK
```

## 33. Controlled Ray Worker Recovery

Do not execute during an active production investigation.

```bash
OLD_WORKER=$(kubectl -n ray-cluster get pods -l ray.io/node-type=worker -o jsonpath='{.items[0].metadata.name}')
echo "OLD_WORKER=$OLD_WORKER"
kubectl -n ray-cluster delete pod "$OLD_WORKER" --wait=false
kubectl -n ray-cluster get pods -o wide -w
```

Expected sequence:

```text
Old worker terminates
New worker is created
New worker becomes 1/1 Running
```

Validate replacement:

```bash
NEW_WORKER=$(kubectl -n ray-cluster get pods -l ray.io/node-type=worker -o jsonpath='{.items[0].metadata.name}')
echo "OLD_WORKER=$OLD_WORKER"
echo "NEW_WORKER=$NEW_WORKER"
kubectl -n ray-cluster get pod "$NEW_WORKER" -o wide
```

Expected Node: `ip-172-31-6-36`.

## 34. Task Retry Semantics

Ray Task recovery uses re-execution. A failed Task starts its function from the beginning.

Retryable Tasks should be:

```text
idempotent
safe to execute multiple times
deterministic where practical
protected from duplicate external side effects
```

Read-only Prometheus, Kubernetes, and Qdrant operations are naturally suitable for retry.

## 35. Actor Recovery Semantics

When the Worker hosting an Actor fails:

```text
Actor process is lost
KubeRay restores worker capacity
Ray reconstructs the Actor
Actor constructor runs again
Runtime state is recreated
```

For KnowledgeActor:

```text
MiniLM reloads
Qdrant client is recreated
Retrieval counter resets
Temporary cache is lost
```

Do not use Actor memory as the only copy of durable workflow state.

## 36. Agent Rollback

```bash
kubectl -n agent-platform rollout history deployment/ai-sre-agent
kubectl -n agent-platform rollout undo deployment/ai-sre-agent
kubectl -n agent-platform rollout status deployment/ai-sre-agent --timeout=10m
```

Previous stable image:

```text
ai-sre-agent:0.1.2
```

The previous image does not contain the final broad Ray route.

## 37. RayCluster Image Update

RayCluster runtime image changes required RayCluster recreation during Phase 3 development.

```bash
kubectl -n ray-cluster delete raycluster ai-sre-ray
kubectl apply -f ray-cluster.yaml
kubectl -n ray-cluster get pods -o wide -w
```

Important versions:

```text
ai-sre-ray:0.1.0
- Does not contain the final ray_sre_collector module

ai-sre-ray:0.1.1
- Final Phase 3 Ray runtime
```

## 38. Source Validation

From `applications/agent-api`:

```bash
python -m py_compile \
  app/langgraph_main.py \
  workflows/sre_monitoring_graph.py \
  tools/ray_sre_collector.py \
  tests/test_langgraph_api.py

pytest -q tests/test_langgraph_api.py
```

Expected:

```text
12 passed
```

## 39. Live Evaluation Test Note

`tests/test_llm_monitoring_graph.py` was written as an executable live evaluation script and can raise `SystemExit` during import.

Do not include it in generic pytest collection until converted into proper pytest tests or moved to an evaluations directory.

## 40. Host Ray Client Testing

Port-forward:

```bash
kubectl -n ray-cluster port-forward svc/ai-sre-ray-head-svc 10001:10001
```

Export:

```bash
export RAY_ADDRESS="ray://127.0.0.1:10001"
export RAY_NAMESPACE="ai-sre-platform"
export RAY_KNOWLEDGE_ACTOR_NAME="ai-sre-knowledge-v1"
```

Test:

```bash
python - <<'PY'
import os
import ray
ray.init(address=os.environ["RAY_ADDRESS"], namespace=os.environ["RAY_NAMESPACE"])
print("RAY_CLIENT_CONNECTION_OK")
print(ray.cluster_resources())
ray.shutdown()
PY
```

## 41. Common Problem: Ray Client Timeout

For host testing, verify the port-forward and variables:

```bash
ss -lnt | grep ':10001'
env | grep '^RAY_'
```

Restart the Ray Client port-forward if necessary.

The deployed FastAPI Pod uses Kubernetes Service DNS and does not require a local port-forward.

## 42. Common Problem: Missing Collector Module

Symptom:

```text
ModuleNotFoundError: No module named 'tools.ray_sre_collector'
```

The required Ray runtime is:

```text
ai-sre-ray:0.1.1
```

## 43. Common Problem: Qwen Classification Failure

Symptom:

```text
route: unsupported
classification_reason: OpenAIConnectionError
```

The classifier intentionally fails closed. Check vLLM before interpreting routing results.

```bash
kubectl -n vllm get pods,svc
```

## 44. Common Problem: Broad Partial Failure

The Ray collector records failures independently per source.

Inspect internal state fields:

```text
distributed_valid
distributed_errors
distributed_evidence
distributed_execution
distributed_duration_seconds
```

One failed source does not automatically discard successful evidence from other sources.

## 45. Common Problem: KnowledgeActor Missing

The collector uses the named detached Actor:

```text
ai-sre-knowledge-v1
```

with `get_if_exists=True`.

If the Actor is missing, the collector recreates it. The first request is slower because MiniLM must load again.

## 46. Common Problem: Ray Worker Missing

```bash
kubectl -n ray-cluster get pods -o wide
kubectl -n ray-cluster get raycluster ai-sre-ray
kubectl -n ray-system logs deployment/kuberay-operator --tail=300
```

KubeRay should restore the desired worker count.

## 47. Safety Principle

Do not add mutation permissions to the Phase 3 ServiceAccounts.

The Phase 3 identities intentionally prohibit:

```text
create
update
patch
delete
```

A future remediation phase should use a separate ServiceAccount, separate RBAC, explicit authorization, approval gates, idempotency keys, audit logging, and rollback procedures.

## 48. Technical Debt

Accepted Phase 3 technical debt:

```text
1. Align Python patch versions between Ray Client and Ray runtime.
2. Investigate removing inherited cupy-cuda12x from the CPU-only Ray image.
3. Consider lazy-loading the host-side Qdrant retriever.
4. Collect more broad-route latency samples.
5. Refine Prometheus histogram buckets.
6. Add durable checkpointing before storing workflow-critical state in Actors.
```

Observed Python versions:

```text
FastAPI Ray Client: Python 3.12.3
Ray Runtime: Python 3.12.14
```

## 49. Files Not to Commit

Do not commit:

```text
Docker image tar archives
__pycache__
*.pyc
.pytest_cache
Ray session data
Virtual environments
Temporary benchmark outputs
*.pre-ray
*.broken
*.corrupt
```

## 50. Operational Completion Criteria

Phase 3 is healthy when:

```text
Kubernetes Nodes are Ready
AI SRE Agent is 1/1 Running
/health returns HTTP 200
/capabilities includes broad
/metrics is scraped
RayCluster status is ready
Ray Worker is available
KnowledgeActor status is ready
Broad investigation succeeds
Prometheus broad route counter increments
Read-only RBAC remains enforced
API tests report 12 passed
```

## 51. Final Workload Boundary

The final execution model is intentional:

```text
CPU route: direct execution
Prometheus health route: direct execution
Kubernetes unhealthy route: direct execution
Kubernetes restart route: direct evidence, retrieval, and guarded analysis
Broad platform investigation: Ray distributed evidence fan-out
```

The architecture is frozen for Phase 3.

Future capabilities should be developed as a new project phase.

Phase 3 operations are documented and closed.
