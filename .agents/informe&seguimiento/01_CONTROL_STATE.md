# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority
- `CURRENT_PHASE`: 02
- `PHASE_STATUS`: RECOVERY_VALIDATION
- `PROGRAM_STATUS`: IN_PROGRESS
- `ACTIVE_ORDER_ID`: AG2-R0-BOOTSTRAP
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `AG2-DISPATCH-20260826-1800-R0-001`
- `LAST_ACKNOWLEDGED_ORDER`: AG2-P02-FINAL-001
- `LAST_HANDOFF`: `03_HANDOFF_AG2-P02-FINAL-001.md`
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P02-FINAL-001.md` (`RECOVERY_REQUIRED`)
- `NEXT_ORDER`: R1 LOCKED until R0 evidence is reviewed

## Watcher contract
Read only from GitHub `JOSFER78/ultrarentable` branch `main`:
- `00_DISPATCH.md`
- `01_CONTROL_STATE.md`
- `02_CURRENT_ORDER.md`

A NEW `dispatch_id` is the only trigger for new work. Antigravity executes only the order named by all three control files.

## Adaptive model
The external reviewer decides the next repair block after reviewing real code and evidence. Antigravity never creates or selects the next order.

## STRICT SCOPE
Only `AG2-R0-BOOTSTRAP` may be executed now. No R1, Phase 03, Discovery, Gates, Research, Meta-Strategy, ULTRA or FONDEO work.

## NO ADVANCE
`CURRENT_PHASE` remains 02 until recovery is explicitly closed by the external reviewer.
