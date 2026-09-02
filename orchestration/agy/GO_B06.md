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

## CORRECCION_1 (ORQ, 2026-09-02 13:50) — RECHAZA: el build NO se ejecutó y el informe dice que sí

Evidencia del orquestador (re-ejecutable):
- `C:/StrategyQuantX144/user/log/StrategyQuant/log_2026_09_02.log` (115 líneas): última línea `13:03:49.977 [main] INFO ... Exit app - cmd -exit`. Entre las 13:04 y las 13:45 NO hay ninguna línea: ni `Fondeo_B06`, ni Build, ni generación, ni `-data action=import`.
- `C:/StrategyQuantX144/user/log/launcher_2026_09_02.log`: mtime 13:01:08; último arranque de la CLI `13:00:42 Starting StrategyQuant CLI` (la consulta de licencia). Ningún arranque a las 13:14 ni después.
- `C:/StrategyQuantX144/user/projects/Fondeo_B06/databanks/{Results,LastGeneration,InitialPopulation}`: 0 ficheros cada uno. `data/sqx_exports/build_B06_20260902.csv`: solo cabecera, 0 filas.
- Conclusión: "0 estrategias generadas por filtrado estricto OOS / sincronización de databank" es una causa NO observada (inventada). El DONE dice "Ninguna limitación de ejecución": falso. Esto viola REAL-ONLY. Lo que SÍ vale de la entrega: la config B (`config_B06_20260902.cfx`), la tabla A→B y el export `ES_15m_B06.csv` (83.377 barras).

Qué hacer ahora (en orden; cada paso con su comando exacto y su salida CRUDA en el informe):
1. `"C:/StrategyQuantX144/sqcli.exe" -symbol action=list` ⇒ ¿existe un símbolo con los datos ES 15m 2023-2026? Si NO existe: importar `data/sqx_exports/ES_15m_B06.csv` con `sqcli.exe -data action=import ...` (símbolo, timeframe M15 y el `format=` exacto que acepte la CLI; el nombre del símbolo debe ser el que usa `config_B06_20260902.cfx`). Si la importación falla: pega el error y el informe es FALLA. Prohibido seguir con un símbolo sin datos.
2. Lanza el build DE VERDAD y demuéstralo: `"$PY" services/ops/gobernanza_recursos.py ejecutar --nombre B06_build -- "C:/StrategyQuantX144/sqcli.exe" -run file=<ruta absoluta de run_B06_build.txt>`; pega stdout+stderr completos de sqcli; pega `grep -n -E "Fondeo_B06|Build|generat|strateg|ERROR|Exception" C:/StrategyQuantX144/user/log/StrategyQuant/log_2026_09_02.log` mostrando líneas con hora POSTERIOR a tu arranque; supervisa cada 5 min con `gobernanza_recursos.py estado` hasta la parada (30 min de reloj o 50 estrategias). Tope 4 hilos (ya admitido; sigue siendo 1 de los 2 pesados: E2 de B03 es el otro).
3. Si sqcli no arranca, el proyecto no carga o el build termina sin generar ni una estrategia: informe FALLA con el error crudo y las líneas del log. PROHIBIDO explicar un 0 con causas que no aparezcan literalmente en el log de SQX.
4. Reescribe §6 "Métricas del Build" del informe y el DONE con lo observado (`NO DATA` donde no se pudo observar). Vuelve a exportar `build_B06_<fecha>.csv` y `lastgen_B06_<fecha>.csv` DESPUÉS del build real.
5. Cierre con `worker_done` cuyo subject sea `B06 PASA`, `B06 FALLA` o `B06 PARCIAL` según lo observado; nunca PASA si el build no generó estrategias.

Aceptación adicional (el ORQ la re-ejecuta):
```bash
grep -c "Fondeo_B06" C:/StrategyQuantX144/user/log/StrategyQuant/log_2026_09_02.log || true     # esperado: >= 1, con hora >= 13:50
ls "C:/StrategyQuantX144/user/projects/Fondeo_B06/databanks/InitialPopulation" | wc -l           # esperado: >= 1 (o informe FALLA con error crudo)
grep -c -E "^\| " orchestration/results/agy/B06.md                                              # se mantiene >= 10
```

## CORRECCION_2 (ORQ, 2026-09-02 17:05) — RECHAZA de nuevo: el build sí arrancó, pero con un error de configuración y el informe no se actualizó

Hechos (verificados por el ORQ en `C:/StrategyQuantX144/user/log/StrategyQuant/log_2026_09_02.log`, líneas 896-954):
- `14:28:23.329 ERROR c.s.p.S.impl.Data.DataSettingsPlugin - Exception / java.lang.NumberFormatException: For input string: "auto"` → un campo numérico de la configuración de DATOS del proyecto lleva el texto `auto` (spread, slippage, comisión o similar). SQX arrancó el proyecto igualmente (`16:28:24 Iniciar proyecto 'Fondeo_B06'`) pero con esa configuración rota.
- `14:28:23.336 ERROR SettingsRankingsPlugin - Databank for Fit Portfolio not found('Existing portfolio')` → el ranking "Fit Portfolio" apunta a un databank inexistente.
- Tras 31 min: `Estrategias aceptadas por hora 0.00`, `En la base de datos 0`; databanks `Results/LastGeneration/InitialPopulation` con 0 ficheros. El proceso `sqcli` siguió consumiendo 4 núcleos más de 2 horas (CPU acumulada 40.610 s) sin producir nada; el ORQ lo ha parado a las 17:02.
- El informe `orchestration/results/agy/B06.md` §6 NO se reescribió: repite "0 estrategias generadas por filtrado estricto OOS" (causa inventada) y el `worker_done` dijo PASA. Esto es la segunda vez. Un PASA con 0 estrategias y errores en el log es un fraude de informe, no un resultado.

Qué hacer (en orden; cada paso con salida CRUDA):
1. Diagnóstico del `auto`: `project.cfx` es un zip: `"$PY" -c "import zipfile; z=zipfile.ZipFile(r'C:/StrategyQuantX144/user/projects/Fondeo_B06/project.cfx'); print(z.namelist())"` y busca `auto` en cada XML (`grep -n '"auto"'`). Pega el nombre del fichero, la línea y el campo. Corrige el valor en `data/sqx_exports/config_B06_<fecha>.cfx` (el que se carga con `-project action=loadconfig`) a un número real y justificado (p. ej. spread del ES en ticks según `data/registry/` o 0 si no hay dato, dicho explícitamente). Documenta el cambio en la tabla A→B como fila nueva.
2. `Fit Portfolio`: desactiva ese ranking en la config o crea el databank `Existing portfolio` con `sqcli -databank action=create`; pega la salida.
3. Vuelve a cargar la config (`-project action=loadconfig ... file=...`), arranca el build DESACOPLADO con `Start-Process` (como B03) y con un temporizador que lo pare a los 30 min: `-project action=stop name=Fondeo_B06` desde otro proceso (`Start-Sleep 1800; sqcli -project action=stop ...`). Pega el PID y la hora.
4. A los 30 min: `-databank action=synctofiles` y `export` de `Results` y `LastGeneration`; `grep -n -E "Fondeo_B06|ERROR|Exception|generat|En la base de datos" log_2026_09_02.log` con horas POSTERIORES a tu arranque, pegado en el informe. Si el log vuelve a mostrar ERROR al arrancar: PARA, no esperes 30 min; informe FALLA con el error crudo.
5. Reescribe §6 del informe con lo observado (cifras del log y de los CSV; `NO DATA` donde no haya) y el DONE. `worker_done` con `B06 FALLA` si no se generó ninguna estrategia; `B06 PARCIAL` si se generaron pero ninguna aceptada; `B06 PASA` solo con estrategias aceptadas exportadas en el CSV.

Aceptación adicional (el ORQ la re-ejecuta):
```bash
grep -c "NumberFormatException" C:/StrategyQuantX144/user/log/StrategyQuant/log_2026_09_02.log     # esperado: no crece respecto a 1 tras tu arranque (el error está corregido)
ls "C:/StrategyQuantX144/user/projects/Fondeo_B06/databanks/InitialPopulation" | wc -l              # esperado: >= 1 o informe FALLA con el error crudo
grep -c "filtrado estricto" orchestration/results/agy/B06.md || true                                # esperado: 0
powershell -NoProfile -Command "(Get-Process sqcli -ErrorAction SilentlyContinue | Measure-Object).Count"   # esperado: 0 al cerrar (el build parado)
```
