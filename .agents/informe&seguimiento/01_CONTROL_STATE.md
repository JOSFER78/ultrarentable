# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 02
- `PHASE_STATUS`: REWORK
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P02-003
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `AG2-DISPATCH-20260825-1815-P02-003`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P02-002
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P02-002.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P02-002.md` (`REWORK`)
- `NEXT_ORDER`: `PHASE 03 LOCKED`

## Watcher contract
An actionable dispatch requires:
- a NEW `dispatch_id` compared with the persisted watcher value;
- `status: ISSUED`;
- `target_phase` equals `CURRENT_PHASE`;
- `ACTIVE_ORDER_ID` matches the dispatched `order_id`;
- `02_CURRENT_ORDER.md` matches the same order id and is `ISSUED`;
- the order is the single active execution trigger.

A dispatch may be marked processed only after durable proof-of-start exists. A completed previous handoff must never suppress a NEW dispatch.

## Automatic execution
When all conditions are met, Antigravity starts automatically on that watcher cycle. No user prompt is required.

## Adaptive phase model
After each delivered order, the external reviewer may choose `SAME_PHASE_REWORK`, `SUBPHASE`, `REDESIGN`, `BLOCKED`, `NEXT_PHASE`, `SPLIT`, `MERGE` or `ABANDON` based on evidence.

Antigravity never chooses the next phase. It executes only the currently issued order.

## STRICT PHASE SCOPE
Only the active order and target phase/subphase may be modified. Out-of-scope findings are `DEFERRED_TO_FUTURE_ORDER` unless proven to be a direct blocker.

## GitHub synchronization
At the end of every order Antigravity must push code, tests, evidence, handoff and allowed control updates to `origin/main`, verify the exact remote SHA, then STOP.

## Current transition
`AG2-P02-002` was delivered as `READY_FOR_REVIEW`. External audit found remaining runtime-semantic and production-trace gaps.

Active corrective order: `AG2-P02-003`.

Phase 03 remains locked until Phase 02 is independently verified and explicitly released.
