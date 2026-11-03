from pprint import pprint

from workflows.cpu_graph import cpu_graph


initial_state = {
    "question": (
        "What is the current CPU utilization "
        "of every Kubernetes node?"
    )
}


final_state = cpu_graph.invoke(initial_state)


print("\nFINAL ANSWER")
print("============")

print(final_state["final_answer"])


print("\nFINAL GRAPH STATE")
print("=================")

pprint(final_state)
