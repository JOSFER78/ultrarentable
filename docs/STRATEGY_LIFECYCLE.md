# ULTRARENTABLE — STRATEGY LIFECYCLE & VERSION GOVERNANCE

## Canonical lifecycle

```text
GENERATED
  ↓
NORMALIZED
  ↓
FAST_FILTERED
  ↓
VALIDATION
  ↓
GATES
  ├─ structural failure → DISCARDED
  └─ promising failure → RESEARCH
                         ↓
                    NEW VERSION
                         ↓
                    REVALIDATION
                         ↓
                CURRENT CERTIFICATION
                         ↓
                    INCUBATION/LIVE
                         ↓
                   META-STRATEGY
```

The exact runtime enum names may differ in the current code; this document is the semantic contract. One code enum must eventually represent it without ambiguous aliases.

## Version immutability

A material change to strategy logic, parameters, execution, risk or other certification-relevant behavior creates a new immutable version. Never rewrite the historical definition of a certified version.

Every version must be traceable to:

- strategy_id
- version
- parent strategy/version/hash where applicable
- strategy snapshot hash
- engine/compiler version
- dataset identity/hash
- execution policy hash
- risk policy hash
- gate policy version
- creation reason/agent

## Failure triage

A failed strategy is not automatically worth research.

The deterministic triage layer should classify failure evidence into:

- `STRUCTURAL_FAILURE`: weak or broadly invalid; discard.
- `PROMISING_FAILURE`: enough gate/evidence support to justify controlled research.
- `CURRENT_POLICY_FAILURE`: may require revalidation when policy changed.
- `INSUFFICIENT_EVIDENCE`: do not call it good or bad; block until evidence exists.

This classification must be evidence-based, not an LLM vote.

## Certification staleness

A strategy certified under an older engine/compiler/dataset/execution/risk/gate policy is never silently current.

```text
CERTIFIED_CURRENT
      ↓ material policy change
STALE
      ↓
REVALIDATION_REQUIRED
      ↓
REVALIDATING
      ├─ pass → CERTIFIED_CURRENT
      └─ fail → FAILED_CURRENT_POLICY
```

Historical certification remains queryable.

## Research rule

Research may change any strategy component allowed by the track policy. It may never mutate the parent version in place. Research produces a proposal; the platform creates the immutable child version; deterministic evaluation and gates produce the verdict.
