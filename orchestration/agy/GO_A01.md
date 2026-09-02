# GO_A01 — Arnés de aceptación: `scripts/aceptar_agy.py`

## Identidad
- ID: A01 · Ola: A · Rama/worktree: JOSFER78/agy-A01 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min
- Variables ya puestas en tu terminal: AGY_AGENT=A01, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.

## OBJETIVO (una frase verificable)
Existe `scripts/aceptar_agy.py <ID> [--worktree RUTA] [--out RUTA.json] [--sin-comandos]` (solo stdlib) que lee `orchestration/agy/GO_<ID>.md` del worktree indicado, verifica territorio, regla #26, comandos de aceptación, lista negra y ficheros de cierre, escribe un veredicto JSON y sale con 0 solo si `ACEPTA`; probado con `tests/test_aceptar_agy.py` sobre repos git reales en `tmp_path`.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/aceptar_agy.py (nuevo)
- tests/test_aceptar_agy.py (nuevo)
- orchestration/results/agy/A01.md (nuevo) · orchestration/agy/DONE_A01.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/agy/PLANTILLA_GO.md y orchestration/agy/PLANTILLA_DONE.md (formato que parseas).
- orchestration/agy/GO_A04.md, GO_A05.md, GO_A06.md (GOs reales: mira cómo escriben TERRITORIO y ACEPTACIÓN; tu parser debe aceptarlos).
- orchestration/state/PLAN_ORCA_ANTIGRAVITY.md §2, ataduras 5, 6 y 8 (lo que este script impone por máquina).

## PASOS (numerados, cortos, en orden)
1. Comprobar punto de partida: `git status --porcelain` vacío; `ls scripts/aceptar_agy.py` no existe.
2. Parser del GO (`leer_go(ruta) -> dict`):
   - TERRITORIO: bajo la línea que empieza por `## TERRITORIO`, cada línea que empieza por `- `; quitar backticks; quedarse con el primer token antes de ` (`; una entrada que termina en `/` es un PREFIJO de directorio; entradas con "SOLO LECTURA" o "TEMPORALES" se ignoran (no son territorio de escritura).
   - ACEPTACIÓN: el primer bloque cercado ```bash bajo `## ACEPTACIÓN`, texto íntegro.
   - MOTOR: `toca_motor = "Toca semántica del motor: SÍ" in texto` (literal, con acento y mayúsculas).
   - Tolerados siempre (dentro de territorio implícito): `orchestration/agy/GO_<ID>.md`, `orchestration/agy/DONE_<ID>.md`, `orchestration/results/agy/<ID>.md`, `orchestration/results/agy/` (prefijo).
3. Ficheros tocados en el worktree: `git -C WT diff --name-only` ∪ `git -C WT diff --name-only --cached` ∪ `git -C WT ls-files --others --exclude-standard`. Fuera de territorio ⇒ `fuera_de_territorio` no vacío ⇒ RECHAZA (no se ejecuta nada más, pero sí se escribe el JSON).
4. Regla #26: si algún fichero tocado empieza por `services/validation/engine/` o es `services/engine_version.py` y `not toca_motor` ⇒ RECHAZA con motivo `regla_26`.
5. Comandos de aceptación (salvo `--sin-comandos`): transformar el bloque en UN script bash: por cada línea no vacía que no empiece por `#`, emitir `echo "### CMD: <línea>"; <línea>; echo "### RC: $?"`; ejecutar `bash -lc <script>` con `cwd=WT`, env `PYTHONPATH=WT` y `AGY_AGENT=<ID>`, timeout 900 s; parsear pares CMD/RC. Cualquier RC≠0 ⇒ RECHAZA (motivo `aceptacion_rc`), salvo líneas que terminen en `# rc-libre`. Guardar por comando `stdout_tail`/`stderr_tail` (últimas 20 líneas).
6. Lista negra sobre `git -C WT diff -U0` más el contenido de los ficheros nuevos dentro de territorio: `git commit`, `git push`, `rm -rf`, `shutil.rmtree` ⇒ RECHAZA (motivo `lista_negra`); `mock`, `MagicMock`, `random`, `synthetic`, `sintetic`, `default=` ⇒ AVISO (se listan con fichero:línea; no rechazan). Excluir de los greps los propios ficheros `orchestration/results/agy/*.md` y `orchestration/agy/*.md` (informes que citan comandos).
7. Cierre: deben existir `orchestration/agy/DONE_<ID>.md` y `orchestration/results/agy/<ID>.md` en WT; si falta alguno ⇒ RECHAZA (motivo `sin_done` / `sin_informe`).
8. Veredicto JSON en `--out` (por defecto `orchestration/results/agy/aceptacion_<ID>.json` del cwd, NO del worktree del agente): `{id, worktree, veredicto: "ACEPTA"|"RECHAZA", motivos: [...], ficheros_tocados: [...], fuera_de_territorio: [...], toca_motor: bool, comandos: [{cmd, rc, stdout_tail, stderr_tail}], avisos: [...], generado_utc}`. Imprimir resumen legible. `exit 0` solo con ACEPTA.
9. `tests/test_aceptar_agy.py` (pytest, `tmp_path`, `subprocess` a `git` real; sin mocks): fixture que hace `git init`, configura user.name/email, crea `src/a.txt`, `README.md`, `orchestration/agy/GO_T1.md` (territorio `src/`; aceptación con `test -f src/a.txt` y `grep -q hola src/a.txt`), commit inicial (aquí SÍ, es un repo temporal ajeno al proyecto: usa `git -c core.hooksPath=/dev/null commit`), y luego modifica `src/a.txt` con "hola" y crea `DONE_T1.md` + `orchestration/results/agy/T1.md`. Casos: (a) todo dentro ⇒ `ACEPTA`, exit 0; (b) además `README.md` modificado ⇒ `RECHAZA`, `fuera_de_territorio == ["README.md"]`; (c) fichero `services/validation/engine/x.py` nuevo sin la cadena de motor ⇒ `RECHAZA` con motivo `regla_26`; (d) aceptación con un comando que falla (`false`) ⇒ `RECHAZA` con `aceptacion_rc`; (e) sin DONE ⇒ `RECHAZA` con `sin_done`. Cada caso lee el JSON de `--out` en `tmp_path`.
10. Ejecutar ACEPTACIÓN; pegar salida cruda en `orchestration/results/agy/A01.md`; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_aceptar_agy.py -q -p no:cacheprovider          # esperado: 5 passed
"$PY" scripts/aceptar_agy.py A01 --sin-comandos --out /tmp/acept_A01.json; echo "rc=$?"   # esperado: veredicto ACEPTA, rc=0 (self-check de territorio y cierre)
"$PY" -c "import json; j=json.load(open('/tmp/acept_A01.json')); print(j['veredicto'], sorted(j['ficheros_tocados']))"
# esperado: ACEPTA ['orchestration/agy/DONE_A01.md', 'orchestration/results/agy/A01.md', 'scripts/aceptar_agy.py', 'tests/test_aceptar_agy.py']
"$PY" -c "import ast,sys; src=open('scripts/aceptar_agy.py',encoding='utf-8').read(); t=ast.parse(src); mods={n.names[0].name.split('.')[0] for n in ast.walk(t) if isinstance(n,ast.Import)}|{n.module.split('.')[0] for n in ast.walk(t) if isinstance(n,ast.ImportFrom) and n.module}; print(sorted(mods))"
# esperado: solo módulos de la stdlib (argparse, datetime, json, os, pathlib, re, subprocess, sys...)
git diff --name-only   # ⊆ TERRITORIO (más GO_A01.md si el ORQ añadió CORRECCION_n)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor (services/validation/engine/ o services/engine_version.py)? NO
- ¿Ejecuta algo pesado? NO (tests de un fichero, ~5 s). Nada de pytest completo.
- El script es el arnés de todos los demás agentes: fail-closed en todo (cualquier duda ⇒ RECHAZA con motivo). Nunca un veredicto ACEPTA por defecto, nunca tragar excepciones: una excepción se convierte en RECHAZA con `motivos=["error_interno: ..."]` y exit 2.
- Rutas: normalizar a `/` y relativas a la raíz del worktree antes de comparar con el territorio.
- Este GO NO se auto-ejecuta con comandos (recursión): por eso el self-check usa `--sin-comandos`.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash en el repo del proyecto (en el repo temporal del test sí, y solo ahí) · rm (se aparca en cuarentena/ con MANIFEST SHA-256) · datos sintéticos, mocks, random/seed, valores por defecto ante falta de dato (se escribe NO DATA) · relajar umbrales · escribir fuera del TERRITORIO · tocar services/engine_version.py · procesos largos sin admisión · inventar una salida que no se ejecutó · declarar subagentes que tu CLI no tiene · dependencias fuera de la stdlib.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A01.md: comandos ejecutados y salida CRUDA pegada literal; lo que no se pudo; hallazgos; veredicto propio.
3. orchestration/agy/DONE_A01.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A01 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json

## CORRECCION_1 (ORQ, 2026-09-02 11:40) — dos defectos encontrados al auditar con casos reales; REPITE

Tu script pasó su propio test, pero al ejecutarlo contra el worktree real de A04 (`scripts/aceptar_agy.py A04 --worktree ../agy-A04`) rechazó en falso: los 11 comandos de aceptación salieron `rc=-1 "No ejecutado"` aunque todos pasan. Causa, en `ejecutar_comandos_aceptacion`: el marcador `echo "### CMD: {cmd}"` NO escapa las comillas del comando, así que bash imprime `PY=C:/...` donde el GO decía `PY="C:/..."`, el texto no coincide con `cmd_lines` y el parser lo da por no ejecutado.

1. **Marcadores por índice, no por texto.** Emite `echo "### CMD 3"` (número de línea del comando) y `echo "### RC 3: $?"`, y asocia por índice con `cmd_lines[i]`. El texto del comando se guarda desde `cmd_lines`, nunca desde la salida del shell. Así ninguna comilla, `$`, `|` o `#` del comando puede romper el emparejamiento.
2. **Ficheros en rutas IGNORADAS bajo `data/`**: hoy `git ls-files --others --exclude-standard` no ve un fichero nuevo en `data/normalized/` (probado: escribí `data/normalized/ds_prueba_orq.json` en A04 y el veredicto fue ACEPTA con 0 ficheros). Añade `git ls-files --others --ignored --exclude-standard -- data/` y vuelca el resultado (máximo 50 rutas) en `avisos` como `ignorado_en_data: <ruta>`. NO es rechazo automático (en algunos worktrees `data/normalized` es un enlace a datos reales), pero el ORQ tiene que verlo.
3. Añade a `tests/test_aceptar_agy.py`: (f) aceptación con un comando que contiene comillas dobles y `$VAR` (p. ej. `PY="$(command -v git)"` seguido de `"$PY" --version`) ⇒ ACEPTA y los dos comandos con `rc=0` y su `cmd` igual al texto original del GO; (g) fichero nuevo en una ruta ignorada por un `.gitignore` del repo temporal bajo `data/` ⇒ ACEPTA pero `avisos` contiene `ignorado_en_data: data/x.json`.
4. Repite la ACEPTACIÓN del GO (ahora `7 passed`) y añade a tu informe la salida de `"$PY" scripts/aceptar_agy.py A04 --worktree ../agy-A04 --out ../agy-A01/orchestration/results/agy/aceptacion_A04_prueba.json` ⇒ `ACEPTA`, 11 comandos con rc=0 (A04 ya está integrado y su árbol limpio: 0 ficheros tocados es lo esperado).
Cierra con un nuevo `worker_done` (subject `A01 CORRECCION_1 <PASA|FALLA>`).
