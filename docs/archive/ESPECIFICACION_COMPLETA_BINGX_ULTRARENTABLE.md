# ESPECIFICACIÓN COMPLETA — BINGX ULTRA STRATEGY LAB

**Fecha de investigación:** 29 de julio de 2026  
**Venue único de mercado y ejecución:** BingX  
**Producto base:** BingX USDⓢ-M Perpetual Futures  
**Objetivo de descubrimiento:** rentabilidad histórica neta ≥ 1000% (equity final ≥ 11×)  
**Política:** no filtrar por drawdown, Sharpe, estabilidad ni probabilidad de ruina; invalidar únicamente simulaciones muertas o técnicamente falsas.

## 1. Decisión ejecutiva

NautilusTrader debe ser el motor canónico, pero BingX no aparece entre sus adaptadores oficiales actuales. El proyecto requiere un adaptador BingX propio sobre REST y WebSocket. El sistema completo combina:

1. Scanner vivo de contratos y reglas BingX.
2. Ingesta REST y grabador WebSocket L2/trades/mark/index/account.
3. Agentes de investigación y formalización.
4. DSL de estrategias fuertemente tipada.
5. Generación genética con DEAP.
6. Criba masiva con VectorBT/Numba.
7. Optimización con Optuna.
8. Paralelización y checkpoints con Ray.
9. Backtest canónico event-driven con NautilusTrader.
10. Validador independiente de PnL, fees, funding, margen y liquidación.
11. BingX prod-vst, shadow mainnet y micro-live.
12. Realimentación de fills, latencia y errores hacia el backtester.

## 2. Realidad del apalancamiento de 500×

BingX anuncia hasta 500× en determinados contratos TradFi, incluyendo forex, índices y commodities. No debe suponerse que BTC, ETH o cualquier cripto-perpetuo admita 500×. El máximo real depende de:

- símbolo y familia de producto;
- región y elegibilidad de la cuenta;
- tier nocional;
- tamaño y posiciones existentes;
- reglas vigentes en el momento de apertura;
- restricciones temporales de BingX.

Por ello, cada campaña comienza con un `RuleSnapshot` consultado a BingX. Una estrategia que solicita un leverage no permitido se marca como `INVALID_VENUE_RULE`, no como perdedora.

## 3. Política de selección Kamikaze

```python
valid = (
    simulation_ok
    and min_equity > 0
    and not fully_liquidated
    and no_lookahead
    and reproducible
    and venue_rules_valid
)
score = float('-inf') if not valid else math.log(final_equity / initial_equity)
```

No filtran:

- drawdown;
- Sharpe/Sortino;
- estabilidad;
- dependencia de pocas operaciones;
- sensibilidad paramétrica;
- pérdidas en otras ventanas;
- fragilidad por régimen.

Todas estas métricas se almacenan como diagnóstico y nivel de evidencia.

## 4. Proceso de 16 etapas

1. Snapshot de reglas BingX.
2. Backfill REST y grabación WebSocket.
3. Investigación de hipótesis.
4. Creación DSL y programación genética.
5. Criba vectorizada.
6. Optimización numérica.
7. Escalado distribuido.
8. Backtest canónico BingX/Nautilus.
9. Auditoría con segundo motor.
10. Ventanas ocultas y diagnóstico estadístico.
11. Prod-VST.
12. Shadow mainnet.
13. Micro-live.
14. Calibración real → simulador.
15. Reoptimización.
16. Biblioteca con linaje y evidencia.

## 5. Scanner de mercado BingX

Debe generar, por símbolo y timestamp:

- contract status;
- tick size y quantity step;
- min/max quantity y notional;
- max leverage por tier;
- maintenance margin rate;
- maintenance amount;
- maker/taker real de la cuenta;
- funding actual, histórico y siguiente settlement;
- horario y pausas;
- tipos de orden y referencias de trigger;
- disponibilidad y fee de Guaranteed Price;
- profundidad y spread observados;
- estado del API y límites.

## 6. Mecánica de precios BingX

Mantener tres series independientes:

- **Last price:** última ejecución BingX; PnL realizado y triggers según configuración.
- **Index price:** referencia compuesta de mercados externos.
- **Mark price:** valor razonable para PnL no realizado y liquidación.

Fórmula documentada:

```text
Price 1 = Index Price
Basis 5m = MA((Best Bid + Best Ask)/2 − Index Price)
Price 2 = Index Price + Basis 5m
Mark Price = median(Price 1, Price 2, Last Price)
```

BingX documenta un mecanismo dual: alcanzar el precio estimado de liquidación con el mark no basta si el last no ha alcanzado el nivel. El motor debe modelar mark y last evento a evento y validar la implementación con eventos reales de cuenta.

## 7. Fees y funding

Tasas públicas estándar encontradas:

- maker: 0,02%;
- taker: 0,05%.

El sistema no las hardcodea: consulta `/openApi/swap/v2/user/commissionRate` y guarda el snapshot por experimento.

Funding:

- se intercambia entre longs y shorts;
- en aislado afecta al margen de posición;
- en cruzado afecta al balance;
- el intervalo puede variar por símbolo (8h, 4h, 1h u otro);
- se carga únicamente si la posición está abierta en el timestamp de settlement.

Guaranteed Price:

- Guaranteed SL puede aplicar una tarifa dinámica cuando se activa el mecanismo;
- Guaranteed TP se anuncia sin fee específico, pero no debe tratarse como garantía absoluta de fill total;
- disponibilidad y coste deben capturarse desde la interfaz/reglas vigentes.

## 8. Margen y liquidación

```text
initial_margin = open_position_value / leverage
notional = mark_price × position_size
maintenance_margin = notional × MMR − maintenance_amount
```

La liquidación se activa cuando el riesgo alcanza o supera 100%, considerando maintenance margin y comisión de cierre. Deben simularse por separado:

- isolated margin;
- cross margin;
- hedge/net mode;
- partial/full liquidation;
- bankruptcy price;
- insurance fund semantics;
- cambios de tier;
- funding y fees que reducen el colateral.

## 9. Datos

### Bootstrap oficial

- contratos;
- trading rules;
- klines;
- mark-price klines;
- trades/historical trades;
- premium index;
- funding history;
- open interest;
- depth snapshot.

### Grabador propio obligatorio

- L2 snapshots/deltas;
- trades;
- mark/index/last;
- ticker y book ticker;
- funding;
- cuenta, órdenes, fills y posiciones;
- `ts_event` y `ts_recv`;
- secuencias, gaps, duplicados y drift de reloj.

No se ha localizado un archivo oficial completo de histórico L2 BingX. Un proveedor comercial solo se incorpora tras confirmar cobertura por símbolo y validar una muestra.

## 10. Adaptador BingX para NautilusTrader

NautilusTrader ofrece una arquitectura oficial para adaptadores, pero BingX no figura en su lista actual de integraciones. Implementar:

### Rust

- HTTP client;
- HMAC SHA-256;
- rate limits;
- retries y clasificación de errores;
- WebSocket GZIP/Ping-Pong;
- listenKey y renovación;
- parsing;
- PyO3 bindings;
- mock-server tests.

### Python

- `InstrumentProvider`;
- `LiveMarketDataClient`;
- `LiveExecutionClient`;
- factories y configs;
- prod/prod-vst separation;
- reconciliation y recovery.

CCXT se limita a bootstrap y prototipos.

## 11. Backtest canónico

Debe incluir:

- L2 y trades;
- fills parciales;
- maker/taker por fill;
- spread/slippage;
- latencia empírica;
- cancel/replace/rejects;
- mark/index/last;
- funding histórico;
- tiers y límites históricos;
- margin modes;
- dual-price liquidation;
- sesiones y gaps TradFi;
- reconciliación y determinismo.

## 12. Fábrica de estrategias

### Investigación

Agentes para fuentes, formalización y replicación.

### Evolución

DEAP con árboles fuertemente tipados. Bloques:

- precio/volumen/volatilidad;
- mark-last basis;
- funding/OI;
- L2 imbalance y aggression;
- calendario/sesión;
- entradas/salidas;
- órdenes;
- leverage/tamaño/piramidación.

### Importación

StrategyQuant, Build Alpha, Pine y Python solo aportan semillas. Todo se recompila a DSL y se revalida en BingX.

## 13. Optimización

- DEAP para estructura;
- VectorBT/Numba para criba;
- Optuna TPE/CMA-ES para parámetros;
- Ray para workers/checkpoints;
- promoción por equity neta de supervivientes;
- no early-stop por drawdown;
- stop técnico por liquidación, equity <= 0, datos corruptos o ejecución inválida.

## 14. Escalera de validación

1. Fast backtest.
2. Nautilus canónico.
3. Replay independiente.
4. Ventanas ocultas.
5. BingX prod-vst.
6. Shadow mainnet.
7. Micro-live.
8. Calibración y nueva campaña.

## 15. API y operación

Entornos:

- producción: `https://open-api.bingx.com`;
- simulated/VST: `https://open-api-vst.bingx.com`.

Controles:

- HMAC SHA-256;
- timestamp/recvWindow;
- NTP y drift monitor;
- token buckets por endpoint;
- 500 market-data requests/10s/IP según actualización de 2025;
- Ping/Pong y GZIP;
- listenKey con renovación;
- idempotencia de órdenes;
- reconciliación tras reconexión;
- límites de cancelación/anti-abuso.

## 16. Arquitectura de carpetas

```text
bingx_ultra_strategy_lab/
├── apps/{web,api}/
├── services/
│   ├── research_agent/
│   ├── strategy_factory/
│   ├── fast_screen/
│   ├── optimizer/
│   ├── orchestrator/
│   ├── bingx_market_scanner/
│   ├── bingx_recorder/
│   ├── canonical_nautilus/
│   ├── independent_validator/
│   ├── shadow_node/
│   └── execution_node/
├── adapters/nautilus_bingx/
├── packages/
│   ├── strategy_dsl/
│   ├── bingx_rules/
│   ├── liquidation_engine/
│   ├── execution_models/
│   └── experiment_contracts/
├── data/{raw_bingx_rest,raw_bingx_ws,normalized,nautilus_catalog}/
├── configs/{campaigns,symbols,prod-vst,production}/
├── tests/{adapter_contract,determinism,mark_dual_price,fees_funding,tiers_liquidation,engine_parity}/
└── artifacts/{rule_snapshots,strategies,experiments,fills,audit_reports}/
```

## 17. Criterios de aceptación

El MVP está terminado cuando:

- consulta reglas BingX vivas;
- graba L2/trades/mark sin gaps críticos;
- ejecuta el mismo StrategySpec en replay y live;
- reproduce fees/funding/tier/liquidación;
- genera y optimiza estrategias automáticamente;
- encuentra y almacena candidatos ≥1000% neto si existen en el espacio probado;
- no declara el objetivo cumplido con una simulación inválida;
- pasa prod-vst y shadow;
- micro-live produce un informe de divergencia;
- cada resultado se reconstruye desde hashes, datos, reglas, código y semilla.

## 18. Fuentes principales

- BingX Dual-Price Mechanism: https://bingx.com/en/support/articles/11263241307407/
- BingX Mark & Index Price: https://bingx.com/en/support/articles/12823291011865-MarkPriceinPerpetualFutures/
- BingX Fee Schedule: https://bingx.com/en/support/articles/360046487573/
- BingX Leverage & Margin: https://bingx.com/en/support/articles/22260528334617/
- BingX Forced Liquidation Rules: https://bingx.com/en/support/articles/16934295548441/
- BingX Forex up to 500x: https://bingxservice.zendesk.com/hc/en-001/articles/13628544052239
- BingX indices up to 500x: https://bingxservice.zendesk.com/hc/en-001/articles/14443497885327
- BingX commodity futures: https://bingx.com/en/how-to-trade-commodity-futures
- BingX API docs: https://github.com/BingX-API/docs
- BingX API skills/prod-vst: https://github.com/BingX-API/api-ai-skills
- Nautilus integrations: https://nautilustrader.io/docs/latest/integrations/
- Nautilus adapter guide: https://nautilustrader.io/docs/latest/developer_guide/adapters/
