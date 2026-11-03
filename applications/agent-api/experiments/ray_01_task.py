import os

import ray


ray.init()


@ray.remote
def identify_worker():
    """
    Execute inside a Ray worker process.
    """

    return {
        "pid": os.getpid(),
        "message": "Hello from a Ray worker",
    }


print("\nRay initialized")
print("===============")

print(
    ray.cluster_resources()
)


result_ref = identify_worker.remote()


print("\nOBJECT REF")
print("==========")

print(result_ref)


result = ray.get(
    result_ref
)


print("\nRESULT")
print("======")

print(result)


ray.shutdown()
