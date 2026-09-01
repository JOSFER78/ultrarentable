# MOTIVO — cuarentena de `deep_strategy_improver.py` (2026-09-01)

> Decisión del ORQUESTADOR LOCAL a petición del carril MEJORA (expediente
> `orchestration/results/I2_diseno_mejora.md` §1, §4.1 y §6), verificada con comandos propios
> antes de mover nada.

**Qué hace el fichero**: `services/api/app/factory/deep_strategy_improver.py` (168 LOC) no ejecuta
ningún backtest. Fabrica "métricas mejoradas" multiplicando las de entrada por constantes fijas
(`pf_gain_multiplier = 1.30 / 1.18`, `new_pf = max(1.35, prev_pf * mult)`, reducción de DD por
factor) y fuerza `status = "CERTIFIED_PASS"` y `tier = "TIER_1_CERTIFIED"` incondicionalmente
(líneas 97-140 del original). Es una violación de libro de la Regla 1 (REAL-ONLY). El propio
historial del repo ya lo tenía fichado como **LEAK-02 (SEV-1)** en
`.agents/informe&seguimiento/03_HANDOFF_AG2-P01-001.md` y lo fue difiriendo cuatro entregas.

**Por qué se mueve ahora y no se reescribe**: está **inerte** — `grep -rn "deep_strategy_improver\|DeepStrategyImprover"`
sobre `services/ scripts/ tests/ apps/` devuelve solo el propio fichero; `factory/__init__.py` no lo
importa. Su pureza de imports (0 internos, `grafo_imports_2026-09-01.md`) lo hacía candidato a
"mover barato" a `services/improvement/` (Movimiento 2 de I7) confiando solo en el grafo; esta
cuarentena evita ese error. `services/improvement/` nace sin heredarlo.

**Cómo se ha movido**: `git mv` (historial conservado), ruta original preservada bajo esta carpeta,
hash en `MANIFEST.sha256`. Nunca se usó `rm`.
