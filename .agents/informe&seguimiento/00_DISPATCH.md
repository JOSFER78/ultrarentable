# ULTRARENTABLE — ACTIVE DISPATCH

## Purpose

This file is the **monotonic execution trigger** for the Antigravity 2.0 watcher.
It exists because `02_CURRENT_ORDER.md` is a reusable control file and its path does not change between phases.

The watcher MUST compare `dispatch_id` against the last dispatched/acknowledged value.
A new `dispatch_id` is a new executable instruction whenever the referenced order is `ISSUED` and matches `01_CONTROL_STATE.md`.

## ACTIVE DISPATCH

```yaml
dispatch_id: AG2-DISPATCH-20260825-1401-P01-001
order_id: AG2-P01-001
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
order_archive: .agents/informe&seguimiento/08_ORDER_AG2-P01-001.md
target_phase: 01
phase_status: READY
status: ISSUED
issued_at_utc: 2026-08-25T14:01:00Z
control_state_commit_required: true
execution_surface: origin/main
scope_mode: STRICT_SINGLE_PHASE
zero_simulation: true
zero_forcing: true
```

## Watcher rule

On every ~3-minute cycle:

1. `git fetch origin main`.
2. Read this file from `origin/main`.
3. Parse `dispatch_id`.
4. Compare it with the persisted `last_processed_dispatch_id`.
5. If it is NEW and `status: ISSUED` and `target_phase == CURRENT_PHASE`, AUTO-START the referenced order.
6. Persist the dispatch as acknowledged only after Antigravity has actually started the order.
7. Do not require the order filename to be new.
8. A changed `dispatch_id` is sufficient to trigger a new run.
9. Never execute two dispatches concurrently.
10. The active order remains strictly limited to the referenced phase/order.

## Important

`04_REVIEW_*.md` files are evidence, not execution triggers.
A future LOCKED order is not executable.
`00_DISPATCH.md` + `01_CONTROL_STATE.md` + `02_CURRENT_ORDER.md` form the execution handshake.

## Delivery

When the active order finishes, Antigravity must push its complete scoped result to `origin/main` and produce the corresponding handoff. The external reviewer then publishes a NEW `dispatch_id` for the next corrective or forward order.
