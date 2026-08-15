# Matriz de Causa Raíz — 5 Errores Principales de la Configuración SQX
> Proyecto: Ultrarentable · Fecha: 2026-08-09 · Regla REAL-ONLY
> Evidencia directa del `Build-Task1.xml` (zip `Ultra_Auto_Pilot/project.cfx`) y de la BD operacional.

---

## Contexto del fracaso (dato real)
- 95 estrategias generadas en BD, 77 backtests, **0 POTENTIAL_WINNER**.
- Mejor retorno IS = 37.17% (`UR-SQX-Strategy_1.1.43`) con **OOS negativo** y DD_OOS 202%.
- Mejor WFE ≈ 0.12 (el protocolo exige ≥ 0.60).
- Firma dominante: **IS positivo/moderado → OOS negativo o ruinoso**. = sobreajuste IS.

---

## ERROR #1 — Fitness = retorno bruto (NetProfit), sin penalización de riesgo
**Evidencia XML:**
```xml
<FitnessCriteria method="ComputeFromStrategyResult"/>
<Ranking type="NetProfit"/>
```
**Diagnóstico:**
- Optimizar por retorno bruto en el rango IS ordena las curvas **más frágiles** primero: las que más compone
  sobre pocos trades, las más dependientes de outliers, las de DD enorme.
- No separa el objetivo **Ultra (perfil A)** del **Fondeo (perfil B)** → una sola métrica para dos problemas opuestos.
- El "miles de %" buscado debería salir del **sizing (Kelly)** no de la señal; no está en el espacio de búsqueda.

---

## ERROR #2 — Sin validación Out-of-Sample / Walk-Forward activa
**Evidencia XML:**
```xml
<WalkForwardOptimization use="false"/>
<WalkForwardMatrix use="false"/>
<MonteCarloRetest use="false"/>
<MonteCarloManipulation use="false"/>
<SysParamPermutation use="false"/><!-- SPP -->
<WhatIf use="false"/>
```
**Diagnóstico:**
- Solo `RetestWithHigherPrecision` está activo. No hay WFA anclado, ni Monte Carlo, ni sensibilidad de parámetros (SPP).
- Sin gate OOS, el optimizador ajusta al ruido del rango de entrenamiento. Resultado real: 24/24 fallan OOS.
- La BD además **no guarda** rango IS/OOS ni serie de trades → ni siquiera se puede certificar WFE/MC a posteriori.

---

## ERROR #3 — Ventana de datos corta y estrecha (un símbolo, un timeframe)
**Evidencia XML:**
```xml
<Symbol name="BTCUSDT_AUTO" timeframe="H1" uSymbol="BTCUSDT" uSymbolName="Binance USDT-M"
        dateFrom="2026.02.26" dateTo="2026.8.4"/>
```
**Diagnóstico:**
- Rango ≈ **5.2 meses** de un único activo (BTC 1h). Muestra insuficiente para estimar CAGR estable ni para
  distinguir edge de régimen puntual.
- Sin multi-instrumento ni multi-timeframe → sin test de degradación graciosa cross-mercado.
- Un retorno de 4 dígitos sobre 5 meses casi siempre es compounding de pocos trades = ruido, no edge.

---

## ERROR #4 — Costes irreales: spread=0 y baja fricción
**Evidencia XML (setup principal):**
```xml
<Setup testPrecision="1" ... slippage="1" engine="MetaTrader4">
  <Chart symbol="BTCUSDT_AUTO" timeframe="H1" spread="0"/>
  <Commissions><Method type="PercentageBased" use="true"> CommissionPct=0.05 </Method>
```
**Diagnóstico:**
- **Spread = 0** en el chart principal → sistemas tipo HFT/pelea de tick "ganan" en simulación y mueren en real.
- Slippage mínimo (1) y comisión baja (0.05%) → sobreestimación sistemática del net.
- Sin spread variable por sesión ni slippage estresado → los costes no representan fricción real.
- Nota: el setup residual de fondeo (`EURUSD_M1_dukas`, spread=2, 2003→2019) sí tiene fricción, pero es un setup
  separado y NO es el que alimenta el ranking principal.

---

## ERROR #5 — Sin filtros de sesión ni de régimen de mercado
**Evidencia:** no existe ningún bloque de filtrado de sesión (Londres/NY) ni de régimen (ATR/ADX/volatilidad) en el XML.
**Diagnóstico:**
- La estrategia opera en TODO tiempo, incluidas sesiones de baja liquidez/alto spread (Asia) y compresiones (whipsaw).
- Sin apagar en regímenes sin edge (rango con ADX<20, vol extrema), la estrategia acumula pérdidas que el optimizador
  "compensa" subiendo sizing sobre la parte rentable → más sobreajuste.
- El MEMO A/B identifica los filtros de sesión como **la mayor ganancia por complejidad** — ausentes hoy.

---

## Resumen priorizado
| # | Error | Gravedad | Impacto real observado |
|---|---|---|---|
| 1 | Fitness NetProfit sin DD/estabilidad | 🔴 P0 | Curvas frágiles, ranking premia overfit |
| 2 | Sin OOS/WFA/MonteCarlo/SPP | 🔴 P0 | 24/24 candidatos fallan OOS |
| 3 | Rango corto (5.2m) + 1 símbolo | 🟠 P1 | Muestra insuficiente, sin generalización |
| 4 | Spread=0 / fricción baja | 🟠 P1 | HFT fantasma, net sobreestimado |
| 5 | Sin filtros sesión/régimen | 🟡 P2 | Opera en regímenes sin edge, más overfit |

*Documento de evidencia propia del orquestador. Coherente con el informe profundo del agente 1 (03_diagnostico_plantilla_sqx_real.md).*
