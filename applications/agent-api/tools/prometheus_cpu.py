from typing import Any

from tools.prometheus import query_prometheus


CPU_UTILIZATION_QUERY = (
    "100 * (1 - avg by (instance) "
    '(rate(node_cpu_seconds_total'
    '{job="node-exporter",mode="idle"}[5m])))'
)


def get_current_node_cpu_percent() -> dict[str, Any]:
    """
    Return current average CPU utilization for every node-exporter
    instance found in Prometheus.

    This is a framework-independent function. It can be called from
    LangChain tools, LangGraph nodes, FastAPI routes, or tests.
    """

    result = query_prometheus(CPU_UTILIZATION_QUERY)
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
        "query": CPU_UTILIZATION_QUERY,
        "node_count": len(nodes),
        "nodes": nodes,
    }
