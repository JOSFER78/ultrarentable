# 📊 ESTADO.md — Mapa Único y Estado Vivo del Proyecto

> **Última actualización:** 2026-08-15 (Reestructuración Integral Dual-Engine Completada)  
> **Doctrina:** REAL-ONLY · **Arquitectura:** DUAL-ENGINE DESACOPLADO (ULTRA · BingX vs FONDEO · Prop Firms CME)

---

## 1. Resumen Ejecutivo y Realidad Verificada

El sistema opera con dos rutas estrictamente desacopladas, validadas mediante endpoints API reales, base de datos SQLite WAL y UI interactiva de 8 pantallas:

1. **🔥 RUTA ULTRA (BingX Perpetuals · Capital Propio):**
   - Aviso de riesgo obligatorio: *Laboratorio de alto riesgo para BingX Perpetuals. No es una estrategia de fondeo ni una promesa de rentabilidad.*
   - Conector BingX: Demo SIM activo (1.051 contratos reconocidos).
   - Dataset en disco: 3.840 barras H1 de `BTCUSDT_AUTO` (26-feb a 4-ago 2026, 5,2 meses).
   - Ejecución Live: Bloqueada por defecto por guardarraíl de capital.

2. **🛡️ RUTA FONDEO (Prop Firms CME · Cuentas Financiadas):**
   - Regla de gobernanza: *Pipeline conservador para evaluar estrategias contra reglas de una firma. Un candidato BTC no se puede ejecutar en CME sin validación específica.*
   - Catálogo de Proveedores: 6 firmas versionadas en SQLite con reglas verificadas de fuentes oficiales (Topstep Combine 50K, TradeDay 50K, Apex 50K, FundedNext Futures 50K, Take Profit Trader 50K, Bulenox 50K).
   - Clasificación Canónica de Candidatas:
     - `Strategy 1.0.54`: 🔴 **`RECHAZADA_FONDEO_DD`** (DD OOS = 10.18% > límite 4.0% de fondeo).
     - `Strategy 1.0.32`: 🟡 **`INVESTIGACION_BTC`** (Candidata sobre BTC H1 de 5,2 meses. Requiere validación específica en dataset CME MES/MNQ, DD intrabar y paper trading previo).

---

## 2. Mapa de Servicios y Puertos en VPS

| Servicio | Puerto | Estado | URL / Proceso | Nota de Integración |
|---|---|---|---|---|
| **Web Frontend** | `5000` | 🟢 **ONLINE** | `http://127.0.0.1:5000` | Next.js 16.2.12 con 8 rutas canónicas y proxy `/api` |
| **API Backend** | `8000` | 🟢 **ONLINE** | `http://127.0.0.1:8000` | FastAPI 3.1.0 + SQLite WAL con 6 routers modulares |
| **StrategyQuant X MCP** | `8081` | 🟢 **ONLINE** | `http://127.0.0.1:8081/mcp` | Jetty MCP Bridge conectado y respondiendo |
| **SQX Web UI** | `8081` | 🟢 **ONLINE** | `http://127.0.0.1:8081/` | Web GUI embebida de SQX |
| **Proceso Externo** | `8080` | 🟡 **OCUPADO** | `MoneyPrinterTurbo` (PID 84200) | Motivo por el cual SQX usa el puerto 8081 |

---

## 3. Estado de Pantallas Oficiales Web (`apps/web`)

1. `GET /` ➔ **Control Center**: Tarjetas grandes ULTRA vs FONDEO con avisos obligatorios y telemetría en vivo.
2. `GET /ultra` ➔ **Wizard ULTRA**: 5 pasos con estados (`PENDIENTE`, `BLOQUEADO`, `EJECUTANDO`, `EXITO`).
3. `GET /fondeo` ➔ **Wizard FONDEO**: 8 pasos con bloqueo preventivo ante ausencia de dataset CME.
4. `GET /prop-firms` ➔ **Catálogo de Prop Firms**: Tabla filtrable con reglas versionadas y badges `VERIFIED` / `UNVERIFIED`.
5. `GET /candidatos` ➔ **Scorecards**: Registro de candidatas con métricas IS/OOS/WFO y diagnósticos de clasificación.
6. `GET /ejecucion` ➔ **Consola de Ejecución**: Tabs BingX vs Prop Firm con telemetría en vivo y modal interactivo de Kill-Switch.
7. `GET /seguimiento` ➔ **Timeline de Auditoría**: Historial inmutable de eventos (`/api/v1/audit/events`).
8. `GET /sistema` ➔ **Diagnóstico del Sistema**: Estado real de puertos, latencias, SQLite WAL y datasets.

---

## 4. Tests y Validación de Código

- `pytest services/api/tests/` ➔ **130 passed, 5 skipped, 0 failed** (100% de la suite pasando).
- Todas las rutas web devuelven **HTTP 200** con renderizado limpio.
