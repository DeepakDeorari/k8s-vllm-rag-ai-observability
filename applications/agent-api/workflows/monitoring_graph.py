from typing import Literal
from typing import TypedDict

from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from tools.prometheus_cpu import get_current_node_cpu_percent
from tools.prometheus_health import get_prometheus_target_health


class MonitoringGraphState(TypedDict, total=False):
    """
    Shared state for the monitoring workflow.

    Each node reads existing fields and returns only the fields that
    the node wants to add or update.
    """

    question: str
    route: str
    cpu_metrics: dict
    health_metrics: dict
    final_answer: str
    error: str


def classify_question_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Classify the question using deterministic keyword rules.

    This first router intentionally does not use an LLM. It makes
    routing predictable and easy to validate.
    """

    question = state.get("question", "").lower()

    cpu_keywords = (
        "cpu",
        "processor",
        "compute utilization",
        "node utilization",
    )

    health_keywords = (
        "up",
        "down",
        "target",
        "targets",
        "health",
        "healthy",
        "scrape",
        "monitoring status",
    )

    if any(
        keyword in question
        for keyword in cpu_keywords
    ):
        return {
            "route": "cpu",
        }

    if any(
        keyword in question
        for keyword in health_keywords
    ):
        return {
            "route": "health",
        }

    return {
        "route": "unsupported",
    }


def route_question(
    state: MonitoringGraphState,
) -> Literal[
    "collect_cpu_metrics",
    "collect_health_metrics",
    "unsupported_question",
]:
    """
    Select the next graph node using the route stored in state.
    """

    route = state.get("route")

    if route == "cpu":
        return "collect_cpu_metrics"

    if route == "health":
        return "collect_health_metrics"

    return "unsupported_question"


def collect_cpu_metrics_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Collect current CPU utilization from Prometheus.
    """

    try:
        cpu_metrics = get_current_node_cpu_percent()

        return {
            "cpu_metrics": cpu_metrics,
        }

    except Exception as exc:
        return {
            "error": (
                "CPU metric collection failed: "
                f"{type(exc).__name__}: {exc}"
            )
        }


def collect_health_metrics_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Collect current Prometheus target-health information.
    """

    try:
        health_metrics = get_prometheus_target_health()

        return {
            "health_metrics": health_metrics,
        }

    except Exception as exc:
        return {
            "error": (
                "Prometheus target-health collection failed: "
                f"{type(exc).__name__}: {exc}"
            )
        }


def format_cpu_response_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Format CPU results deterministically.
    """

    if state.get("error"):
        return {
            "final_answer": state["error"],
        }

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
        cpu_percent = node.get(
            "cpu_utilization_percent"
        )

        if cpu_percent is None:
            lines.append(
                f"- {instance}: unavailable"
            )
        else:
            lines.append(
                f"- {instance}: {cpu_percent}%"
            )

    return {
        "final_answer": "\n".join(lines),
    }


def format_health_response_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Format Prometheus target-health results deterministically.
    """

    if state.get("error"):
        return {
            "final_answer": state["error"],
        }

    health_metrics = state.get(
        "health_metrics",
        {},
    )

    total_count = health_metrics.get(
        "total_target_count",
        0,
    )

    up_count = health_metrics.get(
        "up_target_count",
        0,
    )

    down_count = health_metrics.get(
        "down_target_count",
        0,
    )

    lines = [
        "Prometheus target health:",
        f"- Total targets: {total_count}",
        f"- UP targets: {up_count}",
        f"- DOWN targets: {down_count}",
    ]

    down_targets = [
        target
        for target in health_metrics.get(
            "targets",
            [],
        )
        if target.get("status") == "DOWN"
    ]

    if down_targets:
        lines.append("- Unhealthy targets:")

        for target in down_targets:
            lines.append(
                "- "
                f"{target.get('job')} | "
                f"{target.get('instance')} | "
                f"namespace={target.get('namespace')}"
            )
    else:
        lines.append(
            "- All discovered Prometheus targets are UP."
        )

    return {
        "final_answer": "\n".join(lines),
    }


def unsupported_question_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Return a controlled message for unsupported question types.
    """

    return {
        "final_answer": (
            "This monitoring workflow currently supports only "
            "Kubernetes node CPU-utilization questions and "
            "Prometheus target-health questions."
        )
    }


def build_monitoring_graph():
    """
    Build and compile the conditional monitoring workflow.
    """

    graph = StateGraph(MonitoringGraphState)

    graph.add_node(
        "classify_question",
        classify_question_node,
    )

    graph.add_node(
        "collect_cpu_metrics",
        collect_cpu_metrics_node,
    )

    graph.add_node(
        "collect_health_metrics",
        collect_health_metrics_node,
    )

    graph.add_node(
        "format_cpu_response",
        format_cpu_response_node,
    )

    graph.add_node(
        "format_health_response",
        format_health_response_node,
    )

    graph.add_node(
        "unsupported_question",
        unsupported_question_node,
    )

    graph.add_edge(
        START,
        "classify_question",
    )

    graph.add_conditional_edges(
        "classify_question",
        route_question,
        {
            "collect_cpu_metrics": (
                "collect_cpu_metrics"
            ),
            "collect_health_metrics": (
                "collect_health_metrics"
            ),
            "unsupported_question": (
                "unsupported_question"
            ),
        },
    )

    graph.add_edge(
        "collect_cpu_metrics",
        "format_cpu_response",
    )

    graph.add_edge(
        "collect_health_metrics",
        "format_health_response",
    )

    graph.add_edge(
        "format_cpu_response",
        END,
    )

    graph.add_edge(
        "format_health_response",
        END,
    )

    graph.add_edge(
        "unsupported_question",
        END,
    )

    return graph.compile()


monitoring_graph = build_monitoring_graph()
