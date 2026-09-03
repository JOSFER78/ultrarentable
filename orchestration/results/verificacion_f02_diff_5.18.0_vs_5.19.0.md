# VERIFICACIÓN F02 — motor 5.18.0 vs 5.19.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 319 | +0 | -273.23 | -273.23 | +0.00 | 0.970 | 0.970 | no |
| ultra BTCUSDT 4h | 2 | 352 | +0 | -316.60 | -316.60 | +0.00 | 0.970 | 0.970 | no |
| ultra BTCUSDT 4h | 3 | 307 | +0 | -528.00 | -528.00 | +0.00 | 0.820 | 0.820 | no |
| ultra ETHUSDT 4h | 1 | 307 | +0 | -191.86 | -191.86 | +0.00 | 0.980 | 0.980 | no |
| ultra ETHUSDT 4h | 2 | 367 | +0 | -459.73 | -459.73 | +0.00 | 0.940 | 0.940 | no |
| ultra ETHUSDT 4h | 3 | 312 | +0 | -151.72 | -151.72 | +0.00 | 0.980 | 0.980 | no |
| ultra LINKUSDT 1h | 1 | 785 | +0 | -940.92 | -940.92 | +0.00 | 0.860 | 0.860 | no |
| ultra LINKUSDT 1h | 2 | 833 | +0 | -974.09 | -974.09 | +0.00 | 0.840 | 0.840 | no |
| ultra LINKUSDT 1h | 3 | 764 | +0 | -886.08 | -886.08 | +0.00 | 0.870 | 0.870 | no |
| fondeo ES 4h | 1 | 50 | +0 | -396.10 | -206.10 | +190.00 | 0.880 | 0.920 | SÍ |
| fondeo ES 4h | 2 | 98 | +1 | -2359.31 | -1781.97 | +577.34 | 0.850 | 0.880 | SÍ |
| fondeo ES 4h | 3 | 63 | +0 | 941.18 | 1180.58 | +239.40 | 1.160 | 1.180 | SÍ |
| fondeo GC 4h | 1 | 21 | +0 | -1040.35 | -949.15 | +91.20 | 0.060 | 0.060 | SÍ |
| fondeo GC 4h | 2 | 45 | +1 | 1076.46 | 1857.82 | +781.36 | 1.220 | 1.350 | SÍ |
| fondeo GC 4h | 3 | 41 | +0 | 1856.22 | 2042.42 | +186.20 | 1.340 | 1.360 | SÍ |

Celdas con PnL más bajo en 5.19.0: 0. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.