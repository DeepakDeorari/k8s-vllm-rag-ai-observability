from pprint import pprint

from workflows.sre_monitoring_graph import (
    validate_restart_analysis_node,
)


RESTART_METRICS = {
    "total_pod_count": 41,
    "restarting_pod_count": 38,
    "restarting_pods": [
        {
            "namespace": "observability",
            "pod": (
                "kube-prometheus-stack-grafana-"
                "b586c464f-864gs"
            ),
            "phase": "Running",
            "node": "ip-172-31-7-23",
            "total_restarts": 42,
        },
        {
            "namespace": "gpu-operator-resources",
            "pod": (
                "nvidia-container-toolkit-"
                "daemonset-wwq85"
            ),
            "phase": "Running",
            "node": "ip-172-31-7-23",
            "total_restarts": 30,
        },
        {
            "namespace": "observability",
            "pod": (
                "prometheus-kube-prometheus-stack-"
                "prometheus-0"
            ),
            "phase": "Running",
            "node": "ip-172-31-7-23",
            "total_restarts": 29,
        },
    ],
}


UNSAFE_ANALYSIS = """
Assessment:
- Observability/KubePrometheusStackGrafana restarted 42 times.
- GPUOperatorResources/NVIDIAContainerToolkit restarted 30 times.
- The workloads are currently running.

Evidence interpretation:
- The restart counts may indicate resource contention,
  misconfiguration, or underlying infrastructure instability.

Recommended verification:
- Check pod status and logs.
- Check current resource utilization.

Conclusion:
- Further investigation is required.
""".strip()


SAFE_ANALYSIS = """
Assessment:
- observability/kube-prometheus-stack-grafana-b586c464f-864gs
  has recorded 42 historical restarts.
- gpu-operator-resources/nvidia-container-toolkit-daemonset-wwq85
  has recorded 30 historical restarts.
- observability/prometheus-kube-prometheus-stack-prometheus-0
  has recorded 29 historical restarts.

Evidence interpretation:
- The displayed workloads are currently in the Running phase.
- Historical restart counts confirm previous container restarts.
- Historical restart counts alone do not prove a current incident.

Recommended verification:
- Check current container readiness.
- Check current container waiting reasons.
- Inspect the last terminated reason and exit code.
- Review recent Kubernetes warning events.
- Check whether restart counts continue to increase.

Conclusion:
- An active workload failure is not established by the evidence.
- Root cause cannot be determined from the current evidence.
""".strip()


def run_unsafe_analysis_test():
    """
    Confirm that unsupported and altered Qwen content is rejected.
    """

    state = {
        "restart_metrics": RESTART_METRICS,
        "analysis": UNSAFE_ANALYSIS,
        "analysis_error": "",
    }

    result = validate_restart_analysis_node(
        state
    )

    assert result["analysis_valid"] is False, (
        "Unsafe candidate analysis was incorrectly accepted."
    )

    assert result["analysis_validation_errors"], (
        "Unsafe candidate produced no validation errors."
    )

    assert (
        result["validated_analysis"]
        != UNSAFE_ANALYSIS
    ), (
        "Unsafe candidate was used instead of the fallback."
    )

    assert (
        "Root cause cannot be determined from "
        "the current evidence."
        in result["validated_analysis"]
    ), (
        "Safe fallback is missing the root-cause disclaimer."
    )

    assert (
        "observability/"
        "kube-prometheus-stack-grafana-"
        "b586c464f-864gs"
        in result["validated_analysis"]
    ), (
        "Safe fallback did not preserve the exact "
        "highest-restart workload identifier."
    )

    print("UNSAFE ANALYSIS TEST: PASS")

    print("\nValidation errors:")

    pprint(
        result["analysis_validation_errors"]
    )


def run_safe_analysis_test():
    """
    Confirm that grounded candidate content is accepted unchanged.
    """

    state = {
        "restart_metrics": RESTART_METRICS,
        "analysis": SAFE_ANALYSIS,
        "analysis_error": "",
    }

    result = validate_restart_analysis_node(
        state
    )

    assert result["analysis_valid"] is True, (
        "Safe candidate analysis was incorrectly rejected. "
        f"Errors: "
        f"{result['analysis_validation_errors']}"
    )

    assert not result[
        "analysis_validation_errors"
    ], (
        "Safe candidate produced validation errors."
    )

    assert (
        result["validated_analysis"]
        == SAFE_ANALYSIS
    ), (
        "Safe candidate was modified or replaced."
    )

    print("\nSAFE ANALYSIS TEST: PASS")


def main():
    print(
        "RESTART ANALYSIS VALIDATION EVALUATION"
    )

    print(
        "=" * 40
    )

    run_unsafe_analysis_test()

    run_safe_analysis_test()

    print("\n")
    print(
        "=" * 40
    )

    print(
        "ALL RESTART ANALYSIS VALIDATION TESTS PASSED"
    )


if __name__ == "__main__":
    main()
