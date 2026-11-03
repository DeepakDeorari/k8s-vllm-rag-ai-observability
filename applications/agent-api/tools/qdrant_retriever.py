import os
from typing import Any

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://qdrant.qdrant.svc.cluster.local:6333",
)

COLLECTION = "docs"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

qdrant = QdrantClient(
    url=QDRANT_URL,
)


embedder = SentenceTransformer(
    EMBEDDING_MODEL
)


def retrieve_documents(
    question: str,
    limit: int = 3,
) -> dict[str, Any]:
    """
    Retrieve semantically relevant unique documents from Qdrant.

    More candidates than requested are retrieved because the existing
    Phase 2 collection contains duplicate documents.

    Documents are then deduplicated by their text while preserving
    Qdrant similarity ranking.
    """

    cleaned_question = question.strip()

    if not cleaned_question:
        return {
            "question": question,
            "collection": COLLECTION,
            "embedding_model": EMBEDDING_MODEL,
            "result_count": 0,
            "documents": [],
        }

    # Convert the user's question into the same 384-dimensional
    # embedding space used during Phase 2 ingestion.
    vector = embedder.encode(
        [cleaned_question]
    )[0].tolist()

    # Retrieve extra candidates because duplicate documents may
    # consume some of the highest-ranked positions.
    candidate_limit = max(
        limit * 3,
        limit,
    )

    result = qdrant.query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=candidate_limit,
        with_payload=True,
    )

    documents = []

    seen_texts = set()

    for point in result.points:
        payload = point.payload or {}

        text = payload.get("text")

        if not text:
            continue

        normalized_text = (
            text
            .strip()
            .casefold()
        )

        # Skip duplicate Phase 2 documents.
        if normalized_text in seen_texts:
            continue

        seen_texts.add(
            normalized_text
        )

        documents.append(
            {
                "id": str(point.id),
                "score": round(
                    float(point.score),
                    4,
                ),
                "text": text.strip(),
            }
        )

        # Stop once we have the requested number of unique documents.
        if len(documents) >= limit:
            break

    return {
        "question": cleaned_question,
        "collection": COLLECTION,
        "embedding_model": EMBEDDING_MODEL,
        "result_count": len(documents),
        "documents": documents,
    }
