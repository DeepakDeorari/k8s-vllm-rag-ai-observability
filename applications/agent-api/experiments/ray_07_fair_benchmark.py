import os
import statistics
import time
from typing import Any

import ray


BENCHMARK_ROUNDS = 5

KNOWLEDGE_QUERY = (
    "How should Kubernetes workload health "
    "problems be investigated?"
)


def sequential_prometheus() -> dict[str, Any]:
    """
    Execute Prometheus target-health diagnostics in the driver.
    """

    from tools.prometheus_health import (
        get_prometheus_target_health,
    )

    start = time.perf_counter()

    result = get_prometheus_target_health()

    return {
        "source": "prometheus",
        "pid": os.getpid(),
        "worker_type": "driver",
        "duration_seconds": (
            time.perf_counter() - start
        ),
        "result": result,
    }


def sequential_kubernetes() -> dict[str, Any]:
    """
    Execute Kubernetes unhealthy-pod diagnostics in the driver.
    """

    from tools.kubernetes_pods import (
        get_unhealthy_pods,
    )

    start = time.perf_counter()

    result = get_unhealthy_pods()

    return {
        "source": "kubernetes",
        "pid": os.getpid(),
        "worker_type": "driver",
        "duration_seconds": (
            time.perf_counter() - start
        ),
        "result": result,
    }


def sequential_qdrant() -> dict[str, Any]:
    """
    Execute Qdrant retrieval with the driver-resident MiniLM model.
    """

    from tools.qdrant_retriever import (
        retrieve_documents,
    )

    start = time.perf_counter()

    result = retrieve_documents(
        question=KNOWLEDGE_QUERY,
        limit=3,
    )

    return {
        "source": "qdrant",
        "pid": os.getpid(),
        "worker_type": "driver",
        "duration_seconds": (
            time.perf_counter() - start
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
def prometheus_task() -> dict[str, Any]:
    """
    Lightweight Ray Task for Prometheus diagnostics.
    """

    from tools.prometheus_health import (
        get_prometheus_target_health,
    )

    start = time.perf_counter()

    result = get_prometheus_target_health()

    return {
        "source": "prometheus",
        "pid": os.getpid(),
        "worker_type": "ray-task",
        "duration_seconds": (
            time.perf_counter() - start
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
def kubernetes_task() -> dict[str, Any]:
    """
    Lightweight Ray Task for Kubernetes diagnostics.
    """

    from tools.kubernetes_pods import (
        get_unhealthy_pods,
    )

    start = time.perf_counter()

    result = get_unhealthy_pods()

    return {
        "source": "kubernetes",
        "pid": os.getpid(),
        "worker_type": "ray-task",
        "duration_seconds": (
            time.perf_counter() - start
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
class KnowledgeActor:
    """
    Persistent Ray Actor containing MiniLM and the Qdrant client.
    """

    def __init__(self):
        initialization_start = (
            time.perf_counter()
        )

        from tools.qdrant_retriever import (
            retrieve_documents,
        )

        self.retrieve_documents = (
            retrieve_documents
        )

        self.pid = os.getpid()

        self.retrieval_count = 0

        self.initialization_seconds = (
            time.perf_counter()
            - initialization_start
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "ready",
            "pid": self.pid,
            "initialization_seconds": (
                self.initialization_seconds
            ),
            "retrieval_count": (
                self.retrieval_count
            ),
        }

    def retrieve(
        self,
        question: str,
        limit: int = 3,
    ) -> dict[str, Any]:
        start = time.perf_counter()

        result = self.retrieve_documents(
            question=question,
            limit=limit,
        )

        self.retrieval_count += 1

        return {
            "source": "qdrant",
            "pid": self.pid,
            "worker_type": "ray-actor",
            "duration_seconds": (
                time.perf_counter() - start
            ),
            "actor_retrieval_count": (
                self.retrieval_count
            ),
            "result": result,
        }

    def get_state(self) -> dict[str, Any]:
        return {
            "pid": self.pid,
            "initialization_seconds": (
                self.initialization_seconds
            ),
            "retrieval_count": (
                self.retrieval_count
            ),
        }


def run_sequential_round() -> tuple[
    list[dict[str, Any]],
    float,
]:
    """
    Execute all three diagnostics sequentially.
    """

    start = time.perf_counter()

    results = [
        sequential_prometheus(),
        sequential_kubernetes(),
        sequential_qdrant(),
    ]

    duration = (
        time.perf_counter() - start
    )

    return results, duration


def run_ray_round(
    knowledge_actor,
) -> tuple[
    list[dict[str, Any]],
    float,
]:
    """
    Execute all three diagnostics concurrently through Ray.
    """

    start = time.perf_counter()

    refs = [
        prometheus_task.remote(),
        kubernetes_task.remote(),
        knowledge_actor.retrieve.remote(
            KNOWLEDGE_QUERY,
            3,
        ),
    ]

    results = ray.get(
        refs
    )

    duration = (
        time.perf_counter() - start
    )

    return results, duration


def result_map(
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Index diagnostic results by source name.
    """

    return {
        result["source"]: result
        for result in results
    }


def validate_equivalence(
    sequential_results: list[
        dict[str, Any]
    ],
    ray_results: list[
        dict[str, Any]
    ],
) -> None:
    """
    Validate operational equivalence between execution modes.
    """

    sequential = result_map(
        sequential_results
    )

    ray_results_by_source = result_map(
        ray_results
    )

    sequential_targets = (
        sequential[
            "prometheus"
        ]["result"].get(
            "total_target_count"
        )
    )

    ray_targets = (
        ray_results_by_source[
            "prometheus"
        ]["result"].get(
            "total_target_count"
        )
    )

    sequential_unhealthy = (
        sequential[
            "kubernetes"
        ]["result"].get(
            "unhealthy_pod_count"
        )
    )

    ray_unhealthy = (
        ray_results_by_source[
            "kubernetes"
        ]["result"].get(
            "unhealthy_pod_count"
        )
    )

    sequential_documents = (
        sequential[
            "qdrant"
        ]["result"].get(
            "documents",
            [],
        )
    )

    ray_documents = (
        ray_results_by_source[
            "qdrant"
        ]["result"].get(
            "documents",
            [],
        )
    )

    sequential_texts = [
        document.get("text")
        for document in sequential_documents
    ]

    ray_texts = [
        document.get("text")
        for document in ray_documents
    ]

    assert (
        sequential_targets
        == ray_targets
    ), (
        "Prometheus target counts differ: "
        f"sequential={sequential_targets}, "
        f"ray={ray_targets}"
    )

    assert (
        sequential_unhealthy
        == ray_unhealthy
    ), (
        "Kubernetes unhealthy-pod counts differ: "
        f"sequential={sequential_unhealthy}, "
        f"ray={ray_unhealthy}"
    )

    assert (
        sequential_texts
        == ray_texts
    ), (
        "Qdrant document ordering or content differs."
    )


def diagnostic_timings(
    results: list[dict[str, Any]],
) -> str:
    """
    Format individual diagnostic timings.
    """

    indexed = result_map(
        results
    )

    return (
        "prometheus="
        f"{indexed['prometheus']['duration_seconds']:.4f}s, "
        "kubernetes="
        f"{indexed['kubernetes']['duration_seconds']:.4f}s, "
        "qdrant="
        f"{indexed['qdrant']['duration_seconds']:.4f}s"
    )


def summarize(
    name: str,
    samples: list[float],
) -> None:
    """
    Print descriptive statistics for exact wall-clock samples.
    """

    mean_value = statistics.mean(
        samples
    )

    median_value = statistics.median(
        samples
    )

    minimum_value = min(
        samples
    )

    maximum_value = max(
        samples
    )

    if len(samples) > 1:
        standard_deviation = (
            statistics.stdev(
                samples
            )
        )
    else:
        standard_deviation = 0.0

    print(f"\n{name}")
    print("-" * len(name))

    print(
        f"Samples:   {len(samples)}"
    )

    print(
        f"Mean:      {mean_value:.4f}s"
    )

    print(
        f"Median:    {median_value:.4f}s"
    )

    print(
        f"Minimum:   {minimum_value:.4f}s"
    )

    print(
        f"Maximum:   {maximum_value:.4f}s"
    )

    print(
        "Std dev:   "
        f"{standard_deviation:.4f}s"
    )


def main() -> None:
    """
    Run a fair warm sequential versus warm Ray benchmark.
    """

    ray.init()

    try:
        print("\n")
        print("=" * 72)
        print("RAY CLUSTER RESOURCES")
        print("=" * 72)

        print(
            ray.cluster_resources()
        )


        print("\n")
        print("=" * 72)
        print("INITIALIZING KNOWLEDGE PATHS")
        print("=" * 72)

        driver_warmup_start = (
            time.perf_counter()
        )

        driver_warmup = (
            sequential_qdrant()
        )

        driver_warmup_duration = (
            time.perf_counter()
            - driver_warmup_start
        )

        print(
            "Driver MiniLM/Qdrant warm-up: "
            f"{driver_warmup_duration:.4f}s"
        )

        print(
            "Driver warm-up documents: "
            f"{driver_warmup['result'].get('result_count')}"
        )


        actor_creation_start = (
            time.perf_counter()
        )

        knowledge_actor = (
            KnowledgeActor.remote()
        )

        actor_health = ray.get(
            knowledge_actor.health.remote()
        )

        actor_creation_duration = (
            time.perf_counter()
            - actor_creation_start
        )

        print(
            "KnowledgeActor creation: "
            f"{actor_creation_duration:.4f}s"
        )

        print(
            f"KnowledgeActor health: "
            f"{actor_health}"
        )


        actor_warmup_start = (
            time.perf_counter()
        )

        actor_warmup = ray.get(
            knowledge_actor.retrieve.remote(
                KNOWLEDGE_QUERY,
                3,
            )
        )

        actor_warmup_duration = (
            time.perf_counter()
            - actor_warmup_start
        )

        print(
            "KnowledgeActor retrieval warm-up: "
            f"{actor_warmup_duration:.4f}s"
        )

        print(
            "Actor warm-up documents: "
            f"{actor_warmup['result'].get('result_count')}"
        )


        print("\n")
        print("=" * 72)
        print("WARMING STATELESS RAY TASK WORKERS")
        print("=" * 72)

        task_warmup_start = (
            time.perf_counter()
        )

        task_warmup_results = ray.get(
            [
                prometheus_task.remote(),
                kubernetes_task.remote(),
            ]
        )

        task_warmup_duration = (
            time.perf_counter()
            - task_warmup_start
        )

        print(
            "Task-worker warm-up: "
            f"{task_warmup_duration:.4f}s"
        )

        for result in task_warmup_results:
            print(
                f"- {result['source']} "
                f"pid={result['pid']} "
                f"duration="
                f"{result['duration_seconds']:.4f}s"
            )


        print("\n")
        print("=" * 72)
        print("STEADY-STATE BENCHMARK")
        print("=" * 72)

        sequential_samples = []
        ray_samples = []

        validation_count = 0

        for round_number in range(
            1,
            BENCHMARK_ROUNDS + 1,
        ):
            print(
                f"\nRound {round_number}/"
                f"{BENCHMARK_ROUNDS}"
            )

            # Alternate order to reduce systematic bias from
            # cache state, transient load, and execution order.
            ray_first = (
                round_number % 2 == 0
            )

            if ray_first:
                ray_results, ray_duration = (
                    run_ray_round(
                        knowledge_actor
                    )
                )

                sequential_results, sequential_duration = (
                    run_sequential_round()
                )

                execution_order = (
                    "Ray → Sequential"
                )

            else:
                sequential_results, sequential_duration = (
                    run_sequential_round()
                )

                ray_results, ray_duration = (
                    run_ray_round(
                        knowledge_actor
                    )
                )

                execution_order = (
                    "Sequential → Ray"
                )

            validate_equivalence(
                sequential_results=(
                    sequential_results
                ),
                ray_results=ray_results,
            )

            validation_count += 1

            sequential_samples.append(
                sequential_duration
            )

            ray_samples.append(
                ray_duration
            )

            print(
                f"  Order:      "
                f"{execution_order}"
            )

            print(
                "  Sequential: "
                f"{sequential_duration:.4f}s"
            )

            print(
                "  Ray:        "
                f"{ray_duration:.4f}s"
            )

            print(
                "  Speedup:    "
                f"{sequential_duration / ray_duration:.2f}x"
            )

            print(
                "  Sequential diagnostics: "
                f"{diagnostic_timings(sequential_results)}"
            )

            print(
                "  Ray diagnostics:        "
                f"{diagnostic_timings(ray_results)}"
            )


        print("\n")
        print("=" * 72)
        print("BENCHMARK SUMMARY")
        print("=" * 72)

        summarize(
            "Warm Sequential",
            sequential_samples,
        )

        summarize(
            "Warm Ray Actor",
            ray_samples,
        )

        sequential_mean = statistics.mean(
            sequential_samples
        )

        ray_mean = statistics.mean(
            ray_samples
        )

        mean_speedup = (
            sequential_mean / ray_mean
        )

        sequential_median = (
            statistics.median(
                sequential_samples
            )
        )

        ray_median = statistics.median(
            ray_samples
        )

        median_speedup = (
            sequential_median
            / ray_median
        )

        print("\nComparison")
        print("----------")

        print(
            "Mean speedup:   "
            f"{mean_speedup:.2f}x"
        )

        print(
            "Median speedup: "
            f"{median_speedup:.2f}x"
        )

        print(
            "Mean reduction: "
            f"{(
                1 - (
                    ray_mean
                    / sequential_mean
                )
            ) * 100:.2f}%"
        )

        print(
            "Validated rounds: "
            f"{validation_count}/"
            f"{BENCHMARK_ROUNDS}"
        )


        actor_state = ray.get(
            knowledge_actor.get_state.remote()
        )

        print("\nKnowledgeActor State")
        print("--------------------")

        print(actor_state)


        print("\n")
        print("=" * 72)
        print("BENCHMARK INTERPRETATION")
        print("=" * 72)

        print(
            "One-time driver and Actor initialization "
            "costs were excluded from measured rounds."
        )

        print(
            "Stateless Ray task workers were warmed "
            "before measurement."
        )

        print(
            "Sequential and Ray execution order was "
            "alternated between rounds."
        )

        print(
            "Every measured round passed operational "
            "result-equivalence validation."
        )

    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
