# REVIEW AG2-P01-004 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Lo que SÍ ha terminado Antigravity
AG2-P01-004 sí ejecutó su alcance de Fase 01, creó el registro de aliases, eliminó las transformaciones difusas, añadió validaciones y publicó el resultado en `origin/main`. El handoff existe y declara pruebas ejecutadas. Por tanto, la orden está entregada para revisión; no debe volver a ejecutarse.

## Lo que NO se puede considerar todavía certificado
La entrega no libera Fase 01 porque quedan dos problemas de diseño:

### P01-005-01 — Alias registry como artefacto independiente
`contracts/alias_contracts.py` contiene los registros oficiales como constantes de código. El hash es reproducible, pero el registro no es todavía un artefacto de datos independiente, versionado y validable como SSOT sin depender de recompilar código.

Debe existir un artefacto canónico de alias versionado/hashable, con loader fail-closed y prueba de que el runtime consume exactamente ese artefacto.

### P01-005-02 — UNVERIFIED no puede comportarse como provenance válida
`DatasetRegistry` usa `UNVERIFIED` como valor de `source_id`. Eso puede ser correcto como estado de evidencia, pero debe impedir que el dataset sea tratado como elegible para backtests/certificación que exijan provenance verificable.

Debe distinguirse explícitamente:
`VERIFIED`, `UNVERIFIED`, `NO_EVIDENCE`, `INVALID`.

Y los consumers deben demostrar que no aceptan un dataset `UNVERIFIED` cuando la operación exige provenance certificada.

### P01-005-03 — Cross-check completo de identidad
La validación actual comprueba `data_sha256`, pero la autoconsistencia debe comparar explícitamente, cuando exista manifest:
`source_id + instrument_id + timeframe_id + snapshot_id + version metadata`
contra la identidad que expone el registry.

Cualquier discrepancia debe ser fail-closed.

## Decisión adaptativa
No avanzar a Phase 02 todavía.

Siguiente trabajo:
`01.REWORK.005` — Provenance Eligibility + Alias Artifact SSOT + Full Manifest Identity Cross-check.

## Reglas
- SOLO Fase 01 / subfase de rework.
- ZERO-SIMULATION.
- ZERO-FORCING.
- REAL-ONLY.
- No tocar Discovery, ULTRA, FONDEO, Meta-Strategy ni Phase 02.

## Criterio de salida
Fase 01 sólo podrá liberarse cuando exista evidencia de que:
1. el alias registry es un artefacto versionado/hashable consumido por runtime;
2. `UNVERIFIED/NO_EVIDENCE/INVALID` no puede entrar en rutas que exigen provenance verificada;
3. el manifest y registry son completamente consistentes en identidad;
4. tests independientes lo demuestran;
5. todo está en `origin/main` con SHA remoto verificable.
