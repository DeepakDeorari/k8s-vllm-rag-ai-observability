# Phase 2.7 - Capacity Planning

## Overview

This document estimates platform capacity using benchmark results collected during Phase 2.2.

The objective is to determine scaling boundaries and future infrastructure requirements.

---

# Environment

- AWS g5.xlarge
- Single NVIDIA A10G GPU
- MicroK8s
- vLLM
- Qwen/Qwen2.5-1.5B-Instruct

---

# Observed Capacity

## Benchmark Results

| Concurrency | Requests/sec |
|-------------|--------------|
| 1 | 0.43 |
| 2 | 2.39 |
| 4 | 4.76 |
| 8 | 9.30 |
| 16 | 18.05 |
| 32 | 32.22 |
| 1024 | 67.52 |

---

# Scheduler Capacity

Observed during overload testing:

- Running Requests: ~254
- Waiting Requests: ~767

Observation:

vLLM actively processed approximately 250 requests simultaneously while queuing excess demand.

---

# Operating Regions

## Normal Operation

Concurrency:

1-32

Characteristics:

- SLO compliant
- Low queue time
- Stable TTFT
- Stable latency

---

## High Load

Concurrency:

64-256

Characteristics:

- Increased throughput
- Acceptable latency growth
- Queue buildup begins

---

## Overload

Concurrency:

512-1024

Characteristics:

- Significant queue buildup
- Elevated TTFT
- Elevated latency
- No request failures

---

# Capacity Conclusions

Current platform comfortably supports:

- Interactive workloads
- Development workloads
- Small internal teams

Future production scaling should occur before queue depth exceeds 100 waiting requests.

---

# Recommended Scaling Point

Scale before:

- Waiting Requests > 100
- P95 Queue Time > 1 sec
- P95 TTFT > 2 sec

This avoids entering the overload region.
