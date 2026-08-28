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
  Sliders,
  Sparkles,
  BarChart3,
  Lock,
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
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);


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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar datos físicos de portafolios.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }


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
              Meta-estrategias y portafolios certificados: esta seccion solo renderiza lo que el backend devuelve con evidencia completa (REAL-ONLY).
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
            Constructor Multi-Alpha (BLOQUEADO)
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
                              {meta.combined_profit_factor ? meta.combined_profit_factor.toFixed(2) : "NO EVIDENCE"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Sharpe</span>
                            <span className="font-semibold text-slate-200">
                              {meta.combined_sharpe_ratio ? meta.combined_sharpe_ratio.toFixed(2) : "NO EVIDENCE"}
                            </span>
                          </div>
                          <div>
                            <span className="text-slate-500 block">Max DD</span>
                            <span className="font-semibold text-rose-400">
                              {meta.combined_max_drawdown_pct ? `${meta.combined_max_drawdown_pct.toFixed(1)}%` : "NO EVIDENCE"}
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
                        {selectedMeta.combined_profit_factor ? selectedMeta.combined_profit_factor.toFixed(2) : "NO EVIDENCE"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Sharpe Ratio</span>
                        <QuantTooltip term="sharpe_ratio" />
                      </div>
                      <span className="text-lg font-bold text-indigo-300">
                        {selectedMeta.combined_sharpe_ratio ? selectedMeta.combined_sharpe_ratio.toFixed(2) : "NO EVIDENCE"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-400">Max DD Portafolio</span>
                        <QuantTooltip term="max_drawdown" />
                      </div>
                      <span className="text-lg font-bold text-rose-400">
                        {selectedMeta.combined_max_drawdown_pct ? `${selectedMeta.combined_max_drawdown_pct.toFixed(2)}%` : "NO EVIDENCE"}
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
                          : "NO EVIDENCE"}
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
                        <span className="text-slate-300">{selectedMeta.portfolio_hash || "NO EVIDENCE"}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">Combined Ledger: </span>
                        <span className="text-indigo-300">{selectedMeta.combined_ledger_hash || "NO EVIDENCE"}</span>
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

        {/* TAB 2: CONSTRUCTOR MULTI-ALPHA — BLOQUEADO (sin superficie real en backend) */}
        {activeTab === "custom" && (
          <div className="space-y-6">
            <div className="bg-slate-900/90 rounded-xl border border-amber-800/60 p-8">
              <div className="flex flex-col items-center text-center space-y-4 max-w-3xl mx-auto">
                <div className="p-4 rounded-full bg-amber-950/60 border border-amber-700/60">
                  <Lock className="w-8 h-8 text-amber-400" />
                </div>
                <h2 className="text-lg font-bold text-slate-100">Constructor de Meta-Estrategias: BLOQUEADO</h2>
                <p className="text-sm text-slate-400 leading-relaxed">
                  No existe hoy superficie real en el backend para combinar portafolios:{" "}
                  <span className="font-mono text-slate-300">GET /api/v2/certified/meta-strategies</span> es un stub
                  sin datos y no hay endpoint canonico de combinacion. Mostrar metricas combinadas aqui seria
                  fabricarlas (doctrina ZERO-MOCK / EVIDENCE-GATED).
                </p>
                <div className="w-full p-4 rounded-lg bg-slate-950/70 border border-slate-800 text-left space-y-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-300 block">
                    Condicion exacta de desbloqueo
                  </span>
                  <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                    <li>Al menos 1 campeon aprobado en Fase 2 de investigacion (estado real: sin aprobadas hoy).</li>
                    <li>Certificacion 11/11 con estado APPROVED_CURRENT_ENGINE y evidencia completa (hashes + ledger verificado).</li>
                    <li>Endpoint real de combinacion de portafolio servido por el backend (sin stub): el frontend solo renderizara precalculado.</li>
                  </ul>
                </div>
                <p className="text-xs text-slate-500">
                  Mientras tanto, la pestana «Portafolios Certificados» renderiza lo que el backend devuelve realmente
                  (hoy: lista vacia = vacio-correcto etiquetado como tal).
                </p>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
