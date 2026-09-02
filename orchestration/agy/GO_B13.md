# GO_B13 — W4.2-bis: el candado del discovery no puede fallar en silencio

## Identidad
- ID: B13 · Ola: B · Rama/worktree: JOSFER78/agy-B13 · Timebox: 20 min
- Variables ya puestas: AGY_AGENT=B13, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
En `services/discovery/discovery_validation_pipeline.py::_acquire_singleton_lock`, el `except (ImportError, OSError): pass` añadido por A10 deja de callar: en Windows (sin `fcntl`) imprime `[DISCOVERY] AVISO: candado de instancia única no disponible en este sistema (sin fcntl); ejecución sin protección de instancia` y continúa; un `OSError` distinto del "otra instancia" se re-lanza (no se traga); y un test lo demuestra sin mocks.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/discovery/discovery_validation_pipeline.py (SOLO la función `_acquire_singleton_lock`, líneas ~76-92)
- tests/test_discovery_singleton_lock.py (nuevo)
- orchestration/results/agy/B13.md (nuevo) · orchestration/agy/DONE_B13.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- services/discovery/discovery_validation_pipeline.py líneas 70-95 (el bloque del candado; lee el `except` original que imprime "Otra instancia ya esta en ejecucion" y sale, y el añadido de A10).
- orchestration/results/agy/A10.md §W4.4 (por qué se movió el import).
- services/ops/gobernanza_recursos.py (cómo A03 resolvió el candado portable con `msvcrt`; si es trivial reutilizar su mecanismo aquí, hazlo; si no, aviso explícito).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío. Lee el bloque y pégalo en el informe.
2. Cambio mínimo: `except ImportError:` → print del AVISO literal de arriba y continuar; `except OSError` "otra instancia" → conserva el comportamiento actual (mensaje + `sys.exit(0)`); cualquier otra excepción se propaga. Nada de `pass`.
3. Test real (sin mocks de librería): importa el módulo, llama `_acquire_singleton_lock()` en Windows capturando stdout con `capsys` ⇒ contiene "AVISO: candado de instancia única no disponible"; y `grep` de que no queda `except (ImportError, OSError): pass` en el fichero.
4. Informe + DONE + cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_discovery_singleton_lock.py tests/test_gates_passed_escritores.py -q -p no:cacheprovider   # esperado: todos passed
grep -c "except (ImportError, OSError): pass" services/discovery/discovery_validation_pipeline.py    # esperado: 0
grep -c "AVISO: candado de instancia" services/discovery/discovery_validation_pipeline.py             # esperado: >= 1
git diff --name-only   # ⊆ TERRITORIO; esperado: services/discovery/discovery_validation_pipeline.py
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO.
- No cambies nada más del pipeline (es el discovery del VPS): solo el bloque del candado.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir fuera del TERRITORIO · mocks · `pass` en un except · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B13.md. 3. orchestration/agy/DONE_B13.md.
4. Cierre: orca orchestration send --type worker_done --subject "B13 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
