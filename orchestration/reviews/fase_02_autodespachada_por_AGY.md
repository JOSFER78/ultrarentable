# FASE 2 — INGESTA DUKASCOPY (PROXIES CME $0) + AMPLIACIÓN M1 CRIPTO

> **ANTES DE EMPEZAR, LEE `orchestration/METODOLOGIA_ANTIGRAVITY.md` ENTERO**, empezando por el
> bloque 🛑 ALTO de la primera página.
> Doctrina y decisiones selladas: `DOCTRINA_ORQUESTADOR.md §14 y §15`. Plan: `state/plan_maestro.md`.

---

## ⛔ REGLAS INVARIANTES DE ESTA FASE

1. **PROHIBIDO inventar datos, interpolar ticks o fabricar volumen artificial.** Si una hora no tiene ticks o falla la descarga tras reintentos, el fichero de ticks queda de 0 bytes o el hueco se registra formalmente como `NO_DATA`.
2. **CERO `git commit` y CERO `git push`.** Todo el trabajo debe quedar en el *working tree* para revisión manual del usuario y auditoría del Orquestador.
3. **CERO `rm`.** Todo archivo o script descartado debe enviarse a `cuarentena/` con manifiesto SHA-256.
4. **MÁXIMO CUIDADO CON EL RECURSO VPS:** Throttle de descarga de 0,35s entre peticiones HTTP para evitar bloqueos por rate-limiting de Dukascopy.

---

## 🐢 CÓMO TRABAJAR: DESPACIO Y MULTI-AGENTE

1. **Un entregable cada vez.** E1 completo antes de pasar a E2.
2. **Sello de tiempo** (`date -u +%H:%M:%S`) antes y después de cada entregable en el informe.
3. **Salidas de terminal crudas sin recortar ni resumir.**
4. **Método multi-agente obligatorio:**
   - **A1:** Ingesta y verificación del feed Dukascopy (`services/data_ingestion/dukascopy_feed.py`).
   - **A2:** Agregación de ticks a OHLCV en 5 TFs (`1m`, `5m`, `15m`, `1h`, `4h`) y manifiesto SHA-256.
   - **A3:** Backfill M1 cripto, registro de divergencia proxy ↔ CME y validación del conteo de celdas (≥110 celdas).

---

## OBJETIVO DE LA FASE

Construir e importar la matriz completa de datos cuantitativos a coste 0 € cubriendo 22 activos en 5 temporalidades intradiarias (`1m, 5m, 15m, 1h, 4h`), totalizando **≥110 celdas de datos**. Se combina la ingesta de ticks bid/ask reales de Dukascopy para proxies CME y Forex majors con el backfill de Binance Vision para Cripto.

---

## MAPA DE PROXIES Y ACTIVOS CANÓNICOS

| Categoría | Activo CME Real | Proxy Dukascopy / Feed | Símbolo Canónico | Timeframes |
| :--- | :--- | :--- | :--- | :--- |
| **Proxies Índices** | ES / MES | `USA500IDXUSD` | `USA500IDXUSD` | 1m, 5m, 15m, 1h, 4h |
| **Proxies Índices** | NQ / MNQ | `USATECHIDXUSD` | `USATECHIDXUSD` | 1m, 5m, 15m, 1h, 4h |
| **Proxies Índices** | YM / MYM | `USA30IDXUSD` | `USA30IDXUSD` | 1m, 5m, 15m, 1h, 4h |
| **Proxies Metales** | GC / MGC | `XAUUSD` | `XAUUSD` | 1m, 5m, 15m, 1h, 4h |
| **Proxies Metales** | SI | `XAGUSD` | `XAGUSD` | 1m, 5m, 15m, 1h, 4h |
| **Proxies Energía** | CL / MCL | `LIGHTCMDUSD` | `LIGHTCMDUSD` | 1m, 5m, 15m, 1h, 4h |
| **Proxies Índices** | RTY / M2K | `USARUSSIDXUSD` | `USARUSSIDXUSD` | 1m, 5m, 15m, 1h, 4h |
| **Forex Majors** | EUR/USD | `EURUSD` | `EURUSD` | 1m, 5m, 15m, 1h, 4h |
| **Forex Majors** | GBP/USD | `GBPUSD` | `GBPUSD` | 1m, 5m, 15m, 1h, 4h |
| **Forex Majors** | USD/JPY | `USDJPY` | `USDJPY` | 1m, 5m, 15m, 1h, 4h |
| **Forex Majors** | USD/CHF | `USDCHF` | `USDCHF` | 1m, 5m, 15m, 1h, 4h |
| **Forex Majors** | USD/CAD | `USDCAD` | `USDCAD` | 1m, 5m, 15m, 1h, 4h |
| **Forex Majors** | AUD/USD | `AUDUSD` | `AUDUSD` | 1m, 5m, 15m, 1h, 4h |
| **Cripto (Binance)** | BTC, ETH, SOL, XRP, SUI, AVAX, DOGE, BNB, LINK | Binance Vision Feed | `<SYM>USDT` | 1m, 5m, 15m, 1h, 4h |

---

## LOS 4 ENTREGABLES

### E1 — Ingestor Dukascopy y descarga masiva (`services/data_ingestion/dukascopy_feed.py`)

- **Verificación:** Ejecutar y completar la descarga de los 12 símbolos proxies + FX majors en el rango histórico disponible (mínimo 2024–2026).
- **Manejo atómico:** Descarga por hora en `.part` -> `rename` a `.bi5`, throttle 0,35s, reintentos con backoff.
- **Verificación física obligatoria:**
```bash
date -u +%H:%M:%S
python3 -c "import services.data_ingestion.dukascopy_feed as df; print(df.__file__)"
ls -lh data/raw/dukascopy/ 2>/dev/null | head -15
```

### E2 — Agregador Tick → OHLCV y Manifiesto de Celdas

- **Agregador:** Procesar ticks LZMA de `.bi5` a velas OHLCV en las 5 temporalidades (`1m`, `5m`, `15m`, `1h`, `4h`).
- **Persistencia:** Guardar datasets estandarizados en `data/normalized/` con formato de nombre `<SYM>_<TF>.json` o `.csv`.
- **Manifiesto:** Crear `data/normalized/MANIFEST_SHA256.txt` con la huella SHA-256 de cada celda y la nota explicativa obligatoria: `Aviso: Volumen de Dukascopy corresponde a tick volume del broker (VOLUMEN_PROXY)`.
- **Verificación física obligatoria:**
```bash
date -u +%H:%M:%S
ls -l data/normalized/ | wc -l
head -n 10 data/normalized/MANIFEST_SHA256.txt
```

### E3 — Backfill M1 Cripto y Conteo Global de Celdas (≥110 Celdas)

- Completar la descarga e ingesta de M1 cripto para los 9 activos (BTC, ETH, SOL, XRP, SUI, AVAX, DOGE, BNB, LINK) y agregar a los 5 TFs.
- Verificar que el total de celdas (Cripto 9×5 + Proxies 7×5 + FX 6×5) suma **≥ 110 celdas físicas**.
- **Verificación física obligatoria:**
```bash
date -u +%H:%M:%S
python3 -c "
import glob
files = glob.glob('data/normalized/*_*.*')
print(f'Total celdas normalizadas en disco: {len(files)}')
"
```

### E4 — Auditoría de Divergencia Proxy vs. CME Real y Control Git

- Comparar la muestra de datos real CME previamente importada (ej. ES/NQ M5) contra los proxies de Dukascopy (`USA500IDXUSD`, `USATECHIDXUSD`).
- Calcular e informar el coeficiente de correlación de precios y el spread medio. Si la correlación es `< 0.98`, documentarlo explícitamente sin ocultarlo.
- Verificar `git status` y comprobar que no se ha ejecutado ningún `git commit` ni `git push`.
- **Verificación física obligatoria:**
```bash
date -u +%H:%M:%S
git status --short
git log --oneline -5
```

---

## ENTREGA

Informe en `orchestration/results/fase_02.log`, siguiendo las 9 secciones obligatorias de la metodología.
Al terminar: `status="done"` en `status.json` + fichero `orchestration/state/DONE` con `phase=2` y `report_sha256=<sha256 del informe>`.

**Prohibido escribir en:** `current_phase.md`, `orchestration/reviews/`, `docs/`, `state/plan_maestro.md`.
