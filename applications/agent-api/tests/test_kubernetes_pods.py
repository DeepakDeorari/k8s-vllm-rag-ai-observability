from pprint import pprint

from tools.kubernetes_pods import get_restarting_pods


result = get_restarting_pods()

print("KUBERNETES RESTART DIAGNOSTICS")
print("==============================")

print(
    f"Configuration source: "
    f"{result['config_source']}"
)

print(
    f"Total pods inspected: "
    f"{result['total_pod_count']}"
)

print(
    f"Pods with restarts: "
    f"{result['restarting_pod_count']}"
)

print("\nRESTARTING PODS")
print("===============")

pprint(
    result["restarting_pods"]
)
