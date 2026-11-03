from pprint import pprint

from workflows.sre_monitoring_graph import (
    sre_monitoring_graph,
)


question = (
    "Show the workloads with the highest "
    "historical restart counts."
)


final_state = sre_monitoring_graph.invoke(
    {
        "question": question,
    }
)


print("\nQUESTION")
print("========")
print(question)


print("\nPRIMARY ROUTE")
print("=============")
print(
    final_state.get(
        "route"
    )
)


print("\nKUBERNETES INTENT")
print("=================")
print(
    final_state.get(
        "kubernetes_intent"
    )
)


print("\nRETRIEVAL QUERY")
print("===============")
print(
    final_state.get(
        "retrieval_query"
    )
)


print("\nRETRIEVAL COUNT")
print("===============")
print(
    final_state.get(
        "retrieval_count"
    )
)


print("\nRETRIEVED DOCUMENTS")
print("===================")
pprint(
    final_state.get(
        "retrieved_documents"
    )
)

print("\nGROUNDED ANALYSIS")
print("=================")

print(
    final_state.get(
        "analysis"
    )
)

print("\nANALYSIS ERROR")
print("==============")

print(
    final_state.get(
        "analysis_error"
    )
)

print("\nANALYSIS VALID")
print("==============")

print(
    final_state.get(
        "analysis_valid"
    )
)


print("\nANALYSIS VALIDATION ERRORS")
print("==========================")

pprint(
    final_state.get(
        "analysis_validation_errors"
    )
)


print("\nVALIDATED ANALYSIS")
print("==================")

print(
    final_state.get(
        "validated_analysis"
    )
)

print("\nFINAL ANSWER")
print("============")
print(
    final_state.get(
        "final_answer"
    )
)
