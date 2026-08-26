# ACTIVE ORDER

`STATUS: ACTIVE`

ChatGPT is the direct repository maintainer and executes the stabilization/recovery work in `main`.

## CURRENT BLOCK
`R0.1 — Repository / Dependency Authority`

### Applied
- Added `scripts/stabilization/r0_dependency_authority.py` as a fail-closed dependency authority check.
- Added `tests/stabilization/test_r0_dependency_authority.py` to prevent regression.
- Confirmed the canonical npm lockfile is the root `package-lock.json` and the canonical Python lockfile is `uv.lock`.

### Gate
R0.1 may close only after the checker passes in CI/clean environment and the result is retained as evidence.

## NEXT
After R0.1 evidence is green, advance to `R0.2 — FastAPI Route Surface`.
Do not advance to Discovery, Gates, Research, Meta-Strategy, ULTRA or FONDEO before R0 stabilization is certified.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
