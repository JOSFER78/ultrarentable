# ULTRARENTABLE — CÓMO INTERPRETAR LAS ÓRDENES

## REGLA ABSOLUTA

Antigravity NO decide el trabajo siguiente.
Antigravity NO interpreta el plan maestro como una orden.
Antigravity NO ejecuta archivos históricos.
Antigravity NO salta de fase por iniciativa propia.

La única orden ejecutable es la combinación coherente de:

```text
00_DISPATCH.md
+
01_CONTROL_STATE.md
+
02_CURRENT_ORDER.md
```

Y los tres deben referirse al MISMO:

```text
order_id
phase
phase_status
status
```

## QUÉ SIGNIFICA CADA COSA

### 1. 00_DISPATCH.md
Es el disparador.

Un `dispatch_id` NUEVO significa una nueva instrucción emitida por el Revisor Externo.

Ejemplo:

```text
AG2-DISPATCH-...-P02-002
```

NO significa "fase 02 genérica".
Significa exactamente:

```text
ejecutar AG2-P02-002
```

### 2. 01_CONTROL_STATE.md
Es el estado vivo.

Debe confirmar:

```text
CURRENT_PHASE
PHASE_STATUS
ACTIVE_ORDER_ID
ACTIVE_DISPATCH_ID
```

### 3. 02_CURRENT_ORDER.md
Es la orden exacta que se ejecuta.

No se debe sustituir por un archivo histórico `08_*`, `09_*`, `10_*`, `11_*` etc.

## GENEALOGÍA DE ÓRDENES

Las órdenes forman una cadena de decisiones del Revisor Externo.

Ejemplo real de este proyecto:

```text
P01-005
   ↓ handoff
ChatGPT revisa
   ↓
REVIEW P01-005 = APPROVED_FOR_NEXT_PHASE
   ↓
P02-001
   ↓ handoff
ChatGPT revisa
   ↓
REVIEW P02-001 = REWORK
   ↓
P02-002
   ↓ handoff
STOP
   ↓
ChatGPT revisa ahora
```

Por tanto, P02-002 NO apareció de la nada.
Fue creado como consecuencia directa de la revisión de P02-001.

La regla es siempre:

```text
ORDER N
→ HANDOFF
→ CHATGPT REVIEW
→ DECISIÓN
→ ORDER N+1 / REWORK / SUBPHASE / REDESIGN
→ NUEVO DISPATCH_ID
→ AUTO-START
```

## CUÁNDO EMPEZAR

Empieza automáticamente SOLO si:

```text
dispatch_id = nuevo
status = ISSUED
target_phase = CURRENT_PHASE
ACTIVE_ORDER_ID = order_id
no hay otra orden ejecutándose
```

No hace falta que el usuario diga "empieza".

## CUÁNDO PARAR

PARA inmediatamente cuando:

```text
scope completo
+ tests/evidencia registrados
+ commit realizado
+ push origin/main
+ SHA remoto verificado
+ handoff READY_FOR_REVIEW
```

`READY_FOR_REVIEW` significa:

> LA ORDEN ACTUAL HA TERMINADO Y HA SIDO ENTREGADA.

No significa:

> empieza la siguiente fase.

## QUIÉN DECIDE LA SIGUIENTE ORDEN

Solo el Revisor Externo.

Puede ordenar cualquiera de estas transiciones:

```text
REWORK
01.REWORK.01
01.2
REDESIGN
BLOCKED FIX
NEXT_PHASE
SPLIT
MERGE
ABANDON
```

Por ejemplo:

```text
01.0 → 01.REWORK.01
01.REWORK.01 → 01.REWORK.02
01.REWORK.02 → 02.0
```

No existe obligación de pasar linealmente de 01 a 02.

## QUÉ HACER CON PROBLEMAS FUERA DE ALCANCE

```text
DESCUBRIR
→ DOCUMENTAR
→ CLASIFICAR
→ DEFERRED_TO_FUTURE_ORDER
→ NO MODIFICAR
```

Solo puede tocarse algo fuera de alcance si demuestra ser una dependencia directa que impide ejecutar la orden actual.

## PROYECTO Y GITHUB

Workspace real:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Superficie que revisa ChatGPT:

`origin/main`

Por tanto:

> Si no está en `origin/main`, no está entregado.

La entrega debe incluir todo lo versionable:

```text
código
+ tests
+ evidencia
+ handoff
+ control state
+ current order/dispatch cuando cambien
```

## SSH/VPS

Para procesos largos:

```text
ssh
→ lanzar async/detached
→ remote_job_id
→ continuar trabajo independiente
→ polling
→ exit code real
```

Nunca quedarse 10–20 minutos esperando una suite.

Un timeout o resultado incompleto es `UNVERIFIED`, nunca PASS.

## ZERO-SIMULATION / ZERO-FORCING

Siempre:

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

No fabricar resultados para satisfacer una orden.
No relajar tests para obtener verde.
No inventar datos.
No inventar hashes.
No inventar evidencia.

## ESTADO REAL ACTUAL

La orden actualmente activa es la que indique `01_CONTROL_STATE.md` + `00_DISPATCH.md` + `02_CURRENT_ORDER.md` en `origin/main`.

Nunca usar este README como trigger.
Este README explica cómo leer el sistema; no autoriza ninguna ejecución.
