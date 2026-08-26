# ULTRARENTABLE — ACTIVE DISPATCH

## ACTIVE DISPATCH
```yaml
dispatch_id: AG2-DISPATCH-20260826-1800-R0-001
order_id: AG2-R0-BOOTSTRAP
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/14_ORDER_R0_BOOTSTRAP.md
target_phase: 02
phase_status: RECOVERY_VALIDATION
status: ISSUED
issued_at_utc: 2026-08-26T18:00:00Z
execution_surface: origin/main
scope_mode: STRICT_SINGLE_REPAIR
zero_simulation: true
zero_forcing: true
zero_lookahead: true
```

## EXECUTION TRIGGER
The watcher must read this file from GitHub `JOSFER78/ultrarentable` branch `main`.
A NEW `dispatch_id` is the only event that authorizes new work.
Validate exact equality against `01_CONTROL_STATE.md` and `02_CURRENT_ORDER.md` before auto-start.

## DELIVERY
Execute only `AG2-R0-BOOTSTRAP`. Use the mandatory subagents and evidence ledger in `14_ORDER_R0_BOOTSTRAP.md`. On completion, push scoped code/tests/evidence/handoff to `origin/main`, verify the exact remote SHA, then STOP.

## ABSOLUTE RULES
ZERO-SIMULATION = ON
ZERO-FORCING = ON
REAL-ONLY = ON
ZERO-LOOKAHEAD = ON

A green test suite alone is insufficient. Clean install, typecheck, build, localhost HTTP, backend startup and provenance checks must be evidenced.
