#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Linq;
using System.Net.Http;
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

// ============================================================================
// ULTRARENTABLE V2 PROP FIRM COMBINE ENGINE - NINJATRADER 8 C# STRATEGY
// Strategy Name: UR_Prop_MGC_TrendBreakout
// Asset: MGC (Micro Gold Futures)
// Hard DLL: $1,000.00 | Max DD: $2,000.00
// ============================================================================
namespace NinjaTrader.NinjaScript.Strategies
{
    public class UR_Prop_MGC_TrendBreakout : Strategy
    {
        private EMA fastEma;
        private EMA slowEma;
        private MAX highestHigh;
        private MIN lowestLow;
        private ATR atrIndicator;

        private double dailyPnL = 0.0;
        private double peakSessionEquity = 0.0;
        private DateTime lastTradeDate = DateTime.MinValue;
        private bool isDailyLossHalted = false;
        private bool isTrailingDDHalted = false;
        private bool breakEvenArmed = false;
        private static readonly HttpClient httpClient = new HttpClient();

        [NinjaScriptProperty]
        [Range(1, 20)]
        [Display(Name="Quantity", Description="Contracts to trade (MGC)", Order=1, GroupName="1. Risk & Sizing")]
        public int Contracts { get; set; } = 2;

        [NinjaScriptProperty]
        [Range(100, 10000)]
        [Display(Name="Daily Loss Limit ($)", Description="Hard daily loss limit in USD", Order=2, GroupName="1. Risk & Sizing")]
        public double DailyLossLimit { get; set; } = 1000.0;

        [NinjaScriptProperty]
        [Range(500, 20000)]
        [Display(Name="Max Trailing Drawdown ($)", Description="Maximum allowed drawdown before kill-switch", Order=3, GroupName="1. Risk & Sizing")]
        public double MaxTrailingDrawdown { get; set; } = 2000.0;

        [NinjaScriptProperty]
        [Range(4, 500)]
        [Display(Name="Profit Target (Ticks)", Description="Target ticks (0.1 tick size)", Order=4, GroupName="2. Order Management")]
        public int ProfitTargetTicks { get; set; } = 60;

        [NinjaScriptProperty]
        [Range(4, 300)]
        [Display(Name="Stop Loss (Ticks)", Description="Stop ticks (0.1 tick size)", Order=5, GroupName="2. Order Management")]
        public int StopLossTicks { get; set; } = 20;

        [NinjaScriptProperty]
        [Range(4, 300)]
        [Display(Name="Break-Even Trigger (Ticks)", Description="Ticks in profit to move SL to Entry (+1.5R)", Order=6, GroupName="2. Order Management")]
        public int BreakEvenTriggerTicks { get; set; } = 30;

        [NinjaScriptProperty]
        [Display(Name="Enable Webhook Telemetry", Description="Send fill events to Ultrarentable API", Order=7, GroupName="3. Telemetry")]
        public bool EnableTelemetry { get; set; } = true;

        [NinjaScriptProperty]
        [Display(Name="Telemetry Webhook URL", Description="FastAPI endpoint for real-time tracking", Order=8, GroupName="3. Telemetry")]
        public string TelemetryUrl { get; set; } = "http://127.0.0.1:8000/execution/ninjatrader/telemetry";

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "Ultrarentable Prop Firm Certified Strategy for MGC. Hard DLL, Trailing DD & Auto Break-Even.";
                Name = "UR_Prop_MGC_TrendBreakout";
                Calculate = Calculate.OnBarClose;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 900; // 15 mins before close (15:45 CT)
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
                peakSessionEquity = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar);
                isDailyLossHalted = false;
                isTrailingDDHalted = false;
            }

            // Check Hard Daily Loss Limit
            if (dailyPnL <= -DailyLossLimit)
            {
                if (!isDailyLossHalted)
                {
                    Print(string.Format("{0}: 🚨 HARD DAILY LOSS LIMIT REACHED (${1:F2}). Halting trading for the day.", Time[0], dailyPnL));
                    EmergencyFlatten("DAILY_LOSS_LIMIT");
                    isDailyLossHalted = true;
                }
                return;
            }

            // Check Max Trailing Drawdown
            double currentRealized = Account.Get(AccountItem.RealizedProfitLoss, Currency.UsDollar);
            if (currentRealized > peakSessionEquity)
                peakSessionEquity = currentRealized;

            double currentDrawdown = peakSessionEquity - currentRealized;
            if (currentDrawdown >= MaxTrailingDrawdown)
            {
                if (!isTrailingDDHalted)
                {
                    Print(string.Format("{0}: 🚨 MAX TRAILING DRAWDOWN REACHED (${1:F2}). Kill-switch activated.", Time[0], currentDrawdown));
                    EmergencyFlatten("TRAILING_DRAWDOWN");
                    isTrailingDDHalted = true;
                }
                return;
            }

            if (isDailyLossHalted || isTrailingDDHalted)
                return;

            // Automated Break-Even at +1.5R (+BreakEvenTriggerTicks)
            if (Position.MarketPosition == MarketPosition.Long && !breakEvenArmed)
            {
                double profitTicks = (Close[0] - Position.AveragePrice) / TickSize;
                if (profitTicks >= BreakEvenTriggerTicks)
                {
                    SetStopLoss(CalculationMode.Price, Position.AveragePrice + (2 * TickSize));
                    breakEvenArmed = true;
                    Print(string.Format("{0}: 🛡️ Break-Even armed for LONG position at price ${1:F2}", Time[0], Position.AveragePrice));
                }
            }
            else if (Position.MarketPosition == MarketPosition.Short && !breakEvenArmed)
            {
                double profitTicks = (Position.AveragePrice - Close[0]) / TickSize;
                if (profitTicks >= BreakEvenTriggerTicks)
                {
                    SetStopLoss(CalculationMode.Price, Position.AveragePrice - (2 * TickSize));
                    breakEvenArmed = true;
                    Print(string.Format("{0}: 🛡️ Break-Even armed for SHORT position at price ${1:F2}", Time[0], Position.AveragePrice));
                }
            }

            if (Position.MarketPosition == MarketPosition.Flat)
            {
                breakEvenArmed = false;
                SetStopLoss(CalculationMode.Ticks, StopLossTicks); // Reset to default

                // Trend and Breakout Conditions
                bool trendUp = fastEma[0] > slowEma[0] && Close[0] > fastEma[0];
                bool trendDown = fastEma[0] < slowEma[0] && Close[0] < fastEma[0];

                bool longBreakout = Close[0] >= highestHigh[1] && trendUp;
                bool shortBreakout = Close[0] <= lowestLow[1] && trendDown;

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

        private void EmergencyFlatten(string reason)
        {
            if (Position.MarketPosition != MarketPosition.Flat)
            {
                if (Position.MarketPosition == MarketPosition.Long)
                    ExitLong("KillSwitchLong");
                else if (Position.MarketPosition == MarketPosition.Short)
                    ExitShort("KillSwitchShort");
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution.Order != null && execution.Order.OrderState == OrderState.Filled)
            {
                if (SystemPerformance.RealtimeTrades.Count > 0)
                {
                    dailyPnL = SystemPerformance.RealtimeTrades
                        .Where(t => t.ExitTime.Date == Time[0].Date)
                        .Sum(t => t.ProfitCurrency);
                }

                if (EnableTelemetry && !string.IsNullOrEmpty(TelemetryUrl))
                {
                    SendTelemetryWebhook(execution, price, quantity, marketPosition, time);
                }
            }
        }

        private async void SendTelemetryWebhook(Execution execution, double price, int quantity, MarketPosition marketPosition, DateTime time)
        {
            try
            {
                string jsonStr = string.Format(
                    "\{\"strategy_name\":\"UR_Prop_MGC_TrendBreakout\",\"symbol\":\"MGC\",\"account_name\":\"0\",\"execution_id\":\"1\",\"side\":\"2\",\"price\":3,\"quantity\":4,\"daily_pnl_usd\":5,\"timestamp_utc\":\"6\"\}",
                    Account.Name, execution.ExecutionId, marketPosition.ToString(), price, quantity, dailyPnL, time.ToUniversalTime().ToString("o")
                );

                var content = new StringContent(jsonStr, Encoding.UTF8, "application/json");
                await httpClient.PostAsync(TelemetryUrl, content);
            }
            catch (Exception ex)
            {
                Print("Telemetry send error: " + ex.Message);
            }
        }
    }
}
