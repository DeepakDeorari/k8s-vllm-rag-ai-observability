from pprint import pprint

from tools.prometheus_cpu import get_current_node_cpu_percent


result = get_current_node_cpu_percent()

pprint(result)
