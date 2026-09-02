# DONE_B05 — W3.3 Piloto: 20 Estrategias `.sqx` → AST Canónico → Registro de Gates, Coste Medido

- **Agente**: AGY-B05
- **Estado**: PASA
- **Fecha**: 2026-09-02
- **Rama**: `JOSFER78/agy-B05`

---

## 1. ENTREGABLES PRODUCIDOS (Dentro de TERRITORIO)

1. `services/sqx_bridge/parse_sqx_piloto.py`:
   - Parser de archivos `.sqx` (ZIP + XML).
   - Conversor declarativo a AST canónico `CanonicalStrategy` con funciones puras `leer_sqx()` y `a_ast_canonico()`.
   - Evaluación e integración con `RegistryPipeline` (11 gates v1) con evidencia real y sin invención sintética.
   - Medición de coste en segundos por estrategia y global.

2. `tests/test_parse_sqx_piloto.py`:
   - Suite de pruebas automatizadas con 4 tests unitarios e integrales (determinismo de hash, validación de fixtures, NO DATA explícito y ejecución de 20 estrategias).

3. `tests/fixtures/sqx/`:
   - 3 fixtures reales de estrategias SQX: `Strategy 1.4.138.sqx` (71.5 KB), `Strategy 1.3.117.sqx` (82.4 KB), `EMACross.sqx` (2.87 KB), todos < 200 KB.

4. `orchestration/results/agy/B05.md`:
   - Informe técnico detallado con tabla de 20 filas, desglose de indicadores, estatus de AST, coste en segundos y diagnóstico de certificación.

---

## 2. RESULTADOS DE ACEPTACIÓN RE-EJECUTADOS

```bash
# Test unitario (>= 3 passed):
$ "$PY" -m pytest tests/test_parse_sqx_piloto.py -q -p no:cacheprovider
4 passed in 7.55s

# Ejecución piloto N=20:
$ "$PY" services/sqx_bridge/parse_sqx_piloto.py --csv data/sqx_exports/toimprove_2026-08-31.csv --n 20 --out /tmp/b05_piloto.json
rc=0

# Inspección de JSON de salida:
$ "$PY" -c "import json; j=json.load(open('/tmp/b05_piloto.json')); print(len(j['estrategias']), sum(1 for e in j['estrategias'] if e.get('ast_completo')), round(j['coste_total_s'],1))"
20 9 3.1

# Conteo de fixtures (2 o 3):
$ ls tests/fixtures/sqx/*.sqx | wc -l
3

# Conteo de filas de tabla en informe (>= 21):
$ grep -cE "^\| " orchestration/results/agy/B05.md
23

# Verificación de git diff (vacío, solo ficheros nuevos dentro de territorio):
$ git diff --name-only
(vacío)
```

---

## 3. CONCLUSIÓN Y CIERRE

Tarea W3.3 finalizada con éxito con cumplimiento estricto de los guardarraíles ZERO-MOCKS y REAL-ONLY.
