# EXTERNAL REVIEW — AG2-P00-002

## Decision

`REWORK`

## Reviewed repository

`origin/main` at commit `5f8004f4ab5d235172505d66122a87cb66be0e57`.

## Positive findings

AG2-P00-002 did remove the original static portfolio curves/clamps, added canonical version modules, tightened several API/gate paths, added regression tests, and published the handoff to `origin/main`.

## Why this is NOT APPROVED

The implementation still contains objective violations of the project's REAL-ONLY / ZERO-SIMULATION / ZERO-FORCING doctrine.

### P0/P1-1 — Portfolio still fabricates a derived metric

`services/api/app/factory/ultra_portfolio_engine.py` calculates:

`annualized_roi_pct = total_roi * 1.5`

There is no evidence-based annualization model behind `1.5`. This is a fabricated transformation and cannot be presented as a measured result.

The same file also contains inappropriate defaults/fallback semantics such as:

- `c.ratio_oos_is or 50.0`
- `pf = 999.0 if gross_profit > 0 else 0.0`

These values must never become scientific evidence merely because a source field is missing.

Portfolio component selection is also currently based on top PF ordering and presence of trades rather than an explicit current-certification/evidence predicate.

Required:
- remove arbitrary multipliers;
- derive annualized metrics only from actual timestamp coverage and a documented formula, or mark `NO_EVIDENCE`;
- no fabricated defaults;
- require `CERTIFIED_CURRENT` + valid evidence bundle for certification-grade portfolio inclusion;
- preserve component/version/dataset/ledger lineage.

### P0/P1-2 — Version manager still contains fake fallback identity

`services/version_control_manager.py::_get_git_info()` returns a hardcoded historical commit when git commands fail:

`1cd7516e57e2268ae4aa31db0af3c659eec742b8`

This directly violates ZERO-SIMULATION for provenance. Failure to resolve Git identity must produce an explicit `UNVERIFIED`/error state.

The same module also silently swallows state-file errors in `_load_or_init_state()` / `_persist_state()` / `load_manifest()` and reports healthy state despite possible corruption.

`check_drift()` currently returns `code_drift_detected=False` without comparing the stored fingerprint against the current fingerprint.

Required:
- no fake commit/version fallback;
- fail-closed provenance when Git identity is unavailable;
- explicit corruption/error status for unreadable manifests;
- real stored-vs-current fingerprint comparison;
- drift must become evidence/operational state, not a constant.

### P1-3 — API product descriptions still hardcode the old universe

`services/api/app/main.py` still exposes:

- `TRACK_ULTRA = BingX Crypto Perps...`

and root metadata states the platform is a “Dual-Engine” tied to BingX Crypto Perps, while the master plan explicitly requires ULTRA to be registry-driven across supported asset classes and timeframes.

Required:
- remove hardcoded market universe from platform-level metadata;
- resolve displayed track capabilities from current registries/policies;
- FONDEO remains futures-only;
- ULTRA remains global/registry-driven.

### P1-4 — Full regression evidence is incomplete

The handoff lists focused suites but does not demonstrate the complete regression suite required by the active order. The handoff also does not record the verified `origin/main` SHA in its Git delivery section, despite the repository itself being at `5f8004...`.

Required:
- run the complete discovered regression suite through the non-blocking SSH protocol;
- record remote_job_id, command, exit status, duration, logs/artifacts;
- distinguish PASS from UNVERIFIED/FAILED;
- record exact verified `origin/main` SHA in the handoff.

## ZERO-SIMULATION / ZERO-FORCING ruling

The following are forbidden in the remediation:

- arbitrary ROI/annualization multipliers;
- fake provenance values;
- fake/default financial metrics;
- hardcoded drift=false;
- hardcoded market universe where a registry exists;
- changing tests solely to obtain green output;
- marking the phase complete before the full real evidence exists.

## Required subagents for rework

1. RECON / ARCHITECTURE
2. QUANT / PORTFOLIO SCIENCE
3. VERSION / PROVENANCE
4. API / REGISTRY
5. ZERO-MOCK / RED-TEAM
6. TEST / REGRESSION
7. RELIABILITY / SSH JOB CONTROL
8. UI / PROVENANCE

No implementation subagent may be the sole verifier.

## Disposition

`PHASE 00 = REWORK`

Do not enter Phase 01 yet. The next order must close these integrity defects first.
