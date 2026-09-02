# GO_B18 — Instantánea de la BD canónica del VPS en el PC (solo lectura en el VPS) para que el localhost enseñe los datos reales

## Identidad
- ID: B18 · Ola: B · Rama/worktree: JOSFER78/agy-B18 · Timebox: 30 min
- Variables ya puestas: AGY_AGENT=B18, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- VPS: `ssh oracle-vps` funciona sin contraseña. En el VPS SOLO LECTURA de la BD: `sqlite3 ... ".backup"` a `/tmp` (copia consistente), `sha256sum`, `scp` y borrado de ESE fichero temporal de `/tmp`. PROHIBIDO tocar `~/.local/state/ultrarentable/ultrarentable.sqlite3` del VPS, sus servicios o cualquier otro fichero.

## OBJETIVO (una frase verificable)
En el PC, `~/.local/state/ultrarentable/ultrarentable.sqlite3` (hoy 532.480 bytes: 0 estrategias, 0 backtests, 0 trials) queda sustituida por una copia consistente y verificada por SHA-256 de la BD canónica del VPS (`/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3`, ~65,8 MB, 38.456 trials según `/api/v1/discovery/status` del VPS), con la BD local anterior aparcada en `cuarentena/bd_local_pc_<fecha>/` (copia + `MANIFEST.sha256` + `MOTIVO.md`, nunca `rm`), la API local reiniciada (`scripts/orq/web_local.ps1 -Parar` y `-Arrancar`, puertos 8100/3100) y `http://127.0.0.1:8100/api/v1/discovery/status` devolviendo `total_trials_in_db` > 0 y `/api/v1/candidates?limit=3&include_rejected=true` con filas reales.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- `C:/Users/yo/.local/state/ultrarentable/ultrarentable.sqlite3` (sustitución, con la anterior en cuarentena) y ficheros `-wal`/`-shm` asociados si existen (se aparcan igual)
- cuarentena/bd_local_pc_<YYYYMMDD>/ (nuevo)
- orchestration/site/ (PIDs y logs de web_local.ps1)
- orchestration/results/agy/B18.md (nuevo) · orchestration/agy/DONE_B18.md (nuevo)
- En el VPS: solo `/tmp/ultrarentable_snapshot_<fecha>.sqlite3` (crear, copiar, borrar).

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- services/api/app/config.py líneas 30-40 (`STATE_DB_PATH`: prioridad variable de entorno > `~/.local/state/ultrarentable/ultrarentable.sqlite3`).
- orchestration/OPERACION_WEB_LOCAL.md y scripts/orq/web_local.ps1 (`-Estado`, `-Parar`, `-Arrancar`; el terminal de Orca "web-local 3100/8100" del ORQ tiene la instancia arrancada: la paras y la vuelves a arrancar tú desde tu worktree con `-Arrancar`, que también reconstruye la web).
- `ssh oracle-vps 'ls -la ~/.local/state/ultrarentable/; sqlite3 ~/.local/state/ultrarentable/ultrarentable.sqlite3 "pragma journal_mode; select count(*) from campaign_trials; select count(*) from strategies; select count(*) from backtests;"'` (pega la salida cruda: son las cifras que tienes que reproducir en el PC).
- CLAUDE.md §"BD canónica" y orchestration/OPERACION_VPS.md (carga del VPS: `.backup` con `nice -n 19 ionice -c 3`).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee las ENTRADAS y ejecuta la lectura ssh de arriba.
2. En el VPS: `nice -n 19 ionice -c 3 sqlite3 ~/.local/state/ultrarentable/ultrarentable.sqlite3 ".backup /tmp/ultrarentable_snapshot_<fecha>.sqlite3"`; `sha256sum /tmp/ultrarentable_snapshot_<fecha>.sqlite3`; `sqlite3 /tmp/... "pragma integrity_check; select count(*) from campaign_trials;"`. Pega todo.
3. `scp oracle-vps:/tmp/ultrarentable_snapshot_<fecha>.sqlite3 <tu worktree>/orchestration/site/` (fuera del índice de git: orchestration/site/ está ignorado para logs; comprueba con `git status` que NO aparece; si aparece, muévelo a `cuarentena/bd_local_pc_<fecha>/snapshot_vps.sqlite3` y no lo añadas). `sha256sum` en el PC = el del VPS. Borra el temporal del VPS (`rm /tmp/ultrarentable_snapshot_<fecha>.sqlite3` — única excepción autorizada a "nunca rm", porque es una copia temporal en /tmp del VPS).
4. `scripts/orq/web_local.ps1 -Parar` (pega `-Estado` con todo caído). Aparca la BD local: `mkdir cuarentena/bd_local_pc_<fecha>`, copia allí `ultrarentable.sqlite3` (+ `-wal`/`-shm` si existen), `sha256sum` a `MANIFEST.sha256`, `MOTIVO.md` (BD del PC vacía sustituida por instantánea del VPS de <fecha> con SHA <hash>). Sustituye: copia la instantánea a `C:/Users/yo/.local/state/ultrarentable/ultrarentable.sqlite3` (los `-wal`/`-shm` antiguos se aparcan, no se dejan).
5. `scripts/orq/web_local.ps1 -Arrancar` (PESADO por el `npm run build`, ~2 min, ADMITIDO por el ORQ para esta tarea; usa prioridad baja) y `-Estado`; `curl -s http://127.0.0.1:8100/api/v1/discovery/status`, `curl -s "http://127.0.0.1:8100/api/v1/candidates?limit=3&include_rejected=true" | head -c 600` y `curl -s http://127.0.0.1:8100/api/v2/strategy-lab/overview | head -c 600`: pégalos. `total_trials_in_db` debe coincidir con el `count(*)` de `campaign_trials` del VPS. Deja la instancia ARRANCADA (a diferencia de B16): Emilio la está mirando.
6. Informe con todas las salidas crudas y la tabla VPS vs PC (trials, strategies, backtests, tamaño, SHA); DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
ls -la "C:/Users/yo/.local/state/ultrarentable/ultrarentable.sqlite3" | awk '{print $5}'                    # esperado: > 50000000
"$PY" -c "import sqlite3;c=sqlite3.connect(r'C:/Users/yo/.local/state/ultrarentable/ultrarentable.sqlite3');print(c.execute('pragma integrity_check').fetchone()[0], c.execute('select count(*) from campaign_trials').fetchone()[0])"   # esperado: ok N (N = el del VPS)
ls cuarentena/bd_local_pc_*/MANIFEST.sha256 cuarentena/bd_local_pc_*/MOTIVO.md && sha256sum -c cuarentena/bd_local_pc_*/MANIFEST.sha256   # OK
curl -s http://127.0.0.1:8100/api/v1/discovery/status | grep -o '"total_trials_in_db":[0-9]*'             # esperado: el mismo N
curl -s "http://127.0.0.1:8100/api/v1/candidates?limit=3&include_rejected=true" | head -c 120               # esperado: empieza por [{ (filas reales)
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:3100/estrategias                                   # esperado: 200
git status --porcelain | grep -v -E "^\?\? (cuarentena/bd_local_pc_|orchestration/(results/agy/B18|agy/DONE_B18))" | wc -l   # esperado: 0 (nada más tocado ni ningún .sqlite3 en el índice)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? `sqlite3 .backup` en el VPS (I/O, con nice/ionice) y `npm run build` en el PC (admitido).
- La BD del VPS NO se modifica, ni se para ningún servicio allí. Si `ssh` o `scp` fallan: informe FALLA con el error crudo; no inventes cifras.
- La instantánea NO se versiona en git (ningún `.sqlite3` en `git add`; el arnés bloquea datos).
- Regla #26: no aplica (no se toca el motor).

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm (salvo el temporal `/tmp/...snapshot...` del VPS) · parar/arrancar/instalar nada en el VPS · escribir en la BD del VPS · añadir `.sqlite3` a git · escribir fuera del TERRITORIO · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B18.md. 3. orchestration/agy/DONE_B18.md.
4. Cierre: orca orchestration send --type worker_done --subject "B18 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
