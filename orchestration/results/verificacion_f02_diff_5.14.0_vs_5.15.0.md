# VERIFICACIÓN F02 — motor 5.14.0 vs 5.15.0

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
| fondeo ES 4h | 1 | 50 | +0 | -103.00 | -103.00 | +0.00 | 1.010 | 1.010 | no |
| fondeo ES 4h | 2 | 26 | +0 | -543.16 | -543.16 | +0.00 | 0.550 | 0.550 | no |
| fondeo ES 4h | 3 | 16 | +0 | 165.66 | 165.66 | +0.00 | 1.830 | 1.830 | no |
| fondeo GC 4h | 1 | 21 | +0 | -787.37 | -787.37 | +0.00 | 0.200 | 0.200 | no |
| fondeo GC 4h | 2 | 17 | +0 | -678.93 | -678.93 | +0.00 | 0.240 | 0.240 | no |
| fondeo GC 4h | 3 | 10 | +0 | -253.04 | -253.04 | +0.00 | 0.320 | 0.320 | no |

Celdas con PnL más bajo en 5.15.0: 0. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.