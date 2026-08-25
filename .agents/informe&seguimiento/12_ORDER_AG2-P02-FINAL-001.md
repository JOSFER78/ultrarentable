# ORDER AG2-P02-FINAL-001 — FINAL DEFINITIVE CLOSURE BEFORE PHASE 03

## STATUS
`ISSUED`

## OBJECTIVE
Cerrar definitivamente la Fase 02 y dejar el sistema en un estado coherente y arrancable antes de autorizar Phase 03.

Esta es la ÚLTIMA orden de cierre de Phase 02.

NO iniciar Phase 03.
NO Discovery Factory.
NO Genome.
NO Gates.
NO Robustness.
NO Research.
NO Meta-Strategy.
NO ULTRA implementation.
NO FONDEO implementation.

El trabajo permitido es únicamente:
1. corregir blockers reales de Phase 02;
2. corregir problemas reales de arranque/integración de la aplicación que impidan verificar el sistema;
3. reconciliar documentación/control contradictorio con el estado real;
4. demostrar reproducibilidad y arranque local.

## MANDATORY SUBAGENTS

1. `CLOSURE / RECON`
2. `CANONICAL / AST`
3. `VERSION / LINEAGE`
4. `RUNTIME / EXECUTION BOUNDARY`
5. `QUANT / REPRODUCIBILITY`
6. `DATA / PROVENANCE`
7. `WEB / LOCALHOST / E2E`
8. `RED-TEAM / ZERO-MOCK`
9. `INDEPENDENT TEST / RELIABILITY`
10. `LEAD / FINAL RECONCILIATION`

El Lead NO puede ser el único verificador. Los agentes `WEB/LOCALHOST`, `RED-TEAM` e `INDEPENDENT TEST` deben revisar de forma independiente al implementador.

---

## STEP 0 — CONTROL IDENTITY

Leer desde GitHub `origin/main`:

- `00_DISPATCH.md`
- `01_CONTROL_STATE.md`
- `02_CURRENT_ORDER.md`
- `03_HANDOFF_AG2-P02-008.md`
- `04_REVIEW_AG2-P02-007.md`

Comprobar coincidencia exacta de:

`dispatch_id / order_id / target_phase / status / pre_sha / delivered_sha`

Si no coincide cualquier elemento: `BLOCKED`.

---

## STEP 1 — REVIEW P02-008 AGAINST REAL CODE

No aceptar el texto del handoff como prueba.

Revisar el código real y confirmar o refutar:

- CanonicalStrategy immutable;
- deterministic serialization;
- deterministic strategy hash;
- explicit LONG/SHORT/BOTH semantics;
- explicit AND/OR;
- indicator source/params/shift;
- exits;
- sizing/risk;
- sessions;
- provenance;
- engine/policy lineage;
- fail-closed unsupported cases;
- real execution boundary;
- ledger/result binding.

Cada claim debe quedar `PROVEN`, `UNSUPPORTED_FAIL_CLOSED`, `UNPROVEN`, `FAILED` o `BLOCKED`.

---

## STEP 2 — ZERO-FORCING AUDIT

Red-team debe buscar activamente:

- defaults cuantitativos;
- fallback a `close`;
- fallback temporal;
- fallback de ATR;
- capital por defecto;
- costes inventados;
- fills inventados;
- hashes sintéticos;
- timestamps sintéticos;
- random/seed usados para hacer pasar tests;
- tests tautológicos;
- caller-controlled provenance;
- legacy execution bypassing canonical contracts.

Cualquier hallazgo crítico = `BLOCKED` hasta corregirse.

---

## STEP 3 — DETERMINISTIC RE-RUN

Con una estrategia/dataset/versiones idénticos ejecutar DOS veces de forma independiente.

Comparar exactamente:

- execution_hash;
- ordered trades;
- timestamps;
- entry/exit prices;
- direction;
- size;
- exit_reason;
- pnl;
- ledger hash cuando aplique.

Cualquier diferencia = `BLOCKED`.

Registrar comandos, SHA de código y resultados de ambas ejecuciones.

---

## STEP 4 — REAL BOUNDARY

Probar que la ejecución certificable no es un backtester paralelo aislado.

Demostrar con call-sites reales:

`CanonicalStrategy`
→ `snapshot/serialization`
→ `compile_to_runtime`
→ runtime/adaptor
→ `EventBacktestEngine`
→ reconciliation/ledger
→ validation/certification consumer

Documentar archivos, clases, funciones y líneas reales.

---

## STEP 5 — DATA PROVENANCE

Probar:

instrument + timeframe
→ deterministic registry resolution
→ physical snapshot
→ physical bars
→ physical SHA-256
→ provenance eligibility.

No caller identity override.

Dataset ausente / hash inválido / provenance no verificable = FAIL CLOSED / NO_EVIDENCE.

---

## STEP 6 — LOCALHOST / WEB E2E — OBLIGATORIO

El proyecto NO se considera operativo si la aplicación web no puede arrancar correctamente en local.

El subagente `WEB / LOCALHOST / E2E` debe:

1. identificar el frontend real;
2. identificar el backend real;
3. comprobar `package.json`, scripts y dependencias;
4. comprobar variables de entorno requeridas;
5. comprobar si existen referencias rotas, imports rotos, rutas inexistentes o servicios que impiden arrancar;
6. ejecutar instalación usando el método oficial del repo sin introducir mocks;
7. ejecutar `npm run typecheck`;
8. ejecutar `npm run build`;
9. arrancar el frontend con el comando oficial;
10. verificar HTTP real en `http://localhost:3000`;
11. comprobar una ruta principal real de la aplicación;
12. comprobar conexión con la API si la página depende de ella;
13. comprobar backend real y su endpoint de salud/entrada correspondiente;
14. registrar puertos, PID/process id, comandos, exit codes, logs y resultado;
15. cerrar procesos de prueba al terminar.

Si el frontend no arranca:
- investigar la causa real;
- corregirla dentro del alcance;
- repetir typecheck/build/start;
- no sustituir la aplicación por una página mock;
- no levantar un servidor fake para declarar PASS.

`localhost OK` requiere proceso real + HTTP 200/resultado esperado + build/typecheck coherentes.

---

## STEP 7 — DOCUMENTATION / SSOT RECONCILIATION

No puede existir documentación pública que contradiga el estado real del sistema y se presente como SSOT.

Revisar especialmente:

- `README.md`;
- documentación de versiones;
- descripción del universo de FONDEO;
- versión de engine;
- comandos de arranque;
- estructura de la web;
- referencias a fases antiguas de documentación.

Actualizar sólo cuando la corrección refleje el código real.

No borrar historial útil: marcar legacy/stale cuando corresponda.

---

## STEP 8 — TEST / REGRESSION

Ejecutar:

- Phase 01 dataset chain-of-custody regression;
- Phase 02 canonical/runtime regression;
- version governance regression;
- deterministic rerun;
- web typecheck;
- web build;
- localhost smoke/E2E;
- bounded API health/critical-route checks.

Registrar para cada comando:

`exact command / environment / duration / exit code / target SHA / result`

No aceptar "green" sin comando reproducible.

---

## STEP 9 — FINAL RED TEAM

El red-team debe intentar romper simultáneamente:

- control de versiones;
- provenance;
- runtime;
- deterministic rerun;
- web startup;
- API/UI provenance;
- stale evidence;
- docs contradictions.

Si encuentra un blocker, corregirlo y volver a ejecutar la prueba correspondiente.

---

## STEP 10 — FINAL AGENT LEDGER

Crear:
`.agents/informe&seguimiento/P02-FINAL-001_AGENT_LEDGER.md`

Cada agente debe registrar:

- agent_id;
- role;
- exact task;
- files inspected;
- files changed;
- commands;
- exit codes;
- evidence paths/hashes;
- findings;
- conclusion;
- unresolved items.

Una lista de agentes sin evidencia NO cuenta.

---

## STEP 11 — FINAL RECONCILIATION

Crear:
`.agents/informe&seguimiento/P02-FINAL-001_RECONCILIATION.md`

Cada claim crítico debe quedar:

`PROVEN`
`UNSUPPORTED_FAIL_CLOSED`
`UNPROVEN`
`FAILED`
`BLOCKED`
`DEFERRED`

Para cerrar Phase 02:

`critical_unproven = 0`
`critical_failed = 0`
`critical_blocked = 0`

Y además:

`localhost_e2e = PASS`
`deterministic_rerun = PASS`
`git_remote_parity = PASS`

---

## STEP 12 — FINAL HANDOFF

Crear:
`.agents/informe&seguimiento/03_HANDOFF_AG2-P02-FINAL-001.md`

Debe incluir:

- exact dispatch_id;
- order_id;
- pre/post remote SHA;
- files changed;
- all critical claims;
- unsupported claims;
- unresolved/deferred items;
- exact commands and exit codes;
- localhost proof;
- deterministic rerun proof;
- production boundary proof;
- agent ledger;
- reconciliation;
- limitations.

Disposición permitida:

`READY_FOR_PHASE_03_REVIEW`

ó

`BLOCKED`

No puede autoaprobar Phase 03.

---

## SSH / LONG JOBS

Jobs largos deben ejecutarse detached/asynchronously.
Registrar:

- remote_job_id;
- exact command;
- target SHA;
- log path;
- status;
- exit code.

Nunca esperar 10–20 minutos bloqueando al orquestador si el proceso puede dejarse corriendo con seguimiento posterior.

---

## GIT / DELIVERY

Todo trabajo sobre:
`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Después:

`git status`
→ `git add`
→ `git commit`
→ `git pull --rebase origin main`
→ `git push origin main`
→ `git fetch origin main`
→ verificar exact remote SHA

Las evidencias de la orden deben existir en:
`.agents/informe&seguimiento/`

`origin/main` es la fuente que revisa el auditor externo.

---

## ZERO ABSOLUTE

ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED

No fabricar datos, resultados, hashes, fills, trades, respuestas HTTP, tests ni certificaciones.

## FINAL STOP

Cuando esta orden termine:

PUSH MAIN
→ VERIFY REMOTE SHA
→ HANDOFF
→ STOP ABSOLUTO

No crear Phase 03.
No avanzar CURRENT_PHASE.
No inventar la siguiente orden.
