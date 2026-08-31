---
id: F03
titulo: "Campaña de descubrimiento masiva"
estado: PARCIAL
depende_de: ["F01", "F02"]
desbloquea: ["F04", "F07"]
verificacion_global: "Se mide por volumen de candidatos que superan el criterio 1.1, no por lo bonitas que sean las curvas."
actualizado: "2026-08-31"
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

Mejora operativa de la cola: `heartbeat` del worker (un watchdog externo con umbral 300 s
marcaba RETRYING trabajos vivos → riesgo de minería duplicada; incidente 14:08 documentado en
`services/queue/durable_job_queue.py::heartbeat`) + guardia anti-duplicados + subcomando
`cancelar` con motivo.

Barrer las celdas con dos perfiles de fitness distintos:

- **ULTRA:** asimetría. Payoff alto, cola derecha, tolerancia a DD. No se busca winrate.
- **FONDEO:** consistencia. DD bajo, sin rachas, cierre intradía.

**Nada se declara certificado aquí.** Esta fase produce materia prima, y se mide por volumen de
candidatos que superan el criterio 1.1, no por lo bonitas que sean las curvas.
