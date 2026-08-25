# ULTRARENTABLE — ACTIVE DISPATCH

## Purpose

This file is the monotonic execution trigger for the Antigravity 2.0 watcher.
A new `dispatch_id` is a new executable instruction when the referenced order is `ISSUED` and matches the live control state.

## ACTIVE DISPATCH

```yaml
dispatch_id: AG2-DISPATCH-20260825-1420-P01-002
order_id: AG2-P01-002
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/08_ORDER_AG2-P01-002.md
target_phase: 01
phase_status: REWORK
status: ISSUED
issued_at_utc: 2026-08-25T14:20:00Z
control_state_commit_required: true
execution_surface: origin/main
scope_mode: STRICT_SINGLE_PHASE
zero_simulation: true
zero_forcing: true
```

## Watcher rule

Every ~3 minutes Antigravity MUST:
1. `git fetch origin main`.
2. Read this file from `origin/main`.
3. Parse `dispatch_id`, `order_id`, `status`, `target_phase`.
4. Compare `dispatch_id` against its locally persisted last-processed value.
5. If `dispatch_id` is NEW, `status=ISSUED`, `target_phase=CURRENT_PHASE`, and the order is not already running, AUTO-START immediately.
6. A dispatch may be marked acknowledged ONLY after a durable proof-of-start exists (for example: orchestration job ID, start timestamp, and target commit recorded locally).
7. If the persisted last-processed ID equals the active dispatch but there is NO proof-of-start and NO completed handoff for that dispatch, treat the dispatch as UNPROCESSED and start it.
8. Never require the order filename to be new.
9. Never execute two dispatches concurrently.
10. Execute only the referenced order and phase.

## Delivery

After the order completes, Antigravity pushes the scoped result to `origin/main`, creates the handoff and stops. The external reviewer then issues another NEW `dispatch_id` for the next corrective or forward order.

## Absolute rules

`ZERO-SIMULATION = ON`
`ZERO-FORCING = ON`
`REAL-ONLY = ON`

A timeout, missing job, missing dataset, unverifiable hash or unavailable evidence is never a PASS.
