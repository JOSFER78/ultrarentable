# GO_B04 — Forense E1/E2: refutar la lectura del orquestador (D15: "es edge, no dato ni coste")

## Identidad
- ID: B04 · Ola: B (se despacha cuando B03 aterriza e integrado en tu base) · Rama/worktree: JOSFER78/agy-B04 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B04, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.
- Datos: `data/normalized/` enlazado al checkout principal, SOLO LECTURA.

## OBJETIVO (una frase verificable)
Un informe que intenta REFUTAR, con los JSON de telemetría y sin fiarse de los informes de B02/B03 ni del orquestador, la decisión D15 ("la familia `reversion` de ES no tiene ventaja bruta: es edge, no dato ni coste") y los veredictos por celda de E2, comprobando: (1) que el bucket `sin_ventaja_bruta` se calcula como dice W27 (pf_bruto < umbral de la etapa) y no por un default; (2) que `pf_bruto` no está contaminado por comisiones (recalcúlalo desde un ledger real de al menos 3 configs re-ejecutando el motor sobre la celda con `--max-candidates 3`); (3) que las 6 familias estuvieron representadas en E2 con el conteo esperado (420, por familia según A11) y que ningún registro de IS lleva `is_pf` (W2.8) ni faltan campos; (4) que los umbrales de IS/VAL/OOS de mine.py no cambiaron entre el 4h del 01-09 y hoy (diff de `UMBRALES_EMBUDO`); (5) qué diría el veredicto si el umbral de IS fuera PF ≥ 1,00 en vez de 1,05 (sensibilidad, SOLO como análisis: prohibido cambiar el umbral en código). Veredicto: `D15 CONFIRMADA` o `D15 REFUTADA` con la evidencia.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- orchestration/results/agy/B04.md (nuevo) · orchestration/agy/DONE_B04.md (nuevo)
- Scripts efímeros SOLO en `orchestration/results/agy/B04_*.py`
- orchestration/results/telemetria/ (SOLO los JSON que genere tu re-ejecución de 3 configs; nada más)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- orchestration/results/telemetria/embudo_FONDEO_ES_5m_reversion_20260902T104704Z.json y ..._15m_reversion_20260902T105236Z.json (E1) y los dos embudos `arquetipos` de hoy (E2; localízalos por fecha).
- orchestration/results/W27_telemetria_bruto_neto.md (definición de pf_bruto/sin_ventaja_bruta) y scripts/mine.py (`UMBRALES_EMBUDO`, `_pf_bruto_y_coste`, `resumir_causas`; `git log -p --follow` para ver si cambiaron los umbrales).
- orchestration/state/PLAN_LOCAL_FONDEO.md W2 (reglas pre-selladas) y current_phase.md D15.
- orchestration/results/agy/B02.md y B03.md: SOLO al final, para contrastar tus cifras con las suyas.

## PASOS (numerados, cortos, en orden)
1. Script `B04_leer_embudos.py`: para cada embudo, imprime engine_version, max_candidates, espacio_total, truncado, conteo por familia, conteo por bucket y sub-bucket, y comprueba que cada registro tiene pf, pf_bruto, pf_neto, coste_pct_del_bruto, trades; lista anomalías (registros sin campos, familias ausentes, sumas que no cuadran).
2. Recalcula desde los registros: ¿`sin_ventaja_bruta` ⇔ `pf_bruto < UMBRALES_EMBUDO['IS']['pf_min']`? Cuenta discrepancias.
3. PESADO ligero (pide admisión con `orca orchestration ask`): re-ejecuta `mine.py --track fondeo --symbol ES --tf 15m --profile reversion --max-candidates 3 --dataset-source dukascopy` vía `gobernanza_recursos ejecutar`; compara los 3 registros nuevos con los del embudo de E1 (mismos ids ⇒ mismos pf/pf_bruto/trades: determinismo) y recalcula pf_bruto a mano desde `trades` si el JSON los trae (si no, NO DATA y dilo).
4. Sensibilidad: cuántas configs de E1 y E2 tendrían pf_bruto ≥ 1,00 y ≥ 1,05; tabla por familia. Solo análisis.
5. Informe: §1 lectura de embudos, §2 verificación del bucket, §3 determinismo, §4 sensibilidad, §5 veredicto `D15 CONFIRMADA|REFUTADA` y, para E2, por celda `AGOTADA|SIGUE|NEAR-MISS` según las reglas pre-selladas, coincidan o no con B03.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
"$PY" orchestration/results/agy/B04_leer_embudos.py; echo "rc=$?"          # esperado: tabla por embudo y ANOMALIAS=<n>; rc=0
grep -cE "D15 (CONFIRMADA|REFUTADA)" orchestration/results/agy/B04.md          # esperado: 1
grep -cE "AGOTADA|SIGUE|NEAR-MISS" orchestration/results/agy/B04.md            # esperado: >= 2
git diff --name-only   # ⊆ TERRITORIO; esperado: vacío
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? Una re-ejecución de 3 configs con admisión; nada más.
- Prohibido cambiar umbrales en código: la sensibilidad se calcula sobre los registros.
- No modificas código ni tests: si encuentras un fallo, lo describes con evidencia.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm · escribir en data/ · tocar código · campañas sin admisión · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree limpio salvo ficheros nuevos en `orchestration/results/agy/` (y telemetría de la re-ejecución) y `orchestration/agy/DONE_B04.md`.
2. orchestration/results/agy/B04.md. 3. orchestration/agy/DONE_B04.md.
4. Cierre: orca orchestration send --type worker_done --subject "B04 <CONFIRMADA|REFUTADA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
