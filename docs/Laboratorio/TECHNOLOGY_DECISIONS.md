# Decisiones tecnológicas V2

## Local MVP

- SQLite WAL como metadatos, cola y checkpoints.
- Filesystem local para RAW, Parquet y artefactos.
- FastAPI y Next.js como procesos independientes.
- ProcessPoolExecutor para paralelización local.
- Optuna con storage SQLite.
- DEAP para evolución.
- Numba/NumPy para fast engine.
- NautilusTrader para validación canónica.

## Escalado posterior

PostgreSQL, Redis, S3, Ray y Docker son opciones futuras. No deben bloquear el desarrollo ni el uso local.
