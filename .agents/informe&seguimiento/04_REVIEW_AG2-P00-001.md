# EXTERNAL REVIEW — AG2-P00-001

## Decision

`REWORK`

## Reviewed repository

`origin/main` as delivered by AG2-P00-001.

## Reason

The forensic baseline achieved its primary objective: it established the executable reality and exposed concrete defects with reproducible evidence. The phase should not be treated as a clean engineering baseline because three P0 defects affect foundational trust:

1. synthetic/precomputed portfolio curves in `ultra_portfolio_engine.py`;
2. broken/ghost FastAPI lifespan imports;
3. missing version-lineage modules used by certification/lineage paths.

Additional P1 integrity defects were also identified in API/UI certification paths.

## Disposition

Do not enter Data Chain-of-Custody implementation while these foundational P0 issues remain active.

Issue `AG2-P00-002` as an adaptive same-phase remediation order.

## What was accepted from the baseline

- forensic mapping of executable architecture;
- identified real datasets and evidence paths;
- identified 11-gate implementation and bypass risks;
- identified version/lineage gaps;
- identified UI/API provenance defects;
- identified 24/7 reliability behavior;
- preserved Firebase/RTDB recovery snapshot without writes.

## What remains unaccepted

The current implementation is not yet safe as a trusted production/certification baseline because the P0 defects can produce false portfolio output, mask startup failures, and break version/evidence lineage.

## Next order

`.agents/informe&seguimiento/07_ORDER_AG2-P00-002.md`

The order is now intended to become the active `02_CURRENT_ORDER.md` with `status: ISSUED` and `CURRENT_PHASE: 00` / `PHASE_STATUS: REWORK`.

## Reviewer rule

Antigravity does not wait for a user confirmation. The next watcher cycle after the new order is published must automatically execute AG2-P00-002.
