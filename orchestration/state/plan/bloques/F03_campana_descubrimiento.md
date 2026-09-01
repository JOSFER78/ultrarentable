---
id: F03
titulo: "Campaña de descubrimiento masiva"
estado: EN_CURSO
depende_de: ["F01", "F02"]
desbloquea: ["F04", "F07"]
verificacion_global: "Se mide por volumen de candidatos que superan el criterio 1.1, no por lo bonitas que sean las curvas."
actualizado: "2026-09-01"
---

# FASE 3 — CAMPAÑA DE DESCUBRIMIENTO MASIVA

## 3.1 Datos (corre en segundo plano desde ya, no bloquea)

**Estado:** EN_CURSO — censo real ejecutado 2026-08-31 (read-only, conteo en disco).

- Backfill Dukascopy de los proxies verificados: `USA500IDXUSD`, `USATECHIDXUSD`, `USA30IDXUSD`,
  `XAUUSD`, `XAGUSD`, `LIGHTCMDUSD` + majors forex. **`USARUSSIDXUSD` (RTY) está SIN VERIFICAR**:
  el feed devuelve el mismo tamaño para símbolos inválidos, así que no se da por bueno.
- Backfill M1 cripto (Binance Vision, ya en marcha).
- **Verificación:** conteo real de celdas con cobertura suficiente. No se declara "110 celdas"
  hasta que las 110 existan en disco con su manifiesto.

### CENSO REAL (2026-08-31)

**Celdas aptas para IS/OOS (cobertura ≥95 % y ≥90 días): 27 de las 110 objetivo — solo cripto
15m/1h/4h.** Declarar 110 hoy sería falso por un factor de 4. Detalle:

- Cripto Binance (9 símbolos): 1h/4h con 100 % de cobertura desde 2021/2023 → sólidas. 15m
  (~100 días) aptas. 5m (~35 días) y 1m (**7,3 días**) insuficientes: el "backfill M1 en marcha"
  no ha producido nada más allá de esa semana.
- **Dukascopy: el backfill NO ha empezado de verdad.** Solo `USA500IDXUSD` con 2 días de ticks
  (`data/raw/dukascopy/USA500IDXUSD/2026/08/{25,26}`). Los otros 6 proxies + forex Dukascopy:
  cero ficheros → 60 celdas del objetivo no existen.
- **Yahoo CME/Forex (13 símbolos): sellados `APPROVED` con 64–73 % de cobertura y miles de
  huecos** (ej. `ds_trad_cl_1h_*`: `gap_count=7472`, 64,4 %). Son exactamente los 52 datasets
  que consumió el minero FONDEO el 2026-08-30. **Minar FONDEO/futuros sobre esto viola
  REAL-ONLY: queda BLOQUEADO hasta tener backfill Dukascopy real.**
- Tabla `datasets` de la BD **no utilizable como fuente de verdad**: filas Dukascopy corruptas
  (todas `interval='1h'`, `record_count=0`, pero `coverage_pct=100` y `status='APPROVED'`) y
  doble contabilidad de alias cripto (`BTCUSDT` y `BTC-USDT`: 90 filas para 45 celdas). El
  conteo válido se hace en disco (`data/normalized/`, 118 datasets + 118 manifiestos).
- `USARUSSIDXUSD`: sin datos en disco ni en BD; la única exposición Russell es el proxy Yahoo
  `ds_trad_rty_*` (65–71 % cobertura), que no cierra la verificación.

**Consecuencia operativa:** la campaña F03.3 arranca SOLO sobre las celdas cripto aptas
(ULTRA); FONDEO y ULTRA-futuros esperan al backfill Dukascopy verificado. Tareas de datos
pendientes: (a) backfill Dukascopy masivo 7 proxies + forex, (b) reparar filas `datasets`
corruptas y desduplicar alias, (c) backfill M1/5m cripto profundo.

### ACTUALIZACIÓN DATOS (2026-08-31 ~18:00 UTC)

- **(c) RESUELTO — backfill profundo Binance COMPLETADO:** 18 datasets nuevos 15m/5m desde
  2021-01-01 (198.528 barras 15m / 595.584 5m por símbolo; SUI desde su listado 2023-05-03),
  **0 gaps, cobertura 100 %**, manifiestos SHA-256. Log: `data/binance_backfill_profundo.log`
  + `data/binance_backfill_profundo_summary.json`. Los datasets cortos superseded están en
  `cuarentena/datasets_superseded/` (36 ficheros, manifiesto).
- **(a) EN_CURSO real:** Dukascopy solo ha avanzado en `USA500IDXUSD` (~1.155 ficheros .bi5,
  descarga nohup activa); los otros 6 proxies + forex siguen a cero. Días de descarga por
  throttle. FONDEO sigue BLOQUEADO hasta tener celdas TRADFI verificadas.
- (b) sigue pendiente (reparar tabla `datasets` y desduplicar alias) — no bloquea la minería,
  que cuenta en disco.

## 3.2 Cola de minería gobernada para 4 cores

**Estado:** HECHO (herramienta lista 2026-08-31; el lanzamiento masivo espera a F02).

El VPS tiene 4 cores y sostiene además la API y la web. Cola persistente en SQLite, 2 celdas
concurrentes, `nice`/`ionice`, reanudable tras reinicio, progreso real visible.

Implementado en `scripts/cola_mineria.py` reutilizando la cola durable existente
(`services/queue/durable_job_queue.py`, tabla `durable_job_queue` de la BD canónica, watchdog):
- `encolar [--ver] [--solo-track]` — encola el universo de campaña (33 celdas 4h: 12 FONDEO
  prioridad 7 + 22 ULTRA prioridad 5, omitiendo las ya OK de `campana_02_amplia.jsonl`).
- `trabajar --concurrencia 2` — worker con subprocesos `nice -n 15 ionice -c 3` de `mine.py`,
  recuperación de huérfanos, telemetría a `orchestration/results/cola_mineria.jsonl`.
- `estado` — censo de la cola.
- Nuevo `JobType.MINE_CELL` en `contracts/queue_contracts.py` (aditivo).

Antecedente: la campaña 02 "amplio" (2026-08-31 06:57) tardó 882 s en una sola celda
(BTCUSDT 4h, 0 certificadas) y se abandonó; el barrido secuencial sin cola no escala.

## 3.3 La campaña

**Estado:** EN_CURSO (tramo cripto) — lanzada 2026-08-31 10:12 UTC con motor **5.11.0**.

Primera campaña del proyecto con sizing correcto (fracción canónica + point_value), latencia
next-bar-open y comisiones coherentes. 18 celdas ULTRA cripto (9 símbolos × 4h/1h, cobertura
100 %), perfil `amplio`, `--max-candidates 2000`, worker `cola_mineria.py trabajar
--concurrencia 2` con `nice`/`ionice`. Telemetría: `orchestration/results/cola_mineria.jsonl`
y worker log en `cola_mineria_worker.log`. Los resultados de `campana_02_amplia.jsonl` quedan
invalidados (motor 5.5.0-5.6.0 con el bug de riesgo ÷100).

FONDEO y ULTRA-futuros: esperan el backfill Dukascopy (en curso).

### RESULTADO del tramo cripto 4h/1h (2026-08-31 10:12–13:16)

**18/18 celdas minadas, ~36.000 configuraciones evaluadas, 0 certificadas 11/11.** Es la cifra
honesta con el motor 5.11.0. Near-misses relevantes (materia para F04, NO corpus base):
ETHUSDT 4h PF OOS 2,17 (39 trades) · SOLUSDT 4h 1,56 (36) · LINKUSDT 4h 1,46 (37) ·
SUIUSDT 4h 2,96 (15) · AVAXUSDT 1h 7/11 gates. Telemetría completa en
`orchestration/results/cola_mineria.jsonl` y por-config en `discovery_search_trials`.

**Diagnóstico del orquestador:** el fallo dominante NO es ausencia total de edge sino
**muestra OOS estructuralmente insuficiente**: con señales de EVENTO (cruce) a 4h/1h, el blind
OOS (20 % del histórico) produce 15-120 trades — el criterio 1.1 exige ≥200. A 15m/5m sí caben
≥200 trades OOS, pero el histórico actual es de ~100/35 días. **La ampliación correcta es de
DATOS, no de configuraciones** (el plan prohíbe relajar el criterio):

1. **Backfill profundo Binance 15m/5m desde 2021** — lanzado 2026-08-31 (agente en curso,
   log en `data/binance_backfill_profundo.log`). Al completarse: re-campaña sobre 15m/5m.
2. Backfill Dukascopy TRADFI — en curso (días de descarga por el throttle).
3. Los 4 `APPROVED@5.11.0` que aparecieron durante la campaña eran filas viejas del daemon
   actualizadas por `legacy_revalidation_service` (disparado por tests zero-mock que operan
   sobre la BD canónica — riesgo anotado para 0.4/0.6); barridas por el censo: 15-24 trades
   OOS y dos sobre datos Yahoo con huecos.

Nota operativa: `ultrarentable-discovery.service` fue parado externamente a las 10:05 UTC
(SIGTERM; sigue `enabled`). Con la cola gobernada activa, mantenerlo parado es coherente con
la unificación 0.4 pendiente.

### Campaña 15m (motor 5.13.0, datos profundos) — DETENIDA CON EVIDENCIA (2026-08-31 ~17:00)

Con los datasets profundos (198k barras) y la fricción completa (spread por par, funding,
latencia): BTCUSDT y ETHUSDT 15m → **embudo {'IS': 2000}** en ambas (2 h de CPU por celda,
ninguna config llega siquiera a validación). Conclusión estructural: **la familia de señales
EMA-cross/RSI/Donchian está agotada frente a la fricción honesta** — a 4h/1h por muestra
insuficiente, a 15m por dominancia del coste. Las 7 celdas restantes se cancelaron con motivo
registrado en la cola (evitar 7 h de CPU en un cero predecible). SQX corrobora: su último Build
rechazó 4.193/4.193 (banco `ToImprove` con 2.035 aparcadas, inventario en curso).

**Respuesta:** release **5.14.0 — 4 familias nuevas de arquetipos** (diseño sellado en
`orchestration/reviews/diseno_arquetipos_5_14.md`: reversion_atr, squeeze_breakout,
session_momentum, streak_edge; aditivas, como evento, sin constantes mágicas), en
implementación. Después: re-campaña perfil `arquetipos` sobre cripto 15m + 4h.

**Estado operativo (2026-08-31 ~18:00 UTC):**
- 5.14.0 EN IMPLEMENTACIÓN por subagente (motor + generadores + mine.py + snapshot); criterio
  de aceptación: identidad 5.13.0→5.14.0 en las 15 celdas de `verificacion_f02.py --comparar`.
  El motor en disco sigue pineado a 5.13.0 hasta que la release aterrice completa.
- Cola de minería: 20 COMPLETED / 7 CANCELLED (las 7 de 15m canceladas con motivo). Vacía y
  lista para encolar la re-campaña `arquetipos` al aterrizar 5.14.0.
- SQX: los 2.035 .sqx de ToImprove están materializados en disco
  (`~/StrategyQuantX144/user/projects/Ultra_Matrix/databanks/ToImprove/`) y el **export CSV de
  métricas está HECHO** (`data/sqx_exports/toimprove_2026-08-31.csv`: 2.035 filas, 44 columnas
  IS/OOS, separador `;`, verificado contra el count en RAM). Siguiente paso del carril SQX:
  cruzar CSV + .sqx (parser AST) y validar con el motor propio de 11 gates.

Mejora operativa de la cola: `heartbeat` del worker (un watchdog externo con umbral 300 s
marcaba RETRYING trabajos vivos → riesgo de minería duplicada; incidente 14:08 documentado en
`services/queue/durable_job_queue.py::heartbeat`) + guardia anti-duplicados + subcomando
`cancelar` con motivo.

Barrer las celdas con dos perfiles de fitness distintos:

- **ULTRA:** asimetría. Payoff alto, cola derecha, tolerancia a DD. No se busca winrate.
- **FONDEO:** consistencia. DD bajo, sin rachas, cierre intradía.

**Nada se declara certificado aquí.** Esta fase produce materia prima, y se mide por volumen de
candidatos que superan el criterio 1.1, no por lo bonitas que sean las curvas.

### CUELLO 6 (FONDEO, 2026-09-01): 2 arquetipos EVENTO para futuros intradía de índice

Diagnóstico: ningún arquetipo alcanzaba las ≥200 operaciones OOS del criterio 1.1 sobre
futuros intradía (`session_momentum`: 24-27 operaciones OOS best-case en la campaña FONDEO 1h)
— el techo es 1 señal/día/dirección sobre una sesión RTH estrecha (6,5 h). Con ES 5m ya hay
presupuesto de barras (250.507, OOS 50.101), así que la causa raíz era la frecuencia de la
señal, no los datos.

**Respuesta: motor 5.17.0 — `OPENING_RANGE_BREAKOUT` y `VWAP_REVERSION`** (diseño en
`orchestration/reviews/diseno_arquetipos_5_17_0.md`). Ambos anclados a `session_window`
(sesión RTH real del futuro), aditivos estrictos, solo FONDEO
(`_arquetipos_5_17_0_configs(is_ultra=True)` devuelve `[]`). DoF real contado
(`OPENING_RANGE_BREAKOUT`=4, `VWAP_REVERSION`=3, `risk_pct` incluido) y vecindario del gate 9
verificado NO-NOOP (24/24 combinaciones de rejilla × delta cambian de verdad). Verificado con
backtest real (no solo conteo de eventos) sobre 63 días de sesión ES 5m: 101 y 307 operaciones
respectivamente con una sola config de la rejilla — confirma que el mecanismo genera el
volumen proyectado. Regla #26: `scripts/verificacion_f02.py --comparar 5.16.0 5.17.0` — ver
resultado en `orchestration/results/verificacion_f02_diff_5.16.0_vs_5.17.0.md`.

**Pendiente (siguiente paso, NO ejecutado en esta sesión por carga de VPS):** encolar la
re-campaña perfil `arquetipos` sobre FONDEO ES/NQ/YM 5m y 15m (Dukascopy) vía
`scripts/cola_mineria.py` — 72 configs nuevas por símbolo/timeframe
(`_arquetipos_5_17_0_configs`). Solo entonces hay evidencia de VENTAJA (PF OOS), no solo de
volumen.

## Actualización 2026-09-01 10:20 — la campaña está lista pero hay una duda que la precede

**La infraestructura ya no bloquea.** Datos (250.009 barras 5m de ES), propagación de
`--dataset-source` de la cola a `mine.py`, deduplicación que permite re-encolar con otra fuente
(antes omitía 34 de 34 celdas en silencio), enrutamiento del discovery corregido y dos arquetipos
intradía nuevos. Lo único que impide lanzar es la VPS, pendiente de comandos con sudo.

**Pero antes de lanzar hay que responder una pregunta, porque puede invalidar el diseño de la
campaña.** La tesis vigente era que FONDEO está limitado por falta de barras. Los datos de la
campaña anterior no la sostienen: en GC y ES a 1h con perfil `arquetipos` —las dos únicas celdas de
futuros limpias, sin el bug de comisión del forex— **341 de 348 y 345 de 348 configuraciones mueren
ya en IS**, con 8.220-8.242 barras disponibles y un filtro trivialmente laxo (`trades < 5` o
`PF < 1,05`). Eso no es escasez de OOS: es que casi ninguna combinación de EMA-cross / RSI / ATR
llega a PF 1,05 en su propia muestra de entrenamiento.

Más barras arreglan el recuento de operaciones. No arreglan la ausencia de ventaja. Las dos
hipótesis son distinguibles —basta saber si mueren por `trades < 5` o por `PF < 1,05`— pero nadie
las ha distinguido porque **la telemetría del embudo se calcula y se tira**: `run_mining_pipeline()`
genera un registro por configuración descartada y lo devuelve en un `dict` que nadie serializa. De
14.352 configuraciones evaluadas sobreviven 20 puntos de datos en los logs.

**Orden de trabajo decidido**: persistir la telemetría ANTES de lanzar la campaña de 5m. Es coste
de CPU cero y evita que, si la campaña vuelve a dar cero, sea otra vez indiagnosticable.

Corrección al forense: la cifra "18 de 24 celdas válidas" está mal clasificada. El bug de comisión
del forex afecta a **las 12** celdas de divisas, no sólo a las 6 del perfil `arquetipos`, porque las
6 del perfil `amplio` corrieron en la misma ventana previa al arreglo.
