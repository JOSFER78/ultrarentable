# ULTRARENTABLE — ACTIVE DISPATCH

## ACTIVE DISPATCH
```yaml
dispatch_id: AG2-DISPATCH-20260825-1900-P02-004
order_id: AG2-P02-004
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/10_ORDER_AG2-P02-004.md
target_phase: 02
phase_status: REWORK
status: ISSUED
issued_at_utc: 2026-08-25T17:00:00Z
execution_surface: origin/main
scope_mode: STRICT_SINGLE_PHASE
zero_simulation: true
zero_forcing: true
```

## EXECUTION TRIGGER
The watcher reads this file from GitHub `JOSFER78/ultrarentable` branch `main`.
A NEW `dispatch_id` is the only event that authorizes new work.
Validate against `01_CONTROL_STATE.md` and `02_CURRENT_ORDER.md` before auto-start.

## DELIVERY
Execute only `AG2-P02-004`. On completion push scoped code/tests/evidence/handoff to `origin/main`, verify remote SHA, then STOP.

## ABSOLUTE RULES
ZERO-SIMULATION = ON
ZERO-FORCING = ON
REAL-ONLY = ON
ZERO-LOOKAHEAD = ON
