# Backtester canónico

## Contrato

Dados la misma versión de código, dataset, estrategia, configuración y semilla, debe producir exactamente los mismos fills y resultados.

## Secuencia por evento/barra

1. Aplicar funding correspondiente al timestamp.
2. Actualizar mark price y margen.
3. Comprobar liquidación antes de aceptar decisiones nuevas.
4. Procesar órdenes pendientes según política de fills.
5. Ejecutar salidas protectoras y señales según política intrabar.
6. Calcular señales usando solo información disponible.
7. Crear/modificar/cancelar órdenes.
8. Recalcular balances, equity y margen.
9. Persistir eventos relevantes.

## Política intrabar MVP

Para OHLCV, soportar tres escenarios:

- `PESSIMISTIC`: cuando stop y target son posibles en la misma vela, asumir el resultado peor.
- `OPTIMISTIC`: solo diagnóstico, nunca ranking final.
- `LOWER_TF_REPLAY`: reproducir con 1m cuando se valida una estrategia de 5m/15m.

El ranking canónico usa `PESSIMISTIC` o `LOWER_TF_REPLAY`.

## Liquidación

Debe usar un adaptador por exchange con:

- margen inicial;
- maintenance margin tiers;
- mark price;
- fees de liquidación;
- posiciones cruzadas o aisladas;
- precisión y notional mínimo.

## Salidas obligatorias

- summary.json;
- orders.parquet;
- fills.parquet;
- positions.parquet;
- equity.parquet;
- events.parquet;
- manifest.json.
