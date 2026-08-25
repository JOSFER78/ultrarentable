# ULTRARENTABLE — CONTROL OPERATIVO ÚNICO

Este directorio es el **centro de mando completo y único** de Antigravity 2.0 para ULTRARENTABLE.

Toda orden, estado, dispatch, revisión, handoff y transición operativa debe vivir aquí. El watcher de Antigravity consulta GitHub `origin/main` aproximadamente cada 3 minutos.

## 1. ARCHIVOS IMPORTANTES

| Archivo | Función |
|---|---|
| `00_CONTROL_PROTOCOL.md` | Reglas permanentes del sistema |
| `00_DISPATCH.md` | **Trigger monotónico actual**; cada `dispatch_id` nuevo = nueva ejecución |
| `00_SCOPE_EXECUTION_RULE.md` | Regla de alcance: una orden = una fase/subfase |
| `01_CONTROL_STATE.md` | Estado vivo y autoridad actual |
| `02_CURRENT_ORDER.md` | **ÚNICA orden que Antigravity puede ejecutar ahora** |
| `03_HANDOFF_<order_id>.md` | Resultado real entregado por Antigravity |
| `04_REVIEW_<order_id>.md` | Dictamen de ChatGPT después de revisar `origin/main` |
| `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` | Plan científico/técnico completo |
| `05_REVIEW_PROTOCOL.md` | Método de auditoría externa |
| `07/08/09/10/11_*ORDER*.md` | Histórico/archivo; nunca ejecutable por sí solo |
| `ULTRARENTABLE_Informe_Maestro...docx` | Doctrina histórica; nunca trigger |

**Nunca interpretar un archivo histórico como autorización.** La autorización real sale de `00_DISPATCH + 01_CONTROL_STATE + 02_CURRENT_ORDER`.

## 2. EL MODELO ES ADAPTATIVO, NO LINEAL

Las fases `00, 01, 02...` son familias de trabajo. No existe obligación de pasar directamente de `01 → 02`.

Después de cada entrega, ChatGPT revisa `origin/main` y decide exactamente el siguiente paso. Puede ser:

```text
01.0 → 01.1
01.0 → 01.REWORK.01
01.REWORK.01 → 01.REWORK.02
01.REWORK → 01.REDESIGN.01
01.x → 02.0
```

También puede decidir `BLOCK`, `SPLIT`, `MERGE` o `ABANDON`.

**Antigravity NUNCA decide cuál es el siguiente trabajo.** Ejecuta únicamente el `ACTIVE_ORDER_ID` recibido.

## 3. CICLO AUTOMÁTICO REAL

```text
CRON (~3 min)
    ↓
git fetch origin main
    ↓
lee 00_DISPATCH + 01_CONTROL_STATE + 02_CURRENT_ORDER
    ↓
¿dispatch_id nuevo + ISSUED + fase autorizada?
    ↓ SI
AUTO-START
    ↓
Antigravity 2.0
    ↓
orquesta subagentes
    ↓
trabaja SOLO el alcance de la orden
    ↓
proyecto real + SSH/VPS
    ↓
tests + evidencia + red-team
    ↓
commit + push origin/main
    ↓
verifica SHA remoto
    ↓
handoff
    ↓
STOP
    ↓
CHATGPT revisa origin/main
    ↓
decide REWORK / SUBFASE / REDESIGN / BLOCK / NEXT PHASE
    ↓
publica 04_REVIEW + nueva ORDER + NUEVO dispatch_id
    ↓
CRON vuelve a detectarlo
    ↺
```

### Qué significa realmente “ha terminado”

Cuando Antigravity crea `03_HANDOFF_<order_id>.md` con `READY_FOR_REVIEW`, **la orden ha terminado**. No debe volver a ejecutarla.

Debe quedar:

```text
ORDEN TERMINADA
→ TODO EN origin/main
→ HANDOFF
→ STOP
→ CHATGPT REVISA
```

`READY_FOR_REVIEW` **no significa** “fase aprobada”. Significa solamente “esta orden concreta fue ejecutada y entregada”.

Entonces ChatGPT puede decidir:

```text
REWORK de la misma fase
SUBFASE
REDESIGN
BLOCK
NEXT_PHASE
```

y publica una nueva orden con un `dispatch_id` nuevo.

## 4. WATCHER: QUÉ DEBE DETECTAR

El watcher **no debe esperar un archivo nuevo**. `02_CURRENT_ORDER.md` puede reutilizarse.

Debe detectar el `dispatch_id` monotónico.

Ejemplo:

```text
DISPATCH P01-004
→ ejecuta P01-004
→ handoff
→ STOP
→ ChatGPT revisa
→ DISPATCH P01-005
→ auto-start P01-005
```

Un dispatch ya entregado no se repite. Un dispatch nuevo se ejecuta aunque el anterior esté terminado.

Si el watcher conserva un ID anterior pero encuentra un dispatch nuevo `ISSUED`, **debe arrancarlo**.

## 5. UNA ORDEN = UNA FASE/SUBFASE

Antigravity puede inspeccionar todo el repositorio para entender dependencias, pero sólo puede modificar lo autorizado por `02_CURRENT_ORDER.md` y las dependencias directas demostradas.

Todo hallazgo fuera de alcance:

`DISCOVER → RECORD → CLASSIFY → DEFERRED_TO_FUTURE_ORDER`

No convertir una orden pequeña en una reescritura general.

## 6. ANTIGRAVITY + SUBAGENTES

Cada orden debe utilizar subagentes adecuados al alcance.

Patrón obligatorio:

```text
RECON
→ descomponer
→ lanzar subagentes
→ investigar en paralelo
→ reconciliar
→ implementar
→ verificación independiente
→ tests
→ evidencia
→ commit/push
→ handoff
→ STOP
```

El agente que implementa una propiedad no puede ser su único verificador.

## 7. PROYECTO REAL VS SUPERFICIE DE REVISIÓN

Workspace:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Superficie oficial:

`origin/main`

> **Lo que no está en `origin/main` no está entregado para revisión.**

Al terminar una orden debe quedar en GitHub todo lo versionable: código, tests, evidencia, handoff y documentos de control actualizados por la orden.

Debe constar el SHA exacto de `origin/main`.

## 8. SSH/VPS: EJECUTAR SIN BLOQUEARSE

Para trabajos largos:

```text
SSH
→ lanzar async/detached
→ remote_job_id
→ PID/log/status
→ continuar trabajo independiente
→ polling corto
→ exit code real
→ integrar evidencia
```

No mantener una sesión interactiva 10–20 minutos esperando una suite.

`timeout`, `sin exit code`, `job sin artefactos` o `resultado antiguo` = `UNVERIFIED`, nunca `PASS`.

## 9. ZERO-SIMULATION / ZERO-FORCING / REAL-ONLY

Siempre activos:

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Nunca inventar datos, trades, métricas, curvas, fills, hashes, datasets, provenance o resultados de tests.

Nunca convertir timeout en PASS ni modificar tests sólo para obtener verde.

## 10. ULTRA

ULTRA busca oportunidades globales dentro del universo real soportado por datos y ejecución verificables.

Objetivo de descubrimiento: `+1000% o más`.

Es una meta de investigación, nunca una licencia para forzar resultados.

No hardcodear una lista cerrada de cripto, activos o temporalidades. El universo depende del registry y de los datos reales disponibles.

## 11. FONDEO = FUTUROS ONLY

El track de FONDEO es exclusivamente futuros. Fuera del track quedan Forex/CFD y crypto-perpetuals.

La política se resuelve por:

`FIRM + PRODUCT + ACCOUNT + DATE + RULE_VERSION`

Evaluación y funded son problemas distintos:

```text
EVALUATION
→ agresividad permitida dentro de las reglas

FUNDED
→ preservación de drawdown + payout eligibility + riesgo de ruina
```

## 12. DISCOVERY FACTORY

Cuando Discovery sea autorizado:

```text
GENERATE
→ DIVERSIFY
→ DISCOVER
→ CHEAP SCREEN
→ BACKTEST
→ DISCOVERY SCORE
→ CLUSTER
→ OOS/WFO
→ ROBUSTNESS
→ RESEARCH
→ MUTATE
→ REVALIDATE
→ LEARN
→ REDISCOVER
```

Debe integrar Genome, clustering, trial accounting, genealogy, fertility, exploration/exploitation, research budgets, Fragility Score y blind research.

`DISCOVERY_SCORE != CERTIFICATION_STATUS`.

## 13. VERSIONES Y EVIDENCIA

Cambios materiales en estrategia, engine, execution, costes, datos, riesgo, gates, policy o portfolio pueden invalidar evidencia.

Una versión hija no hereda certificación automáticamente.

La evidencia debe estar ligada al lineage real: strategy version, engine version, dataset/hash, policy/version y commit remoto.

## 14. VALIDACIÓN / RESEARCH / METAESTRATEGIAS

Cadena principal:

`REAL DATA → CANONICAL STRATEGY → CURRENT ENGINE → DETERMINISTIC LEDGER → METRICS → 11 GATES → EVIDENCE → CERTIFICATION`

Research:

`FAILURE → ROOT CAUSE → CHILD → INDEPENDENT OOS → ROBUSTNESS → GATES → RESULT → LEARNING`

Las metaestrategias investigan correlación, tail correlation, drawdown concurrence, exposición, margin, capital efficiency y concentración de fallos.

## 15. 24/7

El laboratorio puede operar 24/7 con jobs duraderos, heartbeats, leases, checkpoints, retry, idempotency, watchdog, recovery y stale-evidence detection.

Runtime autónomo **no** significa que Antigravity pueda decidir cambios de arquitectura o la siguiente fase sin una nueva orden.

## 16. PLAN MAESTRO

`04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` contiene las 16 familias de fases.

Cada familia puede dividirse en tantas subfases como la evidencia requiera.

Ejemplo:

```text
PHASE 01
 ├─ 01.0
 ├─ 01.REWORK.01
 ├─ 01.REWORK.02
 ├─ 01.SUBPHASE.03
 └─ 02.0  ← sólo cuando ChatGPT lo ordene
```

## 17. QUIÉN HACE QUÉ

### Antigravity
Ejecuta exclusivamente la orden activa con subagentes, trabaja sobre el proyecto real, prueba, commit/push, entrega handoff y se detiene.

### Cron
Comprueba GitHub aproximadamente cada 3 minutos y auto-inicia cuando detecta un `dispatch_id` nuevo y autorizado.

### ChatGPT / Revisor externo
Lee `origin/main` después de cada entrega, audita el resultado real y publica la siguiente orden adaptativa.

### Usuario
No necesita aprobar manualmente cada movimiento.

## 18. ESTADO ACTUAL

```text
CURRENT_PHASE   = 01
PHASE_STATUS    = REWORK
ACTIVE_ORDER    = AG2-P01-005
ACTIVE_DISPATCH = AG2-DISPATCH-20260825-1518-P01-005
PHASE_02        = LOCKED
```

### Estado de la orden actual

`AG2-P01-005` **sí ha sido ejecutada**.

Existe:

`.agents/informe&seguimiento/03_HANDOFF_AG2-P01-005.md`

con:

`READY_FOR_REVIEW`

Por tanto Antigravity **no debe volver a ejecutar P01-005**. Debe estar en `STOP` mientras espera una nueva decisión externa.

La siguiente acción no sale del propio handoff. Sale de:

```text
CHATGPT
→ revisa origin/main
→ escribe 04_REVIEW_AG2-P01-005.md
→ decide la siguiente orden
→ crea NUEVO dispatch_id
```

## 19. REGLA FINAL PARA ANTIGRAVITY

> **Lee `00_DISPATCH.md`. Si hay un dispatch nuevo `ISSUED` y autorizado, ejecútalo automáticamente con subagentes. Ejecuta sólo esa orden. Trabaja sobre el proyecto real. Usa SSH de forma asíncrona para trabajos largos. Publica TODO lo versionable en `origin/main`. Crea el handoff y detente. Un handoff READY_FOR_REVIEW significa “orden terminada”, no “siguiente fase automática”. Después el Revisor Externo lee `origin/main`, decide la corrección o avance y publica otro dispatch. Siempre: ZERO-SIMULATION, ZERO-FORCING, REAL-ONLY.**
