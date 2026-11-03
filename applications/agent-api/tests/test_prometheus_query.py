from tools.prometheus_tool import prometheus_query

result = prometheus_query.invoke(
    {"query": "up"}
)

print(result[:500])
