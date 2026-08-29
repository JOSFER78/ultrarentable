# Fase 1 — REPITE (backlog T1): Web — DATABANK de extracción configurable (código, SIN tocar el motor)

> ⚠️ RECUERDOS OBLIGATORIOS: **CERO SIMULACIONES** (todo real; si el motor no responde, error honesto — no mock) · **SUBAGENTES SIEMPRE** (reparte entre tus agentes) · **NO TE CUELGUES** (timeouts ≤60s, ejecuta y avanza) · **NUNCA `rm`** · **NUNCA git commit/push**.

> 🚫 **REITERADO TRAS INTENTO FALLIDO (review `reviews/fase_01_review.md`):**
> 1. **Ejecuta SOLO esta fase (T1, web/código).** La copia de databanks (`Last generation → ToImprove`) y CUALQUIER otra fase del plan_maestro están **BLOQUEADAS** hasta visto bueno explícito del usuario. El intento anterior ejecutó la fase bloqueada y falló.
> 2. **API correcta de SQX headless:** la invocación HTTP es `http://localhost:5050/call?cmd=<comando URL-encodeado>` (solo espacios → `%20`). El intento anterior usó un endpoint inexistente y obtuvo errores espantosos ("Falta el parámetro 'action'"). Verificado por el auditor a las 18:29:53 UTC que esta forma SÍ responde. Si un comando HTTP falla, depura la FORMA de invocación antes de concluir nada del motor.
> 3. En esta fase el motor se toca **SOLO en lectura** (`-databank action=list` y extracción vía API :8000). Prohibido parar/reiniciar proyectos, copiar bancos o escribir en ellos.

## Objetivo
Eliminar el hardcode `"Results"` del DATABANK en `services/api/app/api/strategy_lab_router.py` y hacerlo parametrizable (query param + default vía env `SQX_EXTRACT_DATABANK`), usando el selector que la UI ya tiene (SQXToolsPanel). Verificación REAL: extraer desde `"Last generation"` (con espacio) debe devolver ≥90 estrategias reales.

## Contexto necesario
- Fuente de la tarea: `orchestration/state/backlog.md` § T1 (aprobada en `reviews/fase_00_review.md`).
- El semillero real del motor SQX se llama **`Last generation`** (con espacio, banco legacy, 97 registros verificados por el auditor); `Results` está vacío — por eso el extract actual devuelve 0.
- Motor SQX headless en `http://localhost:5050` — modo SOLO LECTURA: prohibido parar/reiniciar/iniciar proyectos o escribir en bancos. Solo `-databank action=list` (vía `/call?cmd=`) y la extracción.
- El backend FastAPI corre en `:8000` (arranque dev). NO cambies su modo de ejecución ni variables globales.

## Subagentes sugeridos
- Subagente 1 (backend): modificar `strategy_lab_router.py` — aceptar `databank` como query param (URL-encoded, soporta espacios), default desde `os.environ.get("SQX_EXTRACT_DATABANK", "Last generation")`; error 503 honesto con el motivo real si la API del motor falla o el banco no existe.
- Subagente 2 (frontend): conectar el selector existente de `SQXToolsPanel` al nuevo parámetro y mostrar el resultado real (found/N).
- Subagente 3 (verificación REAL): `curl -s -X POST 'http://localhost:8000/api/v2/strategy-lab/extract/Ultra_Matrix?databank=Last%20generation'` → debe reportar found ≥90; probar también `databank=Results` (debe devolver found 0 o error honesto, nunca inventar). Dejar salidas crudas en el log.

## Criterio de éxito (verificable, no subjetivo)
- [ ] `grep -n "Results" services/api/app/api/strategy_lab_router.py` ya no contiene el hardcode como default.
- [ ] `curl` real contra el endpoint con `databank=Last%20generation` devuelve found ≥90 (número crudo pegado en el log, con timestamp).
- [ ] La UI permite elegir el banco y muestra el resultado real (captura/extracto de evidencia en el log).
- [ ] Cero mocks: si el motor no responde, el log contiene el ERROR real y el criterio se marca fallido — no se fabrica nada.
- [ ] `git status` muestra solo los archivos modificados de esta fase (router, panel, tests si aplica). Nada de commit.

## Qué reportar al terminar
- En `orchestration/results/fase_01.log`: acciones por subagente, diffs de los archivos modificados, salidas EXACTAS de los curls (JSON crudo), y cualquier decisión no explícita que hayas tomado.
- Recuerda en el informe: el semillero (97 estrategias crudas, verificado) vive SOLO en RAM del motor — pendiente el visto bueno del usuario para la ventana de parada (Fase 1 del plan maestro).
- Actualiza `orchestration/state/status.json` → `status: "done"`, `last_updated`. NO toques phase_number ni el backlog.
