# ESTADO DE LA VERDAD (STATE OF TRUTH) — ULTRARENTABLE
> **AUTORIDAD ÚNICA DE DOCUMENTACIÓN BASADA EN EVIDENCIA FÍSICA**
> **Última Generación Automática:** `2026-08-21 14:40:23 UTC`
> **Commit Hash:** `a013799` (`a0137997e4bf4eebe46601b141b379eea21c3e64`) | **Rama:** `main`

---

## 1. Declaración de Estado Operacional

| Dimensión | Estado Certificado | Evidencia Física / Fuente |
| :--- | :--- | :--- |
| **Doctrina** | `ZERO-MOCK / REAL-ONLY` | [AGENTS.md](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/.agents/AGENTS.md) |
| **Versión del Motor Activo** | `v1.05 — Ultrarentable V1.05 (Pure Dimensional Quant Architecture, % & R-Multiples Unification & Dynamic Git Versioning)` | [services/version_control_manager.py](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/services/version_control_manager.py) |
| **Huella Criptográfica del Motor** | `d0ea52e994f9c78f73220621...` | [data/evidence/version_manifest.json](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/data/evidence/version_manifest.json) |
| **Estado del Laboratorio** | `CERTIFICADO FORENSE / RECONCILIACIÓN CROSS-ENGINE COMPLETADA` | [data/evidence/execution_reconciliation.json](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/data/evidence/execution_reconciliation.json) |
| **Datasets Físicos Normalizados** | `112 datasets reales` | `data/normalized/*.json` con SHA-256 |
| **Estrategias en SQLite WAL** | `230 totales (v1.00: 92, v1.02: 24, v1.04: 98, v1.05: 16)` | `/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3` |
| **Suite de Tests Backend** | `236 tests pasados (100%)` | `pytest services/api/tests/ tests/` |
| **Compilación Frontend** | `33/33 rutas Next.js compiladas` | `apps/web/` (`npm run build`) |
| **Persistencia Cloud** | `Firebase RTDB (pecemi-default-rtdb)` | `/ultrarentable/engine_versions` |

---

## 2. Invariantes Canónicos del Sistema

1. **Cero Mocks y Generadores Sintéticos**: Ningún test ni motor de cálculo utiliza objetos `Mock` o generadores de velas artificiales.
2. **Capa Canónica de Ejecución (`ExecutionTruth`)**: Toda operación debe contener hashes de procedencia (`market_data_hash`, `strategy_snapshot_hash`, `execution_config_hash`) y desglose exacto de comisiones, slippage y margen.
3. **Ley de Hard Gates**: Un único fallo en los gates fundamentales (datos, costes, lookahead, OOS, DSR, leverage o reglas de fondeo) provoca el descarte inmediato e inmutable (`REJECTED`) de la estrategia.
4. **Cero Defaults Silenciosos**: Prohibido asumir `fee = 0` o `slippage = 0`. Todo activo requiere un `InstrumentCostProfile` explícito en `CANONICAL_COST_REGISTRY`.
5. **Aislamiento de Holdout**: El motor de discovery nunca tiene acceso de lectura al conjunto de datos ciego OOS (*Blind Holdout*).
6. **Control de Versiones y Huella Criptográfica**: Cada cambio estructural en el motor actualiza la huella SHA-256 del código y permite bumps atómicos con trazabilidad absoluta.

---

## 3. Matriz de Componentes y Puertos

| Servicio | Puerto / Protocolo | Archivo Principal |
| :--- | :--- | :--- |
| **FastAPI Backend Core** | `8000` (HTTP / SSE / WebSocket) | `services/api/app/main.py` |
| **Next.js Web UI** | `3000` (Dashboard & Terminal) | `apps/web/` |
| **SQLite WAL Storage** | Local File (`PRAGMA journal_mode=WAL`) | `~/.local/state/ultrarentable/ultrarentable.sqlite3` |
| **Cross-Engine Reconciler** | Interno (FastEngine vs NautilusTrader) | `services/validation/engine/cross_engine_reconciler.py` |
| **Control de Versiones Autónomo** | Interno (SSOT + Manifest) | `services/version_control_manager.py` |
