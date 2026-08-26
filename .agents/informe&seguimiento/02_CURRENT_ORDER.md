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
- R0 gate updated to execute all three runtime/source guards after clean dependency installation.

### Evidence status
GitHub Actions is not currently returning workflow runs for recent pushes through the connected GitHub interface. Therefore R0 is **NOT CERTIFIED GREEN** yet; no certification claim may be made from source inspection alone.

## NEXT
`R0.4 — Execution Safety`
Audit all execution/order routes and reject any path that can place, modify, cancel or simulate-live orders without explicit REAL execution mode, canonical strategy binding, risk limits and audit lineage.

Do not advance to Discovery, Gates, Research, Meta-Strategy, ULTRA or FONDEO before R0 stabilization is certified.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
