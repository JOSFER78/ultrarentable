# ANTIGRAVITY 2.0 — WATCHER READ FIRST / ORDEN DE EJECUCIÓN

## REGLA MÁS IMPORTANTE

**EL CRON NO DECIDE QUÉ TRABAJO HACER.**

El cron solo detecta si **CHATGPT / REVISOR EXTERNO** ha publicado un NUEVO `dispatch_id` ejecutable.

La cadena de autoridad es:

```text
CHATGPT REVISA origin/main
        ↓
CHATGPT DECIDE la siguiente acción
        ↓
CHATGPT publica NUEVO dispatch_id + order_id
        ↓
CRON detecta el NUEVO dispatch_id
        ↓
ANTIGRAVITY ejecuta EXACTAMENTE esa orden
        ↓
HANDOFF + PUSH origin/main
        ↓
STOP
        ↓
CHATGPT vuelve a revisar
```

## 1. LOS 3 ÚNICOS ARCHIVOS QUE DECIDEN SI HAY TRABAJO

En `origin/main` leer siempre, en este orden:

1. `.agents/informe&seguimiento/00_DISPATCH.md`
2. `.agents/informe&seguimiento/01_CONTROL_STATE.md`
3. `.agents/informe&seguimiento/02_CURRENT_ORDER.md`

Estos tres archivos forman un **handshake indivisible**.

### El resto NO es un trigger

Los siguientes archivos son SOLO información/histórico:

- `04_REVIEW_*.md`
- `03_HANDOFF_*.md`
- `ORDER_README_FOR_ANTIGRAVITY.md`
- `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md`
- `07_*`, `08_*`, `09_*`, `10_*`, `11_*` históricos
- DOCX

**Nunca iniciar una orden porque exista un REVIEW, HANDOFF, archivo histórico o cambio de plan.**

## 2. CONDICIONES EXACTAS DE AUTO-START

Auto-start SOLO si TODAS se cumplen:

```text
dispatch_id != last_processed_dispatch_id
status == ISSUED
order_id == ACTIVE_ORDER_ID
target_phase == CURRENT_PHASE
02_CURRENT_ORDER.order_id == dispatch.order_id
02_CURRENT_ORDER.status == ISSUED
no_other_dispatch_running == true
```

Entonces:

```text
AUTO-START AHORA
```

No pedir confirmación al usuario.

## 3. SI NO HAY NUEVO DISPATCH

Si:

```text
dispatch_id == last_processed_dispatch_id
```

y la orden ya tiene:

```text
03_HANDOFF_<same_order_id>.md
status = READY_FOR_REVIEW
```

entonces el resultado correcto es:

```text
STANDBY / STOP
```

**NO buscar otra orden en archivos históricos.**

**NO saltar de fase.**

**NO inventar una siguiente tarea.**

**NO ejecutar una orden antigua.**

Esperar a que el Revisor Externo publique un NUEVO `dispatch_id`.

## 4. CUANDO CHATGPT PUBLICA UNA NUEVA ORDEN

Puede ser cualquier transición adaptativa:

```text
01.0 → 01.1
01.1 → 01.REWORK.01
01.REWORK.01 → 01.REWORK.02
01.x → 02.0
02.0 → 02.REWORK.01
02.x → 03.0
```

Antigravity **NO interpreta el nombre** para decidir qué hacer.

Solo ejecuta el `order_id` que aparece simultáneamente en:

```text
00_DISPATCH.md
01_CONTROL_STATE.md
02_CURRENT_ORDER.md
```

## 5. UNA ORDEN = UNA ÚNICA UNIDAD DE TRABAJO

Una orden puede representar:

- una fase;
- una subfase;
- un rework;
- un redesign;
- una resolución de bloqueo.

Antigravity puede inspeccionar el repo completo, pero solo modifica lo autorizado por la orden.

Cualquier otro problema:

```text
DEFERRED_TO_FUTURE_ORDER
```

## 6. CUANDO ANTIGRAVITY TERMINA

La orden termina cuando:

```text
trabajo realizado
+ tests reales
+ evidencia real
+ commit
+ push origin/main
+ SHA remoto verificado
+ HANDOFF publicado
```

Entonces:

```text
STOP
```

Antigravity NO debe:

- crear la siguiente fase;
- crear otro dispatch;
- interpretar `READY_FOR_REVIEW` como aprobación;
- continuar arreglando el repo por iniciativa propia.

## 7. QUIÉN DECIDE EL SIGUIENTE PASO

**CHATGPT / REVISOR EXTERNO.**

Después de que Antigravity entregue:

```text
ChatGPT lee origin/main
→ revisa código/diff/tests/evidencia
→ decide:
   REWORK
   SUBPHASE
   REDESIGN
   BLOCK
   NEXT_PHASE
→ publica nueva orden + NUEVO dispatch_id
```

## 8. SSH / VPS

SSH es para ejecutar el trabajo real. No mantener al orquestador bloqueado durante 10–20 minutos esperando una suite.

Jobs largos:

```text
SSH
→ detached/async
→ remote_job_id
→ logs/status/exit code
→ seguir trabajando con subagentes
→ polling acotado
```

Timeout o ausencia de evidencia = `UNVERIFIED`, nunca `PASS`.

## 9. ZERO ABSOLUTE

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Nunca inventar una orden, una estrategia, un dataset, una métrica o un resultado para “hacer avanzar” el sistema.

## 10. EJEMPLO ACTUAL

Si GitHub dice:

```text
00_DISPATCH:
  dispatch_id = D100
  order_id = AG2-P02-002
  status = ISSUED

01_CONTROL_STATE:
  CURRENT_PHASE = 02
  ACTIVE_ORDER_ID = AG2-P02-002

02_CURRENT_ORDER:
  order_id = AG2-P02-002
  status = ISSUED
```

Antigravity ejecuta `AG2-P02-002`.

Si después existe:

```text
03_HANDOFF_AG2-P02-002.md
READY_FOR_REVIEW
```

y no existe un dispatch posterior:

```text
NO EXECUTAR NADA MÁS
STOP
```

Cuando ChatGPT publique:

```text
D101
AG2-P02-003
ISSUED
```

el siguiente cron debe arrancar `AG2-P02-003` automáticamente.

## REGLA FINAL

> **NO BUSQUES TRABAJO EN LOS ARCHIVOS. BUSCA SOLO UN NUEVO `dispatch_id` EJECUTABLE EN `00_DISPATCH.md` Y VALÍDALO CONTRA `01_CONTROL_STATE.md` + `02_CURRENT_ORDER.md`. Si no existe, estás en STOP. Si existe y el handshake coincide, AUTO-START.**
