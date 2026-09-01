# DISEÑO 5.17.0 — 2 arquetipos EVENTO para futuros intradía de índice (CUELLO 6)

**Autor:** Hermes (subagente de diseño de arquetipos) · **Fecha:** 2026-09-01 · **Estado:**
IMPLEMENTADO (motor 5.17.0).

## Por qué (CUELLO 6)

Con ES en 5m hay 250.507 barras (OOS 50.101): por primera vez el presupuesto de barras no es
el cuello de botella (basta ~1 operación cada 250 barras para llegar a las ≥200 OOS del
criterio 1.1 sellado). Pero los arquetipos EVENTO existentes (5.14.0: `reversion_atr`,
`squeeze_breakout`, `session_momentum`, `streak_edge`) están pensados para cripto o para
temporalidades altas, y en la campaña FONDEO 1h el mejor caso de `session_momentum` dio 24-27
operaciones OOS — muy por debajo del mínimo. La causa raíz: esos arquetipos disparan **como
mucho 1 señal por día y dirección**, atados a una ventana de sesión estrecha (RTH CME,
13:30-20:00 UTC ≈ 6,5 h/día). Sobre ~174 días de sesión OOS eso da un techo estructural de
~174-348 operaciones en el mejor caso, y en la práctica mucho menos (la señal no dispara todos
los días). Hace falta un arquetipo que **use la sesión real del futuro y dispare con más
frecuencia, pero por un mecanismo con ventaja real**, no por bajar el listón de la señal hasta
operar cada pocas barras (ese es exactamente el modo de fallo ya documentado en forex: operar
mucho sin ventaja).

## Estudio previo (punta a punta)

1. **Declaración:** un arquetipo es una etiqueta (`strategy.archetype`, string) + un diccionario
   plano (`strategy.archetype_params`) sobre el `StrategySnapshot` (aditivo desde 5.14.0, no
   rompe el hash canónico de snapshots anteriores).
2. **Generación de blueprint:** `services/discovery/funding_discovery.py`
   (`FundingDiscoveryEngine.generate_candidate_blueprint`) construye el `StrategySnapshot`:
   despacha por `arch_upper` a un `ConditionNode` de documentación/huella (el intérprete
   genérico de indicadores NO se usa para estas familias), fija `sl_type`/`tp_type` según el
   arquetipo, y resuelve `session_window` vía `resolve_session_window(symbol, ...)` — para
   ES/NQ/YM/MES/MNQ/MYM eso es 13:30-20:00 UTC, L-V, `close_at_eod=True` por defecto.
3. **Ejecución:** `services/validation/engine/event_backtest_engine.py`
   (`EventBacktestEngine.run_backtest`) despacha por `archetype_label` a una rama de
   precómputo causal (arrays por barra, sin lookahead) y a una rama de detección de evento
   dentro del bucle principal (`pending_entry`, fill en la apertura de la vela siguiente —
   modelo de latencia 5.9.0). El SL/TP se resuelve con el mismo mecanismo ATR genérico que
   usan todos los arquetipos (o con un TP dinámico, ver `reversion_atr`).
4. **Conteo de DoF:** `services/discovery/effective_dof.py` cuenta SOLO lo que el arquetipo
   consume físicamente: claves de `archetype_params` que aparecen en `_NEW_ARCHETYPE_PARAMS`
   + claves de primer nivel en `_NEW_ARCHETYPE_BASE_CONSUMED` + `risk_pct`/`risk_per_trade_pct`
   si aparece (SIEMPRE cuenta, ver docstring del módulo).
5. **Vecindario del gate 9:** `services/api/app/validation/gates/gate_09_novelty_antifit.py`
   (`_ARCHETYPE_NEIGHBORHOOD_SPEC` + `_perturb_archetype_params`) re-backtestea el candidato
   con `archetype_params` perturbado ±10 %/±20 % para medir estabilidad. Los enteros usan un
   paso mínimo forzado de 1 unidad (bug histórico: redondear `n*(1±δ)` en enteros pequeños
   podía devolver el mismo valor y convertir el test en un no-op).

## Los 2 arquetipos nuevos

### `OPENING_RANGE_BREAKOUT` — ruptura del rango de apertura de sesión

- **Mecánica:** el rango de apertura (alto/bajo de los primeros `or_minutes` minutos tras
  `session_window.start_time_utc`) queda SELLADO en cuanto ese tramo termina. Evento (no
  estado): el cierre de una vela posterior rompe por primera vez ese día el alto (LONG) o el
  bajo (SHORT) del rango sellado. Una entrada LONG y una SHORT por día (si el día rompe primero
  al alza y luego a la baja, ambas cuentan — no se presupone qué dirección tiene ventaja, lo
  decide la evidencia por celda). SL/TP fijos por múltiplo de ATR (dimensión de búsqueda real,
  igual que `squeeze_breakout`/`session_momentum`).
- **Dimensiones de búsqueda:** `or_minutes` {15, 30, 60} (minutos, independiente de la
  temporalidad de las velas — funciona igual en 5m que en 15m), `sl_atr_mult`, `tp_atr_mult`,
  `risk_pct`.
- **Por qué se espera VENTAJA, no solo volumen:** la apertura de la sesión regular (9:30 ET /
  13:30 UTC en índices CME) concentra el mayor volumen y la mayor densidad de información nueva
  del día — overnight absorbido, datos macro programados en la apertura, órdenes institucionales
  que se ejecutan contra el fixing de apertura. La ruptura decisiva del rango inicial refleja
  conflicto de flujo resuelto (quién gana la primera media hora), un patrón de continuación de
  momentum documentado en literatura de trading institucional desde los años 90 (opening range
  breakout, Crabel) y replicado en múltiples mercados de futuros de índice. Es mecánicamente
  distinto de `session_momentum` (que espera un PULLBACK a una EMA en la dirección de un ancla
  horaria, entrada tardía y de baja frecuencia): aquí la entrada es la propia ruptura, más
  próxima en el tiempo al evento informativo, y permite 2 disparos por día (no 1).

### `VWAP_REVERSION` — reversión al VWAP anclado a sesión

- **Mecánica:** VWAP causal que se reinicia (`cum_pv=cum_v=0`) en la primera barra en sesión de
  cada día — el benchmark real contra el que se miden las ejecuciones institucionales intradía
  (algos TWAP/VWAP de fondos, rebalanceos de índice), distinto del VWAP acumulativo GLOBAL ya
  existente en `services/engine/indicator_engine.py` (nunca se reinicia, uso distinto). Evento
  de re-entrada (misma forma que `reversion_atr`, pero anclado al VWAP de sesión en vez de a
  una EMA continua): el cierre se alejó ≥ `vwap_dev_atr_mult`×ATR del VWAP en la vela previa y
  la vela actual cruza de vuelta esa misma banda. TP dinámico = nivel vivo del VWAP (recalculado
  cada barra con el valor conocido AL ABRIR la barra, sin lookahead — mismo patrón que el TP
  dinámico de `reversion_atr`); SL fijo por ATR.
- **Dimensiones de búsqueda:** `vwap_dev_atr_mult` {1.0, 1.5, 2.0}, `sl_atr_mult`, `risk_pct`
  (`tp_atr_mult` es placeholder inerte, igual que en `reversion_atr`).
- **Por qué se espera VENTAJA, no solo volumen:** el VWAP de sesión es el nivel que la mayoría
  de la ejecución institucional intradía usa como referencia de "precio justo" del día — las
  órdenes grandes se trabajan para completar cerca de él, y el inventario de creadores de
  mercado tiende a desvanecer (fade) las salidas del precio lejos del VWAP mientras dura la
  sesión. Esto es un mecanismo de reversión a la media distinto de `reversion_atr` (ancla
  continua tipo EMA, sin reinicio diario, sin ponderación por volumen): aquí el ancla se
  resetea cada sesión y usa volumen real (Dukascopy trae volumen derivado de tick-count, no
  fabricado — ver `_calc_session_vwap`), reflejando específicamente la dinámica de
  acumulación/distribución intradía de un futuro de índice.

**Fuera de alcance deliberado:** ninguno de los 2 se genera para ULTRA
(`_arquetipos_5_17_0_configs(is_ultra=True)` devuelve `[]`) — ambos dependen de
`session_window` como sesión regulada real (RTH CME), algo que no aplica a un perpetuo 24/7 sin
sesión propia. Track ULTRA además está pausado (2026-09-01, foco 100 % FONDEO).

## Evidencia de volumen esperado (conteo de eventos, no backtest)

Sobre un tramo de ~63 días de sesión de `ds_dukascopy_usa500idxusd_5m` (2024-01→2024-03) y su
equivalente en 15m, conteo puro de cruces/rupturas (sin fricción ni SL/TP, cota superior
orientativa):

| Arquetipo | 5m: eventos/63 días | 15m: eventos/63 días |
| :--- | ---: | ---: |
| ORB `or_minutes=15` | 101 (1,60/día) | 97 (1,54/día) |
| ORB `or_minutes=30` | 97 | 93 |
| ORB `or_minutes=60` | 88 | 85 |
| VWAP `k=1.0` | 208 (3,30/día) | 96 (1,52/día) |
| VWAP `k=1.5` | 132 | 57 |
| VWAP `k=2.0` | 91 | 29 |

Extrapolado al tramo OOS completo (~174-189 días de sesión, ~20 % de las ~945 sesiones totales
en 250k barras de 5m): ambos arquetipos proyectan varios cientos de eventos en la mayoría de
combinaciones de rejilla — muy por encima del mínimo de 200. **Verificado con backtest real**
(no solo conteo) sobre el mismo tramo de 63 días con una config representativa de cada uno
(`ES`→`MES`, `or_minutes=15, sl=1.5, tp=4.0, risk=0.005` y `vwap_dev_atr_mult=1.0, sl=1.5,
tp=4.5, risk=0.005`): **101 operaciones** (ORB) y **307 operaciones** (VWAP_REVERSION) —
confirma que el evento realmente se traduce en operación ejecutada por el motor, entradas en
horario de sesión coherente (primeras entradas ORB a las 14:05-14:25 UTC, justo tras sellarse
el rango de apertura de 13:30-13:45 UTC). No es evidencia de EDGE (PF en este tramo pequeño y
sin optimizar es <1, como es de esperar con un solo punto de la rejilla sin buscar): es
evidencia de que el MECANISMO funciona y genera el volumen proyectado.

## Grados de libertad (services/discovery/effective_dof.py)

| Arquetipo | archetype_params contados | + base consumido (top-level) | + risk_pct | **Total** |
| :--- | :--- | :--- | :---: | :---: |
| `OPENING_RANGE_BREAKOUT` | `or_minutes` (1) | `sl_atr_mult`, `tp_atr_mult` (2) | 1 | **4** |
| `VWAP_REVERSION` | `vwap_dev_atr_mult` (1) | `sl_atr_mult` (1, TP inerte) | 1 | **3** |

## Vecindario del gate 9 — verificación NO-NOOP

`_ARCHETYPE_NEIGHBORHOOD_SPEC` nuevo: `OPENING_RANGE_BREAKOUT: {"or_minutes": ("int", 5)}`,
`VWAP_REVERSION: {"vwap_dev_atr_mult": ("float", 0.25)}`. Enumeración exhaustiva de la rejilla
real × las 4 deltas del gate (±10 %/±20 %): **24/24 combinaciones cambian el valor perturbado
respecto al base (0 no-op)** — el paso mínimo de 1 unidad en enteros (heredado del fix de
2026-08-31) evita el bug histórico de redondeo-a-sí-mismo.

## Regla #26

Motor bump a **5.17.0**. Aditivo estricto: cero líneas tocadas de las familias EMA/RSI/
Donchian/`reversion_atr`/`squeeze_breakout`/`session_momentum`/`streak_edge` existentes; las 2
familias nuevas solo se activan cuando `archetype_label` coincide exactamente con su etiqueta.
`scripts/verificacion_f02.py --comparar 5.16.0 5.17.0` (perfil `champions`, no toca estas 2
familias nuevas) confirma 15/15 celdas idénticas — ver
`orchestration/results/verificacion_f02_diff_5.16.0_vs_5.17.0.md`.
