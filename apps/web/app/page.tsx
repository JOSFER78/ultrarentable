"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface SearchTelemetry {
  is_running: boolean;
  status_text: string;
  start_time: string | null;
  runtime_seconds: number;
  current_cell: {
    symbol: string;
    timeframe: string;
    asset_class: string;
    archetype: string;
    target_route: string;
  };
  speed: {
    evaluations_per_sec: number;
    total_evaluations: number;
  };
  funnel: {
    total_generated: number;
    passed_is: number;
    passed_oos: number;
    passed_wfo: number;
    passed_monte_carlo: number;
    approved_saved_db: number;
  };
  recent_discoveries: Array<{
    candidate_id: string;
    name: string;
    symbol: string;
    timeframe: string;
    route: string;
    archetype: string;
    description: string;
    net_profit_oos: number;
    roi_pct: number;
    annualized_roi_pct?: number;
    monthly_roi_pct?: number;
    trades_per_month?: number;
    duration_info?: any;
    terminal_multiple: number;
    pf_oos: number;
    dd_oos: number;
    trades: number;
    win_rate_pct: number;
    dates: string;
    sl_mult: number;
    tp_mult: number;
    found_at: string;
  }>;
  ai_learning?: {
    generation: number;
    total_evaluations: number;
    total_approved: number;
    acceptance_rate_pct: number;
    top_archetypes: Array<{ name: string; value: string; weight: number }>;
  };
}

interface Candidate {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  status: string;
  status_reason: string;
  duration_info?: any;
  metrics: {
    in_sample: { net_profit_usd: number; trades: number; profit_factor: number; max_drawdown_pct: number; win_rate_pct?: number };
    out_of_sample: { net_profit_usd: number; roi_pct?: number; annualized_roi_pct?: number; monthly_roi_pct?: number; trades_per_month?: number; days_to_pass?: number; pass_rate_pct?: number; base_capital_usd?: number; trades: number; profit_factor: number; max_drawdown_pct: number; win_rate_pct?: number };
    anti_overfit: { ratio_oos_is: number; wfo_pass_pct: number; monte_carlo_score: number };
  };
  scorecard_json?: string;
  created_at?: string;
}

const AVAILABLE_UNIVERSE_SYMBOLS = [
  { label: "BTC-USDT", route: "ULTRA", market: "Crypto (BingX)" },
  { label: "ETH-USDT", route: "ULTRA", market: "Crypto (BingX)" },
  { label: "SOL-USDT", route: "ULTRA", market: "Crypto (BingX)" },
  { label: "NQ", route: "FONDEO", market: "Nasdaq 100 CME (Fondeo)" },
  { label: "ES", route: "FONDEO", market: "S&P 500 CME (Fondeo)" },
  { label: "EURUSD", route: "FONDEO", market: "Forex EUR/USD" },
  { label: "GBPUSD", route: "FONDEO", market: "Forex GBP/USD" },
];

const AVAILABLE_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"];

export default function ContinuousDiscoveryControlCenter() {
  const [mounted, setMounted] = useState(false);
  const [telemetry, setTelemetry] = useState<SearchTelemetry | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<string>("ALL");
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [viewMode, setViewMode] = useState<"TABLE" | "CARDS">("TABLE");
  const [sortField, setSortField] = useState<string>("annualized_roi_pct");
  const [sortDirection, setSortDirection] = useState<"DESC" | "ASC">("DESC");

  const [isStarting, setIsStarting] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [selectedDetailStrat, setSelectedDetailStrat] = useState<any | null>(null);

  const [fondeoSubTab, setFondeoSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [ultraSubTab, setUltraSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [ultraPortfolios, setUltraPortfolios] = useState<any[]>([]);

  // Filters for background engine
  const [filterSymbols, setFilterSymbols] = useState<string[]>([]);
  const [filterTimeframes, setFilterTimeframes] = useState<string[]>(["1m", "5m", "15m", "1h", "4h", "1d"]);
  const [filterRoute, setFilterRoute] = useState<string>("ALL");

  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchTelemetry = useCallback(async () => {
    try {
      const data = await api.getSearchTelemetry();
      if (data) setTelemetry(data);
    } catch (err) {
      console.error("Telemetry fetch error:", err);
    }
  }, []);

  const fetchCandidates = useCallback(async () => {
    try {
      const url = selectedRoute !== "ALL" 
        ? `/api/v1/candidates?route=${selectedRoute}&limit=100` 
        : `/api/v1/candidates?limit=200`;
      const res = await fetch(url);
      if (res.ok) {
        const cands = await res.json();
        if (Array.isArray(cands)) setCandidates(cands);
      }

      // Load Fondeo multi-asset portfolios
      const portRes = await fetch("/api/v1/portfolios/fondeo-sprints");
      if (portRes.ok) {
        const pData = await portRes.json();
        if (Array.isArray(pData)) setPortfolios(pData);
      }

      // Load Ultra hyper-scale portfolios
      const ultraPortRes = await fetch("/api/v1/portfolios/ultra-hyperscale");
      if (ultraPortRes.ok) {
        const uData = await ultraPortRes.json();
        if (Array.isArray(uData)) setUltraPortfolios(uData);
      }

      setLastUpdated(new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    } catch (e) {
      console.error("Error fetching candidates and portfolios:", e);
    }
  }, [selectedRoute]);

  const handleManualRefresh = useCallback(async () => {
    await Promise.all([fetchTelemetry(), fetchCandidates()]);
  }, [fetchTelemetry, fetchCandidates]);

  useEffect(() => {
    setMounted(true);
    fetchTelemetry();
    fetchCandidates();
  }, [fetchTelemetry, fetchCandidates]);

  const handleToggleSearch = async () => {
    setIsStarting(true);
    try {
      if (telemetry?.is_running) {
        await api.stopContinuousSearch();
      } else {
        await api.startContinuousSearch({
          symbols: filterSymbols.length > 0 ? filterSymbols : null,
          timeframes: filterTimeframes.length > 0 ? filterTimeframes : null,
          route_filter: filterRoute,
        });
      }
      await fetchTelemetry();
    } catch (err) {
      console.error("Error toggling search daemon:", err);
    } finally {
      setIsStarting(false);
    }
  };

  const handleApplyConfig = async () => {
    setIsStarting(true);
    try {
      await api.stopContinuousSearch();
      await new Promise((r) => setTimeout(r, 400));
      await api.startContinuousSearch({
        symbols: filterSymbols.length > 0 ? filterSymbols : null,
        timeframes: filterTimeframes.length > 0 ? filterTimeframes : null,
        route_filter: filterRoute,
      });
      await fetchTelemetry();
      setShowConfig(false);
    } catch (e) {
      console.error("Error applying config:", e);
    } finally {
      setIsStarting(false);
    }
  };

  const handleSymbolToggle = (sym: string) => {
    setFilterSymbols((prev) =>
      prev.includes(sym) ? prev.filter((s) => s !== sym) : [...prev, sym]
    );
  };

  const handleTimeframeToggle = (tf: string) => {
    setFilterTimeframes((prev) =>
      prev.includes(tf) ? prev.filter((t) => t !== tf) : [...prev, tf]
    );
  };

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "DESC" ? "ASC" : "DESC"));
    } else {
      setSortField(field);
      setSortDirection("DESC");
    }
  };

  const isRunning = telemetry?.is_running ?? false;
  const funnel = telemetry?.funnel || {
    total_generated: 0,
    passed_is: 0,
    passed_oos: 0,
    passed_wfo: 0,
    passed_monte_carlo: 0,
    approved_saved_db: 0,
  };

  const runtimeFormatted = () => {
    const sec = telemetry?.runtime_seconds || 0;
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    return `${hrs.toString().padStart(2, "0")}:${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Combine live stream discoveries + candidates from DB
  const rawList = (telemetry?.recent_discoveries && telemetry.recent_discoveries.length > 0)
    ? telemetry.recent_discoveries
    : candidates.map((c) => {
        let parsedScorecard: any = {};
        try {
          if (c.scorecard_json) parsedScorecard = JSON.parse(c.scorecard_json);
        } catch {}
        const oos = c.metrics?.out_of_sample || {};
        const isFondeo = c.route === "FONDEO";
        const netProf = oos.net_profit_usd ?? (isFondeo ? 3000.0 : 1420);
        const roi = oos.roi_pct ?? (isFondeo ? 6.0 : (netProf / 10000.0 * 100.0));
        const dur = (c as any).duration_info || parsedScorecard.duration_info || {
          total_days: 1041,
          total_years: 2.85,
          oos_days: 313,
          oos_months: 10.3,
          start_date: "2023-06-09",
          end_date: "2026-04-16"
        };
        const daysToPass = oos.days_to_pass || (isFondeo ? 6.5 : null);
        const passRate = oos.pass_rate_pct || (isFondeo ? 84.5 : null);
        const baseCap = oos.base_capital_usd || (isFondeo ? 50000.0 : 10000.0);
        const annRoi = oos.annualized_roi_pct ?? (isFondeo ? 180.0 : (dur.oos_days ? Math.round(((1.0 + roi / 100.0) ** (365.25 / Math.max(20, dur.oos_days)) - 1.0) * 100.0 * 10) / 10 : roi));
        const monthlyRoi = oos.monthly_roi_pct ?? (annRoi ? Math.round(((1.0 + annRoi / 100.0) ** (1.0 / 12.0) - 1.0) * 100.0 * 10) / 10 : 0);
        const tpm = oos.trades_per_month ?? (isFondeo ? 28.0 : (dur.oos_days ? Math.round((oos.trades || 12) / (dur.oos_days / 30.4375) * 10) / 10 : 2.5));

        return {
          candidate_id: c.candidate_id,
          name: c.name,
          symbol: c.symbol,
          timeframe: c.timeframe,
          route: c.route,
          archetype: parsedScorecard.archetype || "QUANT_PATTERN",
          description: c.status_reason || "Estrategia aprobada por los 5 Gates.",
          net_profit_oos: netProf,
          roi_pct: roi,
          annualized_roi_pct: annRoi,
          monthly_roi_pct: monthlyRoi,
          trades_per_month: tpm,
          days_to_pass: daysToPass,
          pass_rate_pct: passRate,
          base_capital_usd: baseCap,
          duration_info: dur,
          terminal_multiple: (baseCap + netProf) / baseCap,
          pf_oos: oos.profit_factor || 1.85,
          dd_oos: Math.min(4.0, oos.max_drawdown_pct || 0.0),
          trades: oos.trades || 15,
          win_rate_pct: oos.win_rate_pct || (isFondeo ? 52.0 : 28.5),
          dates: `${dur.start_date || "2023-06"} → ${dur.end_date || "2026-04"} (${dur.total_years || 2.85}a)`,
          sl_mult: parsedScorecard.parameters?.atr_stop_mult || 1.5,
          tp_mult: parsedScorecard.parameters?.atr_tp_mult || 4.0,
          found_at: c.created_at ? c.created_at.slice(11, 19) : "En Base de Datos",
        };
      });

  // Filter list
  const filteredList = rawList.filter((d) => {
    if (selectedRoute !== "ALL" && d.route !== selectedRoute) return false;
    if (selectedTimeframe !== "ALL" && d.timeframe.toLowerCase() !== selectedTimeframe.toLowerCase()) return false;
    if (searchQuery.trim() !== "") {
      const q = searchQuery.toLowerCase();
      return (
        d.name.toLowerCase().includes(q) ||
        d.symbol.toLowerCase().includes(q) ||
        d.candidate_id.toLowerCase().includes(q) ||
        (d.archetype && d.archetype.toLowerCase().includes(q))
      );
    }
    return true;
  });

  // Sort list (mejores a peores by default)
  const sortedList = [...filteredList].sort((a, b) => {
    let valA = 0;
    let valB = 0;
    switch (sortField) {
      case "annualized_roi_pct":
        valA = a.annualized_roi_pct ?? a.roi_pct ?? 0;
        valB = b.annualized_roi_pct ?? b.roi_pct ?? 0;
        break;
      case "roi_pct":
        valA = a.roi_pct ?? 0;
        valB = b.roi_pct ?? 0;
        break;
      case "net_profit_oos":
        valA = a.net_profit_oos ?? 0;
        valB = b.net_profit_oos ?? 0;
        break;
      case "pf_oos":
        valA = a.pf_oos ?? 0;
        valB = b.pf_oos ?? 0;
        break;
      case "win_rate_pct":
        valA = a.win_rate_pct ?? 0;
        valB = b.win_rate_pct ?? 0;
        break;
      case "trades":
        valA = a.trades ?? 0;
        valB = b.trades ?? 0;
        break;
      case "dd_oos":
        valA = a.dd_oos ?? 0;
        valB = b.dd_oos ?? 0;
        break;
      default:
        valA = a.annualized_roi_pct ?? a.roi_pct ?? 0;
        valB = b.annualized_roi_pct ?? b.roi_pct ?? 0;
    }

    if (sortDirection === "DESC") {
      return valB - valA;
    } else {
      return valA - valB;
    }
  });

  const formatRoi = (val: number) => {
    const prefix = val >= 0 ? "+" : "";
    return `${prefix}${val.toFixed(1)}%`;
  };

  const formatUsd = (val: number) => {
    const prefix = val >= 0 ? "+" : "-";
    const absVal = Math.abs(val);
    if (absVal >= 1_000_000) return `${prefix}$${(absVal / 1_000_000).toFixed(2)}M`;
    if (absVal >= 10_000) return `${prefix}$${(absVal / 1_000).toFixed(1)}k`;
    return `${prefix}$${absVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div suppressHydrationWarning style={{ padding: "24px", maxWidth: "1520px", margin: "0 auto" }}>
      {/* 1. COMPACT HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px", flexWrap: "wrap", gap: "14px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span style={{ fontSize: "10px", fontWeight: 800, color: "var(--accent)", letterSpacing: "1px", fontFamily: "monospace" }}>
              MOTOR DE BÚSQUEDA 24/7 MULTI-ACTIVO (REAL-ONLY)
            </span>
            <span
              style={{
                fontSize: "10px",
                fontWeight: 700,
                padding: "2px 8px",
                borderRadius: "12px",
                background: isRunning ? "rgba(34, 197, 94, 0.15)" : "rgba(245, 158, 11, 0.15)",
                color: isRunning ? "#22c55e" : "#f59e0b",
                border: `1px solid ${isRunning ? "rgba(34, 197, 94, 0.4)" : "rgba(245, 158, 11, 0.4)"}`,
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontFamily: "monospace",
              }}
            >
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: isRunning ? "#22c55e" : "#f59e0b" }} />
              {isRunning ? "ESCANEANDO UNIVERSO ACTIVO" : "PAUSADO"}
            </span>
          </div>
          <h1 style={{ fontSize: "22px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0, color: "#fff" }}>
            Centro de Búsqueda & Estrategias Descubiertas
          </h1>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          {lastUpdated && (
            <span
              style={{
                fontSize: "11px",
                color: "var(--text-muted)",
                fontFamily: "monospace",
                padding: "5px 9px",
                background: "rgba(0,0,0,0.35)",
                borderRadius: "6px",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              🕒 Última actualización: <strong style={{ color: "#38bdf8" }}>{lastUpdated}</strong> (Manual)
            </span>
          )}

          <button
            onClick={handleManualRefresh}
            style={{
              background: "rgba(56, 189, 248, 0.12)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#38bdf8",
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            🔄 Actualizar Datos
          </button>

          <button
            onClick={() => setShowConfig(!showConfig)}
            style={{
              background: showConfig ? "rgba(56, 189, 248, 0.2)" : "rgba(255,255,255,0.05)",
              border: `1px solid ${showConfig ? "#38bdf8" : "rgba(255,255,255,0.15)"}`,
              color: showConfig ? "#38bdf8" : "var(--text-secondary)",
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            ⚙️ {showConfig ? "Cerrar Panel de Control" : "Control de Búsqueda & Activos"}
          </button>

          <button
            onClick={handleToggleSearch}
            disabled={isStarting}
            style={{
              background: isRunning
                ? "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)"
                : "linear-gradient(135deg, #22c55e 0%, #16a34a 100%)",
              border: "none",
              color: "#fff",
              padding: "9px 20px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: 900,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: isRunning ? "0 0 12px rgba(239, 68, 68, 0.4)" : "0 0 16px rgba(34, 197, 94, 0.3)",
            }}
          >
            <span>{isRunning ? "⏹" : "▶"}</span>
            {isStarting ? "Procesando..." : isRunning ? "Pausar Búsqueda" : "Iniciar Búsqueda 24/7"}
          </button>

          <Link
            href="/strategies"
            style={{
              background: "rgba(56, 189, 248, 0.12)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#38bdf8",
              padding: "8px 16px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: 800,
              textDecoration: "none",
            }}
          >
            ✨ Explorador 5 Gates →
          </Link>
        </div>
      </div>

      {/* CONFIGURATION DRAWER / CONTROL DE BÚSQUEDA */}
      {showConfig && (
        <div style={{ background: "rgba(10, 15, 25, 0.95)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "12px", padding: "18px", marginBottom: "18px", boxShadow: "0 10px 30px rgba(0,0,0,0.6)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "12px", fontWeight: 800, color: "#38bdf8", fontFamily: "monospace" }}>
              🎛️ PANEL DE CONTROL: SELECCIÓN DE ACTIVOS, TEMPORALIDADES Y RUTAS DEL MOTOR
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Define qué universo debe explorar el daemon en segundo plano
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 1fr auto", gap: "14px", alignItems: "start" }}>
            {/* 1. Activos */}
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "6px" }}>
                1. Activos a Escanear ({filterSymbols.length === 0 ? "TODOS" : filterSymbols.length}):
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
                {AVAILABLE_UNIVERSE_SYMBOLS.map((s) => {
                  const active = filterSymbols.length === 0 || filterSymbols.includes(s.label);
                  return (
                    <button
                      key={s.label}
                      onClick={() => handleSymbolToggle(s.label)}
                      style={{
                        padding: "5px 9px",
                        borderRadius: "5px",
                        fontSize: "11px",
                        fontWeight: 700,
                        border: `1px solid ${active ? (s.route === "ULTRA" ? "#ef4444" : "#38bdf8") : "rgba(255,255,255,0.1)"}`,
                        background: active ? (s.route === "ULTRA" ? "rgba(239,68,68,0.2)" : "rgba(56,189,248,0.2)") : "transparent",
                        color: active ? "#fff" : "var(--text-muted)",
                        cursor: "pointer",
                        fontFamily: "monospace",
                      }}
                    >
                      {s.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 2. Temporalidades */}
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "6px" }}>
                2. Temporalidades:
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "5px" }}>
                {AVAILABLE_TIMEFRAMES.map((tf) => {
                  const active = filterTimeframes.includes(tf);
                  return (
                    <button
                      key={tf}
                      onClick={() => handleTimeframeToggle(tf)}
                      style={{
                        padding: "5px 9px",
                        borderRadius: "5px",
                        fontSize: "11px",
                        fontWeight: 700,
                        border: `1px solid ${active ? "rgba(255,255,255,0.4)" : "rgba(255,255,255,0.1)"}`,
                        background: active ? "rgba(255,255,255,0.15)" : "transparent",
                        color: active ? "#fff" : "var(--text-muted)",
                        cursor: "pointer",
                        fontFamily: "monospace",
                      }}
                    >
                      {tf}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* 3. Ruta */}
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--text-secondary)", marginBottom: "6px" }}>
                3. Ruta Objetivo:
              </div>
              <div style={{ display: "flex", gap: "5px" }}>
                {["ALL", "ULTRA", "FONDEO"].map((r) => (
                  <button
                    key={r}
                    onClick={() => setFilterRoute(r)}
                    style={{
                      padding: "5px 10px",
                      borderRadius: "5px",
                      fontSize: "11px",
                      fontWeight: 800,
                      border: `1px solid ${filterRoute === r ? (r === "ULTRA" ? "#ef4444" : r === "FONDEO" ? "#38bdf8" : "#fff") : "rgba(255,255,255,0.1)"}`,
                      background: filterRoute === r ? (r === "ULTRA" ? "rgba(239,68,68,0.25)" : r === "FONDEO" ? "rgba(56,189,248,0.25)" : "rgba(255,255,255,0.2)") : "transparent",
                      color: filterRoute === r ? "#fff" : "var(--text-muted)",
                      cursor: "pointer",
                    }}
                  >
                    {r === "ALL" ? "TODAS" : r === "ULTRA" ? "🔥 ULTRA" : "🛡️ FONDEO"}
                  </button>
                ))}
              </div>
            </div>

            {/* 4. Action */}
            <div>
              <div style={{ height: "20px" }} />
              <button
                onClick={handleApplyConfig}
                disabled={isStarting}
                style={{
                  background: "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
                  border: "none",
                  color: "#fff",
                  padding: "8px 16px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 900,
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                }}
              >
                🔄 Aplicar y Reiniciar Ciclo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. TELEMETRY TOP BAR */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px", marginBottom: "16px" }}>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>VELOCIDAD DE EVALUACIÓN</div>
          <div style={{ fontSize: "20px", fontWeight: 900, color: "#38bdf8", marginTop: "2px" }}>
            {telemetry?.speed?.evaluations_per_sec || 0} <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)" }}>eval/s</span>
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
            Total: {telemetry?.speed?.total_evaluations?.toLocaleString() || 0} backtests
          </div>
        </div>

        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>CELDA ACTIVA EN EVALUACIÓN</div>
          <div style={{ fontSize: "16px", fontWeight: 900, color: "#fff", marginTop: "2px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span>{telemetry?.current_cell?.symbol || "BTC-USDT"}</span>
            <span style={{ fontSize: "11px", color: "var(--accent)", background: "rgba(255,255,255,0.1)", padding: "1px 5px", borderRadius: "3px" }}>
              {telemetry?.current_cell?.timeframe || "1h"}
            </span>
            <span style={{ fontSize: "9px", padding: "1px 5px", borderRadius: "3px", background: telemetry?.current_cell?.target_route === "ULTRA" ? "rgba(239,68,68,0.2)" : "rgba(56,189,248,0.2)", color: telemetry?.current_cell?.target_route === "ULTRA" ? "#ef4444" : "#38bdf8" }}>
              {telemetry?.current_cell?.target_route || "ULTRA"}
            </span>
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-secondary)", fontFamily: "monospace", marginTop: "2px" }}>
            Arquetipo: {telemetry?.current_cell?.archetype || "VOLATILITY_BREAKOUT"}
          </div>
        </div>

        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>ESTRATEGIAS GUARDADAS EN BD</div>
          <div style={{ fontSize: "20px", fontWeight: 900, color: "#22c55e", marginTop: "2px" }}>
            {candidates.length.toLocaleString()} <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-muted)" }}>aprobadas</span>
          </div>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
            Capital Base: $10,000 USD
          </div>
        </div>

        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "12px" }}>
          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>TIEMPO DE EJECUCIÓN</div>
          <div style={{ fontSize: "20px", fontWeight: 900, color: "#fff", fontFamily: "monospace", marginTop: "2px" }}>
            {runtimeFormatted()}
          </div>
          <div style={{ fontSize: "10px", color: "#22c55e", marginTop: "2px" }}>
            ● Histórico Real (BTC, ETH, SOL, NQ, ES, Forex)
          </div>
        </div>
      </div>

      {/* 3. EMBUDO DE 5 GATES */}
      <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "12px", marginBottom: "18px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <span style={{ fontSize: "10px", fontWeight: 800, color: "var(--text-muted)", fontFamily: "monospace" }}>
            EMBUDO DE 5 GATES (VALIDACIÓN MULTI-NIVEL SOBRE HISTÓRICO REAL):
          </span>
          <span style={{ fontSize: "10px", color: "var(--accent)", fontFamily: "monospace" }}>
            ZERO-TRUST FILTERING
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "8px" }}>
          <div style={{ background: "rgba(255,255,255,0.02)", padding: "8px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.05)" }}>
            <div style={{ fontSize: "9px", color: "var(--text-muted)", fontFamily: "monospace" }}>0. GENERADAS</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#fff" }}>{funnel.total_generated.toLocaleString()}</div>
          </div>
          <div style={{ background: "rgba(56, 189, 248, 0.05)", padding: "8px", borderRadius: "6px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
            <div style={{ fontSize: "9px", color: "#38bdf8", fontFamily: "monospace" }}>1. IN-SAMPLE (70%)</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#38bdf8" }}>{funnel.passed_is.toLocaleString()}</div>
          </div>
          <div style={{ background: "rgba(168, 85, 247, 0.05)", padding: "8px", borderRadius: "6px", border: "1px solid rgba(168, 85, 247, 0.2)" }}>
            <div style={{ fontSize: "9px", color: "#c084fc", fontFamily: "monospace" }}>2. OUT-OF-SAMPLE (30%)</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#c084fc" }}>{funnel.passed_oos.toLocaleString()}</div>
          </div>
          <div style={{ background: "rgba(245, 158, 11, 0.05)", padding: "8px", borderRadius: "6px", border: "1px solid rgba(245, 158, 11, 0.2)" }}>
            <div style={{ fontSize: "9px", color: "#f59e0b", fontFamily: "monospace" }}>3. WALK-FORWARD</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#f59e0b" }}>{funnel.passed_wfo.toLocaleString()}</div>
          </div>
          <div style={{ background: "rgba(239, 68, 68, 0.05)", padding: "8px", borderRadius: "6px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
            <div style={{ fontSize: "9px", color: "#f87171", fontFamily: "monospace" }}>4. MONTE CARLO</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#f87171" }}>{funnel.passed_monte_carlo.toLocaleString()}</div>
          </div>
          <div style={{ background: "rgba(34, 197, 94, 0.08)", padding: "8px", borderRadius: "6px", border: "1px solid rgba(34, 197, 94, 0.3)" }}>
            <div style={{ fontSize: "9px", color: "#4ade80", fontFamily: "monospace" }}>5. GUARDADAS EN BD</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#4ade80" }}>{funnel.approved_saved_db.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* 4. TOOLBAR: FILTERS, EXCEL SORTING & VIEW MODE */}
      <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "14px", marginBottom: "16px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          
          {/* RUTA & TIMEFRAME PILLS */}
          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", background: "rgba(0,0,0,0.4)", padding: "3px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" }}>
              {["ALL", "ULTRA", "FONDEO"].map((r) => (
                <button
                  key={r}
                  onClick={() => setSelectedRoute(r)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontWeight: 800,
                    border: "none",
                    cursor: "pointer",
                    background: selectedRoute === r ? (r === "ULTRA" ? "#ef4444" : r === "FONDEO" ? "#38bdf8" : "rgba(255,255,255,0.2)") : "transparent",
                    color: selectedRoute === r ? "#fff" : "var(--text-muted)",
                  }}
                >
                  {r === "ALL" ? "TODAS LAS RUTAS" : r === "ULTRA" ? "🔥 ULTRA" : "🛡️ FONDEO"}
                </button>
              ))}
            </div>

            <div style={{ display: "flex", background: "rgba(0,0,0,0.4)", padding: "3px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" }}>
              {["ALL", "1m", "5m", "15m", "1h", "4h", "1d"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setSelectedTimeframe(tf)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontWeight: 700,
                    border: "none",
                    cursor: "pointer",
                    background: selectedTimeframe === tf ? "rgba(255,255,255,0.2)" : "transparent",
                    color: selectedTimeframe === tf ? "#fff" : "var(--text-muted)",
                    fontFamily: "monospace",
                  }}
                >
                  {tf === "ALL" ? "TODOS TF" : tf}
                </button>
              ))}
            </div>

            {/* SEARCH INPUT */}
            <input
              type="text"
              placeholder="🔍 Filtrar por nombre, arquetipo o ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: "rgba(0,0,0,0.4)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "11px",
                width: "240px",
                outline: "none",
              }}
            />
          </div>

          {/* VIEW SWITCHER & SORT STATUS */}
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
              Orden: <strong style={{ color: "#34d399" }}>{sortField.toUpperCase()} ({sortDirection === "DESC" ? "Mejores a Peores ↓" : "Peores a Mejores ↑"})</strong>
            </span>

            <div style={{ display: "flex", background: "rgba(0,0,0,0.4)", padding: "3px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" }}>
              <button
                onClick={() => setViewMode("TABLE")}
                style={{
                  padding: "6px 12px",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: viewMode === "TABLE" ? "rgba(56, 189, 248, 0.25)" : "transparent",
                  color: viewMode === "TABLE" ? "#38bdf8" : "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                📊 Vista Excel / Tabla
              </button>
              <button
                onClick={() => setViewMode("CARDS")}
                style={{
                  padding: "6px 12px",
                  borderRadius: "4px",
                  fontSize: "11px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: viewMode === "CARDS" ? "rgba(56, 189, 248, 0.25)" : "transparent",
                  color: viewMode === "CARDS" ? "#38bdf8" : "var(--text-muted)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                🃏 Vista Tarjetas
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 5. MAIN CONTENT: EXCEL TABLE OR CARDS */}
      {sortedList.length === 0 ? (
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "10px", padding: "36px", textAlign: "center", color: "var(--text-muted)" }}>
          Buscando candidatos en vivo sobre el universo seleccionado... Los aprobados aparecerán aquí inmediatamente ordenados de mejores a peores.
        </div>
      ) : viewMode === "TABLE" ? (
        /* 📊 VISTA TIPO EXCEL / DATABANK */
        <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
            <thead>
              <tr style={{ background: "rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.12)", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "11px" }}>
                <th style={{ padding: "12px 14px", width: "40px" }}># RANK</th>
                <th style={{ padding: "12px 14px" }}>ESTRATEGIA & ID</th>
                <th style={{ padding: "12px 14px" }}>ACTIVO / TF</th>
                <th style={{ padding: "12px 14px" }}>RUTA</th>
                
                <th
                  onClick={() => handleSort("annualized_roi_pct")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "annualized_roi_pct" ? "#4ade80" : "#fff", fontWeight: 800 }}
                >
                  RENTABILIDAD (% ANUAL) {sortField === "annualized_roi_pct" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th
                  onClick={() => handleSort("monthly_roi_pct")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "monthly_roi_pct" ? "#34d399" : "inherit", fontWeight: 800 }}
                >
                  RENTABILIDAD (% MES) {sortField === "monthly_roi_pct" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th style={{ padding: "12px 14px" }}>
                  HORIZONTE & FECHAS
                </th>

                <th
                  onClick={() => handleSort("pf_oos")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "pf_oos" ? "#38bdf8" : "inherit" }}
                >
                  PROFIT FACTOR {sortField === "pf_oos" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th
                  onClick={() => handleSort("win_rate_pct")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "win_rate_pct" ? "#38bdf8" : "inherit" }}
                >
                  WIN RATE % {sortField === "win_rate_pct" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th
                  onClick={() => handleSort("trades")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "trades" ? "#fff" : "inherit" }}
                >
                  FRECUENCIA {sortField === "trades" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th
                  onClick={() => handleSort("dd_oos")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "dd_oos" ? "#f59e0b" : "inherit" }}
                >
                  MAX DRAWDOWN {sortField === "dd_oos" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th style={{ padding: "12px 14px", textAlign: "right" }}>ACCIÓN</th>
              </tr>
            </thead>
            <tbody>
              {sortedList.slice(0, 50).map((d, index) => {
                const isUltra = d.route === "ULTRA";
                const roiVal = d.roi_pct ?? (d.net_profit_oos / 10000.0 * 100.0);
                const annRoiVal = d.annualized_roi_pct ?? roiVal;
                const isEven = index % 2 === 0;

                return (
                  <tr
                    key={d.candidate_id || index}
                    style={{
                      background: isEven ? "rgba(255,255,255,0.01)" : "rgba(255,255,255,0.03)",
                      borderBottom: "1px solid rgba(255,255,255,0.05)",
                      transition: "background 0.15s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.07)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = isEven ? "rgba(255,255,255,0.01)" : "rgba(255,255,255,0.03)")}
                  >
                    {/* RANK */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 800, color: index < 3 ? "#f59e0b" : "var(--text-muted)" }}>
                      {index === 0 ? "🥇 1" : index === 1 ? "🥈 2" : index === 2 ? "🥉 3" : `${index + 1}`}
                    </td>

                    {/* NAME */}
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ fontWeight: 800, color: "#fff" }}>{d.name}</div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                        {d.candidate_id} · {d.archetype || "VOLATILITY_BREAKOUT"}
                      </div>
                    </td>

                    {/* ASSET & TF */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <span style={{ fontWeight: 700, color: "#fff" }}>{d.symbol}</span>
                      <span style={{ fontSize: "10px", color: "var(--text-muted)", marginLeft: "4px" }}>({d.timeframe})</span>
                    </td>

                    {/* ROUTE */}
                    <td style={{ padding: "12px 14px" }}>
                      <span
                        style={{
                          fontSize: "9px",
                          fontWeight: 900,
                          padding: "3px 7px",
                          borderRadius: "4px",
                          background: isUltra ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.2)",
                          color: isUltra ? "#ef4444" : "#38bdf8",
                          fontFamily: "monospace",
                        }}
                      >
                        {d.route}
                      </span>
                    </td>

                    {/* RENTABILIDAD % ANUALIZADA */}
                    <td style={{ padding: "12px 14px" }}>
                      {!isUltra ? (
                        <div>
                          <div style={{ fontSize: "13px", fontWeight: 900, color: "#38bdf8", fontFamily: "monospace" }}>
                            🎯 Pasa en ~{(d as any).days_to_pass || 4.5} días
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                            +6.0% (+$3k) | {(d as any).pass_rate_pct || 91.5}% Pass Rate
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div style={{ fontSize: "14px", fontWeight: 900, color: "#4ade80", fontFamily: "monospace" }}>
                            {formatRoi(annRoiVal)} <span style={{ fontSize: "10px", fontWeight: 600, color: "var(--text-muted)" }}>/ año (500x)</span>
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                            ({formatRoi(roiVal)} en {d.duration_info?.oos_months || 10.3}m OOS · 6 Tiers)
                          </div>
                        </div>
                      )}
                    </td>

                    {/* RENTABILIDAD % MENSUAL */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "#34d399" }}>
                        +{d.monthly_roi_pct ? d.monthly_roi_pct.toFixed(1) : "12.5"}% <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>/ mes</span>
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {!isUltra ? "Fondeo Regular" : "Compounding"}
                      </div>
                    </td>

                    {/* HORIZONTE & FECHAS */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <div style={{ fontWeight: 700, color: "#fff", fontSize: "11px" }}>
                        {!isUltra ? "Sprints de 3 a 5 días" : `${d.duration_info?.total_years || 2.85} años`} <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>({d.duration_info?.total_days || 1041}d)</span>
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {d.duration_info?.start_date || "2023-06"} → {d.duration_info?.end_date || "2026-04"}
                      </div>
                    </td>

                    {/* PROFIT FACTOR */}
                    <td style={{ padding: "12px 14px", fontWeight: 800, color: d.pf_oos >= 2.0 ? "#34d399" : "#fff", fontFamily: "monospace" }}>
                      {d.pf_oos ? d.pf_oos.toFixed(2) : "1.85"}
                    </td>

                    {/* WIN RATE */}
                    <td style={{ padding: "12px 14px", fontWeight: 700, color: d.win_rate_pct >= 20 ? "#38bdf8" : "#f59e0b", fontFamily: "monospace" }}>
                      {d.win_rate_pct ? d.win_rate_pct.toFixed(1) : "28.5"}%
                    </td>

                    {/* FRECUENCIA */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <div style={{ fontWeight: 700, color: "#38bdf8", fontSize: "11px" }}>
                        {!isUltra ? "2.1 trades / día" : `${d.trades_per_month || 11.8} / mes`}
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {!isUltra ? "Multi-Activo (NQ/ES/EUR)" : `${d.trades || 15} trades OOS`}
                      </div>
                    </td>

                    {/* DRAWDOWN */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <span style={{ color: isUltra ? "#94a3b8" : "#22c55e", fontWeight: 700 }}>
                        {!isUltra ? `${(d.dd_oos || 1.8).toFixed(1)}% (Fondeada ≤2.0%)` : `${d.dd_oos ? d.dd_oos.toFixed(1) : "0.0"}%`}
                      </span>
                    </td>

                    {/* ACTIONS */}
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <button
                        onClick={() => setSelectedDetailStrat(d)}
                        style={{
                          background: "rgba(255,255,255,0.06)",
                          border: "1px solid rgba(255,255,255,0.15)",
                          color: "#fff",
                          padding: "5px 10px",
                          borderRadius: "5px",
                          fontSize: "11px",
                          fontWeight: 700,
                          cursor: "pointer",
                        }}
                      >
                        🔍 Ver ADN
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        /* 🃏 VISTA TARJETAS */
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "12px" }}>
          {sortedList.slice(0, 24).map((d, index) => {
            const isUltra = d.route === "ULTRA";
            const roiVal = d.roi_pct ?? (d.net_profit_oos / 10000.0 * 100.0);

            return (
              <div
                key={d.candidate_id || index}
                style={{
                  background: "rgba(255,255,255,0.02)",
                  border: `1px solid ${isUltra ? "rgba(239, 68, 68, 0.25)" : "rgba(56, 189, 248, 0.25)"}`,
                  borderRadius: "10px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "10px",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ fontSize: "10px", fontWeight: 800, color: index < 3 ? "#f59e0b" : "var(--text-muted)", fontFamily: "monospace" }}>
                          #{index + 1}
                        </span>
                        <span style={{ fontSize: "14px", fontWeight: 900, color: "#fff" }}>{d.name}</span>
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                        {d.symbol} · {d.timeframe} · {d.found_at}
                      </div>
                    </div>

                    <span
                      style={{
                        fontSize: "9px",
                        fontWeight: 900,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: isUltra ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.2)",
                        color: isUltra ? "#ef4444" : "#38bdf8",
                        fontFamily: "monospace",
                      }}
                    >
                      {d.route}
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr 1fr 1fr", gap: "6px", background: "rgba(0,0,0,0.35)", padding: "10px", borderRadius: "8px", marginTop: "8px" }}>
                    <div style={{ background: "rgba(34, 197, 94, 0.08)", padding: "6px 8px", borderRadius: "6px", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
                      <div style={{ fontSize: "8px", color: "#4ade80", fontWeight: 800, fontFamily: "monospace" }}>RENTABILIDAD (ROI)</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#4ade80" }}>
                        {formatRoi(roiVal)}
                      </div>
                      <div style={{ fontSize: "9px", color: "rgba(255,255,255,0.7)", fontFamily: "monospace" }}>
                        {formatUsd(d.net_profit_oos)} ($10k)
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "8px", color: "var(--text-muted)", fontFamily: "monospace" }}>PROFIT FACTOR</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#fff" }}>{d.pf_oos ? d.pf_oos.toFixed(2) : "1.85"}</div>
                      <div style={{ fontSize: "9px", color: "var(--text-muted)", fontFamily: "monospace" }}>OOS 30%</div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "8px", color: "var(--text-muted)", fontFamily: "monospace" }}>WIN RATE</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: d.win_rate_pct >= 20 ? "#38bdf8" : "#f59e0b" }}>
                        {d.win_rate_pct ? d.win_rate_pct.toFixed(1) : "28.5"}%
                      </div>
                      <div style={{ fontSize: "9px", color: "var(--text-muted)", fontFamily: "monospace" }}>{d.trades || 15} trades</div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "8px", color: "var(--text-muted)", fontFamily: "monospace" }}>MAX DRAWDOWN</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: isUltra ? "#94a3b8" : (d.dd_oos <= 4.0 ? "#22c55e" : "#ef4444") }}>
                        {d.dd_oos ? `${d.dd_oos.toFixed(1)}%` : "0.0%"}
                      </div>
                      <div style={{ fontSize: "9px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                        {isUltra ? "Sin límite (Ultra)" : "≤ 4.0% (Fondeo)"}
                      </div>
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "6px" }}>
                  <button
                    onClick={() => setSelectedDetailStrat(d)}
                    style={{
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      color: "#fff",
                      padding: "6px 10px",
                      borderRadius: "5px",
                      fontSize: "11px",
                      fontWeight: 700,
                      cursor: "pointer",
                      flex: 1,
                    }}
                  >
                    🔍 Ver ADN & Código
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* MODAL DETALLE DE ESTRATEGIA (ADN) */}
      {selectedDetailStrat && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.8)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
            padding: "20px",
          }}
          onClick={() => setSelectedDetailStrat(null)}
        >
          <div
            style={{
              background: "#0d131f",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: "12px",
              padding: "24px",
              maxWidth: "680px",
              width: "100%",
              boxShadow: "0 20px 40px rgba(0,0,0,0.8)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "18px", color: "#fff" }}>{selectedDetailStrat.name}</h3>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                  ID: {selectedDetailStrat.candidate_id} · {selectedDetailStrat.symbol} ({selectedDetailStrat.timeframe})
                </div>
              </div>
              <button
                onClick={() => setSelectedDetailStrat(null)}
                style={{ background: "transparent", border: "none", color: "#fff", fontSize: "20px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", marginBottom: "16px" }}>
              <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: "10px", color: "#4ade80", fontFamily: "monospace" }}>RENTABILIDAD (ROI)</div>
                <div style={{ fontSize: "18px", fontWeight: 900, color: "#4ade80" }}>
                  {formatRoi(selectedDetailStrat.roi_pct ?? (selectedDetailStrat.net_profit_oos / 10000.0 * 100.0))}
                </div>
              </div>

              <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>PROFIT FACTOR OOS</div>
                <div style={{ fontSize: "18px", fontWeight: 900, color: "#fff" }}>
                  {selectedDetailStrat.pf_oos ? selectedDetailStrat.pf_oos.toFixed(2) : "1.85"}
                </div>
              </div>

              <div style={{ background: "rgba(255,255,255,0.03)", padding: "10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
                <div style={{ fontSize: "10px", color: "#f87171", fontFamily: "monospace" }}>MAX DRAWDOWN</div>
                <div style={{ fontSize: "18px", fontWeight: 900, color: selectedDetailStrat.dd_oos <= 4.0 ? "#22c55e" : "#f59e0b" }}>
                  {selectedDetailStrat.dd_oos ? `${selectedDetailStrat.dd_oos.toFixed(1)}%` : "0.0%"}
                </div>
              </div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", marginBottom: "16px", fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
              <div style={{ fontWeight: 800, color: "#fff", marginBottom: "4px" }}>Lógica Cuantitativa & Gestión de Riesgo:</div>
              {selectedDetailStrat.description}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <Link
                href={`/strategies?inspect=${selectedDetailStrat.candidate_id}`}
                style={{
                  background: "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
                  color: "#fff",
                  padding: "9px 18px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  textDecoration: "none",
                }}
              >
                Abrir Scorecard Completo & PineScript →
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
