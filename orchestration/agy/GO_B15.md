# GO_B15 — Higiene sostenible de agentes agy: `scripts/orq/` (vaciar MCP, lanzar, censo, matar, limpiar) + procedimiento

## Identidad
- ID: B15 · Ola: B · Rama/worktree: JOSFER78/agy-B15 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B15, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
Existe `scripts/orq/` con cinco herramientas que dejan la máquina SIN agentes cargados de más y lanzan agentes limpios, verificadas sobre procesos reales:
- `mcp_vacio.ps1`: deja `~/.gemini/config/mcp_config.json` y `~/.gemini/antigravity-ide/mcp_config.json` en `{"mcpServers": {}}` (backup fechado al lado si tenían algo); imprime cuántos servidores había en cada uno. Parámetro `-ConfigDir` (por defecto `~/.gemini`) para los tests.
- `agy_censo.ps1 [-Json]`: por cada `agy.exe`: pid, hora de arranque, worktree (leído de `workspaceDirs=` en el `~/.gemini/antigravity-cli/log/cli-<fecha>.log` cuya línea "Starting language server process with pid N" coincida), nº de descendientes y MB, y si tiene descendientes PROTEGIDOS.
- `agy_matar.ps1 -Pid N [-Forzar]`: mata el árbol pero NUNCA un proceso protegido, ni sus ancestros, ni sus descendientes. Protegido = línea de comandos que casa con `gobernanza_recursos|mine\.py|cola_mineria|sqcli|next build`. Sin `-Forzar` se niega si hay protegidos y lo dice.
- `agy_limpiar.ps1 -Conservar <rutas de worktree separadas por coma>`: mata los árboles de agy cuyo worktree NO está en la lista y los procesos MCP huérfanos (padre inexistente y comando con `.gemini|mcp|gbrain|tradingview|notebooklm|obsidian`); imprime censo antes y después.
- `agy_lanzar.sh <ID> "<título>" <fichero_spec>`: la receta verificada: `mcp_vacio` → worktree `--setup skip` → confianza sembrada en `~/.gemini/antigravity-cli/settings.json` (`trustedWorkspaces`) → `terminal create` con comando PURO `agy --model gemini-3.7-flash-high --dangerously-skip-permissions` → bucle hasta ver el banner `Antigravity CLI` en `terminal read` → `terminal wait --for tui-idle` → `task-create` + `worker-start --worktree --terminal` (los dos flags) → 45 s después mide descendientes y, si hay alguno que no sea shell (`powershell|cmd|bash|conhost`), mata el árbol y sale con rc=1 → registra una línea JSON en `orchestration/state/agentes.jsonl` (id, hora, pid, worktree, hijos, mb, task, dispatch).
Más `orchestration/OPERACION_AGENTES.md` (el ciclo completo en una página: lanzar → auditar → integrar → cerrar = `worker-release` + `terminal stop --worktree path:<ruta>` + `agy_matar` + censo a 0; límites ≤6-7 agentes, RAM <78 %, 2 pesados; qué hacer si el IDE de Antigravity reescribe los MCP) y tests reales.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/orq/ (nuevo) · tests/test_orq_agentes.py (nuevo) · orchestration/OPERACION_AGENTES.md (nuevo)
- orchestration/results/agy/B15.md (nuevo) · orchestration/agy/DONE_B15.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- Los scripts de trabajo del ORQ, que YA funcionan y hay que productizar sin cambiar lo que hacen, en `C:/Users/yo/AppData/Local/Temp/claude/C--Users-yo-orca-workspaces-ultrarentable-devilray/db25b38e-7288-468e-b16f-277628646ed9/scratchpad/`: `despachar_agy.sh` (receta de lanzamiento), `medir_agy.ps1` (medición de descendientes), `matar_agy.ps1` (matanza con protección; DEFECTO conocido: protege el proceso pero no a sus ancestros; el 2026-09-02 13:58 murió la campaña E2 de B03 al matar a su agente: corrígelo protegiendo la cadena completa hasta la raíz).
- `~/.gemini/antigravity-cli/log/cli-*.log` (mapa pid→worktree), `~/.gemini/config/mcp_config.json` y `~/.gemini/antigravity-ide/mcp_config.json` (hoy vacíos; backups `mcp_config.backup_ORQ_12srv_20260902.json` al lado).
- orchestration/state/current_phase.md §4 fila "Capacidad del PC" (D17) y CLAUDE.md (carga de la máquina).
- `orca terminal stop --help`, `orca orchestration worker-start --help` (los flags exactos; `terminal stop --worktree path:<ruta>` mata el árbol del terminal: es la primera vía de cierre).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío. Lee las ENTRADAS. Ejecuta `Get-Process agy` y pega la salida cruda (censo de partida).
2. `mcp_vacio.ps1`, `agy_censo.ps1`, `agy_matar.ps1`, `agy_limpiar.ps1` en PowerShell 5.1 (sin `&&`, sin `??`, sin `Get-Counter`; `-ErrorAction` explícito). Cada uno con cabecera de uso y salida legible.
3. `agy_lanzar.sh` en bash (Git Bash) a partir de `despachar_agy.sh`: mismos pasos y guardarraíles (codex PROHIBIDO, comando puro, confianza sembrada antes, banner antes de tui-idle, `--worktree` y `--terminal` juntos), más la medición posterior y el registro en `orchestration/state/agentes.jsonl`.
4. Tests REALES en `tests/test_orq_agentes.py`: (a) sintaxis de cada .ps1 (`powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw <f>))"` rc=0) y `bash -n` del .sh; (b) `agy_matar.ps1` sobre un árbol real que el test crea (`powershell -Command "Start-Process powershell -ArgumentList '-Command','Start-Sleep 120'"` anidado) con un nieto cuya línea de comandos contenga `mine.py` como texto (p. ej. `powershell -Command "Start-Sleep 120; # mine.py"`): el protegido y su padre sobreviven, el resto muere; limpieza final del árbol de prueba con `-Forzar`; (c) `mcp_vacio.ps1 -ConfigDir <tmp>` sobre copias; (d) `agy_censo.ps1 -Json` devuelve JSON válido (lista, puede estar vacía).
5. `orchestration/OPERACION_AGENTES.md` (1 página). Informe con salidas crudas; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_orq_agentes.py -q -p no:cacheprovider                       # esperado: >= 4 passed
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/agy_censo.ps1 -Json | "$PY" -c "import json,sys; d=json.load(sys.stdin); print(type(d).__name__, len(d))"   # esperado: list N
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/mcp_vacio.ps1 | tail -1     # esperado: linea con 'servidores' y 0 tras vaciar
bash -n scripts/orq/agy_lanzar.sh; echo "rc=$?"                                              # esperado: rc=0
grep -c "codex" scripts/orq/agy_lanzar.sh || true                                            # esperado: >= 1 (la prohibicion escrita)
ls scripts/orq/mcp_vacio.ps1 scripts/orq/agy_censo.ps1 scripts/orq/agy_matar.ps1 scripts/orq/agy_limpiar.ps1 scripts/orq/agy_lanzar.sh orchestration/OPERACION_AGENTES.md
git diff --name-only   # ⊆ TERRITORIO; esperado: vacio (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO. NO mates ningún proceso real que no hayas creado tú en el test (hay un build de SQX y otros agentes trabajando): `agy_matar.ps1`/`agy_limpiar.ps1` solo se prueban sobre el árbol de prueba del test.
- Sin dependencias fuera de la stdlib y de lo que ya hay en el sistema (PowerShell 5.1, Git Bash, orca CLI).

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · matar procesos ajenos · tocar `~/.gemini` fuera de `mcp_vacio.ps1` (y este solo con backup) · escribir fuera del TERRITORIO · mocks · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B15.md. 3. orchestration/agy/DONE_B15.md.
4. Cierre: orca orchestration send --type worker_done --subject "B15 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
