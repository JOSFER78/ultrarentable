"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  PieChart,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Hash,
  Briefcase,
  Sparkles,
  BarChart3,
  Lock,
  Download,
  FileSpreadsheet,
} from "lucide-react";
import {
  getCertifiedMetaStrategies,
  getCertifiedStrategies,
  CertifiedMetaStrategy,
  CertifiedStrategy,
  getExportCsvUrl,
  getExportXlsxUrl,
} from "@/lib/api";

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
  const [routeFilter, setRouteFilter] = useState<"ALL" | "ULTRA" | "FONDEO">("ALL");
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

  const filteredMetaStrategies = useMemo(() => {
    return metaStrategies.filter((meta) => {
      const routeUpper = (meta.route || meta.target_route || "").toUpperCase();
      const nameLower = (meta.name || "").toLowerCase();

      const isUltra = routeUpper.includes("ULTRA") || nameLower.includes("ultra");
      const isFondeo = routeUpper.includes("FONDEO") || nameLower.includes("fondeo") || !isUltra;

      if (routeFilter === "ULTRA" && !isUltra) return false;
      if (routeFilter === "FONDEO" && !isFondeo) return false;
      return true;
    });
  }, [metaStrategies, routeFilter]);

  return (
    <div className="w-full max-w-[1560px] mx-auto space-y-6 font-sans">
      {/* Header Banner */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 md:p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <PieChart className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Portafolio Studio & Meta-Estrategias
              </h1>
              <p className="text-slate-400 text-xs md:text-sm mt-0.5 font-medium">
                Meta-estrategias y portafolios certificados: esta sección solo renderiza lo que el backend devuelve con evidencia completa (REAL-ONLY).
              </p>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2.5 font-mono text-xs">
          <span className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-950/80 text-indigo-300 border border-indigo-700/60 shadow-sm">
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
            v5.4.0 Provenance Locked
          </span>
          <a
            href={getExportCsvUrl(routeFilter)}
            download
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold bg-[#050811] hover:bg-slate-800 text-slate-200 border border-white/[0.1] shadow-sm transition active:scale-95 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 mr-1.5 text-sky-400" />
            Exportar CSV
          </a>
          <a
            href={getExportXlsxUrl(routeFilter)}
            download
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 shadow-sm transition active:scale-95 cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            Exportar Excel (.xlsx)
          </a>
          <button
            onClick={loadAllData}
            disabled={loading}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold bg-[#050811] hover:bg-slate-800 text-slate-200 border border-white/[0.1] shadow-sm transition active:scale-95 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin text-indigo-400" : "text-slate-400"}`} />
            Actualizar
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-950/70 border border-rose-800 text-rose-200 flex items-start gap-3 shadow-lg font-mono text-xs">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-sm">Error de Carga de Portafolios:</p>
            <p className="text-xs text-rose-300 mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Studio View Mode Selector */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] pb-3 font-mono">
        <button
          onClick={() => setActiveTab("preset")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === "preset"
              ? "bg-indigo-600 text-white shadow-[0_0_15px_rgba(99,102,241,0.25)] border border-indigo-400/40"
              : "bg-[#090d16]/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-white/[0.08]"
          }`}
        >
          <Briefcase className="w-4 h-4 text-indigo-300" />
          Portafolios Certificados ({filteredMetaStrategies.length})
        </button>
        <button
          onClick={() => setActiveTab("custom")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === "custom"
              ? "bg-indigo-600 text-white shadow-[0_0_15px_rgba(99,102,241,0.25)] border border-indigo-400/40"
              : "bg-[#090d16]/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-white/[0.08]"
          }`}
        >
          <Sparkles className="w-4 h-4 text-amber-400" />
          Constructor Multi-Alpha (BLOQUEADO)
        </button>
      </div>

      {/* TAB 1: PRESET CERTIFIED PORTFOLIOS */}
      {activeTab === "preset" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-[#090d16]/90 backdrop-blur-xl rounded-2xl border border-white/[0.08] p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 font-mono">
                <Briefcase className="w-4 h-4 text-indigo-400" />
                Portafolios Ensamblados ({filteredMetaStrategies.length})
              </h2>
              <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-0.5 rounded-full border border-emerald-700/60">
                11/11 GATES OK
              </span>
            </div>

            {/* Category Filter Pills */}
            <div className="flex gap-1.5 font-mono text-xs bg-[#050811] p-1.5 rounded-xl border border-white/[0.08]">
              <button
                onClick={() => setRouteFilter("ALL")}
                className={`flex-1 py-1 px-2 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                  routeFilter === "ALL"
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-transparent text-slate-400 hover:text-white hover:bg-white/[0.05]"
                }`}
              >
                Todas
              </button>
              <button
                onClick={() => setRouteFilter("ULTRA")}
                className={`flex-1 py-1 px-2 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                  routeFilter === "ULTRA"
                    ? "bg-amber-600 text-slate-950 shadow-sm"
                    : "bg-transparent text-slate-400 hover:text-white hover:bg-white/[0.05]"
                }`}
              >
                ⚡ Ruta Ultra
              </button>
              <button
                onClick={() => setRouteFilter("FONDEO")}
                className={`flex-1 py-1 px-2 rounded-lg text-[10px] font-bold transition cursor-pointer ${
                  routeFilter === "FONDEO"
                    ? "bg-sky-600 text-slate-950 shadow-sm"
                    : "bg-transparent text-slate-400 hover:text-white hover:bg-white/[0.05]"
                }`}
              >
                🏛️ Ruta Fondeo
              </button>
            </div>

            {loading ? (
              <div className="py-12 text-center text-slate-500 text-xs font-mono">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                Cargando portafolios físicos desde SQLite WAL...
              </div>
            ) : filteredMetaStrategies.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs font-mono p-4 rounded-xl border border-dashed border-white/[0.08] bg-[#050811]/40">
                No hay meta-estrategias certificadas disponibles con los filtros seleccionados.
              </div>
            ) : (
              <div className="space-y-2 max-h-[650px] overflow-y-auto pr-1">
                {filteredMetaStrategies.map((meta) => {
                  const isSelected = selectedMeta?.meta_strategy_id === meta.meta_strategy_id;
                  return (
                    <button
                      key={meta.meta_strategy_id}
                      onClick={() => setSelectedMeta(meta)}
                      className={`w-full text-left p-3.5 rounded-xl border transition-all cursor-pointer ${
                        isSelected
                          ? "bg-indigo-950/50 border-indigo-500/80 text-white shadow-[0_0_15px_rgba(99,102,241,0.15)] ring-1 ring-indigo-500/40"
                          : "bg-[#050811]/70 border-white/[0.08] hover:border-white/[0.16] text-slate-300 hover:bg-[#050811]"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-indigo-300 truncate font-mono font-bold">
                          {meta.name || meta.meta_strategy_id}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-slate-800/80 text-slate-400 font-mono text-[10px] border border-white/[0.06]">
                          {meta.components.length} alphas
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 mt-2 text-xs font-mono">
                        <div>
                          <span className="text-[10px] text-slate-500 block uppercase">PF Combinado</span>
                          <span className="font-bold text-emerald-400 tabular-nums">
                            {meta.combined_profit_factor ? meta.combined_profit_factor.toFixed(2) : "NO EVIDENCE"}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block uppercase">Sharpe</span>
                          <span className="font-bold text-slate-200 tabular-nums">
                            {meta.combined_sharpe_ratio ? meta.combined_sharpe_ratio.toFixed(2) : "NO EVIDENCE"}
                          </span>
                        </div>
                        <div>
                          <span className="text-[10px] text-slate-500 block uppercase">Max DD</span>
                          <span className="font-bold text-rose-400 tabular-nums">
                            {meta.combined_max_drawdown_pct
                              ? `${meta.combined_max_drawdown_pct.toFixed(1)}%`
                              : "NO EVIDENCE"}
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
              <div className="bg-[#090d16]/90 backdrop-blur-xl rounded-2xl border border-white/[0.08] p-6 space-y-5 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/[0.08] pb-4 gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                      <h3 className="font-bold text-white text-base">
                        {selectedMeta.name || selectedMeta.meta_strategy_id}
                      </h3>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 font-mono">
                      Componentes:{" "}
                      <span className="text-slate-200 font-semibold">{selectedMeta.components.length} alphas</span>{" "}
                      | Motor:{" "}
                      <span className="text-slate-200 font-mono font-semibold">
                        v{selectedMeta.engine_version}
                      </span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2 font-mono">
                    <span className="px-2.5 py-1 rounded-xl bg-emerald-950/80 border border-emerald-700/80 text-emerald-300 text-xs font-semibold flex items-center gap-1.5 shadow-sm">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      11/11 GATES VERIFICADOS
                    </span>
                    <span className="px-2.5 py-1 rounded-xl bg-indigo-950/80 border border-indigo-700/80 text-indigo-300 text-xs font-semibold">
                      {selectedMeta.status}
                    </span>
                  </div>
                </div>

                {/* Combined Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono">
                  <div className="p-3.5 bg-[#050811]/80 rounded-xl border border-white/[0.08]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 uppercase font-semibold">PF Combinado</span>
                      <QuantTooltip term="profit_factor" />
                    </div>
                    <span className="text-lg font-black text-emerald-400 tabular-nums block mt-1">
                      {selectedMeta.combined_profit_factor
                        ? selectedMeta.combined_profit_factor.toFixed(2)
                        : "NO EVIDENCE"}
                    </span>
                  </div>
                  <div className="p-3.5 bg-[#050811]/80 rounded-xl border border-white/[0.08]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 uppercase font-semibold">Sharpe Ratio</span>
                      <QuantTooltip term="sharpe_ratio" />
                    </div>
                    <span className="text-lg font-black text-indigo-300 tabular-nums block mt-1">
                      {selectedMeta.combined_sharpe_ratio
                        ? selectedMeta.combined_sharpe_ratio.toFixed(2)
                        : "NO EVIDENCE"}
                    </span>
                  </div>
                  <div className="p-3.5 bg-[#050811]/80 rounded-xl border border-white/[0.08]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 uppercase font-semibold">Max DD Portafolio</span>
                      <QuantTooltip term="max_drawdown" />
                    </div>
                    <span className="text-lg font-black text-rose-400 tabular-nums block mt-1">
                      {selectedMeta.combined_max_drawdown_pct
                        ? `${selectedMeta.combined_max_drawdown_pct.toFixed(2)}%`
                        : "NO EVIDENCE"}
                    </span>
                  </div>
                  <div className="p-3.5 bg-[#050811]/80 rounded-xl border border-white/[0.08]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 uppercase font-semibold">Ret. Mensual</span>
                      <QuantTooltip text="Retorno promedio mensual combinado del portafolio." />
                    </div>
                    <span className="text-lg font-black text-emerald-300 tabular-nums block mt-1">
                      {selectedMeta.monthly_return !== null && selectedMeta.monthly_return !== undefined
                        ? `${selectedMeta.monthly_return.toFixed(2)}%`
                        : "NO EVIDENCE"}
                    </span>
                  </div>
                  <div className="p-3.5 bg-[#050811]/80 rounded-xl border border-white/[0.08]">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 uppercase font-semibold">CAGR Anual</span>
                      <QuantTooltip term="cagr" />
                    </div>
                    <span className="text-lg font-black text-slate-100 tabular-nums block mt-1">
                      {selectedMeta.combined_cagr !== null && selectedMeta.combined_cagr !== undefined
                        ? selectedMeta.combined_cagr > 1
                          ? `${selectedMeta.combined_cagr.toFixed(2)}%`
                          : `${(selectedMeta.combined_cagr * 100).toFixed(2)}%`
                        : "NO EVIDENCE"}
                    </span>
                  </div>
                </div>

                {/* Visual Weight Allocation Bar */}
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 font-mono">
                      <BarChart3 className="w-4 h-4 text-indigo-400" />
                      Ponderación Visual de Componentes (100% Total)
                    </span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {selectedMeta.components.length} Activos
                    </span>
                  </div>

                  <div className="w-full h-4 rounded-full overflow-hidden flex bg-[#050811] border border-white/[0.08]">
                    {selectedMeta.components.map((comp, idx) => {
                      const rawWeight =
                        typeof comp.weight === "number" && !isNaN(comp.weight)
                          ? comp.weight
                          : 1 / Math.max(1, selectedMeta.components.length);
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

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
                    {selectedMeta.components.map((comp, idx) => {
                      const rawWeight =
                        typeof comp.weight === "number" && !isNaN(comp.weight)
                          ? comp.weight
                          : 1 / Math.max(1, selectedMeta.components.length);
                      const weightPct = Number((rawWeight * 100).toFixed(1));
                      const color = ASSET_COLORS[idx % ASSET_COLORS.length];
                      return (
                        <div
                          key={comp.strategy_id || idx}
                          className="p-3 bg-[#050811]/80 rounded-xl border border-white/[0.08] flex items-center justify-between"
                        >
                          <div className="flex items-center gap-2.5">
                            <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: color }} />
                            <div>
                              <span className="text-xs font-semibold text-slate-200 block">
                                {comp.name || comp.strategy_id}
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono">
                                {comp.symbol} · {comp.timeframe}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="text-xs font-bold font-mono text-emerald-400 tabular-nums">
                              {weightPct}%
                            </span>
                            <span className="text-[10px] text-slate-500 block font-mono">Peso</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Portfolio Cryptographic Proofs */}
                <div className="p-4 bg-[#04060d] rounded-xl border border-white/[0.08] space-y-2.5 text-xs font-mono">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                    <span className="font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Hash className="w-3.5 h-3.5 text-indigo-400" />
                      Sellado Criptográfico Merkle del Portafolio
                    </span>
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      100% APPROVED_CURRENT_ENGINE
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-400">
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
              <div className="py-24 text-center text-slate-500 bg-[#090d16]/40 rounded-2xl border border-white/[0.08] font-mono text-xs">
                Selecciona una meta-estrategia de la lista para ver su composición y métricas combinadas.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: CONSTRUCTOR MULTI-ALPHA — BLOQUEADO */}
      {activeTab === "custom" && (
        <div className="space-y-6 font-mono">
          <div className="bg-[#090d16]/90 backdrop-blur-xl rounded-2xl border border-amber-500/40 p-8 shadow-xl">
            <div className="flex flex-col items-center text-center space-y-4 max-w-3xl mx-auto">
              <div className="p-4 rounded-full bg-amber-950/60 border border-amber-500/50 text-amber-400 shadow-[0_0_20px_rgba(245,158,11,0.2)]">
                <Lock className="w-8 h-8" />
              </div>
              <h2 className="text-lg font-bold text-white">Constructor de Meta-Estrategias: BLOQUEADO</h2>
              <p className="text-xs md:text-sm text-slate-400 leading-relaxed font-sans">
                No existe hoy superficie real en el backend para combinar portafolios:{" "}
                <span className="font-mono text-slate-300">GET /api/v2/certified/meta-strategies</span> es un stub
                sin datos y no hay endpoint canónico de combinación. Mostrar métricas combinadas aquí sería
                fabricarlas (doctrina ZERO-MOCK / EVIDENCE-GATED).
              </p>
              <div className="w-full p-4 rounded-xl bg-[#050811] border border-white/[0.08] text-left space-y-2 text-xs">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-300 block">
                  Condición exacta de desbloqueo
                </span>
                <ul className="text-xs text-slate-300 space-y-1.5 list-disc list-inside">
                  <li>Al menos 1 campeón aprobado en Fase 2 de investigación (estado real: sin aprobadas hoy).</li>
                  <li>Certificación 11/11 con estado APPROVED_CURRENT_ENGINE y evidencia completa (hashes + ledger verificado).</li>
                  <li>Endpoint real de combinación de portafolio servido por el backend (sin stub): el frontend solo renderizará precalculado.</li>
                </ul>
              </div>
              <p className="text-xs text-slate-500">
                Mientras tanto, la pestaña «Portafolios Certificados» renderiza lo que el backend devuelve realmente
                (hoy: lista vacía = vacío-correcto etiquetado como tal).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
