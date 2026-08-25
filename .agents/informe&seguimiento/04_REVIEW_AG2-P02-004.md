# REVIEW AG2-P02-004 — DECISIÓN EXTERNA

## Resultado
`REWORK`

## Auditoría de origin/main
La orden `AG2-P02-004` fue entregada como `READY_FOR_REVIEW`, pero la revisión del código real demuestra que aún no satisface completamente el contrato de runtime universal.

### R01 — Fallback cuantitativo prohibido
`services/execution/canonical_runtime_adapter.py` todavía usa `entry_price * 0.01` cuando ATR no está disponible en `ATR_MULTIPLE`. Esto es un valor cuantitativo fabricado y viola ZERO-SIMULATION / ZERO-FORCING. Debe fallar cerrado.

### R02 — Dirección incompleta
El runtime ejecuta la lógica de salida sólo para `LONG`. El contrato permite `LONG`, `SHORT` y `BOTH`. No existe evidencia suficiente de semántica correcta de `SHORT` y `BOTH`.

### R03 — Sizing/risk no ejecutado de forma demostrable
`SizingAndRisk` está presente en la estrategia, pero la ejecución no demuestra que `risk_value`, `max_open_positions` y las reglas de tamaño participen realmente en la producción de trades/ledger.

### R04 — Session semantics incompleta
`session_window`, `allowed_days` y `close_at_eod` no están demostrados como restricciones reales del execution path.

### R05 — Semántica intrabar/fill incompleta
Cuando en una misma vela se alcanzan SL y TP, no está demostrada una política canónica de prioridad/fill. La ejecución sobre OHLC no puede declarar equivalencia universal sin una política explícita y pruebas.

### R06 — Cobertura de tests insuficiente para los claims
La suite cubre algunos casos, pero no prueba de forma independiente SHORT, BOTH, sizing/risk, session/day/EOD, ATR sin dato, conflicto SL/TP intrabar ni rejection de combinaciones no soportadas.

### R07 — Evidencia de subagentes insuficiente
El handoff enumera 8 roles pero no entrega un ledger verificable por subagente con: tarea, archivos inspeccionados, hallazgos, comandos/tests ejecutados, conclusión, evidencia y reconciliación. Enumerar nombres no demuestra trabajo independiente.

## Decisión adaptativa
No liberar Phase 02.

Siguiente trabajo:
`AG2-P02-005` — Universal Runtime Contract Closure + Independent Multi-Agent Verification.

## Regla de ejecución
Antigravity debe seguir el plan de esta orden por pasos y no puede declarar `READY_FOR_REVIEW` hasta completar todos los checkpoints de subagentes y evidencia. La orden no debe ejecutarse de forma superficial o como un parche rápido.

## STOP
Al finalizar P02-005: publicar todo en `origin/main`, verificar SHA, crear handoff completo y detenerse. Antigravity no crea la siguiente orden.
