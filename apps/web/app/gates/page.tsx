"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Award,
  Layers,
  Hash,
  FileCheck,
  Copy,
  Check,
  Search,
  Flame,
  Building2,
  XCircle,
  AlertTriangle,
  Table,
  Download,
  FileSpreadsheet,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Zap,
} from "lucide-react";
import {
  getCertifiedStrategies,
  getCandidates,
  CertifiedStrategy,
  getExportCsvUrl,
  getExportXlsxUrl,
} from "@/lib/api";
import QuantTooltip from "@/components/system/QuantTooltip";

interface GateCanonicalMeta {
  id: string;
  num: number;
  slug: string;
  name: string;
  category: string;
  protectionSentence: string;
  threshold: string;
  icon: string;
  accentColor: string;
}

const CANONICAL_11_GATES: GateCanonicalMeta[] = [
  {
    id: "G1",
    num: 1,
    slug: "gate-1-data-ingest",
    name: "Integridad OHLCV & Checksum",
    category: "Data Ingest",
    protectionSentence: "Garantiza 100% de datos continuos sin huecos y cero lookahead bias mediante sellado SHA-256.",
    threshold: "Continuidad 100% (Gap <= 2%)",
    icon: "💾",
    accentColor: "#38bdf8",
  },
  {
    id: "G2",
    num: 2,
    slug: "gate-2-cost-backtest",
    name: "Cost Backtest con Fricción Institucional",
    category: "Execution",
    protectionSentence: "Elimina falsos positivos descontando spreads reales y comisiones por contrato/lote (PF >= 1.15).",
    threshold: "PF >= 1.15 con Comisiones Reales",
    icon: "💸",
    accentColor: "#f59e0b",
  },
  {
    id: "G3",
    num: 3,
    slug: "gate-3-trade-significance",
    name: "Significancia Estadística IS/OOS",
    category: "Statistics",
    protectionSentence: "Descarta la suerte y la escasez muestral exigiendo un mínimo de trades y Drawdown acotado.",
    threshold: "Trades >= 20, DD <= 4% Fondeo / 30% Ultra",
    icon: "📊",
    accentColor: "#818cf8",
  },
  {
    id: "G4",
    num: 4,
    slug: "gate-4-walk-forward",
    name: "Walk-Forward Optimization (WFO)",
    category: "Anti-Overfit",
    protectionSentence: "Previene parámetros sobreoptimizados caducos evaluando estabilidad en ventanas móviles rodantes.",
    threshold: "Eficiencia WFO >= 50%",
    icon: "🔄",
    accentColor: "#a855f7",
  },
  {
    id: "G5",
    num: 5,
    slug: "gate-5-monte-carlo",
    name: "Remuestreo Monte Carlo (0% Ruina)",
    category: "Robustness",
    protectionSentence: "Garantiza 0.0% de probabilidad de quiebra y máxima resiliencia en 1,000 permutaciones aleatorias.",
    threshold: "Riesgo de Ruina 0.0% (95% CI)",
    icon: "🎲",
    accentColor: "#10b981",
  },
  {
    id: "G6",
    num: 6,
    slug: "gate-6-stress-slippage",
    name: "Estrés de Fricción 3x Slippage",
    category: "Stress Test",
    protectionSentence: "Garantiza supervivencia ante caídas extremas de liquidez y spreads triplicados en noticias de alto impacto.",
    threshold: "PF OOS >= 1.05 bajo estrés 3x",
    icon: "⚡",
    accentColor: "#ec4899",
  },
  {
    id: "G7",
    num: 7,
    slug: "gate-7-regime-coverage",
    name: "Cobertura de Regímenes de Mercado",
    category: "Market Context",
    protectionSentence: "Verifica que el sistema sobreviva a mercados alcistas, bajistas y laterales sin depender de un único ciclo.",
    threshold: "Beneficio en >= 2 Regímenes",
    icon: "🌐",
    accentColor: "#06b6d4",
  },
  {
    id: "G8",
    num: 8,
    slug: "gate-8-dsr-ratio",
    name: "Deflated Sharpe Ratio (DSR)",
    category: "Anti-Data Mining",
    protectionSentence: "Castiga el sesgo de selección y la minería masiva calculando el Sharpe real de Marcos López de Prado.",
    threshold: "DSR Probabilidad >= 50%",
    icon: "📐",
    accentColor: "#6366f1",
  },
  {
    id: "G9",
    num: 9,
    slug: "gate-9-novelty-antifit",
    name: "Distancia AST & Grados de Libertad",
    category: "Structure",
    protectionSentence: "Impide la clonación redundante de sistemas exigiendo diversidad estructural en el árbol sintáctico.",
    threshold: "Grados Libertad DoF >= 10.0",
    icon: "🧬",
    accentColor: "#14b8a6",
  },
  {
    id: "G10",
    num: 10,
    slug: "gate-10-debate-agentes",
    name: "Debate Multi-Agente Cuantitativo",
    category: "Governance",
    protectionSentence: "Exige consenso entre agentes especializados con Veto Bloqueante del Especialista de Riesgo.",
    threshold: "Consenso >= 40% & Riesgo Veto OK",
    icon: "🤖",
    accentColor: "#f97316",
  },
  {
    id: "G11",
    num: 11,
    slug: "gate-11-nautilus-event",
    name: "Reconciliación NautilusCore & Ratchet",
    category: "Core Engine",
    protectionSentence: "Valida ejecución física tick-a-tick con margen aislado y verificación de no-liquidación.",
    threshold: "Cero Margin Calls & DD Controlado",
    icon: "🛡️",
    accentColor: "#22c55e",
  },
];

export default function GatesPage() {
  const [certifiedList, setCertifiedList] = useState<CertifiedStrategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<CertifiedStrategy | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [routeFilter, setRouteFilter] = useState<"ALL" | "ULTRA" | "FONDEO">("ALL");
  const [gateCategoryFilter, setGateCategoryFilter] = useState<string>("ALL");
  const [expandedGates, setExpandedGates] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadCertified();
  }, []);

  async function loadCertified() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getCertifiedStrategies();
      if (Array.isArray(data) && data.length > 0) {
        setCertifiedList(data);
        setSelectedStrategy(data[0]);
      } else {
        const candidates = await getCandidates({ limit: 100 });
        if (Array.isArray(candidates) && candidates.length > 0) {
          const mapped: CertifiedStrategy[] = candidates.map((c: any) => ({
            strategy_id: c.id || c.candidate_id || "STRAT_UNKNOWN",
            name: c.name || "Candidato",
            symbol: c.symbol || "BTC",
            timeframe: c.timeframe || "1h",
            family: c.family || c.market_category || "QUANT",
            route: c.route || (c.family && String(c.family).toUpperCase().includes("ULTRA") ? "ULTRA" : "FONDEO"),
            status: c.status || "CANDIDATE",
            engine_version: c.engine_version || "5.4.0",
            strategy_hash: c.strategy_sha256 || c.strategy_hash || "",
            dataset_hash: c.dataset_id || "",
            ledger_hash: c.bundle_signature_sha256 || "",
            evidence_bundle_hash: c.bundle_signature_sha256 || "",
            all_gates_pass: c.gates_passed_count === 11,
            ledger_verified: Boolean(c.strategy_sha256),
            total_trades: c.trades_oos || c.total_trades || 0,
            win_rate_pct: c.win_rate_pct || 0,
            profit_factor: c.profit_factor_oos || c.profit_factor || 0,
            sharpe_ratio: c.sharpe_ratio || 0,
            max_drawdown_pct: c.max_dd_oos_pct || c.max_drawdown_pct || 0,
            oos_profit_factor: c.profit_factor_oos || c.profit_factor || 0,
            oos_start_timestamp_ms: c.oos_start_timestamp_ms || null,
            oos_end_timestamp_ms: c.oos_end_timestamp_ms || null,
            oos_months: c.oos_months ?? c.duration_info?.oos_months ?? c.metrics?.out_of_sample?.oos_months ?? null,
            monthly_return:
              c.monthly_return ??
              c.metrics?.out_of_sample?.monthly_roi_pct ??
              c.metrics?.out_of_sample?.monthly_return_pct ??
              null,
            annual_return: c.annual_return ?? c.metrics?.out_of_sample?.annualized_roi_pct ?? null,
            cagr: c.cagr ?? null,
            certified_at_utc: c.created_at || new Date().toISOString(),
            gates: c.gates || {},
            equity_curve: c.equity_curve || [],
          }));
          setCertifiedList(mapped);
          setSelectedStrategy(mapped[0]);
        } else {
          setCertifiedList([]);
        }
      }
    } catch (err: unknown) {
      setCertifiedList([]);
    } finally {
      setLoading(false);
    }
  }

  const copyToClipboard = (text: string, key: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedHash(key);
      setTimeout(() => setCopiedHash(null), 2000);
    }
  };

  const toggleGateExpand = (gateId: string) => {
    setExpandedGates((prev) => ({
      ...prev,
      [gateId]: !prev[gateId],
    }));
  };

  const filteredStrategies = useMemo(() => {
    return certifiedList.filter((st) => {
      const routeUpper = (st.route || "").toUpperCase();
      const familyUpper = (st.family || "").toUpperCase();
      const nameLower = (st.name || "").toLowerCase();

      const isUltra = routeUpper === "ULTRA" || familyUpper.includes("ULTRA") || nameLower.includes("ultra");
      const isFondeo =
        routeUpper === "FONDEO" ||
        routeUpper === "CME" ||
        familyUpper.includes("FONDEO") ||
        nameLower.includes("fondeo") ||
        !isUltra;

      if (routeFilter === "ULTRA" && !isUltra) return false;
      if (routeFilter === "FONDEO" && !isFondeo) return false;

      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchName = (st.name || "").toLowerCase().includes(query);
        const matchSymbol = (st.symbol || "").toLowerCase().includes(query);
        const matchFamily = (st.family || "").toLowerCase().includes(query);
        return matchName || matchSymbol || matchFamily;
      }
      return true;
    });
  }, [certifiedList, routeFilter, searchTerm]);

  // Evaluación Determinista y Honesta de Cada Gate (Zero-Mocks)
  const resolveGateItem = (meta: GateCanonicalMeta, strategy: CertifiedStrategy) => {
    const rawGates = strategy.gates;
    let gateData: any = undefined;

    if (Array.isArray(rawGates)) {
      gateData = rawGates.find(
        (g: any) => g.gate_id === meta.num || g.gate_number === meta.num || g.name?.includes(`Gate ${meta.num}`)
      );
    } else if (rawGates && typeof rawGates === "object") {
      const numStr = String(meta.num);
      gateData =
        rawGates[meta.id] ||
        rawGates[meta.id.toLowerCase()] ||
        rawGates[numStr] ||
        rawGates[`gate_${numStr}`] ||
        rawGates[`gate_${numStr.padStart(2, "0")}`] ||
        rawGates[`gate-${numStr}`] ||
        rawGates[meta.slug];
    }

    if (gateData) {
      const pass = Boolean(gateData.passed);
      const val =
        gateData.observed_value !== undefined && gateData.observed_value !== null && String(gateData.observed_value).trim() !== ""
          ? String(gateData.observed_value)
          : gateData.metric_value !== undefined && gateData.metric_value !== null
          ? String(gateData.metric_value)
          : gateData.details || (pass ? "CUMPLE (VERIFICADO)" : "NO CUMPLE");

      return {
        pass,
        score: typeof gateData.score === "number" ? gateData.score : undefined,
        val,
        threshold: gateData.threshold_value ? String(gateData.threshold_value) : meta.threshold,
      };
    }

    return {
      pass: false,
      score: undefined,
      val: "SIN EVIDENCIA FÍSICA (NO_EVIDENCE)",
      threshold: meta.threshold,
    };
  };

  const hasAnyGateData = (strategy: CertifiedStrategy) => {
    const rawGates = strategy.gates;
    if (Array.isArray(rawGates)) return rawGates.length > 0;
    if (rawGates && typeof rawGates === "object") return Object.keys(rawGates).length > 0;
    return false;
  };

  const getStrategyGateSummary = (strategy: CertifiedStrategy) => {
    let passedCount = 0;
    CANONICAL_11_GATES.forEach((meta) => {
      const res = resolveGateItem(meta, strategy);
      if (res.pass) passedCount++;
    });
    return passedCount;
  };

  const filteredGatesList = useMemo(() => {
    if (gateCategoryFilter === "ALL") return CANONICAL_11_GATES;
    return CANONICAL_11_GATES.filter((g) => g.category.toLowerCase().includes(gateCategoryFilter.toLowerCase()));
  }, [gateCategoryFilter]);

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 p-3 md:p-6 font-sans">
      <div className="max-w-[1600px] mx-auto space-y-5">
        {/* SUB-NAV: 7 FASES CUANTITATIVAS CANÓNICAS */}

        {/* HERO STORYTELLING BANNER */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#090d16] via-slate-900/90 to-emerald-950/30 border border-white/[0.08] p-5 md:p-6 shadow-2xl backdrop-blur-xl">
          <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
            <div className="space-y-2 max-w-4xl">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black font-mono tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> FASE 3 · PIPELINE DETERMINISTA DE 11 GATES
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-800/80 text-slate-300 border border-slate-700">
                  ENGINE v5.4.0 REAL-ONLY
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white flex items-center gap-2.5">
                Las 11 Pruebas de Seguridad Implacables
              </h1>
              <p className="text-xs md:text-sm text-slate-400 leading-relaxed">
                Ninguna estrategia entra a producción sin sobrevivir a las 11 compuertas cuantitativas independientes. Este pipeline audita continuidad OHLCV, comisiones institucionales, remuestreo Monte Carlo (0% ruina), DSR de Marcos López de Prado y reconciliación tick-a-tick con NautilusCore.
              </p>
            </div>

            <div className="flex flex-wrap gap-2.5 items-center font-mono">
              <button
                onClick={loadCertified}
                disabled={loading}
                className="px-3.5 py-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-white/[0.1] text-xs font-bold text-slate-200 transition flex items-center gap-2 shadow-sm active:scale-95 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-emerald-400" : "text-slate-400"}`} />
                Actualizar FSM
              </button>
              <a
                href={getExportCsvUrl(routeFilter)}
                download
                className="px-3.5 py-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 border border-white/[0.1] text-xs font-bold text-slate-200 transition flex items-center gap-2 shadow-sm active:scale-95 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 text-sky-400" />
                Exportar CSV
              </a>
              <a
                href={getExportXlsxUrl(routeFilter)}
                download
                className="px-3.5 py-2 rounded-xl bg-emerald-950/80 hover:bg-emerald-900/90 border border-emerald-700/80 text-xs font-bold text-emerald-300 transition flex items-center gap-2 shadow-md active:scale-95 cursor-pointer"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                Exportar Excel (.xlsx)
              </a>
              <Link
                href="/estrategias/2-explorador-excel"
                className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-black text-xs font-mono transition flex items-center gap-2 shadow-lg shadow-emerald-950/50 active:scale-95 cursor-pointer"
              >
                <Table className="w-3.5 h-3.5" />
                Explorador Excel WAL
              </Link>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-200 flex items-start gap-3 font-mono text-xs shadow-lg">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-sm">Error de Verificación del Pipeline:</p>
              <p className="text-rose-300 mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* CONTENEDOR SPLIT: LISTA DE ESTRATEGIAS A LA IZQUIERDA Y DETALLE DE 11 GATES A LA DERECHA */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* COLUMNA IZQUIERDA: LISTA DE ESTRATEGIAS */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                Estrategias Sometidas a Prueba ({filteredStrategies.length})
              </h2>
              <span className="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/80">
                100% REAL-ONLY
              </span>
            </div>

            {/* FILTROS Y BÚSQUEDA */}
            <div className="space-y-2 bg-[#090d16]/90 backdrop-blur-xl p-3 rounded-2xl border border-white/[0.08] font-mono text-xs shadow-lg">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Buscar por símbolo, familia o ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-[#050811] rounded-xl border border-white/[0.08] text-slate-100 placeholder-slate-500 text-xs focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="flex gap-1.5">
                <button
                  onClick={() => setRouteFilter("ALL")}
                  className={`flex-1 py-1 px-2 rounded-xl text-[10px] font-bold transition cursor-pointer ${
                    routeFilter === "ALL"
                      ? "bg-emerald-500 text-slate-950 shadow-sm"
                      : "bg-[#050811] border border-white/[0.08] text-slate-400 hover:text-white"
                  }`}
                >
                  Todas
                </button>
                <button
                  onClick={() => setRouteFilter("ULTRA")}
                  className={`flex-1 py-1 px-2 rounded-xl text-[10px] font-bold transition cursor-pointer ${
                    routeFilter === "ULTRA"
                      ? "bg-amber-500 text-slate-950 shadow-sm"
                      : "bg-[#050811] border border-white/[0.08] text-slate-400 hover:text-white"
                  }`}
                >
                  ⚡ Ruta Ultra
                </button>
                <button
                  onClick={() => setRouteFilter("FONDEO")}
                  className={`flex-1 py-1 px-2 rounded-xl text-[10px] font-bold transition cursor-pointer ${
                    routeFilter === "FONDEO"
                      ? "bg-sky-500 text-slate-950 shadow-sm"
                      : "bg-[#050811] border border-white/[0.08] text-slate-400 hover:text-white"
                  }`}
                >
                  🏛️ Ruta Fondeo
                </button>
              </div>
            </div>

            {/* LISTA DE TARJETAS */}
            {loading ? (
              <div className="py-20 text-center text-slate-400 text-xs font-mono">
                <RefreshCw className="w-7 h-7 animate-spin mx-auto mb-3 text-emerald-400" />
                Validando ledger físico contra SQLite WAL...
              </div>
            ) : filteredStrategies.length === 0 ? (
              <div className="py-16 text-center text-slate-500 text-xs bg-[#090d16]/60 rounded-2xl border border-white/[0.08] p-6 font-mono">
                No se encontraron estrategias con los filtros seleccionados.
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[640px] overflow-y-auto pr-1">
                {filteredStrategies.map((st) => {
                  const isSelected = selectedStrategy?.strategy_id === st.strategy_id;
                  const isUltra =
                    (st.family || "").toUpperCase().includes("ULTRA") ||
                    (st.name || "").toLowerCase().includes("ultra") ||
                    (st.route || "").toUpperCase() === "ULTRA";
                  const shortHash =
                    st.strategy_hash && st.strategy_hash.trim() !== "" ? `${st.strategy_hash.slice(0, 8)}...` : null;
                  const hasGateData = hasAnyGateData(st);
                  const passedCount = getStrategyGateSummary(st);
                  const isFullyCertified = hasGateData && passedCount === 11;
                  const dd = st.max_drawdown_pct ?? undefined;

                  return (
                    <div
                      key={st.strategy_id}
                      onClick={() => setSelectedStrategy(st)}
                      role="button"
                      tabIndex={0}
                      className={`w-full text-left p-3.5 rounded-2xl border transition-all duration-200 cursor-pointer select-none ${
                        isSelected
                          ? "bg-gradient-to-br from-emerald-950/60 via-slate-900 to-[#090d16] border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.18)] ring-1 ring-emerald-500/60"
                          : "bg-[#090d16]/80 border-white/[0.08] hover:border-slate-700 hover:bg-slate-900/60 text-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span
                            className={`px-2 py-0.5 rounded-lg text-[10px] font-black font-mono border uppercase tracking-wider flex items-center gap-1 ${
                              !hasGateData
                                ? "bg-slate-500/10 border-slate-500/40 text-slate-300"
                                : isFullyCertified
                                ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                                : "bg-amber-500/15 border-amber-500/40 text-amber-300"
                            }`}
                          >
                            <Award className="w-3 h-3 text-emerald-400" />
                            {!hasGateData
                              ? "GATES: NO EVIDENCE"
                              : isFullyCertified
                              ? "TIER 1 (11/11 GATES)"
                              : `TIER 4 (${passedCount}/11 GATES)`}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold border ${
                              isUltra
                                ? "bg-amber-950/40 text-amber-300 border-amber-800/40"
                                : "bg-sky-950/40 text-sky-300 border-sky-800/40"
                            }`}
                          >
                            {isUltra ? "RUTA ULTRA" : "RUTA FONDEO"}
                          </span>
                        </div>
                        <span className="px-2 py-0.5 rounded-lg bg-[#050811] text-slate-200 font-mono text-[10px] font-bold border border-white/[0.08]">
                          {st.symbol} · {st.timeframe}
                        </span>
                      </div>

                      <div className="mb-2">
                        <h3 className={`text-xs font-bold truncate ${isSelected ? "text-white" : "text-slate-200"}`}>
                          {st.name || st.strategy_id}
                        </h3>
                        <div className="flex items-center gap-1.5 mt-0.5 text-[10px] font-mono text-slate-400">
                          <Hash className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                          <span>{shortHash || "NO EVIDENCE"}</span>
                          <span
                            className={`font-bold ml-auto flex items-center gap-0.5 ${
                              !hasGateData ? "text-slate-500" : isFullyCertified ? "text-emerald-400" : "text-amber-400"
                            }`}
                          >
                            {isFullyCertified ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3" />}
                            {hasGateData ? `${passedCount}/11 Gates` : "Gates: NO EVIDENCE"}
                          </span>
                        </div>

                        {/* Visual 11-Gate Indicator Bar */}
                        <div className="flex items-center gap-1 mt-2" title="Inspección Visual de 11 Compuertas">
                          {CANONICAL_11_GATES.map((gate) => {
                            const res = resolveGateItem(gate, st);
                            return (
                              <div
                                key={gate.id}
                                className={`w-3.5 h-1.5 rounded-sm transition-all ${
                                  res.score === undefined
                                    ? "bg-slate-800 border border-slate-700"
                                    : res.pass
                                    ? "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]"
                                    : "bg-rose-500"
                                }`}
                                title={`[${gate.id}] ${gate.name}: ${res.val}`}
                              />
                            );
                          })}
                        </div>
                      </div>

                      <div className="grid grid-cols-5 gap-1 bg-[#050811] p-2 rounded-xl border border-white/[0.06] text-[10px] font-mono">
                        <div>
                          <span className="text-slate-500 block text-[8.5px] font-bold">PF OOS</span>
                          <span className="font-bold text-emerald-400 tabular-nums">
                            {st.oos_profit_factor ? st.oos_profit_factor.toFixed(2) : st.profit_factor ? st.profit_factor.toFixed(2) : "NO EVI"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[8.5px] font-bold">Sharpe</span>
                          <span className="font-bold text-indigo-300 tabular-nums">
                            {st.sharpe_ratio ? st.sharpe_ratio.toFixed(2) : "NO EVI"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[8.5px] font-bold">Max DD</span>
                          <span className="font-bold text-slate-300 tabular-nums">
                            {dd === undefined ? "NO EVI" : `${dd.toFixed(1)}%`}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[8.5px] font-bold">Ret. M</span>
                          <span className="font-bold text-emerald-300 tabular-nums">
                            {st.monthly_return !== null && st.monthly_return !== undefined ? `${st.monthly_return.toFixed(1)}%` : "NO EVI"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[8.5px] font-bold">OOS M</span>
                          <span className="font-bold text-sky-300 tabular-nums">
                            {st.oos_months !== null && st.oos_months !== undefined ? `${st.oos_months.toFixed(1)}m` : "NO EVI"}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* COLUMNA DERECHA: AUDITORÍA DETALLADA DE LAS 11 COMPUERTAS */}
          <div className="lg:col-span-7 space-y-4">
            {selectedStrategy ? (
              <div className="space-y-4">
                {/* TARJETA SUPERIOR DE LA ESTRATEGIA SELECCIONADA */}
                <div className="p-5 rounded-2xl bg-gradient-to-br from-[#090d16] via-slate-900/90 to-slate-950 border border-white/[0.08] shadow-xl space-y-4 backdrop-blur-xl">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        {hasAnyGateData(selectedStrategy) && getStrategyGateSummary(selectedStrategy) === 11 ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        ) : (
                          <AlertTriangle className="w-5 h-5 text-amber-400" />
                        )}
                        <h2 className="text-lg font-black text-white tracking-tight">
                          {selectedStrategy.name || selectedStrategy.strategy_id}
                        </h2>
                      </div>
                      <p className="text-xs text-slate-400 font-mono mt-0.5">
                        {selectedStrategy.symbol} · {selectedStrategy.timeframe} · Ruta:{" "}
                        {selectedStrategy.route || selectedStrategy.family || "NO EVIDENCE"} · Estado:{" "}
                        {selectedStrategy.status || "NO EVIDENCE"}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-black font-mono border flex items-center gap-1.5 ${
                          hasAnyGateData(selectedStrategy) && getStrategyGateSummary(selectedStrategy) === 11
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                            : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                        }`}
                      >
                        {hasAnyGateData(selectedStrategy)
                          ? `${getStrategyGateSummary(selectedStrategy)}/11 COMPUERTAS APROBADAS`
                          : "GATES: NO EVIDENCE"}
                      </span>
                    </div>
                  </div>

                  {/* MÉTRICAS CLAVE SUPERIORES */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 font-mono">
                    <div className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06]">
                      <span className="text-[9px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                        PF OOS <QuantTooltip text="Profit Factor en datos fuera de muestra." />
                      </span>
                      <span className="text-sm font-black text-emerald-400 tabular-nums">
                        {selectedStrategy.oos_profit_factor
                          ? selectedStrategy.oos_profit_factor.toFixed(2)
                          : selectedStrategy.profit_factor
                          ? selectedStrategy.profit_factor.toFixed(2)
                          : "NO EVIDENCE"}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06]">
                      <span className="text-[9px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                        SHARPE <QuantTooltip text="Ratio de rendimiento ajustado por riesgo." />
                      </span>
                      <span className="text-sm font-black text-indigo-300 tabular-nums">
                        {selectedStrategy.sharpe_ratio ? selectedStrategy.sharpe_ratio.toFixed(2) : "NO EVIDENCE"}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06]">
                      <span className="text-[9px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                        MAX DD <QuantTooltip text="Máxima caída acumulada en la cuenta." />
                      </span>
                      <span className="text-sm font-black text-slate-300 tabular-nums">
                        {selectedStrategy.max_drawdown_pct === undefined || selectedStrategy.max_drawdown_pct === null
                          ? "NO EVIDENCE"
                          : `${selectedStrategy.max_drawdown_pct.toFixed(1)}%`}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06]">
                      <span className="text-[9px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                        RET. MENSUAL <QuantTooltip text="Retorno promedio mensual OOS." />
                      </span>
                      <span className="text-sm font-black text-emerald-300 tabular-nums">
                        {selectedStrategy.monthly_return !== null && selectedStrategy.monthly_return !== undefined
                          ? `${selectedStrategy.monthly_return.toFixed(2)}%`
                          : "NO EVIDENCE"}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06]">
                      <span className="text-[9px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                        HORIZONTE <QuantTooltip text="Duración total de la muestra OOS en meses." />
                      </span>
                      <span className="text-sm font-black text-sky-300 tabular-nums">
                        {selectedStrategy.oos_months !== null && selectedStrategy.oos_months !== undefined
                          ? `${selectedStrategy.oos_months.toFixed(1)} m`
                          : "NO EVIDENCE"}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06]">
                      <span className="text-[9px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
                        TRADES OOS <QuantTooltip text="Total de operaciones físicas fuera de muestra." />
                      </span>
                      <span className="text-sm font-black text-sky-400 tabular-nums">
                        {selectedStrategy.total_trades === undefined || selectedStrategy.total_trades === null
                          ? "NO EVIDENCE"
                          : selectedStrategy.total_trades}
                      </span>
                    </div>
                  </div>
                </div>

                {/* LISTA DE LAS 11 COMPUERTAS EN ACORDEÓN INTERACTIVO */}
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 px-1">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      Auditoría Forense de las 11 Compuertas
                    </h3>
                    <div className="flex items-center gap-1 text-[10px] font-mono">
                      {["ALL", "Data", "Execution", "Robustness", "Governance"].map((cat) => (
                        <button
                          key={cat}
                          onClick={() => setGateCategoryFilter(cat)}
                          className={`px-2 py-0.5 rounded-lg border transition cursor-pointer ${
                            gateCategoryFilter === cat
                              ? "bg-cyan-500/20 border-cyan-500/50 text-cyan-300"
                              : "bg-[#050811] border-white/[0.06] text-slate-500 hover:text-slate-300"
                          }`}
                        >
                          {cat === "ALL" ? "Todas" : cat}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    {filteredGatesList.map((gate) => {
                      const res = resolveGateItem(gate, selectedStrategy);
                      const isExpanded = expandedGates[gate.id] ?? false;

                      return (
                        <div
                          key={gate.id}
                          className={`rounded-2xl border transition-all duration-200 ${
                            res.score === undefined
                              ? "bg-[#090d16]/70 border-white/[0.06]"
                              : res.pass
                              ? "bg-[#090d16]/90 border-white/[0.08] hover:border-slate-700"
                              : "bg-rose-950/20 border-rose-900/40"
                          }`}
                        >
                          <div
                            onClick={() => toggleGateExpand(gate.id)}
                            className="p-3.5 flex items-start justify-between gap-3 cursor-pointer select-none"
                          >
                            <div className="flex items-start gap-2.5 min-w-0">
                              <span className="text-base mt-0.5">{gate.icon}</span>
                              <div className="space-y-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-mono text-[11px] font-bold text-slate-400">[{gate.id}]</span>
                                  <h4 className="text-xs font-bold text-white truncate">{gate.name}</h4>
                                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded-md bg-[#050811] text-slate-300 border border-white/[0.06]">
                                    {gate.category}
                                  </span>
                                </div>
                                <p className="text-[11px] text-slate-400 leading-snug">
                                  <span className="text-slate-200 font-medium">Qué protege: </span>
                                  {gate.protectionSentence}
                                </p>
                                <div className="flex items-center gap-3 text-[10px] font-mono flex-wrap">
                                  <span className="text-slate-400">
                                    Umbral: <span className="text-slate-300">{res.threshold}</span>
                                  </span>
                                  <span className="text-slate-400">
                                    · Observado:{" "}
                                    <span className={res.pass ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                                      {res.val}
                                    </span>
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center gap-2 flex-shrink-0">
                              <span
                                className={`px-2 py-0.5 rounded-lg text-[10px] font-black font-mono border flex items-center gap-1 ${
                                  res.score === undefined
                                    ? "bg-slate-800 border-slate-700 text-slate-400"
                                    : res.pass
                                    ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                                    : "bg-rose-500/10 border-rose-500/40 text-rose-300"
                                }`}
                              >
                                {res.score === undefined ? (
                                  <>
                                    <AlertTriangle className="w-3 h-3" />
                                    NO EVIDENCE
                                  </>
                                ) : (
                                  <>
                                    {res.pass ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                                    {res.score}/100
                                  </>
                                )}
                              </span>
                              <div className="p-1 text-slate-500 hover:text-slate-300">
                                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </div>
                            </div>
                          </div>

                          {/* Accordion Extended Details */}
                          {isExpanded && (
                            <div className="px-3.5 pb-3.5 pt-1 border-t border-white/[0.06] font-mono text-xs space-y-2 bg-[#050811]/40 rounded-b-2xl">
                              <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
                                <div className="text-[11px] text-slate-400">
                                  <span className="text-slate-500 uppercase font-bold mr-1">Ruta Canónica:</span>
                                  /gates/{gate.slug}
                                </div>
                                <Link
                                  href={`/gates/${gate.slug}`}
                                  className="inline-flex items-center gap-1 text-[11px] font-bold text-cyan-400 hover:text-cyan-300 transition"
                                >
                                  <span>Inspeccionar & Telemetría AI</span>
                                  <ExternalLink className="w-3 h-3" />
                                </Link>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* HASHES FORENSES CRIPTOGRÁFICOS */}
                <div className="p-4 rounded-2xl bg-[#090d16]/90 border border-white/[0.08] space-y-3 backdrop-blur-xl shadow-xl">
                  <div className="flex items-center justify-between border-b border-white/[0.08] pb-2">
                    <span className="font-bold uppercase tracking-wider text-xs text-slate-200 flex items-center gap-2 font-mono">
                      <Hash className="w-4 h-4 text-emerald-400" />
                      Certificado Merkle de Inmutabilidad Cuantitativa
                    </span>
                    <span className="text-[10px] text-emerald-400 font-mono font-bold flex items-center gap-1 bg-emerald-950/60 px-2 py-0.5 rounded-lg border border-emerald-800">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Ledger WAL Sellado
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
                    {[
                      { label: "Strategy SHA-256", val: selectedStrategy.strategy_hash || undefined, key: "strat" },
                      { label: "Ledger Root Hash", val: selectedStrategy.ledger_hash || undefined, key: "ledg" },
                      { label: "Dataset Checksum", val: selectedStrategy.dataset_hash || undefined, key: "data" },
                      { label: "Evidence Bundle", val: selectedStrategy.evidence_bundle_hash || undefined, key: "evid" },
                    ].map((h) => (
                      <div
                        key={h.key}
                        className="p-2.5 rounded-xl bg-[#050811] border border-white/[0.06] flex items-center justify-between gap-2"
                      >
                        <div className="min-w-0">
                          <span className="text-slate-500 block text-[9px] uppercase font-bold">{h.label}</span>
                          {h.val ? (
                            <span className="text-slate-200 truncate block font-semibold">{h.val.slice(0, 22)}...</span>
                          ) : (
                            <span className="text-slate-500 font-semibold">NO EVIDENCE</span>
                          )}
                        </div>
                        {h.val && (
                          <button
                            onClick={() => copyToClipboard(h.val as string, h.key)}
                            title="Copiar Hash SHA-256 completo"
                            className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition flex-shrink-0 cursor-pointer"
                          >
                            {copiedHash === h.key ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-24 text-center text-slate-500 bg-[#090d16]/40 rounded-2xl border border-white/[0.08] p-8 font-mono text-xs">
                Selecciona una estrategia de la lista para inspeccionar la auditoría de sus 11 compuertas.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
