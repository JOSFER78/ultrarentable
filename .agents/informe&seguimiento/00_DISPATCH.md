# ULTRARENTABLE — ACTIVE DISPATCH

## Purpose
This file is the monotonic execution trigger for Antigravity 2.0. Every corrective step or phase transition issued by the external reviewer gets a NEW `dispatch_id`.

## ACTIVE DISPATCH

```yaml
dispatch_id: AG2-DISPATCH-20260825-1440-P01-003
order_id: AG2-P01-003
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/09_ORDER_AG2-P01-003.md
target_phase: 01
phase_status: REWORK
status: ISSUED
issued_at_utc: 2026-08-25T14:40:00Z
execution_surface: origin/main
scope_mode: STRICT_SINGLE_PHASE
zero_simulation: true
zero_forcing: true
```

## Watcher rule

Every ~3 minutes Antigravity MUST:
1. `git fetch origin main`.
2. Read `00_DISPATCH.md`, `01_CONTROL_STATE.md`, and `02_CURRENT_ORDER.md` from `origin/main`.
3. Parse `dispatch_id`, `order_id`, `status`, `target_phase`, and `phase_status`.
4. Compare `dispatch_id` against its persisted last-processed value.
5. If NEW, `status=ISSUED`, `target_phase == CURRENT_PHASE`, `ACTIVE_ORDER_ID == order_id`, and no other dispatch is running, AUTO-START immediately.
6. A dispatch may be marked processed ONLY after durable proof-of-start exists: orchestration/job ID + start timestamp + target commit.
7. If the persisted dispatch ID equals the active dispatch but there is no proof-of-start and no matching completed handoff, treat it as UNPROCESSED and start it.
8. If a matching completed handoff exists, do not rerun that dispatch; wait for the next NEW dispatch from the external reviewer.
9. Never require the order filename to be new.
10. Execute only the referenced order and phase.

## Delivery
After the order completes, Antigravity pushes the scoped result to `origin/main`, creates the handoff, verifies the remote SHA, and stops. The external reviewer then inspects `origin/main` and issues the next NEW `dispatch_id`.

## Absolute rules

`ZERO-SIMULATION = ON`
`ZERO-FORCING = ON`
`REAL-ONLY = ON`

A timeout, missing job, missing dataset, unverifiable hash, stale evidence, or absent exit code is never a PASS.
