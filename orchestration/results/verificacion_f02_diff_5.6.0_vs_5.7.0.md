# VERIFICACIÓN F02 — motor 5.6.0 vs 5.7.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 325 | +0 | -57.28 | -53.40 | +3.88 | 0.860 | 0.860 | SÍ |
| ultra BTCUSDT 4h | 2 | 353 | +0 | -36.09 | -31.99 | +4.10 | 0.920 | 0.920 | SÍ |
| ultra BTCUSDT 4h | 3 | 313 | +0 | -91.13 | -87.43 | +3.70 | 0.740 | 0.740 | SÍ |
| ultra ETHUSDT 4h | 1 | 318 | +0 | -5.46 | -4.96 | +0.50 | 0.920 | 0.920 | SÍ |
| ultra ETHUSDT 4h | 2 | 371 | +0 | -5.99 | -5.26 | +0.73 | 0.940 | 0.940 | SÍ |
| ultra ETHUSDT 4h | 3 | 322 | +0 | -3.60 | -3.21 | +0.39 | 0.940 | 0.940 | SÍ |
| ultra LINKUSDT 1h | 1 | 785 | +0 | -17.16 | -15.30 | +1.86 | 0.910 | 0.910 | SÍ |
| ultra LINKUSDT 1h | 2 | 825 | +0 | -25.60 | -23.17 | +2.43 | 0.870 | 0.870 | SÍ |
| ultra LINKUSDT 1h | 3 | 759 | +0 | -11.35 | -10.00 | +1.35 | 0.920 | 0.920 | SÍ |
| fondeo ES 4h | 1 | 84 | +0 | -76.36 | -33.85 | +42.51 | 0.910 | 0.970 | SÍ |
| fondeo ES 4h | 2 | 50 | +0 | -124.25 | -105.54 | +18.71 | 0.360 | 0.400 | SÍ |
| fondeo ES 4h | 3 | 33 | +0 | -20.65 | -7.47 | +13.18 | 0.890 | 1.000 | SÍ |
| fondeo GC 4h | 1 | 49 | +0 | -289.59 | -271.00 | +18.59 | 0.370 | 0.400 | SÍ |
| fondeo GC 4h | 2 | 43 | +0 | -210.41 | -198.57 | +11.84 | 0.350 | 0.370 | SÍ |
| fondeo GC 4h | 3 | 37 | +0 | -50.73 | -39.50 | +11.23 | 0.840 | 0.890 | SÍ |

Celdas con PnL más bajo en 5.7.0: 0. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.