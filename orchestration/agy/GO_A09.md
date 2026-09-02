# GO_A09 — Refutador de A08 (motor 5.18.0)

## Identidad
- ID: A09 · Ola: A (se despacha cuando A08 aterriza e integrado en tu base) · Rama/worktree: JOSFER78/agy-A09 · Timebox: 45 min
- Variables ya puestas en tu terminal: AGY_AGENT=A09, PYTHONPATH=<raíz de tu worktree>.
- Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`. Datos: `data/normalized/` enlazado al checkout principal, SOLO LECTURA.

## OBJETIVO (una frase verificable)
Demostrar, o descartar con evidencia, que 5.18.0 cambia operaciones donde NO debería (celdas ULTRA / sin sesión) o no las cambia donde debería (celdas FONDEO con sesión: apertura 14:30 UTC en invierno y 13:30 UTC en verano; flat 15:10 CT), leyendo los dos baselines y muestreando días concretos del ledger.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- orchestration/results/agy/A09.md (nuevo) · orchestration/agy/DONE_A09.md (nuevo)
- Scripts efímeros SOLO en `orchestration/results/agy/A09_*.py`.

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/verificacion_f02_5.17.0.json y orchestration/results/verificacion_f02_5.18.0.json (estructura: `celdas[]` con track/symbol/tf/config, métricas y huella SHA-256 del ledger).
- orchestration/state/contratos/W29_motor_5_18_sesiones_dst.md §1-§4 (qué DEBE cambiar y qué NO).
- orchestration/results/agy/A08.md (léelo DESPUÉS de tu propia medición, para contrastar).
- services/validation/engine/event_backtest_engine.py (la sesión nueva) y services/engine_version.py.

## PASOS (numerados, cortos, en orden)
1. Script `orchestration/results/agy/A09_baselines.py`: carga los dos JSON; tabla de 15 filas con huella del ledger igual/distinta y métricas antes→después. Regla: ULTRA (9) deben ser idénticas ⇒ cualquier diferencia es FALLO de A08. FONDEO (6): si TODAS son idénticas, sospecha (la sesión no se aplica) y explícalo.
2. Reproduce una celda FONDEO con `scripts/verificacion_f02.py` NO (pesado): en su lugar, usa el motor directamente sobre el dataset de la celda (mira cómo lo hace `scripts/verificacion_f02.py` y copia SOLO la llamada de una celda ES 4h) con `--out` a `orchestration/results/agy/A09_celda.json`; si necesitas más de una celda, pide admisión con `orca orchestration ask`.
3. Del ledger de esa celda: toma 3 días de enero y 3 de julio; comprueba hora UTC de la primera operación/vela admitida en sesión (14:30 en invierno, 13:30 en verano) y que no hay posiciones abiertas después del flat 15:10 CT; busca velas de fin de semana o festivos tratadas como sesión.
4. Comprueba `zoneinfo` real: `"$PY" -c "from zoneinfo import ZoneInfo; import datetime as d; print(d.datetime(2023,1,16,9,30,tzinfo=ZoneInfo('America/New_York')).astimezone(d.timezone.utc), d.datetime(2023,7,17,9,30,tzinfo=ZoneInfo('America/New_York')).astimezone(d.timezone.utc))"` → 14:30 y 13:30 UTC. Si el motor usa otra zona (Chicago para CME), verifica igual.
5. Informe: §1 tabla 15 celdas; §2 muestreo de días con salida cruda; §3 fallos encontrados (o "ninguno") con la evidencia; §4 veredicto `A08 CONFIRMADO` / `A08 REPITE` con lista.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" orchestration/results/agy/A09_baselines.py; echo "rc=$?"    # esperado: imprime ULTRA_IDENTICAS=9 FONDEO_DISTINTAS=<n>; rc=0
grep -c "^| " orchestration/results/agy/A09.md                     # esperado: >= 16 (tabla de 15 celdas con cabecera)
grep -cE "14:30|13:30" orchestration/results/agy/A09.md            # esperado: >= 2
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO (solo lees y ejecutas) · ¿Ejecuta algo pesado? Una celda: permitido; más: `orca orchestration ask`.
- No modificas código: describes el fallo; lo arregla A08 en su REPITE.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · datos sintéticos · escribir fuera del TERRITORIO · escribir en data/ · tocar services/ · `verificacion_f02.py` completo sin admisión · inventar una salida que no se ejecutó · declarar subagentes.

## SALIDA
1. Working tree limpio salvo ficheros nuevos en `orchestration/results/agy/` y `orchestration/agy/DONE_A09.md`.
2. orchestration/results/agy/A09.md con salida cruda y veredicto.
3. orchestration/agy/DONE_A09.md (plantilla: orchestration/agy/PLANTILLA_DONE.md).
4. Cierre: orca orchestration send --type worker_done --subject "A09 <CONFIRMADO|REPITE|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
