# ULTRARENTABLE — CONTROL OPERATIVO ÚNICO

Este directorio es el **centro de mando completo y único** de Antigravity 2.0 para ULTRARENTABLE.

No debe existir otro sistema paralelo de fases/control que pueda contradecirlo. Toda orden, estado, dispatch, revisión y handoff operativo debe vivir aquí.

## 1. QUÉ ES CADA ARCHIVO

| Archivo | Función |
|---|---|
| `00_CONTROL_PROTOCOL.md` | Reglas permanentes: watcher, auto-start, subagentes, SSH/VPS, `origin/main`, Zero-Simulation |
| `00_DISPATCH.md` | **Trigger monotónico actual**. Un `dispatch_id` nuevo = una nueva ejecución autorizada |
| `01_CONTROL_STATE.md` | Estado vivo: fase, subfase, orden, estado y transición actual |
| `02_CURRENT_ORDER.md` | **ÚNICA orden ejecutable ahora** |
| `03_HANDOFF_TEMPLATE.md` | Contrato de entrega de Antigravity |
| `03_HANDOFF_<order_id>.md` | Entrega real de cada orden finalizada |
| `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` | Plan completo del laboratorio y sus 16 fases |
| `04_REVIEW_<order_id>.md` | Revisión externa de ChatGPT y decisión sobre el siguiente trabajo |
| `05_REVIEW_PROTOCOL.md` | Método de auditoría de `origin/main` |
| `07_* / 08_* / 09_*` | Órdenes históricas/reservas; nunca son ejecutables si no están en `02_CURRENT_ORDER.md` + `00_DISPATCH.md` |
| `ULTRARENTABLE_Informe_Maestro...docx` | Doctrina maestra histórica/arquitectónica; contexto, nunca trigger |

## 2. EL MODELO ES ADAPTATIVO, NO LINEAL

Las “fases 00, 01, 02…” son **familias de trabajo**, no un camino obligatorio e irreversible.

Después de cada entrega, ChatGPT revisa `origin/main` y decide exactamente el siguiente paso. Puede ser:

```text
FASE 01.0
→ FASE 01.1
→ FASE 01.2
→ FASE 01.REWORK.1
→ FASE 01.REDESIGN.1
→ FASE 02.0
```

También puede usar:

`SPLIT | MERGE | BLOCK | REDESIGN | REWORK | ABANDON | NEXT_PHASE`

**Antigravity no decide cuál es el siguiente paso.** Antigravity ejecuta únicamente el `ACTIVE_ORDER_ID` que haya sido publicado como `ISSUED`.

## 3. CICLO AUTOMÁTICO COMPLETO

```text
Antigravity watcher (~3 min)
        ↓
lee 00_DISPATCH + 01_CONTROL_STATE + 02_CURRENT_ORDER
        ↓
nuevo dispatch_id + ISSUED + phase autorizada
        ↓
AUTO-START
        ↓
Antigravity orquesta subagentes
        ↓
trabaja sobre el proyecto real
        ↓
SSH/VPS async cuando corresponda
        ↓
trabajo paralelo; nunca espera bloqueado
        ↓
tests + evidencia + red-team
        ↓
commit
        ↓
push origin/main
        ↓
verifica SHA remoto
        ↓
handoff
        ↓
STOP
        ↓
ChatGPT lee origin/main
        ↓
CORRECCIÓN / REWORK / SUBFASE / REDESIGN / BLOQUEO / SIGUIENTE FASE
        ↓
ChatGPT publica nueva ORDER + nuevo dispatch_id
        ↓
cron la detecta
        ↺
```

No existe un paso de “preguntar al usuario si empieza”.

## 4. REGLA DE ALCANCE

Una ejecución = **una sola orden + una sola fase/subfase**.

Antigravity puede inspeccionar todo el repositorio para entender dependencias, pero sólo puede modificar lo autorizado por la orden activa y las dependencias directas demostradas.

Todo hallazgo fuera de alcance:

`DISCOVER → RECORD → CLASSIFY → DEFERRED_TO_FUTURE_ORDER`

Nunca “aprovechar” una orden para arreglar todo el repo.

## 5. ANTIGRAVITY = EJECUTOR + ORQUESTADOR DE SUBAGENTES

En cada orden debe:

```text
RECON
→ descomponer el alcance
→ lanzar subagentes relevantes en paralelo
→ reconciliar hallazgos
→ implementar
→ verificación independiente
→ ejecutar pruebas
→ revisar evidencia
→ commit/push
→ handoff
→ STOP
```

Un agente que implementa una propiedad no puede ser su único verificador.

## 6. PROYECTO REAL VS SUPERFICIE DE REVISIÓN

Workspace real:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Superficie oficial de revisión:

`origin/main`

Por tanto:

> **LO QUE NO ESTÁ EN `origin/main` NO ESTÁ ENTREGADO.**

Al terminar una orden, todo lo versionable debe quedar en `main`, incluido el handoff y los documentos de control actualizados por esa orden.

## 7. SSH/VPS — NUNCA BLOQUEARSE

Para procesos largos:

```text
SSH
→ launch async/detached
→ remote_job_id
→ PID/log/status
→ continuar trabajo independiente
→ polling acotado
→ exit code real
→ integrar resultado
```

Nunca mantener una sesión interactiva abierta 10–20 minutos esperando una suite.

`timeout`, `job lento`, `sin exit code` o `sin artefactos` = `UNVERIFIED`, nunca `PASS`.

## 8. ZERO-SIMULATION / ZERO-FORCING

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Prohibido inventar datos, hashes, trades, curvas, fills, métricas, resultados, provenance o evidencia de gates.

Los fixtures/mocks sólo pueden existir en tests unitarios aislados y nunca son evidencia cuantitativa.

## 9. ULTRA

ULTRA es el laboratorio global de oportunidades. Puede investigar cualquier mercado/instrumento/TF soportado por el registry y por datos/ejecución reales.

Objetivo de descubrimiento: `+1000% o más`.

Ese objetivo **nunca autoriza** relajar validación ni fabricar resultados.

## 10. FONDEO = FUTUROS ONLY

El track de FONDEO excluye Forex/CFD y crypto-perpetuals.

Debe resolver políticas por:

`FIRM + PRODUCT + ACCOUNT + DATE + RULE_VERSION`

con universo real permitido, sesiones, límites, trailing/max loss, DLL, target, consistencia y payout rules.

`EVALUATION RISK != FUNDED RISK`.

## 11. DISCOVERY FACTORY

Cuando Discovery entre en la fase autorizada:

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

Debe conservar Genome, clustering, trial accounting, genealogy, fertility, exploration/exploitation, budgets, Fragility Score y blind OOS/research.

`DISCOVERY_SCORE != CERTIFICATION_STATUS`.

## 12. VERSIONES Y CERTIFICACIÓN

Cambios materiales de estrategia, motor, ejecución, costes, riesgo, datos, policy, gates o portfolio pueden invalidar evidencia.

Una versión hija no hereda certificación automáticamente.

Estados: `CERTIFIED_CURRENT`, `CERTIFIED_LEGACY`, `STALE`, `REVALIDATION_REQUIRED`, `REVALIDATING`, `FAILED_CURRENT_POLICY`.

## 13. VALIDACIÓN Y RESEARCH

Cadena objetivo:

`REAL DATA → CANONICAL STRATEGY → CURRENT ENGINE → DETERMINISTIC LEDGER → METRICS → 11 GATES → EVIDENCE → CERTIFICATION`

Research:

`FAILURE → ROOT CAUSE → RESEARCH PROPOSAL → IMMUTABLE CHILD → INDEPENDENT OOS → ROBUSTNESS → GATES → RESULT → LEARNING`

El holdout no puede usarse para diseñar la mutación que luego será certificada con el mismo holdout.

## 14. METAESTRATEGIAS

Investigar:

- correlation;
- tail correlation;
- drawdown concurrence;
- exposure overlap;
- risk contribution;
- margin;
- capital efficiency;
- regime diversification;
- failure concentration.

ULTRA: convexidad agregada/capital efficiency.

FONDEO: sólo futuros y reglas reales de la firma/producto/cuenta.

## 15. 24/7

El laboratorio puede operar 24/7 con durable jobs, heartbeats, leases, checkpoints, retry, idempotency, watchdog, recovery y stale-evidence detection.

Pero runtime autónomo **no** significa cambios arquitectónicos autónomos.

## 16. PLAN MAESTRO

`04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` contiene las 16 familias de fases:

```text
00 Forensic Baseline / Reality Lock
01 Data Chain of Custody
02 Canonical Strategy + Version Governance
03 Deterministic Universal Execution Engine
04 Discovery Factory
05 Independent Validation + 11 Gates
06 Robustness / WFO / Purged Validation
07 Research + Reprogramming Lab
08 Learning Store + Firebase Recovery
09 Paper / Forward Incubation
10 FONDEO Futures Evaluation Lab
11 FONDEO Funded Preservation Lab
12 ULTRA Bullet / Convexity Lab
13 Meta-Strategy / Portfolio Discovery
14 Certification + UI + API + Continuous Revalidation
15 24/7 Operations / Self-Audit / Disaster Recovery
```

Estas fases **pueden tener tantas subfases como la evidencia requiera**.

## 17. QUIÉN DECIDE

### Antigravity
Ejecuta la orden actual con subagentes, trabaja en el proyecto real, prueba, commit/push y entrega.

### Cron
Detecta el `dispatch_id` nuevo y auto-inicia la orden autorizada.

### ChatGPT / revisión externa
Lee `origin/main`, audita lo que realmente se hizo y decide la siguiente orden adaptativa.

### Usuario
No necesita aprobar manualmente cada movimiento.

## 18. ESTADO ACTUAL

```text
CURRENT_PHASE   = 01
PHASE_STATUS    = REWORK
ACTIVE_ORDER    = AG2-P01-003
ACTIVE_DISPATCH = AG2-DISPATCH-20260825-1440-P01-003
PHASE_02        = LOCKED
```

## 19. REGLA FINAL

> **Antigravity ejecuta exactamente una orden/fase con subagentes y evidencia real. Todo resultado acaba en `origin/main`. ChatGPT revisa `origin/main` y, según lo que realmente encuentra, puede crear una subfase correctiva, otra rework, un redesign o avanzar a la siguiente fase. Cada nueva decisión genera un NUEVO `dispatch_id`. El cron lo detecta automáticamente. Siempre: ZERO-SIMULATION, ZERO-FORCING, REAL-ONLY.**
