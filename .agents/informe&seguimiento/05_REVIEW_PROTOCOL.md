# ULTRARENTABLE — EXTERNAL REVIEW PROTOCOL

This is the review contract between Antigravity 2.0 and the external reviewer.

## Reviewer role

The external reviewer audits the actual repository after every order. The handoff is a pointer to evidence, not proof by itself.

Review sequence:

`CONTROL_STATE -> CURRENT_ORDER -> HANDOFF -> START/FINAL COMMIT -> DIFF -> REAL CODE PATH -> TESTS/LOGS -> DATA/HASHES -> LEDGER/EVIDENCE -> VERSIONING -> API/UI -> CONTRADICTIONS -> EXIT CRITERIA`

## Approval standard

`APPROVED` requires:

- the order scope is actually implemented;
- the phase's central invariant is directly demonstrated;
- required focused and regression tests are real and reproducible;
- real data/evidence are provenance-linked;
- no P0/P1 blocker remains in scope;
- no mock, synthetic, fallback or hardcoded result contaminates the claim;
- version invalidation/revalidation behavior is correct where relevant;
- negative findings are not hidden;
- what remains unproven is explicit.

A green test suite alone never equals APPROVED.

## Outcomes

### APPROVED

1. Record exact audited commit.
2. State what was objectively proven.
3. State residual risks.
4. Adapt the next phase if evidence requires it.
5. Change `01_CONTROL_STATE.md`.
6. Create/update the next `02_CURRENT_ORDER.md`.
7. Publish exact subagent roles, inspections, tests and evidence required next.

### REJECTED

Keep the same phase. Publish a new order ID for rework with exact failing invariants, corrective changes and required evidence. No downstream phase becomes actionable.

### BLOCKED

Identify the real missing dependency or evidence. Define the unblock condition. Do not permit a simulated workaround.

### REDESIGN

Invalidate the current scope, explain the evidence-driven reason and issue a new bounded order. Future phases remain locked until re-planned.

## Special discovery review

Discovery is reviewed as a research process, not an approval-count contest. Verify:

- Strategy Genome and behavioral diversity;
- campaign coverage;
- trial accounting;
- novelty/deduplication;
- fertility measurement;
- exploration/exploitation allocation;
- cascaded screening efficiency;
- Discovery Score vs Certification separation;
- whether high ROI is being mistaken for robust edge;
- whether research is learning from failures without learning to game gates.

## Special version review

For every material change, verify strategy_version, engine_version, contract_version, data_snapshot_id, data_sha256, code_commit_sha, trial_id, validation_run_id and evidence_bundle_id. Old evidence cannot silently certify a new engine/contract/data/gate policy.

## Special Firebase review

Firebase recovery must be forensic first. No write/delete is acceptable before discovery, snapshot, schema reconstruction and reconciliation are proven. Ambiguous records remain UNVERIFIED.

## Final rule

The reviewer does not tell Antigravity merely to “continue”. Every approved review creates a concrete next order. Every rejected review creates bounded rework. Every blocked review defines the real unblock condition. Every redesign creates a new scope before implementation resumes.
