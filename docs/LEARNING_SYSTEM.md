# ULTRARENTABLE — PERSISTENT LEARNING SYSTEM CONTRACT

## Goal
Learning exists to improve discovery and research quality from accumulated real evidence. It does not replace deterministic validation and it must never learn how to bypass Gates.

## Three memory layers

### 1. Failure memory
What failed, where, under which policy/data/regime, and with what evidence.

### 2. Experiment memory
What research hypothesis was tested, which tools were used, what changed, and what the experiment actually produced.

### 3. Knowledge memory
Aggregated evidence-supported patterns such as recurring failure modes, robust repair families, fragile transformations, regime dependencies and complexity/robustness trade-offs.

## Learning graph

```text
Strategy Version
      ↓
Failure / Success Evidence
      ↓
Research Hypothesis
      ↓
Experiment
      ↓
Mutation Proposal
      ↓
Child Strategy Version
      ↓
Independent Evaluation
      ↓
Outcome
      ↺ back to Learning Store
```

## Persistence requirement

`FailureKnowledgeDB` may be used as a runtime/cache component, but it is not sufficient as historical memory when its records exist only in process memory. A durable `LearningStore` must persist lineage and evidence references across process/VPS restarts.

## Firebase recovery

If the historical learning store exists in Firebase/Firestore on the VPS, it must be recovered before replacing it. First perform a read-only inventory/export and map the historical schema into this contract. Preserve original IDs, hashes and timestamps. Ambiguous or unverifiable records remain `UNVERIFIED`; they are never completed by inference.

## SQX feedback

SQX feedback can learn which families/cohorts are fertile or sterile from aggregated real outcomes. It must guide exploration, not optimize a single holdout or force a result.

## Blind research

Research agents must be prevented from optimizing directly against the exact hidden score/threshold of the evaluation they are trying to pass. They can consume failure diagnostics and historical knowledge, create proposals and child versions; the independent evaluator sees the new version and produces the actual verdict.

## No self-certification

Agents can propose. Tools can calculate. Engines can execute. Evidence can prove. Gates decide. No learning component may directly mark a strategy certified.
