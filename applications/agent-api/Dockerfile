FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd \
        --uid 10001 \
        --gid appgroup \
        --create-home \
        --shell /usr/sbin/nologin \
        appuser

COPY requirements-langgraph-working.txt /app/requirements.txt

RUN python -m pip install \
    --no-cache-dir \
    --upgrade pip \
    && python -m pip install \
        --no-cache-dir \
        -r /app/requirements.txt

# Download and save the embedding model during image build.
# The running container will not require Hugging Face network access.
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); model.save('/app/models/all-MiniLM-L6-v2')"

COPY app /app/app
COPY config /app/config
COPY tools /app/tools
COPY workflows /app/workflows

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8082

CMD ["uvicorn", "app.langgraph_main:app", "--host", "0.0.0.0", "--port", "8082"]
