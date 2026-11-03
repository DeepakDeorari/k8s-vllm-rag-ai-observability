from typing import TypedDict

from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from tools.qdrant_retriever import (
    retrieve_documents,
)


class KnowledgeGraphState(
    TypedDict,
    total=False,
):
    """
    Shared state for the knowledge-retrieval workflow.
    """

    question: str
    retrieved_documents: list
    retrieval_count: int
    final_answer: str
    error: str


def retrieve_knowledge_node(
    state: KnowledgeGraphState,
) -> dict:
    """
    Retrieve relevant unique documents from the existing
    Phase 2 Qdrant collection.
    """

    question = state.get(
        "question",
        "",
    ).strip()

    if not question:
        return {
            "retrieved_documents": [],
            "retrieval_count": 0,
            "error": (
                "Cannot retrieve knowledge because "
                "the question is empty."
            ),
        }

    try:
        result = retrieve_documents(
            question=question,
            limit=3,
        )

        return {
            "retrieved_documents": (
                result.get(
                    "documents",
                    [],
                )
            ),
            "retrieval_count": (
                result.get(
                    "result_count",
                    0,
                )
            ),
        }

    except Exception as exc:
        return {
            "retrieved_documents": [],
            "retrieval_count": 0,
            "error": (
                "Qdrant retrieval failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }


def format_knowledge_node(
    state: KnowledgeGraphState,
) -> dict:
    """
    Format retrieved evidence deterministically.

    Qwen is intentionally not used yet.
    """

    if state.get("error"):
        return {
            "final_answer": state["error"],
        }

    documents = state.get(
        "retrieved_documents",
        [],
    )

    if not documents:
        return {
            "final_answer": (
                "No relevant platform knowledge "
                "was retrieved."
            )
        }

    lines = [
        "Relevant platform knowledge:"
    ]

    for index, document in enumerate(
        documents,
        start=1,
    ):
        score = document.get("score")
        text = document.get("text")

        lines.append(
            f"{index}. "
            f"[similarity={score}] "
            f"{text}"
        )

    return {
        "final_answer": "\n".join(lines),
    }


def build_knowledge_graph():
    """
    Build the standalone Qdrant retrieval workflow.
    """

    graph = StateGraph(
        KnowledgeGraphState
    )

    graph.add_node(
        "retrieve_knowledge",
        retrieve_knowledge_node,
    )

    graph.add_node(
        "format_knowledge",
        format_knowledge_node,
    )

    graph.add_edge(
        START,
        "retrieve_knowledge",
    )

    graph.add_edge(
        "retrieve_knowledge",
        "format_knowledge",
    )

    graph.add_edge(
        "format_knowledge",
        END,
    )

    return graph.compile()


knowledge_graph = build_knowledge_graph()
