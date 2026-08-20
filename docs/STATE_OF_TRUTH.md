# ESTADO DE LA VERDAD (STATE OF TRUTH) — ULTRARENTABLE
> **AUTORIDAD ÚNICA DE DOCUMENTACIÓN BASADA EN EVIDENCIA FÍSICA**
> **Última Generación Automática:** `2026-08-20 07:24:11 UTC`
> **Commit Hash:** `cc4032e` (`cc4032e5f1e6d01bc27d8397bc072db45cd2f227`) | **Rama:** `main`

---

## 1. Declaración de Estado Operacional

| Dimensión | Estado Certificado | Evidencia Física / Fuente |
| :--- | :--- | :--- |
| **Doctrina** | `ZERO-MOCK / REAL-ONLY` | [AGENTS.md](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/.agents/AGENTS.md) |
| **Versión del Motor Activo** | `v1.02 (Zero-Simulation Forensic)` | [services/engine_version.py](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/services/engine_version.py) |
| **Estado del Laboratorio** | `EN REPARACIÓN FORENSE / RECONCILIACIÓN P0` | [docs/STATE_OF_TRUTH.md](file:///home/ubuntu/workspace/pro/trading/01%20Ultrarentable/docs/STATE_OF_TRUTH.md) |
| **Datasets Físicos Normalizados** | `112 datasets reales` | `data/normalized/*.json` con SHA-256 |
| **Estrategias en SQLite WAL** | `190 totales (v1.02: 98, v1.00 Legacy: 92)` | `/home/ubuntu/.local/state/ultrarentable/ultrarentable.sqlite3` |
| **Suite de Tests Backend** | `204 tests pasados (100%)` | `pytest services/api/tests/ tests/` |
| **Compilación Frontend** | `33/33 rutas Next.js compiladas` | `apps/web/` (`npm run build`) |
| **Persistencia Cloud** | `Firebase RTDB (pecemi-default-rtdb)` | `/ultrarentable/engine_versions` |

---

## 2. Invariantes Canónicos del Sistema

1. **Cero Mocks y Generadores Sintéticos**: Ningún test ni motor de cálculo utiliza objetos `Mock` o generadores de velas artificiales.
2. **Capa Canónica de Ejecución (`ExecutionTruth`)**: Toda operación debe contener hashes de procedencia (`market_data_hash`, `strategy_snapshot_hash`, `execution_config_hash`) y desglose exacto de comisiones, slippage y margen.
3. **Ley de Hard Gates**: Un único fallo en los gates fundamentales (datos, costes, lookahead, OOS, DSR, leverage o reglas de fondeo) provoca el descarte inmediato e inmutable (`REJECTED`) de la estrategia.
4. **Cero Defaults Silenciosos**: Prohibido asumir `fee = 0` o `slippage = 0`. Todo activo requiere un `InstrumentCostProfile` explícito.
5. **Aislamiento de Holdout**: El motor de discovery nunca tiene acceso de lectura al conjunto de datos ciego OOS (*Blind Holdout*).

---

## 3. Matriz de Componentes y Puertos

| Servicio | Puerto / Protocolo | Archivo Principal |
| :--- | :--- | :--- |
| **FastAPI Backend Core** | `8000` (HTTP / SSE / WebSocket) | `services/api/app/main.py` |
| **Next.js Web UI** | `3000` (Dashboard & Terminal) | `apps/web/` |
| **SQLite WAL Storage** | Local File (`PRAGMA journal_mode=WAL`) | `~/.local/state/ultrarentable/ultrarentable.sqlite3` |
| **Firebase Realtime DB** | Cloud RTDB (`pecemi-default-rtdb`) | `services/api/app/api/firebase_sync_router.py` |

---
*Documento autogenerado por `scripts/generate_state_of_truth.py`. Prohibida la edición manual.*
