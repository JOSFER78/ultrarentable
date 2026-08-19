# 📊 ESTADO.md — Mapa Único y Estado Vivo del Proyecto Ultrarentable

> **Última actualización:** 2026-08-19 (Cierre Forense Integral y Erradicación de los 6 Bloqueantes)  
> **Doctrina:** REAL-ONLY / ZERO-MOCKS (100% Certificado)  
> **Arquitectura:** DUAL-ENGINE DESACOPLADO (Ruta ULTRA / BingX vs Ruta FONDEO / Prop Firms CME)

---

## 1. Resumen Ejecutivo y Realidad Verificada

El laboratorio cuantitativo opera con una separación estricta entre la capa de exploración (Discovery) y la capa ciego-evaluadora (11 Quantitative Gates & Certification):

1. **🔒 Cadena de Custodia Criptográfica y Particionado Ciego Inmutable (Bloqueantes 1 & 2):**
   - Cada dataset físico en `data/normalized/` tiene su hash SHA-256 criptográfico real calculado desde los bytes en disco (`compute_file_sha256()`).
   - Particionado temporal obligatorio antes de discovery:
     - **In-Sample (60%):** Búsqueda combinatoria y optimización algorítmica.
     - **Validation (20%):** Selección y ajuste fino de parámetros.
     - **Blind Holdout OOS (20%):** Partición intocada y congelada donde el juez independiente ejecuta los 11 Gates.

2. **📜 Registro Forense de Trials y DSR Estricto (Bloqueante 5):**
   - Cada hipótesis explorada en In-Sample se registra en la tabla `discovery_search_trials` de SQLite (`ultrarentable.sqlite3`).
   - Gate 8 (Deflated Sharpe Ratio de Bailey & López de Prado) evalúa con el recuento exacto de trials registrados físicamente. Cero fallbacks inventados: si $N_{\text{trials}} \le 0$, el gate emite `BLOCKED / NO_EVIDENCE_TRIALS_UNRECORDED`.

3. **⏱️ Mapeo Temporal Real de Regímenes (Bloqueante 3 - Gate 7):**
   - Eliminada cualquier asignación proporcional. Cada trade físico generado por `EventBacktestEngine` se cruza temporalmente mediante su timestamp exacto (`entry_time_ms`) con el régimen activo de la vela (BULL, BEAR, CHOP, HIGH_VOL).

4. **🔬 Anti-Curve Fit con Re-Backtest Real de Vecindario (Bloqueante 4 - Gate 9):**
   - Eliminadas las estimaciones sintéticas. Gate 9 instancia variantes perturbadas ($\pm 10\%$, $\pm 20\%$) y re-ejecuta `EventBacktestEngine` sobre las velas reales para medir la estabilidad empírica del vecindario.

5. **⚙️ Validación Cruzada Orientada a Eventos (Bloqueante 6 - Gate 11):**
   - Simulación orden a orden de margen cruzado, margen de mantenimiento, apalancamiento pico real ($\text{nominal}/\text{equity}$), distancia mínima a liquidación forzada y costes de funding.

6. **📁 Artefactos de Evidencia Física en Disco (`EvidenceRecord`):**
   - Cada gate genera un archivo JSON en `data/evidence/{strategy_id}/gate_{i}.json` con hashes SHA-256 de entrada y salida, auditables en cualquier momento.

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

- `pytest tests/ -v` ➔ **67 passed, 1 skipped (SQX Server Offline opcional), 0 failed** (100% verificado sin mocks).
- Todos los endpoints de auditoría y controladores REST devuelven respuestas coherentes y matemáticamente reproducibles.
