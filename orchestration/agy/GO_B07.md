# GO_B07 — W3.5.b: esqueleto de `services/improvement/` (M2) en frontera limpia, con test de sustitución nº2

## Identidad
- ID: B07 · Ola: B · Rama/worktree: JOSFER78/agy-B07 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B07, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
Existe el paquete `services/improvement/` que define el contrato de entrada/salida del loop de mejora (M2) SIN implementar ningún optimizador: `contratos.py` (dataclasses `EntradaMejora` con `trials_tested_upstream` obligatorio, `IteracionMejora`, `ResultadoMejora` con estados CERTIFICADA/EN_MEJORA/AGOTADA/SIN_MEJORA), `loop.py` (bucle genérico que recibe un `Mejorador` inyectable, respeta un presupuesto de iteraciones, NUNCA lee el blind OOS dentro del bucle y suma `trials_tested_upstream + iteraciones` antes de evaluar el gate 8 con el registro), y `tests/test_improvement_frontera.py` que demuestra: near-miss con 420 configs + 3 iteraciones ⇒ el gate 8 recibe `trials_tested == 423`; el loop importa SOLO `contracts/` y `services/validation/registry` (test de sustitución nº2: cambiar el `Mejorador` = 1 clase inyectada, cero cambios en el loop).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/improvement/ (nuevo: `__init__.py`, `contratos.py`, `loop.py`)
- tests/test_improvement_frontera.py (nuevo)
- orchestration/results/agy/B07.md (nuevo) · orchestration/agy/DONE_B07.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/I2_diseno_mejora.md (diseño de M2; §2.1 el contrato de entrada exige `trials_tested_upstream`).
- orchestration/state/PLAN_LOCAL_FONDEO.md fila W3.5.b (qué es reutilizable y qué no: `expert_refinement_loop.py` NO; Optuna real en factory si existe).
- orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md §M2 (la máquina de estados del loop).
- services/validation/registry/ (`Evidencia`, `GATE_REGISTRY`, `RegistryPipeline`) y services/validation/registry/gates/gate_08.py (cómo recibe `trials_tested`).
- contracts/canonical_strategy.py (identidad/hash de la estrategia).

## PASOS (numerados, cortos, en orden)
1. Comprobar `git status --porcelain` vacío y `ls services/improvement` inexistente. Lee gate_08 y localiza el parámetro exacto de trials.
2. `contratos.py`: dataclasses frozen; `EntradaMejora(strategy_hash, snapshot, trials_tested_upstream: int, presupuesto_iteraciones: int, holdout_blind: Any)` con validación: `trials_tested_upstream <= 0` ⇒ `ValueError` (REAL-ONLY: sin multiplicidad declarada no hay mejora).
3. `loop.py`: `class Mejorador(Protocol)` con `proponer(iteracion, historial) -> snapshot`; `ejecutar_loop(entrada, mejorador, evaluar_is_val, evaluar_registro) -> ResultadoMejora`: por iteración evalúa SOLO IS/VAL (callable inyectado), nunca `holdout_blind`; al final (o al certificar) llama `evaluar_registro(evidencia, trials_tested=entrada.trials_tested_upstream + n_iteraciones)`; sin defaults que fabriquen métricas.
4. Test: `Mejorador` de prueba que devuelve el mismo snapshot; `evaluar_is_val` y `evaluar_registro` son callables reales del test que registran los argumentos (no mocks de librería: funciones del test); afirmar 423; afirmar que `holdout_blind` no fue tocado (objeto centinela cuyo acceso levanta excepción); afirmar que `services/improvement/loop.py` no importa nada de `services/api`, `services/optimization`, `services/factory` (inspección AST).
5. Informe + DONE + cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_improvement_frontera.py -q -p no:cacheprovider          # esperado: >= 4 passed
"$PY" -c "import ast; t=ast.parse(open('services/improvement/loop.py',encoding='utf-8').read()); m=sorted({(n.module or '') for n in ast.walk(t) if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(t) if isinstance(n,ast.Import) for a in n.names}); print(m); import sys; sys.exit(1 if any(x.startswith(('services.api','services.optimization','services.factory')) for x in m) else 0)"   # esperado: rc=0
"$PY" -c "from services.improvement.contratos import EntradaMejora; import pytest" && echo IMPORTA_OK   # esperado: IMPORTA_OK
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO.
- Frontera limpia: `services/improvement` solo importa `contracts/` y `services/validation/registry`. Nada del monolito `services/api`.
- No implementes ningún optimizador (Optuna, bayesiano, SQX): eso lo decide I2 con el benchmark; aquí solo el contrato y el loop.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir fuera del TERRITORIO · tocar services/validation/engine, engine_version.py o el registro · mocks de librería · datos sintéticos · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B07.md. 3. orchestration/agy/DONE_B07.md.
4. Cierre: orca orchestration send --type worker_done --subject "B07 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
