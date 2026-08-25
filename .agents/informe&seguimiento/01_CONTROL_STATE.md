# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 01
- `PHASE_STATUS`: READY
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P01-001
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P00-002
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P00-002.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P00-002.md` (`APPROVED_FOR_NEXT_PHASE`)
- `NEXT_ORDER`: `PHASE 02 LOCKED`

## Watcher contract

Antigravity's watcher checks `.agents/informe&seguimiento/` approximately every 3 minutes.

A new command is actionable only when:

- `order_id` is newer than the last acknowledged order;
- `status: ISSUED`;
- `target_phase` equals `CURRENT_PHASE`;
- the order file is the single active order.

A locked future order is informational only and MUST NOT be executed.

## Automatic execution rule

When the watcher detects a newer valid `ISSUED` order, Antigravity must automatically start that order on that watcher cycle. No manual user prompt is required.

The watcher is the trigger; `ISSUED` control state is the authorization to execute the currently active phase.

## STRICT PHASE SCOPE

Antigravity MUST execute only the active order and only the active phase.

It may inspect the full repository for context and dependencies, but it may not implement future phases or unrelated cleanup. Out-of-scope findings must be recorded as `DEFERRED_TO_FUTURE_ORDER`.

## GitHub synchronization rule

At the end of every order Antigravity must ensure that implementation state, tests, handoff, evidence references, control-state changes and final commit SHA are published to GitHub before declaring `READY_FOR_REVIEW`.

Local-only completion is NOT completion.

## Authority restriction

Antigravity and subagents must NOT modify without an external issued order:

- `CURRENT_PHASE`
- `PHASE_STATUS`
- `PROGRAM_STATUS`
- `ACTIVE_ORDER_ID`
- `NEXT_ORDER`
- external review decisions

## Phase transition

The external reviewer may issue:

`READY -> IN_PROGRESS -> EVIDENCE_READY -> UNDER_REVIEW`

or adaptive rework:

`REWORK -> IN_PROGRESS -> EVIDENCE_READY -> UNDER_REVIEW`

After review:

`UNDER_REVIEW -> APPROVED_FOR_NEXT_PHASE | REWORK | BLOCKED | REDESIGN`

There is no user waiting gate. The external reviewer issues the next concrete order and the next watcher cycle executes it automatically.

## Current transition reason

AG2-P00-002 remediated the foundational P0/P1 defects sufficiently to leave Phase 00. The active work is now Phase 01 Data & Dataset Chain of Custody.

Phase 01 must finish before Phase 02 becomes actionable.
