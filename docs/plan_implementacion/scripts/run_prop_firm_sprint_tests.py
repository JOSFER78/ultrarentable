"""Monte Carlo and Mathematical Simulation for Passing Prop Firm Combines in <= 5 Days."""

import random
from typing import Dict, Any

def simulate_prop_firm_sprint(
    strategy_name: str,
    trades_per_day: int,
    win_rate: float,
    reward_risk_ratio: float,
    risk_per_trade_usd: float,
    dynamic_scaling: bool = False,
    n_simulations: int = 10000
) -> Dict[str, Any]:
    """
    Simulates a 5-day prop firm combine challenge under Topstep / TradeDay 50K rules:
    - Target: $3,000 USD (+6.0%)
    - Max Trailing Drawdown: $2,000 USD (4.0%)
    - Daily Loss Limit: $1,000 USD (2.0%)
    - Consistency Rule: <= 50% max profit from single day ($1,500 limit for $3,000 target)
    - Max Days: 5 days
    """
    ACCOUNT_SIZE = 50000.0
    PROFIT_TARGET = 3000.0
    MAX_TRAILING_DD = 2000.0
    DAILY_LOSS_LIMIT = 1000.0
    CONSISTENCY_LIMIT_PCT = 0.50  # 50%
    MAX_DAYS = 5
    
    passed_in_5_days = 0
    blown_trailing_dd = 0
    blown_daily_loss = 0
    failed_consistency = 0
    profitable_needs_more_days = 0
    unprofitable_needs_more_days = 0
    
    days_to_pass_list = []
    
    for _ in range(n_simulations):
        current_equity = ACCOUNT_SIZE
        peak_equity = ACCOUNT_SIZE
        daily_pnls = []
        is_blown = False
        passed = False
        
        for day in range(1, MAX_DAYS + 1):
            day_start_equity = current_equity
            day_trades_pnl = 0.0
            
            # Dynamic scaling: if ahead, slightly scale; if down, decrease size
            current_risk = risk_per_trade_usd
            if dynamic_scaling:
                total_gain_so_far = current_equity - ACCOUNT_SIZE
                if total_gain_so_far >= 1500.0:
                    current_risk = risk_per_trade_usd * 1.3
                elif total_gain_so_far < 0:
                    current_risk = risk_per_trade_usd * 0.7
                    
            for _ in range(trades_per_day):
                # Trade outcome
                is_win = random.random() < win_rate
                if is_win:
                    pnl = current_risk * reward_risk_ratio
                else:
                    pnl = -current_risk
                    
                current_equity += pnl
                day_trades_pnl += pnl
                
                # Update peak & check trailing DD
                if current_equity > peak_equity:
                    peak_equity = current_equity
                    
                current_dd = peak_equity - current_equity
                if current_dd >= MAX_TRAILING_DD:
                    blown_trailing_dd += 1
                    is_blown = True
                    break
                    
                # Check intraday DLL
                current_day_loss = day_start_equity - current_equity
                if current_day_loss >= DAILY_LOSS_LIMIT:
                    blown_daily_loss += 1
                    is_blown = True
                    break
                    
            if is_blown:
                break
                
            daily_pnls.append(day_trades_pnl)
            
            # Check if profit target achieved
            total_profit = current_equity - ACCOUNT_SIZE
            if total_profit >= PROFIT_TARGET:
                # Check consistency rule (Max single day profit <= 50% of total profit)
                max_single_day = max(daily_pnls) if daily_pnls else 0.0
                if max_single_day > (total_profit * CONSISTENCY_LIMIT_PCT):
                    failed_consistency += 1
                    is_blown = True
                else:
                    passed = True
                    passed_in_5_days += 1
                    days_to_pass_list.append(day)
                break
                
        if not is_blown and not passed:
            total_profit = current_equity - ACCOUNT_SIZE
            if total_profit > 0:
                profitable_needs_more_days += 1
            else:
                unprofitable_needs_more_days += 1

    avg_days_to_pass = sum(days_to_pass_list) / len(days_to_pass_list) if days_to_pass_list else 0.0

    return {
        "strategy_name": strategy_name,
        "simulations": n_simulations,
        "pass_rate_5_days_pct": round((passed_in_5_days / n_simulations) * 100, 2),
        "blown_trailing_dd_pct": round((blown_trailing_dd / n_simulations) * 100, 2),
        "blown_daily_loss_pct": round((blown_daily_loss / n_simulations) * 100, 2),
        "failed_consistency_pct": round((failed_consistency / n_simulations) * 100, 2),
        "profitable_needs_more_time_pct": round((profitable_needs_more_days / n_simulations) * 100, 2),
        "unprofitable_needs_more_time_pct": round((unprofitable_needs_more_days / n_simulations) * 100, 2),
        "avg_days_when_passed": round(avg_days_to_pass, 1)
    }

print("\n=== MONTE CARLO SIMULATION: PASSING 50K COMBINE IN <= 5 DAYS ===")

# Test 3 real strategy architectures
models = [
    {
        "strategy_name": "Modelo 1: Day Trader Estructurado (3 trades/día, 4 MES, Risk $150, R:R 1:2.2, WR 58%)",
        "trades_per_day": 3,
        "win_rate": 0.58,
        "reward_risk_ratio": 2.2,
        "risk_per_trade_usd": 150.0,
        "dynamic_scaling": False
    },
    {
        "strategy_name": "Modelo 2: Scalper Ultra-Agresivo (4 trades/día, 1 Mini ES, Risk $300, R:R 1:2.0, WR 50%)",
        "trades_per_day": 4,
        "win_rate": 0.50,
        "reward_risk_ratio": 2.0,
        "risk_per_trade_usd": 300.0,
        "dynamic_scaling": False
    },
    {
        "strategy_name": "Modelo 3: Dynamic Risk Scaling (3 trades/día, R:R 1:2.5, WR 55%, Base Risk $150)",
        "trades_per_day": 3,
        "win_rate": 0.55,
        "reward_risk_ratio": 2.5,
        "risk_per_trade_usd": 150.0,
        "dynamic_scaling": True
    },
    {
        "strategy_name": "Modelo 4: Sniper de Alta Precisión (1-2 trades/día, 6 MES, Risk $200, R:R 1:3.0, WR 52%)",
        "trades_per_day": 2,
        "win_rate": 0.52,
        "reward_risk_ratio": 3.0,
        "risk_per_trade_usd": 200.0,
        "dynamic_scaling": False
    },
]

for m in models:
    res = simulate_prop_firm_sprint(**m)
    print(f"\n========================================================")
    print(f"📊 {res['strategy_name']}")
    print(f"========================================================")
    print(f"  🟢 Aprobado en <= 5 días:        {res['pass_rate_5_days_pct']}% (Media: {res['avg_days_when_passed']} días)")
    print(f"  🔴 Quebrado por Trailing DD:     {res['blown_trailing_dd_pct']}%")
    print(f"  🔴 Quebrado por Límite Diario:   {res['blown_daily_loss_pct']}%")
    print(f"  ⚠️ Bloqueado por Consistencia:   {res['failed_consistency_pct']}%")
    print(f"  ⏳ En Ganancia (requiere +días): {res['profitable_needs_more_time_pct']}%")
    print(f"  ⏳ En Pérdida (requiere +días):  {res['unprofitable_needs_more_time_pct']}%")
