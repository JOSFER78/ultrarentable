# ULTRARENTABLE — ACTIVE DISPATCH

## ACTIVE DISPATCH
```yaml
dispatch_id: AG2-DISPATCH-20260825-1815-P02-003
order_id: AG2-P02-003
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/09_ORDER_AG2-P02-003.md
target_phase: 02
phase_status: REWORK
status: ISSUED
issued_at_utc: 2026-08-25T16:15:00Z
execution_surface: origin/main
scope_mode: STRICT_SINGLE_PHASE
zero_simulation: true
zero_forcing: true
```

## EXECUTION TRIGGER
The watcher runs approximately every 3 minutes.

Execute only when ALL are true:
1. this `dispatch_id` is newer than its persisted last processed dispatch;
2. `status == ISSUED`;
3. `order_id == ACTIVE_ORDER_ID`;
4. `target_phase == CURRENT_PHASE`;
5. `02_CURRENT_ORDER.md` has the same order_id and `status: ISSUED`;
6. no other dispatch is running.

A completed previous handoff is not a reason to suppress a NEW dispatch. A new dispatch is the only reason to start new work.

If no new dispatch exists: `NO NEW DISPATCH — STANDBY` and stop that watcher iteration.

## DELIVERY
The active order must be executed only once. After completion Antigravity must push all scoped code/tests/evidence/control updates/handoff to `origin/main`, verify the remote SHA and STOP. The next work can only start after the external reviewer publishes a NEW dispatch_id.

## ABSOLUTE RULES
ZERO-SIMULATION = ON
ZERO-FORCING = ON
REAL-ONLY = ON
ZERO-LOOKAHEAD = ON

Timeout, missing result, stale evidence, missing dataset, missing exit code or unverified runtime trace is never PASS.
