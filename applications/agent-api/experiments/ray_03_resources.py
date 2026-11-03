import os
import time

import ray


ray.init()


@ray.remote(num_cpus=1)
def cpu_task(task_id):
    """
    A task requesting one logical Ray CPU.
    """

    start = time.perf_counter()

    time.sleep(2)

    return {
        "task_id": task_id,
        "pid": os.getpid(),
        "duration": round(
            time.perf_counter() - start,
            2,
        ),
    }


print("\nAVAILABLE RESOURCES")
print("===================")

print(
    ray.cluster_resources()
)


print("\nSUBMITTING 6 TASKS")
print("==================")

start = time.perf_counter()

refs = [
    cpu_task.remote(task_id)
    for task_id in range(6)
]


results = ray.get(
    refs
)


duration = (
    time.perf_counter() - start
)


print("\nRESULTS")
print("=======")

for result in results:
    print(result)


print("\nTOTAL DURATION")
print("==============")

print(
    f"{duration:.2f} seconds"
)


ray.shutdown()
