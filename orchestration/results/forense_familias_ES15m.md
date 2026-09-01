# Forense — 3 anomalías de la campaña FONDEO ES 15m (arquetipos, 420 configs)

**Fecha:** 2026-09-01 · **Carril:** FORENSE (solo lectura) · **Motor leído:** `services/validation/engine/event_backtest_engine.py` (CURRENT_ENGINE_VERSION=5.17.0, no modificado)
**Telemetría fuente:** `orchestration/results/telemetria/embudo_FONDEO_ES_15m_arquetipos_20260901T182459Z.json`
**Dataset leído:** `data/normalized/ds_dukascopy_usa500idxusd_15m_consolidated.json` (83.377 barras, venue=dukascopy, symbol=USA500IDXUSD, `proxy_for`="ES/MES", rango 2023-01-02 → 2026-08-30; IS = primeras 50.026 barras según `contexto.barras_is` de la telemetría)

Todo lo que sigue es lectura de código + medición sobre el dataset real con scripts de un solo proceso (sin lanzar el motor ni ninguna campaña). Ningún fichero de código fue modificado.

---

## ANOMALÍA 1 — VWAP_REVERSION es la peor familia (PF mediano 0,65)

### Hipótesis del orquestador: ¿degrada a defecto silencioso por falta de `volume`?

**REFUTADA con evidencia directa.**

Claves de una barra real del dataset 15m (`ds_dukascopy_usa500idxusd_15m_consolidated.json`, barra índice 0):

```
{'close': 3853.796, 'high': 3877.176, 'low': 3853.113, 'open': 3872.998,
 'spread_mean': 0.5368629, 'tick_count': 1291,
 'timestamp_utc_ms': 1672700400000, 'volume': 1.575439969659783}
```

La clave `'volume'` **SÍ existe** en las 83.377 barras (verificado, no es solo la barra 0). Estadística sobre el dataset completo:

```
n 83377
min vol 0.002100000041536987 max vol 95.30999870598316
mean vol 3.535823440605454
any zero? False
corr(volume,tick_count)= 0.8109098820050795
```

Es un volumen real, variable, positivo en el 100% de las barras, correlacionado 0,81 con `tick_count` — consistente con el propio comentario del motor en `services/validation/engine/event_backtest_engine.py:546-550` ("Volumen Dukascopy (tick-count derivado) es real y variable"). Es un **proxy** (Dukascopy CFD sobre USA500IDXUSD, no volumen real de contratos ES/MES — de ahí valores fraccionarios), pero es dato real de origen, no un relleno.

El código en `services/validation/engine/event_backtest_engine.py:970`:
```python
_volumes_for_vwap = np.array([float(c.get("volume", 1.0) or 1.0) for c in candles], dtype=np.float64)
```
Con `volume` presente y no-cero en el 100% de las barras, el `.get(..., 1.0)` y el `or 1.0` **nunca se activan** para este dataset. El VWAP de sesión (`_calc_session_vwap`, líneas 513-556) sí se pondera por volumen real, no degrada a TWAP. **No hay violación REAL-ONLY aquí.** (Nota menor, no causal: el `or 1.0` de la línea 970 seguiría sustituyendo silenciosamente un volumen exactamente 0 por 1.0 si algún día apareciera — hoy no ocurre, `any zero? False` — lo dejo anotado por higiene, no como causa de la anomalía.)

### Signo de la desviación y alcanzabilidad del TP dinámico

Leída la rama de entrada, `services/validation/engine/event_backtest_engine.py:1666-1679`:
```python
band_lower_prev = _arch_session_vwap_series[i - 1] - _arch_vwap_dev_atr_mult * atr[i - 1]
band_upper_prev = _arch_session_vwap_series[i - 1] + _arch_vwap_dev_atr_mult * atr[i - 1]
was_below = closes[i - 1] <= band_lower_prev
back_above = closes[i] > band_lower_prev
was_above = closes[i - 1] >= band_upper_prev
back_below = closes[i] < band_upper_prev
long_signal = bool(was_below and back_above)
short_signal = bool(was_above and back_below)
```
LONG cuando el precio estaba por debajo de la banda inferior y vuelve a cruzarla hacia arriba (compra barata, apunta al VWAP que está por encima); SHORT simétrico. El signo es **correcto** — no hay inversión de dirección.

TP dinámico, `services/validation/engine/event_backtest_engine.py:1190-1196`:
```python
elif archetype_label == "VWAP_REVERSION" and _arch_session_vwap_series is not None:
    take_profit_price = float(_arch_session_vwap_series[i - 1])
```
Se recalcula cada barra con el VWAP conocido al abrir la barra `i` (anti-lookahead, mismo patrón que `REVERSION_ATR`). Por construcción el VWAP vivo está siempre entre las dos bandas, así que el objetivo es geométricamente alcanzable (no es un TP fuera de rango). No encuentro bug de signo ni de alcanzabilidad en esta rama.

### Diagnóstico

**Dato/calibración, no bug de signo ni de defecto silencioso.** Dos factores, ambos con evidencia:

1. **Compartido con la Anomalía 3** (ver abajo): el ancla de sesión del VWAP (`_calc_session_vwap`, líneas 536-544 — el `cum_pv=cum_v=0` se reinicia en la primera barra dentro de `session_window` de cada día) usa la misma `session_window` fija 13:30-20:00 UTC todo el año. En el 33,4% de los días del dataset (horario estándar, ver Anomalía 3) ese reinicio ocurre una hora ANTES de la apertura real de caja (14:30 UTC en invierno), así que en esos días el VWAP arranca acumulando sobre la última hora del tramo pre-apertura/Globex en vez de sobre la sesión regular — un sesgo sistemático en la referencia que usan tanto la entrada como el TP.
2. **Calibración no verificada con datos de operación** (no pude confirmarlo sin correr el motor, que está fuera de mi carril): la rejilla de `mine.py:451-460` fija el umbral de entrada (desviación) en `vwap_dev_atr_mult` ∈ {1.0, 1.5, 2.0} × ATR, mientras el SL genérico usa `sl_atr_mult` ∈ {1.5, 2.0, 3.0} × ATR (mismo ATR). Cuando `sl_atr_mult` ≤ `vwap_dev_atr_mult` (p. ej. sl=1.5 con dev=1.5 o 2.0), el stop está a la misma distancia o más cerca que el propio umbral que disparó la entrada — la reversión tiene que revertir de inmediato o el SL salta primero. Esto es plausible como causa adicional del PF bajo pero **no lo puedo confirmar sin operaciones reales del motor** (no ejecuté el backtest; ver "no pude").

### Propuesta de corrección
- La parte de sesión (punto 1) se corrige junto con la Anomalía 3 (ver propuesta allí) — es la misma causa raíz de código.
- El punto 2 (relación `sl_atr_mult` vs `vwap_dev_atr_mult`) no es un bug, es un espacio de búsqueda; si se confirma con datos de operación, la corrección sería de rejilla en `mine.py` (excluir combinaciones donde `sl_atr_mult` ≤ `vwap_dev_atr_mult`), no del motor.

### ¿Regla #26?
El punto 1 (fix de sesión) **si se implementa altera las señales que produce el motor** (cambia cuándo se resetea el VWAP y cuándo se abren/cierran posiciones) → exige bump de versión + verificación de identidad 15/15. **No lo aplico.** Detalle de la propuesta en la Anomalía 3.

---

## ANOMALÍA 2 — SQUEEZE_BREAKOUT: 4 operaciones (mediana) en 50.026 barras IS

### Medición de solo lectura sobre el dataset real

Script de un solo proceso que replica exactamente `_calc_squeeze_active` (`services/validation/engine/event_backtest_engine.py:384-403`) y la rama de entrada `SQUEEZE_BREAKOUT` (`:1595-1612`) sobre las 50.026 barras IS del dataset 15m, para las 8 combinaciones de rejilla de `scripts/mine.py:361-363` (`squeeze_pct` ∈ {20,30}, `squeeze_lookback` ∈ {50,100}, `breakout_lookback` ∈ {10,20}):

```
n_is bars = 50026
squeeze_pct=20.0 lookback=50  -> n_active=13592 (27.17%) | breakout_lookback=10 -> long=893  short=644  total=1537
squeeze_pct=20.0 lookback=50  -> n_active=13592 (27.17%) | breakout_lookback=20 -> long=522  short=314  total=836
squeeze_pct=20.0 lookback=100 -> n_active=9021  (18.03%) | breakout_lookback=10 -> long=655  short=440  total=1095
squeeze_pct=20.0 lookback=100 -> n_active=9021  (18.03%) | breakout_lookback=20 -> long=428  short=226  total=654
squeeze_pct=30.0 lookback=50  -> n_active=15988 (31.96%) | breakout_lookback=10 -> long=1062 short=752  total=1814
squeeze_pct=30.0 lookback=50  -> n_active=15988 (31.96%) | breakout_lookback=20 -> long=647  short=387  total=1034
squeeze_pct=30.0 lookback=100 -> n_active=14205 (28.40%) | breakout_lookback=10 -> long=1023 short=709  total=1732
squeeze_pct=30.0 lookback=100 -> n_active=14205 (28.40%) | breakout_lookback=20 -> long=688  short=381  total=1069
```

`_calc_squeeze_active` funciona bien: el porcentaje de barras activas (18-32%) es exactamente el orden de magnitud esperado de un umbral de percentil sobre su propia ventana causal (percentil 20-30 ⇒ ~20-30% activo). **No hay bug de percentil ni de ventana** — el "estado de squeeze" por sí solo NO es el cuello de botella: genera entre 654 y 1814 EVENTOS de ruptura Donchian-durante-squeeze en 50.026 barras (esto sería de sobra para >200 operaciones OOS si se ejecutaran todos).

### Por qué llegan solo 0-16 operaciones reales (telemetría, 96 configs SQUEEZE_BREAKOUT)

```python
trades sorted: [0]*13 + [1]*11 + [3]*20 + [4] + [5]*15 + [6]*20 + [11]*8 + [16]*4
```
(datos literales de `telemetria` en el JSON de la campaña, familia SQUEEZE_BREAKOUT, 96 registros)

La caída de ~1500 eventos brutos a 0-16 operaciones ejecutadas se explica por una causa que la campaña no aisló: **la puerta de sesión `session_window` (RTH 13:30-20:00 UTC) se aplica GLOBALMENTE a TODOS los arquetipos, no solo a los "anclados a sesión"**. Evidencia de código: `services/validation/engine/event_backtest_engine.py:1039` lee `session_window = getattr(strategy, "session_window", None)` **fuera** de cualquier rama por arquetipo; `:1115` calcula `in_session` con ella para toda vela; `:1575` la usa como condición obligatoria (`... and in_session and ...`) para generar CUALQUIER señal de entrada, incluida `SQUEEZE_BREAKOUT`. Y `services/discovery/funding_discovery.py:222-228` — dentro de `generate_candidate_blueprint`, sin ninguna rama condicionada al arquetipo — resuelve y adjunta esa `session_window` a TODAS las estrategias FONDEO, incluidas `REVERSION_ATR`/`SQUEEZE_BREAKOUT`/`STREAK_EDGE`. Esto **contradice el diseño documentado**: `orchestration/reviews/diseno_arquetipos_5_14.md:34-38` solo menciona `session_window` para la familia C (`session_momentum`); las familias A (`reversion_atr`), B (`squeeze_breakout`) y D (`streak_edge`) no la mencionan — el diseño las concibió operando sin restricción horaria, pero en ejecución SÍ quedan restringidas al 13:30-20:00 UTC porque `funding_discovery` nunca deja `session_window=None`.

Repetí la medición filtrando los eventos por si su vela de fill (`i+1`, igual que el motor en `:1123-1127`) cae dentro de esa ventana RTH (lun-vie), con una simulación secuencial simplificada de "una posición a la vez":
```
bars in RTH session (13:30-20:00 UTC, Mon-Fri): 14988 / 50026 = 29.96%
pct=20.0 lb=50  brk=10: raw_events=1537 in_session_fillable=3  flat+session=2
pct=20.0 lb=50  brk=20: raw_events=836  in_session_fillable=1  flat+session=1
pct=20.0 lb=100 brk=10: raw_events=1095 in_session_fillable=10 flat+session=8
pct=20.0 lb=100 brk=20: raw_events=654  in_session_fillable=6  flat+session=6
pct=30.0 lb=50  brk=10: raw_events=1814 in_session_fillable=10 flat+session=7
pct=30.0 lb=50  brk=20: raw_events=1034 in_session_fillable=5  flat+session=5
pct=30.0 lb=100 brk=10: raw_events=1732 in_session_fillable=28 flat+session=21
pct=30.0 lb=100 brk=20: raw_events=1069 in_session_fillable=20 flat+session=18
```
Esto **reproduce el orden de magnitud exacto** de la telemetría (0-28 vs. los 0-16 medidos). La caída NO es proporcional al 30% de barras en sesión que cubre la ventana RTH (eso solo explicaría una reducción a ~460-540 eventos) — es una caída de >98%. Medí la distribución horaria de los eventos crudos (config con más eventos: pct=30, lb=100, brk=10) para explicar por qué:

```
Distribución horaria UTC de eventos squeeze+breakout:
00-07h UTC: 48,129,122,172,180,281,306,208  (1446 de 1732 eventos, 83.5%)
08-12h UTC: 75,17,25,56,65
13-20h UTC: 22,6,3,2,2,0,0,2               (37 de 1732 eventos, 2.1%)
21-23h UTC: 1,1,9
```
El "estado de squeeze" (ATR bajo) y la ruptura que lo termina se concentran de madrugada/Europa temprana (00:00-08:00 UTC — sesión asiática/pre-Londres de baja liquidez en el índice USA500), y prácticamente desaparecen entre las 13:00 y las 20:00 UTC (RTH), justo la única ventana en la que el motor permite entrar. Para cuando abre la sesión regular de NY, la mayoría de las compresiones de volatilidad ya se rompieron horas antes.

### Diagnóstico

**Mixto, con un componente de código real:**
- **Diseño/calibración** (esperado, correcto en el motor): la definición de "evento" (barra de transición, no estado persistente) es intencional (`diseno_arquetipos_5_14.md:26-28`) y correcta — sin ella habría sobre-conteo de operaciones dentro de la misma racha.
- **Desajuste diseño↔implementación** (el hallazgo real de esta anomalía): `funding_discovery.generate_candidate_blueprint` adjunta `session_window` a las 6 familias por igual — el diseño de 5.14.0 nunca pidió eso para A/B/D. Combinado con que la compresión-ruptura de USA500 ocurre mayormente fuera de RTH, el efecto es una asfixia casi total de la familia SQUEEZE_BREAKOUT específicamente (REVERSION_ATR y STREAK_EDGE sobreviven con 612 y 668 operaciones medianas pese a la misma puerta, porque sus señales sí son frecuentes dentro de RTH).

### Propuesta de corrección
En `services/discovery/funding_discovery.py:198-228`, condicionar la resolución/adjunto de `session_window` al arquetipo — por ejemplo, no pasar `session_window` (dejarlo `None`, que en `_is_in_session_window:591-592` significa "sin restricción, 24h") para `REVERSION_ATR`, `SQUEEZE_BREAKOUT` y `STREAK_EDGE`, reservándola para `SESSION_MOMENTUM`, `OPENING_RANGE_BREAKOUT` y `VWAP_REVERSION` (las 3 que sí la necesitan conceptualmente y la mencionan en su diseño/comentarios).

### ¿Regla #26?
**Sí, inequívocamente.** Cambiar si `session_window` es `None` o no para estas 3 familias cambia qué barras generan señal, qué barras permiten fill, y cuándo se fuerza el cierre EOD (`close_at_eod` heredado del mismo `resolve_session_window`) → altera directamente las operaciones que produce el motor. Exige bump de `CURRENT_ENGINE_VERSION` (o del generador `funding_discovery`, según cómo se versione ese componente) + verificación de identidad 15/15. **No lo aplico, solo lo propongo.**

---

## ANOMALÍA 3 — Ventana de sesión fija en UTC (13:30-20:00) sin ajuste por horario de verano (DST)

### Confirmación de código

`services/discovery/funding_discovery.py:37-76` (`resolve_session_window`) fija para símbolos CME (incluye `ES`, `MES`):
```python
def_start, def_end, def_days, def_close = "13:30", "20:00", [0, 1, 2, 3, 4], True
```
Un único par de horas UTC, todo el año, sin ninguna lógica de zona horaria/DST — confirmado por `grep` de `DST|daylight|zoneinfo|America/New_York` en `services/`: no aparece en `funding_discovery.py` ni en `event_backtest_engine.py`. `services/exploitation_engines/prop_firm_engine.py:18-22` documenta la MISMA limitación para otro propósito (cutoff de firmas de fondeo) con una nota explícita: *"LIMITACION CONOCIDA: es un offset fijo -- no modela el cambio EST/EDT por horario de verano"* — confirma que es un patrón conocido y ya señalado en el repo, no una sospecha nueva.

`services/validation/engine/event_backtest_engine.py:451-460` (`_session_start_minutes`) parsea literalmente `session_window.start_time_utc` ("13:30") a minutos-desde-medianoche sin ajuste estacional, y esos minutos anclan directamente:
- **OPENING_RANGE_BREAKOUT**: `:481` `start_min = self._session_start_minutes(session_window)`, usado en `:500-501` como referencia del tramo de apertura.
- **VWAP_REVERSION**: el reseteo diario del VWAP (`:538-544`, `in_sess = self._is_in_session_window(dt, session_window)`) ocurre en la primera barra dentro de esa misma ventana fija.
- **SESSION_MOMENTUM**: aquí hay un matiz — su "ancla" (`_calc_session_anchor_dir`, `:405-442`) usa `dt.hour < ancla_horas` (`:434`), es decir horas **desde medianoche UTC**, NO desde `session_window.start_time_utc` — el tramo-ancla en sí NO se desplaza con DST. Pero sus entradas SÍ están sujetas a la misma puerta `in_session` (`:1115`, `:1575`) que las otras dos, así que la VENTANA EN QUE PUEDE EJECUTAR una señal ya calculada sí se desplaza 1h en invierno.

### Medición sobre el dataset real: ¿la apertura de caja real coincide con 13:30 UTC todo el año?

Localicé, para un día de enero y uno de julio dentro del dataset, la barra de mayor `tick_count` en la ventana 11:00-17:00 UTC (proxy de actividad institucional = apertura real de caja):

```
--- DIA DE ENERO (2023-01-16, invierno) ---
barra de mayor tick_count en [11:00,17:00) UTC -> 14:30 UTC  tick_count=370 (pico claro sobre una base de ~250-300)

--- DIA DE JULIO (2023-07-17, verano) ---
barra de mayor tick_count en [11:00,17:00) UTC -> 13:30 UTC  tick_count=1092 (pico muy marcado sobre una base de ~150-250)
```
Perfil horario completo (`tick_count` sumado por vela de 15m) confirma el patrón: en julio el salto ocurre exactamente a las 13:30 UTC (de 217/184 en las velas previas a 1092, ×4-5); en enero el salto (más moderado pero visible) ocurre a las 14:30 UTC (de ~250-290 a 370), es decir **una hora después** de donde el motor asume que abre la sesión.

Esto es exactamente lo esperado: NY está en UTC-4 (EDT, horario de verano) de marzo a noviembre y en UTC-5 (EST, horario estándar) el resto del año; 9:30 ET = 13:30 UTC solo bajo EDT. `services/discovery/funding_discovery.py` usa siempre 13:30 UTC — correcto en verano, **una hora antes de la apertura real en invierno**.

### Cuantificación: ¿qué fracción del dataset está desplazada?

```python
dias totales con datos: 1141
dias en horario ESTANDAR (invierno, UTC-5, apertura real 14:30 UTC): 381 (33.4%)
dias en horario DE VERANO (DST, UTC-4, apertura real 13:30 UTC): 760 (66.6%)
```
(calculado con `zoneinfo.ZoneInfo('America/New_York')` sobre cada fecha con datos en el dataset 15m, no con una tabla propia — evita adivinar las fechas exactas de cambio de hora)

**El 33,4% de los días del dataset (1 de cada 3) tiene la ventana de sesión desplazada 1 hora respecto a la apertura real de caja.** En esos días concretos:
- El rango de apertura de `OPENING_RANGE_BREAKOUT` se mide sobre los primeros `or_minutes` (15/30/60) minutos a partir de las 13:30 UTC — es decir, sobre la última hora del tramo pre-apertura/Globex, no sobre la apertura real (14:30 UTC).
- El VWAP de `VWAP_REVERSION` se reinicia a las 13:30 UTC en vez de a las 14:30 UTC — acumula una hora "de más" de un régimen de liquidez distinto antes de que abra la sesión real.
- La ventana de entradas ejecutables (`in_session`, todas las familias) es 13:30-20:00 UTC en vez de la real 14:30-21:00 UTC (cierre NYSE 16:00 ET = 21:00 UTC en invierno): se permiten entradas una hora antes de la apertura real Y se pierde la última hora de la sesión real (20:00-21:00 UTC).

### Diagnóstico

**Bug, no calibración ni dato.** El código asume una equivalencia fija ET→UTC que solo es válida bajo DST; no hay ninguna rama estacional. Es una omisión de implementación frente a un hecho conocido del calendario (el propio repo ya documenta la misma limitación en otro módulo, `prop_firm_engine.py:18-22`), no una elección de diseño deliberada ni un problema de calidad del dato (el dataset Dukascopy en sí es correcto — el `tick_count` real confirma la apertura verdadera).

### Propuesta de corrección
`services/discovery/funding_discovery.py:resolve_session_window` debería derivar `start_time_utc`/`end_time_utc` a partir de la hora local real del mercado (p. ej. "09:30 America/New_York" → convertir a UTC POR DÍA usando `zoneinfo`, no una constante), o bien el motor debería aceptar una `session_window` expresada en zona horaria de mercado + calendario de DST y resolver el offset por fecha de cada vela en `_is_in_session_window`/`_session_start_minutes` (`services/validation/engine/event_backtest_engine.py:451-461, 588-614`) en vez de comparar contra un `"HH:MM"` UTC fijo. Cualquiera de las dos rutas toca el contrato `SessionWindow` (`contracts/canonical_strategy.py`, no verificado en este carril) y el motor.

### ¿Regla #26?
**Sí, inequívocamente — y es el cambio de mayor impacto de los tres.** Corregir el desplazamiento DST cambia, para el 33,4% de los días del dataset, qué barras cuentan como "rango de apertura", cuándo se resetea el VWAP, y qué barras son elegibles para entrar/salir en `SESSION_MOMENTUM`, `OPENING_RANGE_BREAKOUT` y `VWAP_REVERSION` — altera directamente las operaciones que produce el motor para estas 3 familias (y de rebote la Anomalía 1, que comparte esta causa). Exige bump de `CURRENT_ENGINE_VERSION` + verificación de identidad 15/15 antes de tocar una sola línea. **No lo aplico, solo lo propongo con evidencia.**

---

## Resumen

| # | Familia(s) | Diagnóstico | ¿Bug de código? | ¿Toca engine (regla #26)? |
|---|---|---|---|---|
| 1 | VWAP_REVERSION | Hipótesis de `volume` faltante REFUTADA (existe, real, no-cero). Signo y alcanzabilidad del TP correctos. Causa principal = comparte la Anomalía 3 (VWAP se resetea con la sesión fija sin DST); causa secundaria sin confirmar = posible relación SL/umbral de entrada en la rejilla de `mine.py` | Parcial (hereda el bug de Anomalía 3) | Sí, para el componente de sesión |
| 2 | SQUEEZE_BREAKOUT | `_calc_squeeze_active` correcto (18-32% de barras activas, como se espera de un percentil 20-30). El cuello de botella real: `funding_discovery` adjunta `session_window` RTH a las 6 familias por igual, contra lo que documenta el propio diseño 5.14.0 (solo pedía sesión para `session_momentum`), y la compresión-ruptura de USA500 ocurre 83,5% de las veces fuera de RTH (00-08h UTC) | Sí (desajuste diseño↔implementación en `funding_discovery.py`) | Sí |
| 3 | SESSION_MOMENTUM, OPENING_RANGE_BREAKOUT, VWAP_REVERSION | `session_window` fija 13:30-20:00 UTC todo el año, sin lógica DST; la apertura real es 14:30 UTC en invierno (confirmado con `tick_count` real del dataset). Afecta al 33,4% de los días del dataset (1141 días medidos) | Sí | Sí |

## No pude / limitaciones de este carril
- No ejecuté el motor de backtest (fuera de mi carril, "solo lectura"; además está prohibido para mí alterar/generar operaciones). Por eso el punto 2 de la Anomalía 1 (relación SL/umbral de entrada de VWAP_REVERSION) queda como hipótesis razonada, no confirmada con datos de operación — lo dejo explícito, no lo presento como hecho.
- No verifiqué `contracts/canonical_strategy.py::SessionWindow` en detalle (fuera del alcance de las 3 anomalías pedidas); lo menciono porque cualquier corrección de la Anomalía 3 lo tocaría.

## Peticiones al orquestador
- Asignar la implementación de las 2 correcciones propuestas (Anomalía 2: no adjuntar `session_window` a REVERSION_ATR/SQUEEZE_BREAKOUT/STREAK_EDGE en `funding_discovery.py`; Anomalía 3: resolver DST en `resolve_session_window`/`_is_in_session_window`) a un carril con permiso de escritura sobre el motor, con el bump de versión + verificación de identidad 15/15 que exige la regla #26 antes de tocar `event_backtest_engine.py` o `funding_discovery.py`.
- Si se prioriza, sugiero Anomalía 3 primero (afecta a 3 familias y al 33,4% de los días) y Anomalía 2 después (afecta específicamente a SQUEEZE_BREAKOUT) — ambas se pueden implementar y verificar juntas en un único bump para no gastar dos ciclos de verificación de identidad.
