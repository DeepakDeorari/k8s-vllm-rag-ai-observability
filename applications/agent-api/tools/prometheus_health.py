from typing import Any

from tools.prometheus import query_prometheus


def get_prometheus_target_health() -> dict[str, Any]:
    """
    Return Prometheus targets and their current scrape-health status.

    Prometheus returns the `up` metric with:
        1 = target is healthy and reachable
        0 = target is unhealthy or unreachable
    """

    result = query_prometheus("up")

    targets = []
    up_count = 0
    down_count = 0

    for item in result.get("data", {}).get("result", []):
        metric = item.get("metric", {})
        value = item.get("value", [None, None])

        current_value = (
            value[1]
            if len(value) > 1
            else None
        )

        status = (
            "UP"
            if current_value == "1"
            else "DOWN"
        )

        if status == "UP":
            up_count += 1
        else:
            down_count += 1

        targets.append(
            {
                "job": metric.get("job"),
                "instance": metric.get("instance"),
                "namespace": metric.get("namespace"),
                "status": status,
            }
        )

    return {
        "total_target_count": len(targets),
        "up_target_count": up_count,
        "down_target_count": down_count,
        "targets": targets,
    }
