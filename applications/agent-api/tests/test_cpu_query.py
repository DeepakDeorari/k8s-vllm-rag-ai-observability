from pprint import pprint

from tools.prometheus_tool import current_node_cpu_percent


result = current_node_cpu_percent.invoke(
    {
        "request": "Return current CPU utilization for every node."
    }
)

pprint(result)
