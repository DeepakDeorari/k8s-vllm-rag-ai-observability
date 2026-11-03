from pprint import pprint

from tools.qdrant_retriever import (
    retrieve_documents,
)


questions = [
    (
        "A Kubernetes pod has accumulated many historical "
        "container restarts but is currently Running and Ready. "
        "How should this condition be investigated?"
    ),
    (
        "A Kubernetes workload is currently in CrashLoopBackOff. "
        "What should be investigated?"
    ),
    (
        "A Prometheus scrape target has up equal to zero. "
        "How should the target be investigated?"
    ),
]


for question in questions:
    print("\n")
    print("=" * 76)

    print("QUESTION")
    print("--------")
    print(question)

    result = retrieve_documents(
        question=question,
        limit=3,
    )

    print("\nRESULTS")
    print("-------")

    pprint(
        result["documents"]
    )
