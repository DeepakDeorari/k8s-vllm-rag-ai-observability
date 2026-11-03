import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer


QDRANT_URL = "http://10.152.183.134:6333"

COLLECTION = "docs"

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


qdrant = QdrantClient(
    url=QDRANT_URL,
)


embedder = SentenceTransformer(
    EMBEDDING_MODEL
)


RUNBOOKS = [
    {
        "title": (
            "Kubernetes Historical Pod Restart Investigation"
        ),
        "text": (
            "Runbook: Kubernetes historical pod restart investigation. "
            "A non-zero container restart count is historical evidence "
            "and does not by itself mean that a pod is currently unhealthy. "
            "Verify the current pod phase, container readiness, current "
            "waiting reason, last terminated reason, exit code, Kubernetes "
            "events, and whether the restart count is continuing to increase. "
            "A pod that is Running, whose containers are Ready, and which "
            "has no current waiting error may be healthy despite previous "
            "restarts. Investigate patterns across node placement and related "
            "platform components before treating accumulated restart counts "
            "as an active incident."
        ),
    },
    {
        "title": (
            "Kubernetes CrashLoopBackOff Investigation"
        ),
        "text": (
            "Runbook: Kubernetes CrashLoopBackOff investigation. "
            "CrashLoopBackOff means a container repeatedly starts, exits, "
            "and is restarted while Kubernetes applies increasing restart "
            "delays. Verify container readiness, restart count, waiting "
            "reason, last terminated reason, exit code, pod events, "
            "application logs, resource limits, configuration, mounted "
            "secrets and ConfigMaps, dependency availability, and health "
            "probe configuration. Determine the actual termination cause "
            "before restarting or modifying the workload."
        ),
    },
    {
        "title": (
            "Prometheus Target Down Investigation"
        ),
        "text": (
            "Runbook: Prometheus target down investigation. "
            "When the Prometheus up metric is zero, first identify the "
            "affected job, instance, namespace, scrape endpoint, and metrics "
            "path. Verify that the monitored workload is running and that "
            "the expected exporter or metrics endpoint exists. Check network "
            "reachability, service and endpoint discovery, authentication, "
            "TLS configuration, scrape configuration, and the Prometheus "
            "target lastError value. Multiple down scrape targets can result "
            "from one unavailable node when several metrics paths from that "
            "node are monitored."
        ),
    },
]


def main():
    texts = [
        runbook["text"]
        for runbook in RUNBOOKS
    ]

    vectors = embedder.encode(
        texts
    ).tolist()

    points = []

    for runbook, vector in zip(
        RUNBOOKS,
        vectors,
    ):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "text": runbook["text"],
                    "title": runbook["title"],
                    "document_type": "runbook",
                    "source": "project-3",
                },
            )
        )

    qdrant.upsert(
        collection_name=COLLECTION,
        points=points,
        wait=True,
    )

    print(
        f"Inserted {len(points)} Project 3 runbooks "
        f"into collection '{COLLECTION}'."
    )

    for runbook in RUNBOOKS:
        print(
            f"- {runbook['title']}"
        )


if __name__ == "__main__":
    main()
