# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 01
- `PHASE_STATUS`: REWORK
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P01-004
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `AG2-DISPATCH-20260825-1510-P01-004`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P01-003
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P01-003.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P01-003.md` (`REWORK`)
- `NEXT_ORDER`: `PHASE 02 LOCKED`

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

The program is NOT a rigid linear sequence. After every delivered order, the external reviewer may issue:

- `SAME_PHASE_REWORK` → e.g. `01.REWORK.01`, `01.REWORK.02`;
- `SUBPHASE` → e.g. `01.1`, `01.2`;
- `REDESIGN`;
- `BLOCKED` resolution;
- `NEXT_PHASE` → e.g. `02.0`;
- `SPLIT`, `MERGE`, or `ABANDON` where evidence justifies it.

Antigravity never chooses the next phase. It only executes the currently issued order.

## STRICT PHASE SCOPE

Antigravity MUST execute only the active order and only the active phase/subphase. Out-of-scope findings are `DEFERRED_TO_FUTURE_ORDER` unless proven to be a direct blocker.

## GitHub synchronization rule

At the end of every order Antigravity must push implementation, tests, evidence, handoff and final SHA to `origin/main`. Local-only completion is not completion.

## Current transition reason

AG2-P01-003 materially improved Phase 01 but external audit found remaining provenance/identity governance gaps: hardcoded runtime alias map, identity mutation before lookup, incomplete manifest/registry self-consistency proof and incomplete exact remote SHA evidence.

Active corrective order: `AG2-P01-004`.

Phase 02 remains locked until Phase 01 rework is independently verified and explicitly released by the external reviewer.
