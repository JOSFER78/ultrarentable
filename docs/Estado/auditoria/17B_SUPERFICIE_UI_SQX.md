# Informe Auditoría de Superficie de Control y Automatización UI de StrategyQuant X

**Fecha:** 11 de Agosto de 2026  
**Host:** VPS Linux (Ubuntu 24.04 / Xvfb :99)  
**Target:** StrategyQuant X Pro Build 144 (Trial License activa hasta 18.08.2026)  
**Ubicación del Documento:** `docs/Estado/auditoria/17B_SUPERFICIE_UI_SQX.md`  

---

## 1. Resumen Ejecutivo y Matriz de Canales

El presente informe establece la factibilidad y la estrategia de automatización para **StrategyQuant X (SQX)** en el VPS. Se analizaron empíricamente 4 canales de control: HTTP 5050 (Jetty/Web), Playwright, Remote Debugging (CDP Electron) y Control GUI Directo por `xdotool` + ImageMagick `import` en la pantalla `:99`.

### Matriz Comparativa de Canales

| Canal / Método | Puerto / Vía | Estado Empírico | Utilidad en Producción | Observaciones |
| :--- | :--- | :--- | :--- | :--- |
| **SQX MCP API** | HTTP 8080 `/mcp` | **OPERATIVO (100%)** | **P0 (Ejecución y Ingest)** | Expone 6 métodos JSON-RPC (`list_projects`, `list_databanks`, `list_strategies`, `get_strategy_stats`, `run_project`, `stop_project`). |
| **Mutación CFX-ZIP** | Sistema de Archivos | **OPERATIVO (100%)** | **P0 (Configuración)** | Modificación directa de XMLs dentro de `project.cfx` (Population, Generations, StrategyType, Indicators, StopConditions). |
| **GUI Automation** | `xdotool` + `import` (`DISPLAY=:99`) | **OPERATIVO (100%)** | **P1 (Fallback / Visual QA)** | Window ID `56623108` (1920x1029). Permite navegar por pestañas (Builder, Optimizer, Retester, Custom Indicators, AlgoWizard) y capturar evidencias reales. |
| **CDP (Electron)** | TCP `--remote-debugging-port` | **NO HABILITADO POR DEFECTO** | **P2 (Avanzado)** | PID 192514 (`strategyquantx_ui`) no se inicia con `--remote-debugging-port`. Requiere modificar el script de arranque o envoltorio. |
| **Playwright Web** | HTTP 5050 | **INAPLICABLE** | **INAPLICABLE (0%)** | El puerto 5050 es un endpoint IPC interno de Jetty 11.0.20. Devuelve HTTP 200 `Unable to resolve the request` ante cualquier petición GET web. |

---

## 2. Auditoría del Puerto HTTP 5050 y Servidor Jetty

### 2.1. Inspección de Procesos y Puertos
Mediante la inspección con `ps` y `fuser`, se determinaron los componentes en ejecución:
- **PID 192358 (`/home/ubuntu/StrategyQuantX/StrategyQuantX`)**: Proceso Java principal. Escucha en los puertos TCP `5050` (Jetty 11.0.20) y `8080` (MCP JSON-RPC Server).
- **PID 192514 (`/home/ubuntu/StrategyQuantX/internal/electron/strategyquantx_ui`)**: Proceso Electron UI lanzado por Java con los argumentos:
  ```bash
  /home/ubuntu/StrategyQuantX/internal/electron/strategyquantx_ui --no-sandbox --disable-setuid-sandbox SQUANT StrategyQuantX sq.png 5050 -854879105
  ```

### 2.2. Pruebas de Probing HTTP en Puerto 5050
Se realizaron solicitudes HTTP `GET` a múltiples rutas candidatas en `http://127.0.0.1:5050`:

```bash
for route in "" "index.html" "api" "api/v1" "ws" "health" "sqx/status" "gui" "swagger" "openapi.json"; do
    curl -s -i "http://127.0.0.1:5050/$route" | head -n 8
done
```

**Respuesta recibida en TODAS las rutas:**
```http
HTTP/1.1 200 OK
Date: Tue, 11 Aug 2026 17:20:42 GMT
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: POST, GET, OPTIONS, PUT, DELETE, HEAD
Access-Control-Allow-Headers: *
Connection: close
Content-Type: text/html;charset=utf-8
Server: Jetty(11.0.20)

Unable to resolve the request <ruta>
```

**Conclusión:** El servidor Jetty en el puerto 5050 actúa como canal IPC/WebSocket propietario entre la app Electron `strategyquantx_ui` y el core Java de StrategyQuant X. **No es un servidor web frontend que sirva una interfaz HTML/SPA.**

---

## 3. Evaluación Empírica de Playwright

Se ejecutó un script en Python con Playwright Async API utilizando el navegador Chromium instalado en el sistema (`/usr/bin/chromium-browser`) en modo headless para navegar a `http://127.0.0.1:5050`.

### 3.1. Código de Prueba
```python
import asyncio
from playwright.async_api import async_playwright
import os

async def test_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path='/usr/bin/chromium-browser',
            headless=True,
            args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
        )
        page = await browser.new_page()
        response = await page.goto('http://127.0.0.1:5050', timeout=10000)
        
        status = response.status if response else 'No response'
        title = await page.title()
        content = await page.content()
        
        print(f"Status: {status}")
        print(f"Title: '{title}'")
        print(f"Content: {content.strip()}")
        
        img_path = '/home/ubuntu/.hermes/profiles/default/images/sqx_playwright_5050.png'
        await page.screenshot(path=img_path)
        os.chmod(img_path, 0o644)
        await browser.close()

asyncio.run(test_playwright())
```

### 3.2. Resultados Obtenidos
- **HTTP Status:** `200`
- **Título de la Página:** `""` (Vacío)
- **Contenido HTML:** `<html><head></head><body>Unable to resolve the request </body></html>`
- **Screenshot Generada:** `/home/ubuntu/.hermes/profiles/default/images/sqx_playwright_5050.png` (`chmod 644`, verificada).

**Dictamen:** Playwright **NO puede automatizar SQX a través del puerto 5050** debido a que no existe una interfaz HTML renderizable.

---

## 4. Inspección de Remote Debugging (CDP)

El proceso Electron PID 192514 se encuentra corriendo bajo Xvfb `:99`. La inspección de la línea de comandos confirma que **NO se incluyó el parámetro `--remote-debugging-port`** en su inicio por defecto.

### Receta para Habilitar CDP (en caso de requerirse en el futuro)
Si se desea automatizar la interfaz nativa mediante Chrome DevTools Protocol (CDP):
1. **Bandera de Inicio:** Pasar `--remote-debugging-port=9223` y `--remote-allow-origins=*` al binario `/home/ubuntu/StrategyQuantX/internal/electron/strategyquantx_ui`.
2. **Verificación de Endpoint:**
   ```bash
   curl -s http://127.0.0.1:9223/json/version
   ```
3. **Conexión Playwright vía CDP:**
   ```python
   browser = await p.chromium.connect_over_cdp('http://127.0.0.1:9223')
   context = browser.contexts[0]
   page = context.pages[0]
   await page.screenshot(path='/home/ubuntu/.hermes/profiles/default/images/sqx_cdp.png')
   ```

---

## 5. Receta Probada de Automatización GUI (`xdotool` + `import` en DISPLAY=:99)

La automatización GUI directa funciona al 100% sobre la ventana activa de Electron en Xvfb.

### 5.1. Variables de Entorno Obligatorias
```bash
export DISPLAY=:99
export XAUTHORITY=/home/ubuntu/.Xauthority
```

### 5.2. Identificación de la Ventana Principal
```bash
WID=$(xdotool search --onlyvisible --name "StrategyQuant" | head -1)
# En nuestras pruebas empíricas: WID = 56623108
# Geometría: 1920x1029 (Origen X=0, Y=75)
```

### 5.3. Matriz de Navegación por Coordenadas
Se determinaron y validaron empíricamente las coordenadas relativas a la ventana para cada pestaña principal en la barra superior:

| Pestaña / Modulo | Coordenadas Ventana (X, Y) | Coordenadas Pantalla (X, Y) | Hash MD5 Screenshot |
| :--- | :--- | :--- | :--- |
| **Data Manager** | `(150, 115)` | `(150, 190)` | `98facc642ec5bca8c840a5a91068e66f` |
| **Builder** | `(280, 115)` | `(280, 190)` | `473ab1f6f303fd6f213624f1744b92fa` |
| **Retester** | `(400, 115)` | `(400, 190)` | `eafb4f85c1082801af2ee69583e9ec3b` |
| **Optimizer** | `(520, 115)` | `(520, 190)` | `6cf8abfd41550c7eb7237d08ddeb40e6` |
| **AlgoWizard** | `(650, 115)` | `(650, 190)` | `d5696afb5e625e7c025b19d5b7e33902` |
| **Custom Indicators**| `(780, 115)` | `(780, 190)` | `e14f1d5180ecab1aee9de31146129b7b` |

### 5.4. Capturas de Pantalla Entregadas (`chmod 644`)
Las capturas se guardaron en la ruta oficial del perfil para entrega web:

- `/home/ubuntu/.hermes/profiles/default/images/sqx_gui_window.png` (368.4 KB, 1920x1029)
- `/home/ubuntu/.hermes/profiles/default/images/sqx_gui_root.png` (375.1 KB, 1920x1080)
- `/home/ubuntu/.hermes/profiles/default/images/sqx_click_data_manager.png`
- `/home/ubuntu/.hermes/profiles/default/images/sqx_click_builder.png`
- `/home/ubuntu/.hermes/profiles/default/images/sqx_click_retester.png`
- `/home/ubuntu/.hermes/profiles/default/images/sqx_click_optimizer.png`
- `/home/ubuntu/.hermes/profiles/default/images/sqx_click_algowizard.png`
- `/home/ubuntu/.hermes/profiles/default/images/sqx_click_custom_indicators.png`

---

## 6. Scripts Python de Automatización Implementados

Se creó el script ejecutable `services/sqx_bridge/sqx_gui_automation.py` que proporciona una interfaz programática completa para controlar la GUI de SQX.

### Código del Script (`services/sqx_bridge/sqx_gui_automation.py`):

```python
#!/usr/bin/env python3
"""
SQX GUI Automation Tool via xdotool & ImageMagick import on Xvfb :99.
Provides reliable window discovery, click navigation, and screenshot capturing for StrategyQuant X.
"""

import os
import sys
import time
import subprocess
import logging
from typing import Optional, Tuple, Dict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DISPLAY = os.environ.get("DISPLAY", ":99")
XAUTHORITY = os.environ.get("XAUTHORITY", "/home/ubuntu/.Xauthority")
DEFAULT_IMG_DIR = "/home/ubuntu/.hermes/profiles/default/images"

NAV_COORDINATES: Dict[str, Tuple[int, int]] = {
    "data_manager": (150, 115),
    "builder": (280, 115),
    "retester": (400, 115),
    "optimizer": (520, 115),
    "algowizard": (650, 115),
    "custom_indicators": (780, 115),
}

def setup_env():
    os.environ["DISPLAY"] = DISPLAY
    os.environ["XAUTHORITY"] = XAUTHORITY

def find_sqx_window() -> Optional[str]:
    """Find SQX main window ID using xdotool."""
    setup_env()
    try:
        cmd = ["xdotool", "search", "--onlyvisible", "--name", "StrategyQuant"]
        res = subprocess.check_output(cmd).decode().strip().split()
        if res:
            return res[0]
        cmd = ["xdotool", "search", "--name", "StrategyQuant"]
        res = subprocess.check_output(cmd).decode().strip().split()
        for w in res:
            geom = subprocess.check_output(["xdotool", "getwindowgeometry", w]).decode()
            if "1920x" in geom or "1800x" in geom:
                return w
        return res[0] if res else None
    except Exception as e:
        logging.error(f"Failed to find SQX window: {e}")
        return None

def capture_window(wid: str, filename: str, output_dir: str = DEFAULT_IMG_DIR) -> str:
    """Capture screenshot of the specified window ID and save with 644 permissions."""
    setup_env()
    os.makedirs(output_dir, exist_ok=True)
    tmp_path = f"/tmp/{filename}"
    dst_path = os.path.join(output_dir, filename)
    
    subprocess.run(["import", "-window", wid, tmp_path], check=True)
    subprocess.run(["cp", tmp_path, dst_path], check=True)
    os.chmod(dst_path, 0o644)
    logging.info(f"Captured window {wid} -> {dst_path}")
    return dst_path

def click_nav_tab(tab_name: str, wait_sec: float = 1.0) -> Optional[str]:
    """Click on a navigation tab by name and take a screenshot."""
    if tab_name not in NAV_COORDINATES:
        raise ValueError(f"Unknown tab '{tab_name}'. Valid tabs: {list(NAV_COORDINATES.keys())}")
    
    wid = find_sqx_window()
    if not wid:
        logging.error("SQX Window not found!")
        return None
    
    x, y = NAV_COORDINATES[tab_name]
    setup_env()
    logging.info(f"Clicking tab '{tab_name}' at ({x}, {y}) on window {wid}...")
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"], check=True)
    time.sleep(wait_sec)
    
    img_name = f"sqx_click_{tab_name}.png"
    return capture_window(wid, img_name)

if __name__ == "__main__":
    logging.info("Testing SQX GUI Automation module...")
    w_id = find_sqx_window()
    if w_id:
        logging.info(f"Found SQX Window ID: {w_id}")
        cap = capture_window(w_id, "sqx_gui_module_test.png")
        print(f"Captured: {cap}")
    else:
        logging.error("SQX window not found.")
```

---

## 7. Conclusión y Arquitectura Recomendada

Para obtener el máximo provecho de StrategyQuant X dentro del pipeline de **Ultrarentable**:

1. **Control de Flujo de Trabajo y Compilaciones (P0):** Utilizar **MCP Client (`sqx_client.py`)** en el puerto `8080` para `run_project`, `stop_project` y monitoreo de databanks.
2. **Configuración de Parámetros de Generación (P0):** Utilizar **Mutación XML/ZIP en `project.cfx`** para alterar configuraciones avanzadas antes de cada ejecución.
3. **Auditoría Visual y Fallback Operativo (P1):** Utilizar el script **`sqx_gui_automation.py`** con `xdotool` e `import` en `DISPLAY=:99` para validación visual de la GUI, interacción con AlgoWizard/CodeEditor y exportación gráfica.
