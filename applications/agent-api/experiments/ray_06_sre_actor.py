import os
import time
from typing import Any

import ray


KNOWLEDGE_QUERY = (
    "How should Kubernetes workload health "
    "problems be investigated?"
)


def run_sequential_prometheus() -> dict[str, Any]:
    """
    Run Prometheus target-health diagnostics in the driver.

    The import is intentionally local so Ray workers executing
    unrelated tasks do not load unnecessary dependencies.
    """

    from tools.prometheus_health import (
        get_prometheus_target_health,
    )

    start = time.perf_counter()

    result = get_prometheus_target_health()

    return {
        "source": "prometheus",
        "worker_type": "driver",
        "pid": os.getpid(),
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


def run_sequential_kubernetes() -> dict[str, Any]:
    """
    Run Kubernetes unhealthy-pod diagnostics in the driver.
    """

    from tools.kubernetes_pods import (
        get_unhealthy_pods,
    )

    start = time.perf_counter()

    result = get_unhealthy_pods()

    return {
        "source": "kubernetes",
        "worker_type": "driver",
        "pid": os.getpid(),
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


def run_sequential_qdrant() -> dict[str, Any]:
    """
    Run Qdrant retrieval in the driver.

    Importing qdrant_retriever here initializes MiniLM in the
    driver process only.
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
        "worker_type": "driver",
        "pid": os.getpid(),
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
def prometheus_task() -> dict[str, Any]:
    """
    Lightweight stateless Ray task for Prometheus diagnostics.

    This worker imports only the Prometheus dependency path.
    It does not import Sentence Transformers or load MiniLM.
    """

    from tools.prometheus_health import (
        get_prometheus_target_health,
    )

    start = time.perf_counter()

    result = get_prometheus_target_health()

    return {
        "source": "prometheus",
        "worker_type": "ray-task",
        "pid": os.getpid(),
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
def kubernetes_task() -> dict[str, Any]:
    """
    Lightweight stateless Ray task for Kubernetes diagnostics.

    This worker imports only the Kubernetes dependency path.
    It does not import Sentence Transformers or load MiniLM.
    """

    from tools.kubernetes_pods import (
        get_unhealthy_pods,
    )

    start = time.perf_counter()

    result = get_unhealthy_pods()

    return {
        "source": "kubernetes",
        "worker_type": "ray-task",
        "pid": os.getpid(),
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
class KnowledgeActor:
    """
    Persistent Ray Actor for semantic knowledge retrieval.

    MiniLM and the Qdrant client are initialized once when the
    Actor starts and remain resident across subsequent calls.
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

        self.initialization_seconds = round(
            (
                time.perf_counter()
                - initialization_start
            ),
            4,
        )

    def health(self) -> dict[str, Any]:
        """
        Confirm that the Actor has initialized and is ready.
        """

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
        """
        Retrieve platform knowledge using the resident MiniLM model
        and Qdrant client.
        """

        start = time.perf_counter()

        result = self.retrieve_documents(
            question=question,
            limit=limit,
        )

        self.retrieval_count += 1

        return {
            "source": "qdrant",
            "worker_type": "ray-actor",
            "pid": self.pid,
            "duration_seconds": round(
                time.perf_counter() - start,
                4,
            ),
            "actor_retrieval_count": (
                self.retrieval_count
            ),
            "result": result,
        }

    def get_state(self) -> dict[str, Any]:
        """
        Return persistent Actor state for validation.
        """

        return {
            "pid": self.pid,
            "initialization_seconds": (
                self.initialization_seconds
            ),
            "retrieval_count": (
                self.retrieval_count
            ),
        }


def print_result_summary(
    result: dict[str, Any],
) -> None:
    """
    Print timing and process information for one diagnostic result.
    """

    print(
        f"{result['source']:12} "
        f"{result['duration_seconds']:.4f}s "
        f"| pid={result['pid']} "
        f"| worker={result['worker_type']}"
    )


def run_sequential_round() -> tuple[
    list[dict[str, Any]],
    float,
]:
    """
    Execute the three diagnostics sequentially in the driver.
    """

    print("\n")
    print("=" * 70)
    print("SEQUENTIAL REAL SRE DIAGNOSTICS")
    print("=" * 70)

    start = time.perf_counter()

    results = [
        run_sequential_prometheus(),
        run_sequential_kubernetes(),
        run_sequential_qdrant(),
    ]

    duration = (
        time.perf_counter() - start
    )

    for result in results:
        print_result_summary(
            result
        )

    print(
        f"\nSequential total: "
        f"{duration:.4f} seconds"
    )

    return results, duration


def run_ray_round(
    knowledge_actor,
    round_name: str,
) -> tuple[
    list[dict[str, Any]],
    float,
]:
    """
    Fan out independent diagnostics concurrently.

    Prometheus and Kubernetes run as lightweight Tasks.
    Qdrant retrieval runs through the persistent KnowledgeActor.
    """

    print("\n")
    print("=" * 70)
    print(round_name)
    print("=" * 70)

    start = time.perf_counter()

    prometheus_ref = (
        prometheus_task.remote()
    )

    kubernetes_ref = (
        kubernetes_task.remote()
    )

    knowledge_ref = (
        knowledge_actor.retrieve.remote(
            KNOWLEDGE_QUERY,
            3,
        )
    )

    refs = [
        prometheus_ref,
        kubernetes_ref,
        knowledge_ref,
    ]

    print("\nObjectRefs:")

    for ref in refs:
        print(ref)

    results = ray.get(
        refs
    )

    duration = (
        time.perf_counter() - start
    )

    print("\nTask timings:")

    for result in results:
        print_result_summary(
            result
        )

    print(
        f"\nRay total: "
        f"{duration:.4f} seconds"
    )

    return results, duration


def validate_results(
    sequential_results: list[
        dict[str, Any]
    ],
    ray_results: list[
        dict[str, Any]
    ],
) -> None:
    """
    Confirm that sequential and Ray execution return equivalent
    diagnostic values.
    """

    sequential_by_source = {
        result["source"]: result
        for result in sequential_results
    }

    ray_by_source = {
        result["source"]: result
        for result in ray_results
    }

    sequential_target_count = (
        sequential_by_source[
            "prometheus"
        ]["result"].get(
            "total_target_count"
        )
    )

    ray_target_count = (
        ray_by_source[
            "prometheus"
        ]["result"].get(
            "total_target_count"
        )
    )

    sequential_unhealthy_count = (
        sequential_by_source[
            "kubernetes"
        ]["result"].get(
            "unhealthy_pod_count"
        )
    )

    ray_unhealthy_count = (
        ray_by_source[
            "kubernetes"
        ]["result"].get(
            "unhealthy_pod_count"
        )
    )

    sequential_document_count = (
        sequential_by_source[
            "qdrant"
        ]["result"].get(
            "result_count"
        )
    )

    ray_document_count = (
        ray_by_source[
            "qdrant"
        ]["result"].get(
            "result_count"
        )
    )

    sequential_document_texts = [
        document.get("text")
        for document in (
            sequential_by_source[
                "qdrant"
            ]["result"].get(
                "documents",
                [],
            )
        )
    ]

    ray_document_texts = [
        document.get("text")
        for document in (
            ray_by_source[
                "qdrant"
            ]["result"].get(
                "documents",
                [],
            )
        )
    ]

    print("\n")
    print("=" * 70)
    print("RESULT VALIDATION")
    print("=" * 70)

    print(
        "\nPrometheus total targets:"
    )
    print(
        "  Sequential:",
        sequential_target_count,
    )
    print(
        "  Ray:",
        ray_target_count,
    )

    print(
        "\nKubernetes unhealthy pods:"
    )
    print(
        "  Sequential:",
        sequential_unhealthy_count,
    )
    print(
        "  Ray:",
        ray_unhealthy_count,
    )

    print(
        "\nQdrant retrieved documents:"
    )
    print(
        "  Sequential:",
        sequential_document_count,
    )
    print(
        "  Ray:",
        ray_document_count,
    )

    assert (
        sequential_target_count
        == ray_target_count
    ), (
        "Prometheus target counts differ between "
        "sequential and Ray execution."
    )

    assert (
        sequential_unhealthy_count
        == ray_unhealthy_count
    ), (
        "Kubernetes unhealthy-pod counts differ between "
        "sequential and Ray execution."
    )

    assert (
        sequential_document_count
        == ray_document_count
    ), (
        "Qdrant result counts differ between "
        "sequential and Ray execution."
    )

    assert (
        sequential_document_texts
        == ray_document_texts
    ), (
        "Qdrant document ranking differs between "
        "sequential and Ray execution."
    )

    print(
        "\nRESULT VALIDATION: PASS"
    )


def main() -> None:
    """
    Compare sequential execution with an Actor-based Ray design.
    """

    ray.init()

    try:
        print("\n")
        print("=" * 70)
        print("RAY CLUSTER RESOURCES")
        print("=" * 70)

        print(
            ray.cluster_resources()
        )


        sequential_results, sequential_duration = (
            run_sequential_round()
        )


        print("\n")
        print("=" * 70)
        print("CREATING KNOWLEDGE ACTOR")
        print("=" * 70)

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
            f"Actor health: {actor_health}"
        )

        print(
            "Actor creation wall time: "
            f"{actor_creation_duration:.4f} seconds"
        )


        print("\n")
        print("=" * 70)
        print("WARMING KNOWLEDGE ACTOR")
        print("=" * 70)

        warmup_start = time.perf_counter()

        warmup_result = ray.get(
            knowledge_actor.retrieve.remote(
                KNOWLEDGE_QUERY,
                3,
            )
        )

        warmup_duration = (
            time.perf_counter()
            - warmup_start
        )

        print_result_summary(
            warmup_result
        )

        print(
            "Warm-up wall time: "
            f"{warmup_duration:.4f} seconds"
        )


        first_results, first_duration = (
            run_ray_round(
                knowledge_actor=(
                    knowledge_actor
                ),
                round_name=(
                    "RAY ACTOR ROUND 1"
                ),
            )
        )


        second_results, second_duration = (
            run_ray_round(
                knowledge_actor=(
                    knowledge_actor
                ),
                round_name=(
                    "RAY ACTOR ROUND 2"
                ),
            )
        )


        actor_state = ray.get(
            knowledge_actor.get_state.remote()
        )


        print("\n")
        print("=" * 70)
        print("KNOWLEDGE ACTOR STATE")
        print("=" * 70)

        print(actor_state)


        print("\n")
        print("=" * 70)
        print("COMPARISON")
        print("=" * 70)

        print(
            "Sequential:      "
            f"{sequential_duration:.4f}s"
        )

        print(
            "Actor creation:  "
            f"{actor_creation_duration:.4f}s"
        )

        print(
            "Actor warm-up:   "
            f"{warmup_duration:.4f}s"
        )

        print(
            "Ray round 1:     "
            f"{first_duration:.4f}s"
        )

        print(
            "Ray round 2:     "
            f"{second_duration:.4f}s"
        )

        if first_duration > 0:
            print(
                "Round 1 speedup: "
                f"{sequential_duration / first_duration:.2f}x"
            )

        if second_duration > 0:
            print(
                "Round 2 speedup: "
                f"{sequential_duration / second_duration:.2f}x"
            )


        validate_results(
            sequential_results=(
                sequential_results
            ),
            ray_results=second_results,
        )


        print("\n")
        print("=" * 70)
        print("INTERPRETATION")
        print("=" * 70)

        print(
            "Prometheus and Kubernetes execute as "
            "lightweight stateless Ray tasks."
        )

        print(
            "MiniLM and the Qdrant client remain resident "
            "inside the persistent KnowledgeActor."
        )

        print(
            "Actor initialization and warm-up are measured "
            "separately from steady-state request latency."
        )

        print(
            "The production-relevant comparison is sequential "
            "latency versus the warmed Ray rounds."
        )

    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
