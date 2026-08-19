# 📊 ESTADO.md — Mapa Único y Estado Vivo del Proyecto Ultrarentable

> **Última actualización:** 2026-08-19 (Cierre Forense Definitivo de las 6 Fases — 100% Real-Only)  
> **Doctrina:** REAL-ONLY / ZERO-MOCKS (100% Certificado con Batería Red-Team)  
> **Arquitectura:** DUAL-ENGINE DESACOPLADO (Ruta ULTRA / BingX vs Ruta FONDEO / Prop Firms CME)

---

## 1. Resumen Ejecutivo y Realidad Verificada

El laboratorio cuantitativo opera con una separación física y cognoscitiva estricta entre la capa de exploración (Discovery) y la capa ciego-evaluadora (11 Quantitative Gates & Certification):

1. **🔒 Cadena de Custodia Criptográfica & Particionado en 4 Etapas:**
   - Cada dataset físico en `data/normalized/` tiene su hash SHA-256 criptográfico real calculado desde los bytes en disco (`compute_file_sha256()`).
   - Particionado temporal obligatorio antes de discovery:
     - **In-Sample (60%):** Búsqueda combinatoria (400+ trials) con score multiobjetivo (PF, DD, Trades, Winrate) $\to$ Filtrado de Top 20.
     - **Validation (20%):** Desempate y selección ciega del campeón #1 sobre datos fuera de muestra de búsqueda.
     - **Freeze Snapshot:** Congelación inmutable del `StrategySnapshot` y su `canonical_hash` SHA-256 de 64 caracteres.
     - **Blind Holdout OOS (20%):** Muestra intocada donde el evaluador independiente ejecuta los 11 Gates.

2. **⚙️ Intérprete Canónico Determinista (`EventBacktestEngine`):**
   - El motor de validación parsea dinámicamente indicadores (EMAs de cualquier período, RSI Wilder recursivo, Donchian Breakouts) y reglas de salida (SL/TP ATR multipliers, risk %) directamente desde los nodos del `StrategySnapshot`.
   - Cero parámetros cableados: las variaciones en los blueprints producen cambios cuantitativos y órdenes físicamente diferentes.

3. **🛡️ Aislamiento Total de Gate 4 (Walk-Forward Optimization):**
   - Gate 4 recibe exclusivamente trades generados sobre el conjunto de desarrollo pre-OOS (`IS + Val`), protegiendo el 20% de Blind Holdout OOS de cualquier contaminación por ventana rodante.

4. **📜 Registro Forense de Trials & Intolerancia a Datos Falsos (Gates 7, 8, 9, 10, 11):**
   - **Gate 7 (Regime Coverage):** Exige `trades_raw` con timestamps físicos mapeados a regímenes ATR/Trend; bloquea ante fallbacks sintéticos.
   - **Gate 8 (Deflated Sharpe Ratio):** Si $N_{\text{trials}} \le 0$ o no está registrado en SQLite, emite `BLOCKED / NO_EVIDENCE`.
   - **Gate 9 (Anti-Curve Fit):** Re-backtesting físico de vecindario ($\pm 10\%, \pm 20\%$) re-ejecutando el motor sobre velas reales.
   - **Gate 10 (Multi-Specialist Audit):** Auditoría cuantitativa determinista de 5 especialistas independientes.
   - **Gate 11 (Cross-Validation Eventual):** Verificación independiente de margen cruzado, margen de mantenimiento, distancia a liquidación y costes de funding.

5. **📁 Evidence Ledger Criptográfico con Hashes Reales:**
   - Cada gate persiste un archivo `EvidenceRecord` en `data/evidence/{strategy_id}/gate_{i}.json`.
   - Hashes SHA-256 de 64 caracteres exactos para `strategy_snapshot_hash`, `input_hash` y `output_hash`.

---

## 2. Mapa de Servicios y Puertos en VPS

| Servicio | Puerto | Estado | URL / Proceso | Nota de Integración |
|---|---|---|---|---|
| **Web Frontend** | `5000` | 🟢 **ONLINE** | `http://127.0.0.1:5000` | Next.js 16.2.12 con interfaz reactiva 100% Real-Only |
| **API Backend** | `8000` | 🟢 **ONLINE** | `http://127.0.0.1:8000` | FastAPI + SQLite WAL + 11 Gates Modulares |
| **StrategyQuant X MCP** | `8081` | 🟢 **ONLINE** | `http://127.0.0.1:8081/mcp` | Bridge MCP conectado |
| **Discovery Daemon** | Background | 🟢 **ACTIVO** | `discovery_validation_pipeline.py` | Minería 24/7 sobre 224 datasets con particionado 60/20/20 |

---

## 3. Estado de la Suite de Pruebas

- `pytest tests/ -v` ➔ **73 passed, 1 skipped (SQX Server Offline opcional), 0 failed** (100% verificado sin mocks).
- Batería Red-Team (`tests/test_red_team_adversarial.py`) pasando 5/5 ataques de estrés y corrupción de datos con 100% de éxito.
