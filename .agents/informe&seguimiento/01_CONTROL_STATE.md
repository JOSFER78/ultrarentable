# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority
- `CURRENT_PHASE`: 02
- `PHASE_STATUS`: FINAL_CLOSURE
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-P02-008
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `AG2-DISPATCH-20260825-2200-P02-008`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P02-007
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P02-007.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P02-007.md` (`FINAL_PHASE_CLOSE_ORDER`)
- `NEXT_ORDER`: `PHASE 03 LOCKED`

## Watcher contract
Read the three control files from GitHub `origin/main` every watcher cycle. Auto-start only when the dispatch is NEW, `status: ISSUED`, target phase equals current phase, active order matches, and `02_CURRENT_ORDER.md` is the same `ISSUED` order.

## Adaptive phase model
The external reviewer chooses `REWORK`, `SUBPHASE`, `REDESIGN`, `BLOCKED`, `NEXT_PHASE`, `SPLIT`, `MERGE` or `ABANDON` after inspecting the delivered state.

Antigravity never chooses the next order.

## STRICT SCOPE
Only `AG2-P02-008` may be executed now. It is the final closure order of Phase 02. Out-of-scope findings are deferred unless they directly block closure.

## GitHub synchronization
The complete scoped result must be committed and pushed to `origin/main`, with exact remote SHA recorded in the handoff, before `READY_FOR_REVIEW` and STOP.

## Current transition
`AG2-P02-007` was delivered as `READY_FOR_REVIEW` after closing the principal behavioral defects in BOTH semantics, explicit unsupported semantics, and production execution-boundary tracing.

Active final closure order: `AG2-P02-008`.

Phase 03 remains locked until the external reviewer explicitly approves Phase 02.
