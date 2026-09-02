# GO_A11 — Telemetría: D2 (espacio completo por defecto) + W2.8 (métricas IS/VAL de quien supera la etapa)

## Identidad
- ID: A11 · Ola: A · Rama/worktree: JOSFER78/agy-A11 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min
- Variables ya puestas en tu terminal: AGY_AGENT=A11, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.

## OBJETIVO (una frase verificable)
`scripts/mine.py` y `scripts/cola_mineria.py` evalúan el espacio COMPLETO por defecto (`--max-candidates` = 0 en ambos; el embudo declara `truncado=False` y `espacio_total == evaluadas`), y cada registro de telemetría de un candidato que superó IS (y VAL) lleva `is_pf`, `is_trades` (y `val_pf`, `val_trades`); probado con `tests/test_mine_telemetria_d2_w28.py` y con los tests existentes de telemetría intactos y verdes.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/mine.py (SOLO: firma de `run_mining_pipeline` línea ~910 `max_candidates`, el `argparse` de `--max-candidates` línea ~1435, su docstring/ayuda, y los 4 puntos `telemetria.append(...)` del bucle principal ~1100-1213 más `_nueva_casilla_causas`/`resumir_causas` si hace falta para W2.8)
- scripts/cola_mineria.py (SOLO: default de `--max-candidates` línea ~318 y `_comando_mine`/`_lanzar` líneas ~147-166)
- tests/test_mine_telemetria_d2_w28.py (nuevo)
- orchestration/results/agy/A11.md (nuevo) · orchestration/agy/DONE_A11.md (nuevo)
- SOLO LECTURA: tests/test_mine_telemetria_cobertura_familias.py, tests/test_mine_telemetria_bruto_neto.py, tests/test_mine_gates_passed_write.py (deben seguir verdes SIN tocarlos), services/ (nada del motor).

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/state/PLAN_LOCAL_FONDEO.md: corrección D1/D2 (líneas ~70-95) y fila W2.8 (línea ~97).
- orchestration/reviews/forense_telemetria_2026-09-01.md (por qué el default 20 mentía).
- scripts/mine.py líneas 800-1010 (bloque W2.6/W2.7: `UMBRALES_EMBUDO`, `_nueva_casilla_causas`, `resumir_causas`, `persistir_telemetria`, cálculo de `espacio_total`/`truncado` ~971-1007) y 1090-1215 (bucle: IS → VAL → OOS → GATES; los 4 `telemetria.append`).
- scripts/cola_mineria.py líneas 147-170 y 318 (`_comando_mine` pasa `payload.get("max_candidates") or max_candidates`; con default 0, `0 or 0` = 0: correcto).
- tests/test_mine_telemetria_cobertura_familias.py y tests/test_mine_telemetria_bruto_neto.py (cómo construyen un espacio pequeño y registros: copia el patrón; nada de campañas reales).

## PASOS (numerados, cortos, en orden)
1. Baseline: `"$PY" -m pytest tests/test_mine_telemetria_cobertura_familias.py tests/test_mine_telemetria_bruto_neto.py tests/test_mine_gates_passed_write.py -q -p no:cacheprovider` (pegar: esperado 3+8+N passed). `git status --porcelain` vacío.
2. D2: `max_candidates` por defecto 20 → 0 en la firma de `run_mining_pipeline` y en el `argparse` (help: "0 = espacio completo (D2); nunca truncar por defecto"); en `cola_mineria.py` default 2000 → 0 y comprobar que `_comando_mine` sigue pasando el valor explícito. NO cambiar la lógica de truncado ni los campos del embudo (`max_candidates`, `espacio_total`, `truncado` ya existen).
3. W2.8: en el bucle, tras el backtest IS que SUPERA el filtro, guarda `is_pf`/`is_trades`; tras VAL superado, `val_pf`/`val_trades`; añade esas claves (solo las que existan en esa etapa) a los registros de telemetría de VAL, OOS y GATES (los de IS ya llevan `pf`/`trades`). Nada de valores por defecto: si no existe la etapa, la clave no aparece.
4. Test `tests/test_mine_telemetria_d2_w28.py` (mismo patrón que los existentes; espacio pequeño real; sin mocks del motor): (a) `run_mining_pipeline` sin `max_candidates` ⇒ embudo con `truncado is False` y `espacio_total == len(evaluadas)`; (b) `argparse` de mine.py: `--max-candidates` default 0; (c) `cola_mineria._comando_mine({})` contiene `"--max-candidates", "0"`; (d) un candidato que muere en VAL lleva `is_pf` e `is_trades` numéricos y NO lleva `val_pf`; uno que muere en OOS lleva `is_*` y `val_*`; (e) un registro de IS no lleva `is_pf` (solo `pf`).
5. Verifica la cifra real del espacio `arquetipos`: `"$PY" -c "..."` que construya el espacio de búsqueda del perfil `arquetipos` (busca la función en mine.py) e imprima `len` y el conteo por familia; pégalo en el informe (el plan dice 420 y 6 familias: confirma o refuta con el número real).
6. Ejecutar ACEPTACIÓN; informe con salida cruda; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_mine_telemetria_d2_w28.py tests/test_mine_telemetria_cobertura_familias.py tests/test_mine_telemetria_bruto_neto.py tests/test_mine_gates_passed_write.py -q -p no:cacheprovider   # esperado: todos passed (>= 5 nuevos + 11 existentes)
"$PY" scripts/mine.py --help | grep -A2 -- "--max-candidates"          # esperado: default 0 / "espacio completo"
grep -n "max_candidates: int = " scripts/mine.py                        # esperado: max_candidates: int = 0
grep -n 'default=' scripts/cola_mineria.py | grep -i "max.candidates"   # esperado: default=0
grep -c "is_pf" scripts/mine.py                                          # esperado: >= 3
git diff --name-only   # ⊆ TERRITORIO (más GO_A11.md si el ORQ añadió CORRECCION_n); esperado: scripts/mine.py scripts/cola_mineria.py
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor (services/validation/engine/ o services/engine_version.py)? NO (telemetría y defaults de CLI; el motor no se toca).
- ¿Ejecuta algo pesado? NO. Prohibido lanzar campañas reales o `cola_mineria.py trabajar`.
- El bucket `sin_ventaja` y sus sub-buckets (W2.7) NO cambian. Los umbrales de IS/VAL/OOS NO cambian.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm · datos sintéticos, mocks del motor, random/seed, valores por defecto ante falta de dato · relajar umbrales · escribir fuera del TERRITORIO · tocar services/ · campañas reales · inventar una salida que no se ejecutó · declarar subagentes · editar los tests existentes.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A11.md: comandos y salida CRUDA (baseline y final), cifra real del espacio `arquetipos` por familia, hallazgos, veredicto propio.
3. orchestration/agy/DONE_A11.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A11 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
