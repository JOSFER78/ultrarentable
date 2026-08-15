"""Parse all 100 strategies in SQX Last Generation using exact column mapping."""

from services.sqx_bridge.sqx_client import SQXMCPClient

c = SQXMCPClient('http://127.0.0.1:8081/mcp', timeout=10)
strats = c.list_strategies('Ultra_Auto_Pilot', 'Last generation')

results = []

for s in strats:
    res = c.get_strategy_stats('Ultra_Auto_Pilot', 'Last generation', s)
    cols = res.get('columns', [])
    vals = res.get('values', [])
    
    # Map by column name
    # SQX columns list: ['Fitness (IS)', 'Symbol (IS)', 'TimeFrame (IS)', 'Net profit (IS)', ...]
    # vals has 2 leading items: [s_name, '', fitness_is, symbol_is, timeframe_is, np_is, ...]
    
    try:
        np_is = float(vals[5])
        trades_is = int(vals[7])
        pf_is = float(vals[8])
        dd_is = float(vals[14])
        
        # OOS values
        # Index 24 is Net profit (OOS)
        np_oos = float(vals[24])
        trades_oos = int(vals[26])
        pf_oos = float(vals[27])
        dd_oos = float(vals[33])
        
        results.append({
            'name': s,
            'np_is': np_is, 'trades_is': trades_is, 'pf_is': pf_is, 'dd_is': dd_is,
            'np_oos': np_oos, 'trades_oos': trades_oos, 'pf_oos': pf_oos, 'dd_oos': dd_oos,
            'ratio_oos_is': round(pf_oos / pf_is, 2) if pf_is > 0 else 0
        })
    except Exception:
        pass

# Filter strategies with positive net profit in OOS
profitable_oos = [r for r in results if r['np_oos'] > 0 and r['trades_oos'] >= 15]
profitable_oos = sorted(profitable_oos, key=lambda x: x['np_oos'], reverse=True)

print(f"Total Parsed: {len(results)} | Profitable in Out-of-Sample (OOS >= 15 trades): {len(profitable_oos)}")
for r in profitable_oos:
    print(f" -> {r['name']}: IS [NP=+${r['np_is']}, Trades={r['trades_is']}, PF={r['pf_is']}, DD={r['dd_is']}%] | OOS [NP=+${r['np_oos']}, Trades={r['trades_oos']}, PF={r['pf_oos']}, DD={r['dd_oos']}%, Ratio={r['ratio_oos_is']}x]")
