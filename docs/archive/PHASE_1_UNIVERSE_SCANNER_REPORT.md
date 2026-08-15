# Fase 1 — UniverseScanner real

Fecha de cierre: 2026-07-31 (UTC)

## Objetivo

Convertir la primera fase del autopiloto en una puerta de datos real: comprobar el universo histórico antes de permitir que el sistema genere o pruebe estrategias.

## Problema encontrado

La implementación anterior devolvía oportunidades incluso con la base de datos vacía. Usaba ETH/BTC de respaldo y valores codificados para liquidez y volatilidad, seleccionaba registros sin un ranking real y permitía que el controlador continuara con ETH 1h. Esto hacía que el proceso aparentara estar preparado cuando no disponía de los datos exigidos.

## Contrato corregido

La fase exige un universo completo de `ETH-USDT` en estos intervalos:

| Intervalo | Historia mínima | Estado requerido |
|---|---:|---|
| 1m | 1.095 días | APPROVED |
| 5m | 1.095 días | APPROVED |
| 15m | 1.095 días | APPROVED |

Si falta o falla uno solo, el universo completo queda `NOT_READY` y el autopiloto responde `BLOCKED_DATA` sin evaluar estrategias.

## Verificaciones implementadas

- Coincidencia entre DB, manifiesto y mercado solicitado.
- Existencia de RAW, normalizado y manifiesto.
- Checksum SHA-256 del RAW y del normalizado.
- Solo velas cerradas.
- Cero gaps, duplicados y desorden temporal.
- Cobertura de al menos 99,999 %.
- Conteo y rango temporal coherentes entre DB, manifiesto y archivo.
- Timestamps exactamente contiguos para el intervalo.
- Valores numéricos finitos e invariantes OHLCV válidas.
- Historia mínima efectiva de 1.095 días.

El lector procesa el JSON normalizado de forma incremental para no cargar varios años de velas en memoria. Con los datos válidos calcula turnover mediano por minuto y volatilidad diaria, normaliza ambas métricas y ordena las oportunidades de manera determinista.

## Archivos modificados

- `services/api/app/factory/autopilot.py`
- `services/api/tests/test_autopilot.py`
- `services/api/tests/test_universe_scanner.py` (nuevo)
- `apps/web/app/page.tsx`
- `tasks.md`, `dispatch-state.json` y archivos de seguimiento `.slen/`

## Evidencia

| Comprobación | Resultado |
|---|---|
| Pruebas de fase 1, incluida descarga live de BingX | 8 passed |
| Ruff sobre los archivos de fase 1 | Passed |
| Build de Next.js | Passed; 12 rutas |
| Inicio API aislado | ONLINE |
| Inicio del autopiloto sin históricos completos | HTTP 202, BLOCKED_DATA, 0 evaluaciones |
| Web compilada servida en Hermes | HTTP 200 |

La suite Python completa quedó en `28 passed, 5 skipped, 3 failed`. Los tres fallos corresponden a pruebas de fases posteriores que combinan manifiestos reales con una base temporal vacía y terminan en `DATASET_NOT_FOUND` o fallo de campaña. Se documentan, pero no se alteran dentro de esta fase.

## Estado al cierre

El código de la fase 1 funciona conforme al contrato real-only. El sistema está correctamente bloqueado porque todavía no existen en la base limpia los tres datasets históricos aprobados. El siguiente trabajo lógico es la ingesta histórica paginada y su aprobación; la generación de estrategias no debe comenzar antes.
