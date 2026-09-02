# GO_B08 — W6.0: nacimiento de `services/meta/` (M4, D8/D9) desde los dos módulos vivos, con correlación honesta (W4.5)

## Identidad
- ID: B08 · Ola: B · Rama/worktree: JOSFER78/agy-B08 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B08, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
Existe `services/meta/` con: `estados.py` (un ÚNICO `certified_statuses` que unifica los que hoy divergen entre `meta_ensemble_service.py:138-145` y `meta_strategy_pipeline.py:48`), `correlacion.py` (correlación de RETORNOS por operación/día con solape temporal real mínimo; con ≤2 pasos alineados o sin solape ⇒ `NO_EVALUABLE`, jamás 0,15 ni PF 5,0 fabricados), `ensamblado.py` (asignación ESTÁTICA D9: HRP y mínima varianza del examen sobre matrices reales; `router` NO se construye), y `tests/test_meta_nacimiento.py` que lo demuestra con series REALES del repo (ledgers/curvas de tests existentes o del baseline F02), incluido el caso corto ⇒ `NO_EVALUABLE`. Los módulos viejos NO se borran: quedan como están (la migración de llamadores es otra tarea).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/meta/ (nuevo: `__init__.py`, `estados.py`, `correlacion.py`, `ensamblado.py`)
- tests/test_meta_nacimiento.py (nuevo)
- orchestration/results/agy/B08.md (nuevo) · orchestration/agy/DONE_B08.md (nuevo)
- SOLO LECTURA: services/portfolio/** (meta_ensemble_service.py, meta_strategy_pipeline.py, meta_strategy_engine.py, portfolio_router.py, autonomous_meta_daemon.py), cuarentena/fabricadores_meta_20260901/ (lo que NO hay que repetir).

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/I3_diseno_meta.md (diseño; §2 fabricaciones detectadas; §7 lo que nace en services/meta).
- orchestration/state/PLAN_LOCAL_FONDEO.md filas W6.0 (a-d), W6.1 y W4.5; current_phase.md decisiones D8 y D9.
- services/portfolio/meta_ensemble_service.py y meta_strategy_pipeline.py (los dos vivos: reutiliza sus lecturas de BD/estados, copia lo honesto, deja fuera lo fabricado).
- cuarentena/fabricadores_meta_20260901/MOTIVO.md (qué se fabricaba y por qué está en cuarentena).
- orchestration/results/verificacion_f02_5.18.0.json (15 celdas con métricas reales; si trae curvas/ledgers, sirven de series reales para el test; si no, usa los fixtures reales de tests/ que ya existan y cítalos).

## PASOS (numerados, cortos, en orden)
1. Comprobar `git status --porcelain` vacío; `ls services/meta` inexistente; lee las dos listas de estados y pega ambas literal en el informe.
2. `estados.py`: `CERTIFIED_STATUSES: frozenset` = la unión JUSTIFICADA (documenta en el docstring qué estado legacy se acepta y por qué; si dudas, EXCLUYE: fail-closed) + `es_certificada(status) -> bool`.
3. `correlacion.py`: `correlacion_honesta(serie_a, serie_b, min_solape=30) -> ResultadoCorrelacion(coef: float | None, n_solape: int, motivo: str)`; alinea por timestamp real, exige `n_solape >= min_solape`, sin NaN→0, sin fallbacks; `matriz_correlacion(series: dict) -> (matriz | None, motivos)`.
4. `ensamblado.py`: `pesos_min_varianza(matriz_cov, restricciones)` y `pesos_hrp(matriz_corr, ...)` con numpy (ya en el venv; verifica), retornos reproducibles (sin `random`); ambos devuelven `None` + motivo si la matriz no es definida positiva o falta dato. NADA de router.
5. Tests con series reales: (a) dos series con solape suficiente ⇒ coef en [-1,1] y n_solape correcto; (b) ≤2 pasos ⇒ `NO_EVALUABLE`; (c) HRP y mín-varianza sobre 3 series reales ⇒ pesos suman 1, sin negativos donde la restricción lo exija, reproducibles en dos pasadas; (d) `es_certificada` acepta `CERTIFIED_CURRENT`/`APPROVED_CURRENT_ENGINE` y rechaza `REJECTED_*`, `LEGACY_*`, `BLOCKED_NO_EVIDENCE`.
6. Informe + DONE + cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_meta_nacimiento.py -q -p no:cacheprovider               # esperado: >= 6 passed
"$PY" -c "from services.meta.correlacion import correlacion_honesta as c; r=c([(1,0.1),(2,0.2)],[(1,0.1),(2,0.3)]); print(r.coef, r.motivo)"   # esperado: None NO_EVALUABLE...
"$PY" -c "import ast; src=open('services/meta/ensamblado.py',encoding='utf-8').read(); t=ast.parse(src); print('random' in src, any(isinstance(n,ast.Import) and any(a.name=='random' for a in n.names) for n in ast.walk(t)))"   # esperado: False False
"$PY" -c "import services.api.app.main" && echo API_IMPORTA                        # esperado: API_IMPORTA (nada roto)
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO.
- D9: sin router dinámico hasta que Emilio conteste la pregunta 5.2. D8: nada de `portfolio_engine`, `portfolio_combiner` ni sprint/ultra engines (están en cuarentena por fabricar datos).
- REAL-ONLY: correlación 0,15 fabricada y PF 5,0 sin perdedoras son exactamente lo prohibido; ante falta de dato, `NO_EVALUABLE`.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir fuera del TERRITORIO · tocar services/portfolio/** · mocks/random/seed · valores por defecto ante falta de dato · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B08.md. 3. orchestration/agy/DONE_B08.md.
4. Cierre: orca orchestration send --type worker_done --subject "B08 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
