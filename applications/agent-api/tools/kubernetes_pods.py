import os
from typing import Any

from kubernetes import client
from kubernetes import config


MICROK8S_KUBECONFIG = (
    "/var/snap/microk8s/current/credentials/client.config"
)

SERVICE_ACCOUNT_TOKEN = (
    "/var/run/secrets/kubernetes.io/serviceaccount/token"
)


def load_kubernetes_config() -> str:
    """
    Load Kubernetes authentication configuration.

    When running inside Kubernetes, use the pod's ServiceAccount.

    When running directly on the MicroK8s host, use the MicroK8s
    kubeconfig file.
    """

    if os.path.exists(SERVICE_ACCOUNT_TOKEN):
        config.load_incluster_config()

        return "in-cluster"

    if not os.path.exists(MICROK8S_KUBECONFIG):
        raise FileNotFoundError(
            "MicroK8s kubeconfig was not found at "
            f"{MICROK8S_KUBECONFIG}"
        )

    config.load_kube_config(
        config_file=MICROK8S_KUBECONFIG,
    )

    return "microk8s-kubeconfig"


def get_container_waiting_reason(
    container_status: Any,
) -> str | None:
    """
    Return the current waiting reason for a container.

    Examples:
        CrashLoopBackOff
        ImagePullBackOff
        ContainerCreating
    """

    state = getattr(
        container_status,
        "state",
        None,
    )

    if state is None:
        return None

    waiting = getattr(
        state,
        "waiting",
        None,
    )

    if waiting is None:
        return None

    return getattr(
        waiting,
        "reason",
        None,
    )


def get_restarting_pods() -> dict[str, Any]:
    """
    Return structured diagnostics for pods whose containers have
    restarted at least once.

    This function is framework-independent and can be called from
    tests, LangGraph nodes, FastAPI routes, or future tool wrappers.
    """

    config_source = load_kubernetes_config()

    core_api = client.CoreV1Api()

    pod_list = core_api.list_pod_for_all_namespaces(
        watch=False,
    )

    restarting_pods = []

    for pod in pod_list.items:
        container_statuses = (
            pod.status.container_statuses or []
        )

        restarting_containers = []

        for container_status in container_statuses:
            restart_count = (
                container_status.restart_count or 0
            )

            waiting_reason = (
                get_container_waiting_reason(
                    container_status
                )
            )

            if restart_count > 0:
                restarting_containers.append(
                    {
                        "container": (
                            container_status.name
                        ),
                        "ready": (
                            container_status.ready
                        ),
                        "restart_count": restart_count,
                        "waiting_reason": waiting_reason,
                    }
                )

        if restarting_containers:
            total_restarts = sum(
                container["restart_count"]
                for container
                in restarting_containers
            )

            restarting_pods.append(
                {
                    "namespace": (
                        pod.metadata.namespace
                    ),
                    "pod": pod.metadata.name,
                    "phase": pod.status.phase,
                    "node": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip,
                    "total_restarts": total_restarts,
                    "containers": (
                        restarting_containers
                    ),
                }
            )

    restarting_pods.sort(
        key=lambda pod: pod["total_restarts"],
        reverse=True,
    )

    return {
        "config_source": config_source,
        "total_pod_count": len(
            pod_list.items
        ),
        "restarting_pod_count": len(
            restarting_pods
        ),
        "restarting_pods": restarting_pods,
    }


def get_unhealthy_pods() -> dict[str, Any]:
    """
    Return pods that are currently unhealthy.

    A pod is considered unhealthy when one or more of these
    conditions is true:

    - Pod phase is Pending, Failed, or Unknown
    - A container is not ready
    - A container is currently waiting because of an error
    - A container is currently terminated unexpectedly

    Completed one-time workloads are excluded from the unhealthy
    result when their phase is Succeeded.
    """

    config_source = load_kubernetes_config()

    core_api = client.CoreV1Api()

    pod_list = core_api.list_pod_for_all_namespaces(
        watch=False,
    )

    unhealthy_pods = []

    for pod in pod_list.items:
        phase = pod.status.phase

        # A successfully completed Job or test pod is not unhealthy.
        if phase == "Succeeded":
            continue

        container_statuses = (
            pod.status.container_statuses or []
        )

        unhealthy_containers = []

        for container_status in container_statuses:
            state = getattr(
                container_status,
                "state",
                None,
            )

            waiting_reason = None
            waiting_message = None
            terminated_reason = None
            exit_code = None

            if state is not None:
                waiting = getattr(
                    state,
                    "waiting",
                    None,
                )

                terminated = getattr(
                    state,
                    "terminated",
                    None,
                )

                if waiting is not None:
                    waiting_reason = getattr(
                        waiting,
                        "reason",
                        None,
                    )

                    waiting_message = getattr(
                        waiting,
                        "message",
                        None,
                    )

                if terminated is not None:
                    terminated_reason = getattr(
                        terminated,
                        "reason",
                        None,
                    )

                    exit_code = getattr(
                        terminated,
                        "exit_code",
                        None,
                    )

            currently_unhealthy = (
                not container_status.ready
                or waiting_reason is not None
                or (
                    terminated_reason is not None
                    and exit_code not in (None, 0)
                )
            )

            if currently_unhealthy:
                unhealthy_containers.append(
                    {
                        "container": (
                            container_status.name
                        ),
                        "ready": (
                            container_status.ready
                        ),
                        "restart_count": (
                            container_status.restart_count
                            or 0
                        ),
                        "waiting_reason": waiting_reason,
                        "waiting_message": waiting_message,
                        "terminated_reason": (
                            terminated_reason
                        ),
                        "exit_code": exit_code,
                    }
                )

        unhealthy_phase = phase in {
            "Pending",
            "Failed",
            "Unknown",
        }

        if unhealthy_phase or unhealthy_containers:
            pod_conditions = []

            for condition in (
                pod.status.conditions or []
            ):
                if condition.status != "True":
                    pod_conditions.append(
                       {
                            "type": condition.type,
                            "status": condition.status,
                            "reason": condition.reason,
                            "message": condition.message,
                        }
                    )

            unhealthy_pods.append(
                {
                    "namespace": (
                        pod.metadata.namespace
                    ),
                    "pod": pod.metadata.name,
                    "phase": phase,
                    "node": pod.spec.node_name,
                    "pod_ip": pod.status.pod_ip,
                    "containers": (
                        unhealthy_containers
                    ),
                    "conditions": pod_conditions,
                }
            )

    return {
        "config_source": config_source,
        "total_pod_count": len(
            pod_list.items
        ),
        "unhealthy_pod_count": len(
            unhealthy_pods
        ),
        "unhealthy_pods": unhealthy_pods,
    }

