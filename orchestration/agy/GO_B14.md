# GO_B14 — Arnés de aceptación v2 (D16): 0 commits sobre la base y GO íntegro

## Identidad
- ID: B14 · Ola: B · Rama/worktree: JOSFER78/agy-B14 · Timebox: 30 min
- Variables ya puestas: AGY_AGENT=B14, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
`scripts/aceptar_agy.py` rechaza además (1) cualquier commit del agente sobre la base (`git -C WT log --oneline <base>..HEAD` no vacío, con `base` = `git merge-base HEAD <rama del ORQ>` o la opción `--base <ref>`; motivo `commits_del_agente`) y (2) cualquier alteración del contrato por el agente: las secciones `## TERRITORIO`, `## ACEPTACIÓN` y `## RIESGO` del GO en el worktree deben ser idénticas a las del GO en `HEAD` (`git show HEAD:orchestration/agy/GO_<ID>.md`); solo se toleran secciones `## CORRECCION_n` añadidas al final (motivo `go_alterado`); con tests reales (repo git temporal) para ambos casos.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/aceptar_agy.py
- tests/test_aceptar_agy.py
- orchestration/results/agy/B14.md (nuevo) · orchestration/agy/DONE_B14.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- scripts/aceptar_agy.py (tal cual está: parser `leer_go`, `obtener_ficheros_tocados`, `main`).
- orchestration/results/agy/A02.md §1 filas c, d, j y k5, y §3 (los agujeros que cierras).
- tests/test_aceptar_agy.py (fixture del repo temporal; añade casos, no rompas los 8 existentes).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; `"$PY" -m pytest tests/test_aceptar_agy.py -q -p no:cacheprovider` ⇒ 8 passed (baseline).
2. Base: nueva opción `--base <ref>` (por defecto: `JOSFER78/orquesta-antigravity-max-10`; si no existe, `origin/main`; si tampoco, el primer padre del primer commit del worktree). `commits = git -C WT log --oneline <merge-base>..HEAD`; si no vacío ⇒ RECHAZA `commits_del_agente` con la lista en el JSON (`commits_agente`).
3. Integridad del GO: extrae de `git -C WT show HEAD:orchestration/agy/GO_<ID>.md` y del fichero en disco las secciones `## TERRITORIO`, `## ACEPTACIÓN`, `## RIESGO` (texto exacto hasta la siguiente `## `); deben coincidir; el resto del fichero solo puede diferir por texto AÑADIDO al final que empiece por `## CORRECCION_`. Si no ⇒ RECHAZA `go_alterado` con las secciones que difieren. Si el GO no existe en HEAD (worktree sin GO commiteado) ⇒ RECHAZA `go_no_versionado`.
4. Tests (repo temporal real): (i) commit hecho por el "agente" sobre la base ⇒ RECHAZA `commits_del_agente`; (j) GO con línea añadida en TERRITORIO ⇒ RECHAZA `go_alterado`; (k) GO con `## CORRECCION_1` añadida al final ⇒ ACEPTA; (l) todo limpio ⇒ ACEPTA con `commits_agente == []`. Los 8 existentes siguen en verde (el fixture ya hace un commit inicial: ese es la base; usa `--base` en los tests).
5. Informe con la salida cruda; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_aceptar_agy.py -q -p no:cacheprovider          # esperado: 12 passed
"$PY" scripts/aceptar_agy.py B14 --sin-comandos --out /tmp/acept_B14.json; echo "rc=$?"   # esperado: ACEPTA rc=0 (tu propio worktree: 0 commits, GO íntegro)
grep -c "commits_del_agente\|go_alterado" scripts/aceptar_agy.py || true    # esperado: >= 2 (rc-libre)
git diff --name-only   # ⊆ TERRITORIO; esperado: scripts/aceptar_agy.py tests/test_aceptar_agy.py
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO.
- Solo stdlib. Fail-closed: si la base no se puede resolver, RECHAZA con `base_no_resuelta`.
- No cambies el formato del JSON existente: añade claves (`commits_agente`, `go_secciones_alteradas`).

## PROHIBIDO (lista negra, sin excepciones)
git de escritura en el repo del proyecto (en el repo temporal del test sí) · rm · escribir fuera del TERRITORIO · mocks · dependencias fuera de la stdlib · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B14.md. 3. orchestration/agy/DONE_B14.md.
4. Cierre: orca orchestration send --type worker_done --subject "B14 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
