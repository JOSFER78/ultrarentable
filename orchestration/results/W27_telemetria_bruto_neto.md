# W2.7 — Telemetría bruto/neto del embudo (CARRIL TELEMETRIA)

**Objetivo del encargo**: que la telemetría del embudo de `scripts/mine.py` distinga "la señal
no vale" (`sin_ventaja_bruta`) de "la señal vale pero se la come el coste" (`sin_ventaja_por_coste`),
sin tocar ningún umbral ni ninguna decisión de la campaña.

## 1. Qué se leyó primero

- `scripts/mine.py` — bloque de telemetría W2.6 (`UMBRALES_EMBUDO`, `_nueva_casilla_causas`,
  `resumir_causas`, `persistir_telemetria`, y el bucle principal de `run_mining_pipeline` que
  llama `telemetria.append(...)` en 4 sitios: etapas IS, VAL, OOS y GATES).
- `tests/test_mine_telemetria_cobertura_familias.py` (W2.6, 3 tests) — respetado íntegro, sin
  tocar ni una línea; sigue en verde tras el cambio (ver §3).
- `services/validation/engine/event_backtest_engine.py`:
  - `EventBacktestResult` (línea ~133) expone `profit_factor` (**NETO**, calculado en la línea
    ~1768-1769 a partir de `TradeRecord.net_pnl_usd`), `total_fees_usd`, `total_slippage_usd` y
    `trades: List[TradeRecord]`.
  - `TradeRecord` (línea ~53) expone, por operación, **`gross_pnl_usd`** (PnL bruto, antes de
    `fees_usd`/`slippage_usd`) además de `net_pnl_usd`, `fees_usd`, `slippage_usd`.
  - **Conclusión verificada**: el motor NO calcula un "profit factor bruto" propio (solo el
    neto), pero SÍ expone `gross_pnl_usd` por operación en el ledger que ya devuelve. Por tanto
    `pf_bruto` **SÍ se pudo calcular sin tocar el motor** — agregando `gross_pnl_usd` del ledger
    de operaciones que `run_backtest()` ya devuelve, exactamente como pedía el encargo. No hizo
    falta escribir `NO DISPONIBLE` para el caso real (esa rama de código existe y está testeada
    para el caso estructural en que un resultado no trajera `trades`, que no ocurre con
    `EventBacktestResult`).

## 2. Cambios (solo el bloque de telemetría, solo aditivos)

Todo en `scripts/mine.py`, sección de telemetría (líneas ~706-850 tras el cambio) y en los 4
puntos donde se construye cada registro de `telemetria` (~línea 1100-1213):

1. **Función nueva `_pf_bruto_y_coste(bt_result) -> dict`**: agrega desde
   `bt_result.trades[i].gross_pnl_usd` — `pf_bruto` (misma convención degenerada que ya usa el
   motor para el PF neto: 99.0 si hay ganancias sin pérdidas, 0.0 si no hay operaciones),
   `pf_neto` (alias de `bt_result.profit_factor`, sin recalcular), `coste_total_usd`
   (`total_fees_usd + total_slippage_usd`, ambos ya calculados por el motor) y
   `coste_pct_del_bruto` (coste total como % de las ganancias brutas; `None` si no hay
   ganancias brutas — no se puede expresar un coste como % de cero sin dividir por cero ni
   inventar un número).
2. **`_nueva_casilla_causas()`**: se añaden dos claves nuevas en 0 (`sin_ventaja_bruta`,
   `sin_ventaja_por_coste`); las 5 claves preexistentes (`total`, `pocas_operaciones`,
   `sin_ventaja`, `ambas`, `otro`) quedan intactas.
3. **`resumir_causas()`**: el cálculo de `bucket` (línea `pocas = ...`, `floja = ...`,
   `bucket = "ambas" if ... else ...`) **no se tocó ni una coma**. Se añadió, DESPUÉS de
   incrementar `casilla[bucket]`/`fam_casilla[bucket]` como siempre, un bloque que — solo
   cuando `bucket == "sin_ventaja"` y el registro trae `pf_bruto` (float) — decide
   `sin_ventaja_bruta` (si `pf_bruto < umbral["pf_min"]`, el mismo umbral de la etapa) o
   `sin_ventaja_por_coste` (si `pf_bruto >= umbral["pf_min"]`). Los registros históricos/de
   test de W2.6 que no traen `pf_bruto` se siguen contando en `sin_ventaja` exactamente igual
   que antes; el desglose nuevo simplemente no se alimenta con ellos (no se inventa el dato).
4. Los 4 sitios donde `run_mining_pipeline` construye un registro de `telemetria` (IS, VAL,
   OOS, GATES) ahora añaden `**_pf_bruto_y_coste(is_bt|val_bt|oos_bt)` al diccionario.
   `UMBRALES_EMBUDO` y las condiciones que deciden si una config sigue al siguiente tramo del
   embudo (`is_bt.total_trades < 5 or is_bt.profit_factor < 1.05`, etc.) no se tocaron.

`persistir_telemetria()` no se modificó: ya serializa `resultado["telemetria"]` completo (con
los campos nuevos dentro de cada registro) y ya llama a `resumir_causas(telemetria)` (con el
desglose nuevo) para `causas_por_etapa`.

## 3. Evidencia — tests

```
$ ./.venv/Scripts/python.exe -m pytest tests/test_mine_telemetria_bruto_neto.py tests/test_mine_telemetria_cobertura_familias.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.8, pytest-8.4.2, pluggy-1.6.0
collected 11 items

tests/test_mine_telemetria_bruto_neto.py::test_pf_bruto_y_coste_calcula_desde_el_ledger_de_operaciones PASSED [  9%]
tests/test_mine_telemetria_bruto_neto.py::test_pf_bruto_y_coste_caso_degenerado_ganancias_sin_perdidas PASSED [ 18%]
tests/test_mine_telemetria_bruto_neto.py::test_pf_bruto_y_coste_sin_operaciones_da_pf_bruto_cero_y_coste_pct_none PASSED [ 27%]
tests/test_mine_telemetria_bruto_neto.py::test_pf_bruto_y_coste_solo_perdidas_brutas_da_coste_pct_none_pero_coste_total_real PASSED [ 36%]
tests/test_mine_telemetria_bruto_neto.py::test_pf_bruto_y_coste_sin_lista_de_trades_declara_no_disponible PASSED [ 45%]
tests/test_mine_telemetria_bruto_neto.py::test_resumir_causas_desglosa_sin_ventaja_en_bruta_y_por_coste_sin_tocar_el_total PASSED [ 54%]
tests/test_mine_telemetria_bruto_neto.py::test_resumir_causas_no_rompe_con_registros_sin_pf_bruto_w26 PASSED [ 63%]
tests/test_mine_telemetria_bruto_neto.py::test_nueva_casilla_causas_trae_las_claves_nuevas_en_cero PASSED [ 72%]
tests/test_mine_telemetria_cobertura_familias.py::test_resumir_causas_desglosa_cada_etapa_por_familia_ademas_del_total PASSED [ 81%]
tests/test_mine_telemetria_cobertura_familias.py::test_resumir_causas_agrupa_bajo_signo_de_interrogacion_si_falta_familia PASSED [ 90%]
tests/test_mine_telemetria_cobertura_familias.py::test_persistir_telemetria_escribe_contexto_y_cobertura_familias_nuevos PASSED [100%]

============================= 11 passed in 0.60s ==============================
```

También verde con el glob de aceptación exacto:
```
$ ./.venv/Scripts/python.exe -m pytest tests/test_mine_telemetria_*.py -q
...........                                                              [100%]
11 passed in 0.48s
```

## 4. Evidencia — `git diff scripts/mine.py` no toca umbrales ni lógica de decisión

`git diff --stat scripts/mine.py`: `1 file changed, 110 insertions(+), 5 deletions(-)`. Las 5
líneas eliminadas son exactamente las 5 líneas que se reemplazaron por su versión con el campo
nuevo añadido (confirmado con `grep -n "^-" ` sobre el diff, ninguna otra):

```
-    return {"total": 0, "pocas_operaciones": 0, "sin_ventaja": 0, "ambas": 0, "otro": 0}
-                "trades": is_bt.total_trades, "pf": round(is_bt.profit_factor, 3)})
-                "trades": val_bt.total_trades, "pf": round(val_bt.profit_factor, 3)})
-                "trades": oos_bt.total_trades, "pf": round(oos_bt.profit_factor, 3)})
-                "dd_oos": round(oos_bt.max_drawdown_pct, 2)})
```

`UMBRALES_EMBUDO` (IS 1.05/5, VAL 1.00/3, OOS 1.10/`MIN_OPERACIONES_OOS`) y la línea que decide
`bucket` (`pocas = ...`, `floja = ...`, `bucket = "ambas" if ... else ...`) no aparecen en el
diff: cero cambios. `services/validation/engine/event_backtest_engine.py` no se tocó (solo se
leyó) — no aplica Regla #26, no hubo motivo para subir versión de motor ni re-verificar
identidad 15/15.

## 5. Evidencia — prueba REAL y ligera

```
$ ./.venv/Scripts/python.exe scripts/mine.py --track fondeo --symbol ES --tf 15m --profile arquetipos --dataset-source dukascopy --max-candidates 6
[2026-09-01 19:44:26] Iniciando minería: Track=FONDEO, Symbol=ES (ejecución: MES), TF=15m, Profile=arquetipos, DryRun=False
[2026-09-01 19:44:26] Dataset físico resuelto: ds_dukascopy_usa500idxusd_15m_consolidated.json (13723.9 KB) [FUENTE=DUKASCOPY, dataset_source pedido='dukascopy']
[2026-09-01 19:44:26] Espacio de búsqueda generado: 420 configuraciones totales -> recortado a 6 (--max-candidates 6) · cobertura por familia: {'REVERSION_ATR': 6}
[2026-09-01 19:44:27] Particionado cronológico: IS=50026 bars, Val=16675 bars, Blind OOS=16676 bars
[2026-09-01 19:45:05] Embudo: {'IS': 6}
[2026-09-01 19:45:05] Minería completada: 0 candidatas certificadas 11/11
[2026-09-01 19:45:05]   causas en IS: 6 muertas -> pocas_operaciones=0 sin_ventaja=6 ambas=0 otro=0
[2026-09-01 19:45:05] Telemetría del embudo escrita en .../orchestration/results/telemetria/embudo_FONDEO_ES_15m_arquetipos_20260901T194505Z.json
```

Confirmado, tal como avisaba el encargo: con el perfil `arquetipos` y `--max-candidates 6` el
prefijo del espacio de búsqueda evalúa 6 configuraciones, **todas** `REVERSION_ATR`
(`cobertura_familias: {"REVERSION_ATR": 6}`) — el mismo comportamiento de prefijo documentado
en W2.6.

Campos nuevos del JSON generado (`causas_por_etapa.IS`, y uno de los 6 registros de
`telemetria`; JSON completo en la ruta de arriba):

```json
"causas_por_etapa": {
  "IS": {
    "total": 6, "pocas_operaciones": 0, "sin_ventaja": 6, "ambas": 0, "otro": 0,
    "sin_ventaja_bruta": 6,
    "sin_ventaja_por_coste": 0,
    "por_familia": { "REVERSION_ATR": { "...": "...", "sin_ventaja_bruta": 6, "sin_ventaja_por_coste": 0 } }
  }
}
```
```json
{
  "strategy_id": "UR_FONDEO_ES_15M_c1", "etapa": "IS", "familia": "REVERSION_ATR",
  "motivo": "trades=839 pf=0.690", "trades": 839, "pf": 0.69,
  "pf_bruto": 0.812, "pf_neto": 0.69,
  "coste_total_usd": 6270.0, "coste_pct_del_bruto": 34.6
}
```

Las 6 configuraciones traen `pf_bruto` entre 0.79 y 0.841 (siempre por debajo del umbral IS de
1.05) y `coste_pct_del_bruto` entre 33.15% y 35.72%. **Lectura honesta de este dato concreto**:
en esta muestra de 6 candidatas REVERSION_ATR a 15m, el campo nuevo dice que la causa de fondo
es `sin_ventaja_bruta` (6/6) — la señal ya no tenía ventaja ANTES de pagar comisión/slippage,
no que el coste se comiera una señal bruta neutra. Esto **no refuta ni confirma** la hipótesis
del orquestador para ES 5m (PF bruto ≈1.0 ahogado por el 64.6% del ATR en comisión) — esa
corrida fue a 15m (temporalidad distinta, con ATR mayor y por tanto la comisión fija es una
fracción menor del ATR) y con solo 6 configuraciones de una única familia (prefijo del espacio
de búsqueda). Lo que esta corrida SÍ demuestra en vivo es que el mecanismo funciona
correctamente sobre datos reales: calcula `pf_bruto` desde el ledger real de 839-840 operaciones
por config, lo compara contra el mismo umbral, y clasifica bien la causa. El escenario
`sin_ventaja_por_coste` (pf_bruto por encima del umbral, pf_neto por debajo) está cubierto con
evidencia por los tests unitarios de función (`_pf_bruto_y_coste`, ver §3), no por esta corrida
real concreta — que no lo produjo porque, para estos 6 candidatos a 15m, el bruto ya perdía.

## 6. Ficheros tocados

- `scripts/mine.py` — bloque de telemetría (única escritura en territorio).
- `tests/test_mine_telemetria_bruto_neto.py` — nuevo, 8 tests.
- `orchestration/results/W27_telemetria_bruto_neto.md` — este informe.
- `orchestration/results/telemetria/embudo_FONDEO_ES_15m_arquetipos_20260901T194505Z.json` —
  generado por la corrida real de §5 (efecto secundario esperado de ejecutar el CLI, no una
  escritura manual).

## 7. Peticiones al orquestador

Ninguna. El campo `pf_bruto` resultó calculable sin tocar el motor (§1), así que no hizo falta
ninguna decisión fuera de este territorio.
