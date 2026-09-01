# DESBLOQUEO DE TRADFI — el bloqueo F03.1 se apoyaba en una métrica mal calculada

Fecha: 2026-08-31 · Autor: orquestador (Hermes), verificado de forma independiente
Track: **FONDEO** (prioridad única desde la orden de Emilio de 2026-08-31)

## Resumen

El censo F03.1 declaró **BLOQUEADO** minar TRADFI porque los datasets de Yahoo tenían
"64-73 % de cobertura". **Esa cifra no mide contaminación de datos: mide que el auditor espera
barras 24/7 en instrumentos que cotizan 5 días por semana con pausa diaria de mantenimiento.**

`services/data/market_ingestor.py:87-89`:

```python
expected_records = ((end_ts - start_ts) // interval_ms) + 1 if end_ts >= start_ts else 1
coverage_pct = round((len(unique_bars) / max(1, expected_records)) * 100.0, 2)
```

`expected_records` cuenta los slots de un calendario **continuo 24/7**. Para un futuro CME
(23 h × 5 días = 115 h de las 168 h de la semana) el techo teórico es **68,5 %**; para forex
(24 × 5 = 120/168), **71,4 %**. Los valores observados (65,2 % en ES 1h, 70,3 % en EURUSD 1h)
**son exactamente ese techo estructural**: un dataset CME perfecto, sin un solo hueco, sacaría
~68 % con esta fórmula.

Peor aún, `market_ingestor.py:110` fija `is_valid=(gap_count == 0 and duplicate_count == 0)`,
con lo que **ningún futuro ni divisa puede ser jamás `is_valid: true`**, por construcción.

## Medición independiente (orquestador, no del auditor del proyecto)

Clasificando cada salto entre barras consecutivas de **ES 1h** (13.701 barras) según su causa:

| Tipo de salto | n | % |
| :--- | ---: | ---: |
| Contiguo (Δ = 1 h) | 13.077 | **95,45 %** |
| Pausa diaria de mantenimiento CME | 469 | 3,42 % |
| Fin de semana | 123 | 0,90 % |
| **Anómalo real** | **31** | **0,23 %** |

Y los peores "anómalos" son **festivos oficiales del mercado**, no fallos de datos:
`2024-03-28` (Viernes Santo), `2024-05-27` (Memorial Day), `2024-06-19` (Juneteenth).

**Conclusión: ES 1h y sus hermanos son datasets REAL-ONLY perfectamente válidos.** Los "7.312
gaps" del manifiesto son 469 pausas de sesión + 123 fines de semana + un puñado de festivos.

## Datasets APTOS hoy (12 símbolos × 1h)

`ES, NQ, YM, RTY, GC, CL` (876 días, 2024-03-26 → 2026-08-18) y
`EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF` (1.022 días, 2023-11-01 → 2026-08-18).
Contigüidad real 94-99 %.

## Lo que SÍ está contaminado (y hay que respetar)

### 1. El timeframe 4h es una fabricación estructural — NO USAR

`services/data/data_downloader.py:266`: `"4h": ("1h", "730d")  # Descarga 1h y re-muestrea`.
El remuestreo no comprueba que la barra de 4 h esté completa. Medido sobre ES:

| Métrica | Valor |
| :--- | ---: |
| Barras 4h totales | 3.714 |
| **Parciales (< 4 velas horarias)** | **750 = 20,2 %** |
| Con **UNA sola** vela horaria | 145 = 3,9 % |

Una barra de 1 hora etiquetada como barra de 4 horas corrompe cualquier indicador de rango o
ATR. **Y 4h es el timeframe por defecto de la campaña** (`scripts/cola_mineria.py:44`,
`TFS = ["4h"]`): las campañas TRADFI en 4h que se hayan corrido con estos datos no son fiables.

### 2. El volumen de forex está fabricado

`services/data/data_downloader.py:319`: `v = float(row.get("Volume", 100.0)) or 100.0`.
Yahoo devuelve 0 en forex, y el `or 100.0` lo convierte en 100. Verificado: EURUSD 1h tiene
17.236 barras y **un único valor distinto de volumen (100,0)**; USDJPY 1h, 17.139 barras, ídem.
Es una violación REAL-ONLY literal.

**Impacto hoy: NINGUNO sobre los backtests.** `grep -n "volume"` sobre
`services/validation/engine/event_backtest_engine.py` no devuelve **ni una línea**: el motor no
consume volumen, y ninguno de los arquetipos lo usa. Queda como riesgo latente: si algún día se
añade un indicador de volumen, hay que prohibirlo en forex o arreglar el descargador antes.

## Presupuesto de trades OOS en FONDEO 1h (aviso honesto)

Con el split IS 60 / Val 20 / **Blind OOS 20 %** y el criterio 1.1 (≥200 trades OOS):

| Símbolo | Barras | Barras OOS | Ritmo necesario para 200 trades |
| :--- | ---: | ---: | :--- |
| ES / NQ / GC | ~13.700 | ~2.740 | 1 trade cada **13,7 barras** (~1,7 al día de sesión) |
| CL | 13.541 | 2.708 | 1 cada 13,5 barras |
| EURUSD | 17.236 | 3.447 | 1 cada 17,2 barras |

Es **exigente pero alcanzable** para arquetipos intradía (`session_momentum` con `ancla_horas`
pequeña, `streak_edge` con `n_racha` bajo), a diferencia del 4h de cripto que era imposible.
El suelo del pipeline es `MIN_OPERACIONES_OOS = 100` (`scripts/mine.py:124`), pero el criterio
1.1 SELLADO exige 200 y no se relaja.

**Coste de intentarlo: bajo.** 12 celdas × 420 configs sobre ~13.700 barras ≈ 4 min por celda,
~48 min en total. Aunque no salga ninguna certificada, mide la frecuencia real de trades por
familia en futuros, que es justo el dato que hoy falta para decidir el timeframe definitivo.

## Corrección pendiente (deuda, no bloqueante)

`MarketDataAuditor.audit` debe calcular la cobertura contra el **calendario de sesión por
`venue`**, no contra un calendario 24/7, y resellar los manifiestos. Mientras no se haga,
cualquier gate automático sobre `coverage_pct`/`is_valid` seguirá bloqueando datos buenos y el
censo seguirá informando cifras falsas.
