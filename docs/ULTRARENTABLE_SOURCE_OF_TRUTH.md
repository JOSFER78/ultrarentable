# ULTRARENTABLE — SOURCE OF TRUTH & AUTHORITY MODEL

## Purpose
This document defines which layer is authoritative for each domain concept. No agent, UI page or convenience adapter may create a competing source of truth.

## Core authority chain

```text
Canonical Strategy
    ↓
Immutable Strategy Version / Snapshot
    ↓
Compiled Runtime Specification
    ↓
Deterministic Engine
    ↓
Execution Ledger
    ↓
Metrics / Evidence
    ↓
Gate Policy + Certification Snapshot
    ↓
Current Certification State
```

## Authorities

| Domain | Authoritative source | Derived consumers |
|---|---|---|
| Strategy definition | CanonicalStrategy | compiler, runtime spec, UI, research |
| Strategy version | immutable StrategyVersion/Snapshot | lineage, evidence, UI |
| Runtime execution spec | compiled immutable projection | engine only |
| Market data identity | validated DatasetSnapshot | engine/evidence |
| Instrument economics | InstrumentSpecification | execution/risk |
| Execution economics | ExecutionSpecification | engine/ledger |
| Risk doctrine | Track-specific RiskPolicy | engine/validation |
| Backtest truth | CanonicalExecutionLedger | metrics/evidence/UI |
| Gate definition | GatePolicy | validation/UI |
| Certification | CertificationSnapshot | approved/current/portfolio |
| Historical learning | persistent LearningStore | research/SQX feedback/agents |
| Product phase definitions | PRODUCT_PHASES | navigation/UI |
| Quant pipeline definitions | QUANT_PIPELINE_PHASES | orchestration |
| Portfolio/meta-strategy | MetaStrategyDefinition + evidence | portfolio/UI |

## Derived-data rule

Adapters, UI components and convenience services may derive read models, but may not mutate or reinterpret authoritative domain state.

## Current vs legacy

Certification is contextual. A certification is current only when its referenced engine, compiler, dataset policy, execution policy, risk policy and gate policy match the current certification contract. Otherwise it becomes `STALE` / `REVALIDATION_REQUIRED` and remains historically reproducible.

## AI governance

AI agents may inspect evidence, debate hypotheses, propose mutations and create new strategy versions through controlled tools. They cannot approve their own work, mutate an existing certified version, or manufacture evidence.

## Zero-truth-downgrade rule

When required evidence is unavailable or an adapter cannot interpret the requested strategy/data semantics exactly, execution must fail closed. Never substitute an unknown indicator with another indicator, an unknown market series with a close series, an unknown dataset with a different dataset, or an absent financial parameter with a convenience default.
