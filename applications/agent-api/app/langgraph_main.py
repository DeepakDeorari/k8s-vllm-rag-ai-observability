import logging
import time
from typing import Any
from typing import Literal

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field

from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import generate_latest
from fastapi import Response

from app.metrics import (
    ANALYSIS_VALIDATION_TOTAL,
    FALLBACK_TOTAL,
    INVESTIGATIONS_TOTAL,
    INVESTIGATION_DURATION,
    RETRIEVED_DOCUMENTS,
    ROUTE_TOTAL,
)

from workflows.sre_monitoring_graph import (
    sre_monitoring_graph,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)


logger = logging.getLogger(
    "langgraph-agent-api"
)


app = FastAPI(
    title="AI SRE LangGraph API",
    description=(
        "Read-only AI SRE investigation API using "
        "LangGraph, Qwen through vLLM, Prometheus, "
        "the Kubernetes API, and Qdrant."
    ),
    version="0.1.0",
)


class InvestigationRequest(BaseModel):
    """
    Input schema for an SRE investigation.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description=(
            "Natural-language operational question."
        ),
        examples=[
            (
                "Show the workloads with the highest "
                "historical restart counts."
            )
        ],
    )


class RetrievedDocument(BaseModel):
    """
    A document retrieved from Qdrant.
    """

    id: str | None = None
    score: float | None = None
    text: str | None = None


class InvestigationResponse(BaseModel):
    """
    Safe API response returned to the caller.

    Large internal objects such as all pod details and raw graph
    state are intentionally not returned through the public API.
    """

    question: str

    route: Literal[
        "cpu",
        "health",
        "kubernetes",
        "broad",
        "unsupported",
    ]

    kubernetes_intent: Literal[
        "restarts",
        "unhealthy",
        "unsupported",
    ] | None = None

    answer: str

    analysis_valid: bool | None = None

    analysis_validation_errors: list[str] = Field(
        default_factory=list
    )

    retrieved_documents: list[
        RetrievedDocument
    ] = Field(
        default_factory=list
    )

    duration_ms: float


@app.get("/health")
def health() -> dict[str, str]:
    """
    Lightweight process-health endpoint.

    This endpoint does not invoke Qwen, Prometheus,
    Kubernetes, or Qdrant.
    """

    return {
        "status": "healthy",
        "service": "ai-sre-langgraph-api",
    }

@app.get("/metrics")
def metrics() -> Response:
    """
    Expose Prometheus metrics for the AI SRE API.
    """

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/capabilities")
def capabilities() -> dict[str, Any]:
    """
    Return currently implemented investigation capabilities.
    """

    return {
        "service": "ai-sre-langgraph-api",
        "read_only": True,
        "capabilities": [
            {
                "route": "cpu",
                "description": (
                    "Current Kubernetes node CPU utilization "
                    "from Prometheus."
                ),
            },
            {
                "route": "health",
                "description": (
                    "Current Prometheus scrape-target health."
                ),
            },
            {
                "route": "kubernetes",
                "intent": "restarts",
                "description": (
                    "Historical Kubernetes pod restart "
                    "investigation enriched with Qdrant "
                    "runbooks and guarded Qwen analysis."
                ),
            },
            {
                "route": "kubernetes",
                "intent": "unhealthy",
                "description": (
                    "Current unhealthy Kubernetes pod "
                    "diagnostics."
                ),
            },
            {
                "route": "broad",
                "description": (
                    "Distributed platform investigation across "
                    "Prometheus, Kubernetes, node CPU, pod "
                    "restart history, and operational knowledge."
                ),
            },
        ],
        "unsupported_examples": [
            "GPU temperature",
            "Node memory utilization",
            "Application log analysis",
            "State-changing remediation",
        ],
    }


@app.post(
    "/investigate",
    response_model=InvestigationResponse,
)
def investigate(
    request: InvestigationRequest,
) -> InvestigationResponse:
    """
    Execute the compiled SRE LangGraph workflow.

    The endpoint returns the deterministic final answer and selected
    safety metadata. The complete graph state remains internal.
    """

    question = request.question.strip()

    logger.info(
        "Starting investigation | question=%r",
        question,
    )

    start_time = time.perf_counter()

    try:
        final_state = sre_monitoring_graph.invoke(
            {
                "question": question,
            }
        )

    except Exception as exc:
        logger.exception(
            "Investigation workflow failed"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The investigation workflow failed: "
                f"{type(exc).__name__}"
            ),
        ) from exc

    duration_ms = round(
        (
            time.perf_counter()
            - start_time
        )
        * 1000,
        2,
    )

    final_answer = final_state.get(
        "final_answer",
        "",
    )

    if not final_answer:
        logger.error(
            "Workflow returned no final answer"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The investigation workflow returned "
                "no final answer."
            ),
        )

    route = final_state.get(
        "route",
        "unsupported",
    )

    kubernetes_intent = final_state.get(
        "kubernetes_intent"
    )

    metrics_kubernetes_intent = (
        kubernetes_intent
        if kubernetes_intent
        else "none"
    )

    INVESTIGATIONS_TOTAL.inc()

    ROUTE_TOTAL.labels(
        route=route,
        kubernetes_intent=(
            metrics_kubernetes_intent
        ),
    ).inc()

    INVESTIGATION_DURATION.labels(
        route=route,
    ).observe(
        duration_ms / 1000.0
    )

    raw_documents = final_state.get(
        "retrieved_documents",
        [],
    )

    RETRIEVED_DOCUMENTS.observe(
        len(raw_documents)
    )


    retrieved_documents = [
        RetrievedDocument(
            id=document.get("id"),
            score=document.get("score"),
            text=document.get("text"),
        )
        for document in raw_documents
    ]

    validation_errors = final_state.get(
        "analysis_validation_errors",
        [],
    )

    analysis_valid = final_state.get(
        "analysis_valid"
    )

    if analysis_valid is True:
        ANALYSIS_VALIDATION_TOTAL.labels(
            result="accepted",
        ).inc()

    elif analysis_valid is False:
        ANALYSIS_VALIDATION_TOTAL.labels(
            result="rejected",
        ).inc()

        FALLBACK_TOTAL.inc()


    logger.info(
        (
            "Investigation completed | "
            "route=%s | "
            "kubernetes_intent=%s | "
            "analysis_valid=%s | "
            "duration_ms=%s"
        ),
        route,
        kubernetes_intent,
        analysis_valid,
        duration_ms,
    )

    return InvestigationResponse(
        question=question,
        route=route,
        kubernetes_intent=(
            kubernetes_intent
        ),
        answer=final_answer,
        analysis_valid=analysis_valid,
        analysis_validation_errors=(
            validation_errors
        ),
        retrieved_documents=(
            retrieved_documents
        ),
        duration_ms=duration_ms,
    )
