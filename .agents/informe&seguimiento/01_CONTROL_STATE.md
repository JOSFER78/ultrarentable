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
- `NEXT_ORDER`: LOCKED

## Watcher contract

Antigravity's watcher checks `.agents/informe&seguimiento/` approximately every 3 minutes.

A new command is actionable only when:

- `order_id` is newer than the last acknowledged order;
- `status: ISSUED`;
- `target_phase` equals `CURRENT_PHASE`;
- the order file is the single active order.

## Authority restriction

Antigravity and all subagents must NOT modify:

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

No automatic phase advancement exists.
