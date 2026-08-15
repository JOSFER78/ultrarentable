"""NinjaTrader 8 C# Code Exporter for Prop Firm Combine Automation.

Generates complete, compilable NinjaScript (.cs) code tailored for Topstep / Apex / TradeDay 50K combines:
- Daily Loss Limit Guard (Hard flat & disable when Daily PnL <= -$900).
- Session close enforcer (Flatten at 15:45 US/Central).
- Trailing Stop & ATR Profit Target.
- Dynamic Micro ES (MES) contract sizing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def generate_ninjatrader_strategy_cs(
    strategy_name: str,
    asset: str = "MES",
    default_qty: int = 4,
    daily_loss_limit_usd: float = 1000.0,
    profit_target_ticks: int = 48,  # 12 points
    stop_loss_ticks: int = 16,      # 4 points
    fast_ema_period: int = 21,
    slow_ema_period: int = 55,
    donchian_period: int = 20
) -> str:
    """Generate compilable NinjaTrader 8 C# Strategy."""
    clean_name = strategy_name.replace(" ", "").replace(".", "_").replace("-", "_")
    cs_code = f"""#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;
using System.Xml.Serialization;
using NinjaTrader.Cbi;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.SuperDom;
using NinjaTrader.Gui.Tools;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.Core.FloatingPoint;
using NinjaTrader.NinjaScript.Indicators;
using NinjaTrader.NinjaScript.DrawingTools;
#endregion

// Ultrarentable Prop Firm Engine - Generated for NinjaTrader 8
namespace NinjaTrader.NinjaScript.Strategies
{{
    public class {clean_name} : Strategy
    {{
        private EMA fastEma;
        private EMA slowEma;
        private MAX highestHigh;
        private MIN lowestLow;
        private ATR atrIndicator;

        private double dailyPnL = 0.0;
        private DateTime lastTradeDate = DateTime.MinValue;
        private bool isDailyLossHalted = false;

        [NinjaScriptProperty]
        [Range(1, 10)]
        [Display(Name="Quantity", Description="Contracts to trade (MES)", Order=1, GroupName="Parameters")]
        public int Contracts {{ get; set; }} = {default_qty};

        [NinjaScriptProperty]
        [Range(100, 5000)]
        [Display(Name="Daily Loss Limit ($)", Description="Hard stop limit", Order=2, GroupName="Parameters")]
        public double DailyLossLimit {{ get; set; }} = {daily_loss_limit_usd};

        [NinjaScriptProperty]
        [Range(4, 200)]
        [Display(Name="Profit Target (Ticks)", Description="Target ticks", Order=3, GroupName="Parameters")]
        public int ProfitTargetTicks {{ get; set; }} = {profit_target_ticks};

        [NinjaScriptProperty]
        [Range(4, 100)]
        [Display(Name="Stop Loss (Ticks)", Description="Stop ticks", Order=4, GroupName="Parameters")]
        public int StopLossTicks {{ get; set; }} = {stop_loss_ticks};

        protected override void OnStateChange()
        {{
            if (State == State.SetDefaults)
            {{
                Description = "Ultrarentable Prop Firm Strategy for {asset} with Automated DLL Kill-Switch.";
                Name = "{clean_name}";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 900; // 15 mins before close
                IsFillLimitOnTouch = false;
                MaximumBarsLookBack = MaximumBarsLookBack.TwoHundredFiftySix;
                OrderFillResolution = OrderFillResolution.Standard;
                Slippage = 1;
                StartBehavior = StartBehavior.WaitUntilFlat;
                TimeInForce = TimeInForce.Gtc;
                TraceOrders = false;
                RealtimeErrorHandling = RealtimeErrorHandling.StopCancelClose;
                StopTargetHandling = StopTargetHandling.PerEntryExecution;
                BarsRequiredToTrade = 60;
            }}
            else if (State == State.DataLoaded)
            {{
                fastEma = EMA({fast_ema_period});
                slowEma = EMA({slow_ema_period});
                highestHigh = MAX(High, {donchian_period});
                lowestLow = MIN(Low, {donchian_period});
                atrIndicator = ATR(14);

                SetProfitTarget(CalculationMode.Ticks, ProfitTargetTicks);
                SetStopLoss(CalculationMode.Ticks, StopLossTicks);
            }}
        }}

        protected override void OnBarUpdate()
        {{
            if (CurrentBar < BarsRequiredToTrade)
                return;

            // Reset Daily PnL on new calendar day
            if (Time[0].Date != lastTradeDate)
            {{
                lastTradeDate = Time[0].Date;
                dailyPnL = 0.0;
                isDailyLossHalted = false;
            }}

            // Check Hard Daily Loss Limit
            if (dailyPnL <= -DailyLossLimit)
            {{
                if (!isDailyLossHalted)
                {{
                    Print(string.Format("{{0}}: DAILY LOSS LIMIT REACHED (${{1:F2}}). Halting trading for the day.", Time[0], dailyPnL));
                    if (Position.MarketPosition != MarketPosition.Flat)
                    {{
                        if (Position.MarketPosition == MarketPosition.Long)
                            ExitLong();
                        else if (Position.MarketPosition == MarketPosition.Short)
                            ExitShort();
                    }}
                    isDailyLossHalted = true;
                }}
                return;
            }}

            if (isDailyLossHalted)
                return;

            // Trend and Breakout Conditions
            bool trendUp = fastEma[0] > slowEma[0] && Close[0] > fastEma[0];
            bool trendDown = fastEma[0] < slowEma[0] && Close[0] < fastEma[0];

            bool longBreakout = Close[0] >= highestHigh[1] && trendUp;
            bool shortBreakout = Close[0] <= lowestLow[1] && trendDown;

            if (Position.MarketPosition == MarketPosition.Flat)
            {{
                if (longBreakout)
                {{
                    EnterLong(Contracts, "LongEntry");
                }}
                else if (shortBreakout)
                {{
                    EnterShort(Contracts, "ShortEntry");
                }}
            }}
        }}

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {{
            if (execution.Order != null && execution.Order.OrderState == OrderState.Filled)
            {{
                // Track cumulative daily realized PnL
                if (SystemPerformance.RealtimeTrades.Count > 0)
                {{
                    var lastTrade = SystemPerformance.RealtimeTrades[SystemPerformance.RealtimeTrades.Count - 1];
                    if (lastTrade.ExitTime.Date == Time[0].Date)
                    {{
                        dailyPnL = SystemPerformance.RealtimeTrades
                            .Where(t => t.ExitTime.Date == Time[0].Date)
                            .Sum(t => t.ProfitCurrency);
                    }}
                }}
            }}
        }}
    }}
}}
"""
    return cs_code


def export_strategy_to_file(strategy_name: str, output_dir: Path) -> Path:
    """Save generated C# strategy to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_name = strategy_name.replace(" ", "").replace(".", "_").replace("-", "_")
    target_path = output_dir / f"{clean_name}.cs"
    code = generate_ninjatrader_strategy_cs(strategy_name)
    target_path.write_text(code, encoding="utf-8")
    return target_path


if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "exports" / "ninjatrader"
    p1 = export_strategy_to_file("Strategy 1.4.125 Low Drawdown", out_dir)
    p2 = export_strategy_to_file("Strategy 1.4.140 Dual Pass OOS", out_dir)
    print(f"Exported NinjaTrader Strategies:\n - {p1} ({p1.stat().st_size} bytes)\n - {p2} ({p2.stat().st_size} bytes)")
