from pprint import pprint

from tools.kubernetes_pods import get_unhealthy_pods


result = get_unhealthy_pods()

print("CURRENT KUBERNETES POD HEALTH")
print("=============================")

print(
    f"Configuration source: "
    f"{result['config_source']}"
)

print(
    f"Total pods inspected: "
    f"{result['total_pod_count']}"
)

print(
    f"Currently unhealthy pods: "
    f"{result['unhealthy_pod_count']}"
)

print("\nUNHEALTHY PODS")
print("==============")

pprint(
    result["unhealthy_pods"]
)
