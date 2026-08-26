# ACTIVE ORDER

`STATUS: ACTIVE`

ChatGPT is the direct repository maintainer and executes the stabilization/recovery work in `main`.

## CURRENT BLOCK
`R0.9 — Canonical Domain Boundary Review`

### Applied
- R0.1 dependency authority guard + regression test.
- Clean-install enforcement with root `package-lock.json` and `uv.lock`.
- R0.2 effective FastAPI route collision guard + regression test.
- R0.3 certification evidence policy enforced at `CertificationRegistry` + regression tests.
- R0.4 execution-session safety guard + regression tests.
- R0.5 web API client surface guard + regression test.
- R0.6 real web/backend E2E contract script + regression test.
- R0.7 backend clean-start contract + regression test.
- R0.8 compile/lint/web build/forbidden-literal CI enforcement.
- R0.9 canonical domain-boundary audit + regression test.

### Current finding
R0.9 is **BLOCKED** because `services/api/app/api/routes.py` nests `sqx_router`, while `services/api/app/main.py` also mounts `sqx_router` as a canonical surface. This creates a second authority path and must be isolated or removed before R0 can close.

### Evidence status
GitHub Actions is still not returning workflow runs for recent pushes through the connected GitHub interface. Therefore R0 remains **NOT CERTIFIED GREEN** regardless of source-level results.

## NEXT
Remove/isolate the nested legacy SQX registration without replacing or truncating the remainder of `routes.py`, then rerun R0.9 and proceed to R0.10 final certification.

Do not advance to Discovery, Gates, Research, Meta-Strategy, ULTRA or FONDEO before R0 stabilization is certified.

## ABSOLUTE
`ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED`
