# ANTIGRAVITY 2.0 — STRICT SCOPE EXECUTION RULE

## Absolute rule

**Antigravity executes ONLY the currently assigned `ACTIVE_ORDER_ID` and its `target_phase`.**

The master plan describes the whole program, but it is NOT a license to implement the whole program.

The active order is the only authorized engineering scope.

## What Antigravity MUST do

1. Read the control protocol, control state, active order and master plan.
2. Orchestrate the subagents required by the active order.
3. Inspect the wider repository only to understand dependencies and avoid breaking existing behavior.
4. Implement only changes necessary to satisfy the active order's explicit requirements and its direct dependency fixes.
5. Run only the focused tests and validation required for the active order, plus bounded regression checks needed to ensure the scoped change did not break existing behavior.
6. Push the scoped result to `origin/main`.
7. Create the handoff.
8. Stop.

## What Antigravity MUST NOT do

Even when discovered during reconnaissance, Antigravity MUST NOT autonomously implement:

- future phases;
- Discovery Factory work before its assigned phase;
- dataset infrastructure before Phase 01;
- meta-strategy work before its assigned phase;
- UI redesign not required by the active order;
- unrelated refactors;
- speculative architecture improvements;
- “cleanup” of unrelated legacy modules;
- fixes belonging to another phase merely because they are easy;
- broad full-project rewrites.

## Handling out-of-scope defects

If a subagent discovers a defect outside the current order:

`DISCOVER -> RECORD -> CLASSIFY -> DO NOT IMPLEMENT`

unless the active order explicitly states that the defect is a direct blocker/dependency of the current work.

The handoff must list out-of-scope findings under:

`DEFERRED_TO_FUTURE_ORDER`

with:

- file/path;
- severity;
- evidence;
- why it is outside current scope;
- suggested future phase/order.

This is preferred over silently fixing it.

## Tests are scoped too

A “full regression suite” does NOT mean Antigravity must spend the whole run waiting for unrelated project tests.

For each order:

- focused tests are mandatory;
- impacted-area regression tests are mandatory;
- broader suites may be launched asynchronously when required by the order or risk profile;
- unrelated failures are reported, not automatically repaired unless the active order makes them a direct blocker.

## Exception: direct dependency blockers

A change outside the nominal file list is permitted ONLY when all are true:

1. the active order cannot function without it;
2. the dependency is demonstrated by real code/tests;
3. the change is minimal and tightly bounded;
4. the handoff identifies it as `DIRECT_DEPENDENCY_FIX`.

No “while I'm here” work.

## Phase boundary

Finishing one order never means starting the next order.

The lifecycle is:

`ONE ORDER -> ONE SCOPE -> ONE HANDOFF -> PUSH MAIN -> STOP`

Then the external reviewer decides whether the next action is:

`REWORK | BLOCK | REDESIGN | NEXT PHASE`

The next action is delivered as a new issued order and is automatically started by the watcher.

## Zero-simulation still applies

Scope restrictions NEVER justify simulation, forcing, fake evidence, synthetic metrics, fabricated passes, arbitrary defaults or test manipulation.

`ZERO-SIMULATION = ON`
`ZERO-FORCING = ON`
`REAL-ONLY = ON`
