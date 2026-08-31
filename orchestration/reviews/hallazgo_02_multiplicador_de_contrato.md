# HALLAZGO CRÍTICO — El motor de backtest ignoraba el multiplicador de contrato

**Hermes · 2026-08-31 · Verificado con ejecución real, no con inspección de código**

## El bug

`services/validation/engine/event_backtest_engine.py` calculaba el resultado de cada operación así:

```python
gross_pnl = (exit_price - position_entry_price) * position_qty
```

**Sin multiplicador de contrato.** Es decir, asumiendo que 1 punto de precio = 1 USD.
`grep -E "point_value|multiplier|contract_size|tick_value"` sobre el motor: **cero coincidencias**.

Correcto en cripto, donde la cantidad es fraccionaria y el nocional coincide.
**Falso en futuros:** ES vale 50 USD/punto, NQ 20, GC 100, CL 1000, SI 5000.

## Cómo se detectó

No por inspección de código, sino siguiendo un síntoma raro: las estrategias FONDEO daban
**Profit Factor ~0,30 en las cuatro temporalidades** (5m 0,26 · 15m 0,31 · 1h 0,44 · 4h 0,30).
Un sistema al azar da PF ≈ 1. Un 0,30 sistemático no es "falta de edge", es un error de medida.

Al abrir las operaciones una a una apareció la prueba:

```
operaciones=846  acierto=27,1%  ganancia_media=1,20 USD  perdida_media=-1,43 USD
primera: SHORT entrada 5196,46 salida 5200,75 -> -1,08 USD
```

Ganancia media de **1,20 USD** en una cuenta de 50.000 con 1 % de riesgo por operación (500 USD).
Y un movimiento adverso de 4,29 puntos en ES debería costar 214 USD con un contrato, o 21 con un
micro. El motor daba 1,08: equivale a **0,05 contratos**, una fracción que no existe.

## Lo más llamativo: el dato ya estaba en el repo

`services/engine/instrument_registry.py` contiene el catálogo completo y correcto:

| Símbolo | point_value | comisión CME |
| :--- | ---: | ---: |
| ES | 50,0 | 2,50 |
| MES | 5,0 | 0,60 |
| NQ | 20,0 | 2,50 |
| GC | 100,0 | 2,50 |
| CL | 1000,0 | 2,50 |
| SI | 5000,0 | 2,50 |

Y `contracts/instrument_specification.py:62` define el campo con la descripción exacta
(*"$20 para NQ, $50 para ES, $1 para Cripto"*). El motor incluso recibe
`cme_fee_per_contract_usd=2.50` en su constructor y **nunca lo usaba**.
El dato estaba; el motor no lo consultaba.

## La corrección

En los **5 puntos de salida** del motor:
- `gross_pnl` se multiplica por el `point_value` del instrumento.
- Comisión: fija por contrato ida y vuelta en futuros; porcentual en cripto.
- Slippage escalado por `point_value`.
- Si el instrumento no se resuelve, se registra un `WARNING` explícito. Cero fallback silencioso.

Copia del fichero previo en `cuarentena/event_backtest_engine_ANTES_point_value.py.bak`.

## Efecto medido (misma estrategia, mismo dataset ES 4h)

| | Antes | Después |
| :--- | ---: | ---: |
| Ganancia media | 1,20 USD | **49,97 USD** |
| Pérdida media | −1,43 USD | −52,94 USD |
| Profit Factor | 0,310 | **0,570** |
| Acierto | 27,1 % | 37,5 % |

El factor 41x concuerda con el point_value de 50 del ES.

## Qué queda invalidado

1. **Todos los backtests de futuros del sistema.** Cualquier métrica de ES, NQ, YM, RTY, GC, CL,
   SI calculada antes de hoy es incorrecta.
2. **Las 12 estrategias "certificadas" del catálogo heredado** (UR_FONDEO_CL_1H, NQ_1H, ES_4H,
   GC_1H, SI_1H, YM_4H, RTY_4H, USDCAD_4H, UR_ULTRA_GC_4H, NQ_4H, SI_4H): **todas CME**. Sus
   11 gates se evaluaron sobre P&L dimensionalmente erróneo.
3. **El análisis económico de examen de fondeo** que dio ROI +1.147 % por cartucho: partía de
   los `oos_returns` de esas mismas candidatas. **Hay que rehacerlo.**
4. La campaña de descubrimiento sobre TRADFI anterior a esta corrección.

**Sigue siendo válido:** todo lo de cripto (`point_value = 1`), incluidas las 27 candidatas ULTRA
certificadas sobre BTCUSDT 4h.

## Lección

El síntoma era "las estrategias de fondeo no tienen edge". La causa era "no sabemos medir futuros".
Antes de concluir que una estrategia es mala, hay que comprobar que la regla de medir es correcta.
