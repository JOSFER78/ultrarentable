# Informe de Implementación — DSL v1.0.0 y Compilador IR (Fase D)

## 1. Arquitectura de la DSL

Se ha implementado la especificación única DSL v1.0.0 compartida entre Python y TypeScript.

- **Contrato Schema**: `schemas/dsl_v1_strategy.json` (`additionalProperties: false` en todos los nodos).
- **Engine Python**: `services/api/app/dsl/engine.py` (Pydantic v2).
- **Seguridad**: Prohibidos `eval`, `exec`, Python/JS libre, imports y look-ahead (offsets negativos).
- **Operadores**:
  - Comparadores: `GT`, `GTE`, `LT`, `LTE`, `EQ`, `CROSS_ABOVE`, `CROSS_BELOW`
  - Lógicos: `ALL`, `ANY`, `NOT`
  - Series: `OPEN`, `HIGH`, `LOW`, `CLOSE`, `VOLUME`, `MARK_PRICE`, `INDEX_PRICE`, `FUNDING_RATE`, `OPEN_INTEREST`
  - Indicadores: `SMA`, `EMA`, `RSI`, `ATR`, `HIGHEST`, `LOWEST`, `ROC`, `STDDEV`, `VOLUME_RATIO`

## 2. Validación Semántica y Compilador IR

- **Validación Semántica**: Comprueba catálogo de instrumentos reales (`InstrumentModel`), límites de apalancamiento reales del venue, disponibilidad de series en el dataset y lookback máximo requerido.
- **Compilador IR**: Traduce la AST declarativa a un flujo de instrucciones IR de 3 direcciones (`LOAD_SERIES`, `COMPUTE_EMA`, `COMPARE_GT`, `ASSIGN_SIGNAL`, `CONFIGURE_POSITION`).
- **Verificación**: Genera `compilerVersion` (`1.0.0`), `dslHash` SHA-256 y `irHash` SHA-256 almacenado en `data/artifacts/compilations/<strategy_id>_<irHash>.json`.

## 3. Pruebas y Cobertura (12/12 PASSED)

El suite `services/api/tests/test_dsl.py` satisface todos los requisitos obligatorios:
1. `test_same_json_different_key_order_same_hash`: PASSED
2. `test_parameter_change_produces_different_hash`: PASSED
3. `test_unknown_property_rejected`: PASSED
4. `test_unknown_indicator_rejected`: PASSED
5. `test_negative_offset_rejected`: PASSED
6. `test_unavailable_series_rejected`: PASSED
7. `test_leverage_exceeds_venue_limit`: PASSED
8. `test_ast_and_ir_deterministic`: PASSED
9. `test_compilation_has_version_hash_artifact`: PASSED
10. `test_hash_stability_across_reparse`: PASSED
11. `test_no_forbidden_patterns_in_dsl_module`: PASSED
12. `test_required_series_extraction`: PASSED

## 4. Limitaciones y Próximos Pasos (Fase E)

- **Sin simulaciones ficticias**: No se calculan retornos ni métricas en la Fase D.
- **Transición a Fase E**: El ejecutor de backtest consumirá los artefactos IR compilados y verificados producidos por este compilador.
