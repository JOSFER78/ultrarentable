# REVIEW AG2-P02-001 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Lo que SÍ terminó Antigravity
La orden `AG2-P02-001` fue ejecutada y entregada en `origin/main` con `READY_FOR_REVIEW`. Se añadió el contrato `CanonicalStrategy`, hashing determinista, inmutabilidad, snapshots y pruebas específicas. El handoff existe y la orden no debe volver a ejecutarse tal cual.

## Por qué todavía NO se libera Fase 02
La auditoría externa del código real encontró que la evidencia todavía no demuestra completamente el contrato pedido:

### P02-002-01 — Hash canónico completo
El hash actual no incluye todos los campos relevantes del objeto canónico, en particular `name` y `provenance`. Debe definirse formalmente qué campos son identidad semántica y demostrar que todo cambio material produce un nuevo hash/versionado.

### P02-002-02 — Runtime realmente consume CanonicalStrategy
La existencia de `StrategySnapshot` no basta. Debe trazarse y probarse la ruta real:
`CanonicalStrategy -> snapshot/compile -> runtime/engine -> execution`.
No se acepta una implementación meramente contractual sin evidencia de consumo real.

### P02-002-03 — Una sola autoridad de estrategia
El repo contiene varios contratos relacionados con ejecución/estrategia. Debe demostrarse qué es SSOT y que no existe una segunda representación autoritativa que pueda alterar reglas, parámetros o defaults.

### P02-002-04 — Defaults e identidad
La implementación contiene defaults de versión, timeframe y campos de instrumento. Debe demostrarse que no pueden convertirse en valores productivos silenciosos y que la identidad real procede del registry/policy aplicable.

### P02-002-05 — Tests de invariantes reales
Faltan pruebas focalizadas que cubran cambios de provenance/policy/engine, deriva semántica canonical->runtime, rechazo de definiciones incompletas, ausencia de overrides y detección de segunda fuente de verdad.

## Decisión adaptativa
No avanzar a Phase 03.

Siguiente trabajo:
`02.REWORK.002` — Canonical Hash Completeness + Runtime Consumption + Single Strategy SSOT + Fail-Closed Defaults.

## Alcance obligatorio
- SOLO Fase 02 / rework.
- Subagentes obligatorios.
- ZERO-SIMULATION.
- ZERO-FORCING.
- REAL-ONLY.
- No tocar Discovery, ULTRA, FONDEO, Meta-Strategy ni Phase 03.

## Criterio de salida
Liberar Fase 02 sólo cuando exista evidencia independiente de:
1. hash/version identity completa y formal;
2. consumo real del CanonicalStrategy por el runtime/engine;
3. una única autoridad canónica sin duplicados;
4. defaults no silenciosos/fail-closed;
5. tests reproducibles y evidencia real;
6. todo publicado y verificado en `origin/main`.
