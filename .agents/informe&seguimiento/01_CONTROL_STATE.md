# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority
- `CURRENT_PHASE`: 02
- `PHASE_STATUS`: RECOVERY_VALIDATION
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-RECOVERY-001
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `AG2-DISPATCH-20260826-1745-RECOVERY-001`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P02-FINAL-001
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P02-FINAL-001.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P02-FINAL-001.md` (`RECOVERY_REQUIRED`)
- `NEXT_ORDER`: `PHASE 03 LOCKED`

## Watcher contract
Read the three control files from GitHub `origin/main` every watcher cycle. Auto-start only when the dispatch is NEW, `status: ISSUED`, target phase equals current phase, active order matches, and `02_CURRENT_ORDER.md` is the same `ISSUED` order.

Antigravity executes only the active order. It never decides or creates the next order.

## Adaptive phase model
The external reviewer chooses `REWORK`, `SUBPHASE`, `REDESIGN`, `BLOCKED`, `NEXT_PHASE`, `SPLIT`, `MERGE` or `ABANDON` after inspecting the delivered state.

## STRICT SCOPE
Only `AG2-RECOVERY-001` may be executed now. Out-of-scope findings are deferred unless they directly block this recovery.

## GitHub synchronization
The complete scoped result must be committed and pushed to `origin/main`, with exact remote SHA recorded in the handoff, before `READY_FOR_REVIEW` and STOP.

## NO ADVANCE
Phase 03 remains LOCKED. Antigravity must not change `CURRENT_PHASE` forward or create any Phase 03 order until explicitly dispatched.
