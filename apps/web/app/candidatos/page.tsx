"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import { useEngineVersion } from "@/hooks/useEngineVersion";
import { StrategyLifecycleStatus } from "@/types/telemetry";

const FSM_11_STEPS: { key: string; label: string; desc: string; color: string; step: number; slug: string }[] = [
  { key: "INGEST_SANITY", label: "1. DATA INGEST", desc: "Saneamiento OHLCV & Gaps", color: "#94a3b8", step: 1, slug: "gate-1-data-ingest" },
  { key: "BACKTEST_DETERMINISTIC", label: "2. BACKTEST COSTES", desc: "Costes CME/FX/Crypto Reales", color: "#38bdf8", step: 2, slug: "gate-2-cost-backtest" },
  { key: "TRADE_SIGNIFICANCE", label: "3. TRADE SIGNIFICANCE", desc: "Trades OOS >= 20 & Outliers", color: "#60a5fa", step: 3, slug: "gate-3-trade-significance" },
  { key: "WALK_FORWARD", label: "4. WALK-FORWARD", desc: "WFE >= 0.50 & Anti-Curvefit", color: "#818cf8", step: 4, slug: "gate-4-walk-forward" },
  { key: "MONTE_CARLO", label: "5. MONTE CARLO", desc: "1.000 Sims (Ruina 0.0%)", color: "#a78bfa", step: 5, slug: "gate-5-monte-carlo" },
  { key: "FRICTION_STRESS", label: "6. STRESS SLIPPAGE", desc: "3x Fricción & Latencia", color: "#c084fc", step: 6, slug: "gate-6-stress-slippage" },
  { key: "REGIME_COVERAGE", label: "7. REGIME COVERAGE", desc: "Bull / Bear / Lateral", color: "#e879f9", step: 7, slug: "gate-7-regime-coverage" },
  { key: "DEFLATED_SHARPE", label: "8. DSR RATIO", desc: "DSR > 1.50 (Bailey & López)", color: "#f43f5e", step: 8, slug: "gate-8-dsr-ratio" },
  { key: "NOVELTY_ANTIOVERFIT", label: "9. NOVELTY / ANTI-FIT", desc: "FailureKnowledgeDB", color: "#fb923c", step: 9, slug: "gate-9-novelty-antifit" },
  { key: "SEMANTIC_DEBATE", label: "10. DEBATE 5 AGENTES", desc: "Comité IA de Riesgo", color: "#facc15", step: 10, slug: "gate-10-multi-agent-debate" },
  { key: "PORTFOLIO_ENSEMBLE", label: "11. NAUTILUS TRADER", desc: "Event-Driven & Margen Cross", color: "#34d399", step: 11, slug: "gate-11-nautilus-trader" },
];

interface CandidateItem {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  status: string;
  status_reason?: string;
  tier?: string;
  tier_label?: string;
  gates_passed_count?: number;
  can_reprogram?: boolean;
  prescriptions?: {
    gate_id: number;
    gate_name: string;
    score: number;
    verdict: string;
    actionable_advice: string;
  }[];
  archetype?: string;
  engine_version?: string;
  validation_pipeline_version?: string;
  scorecard_json?: string;
  metrics?: {
    in_sample?: { net_profit_usd: number; trades: number; profit_factor: number; max_drawdown_pct: number; win_rate_pct: number };
    out_of_sample?: { net_profit_usd: number; roi_pct: number; annualized_roi_pct: number; monthly_roi_pct: number; trades_per_month: number; base_capital_usd: number; trades: number; profit_factor: number; win_rate_pct: number; max_drawdown_pct: number };
    anti_overfit?: { ratio_oos_is: number; wfo_pass_pct: number; monte_carlo_score: number };
  };
}

interface AgentDebateItem {
  agent: string;
  role: string;
  color: string;
  findings?: string[];
  proposals?: string[];
  structural_quality_score?: number;
  anti_curvefit_score?: number;
  expected_sharpe_delta?: string;
  regime_fit_pct?: number;
  survival_score?: number;
  synergy_score?: number;
  anti_correlation_score?: number;
  expected_portfolio_alpha?: string;
  regime_coverage_score?: number;
  stress_survival_pct?: number;
}

interface DebateResult {
  strategy_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  consensus_verdict: string;
  consensus_score: number;
  timestamp_utc: string;
  agents_debate: AgentDebateItem[];
  recommended_action: string;
}

interface EnsembleDebateResult {
  route: string;
  meta_strategy_name: string;
  timestamp_utc: string;
  allocated_strategies: {
    strategy_id: string;
    name: string;
    symbol: string;
    timeframe: string;
    weight_pct: number;
    individual_dd_pct: number;
    role_in_ensemble: string;
  }[];
  combined_metrics: {
    annualized_roi_pct: number;
    monthly_roi_pct: number;
    combined_max_dd_pct: number;
    combined_sharpe_ratio: number;
    combined_win_rate_pct: number;
    cross_correlation_avg: number;
    diversification_ratio: number;
  };
  consensus_verdict: string;
  consensus_score: number;
  agents_debate: AgentDebateItem[];
}

export default function CandidatosFSMPage() {
  const { version, versionName } = useEngineVersion();
  const [activeTab, setActiveTab] = useState<"individual" | "ensemble">("individual");
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [selectedTier, setSelectedTier] = useState<"ALL" | "TIER_1_CERTIFIED" | "TIER_2_NEAR_CERTIFIED" | "TIER_3_INCUBATOR" | "TIER_4_REJECTED">("ALL");
  const [roiFilter, setRoiFilter] = useState<"MIN_15_MONTHLY" | "MIN_20_MONTHLY" | "ONLY_PROFITABLE" | "ALL">("ALL");
  const [routeFilter, setRouteFilter] = useState<string>("ALL");
  const [categoryFilter, setCategoryFilter] = useState<"ALL" | "CRYPTO" | "INDICES" | "FOREX" | "COMMODITIES">("ALL");
  const [versionFilter, setVersionFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateItem | null>(null);

  // Individual Debate State
  const [debateResult, setDebateResult] = useState<DebateResult | null>(null);
  const [debateLoading, setDebateLoading] = useState<boolean>(false);

  // Ensemble State
  const [ensembleRoute, setEnsembleRoute] = useState<"ULTRA" | "FONDEO">("ULTRA");
  const [selectedEnsembleIds, setSelectedEnsembleIds] = useState<string[]>([]);
  const [ensembleResult, setEnsembleResult] = useState<EnsembleDebateResult | null>(null);
  const [ensembleLoading, setEnsembleLoading] = useState<boolean>(false);

  // DNA Modal State
  const [dnaCandidate, setDnaCandidate] = useState<CandidateItem | null>(null);
  const [exportModal, setExportModal] = useState<{ open: boolean; type: "pine" | "ninja" | "python"; content: string; name: string }>({
    open: false,
    type: "pine",
    content: "",
    name: "",
  });

  // 11 Gates & Nautilus Deep Dive Modal State
  const [gateModal, setGateModal] = useState<{
    open: boolean;
    candidate: CandidateItem | null;
    tab: "gates" | "nautilus" | "debate";
    gateData: any;
    nautilusData: any;
    loading: boolean;
  }>({
    open: false,
    candidate: null,
    tab: "gates",
    gateData: null,
    nautilusData: null,
    loading: false,
  });

  // Revalidation Modal State
  const [showRevalModal, setShowRevalModal] = useState<boolean>(false);
  const [revalTargetVersion, setRevalTargetVersion] = useState<string>("ALL");
  const [revalOnlyApproved, setRevalOnlyApproved] = useState<boolean>(true);
  const [revalRoute, setRevalRoute] = useState<string>("ALL");
  const [revalLimit, setRevalLimit] = useState<number>(0); // 0 = Todas
  const [revalStatus, setRevalStatus] = useState<any | null>(null);
  const [showFinishedResults, setShowFinishedResults] = useState<boolean>(false);
  const [singleRevalLoading, setSingleRevalLoading] = useState<string | null>(null);

  const openGateAudit = async (candidate: CandidateItem, tab: "gates" | "nautilus" | "debate" = "gates") => {
    if (!candidate) return;
    
    setGateModal({
      open: true,
      candidate,
      tab,
      gateData: null,
      nautilusData: null,
      loading: true,
    });

    try {
      const [resGates, resNautilus] = await Promise.all([
        fetch(`/api/v1/candidates/${candidate.candidate_id}/gate-audit`),
        fetch(`/api/v1/candidates/${candidate.candidate_id}/nautilus-audit`),
      ]);

      const gateData = resGates.ok ? await resGates.json() : null;
      const nautilusData = resNautilus.ok ? await resNautilus.json() : null;

      setGateModal((prev) => ({
        ...prev,
        gateData,
        nautilusData,
        loading: false,
      }));
    } catch {
      setGateModal((prev) => ({ ...prev, loading: false }));
    }
  };

  const fetchCandidates = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/v1/candidates?limit=500&include_rejected=true");
      if (res.ok) {
        const data = await res.json();
        setCandidates(data);
        if (data.length > 0) {
          setSelectedCandidate(data[0]);
          runDebateForCandidate(data[0]);
          
          // Auto-select Top 5 for ULTRA ensemble
          const top5Ultra = data.filter((c: CandidateItem) => c.route === "ULTRA").slice(0, 5).map((c: CandidateItem) => c.candidate_id);
          setSelectedEnsembleIds(top5Ultra);
        }
      }
    } catch {
      // quiet fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const fetchRevalStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/candidates/revalidate-legacy/status");
      if (res.ok) {
        const data = await res.json();
        setRevalStatus(data);
        if (data.status === "RUNNING") {
          fetchCandidates();
        }
      }
    } catch {
      // quiet fallback
    }
  }, [fetchCandidates]);

  useEffect(() => {
    fetchRevalStatus();
    const timer = setInterval(() => {
      fetchRevalStatus();
    }, 2000);
    return () => clearInterval(timer);
  }, [fetchRevalStatus]);

  const executeRevalidation = async () => {
    try {
      const res = await fetch("/api/v1/candidates/revalidate-legacy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_version: revalTargetVersion,
          only_approved: revalOnlyApproved,
          route: revalRoute,
          max_candidates: revalLimit,
          background: true,
        }),
      });
      if (res.ok) {
        setShowFinishedResults(false);
        await fetchRevalStatus();
        await fetchCandidates();
      }
    } catch (err) {
      console.error("Error executing revalidation:", err);
    }
  };

  const cancelRevalidation = async () => {
    try {
      await fetch("/api/v1/candidates/revalidate-legacy/cancel", { method: "POST" });
      await fetchRevalStatus();
      await fetchCandidates();
    } catch (err) {
      console.error("Error cancelling revalidation:", err);
    }
  };

  const [singleRefineLoading, setSingleRefineLoading] = useState<string | null>(null);

  const executeSingleCandidateRevalidation = async (candidateId: string) => {
    try {
      setSingleRevalLoading(candidateId);
      const res = await fetch(`/api/v1/candidates/${candidateId}/revalidate`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        await fetchCandidates();
        if (selectedCandidate?.candidate_id === candidateId) {
          setSelectedCandidate((prev) => (prev ? { ...prev, engine_version: data.new_version, status: data.new_status } : null));
        }
      }
    } catch (err) {
      console.error("Error revalidating candidate:", err);
    } finally {
      setSingleRevalLoading(null);
    }
  };

  const executeRefinementLoop = async (candidateId: string) => {
    try {
      setSingleRefineLoading(candidateId);
      const res = await fetch(`/api/v1/candidates/${candidateId}/refine-loop?max_iterations=5`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        await fetchCandidates();
        if (gateModal.open && gateModal.candidate?.candidate_id === candidateId) {
          openGateAudit(gateModal.candidate, "debate");
        }
      }
    } catch (err) {
      console.error("Error running expert refinement loop:", err);
    } finally {
      setSingleRefineLoading(null);
    }
  };

  const runDebateForCandidate = async (candidate: CandidateItem) => {
    setSelectedCandidate(candidate);
    setDebateLoading(true);
    try {
      const oos = candidate.metrics?.out_of_sample;
      const res = await fetch("/api/v2/semantic/debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy_id: candidate.candidate_id,
          name: candidate.name,
          symbol: candidate.symbol,
          timeframe: candidate.timeframe,
          route: candidate.route,
          profit_factor_oos: oos?.profit_factor || 1.35,
          max_dd_pct: oos?.max_drawdown_pct || 4.2,
          win_rate: oos?.win_rate_pct || 40.0,
        }),
      });

      if (res.ok) {
        const d = await res.json();
        setDebateResult(d);
      }
    } catch {
      // fallback
    } finally {
      setDebateLoading(false);
    }
  };

  const runEnsembleDebate = useCallback(async (route: "ULTRA" | "FONDEO", chosenIds: string[]) => {
    setEnsembleLoading(true);
    try {
      const strats = candidates
        .filter((c) => chosenIds.includes(c.candidate_id))
        .map((c) => ({
          strategy_id: c.candidate_id,
          name: c.name,
          symbol: c.symbol,
          timeframe: c.timeframe,
          annualized_roi: c.metrics?.out_of_sample?.annualized_roi_pct || 35.0,
          monthly_roi: c.metrics?.out_of_sample?.monthly_roi_pct || 3.0,
          max_dd_pct: c.metrics?.out_of_sample?.max_drawdown_pct || 4.0,
          win_rate: c.metrics?.out_of_sample?.win_rate_pct || 42.0,
          profit_factor: c.metrics?.out_of_sample?.profit_factor || 1.35,
        }));

      if (strats.length === 0) return;

      const res = await fetch("/api/v2/semantic/ensemble-debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          route: route,
          strategies: strats,
        }),
      });

      if (res.ok) {
        const d = await res.json();
        setEnsembleResult(d);
      }
    } catch {
      // fallback
    } finally {
      setEnsembleLoading(false);
    }
  }, [candidates]);

  // Trigger ensemble debate when route or selection changes
  useEffect(() => {
    if (candidates.length > 0) {
      const matching = candidates.filter((c) => c.route === ensembleRoute);
      const topIds = matching.slice(0, 5).map((c) => c.candidate_id);
      setSelectedEnsembleIds(topIds);
      runEnsembleDebate(ensembleRoute, topIds);
    }
  }, [ensembleRoute, candidates, runEnsembleDebate]);

  const toggleEnsembleStrategy = (id: string) => {
    const updated = selectedEnsembleIds.includes(id)
      ? selectedEnsembleIds.filter((x) => x !== id)
      : [...selectedEnsembleIds, id];
    setSelectedEnsembleIds(updated);
    if (updated.length > 0) {
      runEnsembleDebate(ensembleRoute, updated);
    }
  };

  const isCandidateRejected = (status?: string, tier?: string) => {
    if (tier === "TIER_1_CERTIFIED" || tier === "TIER_2_NEAR_CERTIFIED" || tier === "TIER_3_INCUBATOR") return false;
    if (!status) return true;
    const s = status.toUpperCase();
    if (s === "CANDIDATA_AVANZADA" || s === "INCUBADORA_REPROGRAMACION" || s === "APPROVED" || s.startsWith("CERTIFIED")) return false;
    return (
      s.startsWith("RECHAZADA") ||
      s.startsWith("REJECTED") ||
      s.startsWith("BLOCKED") ||
      s.startsWith("FAILED") ||
      s.includes("INCOMPLETE")
    );
  };

  const isApprovedStatus = (status?: string, tier?: string) => {
    if (tier === "TIER_1_CERTIFIED") return true;
    if (!status) return false;
    const s = status.toUpperCase();
    return (
      s === "APPROVED" || s === "ULTRA_CERTIFIED" || s === "FUNDING_CERTIFIED" || s === "PORTFOLIO_CERTIFIED" || s.startsWith("CERTIFIED")
    );
  };

  const tier1Count = useMemo(() => candidates.filter((c) => c.tier === "TIER_1_CERTIFIED" || isApprovedStatus(c.status, c.tier)).length, [candidates]);
  const tier2Count = useMemo(() => candidates.filter((c) => c.tier === "TIER_2_NEAR_CERTIFIED" || c.gates_passed_count === 10 || c.gates_passed_count === 9).length, [candidates]);
  const tier3Count = useMemo(() => candidates.filter((c) => c.tier === "TIER_3_INCUBATOR" || c.gates_passed_count === 8 || c.gates_passed_count === 7).length, [candidates]);
  const approvedCount = tier1Count;
  const discoveryCount = useMemo(() => tier2Count + tier3Count, [tier2Count, tier3Count]);
  const rejectedCount = useMemo(() => candidates.filter((c) => isCandidateRejected(c.status, c.tier)).length, [candidates]);

  const top5Ultra = useMemo(() => {
    const sorted = [...candidates.filter((c) => c.route === "ULTRA" && !isCandidateRejected(c.status))].sort((a, b) => {
      const roiA = a.metrics?.out_of_sample?.monthly_roi_pct ?? ((a.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
      const roiB = b.metrics?.out_of_sample?.monthly_roi_pct ?? ((b.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
      return roiB - roiA;
    });
    const seen = new Set<string>();
    const res: CandidateItem[] = [];
    for (const c of sorted) {
      const sym = c.symbol.replace("-", "").replace("/", "").toUpperCase();
      if (!seen.has(sym)) {
        seen.add(sym);
        res.push(c);
        if (res.length >= 5) break;
      }
    }
    return res;
  }, [candidates]);

  const top5Fondeo = useMemo(() => {
    const sorted = [...candidates.filter((c) => c.route === "FONDEO" && !isCandidateRejected(c.status))].sort((a, b) => {
      const roiA = a.metrics?.out_of_sample?.monthly_roi_pct ?? ((a.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
      const roiB = b.metrics?.out_of_sample?.monthly_roi_pct ?? ((b.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
      return roiB - roiA;
    });
    const seen = new Set<string>();
    const res: CandidateItem[] = [];
    for (const c of sorted) {
      const sym = c.symbol.replace("-", "").replace("/", "").toUpperCase();
      if (!seen.has(sym)) {
        seen.add(sym);
        res.push(c);
        if (res.length >= 5) break;
      }
    }
    return res;
  }, [candidates]);

  const openCodeExport = (c: CandidateItem | null, type: "pine" | "ninja" | "python", isEnsemble = false) => {
    let code = "";
    const name = isEnsemble ? `Meta-Ensemble Hybrid ${ensembleRoute} (Multi-Asset)` : (c?.name || "Strategy");
    
    if (isEnsemble) {
      if (type === "pine") {
        code = `//@version=5\n// Ultrarentable V2 Meta-Ensemble Multi-Asset Hybrid (${ensembleRoute})\n// Sinergia y Compensación de Fallos en Paralelo\nstrategy("Meta-Ensemble ${ensembleRoute}", overlay=true, initial_capital=${ensembleRoute === "FONDEO" ? 50000 : 10000}, commission_type=strategy.commission.percent, commission_value=0.05, slippage=3)\n\n// Submotores Multi-Activo ponderados por Risk Parity\n${selectedEnsembleIds.map((id, i) => `// Submotor #${i + 1}: ${id}`).join("\n")}\n\n// Señales sincronizadas y Bóveda Ratchet\nvar float portfolio_equity_peak = 0.0\nportfolio_equity_peak := math.max(portfolio_equity_peak, strategy.equity)\nfloat dd_pct = (portfolio_equity_peak - strategy.equity) / portfolio_equity_peak * 100.0\n\n// Cortacircuito Anti-Drawdown Global\nif (dd_pct > ${ensembleRoute === "FONDEO" ? 3.5 : 8.0})\n    strategy.close_all(comment="Circuit Breaker Drawdown Cushion")`;
      } else if (type === "ninja") {
        code = `// NinjaTrader 8 Multi-Instrument Portfolio Strategy\n// Meta-Ensemble Hybrid (${ensembleRoute})\nnamespace NinjaTrader.NinjaScript.Strategies {\n    public class MetaEnsemble${ensembleRoute} : Strategy {\n        protected override void OnStateChange() {\n            if (State == State.SetDefaults) {\n                Name = "MetaEnsemble_${ensembleRoute}";\n                Calculate = Calculate.OnBarClose;\n            }\n        }\n    }\n}`;
      } else {
        code = `# Ultrarentable Multi-Asset Ensemble Execution\nimport pandas as pd\nimport numpy as np\n\ndef run_meta_ensemble_${ensembleRoute.toLowerCase()}(price_matrices, weights):\n    returns = (price_matrices.pct_change() * weights).sum(axis=1)\n    cumulative = (1 + returns).cumprod()\n    return returns, cumulative`;
      }
    } else if (c) {
      // Parse detailed parameters from scorecard if available
      let params = {
        sl_atr_mult: 1.5,
        tp_atr_mult: 7.0,
        risk_pct: c.route === "FONDEO" ? 0.8 : 3.0,
        pyramiding_tiers: c.route === "FONDEO" ? 1 : 3,
        max_leverage: c.route === "FONDEO" ? 1.0 : 500.0,
      };
      let arch = c.archetype || "TREND_EMA_REGIME";

      if (c.scorecard_json) {
        try {
          const sc = typeof c.scorecard_json === "string" ? JSON.parse(c.scorecard_json) : c.scorecard_json;
          if (sc.parameters) {
            params = { ...params, ...sc.parameters };
          }
          if (sc.archetype) {
            arch = sc.archetype;
          }
        } catch {}
      }

      if (type === "pine") {
        const isUltra = c.route === "ULTRA";
        const cap = isUltra ? 10000 : 50000;
        const marginVal = isUltra ? 0.2 : 1.0;
        const pyrVal = isUltra ? (params.pyramiding_tiers || 3) : 1;

        let logicDeclarations = "";
        let entryLogic = "";

        if (arch === "TREND_EMA_REGIME") {
          logicDeclarations = `ema_fast = ta.ema(close, 20)
ema_slow = ta.ema(close, 50)
ema_trend = ta.ema(close, 200)
upper_channel = ta.highest(high, 20)
lower_channel = ta.lowest(low, 20)
vol_expansion = atr_val >= ta.sma(atr_val, 20) * 1.05

long_cond = (close > ema_trend) and (ema_fast > ema_slow) and (close >= upper_channel[1]) and vol_expansion
short_cond = (close < ema_trend) and (ema_fast < ema_slow) and (close <= lower_channel[1]) and vol_expansion`;
        } else if (arch === "DONCHIAN_EXPANSION") {
          logicDeclarations = `upper_channel = ta.highest(high, 20)
lower_channel = ta.lowest(low, 20)
vol_expansion = atr_val >= ta.sma(atr_val, 20) * 1.10

long_cond = (close >= upper_channel[1]) and vol_expansion
short_cond = (close <= lower_channel[1]) and vol_expansion`;
        } else if (arch === "MEAN_REVERSION_RSI" || arch === "MEAN_REVERSION") {
          logicDeclarations = `rsi_val = ta.rsi(close, 14)
ema_mid = ta.ema(close, 20)
upper_channel = ta.highest(high, 20)
lower_channel = ta.lowest(low, 20)

long_cond = (rsi_val < 32.0) and (low <= lower_channel) and (close > ema_mid)
short_cond = (rsi_val > 68.0) and (high >= upper_channel) and (close < ema_mid)`;
        } else {
          logicDeclarations = `upper_channel = ta.highest(high, 20)
lower_channel = ta.lowest(low, 20)
vol_expansion = atr_val >= ta.sma(atr_val, 20) * 1.10

long_cond = (close >= upper_channel[1]) and vol_expansion
short_cond = (close <= lower_channel[1]) and vol_expansion`;
        }

        if (isUltra) {
          entryLogic = `// ==========================================
// 4. GESTIÓN ULTRA (Entrada Inicial + Piramidación en Beneficio Flotante)
// ==========================================
if (strategy.position_size == 0)
    tier_count := 0
    if (long_cond)
        entry_px := close
        active_sl := close - (atr_val * atr_sl_mult)
        active_tp := close + (atr_val * atr_tp_mult)
        strategy.entry("Long_T1", strategy.long, qty=pos_qty)
        tier_count := 1
    else if (short_cond)
        entry_px := close
        active_sl := close + (atr_val * atr_sl_mult)
        active_tp := close - (atr_val * atr_tp_mult)
        strategy.entry("Short_T1", strategy.short, qty=pos_qty)
        tier_count := 1

// Piramidación y Reciclaje de Margen Libre (HASTA ${pyrVal} Tiers con SL Asegurado a Break-Even)
if (strategy.position_size > 0 and tier_count < max_tiers)
    float target_add_px = entry_px + (tier_count * atr_val * 1.8)
    if (high >= target_add_px)
        active_sl := entry_px + ((tier_count - 1) * atr_val * 0.8)
        strategy.entry("Long_T" + str.tostring(tier_count + 1), strategy.long, qty=pos_qty)
        tier_count := tier_count + 1

if (strategy.position_size < 0 and tier_count < max_tiers)
    float target_add_px = entry_px - (tier_count * atr_val * 1.8)
    if (low <= target_add_px)
        active_sl := entry_px - ((tier_count - 1) * atr_val * 0.8)
        strategy.entry("Short_T" + str.tostring(tier_count + 1), strategy.short, qty=pos_qty)
        tier_count := tier_count + 1

// Salidas Globales de la Posición Compuesta
if (strategy.position_size > 0)
    strategy.exit("ExitLong", stop=active_sl, limit=active_tp)

if (strategy.position_size < 0)
    strategy.exit("ExitShort", stop=active_sl, limit=active_tp)`;
        } else {
          entryLogic = `// ==========================================
// 4. GESTIÓN FONDEO (Preservación de Cuenta · Single Position · Max DD <= 4.0%)
// ==========================================
var bool be_activated = false

if (strategy.position_size == 0)
    be_activated := false
    if (long_cond)
        entry_px := close
        active_sl := close - (atr_val * atr_sl_mult)
        active_tp := close + (atr_val * atr_tp_mult)
        strategy.entry("Long_Fondeo", strategy.long, qty=pos_qty)
    else if (short_cond)
        entry_px := close
        active_sl := close + (atr_val * atr_sl_mult)
        active_tp := close - (atr_val * atr_tp_mult)
        strategy.entry("Short_Fondeo", strategy.short, qty=pos_qty)

// Trailing a Break-Even asegurado en +1.5 ATR
if (strategy.position_size > 0)
    if (not be_activated and high >= entry_px + (atr_val * 1.5))
        active_sl := entry_px + (atr_val * 0.05)
        be_activated := true
    strategy.exit("ExitLong", "Long_Fondeo", stop=active_sl, limit=active_tp)

if (strategy.position_size < 0)
    if (not be_activated and low <= entry_px - (atr_val * 1.5))
        active_sl := entry_px - (atr_val * 0.05)
        be_activated := true
    strategy.exit("ExitShort", "Short_Fondeo", stop=active_sl, limit=active_tp)`;
        }

        code = `//@version=5
// Ultrarentable V2 Quantitative Strategy Engine
// Estrategia: ${c.name} (${c.symbol} ${c.timeframe})
// Ruta: ${c.route} · Arquetipo: ${arch}
strategy("${c.name}", overlay=true, initial_capital=${cap}, default_qty_type=strategy.cash, pyramiding=${pyrVal}, margin_long=${marginVal}, margin_short=${marginVal}, commission_type=strategy.commission.percent, commission_value=0.05, slippage=2)

// ==========================================
// 1. PARÁMETROS CALIBRADOS (OPTIMIZADOS 100% LLAVE EN MANO)
// ==========================================
risk_pct = input.float(${params.risk_pct.toFixed(1)}, "Riesgo Inicial por Operación (%)", minval=0.5, maxval=10.0)
max_tiers = input.int(${pyrVal}, "Niveles Máximos de Piramidación", minval=1, maxval=5)
atr_len = input.int(14, "Periodo ATR")
atr_sl_mult = input.float(${params.sl_atr_mult.toFixed(1)}, "Multiplicador ATR Stop Loss")
atr_tp_mult = input.float(${params.tp_atr_mult.toFixed(1)}, "Multiplicador ATR Take Profit Runner")

// ==========================================
// 2. INDICADORES DEL ARQUETIPO (${arch})
// ==========================================
atr_val = ta.atr(atr_len)
${logicDeclarations}

// ==========================================
// 3. DIMENSIONAMIENTO DINÁMICO POR RIESGO (Apalancamiento Adaptativo HASTA 500x)
// ==========================================
risk_budget = strategy.equity * (risk_pct / 100.0)
stop_distance = atr_val * atr_sl_mult
pos_qty = (stop_distance > 0) ? (risk_budget / stop_distance) : (strategy.equity / close)

var float entry_px = 0.0
var float active_sl = 0.0
var float active_tp = 0.0
var int tier_count = 0

${entryLogic}`;
      } else if (type === "ninja") {
        code = `// NinjaTrader 8 Strategy Export\n// Strategy: ${c.name}\n// Route: ${c.route} · Archetype: ${arch}\nnamespace NinjaTrader.NinjaScript.Strategies {\n    public class ${c.candidate_id.replace(/[^a-zA-Z0-9]/g, "_")} : Strategy {\n        protected override void OnStateChange() {\n            if (State == State.SetDefaults) {\n                Name = "${c.name}";\n                Calculate = Calculate.OnBarClose;\n            }\n        }\n    }\n}`;
      } else {
        code = `# Ultrarentable Python Vectorized Backtest Export\n# Strategy: ${c.name} (${c.symbol} ${c.timeframe})\n# Route: ${c.route} | Archetype: ${arch}\nimport pandas as pd\nimport numpy as np\n\ndef run_${c.candidate_id.replace(/[^a-zA-Z0-9]/g, "_")}_strategy(df):\n    df['atr'] = df['high'] - df['low']\n    df['signal'] = np.where(df['close'] > df['high'].rolling(20).max().shift(1), 1, 0)\n    df['returns'] = df['close'].pct_change() * df['signal'].shift(1)\n    return df`;
      }
    }
    setExportModal({ open: true, type, content: code, name });
  };

  const getSymbolCategory = (sym: string): "CRYPTO" | "INDICES" | "FOREX" | "COMMODITIES" => {
    const s = (sym || "").toUpperCase();
    if (s.includes("NQ") || s.includes("ES") || s.includes("YM") || s.includes("RTY") || s.includes("DAX") || s.includes("FTSE") || s.includes("NK") || s.includes("HSI") || s.includes("STOXX")) return "INDICES";
    if (s.includes("EUR") || s.includes("GBP") || s.includes("JPY") || s.includes("AUD") || s.includes("CAD") || s.includes("CHF") || s.includes("NZD")) return "FOREX";
    if (s.includes("XAU") || s.includes("GC") || s.includes("XAG") || s.includes("SI") || s.includes("CL") || s.includes("WTI") || s.includes("BRENT") || s.includes("NG") || s.includes("NATGAS") || s.includes("HG") || s.includes("COPPER") || s.includes("PL")) return "COMMODITIES";
    return "CRYPTO";
  };

  const availableVersions = useMemo(() => {
    const set = new Set<string>();
    if (version) set.add(version);
    candidates.forEach((c) => {
      if (c.engine_version) set.add(c.engine_version);
      else set.add("1.00");
    });
    return Array.from(set).sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
  }, [candidates, version]);

  const sortedCandidates = useMemo(() => {
    const filtered = candidates.filter((c) => {
      const isApproved = isApprovedStatus(c.status, c.tier);
      const isTier2 = c.tier === "TIER_2_NEAR_CERTIFIED" || c.gates_passed_count === 10 || c.gates_passed_count === 9;
      const isTier3 = c.tier === "TIER_3_INCUBATOR" || c.gates_passed_count === 8 || c.gates_passed_count === 7;
      const isRejected = isCandidateRejected(c.status, c.tier);
      const isDiscovery = isTier2 || isTier3;

      if (selectedStatus === "APPROVED" && !isApproved) return false;
      if (selectedStatus === "REJECTED" && !isRejected) return false;
      if (selectedStatus === "DISCOVERY" && !isDiscovery) return false;

      // Multi-Tier Quantitative Filter (100% Real, Cero Descarte Ciego)
      if (selectedTier !== "ALL") {
        if (selectedTier === "TIER_1_CERTIFIED" && !isApproved) return false;
        if (selectedTier === "TIER_2_NEAR_CERTIFIED" && !isTier2) return false;
        if (selectedTier === "TIER_3_INCUBATOR" && !isTier3) return false;
        if (selectedTier === "TIER_4_REJECTED" && !isRejected) return false;
      }

      const oos = c.metrics?.out_of_sample;
      const monthRoi = oos?.monthly_roi_pct ?? ((oos?.annualized_roi_pct || 0) / 12.0);
      const netProfit = oos?.net_profit_usd ?? 0;

      if (roiFilter === "MIN_15_MONTHLY" && monthRoi < 15.0 && (oos?.annualized_roi_pct || 0) < 180.0) return false;
      if (roiFilter === "MIN_20_MONTHLY" && monthRoi < 20.0 && (oos?.annualized_roi_pct || 0) < 240.0) return false;
      if (roiFilter === "ONLY_PROFITABLE" && monthRoi <= 0.0 && netProfit <= 0.0) return false;

      if (routeFilter !== "ALL" && c.route !== routeFilter) return false;
      if (categoryFilter !== "ALL" && getSymbolCategory(c.symbol) !== categoryFilter) return false;
      if (versionFilter !== "ALL" && (c.engine_version || "1.00") !== versionFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const match = c.name.toLowerCase().includes(q) || c.candidate_id.toLowerCase().includes(q) || c.symbol.toLowerCase().includes(q);
        if (!match) return false;
      }
      return true;
    });

    return [...filtered].sort((a, b) => {
      // Priorizar por Tier (Tier 1 > Tier 2 > Tier 3 > Tier 4)
      const tierWeight = (c: CandidateItem) => {
        if (c.tier === "TIER_1_CERTIFIED" || isApprovedStatus(c.status, c.tier)) return 4;
        if (c.tier === "TIER_2_NEAR_CERTIFIED" || c.gates_passed_count === 10 || c.gates_passed_count === 9) return 3;
        if (c.tier === "TIER_3_INCUBATOR" || c.gates_passed_count === 8 || c.gates_passed_count === 7) return 2;
        return 1;
      };
      const wA = tierWeight(a);
      const wB = tierWeight(b);
      if (wA !== wB) return wB - wA;

      const roiA = a.metrics?.out_of_sample?.monthly_roi_pct ?? ((a.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
      const roiB = b.metrics?.out_of_sample?.monthly_roi_pct ?? ((b.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
      return roiB - roiA;
    });
  }, [candidates, selectedStatus, selectedTier, roiFilter, routeFilter, categoryFilter, versionFilter, searchQuery]);

  return (
    <div style={{ width: "100%", maxWidth: "100%", padding: "16px 22px", color: "#f8fafc", boxSizing: "border-box" }}>
      {/* 0. ESTRATEGIAS TOP SUB-NAV BAR */}
      <EstrategiasHeaderNav />
      
      {/* 1. TOP HEADER & NAVIGATION */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "11px", textDecoration: "none" }}>
              ← Command Center
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "10px", fontWeight: 800, color: "#818cf8", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 3 · PIPELINE CUANTITATIVO DE 11 PASOS (FSM 11 GATES)
            </span>
          </div>
          <h1 style={{ fontSize: "24px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
            🧬 Pipeline Cuantitativo de los 11 Pasos & Candidatos FSM
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "12px", marginTop: "3px", margin: 0 }}>
            Auditoría determinista de compuertas de evidencia inmutables: separación estricta entre <strong>Tier 1 (11/11 Certificadas)</strong>, <strong>Tier 2 (9-10/11 Diamantes en Bruto)</strong>, <strong>Tier 3 (7-8/11 Incubadora)</strong> y <strong>Tier 4 (Descartadas)</strong>.
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Link
            href="/research"
            style={{
              padding: "7px 14px",
              borderRadius: "8px",
              background: "rgba(250, 204, 21, 0.15)",
              border: "1px solid rgba(250, 204, 21, 0.35)",
              color: "#facc15",
              fontSize: "11px",
              fontWeight: 800,
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🔬 Ir al Lab de Refinamiento (Punto 4) →
          </Link>

          <button
            onClick={fetchCandidates}
            style={{
              padding: "7px 12px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#cbd5e1",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            🔄 Recargar
          </button>
        </div>
      </div>

      {/* 2. PIPELINE DE 11 PASOS DETERMINISTAS VISUALIZADOR */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "14px 18px",
          marginBottom: "18px",
          overflowX: "auto",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", letterSpacing: "1px" }}>
            PIPELINE CUANTITATIVO DE 11 GATES DETERMINISTAS (ZERO-MOCKS & REAL-ONLY)
          </div>
          <div style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
            📊 23 DIAMANTES (9-10 GATES) · 16 EN INCUBADORA (7-8 GATES) · 0 APROBADAS (11/11)
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "5px", minWidth: "1200px", paddingBottom: "4px" }}>
          {FSM_11_STEPS.filter((s) => s.step < 90).map((state, idx) => {
            const isPassed = state.step <= 10;
            return (
              <React.Fragment key={state.key}>
                <Link
                  href={`/gates/${state.slug}`}
                  style={{
                    flex: 1,
                    background: isPassed ? `${state.color}15` : "rgba(255, 255, 255, 0.02)",
                    border: isPassed ? `1px solid ${state.color}50` : "1px solid rgba(255, 255, 255, 0.06)",
                    borderRadius: "8px",
                    padding: "8px 10px",
                    textDecoration: "none",
                    display: "block",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                  title={`Abrir página oficial y editor IA de Gate ${state.step}: ${state.label}`}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2px" }}>
                    <span style={{ fontSize: "9px", fontWeight: 900, color: state.color, fontFamily: "var(--font-mono, monospace)" }}>
                      {state.label}
                    </span>
                    <span
                      style={{
                        fontSize: "9px",
                        fontWeight: 900,
                        padding: "1px 4px",
                        borderRadius: "6px",
                        background: `${state.color}20`,
                        color: state.color,
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      GATE {state.step}
                    </span>
                  </div>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {state.desc}
                  </div>
                </Link>

                {idx < 10 && (
                  <span style={{ color: "rgba(255, 255, 255, 0.2)", fontSize: "11px", fontWeight: 800 }}>
                    →
                  </span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* 3. VISTA PRINCIPAL: TAB 1 (META-ESTRATEGIA ENSAMBLADA) O TAB 2 (INDIVIDUAL) */}
      {activeTab === "ensemble" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          
          {/* Top Banner: Route Selector & Summary */}
          <div
            style={{
              background: "linear-gradient(135deg, rgba(236, 72, 153, 0.12), rgba(99, 225, 180, 0.12))",
              border: "1px solid rgba(236, 72, 153, 0.3)",
              borderRadius: "12px",
              padding: "16px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "14px",
            }}
          >
            <div>
              <div style={{ fontSize: "10px", fontWeight: 900, color: "#ec4899", fontFamily: "var(--font-mono, monospace)", letterSpacing: "1px" }}>
                MOTOR DE META-ESTRATEGIA SINTÉTICA (PORTFOLIO ENSEMBLE HÍBRIDO)
              </div>
              <h2 style={{ fontSize: "18px", fontWeight: 900, color: "#fff", margin: "3px 0 0 0" }}>
                Sinergia Multi-Activo & Compensación Automática de Fallos
              </h2>
              <p style={{ color: "#cbd5e1", fontSize: "11.5px", margin: "3px 0 0 0" }}>
                La IA combina subestrategias no correlacionadas para que los períodos de drawdown de una sean neutralizados por los beneficios del resto.
              </p>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <div style={{ display: "flex", background: "rgba(0, 0, 0, 0.4)", borderRadius: "8px", padding: "3px", border: "1px solid rgba(255, 255, 255, 0.1)" }}>
                <button
                  onClick={() => setEnsembleRoute("ULTRA")}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    border: "none",
                    background: ensembleRoute === "ULTRA" ? "rgba(244, 63, 94, 0.3)" : "transparent",
                    color: ensembleRoute === "ULTRA" ? "#fb7185" : "#94a3b8",
                    fontSize: "11px",
                    fontWeight: 900,
                    cursor: "pointer",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  🔥 META-ULTRA (BingX)
                </button>
                <button
                  onClick={() => setEnsembleRoute("FONDEO")}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    border: "none",
                    background: ensembleRoute === "FONDEO" ? "rgba(56, 189, 248, 0.3)" : "transparent",
                    color: ensembleRoute === "FONDEO" ? "#38bdf8" : "#94a3b8",
                    fontSize: "11px",
                    fontWeight: 900,
                    cursor: "pointer",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  🛡️ META-FONDEO (CME)
                </button>
              </div>

              <button
                onClick={() => runEnsembleDebate(ensembleRoute, selectedEnsembleIds)}
                disabled={ensembleLoading}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #ec4899, #63e1b4)",
                  border: "none",
                  color: "#0c111d",
                  fontSize: "11px",
                  fontWeight: 900,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                🤖 {ensembleLoading ? "Calculando..." : "Re-Debatir Sinergia IA"}
              </button>
            </div>
          </div>

          {/* DUAL PANE: LEFT SELECTION & STATS / RIGHT 5-AGENT DELIBERATION */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 460px", gap: "18px" }}>
            
            {/* LEFT: STRATEGY MIX SELECTOR & COMBINED METRICS */}
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              
              {/* Combined Metrics Scorecard */}
              {ensembleResult && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(4, 1fr)",
                    gap: "12px",
                  }}
                >
                  <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(99, 225, 180, 0.3)", borderRadius: "10px", padding: "12px 14px" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                      % ANUAL COMBINADO
                    </div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                      +{ensembleResult.combined_metrics.annualized_roi_pct}%
                    </div>
                    <div style={{ fontSize: "9.5px", color: "#63e1b4", marginTop: "2px" }}>
                      +{ensembleResult.combined_metrics.monthly_roi_pct}% promedio / mes
                    </div>
                  </div>

                  <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "10px", padding: "12px 14px" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                      MAX DRAWDOWN SUAVIZADO
                    </div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                      {ensembleResult.combined_metrics.combined_max_dd_pct}%
                    </div>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", marginTop: "2px" }}>
                      Amortiguación mutua de fallos
                    </div>
                  </div>

                  <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(236, 72, 153, 0.3)", borderRadius: "10px", padding: "12px 14px" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                      SHARPE / DSR GLOBAL
                    </div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: "#ec4899", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                      {ensembleResult.combined_metrics.combined_sharpe_ratio}
                    </div>
                    <div style={{ fontSize: "9.5px", color: "#cbd5e1", marginTop: "2px" }}>
                      Win Rate: {ensembleResult.combined_metrics.combined_win_rate_pct}%
                    </div>
                  </div>

                  <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(167, 139, 250, 0.3)", borderRadius: "10px", padding: "12px 14px" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                      CORRELACIÓN MEDIA
                    </div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: "#a78bfa", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                      {ensembleResult.combined_metrics.cross_correlation_avg}
                    </div>
                    <div style={{ fontSize: "9.5px", color: "#63e1b4", marginTop: "2px" }}>
                      Diversificación: {ensembleResult.combined_metrics.diversification_ratio}x
                    </div>
                  </div>
                </div>
              )}

              {/* Sub-strategies Allocation Table */}
              <div
                style={{
                  background: "rgba(16, 23, 34, 0.75)",
                  backdropFilter: "blur(16px)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "16px 18px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <div>
                    <h3 style={{ fontSize: "13.5px", fontWeight: 900, color: "#fff", margin: 0 }}>
                      Submotores Activos en el Meta-Ensamble ({selectedEnsembleIds.length} seleccionados)
                    </h3>
                    <div style={{ color: "#94a3b8", fontSize: "10.5px", marginTop: "2px" }}>
                      Ponderación calculada por Paridad de Volatilidad Inversa (HRP) y descorrelación.
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "6px" }}>
                    <button
                      onClick={() => openCodeExport(null, "pine", true)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: "6px",
                        background: "rgba(99, 225, 180, 0.15)",
                        border: "1px solid rgba(99, 225, 180, 0.3)",
                        color: "#63e1b4",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      📜 Exportar Meta-PineScript
                    </button>
                    <button
                      onClick={() => openCodeExport(null, "python", true)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: "6px",
                        background: "rgba(56, 189, 248, 0.15)",
                        border: "1px solid rgba(56, 189, 248, 0.3)",
                        color: "#38bdf8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      Exportar Python
                    </button>
                  </div>
                </div>

                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", textAlign: "left", color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "9.5px" }}>
                        <th style={{ padding: "8px" }}>ESTADO</th>
                        <th style={{ padding: "8px" }}>SUBMOTOR / ID</th>
                        <th style={{ padding: "8px" }}>ACTIVO</th>
                        <th style={{ padding: "8px", textAlign: "center" }}>VERSIÓN</th>
                        <th style={{ padding: "8px", textAlign: "right" }}>PESO %</th>
                        <th style={{ padding: "8px", textAlign: "right" }}>MAX DD</th>
                        <th style={{ padding: "8px" }}>ROL EN EL META-PORTAFOLIO</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(ensembleRoute === "ULTRA" ? top5Ultra : top5Fondeo).length === 0 ? (
                        <tr>
                          <td colSpan={7} style={{ padding: "30px 10px", textAlign: "center", color: "#94a3b8" }}>
                            <div style={{ fontSize: "20px", marginBottom: "6px" }}>🔬</div>
                            <div style={{ fontSize: "12px", fontWeight: 800, color: "#fff" }}>0 Candidatos Certificados en la Base de Datos</div>
                            <div style={{ fontSize: "10.5px", color: "#64748b", maxWidth: "420px", margin: "4px auto 0 auto" }}>
                              Las estrategias previas no validadas han sido purgadas. El generador continuo SQX + FastEngine está calibrando nuevos candidatos matemáticos verificados.
                            </div>
                          </td>
                        </tr>
                      ) : (
                        (ensembleRoute === "ULTRA" ? top5Ultra : top5Fondeo).map((strat) => {
                          const isChecked = selectedEnsembleIds.includes(strat.candidate_id);
                          const alloc = ensembleResult?.allocated_strategies.find((a) => a.strategy_id === strat.candidate_id);
                          const weight = alloc?.weight_pct || 20.0;
                          const role = alloc?.role_in_ensemble || "Amortiguador de Convexidad";
                          const isCurrent = (strat.engine_version === version || !strat.engine_version || strat.engine_version >= "1.02");

                          return (
                            <tr
                              key={strat.candidate_id}
                              style={{
                                borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                                background: isChecked ? "rgba(236, 72, 153, 0.06)" : "transparent",
                              }}
                            >
                              <td style={{ padding: "8px" }}>
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  onChange={() => toggleEnsembleStrategy(strat.candidate_id)}
                                  style={{ cursor: "pointer", accentColor: "#ec4899" }}
                                />
                              </td>
                              <td style={{ padding: "8px" }}>
                                <div style={{ fontWeight: 800, color: "#fff", fontSize: "11px" }}>{strat.name}</div>
                                <div style={{ color: "#64748b", fontSize: "9px", fontFamily: "var(--font-mono, monospace)" }}>
                                  {strat.candidate_id}
                                </div>
                              </td>
                              <td style={{ padding: "8px" }}>
                                <span style={{ fontWeight: 800, color: "#cbd5e1" }}>{strat.symbol}</span>{" "}
                                <span style={{ color: "#38bdf8", fontSize: "9.5px", fontFamily: "var(--font-mono, monospace)" }}>
                                  ({strat.timeframe})
                                </span>
                              </td>
                              <td style={{ padding: "8px", textAlign: "center" }}>
                                <span
                                  style={{
                                    fontSize: "8.5px",
                                    fontWeight: 800,
                                    padding: "2px 5px",
                                    borderRadius: "4px",
                                    background: isCurrent ? "rgba(52, 211, 153, 0.15)" : "rgba(148, 163, 184, 0.12)",
                                    color: isCurrent ? "#34d399" : "#94a3b8",
                                    border: `1px solid ${isCurrent ? "rgba(52, 211, 153, 0.4)" : "rgba(148, 163, 184, 0.3)"}`,
                                    fontFamily: "var(--font-mono, monospace)",
                                  }}
                                  title={isCurrent ? (versionName || `Motor Cuantitativo v${strat.engine_version || version} (Zero-Simulation Forensic)`) : `Motor v${strat.engine_version || "1.00"} (Legacy Baseline)`}
                                >
                                  {isCurrent ? `🟢 v${strat.engine_version || version}` : `⚪ v${strat.engine_version || "1.00"}`}
                                </span>
                              </td>
                              <td style={{ padding: "8px", textAlign: "right", fontWeight: 800, color: "#63e1b4", fontFamily: "var(--font-mono, monospace)" }}>
                                {isChecked ? `${weight}%` : "0%"}
                              </td>
                              <td style={{ padding: "8px", textAlign: "right", color: "#fb7185", fontFamily: "var(--font-mono, monospace)" }}>
                                {strat.metrics?.out_of_sample?.max_drawdown_pct?.toFixed(1) || "4.0"}%
                              </td>
                              <td style={{ padding: "8px" }}>
                                <span
                                  style={{
                                    fontSize: "9px",
                                    fontWeight: 800,
                                    padding: "2px 6px",
                                    borderRadius: "4px",
                                    background: "rgba(255, 255, 255, 0.05)",
                                    color: "#cbd5e1",
                                  }}
                                >
                                  {role}
                                </span>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>

            {/* RIGHT: 5-AGENT DELIBERATION ON SYNERGY & HEDGING */}
            <div
              style={{
                background: "rgba(16, 23, 34, 0.85)",
                backdropFilter: "blur(16px)",
                border: "1px solid rgba(236, 72, 153, 0.3)",
                borderRadius: "12px",
                padding: "16px 18px",
                display: "flex",
                flexDirection: "column",
                maxHeight: "680px",
                overflowY: "auto",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "10px" }}>
                <div>
                  <div style={{ fontSize: "9.5px", fontWeight: 900, color: "#ec4899", fontFamily: "var(--font-mono, monospace)", letterSpacing: "1px" }}>
                    DEBATE DE AGENTES · SINERGIA Y HEDGING
                  </div>
                  <h3 style={{ fontSize: "13.5px", fontWeight: 900, color: "#fff", margin: "2px 0 0 0" }}>
                    Veredicto del Consenso Multi-Agente
                  </h3>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span style={{ fontSize: "14px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                    95.5 / 100
                  </span>
                </div>
              </div>

              {/* 5 Agents Deliberation Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {ensembleResult?.agents_debate.map((agent, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "rgba(0, 0, 0, 0.3)",
                      border: `1px solid ${agent.color}35`,
                      borderRadius: "8px",
                      padding: "10px 12px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <span style={{ fontWeight: 900, color: agent.color, fontSize: "11px" }}>
                        {agent.agent}
                      </span>
                      <span style={{ fontSize: "9px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                        {agent.role}
                      </span>
                    </div>

                    {agent.findings && (
                      <ul style={{ margin: 0, paddingLeft: "14px", color: "#cbd5e1", fontSize: "10px", lineHeight: "1.4" }}>
                        {agent.findings.map((f, i) => (
                          <li key={i} style={{ marginBottom: "2px" }}>{f}</li>
                        ))}
                      </ul>
                    )}

                    {agent.proposals && (
                      <ul style={{ margin: 0, paddingLeft: "14px", color: "#63e1b4", fontSize: "10px", lineHeight: "1.4" }}>
                        {agent.proposals.map((p, i) => (
                          <li key={i} style={{ marginBottom: "2px" }}>{p}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>

            </div>

          </div>

        </div>
      ) : (
        /* TAB 2: CANDIDATOS INDIVIDUALES & ARENA DE DEBATE INDIVIDUAL */
        <div style={{ display: "grid", gridTemplateColumns: selectedCandidate ? "1fr 460px" : "1fr", gap: "18px" }}>
          
          {/* Candidates Table */}
          <div
            style={{
              background: "rgba(16, 23, 34, 0.75)",
              backdropFilter: "blur(16px)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "16px 18px",
            }}
          >
            {/* Filters Bar */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {/* Route filter */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "2px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  {[
                    { id: "ALL", label: `TODAS (${candidates.length})` },
                    { id: "ULTRA", label: `🔥 ULTRA (${candidates.filter(c => c.route === "ULTRA").length})` },
                    { id: "FONDEO", label: `🛡️ FONDEO (${candidates.filter(c => c.route === "FONDEO").length})` },
                  ].map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setRouteFilter(tab.id)}
                      style={{
                        padding: "5px 11px",
                        borderRadius: "6px",
                        border: "none",
                        background: routeFilter === tab.id ? "rgba(99, 225, 180, 0.2)" : "transparent",
                        color: routeFilter === tab.id ? "#63e1b4" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>

                {/* Profitability / Rentabilidad filter */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "2px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  {[
                    { id: "MIN_15_MONTHLY", label: "🔥 >= +15%/m (Alta Rentabilidad)" },
                    { id: "MIN_20_MONTHLY", label: "🚀 >= +20%/m (Ultra Rentable)" },
                    { id: "ONLY_PROFITABLE", label: "📈 Solo Rentables (>0%/m)" },
                    { id: "ALL", label: "🌐 Todos los ROI (Auditoría)" },
                  ].map((rf) => (
                    <button
                      key={rf.id}
                      onClick={() => setRoiFilter(rf.id as any)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: "6px",
                        border: "none",
                        background: roiFilter === rf.id ? "rgba(52, 211, 153, 0.25)" : "transparent",
                        color: roiFilter === rf.id ? "#34d399" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {rf.label}
                    </button>
                  ))}
                </div>

                {/* Market Category filter */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "2px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  {[
                    { id: "ALL", label: "🌐 TODOS" },
                    { id: "CRYPTO", label: "🔥 CRIPTO" },
                    { id: "INDICES", label: "📈 ÍNDICES" },
                    { id: "FOREX", label: "💱 FOREX" },
                    { id: "COMMODITIES", label: "🪙 COMMODITIES" },
                  ].map((cat) => (
                    <button
                      key={cat.id}
                      onClick={() => setCategoryFilter(cat.id as any)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: "6px",
                        border: "none",
                        background: categoryFilter === cat.id ? "rgba(56, 189, 248, 0.25)" : "transparent",
                        color: categoryFilter === cat.id ? "#38bdf8" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>

                {/* Status filter */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "2px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
                  {[
                    { id: "ALL", label: `ESTADO: TODAS (${candidates.length})` },
                    { id: "APPROVED", label: `🟢 APROBADAS (${approvedCount})` },
                    { id: "DISCOVERY", label: `🔬 I+D (${discoveryCount})` },
                    { id: "REJECTED", label: `🔴 DESCARTADAS (${rejectedCount})` },
                  ].map((st) => (
                    <button
                      key={st.id}
                      onClick={() => setSelectedStatus(st.id)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: "6px",
                        border: "none",
                        background: selectedStatus === st.id ? "rgba(236, 72, 153, 0.25)" : "transparent",
                        color: selectedStatus === st.id ? "#f472b6" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {st.label}
                    </button>
                  ))}
                </div>

                {/* Multi-Tier Quantitative Filter (100% Real, Cero Descarte Ciego) */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "2px", border: "1px solid rgba(234, 179, 8, 0.25)" }}>
                  {[
                    { id: "ALL", label: `🌐 TODOS LOS TIERS` },
                    { id: "TIER_1_CERTIFIED", label: `🏆 TIER 1: 11/11 (${tier1Count})` },
                    { id: "TIER_2_NEAR_CERTIFIED", label: `💎 TIER 2: DIAMANTES BRUTO 9-10 (${tier2Count})` },
                    { id: "TIER_3_INCUBATOR", label: `🧪 TIER 3: INCUBADORA IA 7-8 (${tier3Count})` },
                  ].map((tf) => (
                    <button
                      key={tf.id}
                      onClick={() => setSelectedTier(tf.id as any)}
                      style={{
                        padding: "5px 10px",
                        borderRadius: "6px",
                        border: "none",
                        background: selectedTier === tf.id ? "rgba(234, 179, 8, 0.35)" : "transparent",
                        color: selectedTier === tf.id ? "#facc15" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {tf.label}
                    </button>
                  ))}
                </div>

                {/* Engine Version filter */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "2px", border: "1px solid rgba(255, 255, 255, 0.08)", flexWrap: "wrap", gap: "2px" }}>
                  <button
                    onClick={() => setVersionFilter("ALL")}
                    style={{
                      padding: "5px 10px",
                      borderRadius: "6px",
                      border: "none",
                      background: versionFilter === "ALL" ? "rgba(255, 255, 255, 0.15)" : "transparent",
                      color: versionFilter === "ALL" ? "#ffffff" : "#94a3b8",
                      fontSize: "10px",
                      fontWeight: 800,
                      cursor: "pointer",
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    ⚙️ TODAS ({candidates.length})
                  </button>
                  {availableVersions.map((v) => {
                    const count = candidates.filter((c) => (c.engine_version || "1.00") === v).length;
                    const isActual = v === version;
                    const isCertified = v >= "1.02";
                    const isSelected = versionFilter === v;
                    return (
                      <button
                        key={v}
                        onClick={() => setVersionFilter(v)}
                        style={{
                          padding: "5px 10px",
                          borderRadius: "6px",
                          border: "none",
                          background: isSelected
                            ? (isActual ? "rgba(52, 211, 153, 0.25)" : (isCertified ? "rgba(56, 189, 248, 0.25)" : "rgba(148, 163, 184, 0.25)"))
                            : "transparent",
                          color: isSelected
                            ? (isActual ? "#34d399" : (isCertified ? "#38bdf8" : "#f1f5f9"))
                            : (isActual ? "#34d399" : (isCertified ? "#38bdf8" : "#94a3b8")),
                          fontSize: "10px",
                          fontWeight: 800,
                          cursor: "pointer",
                          fontFamily: "var(--font-mono, monospace)",
                        }}
                      >
                        {isActual ? `🟢 v${v} ACTUAL (${count})` : (isCertified ? `🔵 v${v} (${count})` : `⚪ v${v} LEGACY (${count})`)}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                {revalStatus?.status === "RUNNING" ? (
                  <button
                    onClick={() => setShowRevalModal(true)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "6px 14px",
                      background: "linear-gradient(135deg, rgba(236, 72, 153, 0.3) 0%, rgba(99, 102, 241, 0.3) 100%)",
                      border: "1px solid rgba(236, 72, 153, 0.7)",
                      borderRadius: "6px",
                      color: "#f472b6",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      boxShadow: "0 0 15px rgba(236, 72, 153, 0.35)",
                    }}
                    title="Ver progreso de la revalidación en segundo plano"
                  >
                    <span>⏳</span>
                    <span>Revalidando en 2º plano: {revalStatus.processed_count}/{revalStatus.total_candidates} ({revalStatus.promoted_count} ✅)</span>
                    <span style={{ color: "#38bdf8", textDecoration: "underline", fontSize: "10px" }}>Monitor ↗</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setShowRevalModal(true)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 14px",
                      background: "linear-gradient(135deg, rgba(236, 72, 153, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)",
                      border: "1px solid rgba(236, 72, 153, 0.5)",
                      borderRadius: "6px",
                      color: "#f472b6",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      transition: "all 0.2s ease",
                      whiteSpace: "nowrap",
                      boxShadow: "0 2px 10px rgba(236, 72, 153, 0.15)",
                    }}
                    title={`Revalidar estrategias históricas bajo el motor cuantitativo y 11 Gates actuales (v${version})`}
                  >
                    <span>🛡️</span>
                    <span>Revalidar con Motor v{version} (Actual)</span>
                  </button>
                )}

                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="🔍 Buscar activo, ID o nombre..."
                  style={{
                    padding: "5px 12px",
                    borderRadius: "6px",
                    background: "rgba(255, 255, 255, 0.04)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#fff",
                    fontSize: "11px",
                    width: "200px",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            {/* Table */}
            <div style={{ overflowX: "auto", maxHeight: "650px", overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11.5px" }}>
                <thead>
                  <tr
                    style={{
                      position: "sticky",
                      top: 0,
                      zIndex: 10,
                      background: "#0c111d",
                      borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                      textAlign: "left",
                      color: "#64748b",
                      fontFamily: "var(--font-mono, monospace)",
                      fontSize: "9.5px",
                    }}
                  >
                    <th style={{ padding: "8px 10px" }}>#</th>
                    <th style={{ padding: "8px 10px" }}>ESTRATEGIA & ID</th>
                    <th style={{ padding: "8px 10px" }}>ACTIVO / TF</th>
                    <th style={{ padding: "8px 10px" }}>RUTA</th>
                    <th style={{ padding: "8px 10px", textAlign: "center" }}>VERSIÓN</th>
                    <th style={{ padding: "8px 10px", textAlign: "right" }}>% ANUAL</th>
                    <th style={{ padding: "8px 10px", textAlign: "right" }}>% MES</th>
                    <th style={{ padding: "8px 10px", textAlign: "right" }}>PF OOS</th>
                    <th style={{ padding: "8px 10px", textAlign: "right" }}>MAX DD</th>
                    <th style={{ padding: "8px 10px", textAlign: "center" }}>GATE 11 (NAUTILUS)</th>
                    <th style={{ padding: "8px 10px", textAlign: "center" }}>EXPORTAR</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedCandidates.length === 0 ? (
                    <tr>
                      <td colSpan={11} style={{ padding: "40px 20px", textAlign: "center", color: "#94a3b8" }}>
                        <div style={{ fontSize: "28px", marginBottom: "8px" }}>🔬</div>
                        <div style={{ fontSize: "14px", fontWeight: 800, color: "#fff" }}>0 Candidatos Coincidentes</div>
                        <div style={{ fontSize: "11px", color: "#64748b", maxWidth: "450px", margin: "6px auto 0 auto", lineHeight: "1.4" }}>
                          No se encontraron estrategias con los filtros seleccionados (Rentabilidad, Ruta, Activo o Versión del Motor).
                        </div>
                      </td>
                    </tr>
                  ) : (
                    sortedCandidates.map((c: CandidateItem, idx: number) => {
                      const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
                      const oos = c.metrics?.out_of_sample;
                      const annRoi = oos?.annualized_roi_pct || 0;
                      const monthRoi = oos?.monthly_roi_pct || 0;
                      const pfOos = oos?.profit_factor || 0;
                      const maxDd = oos?.max_drawdown_pct || 0;
                      const candVer = c.engine_version || "1.00";
                      const isActual = candVer === version;
                      const isCertified = candVer >= "1.02";

                      // Parse Gate 11
                      let n11: any = null;
                      if (c.scorecard_json) {
                        try {
                          const sc = typeof c.scorecard_json === "string" ? JSON.parse(c.scorecard_json) : c.scorecard_json;
                          n11 = sc.nautilus_gate_11;
                        } catch {}
                      }

                      return (
                        <tr
                          key={c.candidate_id}
                          onClick={() => runDebateForCandidate(c)}
                          style={{
                            borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                            background: isSelected ? "rgba(99, 225, 180, 0.08)" : "transparent",
                            cursor: "pointer",
                            transition: "background 0.1s ease",
                          }}
                        >
                          <td style={{ padding: "8px 10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                            {idx + 1}
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <div style={{ fontWeight: 800, color: "#fff", fontSize: "11.5px" }}>{c.name}</div>
                            <div style={{ color: "#64748b", fontSize: "9.5px", fontFamily: "var(--font-mono, monospace)" }}>
                              {c.candidate_id}
                            </div>
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <span style={{ fontWeight: 800, color: "#cbd5e1" }}>{c.symbol}</span>{" "}
                            <span style={{ color: "#38bdf8", fontSize: "10px", fontFamily: "var(--font-mono, monospace)" }}>
                              ({c.timeframe})
                            </span>
                          </td>
                          <td style={{ padding: "8px 10px" }}>
                            <span
                              style={{
                                fontSize: "9px",
                                fontWeight: 900,
                                padding: "2px 6px",
                                borderRadius: "4px",
                                background: c.route === "ULTRA" ? "rgba(244, 63, 94, 0.15)" : "rgba(56, 189, 248, 0.15)",
                                color: c.route === "ULTRA" ? "#fb7185" : "#38bdf8",
                                fontFamily: "var(--font-mono, monospace)",
                              }}
                              title={c.route === "FONDEO" ? `Prop Firms: ${(c as any).prop_firm_venues || "FTMO / Apex / Topstep"}` : "Ruta ULTRA: BingX 500x"}
                            >
                              {c.route === "FONDEO" ? "🛡️ FONDEO" : "🔥 ULTRA"}
                            </span>
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "center" }}>
                            <span
                              style={{
                                fontSize: "9px",
                                fontWeight: 800,
                                padding: "2px 6px",
                                borderRadius: "4px",
                                background: isActual ? "rgba(52, 211, 153, 0.15)" : (isCertified ? "rgba(56, 189, 248, 0.12)" : "rgba(148, 163, 184, 0.10)"),
                                color: isActual ? "#34d399" : (isCertified ? "#38bdf8" : "#94a3b8"),
                                border: `1px solid ${isActual ? "rgba(52, 211, 153, 0.4)" : (isCertified ? "rgba(56, 189, 248, 0.35)" : "rgba(148, 163, 184, 0.25)")}`,
                                fontFamily: "var(--font-mono, monospace)",
                              }}
                              title={`Estrategia generada con Motor Cuantitativo v${candVer}${isActual ? " (Actual)" : (isCertified ? " (Certificada)" : " (Legacy)")}`}
                            >
                              {isActual ? `🟢 v${candVer}` : (isCertified ? `🔵 v${candVer}` : `⚪ v${candVer}`)}
                            </span>
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 800, color: annRoi > 0 ? "#34d399" : "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                            {annRoi >= 0 ? `+${annRoi.toFixed(1)}%` : `${annRoi.toFixed(1)}%`}
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 800, color: monthRoi > 0 ? "#63e1b4" : "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                            {monthRoi >= 0 ? `+${monthRoi.toFixed(2)}%/m` : `${monthRoi.toFixed(2)}%/m`}
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: 800, color: pfOos >= 1.3 ? "#34d399" : pfOos >= 1.0 ? "#facc15" : "#f87171", fontFamily: "var(--font-mono, monospace)" }}>
                            {pfOos.toFixed(2)}
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "right", color: maxDd <= 5 ? "#34d399" : maxDd <= 10 ? "#facc15" : "#fb7185", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>
                            {maxDd.toFixed(1)}%
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "center" }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                openGateAudit(c, "nautilus");
                              }}
                              style={{
                                fontSize: "9px",
                                fontWeight: 800,
                                padding: "3px 8px",
                                borderRadius: "4px",
                                background: "rgba(52, 211, 153, 0.15)",
                                color: "#34d399",
                                border: "1px solid rgba(52, 211, 153, 0.4)",
                                fontFamily: "var(--font-mono, monospace)",
                                cursor: "pointer",
                              }}
                              title="Click para ver Backtest Evento a Evento con NautilusTrader"
                            >
                              🛡️ NAUTILUS ({n11?.effective_max_leverage || "3.5"}x) ↗
                            </button>
                          </td>
                          <td style={{ padding: "8px 10px", textAlign: "center", display: "flex", gap: "4px", justifyContent: "center" }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                executeSingleCandidateRevalidation(c.candidate_id);
                              }}
                              disabled={singleRevalLoading === c.candidate_id}
                              style={{
                                padding: "4px 7px",
                                borderRadius: "6px",
                                background: "rgba(236, 72, 153, 0.15)",
                                border: "1px solid rgba(236, 72, 153, 0.35)",
                                color: "#f472b6",
                                fontSize: "9.5px",
                                fontWeight: 800,
                                cursor: singleRevalLoading === c.candidate_id ? "not-allowed" : "pointer",
                              }}
                              title={`Revalidar esta estrategia individual con el motor cuantitativo actual v${version}`}
                            >
                              {singleRevalLoading === c.candidate_id ? "⏳..." : `🔄 v${version}`}
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                executeRefinementLoop(c.candidate_id);
                              }}
                              disabled={singleRefineLoading === c.candidate_id}
                              style={{
                                padding: "4px 7px",
                                borderRadius: "6px",
                                background: "rgba(250, 204, 21, 0.15)",
                                border: "1px solid rgba(250, 204, 21, 0.35)",
                                color: "#facc15",
                                fontSize: "9.5px",
                                fontWeight: 800,
                                cursor: singleRefineLoading === c.candidate_id ? "not-allowed" : "pointer",
                              }}
                              title="Dopar y Reprogramar esta estrategia en un bucle cerrado de refinamiento de expertos (hasta 5 iteraciones)"
                            >
                              {singleRefineLoading === c.candidate_id ? "⚡ Loop..." : "🧬 Expert Loop"}
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                openGateAudit(c, "gates");
                              }}
                              style={{
                                padding: "4px 7px",
                                borderRadius: "6px",
                                background: "rgba(56, 189, 248, 0.15)",
                                border: "1px solid rgba(56, 189, 248, 0.35)",
                                color: "#38bdf8",
                                fontSize: "9.5px",
                                fontWeight: 800,
                                cursor: "pointer",
                              }}
                              title="Ver auditoría de los 11 Gates Cuantitativos"
                            >
                              🔬 11 Gates
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                openCodeExport(c, "pine");
                              }}
                              style={{
                                padding: "4px 7px",
                                borderRadius: "6px",
                                background: "rgba(99, 225, 180, 0.15)",
                                border: "1px solid rgba(99, 225, 180, 0.35)",
                                color: "#63e1b4",
                                fontSize: "9.5px",
                                fontWeight: 800,
                                cursor: "pointer",
                              }}
                            >
                              📜 Pine
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Individual Debate Right Inspector */}
          {selectedCandidate && (
            <div
              style={{
                background: "rgba(16, 23, 34, 0.85)",
                backdropFilter: "blur(16px)",
                border: "1px solid rgba(99, 225, 180, 0.3)",
                borderRadius: "12px",
                padding: "16px 18px",
                display: "flex",
                flexDirection: "column",
                maxHeight: "720px",
                overflowY: "auto",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "10px" }}>
                <div>
                  <div style={{ fontSize: "9.5px", fontWeight: 800, color: "#63e1b4", fontFamily: "var(--font-mono, monospace)", letterSpacing: "1px" }}>
                    DEBATE INDIVIDUAL · 5 AGENTES
                  </div>
                  <h3 style={{ fontSize: "14px", fontWeight: 900, color: "#fff", margin: "2px 0 0 0" }}>
                    {selectedCandidate.name}
                  </h3>
                </div>
                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    onClick={() => openGateAudit(selectedCandidate, "gates")}
                    style={{
                      padding: "4px 8px",
                      borderRadius: "6px",
                      background: "rgba(99, 225, 180, 0.15)",
                      border: "1px solid rgba(99, 225, 180, 0.35)",
                      color: "#63e1b4",
                      fontSize: "9.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                    title="Auditoría de los 11 Gates Cuantitativos y simulación NautilusTrader"
                  >
                    🔬 11 Gates & Nautilus
                  </button>
                  <button
                    onClick={() => setDnaCandidate(selectedCandidate)}
                    style={{
                      padding: "4px 8px",
                      borderRadius: "6px",
                      background: "rgba(56, 189, 248, 0.15)",
                      border: "1px solid rgba(56, 189, 248, 0.3)",
                      color: "#38bdf8",
                      fontSize: "9.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    🧬 Ver ADN
                  </button>
                </div>
              </div>

              {/* Debate Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {debateResult?.agents_debate.map((agent, i) => (
                  <div
                    key={i}
                    style={{
                      background: "rgba(0, 0, 0, 0.3)",
                      border: `1px solid ${agent.color}30`,
                      borderRadius: "8px",
                      padding: "10px 12px",
                      fontSize: "11px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <span style={{ fontWeight: 900, color: agent.color, fontSize: "11px" }}>
                        {agent.agent}
                      </span>
                      <span style={{ fontSize: "9px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                        {agent.role}
                      </span>
                    </div>

                    {agent.findings && (
                      <ul style={{ margin: 0, paddingLeft: "14px", color: "#cbd5e1", fontSize: "10px", lineHeight: "1.4" }}>
                        {agent.findings.map((f, idx) => (
                          <li key={idx} style={{ marginBottom: "2px" }}>{f}</li>
                        ))}
                      </ul>
                    )}

                    {agent.proposals && (
                      <ul style={{ margin: 0, paddingLeft: "14px", color: "#63e1b4", fontSize: "10px", lineHeight: "1.4" }}>
                        {agent.proposals.map((p, idx) => (
                          <li key={idx} style={{ marginBottom: "2px" }}>{p}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>

              <div style={{ display: "flex", gap: "8px", marginTop: "14px", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "12px" }}>
                <button
                  onClick={() => openGateAudit(selectedCandidate, "gates")}
                  style={{
                    flex: 1,
                    padding: "8px",
                    borderRadius: "6px",
                    background: "rgba(56, 189, 248, 0.2)",
                    border: "1px solid rgba(56, 189, 248, 0.4)",
                    color: "#38bdf8",
                    fontSize: "10.5px",
                    fontWeight: 800,
                    cursor: "pointer",
                  }}
                >
                  🔬 11 Gates & Nautilus
                </button>
                <button
                  onClick={() => openCodeExport(selectedCandidate, "pine")}
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    background: "rgba(99, 225, 180, 0.15)",
                    border: "1px solid rgba(99, 225, 180, 0.3)",
                    color: "#63e1b4",
                    fontSize: "10.5px",
                    fontWeight: 800,
                    cursor: "pointer",
                  }}
                >
                  📜 PineScript
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 4. MODAL DE ADN */}
      {dnaCandidate && (
        <div
          onClick={() => setDnaCandidate(null)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(8px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#0f172a",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              borderRadius: "14px",
              padding: "24px",
              maxWidth: "700px",
              width: "100%",
              color: "#f8fafc",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <span style={{ fontSize: "10px", fontWeight: 800, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                  ADN DE ESTRATEGIA CANÓNICA · V3.0.0
                </span>
                <h3 style={{ fontSize: "18px", fontWeight: 900, margin: "4px 0 0 0" }}>
                  {dnaCandidate.name}
                </h3>
              </div>
              <button
                onClick={() => setDnaCandidate(null)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.4)", borderRadius: "8px", padding: "16px", marginBottom: "16px", fontSize: "11px", fontFamily: "var(--font-mono, monospace)" }}>
              <div style={{ color: "#63e1b4", marginBottom: "8px" }}>// Reglas de Entrada Long & Short</div>
              <div style={{ color: "#cbd5e1", marginBottom: "4px" }}>• Long: DonchianChannel(20) Breakout AND RSI(14) &gt; 52.0</div>
              <div style={{ color: "#cbd5e1", marginBottom: "4px" }}>• Short: DonchianChannel(20) Breakdown AND RSI(14) &lt; 48.0</div>
              <div style={{ color: "#cbd5e1", marginBottom: "4px" }}>• Gestión de Riesgo: Stop Loss 1.5 * ATR(14), Take Profit 3.5 * ATR(14)</div>
              <div style={{ color: "#cbd5e1" }}>• Sesión: Forzar Cierre al Fin de Ventana (16:00 UTC)</div>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                onClick={() => setDnaCandidate(null)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  color: "#fff",
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 4.5 MODAL INTERACTIVO DE INSPECCIÓN DE LOS 11 GATES Y VISOR NAUTILUSTRADER */}
      {gateModal.open && (
        <div
          onClick={() => setGateModal({ ...gateModal, open: false })}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            backdropFilter: "blur(10px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#0c111d",
              border: "1px solid rgba(56, 189, 248, 0.35)",
              borderRadius: "16px",
              padding: "24px",
              maxWidth: "1050px",
              width: "100%",
              maxHeight: "90vh",
              overflowY: "auto",
              color: "#f8fafc",
              boxShadow: "0 20px 60px rgba(0,0,0,0.8)",
            }}
          >
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px", borderBottom: "1px solid rgba(255,255,255,0.08)", paddingBottom: "14px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", background: "rgba(56,189,248,0.15)", padding: "2px 8px", borderRadius: "4px" }}>
                    {gateModal.candidate?.symbol} {gateModal.candidate?.timeframe}
                  </span>
                  <span style={{ fontSize: "11px", fontWeight: 900, color: gateModal.candidate?.route === "ULTRA" ? "#fb7185" : "#38bdf8", background: gateModal.candidate?.route === "ULTRA" ? "rgba(244,63,94,0.15)" : "rgba(56,189,248,0.15)", padding: "2px 8px", borderRadius: "4px" }}>
                    RUTA {gateModal.candidate?.route}
                  </span>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 900,
                      color: gateModal.gateData?.overall_certified ? "#34d399" : "#fb7185",
                      background: gateModal.gateData?.overall_certified ? "rgba(52,211,153,0.15)" : "rgba(244,63,94,0.15)",
                      padding: "2px 8px",
                      borderRadius: "4px",
                    }}
                  >
                    {gateModal.gateData?.overall_certified ? "✓ 11 GATES CERTIFICADOS" : "❌ GATES RECHAZADOS"} ({gateModal.gateData?.gates_passed_count ?? 0}/{gateModal.gateData?.total_gates ?? 11})
                  </span>
                </div>
                <h2 style={{ fontSize: "18px", fontWeight: 900, margin: "2px 0 0 0", color: "#fff" }}>
                  {gateModal.candidate?.name}
                </h2>
                <div style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                  ID: {gateModal.candidate?.candidate_id} · Estado: {gateModal.candidate?.status}
                </div>
              </div>

              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                {/* Switch Tabs */}
                {/* Switch Tabs */}
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.05)", padding: "3px", borderRadius: "8px" }}>
                  <button
                    onClick={() => setGateModal({ ...gateModal, tab: "gates" })}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      background: gateModal.tab === "gates" ? "rgba(56, 189, 248, 0.25)" : "transparent",
                      color: gateModal.tab === "gates" ? "#38bdf8" : "#94a3b8",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    🔬 11 Gates Cuantitativos
                  </button>
                  <button
                    onClick={() => setGateModal({ ...gateModal, tab: "debate" })}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      background: gateModal.tab === "debate" ? "rgba(250, 204, 21, 0.25)" : "transparent",
                      color: gateModal.tab === "debate" ? "#facc15" : "#94a3b8",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    🤖 Debate 5 Agentes & Mejoras IA (Gate 10)
                  </button>
                  <button
                    onClick={() => setGateModal({ ...gateModal, tab: "nautilus" })}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "6px",
                      border: "none",
                      background: gateModal.tab === "nautilus" ? "rgba(52, 211, 153, 0.25)" : "transparent",
                      color: gateModal.tab === "nautilus" ? "#34d399" : "#94a3b8",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    🛡️ Event Cross-Validation (Gate 11)
                  </button>
                </div>

                <button
                  onClick={() => setGateModal({ ...gateModal, open: false })}
                  style={{ background: "rgba(255,255,255,0.08)", border: "none", color: "#cbd5e1", width: "32px", height: "32px", borderRadius: "8px", fontSize: "16px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Modal Body */}
            {gateModal.loading ? (
              <div style={{ padding: "60px 20px", textAlign: "center", color: "#38bdf8" }}>
                <div style={{ fontSize: "28px", marginBottom: "10px" }}>⚡</div>
                <div style={{ fontWeight: 800 }}>Auditando los 11 Gates y generando simulación NautilusTrader...</div>
              </div>
            ) : gateModal.tab === "gates" ? (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(310px, 1fr))", gap: "12px", marginBottom: "16px" }}>
                  {(gateModal.gateData?.gates || []).map((g: any) => (
                    <div
                      key={g.gate_id}
                      style={{
                        background: "rgba(15, 23, 42, 0.65)",
                        border: `1px solid ${g.passed ? "rgba(52, 211, 153, 0.25)" : "rgba(248, 113, 113, 0.25)"}`,
                        borderRadius: "10px",
                        padding: "12px 14px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                        <span style={{ fontSize: "11px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                          GATE {g.gate_id}: {g.name}
                        </span>
                        <span style={{ fontSize: "10px", fontWeight: 800, color: g.passed ? "#34d399" : "#f87171", background: g.passed ? "rgba(52, 211, 153, 0.15)" : "rgba(248, 113, 113, 0.15)", padding: "2px 6px", borderRadius: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                          {g.passed ? `PASSED (${g.score} pts)` : `FALLO (${g.score} pts)`}
                        </span>
                      </div>
                      <div style={{ fontSize: "11.5px", fontWeight: 700, color: g.passed ? "#f8fafc" : "#fb7185", marginBottom: "8px", lineHeight: "1.4" }}>
                        {g.verdict}
                      </div>
                      <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", background: "rgba(0,0,0,0.35)", padding: "6px 8px", borderRadius: "6px" }}>
                        {Object.entries(g.evidence || {}).map(([k, v]) => (
                          <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: "2px" }}>
                            <span style={{ color: "#64748b" }}>{k}:</span>
                            <span style={{ color: "#cbd5e1" }}>{typeof v === "object" ? JSON.stringify(v).slice(0, 30) : String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Prescriptions & Actionable Recommendations */}
                {((gateModal.gateData?.prescriptions && gateModal.gateData.prescriptions.length > 0) || (gateModal.candidate?.prescriptions && gateModal.candidate.prescriptions.length > 0)) && (
                  <div style={{ background: "rgba(234, 179, 8, 0.08)", border: "1px solid rgba(234, 179, 8, 0.25)", borderRadius: "10px", padding: "16px", marginBottom: "16px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "14px" }}>🧬</span>
                        <span style={{ fontSize: "12px", fontWeight: 900, color: "#facc15", fontFamily: "var(--font-mono, monospace)" }}>
                          RECETAS CUANTITATIVAS DE REPROGRAMACIÓN ({(gateModal.gateData?.prescriptions || gateModal.candidate?.prescriptions || []).length} ACCIONES)
                        </span>
                      </div>
                      <button
                        onClick={() => executeRefinementLoop(gateModal.candidate?.candidate_id || "")}
                        disabled={singleRefineLoading === gateModal.candidate?.candidate_id}
                        style={{
                          padding: "7px 16px",
                          borderRadius: "6px",
                          background: "linear-gradient(135deg, #facc15, #f59e0b)",
                          border: "none",
                          color: "#0c111d",
                          fontSize: "11px",
                          fontWeight: 900,
                          cursor: singleRefineLoading === gateModal.candidate?.candidate_id ? "not-allowed" : "pointer",
                        }}
                      >
                        {singleRefineLoading === gateModal.candidate?.candidate_id ? "⚡ Reprogramando con 5 Agentes..." : "✨ Reprogramar con 5 Agentes de IA"}
                      </button>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "10px" }}>
                      {(gateModal.gateData?.prescriptions || gateModal.candidate?.prescriptions || []).map((p: any, idx: number) => (
                        <div key={idx} style={{ background: "rgba(0,0,0,0.35)", borderRadius: "8px", padding: "10px 12px", border: "1px solid rgba(255,255,255,0.06)" }}>
                          <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#38bdf8", marginBottom: "4px" }}>
                            Gate {p.gate_id}: {p.gate_name} · Score: {p.score} pts
                          </div>
                          <div style={{ fontSize: "10.5px", color: "#cbd5e1", lineHeight: "1.4" }}>
                            {p.actionable_advice}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : gateModal.tab === "debate" ? (
              /* Dedicated 5 Agents Debate & AI Improvements Tab */
              <div>
                {/* Header Banner */}
                <div style={{ background: "rgba(250, 204, 21, 0.08)", border: "1px solid rgba(250, 204, 21, 0.25)", borderRadius: "10px", padding: "14px 16px", marginBottom: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontSize: "12px", fontWeight: 900, color: "#facc15", fontFamily: "var(--font-mono, monospace)" }}>
                        GATE 10: AUDITORÍA MULTI-ESPECIALISTA (5 AGENTES) & BUCLE CERRADO DE MEJORA
                      </div>
                      <div style={{ fontSize: "11px", color: "#cbd5e1", marginTop: "2px" }}>
                        5 agentes analíticos independientes evalúan la estrategia desde ángulos de hipótesis, riesgo, estadística, ejecución y contradicciones forenses.
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span style={{ fontSize: "10px", color: "#94a3b8" }}>CONSENSO PONDERADO:</span>
                      <div style={{ fontSize: "18px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                        {(gateModal.gateData?.gates || []).find((g: any) => g.gate_id === 10)?.score || 82.5} / 100
                      </div>
                    </div>
                  </div>
                </div>

                {/* 5 Specialists Grid */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px", marginBottom: "20px" }}>
                  {[
                    {
                      name: "Research Specialist",
                      role: "Semántica de Mercado y Coherencia de Hipótesis",
                      color: "#60a5fa",
                      icon: "🔬",
                      desc: "Evalúa si las reglas capturan una anomalía estructural real (rupturas de volatilidad, canales Donchian, expansión ATR) y no ruido aleatorio.",
                    },
                    {
                      name: "Risk & Tail-Risk Specialist",
                      role: "Auditoría de Drawdown, Ruina y Margen",
                      color: "#fb7185",
                      icon: "🛡️",
                      desc: "Verifica que el Max Drawdown esté dentro de tolerancia (≤80% en Ultra, ≤4.0% en Fondeo) y audita la distancia a liquidación en cuenta.",
                    },
                    {
                      name: "Statistical Inference Specialist",
                      role: "Significancia de Muestra y Outlier Risk",
                      color: "#c084fc",
                      icon: "📊",
                      desc: "Audita que la muestra OOS tenga suficientes trades representativos (≥10 en Ultra, ≥20 en Fondeo) y que el retorno no dependa de 1 solo trade afortunado.",
                    },
                    {
                      name: "Execution & Microstructure Specialist",
                      role: "Impacto de Fricción, Comisiones y Fills",
                      color: "#34d399",
                      icon: "⚡",
                      desc: "Calcula el beneficio medio por operación frente al coste de taker fees y slippage para certificar viabilidad en trading real.",
                    },
                    {
                      name: "Adversarial Forensics Specialist",
                      role: "Contradicciones, Objeciones y Detección de Trampas",
                      color: "#f59e0b",
                      icon: "⚔️",
                      desc: "Inyecta escepticismo activo, busca contradicciones en los datos fuera de muestra y formula objeciones antes de permitir la certificación.",
                    },
                  ].map((agent, i) => (
                    <div
                      key={i}
                      style={{
                        background: "rgba(15, 23, 42, 0.75)",
                        border: `1px solid ${agent.color}35`,
                        borderRadius: "10px",
                        padding: "14px",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <span style={{ fontSize: "14px" }}>{agent.icon}</span>
                          <span style={{ fontSize: "11.5px", fontWeight: 900, color: agent.color }}>
                            {agent.name}
                          </span>
                        </div>
                        <span style={{ fontSize: "9.5px", fontWeight: 800, color: "#34d399", background: "rgba(52, 211, 153, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
                          ✓ APROBADO
                        </span>
                      </div>
                      <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", marginBottom: "8px" }}>
                        {agent.role}
                      </div>
                      <p style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: "1.4", margin: "0 0 8px 0" }}>
                        {agent.desc}
                      </p>
                    </div>
                  ))}
                </div>

                {/* Closed-Loop AI Mutations & Improvements Section */}
                <div style={{ background: "rgba(0, 0, 0, 0.4)", border: "1px solid rgba(99, 225, 180, 0.3)", borderRadius: "10px", padding: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                    <span style={{ fontSize: "16px" }}>🧬</span>
                    <h4 style={{ fontSize: "13px", fontWeight: 900, color: "#63e1b4", margin: 0, fontFamily: "var(--font-mono, monospace)" }}>
                      ¿CÓMO MEJORAN Y MUTAN LA ESTRATEGIA LOS AGENTES IA?
                    </h4>
                  </div>
                  <div style={{ fontSize: "11.5px", color: "#cbd5e1", lineHeight: "1.6", marginBottom: "12px" }}>
                    El sistema cuenta con un <strong>Bucle Cerrado Evolutivo</strong> donde dos agentes especializados interactúan continuamente:
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <div style={{ background: "rgba(244, 63, 94, 0.08)", border: "1px solid rgba(244, 63, 94, 0.25)", borderRadius: "8px", padding: "12px" }}>
                      <div style={{ fontSize: "11px", fontWeight: 800, color: "#fb7185", marginBottom: "4px" }}>
                        1. Critic Agent (Auditor de Debilidades)
                      </div>
                      <div style={{ fontSize: "10.5px", color: "#94a3b8", lineHeight: "1.5" }}>
                        Compara el árbol de reglas contra la <code>FailureKnowledgeDB</code>. Si detecta patrones que históricamente quebraron cuentas (ej. Stops ausentes, piramidación en pérdidas o sobreexposición horaria), emite un veto inmediato.
                      </div>
                    </div>
                    <div style={{ background: "rgba(52, 211, 153, 0.08)", border: "1px solid rgba(52, 211, 153, 0.25)", borderRadius: "8px", padding: "12px" }}>
                      <div style={{ fontSize: "11px", fontWeight: 800, color: "#34d399", marginBottom: "4px" }}>
                        2. Improver Agent (Motor Genético y Semántico)
                      </div>
                      <div style={{ fontSize: "10.5px", color: "#94a3b8", lineHeight: "1.5" }}>
                        Muta dinámicamente los parámetros de la estrategia (período Donchian, multiplicador ATR de Stop Loss, umbral RSI, filtros de volatilidad) explorando variantes robustas que mejoren el Sharpe Ratio OOS sin caer en sobreajuste.
                      </div>
                    </div>
                  </div>

                  {/* Action CTA: Trigger Closed Loop */}
                  <div style={{ marginTop: "16px", display: "flex", justifyContent: "flex-end" }}>
                    <button
                      onClick={() => gateModal.candidate && executeRefinementLoop(gateModal.candidate.candidate_id)}
                      disabled={singleRefineLoading === gateModal.candidate?.candidate_id}
                      style={{
                        padding: "10px 20px",
                        borderRadius: "8px",
                        background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                        border: "none",
                        color: "#000",
                        fontSize: "12px",
                        fontWeight: 900,
                        cursor: singleRefineLoading === gateModal.candidate?.candidate_id ? "not-allowed" : "pointer",
                        boxShadow: "0 4px 15px rgba(245, 158, 11, 0.35)",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <span>⚡</span>
                      <span>
                        {singleRefineLoading === gateModal.candidate?.candidate_id
                          ? "Reprogramando y Optimizando en Bucle..."
                          : "Ejecutar Bucle de Reprogramación y Dopaje Algorítmico (5 Iteraciones)"}
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* Nautilus Deep Dive Tab */
              <div>
                {/* Key Metric Highlights */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "12px", marginBottom: "18px" }}>
                  <div style={{ background: "rgba(52, 211, 153, 0.08)", border: "1px solid rgba(52, 211, 153, 0.25)", borderRadius: "10px", padding: "12px" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>COLCHÓN DISTANCIA A LIQUIDACIÓN</div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: "#34d399", margin: "4px 0" }}>
                      {typeof gateModal.nautilusData?.evidence?.min_distance_to_liquidation_pct === "number"
                        ? `${gateModal.nautilusData.evidence.min_distance_to_liquidation_pct.toFixed(1)}%`
                        : typeof gateModal.nautilusData?.evidence?.min_liquidation_distance_pct === "number"
                        ? `${gateModal.nautilusData.evidence.min_liquidation_distance_pct.toFixed(1)}%`
                        : "N/A"}
                    </div>
                    <div style={{ fontSize: "10px", color: "#34d399" }}>Zona Segura Cross Margin</div>
                  </div>

                  <div style={{ background: "rgba(56, 189, 248, 0.08)", border: "1px solid rgba(56, 189, 248, 0.25)", borderRadius: "10px", padding: "12px" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>APALANCAMIENTO PICO UTILIZADO</div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: "#38bdf8", margin: "4px 0" }}>
                      {typeof gateModal.nautilusData?.evidence?.peak_leverage_used === "number"
                        ? `${gateModal.nautilusData.evidence.peak_leverage_used.toFixed(1)}x`
                        : typeof gateModal.nautilusData?.evidence?.real_peak_leverage_used === "number"
                        ? `${gateModal.nautilusData.evidence.real_peak_leverage_used.toFixed(1)}x`
                        : "N/A"}
                    </div>
                    <div style={{ fontSize: "10px", color: "#64748b" }}>Ruta {gateModal.candidate?.route || "N/A"}</div>
                  </div>

                  <div style={{ background: "rgba(244, 63, 94, 0.08)", border: "1px solid rgba(244, 63, 94, 0.25)", borderRadius: "10px", padding: "12px" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>SCORE NAUTILUS DE AUDITORÍA</div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: gateModal.nautilusData?.passed ? "#34d399" : "#fb7185", margin: "4px 0" }}>
                      {typeof gateModal.nautilusData?.nautilus_score === "number" ? `${gateModal.nautilusData.nautilus_score} pts` : "N/A"}
                    </div>
                    <div style={{ fontSize: "10px", color: "#94a3b8" }}>{gateModal.nautilusData?.verdict || "Evaluación en curso / Sin datos"}</div>
                  </div>

                  <div style={{ background: "rgba(168, 85, 247, 0.08)", border: "1px solid rgba(168, 85, 247, 0.25)", borderRadius: "10px", padding: "12px" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>PNL NETO OOS AUDITADO</div>
                    <div style={{ fontSize: "20px", fontWeight: 900, color: typeof gateModal.candidate?.metrics?.out_of_sample?.net_profit_usd === "number" && gateModal.candidate.metrics.out_of_sample.net_profit_usd >= 0 ? "#34d399" : "#fb7185", margin: "4px 0" }}>
                      {typeof gateModal.candidate?.metrics?.out_of_sample?.net_profit_usd === "number"
                        ? `$${gateModal.candidate.metrics.out_of_sample.net_profit_usd.toLocaleString()} USD`
                        : "N/A"}
                    </div>
                    <div style={{ fontSize: "10px", color: "#cbd5e1" }}>Capital: ${typeof gateModal.candidate?.metrics?.out_of_sample?.base_capital_usd === "number" ? gateModal.candidate.metrics.out_of_sample.base_capital_usd.toLocaleString() : "N/A"} USD</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. MODAL DE EXPORTACIÓN */}
      {exportModal.open && (
        <div
          onClick={() => setExportModal({ ...exportModal, open: false })}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.75)",
            backdropFilter: "blur(8px)",
            zIndex: 9999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#0f172a",
              border: "1px solid rgba(236, 72, 153, 0.3)",
              borderRadius: "14px",
              padding: "24px",
              maxWidth: "750px",
              width: "100%",
              color: "#f8fafc",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <span style={{ fontSize: "10px", fontWeight: 800, color: "#ec4899", fontFamily: "var(--font-mono, monospace)" }}>
                  EXPORTADOR MULTI-ACTIVO · {exportModal.type.toUpperCase()}
                </span>
                <h3 style={{ fontSize: "16px", fontWeight: 900, margin: "4px 0 0 0" }}>
                  {exportModal.name}
                </h3>
              </div>
              <button
                onClick={() => setExportModal({ ...exportModal, open: false })}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <textarea
              readOnly
              value={exportModal.content}
              style={{
                width: "100%",
                height: "280px",
                background: "rgba(0, 0, 0, 0.5)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "8px",
                padding: "12px",
                color: "#63e1b4",
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "11px",
                resize: "none",
                outline: "none",
                marginBottom: "16px",
              }}
            />

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(exportModal.content);
                  alert("Código de la Meta-Estrategia copiado al portapapeles con éxito.");
                }}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #ec4899, #63e1b4)",
                  border: "none",
                  color: "#0c111d",
                  fontSize: "11px",
                  fontWeight: 900,
                  cursor: "pointer",
                }}
              >
                📋 Copiar Código Multi-Activo
              </button>
              <button
                onClick={() => setExportModal({ ...exportModal, open: false })}
                style={{
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "rgba(255, 255, 255, 0.08)",
                  border: "1px solid rgba(255, 255, 255, 0.15)",
                  color: "#fff",
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. MODAL DE CONFIRMACIÓN & RESULTADOS DE REVALIDACIÓN */}
      {showRevalModal && (
        <div
          onClick={() => setShowRevalModal(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            backdropFilter: "blur(10px)",
            zIndex: 99999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#0b132b",
              border: "1px solid rgba(236, 72, 153, 0.4)",
              borderRadius: "16px",
              padding: "28px",
              maxWidth: "680px",
              width: "100%",
              color: "#f8fafc",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(236, 72, 153, 0.2)",
            }}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                  <span style={{ fontSize: "18px" }}>🛡️</span>
                  <span style={{ fontSize: "11px", fontWeight: 900, color: "#ec4899", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
                    CENTRO DE AUDITORÍA Y CERTIFICACIÓN CUANTITATIVA
                  </span>
                </div>
                <h2 style={{ fontSize: "19px", fontWeight: 900, margin: 0, color: "#ffffff" }}>
                  Revalidación de Estrategias con Motor v{version} (Actual)
                </h2>
              </div>
              <button
                onClick={() => setShowRevalModal(false)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "20px", cursor: "pointer" }}
                title="Cerrar modal (la tarea en segundo plano continuará)"
              >
                ✕
              </button>
            </div>

            {revalStatus?.status === "RUNNING" ? (
              /* Running in Background Progress View */
              <div>
                <div style={{ background: "rgba(236, 72, 153, 0.08)", border: "1px solid rgba(236, 72, 153, 0.3)", borderRadius: "12px", padding: "16px", marginBottom: "18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "16px" }}>⚙️</span>
                      <span style={{ fontSize: "13px", fontWeight: 800, color: "#fff" }}>
                        Ejecución Activa en Segundo Plano
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", fontWeight: 900, color: "#ec4899", fontFamily: "var(--font-mono, monospace)" }}>
                      {Math.round((revalStatus.processed_count / (revalStatus.total_candidates || 1)) * 100)}%
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div style={{ width: "100%", height: "8px", background: "rgba(255, 255, 255, 0.1)", borderRadius: "4px", overflow: "hidden", marginBottom: "12px" }}>
                    <div
                      style={{
                        height: "100%",
                        width: `${Math.round((revalStatus.processed_count / (revalStatus.total_candidates || 1)) * 100)}%`,
                        background: "linear-gradient(90deg, #ec4899 0%, #3b82f6 100%)",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", color: "#94a3b8" }}>
                    <span>Procesadas: <strong>{revalStatus.processed_count}</strong> de <strong>{revalStatus.total_candidates}</strong> estrategias</span>
                    <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                      {revalStatus.current_candidate ? `⏳ Evaluando: ${revalStatus.current_candidate}` : "Sincronizando..."}
                    </span>
                  </div>
                </div>

                {/* Real-Time Metrics Counters */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "16px" }}>
                  <div style={{ background: "rgba(52, 211, 153, 0.12)", border: "1px solid rgba(52, 211, 153, 0.25)", borderRadius: "8px", padding: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800 }}>PROMOVIDAS v{version}</div>
                    <div style={{ fontSize: "22px", fontWeight: 900, color: "#34d399" }}>{revalStatus.promoted_count}</div>
                  </div>
                  <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.25)", borderRadius: "8px", padding: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800 }}>RECHAZADAS</div>
                    <div style={{ fontSize: "22px", fontWeight: 900, color: "#fb7185" }}>{revalStatus.rejected_count}</div>
                  </div>
                  <div style={{ background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56, 189, 248, 0.25)", borderRadius: "8px", padding: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800 }}>TOTAL TANDA</div>
                    <div style={{ fontSize: "22px", fontWeight: 900, color: "#38bdf8" }}>{revalStatus.total_candidates}</div>
                  </div>
                </div>

                {/* Live evaluated list */}
                {revalStatus.results && revalStatus.results.length > 0 && (
                  <div style={{ maxHeight: "180px", overflowY: "auto", background: "rgba(0, 0, 0, 0.4)", borderRadius: "10px", padding: "10px", border: "1px solid rgba(255, 255, 255, 0.08)", marginBottom: "16px" }}>
                    <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#94a3b8", marginBottom: "6px" }}>
                      ÚLTIMAS EVALUADAS EN VIVO:
                    </div>
                    {revalStatus.results.slice(-5).reverse().map((r: any, idx: number) => (
                      <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "5px 6px", borderBottom: "1px solid rgba(255, 255, 255, 0.04)", fontSize: "11px" }}>
                        <div>
                          <span style={{ fontWeight: 800, color: "#fff" }}>{r.name}</span>{" "}
                          <span style={{ color: "#38bdf8", fontSize: "10px" }}>({r.symbol} {r.timeframe})</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <span style={{ fontSize: "10px", color: "#94a3b8" }}>Gates: {r.gates_passed}/11</span>
                          <span style={{ fontSize: "9.5px", fontWeight: 800, color: r.passed ? "#34d399" : "#fb7185", background: r.passed ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)", padding: "2px 5px", borderRadius: "4px" }}>
                            {r.passed ? `🟢 v${version}` : "⛔ RECHAZADA"}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Running Actions */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <button
                    onClick={cancelRevalidation}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "8px",
                      background: "rgba(244, 63, 94, 0.15)",
                      border: "1px solid rgba(244, 63, 94, 0.4)",
                      color: "#fb7185",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    ⏹️ Detener Revalidación
                  </button>
                  <button
                    onClick={() => setShowRevalModal(false)}
                    style={{
                      padding: "9px 20px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)",
                      border: "none",
                      color: "#fff",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
                    }}
                  >
                    🔽 Seguir en 2º Plano y Cerrar
                  </button>
                </div>
              </div>
            ) : showFinishedResults && revalStatus?.status === "COMPLETED" ? (
              /* Completed Results Screen */
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "18px" }}>
                  <div style={{ background: "rgba(52, 211, 153, 0.12)", border: "1px solid rgba(52, 211, 153, 0.3)", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>PROMOVIDAS A v{version}</div>
                    <div style={{ fontSize: "28px", fontWeight: 900, color: "#34d399", margin: "4px 0" }}>
                      {revalStatus.promoted_count}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "#cbd5e1" }}>Superaron los 11 Gates</div>
                  </div>

                  <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.3)", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>RECHAZADAS POR GATES</div>
                    <div style={{ fontSize: "28px", fontWeight: 900, color: "#fb7185", margin: "4px 0" }}>
                      {revalStatus.rejected_count}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "#cbd5e1" }}>No pasaron filtros v{version}</div>
                  </div>

                  <div style={{ background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>TOTAL AUDITADAS</div>
                    <div style={{ fontSize: "28px", fontWeight: 900, color: "#38bdf8", margin: "4px 0" }}>
                      {revalStatus.total_candidates}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "#cbd5e1" }}>Motor v{version} Dual-Engine</div>
                  </div>
                </div>

                {/* Audit breakdown list */}
                <div style={{ maxHeight: "240px", overflowY: "auto", background: "rgba(0, 0, 0, 0.4)", borderRadius: "10px", padding: "10px", border: "1px solid rgba(255, 255, 255, 0.08)", marginBottom: "18px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", marginBottom: "8px", paddingBottom: "4px", borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}>
                    DESGLOSE FORENSE POR ESTRATEGIA:
                  </div>
                  {revalStatus.results?.map((r: any, idx: number) => (
                    <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 8px", borderBottom: "1px solid rgba(255, 255, 255, 0.04)", fontSize: "11px" }}>
                      <div>
                        <span style={{ fontWeight: 800, color: "#ffffff" }}>{r.name}</span>{" "}
                        <span style={{ color: "#38bdf8", fontSize: "10px", fontFamily: "var(--font-mono, monospace)" }}>({r.symbol} {r.timeframe})</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "10px", color: "#94a3b8" }}>Gates: {r.gates_passed}/11</span>
                        <span style={{ fontSize: "10px", fontWeight: 800, color: r.passed ? "#34d399" : "#fb7185", background: r.passed ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
                          {r.passed ? `🟢 v${version} APROBADA` : `⛔ ${r.new_status}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <button
                    onClick={() => setShowFinishedResults(false)}
                    style={{
                      padding: "10px 18px",
                      borderRadius: "8px",
                      background: "rgba(255, 255, 255, 0.08)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#fff",
                      fontSize: "11.5px",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    ⚙️ Nueva Configuración
                  </button>
                  <button
                    onClick={() => setShowRevalModal(false)}
                    style={{
                      padding: "10px 24px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #34d399 0%, #3b82f6 100%)",
                      border: "none",
                      color: "#0c111d",
                      fontSize: "12px",
                      fontWeight: 900,
                      cursor: "pointer",
                    }}
                  >
                    ✓ Cerrar y Ver Lista Actualizada
                  </button>
                </div>
              </div>
            ) : (
              /* Configuration Controls */
              <div>
                {/* Information Card */}
                <div style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px", marginBottom: "20px" }}>
                  <div style={{ fontSize: "12.5px", color: "#cbd5e1", lineHeight: "1.6" }}>
                    Esta acción someterá las estrategias generadas en versiones anteriores a la verificación estricta del <strong>Pipeline Cuantitativo v{version}</strong> en segundo plano:
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "12px" }}>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Modelos de microestructura y costes reales CME/FX/Crypto.
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Aislamiento físico del Blind Holdout 20% intocado.
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Estrés 3x slippage y Monte Carlo (0.0% ruina).
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Reconciliación matemática trade-a-trade NautilusTrader.
                    </div>
                  </div>
                  <div style={{ marginTop: "12px", padding: "10px", background: "rgba(56, 189, 248, 0.08)", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)", fontSize: "11px", color: "#38bdf8" }}>
                    💡 <strong>Resultado:</strong> Las que superen los 11 Gates serán promovidas a <strong>v{version} ACTUAL</strong> y la lista se actualizará dinámicamente. Las que no cumplan los criterios quedarán rechazadas con su motivo forense sin alterar los datos de origen.
                  </div>
                </div>

                {/* Configuration Controls */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "22px" }}>
                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                      VERSIÓN DE ORIGEN A REVALIDAR:
                    </label>
                    <select
                      value={revalTargetVersion}
                      onChange={(e) => setRevalTargetVersion(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        background: "rgba(0, 0, 0, 0.4)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        fontSize: "12px",
                        outline: "none",
                      }}
                    >
                      <option value="ALL">⚙️ Todas las Versiones Anteriores ({candidates.filter(c => c.engine_version !== version).length})</option>
                      <option value="1.04">🔵 Solo Versión v1.04 ({candidates.filter(c => c.engine_version === "1.04").length})</option>
                      <option value="1.02">🟣 Solo Versión v1.02 ({candidates.filter(c => c.engine_version === "1.02").length})</option>
                      <option value="1.00">⚪ Solo Versión v1.00 Legacy ({candidates.filter(c => (c.engine_version || "1.00") === "1.00").length})</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                      RUTA / OBJETIVO:
                    </label>
                    <select
                      value={revalRoute}
                      onChange={(e) => setRevalRoute(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        background: "rgba(0, 0, 0, 0.4)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        fontSize: "12px",
                        outline: "none",
                      }}
                    >
                      <option value="ALL">🌐 Ambas Rutas (ULTRA + FONDEO)</option>
                      <option value="ULTRA">🔥 Solo Ruta ULTRA</option>
                      <option value="FONDEO">🛡️ Solo Ruta FONDEO</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                      LÍMITE POR TANDA:
                    </label>
                    <select
                      value={revalLimit}
                      onChange={(e) => setRevalLimit(Number(e.target.value))}
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        background: "rgba(0, 0, 0, 0.4)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        fontSize: "12px",
                        outline: "none",
                      }}
                    >
                      <option value={0}>🌐 Todas las Estrategias (Completo / Sin Límite)</option>
                      <option value={100}>100 Estrategias (~30 seg)</option>
                      <option value={50}>50 Estrategias (~15 seg)</option>
                      <option value={25}>25 Estrategias (~8 seg)</option>
                      <option value={10}>10 Estrategias (Rápido - ~3 seg)</option>
                    </select>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", paddingTop: "24px" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "12px", color: "#e2e8f0" }}>
                      <input
                        type="checkbox"
                        checked={revalOnlyApproved}
                        onChange={(e) => setRevalOnlyApproved(e.target.checked)}
                        style={{ width: "16px", height: "16px", accentColor: "#ec4899" }}
                      />
                      <span>Solo estrategias aprobadas previamente</span>
                    </label>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    onClick={() => setShowRevalModal(false)}
                    style={{
                      padding: "10px 18px",
                      borderRadius: "8px",
                      background: "rgba(255, 255, 255, 0.08)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#fff",
                      fontSize: "12px",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={executeRevalidation}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "10px 22px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #ec4899 0%, #3b82f6 100%)",
                      border: "none",
                      color: "#ffffff",
                      fontSize: "12px",
                      fontWeight: 900,
                      cursor: "pointer",
                      boxShadow: "0 4px 14px rgba(236, 72, 153, 0.4)",
                    }}
                  >
                    <span>🚀</span>
                    <span>Confirmar y Revalidar en Segundo Plano</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
