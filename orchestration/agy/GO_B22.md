# GO_B22 — `scripts/orq/agy_vigilar.sh`: vigilante único (encuesta, prompt atascado, workers retenidos, hijos MCP) + `PLANTILLA_SPEC.txt` v2

## Identidad
- ID: B22 · Ola: S (sistema) · Rama/worktree: JOSFER78/agy-B22 · Timebox: 30 min
- Variables ya puestas: AGY_AGENT=B22, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
(A) `scripts/orq/agy_vigilar.sh [--intervalo 45] [--una-vez]` recorre cada ciclo los terminales con `agentIdentity: antigravity` de `orca terminal list --json` y (1) si la pantalla muestra `How's the CLI experience`, envía `0` + Enter; (2) si un dispatch de `worker-list` está `dispatchStatus: dispatched` y su pantalla lleva > 120 s mostrando el texto `[CONTRATO]` del spec dentro del cuadro de entrada (prompt sin enviar), lo anota como `PROMPT_ATASCADO <handle>` (no lo arregla: el ORQ decide); (3) cada 10 ciclos ejecuta `scripts/orq/agy_censo.ps1 -Json` y anota los agentes con hijos no-shell > 0 (`MCP_CARGADO <pid>`) y los procesos MCP huérfanos; (4) todo va a `orchestration/state/vigilante.log` con hora, y `--una-vez` hace un ciclo y sale (para tests y para el ORQ). (B) `orchestration/agy/PLANTILLA_SPEC.txt`: el contrato inline que se inyecta a cada agente (parte de la plantilla real usada hoy por el ORQ, que se te da como ENTRADA), con dos reglas nuevas en el `[CONTRATO]`: "VEREDICTO POR COMANDO: PASA solo si cada comando de ACEPTACIÓN da lo esperado; un 0, un fallo o un error de log NO se explican, se pegan" y "si tu tarea corre algo pesado (campaña, build), lo lanzas DESACOPLADO (`Start-Process`) y guardas el PID en un fichero del TERRITORIO"; y `__ID__` como único marcador a sustituir.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/orq/agy_vigilar.sh (nuevo) · orchestration/agy/PLANTILLA_SPEC.txt (nuevo) · orchestration/state/vigilante.log (nuevo; solo el de la prueba `--una-vez`)
- tests/test_orq_agentes.py (añadir casos; no romper los existentes) · orchestration/OPERACION_AGENTES.md (sección "Vigilar")
- orchestration/results/agy/B22.md (nuevo) · orchestration/agy/DONE_B22.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- El vigilante de trabajo del ORQ (funciona; productízalo): `C:/Users/yo/AppData/Local/Temp/claude/C--Users-yo-orca-workspaces-ultrarentable-devilray/db25b38e-7288-468e-b16f-277628646ed9/scratchpad/vigilar_encuesta.sh`, y la plantilla real: `.../scratchpad/spec_template.txt` (cópiala tal cual y añade las dos reglas; no quites ninguna).
- scripts/orq/agy_censo.ps1 (B15) y orchestration/OPERACION_AGENTES.md.
- Hechos medidos hoy: la encuesta bloqueó a B14 y a B06 en mitad de la tarea; el prompt de B12 se quedó en el cuadro de entrada 15 min con `dispatchStatus: failed`; los MCP se cargan si `~/.gemini/config/mcp_config.json` o `~/.gemini/antigravity-ide/mcp_config.json` vuelven a tener servidores.
- `orca terminal list/read/send --help`, `orca orchestration worker-list --json`.

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee las ENTRADAS.
2. `agy_vigilar.sh` (Git Bash; node solo para parsear JSON como hace el ORQ, o `"$PY"`); `--una-vez` obligatorio para el test.
3. Tests reales: (a) `bash -n`; (b) `agy_vigilar.sh --una-vez` con la CLI real termina con rc=0 y escribe al menos una línea con hora en `vigilante.log` (no envía nada si no hay encuesta en pantalla); (c) la función de detección de encuesta/prompt atascado sobre dos capturas de pantalla REALES guardadas por ti con `orca terminal read` (una normal, una con `[CONTRATO]` visible) devuelve lo esperado; (d) `PLANTILLA_SPEC.txt` contiene `__ID__`, `VEREDICTO POR COMANDO` y `Start-Process` y no contiene ningún otro `__MARCADOR__`.
4. OPERACION_AGENTES.md: "Vigilar" (cómo dejarlo corriendo: terminal de Orca `web-local`-style o `nohup`). Informe; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
bash -n scripts/orq/agy_vigilar.sh; echo "rc=$?"                                                     # esperado: rc=0
bash scripts/orq/agy_vigilar.sh --una-vez; echo "rc=$?"; tail -2 orchestration/state/vigilante.log    # esperado: rc=0 y una línea con hora
"$PY" -m pytest tests/test_orq_agentes.py -q -p no:cacheprovider                                    # esperado: >= 8 passed
grep -c -E "VEREDICTO POR COMANDO|Start-Process|__ID__" orchestration/agy/PLANTILLA_SPEC.txt         # esperado: >= 3
grep -o -E "__[A-Z_]+__" orchestration/agy/PLANTILLA_SPEC.txt | sort -u                              # esperado: solo __ID__
git diff --name-only   # ⊆ TERRITORIO
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO. El vigilante NUNCA mata ni reenvía prompts: solo contesta la encuesta y anota.
- No toques los terminales de otros agentes salvo para contestar la encuesta.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · matar procesos · `terminal stop` · escribir fuera del TERRITORIO · mocks (capturas reales guardadas) · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B22.md. 3. orchestration/agy/DONE_B22.md.
4. Cierre: orca orchestration send --type worker_done --subject "B22 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
