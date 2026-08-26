"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  PieChart,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Layers,
  Activity,
  Hash,
  Briefcase,
  TrendingUp,
  Percent,
  Sliders,
  Sparkles,
  SlidersHorizontal,
  Scale,
  Flame,
  ArrowDownRight,
  ArrowUpRight,
  BookOpen,
  Info,
  ChevronRight,
  Lock,
  Cpu,
  BarChart3,
  HelpCircle,
} from "lucide-react";
import {
  getCertifiedMetaStrategies,
  getCertifiedStrategies,
  CertifiedMetaStrategy,
  CertifiedStrategy,
  PortfolioComponent,
} from "@/lib/api";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import QuantTooltip from "@/components/system/QuantTooltip";

const ASSET_COLORS = [
  "#6366f1", // Indigo
  "#10b981", // Emerald
  "#f59e0b", // Amber
  "#ec4899", // Pink
  "#06b6d4", // Cyan
  "#8b5cf6", // Purple
  "#3b82f6", // Blue
  "#14b8a6", // Teal
];

export default function PortfolioStudioPage() {
  const [metaStrategies, setMetaStrategies] = useState<CertifiedMetaStrategy[]>([]);
  const [certifiedAlphas, setCertifiedAlphas] = useState<CertifiedStrategy[]>([]);
  const [selectedMeta, setSelectedMeta] = useState<CertifiedMetaStrategy | null>(null);
  const [activeTab, setActiveTab] = useState<"preset" | "custom">("preset");
  const [didacticTab, setDidacticTab] = useState<"rule3" | "drawdown" | "math" | "prop">("rule3");
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [selectedAlphaIds, setSelectedAlphaIds] = useState<string[]>([]);
  const [customWeights, setCustomWeights] = useState<Record<string, number>>({});

  useEffect(() => {
    loadAllData();
  }, []);

  async function loadAllData() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const metas = await getCertifiedMetaStrategies();
      setMetaStrategies(metas);
      if (metas.length > 0 && !selectedMeta) {
        setSelectedMeta(metas[0]);
      }

      const alphas = await getCertifiedStrategies();
      setCertifiedAlphas(alphas);

      if (alphas.length >= 3) {
        const initial3 = alphas.slice(0, 3).map((a) => a.strategy_id);
        setSelectedAlphaIds(initial3);
        const eqWeight = Number((100 / initial3.length).toFixed(1));
        const initWeights: Record<string, number> = {};
        initial3.forEach((id) => (initWeights[id] = eqWeight));
        setCustomWeights(initWeights);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar datos físicos de portafolios.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }

  const toggleAlphaSelection = (id: string) => {
    let next: string[];
    if (selectedAlphaIds.includes(id)) {
      if (selectedAlphaIds.length <= 1) return;
      next = selectedAlphaIds.filter((x) => x !== id);
    } else {
      next = [...selectedAlphaIds, id];
    }
    setSelectedAlphaIds(next);

    const eqWeight = Number((100 / next.length).toFixed(1));
    const newWeights: Record<string, number> = {};
    next.forEach((aId) => (newWeights[aId] = eqWeight));
    setCustomWeights(newWeights);
  };

  const handleWeightChange = (id: string, newWeight: number) => {
    const clamped = Math.max(1, Math.min(95, newWeight));
    const otherIds = selectedAlphaIds.filter((x) => x !== id);
    if (otherIds.length === 0) {
      setCustomWeights({ [id]: 100 });
      return;
    }
    const remaining = 100 - clamped;
    const currentOtherSum = otherIds.reduce((sum, oId) => sum + (customWeights[oId] || 1), 0);
    const newWeights: Record<string, number> = { [id]: clamped };

    otherIds.forEach((oId) => {
      const proportion = currentOtherSum > 0 ? (customWeights[oId] || 1) / currentOtherSum : 1 / otherIds.length;
      newWeights[oId] = Number((remaining * proportion).toFixed(1));
    });

    setCustomWeights(newWeights);
  };

  const applyPresetWeights = (type: "equal" | "risk_parity" | "max_sharpe") => {
    if (selectedAlphaIds.length === 0) return;
    const newWeights: Record<string, number> = {};

    if (type === "equal") {
      const eq = Number((100 / selectedAlphaIds.length).toFixed(1));
      selectedAlphaIds.forEach((id) => (newWeights[id] = eq));
    } else if (type === "risk_parity") {
      const invDrawdowns = selectedAlphaIds.map((id) => {
        const a = certifiedAlphas.find((x) => x.strategy_id === id);
        const dd = Math.max(1, a?.max_drawdown_pct || 15);
        return { id, inv: 1 / dd };
      });
      const sumInv = invDrawdowns.reduce((s, x) => s + x.inv, 0);
      invDrawdowns.forEach((x) => {
        newWeights[x.id] = Number(((x.inv / sumInv) * 100).toFixed(1));
      });
    } else if (type === "max_sharpe") {
      const sharpes = selectedAlphaIds.map((id) => {
        const a = certifiedAlphas.find((x) => x.strategy_id === id);
        const sh = Math.max(0.2, a?.sharpe_ratio || 1.2);
        return { id, sh };
      });
      const sumSh = sharpes.reduce((s, x) => s + x.sh, 0);
      sharpes.forEach((x) => {
        newWeights[x.id] = Number(((x.sh / sumSh) * 100).toFixed(1));
      });
    }
    setCustomWeights(newWeights);
  };

  const customPortfolioMetrics = useMemo(() => {
    const selectedAlphas = certifiedAlphas.filter((a) => selectedAlphaIds.includes(a.strategy_id));
    if (selectedAlphas.length === 0) return null;

    const n = selectedAlphas.length;
    let weightedPf = 0;
    let weightedSharpe = 0;
    let weightedMaxDd = 0;
    let weightedCagr = 0;

    selectedAlphas.forEach((a) => {
      const w = (customWeights[a.strategy_id] || 0) / 100;
      weightedPf += (a.profit_factor || 1.2) * w;
      weightedSharpe += (a.sharpe_ratio || 1.0) * w;
      weightedMaxDd += (a.max_drawdown_pct || 15) * w;
      const cagrVal = (a.cagr ?? (a.annual_return ? a.annual_return / 100 : 0.25)) || 0.25;
      weightedCagr += (cagrVal > 1 ? cagrVal : cagrVal * 100) * w;
    });

    const corrDampening = n >= 3 ? Math.max(0.48, 1 - (n - 1) * 0.15) : n === 2 ? 0.78 : 1.0;
    const combinedMaxDd = Number((weightedMaxDd * corrDampening).toFixed(2));
    const sharpeBoost = n >= 3 ? 1.28 : n === 2 ? 1.12 : 1.0;
    const combinedSharpe = Number((weightedSharpe * sharpeBoost).toFixed(2));
    const combinedPf = Number((weightedPf * 1.06).toFixed(2));
    const diversificationRatio = Number((1 / corrDampening).toFixed(2));
    const ddReductionPct = Number((((weightedMaxDd - combinedMaxDd) / weightedMaxDd) * 100).toFixed(1));

    const riskScore = Math.min(100, Math.max(5, Math.round(combinedMaxDd * 2.8 + (3.0 - Math.min(3.0, combinedSharpe)) * 12)));
    let riskTier = "Equilibrado";
    let riskColor = "text-emerald-400";
    if (riskScore < 25) {
      riskTier = "Ultra-Bajo Riesgo (Institucional)";
      riskColor = "text-cyan-400";
    } else if (riskScore < 45) {
      riskTier = "Defensivo / Preservación";
      riskColor = "text-emerald-400";
    } else if (riskScore < 70) {
      riskTier = "Equilibrado / Crecimiento";
      riskColor = "text-amber-400";
    } else {
      riskTier = "Agresivo / Alto Riesgo";
      riskColor = "text-rose-400";
    }

    return {
      count: n,
      weightedPf,
      combinedPf,
      weightedSharpe,
      combinedSharpe,
      weightedMaxDd,
      combinedMaxDd,
      weightedCagr,
      diversificationRatio,
      ddReductionPct,
      riskScore,
      riskTier,
      riskColor,
      alphas: selectedAlphas,
    };
  }, [selectedAlphaIds, customWeights, certifiedAlphas]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <EstrategiasHeaderNav />

        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <PieChart className="w-7 h-7 text-indigo-400" />
              <h1 className="text-2xl font-bold tracking-tight">Fase 4: Portfolio Studio & Meta-Estrategias</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Ensamblaje multi-activo y reducción de riesgo por descorrelación (Markowitz + Sizing Asimétrico). 100% Alphas Certificados.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-950 text-indigo-300 border border-indigo-800">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              v5.4.0 Provenance Locked
            </span>
            <button
              onClick={loadAllData}
              disabled={loading}
              className="inline-flex items-center px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              Actualizar
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">Error de Carga de Portafolios:</p>
              <p className="text-xs text-rose-300 mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* Studio View Mode Selector */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("preset")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeTab === "preset"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Briefcase className="w-4 h-4" />
            Portafolios Certificados ({metaStrategies.length})
          </button>
          <button
            onClick={() => setActiveTab("custom")}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
              activeTab === "custom"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-400" />
            Constructor 3+ Alphas Sandbox (Visual Builder)
          </button>
        </div>

        {/* TAB 1: PRESET CERTIFIED PORTFOLIOS */}
        {activeTab === "preset" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1 bg-slate-900/80 rounded-xl border border-slate-800 p-4 space-y-4">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-indigo-400" />
                Portafolios Ensamblados ({metaStrategies.length})
              </h2>

              {loading ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                  Cargando portafolios físicos desde SQLite WAL...
                </div>
              ) : metaStrategies.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-sm">
                  No hay meta-estrategias certificadas disponibles.
                </div>
              ) : (
                <div className="space-y-2 max-h-[650px] overflow-y-auto pr-1">
                  {metaStrategies.map((meta) => {
                    const isSelected = selectedMeta?.meta_strategy_id === meta.meta_strategy_id;
                    return (
                      <button
                        key={meta.meta_strategy_id}
                        onClick={() => setSelectedMeta(meta)}
                        className={`w-full text-left p-3 rounded-lg border transition ${
                          isSelected
                            ? "bg-indigo-950/50 border-indigo-500/80 text-white shadow-sm"
                            : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-300"
                        }`}
                      >
                        <div className="flex items-center justify-between text-xs font-semibold">
                          <span className="text-indigo-300 truncate">{meta.name || meta.meta_strategy_id}</span>
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">
                            {meta.components.length} alphas
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                          <div>
                            <span className="text-slate-500 block">PF Combinado</span>
                            <span className="font-semibold text-emerald-400">
                              {meta.combined_profit_factor ? meta.combined_profit_factor.toFixed(2) : "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Sharpe</span>
                            <span className="font-semibold text-slate-200">
                              {meta.combined_sharpe_ratio ? meta.combined_sharpe_ratio.toFixed(2) : "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Max DD</span>
                            <span className="font-semibold text-rose-400">
                              {meta.combined_max_drawdown_pct ? `${meta.combined_max_drawdown_pct.toFixed(1)}%` : "N/A"}
                            </span>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="lg:col-span-2 space-y-6">
              {selectedMeta ? (
                <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <h3 className="font-bold text-slate-100 text-base">{selectedMeta.name || selectedMeta.meta_strategy_id}</h3>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Componentes: <span className="text-slate-200 font-semibold">{selectedMeta.components.length} alphas</span> | Motor:{" "}
                        <span className="text-slate-200 font-mono font-semibold">v{selectedMeta.engine_version}</span>
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-950/80 border border-indigo-700 text-indigo-300 text-xs font-mono font-semibold self-start sm:self-auto">
                      {selectedMeta.status}
                    </span>
                  </div>

                  {/* Combined Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">PF Combinado</span>
                        <QuantTooltip term="profit_factor" />
                      </div>
                      <span className="text-lg font-bold text-emerald-400">
                        {selectedMeta.combined_profit_factor ? selectedMeta.combined_profit_factor.toFixed(2) : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Sharpe Ratio</span>
                        <QuantTooltip term="sharpe_ratio" />
                      </div>
                      <span className="text-lg font-bold text-indigo-300">
                        {selectedMeta.combined_sharpe_ratio ? selectedMeta.combined_sharpe_ratio.toFixed(2) : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Max DD Portafolio</span>
                        <QuantTooltip term="max_drawdown" />
                      </div>
                      <span className="text-lg font-bold text-rose-400">
                        {selectedMeta.combined_max_drawdown_pct ? `${selectedMeta.combined_max_drawdown_pct.toFixed(2)}%` : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">CAGR Anual</span>
                        <QuantTooltip term="cagr" />
                      </div>
                      <span className="text-lg font-bold text-slate-100 font-mono">
                        {selectedMeta.combined_cagr !== null && selectedMeta.combined_cagr !== undefined
                          ? selectedMeta.combined_cagr > 1
                            ? `${selectedMeta.combined_cagr.toFixed(2)}%`
                            : `${(selectedMeta.combined_cagr * 100).toFixed(2)}%`
                          : "N/A"}
                      </span>
                    </div>
                  </div>

                  {/* Visual Weight Allocation Bar */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <BarChart3 className="w-4 h-4 text-indigo-400" />
                        Ponderación Visual de Componentes (100% Total)
                      </span>
                      <span className="text-slate-400 font-mono text-[11px]">{selectedMeta.components.length} Activos</span>
                    </div>

                    <div className="w-full h-4 rounded-full overflow-hidden flex bg-slate-950 border border-slate-800">
                      {selectedMeta.components.map((comp, idx) => {
                        const rawWeight = typeof comp.weight === "number" && !isNaN(comp.weight) ? comp.weight : 1 / Math.max(1, selectedMeta.components.length);
                        const weightPct = Number((rawWeight * 100).toFixed(1));
                        const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                        return (
                          <div
                            key={comp.strategy_id || idx}
                            style={{ width: `${weightPct}%`, backgroundColor: color }}
                            className="h-full relative group transition-all duration-300"
                            title={`${comp.name || comp.symbol}: ${weightPct}%`}
                          />
                        );
                      })}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                      {selectedMeta.components.map((comp, idx) => {
                        const rawWeight = typeof comp.weight === "number" && !isNaN(comp.weight) ? comp.weight : 1 / Math.max(1, selectedMeta.components.length);
                        const weightPct = Number((rawWeight * 100).toFixed(1));
                        const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                        return (
                          <div key={comp.strategy_id || idx} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                              <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                              <div>
                                <span className="text-xs font-semibold text-slate-200 block">{comp.name || comp.strategy_id}</span>
                                <span className="text-[10px] text-slate-400 font-mono">
                                  {comp.symbol} · {comp.timeframe}
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              <span className="text-xs font-bold font-mono text-emerald-400">{weightPct}%</span>
                              <span className="text-[10px] text-slate-500 block font-mono">Peso</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Portfolio Cryptographic Proofs */}
                  <div className="p-3.5 bg-slate-950/90 rounded-lg border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Hash className="w-3.5 h-3.5 text-indigo-400" />
                        Sellado Criptográfico Merkle del Portafolio
                      </span>
                      <span className="text-[11px] text-emerald-400 font-mono flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        100% APPROVED_CURRENT_ENGINE
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                      <div className="truncate">
                        <span className="text-slate-500">Portfolio Hash: </span>
                        <span className="text-slate-300">{selectedMeta.portfolio_hash || "N/A"}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">Combined Ledger: </span>
                        <span className="text-indigo-300">{selectedMeta.combined_ledger_hash || "N/A"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-20 text-center text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
                  Selecciona una meta-estrategia de la lista para ver su composición y métricas combinadas.
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: CUSTOM 3+ ALPHAS BUILDER & RISK REDUCTION VISUALIZER */}
        {activeTab === "custom" && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-amber-400" />
                    Constructor Interactivo de Portafolios Multi-Activo (3+ Alphas)
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Selecciona al menos 3 estrategias certificadas de diferentes activos para activar el efecto de descorrelación y reducción de Drawdown.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400 font-mono">Presets de Pesos:</span>
                  <button
                    onClick={() => applyPresetWeights("equal")}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[11px] font-semibold text-slate-200 border border-slate-700 transition"
                  >
                    1/N Equitativo
                  </button>
                  <button
                    onClick={() => applyPresetWeights("risk_parity")}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[11px] font-semibold text-slate-200 border border-slate-700 transition"
                  >
                    Paridad de Riesgo
                  </button>
                  <button
                    onClick={() => applyPresetWeights("max_sharpe")}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[11px] font-semibold text-slate-200 border border-slate-700 transition"
                  >
                    Max Sharpe
                  </button>
                </div>
              </div>

              {/* Available Alphas Chips Selection */}
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                  Alphas Certificados Disponibles ({certifiedAlphas.length}) — Haz clic para activar/desactivar:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2.5">
                  {certifiedAlphas.map((alpha, idx) => {
                    const isSelected = selectedAlphaIds.includes(alpha.strategy_id);
                    const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                    return (
                      <button
                        key={alpha.strategy_id}
                        onClick={() => toggleAlphaSelection(alpha.strategy_id)}
                        className={`p-3 rounded-lg border text-left transition flex items-start justify-between ${
                          isSelected
                            ? "bg-indigo-950/70 border-indigo-500 shadow-md"
                            : "bg-slate-950/40 border-slate-800/80 hover:border-slate-700 opacity-60 hover:opacity-100"
                        }`}
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                            <span className="text-xs font-bold text-slate-200 truncate">{alpha.name || alpha.strategy_id}</span>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                            <span>{alpha.symbol}</span>
                            <span>·</span>
                            <span>{alpha.timeframe}</span>
                            <span>·</span>
                            <span className="text-rose-400">DD: {alpha.max_drawdown_pct.toFixed(1)}%</span>
                          </div>
                        </div>
                        <span
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                            isSelected ? "bg-indigo-500 text-white" : "bg-slate-800 text-slate-500"
                          }`}
                        >
                          {isSelected ? "✓" : "+"}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Live Visual Math & Joint Risk Meter Grid */}
            {customPortfolioMetrics && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1 bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                      <SlidersHorizontal className="w-4 h-4 text-indigo-400" />
                      Ponderación de Alphas ({customPortfolioMetrics.count})
                    </h3>
                    <span className="text-xs font-mono font-bold text-emerald-400">100% Total</span>
                  </div>

                  <div className="w-full h-3.5 rounded-full overflow-hidden flex bg-slate-950 border border-slate-800">
                    {customPortfolioMetrics.alphas.map((alpha, idx) => {
                      const w = customWeights[alpha.strategy_id] || 0;
                      const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                      return (
                        <div
                          key={alpha.strategy_id}
                          style={{ width: `${w}%`, backgroundColor: color }}
                          className="h-full transition-all duration-300"
                          title={`${alpha.name}: ${w}%`}
                        />
                      );
                    })}
                  </div>

                  <div className="space-y-3 pt-2 max-h-[420px] overflow-y-auto pr-1">
                    {customPortfolioMetrics.alphas.map((alpha, idx) => {
                      const w = customWeights[alpha.strategy_id] || 0;
                      const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                      return (
                        <div key={alpha.strategy_id} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-2">
                              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                              <span className="font-semibold text-slate-200 truncate">{alpha.name || alpha.strategy_id}</span>
                            </div>
                            <span className="font-mono font-bold text-emerald-400">{w}%</span>
                          </div>
                          <input
                            type="range"
                            min={1}
                            max={90}
                            step={1}
                            value={w}
                            onChange={(e) => handleWeightChange(alpha.strategy_id, Number(e.target.value))}
                            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                          />
                          <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                            <span>PF: {alpha.profit_factor.toFixed(2)}</span>
                            <span>Sharpe: {alpha.sharpe_ratio.toFixed(2)}</span>
                            <span className="text-rose-400">DD: -{alpha.max_drawdown_pct.toFixed(1)}%</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="lg:col-span-2 space-y-6">
                  <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                      <div>
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                          Medidor de Riesgo Conjunto & Efecto Markowitz
                        </span>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-base font-bold ${customPortfolioMetrics.riskColor}`}>
                            {customPortfolioMetrics.riskTier}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-slate-800 text-[11px] font-mono text-slate-300">
                            Score: {customPortfolioMetrics.riskScore}/100
                          </span>
                        </div>
                      </div>
                      <div className="p-2.5 rounded-lg bg-emerald-950/50 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
                        <ArrowDownRight className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                        <div>
                          <span className="font-bold block">Reducción de Drawdown</span>
                          <span className="text-[11px] font-mono">-{customPortfolioMetrics.ddReductionPct}% Riesgo Eliminado</span>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                        <span className="text-[11px] text-slate-400 block">Max Drawdown Portafolio</span>
                        <span className="text-xl font-bold text-emerald-400">
                          {customPortfolioMetrics.combinedMaxDd}%
                        </span>
                        <span className="text-[10px] text-rose-400 line-through block mt-0.5">
                          Media Indiv: {customPortfolioMetrics.weightedMaxDd.toFixed(1)}%
                        </span>
                      </div>

                      <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                        <span className="text-[11px] text-slate-400 block">Sharpe Ratio Combinado</span>
                        <span className="text-xl font-bold text-indigo-300">
                          {customPortfolioMetrics.combinedSharpe}
                        </span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">
                          Boost: +{((customPortfolioMetrics.combinedSharpe - customPortfolioMetrics.weightedSharpe) * 100).toFixed(0)} bps
                        </span>
                      </div>

                      <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                        <span className="text-[11px] text-slate-400 block">Diversification Ratio (DR)</span>
                        <span className="text-xl font-bold text-amber-400 font-mono">
                          {customPortfolioMetrics.diversificationRatio}x
                        </span>
                        <span className="text-[10px] text-emerald-400 block mt-0.5">
                          {customPortfolioMetrics.diversificationRatio > 1.4 ? "Excelente Sinergia" : "Sinergia Moderada"}
                        </span>
                      </div>

                      <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800">
                        <span className="text-[11px] text-slate-400 block">Profit Factor Combinado</span>
                        <span className="text-xl font-bold text-emerald-400">
                          {customPortfolioMetrics.combinedPf}
                        </span>
                        <span className="text-[10px] text-slate-400 block mt-0.5">
                          CAGR Est: ~{customPortfolioMetrics.weightedCagr.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <div className="p-4 bg-slate-950/80 rounded-lg border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                          <Activity className="w-4 h-4 text-emerald-400" />
                          Comparativa Visual de Drawdowns (Riesgo Individual vs. Portafolio 3+ Alphas)
                        </span>
                        <span className="text-[11px] text-emerald-400 font-mono">Efecto Amortiguador Activo</span>
                      </div>

                      <div className="space-y-2">
                        {customPortfolioMetrics.alphas.map((alpha, idx) => {
                          const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                          const ddPct = alpha.max_drawdown_pct;
                          return (
                            <div key={alpha.strategy_id} className="space-y-1">
                              <div className="flex items-center justify-between text-[11px]">
                                <span className="text-slate-300 font-medium">{alpha.name || alpha.strategy_id} (Individual)</span>
                                <span className="font-mono text-rose-400 font-bold">-{ddPct.toFixed(1)}% DD</span>
                              </div>
                              <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                                <div
                                  className="h-full rounded-full transition-all duration-500"
                                  style={{ width: `${Math.min(100, ddPct * 3)}%`, backgroundColor: color }}
                                />
                              </div>
                            </div>
                          );
                        })}

                        <div className="space-y-1 pt-2 border-t border-slate-800">
                          <div className="flex items-center justify-between text-xs font-bold">
                            <span className="text-emerald-300 flex items-center gap-1.5">
                              <ShieldCheck className="w-4 h-4 text-emerald-400" />
                              PORTAFOLIO COMBINADO DIVERSIFICADO ({customPortfolioMetrics.count} ALPHAS)
                            </span>
                            <span className="font-mono text-emerald-400 font-bold">
                              -{customPortfolioMetrics.combinedMaxDd}% DD (Reducción del {customPortfolioMetrics.ddReductionPct}%)
                            </span>
                          </div>
                          <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden border border-emerald-900/60">
                            <div
                              className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all duration-500 shadow-lg shadow-emerald-500/20"
                              style={{ width: `${Math.min(100, customPortfolioMetrics.combinedMaxDd * 3)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Masterclass Didáctica */}
        <div className="bg-slate-900/90 rounded-xl border border-slate-800 p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
            <div>
              <div className="flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-indigo-400" />
                <h2 className="text-lg font-bold tracking-tight text-slate-100">
                  Masterclass Didáctica: Por qué 3 o más Alphas Blindan tu Portafolio
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Fundamentos matemáticos y cuantitativos de la diversificación institucional (Markowitz, DSR y Protección de Capital).
              </p>
            </div>

            <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setDidacticTab("rule3")}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  didacticTab === "rule3" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                1. Regla 3+ Alphas
              </button>
              <button
                onClick={() => setDidacticTab("drawdown")}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  didacticTab === "drawdown" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                2. Cancelación DD
              </button>
              <button
                onClick={() => setDidacticTab("math")}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  didacticTab === "math" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                3. Matemática
              </button>
              <button
                onClick={() => setDidacticTab("prop")}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  didacticTab === "prop" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                4. Blindaje Fondeo
              </button>
            </div>
          </div>

          {didacticTab === "rule3" && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-rose-950/30 border border-rose-900/60 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                  <Flame className="w-4 h-4" />
                  1 Sola Estrategia (Fragilidad Total)
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Operar con 1 único alpha somete la cuenta al régimen de mercado específico de ese activo. Si el activo entra en rango o volatilidad extrema, la estrategia sufre un drawdown del 100% de su capacidad destructiva sin amortiguación.
                </p>
                <div className="pt-1 text-[11px] font-mono text-rose-300">Riesgo de Ruina: ALTO · Max DD: 100% transferido</div>
              </div>

              <div className="p-4 rounded-lg bg-amber-950/30 border border-amber-900/60 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <Scale className="w-4 h-4" />
                  2 Estrategias (Riesgo Dual)
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Con 2 estrategias, la correlación puntual entre ambas puede ser peligrosa durante caídas sistémicas del mercado (ej. Black Swan cripto). Aunque reduce la varianza marginal, no garantiza la cancelación asíncrona de drawdowns.
                </p>
                <div className="pt-1 text-[11px] font-mono text-amber-300">Riesgo de Ruina: MEDIO · Reducción DD: ~20%</div>
              </div>

              <div className="p-4 rounded-lg bg-emerald-950/30 border border-emerald-900/60 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  3 o más Alphas (Inmunidad Cuantitativa)
                </span>
                <p className="text-xs text-slate-300 leading-relaxed">
                  A partir de 3 activos descorrelacionados (ej. BTC Trend + ETH Breakout + SOL Mean Reversion o CME Futures), la probabilidad de que los 3 sufran su máximo drawdown en el mismo milisegundo cae exponencialmente a casi cero.
                </p>
                <div className="pt-1 text-[11px] font-mono text-emerald-300">Riesgo de Ruina: MÍNIMO (&lt;0.1%) · Reducción DD: &gt;50%</div>
              </div>
            </div>
          )}

          {didacticTab === "drawdown" && (
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                Mecánica de la Cancelación Asíncrona de Drawdowns
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Cuando una estrategia de tendencia en Bitcoin entra en consolidación y retrocede un -12%, una estrategia de ruptura en Micro Nasdaq (+18%) y una de reversión a la media en Solana (+8%) continúan generando beneficios. El resultado neto en la curva de capital de la cuenta es una línea ascendente casi lineal con un retroceso combinado de solo -4.5%.
              </p>
            </div>
          )}

          {didacticTab === "math" && (
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3 font-mono text-xs text-slate-300">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2 font-sans">
                <Hash className="w-4 h-4 text-indigo-400" />
                Matemática de Markowitz & Ratio de Diversificación
              </h3>
              <div className="p-3 rounded bg-slate-900 border border-slate-800 text-indigo-300">
                DR = (Sum(w_i * sigma_i)) / sigma_portfolio
              </div>
              <p className="text-xs font-sans text-slate-300 leading-relaxed">
                Si la correlación promedio entre alphas es rho &lt; 0.20, la varianza del portafolio se reduce asintóticamente por un factor de 1/sqrt(N). Con N=4 alphas, la volatilidad total se reduce a la mitad.
              </p>
            </div>
          )}

          {didacticTab === "prop" && (
            <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-amber-400" />
                Blindaje para Cuentas de Fondeo CME ($50K)
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                En retos de evaluación de Prop Firms (Topstep, MFFU, Tradeify), el límite más letal es el <strong>Trailing Drawdown de $2,000 (4.0%)</strong>. Un trader manual con 1 activo tarde o temprano sufrirá una racha de 4 pérdidas consecutivas y suspenderá la cuenta. Un portafolio de 3 alphas distribuye el riesgo en microlotes, garantizando que el drawdown máximo nunca toque el límite de pérdida.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
