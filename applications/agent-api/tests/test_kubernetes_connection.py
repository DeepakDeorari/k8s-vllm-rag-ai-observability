import os

from kubernetes import client
from kubernetes import config


MICROK8S_KUBECONFIG = (
    "/var/snap/microk8s/current/credentials/client.config"
)


def load_kubernetes_config() -> str:
    """
    Load Kubernetes authentication configuration.

    Local/host execution:
        Use the MicroK8s kubeconfig file.

    Future in-cluster execution:
        Use the pod's ServiceAccount credentials.
    """

    if os.path.exists(
        "/var/run/secrets/kubernetes.io/serviceaccount/token"
    ):
        config.load_incluster_config()

        return "in-cluster ServiceAccount configuration"

    if not os.path.exists(MICROK8S_KUBECONFIG):
        raise FileNotFoundError(
            "MicroK8s kubeconfig was not found at: "
            f"{MICROK8S_KUBECONFIG}"
        )

    config.load_kube_config(
        config_file=MICROK8S_KUBECONFIG,
    )

    return MICROK8S_KUBECONFIG


config_source = load_kubernetes_config()

core_api = client.CoreV1Api()

pods = core_api.list_pod_for_all_namespaces(
    watch=False,
)


print("KUBERNETES CONNECTION SUCCESSFUL")
print("================================")

print(f"Configuration source: {config_source}")
print(f"Total pods returned: {len(pods.items)}")

print("\nPOD SAMPLE")
print("==========")

for pod in pods.items[:10]:
    print(
        f"{pod.metadata.namespace}/"
        f"{pod.metadata.name} | "
        f"phase={pod.status.phase} | "
        f"node={pod.spec.node_name}"
    )
