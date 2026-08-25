# ORDER AG2-P02-008 — FINAL PHASE 02 CLOSURE / INDEPENDENT CERTIFICATION

## STATUS
`ISSUED`

## OBJECTIVE
Cerrar definitivamente Phase 02 — Canonical Strategy + Version Governance + Runtime Semantic Contract.

Esta es la **última orden de Phase 02**.

NO añadir nuevas funcionalidades de Discovery, Robustness, Gates, Research, Meta-Strategy, ULTRA o FONDEO.
NO avanzar a Phase 03 por iniciativa propia.

La misión es demostrar que todo lo construido en Phase 02 es coherente, reproducible, versionado y conectado al boundary real, y que cualquier limitación no soportada queda expresamente `UNSUPPORTED_FAIL_CLOSED`.

## PRINCIPIO
P02-008 es una auditoría de cierre, no una carrera por hacer más código.

El implementador puede corregir blockers encontrados dentro del alcance de Phase 02, pero no puede ampliar el alcance ni inventar evidencia.

## MANDATORY SUBAGENTS

1. `RECON / PHASE-02-CLOSURE`
2. `CANONICAL / AST & SERIALIZATION`
3. `VERSION / LINEAGE / CERTIFICATION`
4. `RUNTIME / EXECUTION-BOUNDARY`
5. `QUANT / REPRODUCIBILITY`
6. `DATA / PROVENANCE`
7. `RED-TEAM / ZERO-MOCK`
8. `TEST / INDEPENDENT-VERIFIER`
9. `RELIABILITY / GIT-CONTROL`
10. `LEAD / RECONCILIATION`

El Lead no puede ser el único verificador. Al menos tres subagentes independientes deben revisar los claims críticos.

## STEP 0 — CONTROL IDENTITY / GIT INTEGRITY

Verificar desde GitHub `origin/main`:

- `00_DISPATCH.md`
- `01_CONTROL_STATE.md`
- `02_CURRENT_ORDER.md`
- handoff P02-007
- review P02-007

Comprobar exactamente:

`dispatch_id`
`order_id`
`target_phase`
`status`
`pre_sha`
`delivered_sha`

Si existe cualquier incoherencia: `BLOCKED`.

No aceptar nombres de archivos locales como evidencia.

## STEP 1 — CANONICAL STRATEGY CLOSURE

Auditar el contrato canónico completo.

Demostrar:

- estrategia inmutable;
- hash determinista;
- serialización determinista;
- semántica LONG/SHORT/BOTH explícita;
- AND/OR;
- indicadores, parámetros, source_field y shift;
- exits;
- sizing/risk;
- session policy;
- provenance;
- strategy_version;
- engine_version;
- policy_version.

Para cada propiedad clasificar:

`SUPPORTED_AND_EXECUTED`
`UNSUPPORTED_FAIL_CLOSED`
`NOT_PROVEN`

No se permite `PROVEN` por mera presencia de un campo.

## STEP 2 — BOTH / BIDIRECTIONAL FINAL PROOF

Verificar que `BOTH` usa ramas declarativas explícitas y no inversión heurística.

Diseñar dos casos físicos independientes:

A) sólo branch LONG dispara -> debe producir LONG.
B) sólo branch SHORT dispara -> debe producir SHORT.

Añadir un caso:

C) ambas ramas disparan simultáneamente -> debe respetarse exactamente la política canónica documentada.

Añadir un caso:

D) ninguna rama dispara -> 0 entradas.

La evidencia debe proceder del runtime real, no de una simple inspección del objeto compilado.

## STEP 3 — UNSUPPORTED SEMANTICS / FAIL-CLOSED

Verificar especialmente:

- `max_open_positions > 1`;
- cualquier sizing no soportado;
- exit type no soportado;
- indicator no soportado;
- source field inexistente;
- engine/policy version ausente;
- dataset no elegible;
- strategy hash alterado.

Cada caso debe demostrar rechazo real.

No convertir `UNSUPPORTED` en `SUPPORTED` para aumentar cobertura.

## STEP 4 — VERSION / LINEAGE / INVALIDATION

Demostrar que:

`strategy_id + strategy_version + strategy_hash`

quedan enlazados con:

`engine_version + execution_policy_version + dataset_snapshot + dataset_sha256`.

Demostrar además que una modificación material genera una nueva identidad/evidencia y no hereda silenciosamente certificación previa.

Probar al menos:

- cambio de regla;
- cambio de engine version;
- cambio de policy version;
- cambio de dataset hash.

Cada cambio debe quedar `REVALIDATION_REQUIRED` o equivalente canónico.

## STEP 5 — REAL EXECUTION BOUNDARY

Revalidar la cadena real:

`CanonicalStrategy`
→ `snapshot/serialization`
→ `compile_to_runtime`
→ `CanonicalRuntimeAdapter`
→ `EventBacktestEngine`
→ `CrossEngineReconciler` cuando aplique
→ `ledger / execution result`
→ `validation/certification consumers`

No aceptar un backtester paralelo como sustituto.

Identificar call-sites reales por archivo y línea.

## STEP 6 — DATA PROVENANCE FINAL

Comprobar que el runtime no acepta identidad arbitraria del caller.

Debe resolver mediante la cadena canónica:

instrument + timeframe
→ registry
→ snapshot
→ physical bars
→ sha256
→ provenance eligibility.

Hash manipulado = FAIL CLOSED.
Dataset ausente = FAIL CLOSED.
Dataset no verificable = NO_EVIDENCE/BLOCKED.

## STEP 7 — REPRODUCIBILITY / DETERMINISM

Ejecutar por separado, en la misma revisión, al menos dos veces:

`same strategy snapshot + same dataset snapshot + same engine/policy versions`

y demostrar igualdad de:

- execution hash;
- ordered trades;
- entry/exit timestamps;
- prices;
- sizes;
- exits;
- pnl;
- ledger hash si corresponde.

Si difieren: `BLOCKED`.

## STEP 8 — RED TEAM FINAL

Buscar activamente:

- defaults escondidos;
- fallbacks;
- random/seed shortcuts;
- mocks/synthetic bars;
- lookahead;
- caller-controlled provenance;
- duplicate strategy authority;
- legacy path bypassing CanonicalStrategy;
- tests tautológicos;
- UI/API recreando semántica;
- stale evidence;
- mismatched version lineage.

Todo hallazgo debe quedar registrado.

## STEP 9 — INDEPENDENT TESTER

El equipo independiente debe ejecutar:

1. suite Phase 02;
2. dataset chain-of-custody regression;
3. version governance regression;
4. targeted behavioral tests;
5. deterministic rerun.

Registrar exactamente:

- comando;
- entorno;
- exit code;
- duración;
- commit probado;
- resultado.

## STEP 10 — AGENT LEDGER

Crear:
`.agents/informe&seguimiento/P02-008_AGENT_LEDGER.md`

Cada agente debe registrar:

- agent_id;
- role;
- task;
- files inspected;
- files changed;
- commands;
- exit codes;
- unique findings;
- evidence paths/hashes;
- conclusion;
- unresolved items.

No vale una lista nominal de agentes.

## STEP 11 — FINAL RECONCILIATION

Crear:
`.agents/informe&seguimiento/P02-008_RECONCILIATION.md`

Cada claim debe quedar:

`PROVEN`
`UNPROVEN`
`FAILED`
`BLOCKED`
`DEFERRED`

Para cerrar Phase 02:

`CRITICAL_CLAIMS = 100% PROVEN OR EXPLICITLY UNSUPPORTED_FAIL_CLOSED`

Cualquier `UNPROVEN` crítico = `BLOCKED`.

## STEP 12 — FINAL HANDOFF

Crear:
`.agents/informe&seguimiento/03_HANDOFF_AG2-P02-008.md`

Debe contener:

- exact dispatch_id;
- exact order_id;
- pre-SHA;
- delivered remote SHA;
- cambios realizados;
- claims proven;
- claims unsupported/fail-closed;
- claims unproven;
- comandos y exit codes;
- agent ledger;
- reconciliation;
- deferred items;
- limitaciones reales;
- decisión propuesta: `READY_FOR_PHASE_03_REVIEW` o `BLOCKED`.

## ZERO ABSOLUTE

`ZERO-MOCK`
`ZERO-SIMULATION`
`ZERO-FORCING`
`ZERO-LOOKAHEAD`
`REAL-ONLY`
`EVIDENCE-GATED`

No se permite fabricar fills, trades, hashes, datasets, métricas, resultados ni estados de certificación.

## SSH / LONG JOBS

Los trabajos largos deben ejecutarse detached/asíncronamente.
Registrar:

- remote_job_id;
- comando exacto;
- target SHA;
- log path;
- status;
- exit code.

No bloquear el orquestador esperando 10–20 minutos una suite.

## COMPLETION

Cuando termine esta orden:

`commit`
→ `push origin/main`
→ verificar SHA remoto
→ handoff
→ `STOP ABSOLUTO`

NO crear Phase 03.
NO cambiar `CURRENT_PHASE` hacia adelante.
NO autoaprobar Phase 02.

La decisión de liberar Phase 03 corresponde al revisor externo después de leer `origin/main`.
