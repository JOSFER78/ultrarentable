# GO_A10 — Auditoría con tests de las deudas W4.2 / W4.4 / W4.6 que AG-C dio por cerradas

## Identidad
- ID: A10 · Ola: A · Rama/worktree: JOSFER78/agy-A10 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min
- Variables ya puestas en tu terminal: AGY_AGENT=A10, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.

## OBJETIVO (una frase verificable)
Cada una de las tres deudas queda con veredicto CERRADA o ABIERTA respaldado por un test real: W4.6 (`verificacion_f02.py` no destruye su baseline y aborta sin escribir ante celdas sin datos), W4.4 (los escritores `discovery_validation_pipeline.py` y `legacy_revalidation_service.py` escriben `gates_passed` real; `mine.py` ya tiene `tests/test_mine_gates_passed_write.py`), W4.2 (sin hardcode `5.4.0` de motor y sin `except` mudos alrededor de `engine_version`).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- tests/test_verificacion_f02_w46.py (nuevo)
- tests/test_gates_passed_escritores.py (nuevo)
- services/discovery/discovery_validation_pipeline.py (SOLO si W4.4 está abierta ahí; cambio mínimo)
- services/validation/legacy_revalidation_service.py (SOLO si W4.4 está abierta ahí; cambio mínimo)
- orchestration/results/agy/A10.md (nuevo) · orchestration/agy/DONE_A10.md (nuevo)
- SOLO LECTURA: scripts/mine.py (territorio de A11: si falta algo ahí es HALLAZGO, no lo toques), scripts/verificacion_f02.py, services/engine_version.py, orchestration/results/verificacion_f02_5.17.0.json.

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- `git show ad9e179ff --stat` (el commit de AG-C que dice cerrar W4.1/W4.2/W4.4/W2.6/W4.6) y su diff en los ficheros de tu territorio.
- orchestration/state/PLAN_LOCAL_FONDEO.md filas W4.2, W4.4, W4.6 (criterio de verificación de cada una).
- scripts/verificacion_f02.py: función `correr(out_path, force)` (~líneas 55-185) y `main()`; flags `--out`, `--force`, `--comparar`.
- tests/test_mine_gates_passed_write.py (patrón para tu test de escritores).
- services/discovery/discovery_validation_pipeline.py y services/validation/legacy_revalidation_service.py: `grep -n "gates_passed"` en ambos.

## PASOS (numerados, cortos, en orden)
1. Comprobar `git status --porcelain` vacío y `sha256sum orchestration/results/verificacion_f02_5.17.0.json` (anótalo: debe ser c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8 al final).
2. W4.6 — `tests/test_verificacion_f02_w46.py` (subprocess al script real, `tmp_path`, sin mocks): (a) destino existente sin `--force` ⇒ rc≠0, sha256 del destino intacto, mensaje de aborto; (b) en este worktree NO hay datasets de velas en `data/normalized` (solo manifiestos) ⇒ `--out tmp/nuevo.json` aborta con rc≠0 por celdas `SIN DATOS` y NO crea el fichero; (c) `--comparar 5.17.0 5.17.0` funciona (rc=0, 15 celdas idénticas) — solo lectura del baseline. Tras cada caso, sha256 del baseline 5.17.0 igual al del paso 1.
3. W4.4 — leer los dos escritores; para cada uno, test en `tests/test_gates_passed_escritores.py` que llame a la función real de escritura con un `gates_eval` de 11/11 sobre una BD SQLite temporal (usa el esquema real del proyecto: busca cómo lo crea `tests/test_mine_gates_passed_write.py`) y compruebe `gates_passed == 11` en la fila; y con 7/11 ⇒ 7. Si un escritor sigue escribiendo 0 ⇒ ABIERTA: corrígelo con el cambio mínimo (territorio) y deja el test verde.
4. W4.2 — `grep -rn --include=*.py -E "['\"]5\.4\.0['\"]" services scripts`: esperado solo services/engine_version.py (versiones de política, no de motor), comentarios "antes hardcodeado" y scripts/migrate_historical_candidates.py (literal histórico intencionado). Cualquier otro ⇒ ABIERTA (HALLAZGO; no lo toques si está fuera de tu territorio). `except` mudos: `grep -rn -B3 "except Exception: *pass\|except Exception:$" services/meta* services/api/app/api/*.py | grep -i -A3 "engine_version"` → lista lo que quede como HALLAZGO.
5. Informe con veredicto por deuda (CERRADA/ABIERTA + evidencia + qué test lo demuestra); DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_verificacion_f02_w46.py tests/test_gates_passed_escritores.py -q -p no:cacheprovider   # esperado: >= 5 passed
"$PY" -m pytest tests/test_mine_gates_passed_write.py -q -p no:cacheprovider    # esperado: igual que en HEAD (no se toca)
sha256sum orchestration/results/verificacion_f02_5.17.0.json                     # esperado: c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8
grep -rln --include=*.py -E "['\"]5\.4\.0['\"]" services scripts | sort         # esperado: solo engine_version.py, migrate_historical_candidates.py y ficheros cuyo único uso es un comentario "antes"
grep -cE "^\| W4\.[246] \| (CERRADA|ABIERTA)" orchestration/results/agy/A10.md   # esperado: 3
git diff --name-only   # ⊆ TERRITORIO (más GO_A10.md si el ORQ añadió CORRECCION_n)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor (services/validation/engine/ o services/engine_version.py)? NO
- ¿Ejecuta algo pesado? NO: `verificacion_f02.py` solo en los casos que abortan de inmediato (destino existente; sin datos) y `--comparar` (lectura). Nunca `--force`. Nunca sin `--out` hacia el baseline.
- Un test que "pasa" sin ejercer el código real (mock del script, sqlite falso) invalida la tarea.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm · datos sintéticos, mocks, random/seed, valores por defecto ante falta de dato · relajar umbrales · escribir fuera del TERRITORIO · tocar scripts/mine.py, scripts/verificacion_f02.py o services/engine_version.py · `--force` en verificacion_f02 · procesos largos sin admisión · inventar una salida que no se ejecutó · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A10.md: tabla `| Deuda | Veredicto | Evidencia | Test |` (3 filas), comandos y salida CRUDA, hallazgos fuera de territorio, veredicto propio.
3. orchestration/agy/DONE_A10.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A10 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
