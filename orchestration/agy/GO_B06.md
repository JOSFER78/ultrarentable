# GO_B06 — W3.2: config del Builder de SQX corregida (A/B) y Build de prueba headless ANTES del 2026-09-05

## Identidad
- ID: B06 · Ola: B · Rama/worktree: JOSFER78/agy-B06 · Timebox: 45 min de trabajo tuyo (el Build corre acotado a 30 min de reloj; tú lo lanzas, supervisas y lees)
- Variables ya puestas: AGY_AGENT=B06, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- SQX: `C:/StrategyQuantX144` (Pro Build 144, licencia TRIAL válida hasta 2026-09-05; `sqcli.exe` headless tarda 1-3 min en arrancar por invocación). Sus datos (`user/projects/`, `user/settings/Configs/`) están FUERA del repo: ahí puedes crear un proyecto NUEVO; jamás modificar los proyectos existentes salvo copia.

## OBJETIVO (una frase verificable)
Un informe con el A/B medido: config A = la heredada de `Ultra_Matrix` (backups `.cfx` del repo) tal cual; config B = corregida según I1 (fusible Monte Carlo coherente con `MinTradesInRun`, `MaxTradesPerDay=0` confirmado, databank con nombre direccionable sin el desajuste `LastGeneration`/`Last generation`, fitness custom o ranking con proxy del criterio 1.1: nº trades OOS y PF OOS, sesión RTH y comisiones/slippage reales de MES, hilos ≤4); un Build headless de B acotado a 30 min con `sqcli.exe` que deja estrategias PERSISTIDAS en el databank en disco; export CSV de sus métricas a `data/sqx_exports/build_B06_<fecha>.csv`; y las cifras: estrategias generadas, % aceptadas, tiempo, coste CPU. Si el Build no produce nada, se reporta 0 con la causa.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- data/sqx_exports/ (solo ficheros nuevos `build_B06_*.csv` y `config_B06_*.cfx`)
- `C:/StrategyQuantX144/user/projects/Fondeo_B06/` (proyecto NUEVO, fuera del repo; creado por ti o por sqcli)
- orchestration/results/agy/B06.md (nuevo) · orchestration/agy/DONE_B06.md (nuevo)
- SOLO LECTURA: `C:/StrategyQuantX144/**` (resto), `estrategias_um/**`, services/sqx_bridge/**.

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/I1_sqx_hallazgos.md ENTERO (inventario real: proyectos, `Builder`, `Fondeo_Test_A/B`, cross-checks, Custom Projects, causa de la esterilidad: desajuste de nombre del databank, fusible MC, `MaxTradesPerDay` real = 0).
- estrategias_um/evidencia/backups_cfx/backup_Ultra_Matrix_pre_mcfix_20260829_145109.cfx (config A: ZIP con XML; ábrelo y documenta los parámetros del Builder y de los cross-checks).
- `C:/StrategyQuantX144/user/projects/Fondeo_Test_A/project.cfx` y `Fondeo_Test_B/project.cfx` (existen: inspecciónalos, son solo lectura; di qué son y si sirven de base para B).
- `sqcli.exe -h` (pega la salida completa una vez) y services/sqx_bridge/sqx_client.py (cómo se ha invocado sqcli hasta ahora; "fire-and-verify").
- services/sqx_bridge/export_to_sqx.py + data/normalized/ds_dukascopy_usa500idxusd_15m_consolidated.json del checkout principal (para importar ES 15m a SQX con naming `ES_15m` si el proyecto no tiene datos: usa `export_to_sqx.py --input <ruta absoluta del checkout principal> --output data/sqx_exports/ES_15m_B06.csv` y `sqcli -data action=import` según su ayuda).
- orchestration/state/PLAN_LOCAL_FONDEO.md W3.1/W3.2 y PLAN_INVESTIGACION_PROFUNDA.md I1 preguntas 3-5.

## PASOS (numerados, cortos, en orden)
1. `sqcli.exe -license action=info` (pega literal: debe seguir válida) y `sqcli.exe -h`. Documenta en el informe la tabla de diferencias A → B parámetro a parámetro, con la razón de cada cambio (cita I1).
2. Construye `Fondeo_B06/project.cfx` como copia de A con los cambios de B (un .cfx es un ZIP con XML: descomprime, edita, recomprime; guarda también la copia en `data/sqx_exports/config_B06_<fecha>.cfx`). Hilos ≤4. Duración del Build acotada por config (30 min) o por tu supervisión.
3. Datos: si el proyecto necesita importar ES 15m, hazlo con `export_to_sqx.py` + `sqcli -data action=import` (pesado ligero: pide admisión con `orca orchestration ask` igualmente).
4. PESADO — pide admisión: `orca orchestration ask --question "B06 pide admisión para: sqcli Build headless Fondeo_B06, ≤4 hilos, 30 min" --json`. Con el OK, lanza el Build vía `gobernanza_recursos ejecutar --nombre B06_build -- <sqcli ...>`; supervisa cada 5 min (`gobernanza_recursos estado`, tamaño del databank en disco); a los 30 min, si sigue, detenlo por la vía que documente `sqcli -h` (nunca matando SQX a ciegas si hay otra forma).
5. Exporta las métricas del databank a CSV (`sqcli` según ayuda) a `data/sqx_exports/build_B06_<fecha>.csv`; cuenta estrategias, % que superan los cross-checks, tiempo total, CPU media (de `gobernanza_recursos estado`).
6. Informe + DONE + cierre. Si la licencia falla o sqcli no arranca: NO DATA y salida literal.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
ls data/sqx_exports/config_B06_*.cfx data/sqx_exports/build_B06_*.csv                  # existen
"C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe" -c "import csv,glob; f=sorted(glob.glob('data/sqx_exports/build_B06_*.csv'))[-1]; r=list(csv.DictReader(open(f,encoding='utf-8',errors='replace'))); print(f, len(r), list(r[0].keys())[:8] if r else 'VACIO')"   # esperado: n filas y columnas de métricas
ls "C:/StrategyQuantX144/user/projects/Fondeo_B06/databanks/" | head             # databank(s) en disco
grep -cE "^\| " orchestration/results/agy/B06.md                                  # esperado: >= 10 (tabla A→B)
grep -E "estrategias generadas|aceptadas|NO DATA" orchestration/results/agy/B06.md | head -3
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO (SQX es M1; el motor propio no se toca). ¿Ejecuta algo pesado? SÍ: import y Build, SOLO con admisión y vía gobernanza; hilos ≤4; 30 min máximo.
- No toques `Builder`, `Ultra_Matrix` ni ningún proyecto existente de SQX: proyecto nuevo `Fondeo_B06`.
- No compres ni actives nada (la licencia es decisión de Emilio). Si SQX pide login/activación: NO DATA y para.
- REAL-ONLY: cifras solo de sqcli/CSV/databank.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · modificar proyectos SQX existentes · escribir fuera del TERRITORIO · Build sin admisión · más de 4 hilos · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los ficheros nuevos (SIN commit; los CSV pequeños de sqx_exports sí se versionan, como el toimprove). 2. orchestration/results/agy/B06.md. 3. orchestration/agy/DONE_B06.md.
4. Cierre: orca orchestration send --type worker_done --subject "B06 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
