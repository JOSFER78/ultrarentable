# 01_ESTADO.md — Cartografía del ESTADO ACTUAL del subsistema de estrategias Ultra_Matrix
Fecha: 2026-08-29, 16:17–16:25 UTC. Método: informes previos (/tmp/um_doors/*, /tmp/um_meta/*, /tmp/um_mcprobe/*) + consulta API SOLO-LECTURA (5050) + crontab/systemd/disco. No se tocó motor ni project.cfx.

## Qué existe (inventario)

### 1. Motor / servicio
- `sqx.service` (systemd, enabled): `ExecStart=/home/ubuntu/StrategyQuantX144/sqcli`, `_JAVA_OPTIONS=-Xmx8g`, `Restart=always`, `MemoryHigh=8G / MemoryMax=10G`. Activo desde 13:15:10 UTC (PID 1217516), 3h+ de uptime, 7.7G RSS + 758M swap (cerca del high-watermark).
- API headless en 5050: `-project action=status` responde (SOLO-LECTURA verificado 16:17:20).

### 2. Proyecto Ultra_Matrix + tasks
- Proyecto corriendo (status 16:17): **107.914 estrategias generadas** (run 13:16→), 81.210/h, **Rechazado 100,00 %, Aceptado 0,00 %, En la base de datos 0**.
- `project.cfx` en `/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/` con 2 tasks:
  - **Build-Task1.xml** — genético (pop 100, 8 islas, 60 gens, fitness ReturnDDRatio, MaxTradesPerDay=1, SL 40–50 pips/ATR, PT 51–60). CrossChecks activos: WalkForwardOptimization (thresholdPct=80, MinTradesInRun>20), RetestWithHigherPrecision, MonteCarloRetest (20 sims, RandomizeHistoryData 10/10/10/10 tras fix de hoy), OptProfileSysParamPermutation. Inactivos: RetestOnAdditionalMarkets, WalkForwardMatrix, MonteCarloManipulation, WhatIf. StopCondition databank-full 200.
  - **Improve-Task1.xml** — AÑADIDO HOY (no existe en backup 09:05). Input LastGeneration → Output Results_robust_20260809; WF propio (NetProfit%>65, thresholdPct=65, RobComb 4×4 min10).

### 3. Databanks (API `-databank action=list`, 16:17:20) — EL HALLAZGO DE LOS DOS NOMBRES
| Banco | Records |
|---|---|
| **`Last generation`** (legacy, nombre con espacio) | **91 — las únicas estrategias reales** |
| LastGeneration (renombrado hoy) | 0 |
| InitialPopulation / Initial population | 0 / 0 |
| ToImprove / Strategies to improve / Strategies to optimize | 0 / 0 / 0 |
| Results / Results_robust_20260809 | 0 / 0 |
| Existing portfolio | 0 |

- **Disco: `user/projects/Ultra_Matrix/databanks/*` = 0 archivos en TODOS los bancos** — todo vive en memoria del motor. `data.db` (sqlite, ro) no contiene estrategias.
- El nombre con espacio NO es direccionable por cmd individual (`-databank action=count name=Last generation` → "Databank 'Last' doesn't exist"); solo se ve por `action=list`.

### 4. Scripts
- `/home/ubuntu/improve_cycle.sh`: ciclo por fases (parar→copy LastGeneration→ToImprove→startOnlyTask task=2→export→rearrancar), con candado state-file `~/.improve_cycle_state`. **Cuenta `LastGeneration` (=0 eterno)**.
- `/home/ubuntu/sqx_autostart.sh`: espera API y lanza `project action=start`. **Nunca ejecutado**: `/home/ubuntu/sqx_autostart.log` no existe.

### 5. Cron / triggers
- `crontab -l` (usuario): **CERO entradas sqx/improve_cycle**. Nada en /etc/cron*, ni timers systemd, ni unidades que referencien improve_cycle.sh o sqx_autostart.sh (grep verificado).
- Sin embargo `improve_cycle.log` registra 9 ticks hoy (12:19→16:05, todos "LastGeneration=0 < 30; espero") — el origen del disparo actual es desconocido/frágil (manual u otro mecanismo no encontrado).

### 6. Artefactos: /tmp (volátil) vs permanentes
- /tmp: `/tmp/um_doors/` (72M: config_doors.md, funnel.md, filtros_organicos.md, factory_reference.md, cfx_actual/cfx_backup, docs SQX), `/tmp/um_meta/meta_pipeline.md`, `/tmp/um_mcprobe/` (7.9M: fusible, clases, evidencia MC), `/tmp/um_restruct/` (solo 02_PLAN_PIPELINE.md; este 01_ESTADO.md se añade ahora).
- Permanentes `/home/ubuntu/ORDENAR/`: `um_doors_20260829/` (copia parcial de um_doors: config_doors, funnel, filtros, factory_reference, patcher.py, APLICAR.sh) + **7 backups project.cfx** (pre_window_20260829, pre_mcfix ×2, pre_spread_fix, pre_purga ×3) + `user/projects/backups/project_backup_20260817_061012.cfx`.

## Qué está ROTO (con evidencia citada)

### R1. Fusible MC: BadStrategyException(ReasonNoTrades=1) — mortalidad 100%
- `project.cfx` → `<AutomaticDismissal><Problem code="1" dismiss="true"/>` (fuse_evidence.txt): un backtest sin órdenes lanza BadStrategyException(1) y la estrategia se descarta. Traducción literal (Spanish.csv L1889): **"Filtro automático: sin transacciones"**.
- Log del día (funnel.md + verificación 16:20): **4.826+ dismissals MC / 650 estrategias distintas / 100 % de las que llegan a MC mueren**, motivo ÚNICO en todo el día. API 16:17: Aceptado 0,00 %, En la base de datos **0** tras 107.914 generadas. Disco databanks = 0 archivos.
- Causa raíz (filtros_organicos.md, contradicción #1): **MinTradesInRun>20 (WF) × optim period=20 × MaxTradesPerDay=1 × reglas de 1-3 condiciones** → candidatos con tan pocos trades que cualquier randomización MC (spread 1–5, slippage 0–5, StartingBar 100) vacía el backtest. El fix de hoy (RandomizeHistoryData 30→10) NO tocó la causa (0 líneas ProbabilityUp en el log).
- Además, 99,85 % muere ANTES de MC sin traza individual (solo agregados "Rechazado 100,00 %").

### R2. Config recargada en memoria — rename a medias
- config.xml renombró hoy los databanks ("Last generation"→"LastGeneration", etc.), pero el **runtime sigue escribiendo en el nombre legacy**: API 16:17 muestra `Last generation`=91 y `LastGeneration`=0; disco 0 archivos en todos. El rename solo surtirá efecto al recargar/reiniciar el proyecto (y entonces el banco legacy con 91 estrategias se perderá si no se captura antes).

### R3. Gatillo apuntando al banco equivocado — meta-ciclo muerto
- `improve_cycle.sh` cuenta `LastGeneration` (0 eterno) pero las estrategias caen en `Last generation` (91). Umbral 30 jamás se cruzará. Evidencia: improve_cycle.log, 9 ticks hoy, todos "LastGeneration=0 < threshold (30); espero". El meta-ciclo improve está bloqueado por R2+R3 en cadena.
- Además `count name=Last%20generation` ni siquiera es direccionable (espacio) — el script necesita parsear `action=list`.

### R4. Triggers no instalados
- improve_cycle.sh SIN línea en crontab (ticks de origen desconocido). sqx_autostart.sh nunca ejecutado (sin log) pese a que el servicio se reinició 13:15 — el arranque del proyecto de las 13:16 se hizo por otra vía.

### R5. Ciclo de mejora abierto (sin lazo de retorno)
- improve_cycle.sh termina en export CSV + re-arrancar Build; nada devuelve Results_robust_20260809 → InitialPopulation (meta_pipeline.md §1.3): "estrategias que buscan estrategias" no cierra el lazo.

## Qué es deuda / riesgo

- **D1 — Semillero volátil:** `Last generation` pasó 97→95→91 en vivo (reciclado del Build). 91 estrategias reales sin copia a banco estable ni export CSV; con el rename pendiente de R2, un restart del proyecto las borra. Capturar ANTES de cualquier reinicio.
- **D2 — Todo en memoria:** disco databanks = 0 archivos. Cualquier caída de sqx.service (Restart=always lo levanta, pero el proyecto rearranca vacío) pierde todo lo no exportado. Agravante: 7.7G RSS + swap, cerca de MemoryMax=10G → OOM plausible.
- **D3 — Embudo con caudal cero:** Improve es 100 % downstream del Build; mientras R1 no se arregle, ningún banco recibe validadas. Sin plan B de semillas (usar las 91 crudas), hambre garantizada.
- **D4 — /tmp no persiste:** 72M+7.9M de evidencia y diagnósticos en /tmp; solo copia parcial en ORDENAR. Riesgo de pérdida en reboot/limpieza (hay `vps_auto_clean.sh` en cron cada 6h).
- **D5 — Nombre con espacio no direccionable por API** (solo vía action=list) — fragilidad para cualquier automatización.
- **D6 — Incoherencias de puertas WF** Build (threshold 80) vs Improve (threshold 65, pero NetProfit%>65>60): filosofías opuestas en puertas consecutivas (filtros_organicos.md #3).
- **D7 — Supuestos sin verificar en vivo:** `databank action=copy`, índice de task en startOnlyTask task=2, comportamiento de databanks tras restart del proyecto.
- **D8 — Origen del disparo de improve_cycle desconocido:** algo lo ejecuta cada ~30 min sin estar en crontab visible; antes de reconfigurar cron hay que encontrar/parar el mecanismo actual para evitar doble disparo (el state-file mitiga, no garantiza).
