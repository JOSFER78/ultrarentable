# GO_B05 — W3.3 piloto: 20 estrategias `.sqx` → AST canónico → registro de gates, coste medido

## Identidad
- ID: B05 · Ola: B · Rama/worktree: JOSFER78/agy-B05 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B05, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- Datos: `data/normalized/` enlazado al checkout principal, SOLO LECTURA. SQX instalado en `C:/StrategyQuantX144` (SOLO LECTURA; no ejecutes SQX).

## OBJETIVO (una frase verificable)
Un script `services/sqx_bridge/parse_sqx_piloto.py` que localiza los ficheros `.sqx` del databank ToImprove (2.035 según `data/sqx_exports/toimprove_2026-08-31.csv`), parsea 20 de ellos (un `.sqx` es un ZIP con XML dentro: descomprímelo y léelo) a un AST canónico (`contracts/canonical_strategy.py`), y pasa cada uno por `RegistryPipeline` (`services/validation/registry`) con la evidencia real que exista; informe con 20 filas (id, familia/indicadores, ¿AST completo?, gates aprobados, coste en segundos por estrategia) y el coste total medido. `NO DATA` donde el .sqx no se pueda expresar en el AST.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/sqx_bridge/parse_sqx_piloto.py (nuevo)
- tests/test_parse_sqx_piloto.py (nuevo; usa 2-3 .sqx REALES copiados a `tests/fixtures/sqx/` — territorio también)
- tests/fixtures/sqx/ (nuevo; máximo 3 ficheros .sqx reales, < 200 KB cada uno)
- orchestration/results/agy/B05.md (nuevo) · orchestration/agy/DONE_B05.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- data/sqx_exports/toimprove_2026-08-31.csv (2.035 filas, 44 columnas: nombres de estrategia y métricas de SQX).
- orchestration/results/I1_sqx_hallazgos.md (inventario de SQX en el PC; dónde viven los databanks/proyectos: búscalo ahí antes de rastrear el disco; si no lo dice, `find /c/StrategyQuantX144 -iname "*.sqx" | head`).
- contracts/canonical_strategy.py (el AST canónico: entradas, salidas, indicadores, SessionWindow, hash).
- services/validation/registry/ (RegistryPipeline, Evidencia) y tests/test_gate_registry_paridad_b.py (cómo construir Evidencia).
- services/sqx_bridge/converter.py y ingest_sqx_results.py (lo que ya existe: reutiliza, no dupliques).

## PASOS (numerados, cortos, en orden)
1. Localiza los .sqx (ruta exacta y conteo real `find ... | wc -l`); compara con 2.035 del CSV; anota la diferencia.
2. Inspecciona UN .sqx: `unzip -l` y el XML principal; documenta las 5-8 etiquetas que codifican reglas de entrada/salida, indicadores, parámetros, SL/TP.
3. Escribe el parser (funciones puras: `leer_sqx(path) -> dict`, `a_ast_canonico(dict) -> CanonicalStrategy | None` con lista de motivos `NO DATA` por campo no mapeable). Sin inventar reglas: lo que no esté en el XML es `None`/NO DATA.
4. Para las 20 primeras del CSV (orden del CSV) que existan en disco: parsear, medir `time.perf_counter()` por estrategia, construir `Evidencia` con `candidate_info` mínimo (route FONDEO, symbol/timeframe del .sqx) y SIN trades/velas inventados (los gates que exigen evidencia fallarán: es el resultado honesto del piloto), ejecutar `RegistryPipeline().veredicto(ev)`.
5. Test con 2-3 .sqx reales copiados a `tests/fixtures/sqx/`: parseo determinista, AST con `strategy_hash` estable en dos pasadas, y NO DATA explícito para un campo ausente.
6. Informe con tabla de 20 filas, coste total y por estrategia, % de ASTs completos, y qué haría falta (evidencia de backtest propio) para que el registro pueda certificar.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_parse_sqx_piloto.py -q -p no:cacheprovider          # esperado: >= 3 passed
"$PY" services/sqx_bridge/parse_sqx_piloto.py --csv data/sqx_exports/toimprove_2026-08-31.csv --n 20 --out /tmp/b05_piloto.json; echo "rc=$?"   # esperado: rc=0, imprime 20 filas y coste total
"$PY" -c "import json; j=json.load(open('/tmp/b05_piloto.json')); print(len(j['estrategias']), sum(1 for e in j['estrategias'] if e.get('ast_completo')), round(j['coste_total_s'],1))"   # esperado: 20 <n_completos> <segundos>
ls tests/fixtures/sqx/*.sqx | wc -l                                              # esperado: 2 o 3
grep -cE "^\| " orchestration/results/agy/B05.md                                  # esperado: >= 21
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO (no se toca services/validation/engine ni engine_version). ¿Ejecuta algo pesado? NO (20 parseos + gates sin backtest: segundos). Prohibido lanzar SQX o `sqcli`.
- REAL-ONLY: cero trades/velas inventados para "hacer pasar" gates; el piloto mide parseo y coste, no certifica.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir fuera del TERRITORIO · tocar services/validation/engine, engine_version.py, converter.py existente · datos sintéticos · ejecutar SQX · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B05.md con salida cruda y tabla. 3. orchestration/agy/DONE_B05.md.
4. Cierre: orca orchestration send --type worker_done --subject "B05 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
