# LIMPIEZA Carril 2 — Homónimos de "meta-estrategia" y umbral de `scripts/meta.py`

**Auditor:** Hermes (subagente Carril 2) · **2026-09-01** · Evidencia por grep e importadores reales.

## 1. Los cuatro homónimos

| Módulo | Importadores reales (fuera de sí mismo) | Estado |
| :--- | :--- | :--- |
| `services/portfolio/meta_strategy_engine.py` | `scripts/meta.py`, `scripts/fondeo_examen.py`, `tests/test_meta_strategy_engine.py` | ✅ **SSOT VIVO** — motor de producción: DB canónica (`STATE_DB_PATH`), `EventBacktestEngine`, persistencia SHA-256 en tabla `meta_portfolios`, dedupe de activos (`DuplicateAssetError`), correlación cruzada real. Confirmado además por decisión sellada en `orchestration/state/plan/bloques/F00_limpieza.md` ("No se toca `services/portfolio/meta_strategy_engine.py`"). |
| `services/portfolio/meta_ensemble_service.py` | Carril 1 (en reparación) | Vivo, fuera de este carril — no tocado. |
| `services/portfolio/meta_strategy_pipeline.py` | Carril 1 (en reparación) | Vivo, fuera de este carril — no tocado. |
| `services/discovery/meta_strategy_engine.py` | **Solo** `tests/discovery/test_adaptive_hypothesis_and_meta.py` (una función, `test_meta_engine_rejects_unproven_members`) | ❌ **MUERTO** — retirado en este commit. |

## 2. Prueba de muerte de `services/discovery/meta_strategy_engine.py`

- `git log --follow` muestra un único commit de origen: `a4987758d feat(research): add evidence-driven meta-strategy engine`. Nunca se integró.
- `services/discovery/__init__.py` **no lo exporta** (`__all__ = ["UltraDiscoveryEngine", "FundingDiscoveryEngine"]`).
- `grep -rn "discovery.meta_strategy_engine\|discovery/meta_strategy_engine"` en todo el repo (`.py`, `.md`, `.json`, `.yaml`, `.txt`) solo devuelve el propio test que lo importa.
- Ningún componente de producción lo referencia: `discovery_validation_pipeline.py`, `ultra_discovery.py`, `funding_discovery.py` no lo tocan.
- Su única función probada, `test_meta_engine_rejects_unproven_members`, ejercita exclusivamente la lógica interna del propio módulo muerto (un `StrategyEvidence` sintético con `robustness_passed=False`), no ningún camino de producción.
- Su lógica de diversidad (correlación par a par, selección greedy, `quality = pf * (1 - dd/100)`) está **subsumida y superada** por el motor real: `services/portfolio/meta_strategy_engine.py` ya calcula matriz de correlación cruzada real (`average_cross_correlation`, `correlation_matrix`) sobre retornos OOS reales, con persistencia SHA-256 y motor de backtest determinista — no aporta nada que el SSOT no tenga ya, con evidencia más rigurosa (datos reales de BD, no `StrategyEvidence` sintética pasada en memoria).

**Decisión:** retirado a `cuarentena/servicios_muertos/discovery_meta_strategy_engine.py` (hash SHA-256 en `cuarentena/servicios_muertos/MANIFEST_SHA256.txt`). El test que lo importaba se editó quirúrgicamente para retirar solo esa función + el import ahora roto; el resto del fichero (`AdaptiveHypothesisEngine`, `StrategySearchRegistry`) sigue vivo y sin tocar.

## 3. `scripts/meta.py` — umbral `--min-trades` desalineado con Criterio 1.1

Antes: `--min-trades` por defecto **20**. El suelo SELLADO del Criterio 1.1 (`REGLAS_INVARIANTES.md`) son **200 trades OOS**. Ningún aviso marcaba un ensamblado hecho con 20 como no conforme; salía indistinguible de una meta-estrategia certificable.

**Fix aplicado:**
- Nueva constante `SUELO_SELLADO_TRADES_OOS = 200`, que ahora es el valor por defecto de `--min-trades`.
- Verificado en ejecución real (`nice -n 19 ionice -c 3 python3 scripts/meta.py --route AMBOS`, 2026-09-01): con el suelo sellado, hoy el script falla cerrado en ambas rutas (`NO DATA`, 0 activos ULTRA con ≥200 trades OOS de 5 candidatas 25-68, 0 candidatas FONDEO) — refleja la verdad medida, no una meta-estrategia fabricada con evidencia insuficiente.
- Si se baja `--min-trades` explícitamente por debajo de 200 (modo exploratorio), la marca de no conformidad es **imborrable** en tres capas:
  1. Consola: banner `NO_CONFORME_CRITERIO_1_1` al entrar y en el veredicto final.
  2. JSON de salida (`orchestration/results/meta_resultados.json`): `veredicto` queda prefijado `NO_CONFORME_CRITERIO_1_1__<VEREDICTO>` y se añaden los campos explícitos `criterio_1_1_conforme`, `min_trades_usado`, `suelo_sellado_criterio_1_1`.
  3. Persistencia en la BD canónica (tabla `meta_portfolios`, vía `assemble_meta_portfolio(custom_name=...)`): `portfolio_id` pasa a `EXPLORATORIO_NOCONFORME_C11_<ruta>_<ts>` y el campo `name` lleva el prefijo `[NO_CONFORME_CRITERIO_1_1 min_trades=N<200]` — queda escrito en el registro histórico inmutable, no solo en un log volátil.

## 4. Otros sitios que ensamblan/listan meta-estrategias con umbral propio (reportados, NO tocados — Carril 1 o fuera de alcance)

Búsqueda: `grep -rn "min_trades\|MetaStrategyEngine\|MetaEnsembleService\|assemble_meta_portfolio\|meta_strategy_pipeline" services/ scripts/ apps/web`.

- **`services/portfolio/meta_ensemble_service.py::assemble_meta_portfolio`** (Carril 1) — filtra candidatos solo por `status` (`APPROVED_CURRENT_ENGINE`, `APPROVED`, `ULTRA_CERTIFIED`, `FUNDING_CERTIFIED`, `CERTIFIED_PASS`, `CERTIFICADA_TIER_1`) y por `engine_version` no obsoleto (Regla #26). **No comprueba `trades_oos >= 200` en ningún punto.** Es el mismo hueco que motivó esta tarea, en un módulo distinto.
- **`services/portfolio/autonomous_meta_daemon.py`** — daemon 24/7, arrancado automáticamente en `services/api/app/main.py` (`autonomous_meta_daemon.start_autonomous(interval_seconds=60)`). Cada 60s llama a `MetaEnsembleService.assemble_meta_portfolio(candidate_ids=ultra_cands[:4], ...)` — toma los 4 primeros candidatos ULTRA que cumplan `status`, sin ningún filtro de `trades_oos`. **Es el camino de producción más expuesto**: corre solo, sin intervención humana, y hereda el mismo hueco de `meta_ensemble_service.py`.
- **`services/portfolio/portfolio_router.py::POST /assemble`** — endpoint API que expone manualmente el mismo `MetaEnsembleService.assemble_meta_portfolio` sin control adicional de `trades_oos`.
- **`services/portfolio/meta_strategy_pipeline.py::build_meta_for_route` / `ensure_meta_strategies`** (Carril 1) — filtra solo por `CERTIFIED_STATUS = "APPROVED_CURRENT_ENGINE"`, mismo hueco. Se consume desde `services/api/app/api/certified_summary_router.py::GET /meta-strategies` (endpoint público del catálogo).
- `services/portfolio/meta_strategy_engine.py::load_candidates_from_db` / `assembly_readiness` (el SSOT, no tocado en este carril) **sí** exponen un parámetro `min_trades_oos` (documentado como "criterio de base válida del plan (≥200 operaciones)"), pero su **valor por defecto es 0** — el filtro existe pero no se aplica salvo que el llamador lo pase explícitamente. `scripts/meta.py` ya no lo necesita (filtra antes, en `seleccionar_ortogonales`), pero cualquier otro llamador futuro de este motor puede omitir el argumento y colarse con 0 trades. Reportado, no tocado (motor sellado por decisión de F00.1).

**Conclusión:** el hueco de `scripts/meta.py` era el síntoma visible, pero la causa está más extendida — está en los dos módulos de Carril 1 y, por herencia, en el daemon autónomo 24/7 y en dos endpoints de API que dependen de ellos. Corresponde a Carril 1 aplicar el mismo suelo de 200 trades OOS (o pasar explícitamente `min_trades_oos=200` al SSOT) en `meta_ensemble_service.py` y `meta_strategy_pipeline.py`.

## 5. Tests

- `tests/discovery/test_adaptive_hypothesis_and_meta.py`: se retiró la función `test_meta_engine_rejects_unproven_members` y el import de `services.discovery.meta_strategy_engine` (módulo movido a cuarentena). El resto del fichero (`AdaptiveHypothesisEngine`, `StrategySearchRegistry`) queda intacto.
- `tests/test_meta_strategy_engine.py` — no modificado; sigue importando el SSOT real y pasa (ver ejecución abajo).
