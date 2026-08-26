# ACTIVE ORDER

`STATUS: ACTIVE`

ChatGPT is the direct repository maintainer and executes the stabilization/research work in `main`.

## THREE MACROPHASES
1. `MACROPHASE 1 — TRUSTWORTHY FOUNDATION / RECOVERY`
2. `MACROPHASE 2 — REAL QUANT RESEARCH / DISCOVERY / VALIDATION`
3. `MACROPHASE 3 — PORTFOLIO / ULTRA / FONDEO PRODUCTION SYSTEM`

Full definition: `16_THREE_MACROPHASE_MASTER_PLAN.md`

## CURRENT MACROPHASE
`MACROPHASE 2 — IN PROGRESS`

### R0 ENTRY EVIDENCE
The latest stabilization run on commit `ad806be59b6315e216619af71adb5a0be86123a1` returned `SUCCESS` through the final R0 certification step. All R0 guards, compile/lint, web typecheck/build, focused stabilization tests, real web/backend E2E and backend clean-start completed successfully.

`R0_STABLE = CERTIFIED`

### PHASE 2 WORK ALREADY APPLIED
- Discovery uses central runtime/data configuration; machine-local paths removed from the quantitative pipeline.
- Dataset repository now fails closed when canonical normalized data is missing or malformed; synthetic bar fallbacks were removed.
- Physical normalized dataset bytes are SHA-256 hashed and propagated into dataset identity/provenance.
- Discovery is explicitly partitioned chronologically `60% IS / 20% validation / 20% blind OOS`.
- Blind OOS is not available during champion selection; it is consumed only after the strategy is frozen.
- Search trials are persisted with trial/run/dataset/hash metadata.
- Discovery search dimensions have been made explicit; the campaign has a deterministic reproducible trial budget.
- Phase-2 integrity guard is enforced in CI and currently passes.
- Live BingX historical acquisition is isolated in `.github/workflows/phase2-live-data.yml` as `workflow_dispatch` only, preventing live-data jobs from creating notification storms on every repository push.
- Paginated real-data history loader added at `scripts/sync_phase2_history.ts`.

### CURRENT PHASE 2 TARGET
`P2-A — REAL DATA UNIVERSE / DATASET CUSTODY`

The research engine must receive real historical datasets with sufficient coverage before any profitability claim or candidate promotion is considered valid.

### NEXT EXECUTION BLOCK
1. Acquire real BingX historical datasets using the manual Phase-2 data workflow.
2. Verify dataset manifests, physical SHA-256, closed-candle invariant, continuity and minimum coverage.
3. Run the canonical discovery pipeline against those datasets.
4. Compare trial families using stored trial accounting, not only the winner.
5. Re-run selected candidates through canonical backtest + validation + robustness gates.
6. Promote only candidates with complete evidence; otherwise leave them `BLOCKED`/`REJECTED`.

## EMAIL / CI CONTROL
- Push-triggered CI workflows have `concurrency.cancel-in-progress=true`.
- CI workflows are `permissions: contents: read` and no longer self-commit repairs.
- Live data acquisition is manual-only, not push-triggered.
- No workflow in the Phase-2 path is allowed to mutate `main` automatically.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
