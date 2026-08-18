"""Rank Top 5 Strategies from SQX and Ultra Lab."""

from services.sqx_bridge.sqx_client import SQXMCPClient

c = SQXMCPClient('http://127.0.0.1:8081/mcp', timeout=20)
strats = c.list_strategies('Ultra_Auto_Pilot', 'Last generation')

parsed = []
for s in strats:
    res = c.get_strategy_stats('Ultra_Auto_Pilot', 'Last generation', s)
    cols = res.get('columns', [])
    vals = res.get('values', [])
    
    d = {}
    for col, val in zip(cols, vals[2:]):
        d[col] = val
        
    try:
        np_is = float(d.get('Net profit (IS)', 0))
        pf_is = float(d.get('Profit factor (IS)', 0))
        trades_is = int(d.get('# of trades (IS)', 0))
        dd_is = float(d.get('Drawdown (IS)', 0))
        sharpe_is = float(d.get('Sharpe Ratio (IS)', 0))
        ret_dd_is = float(d.get('Ret/DD Ratio (IS)', 0))
        stability_is = float(d.get('Stability (IS)', 0))
        
        np_oos = float(d.get('Net profit (OOS)', 0))
        pf_oos = float(d.get('Profit factor (OOS)', 0))
        trades_oos = int(d.get('# of trades (OOS)', 0))
        dd_oos = float(d.get('Drawdown (OOS)', 0))
        sharpe_oos = float(d.get('Sharpe Ratio (OOS)', 0))
        
        parsed.append({
            'name': s,
            'np_is': np_is, 'pf_is': pf_is, 'trades_is': trades_is, 'dd_is': dd_is,
            'sharpe_is': sharpe_is, 'ret_dd_is': ret_dd_is, 'stability_is': stability_is,
            'np_oos': np_oos, 'pf_oos': pf_oos, 'trades_oos': trades_oos, 'dd_oos': dd_oos,
            'sharpe_oos': sharpe_oos,
            'ratio_oos_is': round(pf_oos / pf_is, 2) if pf_is > 0 else 0
        })
    except Exception as e:
        pass

print(f"Total parsed: {len(parsed)}")

# 1. TOP 5 FOR FONDEO (Ranked by Ret/DD ratio, Stability, PF IS >= 1.30, Trades >= 30)
fondeo_candidates = [p for p in parsed if p['trades_is'] >= 30 and p['pf_is'] >= 1.20]
fondeo_candidates = sorted(fondeo_candidates, key=lambda x: (x['ret_dd_is'], x['pf_is']), reverse=True)

print("\n========================================================")
print("🛡️ TOP 5 RESULTADOS - MODO FONDEO (StrategyQuant X)")
print("========================================================")
for i, f in enumerate(fondeo_candidates[:5], 1):
    print(f"#{i} {f['name']}:")
    print(f"   - In-Sample (70%): Net Profit=+${f['np_is']} | PF={f['pf_is']} | Trades={f['trades_is']} | Ret/DD Ratio={f['ret_dd_is']} | Drawdown=${f['dd_is']} | Sharpe={f['sharpe_is']} | Estabilidad={f['stability_is']}")
    print(f"   - Out-of-Sample (30%): Net Profit=+${f['np_oos']} | PF={f['pf_oos']} | Trades={f['trades_oos']} | Drawdown=${f['dd_oos']}")

# 2. TOP 5 FOR ULTRARENTABLE (Ranked by Net Profit, Sharpe, Win/Loss Ratio)
ultra_candidates = sorted(parsed, key=lambda x: (x['np_is'], x['sharpe_is']), reverse=True)

print("\n========================================================")
print("🔥 TOP 5 RESULTADOS - MODO ULTRARENTABLE (StrategyQuant X)")
print("========================================================")
for i, u in enumerate(ultra_candidates[:5], 1):
    print(f"#{i} {u['name']}:")
    print(f"   - Retorno Neto IS: +${u['np_is']} USD (+{(u['np_is']/10):.1f}% ROI)")
    print(f"   - Métricas: PF={u['pf_is']} | Trades={u['trades_is']} | Sharpe={u['sharpe_is']} | Max Drawdown=${u['dd_is']} | Ret/DD={u['ret_dd_is']}")
    print(f"   - OOS Telemetría: Net Profit=+${u['np_oos']} | PF={u['pf_oos']} | Trades={u['trades_oos']}")
