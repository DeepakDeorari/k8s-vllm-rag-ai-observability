import os

import ray


ray.init()


@ray.remote(num_cpus=1)
class InvestigationWorker:
    """
    Stateful Ray Actor.

    The actor stays alive and preserves its state
    across multiple remote method calls.
    """

    def __init__(self, worker_name):
        self.worker_name = worker_name
        self.investigation_count = 0
        self.pid = os.getpid()

    def investigate(self, question):
        self.investigation_count += 1

        return {
            "worker_name": self.worker_name,
            "pid": self.pid,
            "question": question,
            "investigation_count": (
                self.investigation_count
            ),
        }

    def get_state(self):
        return {
            "worker_name": self.worker_name,
            "pid": self.pid,
            "investigation_count": (
                self.investigation_count
            ),
        }


print("\nCREATING ACTOR")
print("==============")

worker = InvestigationWorker.remote(
    "sre-worker-1"
)


questions = [
    "Check Kubernetes pods",
    "Check Prometheus health",
    "Check historical restarts",
]


print("\nCALLING ACTOR")
print("=============")

for question in questions:
    result = ray.get(
        worker.investigate.remote(
            question
        )
    )

    print(result)


print("\nACTOR STATE")
print("===========")

state = ray.get(
    worker.get_state.remote()
)

print(state)


ray.shutdown()
