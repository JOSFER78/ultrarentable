# Configuración de campaña

```yaml
campaign:
  name: eth_kamikaze_5m_v1
  mode: KAMIKAZE_DISCOVERY
market:
  exchange: binance_usdm
  instrument: ETHUSDT-PERP
  timeframe: 5m
data:
  history_years: 3
  evaluation_window_days: 90
  seed: 20260728
simulation:
  initial_equity: 1000
  intrabar_policy: PESSIMISTIC
  leverage_range: [1, 50]
  compound: true
search:
  initial_population: 5000
  fast_top_k: 250
  canonical_top_k: 50
  generations: 100
  mutation_rate: 0.65
  crossover_rate: 0.25
  novelty_injection_rate: 0.10
selection:
  reject_only:
    - LIQUIDATED
    - NON_POSITIVE_EQUITY
    - INVALID_SIMULATION
    - NON_REPRODUCIBLE
  rank_by: TERMINAL_MULTIPLE
```
