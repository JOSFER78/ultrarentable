# GO_B02 — Experimento E1: las 20 `REVERSION_ATR` de ES sobre Dukascopy 5m/15m con el motor 5.18.0

## Identidad
- ID: B02 · Ola: B · Rama/worktree: JOSFER78/agy-B02 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min de trabajo tuyo (la campaña corre aparte, tú la lanzas, la supervisas y la lees)
- Variables ya puestas en tu terminal: AGY_AGENT=B02, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.
- Datos: `data/normalized/` de tu worktree está ENLAZADO al checkout principal (SOLO LECTURA): ahí están `ds_dukascopy_usa500idxusd_5m_consolidated.json` y `..._15m_consolidated.json` (ES, 250.009 y 83.377 barras). Prohibido escribir, crear o borrar nada en `data/`.

## OBJETIVO (una frase verificable)
Existen dos embudos de telemetría nuevos en `orchestration/results/telemetria/` (ES 5m y ES 15m, perfil `reversion`, 20 configuraciones, motor 5.18.0, `cobertura_por_familia` presente) y un informe que compara, configuración a configuración, el PF/ops de IS de esas 20 contra las mismas 20 del embudo de ES 4h Yahoo (`embudo_FONDEO_ES_4h_arquetipos_20260901T101102Z.json`, PF 0,03-0,19), separando con cifras: familia mala / dataset contaminado / bug de coste (`sin_ventaja_bruta` vs `sin_ventaja_por_coste`).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- orchestration/results/telemetria/ (solo los JSON que genere `mine.py` en tus dos ejecuciones)
- orchestration/results/agy/B02.md (nuevo) · orchestration/agy/DONE_B02.md (nuevo)
- SOLO LECTURA: scripts/mine.py, services/, data/, la BD canónica (mine.py escribe en ella por su vía normal; tú no haces UPDATE manual).

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/telemetria/embudo_FONDEO_ES_4h_arquetipos_20260901T101102Z.json (las 20 configs `UR_FONDEO_ES_4H_c1..c20`, todas REVERSION_ATR, todas muertas en IS con pf 0,03-0,19).
- orchestration/state/PLAN_LOCAL_FONDEO.md W2.x y la corrección D1/D2; orchestration/state/current_phase.md §7 punto 3 (qué debe separar E1).
- orchestration/results/W27_telemetria_bruto_neto.md (qué significan `sin_ventaja_bruta` y `sin_ventaja_por_coste`).
- `"$PY" scripts/mine.py --help` (flags reales: --track, --tf, --profile, --max-candidates, --dataset-source).
- services/ops/gobernanza_recursos.py (puerta de admisión; ya funciona en Windows).

## PASOS (numerados, cortos, en orden)
1. Comprobar: `git status --porcelain` vacío · `ls data/normalized/ds_dukascopy_usa500idxusd_5m_consolidated.json data/normalized/ds_dukascopy_usa500idxusd_15m_consolidated.json` · `grep -n 'CURRENT_ENGINE_VERSION: str' services/engine_version.py` ⇒ 5.18.0 · `"$PY" -m services.ops.gobernanza_recursos estado`.
2. Calcula ANTES de lanzar nada cuántas configs emite el perfil `reversion` para ES (lee la función del espacio de búsqueda en mine.py y ejecútala en un `-c`): anótalo. Si son más de 20, usarás `--max-candidates 20` para replicar exactamente las 20 del 4h (mismo orden de prefijo).
3. PESADO — pide admisión: `orca orchestration ask --question "B02 pide admisión para: mine.py ES 5m + 15m perfil reversion 20 configs vía gobernanza_recursos (2 procesos secuenciales)" --json`. Con el OK:
   `"$PY" -m services.ops.gobernanza_recursos ejecutar --nombre B02_E1_5m -- "$PY" scripts/mine.py --track fondeo --symbol ES --tf 5m --profile reversion --max-candidates 20 --dataset-source dukascopy` (ajusta el flag del símbolo al nombre real que use `--help`), y después lo mismo con `--tf 15m --nombre B02_E1_15m`. Uno detrás de otro, nunca en paralelo. Pega la salida CRUDA completa de ambos.
4. Localiza los dos embudos nuevos en `orchestration/results/telemetria/` (por `generado_utc` y `contexto`); comprueba `engine_version == "5.18.0"`, `max_candidates == 20`, `cobertura_por_familia`, y que cada registro trae `pf_bruto`, `pf_neto`, `coste_pct_del_bruto`.
5. Informe: tabla de 20 filas × {config, 4h Yahoo: etapa/pf, 5m: etapa/pf_neto/pf_bruto/trades, 15m: ídem} y las tres cuentas: cuántas siguen `sin_ventaja_bruta` (familia mala), cuántas pasan a `sin_ventaja_por_coste` (coste), cuántas cambian de veredicto por dataset. Conclusión en una frase por hipótesis, con las cifras. Si el motor aborta o el dataset no carga: NO DATA y por qué.
6. DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
ls -t orchestration/results/telemetria/embudo_FONDEO_ES_5m_*.json | head -1      # existe, generado hoy
ls -t orchestration/results/telemetria/embudo_FONDEO_ES_15m_*.json | head -1     # existe, generado hoy
for f in $(ls -t orchestration/results/telemetria/embudo_FONDEO_ES_5m_*.json | head -1) $(ls -t orchestration/results/telemetria/embudo_FONDEO_ES_15m_*.json | head -1); do "$PY" -c "import json,sys; j=json.load(open(sys.argv[1])); t=j['telemetria']; print(j['engine_version'], j['contexto'].get('max_candidates'), len(t), sum(1 for r in t if 'pf_bruto' in r), 'cobertura_por_familia' in json.dumps(j))" "$f"; done
# esperado por fichero: 5.18.0 20 20 20 True
grep -cE "^\| UR_FONDEO_ES_4H_c[0-9]+ " orchestration/results/agy/B02.md          # esperado: 20
grep -cE "sin_ventaja_bruta|sin_ventaja_por_coste" orchestration/results/agy/B02.md   # esperado: >= 2
git status --short data/normalized | wc -l                                       # esperado: 0
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO (solo ejecuta). ¿Ejecuta algo pesado? SÍ: dos campañas de 20 configs, SOLO vía `gobernanza_recursos ejecutar` y tras `orca orchestration ask`. Nunca `--max-candidates` distinto de 20 aquí (E1 replica las 20; E2 es otra tarea).
- No cambies umbrales ni flags de mine.py; no edites ficheros de código. Si mine.py falla por dataset (nombre del símbolo, ruta), pégalo tal cual y pregunta con `ask`.
- REAL-ONLY: cifras solo de los JSON y de la salida de mine.py.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm · escribir en data/ · tocar código · datos sintéticos · lanzar campañas sin admisión o en paralelo · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los JSON nuevos (SIN commit).
2. orchestration/results/agy/B02.md: comandos y salida CRUDA, tabla de 20 filas, tres cuentas, conclusión por hipótesis, lo que no se pudo.
3. orchestration/agy/DONE_B02.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "B02 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
