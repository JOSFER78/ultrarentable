# REVIEW AG2-P02-006 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Qué sí ha mejorado
- Se eliminó el default de `account_equity_usd`.
- Se eliminó el fallback ATR a 1%.
- Se añadió sizing instrument-aware.
- Se añadió fail-closed para `max_open_positions != 1`.
- Se ampliaron los tests conductuales y el ledger de subagentes.
- Se verificó ejecución física en VPS con regresión real reportada.

## Hallazgos que impiden liberar Fase 02

### P02-006-R01 — BOTH no demostrado como semántica canónica
El runtime construye LONG/SHORT para `BOTH` mediante inversión heurística de operadores (`_invert_condition`). Esto puede alterar la semántica original de una regla y no demuestra que el contrato canónico defina explícitamente qué condiciones corresponden a cada dirección.

Debe existir una representación canónica inequívoca de las reglas bidireccionales. El runtime no puede inferir la estrategia short simplemente invirtiendo comparadores.

### P02-006-R02 — max_open_positions está soportado solo como rechazo
Rechazar `max_open_positions != 1` es válido únicamente si el contrato/matriz declara ese modo como `UNSUPPORTED_FAIL_CLOSED`. No debe presentarse como “semántica universal soportada”. La matriz debe distinguir claramente `SUPPORTED_AND_EXECUTED` de `UNSUPPORTED_FAIL_CLOSED`.

### P02-006-R03 — Evidencia de boundary sigue siendo secundaria
La entrega demuestra una ruta `CanonicalRuntimeAdapter -> EvaluatedTrade`, pero la liberación de Fase 02 exige demostrar que la semántica llega al boundary de ejecución/ledger canónico real, no solo al adaptador. Debe identificarse el caller real de producción y demostrar que consume esta representación y no otra.

### P02-006-R04 — Suites verdes no equivalen a cierre científico
33/33 tests pasando es positivo, pero no basta para certificar una propiedad si el test comprueba solo representación o una ruta alternativa. Cada claim material debe estar ligado a comportamiento, call-site y evidencia.

## Decisión
No liberar Fase 02 todavía.

## Siguiente orden
`AG2-P02-007 — Canonical Bidirectional Semantics & Real Execution Boundary Proof`

Objetivo: cerrar únicamente los defectos anteriores, sin avanzar a Fase 03.
