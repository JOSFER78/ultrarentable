# VERIFICACIÓN F02 — motor 5.11.0 vs 5.12.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 319 | +0 | -326.97 | -281.12 | +45.85 | 0.950 | 0.970 | SÍ |
| ultra BTCUSDT 4h | 2 | 352 | +0 | -384.17 | -322.74 | +61.43 | 0.950 | 0.970 | SÍ |
| ultra BTCUSDT 4h | 3 | 307 | +0 | -556.22 | -534.35 | +21.87 | 0.810 | 0.820 | SÍ |
| ultra ETHUSDT 4h | 1 | 307 | +0 | -234.24 | -197.95 | +36.29 | 0.970 | 0.980 | SÍ |
| ultra ETHUSDT 4h | 2 | 367 | +0 | -496.79 | -460.46 | +36.33 | 0.930 | 0.940 | SÍ |
| ultra ETHUSDT 4h | 3 | 312 | +0 | -187.28 | -157.56 | +29.72 | 0.970 | 0.980 | SÍ |
| ultra LINKUSDT 1h | 1 | 785 | +12 | -866.30 | -941.56 | -75.26 | 0.900 | 0.860 | SÍ |
| ultra LINKUSDT 1h | 2 | 833 | +11 | -960.74 | -974.11 | -13.37 | 0.870 | 0.840 | SÍ |
| ultra LINKUSDT 1h | 3 | 764 | +11 | -815.37 | -886.79 | -71.42 | 0.900 | 0.870 | SÍ |
| fondeo ES 4h | 1 | 50 | +0 | -103.00 | -103.00 | +0.00 | 1.010 | 1.010 | no |
| fondeo ES 4h | 2 | 26 | +0 | -543.16 | -543.16 | +0.00 | 0.550 | 0.550 | no |
| fondeo ES 4h | 3 | 16 | +0 | 165.66 | 165.66 | +0.00 | 1.830 | 1.830 | no |
| fondeo GC 4h | 1 | 21 | +0 | -787.37 | -787.37 | +0.00 | 0.200 | 0.200 | no |
| fondeo GC 4h | 2 | 17 | +0 | -678.93 | -678.93 | +0.00 | 0.240 | 0.240 | no |
| fondeo GC 4h | 3 | 10 | +0 | -253.04 | -253.04 | +0.00 | 0.320 | 0.320 | no |

Celdas con PnL más bajo en 5.12.0: 3. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.