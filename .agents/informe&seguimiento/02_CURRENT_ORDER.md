# ACTIVE ORDER

`STATUS: ACTIVE`

ChatGPT is the direct repository maintainer and executes the stabilization/recovery work in `main`.

## CURRENT BLOCK
`R0 — Stabilization / Recovery`

### Applied
- R0.1 dependency authority guard + regression test.
- Clean-install enforcement with root `package-lock.json` and `uv.lock`.
- R0.2 effective FastAPI route collision guard + regression test.
- R0.3 certification evidence policy enforced at `CertificationRegistry` + regression tests.
- R0.4 execution-session safety guard + regression tests.
- R0.5 web API client surface guard + regression test.
- R0.6 real web/backend E2E contract script + regression test.
- R0 gate executes all stabilization guards after clean dependency installation and then runs real backend/web E2E.

### Evidence status
Source-level guards and the reproducible E2E procedure are implemented. GitHub Actions is still not returning workflow runs for recent pushes through the connected GitHub interface, therefore R0 remains **NOT CERTIFIED GREEN**. No certification claim may be made from source inspection alone.

## NEXT
`R0.7 — Backend Clean Start`
Verify independent FastAPI startup, DB initialization, health/version response, deterministic local mode and autonomous runtime OFF by default.

Do not advance to Discovery, Gates, Research, Meta-Strategy, ULTRA or FONDEO before R0 stabilization is certified.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
