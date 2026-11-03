import os

import requests


PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    (
        "http://"
        "kube-prometheus-stack-prometheus."
        "observability.svc.cluster.local:9090"
    ),
)


def query_prometheus(
    query: str,
):
    """
    Execute an instant PromQL query against Prometheus.
    """

    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={
            "query": query,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()
