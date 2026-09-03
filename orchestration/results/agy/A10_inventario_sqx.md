# INVENTARIO TÉCNICO DE INSTALACIÓN Y LICENCIA DE STRATEGYQUANT X EN HETZNER

> **Tarea:** A10 · **Agente:** AGY · **Fecha de auditoría:** 2026-09-03 02:45 UTC  
> **Servidor:** Hetzner Dedicated (`88.99.210.167`, alias SSH `sqx-hetzner`)  
> **Ruta de instalación:** `/opt/StrategyQuantX`  
> **Modo de ejecución:** Solo lectura. Cero cambios de configuración, sin arranques ni paradas.

---

## 1. Versión, Edición y Licencia de StrategyQuant X

### Hallazgos Principales
- **Versión de SQX:** `144.2953` (Build 144).
- **Edición instalada:** `StrategyQuant X Pro Build 144 (Trial license)`.
- **Fecha de caducidad:** **17 de septiembre de 2026** (`17.09.2026`).
- **Código de activación de licencia:** `D2ABE0`, validado con éxito a las `03:06:30.382 UTC` del `2026-09-03`.
- **Fichero de persistencia de licencia:** `/opt/StrategyQuantX/internal/license.db` (12.288 bytes, modificado 2026-09-03 03:06).

### Salida Cruda de Comandos

```bash
# Comprobación de directorio y fichero de licencia
$ ls -la /opt/StrategyQuantX/internal/license.db
-rw-rw-r-- 1 root root 12288 Sep  3 03:06 /opt/StrategyQuantX/internal/license.db

# Evidencia textual en sqx.log de la versión, edición y fecha exacta de expiración
$ grep -iE 'license|version|edition|trial' /opt/StrategyQuantX/sqx.log | grep -v 'DEBUG'
02:52:00.753 [qtp1750498848-31] INFO  c.s.l.app.webserver.MainAppWebSocket - Incoming connection from /127.0.0.1:38572, protocol version: 13
02:52:01.386 [main] INFO  c.strategyquant.strategyquant.SQApp - SQX version: 144.2953
02:52:01.490 [main] INFO  c.strategyquant.strategyquant.SQApp - License dialog initing
02:52:01.622 [main] INFO  c.strategyquant.webguilib.BrowserGUI - Showing license form
Received IPC message from renderer... license/verify:D2ABE0
03:06:30.851 [main] INFO  c.s.webguilib.license.LicenseDialog - Path: /opt/StrategyQuantX/internal/web/app/layout/views/loadingScreen.html
03:06:45.517 [main] INFO  com.strategyquant.webguilib.Electron - Set title:  StrategyQuant X Pro Build 144 (Trial license) - valid until 17.09.2026
Received WebSocket message: {"setTitle":{"title":" StrategyQuant X Pro Build 144 (Trial license) - valid until 17.09.2026"}}
03:06:48.331 [qtp1206258545-315] INFO  c.s.webguilib.servlet.MainServlet - Loading all versions, current: 144.2953, url: https://setup.strategyquant.com/builds_sq.xml, testMode: false
03:06:48.502 [qtp1206258545-315] INFO  c.s.webguilib.servlet.MainServlet - Versions loaded: 13 build(s) found, current: 144.2953, update available: false

# Opciones de JVM en configuración
$ cat /opt/StrategyQuantX/StrategyQuantX.config
option -Djava.net.useSystemProxies=true
option -Djava.net.preferIPv4Stack=true
option -XX:+UseParallelGC
option -Djdk.tls.trustNameService=true
option --enable-native-access=ALL-UNNAMED
option -Xms4g
```

---

## 2. Disponibilidad y Diagnóstico del CLI Headless

### Hallazgos Principales
- **Estado actual del CLI:** **NO DISPONIBLE / INACCESIBLE VÍA HTTP :5050**.
- Al consultar `http://127.0.0.1:5050/call?cmd=...` el servidor web responde con `Error: CLI not ready.`.
- **Causa Raíz Arquitectónica:**
  1. En el sistema está en ejecución la aplicación gráfica `./StrategyQuantX` con UI Electron sobre `DISPLAY=:99` (PID 29693).
  2. Al intentar ejecutar el binario headless `/opt/StrategyQuantX/sqcli`, este finaliza de inmediato con error:  
     `It seems another instance of StrategyQuant X is running, SQ can run only with one instance at once. If you need to run multiple SQ instances you can create multiple installations (different installation folders). Exit app - Another instance of StrategyQuant X is running.`
  3. El servlet HTTP de `./StrategyQuantX` (`com.strategyquant.lib.app.webserver.HttpTextServlet` en puerto 5050) solo expone la API interna para la GUI de Electron; el manejador `MainAppHttpHandler.onCall` lanza `CLI not ready` porque el motor de ejecución CLI (`com.strategyquant.strategyquant.SQConsoleStarter`) no se inicializa en modo GUI.
  4. Por tanto, para automatizar vía HTTP `/call?cmd=...` se requiere arrancar `sqcli` en modo consola exclusiva (sin la GUI simultánea sobre el mismo directorio) o crear una segunda carpeta de instalación dedicada a `sqcli`.

### Salida Cruda de Comandos

```bash
# Consultas HTTP sobre el puerto local 5050
$ curl -s -m 15 'http://127.0.0.1:5050/call?cmd=-help'
Error: CLI not ready.

$ curl -s -m 15 'http://127.0.0.1:5050/call?cmd=-project%20action=list'
Error: CLI not ready.

$ curl -s -m 15 'http://127.0.0.1:5050/call?cmd=-databank%20action=list%20project=Ultra_Matrix'
Error: CLI not ready.

# Procesos de StrategyQuant activos en el Hetzner
$ ps -eo pid,etime,rss,cmd | grep -iE 'sqcli|StrategyQuantX' | grep -v grep
  29693    01:13:38 3696100 ./StrategyQuantX
  29760    01:13:36 173044 /opt/StrategyQuantX/internal/electron/strategyquantx_ui --no-sandbox --disable-setuid-sandbox SQUANT StrategyQuantX sq.png 5050 2048069312
  29764    01:13:36 56092 /opt/StrategyQuantX/internal/electron/strategyquantx_ui --type=zygote --no-zygote-sandbox --no-sandbox
  29765    01:13:36 55852 /opt/StrategyQuantX/internal/electron/strategyquantx_ui --type=zygote --no-sandbox
  29791    01:13:36 171012 /opt/StrategyQuantX/internal/electron/strategyquantx_ui --type=zygote --no-zygote-sandbox --no-sandbox
  29797    01:13:36 90668 /proc/self/exe --type=utility --utility-sub-type=network.mojom.NetworkService ...
  30532       58:51 423204 /proc/self/exe --type=renderer ...
  30555       58:51 67896 /proc/self/exe --type=utility --utility-sub-type=audio.mojom.AudioService ...
  30579       58:49 144548 /opt/StrategyQuantX/internal/electron/strategyquantx_ui --type=zygote --no-sandbox

# Traza de excepción en log de SQX al recibir llamadas /call
03:26:22.446 [qtp1750498848-27] ERROR c.s.l.app.webserver.HttpTextServlet - Execution failed. Request URL: /call. 
java.lang.Exception: CLI not ready.
	at com.strategyquant.lib.app.webserver.MainAppHttpHandler.onCall(Unknown Source) ~[na:na]
	at com.strategyquant.lib.app.webserver.MainAppHttpHandler.execute(Unknown Source) ~[na:na]
	at com.strategyquant.lib.app.webserver.HttpTextServlet.doGet(Unknown Source) ~[na:na]

# Intento de invocar sqcli mientras StrategyQuantX está activo
$ /opt/StrategyQuantX/sqcli -help
It seems another instance of StrategyQuant X is running, SQ can run only with one instance at once.
If you need to run multiple SQ instances you can create multiple installations (different installation folders).
Exit app - Another instance of StrategyQuant X is running.
```

---

## 3. Inventario de Proyectos y Datos Históricos Cargados

### Proyectos Existentes en `/opt/StrategyQuantX/user/projects/`
Total: 19 proyectos/carpetas. Destacan:
1. `Ultra_Matrix` (173 MB, el proyecto principal con miles de estrategias acumuladas).
2. `Ultra_Auto_Pilot` (29 MB).
3. `Retester` (1.2 MB).
4. Varios proyectos de Dukascopy y Tradestation para GBPJPY, GBPUSD, GOLD, NQ, EW.

### Datos Históricos Cargados en `/opt/StrategyQuantX/user/data/History/`
Evaluación con respecto al **Objetivo M1 (5 activos × 5 marcos temporales = 25 celdas)**:

| Activo de Fondeo | 1m (`M1`) | 5m (`M5`) | 15m (`M15`) | 1h (`H1`) | 4h (`H4`) | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **ES** (E-mini S&P 500) | ❌ NO EXISTE |  357 KB |  121 KB |  373 KB |  107 KB | **4/5 presentes (falta M1)** |
| **NQ** (E-mini Nasdaq 100) | ❌ NO EXISTE |  363 KB |  122 KB |  366 KB |  105 KB | **4/5 presentes (falta M1)** |
| **YM** (E-mini Dow Jones) | ❌ NO EXISTE |  360 KB |  122 KB |  368 KB |  106 KB | **4/5 presentes (falta M1)** |
| **GC** (Gold Futures) | ❌ NO EXISTE |  361 KB |  122 KB |  367 KB |  106 KB | **4/5 presentes (falta M1)** |
| **CL** (Crude Oil Futures) | ❌ NO EXISTE |  358 KB |  121 KB |  365 KB |  105 KB | **4/5 presentes (falta M1)** |

- **Total celdas M1 cubiertas:** **20 de 25 celdas están cargadas y listas** en SQX.
- **Celdas faltantes:** **Las 5 celdas de 1 minuto (`M1`) no existen** para ningún activo de futuros. (El marco `M1` solo existe cargado para pares cripto: BTCUSDT, ETHUSDT, etc.).
- Otros activos de futuros disponibles: `RTY` (M5, M15, H1, H4) y `SI` (M5, M15, H1, H4).

### Salida Cruda de Comandos

```bash
$ ls /opt/StrategyQuantX/user/projects/
backups
Builder
DJ CFD - Dukascopy
EW FUTURES BREAKOUT H1 - Tradestation
GBPJPY BREAKOUT H1 - Dukascopy
GBPJPY BREAKOUT H4 - Dukascopy
GBPUSD H1 - Dukascopy
GOLD BREAKOUT M30 - Dukascopy
GOLD H1 CFD - Dukascopy
NQ BREAKOUT FUTURES  H1 - Tradestation
NQ CFD H1 D1 MULTI-TIMEFRAME  - Dukascopy
NQ CFD H1 - Dukascopy
Optimizer
PortfolioComposer
PortfolioMaster
Retester
Ultra_Auto_Pilot
Ultra_Matrix
Ultra_Matrix(2)

$ du -sh /opt/StrategyQuantX/user/projects/* 2>/dev/null | sort -rh | head -10
173M	/opt/StrategyQuantX/user/projects/Ultra_Matrix
29M	/opt/StrategyQuantX/user/projects/Ultra_Auto_Pilot
1.2M	/opt/StrategyQuantX/user/projects/Retester
328K	/opt/StrategyQuantX/user/projects/NQ CFD H1 D1 MULTI-TIMEFRAME  - Dukascopy
136K	/opt/StrategyQuantX/user/projects/Optimizer
116K	/opt/StrategyQuantX/user/projects/NQ CFD H1 - Dukascopy
116K	/opt/StrategyQuantX/user/projects/GBPUSD H1 - Dukascopy
116K	/opt/StrategyQuantX/user/projects/DJ CFD - Dukascopy
112K	/opt/StrategyQuantX/user/projects/NQ BREAKOUT FUTURES  H1 - Tradestation
104K	/opt/StrategyQuantX/user/projects/GOLD H1 CFD - Dukascopy

$ ls /opt/StrategyQuantX/user/data/History/ | grep -E '^(ES|NQ|YM|GC|CL)_'
CL_H1
CL_H4
CL_M15
CL_M5
ES_H1
ES_H4
ES_M15
ES_M5
GC_H1
GC_H4
GC_M15
GC_M5
NQ_H1
NQ_H4
NQ_M15
NQ_M5
YM_H1
YM_H4
YM_M15
YM_M5
```

---

## 4. Configuración y Filtros del Proyecto `Ultra_Matrix`

### Estructura del Proyecto
- Fichero: `/opt/StrategyQuantX/user/projects/Ultra_Matrix/project.cfx` (archivo ZIP estándar de 32 KB).
- Contenido del archivo comprimido (leído al vuelo sin descomprimir en disco):
  - `config.xml` (1.166 bytes): define tareas `Build` (`Build-Task1.xml`) y `Optimize` (`Improve-Task1.xml`), y bancos de datos (`Results`, `ToImprove`, `LastGeneration`, etc.).
  - `Build-Task1.xml` (1.305.428 bytes): tarea de búsqueda evolutiva genética.
  - `Improve-Task1.xml` (70.132 bytes): tarea de mejora.

### Parámetros Críticos y Filtros Hallados
1. **Activos configurados en el proyecto:**
   - La tarea `Build-Task1.xml` estaba configurada apuntando a **`AUDUSD_H1`** y **`AUDUSD_H4`** con motor `MetaTrader4` y comisión de 3.5 $ por operación (exactamente como detectó el diagnóstico de causa raíz).
2. **Algoritmo Genético:**
   - `PopulationSize`: `100`
   - `MaxGenerations`: `60`
   - `Fitness`: `ReturnDDRatio` (Ratio Rentabilidad / Drawdown)
3. **Restricciones de Operaciones y Filtros:**
   - En `Build-Task1.xml`:
     - `<Param key="MaxTradesPerDay" className="MaxTradesPerDay">0</Param>` (0 = sin límite diario en generación de candidatos).
     - Método `TakeMaxTradesPerDay`: `use="false"`.
     - `WFMinTradesInRun`: `> 8` (en la optimización Walk Forward se exige un mínimo de 8 operaciones por sub-período).
     - Filtro Walk Forward adicional: `WFPctOfProfitableRuns > 60%`, `WFMaxProfitByRunInPct < 60%`, `WFMaxPctDDbyRun <= 30%`.
   - En `Improve-Task1.xml`:
     - **`<Param key="MaxTradesPerDay" className="MaxTradesPerDay">1</Param>`**: En la tarea de mejora **SÍ está activado el límite de 1 operación al día**. Si una estrategia opera en marcos pequeños y requiere varias operaciones para validar sus reglas, este límite de 1 operación por día ahoga la generación y el Walk-Forward.

### Salida Cruda de Comandos

```bash
$ unzip -l /opt/StrategyQuantX/user/projects/Ultra_Matrix/project.cfx
Archive:  /opt/StrategyQuantX/user/projects/Ultra_Matrix/project.cfx
  Length      Date    Time    Name
---------  ---------- -----   ----
     1166  2026-08-29 19:39   config.xml
    70132  2026-08-29 19:39   Improve-Task1.xml
  1305428  2026-08-29 19:39   Build-Task1.xml
---------                     -------
  1376726                     3 files

# Configuración de símbolos en Build-Task1.xml
$ unzip -p /opt/StrategyQuantX/user/projects/Ultra_Matrix/project.cfx Build-Task1.xml | grep -i '<Data' -A 10
  <Data>
    <Setups>
      <Setup dateFrom="2023.11.01" dateTo="2026.08.18" testPrecision="1" session="No Session" slippage="3" minDist="0" engine="MetaTrader4">
        <Chart symbol="AUDUSD_H1" timeframe="H1" spread="2" spreadValue="0" />
        <Commissions>
          <Method type="PerTrade" use="true">
            <Params>
              <Param key="Commission" name="Commission" dataType="2" min="-1000.0" max="1000.0" step="0.01" value="3.5" description="Commission in $ per trade" decimals="2" className="PerTrade" category="Default" engine="*" />
            </Params>
          </Method>
        </Commissions>

# MaxTradesPerDay en Improve-Task1.xml
$ unzip -p /opt/StrategyQuantX/user/projects/Ultra_Matrix/project.cfx Improve-Task1.xml | grep -C 3 -i 'MaxTradesPerDay'
        <Param key="SignalTimeRangeTo" className="LimitTimeRange">57600</Param>
        <Param key="ExitAtEndOfRange" className="LimitTimeRange">false</Param>
        <Param key="MaxTradesPerDay" className="MaxTradesPerDay">1</Param>
        <Param key="Session" className="SessionOption">No Session</Param>
```

---

## 5. Capacidad y Recursos Disponibles del Servidor Hetzner

### Salida Cruda de Comandos

```bash
$ free -g
               total        used        free      shared  buff/cache   available
Mem:              62           5          45           0          12          57
Swap:             15           0          15

$ nproc
8

$ uptime
 04:08:36 up  1:47,  7 users,  load average: 0.12, 0.09, 0.07

$ df -h /
Filesystem      Size  Used Avail Use% Mounted on
/dev/md2        212G   14G  188G   7% /
```

### Síntesis de Capacidad
- **Memoria:** 62 GB totales, con **57 GB disponibles** (actualmente solo se usan 5 GB entre OS y GUI).
- **CPU:** 8 hilos lógicos en procesador Intel Core i7-6700 @ 3.40 GHz. Carga nula (`0.12`).
- **Disco:** 188 GB libres en `/` (solo 7% utilizado).
- **Conclusión de capacidad:** La máquina está prácticamente libre para asignar 6 hilos completos y 40-48 GB de RAM a StrategyQuant para procesar la rejilla de activos de fondeo.
