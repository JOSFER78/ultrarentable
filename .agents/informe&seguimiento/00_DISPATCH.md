# ULTRARENTABLE — ACTIVE DISPATCH

## ACTIVE DISPATCH
```yaml
dispatch_id: AG2-DISPATCH-20260825-2200-P02-008
order_id: AG2-P02-008
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/10_ORDER_AG2-P02-008.md
target_phase: 02
phase_status: FINAL_CLOSURE
status: ISSUED
issued_at_utc: 2026-08-25T20:00:00Z
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

This is the FINAL CLOSURE ORDER for Phase 02. Do not interpret the master plan as authorization to advance.

## DELIVERY
Execute only `AG2-P02-008`. Follow the mandatory final-closure audit, multi-agent verification and evidence requirements in `10_ORDER_AG2-P02-008.md`. On completion push scoped code/tests/evidence/handoff to `origin/main`, verify remote SHA, then STOP.

## ABSOLUTE RULES
ZERO-SIMULATION = ON
ZERO-FORCING = ON
REAL-ONLY = ON
ZERO-LOOKAHEAD = ON

A green test suite is not sufficient for Phase 02 closure. Any critical unproven claim must remain BLOCKED. Antigravity must not create or start Phase 03.
