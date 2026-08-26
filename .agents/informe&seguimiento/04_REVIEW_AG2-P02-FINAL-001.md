# REVIEW AG2-P02-FINAL-001 — RECOVERY REQUIRED

## Verdict
`RECOVERY_REQUIRED`

The previous Phase 02 closure was not accepted as fully operational because the web application contained concrete portability/startup and evidence-integrity defects.

## Findings fixed directly by external reviewer
1. `apps/web/tsconfig.json` contained machine-local Windows paths. Replaced with portable workspace-relative configuration.
2. Duplicate Next.js configs existed (`next.config.mjs` + `next.config.ts`). Removed the duplicate and made `next.config.ts` the single portable config.
3. Added the Tailwind v4 PostCSS plugin configuration and synchronized web dependencies with the root workspace model.
4. Restored portable Next.js type declarations.
5. Replaced the dashboard page's candidate-to-certified fallback and fabricated KPI/data fallbacks with evidence-only rendering.
6. Normalized UTF-8 metadata in the root layout.

## Known issue still requiring runtime verification
The API client contains a legacy `executeBacktest` helper that historically constructed synthetic/default request values. The recovery order explicitly requires a zero-mock scan and must prevent any such legacy client path from affecting executable or displayed results. Do not claim this is fixed until the real runtime path has been verified.

## Next authority
`AG2-RECOVERY-001` is the only active order.

## Required completion proof
- clean workspace install
- web typecheck PASS
- web build PASS
- real localhost:3000 HTTP PASS
- real backend connectivity PASS
- zero-mock scan PASS
- regression PASS
- exact remote SHA
- handoff + agent ledger + reconciliation

Phase 03 remains LOCKED until external review of the recovery handoff.
