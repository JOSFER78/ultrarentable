# Scripts

## Instalación y arranque local

- `INSTALL_LOCAL.bat`
- `START_LOCAL.bat`
- `scripts/local/install.ps1`
- `scripts/local/start.ps1`

## Ingesta manual

Después de instalar dependencias:

```bash
npm run ingest
```

Los tests de red son opt-in:

```bash
set RUN_LIVE_BINGX_TESTS=1
npm run test:ingestion
```
