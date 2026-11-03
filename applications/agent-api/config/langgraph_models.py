import os


QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL",
    "http://vllm-qwen.vllm.svc.cluster.local:8000/v1",
)

QWEN_MODEL = os.getenv(
    "QWEN_MODEL",
    "Qwen/Qwen2.5-1.5B-Instruct",
)

QWEN_API_KEY = os.getenv(
    "QWEN_API_KEY",
    "not-needed",
)
