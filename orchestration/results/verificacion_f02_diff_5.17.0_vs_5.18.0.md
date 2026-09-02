# VERIFICACIÓN F02 — motor 5.17.0 vs 5.18.0

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
| fondeo ES 4h | 1 | 50 | +0 | -103.00 | -396.10 | -293.10 | 1.010 | 0.880 | SÍ |
| fondeo ES 4h | 2 | 97 | +71 | -543.16 | -2359.31 | -1816.15 | 0.550 | 0.850 | SÍ |
| fondeo ES 4h | 3 | 63 | +47 | 165.66 | 941.18 | +775.52 | 1.830 | 1.160 | SÍ |
| fondeo GC 4h | 1 | 21 | +0 | -787.37 | -1040.35 | -252.98 | 0.200 | 0.060 | SÍ |
| fondeo GC 4h | 2 | 44 | +27 | -678.93 | 1076.46 | +1755.39 | 0.240 | 1.220 | SÍ |
| fondeo GC 4h | 3 | 41 | +31 | -253.04 | 1856.22 | +2109.26 | 0.320 | 1.340 | SÍ |

Celdas con PnL más bajo en 5.18.0: 3. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.