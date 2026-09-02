"""services/meta/estados.py
Unificación canónica de estados de certificación para meta-estrategias (M4 / W6.0).
REAL-ONLY · ZERO-MOCKS · FAIL-CLOSED

Justificación de unificación:
----------------------------
Anteriormente existía divergencia entre módulos vivos:
- `meta_ensemble_service.py:138-145` aceptaba 6 valores de estado heterogéneos:
  {"APPROVED_CURRENT_ENGINE", "APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED",
   "CERTIFIED_PASS", "CERTIFICADA_TIER_1"}.
- `meta_strategy_pipeline.py:48` exigía exclusivamente "APPROVED_CURRENT_ENGINE".

Bajo la doctrina REAL-ONLY y la Regla #26 (engine version pinning):
- "APPROVED_CURRENT_ENGINE": Estado canónico operacional emitido por el pipeline de
  validación/certificación (`discovery_validation_pipeline.py`, `legacy_revalidation_service.py`)
  que garantiza que la estrategia superó los 11 gates bajo la versión vigente del motor
  (`CURRENT_ENGINE_VERSION`).
- "CERTIFIED_CURRENT": Estado canónico expuesto en la capa de API / contratos y frontend
  (`certified_summary_router.py`, `18_STRATEGIES_PAGE_SPEC.md`).

Estados legacy excluidos (fail-closed):
- Los estados "APPROVED", "ULTRA_CERTIFIED", "FUNDING_CERTIFIED", "CERTIFIED_PASS" y
  "CERTIFICADA_TIER_1" pertenecen a iteraciones previas sin comprobación estricta de versión
  de motor ni anclaje de gates canónicos. Aceptarlos en silencio violaría la Regla #26.
- En caso de duda o ausencia de evidencia: EXCLUIR (fail-closed).
"""

from __future__ import annotations

from typing import Optional


CERTIFIED_STATUSES: frozenset[str] = frozenset({
    "APPROVED_CURRENT_ENGINE",
    "CERTIFIED_CURRENT",
})


def es_certificada(status: Optional[str]) -> bool:
    """Evalúa si un estado corresponde a una estrategia legítimamente certificada y vigente.

    Devuelve False para None, cadenas vacías, estados rechazados (REJECTED_*),
    estados obsoletos de motor (LEGACY_*), estados sin evidencia (BLOCKED_NO_EVIDENCE, NO_EVIDENCE)
    y cualquier valor no presente en CERTIFIED_STATUSES.
    """
    if not status or not isinstance(status, str):
        return False
    clean = status.strip().upper()
    return clean in CERTIFIED_STATUSES
