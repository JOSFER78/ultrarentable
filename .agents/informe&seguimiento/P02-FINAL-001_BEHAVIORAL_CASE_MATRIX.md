# BEHAVIORAL CASE MATRIX & DETERMINISTIC RE-RUN PROOF — ORDEN AG2-P02-FINAL-001
**Fase 02 — Canonical Strategy & Version Governance (Final Definitive Pre-Phase 03 Closure)**
**Doctrina Institucional:** ZERO-MOCKS · REAL-ONLY · DETERMINISTIC · NO-LOOKAHEAD · PROVENANCE-LOCKED · FAIL-CLOSED · ZERO-OPTIMISM
**Lead Subagente:** QUANT / REPRODUCIBILITY SPECIALIST
**Timestamp UTC:** 2026-08-25T20:25:00Z
**Veredicto:** **100% PASS (487 TRADES IDÉNTICOS BIT A BIT · HASH DETERMINISTA VERIFICADO · PARIDAD CUANTITATIVA TOTAL)**

---

## 1. Demostración Física de Re-ejecución Determinista (Step 3)

Se ejecutó la prueba automatizada de re-ejecución independiente `scratch/verify_deterministic_rerun.py` sobre el dataset físico real `NQ 1h` bajo la versión de motor SSOT `v5.4.0`:

- **Entorno de Ejecución:** VPS Ubuntu 22.04 LTS / Python 3.12.3.
- **Estrategia Evaluada:** `STRAT_DETERMINISTIC_001` (Bidireccional `BOTH`, EMA 9 cross EMA 21, SL 50 pts, TP 100 pts, Risk 1.0% Equity sobre \$100,000 USD).
- **Resultados de las Dos Ejecuciones Independientes:**
  - **Ejecución 1 (`res1`):** `execution_hash = 1f25df93cae76d7c94773b2a526c74d5e0acdc533232659273a0a67d0546182c` (487 trades).
  - **Ejecución 2 (`res2`):** `execution_hash = 1f25df93cae76d7c94773b2a526c74d5e0acdc533232659273a0a67d0546182c` (487 trades).
- **Verificación Atómica de los 487 Trades:**
  - `entry_time_ms`: 100% idénticos.
  - `exit_time_ms`: 100% idénticos.
  - `entry_price`: 100% idénticos.
  - `exit_price`: 100% idénticos.
  - `direction`: 100% idénticos (`LONG` y `SHORT`).
  - `size_contracts`: 100% idénticos.
  - `exit_reason`: 100% idénticos (`TAKE_PROFIT` y `STOP_LOSS`).
  - `pnl_usd`: 100% idénticos al centavo.
  - `pnl_r`: 100% idénticos con precisión de 64 bits.

---

## 2. Matriz Cuantitativa de Casos Físicos de Comportamiento

| ID Caso | Escenario Cuantitativo | Dirección AST | Ramas Evaluadas ($L_{sig}, S_{sig}$) | Microestructura del Instrumento | Condición de Salida F Física | PnL R Teórico | PnL USD Teórico | Regla Fail-Closed & Criterio de Verificación |
|---|---|:---:|:---:|---|---|:---:|:---:|---|
| **BOTH-A** | Señal LONG Exclusiva | `BOTH` | $L_{sig}=1, S_{sig}=0$ | CME NQ ($pt=\$20, mult=1.0$) | $High_t \ge TP_{tgt}$ ó $Low_t \le SL_{tgt}$ | $TP: +2.0R$ / $SL: -1.0R$ | $TP: +\$2,000.00$ / $SL: -\$1,000.00$ | Apertura física LONG en $Close_i$. Salida real en TP ($PnL>0$) o SL ($PnL<0$). |
| **BOTH-B** | Señal SHORT Exclusiva | `BOTH` | $L_{sig}=0, S_{sig}=1$ | BTCUSDT ($pt=\$1, mult=1.0$) | $Low_t \le TP_{tgt}$ ó $High_t \ge SL_{tgt}$ | $TP: +2.0R$ / $SL: -1.0R$ | $TP: +\$2,000.00$ / $SL: -\$1,000.00$ | Apertura física SHORT en $Close_i$. Salida real en TP ($PnL>0$) o SL ($PnL<0$). |
| **BOTH-C** | Conflicto Simultáneo (Ambas Ramas) | `BOTH` | $L_{sig}=1, S_{sig}=1$ | Cualquier Instrumento | N/A (Indeterminación) | $0.0R$ | $\$0.00$ | Neutralización Fail-Closed: $trigger\_entered = \text{False}$, $0\text{ trades}$. Cero coin-flip. |
| **BOTH-D** | Ausencia Total de Señal | `BOTH` | $L_{sig}=0, S_{sig}=0$ | Cualquier Instrumento | N/A (Inacción) | $0.0R$ | $\$0.00$ | Preservación de capital: $total\_trades = 0$. Cero aperturas espurias. |
| **SIZING-NQ** | Sizing Futuros CME NQ | Cualquier | Disparo válido | NQ ($point\_value = 20.0$) | SL alcanzado ($\Delta_{SL}=50\text{ pts}$) | $-1.0R$ | $-\$1,000.00$ | $Contracts = \frac{\$1,000}{50 \times 20 \times 1} = 1.0$. Pérdida acotada exactamente a $\$1,000$. |
| **SIZING-BTC**| Sizing Cripto BTCUSDT | Cualquier | Disparo válido | BTCUSDT ($point\_value = 1.0$)| SL alcanzado ($\Delta_{SL}=50\text{ pts}$) | $-1.0R$ | $-\$1,000.00$ | $Contracts = \frac{\$1,000}{50 \times 1 \times 1} = 20.0$. Pérdida acotada exactamente a $\$1,000$. |
| **INTRABAR-L**| Conflicto Intrabarra LONG | `LONG` / `BOTH` | Disparo LONG | NQ / BTCUSDT | $Low_t \le SL \land High_t \ge TP$ | $-1.0R$ | $-Risk_{USD}$ | Prioridad institucional pesimista (*Zero-Optimism*): Ejecuta STOP_LOSS. |
| **INTRABAR-S**| Conflicto Intrabarra SHORT | `SHORT` / `BOTH`| Disparo SHORT | NQ / BTCUSDT | $High_t \ge SL \land Low_t \le TP$ | $-1.0R$ | $-Risk_{USD}$ | Prioridad institucional pesimista (*Zero-Optimism*): Ejecuta STOP_LOSS. |

---

## 3. Conclusión Cuantitativa

Queda formalmente demostrado que:
1. Las ejecuciones en runtime son **estrictamente deterministas y reproducibles bit a bit**.
2. El dimensionamiento por riesgo normaliza con precisión matemática las diferencias de microestructura entre Futuros CME (\$20/pt) y Cripto Perpetuo (\$1/pt).
3. La resolución pesimista intrabarra elimina cualquier optimismo en la equidad histórica.
