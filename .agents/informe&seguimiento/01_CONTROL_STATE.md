# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 00
- `PHASE_STATUS`: READY
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P00-001
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `LAST_ACKNOWLEDGED_ORDER`: NONE
- `LAST_HANDOFF`: NONE
- `LAST_EXTERNAL_REVIEW`: NONE
- `NEXT_ORDER`: `06_PHASE_01_ORDER_LOCKED.md` (LOCKED)

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

## GitHub synchronization rule

The repository on GitHub is the shared control surface.

At the end of every phase/order Antigravity must ensure that the implementation state, tests, handoff, evidence references, control-state changes and final commit SHA are published to GitHub before declaring `READY_FOR_REVIEW`.

Local-only completion is NOT completion.

If an artifact cannot be committed to GitHub, the handoff must mark it explicitly as external/unversioned and explain why. It must never claim full reproducibility from GitHub if GitHub does not contain or identify the required evidence.

## Authority restriction

Antigravity and all subagents must NOT modify without an external issued order:

- `CURRENT_PHASE`
- `PHASE_STATUS`
- `PROGRAM_STATUS`
- `ACTIVE_ORDER_ID`
- `NEXT_ORDER`
- external review decisions

They may update only their handoff/evidence files and scoped implementation files.

## Phase transition

Only the external reviewer may move:

`READY -> IN_PROGRESS -> EVIDENCE_READY -> UNDER_REVIEW -> APPROVED`

or:

`UNDER_REVIEW -> REJECTED | BLOCKED | REDESIGN`

No automatic approval exists.

After external `APPROVED`, the reviewer publishes the next order as `ISSUED` and updates the authoritative control fields. The next cron cycle then starts the new order automatically.
