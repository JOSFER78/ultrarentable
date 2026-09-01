# I1 — Investigación StrategyQuant X: inventario verificado y config candidata FONDEO

Agente: AG-9. Fecha de ejecución: 2026-09-01. Idioma: ES.
Territorio de escritura: este fichero únicamente. No se lanzó ningún Build/Optimización.
Se ejecutó `sqcli.exe` dos veces con flags de solo-lectura (`-h`, `-license action=info`);
cada invocación carga la app completa (~1-3 min, datos+proyectos) porque `sqcli` no tiene un
modo "solo ayuda" ligero — está documentado como hallazgo en §2. No se lanzó ningún tercer
proceso pesado por prudencia de presupuesto de máquina.

## MÉTODO Y REGLA DE CITAS

- Fuente primaria 1: la instalación real en `C:\StrategyQuantX144` (ficheros de configuración,
  `.cfx` reales, logs de arranque de `sqcli.exe`).
- Fuente primaria 2: los `.cfx` de backup de `Ultra_Matrix` que SÍ existen en el repo
  (`estrategias_um/evidencia/backups_cfx/*.cfx`) — son ZIP con XML real, se han abierto y
  citado con ruta+línea.
- Fuente primaria 3: documentación oficial de strategyquant.com (WebSearch/WebFetch), con URL
  y fecha de captura (2026-09-01 para todas).
- Los `.md` del repo son AFIRMACIONES PREVIAS. Cada una tocada aquí se marca
  **CONFIRMADA / REFUTADA / NO VERIFICABLE**, nunca se da por buena solo por estar escrita.
- **Hallazgo de entorno crítico, previo a todo lo demás**: el proyecto `Ultra_Matrix` /
  `Ultra_Auto_Pilot` **NO existe en esta instalación local** (`C:\StrategyQuantX144\user\projects\`
  solo contiene `Builder, DJ CFD - Dukascopy, EW FUTURES BREAKOUT H1, GBPJPY BREAKOUT H1/H4,
  GBPUSD H1, GOLD BREAKOUT M30, GOLD H1 CFD, NQ BREAKOUT FUTURES H1, NQ CFD H1, NQ CFD H1 D1
  MULTI-TIMEFRAME, Optimizer, PortfolioComposer, PortfolioMaster, Retester` — proyectos de
  ejemplo de una instalación fresca del 2026-08-02). `Ultra_Matrix`/`Ultra_Auto_Pilot` vivían
  en un VPS Linux (`/home/ubuntu/StrategyQuantX144/...`, según `docs/Estado/auditoria/17A/17B/17C`
  y `orchestration/results/sqx_reconfiguracion_fondeo.md`, ambos con fecha 2026-08-11 y
  2026-09-01 respectivamente) al que **no tengo acceso desde este PC**. Por tanto, para la
  Pregunta 5 la única fuente primaria disponible aquí son los **7 backups `.cfx` de
  `Ultra_Matrix`** que sí quedaron copiados dentro del repo
  (`estrategias_um/evidencia/backups_cfx/backup_Ultra_Matrix_pre_*.cfx`, todos del 2026-08-29).
  Son XML real, no una re-narración — se citan con línea exacta más abajo. El **estado runtime
  en vivo del VPS a hoy 2026-09-01 es NO VERIFICABLE** (la licencia trial del VPS, según el
  propio `17B_SUPERFICIE_UI_SQX.md` línea 5, expiraba el 18.08.2026 — anterior a hoy).
  **Nota adicional de rigor**: existe una carpeta local `C:\Users\yo\AppData\Local\rclone\vfs\
  vps\home\ubuntu\...` (caché de un montaje `rclone` hacia el VPS). Se comprobó explícitamente
  antes de descartarla: **no hay proceso `rclone` corriendo ahora** (`tasklist` vacío) **ni
  aparece en `mount`**, y las subcarpetas de evidencia (`data/evidence/sqx_ultra_auto_pilot_
  strategy_*`) están **vacías por dentro** (0 ficheros) con fecha de modificación del 23-24 de
  agosto — es una caché local obsoleta de un montaje que ya no está activo, no una vía de acceso
  en vivo al VPS. Confirma, no contradice, que el VPS es inalcanzable desde aquí hoy.

---

## 1. Inventario real de la instalación (licencia, módulos)

**Versión**: `StrategyQuant X Pro Build 144` — versión interna exacta `144.2953` (impresa por
`sqcli.exe -h` y `-license action=info`, ver evidencia literal en §2). Coincide con el
`version="144.2953"` de todos los `<Project>` en los `.cfx` de `Ultra_Matrix` inspeccionados.

**Licencia — hallazgo crítico**:
```
StrategyQuant X Pro Build 144 (Trial license) - valid until 05.09.2026, license 46587B
```
(salida literal de `sqcli.exe -license action=info`, capturada 2026-09-01 16:40 UTC local).
Es decir: **licencia de PRUEBA (Trial), nivel "Pro"**, que caduca **en 4 días** desde la fecha
de este informe. Hardware ID ligado: `CBC66D20B937`. Email de licencia embebido en
`internal/SQUANT.dat` (base64 `dGlzdXRlQGdtYWlsLmNvbQ==` → `tisute@gmail.com`) — **no coincide
con el email del usuario de esta sesión**; anotado como dato objetivo, sin más interpretación.
Esto es un **bloqueo para la ventana de Emilio**: sin renovación/activación antes del
05.09.2026 esta instalación deja de generar. (Nota aparte, no verificable desde aquí: el VPS
tenía su propia licencia Trial "Pro Build 144" que ya expiró el 18.08.2026 según
`17B_SUPERFICIE_UI_SQX.md` L5 — son dos licencias Trial distintas, ambas de nivel Pro, ninguna
Ultimate.)

**Nivel de licencia — Starter / Professional ("Pro") / Ultimate**, tabla oficial obtenida de
`https://strategyquant.com/pricing/` (WebFetch, 2026-09-01):

| Módulo | Starter | Professional | Ultimate |
|---|---|---|---|
| Builder, Retester, Improver, Integrated Strategy Editor, Tick precision | ✓ | ✓ | ✓ |
| Advanced Robustness Tests, Monte Carlo, System Parameter Permutation | ✗ | ✓ | ✓ |
| Optimizer (Simple + Walk-Forward), Walk-Forward Matrix | ✗ | ✓ | ✓ |
| Custom Projects (workflow) | ✗ | ✓ | ✓ |
| QuantAnalyzer Pro license | ✗ | ✗ | ✓ |
| SQ for Business, Premium Modules (ATM) | ✗ | ✗ | ✓ |
| Portfolio Master/Composer | limitado a 4 estrategias | limitado a 4 | ilimitado |
| Seasonal Toolbox | ✗ | ✗ | ✓ |
| Market & Volume Profile (datos) | 1 mes | 1 mes | vitalicio |
| Precio (pago único) | $1.290 | $1.490 | $2.900 |

Esta instalación es **"Pro" = Professional** → tiene Monte Carlo, WFO/WF Matrix, SPP, Optimizer
y Custom Projects, pero **NO trae de serie QuantAnalyzer Pro, SQ4Business, ni Portfolio
Master/Composer ilimitado** (confirmado también en disco: no existe ningún `QuantAnalyzer.exe`
en `C:\StrategyQuantX144`, solo `StrategyQuantX.exe`, `sqcli.exe`, `CodeEditor.exe`,
`SQ_Installer.exe`).

**Qué hay realmente en disco** (`C:\StrategyQuantX144`, verificado con `ls`):
- `StrategyQuantX.exe` (GUI, Electron+Java), `sqcli.exe` (headless), `CodeEditor.exe` (editor de
  snippets Java, ver §3), `SQ_Installer.exe`.
- `user/projects/` — 14 proyectos de ejemplo + `Builder`. Cada proyecto es una carpeta con
  `project.cfx` (ZIP) + `databanks/` (subcarpetas `Existing portfolio`, `Initial population`,
  `Last generation`, `Results`, `Strategies to improve` — todas vacías en disco en esta
  instalación fresca).
- `user/settings/Configs/*.cfx` — 8 plantillas de proyecto reutilizables (DJ CFD H1, EW Futures
  H1, GBPJPY FX H1/H4, NQ CFD H1[/D1 Multi TF], XAUUSD CFD H1/M30).
- `user/settings/settings.xml` confirma `language=Spanish`, `skin=Dark`, `gpuAccelerated=true`,
  puertos internos (`WebServerPortUsed=8082`, y por `AppSettings.txt` en `internal/`:
  `AppWebServerPortSQUANT=5052`, `AppWebServerPortSQEDITOR=5051` — puertos distintos a los
  `5050`/`8080` documentados para el VPS en `17A`/`17B`, coherente con ser una instancia
  independiente en otra máquina).
- `user/extend/ResultsPlugins/` — contiene `CustomPlugin/` y `Prop Monte Carlo/` (un plugin de
  resultados ya presente de fábrica orientado a fondeo/prop-firm) + un `CLAUDE.md` de 29.8 KB
  (documentación interna del propio plugin, no inspeccionada en profundidad por estar fuera del
  alcance de esta tarea).
- `VolumeProfile/` — carpeta con `Custom Project/`, `TPO/`, `templates/`, y dos `.cfx`
  (`Custom Project Volume Profile.cfx`, `TPO/Build Config.cfx`). Según la tabla oficial de
  arriba, Volume Profile en tier Pro es "1 mes" de datos (no vitalicio) — **NO VERIFICADO si
  está realmente activo/funcional en esta licencia Trial** sin abrir la GUI (prohibido en este
  turno). Queda como experimento propuesto en la sección final.
- `internal/license.db` es SQLite 3 (confirmado con `file`), `internal/QDM.dat` contiene
  únicamente el texto `125`, `internal/SQUANT.dat` contiene `144` + el email base64 ya citado —
  interpretación razonable (NO CONFIRMADA por el fabricante): son marcadores de versión de
  componentes internos (SQUANT=build 144 coincide con SQX; QDM=125 sería la build interna del
  motor de datos QuantDataManager embebido, distinta de la build de SQX). No se encontró forma
  de confirmar esto con evidencia adicional sin abrir la GUI.
- `user/data/` contiene `data_futures.h2.db` (17,7 MB) y `data_stock.h2.db` (29,8 MB), ambos
  modificados hoy 16:52 (por el arranque de `sqcli.exe` en este turno, que hace
  "Sincronización de bases de datos con ficheros" al salir — ver log literal en §2). No se
  consultó su contenido (qué símbolos/TF hay importados) para no abrir un tercer proceso
  pesado — **NO VERIFICADO**, experimento propuesto en la sección final.

**Builder — genético/aleatorio/plantillas, islas, fitness**: CONFIRMADO presente y con
parámetros reales inspeccionables (ver §5, mismos tags que en `Ultra_Matrix`:
`BuildMode generationType="genetic-evolution"`, `Islands`, `PopulationSize`, `MaxGenerations`,
`EvoInSamplePeriod`, etc. — arquitectura de Build 144, igual en esta instalación y en la del
VPS porque comparten build number).

**Cross-checks disponibles** (mismo esquema XML verificado en los `.cfx` de `Ultra_Matrix`,
aplicable a esta instalación por ser el mismo build): `WalkForwardOptimization`,
`RetestWithHigherPrecision` (bar magnifier / precisión superior), `MonteCarloRetest` (con
métodos `RandomizeHistoryData`, `RandomizeMinDistance`, `RandomizeSlippage`, `RandomizeSpread`,
`RandomizeStrategyParameters`), `OptProfileSysParamPermutation` (System Parameter
Permutation/SPP), `RetestOnAdditionalMarkets`, `WalkForwardMatrix`, `MonteCarloManipulation`
(reordenamiento de trades), `WhatIf`. Todos confirmados como tags XML reales del `CrossChecks`
de Build 144 (ver cita de líneas en §5).

**Optimizer**: proyecto dedicado presente en disco (`user/projects/Optimizer/project.cfx`).
Según tabla de licencias, Simple + Walk-Forward Optimizer están en tier Pro. CONFIRMADO
disponible.

**Improver**: aparece en la tabla oficial bajo "CORE BUILDING" (disponible en TODOS los tiers,
incluido Starter). En los `.cfx` de `Ultra_Matrix` existe como tarea de tipo
`<Task type="Optimize" name="Improve" ... taskXMLFile="Improve-Task1.xml" />` con
`<StrategyType type="improve" ... improveDatabank="...">` (visto también citado en
`17C_PLAN_100_PORCIENTO_SQX.md` L39 para `Ultra_Improve_Pilot`). CONFIRMADO.

**Ranking y fórmulas de fitness CUSTOM**: mecanismo real y documentado — ver §3. CONFIRMADO con
fuente oficial (manual local + `strategyquant.com/doc/strategyquant/ranking-options/`).

**Databanks y su persistencia a disco**: CONFIRMADO que cada proyecto tiene carpetas físicas
`user/projects/<Proyecto>/databanks/<Nombre>/` — en esta instalación están todas vacías (0
ficheros), consistente con lo que `ESTADO.md` L26 y L63 describen para el VPS ("Disco:
`databanks/*` = 0 archivos en TODOS los bancos ... todo vive en memoria del motor"). Esto es un
patrón general de SQX 144 (persistencia bajo demanda vía `-databank action=save/synctofiles`,
no automática), no algo roto específicamente en `Ultra_Matrix` — ver comando real en §2.

**AlgoWizard**: confirmado presente como módulo de navegación (visto en la matriz de
coordenadas de `17B_SUPERFICIE_UI_SQX.md` L20, y `user/settings/AlgoWizardRecentFiles.xml`
existe en esta instalación, 29 bytes — vacío pero el módulo está activo).

**Snippets/indicadores custom en Java**: CONFIRMADO con el máximo nivel de evidencia posible sin
abrir la GUI — ver §3.

**Import/export**: CONFIRMADO vía `sqcli.exe -h` — comandos `-data action=import|export|
exportToMT4|exportToMT5|clone`, `-databank action=export` (a CSV o XLSX), `-symbol
action=add` con `datasource=[dukascopy,file,darwinex,crypto,yahoo,mt5api]`. Texto literal en §2.

---

## 2. CLI headless — salida literal de `sqcli.exe -h`

Comando ejecutado: `cd C:\StrategyQuantX144 && ./sqcli.exe -h` (2026-09-01, ~18:29-18:34 hora
local del PC). **Hallazgo operativo importante**: `sqcli.exe --help` (con doble guion) NO es
reconocido ("Comando --help no reconocido. Especifique -h") — el flag correcto es `-h`.
Además, **cada invocación de `sqcli.exe`, incluida `-h`, arranca la aplicación COMPLETA**
(motor Java, carga de `data.db`/`data_futures.h2.db`/`data_stock.h2.db`, carga de todos los
proyectos, verificación de licencia contra el servidor de StrategyQuant, un servidor HTTP
interno en el puerto 5052) **antes** de ejecutar el comando y salir. En esta máquina eso tomó
entre 66 y 118 segundos según la corrida (33 s + 34 s en el primer intento con datos ya
cacheados; 33 s + 42 s + 85 s en el segundo, con "Projects loaded in 85444 ms" — la carga es
más lenta la segunda vez, posiblemente por I/O contención con el proceso anterior). Esto es
relevante para diseñar cualquier orquestación por lotes: **no hay comando "ligero"** que evite
el arranque completo; cada llamada CLI paga ese coste fijo de 1-2 minutos.

Salida completa y literal (recortada solo en las líneas de log de arranque, que se resumen
arriba; el bloque de ayuda en sí es 100% literal):

```
Lanza StrategyQuant X en modo línea de comandos.
Parámetros: -h
Usage:
sqcli.exe
sqcli.exe license=xxxx
sqcli.exe -command [options]
-------------------------------------------
-project Manage projects.
-------------------------------------------
Arguments:
	action: Performs the specific action [list,start,startOnlyTask,startFromTask,stop,pause,resume,remove,status,loadconfig,saveconfig]
	name: (optional) Project name
	file: (optional) Path of the config file
	task: (optional) Task number, indexed from 1
Example:
	sqcli.exe -project action=list
	sqcli.exe -project action=start name=Builder
	sqcli.exe -project action=startOnlyTask name="Example custom project" task=2
	sqcli.exe -project action=startFromTask name="Example custom project" task=2
	sqcli.exe -project action=stop name=Builder
	sqcli.exe -project action=pause name=Builder
	sqcli.exe -project action=resume name=Builder
	sqcli.exe -project action=remove name=Custom
	sqcli.exe -project action=status name=Builder
	sqcli.exe -project action=loadconfig name=Builder file=Builder.cfx
	sqcli.exe -project action=saveconfig name=Builder file=Builder.cfx
-------------------------------------------
-databank Manage databanks.
-------------------------------------------
Arguments:
	action: Performs the specific action [list,count,save,load,delete,clear,create,remove,synctofiles,syncfromfiles,copy,move,export]
	project: Project name
	name: (optional) Databank name
	position: (optional) Position of databank
	folder: (optional) Path of the folder
	destproject: (optional) Destination project
	destdatabank: (optional) Destination databank
	file: (optional) Path of the file to export databank contents
	view: (optional) View name
	strategies: (optional) Strategies splitted with a semicolumn
Example:
	sqcli.exe -databank action=list project=Builder
	sqcli.exe -databank action=count project=Builder name=Results
	sqcli.exe -databank action=save project=Builder name=Results folder=test
	sqcli.exe -databank action=save project=Builder name=Results folder=test strategies="Strategy 0.1487,Strategy 0.1488"
	sqcli.exe -databank action=load project=Builder name=Results folder=test
	sqcli.exe -databank action=load project=Builder name=Results folder=test strategies="Strategy 0.1487,Strategy 0.1488"
	sqcli.exe -databank action=delete project=Builder name=Results strategies="Strategy 0.1487,Strategy 0.1488"
	sqcli.exe -databank action=clear project=Builder name=Results
	sqcli.exe -databank action=create project=Retester name=Custom
	sqcli.exe -databank action=remove project=Retester name=Custom
	sqcli.exe -databank action=copy project=Builder name=Results destproject=Retester destdatabank=Results
	sqcli.exe -databank action=synctofiles project=Builder name=Results
	sqcli.exe -databank action=syncfromfiles project=Builder name=Results
	sqcli.exe -databank action=move project=Builder name=Results destproject=Retester destdatabank=Results
	sqcli.exe -databank action=export project=Builder name=Results file=C:/data/DatabankExport.csv
	sqcli.exe -databank action=export project=Builder name=Results file=C:/data/DatabankExport.xlsx view=Custom
-------------------------------------------
-symbol Manage symbols.
-------------------------------------------
Arguments:
	action: Performs the specific action [list,add,edit,delete,clear]
	symbols: List of symbols
	instrument: (optional) Symbol instrument
	bartype: (optional) Bar type [startofbar, endofbar] (startofbar)
	datatype: (optional) Data type, [M1,TICK] (M1)
	datasource: (optional) Data source, [dukascopy,file,darwinex,crypto,yahoo,mt5api] (dukascopy)
	exchange: (optional) Exchange, [Bitfinex,BinanceCoinM,BinanceUsdtM,Binance,Coinbase,Poloniex] (Binance)
	timeframe: (optional) Imported timeframe [TICK,M1,M3,M5,M15,M30,H1,H2,H3,H4,H6,H8,H12,D1,Weekly,Monthly]
	postfix: (optional) Data postfix
	broker: (optional) Name of broker (SQ Default)
	path: (for mt5api datasource only) Path to mt5 installation
	datefrom: for mt5api datasource only) Data to be downloaded from
	dateto: (for mt5api datasource only) Data to be downloaded to
Example:
	sqcli.exe -symbol action=list
	sqcli.exe -symbol action=add symbols=EURUSD,GBPUSD datasource=dukascopy datatype=TICK
	sqcli.exe -symbol action=add symbols=ETHBTC datasource=crypto exchange=Binance timeframe=D1
	sqcli.exe -symbol action=add symbols=EURUSD,GBPUSD datasource=darwinex datatype=M1
	sqcli.exe -symbol action=add symbols=EURUSD datasource=darwinex datatype=M1 broker=[[Darwinex]]
	sqcli.exe -symbol action=edit symbol=EURUSD name=EURUSD_OLD
	sqcli.exe -symbol action=delete symbols=EURUSD,GBPUSD
	sqcli.exe -symbol action=clear symbols=EURUSD,GBPUSD
-------------------------------------------
-instrument Manage instruments.
-------------------------------------------
Arguments:
	action: Performs the specific action [list,add,edit,delete]
	instrument: Instrument to add
	description: (optional) Instrument description
	pointvalue: (optional) Point value (100000)
	ticksize: (optional) Pip/Tick size (0.0001)
	tickstep: (optional) Pip/Tick step (0.00001)
	defaultspread: (optional) Default spread (2)
	datatype: (optional) Data type, [stock,futures,forex,cfds,etf,index,crypto] (forex)
	commissions: (optional) Commissions
	minDistance: (optional) Minimal distance (0)
	orderSizeMultiplier: (optional) Order size multiplier (1)
	orderSizeStep: (optional) Order size step (1)
	swap: (optional) Swap
	broker: (optional) Name of broker (SQ Default)
Example:
	sqcli.exe -instrument action=list
	sqcli.exe -instrument action=add instrument=EURUSD
	sqcli.exe -instrument action=edit instrument=EURUSD datatype=forex
	sqcli.exe -instrument action=delete instruments=EURUSD
-------------------------------------------
-data Manage data.
-------------------------------------------
Arguments:
	action: Performs the specific action [update,import,export,exportToMT4,exportToMT5,clone,timezones]
	symbol: Symbol to import
	filepath: Path of file
	filename: Name of file
	instrument: (optional)Symbol instrument
	bartype: (optional)Bar type [startofbar, endofbar]
	errorhandling: (optional)Data errors handling [stop,ignore]
	timezone: (optional) Timezone. To list the available timezones, use command -tz [Etc/UCT, Europe/London, America/New_York...]
	timeframe: (optional) Imported timeframe [auto,Intraday,TICK,M1,M5,M15,M30,H1,H4,D1]
	datefrom: (optional) Date from in format 'yyyy.MM.dd'
	dateto: (optional) Date to in format 'yyyy.MM.dd'
	outputdir: (optional) Target directory
	prefix: (optional) File prefix
	format: (optional) Format, [Generic tick format (comma delimited),Generic bar format (comma delimited),Generic tick format (tab delimited),Generic bar format (tab delimited),MetaTrader4 tick format,MetaTrader4 bar format,Amibroker bar (aqi) format,Amibroker tick (aqi) format,Birt's CSV2FXT format,Forex Tester bar format,Forex SB bar format,Ninja Trader tick format,Ninja Trader bar format,Neuroshell Trader format,Tradestation bar format] (MetaTrader4 bar format)
	cIncludeHeader: (optional - only for Custom format) Include header
	cHeader: (optional - only for Custom format) Header format
	cFormat: (optional - only for Custom format) Format definitio
	postfix: (optional) Data postfix (_{timeframe}_{cloneTime})
	removeWeekends: (optional) Remove weekends [true,false] (false)
	hours: (optional) Fixed shift in hours [stop,ignore]
	appPath: MT4 Installation folder
	dataPath: MT4 Data folder
	serverName: Server name
	mt4Symbol: Symbol from MT4 data specification file
	mt4SymbolName: Name in MT4
	spreadType: Spread type [points,pips,real]
	spreadValue: Spread in points/pips
Example:
	sqcli.exe -data action=update
	sqcli.exe -data action=update symbols=GBPUSD_M1
	sqcli.exe -data action=import symbol=EURUSD instrument=EURUSD filepath=C:/data/EURUSD.csv
	sqcli.exe -data action=export symbols=EURUSD_M1,GBPUSD_M1 timeframe=M1 datefrom=2018.01.01 dateto=2018.12.31 outputdir=C:/data
	sqcli.exe -data action=export symbols=EURUSD_M1 timeframe=M1 format=Custom cFormat=[Date:yyyy.MM.dd],[Time:HH:mm],[Open],[High],[Low],[Close],[Volume] outputdir=C:/data
	sqcli.exe -data action=export symbols=EURUSD_M1 timeframe=M1 format=Custom cIncludeHeader=true cHeader=Date,Time,Open,High,Low,Close,Volume cFormat=[Date:yyyy.MM.dd],[Time:HH:mm],[Open],[High],[Low],[Close],[Volume] outputdir=C:/data
	sqcli.exe -data action=clone symbols=AUDCAD hours=8
	sqcli.exe -data action=timezones
	sqcli.exe -data action=exportToMT4 symbol=EURUSD timeframe=M1 appPath=C:/mt4 dataPath=C:/Users/Tomas/AppData/Roaming/MetaQuotes/Terminal/BB190E062770E27C3E79391AB0D1A117 serverName=Demo
	sqcli.exe -data action=exportToMT4 symbol=EURUSD timeframe=M1 appPath=C:/mt4 dataPath=C:/Users/Tomas/AppData/Roaming/MetaQuotes/Terminal/BB190E062770E27C3E79391AB0D1A117 serverName=Demo mt4Symbol=EURUSD mt4SymbolName=EURUSD
	sqcli.exe -data action=exportToMT5 symbol=EURUSD timeframe=Tick
	sqcli.exe -data action=exportToMT5 symbol=EURUSD timeframe=M1 spreadType=points spreadValue=2 datefrom=2018.01.01 dateto=2018.12.31 outputdir=C:/data filename=EURUSD
-------------------------------------------
-tools Tools.
-------------------------------------------
Arguments:
	action: Performs the specific action [orderstocsv,orderstoxlsx]
	file: Path of the file or folder
	usecomma: (optional) Path of the output file or folder
	data: (optional) Data [main,all]
Example:
	sqcli.exe -tools action=orderstocsv file="Strategy 0.1487.sqx"
	sqcli.exe -tools action=orderstoxlsx file="Strategy 0.1487.sqx"
	sqcli.exe -tools action=orderstocsv file=C:/reports output=C:/trades
	sqcli.exe -tools action=orderstocsv file="Strategy 0.1487.sqx" usecomma=true data=main
-------------------------------------------
-stockgroup Stockgroups.
-------------------------------------------
Arguments:
	action: Performs the specific action [updateAll-update stocks from all group, update-update stocks from specified group, importstocks-import stocks into group from file, exportstocks-export list of stocks from group into file, import-import group definition, export-export geoup definition, list-list of groups]
	id: Id of stockgroup (for action=update|importstocks|exportstocks)
	filepath: path to file (for action=importstocks|exportstocks)
Example:
	sqcli.exe -stockgroup action=updateAll
	sqcli.exe -stockgroup action=update id=1
	sqcli.exe -stockgroup action=list
	sqcli.exe -stockgroup action=importstocks filepath=stocks.csv id=1
	sqcli.exe -stockgroup action=exportstocks filepath=stocks.csv id=1
	sqcli.exe -stockgroup action=import filepath=stocks.csv
	sqcli.exe -stockgroup action=export filepath=stocks.csv id=1
-------------------------------------------
-brokerprofile BrokerProfiles.
-------------------------------------------
Arguments:
	action: Performs the specific action [updateAll, update, importstocks, exportstocks, list]
	id: Id of brokerprofile (for action=update|importstocks|exportstocks)
	filepath: path to file (for action=importstocks|exportstocks)
Example:
	sqcli.exe -brokerprofile action=updateAll
	sqcli.exe -brokerprofile action=update id=1
	sqcli.exe -brokerprofile action=list
	sqcli.exe -brokerprofile action=importstocks filepath=stocks.csv id=1
	sqcli.exe -brokerprofile action=exportstocks filepath=stocks.csv id=1
	sqcli.exe -brokerprofile action=import filepath=stocks.csv
	sqcli.exe -brokerprofile action=export filepath=stocks.csv id=1
-------------------------------------------
-run Runs commands from the file.
-------------------------------------------
Arguments:
	file: Path of the file
Example:
	sqcli.exe -run file=C:/data/commands.txt
-------------------------------------------
-gui Starts webserver to access GUI remotely.
-------------------------------------------
Example:
	sqcli.exe -gui
-------------------------------------------
-deletefile Deletes the specific file.
-------------------------------------------
Arguments:
	file: Path of the file or folder
Example:
	sqcli.exe -deletefile file=C:/reports/evaluate.txt
-------------------------------------------
-waitfor Waits for user/file
-------------------------------------------
Arguments:
	action: Waits for action [user,file]
	file: Path of the file or folder
Example:
	sqcli.exe -waitfor action=user
	sqcli.exe -waitfor action=file file=C:/reports/controlfile.txt
-------------------------------------------
-execute Calls external script
-------------------------------------------
Arguments:
	file: Path of the script
Example:
	sqcli.exe -execute file=C:/reports/evaluate.bat
	sqcli.exe -waitfor
-------------------------------------------
> Redirects output to a file
-------------------------------------------
Example:
	sqcli.exe -symbol action=list > C:/reports/output.log"
-------------------------------------------
-license Manage license
-------------------------------------------
Arguments:
	action: Performs the specific action [info,update]
	code: (optional) License code
Example:
	sqcli.exe -license action=info
	sqcli.exe -license action=update code=xxxxx
-------------------------------------------
-exit Exit.
-------------------------------------------
Example:
	sqcli.exe -exit
```

**Salida literal de `sqcli.exe -license action=info`** (segunda invocación, ~18:39-18:42):
```
StrategyQuant X Pro Build 144 (Trial license) - valid until 05.09.2026, license 46587B
```

**Confirmado también**: existe un servidor HTTP embebido (`API HTTP iniciada, puede acceder a
ella en http://localhost:5052/call?cmd=-h`), es decir todos los comandos de arriba son también
invocables por HTTP GET (`http://localhost:5052/call?cmd=-project%20action=status`), igual al
patrón `http://localhost:5050/call?cmd=...` que usa `improve_cycle.sh` en el VPS según
`sqx_reconfiguracion_fondeo.md` §6 — mismo mecanismo, puerto distinto porque es otra máquina.
Este hallazgo **CONFIRMA** de forma independiente, en esta instalación, el patrón HTTP GET que
el doc del VPS describe para el suyo.

**Efecto colateral observado dos veces**: `sqcli.exe` hace peticiones HTTPS salientes a
`exchange.coinbase.com` en el arranque (warnings de cookie `__cf_bm` de Cloudflare) — SQX
consulta datos de mercado de Coinbase como parte de su inicialización, aunque el proyecto activo
no use cripto. Dato objetivo, sin interpretación adicional (no se investigó el propósito exacto
por estar fuera del alcance y no requerir cómputo pesado adicional).

---

## 3. ¿Se puede expresar el criterio de certificación 1.1 DENTRO de SQX?

**Respuesta: SÍ, por dos mecanismos independientes y complementarios, ambos confirmados con
fuente oficial.**

### Mecanismo A — Condiciones/Rankings nativos (sin programar)

Los `.cfx` reales inspeccionados (§5) usan exactamente esta estructura: cada cross-check
(`WalkForwardOptimization`, `MonteCarloRetest`, etc.) y el bloque `Rankings` tienen un nodo
`<Conditions thresholdPct="N">` con `<Condition use="true"><Left-Side valueType="column">`
(una métrica nativa: `NetProfit`, `NumberOfTrades`, `DrawdownPct`, `WFMinTradesInRun`,
`WFPctOfProfitableRuns`, etc.) `<Comparator value="&gt;="/>` `<Right-Side valueType="numeric">`
(un umbral). Esto es exactamente lo necesario para codificar directamente en el Builder:
"OOS trades ≥ 200" → `Column-Value NumberOfTrades resultType="..." sampleType=<OOS> Comparator
">=" Numeric-Value 200`; "PF OOS ≥ 1,25" → mismo patrón con `ProfitFactor`; el ratio OOS/IS se
puede expresar como condición `Right-Side valueType="column"` contra `pctRatio="50"` (visto
literalmente en `RetestWithHigherPrecision` de `Ultra_Matrix`, L1302-1307: compara
`NetProfit resultType="RetestWithHigherPrecision"` contra `NetProfit resultType="main"
pctRatio="80"` — es decir, SQX YA soporta nativamente "métrica de un cross-check ≥ X% de la
métrica principal", que es estructuralmente el mismo patrón que "PF_OOS/PF_IS ≥ 0,5"). Fuente
oficial que documenta este editor de condiciones:
`https://strategyquant.com/doc/strategyquant/ranking-options/` (WebFetch 2026-09-01): confirma
que Rankings soporta "Automatic Filters" (descarta 0 trades, sin beneficio) y "Custom Filters"
con abreviaturas **IS / OOS / RT (Robustness Tests) / P (Portfolio)**, evaluables en
Money/Percent/Pips, para long/short/ambos — es decir, el propio fabricante documenta IS vs OOS
como ejes de filtro de primera clase en el editor de condiciones, sin necesidad de programar.

### Mecanismo B — Columna de databank custom en Java (para lógica compuesta)

Confirmado con el **manual oficial local** `C:\StrategyQuantX144\Extending_SQX_es.pdf` (traído
en la instalación; nota: el propio `Extending_SQX.pdf` en inglés es solo una portada que redirige
a `https://strategyquant.com/codebase/` — la versión en español SÍ trae el contenido técnico
completo, "Build 109" de 2018, pero la arquitectura de snippets/CodeEditor sigue siendo la misma
en Build 144: existe `CodeEditor.exe` en esta instalación y la carpeta `user/extend/` con
subcarpetas `Code/`, `Plugins/`, `ResultsPlugins/`, `Snippets/` — el mismo árbol descrito en el
manual). El manual documenta paso a paso (páginas 23-30) cómo crear un **"Databank column"**
(clase Java que extiende `DatabankColumn`, método `compute(SQStats stats, ...)` que puede leer
cualquier columna ya calculada vía `stats.getDouble("NombreColumna")`, más
`setDependencies(...)` para encadenar). Esto permite escribir una única columna nueva, p.ej.
`FondeoCertificacion11`, cuyo `compute()` sea literalmente:
```java
boolean pasa = stats.getInt("NumberOfTradesOOS") >= 200
            && stats.getDouble("ProfitFactorOOS") >= 1.25
            && safeDivide(stats.getDouble("ProfitFactorOOS"), stats.getDouble("ProfitFactorIS")) >= 0.5
            && stats.getDouble("WFPctOfProfitableRuns") >= UMBRAL_ESTABILIDAD;
return pasa ? 1.0 : 0.0;
```
y usarla como `Ranking type="FondeoCertificacion11"` en `<FitnessCriteria>` (mismo patrón XML
que `<Ranking type="ReturnDDRatio" />` ya visto en producción) **y/o** como `<Condition>` de
descarte duro en `Rankings type="always"`. Es decir: **lo que salga del Builder puede venir
pre-filtrado exactamente por el criterio 1.1**, sin esperar a un filtro externo posterior. La
limitación documentada por el propio fabricante (manual, p.6 y p.22/25/29, en rojo): "la
funcionalidad de CodeEditor en SQ X aún está en desarrollo... si tienes problemas, podemos
hacerlo por ti" — es decir, el propio fabricante admite que la vía de programación puede
requerir soporte manual, no es "point and click" trivial. Corroborado independientemente por
WebSearch (`strategyquant.com/forum`, 2026-09-01): "You can extend SQ X with your own function
programming it in Java, though this is still in Alpha version, and the documentation is in
development" — coincide con el propio manual.

**Conclusión Q3**: mecanismo CONFIRMADO por fuente oficial (manual + doc web), disponible en
esta licencia (CodeEditor no está gateado por tier en la tabla oficial de §1). No se probó en
vivo (habría requerido compilar y reiniciar SQX — cómputo/GUI, fuera del alcance de este turno).
Experimento propuesto en la sección final.

---

## 4. Configuración FONDEO nativa (sesiones, MaxTradesPerDay, comisiones)

Todo lo siguiente son tags XML reales, confirmados en `Build-Task1.xml` de `Ultra_Matrix`
(arquitectura Build 144, aplicable a cualquier proyecto de esta instalación):

- **Sesión/killzone**: `<Param key="Session" className="SessionOption">LondonNY</Param>` +
  `<Param key="LimitTimeRange" className="LimitTimeRange">true</Param>` +
  `SignalTimeRangeFrom=25200` (07:00 UTC) + `SignalTimeRangeTo=75600` (21:00 UTC) — confirmado
  real (`backup_Ultra_Matrix_pre_mcfix_20260829_145736.cfx` → `Build-Task1.xml` L1-19).
  `SessionOption` acepta valores predefinidos (`LondonNY` visto en uso); no se enumeró la lista
  completa de sesiones disponibles (RTH CME no verificado por nombre exacto — NO VERIFICADO,
  requeriría abrir el combo en GUI).
- **Cierre intradía obligatorio**: `ExitAtEndOfDay` (bool) + `EODExitTime` (segundos) — el tag
  existe y es nativo (visto `false`/`83040` en el `.cfx` de `Ultra_Matrix`, pero el mecanismo
  para forzarlo a `true` es directo).
- **Cierre viernes**: `ExitOnFriday` + `FridayExitTime` — confirmados nativos, ya `true`/`74400`
  (20:40 UTC) en `Ultra_Matrix`.
- **MaxTradesPerDay**: existe como parámetro global de `BuildTradingOptions`
  (`<Param key="MaxTradesPerDay" className="MaxTradesPerDay">N</Param>`, 0=sin límite) **y**
  como bloque de money-management alternativo `Method type="TakeMaxTradesPerDay"` con su propio
  `Param key="Trades"`. Ambos mecanismos son nativos y compatibles con exigir ≥200 operaciones
  OOS siempre que N no sea tan bajo que estrangule el volumen total de trades en el rango de
  fechas usado — ver §5 para la cifra real encontrada en `Ultra_Matrix` (no es 1, ver abajo).
- **Comisiones/slippage reales**: `<Commissions><Method type="PercentageBased"|"PerTrade"|...>`
  visto en uso real (`CommissionPct` en `Ultra_Matrix`); `sqcli -instrument action=add` (§2)
  acepta `commissions`, `pointvalue`, `ticksize`, `tickstep`, `defaultspread` — es decir, se
  puede definir un instrumento sintético `MES`/`MNQ`/`MYM`/`MGC`/`MSI`/`MCL` con sus point
  values y comisión por contrato reales vía CLI sin GUI. **NO VERIFICADO**: no se confirmaron
  los valores exactos de comisión/tick de estos micros CME en esta instalación (no hay
  instrumentos CME definidos en los proyectos de ejemplo locales) — son datos que Emilio/el
  orquestador deben aportar (p.ej. MES $0,62/contrato/lado en muchos brokers, puede variar) y
  cargar con `-instrument action=add`.

---

## 5. Por qué el Build de `Ultra_Matrix` era estéril — confirmación línea por línea

Fuente primaria usada (única disponible desde este PC): los 7 `.cfx` de backup en
`estrategias_um/evidencia/backups_cfx/`, todos del 2026-08-29, abiertos como ZIP y su
`Build-Task1.xml`/`Improve-Task1.xml`/`config.xml` leídos directamente.

### Afirmación previa (`ESTADO.md` L45, `CONFIG_DOORS.md` L25): "MaxTradesPerDay = 1"
**REFUTADA por los `.cfx` disponibles.** En los tres backups examinados
(`pre_window_20260829` 09:05, `pre_mcfix_..._145109` 14:51, `pre_mcfix_..._145736` 14:57),
`Build-Task1.xml` línea 13 dice exactamente:
```xml
<Param key="MaxTradesPerDay" className="MaxTradesPerDay">0</Param>
```
(0 = sin límite, no 1). Además el bloque alternativo `Method use="false" type=
"TakeMaxTradesPerDay"` (L1652-1656) tiene `Param key="Trades" type="Integer">2</Param>` — está
además **desactivado** (`use="false"`), y aunque estuviera activo su valor sería 2, no 1. No se
encontró en ninguno de los 7 backups un `MaxTradesPerDay=1` real. Es posible que la cifra "1"
correspondiera al estado en memoria del motor en el momento exacto de la extracción de las
12:13 del 29-08 (`/tmp/um_doors/cfx_actual/`, no disponible aquí) y que un backup posterior
(14:51/14:57) ya lo hubiera revertido a 0 — **NO VERIFICABLE** cuál era el valor exacto a las
12:13 sin ese fichero; lo que sí es un HECHO citable es que **en los backups que sí existen en
el repo, el valor es 0, no 1**.

### Afirmación previa: "fusible MC con RandomizeHistoryData 10/10/10/10 activo, incompatible con MaxTradesPerDay=1"
**PARCIALMENTE REFUTADA / matizada.** Se rastreó el atributo `use` del método
`RandomizeHistoryData` en los 3 backups:
| Backup (hora) | `use` | Params ProbabilityUp/Down, MaxChangeUp/Down |
|---|---|---|
| `pre_window` 09:05 | `true` | 30/30/30/30 |
| `pre_mcfix..145109` 14:51 | `true` | 10/10/10/10 |
| `pre_mcfix..145736` 14:57 | **`false`** | 10/10/10/10 (valores quedan pero el método está apagado) |

Es decir, entre las 14:51 y 14:57 del propio 29-08 alguien desactivó `RandomizeHistoryData` —
coherente con que el "fix de hoy" mencionado en `ESTADO.md` R1 (L46: "el fix de hoy
(RandomizeHistoryData 30→10) NO tocó la causa") en realidad tuvo una segunda vuelta (10→apagado)
que si el documento data de las 16:2x y el backup `145736` es de las 14:57, es coherente en el
tiempo. **Lo que permanece activo en los tres backups** (y por tanto es la explicación más
sólida y no refutada del "backtest sin transacciones"): `RandomizeMinDistance` (0-10),
`RandomizeSlippage` (0.0-5.0), `RandomizeSpread` (visto parcialmente, mismo patrón `use="true"`)
— es decir, el mecanismo general "el MC introduce variación aleatoria y algunos candidatos con
pocos trades se quedan sin ninguno" sigue siendo plausible y **NO REFUTADO**, pero la cadena
causal exacta escrita en `ESTADO.md` L46 (que ata el problema a `MaxTradesPerDay=1`
específicamente) no se sostiene contra los `.cfx` disponibles: el valor real es 0.

### Afirmación previa: "databank real cae en 'Last generation' (con espacio), gatillo mira 'LastGeneration' (sin espacio)"
**CONFIRMADA con evidencia exacta.** `config.xml` de `pre_window` (09:05, ANTES del rename) —
```xml
<Databank name="Last generation" view="Default - Main data" syncType="Auto-sync never" />
```
`config.xml` de `pre_mcfix..145736` (14:57, DESPUÉS del rename) —
```xml
<Databank name="LastGeneration" .../>
...
<Databank name="Last generation" view="Default" syncType="Auto-sync never" />
```
**ambos nombres coexisten simultáneamente** tras el rename (9 databanks registrados vs 5 antes
— coincide exactamente con la cifra de `CONFIG_DOORS.md` L58 "Databanks registrados | 9 | 5").
`Build-Task1.xml` línea 14840-14843 confirma el mismo patrón en la sección `<Databanks>` del
propio Build (Output/Input apuntan a `LastGeneration`/`InitialPopulation`/`ToImprove` tras el
rename, a `Last generation`/`Initial population`/`Strategies to improve` antes). Y
`Improve-Task1.xml` línea 1169 confirma que la tarea Improve lee explícitamente de
`<Databank label="Input databank" name="Input" value="LastGeneration" />` — el nombre SIN
espacio, exactamente como afirma `ESTADO.md` R3. **Lo que NO es verificable desde aquí** es el
estado runtime en memoria (si el motor seguía escribiendo en el nombre legacy con espacio pese
al rename en disco) — esa es información de la API en vivo del VPS (`-databank action=list`),
inaccesible hoy. Es corroborado indirectamente por un hallazgo independiente de
`17A_CAPACIDADES_MCP_SQX.md` L70: "Si se edita el `.cfx` en disco mientras SQX corre, SQX a
veces conserva el `.cfx` viejo en RAM" — mecanismo consistente con la teoría, pero no una
confirmación directa de las cifras (91 vs 0).

### Otros parámetros del Build confirmados exactos contra `CONFIG_DOORS.md`
Todos via `pre_mcfix..145736/Build-Task1.xml`, líneas 71-93 y 1197-1667:
`PopulationSize=100` ✓, `Islands=8` ✓, `MaxGenerations=60` ✓, `CrossoverProbability=95` ✓,
`MutationProbability=45` ✓, `MigrationRate=15`/`MigrationModulo=20` ✓,
`FreshBloodReplaceSimilar/Weakest=true/true`, `WeakestPct=25`, `WeakestGenerations=2` ✓,
`DecimationCoef=4` ✓, `EvoInSamplePeriod ratio=70` ✓, `EvoRestartOnFinish status=true` ✓,
`EvoRestartOnStagnation status=false generations=30` ✓ (coincide con "OnStagnation false (30
gens)"), `StopCondition type=databank-full passedStrategies=200 minutes=30` ✓, `Rankings
type=always` + `Ranking type=ReturnDDRatio` ✓, `RiskManagement maxDrawdown=30` ✓,
`RiskFixedBalancePct Risk=2 MaxLots=5` ✓. **CONFIRMADOS uno por uno, sin discrepancias.**
`WalkForwardOptimization` (period=5, optimization=20, thresholdPct=80, condiciones NetProfit>0 /
NetProfit%>60 / WFPctOfProfitableRuns>70 / WFMaxProfitByRunInPct<50 / WFMinTradesInRun>20 /
WFMaxPctDDbyRun<=25) ✓ todos exactos. `Improve-Task1.xml` (RobCombRows/Cols=4, condiciones
NetProfit%WFO>65, WFPctOfProfitableRuns>70, WFMaxProfitByRunInPct<45) ✓ exactos. **Veredicto
general sobre `CONFIG_DOORS.md`: CONFIRMADO en el ~95% de las cifras citables; la única cifra
REFUTADA por evidencia directa es `MaxTradesPerDay=1` (el valor real en los backups es 0).**

---

## 6. QuantDataManager (QDM)

**NO instalado como aplicación standalone en este PC** (confirmado: no existe
`QuantDataManager.exe` ni carpeta con ese nombre en `C:\StrategyQuantX144`, `C:\Program Files`,
ni en `C:\Users\yo` hasta profundidad 3). Sí existe `internal/QDM.dat` (contenido: `125`),
compatible con ser un identificador de build de un componente QDM **embebido dentro de SQX X**
(interpretación razonable, NO confirmada por el fabricante).

Según documentación oficial (`strategyquant.com/quantdatamanager/` y páginas de doc asociadas,
WebSearch 2026-09-01): QuantDataManager es una **herramienta de gestión de datos históricos**
con fuentes Dukascopy, Darwinex, Yahoo, varios exchanges cripto — "la misma tecnología está
también integrada directamente en StrategyQuant X a través de su sección Data Manager, así que
los usuarios de SQX pueden preparar y gestionar datos sin salir de la aplicación". Es decir:
**existe como producto standalone separado Y como módulo integrado dentro de SQX** (visible en
la navegación de la GUI, coordenada `(150,115) "Data Manager"` documentada en
`17B_SUPERFICIE_UI_SQX.md` L20, y confirmado en esta instalación por el propio `sqcli -symbol
action=add datasource=dukascopy` de §2 — el datasource `dukascopy` es la opción por defecto del
comando, evidencia adicional de que el Data Manager interno de SQX habla con Dukascopy de
fábrica). "QuantDataManager Pro" es un añadido de pago (~$349 según un resumen de foro/blog no
verificado contra la página oficial de precios directamente) que da descargas más rápidas por
CDN propio y sin publicidad — **separado de la licencia de SQX**.

**Relación con `services/data_ingestion/dukascopy_feed.py`**: inspeccionado directamente
(cabecera del fichero, `services/data_ingestion/dukascopy_feed.py` L1-24). Es un downloader
propio que golpea directamente
`https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0}/{DD}/{HH}h_ticks.bi5` (con el
mes cero-indexado documentado explícitamente como "el error clásico de esta API"), descomprime
LZMA y parsea registros binarios de 20 bytes. **No usa QDM ni el Data Manager de SQX en
absoluto** — es un pipeline REAL-ONLY completamente independiente, con su propia doctrina
("NO sintetiza barras, NO rellena huecos"). Por tanto **no sustituye ni depende de QDM: son dos
vías paralelas hacia la misma fuente (Dukascopy)**. El de SQX (`-symbol action=add
datasource=dukascopy`) importaría directamente al `data.db` interno de SQX en el formato que el
motor necesita para correr Builds; el propio (`dukascopy_feed.py`) alimenta el pipeline de datos
del proyecto (`data/sqx_imports/dukascopy/` según `sqx_reconfiguracion_fondeo.md` §4, aunque en
esta instalación local esa carpeta está vacía). **Recomendación implícita de la evidencia**: para
que SQX pueda correr un Build sobre un símbolo, ese símbolo debe existir en el `data.db` interno
de SQX — importado o bien por el Data Manager/QDM propio de SQX (`-symbol action=add`), o bien
convirtiendo los CSV de `dukascopy_feed.py` al formato que `-data action=import` espera
(`filepath`+`filename`, formato "Generic tick/bar" o custom vía `cFormat`). **NO VERIFICADO**
cuál de las dos vías es más barata en la práctica para este proyecto — sería el experimento
natural a proponer (ver sección final), no ejecutado aquí por ser I/O y no "solo ayuda".

---

## 7. QuantAnalyzer (QA)

**NO instalado en este PC**: no existe ningún ejecutable `QuantAnalyzer*.exe` en
`C:\StrategyQuantX144` (los únicos `.exe` son `StrategyQuantX.exe`, `sqcli.exe`,
`CodeEditor.exe`, `SQ_Installer.exe`). Referencias a "QuantAnalyzer" en el repo
(`docs/plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md` L37) lo listan como "módulo" dentro de
la barra de pestañas de SQX junto a Portfolio/AlgoWizard — **esto es INEXACTO/REFUTADO por la
documentación oficial**: QuantAnalyzer es un **producto separado** de StrategyQuant s.r.o., con
su propia página (`strategyquant.com/quantanalyzer/`) y su propio precio, no una pestaña interna
de SQX X. Lo que sí puede pasar (no verificado aquí) es que exista una integración/exportación
desde SQX hacia QA, no que QA viva dentro de SQX.

**Licencia**: según la tabla oficial de §1, **"QuantAnalyzer Pro license" solo viene incluida
en el tier Ultimate**. Esta instalación es Trial "Pro" (Professional) → **QuantAnalyzer Pro NO
está incluido**. Un resumen de búsqueda web (no una página oficial fetched directamente) cita
que "tu licencia StrategyQuant también es válida para QuantAnalyzer Pro" en ciertos contextos y
un valor de $349 — dato **NO VERIFICADO directamente contra `strategyquant.com/quantanalyzer/
pricing`** (no se hizo fetch de esa URL específica en este turno); se reporta la cifra tal cual
apareció en el resumen de búsqueda, marcada explícitamente como no confirmada de primera mano.

**Qué aportaría QA frente a hacerlo en el motor propio** (según hallazgos de búsqueda web,
`strategyquant.com/quantanalyzer/portfolio-master/` y `.../doc/quantanalyzer/portfolio-
correlation-explained/`, WebSearch 2026-09-01): cálculo de correlación entre estrategias de una
cartera (usable en Portfolio Master para filtrar por correlación máxima), y —según la propia
tabla de licencias de SQX— Walk-Forward y Monte Carlo YA están disponibles en SQX Pro para
estrategias individuales (no exclusivos de QA). El valor diferencial de QA parece concentrarse
en el **análisis de cartera** (multi-estrategia, correlación, "Portfolio Master") más que en
duplicar WF/MC por estrategia. **Conclusión Q7**: dado que esta instalación NO tiene QA, y que
Portfolio Master/Composer en tier Pro está limitado a 4 estrategias (tabla §1), **la vía de
cartera con SQX+QA en este PC bajo la licencia actual es limitada**; hacerlo en el motor propio
(`services/validation/`) evita esa limitación de 4 estrategias y el coste adicional, a cambio de
mantener el código de correlación/MC de cartera propio (que, según `14_analisis_antioverfit.md`
L86-110, ya existe como diseño con NautilusTrader como 2º motor). **NO VERIFICADO** con más
detalle por no tener QA instalado para inspeccionar directamente.

---

## 8. Puente SQX → motor propio

**Formato `.sqx` = ZIP/JAR**: CORROBORADO por analogía de formato, no verificado directamente
sobre un `.sqx` real desde este PC (esta instalación no tiene ningún `.sqx` de estrategia
generada — todos los databanks están vacíos, §1). Lo que SÍ verifiqué directamente aquí es que
**`.cfx` (mismo fabricante, mismo build 144, mismo contenedor de proyecto) es un ZIP real**:
```
$ unzip -l backup_Ultra_Matrix_pre_mcfix_20260829_145736.cfx
  Length      Date    Time    Name
     1166  2026-08-29 14:51   config.xml
    70133  2026-08-29 14:51   Improve-Task1.xml
  1305431  2026-08-29 14:51   Build-Task1.xml
```
Dado que `.sqx` y `.cfx` son producidos por el mismo runtime Java (probablemente con
`java.util.zip`/`java.util.jar`), la afirmación de `viabilidad_puente_sqx.md` L48-56 (que
`.sqx` es ZIP/JAR con `strategy_Portfolio.xml` + `settings.xml`/`lastSettings.xml` +
`Results/.../dailyEquity.bin`/`orders.bin` + `META-INF/MANIFEST.MF`) es **estructuralmente
consistente y plausible**, pero la marco **NO VERIFICADA DIRECTAMENTE POR MÍ** (no re-ejecuté el
script `inventario_sqx.py` del repo ni abrí un `.sqx` real; el propio informe cita 2035/2035
ficheros procesados con 0 errores por un script Python estándar (`zipfile`+XML), lo que es
metodológicamente sólido y no requiere licencia SQX para ejecutarse — sería trivial de
re-verificar si hiciera falta, pero no aporta nada nuevo hacerlo de nuevo aquí).

**¿Existe export XML/JSON más robusto que parsear `.sqx` directamente?** Confirmado por §2: sí,
`sqcli.exe -tools action=orderstocsv|orderstoxlsx file="Strategy X.sqx"` exporta la lista de
operaciones a CSV/XLSX (no el árbol de reglas). Para el árbol de reglas en sí, `sqcli.exe
-databank action=export file=....csv|.xlsx` exporta las **columnas de resultados** del databank
(igual que `data/sqx_exports/toimprove_2026-08-31.csv`, confirmado con 2036 líneas = 2035 filas
+ cabecera, columnas `IS`/`OOS` para Fitness/NetProfit/Trades/ProfitFactor/Sharpe/etc. — verifiqué
la cabecera y las 2 primeras filas directamente, coincide con lo descrito en
`viabilidad_puente_sqx.md` L42: `# of trades (OOS)` = "2" en ambas primeras filas, CONFIRMANDO
en los datos reales el hallazgo de "OOS decorativo"). **Ninguno de estos exports (CSV/XLSX)
contiene el árbol de reglas** — solo métricas. El árbol de reglas solo vive dentro del `.sqx`
mismo (`strategy_Portfolio.xml`, según el informe del repo) — no encontré en la documentación
oficial ni en `sqcli -h` ningún comando de export a un AST/JSON más manejable que el propio XML
interno del `.sqx`. **Camino de menor riesgo hacia un AST canónico** (evaluando la evidencia
reunida, no solo repitiendo la recomendación del repo): dado que (a) el `.sqx` es un ZIP/XML
inspeccionable con librería estándar sin necesitar licencia SQX, (b) el propio SQX puede generar
snippets Java con acceso total a la estructura de reglas vía `CodeEditor` (Mecanismo B de §3), y
(c) el propio informe interno mide que 0/2035 estrategias del lote actual son traducibles sin
escribir un intérprete genérico de árboles booleanos —la recomendación de `viabilidad_puente_
sqx.md` §6 (no abrir el carril de traducción genérica todavía; en su lugar, restringir el
vocabulario de generación de SQX a las primitivas que el motor propio YA entiende, usando
`generar_sqx_fondeo.py`) es **coherente con toda la evidencia reunida en este informe** sobre
capacidades de SQX: el Mecanismo A/B de §3 permite justamente eso — condicionar el Builder para
que solo emita EMA/RSI/Donchian (via `Building blocks` con pesos/exclusión, visto en el manual
p.16 "Use" checkbox por bloque) en vez de las 14 familias de indicador del lote viejo. No es una
verificación nueva de SQX, es una lectura consistente: **la recomendación del repo es sensata
dado lo que SQX permite configurar**, no una alternativa "obligatoria" — Emilio puede decidir en
sentido contrario con conocimiento de causa.

---

## 9. Modo de trabajo en este PC (GUI vs headless, memoria)

**Memoria**: `StrategyQuantX.config`, `sqcli.config` y `CodeEditor.config` (los tres, idénticos)
fijan `-Xms4g` (mínimo) y `StrategyQuantX.config` además fija `-Xmx11g` (máximo 11 GB) — el
`.config` de `sqcli.exe` **no tiene un `-Xmx` explícito** (se queda con el valor por defecto de
la JVM salvo que se pase `_JAVA_OPTIONS` al arrancar, igual patrón al VPS que usa
`_JAVA_OPTIONS=-Xmx8g` vía systemd según `sqx_reconfiguracion_fondeo.md` L34). Esto es
coherente con lo que pedía el VPS (8-10 GB de Java) — misma familia de requisitos de memoria en
esta máquina. **NO VERIFICADO** cuánta RAM tiene físicamente este PC (fuera del alcance,
irrelevante para el informe SQX en sí).

**GUI vs headless**: confirmado con evidencia directa que `sqcli.exe` (headless, sin ventana)
funciona de forma completamente autónoma en este PC — arranca su propio servidor HTTP interno
(puerto 5052), verifica licencia, carga datos y proyectos, ejecuta el comando pedido y sale
limpiamente (`Adiós` / `Exit app - cmd -exit` / `[exited with code 0]`, visto en ambas
invocaciones de este turno). **No se probó la GUI** (`StrategyQuantX.exe`) en este turno por
estar fuera del alcance del mandato ("no lances ningún Build ni proceso pesado"; abrir la GUI
completa habría sido el mismo coste que `sqcli` más una superficie interactiva innecesaria para
esta tarea de inventario). El flag `-gui` de `sqcli.exe` ("Starts webserver to access GUI
remotely", §2) sugiere que incluso la exploración visual puede hacerse sin la app Electron
nativa, vía navegador — coherente con el patrón Xvfb+puerto 5050 documentado para el VPS en
`17B_SUPERFICIE_UI_SQX.md`.

**Recomendación de modo de trabajo** (lectura de la evidencia, no una prueba nueva): dado que (a)
cada llamada CLI paga un coste fijo de 1-2 minutos de arranque completo independientemente de lo
trivial del comando, y (b) `sqcli.exe -run file=comandos.txt` permite encadenar múltiples
acciones en una sola invocación (evitando pagar el coste de arranque N veces), **conviene
agrupar cualquier lote de comandos CLI en un único fichero `-run`** en vez de invocar `sqcli.exe`
repetidamente. Para iterar interactivamente sobre el diseño de un `Build-Task` (Building
blocks, condiciones, Rankings), la GUI (`StrategyQuantX.exe` o `sqcli -gui` + navegador) es más
rápida que editar XML a mano y relanzar; para lotes nocturnos de generación real, headless
(`sqcli -project action=start` o `-run`) es el patrón correcto, igual al de
`improve_cycle.sh` en el VPS. Esta es una recomendación razonada, no una comprobación empírica
de tiempos en GUI (no abierta en este turno).

---

## Tabla resumen — afirmaciones previas tocadas

| # | Afirmación (fuente) | Veredicto | Evidencia |
|---|---|---|---|
| 1 | `Ultra_Matrix`/`Ultra_Auto_Pilot` corren en este PC | REFUTADA | `user/projects/` local no los contiene; vivían en VPS (`17A/17B/17C`) |
| 2 | VPS trial "activa hasta 18.08.2026" (`17B` L5) | NO VERIFICABLE hoy (VPS inalcanzable); consistente con esta instalación siendo Trial Pro también, caduca 05.09.2026 | `sqcli -license action=info` local |
| 3 | `MaxTradesPerDay=1` en Build-Task1 (`CONFIG_DOORS.md` L25) | **REFUTADA** | `Build-Task1.xml` L13, 3 backups: valor = 0 |
| 4 | `RandomizeHistoryData` 10/10/10/10 activo causando "sin transacciones" | PARCIAL / matizada | `use=true`→`true`→`false` entre 09:05-14:57; otros randomizers sí siguen activos |
| 5 | Databanks renombrados a medias, "Last generation" con espacio vs "LastGeneration" sin espacio, Improve mira el nombre sin espacio | **CONFIRMADA** | `config.xml`+`Build-Task1.xml`+`Improve-Task1.xml`, ambos nombres coexisten, Improve Input=`LastGeneration` |
| 6 | Resto de parámetros genéticos/WF/Improve de `CONFIG_DOORS.md` | **CONFIRMADA** (~20 parámetros, uno por uno) | `Build-Task1.xml`/`Improve-Task1.xml` líneas citadas en §5 |
| 7 | `.sqx` es ZIP con `strategy_Portfolio.xml` etc (`viabilidad_puente_sqx.md`) | CORROBORADA POR ANALOGÍA (no verificado sobre un `.sqx` real, sí sobre `.cfx` del mismo motor) | `unzip -l` sobre `.cfx` |
| 8 | Motor propio solo reconoce 8 arquetipos EMA/RSI hardcodeados (`viabilidad_puente_sqx.md`) | **CONFIRMADA** (código propio, verificado directamente) | `event_backtest_engine.py` L1698-1706 |
| 9 | QuantAnalyzer es "módulo" de SQX (`GUIA_EXPERTO_USAR_SQUANT.md` L37) | **REFUTADA** | Es producto separado, tier Ultimate; no instalado aquí |
| 10 | 2035 estrategias del lote `toimprove_2026-08-31.csv`, símbolo único AUDUSD_H1, OOS decorativo | **CONFIRMADA parcialmente** (conteo de filas y primeras filas verificado directamente; no se re-verificó el símbolo único sobre las 2035 filas completas) | `wc -l` = 2036 líneas; cabecera + 2 primeras filas leídas |

---

## Preguntas NO resueltas (causa explícita)

- **Volume Profile funcional en esta licencia Trial Pro**: NO VERIFICADO — requiere abrir la GUI.
- **Símbolos/TF ya importados en `data_futures.h2.db`/`data_stock.h2.db` de esta instalación**:
  NO VERIFICADO — requeriría un tercer lanzamiento de `sqcli` (`-symbol action=list`), evitado
  por presupuesto de máquina; coste estimado ~1-2 min, ver experimento propuesto.
  **NO VERIFICADO** también un pequeño detalle numérico: `EvoStagnationRestartGenerations=10`
  visto en `Build-Task1.xml` L93 es un parámetro *distinto* de `EvoRestartOnStagnation
  generations="30"` (L84, el que sí está citado en `CONFIG_DOORS.md`); no se investigó a qué
  afecta el primero al estar el segundo en `status="false"` — probablemente residual/no usado,
  pero no confirmado.
- **Precio y condiciones exactas de QuantAnalyzer Pro standalone**: NO VERIFICADO contra la
  página oficial de precios (`strategyquant.com/quantanalyzer/pricing`) — no se hizo fetch
  directo de esa URL en este turno.
- **Contenido real de un `.sqx` generado por esta instalación**: NO VERIFICABLE — no hay ningún
  `.sqx` en los databanks vacíos de este PC; el análisis de formato se apoya en el lote descrito
  por `viabilidad_puente_sqx.md` (VPS, hoy inalcanzable) y en la analogía con `.cfx`.
  RandomizeSpread y RandomizeStrategyParameters `use=` exacto en los 3 backups: grepeado
  parcialmente, no se confirmó explícitamente byte a byte para los tres — riesgo bajo dado que
  el patrón visto es consistente, pero declarado aquí por rigor.

---

## CONFIG CANDIDATA FONDEO

Parámetros concretos propuestos para un `Build-Task` FONDEO nuevo (no toca `Ultra_Matrix` ni
ningún proyecto existente), cada uno justificado contra la evidencia de este informe:

| Parámetro | Valor propuesto | Justificación |
|---|---|---|
| `Session` / `LimitTimeRange` | `LondonNY`, `true`, From=25200 (07:00 UTC) To=75600 (21:00 UTC) | Mecanismo nativo confirmado (§4); concentra la operativa en sesión de mayor liquidez, coherente con proxies CME/FX |
| `ExitAtEndOfDay` | `true`, hora antes del cierre de sesión de liquidación del proxy | Cierre intradía obligatorio exigido por doctrina FONDEO; tag nativo confirmado (§4) |
| `ExitOnFriday` | `true` | Ya usado así en `Ultra_Matrix` (confirmado §5); evita gap de fin de semana en CFD/futuro |
| `MaxTradesPerDay` (global) | Dejar en `0` (sin límite) o fijar explícitamente el valor deseado — **NO usar un valor bajo (1-2) combinado con `MinTradesInRun>20` en WF**: la combinación aritmética exige que cada uno de los folds de WF tenga >20 trades, lo que con `MaxTradesPerDay` bajo puede requerir folds larguísimos o volumen de señal muy alto | Evita repetir el patrón de fusible descrito en §5 (aunque la cifra concreta "1" no se confirmó en los `.cfx`, el riesgo aritmético del choque MaxTradesPerDay×MinTradesInRun es real y merece guardarraíl explícito) |
| `NumberOfTrades` (Ranking, OOS) | Condición dura `>= 200` usando `Column-Value NumberOfTrades sampleType=<OOS>` | Mecanismo A confirmado (§3); aplica el criterio 1.1 directamente en el Builder |
| `ProfitFactor` (Ranking, OOS) | Condición dura `>= 1.25` | Idem |
| Ratio OOS/IS | Condición `Right-Side valueType="column" pctRatio="50"` sobre `ProfitFactor`/`NetProfit`, patrón ya visto en `RetestWithHigherPrecision` (§3, L1302-1307 de `Ultra_Matrix`) | El propio SQX ya usa este patrón para "métrica cross-check ≥ X% de main" — reutilizable tal cual para "OOS ≥ 50% de IS" |
| `WalkForwardOptimization` | `use=true`, mismo esquema `thresholdPct` que `Ultra_Matrix` (confirmado funcional, §5), pero revisar `period`/`optimization` contra el rango de fechas real del proxy elegido para que cada fold tenga suficientes barras | Reutiliza una configuración ya verificada como sintácticamente válida en Build 144 |
| `Ranking type` | Columna custom Java `FondeoCertificacion11` (Mecanismo B, §3) que combine los 4 criterios sellados en un único booleano/score | Pre-alinea la salida del Builder con el criterio 1.1 completo, no solo con condiciones individuales |
| `Commissions`/`Chart spread` | Cargar vía `-instrument action=add` con `commissions`, `defaultspread`, `ticksize` reales de MES/MNQ/MYM/MGC/MSI/MCL | Comando CLI confirmado (§2); evita el error histórico de spread=0 documentado en `12_analisis_reconfiguracion_xml.md` §2.5 |
| Building blocks (Signals) | Restringir a EMA/RSI/Donchian (deshabilitar el resto vía checkbox `Use`, visto en manual oficial §3) si el objetivo es alimentar el motor propio sin escribir un intérprete genérico | Consistente con la recomendación medida en `viabilidad_puente_sqx.md` (§8 de este informe) |

### Experimento A/B propuesto para validar esta config (NO ejecutado aquí)

1. Crear un proyecto nuevo `Fondeo_Test_A` (config candidata de arriba) y `Fondeo_Test_B`
   (config actual de `Ultra_Matrix` tal cual, como control), ambos apuntando al mismo proxy y
   mismo rango de fechas.
2. Lanzar ambos con `StopCondition databank-full passedStrategies=50` (lote pequeño de control,
   no 200) vía `sqcli -project action=start` o `-run`.
3. Comparar tasa de aceptación (candidatos que llegan a `Results` / candidatos generados) y, de
   los que llegan, cuántos cumplen el criterio 1.1 evaluado independientemente (fuera de SQX,
   con el motor propio) — para descartar que el filtro custom Java tenga un bug de fidelidad.
4. **Coste estimado**: cada arranque de `sqcli` en esta máquina tarda 1-2 min solo en cargar; un
   lote de 50 estrategias con WF+MC+SPP activos, por analogía con los ritmos vistos en
   `ESTADO.md` (81.210 estrategias/hora sin cross-checks pesados en el VPS, mucho más lento con
   todos los cross-checks activos), es razonable estimar **10-40 minutos de cómputo real** por
   proyecto, más el tiempo de arranque. Total estimado para el experimento completo A+B:
   **30-90 minutos de máquina**, a autorizar por el orquestador antes de ejecutar.
