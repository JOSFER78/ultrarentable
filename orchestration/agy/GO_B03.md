# GO_B03 — Experimento E2: campaña ES 5m + 15m, 6 familias completas (D2), telemetría con cobertura, motor 5.18.0

## Identidad
- ID: B03 · Ola: B · Rama/worktree: JOSFER78/agy-B03 · Timebox: 45 min de trabajo tuyo (las campañas corren aparte; tú lanzas, supervisas, lees)
- Variables ya puestas: AGY_AGENT=B03, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- Datos: `data/normalized/` enlazado al checkout principal, SOLO LECTURA (ES 5m/15m consolidados).

## OBJETIVO (una frase verificable)
Dos embudos nuevos (ES 5m y ES 15m, perfil `arquetipos`, espacio COMPLETO: `max_candidates == 0`, `truncado == False`, `cobertura_por_familia` con las 6 familias) generados con el motor 5.18.0, y un informe con el veredicto data-vs-edge por celda aplicando las reglas pre-selladas de `PLAN_LOCAL_FONDEO.md` W2 (agotada solo si las 6 familias están representadas y ≥80 % muere por `sin_ventaja`; ≥50 % `pocas_operaciones` ⇒ frecuencia/datos; near-miss ⇒ alta en semillas W3).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- orchestration/results/telemetria/ (solo los JSON que genere mine.py en tus ejecuciones)
- orchestration/results/agy/B03.md (nuevo) · orchestration/agy/DONE_B03.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/state/PLAN_LOCAL_FONDEO.md: bloque W2 completo (D1, D2 y las reglas de decisión pre-selladas).
- orchestration/results/W27_telemetria_bruto_neto.md y orchestration/results/agy/A11.md (espacio real del perfil `arquetipos` = 420 configuraciones, 6 familias; campos `is_pf/is_trades/val_pf/val_trades`).
- `"$PY" scripts/mine.py --help`; services/ops/gobernanza_recursos.py.
- Si B02 ya terminó: orchestration/results/agy/B02.md (para no repetir su lectura; E2 la amplía).

## PASOS (numerados, cortos, en orden)
1. Comprobar: `git status --porcelain` vacío · datasets ES 5m/15m presentes · motor 5.18.0 · `gobernanza_recursos estado`.
2. Calcula ANTES el tamaño del espacio `arquetipos` para ES y el conteo por familia (función del espacio en mine.py, en un `-c`); esperado 420 y 6 familias: pega el resultado.
3. PESADO — pide admisión: `orca orchestration ask --question "B03 pide admisión para: mine.py ES 5m y 15m perfil arquetipos espacio completo (420 configs cada uno) vía gobernanza_recursos, secuencial" --json`. Con el OK: `"$PY" -m services.ops.gobernanza_recursos ejecutar --nombre B03_E2_5m -- "$PY" scripts/mine.py --track fondeo --symbol ES --tf 5m --profile arquetipos --dataset-source dukascopy` (sin `--max-candidates`: el default ya es 0 = completo; verifícalo en la cabecera de salida de mine.py), luego `--tf 15m --nombre B03_E2_15m`. Secuencial. Cada ejecución puede tardar mucho: supervisa con `gobernanza_recursos estado` cada 5 min y pega los latidos; no la mates.
4. Al terminar cada una: localiza el embudo, verifica `max_candidates == 0`, `truncado == False`, `espacio_total == 420`, `cobertura_por_familia` con 6 claves, `engine_version == 5.18.0`.
5. Informe por celda (5m, 15m): tabla `familia | evaluadas | muertas IS | sin_ventaja (bruta/por_coste) | pocas_operaciones | supervivientes IS | VAL | OOS | near-misses`; aplica las reglas pre-selladas y escribe el veredicto literal por celda (`AGOTADA` / `FALTA FRECUENCIA O DATOS` / `SIGUE` / `NEAR-MISS: <ids>`). Los near-miss (≥7/11 gates o PF OOS ≥1,25 con <200 ops) listados con sus cifras.
6. DONE; cierre. Si el timebox se agota con una campaña corriendo: informe PARCIAL con lo que hay y el PID/estado; el ORQ continúa.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
for tf in 5m 15m; do f=$(ls -t orchestration/results/telemetria/embudo_FONDEO_ES_${tf}_arquetipos_*.json | head -1); "$PY" -c "import json,sys; j=json.load(open(sys.argv[1])); c=j['contexto']; print(j['engine_version'], c.get('max_candidates'), c.get('espacio_total'), c.get('truncado'), len(j.get('cobertura_por_familia', c.get('cobertura_por_familia', {}))))" "$f"; done
# esperado por fichero: 5.18.0 0 420 False 6
grep -cE "^\| (REVERSION_ATR|OPENING_RANGE_BREAKOUT|VWAP_REVERSION|SQUEEZE_BREAKOUT|[A-Z_]+) \|" orchestration/results/agy/B03.md   # esperado: >= 12 (6 familias x 2 celdas)
grep -cE "AGOTADA|FALTA FRECUENCIA|SIGUE|NEAR-MISS" orchestration/results/agy/B03.md   # esperado: >= 2 (un veredicto por celda)
git status --short data/normalized | wc -l                                            # esperado: 0
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? SÍ: dos campañas completas, SOLO vía gobernanza y tras `ask`; secuenciales; nunca junto a B02 (si B02 sigue corriendo, espera y dilo).
- NUNCA se toca un umbral del criterio 1.1 ni de mine.py. Si todo da 0 supervivientes, se reporta así: es un resultado válido.
- La telemetría se persiste sola (W2.6): si no aparece el JSON, es FALLA (no "lo apunto a mano").

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir en data/ · tocar código · datos sintéticos · campañas sin admisión o en paralelo · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los JSON nuevos (SIN commit).
2. orchestration/results/agy/B03.md con comandos, salida cruda, tablas por celda y veredictos.
3. orchestration/agy/DONE_B03.md.
4. Cierre: orca orchestration send --type worker_done --subject "B03 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
