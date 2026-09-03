# INFORME DE DESPLIEGUE: SEGUNDA INSTALACIÓN STRATEGYQUANT X HEADLESS (HETZNER)

> **Tarea:** A16 · **Agente:** AGY · **Fecha de ejecución:** 2026-09-03 06:55 UTC  
> **Servidor:** Hetzner Dedicated (`88.99.210.167`, alias SSH `sqx-hetzner`)  
> **Objetivo:** Instalar segunda copia aislada de SQX en `/opt/SQX-headless` y levantar `sqcli` en modo REST/CLI para desbloquear la automatización de M1.

---

## 1. Verificación de Espacio y Copia Limpia

1. **Espacio disponible:**
   - Carpeta origen `/opt/StrategyQuantX`: 1.6 GB.
   - Espacio libre en `/`: 188 GB disponibles (solo 7% usado).
2. **Copia a `/opt/SQX-headless`:**
   - Realizada con `cp -a /opt/StrategyQuantX /opt/SQX-headless`.
   - Ajustadas las rutas en `/opt/SQX-headless/user/settings/settings.xml` para que apunten a `/opt/SQX-headless` y no bloqueen la instancia GUI.

---

## 2. Arranque Desacoplado de `sqcli`

- **Comando ejecutado:**
  `cd /opt/SQX-headless && setsid nohup ./sqcli > /opt/SQX-headless/sqcli.log 2>&1 < /dev/null &`
- **Puerto auto-asignado por SQX:** **5051** (al detectar que el 5050 está en uso por la GUI principal, seleccionó automáticamente el puerto 5051).
- **Proceso activo:** PID `38953` (`./sqcli`), ejecutándose con 7 hilos de procesamiento y asignación de memoria `-Xms4g`.

---

## 3. Salidas Crudas de Aceptación

```bash
# 1. Directorio y tamaño
$ ssh sqx-hetzner 'ls -d /opt/SQX-headless && du -sh /opt/SQX-headless'
/opt/SQX-headless
2.1G	/opt/SQX-headless

# 2. Proceso en ejecución
$ ssh sqx-hetzner 'ps -eo pid,etime,cmd | grep "[s]qcli" | cut -c1-120'
  38951    04:24:52 bash -c cd /opt/SQX-headless && setsid nohup ./sqcli > /opt/SQX-headless/sqcli.log 2>&1 < /dev/null 
  38953    04:24:52 ./sqcli

# 3. Log de arranque y puerto
$ ssh sqx-hetzner 'tail -25 /opt/SQX-headless/sqcli.log'
Server started on port 5051
SQX version: 144.2953
Hardware ID: CFF7145CD38B
Verifying license ...
Customizations loaded successfully, count=1
High priority: OFF
Using: 7 cores, core usage configuration: '-1'
Preparing thread executors: 7

# 4. Verificación de respuesta en vivo al comando de proyectos
$ ssh sqx-hetzner 'curl -s -m 5 "http://127.0.0.1:5051/call?cmd=-project%20action=list"'
08:53:30 Lista de proyectos disponibles
--------------------------------------------------
PortfolioMaster
PortfolioComposer
GOLD BREAKOUT M30 - Dukascopy
Optimizer
Builder
GBPJPY BREAKOUT H4 - Dukascopy
NQ BREAKOUT FUTURES  H1 - Tradestation
EW FUTURES BREAKOUT H1 - Tradestation
DJ CFD - Dukascopy
GOLD H1 CFD - Dukascopy
Ultra_Matrix
Ultra_Auto_Pilot
Ultra_Matrix(2)
NQ CFD H1 - Dukascopy
GBPJPY BREAKOUT H1 - Dukascopy
NQ CFD H1 D1 MULTI-TIMEFRAME  - Dukascopy
GBPUSD H1 - Dukascopy
Retester
backups
```

---

## 4. Conclusión

- ¿Arrancó el modo de comandos? **SÍ**.
- ¿En qué puerto? **5051** (socket REST local).
- ¿Responde a la lista de proyectos? **SÍ**, devuelve la lista de todos los proyectos de inmediato sin error `CLI not ready`.
- **M1 queda formalmente desbloqueado para automatización.**
