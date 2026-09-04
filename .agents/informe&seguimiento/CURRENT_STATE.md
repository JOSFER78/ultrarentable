# ULTRARENTABLE — CURRENT STATE

## Current gate
PHASE 0 — CONSTITUTION & SOURCE OF TRUTH

## Status
BLOCKED_REMOTE — GITHUB FOUNDATION COMPLETE; VPS/FIREBASE AUDIT PENDING

## Branch
`plan/foundation-autonomous-lab`

## Mission
Build ULTRARENTABLE as a permanent autonomous 24/7 quantitative research laboratory:
SQX → CanonicalStrategy → real data → universal engine → evidence/Gates → discard or Research/Reprogramming → immutable version → independent re-examination → current certification → meta-strategy → learning → next generation.

## Confirmed product doctrines
- ULTRA: extreme convexity/asymmetry, broad multi-asset universe, leverage/margin/pyramiding/compounding/recycling according to explicit policy, with >=100% monthly as a research ambition only; never as a forced result.
- FONDEO: aggressive, rule-constrained evaluation strategies intended to pass as rapidly as evidence allows, with a desired hard horizon of <=5 trading days; never shorten/alter evidence to force PASS.
- Meta-strategy: strategy-of-strategies across compatible assets/timeframes, with joint correlation/exposure/risk compensation and joint evidence.
- Research may change any material strategy component permitted by policy; material changes create immutable versions.
- Structural failures are discarded; promising partial failures are candidates for Research.

## Non-negotiable engineering rules
- ZERO MOCKS.
- ZERO SYNTHETIC DATA.
- ZERO INVENTIONS.
- ZERO SILENT FALLBACKS.
- ZERO FORCED PASS.
- ZERO FORCED PROFITABILITY.
- Missing evidence => BLOCKED / NO_EVIDENCE / NOT_COMPUTABLE.
- AI proposes; deterministic engines/evidence Gates decide.
- UI is never domain authority.

## GitHub foundation implemented
- `.agents/informe&seguimiento/` master plan, current state, phases, decisions, blockers, changelog and evidence checkpoint.
- `docs/PRINCIPLES.md`, `docs/ULTRARENTABLE_SOURCE_OF_TRUTH.md`, `docs/STRATEGY_LIFECYCLE.md`, `docs/LEARNING_SYSTEM.md`, `docs/META_STRATEGY_LAB.md`.
- CI workflow `.github/workflows/ultrarentable-ci.yml` for Python contract tests and web build.
- Existing canonical `contracts/lineage_contracts.py` strengthened with current/legacy/stale/revalidation certification semantics and context hashing.
- Existing dataset contract hardened to reject missing/non-positive timestamps, invalid OHLC and non-monotonic chronology instead of manufacturing values.
- `contracts/meta_strategy.py` and contract test added for traceable strategy-of-strategies composition.

## Critical existing components discovered and MUST be reused
- `contracts/learning_contracts.py` already defines the persistent learning entities.
- `services/semantic_ai/learning_store.py` ALREADY implements a durable SQLite WAL LearningStore with the 11 learning tables and typed CRUD.
- `services/semantic_ai/failure_knowledge.py` is a volatile runtime memory/cache and must not remain the historical source of truth if durable LearningStore is available.
- `services/semantic_ai/autonomous_discovery_engine.py` already implements an autonomous research loop but contains deterministic legacy mutation/risk behavior that needs reconciliation, not duplication.
- `services/semantic_ai/sqx_feedback_loop.py` already provides SQX fertility feedback through SQLite.
- `contracts/research_contracts.py` already defines 8 specialist roles and BlindScopeContext.
- `contracts/queue_contracts.py` already defines durable jobs and ForwardSufficiency contracts.
- `contracts/lineage_contracts.py` already defines certification records, lineage DAG and PolicyImpact contracts.
- `contracts/portfolio.py` already defines portfolio, Ultra bullet/vault and Prop challenge configuration.

## Current verification blockers
1. VPS/Firebase/Firestore historical learning inventory has not been performed from this GitHub session.
2. Existing LearningStore ↔ Firebase persistence/recovery connection is not verified.
3. Existing lifecycle enums/statuses across CanonicalStrategy, learning_contracts and lineage_contracts need code-level reconciliation.
4. Existing compiler/runtime authority chain needs end-to-end runtime verification.
5. GitHub Actions has been configured but no workflow run has yet been observed for the branch; do not claim CI PASS.

## Provisional implementation work
Contract and safety improvements may be prepared on this branch, but no phase is certified until runtime tests and the remote VPS/Firebase audit provide real evidence.

## Phase gate
PHASE 0 remains BLOCKED_REMOTE. The next real unlock is the VPS/Firebase audit and reconciliation. Once that is available, Phase 1 Strategy Core can be verified rather than re-invented.

## No-claim rule
Never state PASS, CERTIFIED, VERIFIED or COMPLETE without executable evidence recorded here.
