# ULTRARENTABLE — ACTIVE CONTROL DISPATCH

## ACTIVE WORK
```yaml
dispatch_id: DIRECT-20260826-R0-001
order_id: DIRECT-R0-BOOTSTRAP
order_file: .agents/informe&seguimiento/02_CURRENT_ORDER.md
target_phase: 02
phase_status: RECOVERY_VALIDATION
status: ACTIVE_DIRECT_REPAIR
execution_owner: EXTERNAL_REVIEWER
execution_surface: origin/main
scope_mode: STRICT_SINGLE_REPAIR
zero_simulation: true
zero_forcing: true
zero_lookahead: true
```

## SOURCE OF TRUTH
GitHub `JOSFER78/ultrarentable` → branch `main`.

Antigravity is NOT an execution dependency for the current recovery. The external reviewer may inspect and repair the repository directly. The watcher, if active, is informational only and must not create or choose work.

## CURRENT WORK
Direct recovery of repository bootstrap/runtime integrity:
- deterministic web dependency/build surface;
- FastAPI import/startup;
- localhost/proxy wiring;
- evidence-only UI;
- zero-mock runtime paths;
- regression gates.

## DELIVERY
The reviewer updates `main` directly, verifies the resulting repository state, and records evidence in `.agents/informe&seguimiento/`.

## ABSOLUTE RULES
ZERO-SIMULATION = ON
ZERO-FORCING = ON
REAL-ONLY = ON
ZERO-LOOKAHEAD = ON

A green test suite alone is insufficient. Runtime claims require reproducible evidence.
