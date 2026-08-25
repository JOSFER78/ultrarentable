# ULTRARENTABLE — ACTIVE DISPATCH

## Purpose
This file is the monotonic execution trigger for the Antigravity 2.0 watcher.
A NEW `dispatch_id` is a NEW executable instruction when the referenced order is `ISSUED` and matches the live control state.

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
2. Read this file from `origin/main`.
3. Parse `dispatch_id`, `order_id`, `status`, `target_phase`, and `phase_status`.
4. Compare the `dispatch_id` against its persisted last-processed value.
5. If NEW, `status=ISSUED`, `target_phase == CURRENT_PHASE`, and the order is not already running, AUTO-START immediately.
6. A dispatch may be marked processed ONLY after durable proof-of-start exists: orchestration/job ID + start timestamp + target commit.
7. If the persisted dispatch ID equals the active dispatch but a matching handoff exists, DO NOT re-run it; wait for the next external dispatch.
8. Never execute two dispatches concurrently.
9. Execute only the referenced order and phase.
10. A NEW dispatch always overrides standby caused by completion of the previous dispatch; completion of an old order must never suppress a later NEW dispatch.

## Delivery

After the order completes, Antigravity pushes the scoped result to `origin/main`, creates the handoff and stops. The external reviewer then publishes another NEW `dispatch_id` for the next corrective or forward order.

## Absolute rules

`ZERO-SIMULATION = ON`
`ZERO-FORCING = ON`
`REAL-ONLY = ON`

Timeout, missing job, missing dataset, unverifiable hash or unavailable evidence is never a PASS.
