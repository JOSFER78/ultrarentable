# VERIFICACIÓN F02 — motor 5.10.0 vs 5.11.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 319 | +0 | -326.97 | -326.97 | +0.00 | 0.950 | 0.950 | no |
| ultra BTCUSDT 4h | 2 | 352 | +0 | -384.17 | -384.17 | +0.00 | 0.950 | 0.950 | no |
| ultra BTCUSDT 4h | 3 | 307 | +0 | -556.22 | -556.22 | +0.00 | 0.810 | 0.810 | no |
| ultra ETHUSDT 4h | 1 | 307 | +0 | -234.24 | -234.24 | +0.00 | 0.970 | 0.970 | no |
| ultra ETHUSDT 4h | 2 | 367 | +0 | -496.79 | -496.79 | +0.00 | 0.930 | 0.930 | no |
| ultra ETHUSDT 4h | 3 | 312 | +0 | -187.28 | -187.28 | +0.00 | 0.970 | 0.970 | no |
| ultra LINKUSDT 1h | 1 | 773 | +0 | -866.30 | -866.30 | +0.00 | 0.900 | 0.900 | no |
| ultra LINKUSDT 1h | 2 | 822 | +0 | -960.74 | -960.74 | +0.00 | 0.870 | 0.870 | no |
| ultra LINKUSDT 1h | 3 | 753 | +0 | -815.37 | -815.37 | +0.00 | 0.900 | 0.900 | no |
| fondeo ES 4h | 1 | 50 | -1 | -574.91 | -103.00 | +471.91 | 1.030 | 1.010 | SÍ |
| fondeo ES 4h | 2 | 26 | +0 | -3935.61 | -543.16 | +3392.45 | 0.520 | 0.550 | SÍ |
| fondeo ES 4h | 3 | 16 | +0 | 1298.00 | 165.66 | -1132.34 | 1.880 | 1.830 | SÍ |
| fondeo GC 4h | 1 | 21 | -6 | -11807.88 | -787.37 | +11020.51 | 0.230 | 0.200 | SÍ |
| fondeo GC 4h | 2 | 17 | -9 | -6514.47 | -678.93 | +5835.54 | 0.500 | 0.240 | SÍ |
| fondeo GC 4h | 3 | 10 | -7 | -4020.55 | -253.04 | +3767.51 | 0.500 | 0.320 | SÍ |

Celdas con PnL más bajo en 5.11.0: 1. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.