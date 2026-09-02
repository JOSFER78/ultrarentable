# GO_B16 — Sitio local de seguimiento (plan · estado · tareas · agentes · ventana) en una página simple

## Identidad
- ID: B16 · Ola: B · Rama/worktree: JOSFER78/agy-B16 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B16, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
`scripts/orq/sitio_seguimiento.py` genera `orchestration/site/index.html`: UNA página estática y sobria al estilo de la interfaz de Orca / Claude Code (fuente del sistema, negro sobre blanco, bordes grises, tablas; SIN colores, SIN paneles, SIN gráficos, SIN JavaScript, SIN CSS externo, SIN emojis ni iconos, nada que parezca "hecho con IA") con cinco secciones en este orden: **Plan** (la tabla de fases de `orchestration/state/plan_maestro.md`), **Estado** (la sección `## 3 bis` de `orchestration/state/current_phase.md` con su tabla de aterrizajes y el párrafo "En vuelo"), **Tareas** (`gh issue list --state all --limit 100 --json number,title,state,labels,updatedAt`: número, título, estado, etiquetas, fecha; agrupadas en Abiertas / Cerradas), **Agentes** (si existe `scripts/orq/agy_censo.ps1`, su salida `-Json` en tabla; si no, `NO DATA (agy_censo.ps1 no disponible)`), **Ventana de Emilio** (`orchestration/state/VENTANA_EMILIO.md` completo); cabecera con "Generado: <fecha-hora local>" y `<meta http-equiv="refresh" content="60">`. Y `scripts/orq/sitio_servir.ps1` que regenera cada 60 s y sirve la carpeta en `http://localhost:8765` con `python -m http.server` (proceso ligero, sin frameworks).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/orq/sitio_seguimiento.py (nuevo) · scripts/orq/sitio_servir.ps1 (nuevo) · orchestration/site/ (nuevo; index.html generado)
- tests/test_sitio_seguimiento.py (nuevo)
- orchestration/results/agy/B16.md (nuevo) · orchestration/agy/DONE_B16.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/state/plan_maestro.md (tabla de fases), orchestration/state/current_phase.md (sección `## 3 bis` y "En vuelo"), orchestration/state/VENTANA_EMILIO.md.
- `gh issue list --state all --limit 100 --json number,title,state,labels,updatedAt` (ejecútalo y pega las 3 primeras líneas crudas).
- docs/19_UI_STYLE_SPEC.md solo para lo que prohíbe (colores); la referencia visual aquí es la propia terminal de Orca / Claude Code: monocromo, denso, legible.

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee las ENTRADAS.
2. `sitio_seguimiento.py` (stdlib: `argparse, subprocess, re, html, json, datetime, pathlib`): conversor mínimo Markdown→HTML propio (títulos, tablas con `|`, listas, negrita, `código`, párrafos; NADA más), extracción por encabezado (`## 3 bis` hasta el siguiente `## `), llamada a `gh` con timeout 20 s y `NO DATA (gh: <error>)` si falla, escape HTML de todo, `--out` (por defecto `orchestration/site/index.html`) y `--sin-gh` para tests. CSS embebido de ≤ 40 líneas: `font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color:#111; background:#fff; max-width:1100px; border:1px solid #ddd` y grises; PROHIBIDO cualquier otro color.
3. `sitio_servir.ps1 [-Puerto 8765] [-Intervalo 60] [-Parar]`: arranca UNA vez `python -m http.server <puerto>` sobre `orchestration/site/` en segundo plano (`Start-Process`, PID guardado en `orchestration/site/servidor.pid`) y en bucle regenera el HTML cada `-Intervalo` segundos; `-Parar` mata ese PID y sale.
4. Tests reales en `tests/test_sitio_seguimiento.py`: genera con `--sin-gh --out <tmp>` desde los ficheros reales del repo ⇒ el fichero existe, contiene `<h2>Plan`, `<h2>Estado`, `<h2>Tareas`, `<h2>Agentes`, `<h2>Ventana`, contiene `Generado:`, NO contiene `<script`, y ningún color hex fuera de la lista de grises permitida (`#fff #ffffff #111 #000 #333 #555 #777 #999 #ccc #ddd #eee #f5f5f5 #fafafa`).
5. Genera el index.html real (con gh) y pega en el informe sus primeras 30 líneas; arranca `sitio_servir.ps1`, comprueba `curl -s http://localhost:8765/ | head -5`, y PÁRALO (`-Parar`) antes de cerrar (el ORQ lo arranca en producción). DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_sitio_seguimiento.py -q -p no:cacheprovider                   # esperado: >= 3 passed
"$PY" scripts/orq/sitio_seguimiento.py --out /tmp/site_B16.html; echo "rc=$?"; grep -c "<h2" /tmp/site_B16.html   # esperado: rc=0; 5
grep -c "<script" /tmp/site_B16.html || true                                             # esperado: 0 (rc-libre)
grep -oE "#[0-9a-fA-F]{3,6}\b" /tmp/site_B16.html | sort -u | grep -vE "^#(fff|ffffff|111|000|333|555|777|999|ccc|ddd|eee|f5f5f5|fafafa)$" | wc -l   # esperado: 0
grep -c "http.server" scripts/orq/sitio_servir.ps1                                        # esperado: >= 1
git diff --name-only   # ⊆ TERRITORIO; esperado: vacio (solo ficheros nuevos)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO (http.server es trivial).
- La página NO inventa estado: todo sale de los ficheros y de `gh`; donde falte, `NO DATA` con motivo.
- Sin frameworks, sin npm, sin CDN, sin JavaScript, sin emojis, sin iconos, sin colores.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · `npm`/CDN/JS · colores fuera de la lista de grises · escribir fuera del TERRITORIO · dejar el servidor arrancado al cerrar · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B16.md. 3. orchestration/agy/DONE_B16.md.
4. Cierre: orca orchestration send --type worker_done --subject "B16 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
