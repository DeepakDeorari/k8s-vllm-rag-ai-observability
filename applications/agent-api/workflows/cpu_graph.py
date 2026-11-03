from typing import TypedDict

from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from tools.prometheus_cpu import get_current_node_cpu_percent


class CpuGraphState(TypedDict, total=False):
    """
    Shared state passed between LangGraph nodes.
    """

    question: str
    cpu_metrics: dict
    final_answer: str


def collect_cpu_metrics_node(
    state: CpuGraphState,
) -> dict:
    """
    Query Prometheus and store structured CPU metrics in graph state.
    """

    cpu_metrics = get_current_node_cpu_percent()

    return {
        "cpu_metrics": cpu_metrics,
    }


def format_response_node(
    state: CpuGraphState,
) -> dict:
    """
    Create a deterministic response from structured CPU metrics.

    No LLM is involved in this node, so instance names and metric
    values cannot be renamed or rewritten.
    """

    cpu_metrics = state.get("cpu_metrics", {})
    nodes = cpu_metrics.get("nodes", [])

    if not nodes:
        return {
            "final_answer": (
                "No Kubernetes node CPU metrics were returned "
                "by Prometheus."
            )
        }

    lines = [
        "Current Kubernetes node CPU utilization:"
    ]

    for node in nodes:
        instance = node.get("instance")
        cpu_percent = node.get("cpu_utilization_percent")

        if cpu_percent is None:
            lines.append(
                f"- {instance}: CPU utilization unavailable"
            )
        else:
            lines.append(
                f"- {instance}: {cpu_percent}%"
            )

    return {
        "final_answer": "\n".join(lines),
    }


def build_cpu_graph():
    """
    Build and compile the deterministic CPU metrics workflow.
    """

    graph = StateGraph(CpuGraphState)

    graph.add_node(
        "collect_cpu_metrics",
        collect_cpu_metrics_node,
    )

    graph.add_node(
        "format_response",
        format_response_node,
    )

    graph.add_edge(
        START,
        "collect_cpu_metrics",
    )

    graph.add_edge(
        "collect_cpu_metrics",
        "format_response",
    )

    graph.add_edge(
        "format_response",
        END,
    )

    return graph.compile()


cpu_graph = build_cpu_graph()
