# Arquitectura objetivo — local first

```mermaid
graph TD
  WEB[Next.js local] --> API[FastAPI local]
  API --> DB[(SQLite WAL)]
  API --> FS[Filesystem RAW / Parquet / artefactos]
  API --> BX[BingX REST + WebSocket]
  API --> JOBS[SQLite job queue]
  JOBS --> W[Workers multiproceso]
  W --> FAST[Fast Engine]
  W --> CAN[Nautilus Canonical Engine]
  CAN --> VAL[Ledger independiente]
```

## Principios

- Sin Docker obligatorio.
- Rutas portables.
- Una base SQLite para el MVP.
- Artefactos grandes fuera de la base de datos.
- Procesos locales con límites configurables.
- Interfaces preparadas para sustituir SQLite por PostgreSQL y la cola local por Ray en el futuro.
