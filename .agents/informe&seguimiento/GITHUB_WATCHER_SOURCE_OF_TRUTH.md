# GITHUB WATCHER — SOURCE OF TRUTH ABSOLUTE

## REGLA CRÍTICA

El cron NO vigila la carpeta local, ni Obsidian, ni el workspace VPS como fuente de órdenes.

La fuente única para decidir si existe trabajo nuevo es:

**GitHub repository: `JOSFER78/ultrarentable`**
**Branch: `main`**
**Path: `.agents/informe&seguimiento/00_DISPATCH.md`**

El workspace VPS:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

es únicamente la superficie donde Antigravity ejecuta una orden DESPUÉS de haberla detectado en GitHub.

## ORDEN DE LECTURA CADA 3 MINUTOS

1. Ejecutar `git fetch origin main`.
2. Leer SIEMPRE la versión remota:

```bash
git show origin/main:.agents/informe&seguimiento/00_DISPATCH.md
```

3. Extraer el `dispatch_id` real de `origin/main`.
4. Compararlo con el `last_processed_dispatch_id` persistido por el watcher.
5. Si es diferente, leer también desde `origin/main`:

```bash
git show origin/main:.agents/informe&seguimiento/01_CONTROL_STATE.md
git show origin/main:.agents/informe&seguimiento/02_CURRENT_ORDER.md
```

Nunca usar una copia local de estos archivos para decidir si existe un nuevo trabajo.

## ESTADO DEL WATCHER

`last_processed_dispatch_id` NO significa "último dispatch visto en GitHub".

Sólo puede actualizarse a un nuevo ID DESPUÉS de que Antigravity haya iniciado realmente la orden y exista prueba durable de inicio.

Por tanto:

```text
GitHub dispatch nuevo
        ↓
DETECTADO
        ↓
VALIDADO
        ↓
AUTO-START REAL
        ↓
PROOF-OF-START
        ↓
actualizar last_processed_dispatch_id
```

Nunca:

```text
leer dispatch
↓
marcar procesado
↓
no ejecutar
```

## EJEMPLO ACTUAL

GitHub `origin/main` contiene:

```yaml
dispatch_id: AG2-DISPATCH-20260825-1815-P02-003
order_id: AG2-P02-003
status: ISSUED
target_phase: 02
```

Por tanto ese es el despacho que el watcher debe detectar si el último realmente ejecutado es `AG2-DISPATCH-20260825-1730-P02-002`.

Debe arrancar:

`AG2-P02-003`

No debe esperar otra cosa.

## SI EL WATCHER DICE "NO NEW DISPATCH"

Antes de informar `NO NEW DISPATCH`, debe registrar internamente:

```text
REMOTE_DISPATCH_ID=<valor leído con git show origin/main:...>
LAST_PROCESSED_DISPATCH_ID=<valor persistido>
REMOTE_COMMIT_SHA=<origin/main SHA>
```

Y demostrar:

```text
REMOTE_DISPATCH_ID == LAST_PROCESSED_DISPATCH_ID
```

Si no son iguales, **NO puede informar standby**.

## REGLA FINAL

> **GitHub `JOSFER78/ultrarentable` → `main` → `.agents/informe&seguimiento/00_DISPATCH.md` es la única fuente de verdad para detectar NUEVO TRABAJO. El VPS/local sólo ejecuta.**
