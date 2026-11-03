import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import ray

from experiments.ray_07_fair_benchmark import (
    KNOWLEDGE_QUERY,
    KnowledgeActor,
    kubernetes_task,
    prometheus_task,
    run_sequential_round,
    sequential_kubernetes,
    sequential_prometheus,
    sequential_qdrant,
    validate_equivalence,
)


INVESTIGATION_COUNT = 5
THREAD_WORKERS = 4


def run_threaded_investigation() -> tuple[
    list[dict[str, Any]],
    float,
]:
    """
    Run one investigation using native Python threads.

    The same diagnostic operations used by the sequential and
    Ray paths are submitted to a ThreadPoolExecutor.
    """

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:
        prometheus_future = executor.submit(
            sequential_prometheus
        )

        kubernetes_future = executor.submit(
            sequential_kubernetes
        )

        qdrant_future = executor.submit(
            sequential_qdrant
        )

        results = [
            prometheus_future.result(),
            kubernetes_future.result(),
            qdrant_future.result(),
        ]

    duration = (
        time.perf_counter() - start
    )

    return results, duration


def run_sequential_batch() -> tuple[
    list[list[dict[str, Any]]],
    float,
]:
    """
    Run investigations one after another.
    """

    results = []

    start = time.perf_counter()

    for _ in range(
        INVESTIGATION_COUNT
    ):
        investigation_results, _ = (
            run_sequential_round()
        )

        results.append(
            investigation_results
        )

    duration = (
        time.perf_counter() - start
    )

    return results, duration


def run_threaded_batch() -> tuple[
    list[list[dict[str, Any]]],
    float,
]:
    """
    Run complete investigations concurrently using native threads.
    """

    start = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=THREAD_WORKERS
    ) as executor:
        futures = [
            executor.submit(
                run_threaded_investigation
            )
            for _ in range(
                INVESTIGATION_COUNT
            )
        ]

        results = [
            future.result()[0]
            for future in futures
        ]

    duration = (
        time.perf_counter() - start
    )

    return results, duration


def submit_ray_investigation(
    knowledge_actor,
) -> list:
    """
    Submit one Ray-based diagnostic bundle.
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
    Submit every Ray investigation before waiting.
    """

    start = time.perf_counter()

    bundles = [
        submit_ray_investigation(
            knowledge_actor
        )
        for _ in range(
            INVESTIGATION_COUNT
        )
    ]

    flat_refs = [
        ref
        for bundle in bundles
        for ref in bundle
    ]

    flat_results = ray.get(
        flat_refs
    )

    results = []

    for index in range(
        INVESTIGATION_COUNT
    ):
        offset = index * 3

        results.append(
            flat_results[
                offset:offset + 3
            ]
        )

    duration = (
        time.perf_counter() - start
    )

    return results, duration


def validate_batch(
    baseline,
    candidate,
    name: str,
) -> None:
    """
    Validate each candidate investigation against sequential output.
    """

    for index, (
        sequential_results,
        candidate_results,
    ) in enumerate(
        zip(
            baseline,
            candidate,
        ),
        start=1,
    ):
        validate_equivalence(
            sequential_results,
            candidate_results,
        )

        print(
            f"{name} investigation {index}: PASS"
        )


def summarize(
    name: str,
    duration: float,
) -> None:
    """
    Print throughput for one execution model.
    """

    throughput = (
        INVESTIGATION_COUNT
        / duration
    )

    print(f"\n{name}")
    print("-" * len(name))

    print(
        f"Total:      {duration:.4f}s"
    )

    print(
        "Per result: "
        f"{duration / INVESTIGATION_COUNT:.4f}s"
    )

    print(
        "Throughput: "
        f"{throughput:.2f} investigations/s"
    )


def main() -> None:
    ray.init()

    try:
        print("\nWARM-UP")
        print("=======")

        run_sequential_round()

        knowledge_actor = (
            KnowledgeActor.remote()
        )

        ray.get(
            knowledge_actor.health.remote()
        )

        ray.get(
            knowledge_actor.retrieve.remote(
                KNOWLEDGE_QUERY,
                3,
            )
        )

        ray.get(
            [
                prometheus_task.remote(),
                kubernetes_task.remote(),
            ]
        )

        run_threaded_investigation()

        print("Warm-up complete.")


        print("\nRUNNING BENCHMARK")
        print("=================")

        sequential_results, sequential_duration = (
            run_sequential_batch()
        )

        threaded_results, threaded_duration = (
            run_threaded_batch()
        )

        ray_results, ray_duration = (
            run_ray_batch(
                knowledge_actor
            )
        )


        print("\nVALIDATION")
        print("==========")

        validate_batch(
            sequential_results,
            threaded_results,
            "Threaded",
        )

        validate_batch(
            sequential_results,
            ray_results,
            "Ray",
        )


        print("\nSUMMARY")
        print("=======")

        summarize(
            "Sequential Python",
            sequential_duration,
        )

        summarize(
            "ThreadPoolExecutor",
            threaded_duration,
        )

        summarize(
            "Ray + KnowledgeActor",
            ray_duration,
        )


        print("\nCOMPARISON")
        print("==========")

        print(
            "Threads vs sequential: "
            f"{sequential_duration / threaded_duration:.2f}x"
        )

        print(
            "Ray vs sequential:     "
            f"{sequential_duration / ray_duration:.2f}x"
        )

        print(
            "Threads vs Ray:        "
            f"{ray_duration / threaded_duration:.2f}x"
        )

    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
