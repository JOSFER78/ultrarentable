# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority

- `CURRENT_PHASE`: 00
- `PHASE_STATUS`: REWORK
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P00-002
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P00-001
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P00-001.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P00-001.md` (`REWORK`)
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

The external reviewer may issue:

`READY -> IN_PROGRESS -> EVIDENCE_READY -> UNDER_REVIEW`

or adaptive rework:

`REWORK -> IN_PROGRESS -> EVIDENCE_READY -> UNDER_REVIEW`

After review:

`UNDER_REVIEW -> APPROVED | REWORK | BLOCKED | REDESIGN`

There is no automatic approval. There is also no user waiting gate: the external reviewer issues the next concrete order and the next watcher cycle executes it automatically.

## Current rework reason

AG2-P00-001 established the forensic baseline but exposed foundational P0 defects. AG2-P00-002 is the active corrective order. Phase 01 remains locked until these foundational defects are addressed or explicitly superseded by an evidence-based redesign.
