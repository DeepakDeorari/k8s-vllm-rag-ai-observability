# Phase 2.12 - RAG Quality Evaluation

## Overview

Phase 2.12 evaluated the quality of the platform's Retrieval-Augmented Generation pipeline.

Previous phases validated infrastructure, observability, performance, horizontal GPU scaling, multi-model serving, and failure recovery. This phase focused on whether the RAG pipeline retrieves relevant information and generates answers that are correct, grounded, and resistant to hallucination.

The evaluation measured:

- Retrieval accuracy
- Answer accuracy
- Groundedness
- Unsupported-question refusal
- Hallucination rate
- Known retrieval and generation weaknesses

---

## Objectives

The objectives of this phase were to:

1. Expand the initial RAG knowledge base.
2. Create a controlled evaluation question set.
3. Test exact factual retrieval.
4. Test paraphrased retrieval.
5. Test unsupported questions.
6. Measure answer correctness.
7. Measure agreement between answers and retrieved context.
8. Identify retrieval and generation failure modes.
9. Establish a quality baseline for future improvements.

---

## RAG Architecture

The evaluated data path was:

```text
Client
  |
  v
Custom FastAPI RAG Service
  |
  +--> SentenceTransformer Embedding Model
  |
  +--> Qdrant Vector Search
  |
  +--> Retrieved Top-3 Context Chunks
  |
  +--> Qwen/Qwen2.5-1.5B-Instruct
  |
  v
Grounded Answer and Sources
```

---

## Evaluation Environment

| Component | Configuration |
|---|---|
| RAG API | Custom FastAPI application |
| Vector Database | Qdrant |
| Qdrant Collection | `docs` |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding Dimension | 384 |
| Vector Distance | Cosine |
| Retrieval Depth | Top 3 |
| Generation Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Inference Engine | vLLM |
| Kubernetes Platform | MicroK8s |
| RAG Model Alias | `rag-qwen` |

---

## Initial Knowledge Base

The initial Qdrant collection contained four points:

1. MicroK8s is a lightweight Kubernetes distribution.
2. vLLM provides OpenAI-compatible inference APIs.
3. Deepak's secret validation code is `RAG-DEMO-2026-XYZ`.
4. Qdrant is a vector database used for Retrieval-Augmented Generation.

Initial collection state:

```text
Collection: docs
Status: green
Points: 4
Embedding dimension: 384
Distance metric: Cosine
```

The four-point corpus was sufficient for basic functional validation but was too small for meaningful quality evaluation.

---

## Corpus Expansion

The knowledge base was expanded with 30 platform facts covering:

- Two-node MicroK8s architecture
- AWS g5.xlarge instances
- NVIDIA A10G GPUs
- Single-GPU benchmark results
- Dual-GPU benchmark results
- Horizontal scaling efficiency
- Average and P95 latency improvements
- Qwen deployment placement
- Phi-3 deployment placement
- Model-specific Kubernetes Services
- Qdrant
- Open WebUI
- Prometheus
- Grafana
- Loki
- Tempo
- Node hostnames
- Pod recovery times
- Worker-node failure detection
- Worker-node recovery
- Pod-level self-healing
- Node-level high-availability limitations
- Node selectors and hostpath storage limitations

### Ingestion Result

The 30-item dataset was accidentally ingested twice.

```text
Initial points:        4
First ingestion:      30
Second ingestion:     30
Total stored points:  64
```

Final collection state:

```text
Collection: docs
Status: green
Stored vectors: 64
```

### Duplicate-Ingestion Limitation

The ingestion API generates a new UUID for every point:

```python
id=str(uuid.uuid4())
```

Therefore, ingesting the same dataset twice created duplicate vectors instead of updating the existing points.

The duplicate entries did not prevent evaluation, but the duplicates influenced retrieval results. In multiple tests, two of the three retrieved sources contained identical text.

This limitation must be considered when interpreting retrieval quality.

Future ingestion workflows should use deterministic document identifiers or content hashes to provide idempotent upserts.

---

## RAG Prompt

The evaluated prompt instructed the model to answer using only retrieved context:

```text
You are a retrieval-augmented generation assistant.

Answer the user's question using only the context below.

If the answer is present in the context, answer clearly and directly.
If the answer is not present in the context, say you do not know.
```

The prompt provided basic grounding guidance but did not include strict instructions for handling negation, context contradictions, or an exact refusal format.

---

## Evaluation Methodology

A controlled ten-question evaluation set was created with three categories.

### Category 1: Exact Fact Retrieval

These questions requested facts stored directly in the knowledge base.

1. What was the dual GPU throughput at 1024 users?
2. What was the single GPU throughput at 1024 users?
3. Which model is deployed on Node 2?
4. How long did Qwen pod recovery take?
5. What is Deepak's secret validation code?

### Category 2: Paraphrased Retrieval

These questions requested stored facts using wording different from the indexed text.

6. Which GPU is installed in the cluster nodes?
7. Which service routes requests to Phi-3?
8. Does the platform currently provide node-level high availability?

### Category 3: Unsupported Questions

These questions requested information that was not present in the knowledge base.

9. What is the AWS account ID?
10. What is the database administrator password?

---

## Scoring Definitions

### Retrieval Success

A retrieval passed when at least one of the Top-3 returned sources contained the information needed to answer the question correctly.

### Answer Correctness

An answer passed when the final response matched the expected fact or correctly refused to answer an unsupported question.

### Groundedness

An answer was considered grounded when the response agreed with the retrieved context and did not introduce unsupported claims.

### Correct Refusal

A refusal passed when the model clearly stated that the requested information was unavailable from the provided context.

### Hallucination

A hallucination occurred when the model invented unsupported information or contradicted the retrieved evidence.

---

## Question-Level Results

### Q1: Dual-GPU Throughput

Question:

```text
What was the dual GPU throughput at 1024 users?
```

Expected answer:

```text
135.63 requests per second
```

Observed answer:

```text
The dual GPU throughput at 1024 users was 135.63 requests per second.
```

Relevant retrieved source:

```text
Dual GPU throughput at 1024 users was 135.63 requests per second.
```

Evaluation:

```text
Retrieval: PASS
Answer: PASS
Groundedness: PASS
Hallucination: NO
```

---

### Q2: Single-GPU Throughput

Question:

```text
What was the single GPU throughput at 1024 users?
```

Expected answer:

```text
67.52 requests per second
```

Observed answer:

```text
The single GPU throughput at 1024 users was 67.52 requests per second.
```

Relevant retrieved source:

```text
Single GPU throughput at 1024 users was 67.52 requests per second.
```

Evaluation:

```text
Retrieval: PASS
Answer: PASS
Groundedness: PASS
Hallucination: NO
```

---

### Q3: Model Deployed on Node 2

Question:

```text
Which model is deployed on Node 2?
```

Expected answer:

```text
Microsoft Phi-3-mini-4k-instruct
```

Observed answer:

```text
I do not know. The given information does not specify which model is deployed on Node 2.
```

Retrieved sources included:

```text
Qwen Qwen2.5-1.5B-Instruct is deployed on Node 1.
Phase 2.8 expanded the platform from one node to two nodes.
```

The required source was not retrieved:

```text
Microsoft Phi-3-mini-4k-instruct is deployed on Node 2.
```

Evaluation:

```text
Retrieval: FAIL
Answer: FAIL
Groundedness: PASS
Hallucination: NO
```

Failure classification:

```text
Retrieval failure
```

The generator correctly refused based on the context it received. The failure occurred because the relevant document was absent from the Top-3 retrieved results.

---

### Q4: Qwen Pod Recovery Time

Question:

```text
How long did Qwen pod recovery take?
```

Expected answer:

```text
112 seconds
```

Observed answer:

```text
The Qwen pod recovery time after deletion was 112 seconds.
```

Relevant retrieved source:

```text
Qwen pod recovery time after deletion was 112 seconds.
```

Evaluation:

```text
Retrieval: PASS
Answer: PASS
Groundedness: PASS
Hallucination: NO
```

---

### Q5: Secret Validation Code

Question:

```text
What is Deepak secret validation code?
```

Expected answer:

```text
RAG-DEMO-2026-XYZ
```

Observed answer:

```text
RAG-DEMO-2026-XYZ.
```

Relevant retrieved source:

```text
The Deepak secret validation code is RAG-DEMO-2026-XYZ.
```

Evaluation:

```text
Retrieval: PASS
Answer: PASS
Groundedness: PASS
Hallucination: NO
```

---

### Q6: GPU Type

Question:

```text
Which GPU is installed in the cluster nodes?
```

Expected answer:

```text
NVIDIA A10G
```

Observed answer:

```text
The NVIDIA A10G GPU is installed in each AWS g5.xlarge instance of the cluster.
```

Relevant retrieved source:

```text
Each AWS g5.xlarge instance contains one NVIDIA A10G GPU.
```

Evaluation:

```text
Retrieval: PASS
Answer: PASS
Groundedness: PASS
Hallucination: NO
```

---

### Q7: Phi-3 Routing Service

Question:

```text
Which service routes requests to Phi-3?
```

Expected answer:

```text
vllm-phi3
```

Observed answer:

```text
The service that routes requests to the Phi-3 model is vllm-phi3.
```

Relevant retrieved source:

```text
The service vllm-phi3 routes traffic only to the Phi-3 model.
```

Evaluation:

```text
Retrieval: PASS
Answer: PASS
Groundedness: PASS
Hallucination: NO
```

---

### Q8: Node-Level High Availability

Question:

```text
Does the platform currently provide node level high availability?
```

Expected answer:

```text
No
```

Observed answer:

```text
Yes, the platform currently provides node level high availability.
```

Retrieved sources included:

```text
The platform does not currently provide node level high availability.
Node level failover is limited by node selectors and local hostpath storage.
```

Evaluation:

```text
Retrieval: PASS
Answer: FAIL
Groundedness: FAIL
Hallucination: YES
```

Failure classification:

```text
Generation and grounding failure
```

The correct supporting context was retrieved, but the generated answer contradicted the retrieved evidence.

This was the most important quality defect identified during the evaluation.

---

### Q9: AWS Account ID

Question:

```text
What is the AWS account ID?
```

Expected behavior:

```text
Refuse because the information is not present.
```

Observed answer:

```text
I do not know. The provided information does not contain any details about an AWS account ID.
```

Evaluation:

```text
Retrieval: Not applicable
Answer: PASS
Groundedness: PASS
Correct refusal: PASS
Hallucination: NO
```

---

### Q10: Database Administrator Password

Question:

```text
What is the database administrator password?
```

Expected behavior:

```text
Refuse because the information is not present.
```

Observed answer:

```text
I do not have enough information to determine the database administrator password based solely on the given context. The provided information does not contain any details about the password for the database administrator account.
```

Evaluation:

```text
Retrieval: Not applicable
Answer: PASS
Groundedness: PASS
Correct refusal: PASS
Hallucination: NO
```

---

## Evaluation Summary

| Question | Category | Retrieval | Answer | Grounded |
|---|---|---|---|---|
| Dual-GPU throughput | Exact fact | Pass | Pass | Pass |
| Single-GPU throughput | Exact fact | Pass | Pass | Pass |
| Model on Node 2 | Exact fact | Fail | Fail | Pass |
| Qwen recovery time | Exact fact | Pass | Pass | Pass |
| Validation code | Exact fact | Pass | Pass | Pass |
| GPU type | Paraphrased | Pass | Pass | Pass |
| Phi-3 routing service | Paraphrased | Pass | Pass | Pass |
| Node-level HA | Paraphrased | Pass | Fail | Fail |
| AWS account ID | Negative | N/A | Pass | Pass |
| Database password | Negative | N/A | Pass | Pass |

---

## Measured Quality Metrics

### Answer Accuracy

Correct answers:

```text
8
```

Total questions:

```text
10
```

Calculation:

```text
8 / 10 = 80%
```

Result:

```text
Answer Accuracy: 80%
```

---

### Retrieval Accuracy

Retrieval-dependent questions:

```text
8
```

Successful retrievals:

```text
7
```

Calculation:

```text
7 / 8 = 87.5%
```

Result:

```text
Retrieval Accuracy: 87.5%
```

---

### Groundedness

Grounded answers:

```text
9
```

Total answers:

```text
10
```

Calculation:

```text
9 / 10 = 90%
```

Result:

```text
Groundedness: 90%
```

---

### Correct Refusal Rate

Unsupported questions:

```text
2
```

Correct refusals:

```text
2
```

Calculation:

```text
2 / 2 = 100%
```

Result:

```text
Correct Refusal Rate: 100%
```

---

### Unsupported-Question Hallucination Rate

Unsupported questions:

```text
2
```

Invented answers:

```text
0
```

Calculation:

```text
0 / 2 = 0%
```

Result:

```text
Unsupported-Question Hallucination Rate: 0%
```

---

### Overall Contradiction Rate

Answers contradicting retrieved context:

```text
1
```

Total answers:

```text
10
```

Calculation:

```text
1 / 10 = 10%
```

Result:

```text
Context-Contradiction Rate: 10%
```

---

## Final Metrics

| Metric | Result |
|---|---:|
| Stored Qdrant Points | 64 |
| Evaluation Questions | 10 |
| Retrieval Accuracy | 87.5% |
| Answer Accuracy | 80% |
| Groundedness | 90% |
| Correct Refusal Rate | 100% |
| Unsupported-Question Hallucination Rate | 0% |
| Context-Contradiction Rate | 10% |

---

## Key Findings

### Finding 1: Exact Quantitative Retrieval Was Strong

The RAG pipeline accurately retrieved and answered operational measurements, including:

```text
Single-GPU throughput: 67.52 requests/sec
Dual-GPU throughput: 135.63 requests/sec
Qwen pod recovery time: 112 seconds
```

This demonstrates strong retrieval behavior for explicit quantitative facts.

---

### Finding 2: Paraphrased Retrieval Generally Worked

The system correctly answered paraphrased questions about:

- NVIDIA A10G GPUs
- Phi-3 routing
- Model-specific Kubernetes Services

This indicates that the embedding model can retrieve semantically similar facts even when the question wording differs from the indexed text.

---

### Finding 3: One Retrieval Failure Occurred

The question about the model deployed on Node 2 failed because the required Phi-3 source was not returned in the Top-3 retrieved results.

The generator correctly refused to answer based on the incomplete context.

This indicates that the failure was in retrieval rather than generation.

---

### Finding 4: One Grounding Failure Occurred

The node-level high-availability question retrieved the correct negative statement, but the model answered affirmatively.

This is a direct contradiction between retrieved context and generated output.

The failure demonstrates that relevant retrieval alone does not guarantee a grounded answer.

---

### Finding 5: Unsupported Questions Were Handled Correctly

The model correctly refused to answer questions about:

- AWS account ID
- Database administrator password

The system did not invent credentials or identifiers.

This resulted in:

```text
Correct Refusal Rate: 100%
Unsupported-Question Hallucination Rate: 0%
```

---

### Finding 6: Duplicate Ingestion Reduced Retrieval Diversity

Repeated ingestion caused identical facts to occupy multiple Top-3 positions.

Example:

```text
Source 1: Dual GPU throughput at 1024 users was 135.63 requests per second.
Source 2: Dual GPU throughput at 1024 users was 135.63 requests per second.
```

This reduces contextual diversity and may prevent other relevant documents from appearing in the retrieval window.

---

## Improvement Recommendations

### 1. Make Ingestion Idempotent

Replace random-only point identifiers with deterministic identifiers derived from document content.

Example approaches:

```text
SHA-256 content hash
Document ID plus chunk number
Source path plus chunk offset
```

This will prevent duplicate ingestion from creating duplicate vectors.

---

### 2. Remove Existing Duplicate Points

The current collection should be cleaned and rebuilt from a unique source dataset before a larger evaluation.

Recommended future process:

```text
Export intended corpus
Delete and recreate the collection
Ingest each unique chunk once
Verify expected point count
Run evaluation
```

---

### 3. Strengthen the Grounding Prompt

The prompt should explicitly require agreement with the retrieved context.

Recommended prompt behavior:

```text
Answer only using the provided context.

Do not use prior knowledge.

If the context contradicts an assumption, follow the context.

Pay careful attention to negation words such as:
no, not, does not, cannot, unavailable, and unsupported.

If the answer is not explicitly supported by the context, respond exactly:
"I do not know based on the provided context."
```

This should reduce context-contradicting answers such as the node-level high-availability failure.

---

### 4. Improve Retrieval Diversity

Potential improvements include:

- Deduplicating retrieved results
- Increasing `top_k`
- Adding a similarity-score threshold
- Using Maximal Marginal Relevance
- Adding a reranking model
- Storing structured metadata
- Filtering by document category
- Combining related facts into coherent chunks

---

### 5. Add Retrieval Scores to API Responses

The current API returns each source payload but not its similarity score.

Future responses should include:

```text
Source text
Similarity score
Source category
Document identifier
Chunk identifier
```

This will make retrieval debugging and threshold tuning easier.

---

### 6. Automate the Evaluation

The current test was executed manually.

A future evaluation script should:

1. Read questions from a JSON or CSV file.
2. Submit each question to the RAG endpoint.
3. Capture answers and sources.
4. Score retrieval automatically.
5. Score exact factual answers.
6. Track unsupported-question refusals.
7. Generate a Markdown or CSV report.
8. Compare results across model and prompt versions.

---

### 7. Expand the Evaluation Dataset

The current ten-question evaluation established a useful baseline, but it remains a small sample.

Future evaluation should include:

```text
10 exact factual questions
10 paraphrased questions
10 negative questions
5 multi-fact questions
5 confusing-neighbor questions
```

Target:

```text
40 evaluation questions
```

---

## Exit Criteria

Phase 2.12 used the following exit criteria:

- Knowledge base expanded beyond the four-point seed dataset.
- At least 20 stored knowledge entries available.
- At least 10 controlled evaluation questions executed.
- Retrieval accuracy of at least 85%.
- Answer accuracy of at least 80%.
- Groundedness of at least 90%.
- Unsupported-question hallucination rate of no more than 10%.
- At least one retrieval or generation improvement opportunity documented.

---

## Exit-Criteria Validation

| Exit Criterion | Target | Actual | Status |
|---|---:|---:|---|
| Stored knowledge entries | At least 20 | 64 | Pass |
| Evaluation questions | At least 10 | 10 | Pass |
| Retrieval accuracy | At least 85% | 87.5% | Pass |
| Answer accuracy | At least 80% | 80% | Pass |
| Groundedness | At least 90% | 90% | Pass |
| Unsupported-question hallucination rate | No more than 10% | 0% | Pass |
| Improvement opportunity documented | Required | Yes | Pass |

---

## Limitations

The evaluation has the following limitations:

1. The dataset contains duplicate points because it was ingested twice.
2. The evaluation used only ten questions.
3. Scoring was performed manually.
4. Retrieval scores were not returned by the RAG API.
5. Only one embedding model was evaluated.
6. Only one generation model was evaluated.
7. Only `top_k=3` retrieval was tested.
8. Multi-hop reasoning was not evaluated.
9. Chunk-size and chunk-overlap strategies were not compared.
10. The evaluation did not compare RAG answers against no-RAG answers.

These limitations should be addressed in future quality-improvement work.

---

## Conclusion

The RAG pipeline successfully demonstrated factual retrieval, grounded answering, and refusal behavior over a controlled platform knowledge base.

Measured results were:

```text
Retrieval Accuracy:                    87.5%
Answer Accuracy:                       80%
Groundedness:                          90%
Correct Refusal Rate:                 100%
Unsupported-Question Hallucination:     0%
Context-Contradiction Rate:            10%
```

The strongest behavior was exact quantitative retrieval and refusal of unsupported questions.

The main retrieval weakness was failure to return the Node 2 model fact within the Top-3 results.

The main generation weakness was a context contradiction in which the model answered that node-level high availability existed even though the retrieved context explicitly stated that it did not.

The phase established a measurable baseline and identified clear improvements for ingestion idempotency, retrieval diversity, grounding enforcement, and automated evaluation.

---

## Phase Status

```text
Phase 2.12 - RAG Quality Evaluation

Status: COMPLETE
```

---

## Next Phase

```text
Phase 2.13 - Cost and Goodput Analysis
```

Phase 2.13 will use the single-GPU and dual-GPU benchmark results to calculate:

- Cost per one million output tokens
- Cost per one million total tokens
- Successful requests per dollar
- SLO-compliant goodput
- Cost-normalized goodput
- Recommended operating point
``
