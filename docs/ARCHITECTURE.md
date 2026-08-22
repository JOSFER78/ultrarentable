# ULTRARENTABLE — ARQUITECTURA

Estado real del sistema tras la FASE 1 del master refactor (rama
`feature/desarrollo`). Los diagramas describen lo que ES, no lo que se desea.

## Visión general

```
apps/web (Next.js App Router)        services/api (FastAPI)           datos
  6 fases /estrategias/*  ──fetch──▶  routers v1/v2  ──▶  SQLite WAL (fuente primaria)
  lib/strategyPhases.ts              validation/gates      data/evidence/*.json (evidencia)
  (fuente única de fases)            sync/firebase         Firebase RTDB (réplica push 1-way)
```

## Módulos

- **Frontend** (`apps/web`): 37 páginas. El hub `/estrategias` monta las 6 fases
  (re-exports de `/sistema`, `/strategies`, `/candidatos`, `/research`, `/gates`,
  `/portfolio`). Fases definidas UNA vez en `lib/strategyPhases.ts`;
  `components/EstrategiasHeaderNav.tsx` deriva de ahí.
- **Backend** (`services/api`): FastAPI en `app/main.py` (routers v1: routes,
  candidates, gates, sqx, discovery, research, portfolios...; v2: telemetry,
  validation, semantic, ultra, real_data — este último montado 2×, deuda conocida).
- **Validación** (`services/validation`): FSM canónica (`candidate_registry`),
  certificación (`certification_registry`, 11 gates), suite de gates A
  (`services/api/app/validation/gates/`, usada por el pipeline).
- **Motores de backtest** (3, consolidación pendiente):
  1. `UltraRiskControlledEngine` — usado por discovery; EJECUTA UNA ESTRATEGIA
     FIJA EMA20/50+Donchian+vol (deuda crítica: el "discovery" solo barre
     multiplicadores SL/TP). Métricas fabricadas eliminadas en FASE 1.
  2. `FastEngine` DSL/IR (`services/api/app/engine/`) — riguroso, fees de DB;
     usado por `/backtests/fast`.
  3. `UniversalDeterministicBacktestEngine` (`services/engine/`) — el diseño
     canónico (StrategySpecification → ledger Merkle); aún desconectado del pipeline.
- **Evidencia** (`data/evidence/<estrategia>/gate_XX_*.json`): base de
  certificación. Escrita por la automatización en vivo.
- **Sync** (`services/sync/firebase_sync_manager.py`): push one-way SQLite→RTDB,
  sin resolución de conflictos (SQLite manda, siempre).

## Dependencias permitidas

```
contracts/  ◀── services/*  ◀── apps/web (vía API JSON, nunca import directo)
strategyPhases.ts ◀── páginas/nav de apps/web
contracts/gate_directory.py ◀── gates_router (y futuros consumidores)
```

- Las páginas NO dependen unas de otras para obtener estado; todas consultan la
  capa API/dominio.
- `contracts/` no importa de `services/` ni de `apps/`.

## Deuda conocida y plan (FASES 4-8 pendientes)

1. **Motor**: conectar el discovery al `UniversalDeterministicBacktestEngine`
   (estrategia como especificación, no fija). Prioridad máxima de las fases restantes.
2. **6 interfaces `Candidate` duplicadas** en el frontend → crear
   `apps/web/types/candidates.ts` (DTO único) y re-conectar las 6 páginas.
3. **Clasificación TIER reimplementada 4×** → un selector de dominio compartido.
4. **Polling duplicado** (`/api/v2/real/search-telemetry`×3, revalidate×2) →
   capa común de query/cache (o React Query) + SSE existente.
5. **Rutas legadas** (`/strategies`, `/candidatos`, ...) aún son implementaciones
   completas re-exportadas → convertirlas en `redirect()` y mantener una sola
   implementación bajo `/estrategias/*`.
6. **Estados**: 5 vocabularios coexisten (FSM canónica, strategy_core, DB español,
  alias API, tiers) → mapear todos a `StrategyLifecycleStatus`.
7. **Suites de gates B** (`services/validation/engines/`, Gate 11 = EnsembleSynergy)
   diverge de la suite A (Gate 11 = Nautilus) → consolidar sobre
   `contracts/gate_directory.py`.
8. **real_data_router v2** fabrica `canonical_hash`/symbol/route por matching de
   strings → derivar de datos reales o deprecar.

## Operación

- VPS: `oracle-vps` (143.47.35.167), repo en `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`.
- La automatización escribe `data/evidence/*` en vivo: no hacer `git reset --hard`
  ni `checkout` que descarte el árbol de trabajo sin revisar.
- Guardia de regresión: `python3 tests/test_zero_mocks.py`.
