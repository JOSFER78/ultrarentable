# ULTRARENTABLE — STABILIZATION MASTER PLAN

## PURPOSE
Recover a coherent, reproducible, production-safe baseline before implementing or extending quantitative discovery, gates, research, ULTRA or FONDEO functionality.

## CURRENT VERDICT
`STABILIZATION_REQUIRED`

The repository has improved materially, but it is not yet proven stable end-to-end. Direct repairs have removed several known quantitative fabrication paths, but the repository still contains architectural duplication and legacy surfaces that can contradict the canonical contracts.

## HARD FREEZE
Until R0 stabilization is closed:
- NO Discovery Factory expansion
- NO new StrategyQuant campaigns
- NO Gates expansion
- NO Research mutations
- NO Meta-Strategy certification
- NO ULTRA profitability claims
- NO FONDEO profitability claims
- NO live execution claims

## R0 BLOCKS

### R0.1 — Repository / Dependency Authority
Goal: one reproducible dependency model.

Check:
- root workspace + lockfile
- `apps/web/package.json`
- Python `pyproject.toml`
- duplicate manifests/configs
- Node/Python supported versions
- dependency install from clean environment

Exit evidence:
- exact versions
- clean install
- no undeclared runtime dependency
- no machine-local path

### R0.2 — FastAPI Route Surface
Goal: one deterministic route registration surface.

Audit all router registrations in `services/api/app/main.py`.
Remove accidental duplicate registrations and legacy aliases that create conflicting OpenAPI/runtime surfaces unless explicitly required and documented.

Exit evidence:
- route inventory
- duplicate-route report = 0 unexpected duplicates
- one canonical route per capability

### R0.3 — Canonical Data / Certification API
Goal: every certification response is evidence-backed.

Audit:
- certified strategy endpoints
- meta-strategy endpoints
- candidate-to-certified promotion paths
- status mappings
- hash requirements
- gate evidence
- ledger verification

Exit evidence:
- no hardcoded quantitative metrics
- no synthetic hashes
- no candidate fallback
- missing evidence => `NO_EVIDENCE`

### R0.4 — Execution Session Safety
Goal: no endpoint may claim running execution without provider confirmation.

Audit:
- session creation
- provider identity
- environment identity
- capital
- symbol
- heartbeat
- live/paper state transitions
- kill-switch semantics

Exit evidence:
- sessions begin `PENDING_PROVIDER` unless a real provider handshake exists
- transitions to RUNNING require explicit real confirmation
- no synthetic telemetry

### R0.5 — Web API Client Surface
Goal: no frontend helper can fabricate quantitative inputs.

Audit all functions in `apps/web/lib/api.ts` and imported clients.

Exit evidence:
- no hardcoded dataset identity
- no hardcoded timestamps
- no default quantitative capital
- no fake hashes
- no local certification logic
- requests reference canonical API IDs only

### R0.6 — Web Build / E2E Contract
Goal: local UI actually starts against the real API.

Verify:
- clean npm install
- typecheck
- production build
- dev server
- localhost:3000
- `/api/*` rewrite to backend
- truthful `NO_EVIDENCE` when backend/data are absent

Exit evidence:
- exact commands + exit codes
- HTTP status evidence
- no fake API

### R0.7 — Backend Clean Start
Goal: FastAPI starts independently in local mode.

Verify:
- Python dependency install
- import
- DB init
- health/version endpoint
- autonomous runtime remains OFF by default

Exit evidence:
- startup log
- health response
- deterministic local mode

### R0.8 — CI Enforcement
Goal: every future change is blocked if it reintroduces forbidden behavior.

CI must cover:
- Python compile/type/lint/tests
- Web typecheck/build
- zero-mock scan
- route inventory check
- forbidden literal scan

Exit evidence:
- GitHub Actions green on the stabilization commit

### R0.9 — Canonical Domain Boundary Review
Goal: identify remaining legacy modules that can bypass canonical contracts.

Produce a dependency/authority graph:
UI → API → domain/evidence → execution → data.

Every alternative route must be classified:
`CANONICAL`, `LEGACY_ISOLATED`, `TEST_FIXTURE`, or `REMOVE`.

### R0.10 — Final R0 Certification
Only after R0.1–R0.9:
- clean installation
- build
- backend startup
- localhost E2E
- certification endpoint audit
- execution endpoint audit
- zero-mock scan
- route inventory
- CI green

Allowed outcomes:
`R0_STABLE` or `R0_REWORK`.

## RULE
A block is not closed by code edits alone. It requires source revision + reproducible verification + evidence.

## NEXT
After R0 is certified stable, resume the master plan at the next appropriate phase. Do not skip directly to discovery because the UI happens to render.

## ABSOLUTE
ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED
