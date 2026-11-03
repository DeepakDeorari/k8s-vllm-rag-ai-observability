from pprint import pprint

from workflows.llm_monitoring_graph import (
    llm_monitoring_graph,
)


test_questions = [
    (
        "DIRECT CPU QUESTION",
        (
            "What is the current CPU utilization "
            "of every Kubernetes node?"
        ),
        "cpu",
    ),
    (
        "PARAPHRASED CPU QUESTION",
        (
            "How busy are the processors on my cluster "
            "machines right now?"
        ),
        "cpu",
    ),
    (
        "DIRECT HEALTH QUESTION",
        (
            "How many Prometheus targets are "
            "currently UP?"
        ),
        "health",
    ),
    (
        "PARAPHRASED HEALTH QUESTION",
        (
            "Are all systems being monitored by "
            "Prometheus responding correctly?"
        ),
        "health",
    ),
    (
        "UNSUPPORTED POD QUESTION",
        "Which Kubernetes pods are restarting?",
        "unsupported",
    ),
    (
        "UNSUPPORTED MEMORY QUESTION",
        (
            "What is the memory utilization "
            "of every node?"
        ),
        "unsupported",
    ),
]


passed = 0


for (
    test_name,
    question,
    expected_route,
) in test_questions:
    print("\n")
    print("=" * 72)
    print(test_name)
    print("=" * 72)

    final_state = llm_monitoring_graph.invoke(
        {
            "question": question,
        }
    )

    actual_route = final_state.get("route")
    test_passed = (
        actual_route == expected_route
    )

    if test_passed:
        passed += 1

    print("\nQUESTION")
    print("--------")
    print(question)

    print("\nEXPECTED ROUTE")
    print("--------------")
    print(expected_route)

    print("\nACTUAL ROUTE")
    print("------------")
    print(actual_route)

    print("\nRAW CLASSIFICATION")
    print("------------------")
    print(
        repr(
            final_state.get(
                "classification_raw"
            )
        )
    )

    print("\nRESULT")
    print("------")
    print(
        "PASS"
        if test_passed
        else "FAIL"
    )

    print("\nFINAL ANSWER")
    print("------------")
    print(
        final_state.get(
            "final_answer"
        )
    )

    print("\nFINAL STATE")
    print("-----------")
    pprint(final_state)


print("\n")
print("=" * 72)
print("TEST SUMMARY")
print("=" * 72)
print(
    f"Passed {passed} of "
    f"{len(test_questions)} routing tests."
)


if passed != len(test_questions):
    raise SystemExit(1)
