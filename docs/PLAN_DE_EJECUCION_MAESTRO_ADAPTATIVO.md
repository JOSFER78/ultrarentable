# Plan de Ejecución Maestro Adaptativo — Ultrarentable V2 (2026)

> **Directiva:** REAL-ONLY. Cero datos simulados, cero mocks, cero fallbacks hardcodeados. Todo cálculo se ejecuta de forma determinista sobre series de velas reales y modelos Pydantic validados.

---

## 📌 Fases de Ejecución

### [x] FASE 0: Saneamiento REAL-ONLY y Contratos de Código (COMPLETADA)
- **Objetivo:** Dejar la base de código limpia de errores de importación, rutas fijas y bugs de contratos en `services/` y `tests/`.
- **Acciones Ejecutadas:**
  1. **`services/exploitation_engines/prop_firm_engine.py`:**
     - Añadido `Optional` en `typing`.
     - Ejecutado `PropFirmRules.model_rebuild()` para compatibilidad total con Pydantic v2.
  2. **`services/strategy_core/spec.py` y `services/strategy_core/validator.py`:**
     - Definidos enums canónicos `AssetClass` y `StrategySource`.
     - Alias `RuleCondition = RuleConditionSpec` para compatibilidad de tipos.
     - Añadido validador flexible en `StrategySpec` (`_normalize_flexible_input`) y propiedades `@property symbol` y `@property close_at_session_end`.
  3. **`services/sqx_bridge/ingest_sqx_results.py`:**
     - Eliminada ruta absoluta hardcodeada `/home/ubuntu/...` sustituida por resolución dinámica `Path(__file__).resolve().parent.parent.parent`.
  4. **`tests/test_sqx_bridge.py`:**
     - Gestión limpia y robusta del estado `ONLINE` / `OFFLINE` del servidor MCP de StrategyQuant X.
  5. **Verificación de Tests:**
     - Ejecución de `pytest tests/ -v` arrojando **12 tests PASSED, 1 SKIPPED (SQX offline), 0 FAILED**.

---

### [ ] FASE 1: Motor Multi-Arquetipo y Expansión Cuantitativa
- Integración de arquetipos matemáticos adicionales (`VOLATILITY_EXPANSION`, `TREND_FOLLOWING_EMA`, `MOMENTUM_BREAKOUT`, `MEAN_REVERSION`, `RSI_DIVERGENCE`, `DONCHIAN_CHANNEL`).
- Validación exhaustiva de comisiones y slippage en BingX Crypto y CME Futuros.

---

### [ ] FASE 2: Ingesta Determinista y Persistencia SQLite / WAL
- Sincronización continua de candidatos evaluados hacia SQLite sin duplicidad de métricas.
- Índices de ordenación de alta velocidad por beneficio OOS y ruta.

---

### [ ] FASE 3: Interfaz de Usuario y Telemetría en Tiempo Real
- Control Center con paginación optimizada (`25 | 50 | 100` por página).
- Selector de rutas desacoplado (`ULTRA` vs `FONDEO`).
- Vista detallada de ADN con curvas de capital IS/OOS reales.
