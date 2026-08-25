# ORDER AG2-P02-003 — PHASE 02 RUNTIME SEMANTIC EQUIVALENCE REWORK

## Status
`ISSUED`

## Trigger
Auto-start when `00_DISPATCH.md` contains the new matching dispatch and `CURRENT_PHASE=02`, `PHASE_STATUS=REWORK`, `ACTIVE_ORDER_ID=AG2-P02-003`.

## STRICT SCOPE
Execute ONLY this Phase 02 rework. Do not start Phase 03, Discovery Factory, Genome, Meta-Strategy, FONDEO or ULTRA work. Out-of-scope findings = `DEFERRED_TO_FUTURE_ORDER`.

## Required corrections

### P02-003-01 — Remove semantic production defaults
Audit `CanonicalStrategy` and all nested semantic contracts. Any field capable of changing quantitative meaning must be explicit or resolved from an authoritative registry/policy; otherwise fail closed. Do not replace unknowns with convenient production values.

### P02-003-02 — Complete runtime semantic representation
`compile_to_runtime()` must preserve every semantic element required for execution, including logical composition (`AND/OR`), direction, indicator parameters/source/shift, exits, sizing/risk, session rules and all required identity/provenance fields. No semantic field may disappear during compilation.

### P02-003-03 — Production code-path trace
Trace and prove the real production path:
`CanonicalStrategy -> snapshot/serialization -> compile_to_runtime -> adapter -> actual execution engine -> execution/ledger input`.
Find the real call sites. If the current engine bypasses the canonical object, refactor only what is necessary within Phase 02 so the canonical strategy is the sole source of executable semantics.

### P02-003-04 — End-to-end semantic equivalence tests
Add integration tests that construct one canonical strategy, compile it, send the compiled instruction through the real adapter/engine boundary, and assert that the resulting execution input preserves all canonical semantics. Mutate each material semantic field and prove the runtime representation changes accordingly.

### P02-003-05 — Runtime lineage binding
The real execution snapshot/ledger input must carry at minimum:
`strategy_id`, `strategy_version`, `strategy_hash`, `engine_version`, `execution_policy_version`, dataset identity/hash and canonical source commit where applicable.
Missing identity must fail closed.

### P02-003-06 — Single authority / legacy adapters
Identify duplicate legacy strategy models. If retained, they must be explicitly non-authoritative adapters with one-way conversion from CanonicalStrategy. No legacy model may independently redefine executable rules.

### P02-003-07 — Independent red-team
Search for hidden defaults, coercions, duplicated rule trees, alternative execution paths, UI/API recreation of strategy semantics, mock execution, random/seed shortcuts and lookahead.

### P02-003-08 — Evidence
Record exact commands, exit codes, test artifacts, production call sites, changed files, remote SHA and any unproven assumptions. Never write `PASS` for unproven execution paths.

## Mandatory subagents
1. RECON / EXECUTION-TRACE
2. CANONICAL CONTRACT
3. RUNTIME / ENGINE
4. QUANT / SEMANTIC-EQUIVALENCE
5. RED-TEAM / ZERO-MOCK
6. TEST / INTEGRATION
7. LINEAGE / PROVENANCE
8. RELIABILITY

Implementer cannot be sole verifier.

## SSH / VPS
Long jobs MUST be detached/asynchronous. Record `remote_job_id`, exact command, target SHA, log path, state and real exit code. Never block 10–20 minutes waiting for a remote suite.

## ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY
Absolute. Do not fabricate strategy results, runtime output, fills, ledger evidence or certification. Unit-test fixtures are not quantitative evidence.

## GitHub completion
Work on `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`. Before `READY_FOR_REVIEW`:
1. modify only scoped Phase 02 files/dependencies;
2. run focused tests + bounded regression;
3. record commands and exit codes;
4. commit;
5. push `origin/main`;
6. verify exact remote SHA;
7. create `.agents/informe&seguimiento/03_HANDOFF_AG2-P02-003.md`;
8. document call-path evidence, lineage, tests, deferred findings and proven/unproven items;
9. STOP.

Do not advance Phase 03.
