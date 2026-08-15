# Operación local sin Docker

## Procesos

- `uvicorn` para FastAPI;
- `next dev` o `next start` para la web;
- recorder como proceso Python/Node separado;
- workers locales como procesos Python;
- SQLite WAL como registro de verdad;
- filesystem local para RAW, Parquet y artefactos.

## Arranque en Windows

```bat
INSTALL_LOCAL.bat
START_LOCAL.bat
```

## Escalado opcional futuro

Solo cuando el MVP local funcione y el volumen lo justifique:

- PostgreSQL;
- Redis;
- almacenamiento S3;
- Ray;
- contenedores.

El código de negocio no debe depender de Docker.
