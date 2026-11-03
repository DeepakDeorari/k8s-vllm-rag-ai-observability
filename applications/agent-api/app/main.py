from fastapi import FastAPI
from pydantic import BaseModel

from langchain_openai import ChatOpenAI

from config.models import (
    QWEN_BASE_URL,
    QWEN_MODEL,
)

app = FastAPI(title="Project3 Agent API")


class QuestionRequest(BaseModel):
    question: str


llm = ChatOpenAI(
    model=QWEN_MODEL,
    base_url=QWEN_BASE_URL,
    api_key="not-needed",
    temperature=0
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/ask")
def ask(request: QuestionRequest):

    response = llm.invoke(request.question)

    return {
        "question": request.question,
        "answer": response.content,
    }
