# ULTRARENTABLE — LIVE CONTROL STATE

## Current authority
- `CURRENT_PHASE`: 02
- `PHASE_STATUS`: DIRECT_RECOVERY
- `PROGRAM_STATUS`: IN_PROGRESS
- `EXECUTION_OWNER`: EXTERNAL_REVIEWER
- `ACTIVE_ORDER_ID`: DIRECT-R0-BOOTSTRAP
- `ACTIVE_ORDER_FILE`: `02_CURRENT_ORDER.md`
- `ACTIVE_DISPATCH_ID`: `DIRECT-20260826-R0-001`
- `LAST_COMPLETED_REVIEWED_ORDER`: AG2-P02-FINAL-001
- `LAST_EXTERNAL_REVIEW`: `04_REVIEW_AG2-P02-FINAL-001.md` (`RECOVERY_REQUIRED`)
- `NEXT_ORDER`: R1 LOCKED until R0 is actually fixed and verified

## Authority model
GitHub `origin/main` is the source of truth for both code and control state.

The external reviewer may modify the repository directly. Antigravity is not required to execute the recovery and must not invent or select work. The watcher, if present, is only a notification mechanism.

## Current objective
Finish the recovery sequence from R0 onward, one block at a time, with direct repository repair, reproducible verification, and evidence.

## STRICT SCOPE
Only `DIRECT-R0-BOOTSTRAP` is active. No R1, Phase 03, Discovery, Gates, Research, Meta-Strategy, ULTRA or FONDEO work may be considered complete before R0 is closed.

## Advance rule
After the reviewer verifies R0, the reviewer will directly publish the next repair block in these files. No automatic phase advancement exists.

## Evidence rule
No claim of completion without exact source revision, tests/commands, observed result, and provenance.
