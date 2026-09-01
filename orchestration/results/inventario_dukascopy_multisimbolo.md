# Inventario multi-símbolo Dukascopy — CARRIL C (proxies CME)

**Fecha:** 2026-09-01 ~09:30 UTC
**Autor:** subagente Carril C (inventario/consolidación/verificación, NO minería)
**Alcance:** ES/MES, NQ/MNQ, YM/MYM, GC/MGC, SI, CL/MCL, RTY (SSOT: `SYMBOLS` en
`services/data_ingestion/dukascopy_feed.py`, campo `proxy_for`).

Contexto de ejecución: backfill de Dukascopy vivo en segundo plano (PID 705270,
`run_dukascopy_backfill --start 2023-01-01 --end 2026-08-30 --concurrency 3`, arrancado
2026-09-01 01:02 UTC), I/O-bound, no tocado. VPS con load average ~15 en 4 cores por procesos de
otros agentes en paralelo; todas las operaciones de este informe se ejecutaron con
`nice -n 19 ionice -c 3`, en serie, ninguna >2s de CPU.

## 1. Inventario real en disco (leído de manifiestos, no asumido)

| Símbolo Dukascopy | Proxy CME | TF | Chunks | Barras (suma chunks) | Rango cubierto | ¿Consolidado? | Barras consolidado |
|---|---|---|---:|---:|---|---|---:|
| USA500IDXUSD | ES/MES | 1m | 17 | 1.234.207 | 2023-01-02 → 2026-08-30 | **Sí** | 1.230.396 |
| USA500IDXUSD | ES/MES | 5m | 16 | 250.507 | 2023-01-02 → 2026-08-30 | **Sí** | 250.009 |
| USA500IDXUSD | ES/MES | 15m | 16 | 83.543 | 2023-01-02 → 2026-08-30 | **Sí** | 83.377 |
| USA500IDXUSD | ES/MES | 1h | 16 | 21.583 | 2023-01-02 → 2026-08-30 | No (fuera de alcance de esta tarea) | — |
| USA500IDXUSD | ES/MES | 4h | 16 | 5.860 | 2023-01-02 → 2026-08-30 | No (fuera de alcance) | — |
| USATECHIDXUSD | NQ/MNQ | 1m | 7 | 596.747 | 2023-01-02 → **2024-09-30** | **No** | — |
| USATECHIDXUSD | NQ/MNQ | 5m | 7 | 119.453 | 2023-01-02 → **2024-09-30** | **No** | — |
| USATECHIDXUSD | NQ/MNQ | 15m | 7 | 39.859 | 2023-01-02 → **2024-09-30** | **No** | — |
| USA30IDXUSD | YM/MYM | todos | **0** | — | — | — | — |
| XAUUSD | GC/MGC | todos | **0** | — | — | — | — |
| XAGUSD | SI | todos | **0** | — | — | — | — |
| LIGHTCMDUSD | CL/MCL | todos | **0** | — | — | — | — |
| — | RTY | — | — | — | — | Sin proxy en Dukascopy (confirmado por error explícito de `mine.py`) | — |

Progreso del backfill (`data/dukascopy_backfill_progress.json`, trimestres completados):

- **USA500IDXUSD**: 15/15 trimestres (2023-Q1 → 2026-Q3) — **completo**, coincide con
  `--end 2026-08-30`.
- **USATECHIDXUSD**: 7/15 trimestres (2023-Q1 → 2024-Q3) — **~47%, EN CURSO**. Los ficheros de
  chunk se siguen escribiendo (`ds_dukascopy_usatechidxusd_5m_1719792000000_1727740500000.json`
  modificado a las 08:52 UTC, 35 min antes de este informe). Ritmo observado: ~1
  trimestre/28 min → ETA aproximada para completar USATECHIDXUSD ~13:15 UTC hoy (estimación
  gruesa, no comprometida).
- **USA30IDXUSD, XAUUSD, XAGUSD, LIGHTCMDUSD**: 0 trimestres — el backfill aún no ha llegado a
  ellos (procesa símbolos en el orden del diccionario `SYMBOLS`; van después de USATECHIDXUSD).

## 2. Consolidación (`scripts/herramientas/consolidar_dukascopy.py`, 5m y 15m)

**USA500IDXUSD ya estaba consolidado en 5m y 15m** (ficheros `..._consolidated.json` y su
manifiesto, `ingested_at_utc` 2026-09-01T08:30 UTC — obra de otro de los ocho agentes en
paralelo, no de este). Verificación por `--dry-run` (solo lectura, 16 chunks, ~1.5s CPU cada
uno) reproduce **exactamente** los mismos totales que el consolidado ya en disco:

| TF | Chunks | Barras crudas | Duplicados dedupe | Conflictos | Barras finales | Rango |
|---|---:|---:|---:|---:|---:|---|
| 5m | 16 | 250.507 | 498 | 0 | **250.009** | 2023-01-02T23:00 → 2026-08-30T23:55 UTC |
| 15m | 16 | 83.543 | 166 | 0 | **83.377** | 2023-01-02T23:00 → 2026-08-30T23:45 UTC |

Coincide dígito a dígito con `ds_dukascopy_usa500idxusd_{5m,15m}_consolidated_manifest.json`
(`bar_count` 250.009 y 83.377). **No se ejecutó el consolidador en modo escritura**: repetirlo
habría sido trabajo redundante (mismo resultado) y CPU evitable con la VPS a load average 15.

**USATECHIDXUSD: NO se consolidó**, por instrucción explícita de la tarea ante un símbolo a
medio descargar. Un consolidado parcial (solo hasta 2024-Q3) que después se confunda con
"completo" sería peor que no tenerlo — el propio nombre de fichero (`..._consolidated.json`)
no distingue "completo" de "lo que había en ese momento".

**USA30IDXUSD, XAUUSD, XAGUSD, LIGHTCMDUSD: sin chunks, nada que consolidar.**

## 3. Verificación real con `scripts/mine.py --dataset-source dukascopy --dry-run`

| Símbolo | TF | Resultado | Dataset físico resuelto |
|---|---|---|---|
| ES | 5m | OK | `ds_dukascopy_usa500idxusd_5m_consolidated.json` (41.066,9 KB, 20 configs generadas) |
| ES | 15m | OK | `ds_dukascopy_usa500idxusd_15m_consolidated.json` (13.723,9 KB, 20 configs) |
| MES | 5m | OK (alias de ES, mismo proxy) | `ds_dukascopy_usa500idxusd_5m_consolidated.json` |
| NQ | 5m | **OK pero engañoso** | `ds_dukascopy_usatechidxusd_5m_1719792000000_1727740500000.json` (2.944,9 KB) — **un solo chunk trimestral** (jul-oct 2024), NO los 7 disponibles, porque no hay consolidado y el resolver `dataset_source='dukascopy'` elige "el fichero más grande que matchee el patrón" |
| RTY | 5m | **ERROR limpio** (`sys.exit(1)`) | `DatasetSourceError`: "no existe proxy Dukascopy registrado ... Simbolos con proxy disponible: ['CL','ES','GC','MCL','MES','MGC','MNQ','MYM','NQ','SI','YM']" |

**Hallazgo operativo importante para el orquestador**: si hoy se lanzase minería FONDEO sobre NQ
con `--dataset-source dukascopy`, `mine.py` **no falla** — resuelve silenciosamente un único
chunk de ~85.500 barras de 5m (3 meses) en vez de las 119.453 que ya hay en disco repartidas en
7 chunks, y muchas menos que las que habrá al completar el backfill. Es exactamente el fallo que
el docstring de `consolidar_dukascopy.py` describe para USA500IDXUSD antes de consolidar
("5.835 barras de 83.543 disponibles"). **NQ no debe minarse hasta que exista su consolidado**,
y el consolidado no debe generarse hasta que el backfill llegue a 15/15 trimestres.

## 4. Barras OOS y frecuencia de trade necesaria (reparto 60/20/20)

Partición canónica (`services/data/holdout_partitioner.py::HoldoutPartitioner`, ratios reales en
código): **IS 60% / WFO 20% / Blind-Holdout 20%**. El criterio 1.1 sellado exige persistencia
"por mitades OOS" — es decir, cada mitad (WFO y Blind, 20% cada una) debe sostener el resultado
por separado. Se muestran ambas lecturas: OOS combinado (WFO+Blind, 40%) y la exigencia más dura,
que cada mitad por sí sola alcance las 200 operaciones.

| Símbolo (proxy) | TF | Barras totales | WFO (20%) | Blind (20%) | OOS total (40%) | Barras/trade — 200 sobre OOS total | Barras/trade — 200 **por cada mitad** | Usable hoy |
|---|---|---:|---:|---:|---:|---:|---:|---|
| USA500IDXUSD (ES/MES) | 1m | 1.230.396 | 246.079 | 246.080 | 492.159 | 2.460,80 | 1.230,39 | **Sí** |
| USA500IDXUSD (ES/MES) | 5m | 250.009 | 50.001 | 50.003 | 100.004 | 500,02 | 250,00 | **Sí** |
| USA500IDXUSD (ES/MES) | 15m | 83.377 | 16.675 | 16.676 | 33.351 | 166,75 | 83,38 | **Sí** |
| USATECHIDXUSD (NQ/MNQ) | 1m | 596.747* | 119.349 | 119.350 | 238.699 | 1.193,49 | 596,75 | No (parcial, sin consolidar) |
| USATECHIDXUSD (NQ/MNQ) | 5m | 119.453* | 23.890 | 23.892 | 47.782 | 238,91 | 119,45 | No (parcial, sin consolidar) |
| USATECHIDXUSD (NQ/MNQ) | 15m | 39.859* | 7.971 | 7.973 | 15.944 | 79,72 | 39,85 | No (parcial, sin consolidar) |
| USA30IDXUSD (YM/MYM) | — | 0 | — | — | — | — | — | No (sin datos) |
| XAUUSD (GC/MGC) | — | 0 | — | — | — | — | — | No (sin datos) |
| XAGUSD (SI) | — | 0 | — | — | — | — | — | No (sin datos) |
| LIGHTCMDUSD (CL/MCL) | — | 0 | — | — | — | — | — | No (sin datos) |
| RTY | — | — | — | — | — | — | — | No (sin proxy en Dukascopy) |

\* USATECHIDXUSD: suma de chunks crudos sin deduplicar (aún faltan 8/15 trimestres); cifra
orientativa, **no** el resultado de un consolidado real.

Lectura en tiempo real (independiente del TF elegido, porque la ventana OOS es la misma en
calendario): con el rango actual de USA500IDXUSD (2023-01-02 → 2026-08-30, ~3,66 años), cada
mitad OOS cubre ~267 días de trading. Alcanzar 200 operaciones por mitad exige un promedio de
**≈1 operación cada 20,8 horas** (≈0,75 trades/día) — una cadencia intradía moderada, alcanzable
en 5m o 15m sin forzar sobre-trading.

## 5. Ranking de viabilidad para la próxima campaña

1. **USA500IDXUSD (ES/MES), 15m** — dataset consolidado, verificado con `mine.py --dry-run`,
   83.377 barras, exigencia más laxa en barras/trade (83,4 por mitad OOS). **Listo para minar.**
2. **USA500IDXUSD (ES/MES), 5m** — igual de listo, más granularidad (250.009 barras, 250
   barras/trade por mitad). **Listo para minar.**
3. **USA500IDXUSD (ES/MES), 1m** — consolidado y con manifiesto correcto, pero no verificado con
   `mine.py --dry-run` en esta tarea (fuera de alcance explícito, solo 5m/15m). Volumen de datos
   más alto (1,23M barras) a coste de más CPU por backtest.
4. **USATECHIDXUSD (NQ/MNQ)** — **no viable todavía**. Backfill al 47%, sin consolidar. Sembrar
   una campaña hoy correría sobre un solo chunk trimestral por el motivo descrito en §3. Acción:
   esperar a que `data/dukascopy_backfill_progress.json` marque 15/15 trimestres para
   USATECHIDXUSD, y **entonces** ejecutar el consolidador en 5m/15m antes de minar.
5. **USA30IDXUSD (YM), XAUUSD (GC), XAGUSD (SI), LIGHTCMDUSD (CL)** — **sin datos en absoluto**.
   El backfill secuencial (orden del diccionario `SYMBOLS`) tardará varias horas más en
   alcanzarlos tras terminar USATECHIDXUSD. No hay nada que consolidar ni verificar hoy.
6. **RTY** — sin proxy en el catálogo de Dukascopy (confirmado por error explícito de
   `mine.py`, no una suposición). Alternativas ya documentadas en el propio mensaje de error:
   Yahoo (`data_source='auto'`, ~13.700 barras/1h) o excluir RTY de la campaña.

## 6. Conclusión operativa

Hoy solo **ES/MES sobre USA500IDXUSD (5m y 15m)** tiene datos completos, consolidados y
verificados end-to-end (inventario → consolidación confirmada por dry-run → `mine.py` resuelve
el fichero correcto). Es la única combinación symbol+TF de este carril lista para que el
orquestador decida lanzar una campaña de minería FONDEO. Todo lo demás (NQ, YM, GC, SI, CL)
depende del avance del backfill en curso; **NQ no debe minarse aún** aunque `mine.py` no lo
impida (ver hallazgo §3), y consolidarlo antes de que termine el backfill sería fabricar un
"completo" falso.
