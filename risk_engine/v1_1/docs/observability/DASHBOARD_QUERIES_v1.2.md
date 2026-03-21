# Observability Dashboard Queries — v1.2

This document defines canonical dashboard queries for
FAILED.UNKNOWN and edge_case observability.

All queries are derived from:
- terminal_total counter
- DECIDED → FAILED terminal transitions
- v1.2 Constitution reason_code taxonomy

---

## 1. FAILED.UNKNOWN Ratio (15m window)

```promql
sum(
  increase(
    terminal_total{
      terminal_state="FAILED",
      reason_code="FAILED.UNKNOWN"
    }[15m]
  )
)
/
clamp_min(
  sum(
    increase(
      terminal_total{
        terminal_state="FAILED"
      }[15m]
    )
  ),
  1
)

topk(
  10,
  sum by (reason_code) (
    increase(
      terminal_total{
        terminal_state="FAILED"
      }[1h]
    )
  )
)

sum(
  increase(
    terminal_total{
      terminal_state="FAILED",
      reason_code="FAILED.UNKNOWN"
    }[24h]
  )
)
/
clamp_min(
  sum(
    increase(
      terminal_total{
        terminal_state="FAILED"
      }[24h]
    )
  ),
  1
)

- alert: FailedUnknownRatioWarning
  expr: |
    (
      sum(increase(terminal_total{terminal_state="FAILED",reason_code="FAILED.UNKNOWN"}[15m]))
      /
      sum(increase(terminal_total{terminal_state="FAILED"}[15m]))
    ) > 0.01
    and
    sum(increase(terminal_total{terminal_state="FAILED"}[15m])) >= 100
  for: 45m   # 3 × 15m windows
  labels:
    severity: warning
  annotations:
    summary: "FAILED.UNKNOWN ratio > 1%"
    runbook: "docs/observability/FAILED_UNKNOWN_ALERTING_GUIDE_v1.2.md"

- alert: FailedUnknownRatioCritical
  expr: |
    (
      sum(increase(terminal_total{terminal_state="FAILED",reason_code="FAILED.UNKNOWN"}[1h]))
      /
      sum(increase(terminal_total{terminal_state="FAILED"}[1h]))
    ) > 0.03
    and
    sum(increase(terminal_total{terminal_state="FAILED"}[1h])) >= 300
  for: 1h
  labels:
    severity: critical

(
  sum:terminal_total{terminal_state:FAILED,reason_code:FAILED.UNKNOWN}.rollup(sum, 900)
  /
  sum:terminal_total{terminal_state:FAILED}.rollup(sum, 900)
)
AND
sum:terminal_total{terminal_state:FAILED}.rollup(sum, 900) > 100









