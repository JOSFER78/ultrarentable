# ULTRARENTABLE — CONTROL STATE

**Control system:** `informes/00_ADAPTIVE_IMPLEMENTATION_CONTROL.md`
**Master plan:** `informes/01_ADAPTIVE_MASTER_PLAN.md`
**Execution runbook:** `informes/02_ANTIGRAVITY_PHASE_RUNBOOK.md`

## Current state

- `CURRENT_PHASE`: `00`
- `PHASE_STATUS`: `READY`
- `PROGRAM_STATUS`: `IN_PROGRESS`
- `APPROVAL_STATUS`: `NOT_REVIEWED`
- `LAST_EXTERNAL_REVIEW`: `NONE`
- `LAST_APPROVED_PHASE`: `NONE`
- `NEXT_PHASE`: `LOCKED`
- `CONTROL_UPDATED_AT`: `2026-08-25T11:00:00+02:00`
- `CONTROL_COMMIT`: created by adaptive-control initialization

## Important baseline warning

Existing repository documents are not accepted as proof of present state. `AUDIT_FINAL_REAL_ONLY.md` is historical evidence and was followed by additional certification-related commits. The current program therefore requires a fresh baseline from the current executable repository state.

## Phase authority

Antigravity may work only on `PHASE 00` until an external reviewer changes this file.

Do not edit these control fields during implementation:

- `CURRENT_PHASE`
- `PHASE_STATUS`
- `PROGRAM_STATUS`
- `APPROVAL_STATUS`
- `LAST_EXTERNAL_REVIEW`
- `LAST_APPROVED_PHASE`
- `NEXT_PHASE`

## Allowed phase transitions

`READY -> IN_PROGRESS -> EVIDENCE_PENDING -> UNDER_REVIEW`

Only external review may transition:

`UNDER_REVIEW -> APPROVED`
`UNDER_REVIEW -> REJECTED`
`UNDER_REVIEW -> BLOCKED`
`UNDER_REVIEW -> REDESIGN`

Only after `APPROVED` may a new phase instruction file be generated and `CURRENT_PHASE` advanced.

## Current phase package

`informes/fases/PHASE_00_INSTRUCTIONS.md`

## Required phase report

`informes/fases/PHASE_00_EXECUTION_REPORT.md`

## Review protocol

The external reviewer must inspect:

- actual commit;
- changed files;
- test evidence;
- data provenance;
- contradictions with historical docs;
- unresolved P0/P1 defects;
- whether the phase exit criteria are objectively satisfied.

A green test suite alone is never sufficient for approval.
