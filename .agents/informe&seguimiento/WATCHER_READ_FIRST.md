# ANTIGRAVITY 2.0 — WATCHER: LEER ESTO PRIMERO

## MODELO ÚNICO Y SIMPLE

ULTRARENTABLE tiene **UN SOLO PLAN MAESTRO**:

`.agents/informe&seguimiento/04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md`

Ese documento contiene TODAS las fases y el objetivo global del proyecto.

**El plan maestro NO es una cola de trabajo.**
**El plan maestro NO se ejecuta automáticamente.**
**El plan maestro NO te dice qué fase debes ejecutar ahora.**

La fase que debes ejecutar ahora la publica el Revisor Externo (ChatGPT) mediante una nueva orden y un nuevo `dispatch_id`.

## TU TRABAJO COMO ANTIGRAVITY

Tu comportamiento es siempre:

```text
LEER ORDEN ACTIVA
↓
EJECUTAR SOLO ESA ORDEN
↓
SUBAGENTES
↓
IMPLEMENTAR / PROBAR / VERIFICAR
↓
PUSH origin/main
↓
HANDOFF
↓
STOP
↓
ESPERAR NUEVA ORDEN DEL REVISOR EXTERNO
```

**NO debes decidir el siguiente trabajo.**

## LOS 3 ARCHIVOS QUE DETERMINAN SI TIENES TRABAJO

Lee desde `origin/main` únicamente:

1. `.agents/informe&seguimiento/00_DISPATCH.md`
2. `.agents/informe&seguimiento/01_CONTROL_STATE.md`
3. `.agents/informe&seguimiento/02_CURRENT_ORDER.md`

Los tres deben apuntar al MISMO `order_id` y a la MISMA fase.

### Qué significa cada uno

`00_DISPATCH.md` = **disparador**. Un `dispatch_id` NUEVO significa una nueva orden del Revisor Externo.

`01_CONTROL_STATE.md` = **estado vivo**. Indica `CURRENT_PHASE` y `ACTIVE_ORDER_ID`.

`02_CURRENT_ORDER.md` = **orden exacta que debes ejecutar ahora**.

## EL PLAN MAESTRO

Debes conocer el plan maestro para entender dónde encaja la orden actual, pero **NO debes avanzar por el plan por tu cuenta**.

Ejemplo:

```text
PLAN MAESTRO
  PHASE 00
  PHASE 01
  PHASE 02
  PHASE 03
  ...
  PHASE 15
```

Si ChatGPT publica:

```text
CURRENT_PHASE = 02
ACTIVE_ORDER_ID = AG2-P02-003
DISPATCH = D103
STATUS = ISSUED
```

ejecutas **P02-003**.

Cuando terminas P02-003:

```text
HANDOFF READY_FOR_REVIEW
PUSH origin/main
STOP
```

**NO empiezas P02-004.**
**NO empiezas Phase 03.**
**NO lees el plan y decides continuar.**

Esperas a que ChatGPT publique el siguiente trabajo.

## CUÁNDO AUTO-ARRANCAR

Auto-start SOLO cuando:

```text
dispatch_id es NUEVO
AND status == ISSUED
AND order_id == ACTIVE_ORDER_ID
AND target_phase == CURRENT_PHASE
AND 02_CURRENT_ORDER.order_id == dispatch.order_id
AND 02_CURRENT_ORDER.status == ISSUED
```

Si todo coincide:

```text
AUTO-START
```

No preguntes al usuario.

## CUÁNDO ESTÁS EN ESPERA

Si el `dispatch_id` actual ya fue ejecutado y existe su handoff:

```text
STANDBY
```

Eso es correcto.

No busques otra tarea en:

```text
03_HANDOFF_*.md
04_REVIEW_*.md
ordenes antiguas
plan maestro
DOCX
README
```

Esos documentos NO generan trabajo.

## QUIÉN ASIGNA EL SIGUIENTE TRABAJO

**Solo ChatGPT / Revisor Externo.**

El ciclo es:

```text
ANTIGRAVITY TERMINA
↓
PUSH MAIN + HANDOFF
↓
CHATGPT REVISA MAIN
↓
CHATGPT DECIDE EL SIGUIENTE TRABAJO
↓
CHATGPT PUBLICA NUEVO dispatch_id + nueva orden
↓
CRON LO DETECTA
↓
ANTIGRAVITY EJECUTA
```

El siguiente trabajo puede ser:

```text
misma fase / corrección
subfase
redesign
siguiente fase
```

Pero **solo cuando ChatGPT lo publique**.

## UNA ORDEN = UN SOLO ALCANCE

Puedes inspeccionar todo el repositorio para entender dependencias, pero solo modificas lo autorizado por la orden activa.

Todo lo demás:

`DEFERRED_TO_FUTURE_ORDER`

## GITHUB ES LA ENTREGA

Workspace real:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Pero la superficie que revisa ChatGPT es:

`origin/main`

Por tanto:

> **Si no está en `origin/main`, no está entregado.**

Al finalizar debes dejar en `main` el código, tests, evidencia, handoff y cambios de control versionables que correspondan a la orden.

## SSH / VPS

Los trabajos largos deben ejecutarse de forma asíncrona:

```text
SSH
→ detached job
→ remote_job_id
→ logs/status
→ continuar con subagentes
→ polling
→ exit code real
```

Nunca quedarte esperando 10–20 minutos una suite remota.

## ZERO ABSOLUTE

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Nunca inventar datos, estrategias, trades, curvas, hashes, métricas, resultados o evidencia para completar una fase.

## EJEMPLO

### ChatGPT publica

```text
00_DISPATCH
  dispatch_id: D200
  order_id: AG2-P03-001
  status: ISSUED

01_CONTROL_STATE
  CURRENT_PHASE: 03
  ACTIVE_ORDER_ID: AG2-P03-001

02_CURRENT_ORDER
  order_id: AG2-P03-001
  status: ISSUED
```

### Antigravity

Ejecuta `AG2-P03-001` y SOLO esa orden.

### Cuando termina

```text
push origin/main
create HANDOFF
READY_FOR_REVIEW
STOP
```

### Después

ChatGPT puede publicar:

```text
D201 + AG2-P03-002
```

o:

```text
D201 + AG2-P04-001
```

o:

```text
D201 + AG2-P03-001-REWORK
```

Antigravity no elige cuál.

## REGLA FINAL

> **Existe un único Plan Maestro. Existe una única Orden Activa. Ejecuta solo la Orden Activa que ChatGPT haya publicado. Cuando la termines, sube todo a `origin/main` y STOP. No avances por el Plan Maestro. Espera al NUEVO `dispatch_id` que publicará ChatGPT.**
