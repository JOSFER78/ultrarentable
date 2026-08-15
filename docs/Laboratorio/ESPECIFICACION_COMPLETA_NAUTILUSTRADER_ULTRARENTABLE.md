# Especificación completa — Sistema de búsqueda de estrategias ultrarrentables con NautilusTrader

**Fecha de investigación:** 29 de julio de 2026  
**Mercado inicial recomendado:** ETH perpetual en Hyperliquid  
**Objetivo de descubrimiento:** rentabilidad histórica neta igual o superior al 1000% en la ventana objetivo.  
**Equivalencia:** +1000% = capital final 11 veces el capital inicial.  

## 1. Decisión principal

NautilusTrader no debe intentar hacerlo todo. Su papel es ser el motor canónico de simulación y el motor de ejecución. El sistema completo necesita estas capas:

1. Investigación automática de ideas.
2. Formalización en una DSL tipada.
3. Generación aleatoria y programación genética.
4. Criba vectorizada rápida.
5. Optimización numérica.
6. Orquestación distribuida.
7. Backtest canónico event-driven con L2.
8. Verificador independiente.
9. Diagnóstico de selección múltiple y regímenes.
10. Shadow mainnet.
11. Hyperliquid testnet.
12. Micro-live y realimentación.

## 2. Stack recomendado

| Capa | Herramienta principal | Uso |
|---|---|---|
| Investigación | RD-Agent(Q) adaptado + agentes LLM | Crear hipótesis, implementar experimentos y aprender del feedback. |
| Representación | DSL propia en YAML/JSON | Reglas reproducibles y seguras. |
| Generación | DEAP Genetic Programming | Árboles tipados, mutaciones y cruces. |
| Criba | VectorBT | Explorar grandes poblaciones sobre barras. |
| Optimización | Optuna TPE + CMA-ES | Parámetros mixtos y continuos. |
| Paralelización | Ray Tune / Ray Core | Workers, checkpoints y recuperación. |
| Backtest canónico | NautilusTrader | L2, trades, fills, latencia, margen, funding y liquidación. |
| Datos | Hyperliquid S3 + captura propia | Ruta de coste bajo. |
| Datos profesionales | Tardis | Replay granular a catálogo Parquet de Nautilus. |
| Segundo motor | Replay independiente; LEAN opcional | Auditoría operación a operación. |
| Ejecución | NautilusTrader Hyperliquid adapter | Testnet y mainnet. |

StrategyQuant X y Build Alpha son proveedores opcionales de estrategias semilla. Sus métricas originales no deben conservarse: toda estrategia importada debe repetirse desde cero en el laboratorio.

## 3. Política de selección Kamikaze

### Restricciones duras

Una prueba es inválida únicamente cuando ocurre alguno de estos casos:

- equity mínima menor o igual a cero;
- liquidación;
- error de simulación;
- fuga de datos o look-ahead;
- fill imposible;
- costes, funding o margen omitidos;
- resultado no reproducible.

### No son filtros

Se calculan y almacenan, pero no eliminan candidatos:

- drawdown;
- Sharpe o Sortino;
- estabilidad;
- concentración del beneficio;
- pocas operaciones;
- sensibilidad paramétrica;
- fallar en otras ventanas;
- PBO o Deflated Sharpe.

### Score principal

```python
valid = simulation_ok and min_equity > 0 and not liquidated
score = -float("inf") if not valid else math.log(final_equity / initial_equity)
```

El nivel de evidencia se guarda por separado del score de rentabilidad.

## 4. Fábricas de estrategias

### 4.1 Investigación externa

Fuentes:

- papers y working papers;
- repositorios y notebooks reproducibles;
- documentación de exchanges;
- competiciones cuantitativas;
- foros técnicos;
- estrategias públicas de TradingView, Freqtrade y plataformas similares;
- StrategyQuant X y Build Alpha.

Cada idea se convierte en una ficha:

```yaml
hypothesis_card:
  source_url: "..."
  published_at: "..."
  market: "ETH perpetual"
  mechanism: "liquidation cascade continuation"
  required_inputs: [trades, l2, mark_price, open_interest]
  entry_logic: "..."
  exit_logic: "..."
  falsification_test: "..."
  leakage_risks: ["..."]
```

### 4.2 Programación genética

Usar DEAP con primitivas fuertemente tipadas:

- series de precio;
- series de volumen;
- funding;
- open interest;
- microestructura L2;
- operadores booleanos;
- comparadores;
- agregadores temporales con lag obligatorio;
- bloques de entrada, salida, sizing y ejecución.

No permitir Python libre generado por agentes dentro del motor.

### 4.3 Importadores

- StrategyQuant X → AST/reglas → DSL propia.
- Build Alpha/Python → señales → DSL.
- Pine Script → parser limitado o traducción auditada.
- Freqtrade → reglas y parámetros → DSL.

## 5. Familias prioritarias

1. Ruptura explosiva tras compresión de volatilidad.
2. Continuación o reversión de cascadas de liquidación.
3. Momentum condicionado por régimen.
4. Piramidación convexa a favor.
5. Extremos de funding condicionados por OI y precio.
6. Desequilibrios y agotamiento del libro L2.
7. Eventos y franjas horarias.
8. Ensemble adaptativo por régimen.

La optimización se hace por capas:

1. señal;
2. salida;
3. ejecución;
4. apalancamiento, compound y piramidación.

## 6. Datos

### Ruta de coste bajo

- Archivo S3 oficial de Hyperliquid para snapshots L2.
- Endpoints de funding, mark, metadata y margin tables.
- Grabador WebSocket propio para l2Book, trades, mark, funding y OI.
- Catálogo Parquet de NautilusTrader.

El archivo oficial se actualiza aproximadamente una vez al mes, puede tener huecos y cobra transferencia al requester.

### Ruta profesional

Tardis permite replay de:

- snapshots y deltas L2;
- trades;
- funding;
- mark/index;
- open interest;
- liquidaciones cuando estén disponibles.

La integración de Nautilus puede convertir el replay directamente a Parquet. El primer día de cada mes se puede usar sin clave de Tardis Machine; el resto requiere suscripción.

### Reglas de calidad

- UTC y nanosegundos.
- `ts_event` y `ts_init` separados.
- snapshots antes de deltas.
- detección de gaps, duplicados y eventos desordenados.
- checksums y manifiestos por partición.
- fees, leverage máximo, margin tiers y precisiones versionados por fecha.

## 7. NautilusTrader canónico

Última versión localizada durante la investigación: **1.227.0 Beta**, publicada el 18 de mayo de 2026.

Configuración mínima:

```python
venue = BacktestVenueConfig(
    name="HYPERLIQUID_SIM",
    oms_type="NETTING",
    account_type="MARGIN",
    book_type="L2_MBP",
    starting_balances=["1000 USDC"],
    trade_execution=True,
    bar_execution=False,
    liquidity_consumption=True,
    queue_position=True,
    random_seed=campaign.seed,
)
```

Obligatorio para finalistas:

- L2 y trades;
- consumo de liquidez;
- latencia calibrada;
- fees y funding;
- mark price;
- reglas de margin tiers;
- liquidación Hyperliquid;
- rechazos y precisiones del venue;
- semillas y versión fijadas.

## 8. Optimización

Distribución de presupuesto recomendada:

- 40% exploración aleatoria/QMC/genética;
- 40% explotación con TPE/CMA-ES;
- 20% mutaciones radicales y búsqueda de novedad.

Pseudoflujo:

```python
for generation in campaign:
    ideas = research_agent.propose(memory, failures, regimes)
    population = gp_factory.create(ideas, parents, novelty_budget)
    fast = vector_engine.run(population, discovery_windows)
    top = rank(valid_survivors(fast), by="final_equity")
    tuned = optuna_refine(top)
    canonical = ray_map(nautilus_l2_backtest, tuned[:budget])
    audited = independent_replay(canonical.top_n)
    memory.store_all(population, fast, canonical, audited)
    parents = select_by_return_and_novelty(canonical)
```

## 9. Doble validación

### Motor A

NautilusTrader produce:

- órdenes;
- fills;
- fees;
- funding;
- margin calls;
- liquidaciones;
- equity.

### Motor B

Un replay independiente pequeño recibe:

- los mismos datos;
- las mismas decisiones;
- las mismas órdenes;
- reglas de fees y margen implementadas separadamente.

Compara por operación:

- timestamp;
- precio;
- cantidad;
- comisión;
- funding;
- realized/unrealized PnL;
- equity;
- liquidation state.

LEAN puede añadirse para los finalistas, pero requiere un brokerage model y datos personalizados para Hyperliquid.

## 10. Diagnósticos de sobreajuste

Se calculan sin usarlos como filtros obligatorios:

- Probability of Backtest Overfitting mediante CSCV;
- Deflated Sharpe Ratio;
- ventanas temporales ocultas;
- walk-forward;
- purga y embargo temporal;
- sensibilidad paramétrica;
- perturbación de latencia, slippage y orden de eventos;
- clasificación por régimen.

## 11. Producción

1. Replay de datos live sin órdenes.
2. Testnet para validar el sistema operativo.
3. Shadow mainnet para medir precios ejecutables y latencia.
4. Micro-live con tamaño mínimo.
5. Realimentación automática del fill model y latency model.

Testnet no certifica la rentabilidad porque su liquidez no replica mainnet.

## 12. Estructura del repositorio

```text
ultra_strategy_lab/
├── apps/web/
├── apps/api/
├── services/research_agent/
├── services/strategy_factory/
├── services/external_importers/
├── services/fast_screen/
├── services/optimizer/
├── services/orchestrator/
├── services/canonical_nautilus/
├── services/independent_validator/
├── services/live_shadow/
├── services/execution_node/
├── data/download_hyperliquid_s3/
├── data/record_live_feeds/
├── data/tardis_pipeline/
├── data/catalog/
├── packages/strategy_dsl/
├── packages/indicators_no_lookahead/
├── packages/venue_rules/
├── packages/experiment_contracts/
├── packages/evidence_metrics/
├── configs/campaigns/
├── configs/venues/
├── configs/execution_models/
├── tests/leakage/
├── tests/fill_engine/
├── tests/margin_liquidation/
├── tests/determinism/
├── tests/engine_parity/
└── artifacts/
```

## 13. Orden de implementación

1. Contratos y hashes.
2. Datos y manifiestos.
3. Motor canónico y escenarios manuales.
4. Motor rápido y paridad documentada.
5. Generador DEAP.
6. Optuna y Ray.
7. Agentes de investigación.
8. Segundo motor.
9. Panel web.
10. Testnet, shadow y micro-live.

## 14. Criterio de aceptación del MVP

El sistema está completo cuando puede:

- recibir una hipótesis nueva;
- formalizarla;
- generar miles de variantes;
- buscar explícitamente +1000%;
- guardar todos los intentos;
- repetir finalistas en Nautilus L2;
- comparar con un segundo motor;
- ejecutar la misma estrategia en shadow/testnet;
- medir la divergencia real;
- realimentar la simulación;
- mostrar por separado retorno rápido, canónico, independiente y real.

## 15. Fuentes principales

- NautilusTrader docs: https://nautilustrader.io/docs/latest/
- Nautilus backtesting: https://nautilustrader.io/docs/latest/concepts/backtesting/
- Hyperliquid adapter: https://nautilustrader.io/docs/latest/integrations/hyperliquid/
- Releases: https://github.com/nautechsystems/nautilus_trader/releases
- Hyperliquid historical data: https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
- Hyperliquid liquidations: https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations
- Tardis integration: https://nautilustrader.io/docs/latest/integrations/tardis/
- RD-Agent(Q): https://github.com/microsoft/RD-Agent
- DEAP GP: https://deap.readthedocs.io/en/stable/api/gp.html
- VectorBT: https://vectorbt.dev/
- Optuna: https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
- Ray Tune: https://docs.ray.io/en/latest/tune/
- StrategyQuant workflow: https://strategyquant.com/doc/strategyquant/workflow/
- Build Alpha Python: https://www.buildalpha.com/python-trading-strategy-builder/
- PBO paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253
- Deflated Sharpe: https://doi.org/10.3905/jpm.2014.40.5.094
