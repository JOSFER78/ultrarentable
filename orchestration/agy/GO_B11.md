# GO_B11 — W1.2/W1.3 + cierre de B01: inventario verificado de datos FONDEO en el PC y el VPS, consolidación de lo que exista

## Identidad
- ID: B11 · Ola: B · Rama/worktree: JOSFER78/agy-B11 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B11, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- Datos: `data/normalized/` de tu worktree está ENLAZADO al checkout principal. Aquí SÍ puedes escribir, pero SOLO ficheros nuevos `*_consolidated.json` + su `_manifest.json` producidos por `scripts/herramientas/consolidar_dukascopy.py`; jamás modificar ni borrar un fichero existente.
- ssh al VPS: `ssh oracle-vps` funciona sin contraseña. SOLO LECTURA en el VPS (ls, du, sha256sum, cat): ningún comando que escriba, pare o instale nada allí.

## OBJETIVO (una frase verificable)
Un inventario en `orchestration/results/agy/B11.md` con, por símbolo del universo FONDEO (ES=USA500IDXUSD, NQ=USATECHIDXUSD, YM=USA30IDXUSD, GC=XAUUSD, SI=XAGUSD, CL=LIGHTCMDUSD, y los 6 majors forex que nombra W1.1) y timeframe (1m/5m/15m/1h/4h): trimestres presentes en el PC (con `bar_count` y `hours_failed` del manifiesto), consolidados presentes (con `sha256` verificado contra manifiesto vía `services.data.market_ingestor.verificar_dataset_contra_manifiesto`), y lo que existe en el VPS y NO en el PC (ruta, tamaño, sha256); más los consolidados 5m/15m NUEVOS de cualquier símbolo cuyos trimestres estén completos en el PC y aún no tenga consolidado, con su manifiesto y verificación de custodia.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- data/normalized/ (SOLO ficheros nuevos `ds_dukascopy_<símbolo>_<tf>_consolidated.json` y `..._manifest.json`)
- orchestration/results/agy/B11.md (nuevo) · orchestration/agy/DONE_B11.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/state/PLAN_LOCAL_FONDEO.md W1.1-W1.8 (universo, W1.3 correlación ≥0,90 o NO APTO, W1.5 RTY fuera).
- scripts/herramientas/consolidar_dukascopy.py (`--help`; cómo se consolidó ES: 16 chunks → 5m/15m/1m, gaps clasificados por calendario).
- services/data/market_ingestor.py (`verificar_dataset_contra_manifiesto`, A04).
- orchestration/results/AG-D_datos_2026-09-01.md y results/setup/orq_sync_vps_datasets_20260901.log (qué se rescató del VPS y a dónde).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain data/normalized` vacío. Inventario PC: `ls data/normalized/*_manifest.json` agrupado por símbolo/tf; lee de cada manifiesto `bar_count`, `hours_failed`, rango; tabla.
2. Verificación de custodia de TODOS los consolidados presentes con `verificar_dataset_contra_manifiesto` (pega el resumen: n, coinciden, no coinciden con motivo).
3. Inventario VPS (solo lectura): `ssh oracle-vps 'find ~ -maxdepth 6 -path "*normalized*" -name "*_manifest.json" 2>/dev/null | head -400'` y para lo que no exista en el PC: `sha256sum` y tamaño. Tabla "solo en VPS".
4. Para cada símbolo con trimestres 2023-01→2026-08 completos en el PC en 5m y 15m y SIN consolidado: consolida con el script (misma invocación que ES; pega la salida), genera manifiesto y verifica custodia. Si ningún símbolo está completo: NO DATA y la lista de trimestres que faltan por símbolo.
5. W1.3 solo si hay muestra Yahoo del mismo símbolo en `data/normalized` (`ds_trad_*`): correlación de retornos diarios proxy↔CME y peor subperiodo; si no hay muestra: NO DATA.
6. Informe + DONE + cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
grep -cE "^\| (USA500IDXUSD|USATECHIDXUSD|USA30IDXUSD|XAUUSD|XAGUSD|LIGHTCMDUSD|EURUSD|GBPUSD|USDJPY|AUDUSD|USDCAD|USDCHF)" orchestration/results/agy/B11.md   # esperado: >= 12
grep -cE "solo en VPS|SOLO EN VPS" orchestration/results/agy/B11.md               # esperado: >= 1
for f in $(ls data/normalized/*_consolidated.json); do "$PY" -c "import sys; from services.data.market_ingestor import verificar_dataset_contra_manifiesto as v; from pathlib import Path; r=v(Path(sys.argv[1])); print(Path(sys.argv[1]).name, r.coincide, r.motivo)" "$f"; done   # esperado: todos True OK
git status --short data/normalized | grep -v "^??" | wc -l                       # esperado: 0 (nada existente modificado ni borrado)
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? La consolidación de un símbolo en 5m/15m sí (minutos, CPU): pide admisión con `orca orchestration ask` antes de cada consolidación; los inventarios y hashes no son pesados.
- Nunca relanzar el backfill (W1.7 recién integrada, pero el backfill real lo lanza el ORQ). Nunca `rm`, nunca sobrescribir un consolidado existente.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · sobrescribir ficheros existentes en data/ · escribir en el VPS · backfill · datos sintéticos · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los consolidados nuevos (SIN commit; los .json de velas están ignorados por git, los manifiestos no). 2. orchestration/results/agy/B11.md. 3. orchestration/agy/DONE_B11.md.
4. Cierre: orca orchestration send --type worker_done --subject "B11 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
