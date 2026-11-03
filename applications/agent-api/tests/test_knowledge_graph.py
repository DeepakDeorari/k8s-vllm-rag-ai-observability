from pprint import pprint

from workflows.knowledge_graph import (
    knowledge_graph,
)


questions = [
    "What is the worker node hostname?",
    "Which model is deployed on Node 1?",
    "What Kubernetes distribution is being used?",
]


for question in questions:
    print("\n")
    print("=" * 72)

    final_state = knowledge_graph.invoke(
        {
            "question": question,
        }
    )

    print("QUESTION")
    print("--------")
    print(question)

    print("\nRETRIEVAL COUNT")
    print("---------------")
    print(
        final_state.get(
            "retrieval_count"
        )
    )

    print("\nFINAL ANSWER")
    print("------------")
    print(
        final_state.get(
            "final_answer"
        )
    )

    print("\nRETRIEVED DOCUMENTS")
    print("-------------------")
    pprint(
        final_state.get(
            "retrieved_documents"
        )
    )
