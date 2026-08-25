"use client";

import React, { useState, useEffect } from "react";
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
} from "lucide-react";
import { getCertifiedMetaStrategies, CertifiedMetaStrategy } from "@/lib/api";

export default function PortfolioPage() {
  const [metaStrategies, setMetaStrategies] = useState<CertifiedMetaStrategy[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<CertifiedMetaStrategy | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadMetaStrategies();
  }, []);

  async function loadMetaStrategies() {
    setLoading(true);
    setErrorMsg(null);
    try {
      // LLAMADA DIRECTA A GET /api/v2/certified/meta-strategies (ZERO MOCKS)
      const data = await getCertifiedMetaStrategies();
      setMetaStrategies(data);
      if (data.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(data[0]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar meta-estrategias certificadas.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <PieChart className="w-7 h-7 text-indigo-400" />
              <h1 className="text-2xl font-bold tracking-tight">Página 6: Meta-Estrategia Ensamblada & Portfolio Studio</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Portafolios multiactivo optimizados. Requiere que el 100% de componentes tengan certificación APPROVED_CURRENT_ENGINE.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-950 text-indigo-300 border border-indigo-800">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              100% v5.3.0 Components
            </span>
            <button
              onClick={loadMetaStrategies}
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
              <p className="font-semibold text-sm">Error de Carga de Meta-Estrategias:</p>
              <p className="text-xs text-rose-300 mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Meta-Strategies List */}
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
                  const isSelected = selectedPortfolio?.meta_strategy_id === meta.meta_strategy_id;
                  return (
                    <button
                      key={meta.meta_strategy_id}
                      onClick={() => setSelectedPortfolio(meta)}
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

          {/* Right Column: Meta-Strategy Details & Component Breakdown */}
          <div className="lg:col-span-2 space-y-6">
            {selectedPortfolio ? (
              <>
                {/* Meta-Strategy Header Card */}
                <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <h3 className="font-bold text-slate-100 text-base">{selectedPortfolio.name || selectedPortfolio.meta_strategy_id}</h3>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Componentes: <span className="text-slate-200 font-semibold">{selectedPortfolio.components.length} estrategias</span> | Motor:{" "}
                        <span className="text-slate-200 font-mono font-semibold">v{selectedPortfolio.engine_version}</span>
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-indigo-950/80 border border-indigo-700 text-indigo-300 text-xs font-mono font-semibold self-start sm:self-auto">
                      {selectedPortfolio.status}
                    </span>
                  </div>

                  {/* Combined Metrics */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">Profit Factor Combinado</span>
                      <span className="text-lg font-bold text-emerald-400">
                        {selectedPortfolio.combined_profit_factor ? selectedPortfolio.combined_profit_factor.toFixed(2) : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">Sharpe Ratio Combinado</span>
                      <span className="text-lg font-bold text-indigo-300">
                        {selectedPortfolio.combined_sharpe_ratio ? selectedPortfolio.combined_sharpe_ratio.toFixed(2) : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">Max Drawdown Portafolio</span>
                      <span className="text-lg font-bold text-rose-400">
                        {selectedPortfolio.combined_max_drawdown_pct ? `${selectedPortfolio.combined_max_drawdown_pct.toFixed(2)}%` : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">CAGR Anual Combinado</span>
                      <span className="text-lg font-bold text-slate-100 font-mono">
                        {selectedPortfolio.combined_cagr !== null && selectedPortfolio.combined_cagr !== undefined
                          ? `${(selectedPortfolio.combined_cagr * 100).toFixed(2)}%`
                          : "N/A"}
                      </span>
                    </div>
                  </div>

                  {/* Components Allocation Breakdown */}
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Sliders className="w-4 h-4 text-indigo-400" />
                      Desglose de Alphas Componentes (100% APPROVED_CURRENT_ENGINE)
                    </h4>

                    <div className="space-y-2">
                      {selectedPortfolio.components.map((comp) => (
                        <div
                          key={comp.strategy_id}
                          className="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800 gap-2"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-xs text-indigo-300">{comp.name || comp.strategy_id}</span>
                              <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-400">
                                {comp.symbol} · {comp.timeframe}
                              </span>
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono truncate">
                              Ledger Hash: {comp.ledger_hash || "N/A"}
                            </div>
                          </div>

                          <div className="flex items-center gap-3 self-end sm:self-auto">
                            <div className="text-right">
                              <span className="text-[10px] text-slate-500 block">Ponderación</span>
                              <span className="text-xs font-bold text-emerald-400 font-mono">
                                {(comp.weight * 100).toFixed(1)}%
                              </span>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 text-[10px] font-mono">
                              {comp.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Portfolio Merkle Proofs */}
                  <div className="p-3.5 bg-slate-950/90 rounded-lg border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Hash className="w-3.5 h-3.5 text-indigo-400" />
                        Sellado Criptográfico del Portafolio
                      </span>
                      <span className="text-[11px] text-indigo-300 font-mono flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        Ledger Combinado Activo
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                      <div className="truncate">
                        <span className="text-slate-500">Portfolio Hash: </span>
                        <span className="text-slate-300">{selectedPortfolio.portfolio_hash || "N/A"}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">Combined Ledger: </span>
                        <span className="text-indigo-300">{selectedPortfolio.combined_ledger_hash || "N/A"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="py-20 text-center text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
                Selecciona una meta-estrategia de la lista para ver su composición y métricas combinadas.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
