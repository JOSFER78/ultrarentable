# Modelo de Decisiones del Autopiloto Ultra (v5)

## 1. Arquitectura de Decisión Autónoma

Cada decisión tomada por el `AutopilotController` se registra con trazabilidad inmutable en la tabla SQLite `autopilot_decisions`.

### Estructura de Decisión (`AutopilotDecisionModel`):
- `decision_id`: Identificador único (ej. `dec_a1b2c3d4`).
- `run_id`: Identificador de la ejecución activa.
- `module`: Módulo emisor (`UniverseScanner`, `OpportunityRanker`, `LeverageAutopilot`, `CandidateRepairer`).
- `decision`: Acción o elección tomada.
- `reason`: Justificación técnica de la decisión basada en métricas reales de liquidez, apalancamiento y rentabilidad FAST.
- `alternatives_json`: Alternativas consideradas y descartadas.

## 2. Flujo Decisional Autónomo

1. **Universe Scan**: El `UniverseScanner` evalúa los pares BingX disponibles y rankea por liquidez y volatilidad histórica.
2. **Selección de Oportunidad**: Se selecciona la oportunidad número 1 (ej. `ETH-USDT` 1h) sin fallbacks hardcodeados.
3. **Generación & Evolución**: La gramática tipada produce estrategias AST válidas por construcción.
4. **Escalera de Leverage Agresivo**: El `LeverageAutopilot` prueba apalancamientos escalonados hasta el máximo permitido por BingX para ese notional tier.
5. **Optimización de Parámetros**: `OptunaOptimizer` realiza el ajuste fino de periodos de indicadores y umbrales.
6. **Selección Kamikaze**: Ordenación estricta por capital final con descarte duro de liquidaciones.
