> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: hallazgo P0 del 2026-08-25 ya integrado en la gobernanza vigente (17_PHASE2_EXECUTION_STATUS.md y master §4). **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# P0 Audit — Approved/Gates Metrics Integrity — 2026-08-25

## Finding
The candidates API and the previous Gates UI were capable of presenting derived/fallback values as if they were certified quantitative evidence.

### Confirmed backend issues

1. `/api/v1/candidates/summary` calls `compute_financial_metrics(..., 2.4, ...)`, hardcoding 2.4 months for annualization.
2. `/api/v1/candidates` and `/api/v1/candidates/{id}` use fallback duration data (`3840` bars and derived OOS months) when duration evidence is absent.
3. `passed_count` can be inferred as `11` solely because `status` is APPROVED/ULTRA_CERTIFIED/FUNDING_CERTIFIED, without requiring explicit evidence for Gates 1–11.
4. Missing drawdown values are converted to `0.0`, which is misleading because missing DD is not zero DD.
5. Missing SHA-256 can fall back to a hash constructed from candidate metadata; that is not the canonical strategy hash.
6. The previous frontend could derive approval/gate states from PF/DD and invent missing values (e.g. symbol/timeframe/engine defaults).

## Evidence example
`data/evidence/UR-SEM-MES-4D730A/evidence_bundle.json` contains `gates_evaluation.approved=true` and only `gate_01=PASSED`; it does not contain explicit evidence for Gates 2–11. This cannot be displayed as 11/11 certification.

## Required contract

- Missing metric -> `null` / `N/D`, never 0.
- Missing duration -> no annualized/monthly ROI.
- Missing explicit Gates 1–11 -> `NO_EVIDENCE`, never 11/11.
- Certification requires an explicit evidence bundle covering the current gate policy.
- Canonical hash must come from the canonical strategy/bundle; never derive a pseudo-hash from metadata.
- UI must never infer certification from status alone.

## Immediate mitigation applied
`apps/web/app/estrategias/5-estrategias-aprobadas/page.tsx` and `apps/web/app/gates/page.tsx` now use `CertifiedStrategiesTable`, which only displays `11/11 VERIFICADO` when explicit Gate 1–11 evidence exists and otherwise displays `NO_EVIDENCE`. The view no longer displays annual ROI from the contaminated summary calculation.

## Next backend repair
Refactor the candidate summary/detail APIs so they expose raw evidence-backed metrics only and remove all fabricated duration, Gate-count, DD, and hash fallbacks. Then rebuild the Gates/certification view on the canonical evidence contract.
