from typing import Literal
from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

from config.langgraph_models import (
    QWEN_API_KEY,
    QWEN_BASE_URL,
    QWEN_MODEL,
)
from tools.prometheus_cpu import (
    get_current_node_cpu_percent,
)
from tools.prometheus_health import (
    get_prometheus_target_health,
)


class MonitoringGraphState(TypedDict, total=False):
    """
    Shared state for the LLM-routed monitoring workflow.
    """

    question: str

    route: Literal[
        "cpu",
        "health",
        "unsupported",
    ]

    classification_raw: str
    classification_reason: str

    cpu_metrics: dict
    health_metrics: dict

    final_answer: str
    error: str


classifier_llm = ChatOpenAI(
    model=QWEN_MODEL,
    base_url=QWEN_BASE_URL,
    api_key=QWEN_API_KEY,
    temperature=0,
    max_tokens=30,
    timeout=30,
    max_retries=2,
)


def normalize_route(
    model_output: str,
) -> Literal[
    "cpu",
    "health",
    "unsupported",
]:
    """
    Convert model output into one of the graph's valid routes.

    The function is deliberately strict. Any unclear response is
    routed to unsupported rather than guessed.
    """

    cleaned_output = model_output.strip().upper()

    if cleaned_output == "CPU":
        return "cpu"

    if cleaned_output == "HEALTH":
        return "health"

    if cleaned_output == "UNSUPPORTED":
        return "unsupported"

    return "unsupported"


def classify_question_with_llm_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Use Qwen through vLLM to classify the user's intent.

    Qwen performs only classification. It does not generate PromQL,
    execute tools, or format operational values.
    """

    question = state.get("question", "").strip()

    if not question:
        return {
            "route": "unsupported",
            "classification_raw": "",
            "classification_reason": (
                "The question was empty."
            ),
        }

    messages = [
        (
            "system",
            (
                "You are an intent classifier for an SRE "
                "monitoring workflow.\n\n"
                "Classify the user's question into exactly one "
                "of these categories:\n\n"
                "CPU\n"
                "- Current Kubernetes node CPU usage\n"
                "- Node processor utilization\n"
                "- Compute utilization of cluster nodes\n\n"
                "HEALTH\n"
                "- Prometheus scrape-target status\n"
                "- Whether monitored targets are UP or DOWN\n"
                "- Whether monitored systems are reachable\n"
                "- Monitoring target health\n\n"
                "UNSUPPORTED\n"
                "- Memory, GPU, pods, logs, deployments, "
                "restarts, or anything outside CPU and "
                "Prometheus target health\n\n"
                "Return only one word:\n"
                "CPU\n"
                "HEALTH\n"
                "UNSUPPORTED\n\n"
                "Do not explain your answer."
            ),
        ),
        (
            "human",
            question,
        ),
    ]

    try:
        response = classifier_llm.invoke(messages)
        raw_output = str(response.content).strip()
        route = normalize_route(raw_output)

        return {
            "route": route,
            "classification_raw": raw_output,
            "classification_reason": (
                "Route selected by Qwen through vLLM."
            ),
        }

    except Exception as exc:
        return {
            "route": "unsupported",
            "classification_raw": "",
            "classification_reason": (
                "LLM classification failed: "
                f"{type(exc).__name__}: {exc}"
            ),
            "error": (
                "Question classification failed."
            ),
        }


def route_question(
    state: MonitoringGraphState,
) -> Literal[
    "collect_cpu_metrics",
    "collect_health_metrics",
    "unsupported_question",
]:
    """
    Route graph execution using the normalized classification.
    """

    route = state.get(
        "route",
        "unsupported",
    )

    if route == "cpu":
        return "collect_cpu_metrics"

    if route == "health":
        return "collect_health_metrics"

    return "unsupported_question"


def collect_cpu_metrics_node(
    state: MonitoringGraphState,
) -> dict:
    """
    Collect validated CPU metrics from Prometheus.
    """

    try:
        return {
            "cpu_metrics": (
                get_current_node_cpu_percent()
            )
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
    Collect validated target-health data from Prometheus.
    """

    try:
        return {
            "health_metrics": (
                get_prometheus_target_health()
            )
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
    Format CPU metrics without using an LLM.
    """

    if state.get("error"):
        return {
            "final_answer": state["error"],
        }

    nodes = state.get(
        "cpu_metrics",
        {},
    ).get(
        "nodes",
        [],
    )

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
    Format target-health metrics without using an LLM.
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
                f"namespace="
                f"{target.get('namespace')}"
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
    Return a controlled response for unsupported intents.
    """

    if state.get("error"):
        details = state.get(
            "classification_reason",
            state["error"],
        )

        return {
            "final_answer": (
                "The monitoring request could not be "
                f"classified safely. Details: {details}"
            )
        }

    return {
        "final_answer": (
            "This workflow currently supports only "
            "Kubernetes node CPU-utilization questions and "
            "Prometheus target-health questions."
        )
    }


def build_llm_monitoring_graph():
    """
    Build and compile the LLM-routed monitoring graph.
    """

    graph = StateGraph(MonitoringGraphState)

    graph.add_node(
        "classify_question_with_llm",
        classify_question_with_llm_node,
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
        "classify_question_with_llm",
    )

    graph.add_conditional_edges(
        "classify_question_with_llm",
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


llm_monitoring_graph = (
    build_llm_monitoring_graph()
)
