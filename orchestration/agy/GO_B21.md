# GO_B21 — `scripts/aceptar_agy.py` v3: territorio con varias rutas por línea y comodines, bloque de aceptación robusto, informe de auditoría en disco

## Identidad
- ID: B21 · Ola: S (sistema) · Rama/worktree: JOSFER78/agy-B21 · Timebox: 30 min
- Variables ya puestas: AGY_AGENT=B21, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
El arnés de aceptación del orquestador deja de dar falsos rechazos y de romperse con comandos con paréntesis o comillas: (1) `## TERRITORIO` acepta varias rutas en una misma línea separadas por ` · ` y paréntesis aclaratorios (`scripts/orq/ (nuevo) · tests/x.py (nuevo)` ⇒ dos rutas), y comodines `<fecha>`, `<YYYYMMDD>`, `<ID>`, `*` que casan con `[A-Za-z0-9_.-]+` (hoy `cuarentena/web_prop_firms_ts_<fecha>/` rechazó a B10 y `deploy/vigia/ (nuevo)` marcó FUERA a B12 y B15); (2) el bloque `## ACEPTACIÓN` se ejecuta línea a línea con `bash -lc` pasando cada comando como argumento (nunca reconstruido con `echo`), de modo que `grep -cE "a|b(6|8)"` o `awk '{print ($1<=700)?"OK":"NO"}'` funcionan; cada comando queda en el JSON con `cmd`, `rc`, `stdout` (≤ 2.000 caracteres) y `stderr`; (3) `--informe` escribe `orchestration/results/auditorias/<ID>_<fecha-hora>.md` con veredicto, motivos, ficheros tocados, territorio, comandos y salidas; (4) veredicto ACEPTA/RECHAZA inalterado en el resto (D16: commits del agente, GO alterado).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/aceptar_agy.py · tests/test_aceptar_agy.py (añadir casos; los 12 existentes siguen en verde)
- orchestration/results/auditorias/ (nuevo; solo el informe de prueba)
- orchestration/results/agy/B21.md (nuevo) · orchestration/agy/DONE_B21.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- scripts/aceptar_agy.py (v2 de B14: `leer_go`, `obtener_ficheros_tocados`, `main`, `--base`, `--sin-comandos`, `--out`) y tests/test_aceptar_agy.py (fixture de repo git temporal real).
- Casos reales que fallaron hoy (reprodúcelos como tests): GO_B10 (territorio `cuarentena/web_prop_firms_ts_<fecha>/`, ficheros `cuarentena/web_prop_firms_ts_20260902/MANIFEST.sha256` ⇒ debía ACEPTAR), GO_B15 (línea `scripts/orq/ (nuevo) · tests/test_orq_agentes.py (nuevo) · orchestration/OPERACION_AGENTES.md (nuevo)` ⇒ tres rutas), GO_B17 (comando de aceptación con `(6|8|10)` y comillas escapadas).
- Los GO reales están en orchestration/agy/GO_B10.md, GO_B15.md, GO_B17.md (solo lectura).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; `"$PY" -m pytest tests/test_aceptar_agy.py -q -p no:cacheprovider` ⇒ 12 passed (baseline).
2. Parser de TERRITORIO (separador ` · `, paréntesis, comodines → regex; prefijo con `/` cubre subárbol). Ejecutor de ACEPTACIÓN con `subprocess.run(["bash","-lc",cmd], cwd=WT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)`. `--informe`.
3. Tests (repo temporal real): (m) territorio con ` · ` y paréntesis ⇒ 3 rutas; (n) comodín `<fecha>` acepta `..._20260902/x`; (o) comando con paréntesis y comillas se ejecuta y su rc se registra; (p) `--informe` crea el .md con las secciones. Los 12 previos en verde.
4. Ejecuta el arnés real sobre tu propio worktree con `--informe` y pega el informe. DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_aceptar_agy.py -q -p no:cacheprovider                       # esperado: >= 16 passed
"$PY" scripts/aceptar_agy.py B21 --sin-comandos --informe --out /tmp/acept_B21.json; echo "rc=$?"   # esperado: ACEPTA rc=0
ls orchestration/results/auditorias/B21_*.md | head -1                                   # existe
grep -c -E "bash\", *\"-lc\"|<fecha>|YYYYMMDD" scripts/aceptar_agy.py || true          # esperado: >= 2
git diff --name-only   # ⊆ TERRITORIO; esperado: scripts/aceptar_agy.py tests/test_aceptar_agy.py
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO. Solo stdlib. Fail-closed: un comando de aceptación que no se pueda ejecutar cuenta como rc=1.
- No cambies el formato JSON existente: añade claves.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura en el repo del proyecto · rm · dependencias fuera de la stdlib · mocks · escribir fuera del TERRITORIO · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B21.md. 3. orchestration/agy/DONE_B21.md.
4. Cierre: orca orchestration send --type worker_done --subject "B21 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
