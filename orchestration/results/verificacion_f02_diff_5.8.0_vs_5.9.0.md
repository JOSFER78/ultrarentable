# VERIFICACIÓN F02 — motor 5.8.0 vs 5.9.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 319 | -6 | -53.40 | -51.59 | +1.81 | 0.860 | 0.870 | SÍ |
| ultra BTCUSDT 4h | 2 | 352 | -1 | -31.99 | -14.25 | +17.74 | 0.920 | 0.990 | SÍ |
| ultra BTCUSDT 4h | 3 | 307 | -6 | -87.43 | -96.28 | -8.85 | 0.740 | 0.720 | SÍ |
| ultra ETHUSDT 4h | 1 | 307 | -11 | -4.96 | -0.89 | +4.07 | 0.920 | 1.010 | SÍ |
| ultra ETHUSDT 4h | 2 | 367 | -4 | -5.26 | -4.37 | +0.89 | 0.940 | 0.960 | SÍ |
| ultra ETHUSDT 4h | 3 | 312 | -10 | -3.21 | -1.19 | +2.02 | 0.940 | 0.990 | SÍ |
| ultra LINKUSDT 1h | 1 | 773 | -12 | -15.30 | -15.83 | -0.53 | 0.910 | 0.900 | SÍ |
| ultra LINKUSDT 1h | 2 | 822 | -3 | -23.17 | -26.93 | -3.76 | 0.870 | 0.840 | SÍ |
| ultra LINKUSDT 1h | 3 | 753 | -6 | -10.00 | -14.26 | -4.26 | 0.920 | 0.870 | SÍ |
| fondeo ES 4h | 1 | 0 | +0 | 0.00 | 0.00 | +0.00 | 0.000 | 0.000 | no |
| fondeo ES 4h | 2 | 0 | +0 | 0.00 | 0.00 | +0.00 | 0.000 | 0.000 | no |
| fondeo ES 4h | 3 | 0 | +0 | 0.00 | 0.00 | +0.00 | 0.000 | 0.000 | no |
| fondeo GC 4h | 1 | 0 | +0 | 0.00 | 0.00 | +0.00 | 0.000 | 0.000 | no |
| fondeo GC 4h | 2 | 0 | +0 | 0.00 | 0.00 | +0.00 | 0.000 | 0.000 | no |
| fondeo GC 4h | 3 | 0 | +0 | 0.00 | 0.00 | +0.00 | 0.000 | 0.000 | no |

Celdas con PnL más bajo en 5.9.0: 4. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.