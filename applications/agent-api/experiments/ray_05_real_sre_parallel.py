import time

import ray

from tools.kubernetes_pods import (
    get_unhealthy_pods,
)
from tools.prometheus_health import (
    get_prometheus_target_health,
)
from tools.qdrant_retriever import (
    retrieve_documents,
)


KNOWLEDGE_QUERY = (
    "How should Kubernetes workload health "
    "problems be investigated?"
)


def run_prometheus():
    """
    Retrieve the current Prometheus target-health evidence.
    """

    start = time.perf_counter()

    result = get_prometheus_target_health()

    return {
        "source": "prometheus",
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


def run_kubernetes():
    """
    Retrieve the current unhealthy Kubernetes pod evidence.
    """

    start = time.perf_counter()

    result = get_unhealthy_pods()

    return {
        "source": "kubernetes",
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


def run_qdrant():
    """
    Retrieve relevant platform knowledge from Qdrant.
    """

    start = time.perf_counter()

    result = retrieve_documents(
        question=KNOWLEDGE_QUERY,
        limit=3,
    )

    return {
        "source": "qdrant",
        "duration_seconds": round(
            time.perf_counter() - start,
            4,
        ),
        "result": result,
    }


@ray.remote(num_cpus=1)
def ray_prometheus():
    """
    Execute the Prometheus diagnostic as a Ray task.
    """

    return run_prometheus()


@ray.remote(num_cpus=1)
def ray_kubernetes():
    """
    Execute the Kubernetes diagnostic as a Ray task.
    """

    return run_kubernetes()


@ray.remote(num_cpus=1)
def ray_qdrant():
    """
    Execute the Qdrant retrieval as a Ray task.
    """

    return run_qdrant()


def print_result_summary(result):
    """
    Print the internal execution time reported by one diagnostic.
    """

    source = result["source"]

    duration = result[
        "duration_seconds"
    ]

    print(
        f"{source:12} "
        f"{duration:.4f} seconds"
    )


def run_ray_round(round_name):
    """
    Submit all independent diagnostics before waiting for results.

    The first invocation measures cold Ray worker behavior.
    The second invocation measures warm worker behavior within
    the same Ray runtime.
    """

    print("\n")
    print("=" * 60)
    print(round_name)
    print("=" * 60)

    start = time.perf_counter()

    refs = [
        ray_prometheus.remote(),
        ray_kubernetes.remote(),
        ray_qdrant.remote(),
    ]

    print("\nObjectRefs:")

    for ref in refs:
        print(ref)

    results = ray.get(
        refs
    )

    duration = (
        time.perf_counter()
        - start
    )

    print("\nTask timings:")

    for result in results:
        print_result_summary(
            result
        )

    print(
        f"\nTotal: {duration:.4f} seconds"
    )

    return results, duration


def validate_results(
    sequential_results,
    ray_results,
):
    """
    Confirm that Ray execution returned the same operational values
    as sequential execution.

    Faster execution is not useful if diagnostic results differ.
    """

    sequential_by_source = {
        item["source"]: item
        for item in sequential_results
    }

    ray_by_source = {
        item["source"]: item
        for item in ray_results
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

    print("\n")
    print("=" * 60)
    print("RESULT VALIDATION")
    print("=" * 60)

    print(
        "\nPrometheus total targets:"
    )

    print(
        "  Sequential:",
        sequential_target_count,
    )

    print(
        "  Ray warm:",
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
        "  Ray warm:",
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
        "  Ray warm:",
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

    print(
        "\nRESULT VALIDATION: PASS"
    )


def main():
    """
    Compare sequential diagnostics with cold and warm Ray execution.
    """

    ray.init()

    try:
        print("\n")
        print("=" * 60)
        print("RAY CLUSTER RESOURCES")
        print("=" * 60)

        print(
            ray.cluster_resources()
        )


        print("\n")
        print("=" * 60)
        print("SEQUENTIAL REAL SRE DIAGNOSTICS")
        print("=" * 60)

        sequential_start = (
            time.perf_counter()
        )

        sequential_results = [
            run_prometheus(),
            run_kubernetes(),
            run_qdrant(),
        ]

        sequential_duration = (
            time.perf_counter()
            - sequential_start
        )

        for result in sequential_results:
            print_result_summary(
                result
            )

        print(
            "\nSequential total: "
            f"{sequential_duration:.4f} seconds"
        )


        cold_results, cold_duration = (
            run_ray_round(
                "RAY COLD EXECUTION"
            )
        )


        warm_results, warm_duration = (
            run_ray_round(
                "RAY WARM EXECUTION"
            )
        )


        print("\n")
        print("=" * 60)
        print("COMPARISON")
        print("=" * 60)

        print(
            "Sequential: "
            f"{sequential_duration:.4f}s"
        )

        print(
            "Ray cold:   "
            f"{cold_duration:.4f}s"
        )

        print(
            "Ray warm:   "
            f"{warm_duration:.4f}s"
        )

        if cold_duration > 0:
            print(
                "Cold speedup: "
                f"{sequential_duration / cold_duration:.2f}x"
            )

        if warm_duration > 0:
            print(
                "Warm speedup: "
                f"{sequential_duration / warm_duration:.2f}x"
            )

        print(
            "\nCold overhead: "
            f"{cold_duration - sequential_duration:.4f}s"
        )

        print(
            "Warm difference: "
            f"{warm_duration - sequential_duration:.4f}s"
        )


        validate_results(
            sequential_results=(
                sequential_results
            ),
            ray_results=warm_results,
        )


        print("\n")
        print("=" * 60)
        print("INTERPRETATION")
        print("=" * 60)

        print(
            "Cold execution includes Ray worker startup, "
            "module import, and model initialization costs."
        )

        print(
            "Warm execution reuses the existing Ray runtime "
            "and available worker processes."
        )

        print(
            "The comparison is valid only when sequential "
            "and Ray diagnostic values match."
        )

    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
