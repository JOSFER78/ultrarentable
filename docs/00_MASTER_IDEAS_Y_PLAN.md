# 00_MASTER_IDEAS_Y_PLAN — ULTRARENTABLE (SSOT DOCUMENTAL ÚNICO)

> **ESTE DOCUMENTO ES LA ÚNICA FUENTE CANÓNICA (SSOT) de ideas, arquitectura actual real, fases y decisiones abiertas del proyecto.**
> **Fecha de consolidación:** 2026-08-29 (consolidación documental, working tree — NO commitear).
> **Jerarquía documental (vigente desde hoy):**
> 1. `docs/00_MASTER_IDEAS_Y_PLAN.md` — **ESTE documento** (ideas, plan, estado real, decisiones abiertas).
> 2. `AUTHORITY_GRAPH.md` — cadena de autoridad técnica de contratos (vigente, no contradice).
> 3. `docs/VERSION_GOVERNANCE_AND_CONTROL.md` — política de versionado/certificación (vigente, no contradice).
> 4. `docs/ULTRARENTABLE_PRINCIPLES.md` — los 15 principios (vigentes, no contradicen).
> 5. Todo lo demás: histórico o SUPERSEDED (ver banner al inicio de cada doc).
>
> **Doctrina transversal (obligatoria, de `.agents/AGENTS.md`):** ZERO-MOCKS / REAL-ONLY · cero datos inventados · cero fallbacks complacientes (`NO DATA / ERROR`, nunca valores por defecto) · PROHIBIDO `git commit`/`git push` automático (working tree solo, inspección manual del usuario).
>
> **Regla de mantenimiento:** cuando la realidad del sistema cambie, se actualiza SOLO este documento (y la sección correspondiente). Los docs con banner SUPERSEDED no se actualizan ni se borran.

---

## 1. IDEA DEL PROYECTO (definición estable)

**Ultrarentable** es un laboratorio cuantitativo real-only que descubre, valida y explota estrategias de trading bajo **dos vías de negocio segregadas** (bifurcación dual canónica, definida por el usuario y no renegociable):

| Dimensión | 🚀 **TRACK_ULTRA** | 🏛️ **TRACK_FONDEO** |
| :--- | :--- | :--- |
| Objetivo | Crecimiento asimétrico/convexo (hiperescalado) | Pasar evaluaciones de prop firms y sostener retiros netos |
| Activos | **TODOS LOS ACTIVOS (100% Universo):** Cripto Perpetuos (BingX), Futuros CME (ES/NQ/YM/RTY/GC/CL/SI), Forex Majors y Commodities. **NUNCA es solo cripto**. | Cuentas de prop firms (futuros CME: MES/MNQ/MYM/M2K, MGC/MCL y majors forex) |
| Temporalidades | **1min (1m), 5min (5m), 15min (15m), 1h (1h) y 4h (4h)** — **SOLO INTRADIA** en todos los activos. | **1min (1m), 5min (5m), 15min (15m), 1h (1h) y 4h (4h)** — **SOLO INTRADIA** (cierre diario obligatorio). |
| Horizonte | **SOLO INTRADIA** (cero riesgo overnight destructivo; salidas en sesión, sin depender de swing multi-día). **NUNCA es solo 4H conservador**. | **SOLO INTRADIA** (cierre obligatorio a las 16:59 EST para CME/FX; cero riesgo overnight de fin de semana). |
| Riesgo | DD flotante hasta ~80%, realizado hasta ~75%; bala de margen aislado 1R ($100–$1,000) | DD realizado ≤ 4.0–4.5%; pérdida diaria ≤ 2% (~$1,000/50k); contratos fijos, 0% compounding |
| Gestión | Sistema de **Balas y Estados** (INICIO → CONFIRMACIÓN → CRECIMIENTO → COSECHA → PROTECCIÓN → CIERRE) con bóveda ratchet (beneficio cosechado intocable, 50–85%) | Preservación institucional: cierre intradía obligatorio, 0 margin calls, sesión RTH |
| Métrica reina | Payoff ≥ 3R–10R (skew derecho) | **Economía real neta**: retiros − (exámenes + activaciones + reinicios + datos) |

> [!IMPORTANT]
> **DIRECTIVA VIGENTE DE TEMPORALIDADES Y ACTIVOS (MANDATO PERMANENTE DEL USUARIO):**
> 1. **ULTRA NO ES SOLO CRIPTO NI SOLO 4H CONSERVADOR:** ULTRA es un motor de convexidad hiper-asimétrica con balas aisladas y piramidación que opera en **TODOS los activos** (Cripto, Futuros CME, Forex, Commodities).
> 2. **5 TEMPORALIDADES INTRADÍA EN TODOS LOS ACTIVOS:** **1min (`1m`), 5min (`5m`), 15min (`15m`), 1h (`1h`) y 4h (`4h`)**.
> 3. **SOLO INTRADIA:** Todas las operativas y reglas cuantitativas en todas las temporalidades están concebidas y acotadas para ejecución intradía (cierre de posiciones al terminar la jornada/sesión, sin exposición a gaps o eventos overnight no controlados).

Ambas vías comparten: motor de descubrimiento (SQX), validación canónica determinista (11 Evidence Gates), partición ciega IS/Validation/Blind-Holdout, registry de trials (DSR) y trazabilidad SHA-256 end-to-end. **Nunca comparten lógica de riesgo.**

**Ecosistema de negocio (fase de negocio, no de motor):** el corpus `docs/tradesfera/` (16 módulos, certificado 2026-08-27) y `docs/Fondeo/` + `docs/conexiones_automatizar/` documentan la estrategia de fondeo de futuros CME (prop firms, bankroll, varianza, playbook diario, infraestructura NinjaTrader/Tradovate, IPs/VPN residencial). Es la capa de NEGOCIO sobre el TRACK_FONDEO; se respeta como corpus de referencia, no como especificación de motor.

---

## 2. ARQUITECTURA ACTUAL REAL (verificada físicamente el 2026-08-29)

> Esta sección describe **lo que ES hoy en disco y en los puertos**, no lo deseado. Verificación: procesos `ss -tlnp`/`ps` en vivo, archivos y scripts reales.

### 2.1 Motor de descubrimiento: SQX headless (sqcli, puerto 5050)

- **Motor:** StrategyQuant X corre **headless** como `sqcli` (binario `/home/ubuntu/StrategyQuantX144/sqcli`, pid 222850), escuchando **HTTP API en `0.0.0.0:5050`** (`/call?cmd=...`). NO hay GUI, NO hay MCP en 8080 activo para SQX.
- **Estado físico verificado:** `user/data/History/` contiene **97 carpetas `<SYM>_<TF>` reales** (98 entradas − `sq_equity`), exactamente: 9 cripto (AVAX/BNB/BTC/DOGE/ETH/LINK/SOL/SUI/XRP **USDT**) × {M1, M5, M15, H1, H4} + 7 futuros CME (ES, NQ, YM, RTY, GC, CL, SI) × {M5, M15, H1, H4} + 6 forex (EUR, GBP, USD-JPY/CHF/CAD, AUD USD) × {M5, M15, H1, H4} = 45 + 28 + 24 = **97 celdas**.
- **Naming canónico:** `<SYM>_<TF>` (p. ej. `ES_M5`, `BTCUSDT_H1`) — necesario porque SQX fuerza 1 timeframe base por símbolo.
- **Proyectos SQX en disco** (`user/projects/`): `Ultra_Auto_Pilot` (**activo**, 1 setup inicial — el subagente A está construyendo la matriz 97 setups AHORA), `Builder`, `Optimizer`, `Retester`, `PortfolioComposer`, `PortfolioMaster`, `Ultra_Matrix`, `backups`.
- **Instrumentos:** specs reales CME/forex/cripto importados (tick size, point value, clases de comisión reales: `PerTrade` para CME ~$2.4 MES, `PercentageBased` 0.05% cripto). SSOT de instrumentos: **`canonical_instrument_aliases.json`** (raíz del repo, `registry_version` 1.0.0, `registry_sha256` 4392a832…): mapea alias (BingX `BTC-USDT`/`BTC_USDT`, Yahoo `EURUSD=X`, etc.) → símbolo canónico (`BTCUSDT`, `EURUSD`…).
- **Nota histórica:** los docs antiguos (Plan 10 Fases, Motor SQX, Estado/estado_sistema_real.md) describen SQX como "MCP en puerto 8080/8081". **Hoy eso está SUPERSEDED**: el motor es sqcli HTTP en 5050. (El puerto 8080 TCP está ocupado por otro proceso Python ajeno a SQX.)

### 2.2 Autopiloto de búsqueda: `services/background_searcher.py`

- Motor de fondo autónomo ULTRA+FONDEO. **`SEARCH_MATRIX` ya reescrita a las 97 celdas reales** (verificado: `py_compile` OK, conteo 9+88=97, `mode:"ultra"`, proyecto `Ultra_Auto_Pilot`, databank `Results`, `chartSymbol` `<SYM>_<TF>` 1:1 con SQX).
- Flujo por celda: run SQX → monitoriza databank → ingesta candidatos a BD operacional (`~/.local/state/ultrarentable/ultrarentable.sqlite3`, merge upsert) → quality gates → log central (tabla `search_logs`) + % progreso para la web.
- Real-only: no descarga histórico ni inventa métricas; cada candidato proviene de resultados reales de SQX.
- Consumidor API: `services/api/app/api/routes.py` importa `run_matrix` + `SEARCH_MATRIX` (endpoint de arranque de búsqueda en segundo plano).

### 2.3 Datos (estado real 2026-08-29)

- **Backfill M1 cripto EN CURSO:** `python3 /home/ubuntu/binance_m1_dl.py` (pid 201108) descarga klines M1 mensuales/diarios reales de **data.binance.vision** (spot) a `/home/ubuntu/binance_m1_zips/` — zips reales ya en disco (9 símbolos, desde ~2018). Descarga atómica (`.part`→rename, 3 reintentos), log en `download.log`.
- **Backfill 5m CME/forex: SIN fuente gratuita verificable conocida — BLOQUEADO (honesto).** No se inventa fuente ni se finge progreso. Decisión de negocio pendiente (ver §5).
- Cobertura ya importada en SQX (per skill sqx-headless-workflow): M1 cripto ~7 días (el backfill M1 en curso ampliará esto), 5m ~2–3 meses, H1/H4 años.
- `data/` del repo: `normalized/`, `raw/`, `evidence/`, `registry/`, `sqx_imports/`, `sqlite.db`, `candidates.db`, manifiestos SHA-256.

### 2.4 Stack web/API (deuda viva, puertos reales)

| Servicio | Puerto REAL hoy | Proceso | Nota |
| :--- | :---: | :--- | :--- |
| **API FastAPI** (`services/api/app/main.py`) | **8000** | `ultrarentable-api.service` (uvicorn, pid 4074143) | ✅ Responde. `GET /` reporta `version 2.2.0 / engine_version 5.4.0`, tracks FONDEO/ULTRA/PORTFOLIO. Health reporta `overall_status: DEGRADED` porque su check apunta al 3000 (puerto obsoleto). |
| **Web Next.js** (`apps/web`) | **3005** (NO 3000) | `ultrarentable-web.service` → `ultra-web-wrapper.sh` → `next dev -p 3005` | ✅ Next 14.2.35 en dev. **Contradicción abierta de gobernanza**: STATE_OF_TRUTH/README dicen "puerto 3000"; el wrapper real dice 3005. Listada en §5. |
| **SQX headless (sqcli)** | **5050** | pid 222850 | Motor de descubrimiento. |
| Puerto 8080 | 8080 | proceso python ajeno (NO SQX) | No es SQX; los docs que dicen "SQX MCP 8080" están superados. |

### 2.5 Cadena de verdad canónica (de docs/ARCHITECTURE_CURRENT.md — sigue vigente)

```text
PHYSICAL DATASET → DATASET SNAPSHOT/HASH → CANONICAL STRATEGY AST → DISCOVERY/GENERATION
→ DETERMINISTIC BACKTEST → TRADE LEDGER → RESEARCH DEBATE/MUTATION → VALIDATION
→ BLIND OOS → 11 EVIDENCE GATES → LIFECYCLE/EVIDENCE → API → FRONTEND → PAPER/LIVE
```

Ninguna capa superior puede inventar/sobrescribir resultados de una inferior. Ciclo de investigación: `GENERATED → BACKTESTED → CANDIDATE → SEMANTIC_RESEARCH → MUTATED → REBACKTESTED → OOS_PASSED → ROBUSTNESS_PASSED → EVIDENCE_APPROVED → CERTIFIED_CURRENT`. Certificación = estrictamente 11/11 gates, jamás por heurística o intervención de agente.

---

## 3. MAPA DE ESTRUCTURA DE CÓDIGO (servicios, rutas, tests, flujos de datos)

```text
"01 Ultrarentable/"  (raíz repo, working tree — PROHIBIDO commit/push automático)
├── contracts/                  ← SSOT de dominio (Pydantic inmutable). NO importa de services/.
│   ├── canonical_strategy.py       ← SSOT ÚNICO de estrategia (CanonicalStrategy + hash)
│   ├── canonical_execution.py      ← SSOT de ejecución (costes/microestructura, ledger Merkle)
│   ├── canonical_runtime_adapter ↔ raíz: canonical_runtime_adapter.py  (compilación→ejecución)
│   ├── canonical_strategy.py ↔ raíz: canonical_strategy.py
│   ├── backtest.py, validation_contracts.py, portfolio.py, risk_model.py,
│   │   instrument_specification.py, dataset_specification.py, alias_contracts.py,
│   │   evidence_bundle.py, gate_directory.py, universal_ledger.py, universal_strategy.py,
│   │   learning_contracts.py, lineage_contracts.py, queue_contracts.py, research_contracts.py,
│   │   execution_model.py, dataset_contracts.py
│   └── snapshots/                  ← snapshots inmutables (estrategia, dataset, EvidenceRecord)
├── services/                   ← capa de aplicación (25 módulos)
│   ├── background_searcher.py      ← ★ AUTOPILOTO: SEARCH_MATRIX 97 celdas → SQX sqcli
│   │                                  (proyecto Ultra_Auto_Pilot) → BD → gates → search_logs
│   ├── sqx_bridge/                 ← cliente SQX (sqx_client.py, converter.py, ingest_sqx_results.py,
│   │                                  backfill_sqx_oos.py, sqx_sync_worker.py, sqx_gui_automation.py)
│   ├── api/  (FastAPI :8000)
│   │   └── app/
│   │       ├── main.py             ← app uvicorn ("ultrarentable-api.service")
│   │       ├── api/                ← routers v1 (routes.py, sqx_router, candidates_router,
│   │       │                          gates_router, discovery_router, research_router,
│   │       │                          research_lab_router, portfolios_router, prop_firms,
│   │       │                          real_data_router, version_router, audit_router, …)
│   │       ├── engine/             ← FastEngine (DSL/IR) — motor de backtest rápido
│   │       ├── validation/         ← gates (gate_01..11), FSM de validación
│   │       ├── data_feed/, ingestion/, dsl/, bingx/, factory/, export/, maintenance/
│   │       └── routes/ (providers_ai.py)
│   ├── validation/                 ← candidate_registry (FSM), certification_registry (11 gates)
│   ├── discovery/                  ← strategy_search_registry (trials→DSR), strategy_evolution_engine
│   ├── engine/                     ← UniversalDeterministicBacktestEngine (canónico, ledger Merkle)
│   ├── execution/                  ← canonical_runtime_adapter (SSOT ejecutor → EvaluatedTrade)
│   ├── backtest/                   ← fast_engine_adapter
│   ├── data/                       ← dataset_registry, holdout_gateway (firewall IS/Val/Holdout)
│   ├── portfolio/                  ← allocator (ERC/Markowitz/MaxSharpe, solo certificadas)
│   ├── ultra/                      ← bala_convex_engine (máquina de estados Bala)
│   ├── fondeo (en api/prop_firms)  ← challenge_evaluator (State Machine Fondeo)
│   ├── strategy_core/, research/, semantic_ai/, monitoring/, policy/, paper/,
│   │   queue/, sync/ (firebase push one-way), lineage/, optimization/, data-ingestion/,
│   │   exploitation_engines/, ai_updater/, core/
│   ├── version_control_manager.py  ← SSOT versionado motor (huella SHA-256, manifest)
│   └── engine_version.py
├── apps/web/  (Next.js :3005, dev)
│   └── app/  ← 30+ rutas: estrategias (hub 6 fases), gates, portfolio, research(-lab),
│              candidatos, sistema, dashboard, fondeo, prop-firms, robots, strategyquant,
│              nautilus, trading-desk (auditoria/config/estrategias/posiciones), seguimiento,
│              alertas, seguridad, bifurcacion, leaderboard, campaigns, data, panel…
│   └── lib/strategyPhases.ts  ← fuente ÚNICA de definición de fases (nav deriva de ahí)
├── scripts/                    ← orquestación SQX/Phase2: create_sqx_autonomous_project.py,
│   │                              prepare_sqx_dataset.py, sqx_kamikaze_runner.py, sqx_vps_ingest.py,
│   │                              phase2_* (trial_planner, research_run, blind_oos, validation),
│   │                              mine_and_certify_*.py, diagnose_gates.py, ip_guard.py, stabilization/
├── tests/                      ← suites pytest (test_canonical_*, test_event_backtest_deterministic,
│   │                              test_blind_and_certification, test_fail_closed_engine_and_dataset,
│   │                              test_zero_mocks, tests/api/, tests/discovery/, stabilization/)
│   + test_phase01_dataset_chain_of_custody.py, test_phase02_canonical_strategy.py (raíz)
├── canonical_instrument_aliases.json  ← ★ SSOT de instrumentos/aliases (hash sellado)
├── version_manifest.json, database.sqlite, learning_store.sqlite
├── AUTHORITY_GRAPH.md                 ← gobernanza técnica vigente
├── ESTADO.md, README.md, SYSTEM_DOCTRINE.md, SPEC_MASTER_ULTRA_VS_FONDEO.md, ARCHITECTURE.md  ← SUPERSEDED
└── docs/                              ← consolidado (ver §0 jerarquía + banners)
```

**Flujos de datos principales (hoy, reales):**
1. **Descubrimiento:** `binance_m1_dl.py`/zips → import SQX (`History/<SYM>_<TF>`) → `background_searcher.run_matrix(SEARCH_MATRIX[97])` → sqcli :5050 (proyecto `Ultra_Auto_Pilot`) → candidatos → `ultrarentable.sqlite3` (+`search_logs`) → quality gates → API :8000 → Web :3005.
2. **Validación:** DatasetRegistry (hash físico) → holdout_gateway (IS 60/Val 20/Blind 20) → EventBacktestEngine/CanonicalRuntimeAdapter → ledger → 11 gates → EvidenceRecord (`data/evidence/<sid>/gate_XX.json`) → certificación 11/11 → Vista 5.
3. **Instrumentos:** `canonical_instrument_aliases.json` → resolver alias→canónico en ingesta/backtest; specs reales CME/cripto viven en SQX (`-instrument`).

---

## 4. FASES DE IMPLEMENTACIÓN — ESTADO REAL HOY (2026-08-29)

> Estados de los planes antiguos (Plan 10 Fases, Plan 12 Fases, Plan Adaptativo 8 fases, PHASED/MVP_BUILD_PLAN) están consolidados aquí y SUPERSEDED. Esta tabla es la única vigente.

| # | Fase | Estado hoy (2026-08-29) | Evidencia real |
| :--- | :--- | :--- | :--- |
| 0 | Doctrina, contratos y gobernanza (ZERO-MOCKS, SSOT, AUTHORITY_GRAPH, 15 principios) | ✅ VIGENTE | `.agents/AGENTS.md`, AUTHORITY_GRAPH.md, ULTRARENTABLE_PRINCIPLES.md, tests/test_zero_mocks |
| 1 | Motor SQX headless operativo + specs reales de instrumentos | ✅ HECHA | sqcli :5050, 97 carpetas `<SYM>_<TF>` en History, INSTRUMENTS CME/forex/cripto reales |
| 2 | Matriz de búsqueda 97 celdas en el autopiloto | 🔄 EN CURSO | `SEARCH_MATRIX`=97 verificado (py_compile OK); proyecto `Ultra_Auto_Pilot` con 1 setup; subagente A construyendo la matriz 97 setups AHORA |
| 3 | Datos M1 cripto | 🔄 EN CURSO | `binance_m1_dl.py` activo; zips reales en `/home/ubuntu/binance_m1_zips/` (desde 2018) |
| 4 | Datos 5m CME/forex | 🚫 BLOQUEADO (sin fuente gratuita verificable conocida) | No hay fuente; no se inventa. Decisión de negocio pendiente (§5.1) |
| 5 | Validación canónica independiente (IS/Val/Blind-Holdout, EventBacktestEngine, 11 gates, DSR) | ✅ ESTRUCTURA HECHA (contracts, gateways, registry, suites de tests); espera volumen de candidatos reales de las fases 2–3 | AUTHORITY_GRAPH, suites tests/, walkthrough.md (histórico de reparación) |
| 6 | Web/API de explotación (catálogo, gates, portfolio, fondeo) | ⚠️ PARCIAL con deuda | API :8000 responde (engine 5.4.0); Web :3005 en dev; health DEGRADED por puerto obsoleto 3000 |
| 7 | Gestión de capital (Balas y Estados, bóveda ratchet) | 🟡 DISEÑO (doc de negocio vigente) | `docs/Gestion de Capital — Balas y Estados.md` + contracts/ultra |
| 8 | Ejecución/paper/live (BingX, NinjaTrader/Tradovate, conexiones) | ⚪ PENDIENTE (corpus de negocio listo: conexiones_automatizar, tradesfera) | docs/conexiones_automatizar/, NINJATRADER8_DEMO_PROP_RUNBOOK.md |
| 9 | Portfolio sobre certificadas (ERC/Markowitz, solo Vista 5) | ⚪ PENDIENTE (requiere certificadas 11/11) | VERSION_GOVERNANCE §3 |
| 10 | Fase de negocio: fondeo prop firms (economía neta, playbook) | 🟡 CORPUS COMPLETO (negocio) | docs/tradesfera/ (16 módulos), docs/Fondeo/ |

**Siguiente objetivo de ingeniería (secuencia aprobada):** terminar matriz 97 setups en `Ultra_Auto_Pilot` (subagente A) → primera campaña de búsqueda en segundo plano → ingesta de candidatos → validación/gates con datos M1 cripto ampliados por el backfill.

---

## 5. CONTRADICCIONES Y DECISIONES ABIERTAS (SOLO LISTADAS — requieren decisión de NEGOCIO del usuario; no se resuelven aquí)

### 5.0 Contradicciones documentales detectadas (listadas, no resueltas aquí)

- **C1 → decisión #2:** `docs/STATE_OF_TRUTH.md`/`README.md` dicen "puerto web 3000"; el servicio real corre en **3005** (`ultra-web-wrapper.sh`). Además el health de la API :8000 reporta `DEGRADED` porque su check apunta al 3000 obsoleto.
- **C2 → decisión #7:** `docs/STATE_OF_TRUTH.md` declara **230 estrategias certificadas v5.4.0 / 258 catalogadas**; la gobernanza posterior (17_PHASE2 + auditoría forense) declara **"NO STRATEGY IS CERTIFIED BY ASSUMPTION"**. Estatus del catálogo heredado sin resolver.
- **C3 → resuelta documentalmente (no requiere negocio):** docs antiguos describen SQX como "MCP 8080/8081"; la realidad física es **sqcli HTTP :5050**. Reflejada en §2.1 y banners SUPERSEDED de 2026-08-29.
- **C4:** `ARCHITECTURE.md`/`SYSTEM_DOCTRINE.md` (raíz) aún se titulan "V2 canónico" mientras el motor real es v5.4.0 y el SSOT es este master. Marcados SUPERSEDED; se listan porque cualquier cita externa a ellos produce inconsistencia hasta que el usuario decida su destino (archivar/borrar).

### 5.0.1 Directiva Canónica Sellada por el Usuario (2026-08-30) — NO MODIFICABLE:
- **ULTRA NO ES SOLO CRIPTO NI SOLO 4H CONSERVADOR:** ULTRA opera sobre el 100% del universo de activos (Cripto Perpetuos BingX, Futuros CME, Forex Majors, Commodities). Queda terminantemente prohibido restringir ULTRA a criptomonedas o a estrategias conservadoras de 4H.
- **5 TEMPORALIDADES INTRADÍA EN TODOS LOS ACTIVOS:** Ambos tracks (ULTRA y FONDEO) buscan, validan y explotan estrategias en **1min (`1m`), 5min (`5m`), 15min (`15m`), 1h (`1h`) y 4h (`4h`)**.
- **SOLO INTRADIA:** Todas las estrategias en todas las temporalidades tienen un horizonte operativo estrictamente intradía (cero riesgo overnight de fin de semana o multi-día descontrolado).

1. **Fuente de datos 5m CME/forex (bloqueo real):** no existe fuente gratuita verificable conocida. Opciones a decidir: pagar datos (Databento/Polygon/CME oficial), reducir la matriz a las celdas con datos, u otra vía que el usuario defina. Sin decisión, 24 de las 97 celdas CME/forex a 5m-equivalente y toda la expansión M5 quedan limitadas a lo ya importado (~2–3 meses).
2. **Puerto web canónico (3000 vs 3005):** la gobernanza documental dice 3000; el servicio real corre en 3005 (wrapper). Decidir: normalizar servicio a 3000+doc, o actualizar documentación a 3005.
3. **Cobertura mínima de barras para activar cada celda:** ¿cuánto histórico mínimo (meses/años) se exige por celda antes de que el autopiloto la lance? (impacta cuándo arranca la campaña).
4. **Uso de los 2–3 meses de 5m CME/forex ya importados:** ¿se permiten campañas exploratorias cortas en esas celdas con la etiqueta honesta de "datos limitados", o se prohíbe cualquier run sin el mínimo de cobertura?
5. **Alcance del TRACK_FONDEO en el MVP:** ¿el autopiloto corre también celdas con `mode:fondeo` desde el inicio, o primero solo ULTRA y FONDEO se activa tras el corpus de negocio (tradesfera playbook)?
6. **Prioridad entre continuar backfill M1 cripto (años de historia) vs. arrancar ya la campaña con la cobertura actual (~7 días M1 + H1/H4 años).**
7. **Gestión de la BD heredada:** STATE_OF_TRUTH declara 230 estrategias certificadas v5.4.0 y 258 catalogadas, pero la gobernanza más reciente (17_PHASE2) declara "NO STRATEGY IS CERTIFIED BY ASSUMPTION" tras la auditoría forense. Decidir el estatus real de ese catálogo: re-validar todo bajo pipeline actual, o archivarlo como legacy no certificado.

---

## 5.1 DECISIONES RESUELTAS POR EL USUARIO (2026-08-31) — CIERRE DE §5

El 2026-08-31 el usuario respondió a las 20 preguntas del Orquestador. Las 20 respuestas están
selladas en `orchestration/DOCTRINA_ORQUESTADOR.md §14` y son **no renegociables**. Cierre de §5:

| Decisión abierta de §5 | Estado | Resolución |
| :--- | :--- | :--- |
| 1. Fuente de datos 5m CME/forex | ✅ **RESUELTA** | **Coste 0 €** con proxies equivalentes. Verificado físicamente por el Orquestador: el datafeed público de **Dukascopy** sirve ticks bid/ask reales sin API key (`USA500IDXUSD`→ES, `USATECHIDXUSD`→NQ, `USA30IDXUSD`→YM, `XAUUSD`→GC, `XAGUSD`→SI, `LIGHTCMDUSD`→CL + FX majors), con ≥10 años de profundidad. Aviso: el volumen es **de tick del broker**, no del contrato CME (verificado: 100 % de barras con volumen > 0 en `USA500IDXUSD`, 49 ticks/barra, spread medio 0,50 pts). |
| 2. Puerto web canónico (3000 vs 3005) | ✅ **RESUELTA** | El canónico es **3005** (la realidad física manda). La documentación se alinea a 3005; el health-check de la API debe apuntar ahí. |
| 3. Cobertura mínima de barras por celda | ⏳ Se fija en la Fase 3 | La define el planificador de la cola de minería, con el dato de cobertura real por celda tras la ingesta Dukascopy. |
| 4. Uso de los 2–3 meses de 5m CME/FX ya importados | ✅ **RESUELTA** | Se usan como **muestra de control** para medir la divergencia proxy↔CME real (correlación y spread). Deja de ser la fuente principal. |
| 5. Alcance de TRACK_FONDEO en el MVP | ✅ **RESUELTA** | Ambos perfiles (ULTRA y FONDEO) se generan desde el inicio (Fase 3), pero **la gestión de cuentas prop queda pospuesta** (decisión #10): la prioridad exclusiva es generar estrategias. |
| 6. Backfill M1 cripto vs. arrancar campaña | ✅ **RESUELTA** | **Ambos en paralelo.** El backfill sigue; la campaña arranca con la cobertura disponible y las celdas se activan a medida que alcanzan cobertura. |
| 7. Catálogo heredado (230 "certificadas") | ⏳ Depende de la Fase 0 | El veredicto de la auditoría del changeset `23c8733a9..245009fef` determina si se revalida o se archiva como legacy no certificado. |

### 5.1.1 Parámetros de riesgo actualizados (deroga valores anteriores)
- **ULTRA: 70 % DD realizado · 80 % DD flotante** (el 75 % que figura en §1 y en docs antiguos queda derogado).
- **Apalancamiento ULTRA: hasta 500x nominal en BingX**, gestionado dinámicamente por IA, con cap duro
  por el máximo real que ofrezca el exchange en cada par.
- **Dimensionamiento 100 % en porcentajes**, agnóstico al capital nominal.
- **Objetivo ULTRA: ~100 % mensual.** Es una meta, no un permiso para maquillar resultados.
- **Arranque 100 % paper/demo.** Capital real solo con autorización explícita del usuario.
- **Killzones y filtro de noticias: capa POSTERIOR de optimización**, nunca dentro de la generación inicial.
- **Meta-estrategias: router dinámico con debate IA multi-activo**, sin reglas hardcodeadas.

### 5.1.2 Reorganización documental del 2026-08-31
La raíz del repo pasó de 11 a 3 `.md` (`README.md` reescrito como índice, `AUTHORITY_GRAPH.md`,
`GEMINI.md`) y `docs/` de 19 a 8 documentos canónicos. Todo lo superado se movió con `git mv` a
`docs/archive/` (**cero borrados**), trazado en `docs/archive/MANIFIESTO_REORGANIZACION_2026-08-31.md`.
El índice de vigencia de §6 sigue siendo válido en cuanto a *qué* está vigente; las **rutas** de los
documentos SUPERSEDED son ahora `docs/archive/`, `docs/archive/root/` y `docs/archive/Estado/`.

---

## 6. ÍNDICE DEL RESTO DE DOCS (qué queda vigente y qué está SUPERSEDED)

- **Vigentes (sin banner):** este doc, `AUTHORITY_GRAPH.md` (raíz), `docs/VERSION_GOVERNANCE_AND_CONTROL.md`, `docs/ULTRARENTABLE_PRINCIPLES.md`, `docs/ARCHITECTURE_CURRENT.md` (cadena de verdad, coherente), `docs/18_STRATEGIES_PAGE_SPEC.md` (spec de página vigente), `docs/tradesfera/*` (corpus de negocio, certificado), `docs/MULTIAGENTE_Y_SEGUIMIENTO.md` (modelo de trabajo orquestador+subagentes, vigente), `docs/Gestion de Capital — Balas y Estados.md` (diseño de negocio vigente), corpus de investigación (`docs/Investigacion/`, `docs/Fondeo/`, `docs/conexiones_automatizar/`, `docs/plan_implementacion/`) como **material de referencia**, y `docs/archive/` (ya archivado de por sí).
- **SUPERSEDED (banner añadido 2026-08-29, contenido intacto) — 27 docs:** raíz: `ESTADO.md`, `ARCHITECTURE.md`, `README.md`, `SYSTEM_DOCTRINE.md`, `SPEC_MASTER_ULTRA_VS_FONDEO.md`, `Plan 10 Fases.md`, `walkthrough.md`, `AUDIT_FINAL_REAL_ONLY.md`; `docs/`: `STATE_OF_TRUTH.md`, `ARCHITECTURE.md`, `PLAN_DE_EJECUCION_MAESTRO_ADAPTATIVO.md`, `Dashboard Web.md`, `Motor StrategyQuant X.md`, `Motor de Fondeo y Prop Firms.md`, `Ultrarentable - Ficha anterior 2026-08-03.md`, `Ultrarentable_Residuales.md`, `FIX_RECORD_20260809.md`, `AUDIT_BASELINE_2026-08-19.md`, `AUDIT_2026-08-25_APPROVED_METRICS.md`; `docs/Estado/`: `PLAN_MAESTRO_12_FASES.md`, `MVP_BUILD_PLAN.md`, `PHASED_BUILD_PLAN.md`, `CURRENT_IMPLEMENTATION_STATUS.md`, `IMPLEMENTATION_GAP_ANALYSIS.md`, `estado_sistema_real.md`, `ORQUESTACION_MOTOR_BUSQUEDA_20260809.md`; `docs/Estado/auditoria/00_INDICE_Y_CABECERA.md`. Ver el banner en la cabecera de cada uno para el motivo exacto.
- **Regla de conflicto:** si cualquier doc dice algo distinto a este documento, manda este documento (y si este está desactualizado respecto a la realidad física, se corrige aquí primero).

---

## 7. SUBPROYECTO ULTRA_MATRIX (pipeline de estrategias SQX) — añadido 2026-08-29

> **Ubicación documental:** `estrategias_um/` (carpeta propia, autocontenida, con README-mapa).
> Motor StrategyQuant X headless (sqx.service, API 5050) + proyecto Ultra_Matrix. Mandato del usuario: AUTOSUFICIENCIA (evidencia propia, no fábrica/docs) y SOLO la línea de estrategias: buscar → validar → mejorar → meta-estrategias → estudios.
> **Estado 2026-08-29:** embudo con caudal 0 validadas (fusible MC por trades=0, mechanism verificado); semillero legacy "Last generation" con ~91-93 crudas reales en memoria; plan de reestructuración por fases listo en `estrategias_um/docs/PLAN_PIPELINE.md`, pendiente de aprobación del usuario antes de tocar el motor.
> **Documentos:** README.md (mapa) · docs/ESTADO.md · docs/PLAN_PIPELINE.md · docs/META_PIPELINE.md · docs/CONFIG_DOORS.md · docs/FUNNEL.md · docs/FILTROS_ORGANICOS.md · docs/HECHOS_Y_DECISIONES.md · docs/DECISIONES_LOG.md · docs/RUNBOOK_OPERACION.md · evidencia/ (fechada, inmutable).
