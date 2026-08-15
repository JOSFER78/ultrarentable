#region Using declarations
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
{
    public class Strategy1_4_140DualPassOOS : Strategy
    {
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
        public int Contracts { get; set; } = 4;

        [NinjaScriptProperty]
        [Range(100, 5000)]
        [Display(Name="Daily Loss Limit ($)", Description="Hard stop limit", Order=2, GroupName="Parameters")]
        public double DailyLossLimit { get; set; } = 1000.0;

        [NinjaScriptProperty]
        [Range(4, 200)]
        [Display(Name="Profit Target (Ticks)", Description="Target ticks", Order=3, GroupName="Parameters")]
        public int ProfitTargetTicks { get; set; } = 48;

        [NinjaScriptProperty]
        [Range(4, 100)]
        [Display(Name="Stop Loss (Ticks)", Description="Stop ticks", Order=4, GroupName="Parameters")]
        public int StopLossTicks { get; set; } = 16;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Ultrarentable Prop Firm Strategy for MES with Automated DLL Kill-Switch.";
                Name = "Strategy1_4_140DualPassOOS";
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
            }
            else if (State == State.DataLoaded)
            {
                fastEma = EMA(21);
                slowEma = EMA(55);
                highestHigh = MAX(High, 20);
                lowestLow = MIN(Low, 20);
                atrIndicator = ATR(14);

                SetProfitTarget(CalculationMode.Ticks, ProfitTargetTicks);
                SetStopLoss(CalculationMode.Ticks, StopLossTicks);
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade)
                return;

            // Reset Daily PnL on new calendar day
            if (Time[0].Date != lastTradeDate)
            {
                lastTradeDate = Time[0].Date;
                dailyPnL = 0.0;
                isDailyLossHalted = false;
            }

            // Check Hard Daily Loss Limit
            if (dailyPnL <= -DailyLossLimit)
            {
                if (!isDailyLossHalted)
                {
                    Print(string.Format("{0}: DAILY LOSS LIMIT REACHED (${1:F2}). Halting trading for the day.", Time[0], dailyPnL));
                    if (Position.MarketPosition != MarketPosition.Flat)
                    {
                        if (Position.MarketPosition == MarketPosition.Long)
                            ExitLong();
                        else if (Position.MarketPosition == MarketPosition.Short)
                            ExitShort();
                    }
                    isDailyLossHalted = true;
                }
                return;
            }

            if (isDailyLossHalted)
                return;

            // Trend and Breakout Conditions
            bool trendUp = fastEma[0] > slowEma[0] && Close[0] > fastEma[0];
            bool trendDown = fastEma[0] < slowEma[0] && Close[0] < fastEma[0];

            bool longBreakout = Close[0] >= highestHigh[1] && trendUp;
            bool shortBreakout = Close[0] <= lowestLow[1] && trendDown;

            if (Position.MarketPosition == MarketPosition.Flat)
            {
                if (longBreakout)
                {
                    EnterLong(Contracts, "LongEntry");
                }
                else if (shortBreakout)
                {
                    EnterShort(Contracts, "ShortEntry");
                }
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order != null && execution.Order.OrderState == OrderState.Filled)
            {
                // Track cumulative daily realized PnL
                if (SystemPerformance.RealtimeTrades.Count > 0)
                {
                    var lastTrade = SystemPerformance.RealtimeTrades[SystemPerformance.RealtimeTrades.Count - 1];
                    if (lastTrade.ExitTime.Date == Time[0].Date)
                    {
                        dailyPnL = SystemPerformance.RealtimeTrades
                            .Where(t => t.ExitTime.Date == Time[0].Date)
                            .Sum(t => t.ProfitCurrency);
                    }
                }
            }
        }
    }
}
