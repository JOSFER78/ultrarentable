# AUDITORIA LECTURA FASE 0 — Código, Servicios y Tests (Agente B)

> **Proyecto:** Ultrarentable (Trading Cuantitativo Multi-Motor)  
> **Fecha de auditoría:** 2026-08-15  
> **Doctrina:** REAL-ONLY (verificado contra ejecución real en VPS)  
> **Auditor:** Agente B (Código y Servicios)

---

## 1. Inventario de Árbol de Código

### A. Frontend (`apps/web/`)
- **Framework:** Next.js 16.2.12 (App Router) + React 19.2.4 + TypeScript.
- **Rutas Principales:**
  - `app/page.tsx` (Buscador SQX / Telemetría / Panel Principal)
  - `app/dashboard/` (Dashboard General de Métricas)
  - `app/ultra/` (Modo Ultrarentable — BingX Perps)
  - `app/fondeo/` & `app/prop-firms/` (Modo Fondeo y Catálogo de 34 Firmas)
  - `app/strategies/` & `app/backtest/` (Estrategias y Backtesting determinista)
  - `app/campaigns/` (Gestión de Campañas evolutivas)
  - `app/data/` (Gestión de Datasets y Manifiestos de Calidad)
  - `app/strategyquant/` (Monitor del servidor SQX MCP)
  - `app/leaderboard/` (Leaderboard de estrategias aprobadas)
  - `app/research/` (Repositorio de fuentes de investigación)
- **Proxy inverso configurado:** `next.config.ts` reenvía `/api/:path*` ➔ `http://127.0.0.1:8000/api/:path*`.

### B. Backend (`services/api/`)
- **Framework:** FastAPI 3.0.0 + SQLAlchemy + SQLite WAL (`~/.local/state/ultrarentable/ultrarentable.sqlite3`).
- **Módulos Core:**
  - `app/dsl/`: Compilador y validador de DSL determinista con hash canónico SHA256.
  - `app/engine/`: `fast_engine.py` (motor determinista aproximado), `ledger.py` (contabilidad precisa), `margin_model.py` (cálculo de margen y liquidación con reglas reales de BingX).
  - `app/factory/`: Algoritmo genético, `campaign_pipeline.py`, `quality_gates.py`, `adversarial_validation.py`.
  - `app/ingestion/`: Pipeline de datos y clientes BingX (`client.py`, `eth_pipeline.py`).
  - `app/api/`: Rutas REST (`routes.py`, `sqx_router.py`, `prop_firms.py`).
  - `services/sqx_bridge/`: Cliente y conversor de databanks SQX.

---

## 2. Suite Canónica de Tests (`services/api/tests/`)

Ejecución verificada con `pytest services/api/tests/ -v`:
- **Total recolectados:** 130 tests
- **PASSED:** 125 tests (0.00% fallos)
- **SKIPPED:** 5 tests (pruebas de red directa contra endpoints privados de BingX que requieren `RUN_LIVE_BINGX_TESTS=1`)
- **FAILED:** 0 tests
- **Tiempo de ejecución:** 8.15 segundos

---

## 3. Estado Real de Servicios y Puertos en el VPS

| Puerto | Servicio Asociado | Estado Verificado | Respuesta Real |
|---|---|---|---|
| **5000** | Next.js Frontend (`ultrarentable-web`) | 🟢 **ACTIVO** | `HTTP/1.1 200 OK` (sirviendo UI y proxyeando API) |
| **8000** | FastAPI Backend (`ultrarentable-api`) | 🟢 **ACTIVO** | `HTTP/1.1 200 OK` (`/api/v1/status` reporta `ONLINE`, WAL activo, 1.051 contratos BingX) |
| **8080** | Proceso Python externo (`MoneyPrinterTurbo`, PID 84200) | ⚠️ **OCUPADO POR OTRO SERVICIO** | `405 Method Not Allowed` al intentar conectar MCP SQX |
| **5050** | Web UI SQX | 🔴 **OFFLINE** | Conexión rechazada (SQX systemd parado) |
| **3000** | Antiguo puerto Next.js | ℹ️ **Liberado** | Migrado a puerto 5000 |

---

## 4. Modos Ultra vs Fondeo en el Código

- **En Frontend (`page.tsx`):**
  - Existe un toggle `cfgMode`: `"ultra"` (con `targetMultiplier`, por defecto 1000x) vs `"fondeo"` (con `maxDrawdownPct`, por defecto 15%, y `consistencyTarget`, por defecto 85%).
  - La opción "Ultra" está actualmente accesible como tab principal.
- **En Backend (`routes.py` y `quality_gates.py`):**
  - `quality_gates.py` evalúa de forma diferenciada: en modo `fondeo` penaliza drawdowns destructivos (rechaza cualquier perfil ruinoso o con pobre Calmar), mientras que en modo `ultra` toleraba drawdowns más agresivos si no eran liquidación total.

---

## 5. Deudas Técnicas Identificadas

1. **Conflicto en puerto 8080:** La API FastAPI busca el MCP de StrategyQuant en `http://localhost:8080/mcp`, pero en el host el puerto 8080 está tomado por un servicio independiente (`MoneyPrinterTurbo`).
2. **Servicio SQX en systemd:** `strategyquantx.service` fue deshabilitado (`ExecStart=/usr/bin/false`). Para ejecutar SQX se requiere lanzar el binario directamente con su entorno X virtual o ajustar el servicio.
3. **Modo Ultra Activo en UI:** Se requiere congelar el switch y la opción "Ultra" para que el usuario no pueda lanzar configuraciones kamikaze de 1000%.
