# Auditoría de fuente histórica — ETH-USDT

Fecha: 2026-07-31 (UTC)

## Requisito del proyecto

- ETH-USDT.
- Intervalos 1m, 5m y 15m.
- 1.095 días completos por intervalo.
- Datos reales, trazables y sin reconstrucción inventada.

## Capacidad documentada

La referencia oficial de BingX para perpetual swap usa `GET /openApi/swap/v3/quote/klines`, acepta `startTime` y `endTime`, limita cada página a 1.440 velas y declara 1 solicitud por segundo por IP:

<https://github.com/BingX-API/api-ai-skills/blob/main/skills/swap-market/api-reference.md#6-kline--candlestick-data>

La implementación existente no aprovechaba esa capacidad: `/ingestion/backfill` pedía solo una página sin rango y la marcaba como `complete_history: false`.

## Resultado de las pruebas en vivo desde Hermes

Las consultas se realizaron directamente contra `open-api.bingx.com`, con ventanas históricas explícitas y una cadencia conservadora de al menos un segundo.

| Intervalo | Último punto con datos observado | Primer punto vacío observado | Conclusión |
|---|---:|---:|---|
| 1m | ~608 días atrás | ~609 días atrás | No alcanza 1.095 días |
| 5m | ~85 días atrás | ~90 días atrás | No alcanza 1.095 días |
| 15m | 180 días atrás | 365 días atrás | No alcanza 1.095 días |

Una consulta centrada en 2023-08-01 devolvió cero velas para 1m, 5m y 15m. El endpoint histórico de spot (`/openApi/market/his/v1/kline`) llega más atrás que el estándar, pero también rechazó rangos de 730 y 1.095 días; además no representa el mercado perpetual objetivo.

Los límites de retención no están especificados en la documentación y pueden cambiar. Las cifras anteriores son evidencia empírica de esta fecha, no una garantía contractual.

## Decisión obligatoria

No existe una corrección de código que convierta un histórico inexistente en datos nativos de BingX. Para continuar hay tres alternativas honestas:

1. Doble fuente: tres años de ETHUSDT perpetual de una fuente oficial adicional para investigación, más validación obligatoria e independiente sobre el histórico nativo disponible de BingX. Ningún dato externo se etiquetará como BingX.
2. Solo BingX: reducir la historia mínima al máximo común real disponible y renunciar al requisito de tres años.
3. Archivo BingX: importar una exportación histórica verificable aportada por el usuario o por BingX.

La ingesta queda bloqueada hasta elegir una alternativa. La generación de estrategias sigue sin autorización.
