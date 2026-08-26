# RECOVERY-001 — Direct Repair Record

Date: 2026-08-26
Branch: `main`

## Direct repairs published

1. `apps/web/app/page.tsx`
   - Restored valid Next.js client page after detecting an empty file.
   - Removed candidate-to-certification fallback logic.
   - Displays only values returned by canonical API endpoints.
   - Shows `NO_EVIDENCE`/connection error when the API cannot provide evidence.

2. `apps/web/next.config.ts`
   - Backend proxy is now configurable with `ULTRARENTABLE_API_URL`.
   - Default remains `http://127.0.0.1:8000` for local development.

3. `apps/web/package.json`
   - Removed architecture-specific `@next/swc-linux-arm64-gnu` from the application manifest.
   - Keeps Next responsible for selecting the platform-compatible SWC package.

4. `services/api/app/main.py`
   - 24/7 supervisor/daemon startup is explicitly opt-in through `ULTRARENTABLE_AUTONOMOUS_RUNTIME=true`.
   - Local API startup no longer requires the autonomous worker fleet.

5. `.github/workflows/web-quality.yml`
   - Added clean-install, TypeScript typecheck and production-build gate for every push to `main` and every PR.

## Important remaining verification

GitHub access can modify and inspect the repository, but it does not execute the VPS/local process in this session. Therefore `npm ci`, `typecheck`, `build`, FastAPI startup and localhost E2E must still be confirmed by GitHub Actions or the real runtime host before declaring runtime green.

## Zero-mock requirement

The legacy `executeBacktest()` helper in `apps/web/lib/api.ts` still contains synthetic request/dataset construction and must not be considered a trusted execution path until replaced by a canonical dataset-backed request. The UI does not use it for certification claims.

## Current HEAD

`5d5f0fe4093c9efd1f5136faee5e83ea4f4a6c1e`
