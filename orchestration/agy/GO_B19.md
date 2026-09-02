# GO_B19 — `scripts/orq/agy_lanzar.sh` v2: despacho que no falla, con tiempos medidos por fase

## Identidad
- ID: B19 · Ola: S (sistema) · Rama/worktree: JOSFER78/agy-B19 · Timebox: 30 min
- Variables ya puestas: AGY_AGENT=B19, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
`scripts/orq/agy_lanzar.sh <ID> "<título>" <spec>` (ya integrado por B15) queda endurecido con cuatro cambios medidos hoy por el ORQ: (1) si `orca worktree create` agota su timeout (60-90 s) pero el directorio aparece, NO aborta: espera a que exista `<worktree>/.git` (≤ 90 s, sondeo cada 2 s) y sigue; (2) tras `worker-start`, comprueba durante 60 s que el prompt se envió: si `orca orchestration worker-list --json` muestra ese `dispatchId` con `dispatchStatus: failed` o la pantalla (`terminal read`) sigue mostrando el texto del spec en el cuadro de entrada, hace `terminal stop --worktree path:<ruta>` y re-despacha UNA vez (nuevo terminal, misma tarea con `task-update --id <task> --status ready`); (3) durante los primeros 180 s vigila la pantalla cada 10 s y, si aparece `How's the CLI experience`, envía `0` + Enter; (4) registra en `orchestration/state/agentes.jsonl` una línea JSON con los tiempos por fase en segundos (`t_worktree`, `t_terminal`, `t_banner`, `t_idle`, `t_start`, `t_total`, `hijos`, `mb`, `reintento_prompt` true/false, `task`, `dispatch`, `terminal`) y sale con rc=0 solo si `t_total` ≤ 180 y `hijos_no_shell` = 0.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/orq/agy_lanzar.sh · tests/test_orq_agentes.py (añadir casos; no romper los 5 existentes)
- orchestration/OPERACION_AGENTES.md (sección "Lanzar": los 4 cambios y los tiempos esperados)
- orchestration/results/agy/B19.md (nuevo) · orchestration/agy/DONE_B19.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- scripts/orq/agy_lanzar.sh (tal cual) y el despachador de trabajo del ORQ, que YA tiene el cambio (1) aplicado y probado: `C:/Users/yo/AppData/Local/Temp/claude/C--Users-yo-orca-workspaces-ultrarentable-devilray/db25b38e-7288-468e-b16f-277628646ed9/scratchpad/despachar_agy.sh` (líneas 18-30) y `.../scratchpad/vigilar_encuesta.sh` (cambio 3) y `.../scratchpad/redespachar.sh` (re-despacho en worktree existente).
- Tiempos medidos hoy por el ORQ (referencia para OPERACION_AGENTES.md): CLI de Orca 0,7-0,9 s por llamada; despacho con worktree existente 17-75 s; timeout de `worktree create` 60-90 s con el worktree creado igual.
- `orca orchestration worker-list --json` (campos `dispatchId`, `dispatchStatus`, `workerState`, `terminalState`, `agentTerminalHandle`), `orca orchestration task-update --help`, `orca terminal read/send/stop --help`.

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee las ENTRADAS; `bash -n scripts/orq/agy_lanzar.sh`.
2. Implementa (1)-(4) en `agy_lanzar.sh` (bash de Git Bash; `date +%s` para los tiempos; JSON con `printf`, sin jq). El re-despacho (2) reutiliza la propia función de creación de terminal + banner + tui-idle + worker-start.
3. Tests reales en `tests/test_orq_agentes.py`: (a) `bash -n`; (b) la función de espera del worktree devuelve 0 cuando un directorio de prueba con `.git` aparece a los 4 s (créalo en segundo plano desde el test) y rc≠0 si no aparece en 6 s (usa una variable de entorno `AGY_LANZAR_MAX_ESPERA=6` para el test); (c) el registro JSON escrito en un fichero temporal es JSON válido con las claves listadas. No lances ningún agente real desde el test.
4. Actualiza OPERACION_AGENTES.md ("Lanzar": pasos, tiempos esperados por fase y qué hacer si `t_total` > 180 s). Informe; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
bash -n scripts/orq/agy_lanzar.sh; echo "rc=$?"                                                     # esperado: rc=0
"$PY" -m pytest tests/test_orq_agentes.py -q -p no:cacheprovider                                    # esperado: >= 8 passed
grep -c -E "How's the CLI experience|task-update|t_total|\.git" scripts/orq/agy_lanzar.sh || true  # esperado: >= 4
grep -c "t_total" orchestration/OPERACION_AGENTES.md                                                 # esperado: >= 1
git diff --name-only   # ⊆ TERRITORIO
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO. NO lances agentes ni toques terminales de Orca desde los tests: el ORQ prueba el lanzador real con un trabajo de humo después de integrar.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · lanzar agentes/terminales reales desde el test · escribir fuera del TERRITORIO · mocks de la CLI de Orca (los tests prueban funciones puras del script sobre ficheros reales) · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B19.md. 3. orchestration/agy/DONE_B19.md.
4. Cierre: orca orchestration send --type worker_done --subject "B19 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
