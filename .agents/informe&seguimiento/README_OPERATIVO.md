# ULTRARENTABLE — CONTROL OPERATIVO ÚNICO

Este directorio es el centro de mando completo y único de Antigravity 2.0 para ULTRARENTABLE.

Toda orden, estado, dispatch, revisión, handoff y transición operativa debe vivir aquí. El watcher consulta GitHub `origin/main` aproximadamente cada 3 minutos.

## 1. AUTORIDAD REAL

La única orden ejecutable se determina por la combinación coherente de:

```text
00_DISPATCH.md
+
01_CONTROL_STATE.md
+
02_CURRENT_ORDER.md
```

Los archivos históricos, el plan maestro y este README explican el sistema, pero NO autorizan por sí mismos una ejecución.

## 2. MODELO ADAPTATIVO

Las fases son familias de trabajo, no una escalera rígida.

```text
01.0
→ 01.REWORK.01
→ 01.REWORK.02
→ 01.2
→ 01.REDESIGN.01
→ 02.0
```

Después de cada entrega, ChatGPT revisa `origin/main` y decide exactamente el siguiente trabajo.

Antigravity nunca decide la siguiente fase.

## 3. GENEALOGÍA DE ÓRDENES

La cadena real es siempre:

```text
ORDEN N
→ HANDOFF
→ REVISIÓN EXTERNA
→ DECISIÓN
→ ORDEN N+1 / REWORK / SUBFASE / REDESIGN
→ NUEVO dispatch_id
→ AUTO-START
```

Ejemplo real de este proyecto:

```text
AG2-P01-005
→ REVIEW P01-005 = APPROVED_FOR_NEXT_PHASE
→ AG2-P02-001
→ HANDOFF P02-001
→ REVIEW P02-001 = REWORK
→ AG2-P02-002
→ HANDOFF P02-002
→ STOP
→ ChatGPT revisa
```

Por tanto, `AG2-P02-002` NO aparece de la nada. Es consecuencia de `04_REVIEW_AG2-P02-001.md`, que ordenó explícitamente el rework de la Fase 02. fileciteturn202file0

## 4. CUÁNDO AUTO-INICIAR

El cron debe:

1. hacer `git fetch origin main`;
2. leer `00_DISPATCH.md`, `01_CONTROL_STATE.md`, `02_CURRENT_ORDER.md` desde `origin/main`;
3. comprobar `dispatch_id`, `order_id`, `status`, `target_phase`, `CURRENT_PHASE` y `ACTIVE_ORDER_ID`;
4. ejecutar automáticamente solo si:

```text
dispatch_id = NUEVO
status = ISSUED
target_phase = CURRENT_PHASE
ACTIVE_ORDER_ID = order_id
no existe otra orden activa
```

No necesita un archivo nuevo.
No necesita confirmación manual del usuario.

## 5. CUÁNDO PARAR

Cuando la orden actual esté terminada:

```text
implementación
→ tests/evidencia
→ commit
→ push origin/main
→ verificación SHA remoto
→ handoff READY_FOR_REVIEW
→ STOP
```

`READY_FOR_REVIEW` significa únicamente:

> LA ORDEN ACTUAL HA TERMINADO Y HA SIDO ENTREGADA.

No significa que Antigravity pueda empezar otra orden.

La siguiente orden solo existe cuando ChatGPT publica un nuevo `dispatch_id`.

## 6. UNA ORDEN = UN SOLO ALCANCE

Antigravity puede inspeccionar el repositorio entero, pero solo modifica lo autorizado por `02_CURRENT_ORDER.md` y las dependencias directas demostradas.

Fuera de alcance:

`DISCOVER → RECORD → CLASSIFY → DEFERRED_TO_FUTURE_ORDER`

No reparar todo el repositorio aprovechando una orden pequeña.

## 7. ANTIGRAVITY + SUBAGENTES

Cada orden debe ejecutarse con subagentes adecuados:

```text
RECON
→ descomponer
→ subagentes en paralelo
→ reconciliar
→ implementar
→ verificación independiente
→ tests
→ evidencia
→ commit/push
→ handoff
→ STOP
```

El implementador no puede ser el único verificador.

## 8. PROYECTO REAL VS REVISIÓN

Workspace real:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Superficie oficial de auditoría:

`origin/main`

> LO QUE NO ESTÁ EN `origin/main` NO ESTÁ ENTREGADO.

Todo lo versionable de una orden debe quedar publicado en `main`.

## 9. SSH/VPS SIN BLOQUEAR

Los procesos largos se ejecutan de forma asíncrona:

```text
SSH
→ launch async/detached
→ remote_job_id
→ PID/log/status
→ continuar trabajo independiente
→ polling
→ exit code real
```

Nunca mantener el orquestador esperando 10–20 minutos.

Timeout, falta de exit code, job incompleto o evidencia antigua = `UNVERIFIED`, nunca `PASS`.

## 10. ZERO-SIMULATION / ZERO-FORCING

Siempre:

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Nunca inventar datasets, trades, métricas, curvas, hashes, fills, provenance, candidatos ni resultados de tests.

## 11. ULTRA

ULTRA investiga oportunidades globales dentro del universo soportado realmente por datos y ejecución verificables.

Objetivo de descubrimiento: `+1000% o más`.

No hardcodear una lista cerrada de activos o temporalidades. El universo debe venir del registry y de datos reales.

La meta de +1000% no autoriza jamás relajar validación.

## 12. FONDEO = FUTUROS ONLY

El track FONDEO usa exclusivamente futuros.

Excluir Forex/CFD y crypto-perpetuals.

Las reglas se resuelven por:

`FIRM + PRODUCT + ACCOUNT + DATE + RULE_VERSION`

Separar siempre `EVALUATION RISK != FUNDED RISK`.

## 13. DISCOVERY FACTORY

Cuando el plan autorice Discovery:

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

Debe incluir Genome, clustering, trial accounting, genealogy, fertility, exploration/exploitation, research budgets, Fragility Score y blind research.

`DISCOVERY_SCORE != CERTIFICATION_STATUS`.

## 14. VERSIONES Y EVIDENCIA

Cambios materiales en estrategia, engine, ejecución, costes, datos, riesgo, policy, gates o portfolio pueden invalidar evidencia.

Una versión hija no hereda certificación automáticamente.

## 15. PLAN MAESTRO

`04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` contiene las familias de fases.

Cada fase puede subdividirse sin límite fijo si la evidencia lo exige.

## 16. QUIÉN DECIDE QUÉ

### Antigravity
Ejecuta la orden activa, usa subagentes, trabaja sobre el proyecto real, prueba, publica en `main` y se detiene.

### Cron
Detecta el `dispatch_id` nuevo y auto-inicia la orden autorizada.

### ChatGPT / Revisor externo
Lee `origin/main`, audita el resultado real y decide el siguiente trabajo.

### Usuario
No tiene que aprobar manualmente cada transición.

## 17. ESTADO ACTUAL

El estado autoritativo debe leerse siempre de `01_CONTROL_STATE.md` y `00_DISPATCH.md` en `origin/main`.

No copiar aquí una fase/orden fija porque este README se convertiría en una segunda fuente de verdad.

## 18. LECTURA OBLIGATORIA DEL WATCHER

Antes de ejecutar, el watcher debe leer también:

`.agents/informe&seguimiento/ORDER_README_FOR_ANTIGRAVITY.md`

Ese archivo explica la genealogía, la diferencia entre `READY_FOR_REVIEW` y una nueva orden y cómo interpretar `dispatch_id`.

## 19. REGLA FINAL

> Antigravity ejecuta únicamente la orden representada simultáneamente por `00_DISPATCH + 01_CONTROL_STATE + 02_CURRENT_ORDER`. Trabaja con subagentes, usa SSH/VPS de forma asíncrona, entrega todo en `origin/main`, crea el handoff y se detiene. ChatGPT revisa `origin/main`, decide el siguiente trabajo y publica un nuevo `dispatch_id`. Siempre: ZERO-SIMULATION, ZERO-FORCING, REAL-ONLY.
