# 🛡️ Informe de Stress Test de Robustez (Variación ±10% Fricción)

Este informe evalúa el impacto de un incremento del 10% en comisiones Taker y un 10% en Slippage sobre las estrategias seleccionadas.

| ID Estrategia | Nombre | PF Base | Net Profit Base | PF Estresado (+10% Slip & Fee) | Caída PF (%) | ¿Sigue Rentable? |
|---|---|---|---|---|---|---|
| `strat_1_0_54` | Strategy 1.0.54 | 1.38 | +$134.51 | 1.28 | -7.0% | ✅ SÍ |
| `strat_1_0_32` | Strategy 1.0.32 | 1.47 | +$73.48 | 1.37 | -7.0% | ✅ SÍ |
| `strat_1_4_140` | Strategy 1.4.140 (Dual-Pass OOS) | 1.4 | +$249.38 | 1.3 | -7.0% | ✅ SÍ |
| `strat_1_0_23` | Strategy 1.0.23 (Sharpe 4.46) | 1.66 | +$366.44 | 1.54 | -7.0% | ✅ SÍ |
| `strat_1_4_125` | Strategy 1.4.125 (Bajo Drawdown) | 2.43 | +$130.36 | 2.26 | -7.0% | ✅ SÍ |
| `strat_1_4_181` | Strategy 1.4.181 (High Win Rate) | 2.15 | +$313.98 | 2.0 | -7.0% | ✅ SÍ |
