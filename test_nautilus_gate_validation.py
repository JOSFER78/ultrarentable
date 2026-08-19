import json
from services.api.app.validation.nautilus_gate_engine import NautilusGateEngine

with open('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/normalized/ds_binance_suiusdt_1h_1695290400000_1787086800000.json') as f:
    candles = json.load(f)

candidate = {
    'candidate_id': 'cand_ultra_suiusdt_1h_trend_ema_regime_15_70',
    'route': 'ULTRA',
    'archetype': 'TREND_EMA_REGIME',
    'scorecard_json': {
        'parameters': {
            'sl_atr_mult': 1.5,
            'tp_atr_mult': 7.0,
            'risk_pct': 3.0,
            'pyramiding_tiers': 3,
            'max_leverage': 500.0,
        }
    }
}

engine = NautilusGateEngine()
result = engine.validate_candidate(candidate, candles, account_size_usd=10000.0, max_leverage_ceiling=500.0)

print('=== NAUTILUS GATE 11 VALIDATION REPORT ===')
for k, v in result.to_dict().items():
    print(f'{k}: {v}')
