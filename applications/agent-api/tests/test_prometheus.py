from tools.prometheus import query_prometheus

result = query_prometheus("up")

print(result["status"])
print(len(result["data"]["result"]))
