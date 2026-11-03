import json
from typing import Any

from langchain.tools import tool

from tools.prometheus import query_prometheus


def _extract_query(query: str) -> str:
    """
    Accept either a plain PromQL string or JSON-encoded tool input.

    Examples:
        up
        {"query": "up"}
    """

    if not isinstance(query, str):
        return str(query)

    cleaned_query = query.strip()

    if cleaned_query.startswith("{"):
        try:
            parsed_input = json.loads(cleaned_query)

            if isinstance(parsed_input, dict) and "query" in parsed_input:
                return str(parsed_input["query"]).strip()

        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    return cleaned_query


def _format_instant_vector(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Convert a Prometheus instant-vector response into an
    LLM-friendly structure.

    Prometheus represents a sample as:

        [timestamp, value]

    The timestamp is intentionally removed so that the model does
    not confuse it with the actual metric value.
    """

    formatted_results = []

    for item in result.get("data", {}).get("result", []):
        value = item.get("value", [None, None])

        formatted_results.append(
            {
                "metric": item.get("metric", {}),
                "current_value": (
                    value[1]
                    if len(value) > 1
                    else None
                ),
            }
        )

    return formatted_results


@tool
def prometheus_up(request: str) -> dict[str, Any]:
    """
    Return the count and details of Prometheus scrape targets
    currently reporting UP.

    Use this tool for target-health and scrape-health questions.

    The request argument contains the user's question and does not
    need to contain PromQL.
    """

    result = query_prometheus("up")
    targets = []

    for item in result.get("data", {}).get("result", []):
        metric = item.get("metric", {})
        value = item.get("value", [None, None])

        current_value = (
            value[1]
            if len(value) > 1
            else None
        )

        if current_value == "1":
            targets.append(
                {
                    "job": metric.get("job"),
                    "instance": metric.get("instance"),
                    "namespace": metric.get("namespace"),
                    "current_value": current_value,
                }
            )

    return {
        "up_target_count": len(targets),
        "targets": targets,
    }


@tool
def current_node_cpu_percent(
    request: str,
) -> dict[str, Any]:
    """
    Return the current average CPU utilization percentage for every
    Kubernetes node monitored by Prometheus Node Exporter.

    Use this dedicated tool for questions about current Kubernetes
    node CPU usage or CPU utilization.

    Do not generate PromQL when this tool matches the user's question.
    """

    query = (
        "100 * (1 - avg by (instance) "
        '(rate(node_cpu_seconds_total'
        '{job="node-exporter",mode="idle"}[5m])))'
    )

    result = query_prometheus(query)
    nodes = []

    for item in result.get("data", {}).get("result", []):
        metric = item.get("metric", {})
        value = item.get("value", [None, None])

        raw_value = (
            value[1]
            if len(value) > 1
            else None
        )

        try:
            cpu_percent = round(float(raw_value), 2)
        except (TypeError, ValueError):
            cpu_percent = None

        nodes.append(
            {
                "instance": metric.get("instance"),
                "cpu_utilization_percent": cpu_percent,
            }
        )

    return {
        "query": query,
        "node_count": len(nodes),
        "nodes": nodes,
    }


@tool
def prometheus_query(
    query: str,
) -> dict[str, Any]:
    """
    Execute a supplied PromQL instant query and return structured
    results.

    Use this generic tool only when no dedicated Prometheus tool
    matches the user's request.

    The supplied query must use metrics that exist in Prometheus.
    """

    cleaned_query = _extract_query(query)

    result = query_prometheus(cleaned_query)
    rows = _format_instant_vector(result)

    return {
        "query": cleaned_query,
        "result_count": len(rows),
        "results": rows,
    }
