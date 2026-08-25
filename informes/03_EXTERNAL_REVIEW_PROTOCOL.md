# EXTERNAL REVIEW PROTOCOL — ULTRARENTABLE

## Purpose

This document defines how each phase is reviewed before another phase is authorized.

## Reviewer input

The reviewer must use:

1. current repository state;
2. current commit SHA;
3. phase instruction file;
4. phase execution report;
5. relevant changed code;
6. tests and execution evidence;
7. existing data/evidence artifacts;
8. prior approved phase result.

## Review sequence

### 1. Reconstruct the change

Confirm what changed between the baseline and final commit.

### 2. Verify the central property

Identify the one invariant the phase was supposed to establish and test it directly.

### 3. Attack the claim

Look for:
- hardcoded values;
- hidden defaults;
- mocks;
- synthetic data;
- leakage;
- stale evidence;
- version mismatch;
- bypass routes;
- UI inference;
- tests that prove implementation details but not behavior.

### 4. Verify evidence chain

Confirm:

`input hash -> execution identity -> ledger -> metrics -> gates -> evidence bundle -> API/UI`

### 5. Decide

Possible outcomes:

`APPROVED`
`REJECTED`
`BLOCKED`
`REDESIGN`

## Approval contract

Approval text must state:

- phase number;
- exact audited commit;
- what was objectively proven;
- what remains unproven;
- residual risks;
- next phase authorized;
- exact next-phase objective;
- exact deliverables;
- exact exit criteria;
- any constraints carried forward.

## Rejection contract

When rejected, identify:

- blocking invariant;
- evidence demonstrating failure;
- root-cause hypothesis;
- minimum corrective work;
- tests required for re-review.

## No automatic approval

A historical report, green CI badge, test count, version tag, or developer assertion is never enough by itself.

## Promotion rule

Only `APPROVED` can unlock a new `PHASE_<NN>_INSTRUCTIONS.md` and change `CURRENT_PHASE`.

The reviewer may also shrink, expand, split, merge, reorder or replace future phases when the evidence warrants it. This is the adaptive component of the plan.
