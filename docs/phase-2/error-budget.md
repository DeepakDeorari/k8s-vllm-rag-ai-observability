# Phase 2.3 - Error Budget

## Availability SLO

99.5%

## Error Budget

0.5%

## Monthly Budget

30 days

Allowed outage:

```text
216 minutes/month
```

or:

```text
3.6 hours/month
```

---

# Request Error Budget

Request Success SLO:

99%

Allowed Failure Rate:

1%

Examples:

100,000 requests/month

Allowed failures:

```text
1,000 requests
```

---

# Error Budget Consumption

Budget is consumed by:

- HTTP 5xx errors
- Timeouts
- Failed inference requests
- Invalid model responses

---

# Not Counted Against Budget

- Planned maintenance
- Benchmark testing
- Controlled failure engineering experiments
