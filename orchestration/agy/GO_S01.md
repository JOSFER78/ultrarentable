# GO_S01 — Trabajo de humo del bucle completo (enviar → recibir → auditar → cerrar), cronometrado

## Identidad
- ID: S01 · Ola: S (sistema) · Rama/worktree: JOSFER78/agy-S01 · Timebox: 10 min
- Variables ya puestas: AGY_AGENT=S01, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
Existe `orchestration/results/agy/S01.md` con exactamente tres cifras medidas con comandos y su salida cruda: el número de líneas de `CLAUDE.md`, el número de ficheros `GO_*.md` en `orchestration/agy/` y el número de tests que pasan en `tests/test_engine_version.py` (o `NO DATA` con el error si ese fichero no existe), más `orchestration/agy/DONE_S01.md`; nada más se toca.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- orchestration/results/agy/S01.md (nuevo) · orchestration/agy/DONE_S01.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- CLAUDE.md · orchestration/agy/ · tests/ (solo lectura).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío.
2. `wc -l CLAUDE.md`; `ls orchestration/agy/GO_*.md | wc -l`; `"$PY" -m pytest tests/test_engine_version.py -q -p no:cacheprovider` (si no existe: `NO DATA` + error crudo).
3. Escribe el informe con los tres comandos y sus salidas literales; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
test -f orchestration/results/agy/S01.md && echo OK                                  # esperado: OK
grep -c -E "wc -l CLAUDE.md|GO_\*.md|pytest" orchestration/results/agy/S01.md || true   # esperado: >= 3
git diff --name-only   # esperado: vacío (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir fuera del TERRITORIO · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/S01.md. 3. orchestration/agy/DONE_S01.md.
4. Cierre: orca orchestration send --type worker_done --subject "S01 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
