# R0 DIRECT REPAIR — 2026-08-26

## Execution owner
External reviewer / direct repository repair.

## Changes published directly to `main`

### Web
- `apps/web/app/page.tsx`: restored a valid dashboard and kept it evidence-only.
- `apps/web/next.config.ts`: configurable backend URL through `ULTRARENTABLE_API_URL`.
- `apps/web/tsconfig.json`: removed machine-local paths.
- `apps/web/postcss.config.mjs`: portable Tailwind v4 PostCSS configuration.
- `apps/web/package.json`: removed architecture-specific SWC dependency.

### Backend
- `services/api/app/main.py`: autonomous 24/7 workers are opt-in through `ULTRARENTABLE_AUTONOMOUS_RUNTIME=true`; local API startup is independent.

### Quantitative client safety
- `apps/web/lib/api.ts`: removed synthetic dataset/hash/timestamp/capital generation from the backtest client.
- `executeBacktest()` now requires a real existing `dataset_id` and fails closed if it is absent.
- `api.runFastBacktest()` now requires a real `datasetId` and does not invent capital when omitted.

### CI
- `.github/workflows/web-quality.yml`: clean install + typecheck + production build.
- `.github/workflows/backend-quality.yml`: Python dependency install + compileall + pytest.

## Remaining verification

The repository is repaired directly, but the available GitHub API does not provide a local/VPS shell in this session. Therefore runtime claims must be confirmed by CI results or the actual host. No runtime PASS is asserted here without that evidence.

## Absolute doctrine
ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED
