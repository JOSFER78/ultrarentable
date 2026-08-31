# VERIFICACIÓN F02 — motor 5.7.0 vs 5.8.0

| Celda | cfg | trades | Δtrades | PnL viejo | PnL nuevo | ΔPnL | PF viejo | PF nuevo | ledger cambió |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| ultra BTCUSDT 4h | 1 | 325 | +0 | -53.40 | -53.40 | +0.00 | 0.860 | 0.860 | no |
| ultra BTCUSDT 4h | 2 | 353 | +0 | -31.99 | -31.99 | +0.00 | 0.920 | 0.920 | no |
| ultra BTCUSDT 4h | 3 | 313 | +0 | -87.43 | -87.43 | +0.00 | 0.740 | 0.740 | no |
| ultra ETHUSDT 4h | 1 | 318 | +0 | -4.96 | -4.96 | +0.00 | 0.920 | 0.920 | no |
| ultra ETHUSDT 4h | 2 | 371 | +0 | -5.26 | -5.26 | +0.00 | 0.940 | 0.940 | no |
| ultra ETHUSDT 4h | 3 | 322 | +0 | -3.21 | -3.21 | +0.00 | 0.940 | 0.940 | no |
| ultra LINKUSDT 1h | 1 | 785 | +0 | -15.30 | -15.30 | +0.00 | 0.910 | 0.910 | no |
| ultra LINKUSDT 1h | 2 | 825 | +0 | -23.17 | -23.17 | +0.00 | 0.870 | 0.870 | no |
| ultra LINKUSDT 1h | 3 | 759 | +0 | -10.00 | -10.00 | +0.00 | 0.920 | 0.920 | no |
| fondeo ES 4h | 1 | 0 | -84 | -33.85 | 0.00 | +33.85 | 0.970 | 0.000 | SÍ |
| fondeo ES 4h | 2 | 0 | -50 | -105.54 | 0.00 | +105.54 | 0.400 | 0.000 | SÍ |
| fondeo ES 4h | 3 | 0 | -33 | -7.47 | 0.00 | +7.47 | 1.000 | 0.000 | SÍ |
| fondeo GC 4h | 1 | 0 | -49 | -271.00 | 0.00 | +271.00 | 0.400 | 0.000 | SÍ |
| fondeo GC 4h | 2 | 0 | -43 | -198.57 | 0.00 | +198.57 | 0.370 | 0.000 | SÍ |
| fondeo GC 4h | 3 | 0 | -37 | -39.50 | 0.00 | +39.50 | 0.890 | 0.000 | SÍ |

Celdas con PnL más bajo en 5.8.0: 0. Criterio del plan: al añadir fricción el
P&L debe bajar; si no baja, el motor nuevo no modela fricción de verdad.