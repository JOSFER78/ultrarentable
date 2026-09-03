# INVENTARIO DE DATOS HISTÓRICOS EN DISCO: REJILLA M1 (5 ACTIVOS × 5 TIMEFRAMES)

> **Tarea:** A11 · **Agente:** AGY · **Fecha de auditoría:** 2026-09-03 03:00 UTC  
> **Ámbito:** `data/normalized/` y registros de ingesta del repositorio local PC  
> **Modo de ejecución:** Solo lectura. Cero descargas, cero modificaciones en `data/`.

---

## 1. Mapeo de Activos de Fondeo (CME) a Proxies Dukascopy

Determinado a partir de `services/data_ingestion/dukascopy_feed.py` (diccionario `SYMBOLS`) y referencias en `scripts/mine.py`:

| Activo Fondeo | Descripción CME | Símbolo Proxy Dukascopy | Naming en Ficheros (`data/normalized/`) | Divisor Precio | Rango Cordura |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ES** | E-mini S&P 500 | `USA500IDXUSD` | `ds_dukascopy_usa500idxusd_<tf>_...` | 1.000,0 | 1.000 - 30.000 |
| **NQ** | E-mini Nasdaq 100 | `USATECHIDXUSD` | `ds_dukascopy_usatechidxusd_<tf>_...` | 1.000,0 | 3.000 - 100.000 |
| **YM** | E-mini Dow Jones | `USA30IDXUSD` | `ds_dukascopy_usa30idxusd_<tf>_...` | 1.000,0 | 10.000 - 200.000 |
| **GC** | Gold Futures | `XAUUSD` | `ds_dukascopy_xauusd_<tf>_...` | 1.000,0 | 500 - 20.000 |
| **CL** | Light Sweet Crude Oil | `LIGHTCMDUSD` | `ds_dukascopy_lightcmdusd_<tf>_...` | 1.000,0 | 5 - 400 |

Los 5 marcos temporales canónicos intradiarios son: `1m` (60s), `5m` (300s), `15m` (900s), `1h` (3.600s) y `4h` (14.400s).  
Total celdas a auditar: 5 activos × 5 temporalidades = **25 celdas**.

---

## 2. Tabla Canónica de las 25 Celdas de la Rejilla M1

| # | Activo | TF | Proxy Dukascopy | Estado en Disco | Fichero Principal / Chunks | Tamaño | Nº Velas | Primera Vela (UTC) | Última Vela (UTC) | Manifiesto |
| :-: | :--- | :-: | :--- | :--- | :--- | -: | -: | :--- | :--- | :-: |
| 1 | **ES** | 1m | `USA500IDXUSD` | 2 chunks (incompleto) | `ds_dukascopy_usa500idxusd_1m_...` (2 trimestres) | 26,72 MB | 167.757 | 2023-01-02 23:00 | 2023-06-30 20:14 | SÍ (2) |
| 2 | **ES** | 5m | `USA500IDXUSD` | **CONSOLIDADO (COMPLETO)** | `ds_dukascopy_usa500idxusd_5m_consolidated.json` | 40,10 MB | 250.009 | 2023-01-02 23:00 | 2026-08-30 23:55 | SÍ |
| 3 | **ES** | 15m | `USA500IDXUSD` | **CONSOLIDADO (COMPLETO)** | `ds_dukascopy_usa500idxusd_15m_consolidated.json` | 13,40 MB | 83.377 | 2023-01-02 23:00 | 2026-08-30 23:45 | SÍ |
| 4 | **ES** | 1h | `USA500IDXUSD` | 2 chunks (incompleto) | `ds_dukascopy_usa500idxusd_1h_...` (2 trimestres) | 0,47 MB | 2.941 | 2023-01-02 23:00 | 2023-06-30 20:00 | SÍ (2) |
| 5 | **ES** | 4h | `USA500IDXUSD` | 2 chunks (incompleto) | `ds_dukascopy_usa500idxusd_4h_...` (2 trimestres) | 0,13 MB | 798 | 2023-01-02 20:00 | 2023-06-30 20:00 | SÍ (2) |
| 6 | **NQ** | 1m | `USATECHIDXUSD` | **15 CHUNKS (COMPLETO)** | `ds_dukascopy_usatechidxusd_1m_...` (15 trimestres) | 206,37 MB | 1.248.322 | 2023-01-02 23:00 | 2026-08-30 23:59 | SÍ (15) |
| 7 | **NQ** | 5m | `USATECHIDXUSD` | **CONSOLIDADO (COMPLETO)** | `ds_dukascopy_usatechidxusd_5m_consolidated.json` | 41,34 MB | 249.863 | 2023-01-02 23:00 | 2026-08-30 23:55 | SÍ |
| 8 | **NQ** | 15m | `USATECHIDXUSD` | **CONSOLIDADO (COMPLETO)** | `ds_dukascopy_usatechidxusd_15m_consolidated.json` | 13,79 MB | 83.374 | 2023-01-02 23:00 | 2026-08-30 23:45 | SÍ |
| 9 | **NQ** | 1h | `USATECHIDXUSD` | **15 CHUNKS (COMPLETO)** | `ds_dukascopy_usatechidxusd_1h_...` (15 trimestres) | 3,57 MB | 21.541 | 2023-01-02 23:00 | 2026-08-30 23:00 | SÍ (15) |
| 10 | **NQ** | 4h | `USATECHIDXUSD` | **15 CHUNKS (COMPLETO)** | `ds_dukascopy_usatechidxusd_4h_...` (15 trimestres) | 0,97 MB | 5.847 | 2023-01-02 20:00 | 2026-08-30 20:00 | SÍ (15) |
| 11 | **YM** | 1m | `USA30IDXUSD` | **15 CHUNKS (COMPLETO)** | `ds_dukascopy_usa30idxusd_1m_...` (15 trimestres) | 206,67 MB | 1.247.778 | 2023-01-02 23:00 | 2026-08-30 23:59 | SÍ (15) |
| 12 | **YM** | 5m | `USA30IDXUSD` | **CONSOLIDADO (COMPLETO)** | `ds_dukascopy_usa30idxusd_5m_consolidated.json` | 41,50 MB | 249.920 | 2023-01-02 23:00 | 2026-08-30 23:55 | SÍ |
| 13 | **YM** | 15m | `USA30IDXUSD` | **CONSOLIDADO (COMPLETO)** | `ds_dukascopy_usa30idxusd_15m_consolidated.json` | 13,84 MB | 83.325 | 2023-01-02 23:00 | 2026-08-30 23:45 | SÍ |
| 14 | **YM** | 1h | `USA30IDXUSD` | **15 CHUNKS (COMPLETO)** | `ds_dukascopy_usa30idxusd_1h_...` (15 trimestres) | 3,58 MB | 21.527 | 2023-01-02 23:00 | 2026-08-30 23:00 | SÍ (15) |
| 15 | **YM** | 4h | `USA30IDXUSD` | **15 CHUNKS (COMPLETO)** | `ds_dukascopy_usa30idxusd_4h_...` (15 trimestres) | 0,97 MB | 5.848 | 2023-01-02 20:00 | 2026-08-30 20:00 | SÍ (15) |
| 16 | **GC** | 1m | `XAUUSD` | 1 chunk (solo 2023-Q1) | `ds_dukascopy_xauusd_1m_1672700400000_1680296340000.json` | 14,20 MB | 87.837 | 2023-01-02 23:00 | 2023-03-31 20:59 | SÍ |
| 17 | **GC** | 5m | `XAUUSD` | 1 chunk (solo 2023-Q1) | `ds_dukascopy_xauusd_5m_1672700400000_1680296100000.json` | 2,84 MB | 17.572 | 2023-01-02 23:00 | 2023-03-31 20:55 | SÍ |
| 18 | **GC** | 15m | `XAUUSD` | 1 chunk (solo 2023-Q1) | `ds_dukascopy_xauusd_15m_1672700400000_1680295500000.json` | 0,95 MB | 5.858 | 2023-01-02 23:00 | 2023-03-31 20:45 | SÍ |
| 19 | **GC** | 1h | `XAUUSD` | 1 chunk (solo 2023-Q1) | `ds_dukascopy_xauusd_1h_1672700400000_1680292800000.json` | 0,24 MB | 1.465 | 2023-01-02 23:00 | 2023-03-31 20:00 | SÍ |
| 20 | **GC** | 4h | `XAUUSD` | 1 chunk (solo 2023-Q1) | `ds_dukascopy_xauusd_4h_1672689600000_1680292800000.json` | 0,06 MB | 397 | 2023-01-02 20:00 | 2023-03-31 20:00 | SÍ |
| 21 | **CL** | 1m | `LIGHTCMDUSD` | **NO HAY DATOS** | `NO HAY` | - | 0 | - | - | NO |
| 22 | **CL** | 5m | `LIGHTCMDUSD` | **NO HAY DATOS** | `NO HAY` | - | 0 | - | - | NO |
| 23 | **CL** | 15m | `LIGHTCMDUSD` | **NO HAY DATOS** | `NO HAY` | - | 0 | - | - | NO |
| 24 | **CL** | 1h | `LIGHTCMDUSD` | **NO HAY DATOS** | `NO HAY` | - | 0 | - | - | NO |
| 25 | **CL** | 4h | `LIGHTCMDUSD` | **NO HAY DATOS** | `NO HAY` | - | 0 | - | - | NO |

---

## 3. Diagnóstico de Cobertura y Aptitud para Generación / Validación

### Clasificación por Estado de Utilización
1. **Totalmente Utilizables para Certificación (11/11 Gates, >3,6 años de datos 2023-2026):**
   - **NQ** (`USATECHIDXUSD`): los 5 marcos temporales (`1m`, `5m`, `15m`, `1h`, `4h`).
   - **YM** (`USA30IDXUSD`): los 5 marcos temporales (`1m`, `5m`, `15m`, `1h`, `4h`).
   - **ES** (`USA500IDXUSD`): marcos `5m` (250.009 velas) y `15m` (83.377 velas), ambos consolidados.
   - **Subtotal utilizables plenamente:** **12 celdas de 25**.
2. **Parciales / Insuficientes para Walk-Forward Completo (<6 meses de historia):**
   - **ES** en `1m`, `1h`, `4h`: solo 2 trimestres (2023-Q1 y 2023-Q2, enero a junio 2023).
   - **GC** (`XAUUSD`) en `1m`, `5m`, `15m`, `1h`, `4h`: solo 1 trimestre (2023-Q1, enero a marzo 2023).
   - **Subtotal celdas parciales:** **8 celdas de 25**.
3. **Cero Datos en Disco:**
   - **CL** (`LIGHTCMDUSD`): no existe ningún fichero descargado ni normalizado en ningún marco temporal.
   - **Subtotal celdas vacías:** **5 celdas de 25**.

---

## 4. Estado del Fichero de Progreso de Backfill

Contenido exacto de `data/dukascopy_backfill_progress.json`:

```json
{
 "USA500IDXUSD": [
  "2023-Q1",
  "2023-Q2"
 ],
 "USATECHIDXUSD": [
  "2023-Q1",
  "2023-Q2"
 ]
}
```

**Diagnóstico del progreso:**
- El fichero `dukascopy_backfill_progress.json` quedó estancado registrando solo 2 trimestres de prueba inicial para `USA500IDXUSD` y `USATECHIDXUSD`.
- Sin embargo, en disco existen **15 trimestres completos para `USATECHIDXUSD` y `USA30IDXUSD`**, y los consolidados completos de `USA500IDXUSD` en 5m y 15m fueron consolidados a partir de 16 chunks mediante `scripts/herramientas/consolidar_dukascopy.py`.
- `XAUUSD` tiene únicamente el trimestre `2023-Q1`.
- `LIGHTCMDUSD` no ha sido iniciado en absoluto.

---

## 5. Salidas Crudas de Comandos

```bash
# Total de ficheros en data/normalized y conteo Dukascopy
$ ls data/normalized/ | wc -l
532

$ ls data/normalized/*dukascopy* | wc -l
414

$ ls data/normalized/*manifest*.json | wc -l
286

# Inspección de estructura interna de velas (bars)
$ .venv/Scripts/python.exe -c "import json; d=json.load(open('data/normalized/ds_dukascopy_usa30idxusd_15m_consolidated.json', encoding='utf-8')); print(d['bars'][0]); print(d['bars'][-1])"
{'close': 33267.789, 'high': 33399.739, 'low': 33260.729, 'open': 33368.769, 'spread_mean': 5.01758784, 'tick_count': 3290, 'timestamp_utc_ms': 1672700400000, 'volume': 0.24706400097238657}
{'close': 41656.789, 'high': 41673.789, 'low': 41648.789, 'open': 41656.789, 'spread_mean': 3.125, 'tick_count': 32, 'timestamp_utc_ms': 1788133500000, 'volume': 0.00392800010740757}

# Inspección de estado de descarga backfill
$ .venv/Scripts/python.exe -c "import json; d=json.load(open('data/dukascopy_backfill_progress.json', encoding='utf-8')); print(json.dumps(d, indent=1))"
{
 "USA500IDXUSD": [
  "2023-Q1",
  "2023-Q2"
 ],
 "USATECHIDXUSD": [
  "2023-Q1",
  "2023-Q2"
 ]
}
```
