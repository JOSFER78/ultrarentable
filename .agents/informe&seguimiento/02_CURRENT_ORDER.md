# ORDER AG2-P02-007 — CANONICAL BIDIRECTIONAL SEMANTICS & REAL EXECUTION BOUNDARY PROOF

## STATUS
`ISSUED`

## OBJECTIVE
Cerrar exclusivamente los defectos detectados en la revisión de `AG2-P02-006`. No avanzar a Fase 03.

## STRICT SCOPE
SOLO PHASE 02 / REWORK.
No Discovery, Genome, Meta-Strategy, ULTRA research, FONDEO.

## MANDATORY PLAN
### STEP 0 — CONTROL IDENTITY
- Verificar que `dispatch_id`, `order_id`, phase y status coinciden entre `00_DISPATCH`, `01_CONTROL_STATE` y `02_CURRENT_ORDER`.
- Handoff final debe usar exactamente el dispatch vigente.

### STEP 1 — CANONICAL BOTH SEMANTICS
- Revisar el contrato canónico para determinar cómo se expresa una estrategia LONG/SHORT/BOTH.
- Prohibido inferir SHORT mediante inversión heurística de comparadores si el contrato no lo define así.
- Si BOTH requiere dos ramas explícitas, representarlas en el AST/contracto y compilarlas sin pérdida semántica.
- Si el contrato no soporta una forma concreta, `UNSUPPORTED_FAIL_CLOSED`.

### STEP 2 — BEHAVIORAL PROOF
Diseñar casos físicos reproducibles donde una misma estrategia BOTH produzca de forma demostrable:
- una entrada LONG;
- una entrada SHORT;
- ausencia de entrada cuando ninguna rama se cumple.

Los tests deben inspeccionar dirección, precio, salida y PnL reales.

### STEP 3 — MAX OPEN POSITIONS CONTRACT
- Clasificar explícitamente `max_open_positions > 1` como `UNSUPPORTED_FAIL_CLOSED` si el motor sigue siendo single-position.
- No declarar “universalmente soportado” algo que se rechaza.
- Añadir esa clasificación a la matriz canónica y a los tests.

### STEP 4 — REAL EXECUTION BOUNDARY
- Mapear el caller de producción que invoca el engine universal.
- Demostrar el recorrido:
  `CanonicalStrategy -> snapshot/serialization -> compile_to_runtime -> real execution boundary -> ledger/execution input`.
- Identificar archivos, funciones y líneas de llamada reales.
- No usar el adaptador aislado como sustituto del engine de producción.

### STEP 5 — INDEPENDENT VERIFICATION
Subagentes obligatorios:
1. RECON / BOUNDARY
2. CANONICAL / AST
3. QUANT / BIDIRECTIONAL
4. RUNTIME
5. LEDGER / PROVENANCE
6. TEST / BEHAVIOR
7. RED-TEAM
8. RECONCILIATION

Cada uno debe producir evidencia en `P02-007_AGENT_LEDGER.md`.

### STEP 6 — TESTS
- focused Phase 02 tests;
- boundary integration tests;
- regression affected by changed runtime.

Green tests alone do not close the order.

### STEP 7 — DELIVERY
Antes de `READY_FOR_REVIEW`:
- evidence complete;
- all required agents have ledger rows;
- real boundary proven;
- exact dispatch identity consistent;
- commit;
- push `origin/main`;
- verify remote SHA;
- create `03_HANDOFF_AG2-P02-007.md`;
- STOP.

## ZERO ABSOLUTE
ZERO-MOCK.
ZERO-SIMULATION.
ZERO-FORCING.
ZERO-LOOKAHEAD.
REAL-ONLY.
EVIDENCE-GATED.
