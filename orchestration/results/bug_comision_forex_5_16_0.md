# BUG CRÍTICO — el forex se cobraba con comisión de bolsa CME (corregido en 5.16.0)

Fecha: 2026-09-01 · Track: FONDEO · Motor: 5.15.0 → **5.16.0**
Detectado por el orquestador durante la línea base de la campaña FONDEO 1h.

## Síntoma

Las 6 celdas de forex de la campaña daban un embudo `{'IS': 348}`: las 348 configuraciones
morían en in-sample sin generar ni 5 operaciones. Medido directamente sobre
`data/normalized/ds_trad_eurusd_1h_*.json` (10.341 barras IS, capital 50.000 USD, riesgo
0,5-4 %):

```
REVERSION_ATR      trades=3  pnl= -53.838 $
SQUEEZE_BREAKOUT   trades=3  pnl= -70.113 $
SESSION_MOMENTUM   trades=3  pnl= -67.413 $
STREAK_EDGE        trades=3  pnl= -53.181 $
```

Perder 53.000-70.000 USD de un capital de 50.000 en **3 operaciones** con riesgo del 0,5-4 %
es aritméticamente imposible. Los futuros (ES vía MES) en las mismas condiciones daban 30-177
operaciones y pérdidas de magnitud normal: el fallo era **específico de forex**.

## Causa raíz

En `services/validation/engine/event_backtest_engine.py`, la clasificación del instrumento se
hacía por un umbral numérico sobre el multiplicador:

```python
es_futuro = point_value != 1.0
```

`InstrumentRegistry` da a las divisas `point_value = 10.0` (convención de mercado: 10 USD por
pip y lote estándar), que es un dato **correcto**. Pero ese `!= 1.0` hace que el motor clasifique
el forex como contrato CME liquidado en bolsa, y eso activa la rama de comisión fija
(`_comision`):

```python
return (self.cme_fee * qty) if es_futuro else (precio_fill * qty * self.taker_fee)
```

`cme_fee` son 2,50 USD **por unidad de `qty`**, bajo el supuesto "1 unidad = 1 contrato". En
forex, representar ~50.000 USD de nocional con `point_value = 10` exige `qty` del orden de
miles. La aritmética del desastre:

```
comisión = 2,50 $ × 4.677 unidades = 11.692 $ POR LADO
PnL bruto de la operación = ±30-100 $
```

Desglose real de las 3 operaciones de EURUSD antes del arreglo:

| # | qty | entry | exit | PnL bruto | **comisión** | PnL neto | salida |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 1 | 4.677 | 1,06905 | 1,06973 | +32,1 | **11.692,5** | −11.670,4 | TAKE_PROFIT |
| 2 | 4.680 | 1,06825 | 1,06668 | −73,3 | **11.700,0** | −11.783,2 | STOP_LOSS |
| 3 | 2.741 | 1,07079 | 1,07135 | −15,3 | **6.852,5** | −6.873,7 | SESSION_EOD |

Obsérvese la operación 1: **cierra en take profit con beneficio bruto y aun así pierde 11.670 USD**.

**El dimensionamiento por riesgo y el stop loss eran correctos.** La hipótesis inicial del
orquestador (SL que no corta o sizing desbocado) queda refutada por estos números: el 100 % del
problema estaba en la rama de comisión.

## Corrección

`es_futuro` pasa a derivarse de la clase de activo real de la especificación, no de un umbral
sobre el multiplicador:

```python
es_futuro = getattr(_spec, "asset_class", None) == AssetClass.CME_FUTURES
```

No se tocó `InstrumentRegistry`: el `point_value = 10.0` del forex es correcto. El defecto era
de **clasificación en el motor**, no de datos.

## Efecto medido (EURUSD IS, REVERSION_ATR)

| | 5.15.0 | 5.16.0 |
| :--- | ---: | ---: |
| operaciones | 3 | **313** |
| comisiones | 60.490 $ | 1.565 $ |
| PnL neto | −60.572 $ (quiebra) | −8.529 $ (17 % DD) |
| Profit factor | 0,00 | 0,38 |

Comprobado en las 6 divisas × 4 arquetipos: 100-447 operaciones, PF 0,24-0,96, pérdidas de
500-13.000 USD sobre 50.000 — mismo orden de magnitud que los futuros.

## Regla #26

`CURRENT_ENGINE_VERSION` 5.15.0 → **5.16.0** con entrada en `VERSION_HISTORY`. Verificación de
identidad `scripts/verificacion_f02.py --comparar 5.15.0 5.16.0`: **las 15 celdas de referencia
salen IDÉNTICAS** (Δtrades +0, ΔPnL +0,00, ledger sin cambios). Es el resultado que predice la
aritmética: ninguna celda de referencia es forex, y ES/GC (vía MES/MGC) ya tenían
`asset_class = CME_FUTURES`, así que su clasificación no varía.
Evidencia: `orchestration/results/verificacion_f02_diff_5.15.0_vs_5.16.0.md`.

## Consecuencias para las campañas

- Las 6 celdas de **forex** minadas con ≤5.15.0 producen resultados **inválidos**: hay que
  re-minarlas. Ya re-encoladas con perfil `amplio` sobre el motor 5.16.0.
- Las celdas de **futuros** (ES, NQ, YM, RTY, GC, CL) son **válidas**: su clasificación no
  cambia entre 5.15.0 y 5.16.0, como confirma la verificación de identidad. Su resultado de
  0 certificadas es un veredicto honesto, no un artefacto.
