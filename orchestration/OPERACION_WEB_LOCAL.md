# OPERACIÓN: Instancia Local Desacoplada de ULTRARENTABLE

> **Propósito:** Levantar una instancia local completa de Ultrarentable en el PC (FastAPI + Next.js en build de producción) para desarrollo, auditoría y visualización inmediata de `/estrategias` sin interferir con el túnel `sshd` hacia el VPS (que ocupa los puertos 3000 y 8000).

---

## 1. Arquitectura de Puertos y Servicios

| Servicio | Puerto Local | Tecnología | Rol / Endpoints Clave |
|---|---|---|---|
| **API Backend** | **8100** | FastAPI + Uvicorn | `http://127.0.0.1:8100/`<br>`http://127.0.0.1:8100/api/v1/version`<br>`http://127.0.0.1:8100/api/v1/system/health` |
| **Web Frontend** | **3100** | Next.js (Build de Producción) | `http://127.0.0.1:3100/`<br>`http://127.0.0.1:3100/estrategias`<br>`http://127.0.0.1:3100/prop-firms` |
| **Túnel VPS** | *3000 / 8000* | OpenSSH / sshd | *Intocable (conectado al VPS)* |

---

## 2. Comandos Operativos (`scripts/orq/web_local.ps1`)

El script `scripts/orq/web_local.ps1` gestiona el ciclo de vida de los servicios locales como procesos desacoplados en segundo plano.

### 2.1 Arrancar Servicios (Modo por Defecto)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1 -Arrancar
# o simplemente:
powershell -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1
```
- Inicia la API FastAPI con Uvicorn en el puerto `8100` (`PYTHONPATH` configurado a la raíz del worktree).
- Espera liveness de la API.
- Si no existe build de producción previo en `apps/web/.next`, ejecuta `npm run build`.
- Inicia el servidor Next.js en producción (`npm run start -- -p 3100`) con `BACKEND_URL=http://127.0.0.1:8100`.
- Registra los PIDs en `orchestration/site/local.pids.json` e imprime la tabla de estado.

### 2.2 Consultar Estado y Salud
```powershell
powershell -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1 -Estado
```
- Verifica PIDs activos y puertos en escucha (`8100`, `3100`).
- Sondea los 6 endpoints HTTP (`/`, `/api/v1/version`, `/api/v1/system/health`, `/`, `/estrategias`, `/prop-firms`).
- Reporta la versión del motor (`engine_version`), estado de base de datos (`STATE_DB_PATH`) y latencias.

### 2.3 Reconstruir Web de Producción
```powershell
powershell -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1 -Reconstruir
```
- Detiene el proceso Web Next.js activo.
- Ejecuta `npm run build` en `apps/web`.
- Reinicia la Web en el puerto `3100` con `BACKEND_URL=http://127.0.0.1:8100`.
- Actualiza el registro de PIDs y muestra el estado.

### 2.4 Parar Servicios
```powershell
powershell -ExecutionPolicy Bypass -File scripts/orq/web_local.ps1 -Parar
```
- Detiene limpiamente los procesos de API y Web.
- Cierra cualquier proceso remanente en los puertos `8100` y `3100`.
- **Regla Nunca RM:** Archiva `orchestration/site/local.pids.json` como `orchestration/site/local.pids.<timestamp>.json`.

---

## 3. Logs y Diagnóstico

Los logs de ejecución y error de los procesos desacoplados se almacenan en `orchestration/site/`:
- `orchestration/site/api.log` / `api_err.log`: Logs de FastAPI / Uvicorn.
- `orchestration/site/web.log` / `web_err.log`: Logs del servidor Next.js en producción.
- `orchestration/site/build.log` / `build_err.log`: Logs del proceso `npm run build`.
- `orchestration/site/local.pids.json`: PIDs y metadatos de la sesión activa.
