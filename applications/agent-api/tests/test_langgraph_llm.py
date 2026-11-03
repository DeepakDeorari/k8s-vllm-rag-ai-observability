from langchain_openai import ChatOpenAI


llm = ChatOpenAI(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    base_url="http://10.152.183.65:8000/v1",
    api_key="not-needed",
    temperature=0,
    max_tokens=20,
    timeout=30,
    max_retries=2,
)


response = llm.invoke(
    [
        (
            "system",
            (
                "Classify the user question into exactly one category: "
                "CPU, HEALTH, or UNSUPPORTED. "
                "Return only the category name."
            ),
        ),
        (
            "human",
            "Are the monitored systems responding correctly?",
        ),
    ]
)


print("RAW RESPONSE:")
print(repr(response.content))

print("\nCLEAN RESPONSE:")
print(response.content.strip())
