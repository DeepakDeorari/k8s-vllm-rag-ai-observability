import uuid
from fastapi import FastAPI
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from sentence_transformers import SentenceTransformer
from openai import OpenAI

app = FastAPI()

qdrant = QdrantClient(
    url="http://qdrant.qdrant.svc.cluster.local:6333"
)

embedder = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

llm = OpenAI(
    base_url="http://vllm.vllm.svc.cluster.local:8000/v1",
    api_key="dummy"
)

COLLECTION = "docs"


class IngestRequest(BaseModel):
    texts: list[str]


class QueryRequest(BaseModel):
    question: str


@app.on_event("startup")
def startup():
    dim = embedder.get_sentence_embedding_dimension()

    try:
        qdrant.get_collection(COLLECTION)
    except Exception:
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=dim,
                distance=Distance.COSINE,
            ),
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest(req: IngestRequest):

    vectors = embedder.encode(req.texts).tolist()

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=v,
            payload={"text": t},
        )
        for t, v in zip(req.texts, vectors)
    ]

    qdrant.upsert(
        collection_name=COLLECTION,
        points=points,
    )

    return {"inserted": len(points)}


@app.post("/query")
def query(req: QueryRequest):

    vec = embedder.encode([req.question])[0].tolist()

    result = qdrant.query_points(
        collection_name=COLLECTION,
        query=vec,
        limit=3,
    )

    hits = result.points

    context = "\n\n".join(
        h.payload["text"]
        for h in hits
    )

    prompt = f"""
Context:
{context}

Question:
{req.question}
"""

    answer = llm.chat.completions.create(
        model="Qwen/Qwen2.5-1.5B-Instruct",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=400
    )

    return {
        "answer":
            answer.choices[0].message.content,
        "sources":
            [h.payload for h in hits]
    }

