# ANTIGRAVITY 2.0 — HANDOFF TEMPLATE

Copy this template for each completed order.

## 1. Order

- order_id:
- target_phase:
- status: `READY_FOR_REVIEW` or `BLOCKED`
- started_at_utc:
- finished_at_utc:

## 2. Workspace / Git delivery

- workspace:
- start_commit:
- final_local_commit:
- `origin/main` verified commit:
- branch used during implementation:
- pushed_to_origin_main: `YES` / `NO`

**Rule:** `READY_FOR_REVIEW` requires the complete deliverable to be present on `origin/main`. Local-only work is not delivered.

## 3. Subagents

| Role | Subagent | Scope | Result |
|---|---|---|---|
| RECON | | | |
| IMPLEMENTATION | | | |
| TEST/VERIFICATION | | | |
| DATA/EVIDENCE | | | |
| RED-TEAM | | | |
| UI/PROVENANCE | | | |
| DISCOVERY | | | |
| LEARNING/FIREBASE | | | |
| RELIABILITY | | | |

## 4. Findings

### Proven

### Unverified

### Failed

### Blocked

## 5. Files changed

List every changed file delivered to `origin/main`.

## 6. Commands executed

| Command | Exit code | Result |
|---|---:|---|

Include repository synchronization commands where relevant, for example fetch/status/commit/push/remote verification.

## 7. Tests

### Focused

### Regression

## 8. Real data / evidence

- dataset IDs:
- dataset SHA-256:
- strategy hashes:
- ledger hashes:
- evidence bundle IDs:
- external artifact IDs/URIs/hashes, if applicable:

## 9. Version lineage

- strategy_version:
- engine_version:
- contract_version:
- gate_policy_version:
- validation_run_id:
- code_commit_sha:
- data_snapshot_id:

## 10. Control-document updates

List which files under `.agents/informe&seguimiento/` were changed and why.

The handoff itself must be committed/pushed to `origin/main` before `READY_FOR_REVIEW`.

## 11. Contradictions / risks

## 12. What this order actually proved

## 13. What it did NOT prove

## 14. Phase exit criteria

| Criterion | Status | Evidence |
|---|---|---|

## 15. Final delivery gate

- implementation on `origin/main`: `YES` / `NO`
- handoff on `origin/main`: `YES` / `NO`
- remote SHA verified after push: `YES` / `NO`
- local-only artifacts remaining that matter to review:

If any required delivery item is `NO`, final status must be `BLOCKED`.

## 16. Final handoff

`READY_FOR_REVIEW`
