from pprint import pprint

from workflows.sre_monitoring_graph import (
    sre_monitoring_graph,
)


test_questions = [
    (
        "CPU QUESTION",
        (
            "How busy are the processors on my "
            "Kubernetes cluster nodes?"
        ),
        "cpu",
        None,
    ),
    (
        "PROMETHEUS HEALTH QUESTION",
        (
            "Are all Prometheus monitoring targets "
            "responding correctly?"
        ),
        "health",
        None,
    ),
    (
        "POD RESTART QUESTION",
        "Which Kubernetes pods have restarted?",
        "kubernetes",
        "restarts",
    ),
    (
        "RESTART COUNT QUESTION",
        (
            "Show the workloads with the highest "
            "historical restart counts."
        ),
        "kubernetes",
        "restarts",
    ),
    (
        "UNHEALTHY POD QUESTION",
        "Are any Kubernetes pods unhealthy right now?",
        "kubernetes",
        "unhealthy",
    ),
    (
        "CRASH LOOP QUESTION",
        (
            "Are any workloads currently in "
            "CrashLoopBackOff?"
        ),
        "kubernetes",
        "unhealthy",
    ),
    (
        "UNSUPPORTED GPU QUESTION",
        "What is the current GPU temperature?",
        "unsupported",
        None,
    ),
]


passed = 0


for (
    test_name,
    question,
    expected_route,
    expected_kubernetes_intent,
) in test_questions:
    print("\n")
    print("=" * 76)
    print(test_name)
    print("=" * 76)

    final_state = sre_monitoring_graph.invoke(
        {
            "question": question,
        }
    )

    actual_route = final_state.get("route")

    actual_kubernetes_intent = final_state.get(
        "kubernetes_intent"
    )

    route_passed = (
        actual_route == expected_route
    )

    kubernetes_intent_passed = (
        expected_kubernetes_intent is None
        or actual_kubernetes_intent
        == expected_kubernetes_intent
    )

    test_passed = (
        route_passed
        and kubernetes_intent_passed
    )

    if test_passed:
        passed += 1

    print("\nQUESTION")
    print("--------")
    print(question)

    print("\nPRIMARY CLASSIFICATION")
    print("----------------------")
    print(
        repr(
            final_state.get(
                "classification_raw"
            )
        )
    )

    print("\nPRIMARY ROUTE")
    print("-------------")
    print(actual_route)

    print("\nKUBERNETES CLASSIFICATION")
    print("-------------------------")
    print(
        repr(
            final_state.get(
                "kubernetes_classification_raw"
            )
        )
    )

    print("\nKUBERNETES INTENT")
    print("-----------------")
    print(actual_kubernetes_intent)

    print("\nEXPECTED")
    print("--------")
    print(
        {
            "route": expected_route,
            "kubernetes_intent": (
                expected_kubernetes_intent
            ),
        }
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
print("=" * 76)
print("TEST SUMMARY")
print("=" * 76)

print(
    f"Passed {passed} of "
    f"{len(test_questions)} tests."
)


if passed != len(test_questions):
    raise SystemExit(1)
