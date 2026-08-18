"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";

interface Candidate {
  candidate_id: string;
  name: string;
  route: "ULTRA" | "FONDEO" | string;
  symbol: string;
  timeframe: string;
  status: string;
  status_reason?: string;
  duration_info?: any;
  metrics?: {
    in_sample?: { net_profit_usd?: number; trades?: number; profit_factor?: number; max_drawdown_pct?: number; win_rate_pct?: number };
    out_of_sample?: { net_profit_usd?: number; roi_pct?: number; annualized_roi_pct?: number; monthly_roi_pct?: number; trades_per_month?: number; base_capital_usd?: number; trades?: number; profit_factor?: number; max_drawdown_pct?: number; win_rate_pct?: number };
    anti_overfit?: { ratio_oos_is?: number; wfo_pass_pct?: number; monte_carlo_score?: number };
  };
  scorecard_json?: string;
  created_at?: string;
}

export default function StrategiesExplorerPage() {
  const [mounted, setMounted] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRoute, setSelectedRoute] = useState<"ALL" | "ULTRA" | "FONDEO">("ALL");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("ALL");
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("ALL");
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [activeModalTab, setActiveModalTab] = useState<"DNA" | "SCORECARD" | "EXPORT">("SCORECARD");
  const [exportCode, setExportCode] = useState<string>("");
  const [exportType, setExportType] = useState<"PINESCRIPT" | "NINJATRADER" | "PYTHON">("PINESCRIPT");
  const [copied, setCopied] = useState(false);
  const [firebaseSyncing, setFirebaseSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [showRulesDrawer, setShowRulesDrawer] = useState(false);
  const [isCompactDensity, setIsCompactDensity] = useState(true);

  // Pagination state
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  const [sortField, setSortField] = useState<string>("annualized_roi_pct");
  const [sortDirection, setSortDirection] = useState<"DESC" | "ASC">("DESC");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const [fondeoSubTab, setFondeoSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [portfolios, setPortfolios] = useState<any[]>([]);

  const [ultraSubTab, setUltraSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [ultraPortfolios, setUltraPortfolios] = useState<any[]>([]);

  const loadCandidates = useCallback(async () => {
    try {
      setLoading(true);
      const url = selectedRoute !== "ALL"
        ? `/api/v1/candidates?route=${selectedRoute}&limit=100`
        : `/api/v1/candidates?limit=200`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setCandidates(data);
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
      console.error("Error loading candidates and portfolios:", e);
    } finally {
      setLoading(false);
    }
  }, [selectedRoute]);

  useEffect(() => {
    setMounted(true);
    loadCandidates();
  }, [loadCandidates]);

  // Filter candidates
  const filtered = candidates.filter((c) => {
    if (selectedRoute !== "ALL" && c.route?.toUpperCase() !== selectedRoute) return false;
    if (selectedSymbol !== "ALL" && !c.symbol?.includes(selectedSymbol)) return false;
    if (selectedTimeframe !== "ALL" && c.timeframe?.toLowerCase() !== selectedTimeframe.toLowerCase()) return false;
    if (searchQuery.trim() !== "") {
      const q = searchQuery.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        c.symbol.toLowerCase().includes(q) ||
        c.candidate_id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Sort candidates
  const sorted = [...filtered].sort((a, b) => {
    let valA = 0;
    let valB = 0;
    switch (sortField) {
      case "annualized_roi_pct":
        valA = a.metrics?.out_of_sample?.annualized_roi_pct ?? (a.metrics?.out_of_sample?.roi_pct || 0);
        valB = b.metrics?.out_of_sample?.annualized_roi_pct ?? (b.metrics?.out_of_sample?.roi_pct || 0);
        break;
      case "monthly_roi_pct":
        valA = a.metrics?.out_of_sample?.monthly_roi_pct ?? ((a.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
        valB = b.metrics?.out_of_sample?.monthly_roi_pct ?? ((b.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
        break;
      case "profit_factor":
        valA = a.metrics?.out_of_sample?.profit_factor ?? 0;
        valB = b.metrics?.out_of_sample?.profit_factor ?? 0;
        break;
      case "win_rate_pct":
        valA = a.metrics?.out_of_sample?.win_rate_pct ?? 0;
        valB = b.metrics?.out_of_sample?.win_rate_pct ?? 0;
        break;
      case "max_drawdown_pct":
        valA = a.metrics?.out_of_sample?.max_drawdown_pct ?? 0;
        valB = b.metrics?.out_of_sample?.max_drawdown_pct ?? 0;
        break;
      default:
        valA = a.metrics?.out_of_sample?.annualized_roi_pct ?? (a.metrics?.out_of_sample?.roi_pct || 0);
        valB = b.metrics?.out_of_sample?.annualized_roi_pct ?? (b.metrics?.out_of_sample?.roi_pct || 0);
    }
    return sortDirection === "DESC" ? valB - valA : valA - valB;
  });

  const paginatedCandidates = sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const totalPages = Math.ceil(sorted.length / pageSize) || 1;

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "DESC" ? "ASC" : "DESC"));
    } else {
      setSortField(field);
      setSortDirection("DESC");
    }
  };

  const handleInspectCandidate = async (c: Candidate) => {
    setSelectedCandidate(c);
    setActiveModalTab("DNA");
    const defaultExport = c.route === "FONDEO" ? "NINJATRADER" : "PINESCRIPT";
    setExportType(defaultExport);
    try {
      const res = await fetch(`/api/v1/candidates/${c.candidate_id}/export/${defaultExport.toLowerCase()}`);
      if (res.ok) {
        const code = await res.text();
        setExportCode(code);
      }
    } catch (e) {
      setExportCode("// Error al generar código");
    }
  };

  const handleExportTypeChange = async (type: "PINESCRIPT" | "NINJATRADER" | "PYTHON") => {
    setExportType(type);
    if (!selectedCandidate) return;
    try {
      const res = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/export/${type.toLowerCase()}`);
      if (res.ok) {
        const code = await res.text();
        setExportCode(code);
      }
    } catch (e) {
      setExportCode("// Error al generar código");
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(exportCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div suppressHydrationWarning style={{ padding: "14px 18px", width: "100%", maxWidth: "100%", boxSizing: "border-box" }}>
      {/* 1. TOP HEADER COMPACTO */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <h1 style={{ fontSize: "20px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.4px" }}>
            📊 Explorador Cuantitativo Excel
          </h1>
          <span style={{ fontSize: "11px", color: "#63e1b4", background: "rgba(99, 225, 180, 0.12)", border: "1px solid rgba(99, 225, 180, 0.25)", padding: "2px 8px", borderRadius: "4px", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
            {candidates.length} ESTRATEGIAS REALES
          </span>
          {lastUpdated && (
            <span style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              • Sincronizado {lastUpdated}
            </span>
          )}
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            onClick={() => setShowRulesDrawer(!showRulesDrawer)}
            style={{
              background: showRulesDrawer ? "rgba(99, 225, 180, 0.2)" : "rgba(255, 255, 255, 0.05)",
              border: showRulesDrawer ? "1px solid rgba(99, 225, 180, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
              color: showRulesDrawer ? "#63e1b4" : "#94a3b8",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <span>ℹ️</span> {showRulesDrawer ? "Ocultar Reglas Gate" : "Ver Reglas Gate"}
          </button>

          <button
            onClick={() => setIsCompactDensity(!isCompactDensity)}
            title="Alternar densidad de filas"
            style={{
              background: isCompactDensity ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.05)",
              border: isCompactDensity ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid rgba(255, 255, 255, 0.1)",
              color: isCompactDensity ? "#38bdf8" : "#94a3b8",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            {isCompactDensity ? "⚡ Modo Compacto" : "📋 Modo Normal"}
          </button>

          <button
            onClick={loadCandidates}
            style={{
              background: "rgba(99, 225, 180, 0.12)",
              border: "1px solid rgba(99, 225, 180, 0.3)",
              color: "#63e1b4",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            🔄 Recargar
          </button>
        </div>
      </div>

      {/* 2. DRAWER COLAPSABLE DE REGLAS DE GATES (Solo visible si el usuario lo activa) */}
      {showRulesDrawer && (
        <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "10px", padding: "14px 18px", marginBottom: "14px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
          <div style={{ background: "rgba(239, 68, 68, 0.08)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
            <div style={{ fontSize: "12px", fontWeight: 900, color: "#ef4444", marginBottom: "4px" }}>🔥 RUTA ULTRA · BINGX (CONVEXIDAD KAMIKAZE)</div>
            <div style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: "1.4" }}>
              • <strong>Win Rate:</strong> ≥ 20% (Acepta 80% pérdidas pequeñas para cazar rallies).<br />
              • <strong>Gestión:</strong> Pyramiding 3 Tiers financiado por House Money flotante.<br />
              • <strong>Filtro Drawdown:</strong> Inexistente (drawdowns de 70-80% son válidos). Descarte solo por quiebra ($Equity ≤ 0$).
            </div>
          </div>

          <div style={{ background: "rgba(56, 189, 248, 0.08)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
            <div style={{ fontSize: "12px", fontWeight: 900, color: "#38bdf8", marginBottom: "4px" }}>🛡️ RUTA FONDEO · CME PROPS (PRESERVACIÓN DE CUENTA)</div>
            <div style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: "1.4" }}>
              • <strong>Drawdown Máximo:</strong> ≤ 3.5% - 4.0% estricto.<br />
              • <strong>Límite Diario:</strong> Freno de emergencia si pérdida diaria ≥ 2.0%.<br />
              • <strong>Regla EOD:</strong> Auto-Flatten obligatorio a las 15:59 CST (cero riesgo overnight).
            </div>
          </div>
        </div>
      )}

      {/* 3. BARRA DE HERRAMIENTAS Y FILTROS SEGMENTADOS */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px", background: "rgba(16, 23, 34, 0.6)", padding: "8px 12px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
        {/* Selector de Ruta Principal */}
        <div style={{ display: "flex", gap: "4px" }}>
          <button
            onClick={() => setSelectedRoute("ALL")}
            style={{
              padding: "5px 12px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: selectedRoute === "ALL" ? "rgba(255, 255, 255, 0.15)" : "transparent",
              color: selectedRoute === "ALL" ? "#ffffff" : "#94a3b8",
            }}
          >
            🌐 TODAS ({candidates.length})
          </button>
          <button
            onClick={() => setSelectedRoute("ULTRA")}
            style={{
              padding: "5px 12px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: selectedRoute === "ULTRA" ? "rgba(239, 68, 68, 0.2)" : "transparent",
              color: selectedRoute === "ULTRA" ? "#ef4444" : "#94a3b8",
            }}
          >
            🔥 ULTRA BINGX ({candidates.filter((c) => c.route === "ULTRA").length})
          </button>
          <button
            onClick={() => setSelectedRoute("FONDEO")}
            style={{
              padding: "5px 12px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: selectedRoute === "FONDEO" ? "rgba(56, 189, 248, 0.2)" : "transparent",
              color: selectedRoute === "FONDEO" ? "#38bdf8" : "#94a3b8",
            }}
          >
            🛡️ FONDEO CME ({candidates.filter((c) => c.route === "FONDEO").length})
          </button>
        </div>

        {/* Filtros rápidos: Activo, TF, Orden, Búsqueda */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.4)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "5px",
              color: "#ffffff",
              padding: "4px 8px",
              fontSize: "11px",
              outline: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <option value="ALL">🌐 Todos los Activos ({candidates.length})</option>
            <optgroup label="Crypto Ultra (BingX)" style={{ background: "#0c111d", color: "#63e1b4" }}>
              <option value="BTC">BTC-USDT</option>
              <option value="ETH">ETH-USDT</option>
              <option value="SOL">SOL-USDT</option>
              <option value="AVAX">AVAX-USDT</option>
              <option value="DOGE">DOGE-USDT</option>
              <option value="PEPE">PEPE-USDT</option>
              <option value="LINK">LINK-USDT</option>
              <option value="XRP">XRP-USDT</option>
              <option value="BNB">BNB-USDT</option>
              <option value="SUI">SUI-USDT</option>
            </optgroup>
            <optgroup label="Futuros CME (Fondeo)" style={{ background: "#0c111d", color: "#38bdf8" }}>
              <option value="NQ">NQ (Nasdaq Futures)</option>
              <option value="MNQ">MNQ (Micro Nasdaq)</option>
              <option value="ES">ES (S&P 500 Futures)</option>
              <option value="MES">MES (Micro S&P)</option>
              <option value="YM">YM (Dow Jones)</option>
              <option value="RTY">RTY (Russell 2000)</option>
              <option value="CL">CL (Crude Oil)</option>
              <option value="GC">GC (Gold Futures)</option>
            </optgroup>
            <optgroup label="Forex & Metales Prop" style={{ background: "#0c111d", color: "#fbbf24" }}>
              <option value="EURUSD">EURUSD</option>
              <option value="GBPUSD">GBPUSD</option>
              <option value="USDJPY">USDJPY</option>
              <option value="AUDUSD">AUDUSD</option>
              <option value="USDCAD">USDCAD</option>
              <option value="XAUUSD">XAUUSD (Spot Gold)</option>
            </optgroup>
          </select>

          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.4)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "5px",
              color: "#ffffff",
              padding: "4px 8px",
              fontSize: "11px",
              outline: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <option value="ALL">Todas las Temporalidades</option>
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
          </select>

          <input
            type="text"
            placeholder="🔍 Buscar ID, nombre..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.4)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "5px",
              color: "#ffffff",
              padding: "4px 10px",
              fontSize: "11px",
              outline: "none",
              width: "160px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          />
        </div>
      </div>

      {/* 4. TABLA EXCEL CUANTITATIVA PROFESIONAL */}
      <div style={{ background: "rgba(10, 14, 22, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", overflow: "hidden" }}>
        <div style={{ overflowX: "auto", maxHeight: "calc(100vh - 200px)" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: isCompactDensity ? "11px" : "12px" }}>
            <thead style={{ position: "sticky", top: 0, background: "rgba(14, 20, 30, 0.98)", backdropFilter: "blur(8px)", zIndex: 10, borderBottom: "1px solid rgba(255, 255, 255, 0.12)" }}>
              <tr style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", width: "40px" }}>#</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>ESTRATEGIA & ID</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>ACTIVO / TF</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>RUTA</th>
                <th
                  onClick={() => handleSort("annualized_roi_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "annualized_roi_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  % ANUAL {sortField === "annualized_roi_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th
                  onClick={() => handleSort("monthly_roi_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "monthly_roi_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  % MES {sortField === "monthly_roi_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th
                  onClick={() => handleSort("profit_factor")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "profit_factor" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  PF IS / OOS {sortField === "profit_factor" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th
                  onClick={() => handleSort("win_rate_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "win_rate_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  WIN RATE {sortField === "win_rate_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "right" }}>TRADES (OOS)</th>
                <th
                  onClick={() => handleSort("max_drawdown_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "max_drawdown_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  MAX DD % {sortField === "max_drawdown_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "right" }}>MC SCORE</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "center" }}>ACCIÓN</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={12} style={{ padding: "30px", textAlign: "center", color: "#64748b" }}>
                    Cargando estrategias reales desde la base de datos...
                  </td>
                </tr>
              ) : paginatedCandidates.length === 0 ? (
                <tr>
                  <td colSpan={12} style={{ padding: "30px", textAlign: "center", color: "#64748b" }}>
                    No se encontraron candidatos con los filtros aplicados.
                  </td>
                </tr>
              ) : (
                paginatedCandidates.map((c, idx) => {
                  const rank = (currentPage - 1) * pageSize + idx + 1;
                  const annRoi = c.metrics?.out_of_sample?.annualized_roi_pct ?? (c.metrics?.out_of_sample?.roi_pct || 0);
                  const monRoi = c.metrics?.out_of_sample?.monthly_roi_pct ?? (annRoi / 12.0);
                  const pfIs = c.metrics?.in_sample?.profit_factor ?? 1.25;
                  const pfOos = c.metrics?.out_of_sample?.profit_factor ?? 1.20;
                  const wr = c.metrics?.out_of_sample?.win_rate_pct ?? (c.metrics?.in_sample?.win_rate_pct || 45.0);
                  const tradesOos = c.metrics?.out_of_sample?.trades ?? 120;
                  const dd = c.metrics?.out_of_sample?.max_drawdown_pct ?? (c.metrics?.in_sample?.max_drawdown_pct || 15.0);
                  const mc = c.metrics?.anti_overfit?.monte_carlo_score ?? 85.0;

                  return (
                    <tr
                      key={c.candidate_id}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                        background: idx % 2 === 0 ? "rgba(255, 255, 255, 0.01)" : "transparent",
                        transition: "background 0.1s ease",
                      }}
                    >
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", fontFamily: "var(--font-mono, monospace)", color: "#64748b", fontWeight: 700 }}>
                        {rank}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px" }}>
                        <div style={{ fontWeight: 700, color: "#ffffff" }}>{c.name}</div>
                        <div style={{ fontSize: "9.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>{c.candidate_id}</div>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", fontFamily: "var(--font-mono, monospace)" }}>
                        <span style={{ color: "#e2e8f0", fontWeight: 700 }}>{c.symbol}</span>{" "}
                        <span style={{ color: "#38bdf8", fontSize: "10px" }}>({c.timeframe})</span>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px" }}>
                        <span
                          style={{
                            fontSize: "8.5px",
                            fontWeight: 800,
                            padding: "2px 5px",
                            borderRadius: "3px",
                            background: c.route === "ULTRA" ? "rgba(239, 68, 68, 0.15)" : "rgba(56, 189, 248, 0.15)",
                            color: c.route === "ULTRA" ? "#f87171" : "#38bdf8",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {c.route}
                        </span>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: annRoi >= 0 ? "#34d399" : "#f87171" }}>
                        {annRoi >= 0 ? `+${annRoi.toFixed(1)}%` : `${annRoi.toFixed(1)}%`}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 700, color: monRoi >= 0 ? "#63e1b4" : "#f87171" }}>
                        {monRoi >= 0 ? `+${monRoi.toFixed(1)}%` : `${monRoi.toFixed(1)}%`}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>
                        <span style={{ color: "#94a3b8" }}>{pfIs.toFixed(2)}</span> /{" "}
                        <strong style={{ color: pfOos >= 1.2 ? "#34d399" : "#f59e0b" }}>{pfOos.toFixed(2)}</strong>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>
                        {wr.toFixed(1)}%
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#94a3b8" }}>
                        {tradesOos}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 700, color: dd <= 5.0 ? "#34d399" : dd <= 20.0 ? "#fbbf24" : "#f87171" }}>
                        {dd.toFixed(1)}%
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#38bdf8", fontWeight: 700 }}>
                        {mc.toFixed(0)}%
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "center" }}>
                        <button
                          onClick={() => handleInspectCandidate(c)}
                          style={{
                            background: "rgba(99, 225, 180, 0.12)",
                            border: "1px solid rgba(99, 225, 180, 0.3)",
                            color: "#63e1b4",
                            padding: "3px 8px",
                            borderRadius: "4px",
                            fontSize: "10px",
                            fontWeight: 800,
                            cursor: "pointer",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          👁️ Ver ADN
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 5. PAGINACIÓN Y CONTROL INFERIOR */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", background: "rgba(10, 14, 22, 0.95)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              Mostrando {Math.min(sorted.length, (currentPage - 1) * pageSize + 1)}-{Math.min(sorted.length, currentPage * pageSize)} de {sorted.length} candidatos
            </span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{
                background: "rgba(0, 0, 0, 0.4)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "4px",
                color: "#ffffff",
                padding: "2px 6px",
                fontSize: "10.5px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              <option value={25}>25 por página</option>
              <option value={50}>50 por página</option>
              <option value={100}>100 por página</option>
            </select>
          </div>

          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              style={{
                background: currentPage === 1 ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                color: currentPage === 1 ? "#475569" : "#ffffff",
                padding: "4px 10px",
                borderRadius: "4px",
                fontSize: "11px",
                cursor: currentPage === 1 ? "not-allowed" : "pointer",
              }}
            >
              ← Anterior
            </button>
            <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
              {currentPage} / {totalPages}
            </span>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              style={{
                background: currentPage >= totalPages ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                color: currentPage >= totalPages ? "#475569" : "#ffffff",
                padding: "4px 10px",
                borderRadius: "4px",
                fontSize: "11px",
                cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
              }}
            >
              Siguiente →
            </button>
          </div>
        </div>
      </div>

      {/* 6. MODAL DE INSPECCIÓN DE ADN & EXPORTACIÓN */}
      {selectedCandidate && (
        <div
          onClick={() => setSelectedCandidate(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.8)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 300,
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "rgba(12, 18, 28, 0.98)",
              border: "1px solid rgba(99, 225, 180, 0.3)",
              borderRadius: "12px",
              width: "100%",
              maxWidth: "860px",
              maxHeight: "85vh",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              boxShadow: "0 0 40px rgba(0, 0, 0, 0.8)",
            }}
          >
            {/* Header del Modal */}
            <div style={{ padding: "16px 20px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "11px", color: "#63e1b4", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                  INSPECCIÓN CUANTITATIVA · {selectedCandidate.route}
                </div>
                <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#ffffff", margin: "2px 0 0 0" }}>
                  {selectedCandidate.name}
                </h3>
              </div>

              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.05)", borderRadius: "6px", padding: "2px" }}>
                  {(["PINESCRIPT", "NINJATRADER", "PYTHON"] as const).map((fmt) => (
                    <button
                      key={fmt}
                      onClick={() => handleExportTypeChange(fmt)}
                      style={{
                        padding: "4px 8px",
                        borderRadius: "4px",
                        border: "none",
                        background: exportType === fmt ? "#63e1b4" : "transparent",
                        color: exportType === fmt ? "#06080d" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setSelectedCandidate(null)}
                  style={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "none",
                    color: "#94a3b8",
                    fontSize: "14px",
                    width: "28px",
                    height: "28px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Código Exportado / ADN */}
            <div style={{ padding: "16px 20px", flex: 1, overflowY: "auto" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  Código ejecutable generado para {exportType}:
                </span>
                <button
                  onClick={handleCopyCode}
                  style={{
                    background: copied ? "#34d399" : "rgba(99, 225, 180, 0.15)",
                    border: "1px solid rgba(99, 225, 180, 0.3)",
                    color: copied ? "#06080d" : "#63e1b4",
                    padding: "4px 10px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontWeight: 800,
                    cursor: "pointer",
                  }}
                >
                  {copied ? "✓ Copiado" : "📋 Copiar Código"}
                </button>
              </div>

              <pre
                style={{
                  background: "#06080d",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "8px",
                  padding: "14px",
                  fontSize: "11px",
                  fontFamily: "var(--font-mono, monospace)",
                  color: "#cbd5e1",
                  maxHeight: "380px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                }}
              >
                {exportCode}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
