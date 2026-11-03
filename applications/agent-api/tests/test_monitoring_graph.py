from pprint import pprint

from workflows.monitoring_graph import monitoring_graph


test_questions = [
    (
        "CPU TEST",
        "What is the current CPU utilization "
        "of every Kubernetes node?",
    ),
    (
        "HEALTH TEST",
        "How many Prometheus targets are "
        "currently UP?",
    ),
    (
        "UNSUPPORTED TEST",
        "Which Kubernetes pods are restarting?",
    ),
]


for test_name, question in test_questions:
    print("\n")
    print("=" * 70)
    print(test_name)
    print("=" * 70)

    final_state = monitoring_graph.invoke(
        {
            "question": question,
        }
    )

    print("\nQUESTION")
    print("--------")
    print(question)

    print("\nSELECTED ROUTE")
    print("--------------")
    print(final_state.get("route"))

    print("\nFINAL ANSWER")
    print("------------")
    print(final_state.get("final_answer"))

    print("\nFINAL STATE")
    print("-----------")
    pprint(final_state)
