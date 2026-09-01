# ANÁLISIS — Elección de timeframe: coste por operación vs. presupuesto de trades OOS

Fecha: 2026-08-31T21:45:58Z · Autor: orquestador (Hermes) · Motor vigente: 5.14.0
Reproducible: `.venv/bin/python scripts/herramientas/analisis_tf_coste_vs_trades.py`
Fuentes REAL-ONLY: `data/normalized/*.json` (Binance, 100 % cobertura, 0 gaps) y
`data/registry/bingx_friction.json` (SHA-256 `563b9b1917bcf89881ae577bff8605822f197dafa38d260fb666c21dd8e765d5`).

## Por qué este análisis

El universo de campaña (`scripts/cola_mineria.py:38`) fija 4h con este razonamiento:
*"4h primero, único TF donde el edge sobrevive al coste por operación con el motor actual"*.
Es cierto, pero **ignora la otra restricción del criterio 1.1 SELLADO: ≥200 trades OOS**.
El censo F01 lo confirma: las 4 candidatas `APPROVED_CURRENT_ENGINE` no cayeron por mal edge,
cayeron por `trades_oos` de **15, 20, 23 y 24**.

Las dos restricciones tiran en direcciones opuestas y hay que satisfacer LAS DOS a la vez.

## Restricción A — presupuesto de trades OOS

Split real del pipeline (`scripts/mine.py:608-612`): **IS 60 % / Val 20 % / Blind OOS 20 %**.

| TF | Barras totales | Barras Blind OOS | Ritmo necesario para 200 trades OOS | Veredicto |
| :--- | ---: | ---: | :--- | :--- |
| 4h | 10.500 | 2.100 | 1 trade cada **10,5 barras** (42 h) | al límite de lo posible |
| 15m | 198.528 | 39.706 | 1 trade cada **198 barras** (~2 días) | holgado |
| 5m | 595.584 | 119.117 | 1 trade cada **596 barras** (~2 días) | holgado |

En 4h haría falta estar en mercado casi permanentemente con trades de ~10 barras de media.
No es imposible para `streak_edge` con SL ajustado, pero es el caso extremo, no el típico.
(SUIUSDT 4h sólo tiene 7.220 barras → 1.444 OOS → 1 trade cada 7,2 barras: descartable.)

## Restricción B — coste por operación

Coste round-trip = 1 spread completo + 2 comisiones taker (5 bps/lado). Medido sobre el tramo
Blind OOS real, ATR(14) mediano como % del precio:

| Símbolo | TF | Barras OOS | ATR% mediano | Coste% RT | Coste/ATR | **% de un TP de 4 ATR que sobrevive** |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | 5m | 119.117 | 0,1379 | 0,1004 | 72,8 % | **81,8 %** |
| BTCUSDT | 15m | 39.706 | 0,2611 | 0,1004 | 38,4 % | **90,4 %** |
| BTCUSDT | 4h | 2.100 | 1,2163 | 0,1004 | 8,3 % | **97,9 %** |
| ETHUSDT | 5m | 119.117 | 0,2126 | 0,1012 | 47,6 % | **88,1 %** |
| ETHUSDT | 15m | 39.706 | 0,4001 | 0,1012 | 25,3 % | **93,7 %** |
| ETHUSDT | 4h | 2.100 | 1,7218 | 0,1012 | 5,9 % | **98,5 %** |
| SOLUSDT | 5m | 119.117 | 0,2530 | 0,1107 | 43,8 % | **89,1 %** |
| SOLUSDT | 15m | 39.706 | 0,4646 | 0,1107 | 23,8 % | **94,0 %** |
| SOLUSDT | 4h | 2.100 | 1,9627 | 0,1107 | 5,6 % | **98,6 %** |
| DOGEUSDT | 5m | 119.117 | 0,2589 | 0,1849 | 71,4 % | **82,1 %** |
| DOGEUSDT | 15m | 39.706 | 0,4765 | 0,1849 | 38,8 % | **90,3 %** |
| DOGEUSDT | 4h | 2.100 | 2,0300 | 0,1849 | 9,1 % | **97,7 %** |
| XRPUSDT | 5m | 119.117 | 0,2185 | 0,1439 | 65,9 % | **83,5 %** |
| XRPUSDT | 15m | 39.706 | 0,4019 | 0,1439 | 35,8 % | **91,0 %** |
| XRPUSDT | 4h | 2.100 | 1,6562 | 0,1439 | 8,7 % | **97,8 %** |

Traducción a PF: el coste erosiona el PF bruto aproximadamente en la proporción de la última
columna. Un PF bruto de 1,40 queda en ~1,27 en 15m, pero en ~1,15-1,25 en 5m — es decir,
**en 5m el propio coste hunde por debajo del umbral PF OOS ≥1,25 a una estrategia que en 15m
sí certificaría**.

## Conclusión: 15m es el único punto que satisface AMBAS restricciones

| TF | Trades OOS suficientes | Coste tolerable | Apto |
| :--- | :---: | :---: | :---: |
| 4h | ✗ (2.100 barras) | ✓ (98 %) | no |
| **15m** | **✓ (39.706 barras)** | **✓ (90-94 %)** | **sí** |
| 5m | ✓ (119.117 barras) | ✗ (82-89 %) | marginal |

**Nada de esto relaja el criterio 1.1, que sigue SELLADO.** Es una decisión de dónde gastar CPU:
minar 4h bajo un criterio de ≥200 trades OOS es aritméticamente estéril salvo en el caso
extremo de trades de ~10 barras.

## Prioridad de campaña que se deriva

1. **15m, los 9 pares cripto** (9 celdas × 420 configs = 3.780 backtests). Prioridad máxima.
2. **5m sólo en BTC/ETH/SOL** (los de coste/ATR más bajo: 44-48 %); DOGE (71 %) y XRP (66 %)
   en 5m son sangría de comisiones.
3. **4h como diagnóstico barato** (10.500 barras, muy rápido): sirve para MEDIR la frecuencia
   real de trades por familia, no para esperar certificadas. Si `streak_edge` resultara operar
   cada ~8 barras, 4h volvería a la mesa con evidencia.

## Riesgo verificado y CERRADO

`spread_median_pct` se interpreta aquí como **porcentaje**, y es lo correcto: el motor hace
`_half_spread_frac = (spread_median_pct / 100.0) / 2.0` en
`services/validation/engine/event_backtest_engine.py:580`. La comisión también:
`self.taker_fee = taker_fee_pct / 100.0` (línea 220, default 0,05 → 5 bps).

Las "unidades mixtas" que advierte CLAUDE.md son reales pero están bien tratadas: `funding_mean`
SÍ viene en fracción (BTC 4,26e-05 ≈ 0,0043 % por periodo) y el motor lo consume directo, sin
dividir (línea 891). Es decir, spread en % y funding en fracción, cada uno con su conversión
correcta. **La tabla de costes de arriba es válida.**
