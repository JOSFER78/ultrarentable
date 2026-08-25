# ORDER AG2-P02-005 — PHASE 02 UNIVERSAL RUNTIME CONTRACT CLOSURE

## STATUS
`ISSUED`

## OBJECTIVE
Cerrar de forma demostrable el contrato universal de ejecución de `CanonicalStrategy` sin simulaciones ni simplificaciones. Esta orden NO es para añadir otra capa conceptual: debe demostrar que la semántica canónica llega al runtime real y al boundary de ejecución/ledger, y que toda semántica no soportada falla cerrado.

## STRICT SCOPE
SOLO PHASE 02 / REWORK.
NO Phase 03.
NO Discovery Factory.
NO Strategy Genome.
NO Meta-Strategy.
NO ULTRA research implementation.
NO FONDEO implementation.
Cualquier hallazgo fuera de alcance se registra como `DEFERRED_TO_FUTURE_ORDER`.

## MANDATORY EXECUTION PLAN — DO NOT SKIP STEPS

### STEP 0 — CHECKPOINT / RECON BEFORE WRITING
Subagents required:
- RECON / REAL ENGINE TRACE
- ARCHITECTURE / SSOT

Deliverable before implementation:
`P02-005_RECON_REPORT.md`

Must contain:
- real production call sites;
- current execution/ledger boundary;
- canonical strategy consumers;
- existing legacy strategy models;
- exact semantic gaps;
- files allowed to change;
- files explicitly out of scope.

Do not implement before this checkpoint is completed.

### STEP 1 — RUNTIME CONTRACT MATRIX
Subagents required:
- CANONICAL CONTRACT
- QUANT / SEMANTIC EQUIVALENCE

Create:
`P02-005_RUNTIME_SEMANTIC_MATRIX.md`

Matrix must cover at minimum:
- LONG
- SHORT
- BOTH
- AND / OR
- indicators + params + source_field + shift
- SL types
- TP types
- trailing
- time stop
- sizing_type
- risk_value
- max_open_positions
- session start/end
- allowed_days
- close_at_eod
- engine_version
- policy_version
- dataset identity
- strategy lineage

For EACH item state:
`SUPPORTED_AND_EXECUTED` / `UNSUPPORTED_FAIL_CLOSED` / `NOT_PROVEN`.

No claim of support without an executable code path and test.

### STEP 2 — REMOVE ALL QUANTITATIVE FALLBACKS
Subagents:
- RUNTIME IMPLEMENTATION
- RED-TEAM / ZERO-MOCK

Rules:
- ATR unavailable => FAIL CLOSED.
- Unknown indicator => FAIL CLOSED.
- Missing parameter => FAIL CLOSED.
- Missing source field => FAIL CLOSED.
- Missing version identity => FAIL CLOSED.
- Missing session semantics => FAIL CLOSED if required by strategy.
- Unsupported direction => FAIL CLOSED.
- Unsupported exit type => FAIL CLOSED.

ABSOLUTELY FORBIDDEN:
- fabricated percentages;
- default ATR;
- fallback to close;
- default timeframe;
- default engine/policy version;
- silent coercion.

### STEP 3 — UNIVERSAL DIRECTION SEMANTICS
Subagents:
- RUNTIME
- QUANT
- TEST / INTEGRATION

Implement and test independently:
- LONG
- SHORT
- BOTH

Prove that price movement, SL, TP, trailing, pnl and exit price are directionally correct.

### STEP 4 — SIZING AND RISK EXECUTION
Subagents:
- QUANT / RISK
- RUNTIME
- LEDGER / LINEAGE

Demonstrate that:
- sizing_type is actually consumed;
- risk_value changes quantity/notional/risk as contract specifies;
- max_open_positions is enforced;
- unsupported sizing semantics fail closed;
- resulting trade/evidence contains the actual size/risk used.

A field existing in `CanonicalStrategy` is NOT evidence of execution.

### STEP 5 — SESSION SEMANTICS
Subagents:
- RUNTIME
- DATA
- TEST

Test:
- UTC start/end;
- allowed_days;
- close_at_eod;
- rejection/closure behavior when outside session.

No implicit all-days/all-hours behavior when the strategy requires explicit constraints.

### STEP 6 — EXIT/FILL POLICY
Subagents:
- QUANT EXECUTION
- RUNTIME
- RED-TEAM

For each supported exit type, prove behavior.
Explicitly define what happens when the same OHLC bar touches SL and TP.
Do not invent a fill rule merely to pass tests.
If the real engine has an existing fill policy, reuse it and prove binding.
If no policy exists, FAIL CLOSED and report BLOCKED instead of inventing one.

### STEP 7 — REAL ENGINE / LEDGER BINDING
Subagents:
- REAL ENGINE TRACE
- LEDGER / PROVENANCE
- API/UI PROVENANCE

Trace and document:
`CanonicalStrategy -> snapshot/serialization -> compile_to_runtime -> real adapter -> actual execution engine -> ledger/execution input`

A new toy backtester is NOT acceptable as proof.
The final evidence must identify real production call sites and prove they consume the canonical representation.

### STEP 8 — DATA PROVENANCE
Use only the canonical `DatasetRegistry` / chain-of-custody.

Prove:
- requested instrument/timeframe resolved deterministically;
- physical dataset loaded;
- dataset hash verified;
- provenance eligibility verified;
- caller cannot override dataset identity silently.

No supplied fake bars, synthetic bars or caller-supplied identity as certification evidence.

### STEP 9 — INDEPENDENT TEST MATRIX
Subagents:
- TEST / INTEGRATION
- RED-TEAM
- RELIABILITY

Tests MUST include independently:
1. LONG
2. SHORT
3. BOTH
4. AND
5. OR
6. shift semantics
7. indicator parameters
8. unsupported indicator fail-closed
9. ATR missing-data fail-closed
10. each supported SL type
11. each supported TP type
12. intrabar SL/TP conflict policy
13. trailing
14. time stop
15. sizing/risk
16. max_open_positions
17. session window
18. allowed_days
19. close_at_eod
20. lineage binding
21. dataset hash binding
22. tampered strategy hash
23. missing engine/policy identity
24. deterministic repeatability

Tests must use real repository data/evidence where quantitative execution is claimed.

### STEP 10 — MULTI-AGENT RECONCILIATION CHECKPOINT
This is mandatory and cannot be skipped.

Each subagent must produce a machine-readable row in:
`.agents/informe&seguimiento/P02-005_AGENT_LEDGER.md`

For each agent record:
- agent_id;
- role;
- task;
- files inspected;
- files changed (if any);
- commands executed;
- exit codes;
- findings;
- evidence path/hash;
- conclusion;
- unresolved items.

Then a final reconciliation section must classify every finding as:
`PROVEN`, `UNPROVEN`, `FAILED`, `DEFERRED`.

The implementer cannot be the sole verifier.

### STEP 11 — RED-TEAM GATE
A separate red-team agent must try to break the claimed closure by searching for:
- hidden defaults;
- fallback values;
- duplicate strategy authority;
- alternative execution paths;
- caller-controlled provenance;
- mocks/synthetic bars;
- lookahead;
- UI/API semantic recreation;
- tests that can pass without exercising production code.

If red-team finds a blocker, the order remains `REWORK`.

### STEP 12 — FINAL DELIVERY
Only after ALL checkpoints pass:
1. run focused Phase 02 suite;
2. run bounded regression directly affected;
3. record exact commands + exit codes;
4. verify remote jobs are complete and not stale;
5. commit;
6. push `origin/main`;
7. verify exact remote SHA;
8. create `03_HANDOFF_AG2-P02-005.md`;
9. include proven/unproven/deferred items;
10. STOP.

## SUBAGENT EXECUTION PROOF
A list of roles in the final handoff is NOT sufficient. The handoff must reference `P02-005_AGENT_LEDGER.md` and show that each required agent actually produced evidence or a recorded finding. If a subagent could not run, the order is `BLOCKED`, not `READY_FOR_REVIEW`.

## SSH / LONG JOB RULE
Long jobs must run detached/asynchronously. Record `remote_job_id`, exact command, target SHA, log path, status and exit code. Never sit 10–20 minutes waiting on SSH output.

## ZERO ABSOLUTE
ZERO-MOCK.
ZERO-SIMULATION.
ZERO-FORCING.
ZERO-LOOKAHEAD.
REAL-ONLY.
EVIDENCE-GATED.

A timeout, missing artifact, missing exit code, fabricated fallback or unsupported semantic is NEVER PASS.

## COMPLETION RULE
Do not mark this order `READY_FOR_REVIEW` because tests are green alone. The handoff must demonstrate the actual production path, subagent ledger, semantic matrix, real evidence and all required checkpoints.

After delivery: STOP. Do not create Phase 03 or any other order.
