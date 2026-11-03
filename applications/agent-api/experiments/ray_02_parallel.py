import time

import ray


TASK_DURATION = 2
TASK_COUNT = 3


def normal_task(task_id):
    """
    Ordinary sequential Python function.
    """

    time.sleep(TASK_DURATION)

    return {
        "task_id": task_id,
        "status": "complete",
    }


@ray.remote
def ray_task(task_id):
    """
    Same operation executed as a Ray task.
    """

    time.sleep(TASK_DURATION)

    return {
        "task_id": task_id,
        "status": "complete",
    }


ray.init()


print("\nSEQUENTIAL EXECUTION")
print("====================")

start = time.perf_counter()

sequential_results = []

for task_id in range(TASK_COUNT):
    sequential_results.append(
        normal_task(task_id)
    )

sequential_duration = (
    time.perf_counter() - start
)

print(
    f"Results: {sequential_results}"
)

print(
    f"Duration: {sequential_duration:.2f} seconds"
)


print("\nRAY PARALLEL EXECUTION")
print("======================")

start = time.perf_counter()

object_refs = [
    ray_task.remote(task_id)
    for task_id in range(TASK_COUNT)
]

print(
    f"ObjectRefs: {object_refs}"
)

parallel_results = ray.get(
    object_refs
)

parallel_duration = (
    time.perf_counter() - start
)

print(
    f"Results: {parallel_results}"
)

print(
    f"Duration: {parallel_duration:.2f} seconds"
)


print("\nCOMPARISON")
print("==========")

print(
    f"Sequential: {sequential_duration:.2f}s"
)

print(
    f"Ray:        {parallel_duration:.2f}s"
)

print(
    "Speedup:    "
    f"{sequential_duration / parallel_duration:.2f}x"
)


ray.shutdown()
