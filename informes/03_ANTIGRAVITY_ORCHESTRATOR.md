# ULTRARENTABLE — ANTIGRAVITY 2.0 ORCHESTRATOR

## Purpose

This is the operational control plane for Antigravity 2.0. It converts the adaptive plan into a closed execution/review loop.

Antigravity is the implementation agent. It is NOT the certification authority and it is NOT allowed to decide that the program should advance.

## Operating loop

```text
CONTROL_STATE
    ↓
PHASE PACKAGE
    ↓
ANTIGRAVITY IMPLEMENTS
    ↓
REAL TESTS / REAL DATA
    ↓
EXECUTION REPORT
    ↓
STOP
    ↓
EXTERNAL REVIEW
    ├── APPROVE → next phase package is issued
    ├── REJECT  → correction package for same phase
    ├── BLOCK   → dependency/evidence package
    └── REDESIGN → revised scope package
```

## Authority model

### Layer 1 — Repository truth
Code, real data, executable tests, logs, hashes and persisted evidence.

### Layer 2 — Antigravity
Can inspect, implement, test, refactor when necessary, and document. Cannot certify or advance phases.

### Layer 3 — External reviewer
Reviews the exact commit produced by Antigravity. Decides APPROVE / REJECT / BLOCK / REDESIGN.

### Layer 4 — Control State
`informes/CONTROL_STATE.md` is the machine-readable lock. Only an external review can advance it.

## Every Antigravity turn

Before doing work:

1. Read `informes/CONTROL_STATE.md`.
2. Read `informes/00_ADAPTIVE_IMPLEMENTATION_CONTROL.md`.
3. Read `informes/01_ADAPTIVE_MASTER_PLAN.md`.
4. Read the current `informes/fases/PHASE_<NN>_INSTRUCTIONS.md`.
5. Inspect the current repository state and recent commits.
6. Determine the smallest safe implementation scope for the current phase.

During work:

- Work ONLY on the current phase.
- Preserve existing real evidence unless the phase explicitly requires regeneration.
- Never manufacture missing data.
- Never weaken gates to increase yield.
- Never change certification state from the implementation agent.
- Never create a fake pass because an external dependency is unavailable.
- Record what is not proven.

At the end:

- Run the required tests.
- Capture exact commands and exit codes.
- Capture real data IDs/hashes where applicable.
- Create/update only the current phase execution report.
- Mark the report `READY_FOR_REVIEW`.
- STOP.

## Adaptive instructions after external review

### APPROVE
The external reviewer has verified the phase. A new package may be issued for the next phase.

### REJECT
Do not start the next phase. Create a `REWORK` instruction set describing the exact defects and the tests/evidence required to close them.

### BLOCK
Do not work around the missing dependency. Record the real dependency and the exact unblock condition.

### REDESIGN
Freeze the old scope. The external reviewer defines the new phase scope before implementation resumes.

## Required evidence packet

Every phase report must make it possible for an external reviewer to answer:

- What commit was actually audited?
- What changed?
- What commands actually ran?
- Which tests passed/failed/skipped?
- Which real datasets were used?
- Which hashes/IDs prove provenance?
- What became demonstrably true?
- What remains unproven?
- Are there P0/P1 defects?
- Did the phase exit criteria really pass?

## Research-specific controls

The discovery architecture is controlled as a research system, not as a profitability contest.

Antigravity must preserve these distinctions:

```text
DISCOVERY_SCORE ≠ CERTIFICATION
PROMISING ≠ APPROVED
HIGH ROI ≠ ROBUST EDGE
NO EVIDENCE ≠ PASS
FAILED RESEARCH ≠ SYSTEM FAILURE
```

The following are mandatory when their phase is active:

- Strategy Genome;
- behavioral diversity/clustering;
- campaign-level discovery;
- trial accounting;
- exploration/exploitation allocation;
- fertility measurement;
- cheap-to-expensive cascaded screening;
- blind OOS protection;
- mutation genealogy;
- Fragility Score;
- learning store;
- meta-strategy component eligibility.

These mechanisms are not allowed to bypass validation gates.

## Version invalidation rule

Any material change to engine, strategy contract, costs, execution model, data schema, partitioning or validation gates must identify affected evidence and force the required revalidation. Historical evidence may be used for comparison but not silently promoted as evidence of the new implementation.

## Anti-loop rule

If the same root defect appears in two consecutive reworks, do not issue a third blind implementation cycle. External review must redesign the approach.

If discovery yield remains near zero, first verify that the discovery and validation machinery is functioning correctly. Only then change search-space allocation or campaign design. Never relax evidence gates merely to create approvals.

## Human/AI handoff protocol

When the user reports that Antigravity has finished a phase, the reviewer must first inspect the repository itself. Do not rely on the user's verbal summary or Antigravity's own claims.

The reviewer reads:

`CONTROL_STATE -> phase instructions -> execution report -> commit -> changed files -> tests -> data/evidence -> contradictions`

Only after that review may the reviewer update `CONTROL_STATE` and issue the next phase instructions.
