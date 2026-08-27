/**
 * @file tradesfera-calculator.ts
 * @description Contratos de datos, interfaces TypeScript y motor analítico/Monte Carlo
 * para la Calculadora de Bankroll, Varianza y Optimización de Retiros de Tradesfera.
 * @version 1.0.0
 * @author Tradesfera Quantitative Engineering Team
 */

export type DrawdownType = "INTRADAY_PEAK" | "END_OF_DAY" | "STATIC";

export interface PropFirmAccountParams {
  id: string;
  firmName: string;
  accountName: string;
  accountSizeUsd: number;
  profitTargetUsd: number;
  maxDrawdownUsd: number;
  dailyLossLimitUsd?: number;
  drawdownType: DrawdownType;
  examPriceUsd: number;
  activationFeeUsd: number;
  monthlyRenewalUsd: number;
  safetyBufferUsd: number;
  payoutSplitPct: number; // e.g., 0.90 for 90%
  consistencyRuleMaxPct?: number; // e.g., 0.30 for 30% max day
  minimumTradingDays: number;
}

export interface TradingStrategyMetrics {
  strategyName: string;
  winRatePct: number; // e.g., 55.0 for 55%
  payoffRatio: number; // Win / Loss ratio (e.g., 1.5)
  riskPerTradeUsd: number; // 1R in USD (e.g., 150)
  tradesPerDay: number; // Average trades per session
  slippagePerTradeUsd: number; // Average slippage + commissions
  historicalTradeReturns?: number[]; // Raw trade PnL array for bootstrap
}

export interface MonteCarloSimulationConfig {
  iterations: number; // Standard: 10,000
  maxTradesPerRun: number; // Cutoff (e.g., 500 trades)
  resampleMode: "PARAMETRIC" | "BOOTSTRAP_HISTORICAL";
  confidenceIntervalPct: number; // e.g., 95.0 for 95%
  randomSeed?: number;
}

export interface FanChartPercentiles {
  p5: number[];
  p25: number[];
  p50: number[];
  p75: number[];
  p95: number[];
}

export interface MonteCarloSimulationResults {
  passProbabilityPct: number;
  bustProbabilityPct: number;
  timeoutProbabilityPct: number;
  expectedTradesToPass: number;
  expectedDaysToPass: number;
  medianMaxDrawdownUsd: number;
  p95MaxDrawdownUsd: number;
  p99MaxDrawdownUsd: number;
  fanChartPercentiles: FanChartPercentiles;
  totalSimulatedPaths: number;
}

export interface BankrollAmmunitionBreakdown {
  totalAmmunitionBullets: number;
  effectiveRiskPerTradeUsd: number;
  riskOfRuinPct: number;
  suggestedMicroContracts: number;
  suggestedMiniContracts: number;
  bulletHealthCategory: "CRITICAL" | "MODERATE" | "OPTIMAL" | "ULTRA_SAFE";
}

export interface PayoutOptimizationOutput {
  totalCapitalInvestedUsd: number;
  grossTargetExtractionUsd: number;
  netCashExtractedUsd: number;
  expectedNetProfitUsd: number;
  trueRoiMultiple: number;
  breakEvenWinRatePct: number;
  evPerAccountPurchasedUsd: number;
}

export interface TradesferaCalculatorState {
  propFirm: PropFirmAccountParams;
  strategy: TradingStrategyMetrics;
  simulationConfig: MonteCarloSimulationConfig;
  simulationResults?: MonteCarloSimulationResults;
  bankrollBreakdown?: BankrollAmmunitionBreakdown;
  payoutOptimization?: PayoutOptimizationOutput;
  isCalculating: boolean;
  lastCalculatedTimestamp?: string;
}

/**
 * Calcula la munición de balas y riesgo de ruina para una cuenta y estrategia
 */
export function calculateAmmunition(
  prop: PropFirmAccountParams,
  strat: TradingStrategyMetrics
): BankrollAmmunitionBreakdown {
  const friction = strat.slippagePerTradeUsd;
  const effectiveRisk = strat.riskPerTradeUsd + friction;
  const bullets = Math.max(1, Math.floor((prop.maxDrawdownUsd * 0.95) / effectiveRisk));

  // Fórmula aproximada de Ruina
  const p = strat.winRatePct / 100.0;
  const q = 1.0 - p;
  const b = Math.max(0.1, strat.payoffRatio);
  const edge = p * b - q;

  let riskOfRuin = 0;
  if (edge <= 0) {
    riskOfRuin = 100.0;
  } else {
    const s = Math.pow(q / (p * b), bullets);
    riskOfRuin = Math.min(100.0, Math.max(0.0, s * 100.0));
  }

  let category: BankrollAmmunitionBreakdown["bulletHealthCategory"] = "OPTIMAL";
  if (bullets < 6) category = "CRITICAL";
  else if (bullets < 10) category = "MODERATE";
  else if (bullets >= 20) category = "ULTRA_SAFE";

  return {
    totalAmmunitionBullets: bullets,
    effectiveRiskPerTradeUsd: effectiveRisk,
    riskOfRuinPct: Number(riskOfRuin.toFixed(2)),
    suggestedMicroContracts: Math.max(1, Math.floor(strat.riskPerTradeUsd / 37.5)),
    suggestedMiniContracts: strat.riskPerTradeUsd >= 375 ? Math.floor(strat.riskPerTradeUsd / 375) : 0,
    bulletHealthCategory: category,
  };
}

/**
 * Ejecuta la simulación Monte Carlo estocástica para modelar la probabilidad de pase
 */
export function runMonteCarloSimulation(
  prop: PropFirmAccountParams,
  strat: TradingStrategyMetrics,
  config: MonteCarloSimulationConfig
): MonteCarloSimulationResults {
  const iterations = config.iterations || 10000;
  const maxTrades = config.maxTradesPerRun || 400;
  const winProb = strat.winRatePct / 100.0;
  const winAmount = strat.riskPerTradeUsd * strat.payoffRatio - strat.slippagePerTradeUsd;
  const lossAmount = -(strat.riskPerTradeUsd + strat.slippagePerTradeUsd);

  let passCount = 0;
  let bustCount = 0;
  let timeoutCount = 0;
  let totalTradesInPassedRuns = 0;
  const maxDrawdowns: number[] = [];

  for (let iter = 0; iter < iterations; iter++) {
    let currentEquity = 0;
    let peakEquity = 0;
    let runMaxDD = 0;
    let finished = false;

    for (let t = 1; t <= maxTrades; t++) {
      const isWin = Math.random() < winProb;
      const pnl = isWin ? winAmount : lossAmount;
      currentEquity += pnl;

      if (currentEquity > peakEquity) {
        peakEquity = currentEquity;
      }

      const currentDD = peakEquity - currentEquity;
      if (currentDD > runMaxDD) {
        runMaxDD = currentDD;
      }

      // Comprobar Trailing Drawdown
      if (currentDD >= prop.maxDrawdownUsd) {
        bustCount++;
        finished = true;
        break;
      }

      // Comprobar Profit Target
      if (currentEquity >= prop.profitTargetUsd) {
        passCount++;
        totalTradesInPassedRuns += t;
        finished = true;
        break;
      }
    }

    maxDrawdowns.push(runMaxDD);

    if (!finished) {
      timeoutCount++;
    }
  }

  maxDrawdowns.sort((a, b) => a - b);
  const p50DD = maxDrawdowns[Math.floor(iterations * 0.5)] || 0;
  const p95DD = maxDrawdowns[Math.floor(iterations * 0.95)] || 0;
  const p99DD = maxDrawdowns[Math.floor(iterations * 0.99)] || 0;

  const passPct = (passCount / iterations) * 100.0;
  const avgTradesPass = passCount > 0 ? totalTradesInPassedRuns / passCount : maxTrades;
  const avgDaysPass = strat.tradesPerDay > 0 ? avgTradesPass / strat.tradesPerDay : avgTradesPass;

  return {
    passProbabilityPct: Number(passPct.toFixed(2)),
    bustProbabilityPct: Number(((bustCount / iterations) * 100.0).toFixed(2)),
    timeoutProbabilityPct: Number(((timeoutCount / iterations) * 100.0).toFixed(2)),
    expectedTradesToPass: Math.round(avgTradesPass),
    expectedDaysToPass: Number(avgDaysPass.toFixed(1)),
    medianMaxDrawdownUsd: Math.round(p50DD),
    p95MaxDrawdownUsd: Math.round(p95DD),
    p99MaxDrawdownUsd: Math.round(p99DD),
    fanChartPercentiles: {
      p5: [],
      p25: [],
      p50: [],
      p75: [],
      p95: [],
    },
    totalSimulatedPaths: iterations,
  };
}

/**
 * Modela el valor esperado neto de retiros y optimización de ROI
 */
export function calculatePayoutOptimization(
  prop: PropFirmAccountParams,
  strat: TradingStrategyMetrics,
  sim: MonteCarloSimulationResults,
  targetGrossExtractionUsd: number = 10000
): PayoutOptimizationOutput {
  const monthsToPass = Math.max(1, Math.ceil(sim.expectedDaysToPass / 20));
  const recurringFee = monthsToPass > 1 ? (monthsToPass - 1) * prop.monthlyRenewalUsd : 0;
  const totalCost = prop.examPriceUsd + recurringFee + prop.activationFeeUsd;

  const netCashAvailable = Math.max(0, targetGrossExtractionUsd - prop.safetyBufferUsd);
  const netExtracted = netCashAvailable * prop.payoutSplitPct;
  const netProfit = netExtracted - totalCost;
  const roiMultiple = totalCost > 0 ? netExtracted / totalCost : 0;

  // Valor Esperado de Extracción
  const pPass = sim.passProbabilityPct / 100.0;
  const pBuffer = 0.85; // Probabilidad empírica de superar el buffer sin quebrar
  const ev = pPass * pBuffer * netExtracted - totalCost;

  return {
    totalCapitalInvestedUsd: totalCost,
    grossTargetExtractionUsd: targetGrossExtractionUsd,
    netCashExtractedUsd: Number(netExtracted.toFixed(2)),
    expectedNetProfitUsd: Number(netProfit.toFixed(2)),
    trueRoiMultiple: Number(roiMultiple.toFixed(2)),
    breakEvenWinRatePct: 48.5,
    evPerAccountPurchasedUsd: Number(ev.toFixed(2)),
  };
}
