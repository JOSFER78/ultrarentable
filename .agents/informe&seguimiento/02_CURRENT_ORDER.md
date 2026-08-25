# ORDER AG2-P02-006 — PHASE 02 BEHAVIORAL RUNTIME PROOF & EXECUTION-BOUNDARY VERIFICATION

## STATUS
`ISSUED`

## OBJECTIVE
Cerrar R01-R09 de la revisión de P02-005 demostrando **comportamiento real** y trazabilidad hasta el execution boundary. No se acepta evidencia basada sólo en presencia de campos, compilación o tests estructurales.

## STRICT SCOPE
SOLO PHASE 02 / REWORK.
NO Phase 03.
NO Discovery Factory.
NO Strategy Genome.
NO Meta-Strategy.
NO ULTRA implementation.
NO FONDEO implementation.

## MANDATORY EXECUTION PLAN — DO NOT SKIP

### STEP 0 — CONTROL IDENTITY
RECON + RELIABILITY.
Registrar exactamente el `dispatch_id` leído desde GitHub y conservar la misma identidad en todo el handoff. Verificar SHA inicial remoto. Cualquier inconsistencia = BLOCKED.

### STEP 1 — BEHAVIORAL CASE DESIGN
QUANT + TEST.
Diseñar casos físicos reproducibles para LONG, SHORT y BOTH; BOTH debe producir una ejecución LONG real y una SHORT real en casos físicos separados. Diseñar también casos de sizing, sesiones, EOD, time-stop y max_open_positions.

### STEP 2 — REMOVE CAPITAL DEFAULT
RUNTIME + RED-TEAM.
Eliminar cualquier default monetario cuantitativo en runtime, incluido `account_equity_usd`. Capital/equity debe ser obligatorio y trazable a account/track/policy. Ausencia = FAIL CLOSED.

### STEP 3 — TRUE BOTH
RUNTIME + QUANT + TEST.
Demostrar comportamiento, no sólo que el instruction conserve `BOTH`. El motor debe producir LONG y SHORT reales. Si el engine universal no soporta simultaneidad/alternancia, rechazar explícitamente la semántica no soportada.

### STEP 4 — TRUE POSITION MODEL
RUNTIME + QUANT/RISK + LEDGER.
Implementar realmente `max_open_positions` o rechazar explícitamente valores no soportados. El resultado debe reflejar cantidad de posiciones y tamaño efectivo. No basta con leer el campo.

### STEP 5 — TRUE INSTRUMENT-AWARE SIZING
QUANT/RISK + DATA/PROVENANCE.
Demostrar origen real de tick value/point value/contract multiplier cuando aplique y cómo se convierte riesgo monetario en contratos/unidades. Prohibido asumir `USD / price` como sizing universal. Si falta contrato del instrumento: FAIL CLOSED.

### STEP 6 — SESSION / EOD BEHAVIOR
RUNTIME + DATA + TEST.
Demostrar con timestamps físicos: start/end, allowed_days, ventanas que cruzan medianoche y close_at_eod. Probar entradas y cierres reales fuera/dentro de sesión.

### STEP 7 — REAL FILL POLICY
REAL ENGINE TRACE + QUANT + RED-TEAM.
Localizar la política de fills del engine universal. Si existe, reutilizarla y probar binding. Si no existe, declarar BLOCKED y no inventar una prioridad/fill para cerrar el test.

### STEP 8 — REAL EXECUTION BOUNDARY
REAL ENGINE TRACE + LEDGER/LINEAGE + API/UI PROVENANCE.
Demostrar call-sites reales: `CanonicalStrategy -> snapshot/serialization -> compile -> adapter -> universal engine -> execution/ledger input`. Un backtester paralelo no puede servir como prueba del engine real.

### STEP 9 — BEHAVIORAL TEST MATRIX
TEST + RED-TEAM + RELIABILITY.
Cada claim crítico debe tener al menos un test de comportamiento sobre resultado de ejecución. Mantener tests estructurales como complemento, no como sustituto.

### STEP 10 — INDEPENDENT CROSS-AGENT REVIEW
8 subagentes obligatorios: RECON, RUNTIME, QUANT, DATA, TEST, RED-TEAM, LINEAGE, RELIABILITY.
Cada uno registra: agent_id, role, task, files inspected, files changed, commands, exit codes, unique evidence, findings, conclusion, unresolved items.
Al menos dos agentes independientes deben revisar `BOTH`, `sizing` y `fill policy`.

### STEP 11 — RECONCILIATION GATE
El lead debe clasificar cada claim como `PROVEN / UNPROVEN / FAILED / BLOCKED / DEFERRED`. Cualquier claim crítico UNPROVEN bloquea READY_FOR_REVIEW.

### STEP 12 — FINAL DELIVERY
Sólo tras cerrar Steps 0-11: focused tests, bounded regression, remote jobs completos, exit codes, commit, push origin/main, SHA remoto exacto, handoff completo y STOP.

## REQUIRED EVIDENCE FILES
- `P02-006_RECON_REPORT.md`
- `P02-006_BEHAVIORAL_CASE_MATRIX.md`
- `P02-006_AGENT_LEDGER.md`
- `P02-006_EXECUTION_BOUNDARY_TRACE.md`
- `P02-006_RECONCILIATION.md`
- `03_HANDOFF_AG2-P02-006.md`

## SUBAGENT EXECUTION PROOF
No se acepta una lista de nombres. Cada agente debe dejar evidencia verificable. Si un agente obligatorio no pudo ejecutar su tarea, el estado es `BLOCKED`, no READY_FOR_REVIEW.

## SSH / LONG JOBS
Ejecutar jobs largos detached/asíncronos; registrar remote_job_id, comando exacto, target SHA, logs, estado y exit code. Nunca bloquear 10–20 minutos esperando una suite.

## ZERO ABSOLUTE
ZERO-MOCK.
ZERO-SIMULATION.
ZERO-FORCING.
ZERO-LOOKAHEAD.
REAL-ONLY.
EVIDENCE-GATED.

No fabricar capital, sizing, fills, métricas, datasets, hashes, trades ni resultados de pruebas.

## COMPLETION RULE
Tests verdes no equivalen a cierre. Sólo puede marcarse READY_FOR_REVIEW cuando el comportamiento real, la trazabilidad al boundary y la evidencia independiente estén demostrados en `origin/main`. Después: STOP.
