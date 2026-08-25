# ULTRARENTABLE — CONTROL OPERATIVO ÚNICO

## MODELO DEFINITIVO

Este directorio es la torre de control de Antigravity 2.0.

### Solo existen dos cosas que importan para decidir qué hacer

**1. PLAN MAESTRO**

`.agents/informe&seguimiento/04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md`

Es el único roadmap del proyecto. Contiene todas las fases y objetivos.

**2. ORDEN ACTIVA**

La determina la combinación:

```text
00_DISPATCH.md
+
01_CONTROL_STATE.md
+
02_CURRENT_ORDER.md
```

No hay una cola automática de fases.

El Plan Maestro NO se recorre automáticamente.

## FLUJO DEFINITIVO

```text
CHATGPT REVISA origin/main
        ↓
DECIDE QUÉ TRABAJO SIGUE
        ↓
PUBLICA NUEVA ORDEN + NUEVO dispatch_id
        ↓
CRON (~3 min)
        ↓
DETECTA NUEVO dispatch
        ↓
ANTIGRAVITY + SUBAGENTES
        ↓
EJECUTA SOLO ESA ORDEN
        ↓
TESTS + EVIDENCIA
        ↓
COMMIT + PUSH origin/main
        ↓
HANDOFF READY_FOR_REVIEW
        ↓
STOP
        ↓
CHATGPT REVISA
        ↺
```

## QUÉ DEBE HACER ANTIGRAVITY

Cuando hay una orden `ISSUED` nueva:

1. Leer `00_DISPATCH.md`.
2. Leer `01_CONTROL_STATE.md`.
3. Leer `02_CURRENT_ORDER.md`.
4. Confirmar que los tres apuntan al mismo `order_id` y fase.
5. Lanzar los subagentes necesarios.
6. Ejecutar SOLO esa orden.
7. Trabajar sobre el proyecto real.
8. Ejecutar tests y obtener evidencia real.
9. Commit + push a `origin/main`.
10. Verificar SHA remoto.
11. Crear handoff.
12. STOP.

## CUÁNDO NO DEBE HACER NADA

Si la orden actual ya tiene:

```text
HANDOFF = READY_FOR_REVIEW
```

y no existe un `dispatch_id` posterior publicado por ChatGPT:

```text
STOP / STANDBY
```

Eso es correcto.

NO debe:

- avanzar a la siguiente fase por el Plan Maestro;
- interpretar `04_REVIEW_*.md` como trigger;
- ejecutar órdenes históricas;
- inventar una siguiente tarea;
- modificar otras fases;
- pedir al usuario que le diga qué hacer.

## QUIÉN DECIDE LA SIGUIENTE FASE

**ChatGPT / Revisor Externo.**

Después de revisar `origin/main`, puede ordenar:

```text
REWORK
SUBFASE
REDESIGN
BLOCK FIX
NEXT PHASE
```

Luego publica una nueva orden y un nuevo `dispatch_id`.

Antigravity la ejecuta automáticamente en el siguiente ciclo del cron.

## ARCHIVOS QUE NO SON TRIGGERS

Estos archivos sirven para información, historial o auditoría, pero NO generan trabajo:

```text
03_HANDOFF_*.md
04_REVIEW_*.md
04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md
ORDER_README_FOR_ANTIGRAVITY.md
WATCHER_READ_FIRST.md
órdenes históricas
DOCX
```

El único trigger es un **NUEVO `dispatch_id`** en `00_DISPATCH.md` que coincida con `01_CONTROL_STATE.md` y `02_CURRENT_ORDER.md`.

## ALCANCE

Una orden = una fase/subfase/unidad de trabajo.

Antigravity puede inspeccionar todo el repositorio para entender dependencias, pero solo puede modificar el alcance de la orden actual.

Fuera de alcance:

`DEFERRED_TO_FUTURE_ORDER`

## GITHUB

Workspace real:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Superficie oficial de revisión:

`origin/main`

> Lo que no está en `origin/main` no está entregado.

## SSH / VPS

Los procesos largos se ejecutan de forma asíncrona y no pueden bloquear el orquestador durante 10–20 minutos.

```text
SSH
→ detached/async
→ remote_job_id
→ logs/status/exit code
→ polling acotado
```

## ZERO ABSOLUTE

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Nunca fabricar datos, estrategias, trades, curvas, métricas, hashes, fills o resultados.

## VISION DEL PROYECTO

El Plan Maestro mantiene el objetivo completo de ULTRARENTABLE:

- laboratorio cuantitativo real y reproducible;
- Discovery Factory adaptativa;
- Genome + clustering + trial accounting;
- Research / reprogramming / learning;
- robustez y validación independiente;
- ULTRA global con objetivo de descubrimiento `+1000%` sin forzar resultados;
- FONDEO **solo futuros**;
- metaestrategias y portfolio;
- versionado y evidencia actual;
- operación 24/7.

Estas capacidades se implementan solo cuando la fase correspondiente sea publicada como orden activa por ChatGPT.

## REGLA FINAL

> **UN SOLO PLAN MAESTRO. UNA SOLA ORDEN ACTIVA. CHATGPT PUBLICA LA SIGUIENTE. ANTIGRAVITY EJECUTA SOLO ESA ORDEN CON SUBAGENTES, LA ENTREGA EN `origin/main` Y SE DETIENE. NO AVANZA POR SU CUENTA.**
