# Informe de Entrega — Fase F: Fábrica Autónoma de Estrategias & Campaigns Autopilot

## 1. Resumen de Implementación

Se ha implementado el sistema completo de generación, optimización, reparación y selección de estrategias autónomas.

- **Ubicación del paquete**: `services/api/app/factory/`
  - `grammar.py`: Gramática tipada que construye árboles AST válidos por construcción.
  - `seed_factory.py`: Generador de población inicial con plantillas cuantitativas y gramática procedimental.
  - `genetic.py`: Operadores genéticos de mutación estructural y cruce de condiciones/gestión monetaria.
  - `optimizer.py`: Integración con Optuna (TPE, QMC, CMA-ES) para afinación paramétrica.
  - `repairer.py`: Reparación dirigida basada en motivos de fallo (`LIQUIDATED`, `NO_TRADES`, `FEES_DOMINATE`, etc.).
  - `selection.py`: Selección Kamikaze ($f = \log(\text{equity}_{\text{final}} / \text{capital}_{\text{inicial}})$, descarte duro de liquidaciones/errores) y `NoveltyArchive`.
  - `orchestrator.py`: Orquestador de campañas local reanudable con SQLite WAL.

## 2. Experiencia de Usuario — Campaigns Autopilot

- La interfaz `/campaigns` es la consola principal. El usuario selecciona únicamente parámetros de alto nivel (símbolo `AUTO` o específico, timeframe `AUTO`, presupuesto, capital y objetivo $11\times$).
- Un solo botón: `🚀 INICIAR BÚSQUEDA AUTÓNOMA`.
- Cero diseño de JSON o código manual exigido al usuario.

## 3. Endpoints API Creados

- `POST /api/v1/campaigns/autonomous`
- `POST /api/v1/campaigns/{id}/start`
- `POST /api/v1/campaigns/{id}/pause`
- `POST /api/v1/campaigns/{id}/resume`
- `POST /api/v1/campaigns/{id}/stop`
- `GET /api/v1/campaigns/{id}/population`
- `GET /api/v1/campaigns/{id}/events`

## 4. Resultados de Pruebas (6/6 PASSED)

- `test_typed_grammar_generates_valid_strategy_ast`: PASSED
- `test_seed_factory_generates_population`: PASSED
- `test_genetic_operators_mutation_and_crossover`: PASSED
- `test_directed_repairer`: PASSED
- `test_kamikaze_selection_filters_failures`: PASSED
- `test_autonomous_campaign_orchestration`: PASSED

## 5. Próximos Pasos (Fase G)

- Integración del motor canónico NautilusTrader con libro de órdenes/eventos BingX y ledger independiente para validar los candidatos `FAST_TARGET_HIT`.
