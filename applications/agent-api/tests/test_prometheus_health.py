from pprint import pprint

from tools.prometheus_health import get_prometheus_target_health


result = get_prometheus_target_health()

pprint(result)
