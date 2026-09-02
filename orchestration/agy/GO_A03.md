# GO_A03 — W0.8: portar la puerta de admisión (`gobernanza_recursos`) a Windows

## Identidad
- ID: A03 · Ola: A · Rama/worktree: JOSFER78/agy-A03 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min
- Variables ya puestas en tu terminal: AGY_AGENT=A03, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.

## OBJETIVO (una frase verificable)
`python -m services.ops.gobernanza_recursos estado` y `... ejecutar --nombre X -- <cmd>` funcionan en Windows nativo con la MISMA semántica que hoy en Linux (turno único con candado de fichero; admisión que rechaza arrancar con la máquina saturada; mismos umbrales y subcomandos), solo con la stdlib, sin romper Linux; probado con `tests/test_gobernanza_recursos_windows.py` (candado real entre dos procesos).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/ops/gobernanza_recursos.py (existe, 274 líneas)
- tests/test_gobernanza_recursos_windows.py (nuevo)
- orchestration/results/agy/A03.md (nuevo) · orchestration/agy/DONE_A03.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- services/ops/gobernanza_recursos.py ENTERO: hoy `import fcntl` (línea ~33) revienta en Windows con `ModuleNotFoundError`; localiza el candado (`flock`), la lectura de recursos (`/proc`, `os.getloadavg`, `free`…), los umbrales y el `argparse` (línea 239 en adelante; subcomandos y flags EXACTOS: no cambies ninguno).
- orchestration/OPERACION_VPS.md (cómo se usa la puerta; solo lectura).
- orchestration/state/PLAN_LOCAL_FONDEO.md fila W0.8 (el mandato).
- HECHO MEDIDO: ni `psutil` ni `portalocker` están instalados en el venv, y NO puedes instalar nada (venv compartido). Solo stdlib.

## PASOS (numerados, cortos, en orden)
1. Comprobar: `"$PY" -m services.ops.gobernanza_recursos estado; echo rc=$?` → hoy `ModuleNotFoundError: fcntl`, rc≠0 (pegar). `git status --porcelain` vacío.
2. Candado portable, en el mismo módulo: `if os.name == "nt": import msvcrt` / `else: import fcntl`. Funciones `_bloquear(fh)` y `_liberar(fh)`: en POSIX `fcntl.flock(fh, LOCK_EX | LOCK_NB)`; en Windows `msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)` sobre el primer byte (el fichero debe tener ≥1 byte: escribe `b"\0"` si está vacío) y `LK_UNLCK` al liberar. El error de "ocupado" se traduce al MISMO mensaje/exit que hoy en Linux (léelo en el código y consérvalo).
3. Recursos portables: en Windows, CPU % = `powershell -NoProfile -Command "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average"` (subprocess, timeout 10 s, cache 5 s); RAM total/libre = `ctypes` `GlobalMemoryStatusEx` (kernel32); load average = `None` (Windows no lo tiene) y la admisión usa CPU % y RAM % con los MISMOS umbrales numéricos que hoy (si hoy la admisión decide por load average, mapea a CPU % = load/núcleos×100 y documéntalo en el informe; no inventes umbrales nuevos). En POSIX, código intacto.
4. Lo que no se pueda medir en Windows se devuelve como `None` y se imprime como `NO DATA`, nunca 0.
5. `estado` imprime lo mismo que hoy más las claves nuevas si las hay; `ejecutar --nombre X -- cmd` corre el comando con el candado cogido y lo libera al terminar (también si el comando falla). Comprueba que el `--` con un comando `python -c "print(1)"` funciona en Windows (comillas).
6. Test `tests/test_gobernanza_recursos_windows.py` (sin mocks; se salta con `pytest.skip("solo Windows")` si `os.name != "nt"`): (a) `estado` devuelve/imprime cpu_pct numérico 0-100 y ram_pct numérico; (b) candado real: proceso A = `subprocess.Popen([PY, "-m", "services.ops.gobernanza_recursos", "ejecutar", "--nombre", "t_a03", "--", PY, "-c", "import time; time.sleep(6)"], env con candado en tmp_path si el módulo permite ruta por env/flag; si no, añade el flag `--lock-dir` o la variable `GOBERNANZA_LOCK_DIR` y documéntalo)`; tras 1 s, proceso B con el mismo nombre ⇒ termina con rc≠0 y el mensaje de "ocupado"; al acabar A, B vuelve a lanzarse y pasa; (c) `ejecutar` con un comando que falla ⇒ rc del comando propagado y candado liberado (un tercer `ejecutar` pasa).
7. Ejecutar ACEPTACIÓN; pegar salidas crudas en `orchestration/results/agy/A03.md`; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m services.ops.gobernanza_recursos estado; echo "rc=$?"       # esperado: cifras reales de CPU y RAM (no NO DATA en esas dos), rc=0
"$PY" -m services.ops.gobernanza_recursos ejecutar --nombre prueba_a03 -- "$PY" -c "print('DENTRO_DEL_CANDADO')"; echo "rc=$?"   # esperado: DENTRO_DEL_CANDADO, rc=0
"$PY" -m pytest tests/test_gobernanza_recursos_windows.py -q -p no:cacheprovider   # esperado: 3 passed
"$PY" -c "import ast; t=ast.parse(open('services/ops/gobernanza_recursos.py',encoding='utf-8').read()); print(sorted({(n.names[0].name if isinstance(n,ast.Import) else n.module) for n in ast.walk(t) if isinstance(n,(ast.Import,ast.ImportFrom))}))"
# esperado: solo stdlib (msvcrt y fcntl bajo condición; nada de psutil/portalocker)
grep -n "argparse\|add_parser\|add_argument" services/ops/gobernanza_recursos.py | wc -l   # esperado: >= el valor de HEAD (no se quitan flags): compara con `git show HEAD:services/ops/gobernanza_recursos.py | grep -c "add_argument"`
git diff --name-only   # ⊆ TERRITORIO (más GO_A03.md si el ORQ añadió CORRECCION_n)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor (services/validation/engine/ o services/engine_version.py)? NO
- ¿Ejecuta algo pesado? NO (el test duerme 6 s; nada más).
- Umbrales de admisión: NO se cambian. Subcomandos y flags: NO se renombran ni se quitan.
- Este módulo es la puerta de admisión de TODOS los procesos pesados del proyecto: un error aquí abre la puerta a saturar el PC. Fail-closed: si no se puede medir CPU o RAM, la admisión RECHAZA con `NO DATA`, no acepta.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/checkout/merge/stash · rm (se aparca en cuarentena/ con MANIFEST SHA-256) · datos sintéticos, mocks, random/seed, valores por defecto ante falta de dato (se escribe NO DATA) · relajar umbrales · escribir fuera del TERRITORIO · tocar services/engine_version.py · pip install de cualquier cosa · procesos largos sin admisión · inventar una salida que no se ejecutó · declarar subagentes que tu CLI no tiene.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A03.md: comandos y salida CRUDA; qué medida se mapea a qué umbral y por qué; lo que no se pudo; hallazgos; veredicto propio.
3. orchestration/agy/DONE_A03.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A03 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
