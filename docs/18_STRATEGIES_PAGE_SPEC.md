# ULTRARENTABLE — STRATEGIES PAGE SPEC

## Scope
La página canónica es `/estrategias`. `/strategies` es únicamente un alias legacy que redirige a `/estrategias`.

## Objetivo de producto
La página de Estrategias es el **catálogo de inteligencia cuantitativa**. Su misión es permitir encontrar, inspeccionar y enviar a investigación estrategias reales sin mezclar ejecución ni cuentas.

## Qué representa una estrategia
Una estrategia se identifica por:
- `strategy_id`
- estructura/DSL o snapshot canónico cuando exista
- `strategy_hash`
- activo
- timeframe
- procedencia/origen
- dataset y `dataset_hash` cuando exista
- estado de validación
- artefacto de origen cuando exista

## Separación fundamental
**STRATEGY IDENTITY != EXECUTION VENUE**

El activo y la estrategia no se duplican por exchange. Un venue añade una capa posterior de microestructura, costes, slippage, liquidez y reglas de ejecución.

Por tanto, en esta página NO se deben introducir:
- BingX como filtro de identidad de la estrategia;
- broker/exchange como dimensión del catálogo;
- cuentas de 25K/50K/etc.;
- capital inicial para decidir una estrategia;
- sizing de prop firm;
- ejecución live;
- posiciones o órdenes.

## Estados
`EXTRACTED → STRUCTURALLY_VERIFIED → BACKTEST_VERIFIED → CERTIFIED_CURRENT`

Un estado superior requiere la evidencia correspondiente. La UI no promociona una estrategia por métricas atractivas.

## Métricas
Las métricas de rentabilidad (PF, ROI, CAGR, DD, Sharpe, etc.) solo deben mostrarse cuando proceden de un backtest canónico/evidencia asociada. La extracción SQX por sí sola no es un backtest.

Ausencia de evidencia = `NO EVIDENCE`, nunca `0`, nunca un valor generado.

## Funciones de la página
1. Buscar y filtrar catálogo.
2. Ver procedencia, activo, timeframe y estado.
3. Inspeccionar hashes y dataset asociado.
4. Extraer hipótesis reales desde SQX.
5. Navegar a Candidatos/Investigación para optimización y validación.
6. Refrescar el catálogo desde la API canónica.

## Criterio de calidad
La página debe seguir una única fuente de verdad de API y no mantener una segunda implementación de backtest o de clasificación de rentabilidad en el cliente.

## No regresión
No reintroducir `MotorBacktestView` como segunda página de estrategias ni controles de capital/slippage/cuenta dentro del catálogo.
