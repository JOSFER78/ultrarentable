# ORDER AG2-RECOVERY-001 — FINAL SYSTEM RECOVERY + WEB LOCALHOST VERIFICATION

## STATUS
`ISSUED`

## OBJECTIVE
Verificar en el proyecto real que las reparaciones directas publicadas por el revisor han dejado la aplicación web portable y arrancable, y cerrar cualquier blocker real restante antes de autorizar Phase 03.

## SOURCE OF TRUTH
Todas las órdenes se leen desde GitHub `JOSFER78/ultrarentable` / `main`.

## STRICT SCOPE
SOLO recuperación/verificación del sistema actual.
NO Phase 03.
NO Discovery.
NO Genome.
NO Gates.
NO Robustness.
NO Research.
NO Meta-Strategy.
NO ULTRA research.
NO FONDEO research.

## KNOWN DIRECT REPAIRS ALREADY APPLIED BY REVIEWER
- Removed machine-local Windows paths from `apps/web/tsconfig.json`.
- Removed duplicate `next.config.mjs`.
- Made `apps/web/next.config.ts` the single portable Next.js config with local API proxy.
- Added portable Tailwind v4 PostCSS configuration.
- Restored portable `next-env.d.ts`.
- Aligned `apps/web/package.json` with the workspace dependency model.
- Replaced the dashboard home page so it renders only evidence returned by the canonical API and never promotes candidates to certification or invents metrics.
- Normalized UTF-8 metadata in `apps/web/app/layout.tsx`.

These changes are NOT evidence of runtime success until independently verified.

## MANDATORY SUBAGENTS
1. `RECON / REPOSITORY STARTUP`
2. `WEB / NEXT BUILD`
3. `WEB / LOCALHOST E2E`
4. `API / BACKEND CONNECTIVITY`
5. `DEPENDENCY / WORKSPACE LOCK`
6. `ZERO-MOCK / UI PROVENANCE`
7. `RED-TEAM / STARTUP`
8. `INDEPENDENT TEST / RELIABILITY`
9. `GIT / REMOTE PARITY`
10. `LEAD / FINAL RECONCILIATION`

The lead cannot be the sole verifier.

## STEP 0 — CONTROL IDENTITY
Read from GitHub main:
- `00_DISPATCH.md`
- `01_CONTROL_STATE.md`
- `02_CURRENT_ORDER.md`
- this order archive

The exact dispatch/order/phase/status must match. Any mismatch = BLOCKED.

## STEP 1 — CLEAN INSTALL / WORKSPACE
From the real repository:
- verify root workspace configuration;
- use the repository's package manager/lockfile;
- no copying of a local `node_modules` from another machine;
- no manual dependency injection outside the manifest;
- record exact Node/npm versions.

## STEP 2 — WEB TYPECHECK + BUILD
Run from the repository using the workspace scripts:
- `npm install` / workspace-equivalent according to the committed lockfile;
- `npm --workspace apps/web run typecheck`;
- `npm --workspace apps/web run build`.

Record exact commands, exit codes, duration and target commit SHA.

Any error must be fixed at source, then rerun.

## STEP 3 — LOCALHOST E2E
Start the REAL frontend with:
- `npm --workspace apps/web run dev`

Verify:
- process actually remains alive;
- HTTP response from `http://localhost:3000`;
- one principal application route returns successfully;
- browser/client can reach `/api/...` through the real Next rewrite;
- backend on the configured port is reachable;
- no fake API/data fallback is used to declare success.

If frontend fails:
- inspect stack trace;
- fix root cause;
- restart;
- repeat typecheck/build/start;
- never replace the application with a mock server/page.

Record PID, port, exact URL, response status, startup log and exit state.

## STEP 4 — BACKEND CONNECTIVITY
Verify the real FastAPI service used by the web app is importable and starts.
Verify its health/root endpoint if available.
Confirm the Next proxy points to the actual backend port.

A disconnected backend must show a truthful error/NO_EVIDENCE state, not synthetic metrics.

## STEP 5 — UI PROVENANCE
Audit the main dashboard and the paths it imports.
Confirm:
- no candidate is rendered as certification;
- no fabricated dataset/hash/capital/timestamp is created in the UI;
- missing API data renders `NO_EVIDENCE` or an honest error;
- certification is based on the canonical API state only.

## STEP 6 — ZERO-MOCK SCAN
Search the web/runtime path for:
- `Math.random`
- synthetic bars
- hardcoded dataset hashes
- fabricated timestamps
- fabricated PF/ROI/DD
- fake API success
- default quantitative capital
- fallback candidate->certified logic

Any quantitative fake/fallback that can affect displayed or executable results = BLOCKED until removed or isolated as an explicitly non-production test fixture.

## STEP 7 — REGRESSION
Run:
- affected Phase 01 tests;
- Phase 02 runtime/version tests;
- web typecheck;
- web build;
- localhost smoke;
- backend health check.

No green claim without exact command + exit code.

## STEP 8 — GIT DELIVERY
All corrections must be made in:
`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Then:
`git status`
→ `git add`
→ `git commit`
→ `git pull --rebase origin main`
→ `git push origin main`
→ `git fetch origin main`
→ verify exact remote SHA.

## STEP 9 — EVIDENCE
Create:
- `.agents/informe&seguimiento/RECOVERY-001_AGENT_LEDGER.md`
- `.agents/informe&seguimiento/RECOVERY-001_RECONCILIATION.md`
- `.agents/informe&seguimiento/03_HANDOFF_AG2-RECOVERY-001.md`

Every subagent must record its own command evidence and exit code.

## FINAL STATE
Allowed outcomes only:
- `READY_FOR_PHASE_03_REVIEW`
- `BLOCKED`

Antigravity must NOT create Phase 03 or change `CURRENT_PHASE`.

## ABSOLUTE
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED

No fabricated data, no synthetic success, no fake HTTP, no fake tests.

## STOP
After delivery: push main, verify remote SHA, create handoff, STOP.
