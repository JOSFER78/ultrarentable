# ULTRARENTABLE — ACTIVE DISPATCH

## ACTIVE DISPATCH
```yaml
dispatch_id: AG2-DISPATCH-20260825-2030-P02-006
order_id: AG2-P02-006
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/11_ORDER_AG2-P02-006.md
target_phase: 02
phase_status: REWORK
status: ISSUED
issued_at_utc: 2026-08-25T18:30:00Z
execution_surface: origin/main
scope_mode: STRICT_SINGLE_PHASE
zero_simulation: true
zero_forcing: true
zero_lookahead: true
```

## EXECUTION TRIGGER
The watcher reads this file from GitHub `JOSFER78/ultrarentable` branch `main`.
A NEW `dispatch_id` is the only event that authorizes new work.
Validate against `01_CONTROL_STATE.md` and `02_CURRENT_ORDER.md` before auto-start.

## DELIVERY
Execute only `AG2-P02-006`. Follow the mandatory step plan and multi-agent evidence requirements in `11_ORDER_AG2-P02-006.md`. On completion push scoped code/tests/evidence/handoff to `origin/main`, verify remote SHA, then STOP.

## ABSOLUTE RULES
ZERO-SIMULATION = ON
ZERO-FORCING = ON
REAL-ONLY = ON
ZERO-LOOKAHEAD = ON

A test passing is not sufficient evidence of semantic support. Unsupported or unproven behavior must fail closed or remain BLOCKED.
