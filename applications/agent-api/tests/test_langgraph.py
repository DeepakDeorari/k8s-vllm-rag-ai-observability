from typing import TypedDict

from langgraph.graph import StateGraph
from langgraph.graph import START
from langgraph.graph import END


class GraphState(TypedDict):
    question: str
    classification: str


def classify_node(state):
    question = state["question"]

    return {
        "classification": f"Question received: {question}"
    }


def answer_node(state):
    print("\nClassification:")
    print(state["classification"])

    return {}


graph = StateGraph(GraphState)

graph.add_node(
    "classify",
    classify_node
)

graph.add_node(
    "answer",
    answer_node
)

graph.add_edge(
    START,
    "classify"
)

graph.add_edge(
    "classify",
    "answer"
)

graph.add_edge(
    "answer",
    END
)

app = graph.compile()

app.invoke(
    {
        "question": "What is Kubernetes?"
    }
)
