# ULTRARENTABLE — CURRENT STATE

## Current phase
PHASE 0 — CONSTITUTION & SOURCE OF TRUTH

## Status
IN_PROGRESS — GITHUB FOUNDATION CHECKPOINT COMPLETE; VPS/FIREBASE AUDIT PENDING

## Branch
`plan/foundation-autonomous-lab`

## Objective
Establish one coherent development/architecture contract before modifying quantitative runtime behavior.

## Confirmed project intent
- Permanent 24/7 autonomous quantitative research laboratory.
- SQX is the primary hypothesis factory when available; it is not the final certifier.
- One canonical strategy identity with immutable versions and lineage.
- ULTRA and FONDEO share the technical core but use distinct objective/risk/evaluation policies.
- Research may modify any strategy component allowed by policy, but every material change creates a new version and re-enters independent validation.
- Promising failures go to Research; structural failures are discarded.
- Meta-strategies are first-class: compatible strategies across assets/timeframes may be combined under a joint risk/correlation/exposure budget when evidence supports the combination.
- The system must learn from real successes and failures without learning how to bypass the evaluation.

## Current doctrine constraints
- ZERO MOCKS.
- ZERO SYNTHETIC DATA.
- ZERO INVENTIONS.
- ZERO SILENT FALLBACKS.
- ZERO FORCED PASS.
- ZERO FORCED PROFITABILITY.
- Missing required evidence => BLOCKED / NO_EVIDENCE / NOT_COMPUTABLE.
- UI never becomes the source of domain truth.
- AI proposes; deterministic engines and evidence gates decide.

## Phase 0 completed on GitHub
- Master implementation plan.
- Phase/state/checkpoint workflow.
- Product principles.
- Source-of-truth authority model.
- Strategy lifecycle and certification staleness semantics.
- Persistent learning contract and blind-research contract.
- Meta-strategy laboratory contract.
- Evidence checklist.

## Phase 0 still pending
- VPS audit of Firebase/Firestore historical learning data.
- Reconciliation of existing semantic_ai learning components with the new LearningStore contract.
- Final code-level authority reconciliation: CanonicalStrategy → compiled runtime specification → engine.
- Final reconciliation of existing lifecycle enum/status names against the semantic lifecycle contract.
- Verify all current doctrine/runtime contradictions before Phase 1.

## Important current code findings
- Existing semantic_ai components include FailureKnowledgeDB, autonomous_discovery_engine, mutation_engine, semantic_engine and SQX feedback loop; do not create a parallel learning stack.
- FailureKnowledgeDB currently keeps historical records in process memory and therefore cannot alone satisfy durable learning requirements.
- Autonomous discovery currently contains deterministic parameter/track behavior; this must be treated as legacy implementation to be reconciled against the future Research Lab contract, not as the final autonomous research architecture.

## Phase gate
Phase 0 can only become PASS after the VPS/Firebase learning inventory is completed and all remaining authority/lifecycle contradictions are resolved in code + documentation.

## Evidence requirements
A phase can only become PASS after:
1. Code/document changes are complete for that phase.
2. Relevant tests are executed.
3. Red-team/negative-path checks are executed.
4. Results are recorded here.
5. No mock/synthetic/invented data is used.

## Rule
DO NOT start Phase 1 until Phase 0 is marked PASS here.
