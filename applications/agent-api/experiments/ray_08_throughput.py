import statistics
import time
from typing import Any

import ray

from experiments.ray_07_fair_benchmark import (
    KNOWLEDGE_QUERY,
    KnowledgeActor,
    kubernetes_task,
    prometheus_task,
    run_sequential_round,
    validate_equivalence,
)


INVESTIGATION_COUNT = 5


def run_sequential_batch() -> tuple[
    list[list[dict[str, Any]]],
    float,
]:
    """
    Execute complete investigation bundles one after another.
    """

    all_results = []

    start = time.perf_counter()

    for investigation_id in range(
        1,
        INVESTIGATION_COUNT + 1,
    ):
        results, duration = (
            run_sequential_round()
        )

        all_results.append(
            results
        )

        print(
            f"Sequential investigation "
            f"{investigation_id}/"
            f"{INVESTIGATION_COUNT}: "
            f"{duration:.4f}s"
        )

    total_duration = (
        time.perf_counter() - start
    )

    return all_results, total_duration


def submit_ray_investigation(
    knowledge_actor,
) -> list:
    """
    Submit one complete diagnostic bundle without blocking.

    Each bundle contains:
    - Prometheus target health
    - Kubernetes pod health
    - Qdrant knowledge retrieval
    """

    return [
        prometheus_task.remote(),
        kubernetes_task.remote(),
        knowledge_actor.retrieve.remote(
            KNOWLEDGE_QUERY,
            3,
        ),
    ]


def run_ray_batch(
    knowledge_actor,
) -> tuple[
    list[list[dict[str, Any]]],
    float,
]:
    """
    Submit all investigation bundles before waiting for results.

    This measures batch throughput rather than one-request latency.
    """

    submitted_investigations = []

    start = time.perf_counter()

    for investigation_id in range(
        1,
        INVESTIGATION_COUNT + 1,
    ):
        refs = submit_ray_investigation(
            knowledge_actor
        )

        submitted_investigations.append(
            refs
        )

        print(
            f"Submitted Ray investigation "
            f"{investigation_id}/"
            f"{INVESTIGATION_COUNT}"
        )

    all_refs = [
        ref
        for investigation_refs
        in submitted_investigations
        for ref in investigation_refs
    ]

    all_values = ray.get(
        all_refs
    )

    total_duration = (
        time.perf_counter() - start
    )

    results_by_investigation = []

    values_per_investigation = 3

    for index in range(
        INVESTIGATION_COUNT
    ):
        start_index = (
            index
            * values_per_investigation
        )

        end_index = (
            start_index
            + values_per_investigation
        )

        results_by_investigation.append(
            all_values[
                start_index:end_index
            ]
        )

    return (
        results_by_investigation,
        total_duration,
    )


def validate_batches(
    sequential_batch,
    ray_batch,
) -> None:
    """
    Validate every Ray result bundle against its corresponding
    sequential result bundle.
    """

    assert len(
        sequential_batch
    ) == len(
        ray_batch
    )

    for index, (
        sequential_results,
        ray_results,
    ) in enumerate(
        zip(
            sequential_batch,
            ray_batch,
        ),
        start=1,
    ):
        validate_equivalence(
            sequential_results=(
                sequential_results
            ),
            ray_results=ray_results,
        )

        print(
            f"Investigation {index}: "
            "result validation PASS"
        )


def summarize_batch(
    name: str,
    total_duration: float,
) -> None:
    """
    Print batch throughput statistics.
    """

    throughput = (
        INVESTIGATION_COUNT
        / total_duration
    )

    average_completion_cost = (
        total_duration
        / INVESTIGATION_COUNT
    )

    print(f"\n{name}")
    print("-" * len(name))

    print(
        f"Investigations: "
        f"{INVESTIGATION_COUNT}"
    )

    print(
        f"Total duration: "
        f"{total_duration:.4f}s"
    )

    print(
        "Average wall-clock cost per "
        "completed investigation: "
        f"{average_completion_cost:.4f}s"
    )

    print(
        "Throughput: "
        f"{throughput:.2f} "
        "investigations/second"
    )


def main() -> None:
    """
    Compare sequential and Ray batch throughput.
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
        print("WARMING SEQUENTIAL KNOWLEDGE PATH")
        print("=" * 72)

        warmup_results, warmup_duration = (
            run_sequential_round()
        )

        print(
            "Sequential warm-up duration: "
            f"{warmup_duration:.4f}s"
        )


        print("\n")
        print("=" * 72)
        print("CREATING AND WARMING KNOWLEDGE ACTOR")
        print("=" * 72)

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
            "Actor creation duration: "
            f"{actor_creation_duration:.4f}s"
        )

        print(
            f"Actor health: "
            f"{actor_health}"
        )

        actor_warmup_start = (
            time.perf_counter()
        )

        actor_warmup_result = ray.get(
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
            "Actor retrieval warm-up: "
            f"{actor_warmup_duration:.4f}s"
        )

        print(
            "Actor warm-up documents: "
            f"{actor_warmup_result['result'].get(
                'result_count'
            )}"
        )


        print("\n")
        print("=" * 72)
        print("WARMING STATELESS RAY WORKERS")
        print("=" * 72)

        worker_warmup_start = (
            time.perf_counter()
        )

        worker_warmup_results = ray.get(
            [
                prometheus_task.remote(),
                kubernetes_task.remote(),
            ]
        )

        worker_warmup_duration = (
            time.perf_counter()
            - worker_warmup_start
        )

        print(
            "Worker warm-up duration: "
            f"{worker_warmup_duration:.4f}s"
        )

        for result in worker_warmup_results:
            print(
                f"- {result['source']} "
                f"pid={result['pid']} "
                f"duration="
                f"{result['duration_seconds']:.4f}s"
            )


        print("\n")
        print("=" * 72)
        print("SEQUENTIAL THROUGHPUT TEST")
        print("=" * 72)

        (
            sequential_batch,
            sequential_duration,
        ) = run_sequential_batch()


        print("\n")
        print("=" * 72)
        print("RAY CONCURRENT THROUGHPUT TEST")
        print("=" * 72)

        (
            ray_batch,
            ray_duration,
        ) = run_ray_batch(
            knowledge_actor
        )


        print("\n")
        print("=" * 72)
        print("RESULT VALIDATION")
        print("=" * 72)

        validate_batches(
            sequential_batch=(
                sequential_batch
            ),
            ray_batch=ray_batch,
        )


        print("\n")
        print("=" * 72)
        print("THROUGHPUT SUMMARY")
        print("=" * 72)

        summarize_batch(
            "Sequential Batch",
            sequential_duration,
        )

        summarize_batch(
            "Ray Concurrent Batch",
            ray_duration,
        )


        throughput_speedup = (
            sequential_duration
            / ray_duration
        )

        sequential_throughput = (
            INVESTIGATION_COUNT
            / sequential_duration
        )

        ray_throughput = (
            INVESTIGATION_COUNT
            / ray_duration
        )

        throughput_improvement = (
            (
                ray_throughput
                / sequential_throughput
            )
            - 1
        ) * 100


        print("\nComparison")
        print("----------")

        print(
            "Batch completion speedup: "
            f"{throughput_speedup:.2f}x"
        )

        print(
            "Throughput improvement: "
            f"{throughput_improvement:.2f}%"
        )


        actor_state = ray.get(
            knowledge_actor.get_state.remote()
        )

        print("\nKnowledgeActor State")
        print("--------------------")

        print(actor_state)


        print("\n")
        print("=" * 72)
        print("INTERPRETATION")
        print("=" * 72)

        print(
            "The sequential batch completes one full "
            "investigation before starting the next."
        )

        print(
            "The Ray batch submits all independent "
            "diagnostic work before waiting for results."
        )

        print(
            "The KnowledgeActor processes retrieval calls "
            "using one persistent MiniLM/Qdrant worker."
        )

        print(
            "Every Ray investigation was validated against "
            "the corresponding sequential result."
        )

    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
