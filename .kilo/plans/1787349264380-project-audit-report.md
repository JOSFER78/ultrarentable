# INFORME DE AUDITORÍA — Proyecto "01 Ultrarentable"

**Fecha:** 2026-08-22 · **Método:** lectura directa del código fuente (no de la documentación)
**Estado git:** árbol limpio, último commit `1560870` ("feat: implement universal backtest engine and contracts with automated evidence updates")

---

## 1. Qué es el proyecto (verificado en código)

Laboratorio cuantitativo de estrategias de trading con dos rutas (ULTRA/BingX cripto-perpetuos y FONDEO/prop firms CME):

- **Backend:** FastAPI (`services/api/`) sobre SQLite WAL, con pipeline de 11 "gates" de validación cuantitativa, evidencia JSON por candidato, y sincronización Firebase.
- **Nuevo motor v3.0.0 (commit actual):** `services/engine/` — `UniversalDeterministicBacktestEngine` (bucle barra-a-barra, indicadores dinámicos, sizing por riesgo, piramidación, hash Merkle de procedencia). Los 6 contratos nuevos en `contracts/` (universal_strategy, universal_ledger, instrument_specification, etc.) son código Pydantic v2 genuino y bien estructurado.
- **`EventBacktestEngine`** (`services/validation/engine/event_backtest_engine.py`) ahora es un adaptador fino que convierte `StrategySnapshot` → `StrategySpecification` y delega en el motor universal. Refactor correcto.
- **Frontend:** Next.js 16 en `apps/web/`, proxy hacia el puerto 8000, ~30 páginas.
- **Tests:** 319 tests coleccionables (suite raíz `tests/` + `services/api/tests/`).

La arquitectura del **nuevo motor universal es sólida**: determinista, sin hardcodes de estrategia, con registro bar-by-bar y hash de procedencia. Es la mejor parte del repo.

---

## 2. 🔴 CRÍTICO — La API sigue fabricando datos (viola doctrina REAL-ONLY)

Confirmado por grep en esta sesión; nada ha cambiado desde la auditoría previa:

| Archivo:línea | Fabricación |
|---|---|
| `services/api/app/api/candidates_router.py:265-266` | `engine_version` y `validation_pipeline_version` → `or "1.02"` hardcodeado (la versión vigente real es `2.0.0` según `services/engine_version.py:11`) |
| `candidates_router.py:260-262` | Anti-overfit inventado: `ratio_oos_is → 0.85`, `wfo_pass_pct → 85.0`, `monte_carlo_score → 90.0` cuando faltan datos |
| `candidates_router.py:174-193` | `gates_passed_count` **adivinado** (11/10/9/7/5) a partir de umbrales de PF/DD/trades, sin evidencia real de gates |
| `candidates_router.py:114-123` | Fechas y duraciones hardcodeadas (`2025-10-01`, 197 días…) cuando falta `duration_info`; `:153` fallback `oos_months = 6.0` |
| `candidates_router.py:401,491` | `dataset_sha256="sha256_verified"` — **hash falso literal** |
| `candidates_router.py:84` | Filtra por `CandidateModel.engine_version`, columna que **no existe en el ORM** (`services/api/app/db/database.py`) → 500 cuando se usa el parámetro |
| `services/api/app/api/firebase_sync_router.py:51` | Estado cloud hardcoded `"ONLINE"` sin comprobación real |
| `firebase_sync_router.py:161-162` | Mismo fallback `or "1.02"` |
| `services/semantic_ai/autonomous_discovery_engine.py:230,259` | `"sha256_verified_real"` — hash falso literal |

**Patrón sistémico:** `try/except` y `or` que devuelven valores inventados en lugar de fallar. En un sistema de certificación cuantitativa, esto invalida lo que la UI muestra como "certificado".

## 3. 🔴 El motor nuevo NO cobra funding (y la spec promete lo contrario)

En `services/engine/universal_backtest_engine.py`:
- `:101` `funding_cum = 0.0` — **nunca se incrementa en todo el bucle**.
- `:276` `funding_usd=0.0` en cada trade; `:455` `total_funding_usd` siempre 0.
- `ExecutionModel` sí define `funding_rate_8h` e `instrument_registry.py:72` define `default_funding_rate=0.0001`, pero el motor **los ignora**.

Consecuencia: para perpetuos apalancados 5x-15x mantenidos varias barras/semanas, el coste real de funding (0.01%/8h sobre el nocional apalancado) se omite → el PnL neto reportado está **sobreestimado**. Es la violación más directa de la invariante "tasas de funding siempre computadas de forma realista" del README.

## 4. 🔴 Entorno de desarrollo roto

Confirmado ahora mismo:
- `.venv/bin/pytest` y `.venv/bin/mypy` tienen shebang `#!/tmp/empty_dir/ultrarentable/.venv/bin/python3` → **binarios in-ejecutables**; el venv fue copiado desde otra ruta. Solo funcionan vía `python3 -m pytest`. Solución: `uv sync` para recrear el venv.
- npm raíz incompleto (hallazgo de la sesión previa): `tsx`/`ws` declarados en `package.json` pero ausentes de `node_modules` → `npm run ingest` falla.

## 5. 🟠 Deriva de versiones del motor (3 fuentes de verdad)

Existen simultáneamente:
- `services/engine_version.py:11` → `CURRENT_ENGINE_VERSION = "2.0.0"` (SSOT oficial)
- `services/engine/universal_backtest_engine.py:38` → `ENGINE_VERSION = "3.0.0"` (motor nuevo)
- API → fallback `"1.02"` (ver tabla de arriba)

El motor nuevo **no se registra** en `VERSION_HISTORY` ni en `engine_version.py`. Cualquier evidencia creada con `3.0.0` no coincide con lo que reporta `/api/v1/version`.

## 6. 🟠 Defectos menores del adaptador `EventBacktestEngine`

`services/validation/engine/event_backtest_engine.py`:
- `:280,283` `stop_loss_atr_period=14` hardcodeado (contradice la arquitectura "universal").
- `:292` toda estrategia convertida se etiqueta `StrategyFamily.MOMENTUM_BREAKOUT`.
- `:123,159-160,183` `to_canonical_ledger` hardcodea `leverage_actual=10.0` y `margin = notional/10` y convierte salidas `TIME_EXIT`/`LIQUIDATION` a `ExitReason.KILL_SWITCH`.
- `:76-94` dataclass `TradeRecord` con defaults `equity_before_usd=1000.0` — datos demo embutidos en el modelo.
- `:423` `min_liquidation_distance_pct=100.0` constante; el motor universal sí calcula precios de liquidación pero el adaptador los descarta.

## 7. 🟠 Estado de tests (ejecutados en la sesión previa, no ahora)

- **319 tests, 307 passed, 5 failed, 7 skipped** en total.
- Fallos reales: columna `portfolios.current_equity_usd` inexistente en el esquema (2 tests); test obsoleto que espera versión `'1.05'`; test no determinista por estado compartido (`test_candidates_endpoint_honest_reclassification`).
- `tests/` raíz **no tiene `conftest.py`** → escribe en la BD de producción; solo `services/api/tests/conftest.py` se aísla.
- Ruff (sesión previa): 2798 errores, 10 `F821` (nombres indefinidos = posibles `NameError`).

## 8. 🟡 Higiene del repo

- 8 scripts `test_*.py` en la raíz que no son tests (1 duplicado exacto de `tests/`, 1 con import imposible `nautilus_trader`, 4 scripts de investigación, 2 drivers sin `def test_`).
- `populate_real_ultra_candidates.py` contaminó la BD de producción con métricas hardcodeadas y contiene un `DELETE FROM candidates` destructivo — sigue en la raíz.
- `data/evidence/` (2720 JSON, 12 MB) se commitea y se regenera en cada run (los últimos 5 commits son churn de evidencia).
- `apps/web/app/page.tsx:759-811`: matriz de 44 activos con PF/ROI hardcodeados presentada como datos en vivo.

---

## Diagnóstico final

El **núcleo nuevo (motor universal + contratos) es de calidad alta** y el refactor del adaptador es correcto. Pero el proyecto tiene una fractura de integridad: **la capa de presentación/servicio (API y frontend) miente de forma sistemática** con fallbacks hardcodeados, mientras el motor nuevo —que es honesto— **omite el funding**, el coste que más castiga a las rutas apalancadas que el proyecto vende como núcleo del negocio.

### Orden de corrección recomendado

1. **Funding en el motor universal:** acumular `funding_cum` por barra/8h sobre nocional × `funding_rate_8h` y cobrarlo en cada trade (afecta directamente a la validez de todos los backtests).
2. **Eliminar fabricaciones de la API:** devolver `null`/404 cuando falte dato real; borrar `or "1.02"`, `gates_passed_count` adivinado, fechas hardcodeadas y `"sha256_verified*"`; quitar el filtro por columna inexistente `CandidateModel.engine_version`.
3. **Unificar versión:** registrar `3.0.0` en `services/engine_version.py` y que el adaptador use esa constante.
4. **Recrear entorno:** `uv sync` + `npm install`.
5. **Aislar tests:** portar el `conftest.py` a `tests/` raíz; añadir migración/columna para `portfolios.current_equity_usd`; envejecer o actualizar el test que espera `'1.05'`.
6. **Higiene:** mover los 8 scripts de raíz a `scratch/`, cuarentenar `populate_real_ultra_candidates.py`, sacar `data/evidence/` de git.
7. **Frontend:** sustituir la matriz hardcodeada de `page.tsx` por datos de `/api/v2/real/search-telemetry` o eliminarla.

### Validación tras los cambios
- `python3 -m pytest tests/ services/api/tests/ -q` debe dar 0 failed.
- Grep de `"sha256_verified`, `or "1.02"`, `ONLINE"` en `services/api` → 0 coincidencias.
- Backtest de referencia: ejecutar un caso con posición abierta >8h y verificar que `total_funding_usd > 0`.
- `uv sync && .venv/bin/pytest --version` debe funcionar directamente.
