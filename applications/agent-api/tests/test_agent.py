from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI

from tools.prometheus_tool import (
    current_node_cpu_percent,
    prometheus_query,
    prometheus_up,
)


llm = ChatOpenAI(
    model="Qwen/Qwen2.5-1.5B-Instruct",
    base_url="http://10.152.183.65:8000/v1",
    api_key="not-needed",
    temperature=0,
)


agent = initialize_agent(
    tools=[
        prometheus_up,
        current_node_cpu_percent,
        prometheus_query,
    ],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=(
        "Your previous response did not follow the required agent format. "
        "Use exactly one valid Action from the available tools, or provide "
        "a Final Answer when you have enough evidence."
    ),
    max_iterations=5,
    early_stopping_method="force",
)


response = agent.invoke(
    {
        "input": (
            """
Check the current CPU utilization of every Kubernetes node.

Use the dedicated current_node_cpu_percent tool.

Preserve the exact instance names from the tool output.

Do not rename nodes as Node 1 or Node 2.

Report:
- instance
- cpu utilization percentage
"""
        )
    }
)


print("\n====================\n")
print(response)
