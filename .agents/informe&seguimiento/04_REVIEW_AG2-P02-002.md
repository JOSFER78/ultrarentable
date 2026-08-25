# REVIEW AG2-P02-002 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Qué sí terminó Antigravity
`AG2-P02-002` fue ejecutada y entregada en `origin/main` con `READY_FOR_REVIEW`. El handoff declara hashing semántico, `compile_to_runtime()`, SSOT canónico, fail-closed y pruebas. El trabajo de esta orden está terminado y no debe repetirse como el mismo dispatch.

## Auditoría del resultado real

### P02-REWORK-01 — Persisten defaults semánticos
En `contracts/canonical_strategy.py` todavía existen defaults dentro de modelos que pueden cambiar significado cuantitativo sin aparecer como resolución explícita de registry/policy, entre ellos defaults de indicador/source/shift, lógica/dirección, gestión temporal, `TargetInstrument` y metadatos de provenance. La orden P02-002 exigía fail-closed para cualquier default que altere identidad o ejecución.

### P02-REWORK-02 — `compile_to_runtime()` no demuestra equivalencia semántica completa
La instrucción runtime compilada no conserva explícitamente toda la semántica necesaria del árbol canónico. En particular, la estructura `RuleTree.logic` no forma parte de la instrucción compilada, y tampoco existe una prueba de equivalencia end-to-end que demuestre que el runtime evaluará exactamente la misma composición lógica que el canonical AST.

### P02-REWORK-03 — Runtime de producción no demostrado
La existencia de `compile_to_runtime()` y sus unit tests no demuestra que el engine de producción lo invoque. Falta una trazabilidad ejecutable y reproducible:
`CanonicalStrategy -> snapshot/compile -> adapter -> actual execution engine -> ledger/execution input`.
Debe demostrarse con tests de integración/code-path y una autoridad única de entrada al runtime.

### P02-REWORK-04 — Campos semánticos deben estar cerrados por contrato
Debe definirse formalmente qué campos son identidad semántica y cuáles son metadata no semántica. El hash actual usa transformaciones internas y modelos con defaults; antes de certificar debe existir un contrato explícito y pruebas de mutación campo-por-campo.

### P02-REWORK-05 — Linaje runtime no probado extremo a extremo
Debe demostrarse que `strategy_hash`, `strategy_version`, `engine_version`, `execution_policy_version` y dataset identity sobreviven hasta el snapshot/ledger real, no sólo existen en `CanonicalStrategy`.

## Decisión adaptativa
No avanzar a Phase 03.

Siguiente trabajo:
`AG2-P02-003` — Runtime Semantic Equivalence + Fail-Closed Canonical Defaults + Production Trace.

## STRICT SCOPE
Solo Phase 02. No Discovery, Genome, Meta-Strategy, ULTRA, FONDEO ni Phase 03.

## ZERO RULES
ZERO-SIMULATION.
ZERO-FORCING.
REAL-ONLY.
ZERO-LOOKAHEAD.
No fabricar estrategias rentables ni resultados de runtime para demostrar la arquitectura.

## Exit criteria
1. Defaults semánticos de producción eliminados o convertidos en resolución explícita/fail-closed.
2. `RuleTree.logic` y toda semántica necesaria están representadas en runtime.
3. Existe traza ejecutable real `CanonicalStrategy -> compile/snapshot -> adapter -> execution engine`.
4. Tests de integración prueban que el engine ejecuta exactamente la semántica canónica.
5. Lineage completo queda ligado al snapshot/ledger real.
6. Cambios materiales alteran hash/lineage y no heredan certificación.
7. Todo en `origin/main` con SHA remoto verificable.
