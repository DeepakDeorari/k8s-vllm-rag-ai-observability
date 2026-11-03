from pprint import pprint

from tools.qdrant_retriever import (
    retrieve_documents,
)


questions = [
    "What is the worker node hostname?",
    "Which model is deployed on Node 1?",
    "What Kubernetes distribution is being used?",
]


for question in questions:
    print("\n")
    print("=" * 70)

    print("QUESTION")
    print(question)

    print("=" * 70)

    result = retrieve_documents(
        question=question,
        limit=3,
    )

    pprint(result)
