# SMOKE — 4 familias de arquetipos nuevas (5.14.0 / F03.3)

**Fecha:** 2026-08-31 · **Motor:** 5.14.0 · **Dataset:** REAL, sin mocks —
`data/normalized/ds_binance_btcusdt_15m_1609459200000_1788133500000.json`
(BTCUSDT 15m, 198.528 velas, 2021-01-01 → cobertura profunda hasta el final del dataset).

## Objetivo

Verificar que cada una de las 4 familias EVENTO nuevas (`reversion_atr`, `squeeze_breakout`,
`session_momentum`, `streak_edge`) genera ≥1 operación en al menos una configuración de su
rejilla (`scripts.mine._arquetipos_5_14_0_configs`), usando el motor tal como despacha por
`strategy.archetype` + `archetype_params` (sin atajos, sin datos sintéticos).

Se probaron 3 configuraciones por familia (primera, mediana y última del listado generado por
`_arquetipos_5_14_0_configs(is_ultra=True)`), instanciando el snapshot vía
`UltraDiscoveryEngine.generate_candidate_blueprint(..., archetype=..., archetype_params=...)`
y ejecutando `EventBacktestEngine.run_backtest` directamente sobre las velas reales cargadas
con `scripts.mine.load_candles_from_file`.

## Comando

```bash
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
.venv/bin/python <script_temporal_que_reproduce_lo_siguiente>
```

Lógica exacta reproducible (equivalente a lo ejecutado):

```python
import importlib.util, sys, time
from pathlib import Path
REPO_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
sys.path.insert(0, str(REPO_ROOT))
spec = importlib.util.spec_from_file_location("mine", REPO_ROOT / "scripts" / "mine.py")
mine = importlib.util.module_from_spec(spec); spec.loader.exec_module(mine)
from services.validation.engine.event_backtest_engine import EventBacktestEngine
from services.discovery.ultra_discovery import UltraDiscoveryEngine

engine = EventBacktestEngine(); disc = UltraDiscoveryEngine()
dataset_file = REPO_ROOT / "data/normalized/ds_binance_btcusdt_15m_1609459200000_1788133500000.json"
candles = mine.load_candles_from_file(dataset_file)
sha = mine.compute_file_sha256(dataset_file)
dataset_id = dataset_file.stem.replace("_manifest", "")

by_arch = {}
for c in mine._arquetipos_5_14_0_configs(is_ultra=True):
    by_arch.setdefault(c["archetype"], []).append(c)

for arch, cfgs in by_arch.items():
    for si in sorted({0, len(cfgs)//2, len(cfgs)-1}):
        cfg = cfgs[si]
        snap = disc.generate_candidate_blueprint(
            strategy_id=f"SMOKE_{arch}_{si}", symbol="BTCUSDT", timeframe="15m",
            dataset_id=dataset_id, dataset_sha256=sha, leverage=5.0,
            risk_pct=cfg["risk_pct"], sl_atr_mult=cfg["sl_atr_mult"], tp_atr_mult=cfg["tp_atr_mult"],
            ema_fast=cfg["ema_fast"], ema_slow=cfg["ema_slow"], archetype=cfg["archetype"],
            archetype_params=cfg.get("archetype_params"),
        )
        bt = engine.run_backtest(snap, candles, initial_capital_usd=1000.0)
        print(arch, si, cfg.get("archetype_params"), bt.total_trades, bt.profit_factor)
```

## Salida real

```
dataset=ds_binance_btcusdt_15m_1609459200000_1788133500000.json candles=198528
REVERSION_ATR    idx=  0 params={'ema_ancla': 20, 'banda_atr_mult': 1.5} sl=1.5 tp=4.5 risk=0.02 -> trades= 1476 pf=0.680 time=4.41s
REVERSION_ATR    idx= 54 params={'ema_ancla': 50, 'banda_atr_mult': 2.0} sl=2.0 tp=6.0 risk=0.1 -> trades=  794 pf=0.720 time=4.86s
REVERSION_ATR    idx=107 params={'ema_ancla': 100, 'banda_atr_mult': 3.0} sl=3.0 tp=9.0 risk=0.2 -> trades=  544 pf=0.800 time=4.20s
SQUEEZE_BREAKOUT idx=  0 params={'squeeze_pct': 20.0, 'squeeze_lookback': 50, 'breakout_lookback': 10} sl=1.5 tp=4.0 risk=0.02 -> trades=  763 pf=0.760 time=4.51s
SQUEEZE_BREAKOUT idx= 48 params={'squeeze_pct': 30.0, 'squeeze_lookback': 50, 'breakout_lookback': 10} sl=1.5 tp=4.0 risk=0.02 -> trades=  919 pf=0.850 time=5.72s
SQUEEZE_BREAKOUT idx= 95 params={'squeeze_pct': 30.0, 'squeeze_lookback': 100, 'breakout_lookback': 20} sl=3.0 tp=8.0 risk=0.2 -> trades=  859 pf=1.010 time=5.60s
SESSION_MOMENTUM idx=  0 params={'ancla_horas': 1, 'ema_pull': 20, 'cierre_eod': True} sl=1.5 tp=4.0 risk=0.02 -> trades= 1140 pf=0.780 time=6.57s
SESSION_MOMENTUM idx= 72 params={'ancla_horas': 2, 'ema_pull': 50, 'cierre_eod': True} sl=1.5 tp=4.0 risk=0.02 -> trades=  903 pf=0.700 time=6.50s
SESSION_MOMENTUM idx=143 params={'ancla_horas': 4, 'ema_pull': 50, 'cierre_eod': False} sl=3.0 tp=8.0 risk=0.2 -> trades=  517 pf=0.910 time=8.85s
STREAK_EDGE      idx=  0 params={'n_racha': 3, 'modo': 'continuacion'} sl=1.5 tp=4.0 risk=0.02 -> trades= 2254 pf=0.970 time=4.66s
STREAK_EDGE      idx= 36 params={'n_racha': 4, 'modo': 'reversion'} sl=1.5 tp=4.0 risk=0.02 -> trades= 1013 pf=0.790 time=5.18s
STREAK_EDGE      idx= 71 params={'n_racha': 5, 'modo': 'reversion'} sl=3.0 tp=8.0 risk=0.2 -> trades=  172 pf=0.310 time=5.23s

=== RESUMEN POR FAMILIA ===
REVERSION_ATR: OK (>=1 trade) -- [1476, 794, 544]
SQUEEZE_BREAKOUT: OK (>=1 trade) -- [763, 919, 859]
SESSION_MOMENTUM: OK (>=1 trade) -- [1140, 903, 517]
STREAK_EDGE: OK (>=1 trade) -- [2254, 1013, 172]
```

## Veredicto

Las 4 familias generan operaciones reales sobre datos reales en TODAS las muestras probadas
(no solo en una configuración aislada). PF por debajo de 1.0 en la mayoría de celdas es
esperable y no es motivo de bloqueo del smoke: el criterio de este paso es solo generación de
señal/operativa, no rentabilidad (eso lo decide el censo 1.1 / los gates en la re-campaña
`arquetipos`, paso siguiente del plan).

## Nota de auditoría relevante para este resultado

Este smoke se ejecutó **después** de corregir un bug de wiring encontrado en la auditoría:
`scripts/mine.py` construía `cfg["archetype_params"]` con la rejilla real por familia, pero no
lo reenviaba a `UltraDiscoveryEngine.generate_candidate_blueprint` /
`FundingDiscoveryEngine.generate_candidate_blueprint` (ambos aceptan el kwarg
`archetype_params` y lo reenvían a `StrategySnapshot.create_and_hash`, pero sin el kwarg
explícito en la llamada quedaba en `None` — con lo que TODAS las configuraciones de una misma
familia colapsaban a los valores por defecto del motor, anulando la búsqueda por dimensión).
Corregido en `scripts/mine.py` (ambas llamadas, ULTRA y FONDEO) añadiendo
`archetype_params=cfg.get("archetype_params")`. Sin este fix, el smoke seguía dando trades
(los defaults del motor son valores válidos dentro de la rejilla), pero la rejilla en sí nunca
se habría explorado en una campaña real.
