> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: plan local por fases antiguo, sustituido por docs/00_MASTER_IDEAS_Y_PLAN.md §4. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# Plan local de construcción

## Fase A — base local

- Python `.venv`.
- Node workspaces.
- FastAPI.
- SQLite WAL.
- rutas portables.
- scripts Windows/PowerShell.
- build y tests reproducibles.

## Fase B — BingX y datos

- REST público/privado.
- WebSocket público/privado.
- RAW inmutable.
- histórico paginado.
- velas cerradas.
- trades, L2, mark, index, funding y OI.
- Parquet.
- aprobación de datasets.

## Fase C — DSL

- Pydantic y JSON Schema.
- tipos TypeScript.
- parser, normalizador, hash y compilador.
- CRUD SQLite.

## Fase D — fast engine

- Python/Numba.
- fees, funding, mark y liquidación.
- ledger y artefactos.
- `FAST_APPROXIMATE`.

## Fase E — campañas locales

- SQLite queue.
- ProcessPoolExecutor.
- Optuna y DEAP.
- checkpoints.

## Fase F — NautilusTrader

- adaptador BingX.
- replay L2.
- motor canónico.
- ledger independiente.

## Fase G — shadow y micro-live

- feed mainnet.
- comparación con ejecución observada.
- órdenes reales solo con activación y confirmación explícitas.

Docker, PostgreSQL, Redis, MinIO y Ray no son requisitos del MVP local.
