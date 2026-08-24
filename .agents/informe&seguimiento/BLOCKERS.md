# ULTRARENTABLE — ACTIVE BLOCKERS

## BLOCKER-001 — Firebase learning source
Need to inspect the VPS for the historical Firebase/Firestore learning store referenced by project history.

Required before Phase 5 final design:
- locate credentials/configuration and project identifiers;
- identify historical collections and subcollections;
- create read-only recovery export;
- map data to the new LearningStore;
- preserve provenance and unresolved records as UNVERIFIED.

## BLOCKER-002 — Certification policy authority
Current repository has multiple policy/document references across README, doctrine, contracts and implementation. Phase 0 must establish which files/contracts become authoritative before changing certification logic.

## BLOCKER-003 — Current strategy/runtime boundary
CanonicalStrategy and runtime StrategySpecification both exist. Phase 1 must explicitly establish CanonicalStrategy as SSOT and runtime specification as an immutable compiled projection.

## BLOCKER-004 — Existing semantic-ai consolidation
Existing FailureKnowledgeDB, semantic engine, mutation engine, autonomous discovery and SQX feedback must be integrated rather than duplicated.

## Rule
A blocker may be resolved only with evidence. Do not replace a missing external dependency with a mock, sample, synthetic dataset or invented state.