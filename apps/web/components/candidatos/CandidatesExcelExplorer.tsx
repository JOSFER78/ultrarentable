"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  Table,
  Search,
  Download,
  Copy,
  Check,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  Hash,
  SlidersHorizontal,
} from "lucide-react";
import QuantTooltip from "@/components/system/QuantTooltip";
import { getCandidates, CandidateStrategy } from "@/lib/api";

export interface CandidateRow {
  candidate_id: string;
  name: string;
  symbol?: string;
  timeframe?: string;
  route?: string;
  family?: string;
  archetype?: string;
  status: string;
  status_reason?: string;
  tier?: string;
  tier_label?: string;
  gates_passed_count?: number;
  profit_factor_is?: number;
  profit_factor_oos?: number;
  profit_factor?: number;
  max_dd_is_pct?: number;
  max_dd_oos_pct?: number;
  max_dd_floating_pct?: number;
  max_dd_realized_pct?: number;
  max_drawdown_pct?: number;
  net_profit_is?: number;
  net_profit_oos?: number;
  win_rate_pct?: number;
  trades_is?: number;
  trades_oos?: number;
  total_trades?: number;
  trades_per_month?: number;
  monthly_return_pct?: number;
  annual_return_pct?: number;
  cumulative_return_pct?: number;
  cagr?: number | null;
  sharpe_ratio?: number;
  dsr_ratio?: number;
  wfo_pass_pct?: number;
  monte_carlo_score?: number;
  strategy_sha256?: string;
  strategy_hash?: string;
  engine_version?: string;
}

type TabType = "FONDEO_CME" | "ULTRA_CRYPTO" | "APPROVED_ONLY" | "ALL_STRATEGIES";

type SortField =
  | "symbol"
  | "timeframe"
  | "name"
  | "route"
  | "status"
  | "gates_passed_count"
  | "profit_factor_oos"
  | "profit_factor_is"
  | "max_dd_oos_pct"
  | "net_profit_oos"
  | "cumulative_return_pct"
  | "annual_return_pct"
  | "monthly_return_pct"
  | "win_rate_pct"
  | "trades_oos"
  | "trades_is"
  | "sharpe_ratio"
  | "dsr_ratio"
  | "wfo_pass_pct"
  | "monte_carlo_score";

type SortOrder = "asc" | "desc" | null;
type DensityType = "compact" | "normal" | "spacious";

export default function CandidatesExcelExplorer() {
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filtros
  const [activeTab, setActiveTab] = useState<TabType>("FONDEO_CME");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [timeframeFilter, setTimeframeFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("APPROVED");
  const [density, setDensity] = useState<DensityType>("normal");

  // Ordenación
  const [sortField, setSortField] = useState<SortField | null>("profit_factor_oos");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    loadCandidatesData();
  }, []);

  async function loadCandidatesData() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getCandidates({ limit: 500, include_rejected: true });
      const mapped: CandidateRow[] = (data || []).map((c: any) => {
        const isM = c.metrics?.in_sample || {};
        const oosM = c.metrics?.out_of_sample || {};
        const antiOverfit = c.metrics?.anti_overfit || {};
        const routeRaw = typeof c.route === "string" ? c.route.toUpperCase() : undefined;
        const pfOos = c.profit_factor_oos ?? c.profit_factor ?? undefined;
        const tradesOos = c.trades_oos ?? c.total_trades ?? undefined;

        return {
          candidate_id: c.candidate_id,
          name: c.name || c.candidate_id,
          symbol: c.symbol || undefined,
          timeframe: c.timeframe || undefined,
          route: routeRaw,
          family: c.family ?? c.archetype ?? undefined,
          archetype: c.archetype ?? c.family ?? undefined,
          status: c.status || "NO_EVIDENCE",
          status_reason: c.status_reason || undefined,
          tier: c.tier || undefined,
          tier_label: c.tier_label || undefined,
          gates_passed_count: c.gates_passed_count ?? undefined,
          profit_factor_is: isM.profit_factor ?? c.profit_factor_is ?? undefined,
          profit_factor_oos: pfOos,
          profit_factor: pfOos,
          max_dd_is_pct: isM.max_drawdown_pct ?? c.max_dd_is_pct ?? undefined,
          max_dd_oos_pct: c.max_dd_oos_pct ?? undefined,
          max_dd_floating_pct: c.max_dd_floating_pct ?? undefined,
          max_dd_realized_pct: c.max_dd_realized_pct ?? undefined,
          max_drawdown_pct: c.max_dd_oos_pct ?? undefined,
          net_profit_is: isM.net_profit_usd ?? c.net_profit_is ?? undefined,
          net_profit_oos: c.net_profit_oos ?? undefined,
          win_rate_pct: c.win_rate_pct ?? undefined,
          trades_is: isM.trades ?? c.trades_is ?? undefined,
          trades_oos: tradesOos,
          total_trades: tradesOos,
          cumulative_return_pct: oosM.roi_pct ?? c.cumulative_return_pct ?? undefined,
          // Solo se acepta el ROI que declara el scorecard de la candidata. Si la API dice
          // NO_EVIDENCE, la celda escribe NO EVIDENCE: la alternativa era derivarlo de
          // net_profit_oos, una columna con unidades mixtas que daba cifras falsas e
          // incluso con el signo cambiado (medido el 2026-09-02 en UR_ULTRA_ETH_USDT_5M).
          annual_return_pct: oosM.roi_source === "SCORECARD" ? oosM.annualized_roi_pct ?? undefined : undefined,
          monthly_return_pct: oosM.roi_source === "SCORECARD" ? oosM.monthly_roi_pct ?? undefined : undefined,
          sharpe_ratio: c.sharpe_ratio ?? undefined,
          dsr_ratio: c.dsr_ratio ?? undefined,
          wfo_pass_pct: antiOverfit.wfo_pass_pct ?? c.wfo_pass_pct ?? undefined,
          monte_carlo_score: antiOverfit.monte_carlo_score ?? c.monte_carlo_score ?? undefined,
          strategy_sha256: c.strategy_sha256 || c.canonical_hash || undefined,
          engine_version: c.engine_version || undefined,
        };
      });

      setCandidates(mapped);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al conectar con SQLite WAL.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }

  const copyToClipboard = (text: string, key: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedId(key);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  // Filtrado reactivo por pestaña
  const filteredData = useMemo(() => {
    return candidates.filter((item) => {
      // 1. Pestaña
      if (activeTab === "FONDEO_CME" && item.route !== "FONDEO") return false;
      if (activeTab === "ULTRA_CRYPTO" && item.route !== "ULTRA") return false;
      if (activeTab === "APPROVED_ONLY") {
        const isAppr = item.status.includes("CERTIFIED") || item.status.includes("APPROVED");
        if (!isAppr) return false;
      }

      // 2. Búsqueda texto
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchSymbol = (item.symbol || "").toLowerCase().includes(q);
        const matchName = item.name.toLowerCase().includes(q);
        const matchId = item.candidate_id.toLowerCase().includes(q);
        if (!matchSymbol && !matchName && !matchId) return false;
      }

      // 3. Timeframe
      if (timeframeFilter !== "ALL" && (item.timeframe || "").toLowerCase() !== timeframeFilter.toLowerCase()) {
        return false;
      }

      // 4. Status
      if (statusFilter !== "ALL") {
        const isAppr = item.status.includes("CERTIFIED") || item.status.includes("APPROVED");
        if (statusFilter === "APPROVED" && !isAppr) return false;
        if (statusFilter === "REJECTED" && isAppr) return false;
      }

      return true;
    });
  }, [candidates, activeTab, searchQuery, timeframeFilter, statusFilter]);

  // Ordenación
  const sortedData = useMemo(() => {
    if (!sortField || !sortOrder) return filteredData;

    return [...filteredData].sort((a, b) => {
      let valA: any = a[sortField as keyof CandidateRow] ?? 0;
      let valB: any = b[sortField as keyof CandidateRow] ?? 0;

      if (typeof valA === "string") {
        return sortOrder === "asc" ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortOrder === "asc" ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
    });
  }, [filteredData, sortField, sortOrder]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      if (sortOrder === "asc") setSortOrder("desc");
      else if (sortOrder === "desc") setSortOrder(null);
      else setSortOrder("asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  // KPIs
  const kpis = useMemo(() => {
    const total = sortedData.length;
    const approvedCount = sortedData.filter((c) =>
      c.status.includes("CERTIFIED") || c.status.includes("APPROVED")
    ).length;
    const pfValues = sortedData.map((c) => c.profit_factor_oos).filter((v): v is number => typeof v === "number");
    const ddValues = sortedData.map((c) => c.max_dd_oos_pct).filter((v): v is number => typeof v === "number");
    const passRate = total > 0 ? (approvedCount / total) * 100 : 0;
    return {
      total,
      approvedCount,
      passRate,
      avgPf: pfValues.length > 0 ? pfValues.reduce((acc, v) => acc + v, 0) / pfValues.length : null,
      avgDd: ddValues.length > 0 ? ddValues.reduce((acc, v) => acc + v, 0) / ddValues.length : null,
    };
  }, [sortedData]);

  // Exportar a CSV
  const exportToCSV = () => {
    if (sortedData.length === 0) return;

    const headers = [
      "ID",
      "Símbolo",
      "Timeframe",
      "Ruta",
      "Estatus",
      "Motivo",
      "Gates Aprobados",
      "Profit Factor OOS",
      "Max Drawdown OOS %",
      "PnL Neto OOS USD",
      "Trades OOS",
      "Win Rate %",
      "Rendimiento Mensual %",
      "Rendimiento Anual %",
      "Sharpe Ratio",
      "DSR Ratio",
      "Profit Factor IS",
      "Trades IS",
      "WFO Pass %",
      "Monte Carlo Score",
      "SHA256 Hash",
    ];

    const rows = sortedData.map((r) => [
      `"${r.candidate_id}"`,
      `"${r.symbol || "NO EVIDENCE"}"`,
      `"${r.timeframe || "NO EVIDENCE"}"`,
      `"${r.route || "NO EVIDENCE"}"`,
      `"${r.status}"`,
      `"${(r.status_reason || "").replace(/"/g, '""')}"`,
      r.gates_passed_count ?? "NO EVIDENCE",
      r.profit_factor_oos?.toFixed(2) ?? "NO EVIDENCE",
      r.max_dd_oos_pct?.toFixed(2) ?? "NO EVIDENCE",
      r.net_profit_oos?.toFixed(2) ?? "NO EVIDENCE",
      r.trades_oos ?? "NO EVIDENCE",
      r.win_rate_pct?.toFixed(1) ?? "NO EVIDENCE",
      r.monthly_return_pct?.toFixed(2) ?? "NO EVIDENCE",
      r.annual_return_pct?.toFixed(2) ?? "NO EVIDENCE",
      r.sharpe_ratio?.toFixed(2) ?? "NO EVIDENCE",
      r.dsr_ratio?.toFixed(2) ?? "NO EVIDENCE",
      r.profit_factor_is?.toFixed(2) ?? "NO EVIDENCE",
      r.trades_is ?? "NO EVIDENCE",
      r.wfo_pass_pct?.toFixed(1) ?? "NO EVIDENCE",
      r.monte_carlo_score?.toFixed(1) ?? "NO EVIDENCE",
      `"${r.strategy_sha256 || ""}"`,
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ultrarentable_estrategias_${activeTab.toLowerCase()}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const pad =
    density === "compact"
      ? "py-1.5 px-2.5 text-[11px]"
      : density === "spacious"
      ? "py-3.5 px-3.5 text-xs"
      : "py-2.5 px-3 text-xs";

  return (
    <div className="w-full max-w-[1720px] mx-auto space-y-5 font-sans">
      {/* CABECERA */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 md:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
              <Table className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-black tracking-tight text-[var(--text-1)] flex items-center gap-2">
                Tabla Comparativa de Candidatos
              </h1>
              <p className="text-[var(--text-2)] text-xs sm:text-sm mt-0.5 font-medium">
                Inventario de estrategias candidatas. Filtra por aprobadas para ver las que han superado los 11 gates.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap font-mono">
          <button
            onClick={exportToCSV}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[var(--profit-dim)] hover:bg-[var(--surface-3)] text-[var(--profit)] border border-[var(--profit)] shadow-sm transition active:scale-95 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 mr-1.5 text-[var(--profit)]" />
            Descargar CSV
          </button>
          <button
            onClick={loadCandidatesData}
            disabled={loading}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[var(--bg)] hover:bg-[var(--surface-1)] text-[var(--text-1)] border border-white/[0.1] transition active:scale-95 shadow-sm cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin text-[var(--text-2)]" : "text-[var(--text-2)]"}`} />
            Refrescar WAL
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)] flex items-start gap-3 shadow-lg font-mono text-xs">
          <AlertTriangle className="w-5 h-5 text-[var(--loss)] flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-sm">Error de Comunicación con SQLite WAL:</p>
            <p className="text-xs text-[var(--loss)] mt-0.5">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* PESTAÑAS PRINCIPALES */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[var(--surface-1)] backdrop-blur-xl p-2.5 rounded-2xl border border-white/[0.08] shadow-xl">
        <div className="flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("FONDEO_CME")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-mono text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "FONDEO_CME"
                ? "bg-[var(--surface-1)]   text-[var(--text-1)] border border-[var(--border)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-white/[0.04] border border-transparent"
            }`}
          >
            <span className="text-sm">🏛️</span>
            <div className="text-left">
              <span className="block font-black leading-tight">Cuentas Fondeo CME ($50K)</span>
              <span className="text-[10px] text-[var(--text-2)] font-normal">Regla Estricta: Max DD &le; 4.5%</span>
            </div>
          </button>

          <button
            onClick={() => setActiveTab("ULTRA_CRYPTO")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-mono text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "ULTRA_CRYPTO"
                ? "bg-[var(--surface-1)]   text-[var(--text-1)] border border-[var(--border)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-white/[0.04] border border-transparent"
            }`}
          >
            <span className="text-sm">⚡</span>
            <div className="text-left">
              <span className="block font-black leading-tight">Cuentas Ultra Cripto ($1,000)</span>
              <span className="text-[10px] text-[var(--text-2)] font-normal">1R Aislado / Max DD &le; 75.0% (Doctrina Convexidad)</span>
            </div>
          </button>

          <button
            onClick={() => setActiveTab("APPROVED_ONLY")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-mono text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "APPROVED_ONLY"
                ? "bg-[var(--surface-1)]   text-[var(--profit)] border border-[var(--profit)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-white/[0.04] border border-transparent"
            }`}
          >
            <span className="text-sm">🏆</span>
            <div className="text-left">
              <span className="block font-black leading-tight">Aprobadas Reales (11/11)</span>
              <span className="text-[10px] text-[var(--profit)] font-normal">Sin Violación de Drawdown</span>
            </div>
          </button>

          <button
            onClick={() => setActiveTab("ALL_STRATEGIES")}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl font-mono text-xs font-bold transition-all whitespace-nowrap cursor-pointer ${
              activeTab === "ALL_STRATEGIES"
                ? "bg-[var(--surface-1)]   text-[var(--text-1)] border border-[var(--border)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-white/[0.04] border border-transparent"
            }`}
          >
            <span className="text-sm">📊</span>
            <div className="text-left">
              <span className="block font-black leading-tight">Catálogo Completo ({candidates.length})</span>
              <span className="text-[10px] text-[var(--text-2)] font-normal">Inventario Maestro SQLite WAL</span>
            </div>
          </button>
        </div>

        <div className="flex items-center gap-1 self-end sm:self-auto bg-[var(--bg)] p-1 rounded-xl border border-white/[0.08] text-[10px] font-mono">
          <span className="text-[var(--text-2)] px-2 font-semibold">Densidad:</span>
          {(["compact", "normal", "spacious"] as DensityType[]).map((d) => (
            <button
              key={d}
              onClick={() => setDensity(d)}
              className={`px-2 py-1 rounded-lg capitalize transition font-bold cursor-pointer ${
                density === d ? "bg-[var(--surface-3)] text-[var(--text-1)] shadow-sm" : "text-[var(--text-2)] hover:text-[var(--text-1)]"
              }`}
            >
              {d === "compact" ? "Compacta" : d === "normal" ? "Normal" : "Amplia"}
            </button>
          ))}
        </div>
      </div>

      {/* KPIS DE BANNER */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono">
        <div className="p-3.5 bg-[var(--surface-1)] backdrop-blur-md rounded-xl border border-white/[0.08]">
          <span className="text-[10px] uppercase text-[var(--text-2)] font-bold block">Estrategias Listadas</span>
          <span className="text-lg font-black text-[var(--text-1)] tabular-nums">{kpis.total}</span>
        </div>
        <div className="p-3.5 bg-[var(--surface-1)] backdrop-blur-md rounded-xl border border-white/[0.08]">
          <span className="text-[10px] uppercase text-[var(--text-2)] font-bold block">Certificadas Reales</span>
          <span className="text-lg font-black text-[var(--profit)] tabular-nums">{kpis.approvedCount}</span>
        </div>
        <div className="p-3.5 bg-[var(--surface-1)] backdrop-blur-md rounded-xl border border-white/[0.08]">
          <span className="text-[10px] uppercase text-[var(--text-2)] font-bold block">Profit Factor OOS Medio</span>
          <span className="text-lg font-black text-[var(--text-2)] tabular-nums">
            {kpis.avgPf === null ? "NO EVIDENCE" : kpis.avgPf.toFixed(2)}
          </span>
        </div>
        <div className="p-3.5 bg-[var(--surface-1)] backdrop-blur-md rounded-xl border border-white/[0.08]">
          <span className="text-[10px] uppercase text-[var(--text-2)] font-bold block">Tasa de Aprobación OOS</span>
          <span
            className={`text-lg font-black tabular-nums ${
              kpis.total === 0 ? "text-[var(--text-3)]" : kpis.passRate > 0 ? "text-[var(--profit)]" : "text-[var(--text-2)]"
            }`}
          >
            {kpis.total === 0 ? "NO EVIDENCE" : `${kpis.passRate.toFixed(1)}%`}
          </span>
        </div>
        <div className="p-3.5 bg-[var(--surface-1)] backdrop-blur-md rounded-xl border border-white/[0.08]">
          <span className="text-[10px] uppercase text-[var(--text-2)] font-bold block">Max DD OOS Promedio</span>
          <span
            className={`text-lg font-black tabular-nums ${
              kpis.avgDd === null ? "text-[var(--text-3)]" : kpis.avgDd <= 4.5 ? "text-[var(--profit)]" : "text-[var(--text-2)]"
            }`}
          >
            {kpis.avgDd === null ? "NO EVIDENCE" : `${kpis.avgDd.toFixed(1)}%`}
          </span>
        </div>
      </div>

      {/* BUSCADOR Y FILTROS */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-[var(--surface-1)] backdrop-blur-md p-3.5 rounded-2xl border border-white/[0.08] font-mono text-xs shadow-lg">
        <div className="relative">
          <Search className="w-4 h-4 text-[var(--text-3)] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Buscar símbolo, ID o hash..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-[var(--bg)] rounded-xl border border-white/[0.1] text-[var(--text-1)] placeholder-[var(--text-3)] text-xs focus:border-[var(--border)] focus:outline-none"
          />
        </div>

        <div>
          <select
            value={timeframeFilter}
            onChange={(e) => setTimeframeFilter(e.target.value)}
            className="w-full py-2 px-3 bg-[var(--bg)] rounded-xl border border-white/[0.1] text-[var(--text-1)] text-xs focus:border-[var(--border)] focus:outline-none"
          >
            <option value="ALL">Timeframe: TODOS</option>
            <option value="1m">1 Minuto (1m)</option>
            <option value="5m">5 Minutos (5m)</option>
            <option value="15m">15 Minutos (15m)</option>
            <option value="1h">1 Hora (1h)</option>
            <option value="4h">4 Horas (4h)</option>
            <option value="1d">Diario (1d)</option>
          </select>
        </div>

        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full py-2 px-3 bg-[var(--bg)] rounded-xl border border-white/[0.1] text-[var(--text-1)] text-xs focus:border-[var(--border)] focus:outline-none"
          >
            <option value="ALL">Estatus: TODOS</option>
            <option value="APPROVED">Solo Certificadas</option>
            <option value="REJECTED">Solo Rechazadas / Investigación</option>
          </select>
        </div>
      </div>

      {/* TABLA EXCEL MULTI-COLUMNA ULTRA-COMPLETA */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl rounded-2xl border border-white/[0.08] overflow-hidden shadow-2xl">
        <div className="overflow-x-auto max-h-[750px]">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead className="bg-[var(--bg)] sticky top-0 z-10 border-b border-white/[0.08] text-[var(--text-2)] text-[11px] select-none">
              <tr>
                <th className="py-3 px-2 w-10 text-center text-[var(--text-3)]">#</th>
                <th onClick={() => handleSort("symbol")} className="py-3 px-3 cursor-pointer hover:text-[var(--text-1)] transition w-24">
                  Símbolo {sortField === "symbol" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("timeframe")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition w-14 text-center">
                  TF {sortField === "timeframe" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("name")} className="py-3 px-3 cursor-pointer hover:text-[var(--text-1)] transition min-w-[180px]">
                  Estrategia {sortField === "name" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("route")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-center w-20">
                  Ruta
                </th>
                <th onClick={() => handleSort("gates_passed_count")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-center w-20">
                  Gates {sortField === "gates_passed_count" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th className="py-3 px-3 text-center min-w-[140px]">Estatus & Causa</th>
                <th onClick={() => handleSort("profit_factor_oos")} className="py-3 px-3 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  PF OOS {sortField === "profit_factor_oos" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("max_dd_oos_pct")} className="py-3 px-3 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Max DD % {sortField === "max_dd_oos_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("net_profit_oos")} className="py-3 px-3 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  PnL Neto OOS {sortField === "net_profit_oos" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("monthly_return_pct")} title="Rendimiento OOS mensual compuesto. NO EVIDENCE si la duración OOS no es real." className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Rend. mes {sortField === "monthly_return_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("annual_return_pct")} title="Rendimiento OOS anualizado (CAGR). NO EVIDENCE si la duración OOS no es real." className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Rend. año {sortField === "annual_return_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("win_rate_pct")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Win% {sortField === "win_rate_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("trades_oos")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Trades OOS
                </th>
                <th onClick={() => handleSort("sharpe_ratio")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Sharpe
                </th>
                <th onClick={() => handleSort("profit_factor_is")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  PF IS
                </th>
                <th onClick={() => handleSort("trades_is")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  Trades IS
                </th>
                <th onClick={() => handleSort("wfo_pass_pct")} className="py-3 px-2 cursor-pointer hover:text-[var(--text-1)] transition text-right">
                  WFO %
                </th>
                <th className="py-3 px-3 text-center w-28">SHA-256</th>
                <th className="py-3 px-2 text-center w-16">Acción</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/[0.05]">
              {loading ? (
                <tr>
                  <td colSpan={20} className="py-16 text-center text-[var(--text-3)] text-xs font-mono">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-[var(--text-3)]" />
                    Cargando catálogo físico desde SQLite WAL...
                  </td>
                </tr>
              ) : sortedData.length === 0 ? (
                <tr>
                  <td colSpan={20} className="py-16 text-center text-[var(--text-3)] text-xs font-mono">
                    No se encontraron estrategias para los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                sortedData.map((row, idx) => {
                  const pfOos = row.profit_factor_oos ?? row.profit_factor;
                  const ddOos = row.max_dd_oos_pct ?? row.max_drawdown_pct;
                  const isFondeo = row.route === "FONDEO";

                  const isCertified = row.status.includes("CERTIFIED") || row.status === "APPROVED";
                  const isRejected = row.status.startsWith("REJECTED") || row.status === "ANOMALY_REVIEW";

                  return (
                    <tr key={row.candidate_id || idx} className="hover:bg-white/[0.03] transition">
                      <td className={`${pad} text-center text-[var(--text-3)]`}>{idx + 1}</td>
                      <td className={`${pad} font-bold text-[var(--text-1)]`}>
                        <span>{row.symbol || "NO EVIDENCE"}</span>
                      </td>
                      <td className={`${pad} text-[var(--text-2)] text-center font-bold`}>{row.timeframe || "NO EVIDENCE"}</td>
                      <td className={`${pad} text-[var(--text-1)] font-sans font-medium`}>
                        <div className="truncate max-w-[200px]" title={row.name}>
                          {row.name}
                        </div>
                      </td>
                      <td className={`${pad} text-center`}>
                        {row.route ? (
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                              isFondeo
                                ? "bg-[var(--surface-2)] text-[var(--text-1)] border-[var(--border)]"
                                : "bg-[var(--surface-2)] text-[var(--text-1)] border-[var(--border)]"
                            }`}
                          >
                            {row.route}
                          </span>
                        ) : (
                          <span className="text-[var(--text-3)] text-[10px]">NO EVIDENCE</span>
                        )}
                      </td>
                      <td className={`${pad} text-center font-bold`}>
                        {row.gates_passed_count === undefined ? (
                          <span className="text-[var(--text-3)] text-[10px]">NO EVIDENCE</span>
                        ) : (
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] border ${
                              row.gates_passed_count === 11
                                ? "bg-[var(--profit-dim)] text-[var(--profit)] border-[var(--profit)]"
                                : row.gates_passed_count >= 9
                                ? "bg-[var(--surface-2)] text-[var(--text-1)] border-[var(--border)]"
                                : "bg-[var(--loss-dim)] text-[var(--loss)] border-[var(--loss)]"
                            }`}
                          >
                            {row.gates_passed_count}/11
                          </span>
                        )}
                      </td>
                      <td className={`${pad} text-center`}>
                        <div className="flex flex-col items-center">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              isCertified
                                ? "bg-[var(--profit-dim)] text-[var(--profit)] border-[var(--profit)]"
                                : isRejected
                                ? "bg-[var(--loss-dim)] text-[var(--loss)] border-[var(--loss)]"
                                : "bg-[var(--surface-1)] text-[var(--text-1)] border-white/[0.08]"
                            }`}
                          >
                            {row.status}
                          </span>
                          {row.status_reason && (
                            <span className="text-[9px] text-[var(--text-3)] truncate max-w-[130px]" title={row.status_reason}>
                              {row.status_reason}
                            </span>
                          )}
                        </div>
                      </td>
                      <td
                        className={`${pad} text-right font-bold tabular-nums ${
                          pfOos === undefined
                            ? "text-[var(--text-3)]"
                            : pfOos >= 1.3
                            ? "text-[var(--profit)]"
                            : pfOos >= 1.1
                            ? "text-[var(--text-1)]"
                            : "text-[var(--text-2)]"
                        }`}
                      >
                        {pfOos === undefined ? "NO EVIDENCE" : pfOos.toFixed(2)}
                      </td>
                      <td className={`${pad} text-right font-mono tabular-nums`}>
                        <span className="px-1.5 py-0.5 rounded border border-white/[0.08] text-[11px] text-[var(--text-1)]">
                          {ddOos === undefined ? "NO EVIDENCE" : `${ddOos.toFixed(1)}%`}
                        </span>
                      </td>
                      <td
                        className={`${pad} text-right font-bold tabular-nums ${
                          row.net_profit_oos === undefined
                            ? "text-[var(--text-3)]"
                            : row.net_profit_oos >= 0
                            ? "text-[var(--profit)]"
                            : "text-[var(--loss)]"
                        }`}
                      >
                        {row.net_profit_oos === undefined ? "NO EVIDENCE" : `$${row.net_profit_oos.toFixed(2)}`}
                      </td>
                      <td className={`${pad} text-right font-mono tabular-nums ${
                        row.monthly_return_pct === undefined ? "text-[var(--text-3)]" : row.monthly_return_pct >= 0 ? "text-[var(--profit)]" : "text-[var(--loss)]"
                      }`}>
                        {row.monthly_return_pct === undefined ? "NO EVIDENCE" : `${row.monthly_return_pct >= 0 ? "+" : ""}${row.monthly_return_pct.toFixed(2)}%`}
                      </td>
                      <td className={`${pad} text-right font-mono tabular-nums ${
                        row.annual_return_pct === undefined ? "text-[var(--text-3)]" : row.annual_return_pct >= 0 ? "text-[var(--profit)]" : "text-[var(--loss)]"
                      }`}>
                        {row.annual_return_pct === undefined ? "NO EVIDENCE" : `${row.annual_return_pct >= 0 ? "+" : ""}${row.annual_return_pct.toFixed(2)}%`}
                      </td>
                      <td className={`${pad} text-right text-[var(--text-1)] tabular-nums`}>
                        {row.win_rate_pct === undefined ? (
                          <span className="text-[var(--text-3)]">NO EVIDENCE</span>
                        ) : (
                          `${row.win_rate_pct.toFixed(1)}%`
                        )}
                      </td>
                      <td className={`${pad} text-right text-[var(--text-1)] tabular-nums`}>
                        {row.trades_oos === undefined ? <span className="text-[var(--text-3)]">NO EVIDENCE</span> : row.trades_oos}
                      </td>
                      <td className={`${pad} text-right text-[var(--text-1)] tabular-nums`}>
                        {row.sharpe_ratio === undefined ? <span className="text-[var(--text-3)]">NO EVIDENCE</span> : row.sharpe_ratio.toFixed(2)}
                      </td>
                      <td className={`${pad} text-right text-[var(--text-2)] tabular-nums`}>
                        {row.profit_factor_is === undefined ? (
                          <span className="text-[var(--text-3)]">NO EVIDENCE</span>
                        ) : (
                          row.profit_factor_is.toFixed(2)
                        )}
                      </td>
                      <td className={`${pad} text-right text-[var(--text-2)] tabular-nums`}>
                        {row.trades_is === undefined ? <span className="text-[var(--text-3)]">NO EVIDENCE</span> : row.trades_is}
                      </td>
                      <td className={`${pad} text-right text-[var(--text-1)] tabular-nums`}>
                        {row.wfo_pass_pct === undefined ? (
                          <span className="text-[var(--text-3)]">NO EVIDENCE</span>
                        ) : (
                          `${row.wfo_pass_pct.toFixed(1)}%`
                        )}
                      </td>
                      <td className={`${pad} text-center`}>
                        {row.strategy_sha256 ? (
                          <button
                            onClick={() => copyToClipboard(row.strategy_sha256!, row.candidate_id)}
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[var(--bg)] border border-white/[0.08] hover:border-white/[0.16] text-[10px] text-[var(--text-2)] cursor-pointer"
                            title={row.strategy_sha256}
                          >
                            <Hash className="w-2.5 h-2.5 text-[var(--text-2)]" />
                            <span>{row.strategy_sha256.slice(0, 8)}...</span>
                            {copiedId === row.candidate_id ? (
                              <Check className="w-2.5 h-2.5 text-[var(--profit)]" />
                            ) : (
                              <Copy className="w-2.5 h-2.5" />
                            )}
                          </button>
                        ) : (
                          <span className="text-[var(--text-3)] text-[10px]">SIN HASH</span>
                        )}
                      </td>
                      <td className={`${pad} text-center`}>
                        <Link
                          href="/estrategias"
                          className="inline-flex items-center px-2 py-0.5 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border)] text-[10px] font-bold transition shadow-sm"
                        >
                          Probar
                        </Link>
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
  );
}
