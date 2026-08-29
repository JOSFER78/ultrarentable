# 06 — INVENTARIO DE ACTIVOS REALES (Ultra vs Fondeo)

> Fecha: 2026-08-29 · Fuente de verdad: API SQX `:5050/call?cmd=-symbol action=list` (SOLO lectura), `docs/00_MASTER_IDEAS_Y_PLAN.md`, `canonical_instrument_aliases.json`, `services/background_searcher.py` (SEARCH_MATRIX 97 celdas), `docs/tradesfera/`, `docs/Fondeo/`.
> Temporalidades objetivo (mandato del usuario): **M1, M5, M15, H1, H4** (5 TFs).
> Convención SQX: símbolo dedicado por TF `<SYM>_<TF>`. "OK" = datos con cobertura real; "PARCIAL" = cobertura corta (ver días); "FALTA" = sin datos.

## Universo del usuario (22 activos)
- **Cripto BingX (9):** BTC, ETH, SOL, XRP, DOGE, AVAX, BNB, LINK, SUI (USDT perpetuals).
- **Futuros CME (7):** ES, NQ, YM, RTY, GC, CL, SI (los micros MES/MNQ/MYM/M2K/MGC/MCL se ejecutan en NinjaTrader/Tradovate; SQX usa el contrato base como proxy de datos).
- **Forex majors (6):** EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD.

## Fondeo (activos permitidos prop firms, según docs)
- CME: **MES/MNQ/MYM/M2K, MGC/MCL** (equivalen a ES/NQ/YM/RTY/GC/CL en SQX) + **SI** no está en el corpus de fondeo.
- **Forex: NO permitido** en las prop firms de futuros documentadas (Topstep, MFFU, Bulenox, Take Profit Trader, OneUp, Tradeify, MFF…) → 6 majors marcados ✗ en Fondeo.
- Reglas firmadas: Apex/TPT prohíben bots; Topstep prohíbe API desde VPS; MFFU/FundedNext/Tradeify/TradeDay permiten bots propios.
- Cripto: fuera de prop firms de futuros → solo vía ULTRA.

## Matriz activo × temporalidad (datos reales leídos por API SQX, 2026-08-18)

### Cripto BingX (Ultra ✓ · Fondeo ✗)
| Activo | M1 | M5 | M15 | H1 | H4 | Ultra | Fondeo |
|---|---|---|---|---|---|---|---|
| BTCUSDT | OK (2017→, 207k rec.) | PARCIAL (37 días) | PARCIAL (110 días) | OK (2023→, 25.5k) | OK (2021→) | ✓ | ✗ |
| ETHUSDT | OK (2017→, 207k) | PARCIAL (37 d) | PARCIAL (110 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| SOLUSDT | OK (2020→, 216k) | PARCIAL (37 d) | PARCIAL (110 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| XRPUSDT | OK (2018→, 357k) | PARCIAL (32 d) | PARCIAL (94 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| DOGEUSDT | OK (2019→, 268k) | PARCIAL (32 d) | PARCIAL (94 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| LINKUSDT | OK (2019→, 512k) | PARCIAL (32 d) | PARCIAL (94 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| AVAXUSDT | PARCIAL (160k rec. pero fecha "hasta" corrupta 58619) | PARCIAL (32 d) | PARCIAL (94 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| BNBUSDT | PARCIAL (101k rec., fecha "hasta" corrupta) | PARCIAL (32 d) | PARCIAL (94 d) | OK (2023→) | OK (2021→) | ✓ | ✗ |
| SUIUSDT | OK (2023→, 360k) | PARCIAL (32 d) | PARCIAL (94 d) | OK (2023→) | PARCIAL (2023→, 7.2k) | ✓ | ✗ |

### Futuros CME (Ultra ✓ · Fondeo ✓ salvo SI)
| Activo | M1 | M5 | M15 | H1 | H4 | Ultra | Fondeo |
|---|---|---|---|---|---|---|---|
| ES (MES) | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✓ |
| NQ (MNQ) | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✓ |
| YM (MYM) | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✓ |
| RTY (M2K) | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✓ |
| GC (MGC) | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✓ |
| CL (MCL) | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✓ |
| SI | FALTA | PARCIAL (72 d) | PARCIAL (72 d) | OK (2024→) | OK (2024→) | ✓ | ✗ (no en corpus prop firms) |

### Forex majors (Ultra ✓ · Fondeo ✗)
| Activo | M1 | M5 | M15 | H1 | H4 | Ultra | Fondeo |
|---|---|---|---|---|---|---|---|
| EURUSD | FALTA | PARCIAL (84 d) | PARCIAL (84 d) | OK (2023→) | OK (2023→) | ✓ | ✗ |
| GBPUSD | FALTA | PARCIAL (84 d) | PARCIAL (84 d) | OK (2023→) | OK (2023→) | ✓ | ✗ |
| USDJPY | FALTA | PARCIAL (84 d) | PARCIAL (84 d) | OK (2023→) | OK (2023→) | ✓ | ✗ |
| USDCHF | FALTA | PARCIAL (84 d) | PARCIAL (84 d) | OK (2023→) | OK (2023→) | ✓ | ✗ |
| USDCAD | FALTA | PARCIAL (84 d) | PARCIAL (84 d) | OK (2023→) | OK (2023→) | ✓ | ✗ |
| AUDUSD | FALTA | PARCIAL (84 d) | PARCIAL (84 d) | OK (2023→) | OK (2023→) | ✓ | ✗ |

## Resumen numérico (matriz 22×5 = 110 celdas)
- **Con datos OK o PARCIAL:** 97/110 celdas. **FALTA total:** 13 celdas = M1 de los 7 futuros (ES/NQ/YM/RTY/GC/CL/SI) + M1 de los 6 forex.
- Cripto M1: 7/9 OK (AVAX y BNB con metadato de fecha corrupto, verificados por nº de registros).
- M5/M15 CME+forex: solo ~2–3 meses (72–84 días) → backfill BLOQUEADO (sin fuente gratuita verificable, decisión de negocio abierta, §5 del MASTER).
- H1/H4: años de cobertura en los 22 activos → celdas listas.

## Huecos críticos
1. **M1 futuros CME (7 celdas):** cero datos en SQX (ES/NQ/YM/RTY/GC/CL/SI).
2. **M1 forex (6 celdas):** cero datos en SQX.
3. **M5/M15 CME (14 celdas):** solo ~72 días.
4. **M5/M15 forex (12 celdas):** solo ~84 días.
5. **M5/M15/M1 cripto:** 32–110 días (M1 BTC/ETH/SOL/XRP/DOGE/LINK/SUI sí tienen años).
6. **Fondeo:** forex majors (6 activos × 5 TFs) fuera de alcance; SI fuera del corpus de prop firms.
7. Metadatos corruptos: AVAXUSDT_M1 y BNBUSDT_M1 reportan "Date to" 58619.12.31 (fecha inválida; datos reales por nº de registros).
