# Phase 3: Ray Benchmarks and Failure Engineering

## 1. Overview

Phase 3 introduced Ray as the distributed execution layer underneath selected AI SRE investigation workflows.

The goal was not simply to add Ray to the technology stack.

The engineering objectives were to determine:

- Where Ray improves execution
- Where Ray introduces unnecessary overhead
- Which workloads should remain sequential
- When Ray Tasks should be used
- When Ray Actors should be used
- How Ray schedules workloads according to logical resources
- How Ray behaves across multiple Kubernetes nodes
- How KubeRay responds to worker failure
- How Ray Tasks recover from worker loss
- How Ray Actors recover from worker loss
- What happens to Actor state during reconstruction
- How distributed execution should be combined with LangGraph

The experiments progressed from isolated Ray fundamentals to real SRE diagnostics, multi-node execution, controlled worker failure, and finally the deployed broad AI SRE investigation route.

---

# 2. Final Ray Architecture

The final Ray deployment uses KubeRay on MicroK8s.

```text
                         MicroK8s
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
     Kubernetes Node 1             Kubernetes Node 2
      ip-172-31-7-23                ip-172-31-6-36
             │                             │
             ▼                             ▼
         Ray Head                      Ray Worker
             │                             │
             │                             ├── Prometheus Tasks
             │                             ├── Kubernetes Tasks
             │                             └── KnowledgeActor
             │                                      │
             │                                    MiniLM
             │                                      │
             │                                    Qdrant
             │
             └──────── Ray scheduling ───────────────┘
```

Final runtime images:

```text
Ray Head:
ai-sre-ray:0.1.1

Ray Worker:
ai-sre-ray:0.1.1
```

Ray version:

```text
2.59.0
```

The Ray runtime is CPU-only.

The Ray workload does not request GPUs.

---

# 3. Ray Core Fundamentals

Before integrating Ray with the AI SRE platform, the core Ray execution model was validated independently.

The practical learning sequence included:

```text
Ray local runtime
        ↓
Remote Task
        ↓
ObjectRef
        ↓
ray.get()
        ↓
Parallel Tasks
        ↓
Resource scheduling
        ↓
Actors
        ↓
Persistent Actor state
```

---

# 4. First Ray Task

The first experiment created a simple remote function.

Conceptually:

```python
@ray.remote
def identify_worker():
    ...
```

Invocation:

```text
identify_worker.remote()
        ↓
ObjectRef
        ↓
ray.get()
        ↓
Python result
```

The result returned a different process ID from the Python driver.

This demonstrated that the function executed in a Ray worker process rather than directly inside the calling Python process.

Validated:

```text
Ray initialization        PASS
Remote Task               PASS
ObjectRef                 PASS
ray.get()                 PASS
Separate worker process   PASS
```

---

# 5. Synthetic Parallelism Benchmark

A simple benchmark compared normal sequential Python execution with Ray parallel execution.

Three operations each slept for two seconds.

## 5.1 Sequential execution

```text
Task 1
2 seconds
    ↓
Task 2
2 seconds
    ↓
Task 3
2 seconds
```

Measured result:

```text
6.00 seconds
```

## 5.2 Ray execution

All three Tasks were submitted before waiting for results.

```text
Task 1 ───────── 2 seconds ──────┐
Task 2 ───────── 2 seconds ──────┤
Task 3 ───────── 2 seconds ──────┘
                                 │
                                 ▼
                              ray.get()
```

Measured result:

```text
2.24 seconds
```

Measured speedup:

```text
2.68x
```

## 5.3 Conclusion

Ray provided a clear performance improvement when:

- Tasks were independent
- Each Task performed enough work
- All Tasks could run concurrently
- Scheduling overhead was small relative to useful Task duration

This established the basic parallel-execution benefit before applying Ray to real SRE workloads.

---

# 6. Logical CPU Scheduling Benchmark

The local Ray runtime reported:

```text
CPU: 4
GPU: 1
Accelerator type: A10G
```

The experiment submitted six Tasks.

Each Task requested:

```python
num_cpus=1
```

Each Task slept for:

```text
2 seconds
```

## 6.1 Expected scheduling

With four logical CPUs:

```text
Wave 1:
Task 0
Task 1
Task 2
Task 3

Wave 2:
Task 4
Task 5
```

## 6.2 Measured result

```text
Total duration:
4.27 seconds
```

Worker PIDs from the first wave were reused for Tasks in the second wave.

## 6.3 Conclusion

The experiment validated:

- Ray logical CPU accounting
- Resource-based Task admission
- Scheduling in waves
- Worker process reuse
- Difference between submitted Tasks and simultaneously runnable Tasks

---

# 7. Ray Actor State Experiment

A Ray Actor was created with persistent state.

The Actor maintained:

```text
investigation_count
```

Three method calls returned:

```text
Call 1:
investigation_count = 1

Call 2:
investigation_count = 2

Call 3:
investigation_count = 3
```

The same PID handled all three calls.

## 7.1 Conclusion

The experiment demonstrated the difference between:

```text
Ray Task
→ stateless or independently reusable work

Ray Actor
→ persistent worker process with reusable state
```

This became important later when MiniLM initialization was identified as an expensive repeated operation.

---

# 8. First Real SRE Ray Benchmark

The first real Ray benchmark executed:

```text
Prometheus target health
Kubernetes unhealthy-pod diagnostics
Qdrant knowledge retrieval
```

The same operations were executed sequentially and through Ray.

## 8.1 Sequential result

```text
Prometheus:
0.0377 seconds

Kubernetes:
1.0449 seconds

Qdrant:
1.2982 seconds

Sequential total:
2.3808 seconds
```

## 8.2 Ray result

Internal Task timings:

```text
Prometheus:
0.0091 seconds

Kubernetes:
0.6990 seconds

Qdrant:
0.3189 seconds
```

However, total Ray wall time was:

```text
7.9167 seconds
```

Measured speedup:

```text
0.30x
```

Ray was significantly slower.

---

# 9. Root Cause: Incorrect Dependency Boundary

The poor Ray result was investigated rather than treated as a Ray failure.

The original experiment imported:

```text
tools.qdrant_retriever
```

at module import time.

The Qdrant retriever initialized:

```text
SentenceTransformer
MiniLM
Qdrant client
```

during import.

This meant unrelated Ray workers could load MiniLM.

Conceptually:

```text
Prometheus Ray Worker
        ↓
imports experiment module
        ↓
imports qdrant_retriever
        ↓
loads MiniLM
        ↓
finally queries Prometheus
```

This was unnecessary.

The workload had an incorrect dependency boundary.

---

# 10. Cold Versus Warm Task Experiment

The experiment was repeated to determine whether worker reuse would eliminate the initialization cost.

Results:

```text
Sequential:
1.1662 seconds

Ray cold:
7.8496 seconds

Ray warm:
7.7209 seconds
```

The warm result remained slow.

Logs showed MiniLM initialization occurring in another Ray worker during the second round.

## 10.1 Conclusion

Stateless Ray Tasks do not provide guaranteed application-specific affinity to one initialized worker.

Worker reuse alone was not sufficient for the embedding model.

A persistent Actor was required.

---

# 11. KnowledgeActor Design

The architecture was redesigned.

### Stateless diagnostics

```text
Prometheus
→ Ray Task

Kubernetes
→ Ray Task
```

### Stateful knowledge retrieval

```text
KnowledgeActor
├── Load MiniLM once
├── Create Qdrant client once
├── Retain runtime state
└── Handle repeated retrieval calls
```

This isolated the expensive embedding runtime from unrelated Ray workers.

---

# 12. KnowledgeActor Benchmark

The Actor-based design produced:

```text
Sequential:
8.4986 seconds

Actor creation:
7.5089 seconds

Actor warm-up:
0.3301 seconds

Ray Actor round 1:
0.8287 seconds

Ray Actor round 2:
0.6968 seconds
```

The initial sequential measurement included first-time MiniLM initialization.

Therefore the initially displayed:

```text
12.20x
```

speedup was not considered a fair steady-state comparison.

The more defensible steady-state improvement was approximately:

```text
1.3x to 1.7x
```

depending on the sequential baseline used.

## 12.1 Conclusion

The Actor solved the initialization problem.

However, accurate benchmarking required removing initialization costs from both sides.

---

# 13. Fair Warm Benchmark

A fair benchmark was created with:

- Driver-side warm-up
- KnowledgeActor warm-up
- Stateless worker warm-up
- Alternating execution order
- Five measured rounds
- Result-equivalence validation

Execution order alternated:

```text
Round 1:
Sequential → Ray

Round 2:
Ray → Sequential

Round 3:
Sequential → Ray

Round 4:
Ray → Sequential

Round 5:
Sequential → Ray
```

## 13.1 Warm sequential results

```text
Samples:
5

Mean:
0.2265 seconds

Median:
0.0639 seconds

Minimum:
0.0621 seconds

Maximum:
0.8770 seconds

Standard deviation:
0.3636 seconds
```

## 13.2 Warm Ray results

```text
Samples:
5

Mean:
0.2073 seconds

Median:
0.0633 seconds

Minimum:
0.0610 seconds

Maximum:
0.7869 seconds

Standard deviation:
0.3240 seconds
```

## 13.3 Comparison

```text
Mean speedup:
1.09x

Median speedup:
1.01x

Mean reduction:
8.47%

Validated rounds:
5/5
```

## 13.4 Conclusion

The median result showed essentially no meaningful performance difference.

The warmed diagnostic workload was already too fast.

Typical source timings were approximately:

```text
Prometheus:
2–4 ms

Kubernetes:
50–60 ms

Qdrant:
9–13 ms
```

The theoretical parallelism benefit was only a few milliseconds.

Ray scheduling and result-transfer overhead consumed most of the available improvement.

---

# 14. Investigation Throughput Benchmark

The experiment then compared five complete sequential investigations against five concurrently submitted Ray investigations.

## 14.1 Sequential batch

```text
Investigations:
5

Total duration:
0.3207 seconds

Average wall-clock cost:
0.0641 seconds

Throughput:
15.59 investigations/second
```

## 14.2 Ray concurrent batch

```text
Investigations:
5

Total duration:
0.9327 seconds

Average wall-clock cost:
0.1865 seconds

Throughput:
5.36 investigations/second
```

## 14.3 Comparison

```text
Batch completion speedup:
0.34x

Throughput improvement:
-65.61%
```

## 14.4 Conclusion

Concurrency decreased throughput for this workload.

The operations were too inexpensive to benefit from distributed scheduling.

---

# 15. Sequential vs ThreadPoolExecutor vs Ray

A final local concurrency comparison tested:

```text
Sequential Python

ThreadPoolExecutor

Ray + KnowledgeActor
```

Five investigations were executed.

## 15.1 Sequential Python

```text
Total:
0.3370 seconds

Per investigation:
0.0674 seconds

Throughput:
14.84 investigations/second
```

## 15.2 ThreadPoolExecutor

```text
Total:
0.6247 seconds

Per investigation:
0.1249 seconds

Throughput:
8.00 investigations/second
```

## 15.3 Ray + KnowledgeActor

```text
Total:
0.9281 seconds

Per investigation:
0.1856 seconds

Throughput:
5.39 investigations/second
```

## 15.4 Comparison

```text
Threads vs sequential:
0.54x

Ray vs sequential:
0.36x

Threads vs Ray:
1.49x
```

## 15.5 Conclusion

The final ranking for the small warmed workload was:

```text
1. Sequential Python
2. ThreadPoolExecutor
3. Ray
```

This benchmark directly influenced the final architecture.

Ray was not added to the existing lightweight routes.

---

# 16. Multi-Node KubeRay Deployment

KubeRay was deployed on the MicroK8s cluster.

The RayCluster was configured as:

```text
Ray Head:
Node 1
ip-172-31-7-23
Normal task CPUs = 0

Ray Worker:
Node 2
ip-172-31-6-36
Logical CPUs = 2
```

Ray cluster resources reported:

```text
CPU:
2

GPU:
0
```

This ensured normal Ray Tasks had to execute on the worker.

---

# 17. Cross-Node Task Execution Test

A remote Task was submitted from the Ray Head.

The Task returned execution metadata.

Result:

```text
Hostname:
Ray Worker Pod

Pod IP:
10.1.227.x

Assigned resources:
CPU = 1
```

The worker Pod was scheduled on:

```text
ip-172-31-6-36
```

The driver ran on Node 1.

## 17.1 Conclusion

This proved genuine distributed execution:

```text
Node 1
Ray Head / Driver
        ↓
Ray Scheduler
        ↓
Node 2
Ray Worker
        ↓
Python Task
```

---

# 18. Multi-Node Resource Scheduling Test

The Ray Worker advertised:

```text
2 CPUs
```

Four Tasks were submitted.

Each requested:

```text
1 CPU
```

Each slept for:

```text
2 seconds
```

The Tasks executed in two waves.

Measured total duration:

```text
5.33 seconds
```

The useful synthetic work represented approximately:

```text
4 seconds
```

The additional time included first-run distributed scheduling and worker overhead.

---

# 19. Ray Task Failure Engineering

A long-running retryable Task was created.

Configuration:

```python
@ray.remote(
    num_cpus=1,
    max_retries=3,
)
```

The Task slept for:

```text
120 seconds
```

The active Ray Worker Pod was deliberately deleted while the Task was running.

---

# 20. Task Failure Timeline

Original Task:

```text
Started:
2026-10-29 14:29:24 UTC

Worker Pod IP:
10.1.227.20

Worker PID:
525
```

The worker was deleted.

Ray reported:

```text
Task resilient_task failed.

There are 3 retries remaining,
so the task will be retried.

Task failed because the node it
was running on is dead or unavailable.
```

KubeRay created a replacement worker.

The retried Task started:

```text
2026-10-29 14:30:37 UTC
```

Replacement worker IP:

```text
10.1.227.36
```

Replacement worker PID:

```text
117
```

Task completed:

```text
2026-10-29 14:32:37 UTC
```

Total wall time:

```text
193.90 seconds
```

---

# 21. Task Failure Conclusion

The recovery sequence was:

```text
Task starts
    ↓
Worker Pod deleted
    ↓
Ray detects node loss
    ↓
Task execution fails
    ↓
KubeRay creates replacement worker
    ↓
Replacement worker joins Ray cluster
    ↓
Ray reschedules Task
    ↓
Task starts from beginning
    ↓
Task completes
```

The Task did not resume from the interrupted `sleep()` position.

It executed again from the beginning.

This implies retryable distributed Tasks should be:

- Idempotent
- Safe to execute multiple times
- Deterministic where possible
- Protected from duplicate irreversible side effects

---

# 22. Ray Actor Failure Engineering

A second failure experiment tested a Ray Actor.

Actor configuration:

```python
@ray.remote(
    num_cpus=1,
    max_restarts=1,
    max_task_retries=1,
)
```

The Actor contained:

```text
counter = 0
```

The long-running Actor method incremented:

```text
counter = 1
```

then slept for:

```text
120 seconds
```

The active worker Pod was deleted while the method was executing.

---

# 23. Actor Failure Timeline

Original Actor:

```text
Created:
2026-10-29 14:35:39 UTC

Worker Pod:
ai-sre-ray-cpu-workers-worker-n8qz8

Pod IP:
10.1.227.36

PID:
238

Counter after method start:
1
```

Worker deletion:

```text
2026-10-29 14:35:48 UTC
```

Ray reported:

```text
Task ResilientActor.long_operation failed.

There are 1 retries remaining.

The actor is temporarily unavailable:
The actor was restarted.
```

KubeRay created a replacement worker.

Reconstructed Actor:

```text
Created:
2026-10-29 14:36:33 UTC

Worker Pod:
ai-sre-ray-cpu-workers-worker-vpj92

Pod IP:
10.1.227.27

PID:
114
```

The Actor constructor reset:

```text
counter = 0
```

The retried method then incremented:

```text
counter = 1
```

The Actor method completed:

```text
2026-10-29 14:38:33 UTC
```

Total wall time:

```text
174.63 seconds
```

---

# 24. Actor Failure Conclusion

Actor recovery behaved as:

```text
Actor state:
counter = 1
      ↓
Worker failure
      ↓
Actor process lost
      ↓
KubeRay restores worker
      ↓
Ray reconstructs Actor
      ↓
Actor constructor reruns
      ↓
counter = 0
      ↓
method retries
      ↓
counter = 1
```

This demonstrated a critical distributed-systems lesson:

```text
Ray Actor memory
≠ durable application state
```

Actors should retain:

- Models
- API clients
- Runtime connections
- Temporary caches
- Reconstructable state

Actors should not be the only copy of:

- Incident workflow state
- Audit records
- Completed remediation state
- Idempotency records
- Durable checkpoints

---

# 25. Custom Ray Runtime Image

The generic Ray image was extended with the SRE application dependencies.

Final image:

```text
ai-sre-ray:0.1.1
```

The runtime includes:

```text
Ray 2.59.0
Kubernetes client
Requests
Qdrant client
Sentence Transformers
Transformers
CPU-only PyTorch
Offline MiniLM
SRE diagnostic tools
Ray collector
```

CPU-only PyTorch validation:

```text
Torch:
2.14.1+cpu

CUDA available:
False

Torch CUDA version:
None
```

The MiniLM model successfully loaded with:

```text
--network none
```

and produced:

```text
384-dimensional embeddings
```

---

# 26. Ray Image Optimization

Full AI SRE Agent content size:

```text
3.62 GB
```

Dedicated Ray SRE content size:

```text
1.48 GB
```

Approximate content reduction:

```text
59%
```

The dedicated runtime avoids installing the full GPU-enabled PyTorch dependency chain required by other environments.

An unused:

```text
cupy-cuda12x
```

package remains inherited from the Ray base image and is documented as technical debt.

---

# 27. Ray RBAC

The Ray Pods use:

```text
ServiceAccount:
ai-sre-ray
```

A ClusterRoleBinding grants:

```text
ai-sre-agent-readonly
```

permissions.

Validated:

```text
List Pods:
yes

Get Nodes:
yes

List Events:
yes

Delete Pods:
no

Patch Deployments:
no

Create Secrets:
no
```

This means the distributed runtime can investigate the cluster but cannot remediate it.

---

# 28. Real Distributed SRE Fan-Out

The first real broad distributed investigation executed:

```text
Prometheus target health
Prometheus node CPU
Kubernetes workload health
Kubernetes restart history
Qdrant knowledge retrieval
```

All operations executed on the Ray Worker on Node 2.

Example execution metadata:

```text
Worker:
ai-sre-ray-cpu-workers-worker-b7gkh

Pod IP:
10.1.227.33
```

---

# 29. Real Distributed Source Timings

Example source timings:

```text
Prometheus health:
0.0124 seconds

Prometheus CPU:
0.0194 seconds

Kubernetes health:
0.0467 seconds

Kubernetes restarts:
0.5225 seconds

Knowledge retrieval:
0.3433 seconds
```

Total distributed wall time:

```text
1.9732 seconds
```

All five sources completed successfully.

---

# 30. Fractional CPU Scheduling

The initial real fan-out used one CPU per operation.

With only two Ray CPUs and one CPU reserved by the KnowledgeActor, stateless diagnostics were effectively serialized.

The final collector changed the stateless Task allocations to:

```text
0.25 CPU
```

per Task.

The KnowledgeActor uses:

```text
0.5 CPU
```

This provides enough logical scheduling capacity for the I/O-heavy Tasks to execute concurrently.

---

# 31. External Ray Collector Validation

The reusable collector was tested through the Ray Client endpoint.

First collector call:

```text
Valid:
True

Successful sources:
5/5

Collector duration:
10.9315 seconds

Client wall time:
13.9988 seconds

Retrieved documents:
3
```

This initial call included:

- Ray Client initialization
- Actor creation
- MiniLM initialization
- Distributed Task startup

---

# 32. Warm Collector Validation

The same collector was called again.

Result:

```text
Valid:
True

Successful sources:
5/5

Collector duration:
3.51 seconds

Client wall time:
6.4411 seconds

Knowledge retrieval count:
2
```

The same named Actor was reused.

Actor identity remained:

```text
Actor:
ai-sre-knowledge-v1

Worker:
same Ray Worker

PID:
same Actor PID
```

This demonstrated persistent runtime reuse across investigations.

---

# 33. LangGraph + Ray Integration

The final LangGraph architecture added:

```text
BROAD
```

as a primary route.

The new execution path is:

```text
classify_primary_intent
        ↓
BROAD
        ↓
collect_ray_evidence
        ↓
Ray Client
        ↓
KubeRay
        ↓
Evidence bundle
        ↓
format_ray_response
        ↓
END
```

Existing CPU, health, Kubernetes restart, unhealthy, validation, and safe-fallback routes were preserved.

---

# 34. Full Broad Graph Validation

A complete graph invocation returned:

```text
route:
broad

distributed_valid:
True

distributed_errors:
[]

retrieved documents:
3
```

Collector duration:

```text
3.1053 seconds
```

Full graph wall time:

```text
5.9931 seconds
```

Execution metadata confirmed the distributed Tasks and KnowledgeActor executed on the Ray Worker.

Validation result:

```text
FULL_BROAD_GRAPH_PASS
```

---

# 35. API Regression Validation

The FastAPI contract suite was expanded with a broad-route test.

Final result:

```text
12 passed
```

The existing endpoints and routes remained compatible.

The `/capabilities` endpoint now advertises:

```text
cpu
health
kubernetes/restarts
kubernetes/unhealthy
broad
```

---

# 36. Final Deployed Broad Investigation

The final AI SRE Agent image was deployed:

```text
ai-sre-agent:0.1.3
```

The deployed FastAPI Pod connects to Ray using:

```text
RAY_ADDRESS=
ray://ai-sre-ray-head-svc.ray-cluster.svc.cluster.local:10001
```

The full path became:

```text
Client
  ↓
FastAPI
  ↓
LangGraph
  ↓
Ray Client
  ↓
KubeRay Head
  ↓
Ray Worker
  ↓
Prometheus / Kubernetes / Qdrant
  ↓
Evidence bundle
  ↓
LangGraph
  ↓
API response
```

---

# 37. Final Five-Request Sample

Five deployed broad investigations were executed.

Results:

```text
Request 1:
1848.49 ms

Request 2:
251.11 ms

Request 3:
255.34 ms

Request 4:
1167.31 ms

Request 5:
2144.99 ms
```

All five returned:

```text
route = broad
documents = 3
```

Success rate:

```text
5/5
```

---

# 38. Prometheus Final Broad-Route Metrics

Prometheus recorded six broad-route investigation samples, including the earlier deployment-validation request.

Sample count:

```text
6
```

Average accumulated latency:

```text
3.10753 seconds
```

Histogram p50 estimate:

```text
1.50 seconds
```

Histogram p95 estimate:

```text
approximately 17 seconds
```

The p95 value is not treated as a reliable exact percentile because:

- Only six observations existed
- Histogram buckets were relatively coarse
- `histogram_quantile()` estimates values from buckets
- The directly observed final requests were significantly below 17 seconds

The directly observed five-request range was:

```text
Minimum:
0.251 seconds

Maximum:
2.145 seconds
```

---

# 39. Persistent KnowledgeActor Final Validation

The deployed named Actor reported:

```text
status:
ready

hostname:
ai-sre-ray-cpu-workers-worker-2n56d

pod_ip:
10.1.227.32

pid:
160

initialization_seconds:
16.5236

retrieval_count:
3
```

This confirmed that the Actor remained resident and reused MiniLM across requests.

---

# 40. Final Ray Engineering Decision

The most important result from the Ray work was not a benchmark number.

The important result was identifying the correct workload boundary.

The experiments demonstrated:

```text
Parallelism
does not automatically mean
better performance.
```

For tiny warmed diagnostics:

```text
Sequential Python
was faster than
ThreadPoolExecutor
and Ray.
```

For broader distributed investigations, Ray provides:

- Cross-node execution
- Resource scheduling
- Failure isolation
- Worker reconstruction
- Task retry
- Actor reconstruction
- Persistent model runtime
- Operational scalability

The final architecture therefore uses:

```text
Small diagnostics
→ Sequential execution

Broad investigations
→ Ray distributed fan-out

Expensive reusable model state
→ Ray Actor

Durable workflow state
→ LangGraph or external storage
```

---

# 41. Key Lessons

## Lesson 1: Benchmark before distributing

Distributed execution has non-zero cost.

Scheduling, serialization, process startup, dependency loading, and result transfer can exceed the useful work of very small Tasks.

---

## Lesson 2: Dependency boundaries matter

The initial design caused unrelated workers to load MiniLM.

Separating lightweight Tasks from the persistent KnowledgeActor removed unnecessary initialization.

---

## Lesson 3: Actors are not databases

Actor state is convenient runtime state.

Actor reconstruction reruns the constructor.

Durable state must live elsewhere.

---

## Lesson 4: Retries imply duplicate execution

Task and Actor-method retries can execute code more than once.

Mutating operations require idempotency protection.

---

## Lesson 5: Kubernetes and Ray solve different scheduling problems

```text
Kubernetes
→ schedules Pods onto Nodes

Ray
→ schedules Python Tasks and Actors
  onto Ray workers
```

KubeRay connects these two layers.

---

## Lesson 6: Reliability is more than successful startup

The Ray cluster was intentionally subjected to worker failure.

Recovery behavior was observed end to end rather than assumed.

---

# 42. Final Validation Matrix

```text
Ray Core Tasks
PASS

ObjectRefs
PASS

ray.get()
PASS

Parallel execution
PASS

Resource scheduling
PASS

Fractional resources
PASS

Actors
PASS

Persistent Actor state
PASS

Real Prometheus Tasks
PASS

Real Kubernetes Tasks
PASS

Qdrant Actor
PASS

Offline MiniLM
PASS

Multi-node KubeRay
PASS

Cross-node scheduling
PASS

Task worker failure
PASS

Task retry
PASS

KubeRay worker restoration
PASS

Actor worker failure
PASS

Actor reconstruction
PASS

Actor method retry
PASS

RBAC
PASS

LangGraph integration
PASS

FastAPI integration
PASS

Prometheus instrumentation
PASS

API regression tests
12/12 PASS

Deployed broad investigations
5/5 PASS
```

---

# 43. Technical Debt

The following items remain intentionally outside Phase 3 scope.

### Python patch-version alignment

Observed:

```text
FastAPI Ray Client:
Python 3.12.3

Ray runtime:
Python 3.12.14
```

The integration worked successfully, but matching patch versions is preferred.

### CPU-only Ray image cleanup

The Ray image still includes:

```text
cupy-cuda12x
```

from the base image.

The runtime was confirmed CPU-only for PyTorch, but further image optimization remains possible.

### More latency samples

Six Prometheus samples are insufficient for a reliable high-percentile latency analysis.

Future performance testing should collect significantly more observations.

### Histogram buckets

The broad-route latency distribution would benefit from more granular histogram buckets around the observed sub-three-second range.

### Durable checkpointing

If future Ray Actors own workflow-critical state, external persistence or checkpointing should be introduced.

---

# 44. Final Outcome

Phase 3 demonstrated that Ray can be integrated into an AI SRE platform without forcing distributed execution into every workflow.

The final system uses Ray where Ray provides architectural value:

- Distributed broad investigation
- Cross-node execution
- Persistent model runtime
- Failure isolation
- Task recovery
- Actor reconstruction

The project also demonstrates where Ray should not be used:

- Tiny, low-latency diagnostic operations that execute more efficiently sequentially

This evidence-based distinction is the central engineering outcome of the Ray phase.

The Ray architecture and benchmark work are now complete.
