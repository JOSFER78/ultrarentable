# CONTRATO W1.7 — El backfill Dukascopy deja de degradar datasets versionados

> Emitido por el ORQUESTADOR LOCAL el 2026-09-01 (ciclo 2). Estado: **PENDIENTE DE DESPACHO**
> (cuando el semáforo de 2 agentes tenga hueco). Modelo: Sonnet 5. Aceptación re-ejecutada por
> el orquestador.

## 1. El defecto, medido (no supuesto)

`services/data_ingestion/run_dukascopy_backfill.py` (lanzado el 01-09 con
`--symbols USATECHIDXUSD,... --concurrency 3`) **re-descargó trimestres que ya existían con
manifiesto y los sobrescribió sin comparar**, aceptando `hours_failed > 0`. Medido por el
orquestador sobre 20 chunks (ES y NQ, 2023 Q1-Q2, 5 timeframes) comparando el manifiesto de
HEAD con el de disco:

| chunk | bar_count HEAD → disco | hours_failed HEAD → disco |
| :--- | :--- | :--- |
| usatechidxusd_5m_2023Q1 | 17.010 → 16.986 | 0 → 2 |
| usatechidxusd_1m_2023Q1 | 85.039 → 84.919 | 0 → 2 |
| usa500idxusd_5m_2023Q1 | 17.009 → 16.985 | 1 → 4 |
| usa500idxusd_1m_2023Q2 | 83.308 → 83.200 | 4 → 8 |
| (los 20: todos con menos barras y más horas fallidas) | | |

Los originales se rescataron del VPS (hash idéntico al de HEAD, 20/20) y los degradados están en
`data/quarantine/backfill_degradado_20260901/` (con sus manifiestos `.degradado`) como
**fixture real** para tus tests.

## 2. Territorio de escritura

- `services/data_ingestion/run_dukascopy_backfill.py` y los módulos de `services/data_ingestion/`
  que él llame para escribir chunk + manifiesto.
- `tests/test_dukascopy_backfill_idempotente.py` (nuevo).
- `orchestration/results/W17_backfill_informe.md` (tu informe).

Prohibido: descargar nada de Dukascopy durante la tarea (los tests usan fixtures locales o
mocks del descargador etiquetados como tales; regla #1 lo permite para infraestructura), tocar
`data/normalized/`, `scripts/mine.py`, el consolidador o el motor.

## 3. Comportamiento exigido

1. **Saltar lo que ya está bien**: si existe `<chunk>_manifest.json` y su `checksum_sha256`
   coincide con el sha256 del contenido de `<chunk>.json`, el chunk **no se descarga** (log
   `SKIP <chunk>: manifiesto válido`). Solo con `--force` se re-descarga.
2. **Nunca empeorar**: la descarga se escribe en un temporal (`<chunk>.json.tmp` + manifiesto
   temporal). Solo sustituye al existente si `hours_failed_nuevo <= hours_failed_viejo` **y**
   `bar_count_nuevo >= bar_count_viejo`; si no, el temporal se mueve a
   `data/quarantine/backfill_rechazado_<fecha>/` (nunca `rm`) y se registra
   `RECHAZADO <chunk>: peor que el existente (barras a→b, horas fallidas c→d)`.
3. **Reintentar antes de sellar**: una hora con descarga fallida se reintenta (≥3 intentos con
   espera creciente) antes de contarse en `hours_failed`. Un chunk con `hours_failed > 0` se
   escribe igualmente (es dato real incompleto, no inventado) pero su manifiesto lo declara y el
   log lo resume al final por símbolo/timeframe.
4. **Manifiesto = hash de CONTENIDO** del fichero final (sha256 de los bytes), nunca de
   metadatos (W1.6). Si el escritor actual usa el sello de metadatos, corrígelo aquí solo para
   el backfill Dukascopy y dilo en el informe.
5. **Resumen final** (`dukascopy_backfill_progress.json` o equivalente que ya exista): por
   símbolo/tf, chunks `saltados`, `escritos`, `rechazados`, `con_horas_fallidas`.

## 4. Aceptación (el orquestador la re-ejecuta)

1. `./.venv/Scripts/python.exe -m pytest -q tests/test_dukascopy_backfill_idempotente.py` verde,
   con al menos: (a) chunk existente con manifiesto válido ⇒ el descargador **no se llama**;
   (b) descarga nueva peor que la existente (usa como fixture un par manifiesto/`.degradado` de
   `data/quarantine/backfill_degradado_20260901/`) ⇒ el fichero en disco **no cambia** (mismo
   sha256 antes/después) y el temporal acaba en cuarentena; (c) descarga igual o mejor ⇒ sustituye
   y el manifiesto lleva el sha256 del contenido; (d) `--force` re-descarga aunque el manifiesto
   sea válido; (e) manifiesto con checksum que NO coincide con el contenido ⇒ se trata como
   inexistente (se re-descarga) y se avisa.
2. Ejecución en seco real: `./.venv/Scripts/python.exe -m services.data_ingestion.run_dukascopy_backfill --start 2023-01-01 --end 2023-06-30 --symbols USATECHIDXUSD --dry-run`
   (añade `--dry-run` si no existe) lista los 10 chunks NQ 2023 Q1-Q2 como `SKIP` y no crea
   ni modifica ningún fichero en `data/normalized/` (`git status --short data/normalized` vacío;
   sha256 de los 10 chunks iguales antes/después).
3. `git status --short` sin cambios fuera del territorio de §2.

## 5. Después (lo asume el orquestador)

Con W1.7 cerrado se relanza el backfill **solo** para lo que el VPS no tiene (XAGUSD, LIGHTCMDUSD,
las 6 divisas) y se consolida 5m/15m (W1.2) símbolo a símbolo.
