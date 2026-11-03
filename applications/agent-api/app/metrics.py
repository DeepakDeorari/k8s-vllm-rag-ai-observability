from prometheus_client import Counter
from prometheus_client import Histogram


INVESTIGATIONS_TOTAL = Counter(
    "ai_sre_investigations_total",
    "Total number of SRE investigations completed.",
)


ROUTE_TOTAL = Counter(
    "ai_sre_route_total",
    "Total investigations by selected route.",
    [
        "route",
        "kubernetes_intent",
    ],
)


INVESTIGATION_DURATION = Histogram(
    "ai_sre_investigation_duration_seconds",
    "End-to-end SRE investigation duration in seconds.",
    [
        "route",
    ],
    buckets=(
        0.05,
        0.1,
        0.25,
        0.5,
        1.0,
        2.0,
        3.0,
        5.0,
        7.5,
        10.0,
        20.0,
        30.0,
    ),
)


ANALYSIS_VALIDATION_TOTAL = Counter(
    "ai_sre_analysis_validation_total",
    "Total restart-analysis validation decisions.",
    [
        "result",
    ],
)


FALLBACK_TOTAL = Counter(
    "ai_sre_fallback_total",
    "Total times deterministic safe analysis fallback was used.",
)


RETRIEVED_DOCUMENTS = Histogram(
    "ai_sre_retrieved_documents",
    "Number of Qdrant documents returned per investigation.",
    buckets=(
        0,
        1,
        2,
        3,
        5,
        10,
    ),
)
