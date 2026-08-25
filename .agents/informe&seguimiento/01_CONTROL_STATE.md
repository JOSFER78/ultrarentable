# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 02
- `PHASE_STATUS`: REWORK
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P02-002
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `AG2-DISPATCH-20260825-1730-P02-002`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P02-001
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P02-001.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P02-001.md` (`REWORK`)
- `NEXT_ORDER`: `PHASE 03 LOCKED`

## Watcher contract
Antigravity's watcher checks `.agents/informe&seguimiento/` approximately every 3 minutes.

An actionable dispatch requires:
- a NEW `dispatch_id` compared with the persisted watcher value;
- `status: ISSUED`;
- `target_phase` equals `CURRENT_PHASE`;
- `ACTIVE_ORDER_ID` matches the dispatched `order_id`;
- the order is the single active order.

A dispatch may be marked processed only after durable proof-of-start exists. If a new dispatch exists, the watcher MUST NOT remain in standby merely because a previous dispatch was completed.

## Automatic execution rule
When those conditions are met, Antigravity must automatically start the order on that watcher cycle. No manual user prompt is required.

## Adaptive phase model
The program is NOT a rigid linear sequence. After every delivered order, the external reviewer may issue SAME_PHASE_REWORK, SUBPHASE, REDESIGN, BLOCKED resolution, NEXT_PHASE, SPLIT, MERGE or ABANDON where evidence justifies it.

Antigravity never chooses the next phase. It only executes the currently issued order.

## STRICT PHASE SCOPE
Antigravity MUST execute only the active order and only the active phase/subphase. Out-of-scope findings are `DEFERRED_TO_FUTURE_ORDER` unless proven a direct blocker.

## GitHub synchronization rule
At the end of every order Antigravity must push implementation, tests, evidence, handoff and final SHA to `origin/main`. Local-only completion is not completion.

## Current transition
Phase 02 order `AG2-P02-001` was delivered as `READY_FOR_REVIEW`. External review found incomplete hash identity, insufficient proof of runtime consumption, possible duplicate strategy authorities and silent production defaults.

Active corrective order: `AG2-P02-002` — Canonical Hash Completeness + Runtime Consumption + Single Strategy SSOT + Fail-Closed Defaults.

Phase 03 remains locked until Phase 02 rework is independently verified and explicitly released.
