# GO_A08 — W2.9: motor 5.18.0, sesiones con DST y ventana por familia (regla #26, D10)

## Identidad
- ID: A08 · Ola: A · Rama/worktree: JOSFER78/agy-A08 (Orca; la rama real lleva el prefijo del usuario) · Timebox: 45 min (si no llega, PARCIAL honesto con todo lo verde que haya; nunca un motor a medias sin decirlo)
- Variables ya puestas en tu terminal: AGY_AGENT=A08, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Todo desde la raíz del worktree.
- Datos: `data/normalized/` de tu worktree está ENLAZADO (junction) al checkout principal para que `verificacion_f02.py` encuentre los 5 datasets de identidad. SOLO LECTURA: prohibido escribir, crear o borrar nada ahí.

## OBJETIVO (una frase verificable)
Implementar `orchestration/state/contratos/W29_motor_5_18_sesiones_dst.md` completo: sesión en hora local de mercado con `zoneinfo` por vela (no 13:30 UTC fijo), familias A/B/D con ventana Globex y flat 15:10 CT (no `None`), `CURRENT_ENGINE_VERSION` 5.17.0 → 5.18.0 con su entrada en `VERSION_HISTORY`, baseline F02 nuevo escrito con `--out` a `orchestration/results/verificacion_f02_5.18.0.json` (el de 5.17.0 intacto) y comparación 5.17.0 → 5.18.0 explicada celda a celda (9 ULTRA idénticas; 6 FONDEO explicadas), con `tests/test_motor_5_18_sesiones_dst.py` verde.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- services/validation/engine/ (solo los ficheros que el contrato W29 nombre; lista los que tocas en el informe)
- services/engine_version.py (bump + `VERSION_HISTORY`, nada más)
- tests/test_motor_5_18_sesiones_dst.py (nuevo)
- orchestration/results/verificacion_f02_5.18.0.json (nuevo) y orchestration/results/verificacion_f02_diff_5.17.0_5.18.0.md (nuevo, si `--comparar` lo genera; si no, la tabla va en tu informe)
- orchestration/results/agy/A08.md (nuevo) · orchestration/agy/DONE_A08.md (nuevo)
- SOLO LECTURA: scripts/verificacion_f02.py (se ejecuta, no se edita), orchestration/results/verificacion_f02_5.17.0.json (sha256 debe seguir siendo `c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8`), data/.

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/state/contratos/W29_motor_5_18_sesiones_dst.md ENTERO (§1-§4). Es el contrato; cítalo por sección en el informe.
- orchestration/results/forense_familias_ES15m.md (el bug medido: sesión fija 13:30 UTC; ventana RTH pegada a las 6 familias).
- services/validation/engine/event_backtest_engine.py: busca `13:30`, `session`, `rth`, `flat`, `funding_discovery`; lee la función de sesión entera antes de tocarla.
- services/engine_version.py líneas 93 (`CURRENT_ENGINE_VERSION`) y 106-140 (`VERSION_HISTORY`: copia el formato de la entrada 5.17.0).
- scripts/verificacion_f02.py: `--help` (flags `--out`, `--force`, `--comparar`).

## PASOS (numerados, cortos, en orden)
1. Comprobar: `git status --porcelain` vacío · `sha256sum orchestration/results/verificacion_f02_5.17.0.json` = c1c3a7bb… · `ls data/normalized/*.json | wc -l` > 0 (junction viva; si 0 ⇒ `orca orchestration ask` y para).
2. Implementar el contrato §1-§3 en el motor: zona horaria por mercado (`zoneinfo.ZoneInfo`), conversión por vela, ventanas por familia, flat 15:10 CT. Sin cambiar NADA fuera de sesión/ventana: las 9 celdas ULTRA deben dar ledger idéntico.
3. `tests/test_motor_5_18_sesiones_dst.py` con al menos los casos §4.1 (a)-(e) del contrato, con fechas y horas literales.
4. Bump: `CURRENT_ENGINE_VERSION = "5.18.0"`; nueva entrada al principio de `VERSION_HISTORY` con `version`, fecha, y `changes` describiendo DST + ventanas + flat (formato de la entrada 5.17.0). Si hay lista de versiones conocidas en el módulo, añade "5.18.0".
5. PESADO — pide admisión ANTES: `orca orchestration ask --question "A08 pide admisión para: verificacion_f02.py --out orchestration/results/verificacion_f02_5.18.0.json (15 celdas)" --json`. Con el OK: ejecutar; debe terminar rc=0 con 15 celdas OK. Luego `"$PY" scripts/verificacion_f02.py --comparar 5.17.0 5.18.0`.
6. Informe: tabla celda a celda (15 filas: track, símbolo, tf, config, trades/PF/net antes→después, ledger SHA igual/distinto, explicación mecánica de cada diferencia FONDEO: qué velas entran/salen de sesión por el desplazamiento de invierno, qué cierres EOD se mueven). Una celda FONDEO idéntica también se explica.
7. Ejecutar ACEPTACIÓN; pegar salidas crudas en `orchestration/results/agy/A08.md`; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" -m pytest tests/test_motor_5_18_sesiones_dst.py -q -p no:cacheprovider      # esperado: >= 5 passed
grep -n 'CURRENT_ENGINE_VERSION: str' services/engine_version.py                  # esperado: "5.18.0"
grep -c '"version": "5.18.0"' services/engine_version.py                           # esperado: >= 1
sha256sum orchestration/results/verificacion_f02_5.17.0.json                       # esperado: c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8
"$PY" -c "import json; j=json.load(open('orchestration/results/verificacion_f02_5.18.0.json')); print(j['engine_version'], len(j['celdas']), sum(1 for c in j['celdas'] if c['estado']=='OK'))"   # esperado: 5.18.0 15 15
"$PY" scripts/verificacion_f02.py --comparar 5.17.0 5.18.0 | tail -20              # esperado: 9 celdas ULTRA IDÉNTICAS; las FONDEO listadas con diff
git status --short data/normalized | wc -l                                          # esperado: 0 (no has escrito en datos)
git diff --name-only   # ⊆ TERRITORIO (más GO_A08.md si el ORQ añadió CORRECCION_n)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor (services/validation/engine/ o services/engine_version.py)? **Toca semántica del motor: SÍ** → bump 5.18.0 + baseline F02 nuevo con `--out` + comparación explicada (regla #26). NUNCA sobrescribir el baseline 5.17.0 ni usar `--force`.
- ¿Ejecuta algo pesado? SÍ: `verificacion_f02.py` (15 backtests). SOLO tras `orca orchestration ask` con OK del orquestador. pytest completo PROHIBIDO.
- Una celda `SIN DATOS` en el baseline ⇒ el script aborta sin escribir (W4.6): no lo fuerces; reporta y pregunta.
- Si el timebox se agota: deja el motor coherente (o revierte tus cambios con `git checkout -- <fichero>`, autorizado SOLO para tus propios cambios no terminados) y reporta PARCIAL con lo que sí quedó verde.

## PROHIBIDO (lista negra, sin excepciones)
git add/commit/push/reset/merge/stash · rm · datos sintéticos, mocks, random/seed, valores por defecto ante falta de dato · relajar umbrales · escribir fuera del TERRITORIO · escribir en data/ · `--force` en verificacion_f02 · procesos pesados sin admisión · inventar una salida que no se ejecutó · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit).
2. orchestration/results/agy/A08.md: ficheros tocados, comandos y salida CRUDA, tabla de 15 celdas con explicación, lo que no se pudo, veredicto propio.
3. orchestration/agy/DONE_A08.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A08 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
