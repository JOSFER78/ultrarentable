# GO_B12 — W7 vigía V0: unit systemd read-only e informe diario, preparados en seco (la instalación la hace el ORQ por ssh)

## Identidad
- ID: B12 · Ola: B · Rama/worktree: JOSFER78/agy-B12 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B12, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- VPS: `ssh oracle-vps` funciona. SOLO LECTURA allí (`ls`, `cat`, `systemctl status`, `df`, `free`): PROHIBIDO instalar, copiar, parar o arrancar nada en el VPS; eso lo hace el orquestador cuando Emilio autorice la limpieza (issue #22 punto 1).

## OBJETIVO (una frase verificable)
Existen en el repo `services/vigia/` (`vigia_v0.py`: script de SOLO LECTURA que cada ejecución escribe un informe JSON+MD en `orchestration/results/vigia/<fecha>.{json,md}` con: estado de la API :8000, servicios systemd relevantes, carga/RAM/swap, `memory.events` del discovery si existe, últimos trades/exámenes de la BD canónica si hay, y `NO DATA` donde no; nunca envía órdenes ni toca BD), `deploy/vigia/ultrarentable-vigia.service` + `.timer` (systemd, diario, `ProtectSystem=strict`, `ReadOnlyPaths`, usuario sin sudo, sin capacidad de red saliente salvo localhost), `deploy/vigia/INSTALAR.md` (los comandos exactos que ejecutará el ORQ) y `tests/test_vigia_v0.py` (el informe se genera en el PC con `NO DATA` donde no hay VPS; JSON válido; sin campos inventados).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/vigia/ (nuevo) · deploy/vigia/ (nuevo) · tests/test_vigia_v0.py (nuevo)
- orchestration/results/vigia/ (nuevo; solo el informe de prueba generado en el PC)
- orchestration/results/agy/B12.md (nuevo) · orchestration/agy/DONE_B12.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/HERMES_VPS_VIGIA.md (diseño V0/V1/V2; V0 = solo lectura, permanente mientras Topstep/TradeDay estén en juego: current_phase.md §5 del ciclo 1).
- orchestration/OPERACION_VPS.md (servicios, cron `improve_cycle.sh`, sección A de limpieza) y VENTANA_EMILIO.md §1.
- services/api/app/config.py (`STATE_DB_PATH`, puerto de la API) y services/ops/gobernanza_recursos.py (cómo lee recursos; en Linux `/proc`).
- `ssh oracle-vps 'systemctl list-units --type=service | grep -i ultrarentable; cat /sys/fs/cgroup/system.slice/ultrarentable-discovery.service/memory.events 2>/dev/null; free -h; uptime'` (solo lectura; pega la salida cruda).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee el diseño y la operación del VPS; ejecuta la lectura ssh de ENTRADAS y pégala.
2. `services/vigia/vigia_v0.py`: funciones puras por fuente (api, systemd, recursos, discovery, bd), cada una devuelve dict con `NO DATA` + motivo si no puede leer; `main()` escribe `orchestration/results/vigia/<YYYY-MM-DD>.json` y `.md`; flag `--dry-run` (no escribe) y `--out-dir`. Sin `requests` a internet; solo localhost y ficheros.
3. `deploy/vigia/ultrarentable-vigia.service` (Type=oneshot, User=ubuntu o dedicado, `ProtectSystem=strict`, `ProtectHome=read-only`, `ReadWritePaths=` solo la carpeta de informes, `NoNewPrivileges=yes`, `Nice=19`, `CPUQuota=10%`), `.timer` diario 06:30 UTC, `INSTALAR.md` con los comandos exactos (copiar, `systemctl daemon-reload`, `enable --now`, verificación) para que el ORQ los ejecute tal cual.
4. `tests/test_vigia_v0.py`: ejecutar `main(out_dir=tmp_path, dry_run=False)` en el PC ⇒ JSON válido con todas las claves, las fuentes no disponibles marcadas `NO DATA` con motivo (no 0, no None mudo), MD con la misma información; test de que el módulo no importa nada que envíe órdenes (grep AST: sin `pickmytrade`, `tradovate`, `bingx` ni `requests.post`).
5. Genera un informe real en el PC (`orchestration/results/vigia/`) y pégalo en tu informe. DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_vigia_v0.py -q -p no:cacheprovider                       # esperado: >= 3 passed
"$PY" -m services.vigia.vigia_v0 --dry-run; echo "rc=$?"                              # esperado: imprime el informe con NO DATA donde toca, rc=0, no escribe
ls orchestration/results/vigia/*.json | head -1                                       # existe (el de prueba)
grep -cE "ProtectSystem=strict|NoNewPrivileges=yes|OnCalendar" deploy/vigia/ultrarentable-vigia.service deploy/vigia/ultrarentable-vigia.timer | tail -1
grep -cE "pickmytrade|tradovate|bingx|requests\.post" services/vigia/vigia_v0.py || true   # esperado: 0 (rc-libre)
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO.
- V0 es SOLO LECTURA por regla de las prop firms (Topstep/TradeDay prohíben operar desde VPS): ni un `send` de órdenes, ni escritura en la BD canónica.
- Nada se instala en el VPS en esta tarea.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir/instalar/parar/arrancar nada en el VPS · escribir en la BD · enviar órdenes · datos inventados · escribir fuera del TERRITORIO · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B12.md. 3. orchestration/agy/DONE_B12.md.
4. Cierre: orca orchestration send --type worker_done --subject "B12 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json

## CORRECCION_1 (ORQ, 2026-09-02 14:05) — continuación: el agente anterior murió a las 13:30 sin informe ni DONE

Hechos (verificados por el ORQ): en este worktree ya existen `services/vigia/`, `deploy/vigia/`, `tests/test_vigia_v0.py` y `orchestration/results/vigia/` (sin versionar), escritos por el agente anterior antes de morir; NO existen `orchestration/results/agy/B12.md` ni `orchestration/agy/DONE_B12.md`. Tú eres un agente nuevo: no rehagas desde cero; verifica lo que hay.

Qué hacer:
1. `git status --porcelain` (pega la salida) y lee los ficheros existentes.
2. Ejecuta los comandos de ACEPTACIÓN tal cual. Lo que falle, corrígelo (dentro del TERRITORIO). Lo que no puedas verificar: `NO DATA`.
3. Ejecuta la lectura ssh de ENTRADAS (solo lectura) y pégala en el informe; si `ssh oracle-vps` falla, `NO DATA` con el error.
4. Escribe `orchestration/results/agy/B12.md` (con las salidas crudas) y `orchestration/agy/DONE_B12.md`; cierre con `worker_done`.
