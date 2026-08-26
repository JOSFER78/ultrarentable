# ORDER R0 — BOOTSTRAP / REPOSITORY HEALTH

## STATUS
`ISSUED`

## PURPOSE
Primer bloque de reparación continua. No se trabaja en cuantitativa ni en funcionalidades nuevas. El objetivo es demostrar que el repositorio puede instalarse, tiparse, compilarse y arrancar sus servicios básicos en un entorno limpio.

## STRICT SCOPE
SOLO:
- workspace Node/npm
- apps/web
- FastAPI import/startup básico
- configuración/entorno necesario para arrancar
- documentación de arranque
- tests de humo

NO:
- Discovery
- StrategyQuant
- nuevas estrategias
- Gates
- Research
- Meta-Strategies
- ULTRA
- FONDEO
- cambios cuantitativos de riesgo

## EXECUTION MODEL
Antigravity debe usar subagentes. El lead no puede ser el único verificador.

### SUBAGENTES OBLIGATORIOS
1. RECON — mapear entrypoints y scripts reales.
2. NODE/DEPENDENCY — instalación limpia y lockfile.
3. NEXT — typecheck/build/start.
4. FASTAPI — import/startup real sin workers autónomos.
5. E2E — HTTP localhost + proxy API real.
6. ZERO-MOCK — detectar datos sintéticos en rutas de arranque/UI.
7. RED-TEAM — intentar romper el arranque y detectar fallbacks.
8. LEAD — reconciliar evidencias y resolver discrepancias.

Cada subagente debe registrar comandos, exit codes, archivos revisados y conclusiones en `R0_AGENT_LEDGER.md`.

## STEP 0 — CONTROL
Leer desde GitHub main:
- `00_DISPATCH.md`
- `01_CONTROL_STATE.md`
- `02_CURRENT_ORDER.md`
- este archivo

Si order_id/dispatch/phase/status no coinciden: `BLOCKED`.

## STEP 1 — CLEAN WORKSPACE
En el repositorio real:
- comprobar Node/npm reales;
- instalación limpia usando lockfile;
- prohibido copiar `node_modules` de otra máquina;
- registrar versiones exactas;
- `git status` limpio antes de cambios.

## STEP 2 — WEB
Ejecutar:
- `npm ci` o equivalente exacto del lockfile;
- `npm --workspace apps/web run typecheck`;
- `npm --workspace apps/web run build`;
- `npm --workspace apps/web run dev`.

Demostrar:
- proceso vivo;
- HTTP 200 de `/`;
- una ruta principal real;
- proxy `/api/*` hacia backend real;
- sin mocks para declarar éxito.

## STEP 3 — BACKEND
Arrancar FastAPI en modo local sin `ULTRARENTABLE_AUTONOMOUS_RUNTIME=true`.
Demostrar import/startup y endpoint de salud/versiones.
Registrar logs y exit codes.

## STEP 4 — ZERO-MOCK STARTUP SCAN
Buscar y aislar cualquier:
- `Math.random`
- hash dataset fijo
- timestamp fijo
- capital cuantitativo por defecto usado para producir resultados
- fallback candidato→certificado
- respuesta HTTP simulada

Los fixtures de tests pueden existir sólo dentro de tests claramente marcados y nunca en rutas productivas.

## STEP 5 — REPAIR
Todo blocker descubierto dentro del alcance debe repararse antes de entregar.
No declarar éxito dejando errores conocidos como "pendientes" si bloquean el arranque.

## STEP 6 — EVIDENCE
Crear:
- `.agents/informe&seguimiento/R0_AGENT_LEDGER.md`
- `.agents/informe&seguimiento/R0_RECONCILIATION.md`
- `.agents/informe&seguimiento/03_HANDOFF_AG2-R0-BOOTSTRAP.md`

El handoff debe incluir:
- commit SHA local y remoto;
- comandos exactos;
- exit codes;
- tiempo de ejecución;
- URL localhost;
- estado FastAPI;
- blockers restantes.

## FINAL STATE
Sólo:
- `READY_FOR_NEXT_REPAIR`
- `BLOCKED`

Antigravity NO decide R1 ni modifica `CURRENT_PHASE`.

## ABSOLUTE
ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED

## STOP
Después de commit + push + verificación exacta de `origin/main`, crear handoff y STOP.