# GO_A07 — Refutador de A06 (registro de gates v1 vs suite B)

## Identidad
- ID: A07 · Ola: A (se despacha cuando A06 aterriza e integrado en tu base) · Rama/worktree: JOSFER78/agy-A07 · Timebox: 45 min
- Variables ya puestas en tu terminal: AGY_AGENT=A07, PYTHONPATH=<raíz de tu worktree>, A06_DATASET_FILE=<dataset real ES 15m, solo lectura>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.

## OBJETIVO (una frase verificable)
Demostrar, o descartar con evidencia, que existe algún gate cuyo resultado difiere entre `services/validation/registry/` (A06) y la suite B `services/api/app/validation/gates/` sobre las mismas entradas: informe con 0 divergencias o la lista exacta gate → valor B → valor registro → entrada que lo provoca.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- orchestration/results/agy/A07.md (nuevo) · orchestration/agy/DONE_A07.md (nuevo)
- Scripts efímeros SOLO en `orchestration/results/agy/A07_*.py` (se citan en el informe; no se borran).

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/agy/GO_A06.md y orchestration/results/agy/A06.md (qué afirma A06 y con qué cifras).
- services/validation/registry/ (todo) y services/api/app/validation/gates/ (todo). NO leas primero las conclusiones de A06: primero mide, luego compara.
- orchestration/results/W43_spec_registro_gates.md §1 (tabla de umbrales de B).
- tests/test_gates_multitier_and_incubator.py (fixture TIER_2 real) y tests/test_gates_modular_quad_state.py (patrón con dataset real).

## PASOS (numerados, cortos, en orden)
1. Umbral a umbral: para cada gate 01..11 extrae con `grep -n` los literales numéricos de B y el dict `UMBRALES` del registro; tabla con las 11 filas y cualquier diferencia (valor, o umbral presente en B y ausente en el registro, o al revés).
2. Ejecución cruzada: script `orchestration/results/agy/A07_cruce.py` que construye TRES evidencias (fixture TIER_2 copiada de `test_gates_multitier_and_incubator.py`; evidencia vacía `route=FONDEO`; evidencia con el dataset real `A06_DATASET_FILE` siguiendo `test_gates_modular_quad_state.py`), pasa cada una por `GatePipelineOrchestrator.run_all_gates` (B) y por `RegistryPipeline().veredicto` (registro) y hace `diff` campo a campo de los 11 dicts (`passed`, `score`, `verdict`, `evidence`), más `gates_passed_count`, `tier`, `overall_score`. Imprime cada diferencia con gate, campo, valor B, valor registro.
3. Determinismo: ejecuta el cruce DOS veces; si algún gate cambia entre pasadas (p. ej. Monte Carlo sin semilla fija), es divergencia interna y se reporta aparte.
4. Búsqueda de rellenos: `grep -n "default\|or 1.5\|or 1.0\|except" services/validation/registry/gates/*.py` y lo mismo en B; cualquier default que fabrique un valor cuando falta evidencia se lista (aunque sea idéntico en B: eso es hallazgo, no divergencia).
5. Informe `orchestration/results/agy/A07.md`: §1 tabla de umbrales, §2 salida CRUDA del cruce (las dos pasadas), §3 divergencias (0 o lista exacta), §4 rellenos, §5 veredicto: `A06 CONFIRMADO` o `A06 REPITE` con la lista.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" orchestration/results/agy/A07_cruce.py; echo "rc=$?"     # esperado: imprime DIVERGENCIAS=<n>; rc=0 si n=0, rc=1 si n>0
grep -c "^| gate_" orchestration/results/agy/A07.md           # esperado: 11 (tabla de umbrales completa)
grep -cE "DIVERGENCIAS=[0-9]+" orchestration/results/agy/A07.md   # esperado: >= 2 (dos pasadas pegadas)
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío (solo ficheros nuevos en orchestration/results/agy/)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO · ¿Ejecuta algo pesado? NO (el fixture tarda ~4 s por pasada; el dataset real, decenas de segundos: permitido una vez por pasada).
- No modificas código de producción ni tests: si encuentras el fallo, lo describes; lo arregla A06 en su REPITE.
- Sin dataset real (`A06_DATASET_FILE` ausente) ⇒ esa evidencia queda `NO DATA` en el informe; las otras dos se ejecutan igual.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm · datos sintéticos, mocks, random/seed (los trades y velas vienen de los fixtures reales del repo o del dataset real) · escribir fuera del TERRITORIO · tocar services/ · inventar una salida que no se ejecutó · declarar subagentes.

## SALIDA
1. Working tree limpio salvo ficheros nuevos en `orchestration/results/agy/` y `orchestration/agy/DONE_A07.md`.
2. orchestration/results/agy/A07.md con salida cruda y veredicto.
3. orchestration/agy/DONE_A07.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A07 <CONFIRMADO|REPITE|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
