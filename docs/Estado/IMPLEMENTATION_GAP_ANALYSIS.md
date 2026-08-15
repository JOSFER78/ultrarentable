# Brechas de implementación — V2 local

## Estado

El proyecto tiene una base de UI, conectividad pública BingX y código inicial de ingesta. No es todavía un laboratorio de estrategias.

## Brechas críticas

1. Cadena de custodia completa de datos.
2. Histórico paginado y Parquet.
3. L2 secuenciado y WebSocket privado.
4. DSL única persistida.
5. Fast engine.
6. Campañas locales.
7. NautilusTrader y adaptador BingX.
8. Ledger independiente.
9. Shadow y micro-live.

## Componentes que se conservan

- diseño Next.js;
- Data Pipeline como consulta pública;
- clientes BingX como base, después de tests;
- FastAPI y SQLite local;
- documentación de reglas BingX.

## Componentes que deben construirse

```text
services/
  data-ingestion/
  strategy-service/
  fast-backtester/
  campaign-worker/
  canonical-backtester/
  result-validator/

data/
  raw/
  normalized/
  state/
  artifacts/
```

No usar Docker como dependencia. La sustitución futura por infraestructura distribuida debe hacerse mediante adaptadores.
