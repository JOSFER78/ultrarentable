# VERIFICACIÓN F02 — motor 5.9.0 vs 5.10.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 319 | +0 | -51.59 | -326.97 | -275.38 | 0.870 | 0.950 | SÍ |
| ultra BTCUSDT 4h | 2 | 352 | +0 | -14.25 | -384.17 | -369.92 | 0.990 | 0.950 | SÍ |
| ultra BTCUSDT 4h | 3 | 307 | +0 | -96.28 | -556.22 | -459.94 | 0.720 | 0.810 | SÍ |
| ultra ETHUSDT 4h | 1 | 307 | +0 | -0.89 | -234.24 | -233.35 | 1.010 | 0.970 | SÍ |
| ultra ETHUSDT 4h | 2 | 367 | +0 | -4.37 | -496.79 | -492.42 | 0.960 | 0.930 | SÍ |
| ultra ETHUSDT 4h | 3 | 312 | +0 | -1.19 | -187.28 | -186.09 | 0.990 | 0.970 | SÍ |
| ultra LINKUSDT 1h | 1 | 773 | +0 | -15.83 | -866.30 | -850.47 | 0.900 | 0.900 | SÍ |
| ultra LINKUSDT 1h | 2 | 822 | +0 | -26.93 | -960.74 | -933.81 | 0.840 | 0.870 | SÍ |
| ultra LINKUSDT 1h | 3 | 753 | +0 | -14.26 | -815.37 | -801.11 | 0.870 | 0.900 | SÍ |
| fondeo ES 4h | 1 | 51 | +51 | 0.00 | -574.91 | -574.91 | 0.000 | 1.030 | SÍ |
| fondeo ES 4h | 2 | 26 | +26 | 0.00 | -3935.61 | -3935.61 | 0.000 | 0.520 | SÍ |
| fondeo ES 4h | 3 | 16 | +16 | 0.00 | 1298.00 | +1298.00 | 0.000 | 1.880 | SÍ |
| fondeo GC 4h | 1 | 27 | +27 | 0.00 | -11807.88 | -11807.88 | 0.000 | 0.230 | SÍ |
| fondeo GC 4h | 2 | 26 | +26 | 0.00 | -6514.47 | -6514.47 | 0.000 | 0.500 | SÍ |
| fondeo GC 4h | 3 | 17 | +17 | 0.00 | -4020.55 | -4020.55 | 0.000 | 0.500 | SÍ |

Celdas con PnL más bajo en 5.10.0: 14. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.