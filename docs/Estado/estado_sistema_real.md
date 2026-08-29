> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: verificación VPS del 2026-08-08 que describe MCP SQX 8080 y servicios antiguos; la realidad de hoy vive en docs/00_MASTER_IDEAS_Y_PLAN.md §2. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# Estado real del sistema Ultrarentable — Verificación VPS
**Fecha:** 2026-08-08  
**Entorno:** VPS 24/7, systemd user, modo REAL-ONLY  
**Alcance:** servicios, MCP SQX, API FastAPI, frontend, datos y BD.

---

## 1. Resumen ejecutivo
- **Servicios:** los 3 servicios systemd están activos y escuchando en los puertos esperados.
- **SQX MCP:** funciona, pero requiere handshake `initialize` previo y sesión `mcp-session-id`. Sin handshake, `tools/list` devuelve `400 Bad Request`.
- **API FastAPI:** endpoints principales responden `200` y exponen datos reales.
- **Frontend:** responde `200`, título correcto, pero en estado READY sin datos producidos.
- **Datos:** existen datasets reales en `data/normalized/`; la BD contiene 5 datasets, 30 estrategias, 1 campaña y 29 backtests. Hay al menos un dataset no aprobado/ficticio y rutas antiguas en artefactos.

---

## 2. Servicios systemd

| Servicio | Estado | Puerto / bind | Notas |
|---|---|---|---|
| `strategyquantx` | `active (running)` | `127.0.0.1:8080` | Escucha MCP; logs muestran handshakes de clientes `Antigravity-UltraRentableV2` y `hermes` con protocolo `2024-11-05` y `2025-03-26`. |
| `ultrarentable-api` | `active (running)` | `127.0.0.1:8000` | Uvicorn con `127.0.0.1`. |
| `ultrarentable-web` | `active (running)` | `localhost:3000` | Next.js `next-server (v16.2.12)`; warning de múltiples lockfiles detectados. |

Verificación: `systemctl --user status strategyquantx ultrarentable-api ultrarentable-web`.

---

## 3. StrategyQuant X MCP — Verificación real

### 3.1 Handshake
- Endpoint: `POST http://127.0.0.1:8080/mcp`
- Llamada directa sin handshake a `tools/list`: `400 Bad Request`.
- Llamada correcta:
  1. `initialize` → `200`, devuelve `protocolVersion`, `capabilities`, `serverInfo`.
  2. Header de respuesta: `mcp-session-id` con UUID de sesión.
  3. Usar ese header en llamadas siguientes.

Respuesta `initialize` real:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"logging": {}, "tools": {"listChanged": false}},
    "serverInfo": {"name": "StrategyQuant X", "version": "1.0.0"}
  }
}
```

### 3.2 Tools expuestos por SQX MCP
Llamada real a `tools/list` con sesión:
- Content-Type recibido: `text/event-stream;charset=utf-8`
- Cuerpo envuelto en SSE: `event: message` / `data: {...}`

Tools disponibles:
1. `list_projects`
2. `list_databanks` — requiere `name: string`
3. `list_strategies` — requiere `name`, `databank`
4. `get_strategy_stats` — requiere `name`, `databank`, `strategy`
5. `run_project` — requiere `name`
6. `stop_project` — requiere `name`

Proyectos reales en SQX:
- `PortfolioMaster`
- `PortfolioComposer`
- `Optimizer`
- `Builder`
- `Ultra_Auto_Pilot`
- `Ultra_Improve_Pilot`
- `Retester`

### 3.3 Código del proyecto
`services/sqx_bridge/sqx_client.py` implementa exactamente este flujo:
- `initialize()`: hace handshake y lee `mcp-session-id`.
- `list_tools()`, `list_projects()`, `list_databanks()`, `list_strategies()`, `get_strategy_stats()`, `run_project()`, `stop_project()`.
- Acepta encabezados `Accept: text/event-stream, application/json`.
- Incluye parseo SSE con fallback a JSON directo.

`services/sqx_bridge/converter.py` convierte métricas SQX a `StrategySpec` interno, pero no se verificó su ejecución real en esta pasada.

### 3.4 Conclusión MCP
- **Qué funciona:** handshake, listado de tools, listado de proyectos, consulta de status desde API.
- **Qué NO funciona todavía desde MCP puro sin wrapper:** llamadas directas sin sesión; hay que seguir el flujo initialize → tools/call.

---

## 4. API FastAPI — Endpoints probados

| Endpoint | Método | Estado real | Cuerpo / observación |
|---|---|---|---|
| `/` | GET | `200 OK` | JSON con `service`, `status: RUNNING`, `mode: LOCAL_REAL_ONLY`, implementaciones declaradas. |
| `/docs` | GET | `200 OK` | Swagger UI titulado *BingX Ultra Strategy Lab — Local Backend*. |
| `/api/v1/status` | GET | `200 OK` | `status: ONLINE`, `bingx_status: ONLINE`, `sqlite_status: WAL_ACTIVE`, `datasets_count: 5`, `approved_datasets: 4`, `strategies_count: 30`, `backtests_count: 29`, `campaigns_count: 1`, `account_status: NOT_CONFIGURED`. |
| `/api/v1/datasets` | GET | `200 OK` | Array JSON; al menos 1 dataset `VALIDATING` y 4 `APPROVED`. Incluye `filePath` y `manifestPath` reales. |
| `/api/v1/strategies` | GET | `200 OK` | Array JSON grande; 1 muestra analizada con `family: statistical_arbitrage`, `leverage: 52`, `status` implícito en payload. |
| `/api/v1/campaigns` | GET | `200 OK` | 1 campaña `FAST_EVALUATING`: `Autonomous_ETH-USDT_1h`, `populationSize: 4`, `currentGeneration: 1`. |
| `/api/v1/sqx/status` | GET | `200 OK` | `status: ONLINE`, `session_id` activo, `server_info: StrategyQuant X v1.0.0`. |
| `/api/v1/sqx/tools` | GET | `200 OK` | Devuelve exactamente los 6 tools listados arriba. |
| `/api/v1/sqx/projects` | GET | `200 OK` | Devuelve los 7 proyectos listados arriba. |
| `/api/v1/sqx/projects/{name}/databanks` | GET | *No probado en esta verificación* | Ruta documentada en OpenAPI; se puede probar en pasos siguientes. |

### Observaciones API
- `/api/v1/health` no existe; el servicio devuelve `404 Not Found`. El healthcheck real es `/api/v1/status`.
- La API actúa como proxy hacia SQX MCP con inicialización automática; por eso `/api/v1/sqx/*` funciona aunque el cliente directo necesite handshake.

---

## 5. Frontend — Verificación real

- URL: `http://127.0.0.1:3000/`
- Estado: `200 OK`
- Título: `BingX Ultra Strategy Lab`
- Modo prerender estático: cabeceras `x-nextjs-prerender: 1`, `x-nextjs-cache: HIT`
- Navegación presente: Command Center, Data Pipeline, Strategy Lab, StrategyQuant MCP, Backtester, Campaigns, Leaderboard, Prop Firms, Research.
- Estado visible: `READY`, `LOCAL REAL-ONLY`.
- Estadísticas actuales mostradas: `0` estrategias evaluadas, `0` mercados verificados, validación adversarial `PENDIENTE`.
- Botones funcionales presentes: INICIAR AUTOPILOTO ULTRA, PAUSAR, REANUDAR, DETENER.

Conclusión frontend: sirve correctamente, pero es una UI vacía a la espera de ejecución real del pipeline.

---

## 6. Datos y datasets

### 6.1 `data/normalized/`
- Ruta existe: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized`
- Archivos reales: 31 entradas contando manifiestos y `.gitkeep`.
- Se observan datasets duplicados por timeframe:
  - `1m`
  - `5m`
  - `15m`
  - `1h`
- Formato: pares `...json` + `..._manifest.json`.
- No existe carpeta `data/normalized/` en el listado inicial porque la búsqueda先 usó ruta incorrecta; verificación posterior confirma existencia y contenido real.

### 6.2 SQLite
- Ruta: `~/.local/state/ultrarentable/ultrarentable.sqlite3`
- Tamaño: `434176` bytes.
- Tablas reales:
  - `instruments`
  - `datasets`
  - `raw_ingest_logs`
  - `strategies`
  - `strategy_compilations`
  - `validation_errors`
  - `backtests`
  - `campaigns`
  - `campaign_events`
  - `campaign_trials`
  - `research_sources`
  - `instrument_rule_snapshots`
  - `account_fee_snapshots`
  - `autopilot_runs`
  - `autopilot_decisions`
  - `opportunity_matrix`
  - `leverage_trials`
  - `novelty_archive`
  - `canonical_validations`
- Conteos:
  - `datasets`: 5
  - `strategies`: 30
  - `backtests`: 29
  - `campaigns`: 1
- Rutas de artefactos en `backtests` apuntan a `/home/ubuntu/workspace/pro/03-trading/ultrarentable/data/artifacts/...`, que **no coincide** con la ruta canónica actual `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/`. Eso puede romper trazabilidad.

---

## 7. Gaps y lo que falta para flujo completo SQX → API → Web

| Capa | Estado | Gap |
|---|---|---|
| SQX MCP | Conectado y con tools | Falta probar `run_project`, `list_databanks`, `list_strategies`, `get_strategy_stats` extremo a extremo desde API y desde cliente Python. |
| API → SQX | Proxy funciona | Endpoint de databanks/estrategias por nombre no verificado aún en llamada real; falta probar `/api/v1/sqx/projects/{name}/databanks`. |
| API | Funcional | Falta healthcheck oficial; `/api/v1/health` da 404. |
| Web → API | No verificado | No se hicieron llamadas desde frontend; solo se verificó HTML inicial. |
| Datos | Existen | Hay datasets no aprobados en BD y rutas de artefactos inconsistentes con la ruta canónica actual. |
| Cuenta | No configurada | `account_status: NOT_CONFIGURED` impide operativa real brokerage-side. |

---

## 8. Evidencia de comandos usados
- `systemctl --user status strategyquantx ultrarentable-api ultrarentable-web`
- `curl http://127.0.0.1:8080/` → `302` a `/SQUANT/index.html`
- `curl http://127.0.0.1:8000/`, `/docs`, `/api/v1/status`, `/api/v1/datasets`, `/api/v1/strategies`, `/api/v1/campaigns`, `/api/v1/sqx/status`, `/api/v1/sqx/tools`, `/api/v1/sqx/projects`
- `curl http://127.0.0.1:3000/`
- Python `urllib` contra `/mcp` con y sin handshake
- Lectura de `services/sqx_bridge/sqx_client.py` y `converter.py`
- Inspección SQLite de tablas, columnas y muestras

---

## 9. Próximos pasos recomendados
1. Corregir rutas de artefactos antiguas en `backtests` y verificar existencia real de `ledger.json`.
2. Eliminar o aprobar el dataset no aprobado `ds_unapproved_test`.
3. Probar `/api/v1/sqx/projects/{name}/databanks` con proyecto real, p. ej. `Ultra_Auto_Pilot`.
4. Definir un healthcheck oficial en API (`/api/v1/health`) o documentar `/api/v1/status` como tal.
5. Configurar `account_status` una vez se prepare entorno de brokerage seguro.
6. Probar flujo completo frontend → API → SQX con un proyecto real y registrar salida.
