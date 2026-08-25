# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 01
- `PHASE_STATUS`: REWORK
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P01-002
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P01-001
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P01-001.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P01-001.md` (`REWORK`)
- `NEXT_ORDER`: `PHASE 02 LOCKED`

## Watcher contract

Antigravity's watcher checks `.agents/informe&seguimiento/` approximately every 3 minutes.

An actionable dispatch requires:
- a NEW `dispatch_id` compared with the persisted watcher value, or an existing dispatch with no durable proof that it was ever started;
- `status: ISSUED`;
- `target_phase` equals `CURRENT_PHASE`;
- `ACTIVE_ORDER_ID` matches the dispatched `order_id`;
- the order is the single active order.

## Automatic execution rule

When those conditions are met, Antigravity must automatically start the order on that watcher cycle. No manual user prompt is required.

A dispatch may be marked processed only after durable proof-of-start exists. A stale local acknowledgement without proof-of-start must not suppress execution.

## STRICT PHASE SCOPE

Antigravity MUST execute only the active order and only the active phase. Out-of-scope findings are `DEFERRED_TO_FUTURE_ORDER` unless proven to be a direct blocker.

## GitHub synchronization rule

At the end of every order Antigravity must push implementation, tests, evidence, handoff and final SHA to `origin/main`. Local-only completion is not completion.

## Current transition reason

AG2-P01-001 completed a first implementation of Dataset Chain of Custody, but external audit found fabricated partition hashes and provenance fallbacks in `services/data/dataset_registry.py`. The phase therefore remains in REWORK.

Active corrective order: `AG2-P01-002`.

Phase 02 remains locked until Phase 01 rework is independently verified and explicitly released by the external reviewer.
