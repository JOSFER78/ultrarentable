> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: plan de construcción MVP antiguo, sustituido por docs/00_MASTER_IDEAS_Y_PLAN.md §4. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# Plan de construcción del MVP

## Fase 0 — Contratos

- Monorepo, schemas y ADR.
- DSL v0.1.
- Modelo de datos.
- Configuración de campaña.

**Salida:** estrategia de ejemplo validada y hasheada.

## Fase 1 — Datos

- Adaptador de exchange.
- OHLCV/funding.
- Parquet versionado.
- Generador de ventanas reproducibles.

**Salida:** catálogo de tres años en 5m/15m.

## Fase 2 — Backtester canónico

- Posiciones long/short.
- Órdenes, fills, fees y funding.
- Margen, liquidación y compound.
- Intrabar pesimista.

**Salida:** suite de golden tests.

## Fase 3 — Fast Explorer

- Compilador DSL vectorizado.
- Lotes de parámetros.
- Comparación diferencial.

**Salida:** miles de pruebas por campaña.

## Fase 4 — Evolución

- Poblaciones, mutaciones y cruces.
- Linaje y memoria de intentos.
- Selección Kamikaze.

**Salida:** generaciones autónomas reanudables.

## Fase 5 — Web

- Campañas, leaderboard, inspector y árbol.
- WebSockets y exportación.

**Salida:** MVP operable sin terminal.

## Fase 6 — Investigación multiagente

- Inbox de ideas.
- Conversión a DSL.
- Auditor de simulación.

**Salida:** ideas externas integradas sin código libre.

## Definición de terminado

El MVP está terminado cuando puede ejecutar una campaña de al menos 5.000 candidatos, validar canónicamente los mejores, sobrevivir a un reinicio, mostrar linajes y exportar un resultado reproducible.
