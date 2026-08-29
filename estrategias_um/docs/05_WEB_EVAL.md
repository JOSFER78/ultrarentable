# 05_WEB_EVAL — Estado real de la página /estrategias (2026-08-29)

## VEREDICTO: PARCIAL

La página existe, es única (no hay duplicado en conflicto) y carga datos reales desde la API canónica v2. Lo que NO funciona hoy: la extracción desde SQX (función 4 de la spec) — el bridge apunta a un endpoint MCP muerto/incorrecto mientras el SQX real vive en :5050.

## 1. Implementación localizada

| Pieza | Ruta |
|---|---|
| Página canónica (client component) | `apps/web/app/estrategias/page.tsx` (única; ~105 líneas) |
| Contrato de producto | `apps/web/app/estrategias/README_STRATEGIES_PAGE.md` |
| Alias legacy `/strategies` | `app/strategies/page.tsx` → `redirect("/estrategias")` (307 verificado en runtime) — conforme a spec |
| Cliente API (única fuente) | `apps/web/lib/api.ts`: `getStrategyLabOverview/Strategies/SQXStatus`, `extractStrategyLabProject` |
| Router backend canónico | `services/api/app/api/strategy_lab_router.py` (FastAPI, prefix `/strategy-lab`, montado en `/api/v2`) |
| Bridge SQX | `services/sqx_bridge/sqx_client.py` (`SQX_MCP_URL`, default `http://127.0.0.1:8080/mcp`) + `ingest_sqx_results.py` |
| Estados | API emite pipeline `EXTRACTED_UNVERIFIED → …`; UI mapea/ordena `EXTRACTED → STRUCTURALLY_VERIFIED → BACKTEST_VERIFIED → CERTIFIED_CURRENT` |

## 2. Runtime real verificado

- `next dev` en :3111 → `GET /estrategias` = **200**, renderiza "Catálogo canónico", tarjetas de pipeline, tabla, botones "Explorar candidatos" y "Extraer".
- Subrutas enlazadas OK (200): `1-motor-en-vivo`, `2-explorador-excel`, `4-panel-investigador` (hub 6 fases).
- API en :8000 viva: `/api/v2/strategy-lab/overview` → `{extracted: 59, structurally_verified: 0, backtest_verified: 0, certified_current: 5, approved_datasets: 142}`.
- `/api/v2/strategy-lab/strategies` devuelve registros reales con hash, procedencia SQX (`Ultrarentable_Research/Results`), símbolo/TF (ej. `UR_FONDEO_ES_4h`, BACKTEST_VERIFIED, PF OOS 1.42).
- Proxy de rewrites de Next (`/api/*` → `ULTRARENTABLE_API_URL`, default 127.0.0.1:8000) verificado funcionando en :3111.
- Nota operativa: NO existe build de producción (`.next` vacío tras limpieza; `next start` falla). Solo `next dev`. El servicio web no estaba levantado al inicio de la evaluación.

## 3. ¿Dos implementaciones en conflicto? NO

- Una sola página de catálogo (`app/estrategias/page.tsx`); toda la data vía `lib/api.ts` → API v2 (cumple "única fuente de verdad" de la spec).
- `/strategies` = redirect alias, no implementación duplicada.
- `app/trading-desk/estrategias/page.tsx` existe pero es la vista del desk de EJECUCIÓN (venue/sesiones), otro dominio; no reintroduce `MotorBacktestView` ni controles de capital en el catálogo. No hay conflicto, pero conviene documentar en la spec que esa ruta es venue-scoped.
- Subpáginas de fases (1..6) viven bajo `/estrategias/*` — jerarquía limpia.

## 4. Conexión SQX hoy (función 4: "Extraer hipótesis reales") — ROTA

- Flujo diseñado: UI input proyecto → `POST /api/v2/strategy-lab/extract/{project}` → `SQXMCPClient.list_strategies` + `get_strategy_stats` → parse `extract_stats` → upsert en SQLite con `strategy_id=sqx:<proj>:Results:<name>`, hash sha256 canónico, estado `EXTRACTED_UNVERIFIED`. Diseño correcto y evidence-first (cuarentena para items sin nombre/stats; `next_step: REQUIRES_EXPLICIT_RULE_SOURCE_AND_REAL_DATASET_AND_CANONICAL_BACKTEST`).
- **Realidad**: `GET /api/v2/strategy-lab/sqx/status` → `OFFLINE` ("Failed to connect to SQX MCP at http://127.0.0.1:8080/mcp: Method Not Allowed"). El puerto 8080 está ocupado por OTRO proceso python que no es el MCP de SQX. El SQX real (sqcli) escucha en **:5050** (proceso `sqcli` vivo), pero el bridge no habla con él.
- Consecuencia: el botón "Extraer" siempre devuelve 502 `SQX_UNAVAILABLE` hoy. No hay extracción real posible desde la UI.
- Endpoints extra del router no expuestos en la página: `/source/{proj}/{name}` (fuente ejecutable), `/improvement/plan/{id}` (plan orgánico sin mutación), `/strategies/{id}/bind-dataset` + `/binding`.

## 5. Funciones de la spec (18_STRATEGIES_PAGE_SPEC) — estado

1. Buscar/filtrar catálogo → **OK** (búsqueda texto + filtros activo/estado, verificados en código y render).
2. Ver procedencia, activo, TF, estado → **OK** (columnas + ficha lateral con datos reales).
3. Inspeccionar hashes/dataset → **OK** (strategy_hash, dataset_hash, artifact, `EvidenceLink`; NO EVIDENCE nunca 0 — respeta la regla).
4. Extraer hipótesis reales desde SQX → **ROTO** (bridge apunta a :8080/mcp muerto; SQX real en :5050).
5. Navegar a Candidatos/Investigación → **OK** (links a 2-explorador-excel / 4-panel-investigador, ambos 200).
6. Refrescar catálogo desde API canónica → **OK** (botón Actualizar + refresh tras extracción; API v2 viva).

## 6. QUÉ ARREGLAR (existe, está roto)

1. **[P0] Bridge SQX**: apuntar `SQX_MCP_URL` al endpoint real del sqcli (:5050) o adaptar `SQXMCPClient` al protocolo de esa API; hoy el 8080/mcp está ocupado por un proceso ajeno. Probar `POST /extract/<proyecto real>` end-to-end.
2. **[P1] Mismatch de estado**: API emite `EXTRACTED_UNVERIFIED`, la UI ordena/filtra por `EXTRACTED` → las extraídas caen en el bucket "otro estado" (chip ámbar fallback). Unificar el literal en un solo lugar.
3. **[P1] Producción**: no hay build (`next start` falla); solo dev. Construir `.next` y dejar el servicio levantado (systemd/pm2) si /estrategias debe estar disponible.
4. **[P2] Gobernanza del catálogo heredado**: la BD muestra 5 CERTIFIED_CURRENT + BACKTEST_VERIFIED legacy v5.4.0 que la auditoría declara no certificadas por asunción; decidir re-validación o archivado (tarea de gobernanza, no de UI).

## 7. QUÉ HACER NUEVO (no existe)

1. Botón/acción "Inspeccionar fuente SQX" conectado al endpoint ya existente `/strategy-lab/source/{proj}/{name}` (fuente ejecutable + sha256).
2. Flujo de bind-dataset en UI (`/strategies/{id}/bind-dataset` existe en API, no en página) para pasar EXTRACTED → STRUCTURALLY_VERIFIED.
3. Indicador de salud SQX en la cabecera (hoy solo un texto gris "SQX: NO EVIDENCE/status") con detalle del error cuando esté OFFLINE.
4. Selector de databank (hoy hardcodeado `DATABANK="Results"` en `ingest_sqx_results.py`).

## Veredicto resumido
**PARCIAL** — catálogo real, único y conforme a spec (5/6 funciones OK); extracción SQX rota por desalineación de puertos/protocolo del bridge (función 4 caída).
