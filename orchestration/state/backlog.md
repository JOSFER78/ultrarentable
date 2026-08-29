# BACKLOG — Cola de tareas del ejecutor (el Orquestador promueve a current_phase.md una a una)

> Orden de ejecución. Una tarea a la vez. Nada aquí toca el motor SQX ni requiere ventana de parada (eso es la Fase 1, bloqueada hasta visto bueno del usuario).

## T1 — Web: DATABANK de extracción configurable (código, sin tocar motor)
- `services/api/app/api/strategy_lab_router.py` tiene DATABANK hardcodeado ("Results") y el semillero real es "Last generation" (con espacio).
- Tarea: hacer el databank parametrizable (query param + default configurable por env `SQX_EXTRACT_DATABANK`), usar el selector que la UI ya tiene (SQXToolsPanel), y verificar REAL: extraer de "Last generation" debe devolver ≥90 estrategias reales (hoy ~96-99). Cero mocks; error honesto si el motor no responde.
- Criterio: `curl POST /api/v2/strategy-lab/extract/Ultra_Matrix?databank=Last%20generation` → found ≥90; la UI permite elegir el banco y muestra el resultado.

## T2 — Parche C4 del gatillo (nuestro script, sin tocar motor)
- `improve_cycle.sh` cuenta el banco equivocado (LastGeneration=0 eterno) vía `count name=` que además falla con espacios (H9/H10).
- Tarea: parchear para parsear counts desde `-databank action=list` (soporta el legacy con espacio), semillero = "Last generation" + LastGeneration; añadir crontab `*/15 * * * *` para el usuario ubuntu; probar el script en modo lectura (sin disparar el ciclo real) y dejar la prueba en el log.
- Criterio: `bash -n` OK; una ejecución manual registra en el log el count real (>0) y decide correctamente ("espero" si < umbral o no corresponde); crontab -l contiene la línea.

## T3 — Huecos de datos M1 (informe + preparación, SIN descargar aún)
- 13 celdas activo×TF sin datos: M1 en 7 futuros CME y 6 forex (informe 06_ACTIVOS.md).
- Tarea: investigar las vías reales de descarga que SQX ya tiene configuradas (datasources del motor, SOLO lectura de su API/docs locales) y preparar el procedimiento exacto de descarga M1 para cada activo (comandos/lista), con coste si lo hubiera. NO ejecutar descargas (tocan datos del motor — decisión aparte).
- Criterio: documento `estrategias_um/docs/DATOS_M1_PLAN.md` con: activo | fuente disponible | procedimiento | coste | riesgo.

## T4 — Modo 24/7 del backend (systemd)
- El backend arranca en modo dev con ULTRARENTABLE_AUTONOMOUS_RUNTIME=false (log de arranque).
- Tarea: crear unit systemd `ultrarentable-api.service` (WorkingDirectory repo, ExecStart .venv uvicorn :8000, Restart=always, User=ubuntu), con el modo autónomo que corresponda tras revisar qué activa esa variable en el código; NO activar flota de workers aún si su activación ejecuta trading real — documentar qué haría y pedir decisión si hay duda (needs_user_input).
- Criterio: unit instalado, `systemctl enable` hecho, arranque verificado y `/estrategias` respondiendo 200 vía el servicio; documento de qué cambia con AUTONOMOUS_RUNTIME=true.

## BLOQUEADA — Fase 1 ventana de parada (motor)
- Requiere visto bueno EXPLÍCITO del usuario para `stop → copy 'Last generation'→ToImprove → export CSV → start`.
- Riesgo si se retrasa: el semillero (~96-99 crudas) vive SOLO en RAM del motor; un reinicio del servicio lo pierde. Recordárselo al usuario en cada checkpoint.

## T5 — Verificación post-reorganización (imports/paths rotos por los movimientos)
- La reorganización movió ficheros Python (canonical_strategy.py → services/strategy_core/, version_control_manager.py → scripts/herramientas/, tests → tests/phase_phase/, sqlite → data/db/). Los módulos que los importaban pueden estar rotos.
- Tarea: buscar todos los imports/rutas que referencien las rutas ANTIGUAS (grep 'canonical_strategy', 'version_control_manager', 'database.sqlite', 'learning_store' en todo el repo sin node_modules/.venv), arreglar las referencias rotas, y correr los tests que existen (pytest tests/) con salida real.
- Criterio: 0 referencias a rutas antiguas rotas; pytest corre y reporta su resultado real (pasa o falla — lo que sea, en el log).
