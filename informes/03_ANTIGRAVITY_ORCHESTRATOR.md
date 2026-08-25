# ULTRARENTABLE — ANTIGRAVITY 2.0 ORCHESTRATOR

## Purpose

This document is the operational control plane for Antigravity 2.0.

The model is explicitly **two-level**:

```text
EXTERNAL RESEARCH CONTROL (ChatGPT)
              ↓
       PHASE AUTHORITY
              ↓
      ANTIGRAVITY 2.0
              ↓
       SUBAGENT TEAM
              ↓
   IMPLEMENT / TEST / AUDIT
              ↓
       EVIDENCE REPORT
              ↓
        STOP + HANDOFF
```

Antigravity 2.0 is the **execution/orchestration agent**. It is responsible for using its own subagents to inspect, implement, test and cross-check the current phase. It is **not** the certification authority and it is **not** allowed to advance the program by itself.

ChatGPT is the external reviewer/control authority: it reads the actual repository and evidence after each phase, decides the disposition, and writes or authorizes the next phase package.

## 1. Non-negotiable control loop

```text
CONTROL_STATE
    ↓
CURRENT PHASE PACKAGE
    ↓
ANTIGRAVITY ORCHESTRATOR
    ↓
SUBAGENTS
    ├── RESEARCH / CODE INSPECTION
    ├── IMPLEMENTATION
    ├── TESTING
    ├── DATA / PROVENANCE AUDIT
    └── ADVERSARIAL / REGRESSION REVIEW
    ↓
INTEGRATION BY ANTIGRAVITY
    ↓
REAL TESTS + REAL DATA
    ↓
PHASE EXECUTION REPORT
    ↓
STOP
    ↓
EXTERNAL REVIEW
    ├── APPROVE    → next phase package
    ├── REJECT     → same-phase rework package
    ├── BLOCK      → dependency/evidence unblock package
    └── REDESIGN   → revised phase scope package
```

There is **no automatic transition from one phase to another**.

## 2. Authority model

### Layer 1 — Repository truth

Highest authority:

- code actually executed;
- actual commit SHA;
- real datasets and hashes;
- test execution and logs;
- generated ledgers;
- evidence bundles;
- persisted database state;
- API responses generated from the audited commit.

Documentation and UI claims are lower authority.

### Layer 2 — Antigravity 2.0

Antigravity may inspect the whole repository, plan the current phase, delegate work to subagents, implement, test, integrate and stop when evidence is insufficient.

Antigravity may NOT:

- approve a phase;
- certify a strategy;
- advance `CURRENT_PHASE`;
- mark historical evidence as valid for a new engine/version;
- weaken a gate to create approvals;
- invent a missing result;
- conceal a failed subagent result;
- declare success solely because tests compile or pass.

### Layer 3 — Antigravity subagents

**All substantive phase work must be executed through Antigravity's subagent system whenever the IDE supports it.**

The main agent must behave as an orchestrator, not as a monolithic coder.

Use role-separated subagents when applicable:

1. **RECON / ARCHITECTURE** — map current code paths, dependencies and contracts before edits.
2. **IMPLEMENTATION** — perform the smallest scoped code changes.
3. **TEST / VERIFICATION** — design and execute focused and regression tests.
4. **DATA / EVIDENCE** — verify real-data provenance, hashes, ledgers and evidence artifacts.
5. **ADVERSARIAL / RED-TEAM** — search for bypasses, mocks, hidden defaults, lookahead, stale evidence and false-positive certification paths.
6. **UI / PROVENANCE** — use when API/UI behavior is in scope; verify displayed values come from canonical evidence.
7. **DISCOVERY-RESEARCH** — use when Discovery phases are active; evaluate Genome, diversity, trial accounting, campaign fertility and exploration/exploitation.

Not every phase needs every role. Antigravity chooses the smallest set that gives independent coverage and records which roles were used and why.

A subagent that implements code must not be the only authority verifying that same code.

### Layer 4 — External reviewer

After a phase is delivered, ChatGPT reviews the exact repository state and evidence packet.

Only the external review can decide:

`APPROVE | REJECT | BLOCK | REDESIGN`

### Layer 5 — CONTROL_STATE

`informes/CONTROL_STATE.md` is the machine-readable lock. Only an external review may advance or alter phase-authority fields.

## 3. Mandatory startup protocol

At the start of every Antigravity turn/session:

1. Read `informes/CONTROL_STATE.md`.
2. Read `informes/00_ADAPTIVE_IMPLEMENTATION_CONTROL.md`.
3. Read `informes/01_ADAPTIVE_MASTER_PLAN.md`.
4. Read `informes/02_ANTIGRAVITY_PHASE_RUNBOOK.md`.
5. Read this file.
6. Read the current `informes/fases/PHASE_<NN>_INSTRUCTIONS.md`.
7. Inspect the current commit and recent changes.
8. Check for any previous phase execution report.
9. Confirm exactly which phase is authorized.
10. Stop rather than improvise if the control state is incompatible with execution.

## 4. Mandatory subagent orchestration

For every non-trivial phase, follow:

```text
ORCHESTRATOR
    ↓
DECOMPOSE CURRENT PHASE
    ↓
CREATE BOUNDED SUBTASKS
    ↓
ASSIGN SUBAGENTS
    ↓
COLLECT FINDINGS
    ↓
CROSS-CHECK DISAGREEMENTS
    ↓
IMPLEMENT
    ↓
RUN VERIFICATION SUBAGENTS
    ↓
INTEGRATE
    ↓
FINAL REAL TESTS
    ↓
EVIDENCE PACKET
```

### Subagent isolation

Every subagent must receive the exact phase and bounded subtask. It must report files inspected, files changed, commands executed and results; distinguish `PROVEN`, `UNVERIFIED`, `BLOCKED` and `FAILED`; never invent outputs; never silently change phase scope; and surface conflicting findings.

Important negative findings must survive into the final phase report.

### Parallelism

Subagents may work in parallel on read-only investigation.

Write operations must be coordinated by the main Antigravity agent. Independent subagents must not edit the same file, schema or contract simultaneously. Independent implementation streams must be integrated one at a time with relevant tests rerun after each integration.

## 5. Required review scope for every phase

Before `READY_FOR_REVIEW`, Antigravity must check:

### Functional

- requested behavior is implemented;
- real execution paths use it;
- no bypass/dead path defeats it.

### Architecture

- canonical contracts remain authoritative;
- no competing source of truth exists;
- evidence/gate architecture is not bypassed.

### Data

- inputs are real;
- dataset versions and hashes are known;
- IS/Validation/OOS isolation remains intact.

### Quantitative

Where applicable: deterministic calculations, no-lookahead, canonical costs/slippage, no hidden constants, correct sample sizes, trial accounting, multiple-testing awareness and robust OOS treatment.

### Integrity

Check operational paths for mocks, synthetic data, random generators, fake trades, placeholder hashes, hardcoded metrics, evidence bypasses, mutable evidence and certification inference.

### Version governance

Verify:

`strategy_version`
`engine_version`
`contract_version`
`data_snapshot_id`
`data_sha256`
`code_commit_sha`
`trial_id`
`validation_run_id`
`evidence_bundle_id`

Material changes must invalidate affected evidence where required.

### UI/API provenance

When applicable: canonical API output, read-only certification UI, `NO_EVIDENCE` for missing data, no UI-derived approval, and traceability from displayed values to evidence.

### Regression

Run focused tests plus the global regression suite available to the repository. A green test suite is evidence of test behavior, not automatic proof of the phase objective.

## 6. Special protocol for Discovery Engine phases

When Discovery is in scope, Antigravity must use specialized research subagents where supported and report:

```text
campaigns
trial_count
family_count
genome_count
unique_behavior_count
duplicate_rate
retained_count
rejected_count
fertility_by_family
budget_allocation
explore_vs_exploit
Discovery Score distribution
Fragility distribution
```

Preserve:

`DISCOVERY_SCORE != CERTIFICATION_STATUS`

`HIGH ROI != ROBUST EDGE`

Discovery optimizes search quality, diversity and research value rather than approval count.

## 7. End-of-phase handoff

At the end of a phase create:

`informes/fases/PHASE_<NN>_EXECUTION_REPORT.md`

The report must include:

1. Scope
2. Phase objective
3. Start commit
4. Final commit
5. Subagents used and roles
6. Subagent findings summary
7. Files changed
8. Architecture impact
9. Exact commands executed
10. Test results with exit codes
11. Real data/evidence used
12. Hashes/IDs
13. Discovery statistics when applicable
14. Defects found
15. Contradictions found
16. Residual risks
17. What was NOT proven
18. External dependencies/blockers
19. Exact exit-criteria assessment
20. `READY_FOR_REVIEW`

The report must never contain `APPROVED`.

Then Antigravity must **STOP WORK**.

## 8. How ChatGPT updates and guides the project

After Antigravity stops, ChatGPT reviews the repository itself using this sequence:

```text
CONTROL_STATE
→ CURRENT PHASE INSTRUCTIONS
→ EXECUTION REPORT
→ START/FINAL COMMIT
→ DIFF / CHANGED FILES
→ CODE PATHS
→ TESTS / LOGS
→ REAL DATA / HASHES
→ EVIDENCE BUNDLES
→ UI/API PROVENANCE
→ HISTORICAL CONTRADICTIONS
→ P0/P1 RISKS
→ EXIT CRITERIA
```

### APPROVE

ChatGPT records why the phase is proven, identifies residual risks, adapts the next phase if evidence warrants, updates `CONTROL_STATE.md`, creates or updates `PHASE_<NN+1>_INSTRUCTIONS.md`, and explicitly states what Antigravity must read, which subagents to use, what each subagent must inspect, what tests must run and what evidence must be returned.

### REJECT

ChatGPT keeps the same phase active, identifies failing invariants, specifies exact corrections, specifies new tests/evidence, and creates/updates a rework package. Downstream phases remain locked.

### BLOCK

ChatGPT names the missing real dependency, defines the exact unblock condition, prohibits simulation/workarounds that falsify evidence, and keeps the phase blocked.

### REDESIGN

ChatGPT invalidates the old scope, records the evidence-driven reason, defines a new bounded scope and issues a new instruction package.

This means **ChatGPT does not merely say “continue”**. Every approval produces the next concrete execution package for Antigravity.

## 9. Adaptive planning rule

The master plan is a hypothesis, not a prison. Evidence may cause the reviewer to split/merge phases, insert forensic work, remove features, postpone subsystems, change implementation order, redesign discovery campaigns, change research allocation or introduce validation experiments.

Adaptation happens **before the next phase is executed**. Antigravity must never anticipate the next adaptation or start future work without an explicit unlocked package.

## 10. Anti-gaming rules

Never loosen thresholds because few strategies pass; delete failed candidates; hide negative runs; rerun until favorable without trial accounting; mutate OOS using holdout information; reuse parent evidence for mutated children; replace real data with fixtures in operational paths; convert `NO_EVIDENCE` into zero/PASS; change tests merely for green output; or declare certification from a UI card, score or label.

If research produces zero certified strategies, report zero. That is scientifically valid.

## 11. Stopping rules

Antigravity stops immediately when the phase is complete and reported, when a P0 invariant blocks continuation, when a real dependency is unavailable, when evidence is insufficient, when scope would expand, or when work would require changing `CONTROL_STATE`.

## 12. Responsibility matrix

| Responsibility | Antigravity | Subagents | ChatGPT external reviewer |
|---|---|---|---|
| Inspect repository | YES | YES | YES |
| Plan current phase | YES | support | YES at review |
| Implement | YES | YES, delegated | NO |
| Run tests | YES | YES | verify evidence |
| Investigate data | YES | YES | YES, audit |
| Build evidence | YES | YES, support | verify |
| Find defects | YES | YES | YES |
| Decide phase APPROVED | NO | NO | YES |
| Advance phase | NO | NO | YES |
| Change control authority | NO | NO | YES |
| Certify strategy | NO | NO | YES / canonical evidence |

## 13. Golden rule

**Antigravity works. Its subagents investigate. The repository provides the evidence. ChatGPT audits. Only then does the next instruction exist.**
