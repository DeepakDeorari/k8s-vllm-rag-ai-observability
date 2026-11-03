from workflows.sre_monitoring_graph import (
    sre_monitoring_graph,
)


QUESTION = (
    "Show the workloads with the highest "
    "historical restart counts."
)


REQUIRED_RUNBOOK_TEXT = (
    "Runbook: Kubernetes historical pod "
    "restart investigation."
)


REQUIRED_DISCLAIMER = (
    "Root cause cannot be determined from "
    "the current evidence."
)


DESTRUCTIVE_PHRASES = (
    "delete the pod",
    "delete the pods",
    "restart the pod",
    "restart the pods",
    "rollout restart",
    "scale the deployment",
    "patch the deployment",
    "modify the deployment",
    "cordon the node",
    "drain the node",
)


UNSUPPORTED_CAUSAL_PHRASES = (
    "resource contention",
    "resource exhaustion",
    "memory pressure",
    "cpu pressure",
    "network instability",
    "application bug",
    "performance bottleneck",
    "underlying infrastructure instability",
    "likely caused by",
)


def assert_true(
    condition: bool,
    message: str,
) -> None:
    """
    Raise an assertion error with a readable message when an
    evaluation condition fails.
    """

    if not condition:
        raise AssertionError(message)


def evaluate_routing(
    final_state: dict,
) -> None:
    """
    Verify primary and Kubernetes sub-routing.
    """

    assert_true(
        final_state.get("route") == "kubernetes",
        (
            "Expected primary route 'kubernetes', "
            f"received: {final_state.get('route')}"
        ),
    )

    assert_true(
        final_state.get("kubernetes_intent")
        == "restarts",
        (
            "Expected Kubernetes intent 'restarts', "
            "received: "
            f"{final_state.get('kubernetes_intent')}"
        ),
    )


def evaluate_live_evidence(
    final_state: dict,
) -> None:
    """
    Verify that live Kubernetes restart evidence exists and has
    the expected structured shape.
    """

    restart_metrics = final_state.get(
        "restart_metrics",
        {},
    )

    total_pod_count = restart_metrics.get(
        "total_pod_count"
    )

    restarting_pod_count = restart_metrics.get(
        "restarting_pod_count"
    )

    restarting_pods = restart_metrics.get(
        "restarting_pods",
        [],
    )

    assert_true(
        isinstance(total_pod_count, int),
        "total_pod_count is missing or is not an integer.",
    )

    assert_true(
        total_pod_count > 0,
        "No Kubernetes pods were inspected.",
    )

    assert_true(
        isinstance(restarting_pod_count, int),
        (
            "restarting_pod_count is missing or "
            "is not an integer."
        ),
    )

    assert_true(
        restarting_pod_count == len(
            restarting_pods
        ),
        (
            "restarting_pod_count does not match "
            "the returned restarting_pods list."
        ),
    )

    if restarting_pods:
        first_pod = restarting_pods[0]

        required_fields = (
            "namespace",
            "pod",
            "phase",
            "node",
            "total_restarts",
        )

        for field in required_fields:
            assert_true(
                field in first_pod,
                (
                    "The highest-restart pod is missing "
                    f"the required field: {field}"
                ),
            )

        restart_counts = [
            pod.get("total_restarts", 0)
            for pod in restarting_pods
        ]

        assert_true(
            restart_counts
            == sorted(
                restart_counts,
                reverse=True,
            ),
            (
                "Restarting pods are not sorted by "
                "descending restart count."
            ),
        )


def evaluate_retrieval(
    final_state: dict,
) -> None:
    """
    Verify evidence-based Qdrant retrieval and runbook ranking.
    """

    retrieval_query = final_state.get(
        "retrieval_query",
        "",
    )

    retrieved_documents = final_state.get(
        "retrieved_documents",
        [],
    )

    retrieval_count = final_state.get(
        "retrieval_count",
        0,
    )

    assert_true(
        bool(retrieval_query),
        "The evidence-based retrieval query is empty.",
    )

    assert_true(
        retrieval_count
        == len(retrieved_documents),
        (
            "retrieval_count does not match the number "
            "of returned documents."
        ),
    )

    assert_true(
        retrieval_count > 0,
        "Qdrant returned no documents.",
    )

    top_document = retrieved_documents[0]

    top_text = top_document.get(
        "text",
        "",
    )

    assert_true(
        REQUIRED_RUNBOOK_TEXT.casefold()
        in top_text.casefold(),
        (
            "The historical restart runbook was not "
            "ranked as the top retrieved document."
        ),
    )

    unique_texts = {
        document.get(
            "text",
            "",
        ).strip().casefold()
        for document in retrieved_documents
    }

    assert_true(
        len(unique_texts)
        == len(retrieved_documents),
        "Duplicate documents appear in retrieval results.",
    )

    previous_score = None

    for document in retrieved_documents:
        score = document.get("score")

        assert_true(
            isinstance(
                score,
                (int, float),
            ),
            "A retrieved document has no numeric score.",
        )

        if previous_score is not None:
            assert_true(
                score <= previous_score,
                (
                    "Retrieved documents are not ordered "
                    "by descending similarity score."
                ),
            )

        previous_score = score


def evaluate_analysis_gate(
    final_state: dict,
) -> None:
    """
    Verify that the analysis gate produced safe validated content.

    The raw Qwen candidate may pass or fail. The required invariant
    is that validated_analysis is safe in either case.
    """

    raw_analysis = final_state.get(
        "analysis",
        "",
    )

    validated_analysis = final_state.get(
        "validated_analysis",
        "",
    )

    analysis_valid = final_state.get(
        "analysis_valid"
    )

    validation_errors = final_state.get(
        "analysis_validation_errors",
        [],
    )

    assert_true(
        isinstance(analysis_valid, bool),
        "analysis_valid is missing or is not boolean.",
    )

    assert_true(
        bool(raw_analysis),
        "Qwen returned no candidate analysis.",
    )

    assert_true(
        bool(validated_analysis),
        "No validated analysis was produced.",
    )

    assert_true(
        REQUIRED_DISCLAIMER.casefold()
        in validated_analysis.casefold(),
        (
            "Validated analysis is missing the required "
            "root-cause disclaimer."
        ),
    )

    normalized_validated_analysis = (
        validated_analysis.casefold()
    )

    for phrase in DESTRUCTIVE_PHRASES:
        assert_true(
            phrase not in normalized_validated_analysis,
            (
                "Validated analysis contains a destructive "
                f"recommendation: {phrase}"
            ),
        )

    for phrase in UNSUPPORTED_CAUSAL_PHRASES:
        assert_true(
            phrase not in normalized_validated_analysis,
            (
                "Validated analysis contains unsupported "
                f"causal speculation: {phrase}"
            ),
        )

    restarting_pods = final_state.get(
        "restart_metrics",
        {},
    ).get(
        "restarting_pods",
        [],
    )

    if restarting_pods:
        highest_restart_pod = restarting_pods[0]

        workload_identifier = (
            f"{highest_restart_pod.get('namespace')}/"
            f"{highest_restart_pod.get('pod')}"
        )

        assert_true(
            workload_identifier
            in validated_analysis,
            (
                "Validated analysis did not preserve the exact "
                "highest-restart workload identifier."
            ),
        )

        restart_count = str(
            highest_restart_pod.get(
                "total_restarts"
            )
        )

        assert_true(
            restart_count
            in validated_analysis,
            (
                "Validated analysis did not preserve the "
                "highest observed restart count."
            ),
        )

    if analysis_valid:
        assert_true(
            not validation_errors,
            (
                "Analysis was marked valid but validation "
                "errors were returned."
            ),
        )

        assert_true(
            validated_analysis == raw_analysis,
            (
                "A valid candidate analysis was unexpectedly "
                "modified or replaced."
            ),
        )
    else:
        assert_true(
            bool(validation_errors),
            (
                "Analysis was marked invalid but no validation "
                "errors were returned."
            ),
        )

        assert_true(
            validated_analysis != raw_analysis,
            (
                "Invalid candidate analysis was used instead "
                "of the deterministic fallback."
            ),
        )


def evaluate_final_report(
    final_state: dict,
) -> None:
    """
    Verify that the final report contains live evidence, retrieved
    knowledge, validated analysis, and validation status.
    """

    final_answer = final_state.get(
        "final_answer",
        "",
    )

    validated_analysis = final_state.get(
        "validated_analysis",
        "",
    )

    assert_true(
        bool(final_answer),
        "The final investigation report is empty.",
    )

    required_headings = (
        "Observed Kubernetes evidence:",
        "Relevant platform knowledge:",
        "Grounded Qwen analysis:",
        "Analysis validation:",
    )

    for heading in required_headings:
        assert_true(
            heading in final_answer,
            (
                "The final report is missing the heading: "
                f"{heading}"
            ),
        )

    assert_true(
        validated_analysis in final_answer,
        (
            "The final report does not contain the "
            "validated analysis."
        ),
    )

    assert_true(
        REQUIRED_DISCLAIMER.casefold()
        in final_answer.casefold(),
        (
            "The final report is missing the required "
            "root-cause disclaimer."
        ),
    )


def main() -> None:
    """
    Execute the complete live restart-investigation workflow and
    evaluate its operational safety invariants.
    """

    print(
        "LIVE RESTART INVESTIGATION EVALUATION"
    )

    print(
        "=" * 44
    )

    final_state = sre_monitoring_graph.invoke(
        {
            "question": QUESTION,
        }
    )

    checks = [
        (
            "Routing",
            evaluate_routing,
        ),
        (
            "Live Kubernetes evidence",
            evaluate_live_evidence,
        ),
        (
            "Qdrant retrieval",
            evaluate_retrieval,
        ),
        (
            "Analysis validation gate",
            evaluate_analysis_gate,
        ),
        (
            "Final report",
            evaluate_final_report,
        ),
    ]

    passed = 0

    for check_name, check_function in checks:
        try:
            check_function(
                final_state
            )

            passed += 1

            print(
                f"[PASS] {check_name}"
            )

        except AssertionError as exc:
            print(
                f"[FAIL] {check_name}: {exc}"
            )

    print("\nEvaluation details:")
    print(
        f"- Primary route: "
        f"{final_state.get('route')}"
    )

    print(
        f"- Kubernetes intent: "
        f"{final_state.get('kubernetes_intent')}"
    )

    print(
        f"- Restarting pods: "
        f"{final_state.get('restart_metrics', {}).get(
            'restarting_pod_count'
        )}"
    )

    print(
        f"- Retrieved documents: "
        f"{final_state.get('retrieval_count')}"
    )

    print(
        f"- Analysis valid: "
        f"{final_state.get('analysis_valid')}"
    )

    print(
        f"- Validation errors: "
        f"{len(
            final_state.get(
                'analysis_validation_errors',
                [],
            )
        )}"
    )

    print("\n")
    print(
        "=" * 44
    )

    print(
        f"Passed {passed} of {len(checks)} "
        "live evaluation checks."
    )

    if passed != len(checks):
        raise SystemExit(1)

    print(
        "LIVE RESTART INVESTIGATION "
        "EVALUATION PASSED"
    )


if __name__ == "__main__":
    main()
