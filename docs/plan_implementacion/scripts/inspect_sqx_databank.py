"""Inspect SQX Last Generation Databank."""

from services.sqx_bridge.sqx_client import SQXMCPClient

c = SQXMCPClient('http://127.0.0.1:8081/mcp', timeout=10)
strats = c.list_strategies('Ultra_Auto_Pilot', 'Last generation')
print(f"Total strategies in SQX 'Last generation': {len(strats)}")

approved = []
for s in strats:
    res = c.get_strategy_stats('Ultra_Auto_Pilot', 'Last generation', s)
    cols = res.get('columns', [])
    vals = res.get('values', [])
    data = dict(zip(cols, vals))
    
    try:
        np_is = float(data.get('Net profit (IS)', 0))
        pf_is = float(data.get('Profit factor (IS)', 0))
        trades_is = int(data.get('# of trades (IS)', 0))
        dd_is = float(data.get('Drawdown (IS)', 0))
        
        np_oos = float(data.get('Net profit (OOS)', 0))
        pf_oos = float(data.get('Profit factor (OOS)', 0))
        trades_oos = int(data.get('# of trades (OOS)', 0))
        dd_oos = float(data.get('Drawdown (OOS)', 0))
        
        if np_oos > 0 and pf_oos >= 1.10 and trades_oos >= 20:
            approved.append({
                'name': s,
                'np_is': np_is, 'pf_is': pf_is, 'trades_is': trades_is, 'dd_is': dd_is,
                'np_oos': np_oos, 'pf_oos': pf_oos, 'trades_oos': trades_oos, 'dd_oos': dd_oos,
                'ratio_oos_is': round(pf_oos / pf_is, 2) if pf_is > 0 else 0
            })
    except Exception as e:
        pass

print(f"\nCandidates with Positive OOS Profit Factor & >=20 Trades: {len(approved)}")
for a in approved:
    print(f" -> {a['name']}: IS [NP=+${a['np_is']}, PF={a['pf_is']}, DD={a['dd_is']}%] | OOS [NP=+${a['np_oos']}, PF={a['pf_oos']}, DD={a['dd_oos']}%, Trades={a['trades_oos']}] | Ratio OOS/IS={a['ratio_oos_is']}")
