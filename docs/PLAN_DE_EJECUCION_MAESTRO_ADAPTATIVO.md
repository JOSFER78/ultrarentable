# Plan de Ejecución Maestro Adaptativo — Ultrarentable V2 (2026)

> **Directiva Fundamental:** REAL-ONLY. Cero datos simulados, cero mocks, cero arrays inventados. Toda la operativa se alimenta de series de velas reales de BingX USD-M Perpetuals y Futuros CME, contratos Pydantic v2 inmutables, eventos del bus asíncrono y firmas SHA-256 de procedencia.

---

## 🗺️ Mapa de Fases Evolutivas del Sistema

| Fase | Título de la Fase | Estado | Alcance Técnico |
| :--- | :--- | :---: | :--- |
| **FASE 0** | **Saneamiento Base & Contratos Pydantic v2** | `COMPLETADA` | Limpieza de imports, modelos inmutables `contracts/` y 45 tests en verde. |
| **FASE 1** | **Data Ingestor Multi-Venue & Snapshots Deterministas** | `COMPLETADA` | Ingesta real BingX/CME, verificación de gaps, `DatasetRepository` y `DataWorker`. |
| **FASE 2** | **Bridge Activo StrategyQuant X & Ingestor Canónico** | `SIGUIENTE` | Cliente JSON-RPC :8081, streaming de proyectos SQX y traducción a `CanonicalStrategy`. |
| **FASE 3** | **Arnés FastEngine Masivo & Golden Tests Bit a Bit** | `PENDIENTE` | Backtest determinista 1R margen aislado, slippage real y `FastBacktestWorker`. |
| **FASE 4** | **Semantic AI Closed Loop & Failure DB Explorer** | `PENDIENTE` | 5 agentes IA, mutaciones anti-sobreajuste y catálogo de 11 firmas de fallos. |
| **FASE 5** | **Quant Validation Fabric Dual & Promoción FSM** | `PENDIENTE` | Compuertas `FondeoEvidenceGate` vs `UltraEvidenceGate` y `CandidateRegistry`. |
| **FASE 6** | **Portfolio HRP/ERC & Ultra Bala Hyper-Scaling** | `PENDIENTE` | Matriz UTC multiactivo, piramidación 40% House Money y Bóveda Ratchet. |
| **FASE 7** | **Paper Sandbox 14 Días & Live Execution Router** | `PENDIENTE` | Incubación en vivo, detección de drift $\le 30\%$ y envío de órdenes a BingX/CME. |

---

## 📌 Historial de Fases Ejecutadas

### [x] FASE 1: Data Ingestor Multi-Venue & Snapshots Deterministas (COMPLETADA)
- **Objetivo:** Implementar la ingesta y auditoría matemática de datos reales (BingX Crypto y CME Futures), carga determinista de datasets con manifests criptográficos SHA-256 y partición IS (70%) / OOS (30%) libre de sesgo retrospectivo.
- **Acciones Ejecutadas:**
  1. **`services/data/dataset_repository.py`:**
     - Consolidado el repositorio desacoplado con carga y parsing directo de archivos `data/normalized/*.json`.
     - Generación determinista de `DatasetSnapshot` con hash SHA-256 inmutable de 64 caracteres.
     - Partición matemática estricta IS / OOS sobre el volumen temporal de velas.
  2. **`services/data/market_ingestor.py`:**
     - `MarketDataAuditor`: Detección automática y corrección de velas fuera de orden, eliminación de duplicados, conteo de gaps temporales y cálculo de porcentaje de cobertura (`coverage_pct`).
     - `MarketDataIngestor`: Normalización y persistencia de datasets `.json` y manifests `_manifest.json` con metadatos completos y timestamps UTC.
  3. **Verificación de Tests:**
     - Creado `tests/test_data_pipeline.py` (4 tests unitarios de integridad y auditoría).
     - Ejecución de `pytest tests/ -v` arrojando **49 tests PASSED, 1 SKIPPED, 0 FAILED**.

---

### [ ] FASE 2: Bridge Activo StrategyQuant X & Ingestor Canónico (SIGUIENTE)
- **Objetivo:** Conectar el generador genético masivo SQX (:8081 JSON-RPC) hacia `CanonicalStrategy` Pydantic v2 en streaming a través del `SQXWorker`.
