# Viabilidad medida del puente SQX -> motor honesto (CUELLO 5)

**Fecha**: 2026-09-01
**Script**: `scripts/herramientas/inventario_sqx.py`
**Evidencia bruta**: `orchestration/results/inventario_sqx_histograma.json` (histograma completo, 2035/2035 ficheros procesados, 0 errores)
**Comando de reproducción**:
```
nice -n 19 ionice -c 3 python3 scripts/herramientas/inventario_sqx.py \
  --dir "/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/databanks/ToImprove" \
  --out orchestration/results/inventario_sqx_histograma.json
```

## Veredicto en una frase

**Hoy, 0 de las 2035 estrategias del lote es traducible al motor sin tocarlo**, y no es un
problema de "faltan dos o tres indicadores": el motor (`event_backtest_engine.py`) no
interpreta árboles de reglas — despacha una lista **fija de 8 patrones de señal
hardcodeados** (cruce EMA rápida/lenta, umbral RSI, ruptura estilo Donchian, y las 4 familias
EVENTO de 5.14.0). El lote usa 14 familias de indicador distintas (Keltner, Bollinger, MACD,
Ichimoku, Parabolic SAR, Regresión Lineal, ATR, Medias Móviles con lógica de estado "abrió por
encima tras abrir por debajo"...) — **ninguna de esas familias existe hoy en el intérprete del
motor**, y dos tercios del lote además las combina 2 o más a la vez por AND (ver §3). Abrir el
carril exige construir primero un intérprete genérico de árbol de reglas (hoy no existe) y
luego, encima, las familias de indicador — no es "añadir una primitiva", es escribir el
motor de reglas que hoy no está.

## 1. El lote real (localizado, no supuesto)

Los `.sqx` **no están en el repo** (`data/sqx_imports/`, `data/sqx_exports/` solo contienen
CSVs de precio y un export de resultados). El lote real vive en la instalación de SQX:

```
/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/databanks/ToImprove/*.sqx
```

- **2035 ficheros**, 172 MB, todos `Strategy X.Y.Z.sqx`.
- Es el único databank con `.sqx` de verdad entre los 9 proyectos de SQX en disco (Retester,
  Builder, backups, Ultra_Matrix(2), PortfolioMaster, Optimizer, PortfolioComposer,
  Ultra_Auto_Pilot solo tienen carpetas `Results/` vacías de `.sqx`).
- Coincide 1:1 con `data/sqx_exports/toimprove_2026-08-31.csv` (2035 filas de datos + cabecera):
  ese CSV es el export de resultados de este mismo databank. Dato relevante para el veredicto
  final: la columna `# of trades (OOS)` de esas filas es sistemáticamente ~0-2 (p.ej. "2", "2"
  en las dos primeras filas) — confirma en datos el bug de "OOS decorativo" ya diagnosticado en
  `scripts/herramientas/generar_sqx_fondeo.py`. El "edge" que SQX reporta en IS para este lote
  no está verificado ni siquiera por el propio SQX fuera de muestra.

## 2. Formato `.sqx`

Confirmado: es un ZIP/JAR. Contenido de un fichero típico:

| Entrada | Tamaño típico | Contenido |
|---|---|---|
| `strategy_Portfolio.xml` | ~20-85 KB | Árbol de reglas completo (lo que se parsea) |
| `settings.xml` / `lastSettings.xml` | 36-156 KB | Configuración de builder/optimizer, no de la estrategia |
| `Results/.../dailyEquity.bin`, `orders.bin` | ~13 KB / ~0.5 KB | Resultados de SQX (no se usan; el motor honesto recalcula) |
| `META-INF/MANIFEST.MF`, `version.txt` | trivial | Metadatos JAR |

`strategy_Portfolio.xml` describe: `MoneyManagement`, `GlobalSLPT`, un árbol `Rules/Events/
Event[OnBarUpdate]` con `Rule type="Signal"` (variables booleanas de señal) y `Rule
type="IfThen"` (entradas/salidas), y bloques `Variables`/`Datas`. Cada nodo de regla es un
`<Item key="..." mI="..." categoryType="..." returnType="...">`; las primitivas cuantificables
son sus atributos `key` (regla específica) y `mI` (familia de indicador).

## 3. Histograma real de primitivas (2035/2035 ficheros, 0 errores)

Estructura uniforme en el 100% del lote — es un solo run de generación de SQX, no una mezcla
heterogénea:

| Campo estructural | Valor | Cobertura |
|---|---|---|
| `engine` | `MetaTrader4` | 100% |
| `MoneyManagement` | `FixedSize` | 100% |
| Tipo de orden de entrada | `EnterAtStop` (única) | 100% — nunca `EnterAtMarket`/`EnterAtLimit` |
| Precio de entrada | `Price.UseFormula` (anclado a un indicador, no a un offset fijo) | 100% |
| Filtro de sesión/horario | — | **0%** (ninguno de los 2035 usa filtro de sesión) |
| Gestión de posición en salida | `MarketPositionIsLong/Short` + `CloseAllPositions` | 100% |
| SL/TP | `SLPT.ATRBasedValue` (ambas piernas, con periodo de ATR propio por pierna) | 100% |
| Trailing stop **activo** (no `None`) | `RangeLevel.FixedValue` o `RangeLevel.ATRBasedValue` | ~51% de los ficheros (26,0% + 24,6%) |

Familias de indicador (atributo `mI`) usadas en las condiciones de entrada/salida, por
cobertura de ficheros:

| Familia | Ficheros | % del lote | ¿La reconoce el motor hoy? |
|---|---:|---:|---|
| KeltnerChannel | 699 | 34,3% | No |
| MovingAverage | 693 | 34,1% | Solo el número "período de EMA", no la lógica real |
| BollingerBands | 580 | 28,5% | No |
| MACD | 500 | 24,6% | No |
| LinearRegression (+ LinReg) | 394 | 19,4% | No |
| ATR (condición, no exit) | 225 | 11,1% | No (y el ATR interno del motor es fijo a 14 barras) |
| Ichimoku | 195 | 9,6% | No |
| ParabolicSAR | 155 | 7,6% | No |
| Highest/Lowest/HighestIndex/LowestIndex (ruptura) | 192 | 9,4% | Parcial — el motor tiene un heurístico Donchian genérico, no esta forma exacta |
| MTKeltnerChannel | 105 | 5,2% | No |

Distribución real de cuántas familias de indicador distintas combina cada estrategia
(excluyendo `StrategyControl`, que es estructural y aparece en el 100% de los ficheros por
razones ajenas al vocabulario de la señal — es el chequeo "¿hay posición abierta?" antes de
cerrar, no una condición de entrada):

| Familias de indicador combinadas | Ficheros | % del lote |
|---:|---:|---:|
| 1 (una sola familia, ej. solo Keltner) | 682 | 33,5% |
| 2 | 1048 | 51,5% |
| 3 | 261 | 12,8% |
| 4 | 43 | 2,1% |
| 5 | 1 | 0,05% |

Es decir: un tercio del lote usaría en teoría una sola familia de indicador si esa familia
estuviera implementada (aunque seguiría exigiendo el intérprete genérico de §4 y la lógica de
estado de sus reglas finas); los otros dos tercios combinan 2 o más por AND — de ahí que la
tabla de rentabilidad de §5 no sea una simple suma de coberturas individuales, sino un
*set-cover* real. 87 reglas de condición finas distintas (p.ej.
`MABarOpensAboveAfterOpenBelow`, `IchimokuKumoBreakoutBullish`, `BBBarClosesAboveDown`,
`KCUpperRising`, `MACDSignalFalling`, `PSARBarLower`...) y 13 bloques de indicador-valor
(usados como ancla de precio de entrada o de un `Formula`, no como condición booleana).
Histograma completo (todas las 87+13 primitivas finas, con `n_ficheros`/`n_total`) en
`orchestration/results/inventario_sqx_histograma.json`.

## 4. Cruce con lo que el motor y el generador saben expresar HOY

Este es el hallazgo que decide el veredicto. Se inspeccionó
`services/discovery/funding_discovery.py::generate_candidate_blueprint` (generador de
blueprints para FONDEO) y `services/validation/engine/event_backtest_engine.py` (motor
honesto que ejecuta los 11 gates).

**El generador de blueprints** reconoce 8 arquetipos con nombre fijo: `MEAN_REVERSION`/
`RSI_REVERSION`, `TREND_FOLLOWING`/`EMA_CROSS`, `RSI_MOMENTUM`/`MOMENTUM_RSI`, y las 4
familias EVENTO de 5.14.0 (`REVERSION_ATR`, `SQUEEZE_BREAKOUT`, `SESSION_MOMENTUM`,
`STREAK_EDGE`). Todos se construyen a partir únicamente de `EMA` y `RSI` como
`IndicatorSpec`.

**El motor**, en la rama que ejecuta cualquier arquetipo anterior a 5.14.0 (líneas
~734-786 y ~1500-1530 de `event_backtest_engine.py`), no evalúa el árbol de condiciones que
recibe: **extrae de él solo tres números** — período de EMA rápida, período de EMA lenta,
período/umbral de RSI, y opcionalmente un `lookback` de ruptura si detecta la palabra
"DONCHIAN" — y con esos tres números reconstruye **su propia señal sintética**:

```python
cruce_alcista = (ema_fast_prev <= ema_slow_prev) and (ema_fast_val > ema_slow_val)
long_signal = cruce_alcista and breakout_long and rsi_long_ok
```

Es decir: **da igual qué árbol de reglas reciba** — Bollinger, Keltner, Ichimoku, MACD,
Parabolic SAR, regresión lineal, lógica de estado "abrió por encima tras abrir por debajo"...
todo eso se descarta en silencio y el motor ejecuta uno de sus 8 patrones fijos. Traducir un
`.sqx` a un `StrategySnapshot` que "pase" por el motor no reproduciría la estrategia real:
reproduciría una de 8 plantillas EMA/RSI/breakout con los números que el traductor lograra
extraer, mientras el resto de la lógica del árbol original se tira.

Gaps adicionales confirmados en el propio motor, más allá del intérprete de condiciones:

- **ATR de periodo fijo**: el motor calcula un único ATR interno a 14 barras hardcodeado
  (`atr[i] = np.mean(tr[i-14:i])`); el lote SQX usa periodos de ATR *distintos por pierna*
  (ejemplo medido: SL con ATR(32), TP con ATR(12), Trailing con ATR(70) en la misma
  estrategia) — el motor no tiene forma de expresar eso aunque tuviera un intérprete genérico.
- **Sin precio de entrada por fórmula**: el 100% del lote ancla el precio de la orden
  `EnterAtStop` a un valor de indicador (`Price.UseFormula`); `ExitModel`/las órdenes del
  motor no tienen concepto de "precio de entrada = f(indicador)", solo entrada a mercado
  implícita por el arquetipo. (Nota aparte: `GlobalSLPT` está inactivo por defecto
  (`type="fixed"`, valor 0) en el fichero de muestra inspeccionado a mano — no se generalizó
  ese dato a los 2035 porque no aporta al veredicto; el SL/TP real vive en
  `#StopLoss.StopLoss#`/`#ProfitTarget.ProfitTarget#`, que sí se midió al 100% vía
  `formula_exit`.)
- **Sin trailing stop real**: `ExitModel.trail_after_r` es "mover a BE tras N múltiplos de R"
  (un salto único); ~51% del lote usa un trailing *continuo* ATR-based o de pips fijos con
  nivel de activación propio (`TrailingStop.TrailingStop` + `TrailingStop.TrailingActivation`)
  — no existe ese mecanismo en el motor.

## 5. Qué haría falta, ordenado por rentabilidad (cuántas estrategias desbloquea cada pieza)

**Prerrequisito no negociable, coste 0 estrategias desbloqueadas por sí solo pero
bloqueante para el 100%**: escribir un intérprete genérico de árbol de reglas booleano
(AND/OR/NOT anidado sobre condiciones de indicador) dentro del motor, sustituyendo el
despachador de 8 arquetipos fijos para las condiciones de entrada/salida. Sin esto,
implementar indicadores nuevos no desbloquea nada — solo les da al motor un número más
que ignorar.

Con ese intérprete ya construido, el orden de rentabilidad de añadir familias de indicador
(*greedy set-cover* sobre las combinaciones reales del lote — cada paso es la familia que
desbloquea el máximo de estrategias NUEVAS dado lo ya implementado):

| Paso | Familia a implementar | Estrategias que desbloquea (acumulado) | % lote (acumulado) |
|---:|---|---:|---:|
| 1 | KeltnerChannel | 177 | 8,7% |
| 2 | MovingAverage | 381 | 18,7% |
| 3 | BollingerBands | 688 | 33,8% |
| 4 | MACD | 986 | 48,5% |
| 5 | LinearRegression | 1213 | 59,6% |
| 6 | ATR | 1358 | 66,7% |
| 7 | Ichimoku | 1531 | 75,2% |
| 8 | ParabolicSAR | 1681 | 82,6% |
| 9 | HighestIndex | 1784 | 87,7% |
| 10 | MTKeltnerChannel | 1888 | 92,8% |
| 11 | LinReg (variante corta) | 1966 | 96,6% |
| 12 | LowestIndex | 2017 | 99,1% |
| 13-14 | Highest, Lowest | 2035 | 100% |

Lectura: con el intérprete genérico + las **primeras 5 familias** (Keltner, Moving Average,
Bollinger, MACD, Regresión Lineal) se cubriría el 59,6% del lote. Las 9 familias restantes
tienen retorno marginal decreciente y rápido (las últimas 4 juntas desbloquean <4%). Esto
NO incluye todavía: el intérprete de estado ("abrió por encima tras abrir por debajo",
~87 variantes finas de regla dentro de esas familias), el ATR por pierna con periodo propio,
el precio de entrada por fórmula, ni el trailing stop continuo — cada uno de esos es trabajo
adicional transversal a todas las familias, no una fila más en esta tabla.

## 6. Veredicto sobre si el carril merece la inversión

**Con los datos medidos, no es "añadir 2-3 primitivas" — es escribir un intérprete de reglas
genérico que hoy no existe, más ~10 familias de indicador, más ATR paramétrico por pierna,
más precio de entrada por fórmula, más trailing stop continuo, para poder ejecutar con
fidelidad este lote concreto.** Ese es un proyecto de motor, no un puente. Y aun haciéndolo:

- El propio SQX reporta este lote con OOS decorativo (2 trades OOS típico) — el "edge" IS que
  se traduciría no está siquiera pre-validado por SQX fuera de muestra, así que el suelo de
  candidatas realmente prometedoras dentro del lote es desconocido hasta que se re-genere con
  el fix de `generar_sqx_fondeo.py` (Setup único por Build-Task + rango OOS anidado).
- Todas las 2035 estrategias comparten símbolo/TF (`AUDUSD_H1`) y motor (`MetaTrader4`) — es
  un solo run de un generador aleatorio de SQX, no una colección curada; el volumen (2035) no
  implica 2035 ideas independientes, implica una combinatoria de ~14 familias de indicador
  bien determinadas.
- Recomendación: **no abrir el carril de traducción genérica todavía**. Si se quiere
  capitalizar SQX como fuente de estrategias (doctrina vigente del proyecto), el camino más
  barato y coherente con REAL-ONLY es al revés de lo que hace este lote: usar
  `scripts/herramientas/generar_sqx_fondeo.py` (ya corregido) para que SQX *vuelva a construir*
  candidatas sobre datasets FONDEO con OOS real, y limitar el vocabulario de SQX en el
  `project.cfx` de origen a las primitivas que el motor YA soporta (EMA, RSI, ruptura estilo
  Donchian) en vez de traducir después un vocabulario de 14 familias que el motor no entiende.
  Eso convierte "SQX como fuente" en trabajo de configuración (barato, ya con precedente en el
  repo) en vez de en un intérprete de reglas nuevo (caro, con riesgo de introducir bugs de
  fidelidad silenciosos exactamente del tipo que la Regla 26 existe para atrapar).

## Ficheros de esta entrega

- `scripts/herramientas/inventario_sqx.py` — parser reutilizable (ZIP + XML), sin dependencias
  fuera de la librería estándar.
- `orchestration/results/inventario_sqx_histograma.json` — histograma completo (100 primitivas
  finas con `n_ficheros`/`pct_lote`/`n_total`), fuente de las tablas de este informe.
- `orchestration/results/viabilidad_puente_sqx.md` — este informe.
