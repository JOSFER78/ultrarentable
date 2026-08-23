"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";

interface CandidateItem {
  candidate_id: string;
  name: string;
  symbol: string;
  clean_symbol: string;
  timeframe: string;
  route: string;
  status: string;
  tier: string;
  gates_passed_count: number;
  profit_factor: number;
  max_dd_pct: number;
  net_profit_usd: number;
}

interface MetaStrategyRow {
  portfolio_id: string;
  name: string;
  target_route: string;
  base_capital_usd: number;
  current_equity_usd: number;
  symbols: string[];
  components_count: number;
  total_trades: number;
  win_rate_pct: number;
  profit_factor: number;
  annualized_roi_pct: number;
  max_drawdown_pct: number;
  sharpe_ratio: number;
  diversification_ratio: number;
  avg_cross_correlation: number;
  consensus_score: number;
  consensus_verdict: string;
  is_approved: boolean;
  tier: string;
  canonical_hash: string;
  status: string;
  created_at: string | null;
  details: any;
}

interface DaemonStatus {
  is_running: boolean;
  current_generation: number;
  cycles_completed: number;
  total_evaluated?: number;
  total_approved?: number;
  total_ensembles_evaluated?: number;
  total_ensembles_approved?: number;
  current_evaluating_name: string;
  current_route: string;
  last_evaluation_time: string | null;
  last_error: string | null;
  timestamp_utc: string;
}

export default function PortfolioMasterExcelPage() {
  // ── 1. FILTROS PRINCIPALES (HOJA DE CÁLCULO EXCEL) ──
  const [routeFilter, setRouteFilter] = useState<"ALL" | "FONDEO" | "ULTRA">("ALL");
  const [tierFilter, setTierFilter] = useState<"ALL" | "TIER_1" | "TIER_2" | "TIER_3">("ALL");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "CERTIFIED" | "INCUBATING">("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sortBy, setSortBy] = useState<string>("sharpe");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // ── 2. DATOS DE LA TABLA (100% SQLITE WAL) ──
  const [metaStrategies, setMetaStrategies] = useState<MetaStrategyRow[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [daemonStatus, setDaemonStatus] = useState<DaemonStatus | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<MetaStrategyRow | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [drawerTab, setDrawerTab] = useState<"EQUITY" | "CORRELATION" | "ERC_WEIGHTS" | "DEBATE" | "GOVERNANCE">("EQUITY");
  const [loadingTable, setLoadingTable] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);

  // ── 3. LABORATORIO MANUAL ASISTIDO (SUBSECCIÓN INFERIOR) ──
  const [showStudioLab, setShowStudioLab] = useState<boolean>(false);
  const [studioRoute, setStudioRoute] = useState<"FONDEO" | "ULTRA">("FONDEO");
  const [candidatesGrouped, setCandidatesGrouped] = useState<Record<string, CandidateItem[]>>({});
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [synthesizing, setSynthesizing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Status del Demonio Autónomo 24/7
  const fetchDaemonStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v2/portfolio/daemon/status", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setDaemonStatus(data);
      }
    } catch (e) {
      console.error("Error cargando status del demonio:", e);
    }
  }, []);

  // Carga de la Tabla Canónica desde SQLite WAL (Soft Refetch: Zero-Flicker)
  const fetchMetaStrategiesTable = useCallback(async (isManual: boolean = false) => {
    try {
      if (isManual) {
        setIsRefreshing(true);
      } else {
        setLoadingTable((prev) => prev);
      }

      const params = new URLSearchParams({
        route: routeFilter,
        status: statusFilter,
        search: searchQuery,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: "100",
      });

      const res = await fetch(`/api/v2/portfolio/meta-strategies/table?${params.toString()}`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        const list = data.meta_strategies || [];
        setMetaStrategies(list);
        setTotalCount(data.total || list.length);
        setLastSyncTime(new Date());

        // Solo preseleccionar si no hay ninguna seleccionada
        setSelectedStrategy((prev) => prev || (list.length > 0 ? list[0] : null));
      }
    } catch (e) {
      console.error("Error cargando tabla de meta-estrategias:", e);
    } finally {
      setLoadingTable(false);
      setIsRefreshing(false);
    }
  }, [routeFilter, statusFilter, searchQuery, sortBy, sortOrder]);

  // Carga de Candidatos para el Laboratorio Opcional
  const fetchEligibleCandidates = useCallback(async () => {
    try {
      const res = await fetch(`/api/v2/portfolio/eligible-candidates?route=${studioRoute}&min_gates=7`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setCandidatesGrouped(data.grouped_by_asset || {});
      }
    } catch (e) {
      console.error("Error cargando candidatos de estudio:", e);
    }
  }, [studioRoute]);

  useEffect(() => {
    fetchDaemonStatus();
    fetchMetaStrategiesTable();

    const interval = setInterval(() => {
      fetchDaemonStatus();
      fetchMetaStrategiesTable();
    }, 8000);

    return () => clearInterval(interval);
  }, [fetchDaemonStatus, fetchMetaStrategiesTable]);

  useEffect(() => {
    if (showStudioLab) {
      fetchEligibleCandidates();
    }
  }, [showStudioLab, studioRoute, fetchEligibleCandidates]);

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
  };

  const handleOpenDrawer = (strategy: MetaStrategyRow) => {
    setSelectedStrategy(strategy);
    setIsDrawerOpen(true);
  };

  const copyHash = (hash: string) => {
    if (hash) {
      navigator.clipboard.writeText(hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

  const handleSynthesizeManual = async () => {
    if (selectedCandidateIds.length < 2) {
      setErrorMessage("Debes seleccionar al menos 2 estrategias en activos distintos.");
      return;
    }

    setSynthesizing(true);
    setErrorMessage(null);

    try {
      const res = await fetch("/api/v2/portfolio/synthesize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: selectedCandidateIds,
          route: studioRoute,
          total_capital_usd: studioRoute === "ULTRA" ? selectedCandidateIds.length * 1000.0 : 50000.0,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Error sintetizando Meta-Estrategia");
      }

      fetchMetaStrategiesTable();
      setShowStudioLab(false);
    } catch (e: any) {
      setErrorMessage(e.message || "Error en síntesis");
    } finally {
      setSynthesizing(false);
    }
  };

  // Curva de equidad SVG para el drawer
  const equityPoints = useMemo(() => {
    const raw = selectedStrategy?.details?.combined_equity_curve;
    if (Array.isArray(raw) && raw.length > 1) return raw;
    const base = selectedStrategy?.base_capital_usd || 50000;
    return [base];
  }, [selectedStrategy]);

  const minEquity = Math.min(...equityPoints) * 0.98;
  const maxEquity = Math.max(...equityPoints) * 1.02;
  const rangeEquity = maxEquity - minEquity || 1;
  const svgWidth = 700;
  const svgHeight = 200;
  const paddingX = 35;
  const paddingY = 15;

  const getSvgCoordinates = (val: number, idx: number, total: number) => {
    const x = paddingX + (idx / Math.max(1, total - 1)) * (svgWidth - paddingX * 2);
    const y = svgHeight - paddingY - ((val - minEquity) / rangeEquity) * (svgHeight - paddingY * 2);
    return { x, y };
  };

  const polylinePoints = equityPoints
    .map((val, idx) => {
      const { x, y } = getSvgCoordinates(val, idx, equityPoints.length);
      return `${x},${y}`;
    })
    .join(" ");

  const areaPoints = `${getSvgCoordinates(equityPoints[0], 0, equityPoints.length).x},${
    svgHeight - paddingY
  } ${polylinePoints} ${
    getSvgCoordinates(equityPoints[equityPoints.length - 1], equityPoints.length - 1, equityPoints.length).x
  },${svgHeight - paddingY}`;

  return (
    <div style={{ padding: "16px 24px", maxWidth: "1720px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "16px", color: "#f8fafc" }}>
      
      {/* ── 1. HOJA DE CÁLCULO EXCEL: TABLA DE META-ESTRATEGIAS (LO PRIMERO EN PANTALLA) ── */}
      <div
        style={{
          background: "#080e18",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          boxShadow: "0 8px 30px rgba(0, 0, 0, 0.5)",
          overflow: "hidden",
        }}
      >
        {/* BARRA SUPERIOR ESTILO TOOLBAR DE EXCEL */}
        <div
          style={{
            background: "#0c1524",
            borderBottom: "1px solid #1e293b",
            padding: "10px 16px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          {/* SHEET TABS: SELECTOR DE RUTA INSTANTÁNEO */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              📊 HOJA DE CÁLCULO:
            </span>
            <div style={{ display: "flex", gap: "2px", background: "#030712", padding: "2px", borderRadius: "6px", border: "1px solid #1e293b" }}>
              <button
                onClick={() => setRouteFilter("ALL")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "4px",
                  fontSize: "11.5px",
                  fontWeight: 800,
                  cursor: "pointer",
                  background: routeFilter === "ALL" ? "#1e293b" : "transparent",
                  color: routeFilter === "ALL" ? "#c084fc" : "#94a3b8",
                  border: routeFilter === "ALL" ? "1px solid #a855f7" : "none",
                }}
              >
                🌐 TODAS ({totalCount})
              </button>
              <button
                onClick={() => setRouteFilter("FONDEO")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "4px",
                  fontSize: "11.5px",
                  fontWeight: 800,
                  cursor: "pointer",
                  background: routeFilter === "FONDEO" ? "rgba(56, 189, 248, 0.2)" : "transparent",
                  color: routeFilter === "FONDEO" ? "#38bdf8" : "#94a3b8",
                  border: routeFilter === "FONDEO" ? "1px solid #38bdf8" : "none",
                }}
              >
                🏛️ FONDEO (CME, FX & Cripto · DD &le; 4.0%)
              </button>
              <button
                onClick={() => setRouteFilter("ULTRA")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "4px",
                  fontSize: "11.5px",
                  fontWeight: 800,
                  cursor: "pointer",
                  background: routeFilter === "ULTRA" ? "rgba(99, 225, 180, 0.2)" : "transparent",
                  color: routeFilter === "ULTRA" ? "#63e1b4" : "#94a3b8",
                  border: routeFilter === "ULTRA" ? "1px solid #63e1b4" : "none",
                }}
              >
                ⚡ ULTRA (22 Activos Globales · Margen 1R)
              </button>
            </div>
          </div>

          {/* TELEMETRÍA VIVA 24/7, BOTÓN MANUAL DE REFRESCO & BUSCADOR ESTILO EXCEL */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(0,0,0,0.4)", padding: "4px 10px", borderRadius: "5px", border: "1px solid rgba(99, 225, 180, 0.3)", fontSize: "11px" }}>
              <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#63e1b4", boxShadow: "0 0 6px #63e1b4" }} />
              <span style={{ fontWeight: 800, color: "#ffffff" }}>24/7 ACTIVO</span>
              <span style={{ color: "#c084fc", fontWeight: 800 }}>Gen #{daemonStatus?.current_generation || 1}</span>
            </div>

            {/* BOTÓN MANUAL DE REFRESCO (SOFT SYNC) */}
            <button
              onClick={() => fetchMetaStrategiesTable(true)}
              disabled={isRefreshing}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "5px",
                background: "rgba(56, 189, 248, 0.15)",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                color: "#38bdf8",
                fontSize: "11.5px",
                fontWeight: 800,
                cursor: isRefreshing ? "not-allowed" : "pointer",
                transition: "all 0.15s ease",
              }}
              title="Actualizar datos de SQLite WAL en segundo plano"
            >
              <span style={{ display: "inline-block", animation: isRefreshing ? "spin 1s linear infinite" : "none" }}>🔄</span>
              <span>{isRefreshing ? "Sincronizando..." : "Actualizar"}</span>
            </button>

            {lastSyncTime && (
              <span style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                Última sync: {lastSyncTime.toLocaleTimeString()}
              </span>
            )}

            {/* BUSCADOR DE CELDAS */}
            <input
              type="text"
              placeholder="🔍 Filtrar por activo (NQ, BTC, GC, EURUSD)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: "6px 12px",
                borderRadius: "5px",
                background: "#030712",
                border: "1px solid #1e293b",
                color: "#f8fafc",
                fontSize: "11.5px",
                outline: "none",
                width: "240px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            />

            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              Filas: <b style={{ color: "#38bdf8" }}>{metaStrategies.length}</b> de {totalCount}
            </span>
          </div>
        </div>

        {/* DATA GRID EXCEL CANÓNICO */}
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11.5px", textAlign: "left", fontFamily: "var(--font-mono, monospace)" }}>
            <thead>
              <tr style={{ background: "#0a101d", borderBottom: "2px solid #1e293b", color: "#94a3b8" }}>
                <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800 }}>ID Meta-Estrategia</th>
                <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800 }}>Canasta de Activos (Ortogonales)</th>
                <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800 }}>Ruta</th>
                <th
                  onClick={() => handleSort("trades")}
                  style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right", cursor: "pointer" }}
                >
                  Trades {sortBy === "trades" && (sortOrder === "desc" ? "↓" : "↑")}
                </th>
                <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right" }}>Win Rate</th>
                <th
                  onClick={() => handleSort("pf")}
                  style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right", cursor: "pointer" }}
                >
                  PF {sortBy === "pf" && (sortOrder === "desc" ? "↓" : "↑")}
                </th>
                <th
                  onClick={() => handleSort("roi")}
                  style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right", cursor: "pointer" }}
                >
                  ROI Anual {sortBy === "roi" && (sortOrder === "desc" ? "↓" : "↑")}
                </th>
                <th
                  onClick={() => handleSort("dd")}
                  style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right", cursor: "pointer" }}
                >
                  Max DD {sortBy === "dd" && (sortOrder === "desc" ? "↓" : "↑")}
                </th>
                <th
                  onClick={() => handleSort("sharpe")}
                  style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right", cursor: "pointer" }}
                >
                  Sharpe {sortBy === "sharpe" && (sortOrder === "desc" ? "↓" : "↑")}
                </th>
                <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right" }}>Div. Ratio (DR)</th>
                <th
                  onClick={() => handleSort("consensus")}
                  style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "center", cursor: "pointer" }}
                >
                  Consenso IA {sortBy === "consensus" && (sortOrder === "desc" ? "↓" : "↑")}
                </th>
                <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "center" }}>Estado / Tier</th>
                <th style={{ padding: "10px 12px", fontWeight: 800, textAlign: "center" }}>Acción</th>
              </tr>
            </thead>
            <tbody>
              {loadingTable && metaStrategies.length === 0 ? (
                <tr>
                  <td colSpan={13} style={{ padding: "28px", textAlign: "center", color: "#94a3b8" }}>
                    ⏳ Consultando registros físicos desde SQLite WAL...
                  </td>
                </tr>
              ) : metaStrategies.length === 0 ? (
                <tr>
                  <td colSpan={13} style={{ padding: "28px", textAlign: "center", color: "#64748b" }}>
                    No se encontraron Meta-Estrategias con el filtro seleccionado.
                  </td>
                </tr>
              ) : (
                metaStrategies.map((row, idx) => {
                  const isSelected = selectedStrategy?.portfolio_id === row.portfolio_id;
                  const isFondeo = row.target_route.includes("FONDEO");

                  return (
                    <tr
                      key={row.portfolio_id}
                      onClick={() => handleOpenDrawer(row)}
                      style={{
                        borderBottom: "1px solid #1e293b",
                        background: isSelected
                          ? "rgba(168, 85, 247, 0.12)"
                          : idx % 2 === 0
                          ? "rgba(12, 19, 32, 0.5)"
                          : "rgba(8, 14, 24, 0.5)",
                        cursor: "pointer",
                        transition: "background 0.1s ease",
                      }}
                    >
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", color: "#c084fc", fontWeight: 800 }}>
                        {row.portfolio_id}
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b" }}>
                        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                          {row.symbols?.map((sym) => (
                            <span
                              key={sym}
                              style={{
                                fontSize: "10px",
                                fontWeight: 800,
                                padding: "1px 5px",
                                borderRadius: "3px",
                                background: isFondeo ? "rgba(56, 189, 248, 0.15)" : "rgba(99, 225, 180, 0.15)",
                                color: isFondeo ? "#38bdf8" : "#63e1b4",
                                border: `1px solid ${isFondeo ? "rgba(56, 189, 248, 0.3)" : "rgba(99, 225, 180, 0.3)"}`,
                              }}
                            >
                              {sym}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b" }}>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 900,
                            padding: "2px 6px",
                            borderRadius: "3px",
                            background: isFondeo ? "rgba(56, 189, 248, 0.15)" : "rgba(99, 225, 180, 0.15)",
                            color: isFondeo ? "#38bdf8" : "#63e1b4",
                          }}
                        >
                          {isFondeo ? "FONDEO" : "ULTRA"}
                        </span>
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", color: "#f8fafc", fontWeight: 700 }}>
                        {row.total_trades}
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", color: "#cbd5e1" }}>
                        {row.win_rate_pct?.toFixed(1)}%
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", fontWeight: 800, color: "#63e1b4" }}>
                        {row.profit_factor?.toFixed(2)}
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", fontWeight: 900, color: "#63e1b4" }}>
                        +{row.annualized_roi_pct?.toFixed(1)}%
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", fontWeight: 800, color: row.max_drawdown_pct <= 4.0 ? "#63e1b4" : "#38bdf8" }}>
                        {row.max_drawdown_pct?.toFixed(2)}%
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", fontWeight: 900, color: "#c084fc" }}>
                        {row.sharpe_ratio?.toFixed(2)}
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", fontWeight: 800, color: "#facc15" }}>
                        {row.diversification_ratio?.toFixed(2)}x
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "center" }}>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 900,
                            padding: "1px 5px",
                            borderRadius: "3px",
                            background: row.consensus_score >= 85 ? "rgba(99, 225, 180, 0.15)" : "rgba(250, 204, 21, 0.15)",
                            color: row.consensus_score >= 85 ? "#63e1b4" : "#facc15",
                          }}
                        >
                          {row.consensus_score?.toFixed(1)}/100
                        </span>
                      </td>
                      <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "center" }}>
                        <span
                          style={{
                            fontSize: "9.5px",
                            fontWeight: 800,
                            padding: "1px 5px",
                            borderRadius: "3px",
                            background: row.is_approved ? "rgba(99, 225, 180, 0.15)" : "rgba(244, 63, 94, 0.15)",
                            color: row.is_approved ? "#63e1b4" : "#f43f5e",
                            border: `1px solid ${row.is_approved ? "rgba(99, 225, 180, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
                          }}
                        >
                          {row.tier}
                        </span>
                      </td>
                      <td style={{ padding: "8px 12px", textAlign: "center" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenDrawer(row);
                          }}
                          style={{
                            padding: "3px 8px",
                            borderRadius: "4px",
                            background: "rgba(168, 85, 247, 0.2)",
                            color: "#c084fc",
                            border: "1px solid rgba(168, 85, 247, 0.4)",
                            fontSize: "10px",
                            fontWeight: 800,
                            cursor: "pointer",
                          }}
                        >
                          👁️ Ver Detalle
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

      {/* ── 2. SECCIÓN SECUNDARIA INFERIOR: LABORATORIO DE SÍNTESIS MANUAL ── */}
      <div
        style={{
          background: "#080e18",
          border: "1px solid #1e293b",
          borderRadius: "10px",
          padding: "14px 18px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h3 style={{ fontSize: "13px", fontWeight: 800, color: "#ffffff", margin: 0, display: "flex", alignItems: "center", gap: "6px" }}>
              <span>🎯</span> LABORATORIO DE SÍNTESIS MANUAL & DEBATE ASISTIDO (OPCIONAL)
            </h3>
            <p style={{ fontSize: "11px", color: "#94a3b8", margin: "2px 0 0 0" }}>
              Herramienta secundaria para crear canastas personalizadas y lanzar el comité de 5 agentes sobre combinaciones ad-hoc.
            </p>
          </div>

          <button
            onClick={() => setShowStudioLab(!showStudioLab)}
            style={{
              padding: "5px 12px",
              borderRadius: "5px",
              background: showStudioLab ? "rgba(168, 85, 247, 0.2)" : "rgba(255, 255, 255, 0.05)",
              color: showStudioLab ? "#c084fc" : "#cbd5e1",
              border: showStudioLab ? "1px solid #a855f7" : "1px solid #1e293b",
              fontSize: "10.5px",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            {showStudioLab ? "▲ Ocultar Laboratorio" : "▼ Abrir Laboratorio"}
          </button>
        </div>

        {errorMessage && (
          <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.3)", borderRadius: "5px", padding: "6px 10px", color: "#f43f5e", fontSize: "11px", fontWeight: 700 }}>
            ⚠️ {errorMessage}
          </div>
        )}

        {showStudioLab && (
          <div style={{ display: "flex", flexDirection: "column", gap: "14px", paddingTop: "10px", borderTop: "1px solid #1e293b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
              <div style={{ display: "flex", gap: "4px" }}>
                <button
                  onClick={() => setStudioRoute("FONDEO")}
                  style={{
                    padding: "4px 10px",
                    borderRadius: "4px",
                    fontSize: "10.5px",
                    fontWeight: 800,
                    cursor: "pointer",
                    background: studioRoute === "FONDEO" ? "rgba(56, 189, 248, 0.2)" : "transparent",
                    color: studioRoute === "FONDEO" ? "#38bdf8" : "#94a3b8",
                    border: studioRoute === "FONDEO" ? "1px solid #38bdf8" : "none",
                  }}
                >
                  🏛️ FONDEO (CME/FX)
                </button>
                <button
                  onClick={() => setStudioRoute("ULTRA")}
                  style={{
                    padding: "4px 10px",
                    borderRadius: "4px",
                    fontSize: "10.5px",
                    fontWeight: 800,
                    cursor: "pointer",
                    background: studioRoute === "ULTRA" ? "rgba(99, 225, 180, 0.2)" : "transparent",
                    color: studioRoute === "ULTRA" ? "#63e1b4" : "#94a3b8",
                    border: studioRoute === "ULTRA" ? "1px solid #63e1b4" : "none",
                  }}
                >
                  ⚡ ULTRA (Cripto)
                </button>
              </div>

              <button
                onClick={handleSynthesizeManual}
                disabled={synthesizing || selectedCandidateIds.length < 2}
                style={{
                  padding: "6px 14px",
                  borderRadius: "5px",
                  background: selectedCandidateIds.length >= 2 ? "linear-gradient(135deg, #a855f7 0%, #6366f1 100%)" : "rgba(255, 255, 255, 0.05)",
                  color: selectedCandidateIds.length >= 2 ? "#ffffff" : "#64748b",
                  fontWeight: 900,
                  fontSize: "11px",
                  cursor: selectedCandidateIds.length >= 2 ? "pointer" : "not-allowed",
                  border: "none",
                }}
              >
                {synthesizing ? "⏳ SINTETIZANDO..." : `⚡ SINTETIZAR (${selectedCandidateIds.length} ACTIVOS)`}
              </button>
            </div>

            {/* GRILLA DE SELECCIÓN POR ACTIVO */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
              {Object.entries(candidatesGrouped).map(([assetSymbol, strats]) => {
                const selectedInAsset = strats.find((s) => selectedCandidateIds.includes(s.candidate_id));

                return (
                  <div
                    key={assetSymbol}
                    style={{
                      background: selectedInAsset ? "rgba(168, 85, 247, 0.08)" : "#0c1524",
                      border: selectedInAsset ? "1px solid rgba(168, 85, 247, 0.4)" : "1px solid #1e293b",
                      borderRadius: "6px",
                      padding: "8px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "5px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontSize: "11.5px", fontWeight: 900, color: "#f8fafc" }}>📊 {assetSymbol}</span>
                      <span style={{ fontSize: "9px", fontWeight: 800, padding: "1px 4px", borderRadius: "3px", background: selectedInAsset ? "#a855f7" : "#1e293b", color: selectedInAsset ? "#fff" : "#94a3b8" }}>
                        {selectedInAsset ? "✓ SELECCIONADO" : `${strats.length} CANDIDATAS`}
                      </span>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "3px", maxHeight: "120px", overflowY: "auto" }}>
                      {strats.map((c) => {
                        const isChecked = selectedCandidateIds.includes(c.candidate_id);
                        return (
                          <div
                            key={c.candidate_id}
                            onClick={() => {
                              if (isChecked) {
                                setSelectedCandidateIds(selectedCandidateIds.filter((id) => id !== c.candidate_id));
                              } else {
                                const filtered = selectedCandidateIds.filter((id) => !strats.some((s) => s.candidate_id === id));
                                setSelectedCandidateIds([...filtered, c.candidate_id]);
                              }
                            }}
                            style={{
                              padding: "4px 6px",
                              borderRadius: "3px",
                              background: isChecked ? "rgba(168, 85, 247, 0.2)" : "#030712",
                              border: isChecked ? "1px solid #a855f7" : "1px solid #1e293b",
                              cursor: "pointer",
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              fontSize: "10px",
                            }}
                          >
                            <span style={{ fontWeight: 800, color: isChecked ? "#ffffff" : "#cbd5e1" }}>{c.name} ({c.timeframe})</span>
                            <span style={{ color: "#63e1b4", fontWeight: 800 }}>PF {c.profit_factor.toFixed(2)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ── 3. DRAWER MODAL DE INSPECCIÓN FORENSE ── */}
      {isDrawerOpen && selectedStrategy && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(3, 7, 18, 0.75)",
            backdropFilter: "blur(8px)",
            zIndex: 100,
            display: "flex",
            justifyContent: "flex-end",
          }}
          onClick={() => setIsDrawerOpen(false)}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "1000px",
              height: "100vh",
              backgroundColor: "#080e18",
              borderLeft: "1px solid #1e293b",
              boxShadow: "-12px 0 40px rgba(0, 0, 0, 0.7)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              color: "#f8fafc",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* CABECERA DRAWER */}
            <div
              style={{
                padding: "16px 20px",
                background: "#0c1524",
                borderBottom: "1px solid #1e293b",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "16px",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "20px" }}>🧬</span>
                  <h2 style={{ fontSize: "15px", fontWeight: 900, color: "#ffffff", margin: 0 }}>
                    {selectedStrategy.name}
                  </h2>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 900,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: selectedStrategy.target_route === "ULTRA" ? "rgba(99, 225, 180, 0.15)" : "rgba(56, 189, 248, 0.15)",
                      color: selectedStrategy.target_route === "ULTRA" ? "#63e1b4" : "#38bdf8",
                    }}
                  >
                    {selectedStrategy.target_route} · {selectedStrategy.components_count} ACTIVOS
                  </span>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 900,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: selectedStrategy.is_approved ? "rgba(99, 225, 180, 0.2)" : "rgba(244, 63, 94, 0.2)",
                      color: selectedStrategy.is_approved ? "#63e1b4" : "#f43f5e",
                    }}
                  >
                    {selectedStrategy.consensus_verdict}
                  </span>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "11px", color: "#94a3b8" }}>
                  <span>ID: <code style={{ color: "#c084fc", fontWeight: 700 }}>{selectedStrategy.portfolio_id}</code></span>
                  <span>•</span>
                  <span>Capital: <b style={{ color: "#ffffff" }}>${selectedStrategy.base_capital_usd?.toLocaleString()}</b></span>
                  <span>•</span>
                  <span>Consenso IA: <b style={{ color: "#facc15" }}>{selectedStrategy.consensus_score?.toFixed(1)}/100</b></span>
                  <span>•</span>
                  <button
                    onClick={() => copyHash(selectedStrategy.canonical_hash)}
                    title="Copiar Hash SHA-256 de Procedencia"
                    style={{
                      background: "#030712",
                      border: "1px solid #1e293b",
                      borderRadius: "4px",
                      padding: "1px 5px",
                      color: "#cbd5e1",
                      fontSize: "10px",
                      fontFamily: "var(--font-mono, monospace)",
                      cursor: "pointer",
                    }}
                  >
                    🔒 SHA-256: {selectedStrategy.canonical_hash ? `${selectedStrategy.canonical_hash.substring(0, 10)}...` : "VERIFIED"} {copiedHash ? "✓" : "📋"}
                  </button>
                </div>
              </div>

              <button
                onClick={() => setIsDrawerOpen(false)}
                style={{
                  width: "26px",
                  height: "26px",
                  borderRadius: "5px",
                  background: "#030712",
                  border: "1px solid #1e293b",
                  color: "#cbd5e1",
                  fontSize: "13px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                ✕
              </button>
            </div>

            {/* PESTAÑAS DEL DRAWER */}
            <div style={{ display: "flex", background: "#060b13", borderBottom: "1px solid #1e293b", padding: "0 18px", gap: "4px", overflowX: "auto" }}>
              {[
                { id: "EQUITY", label: "📈 Curva de Equidad" },
                { id: "CORRELATION", label: "📊 Matriz Correlación" },
                { id: "ERC_WEIGHTS", label: "⚖️ Pesos ERC" },
                { id: "DEBATE", label: "💬 Debate 5 Agentes IA" },
                { id: "GOVERNANCE", label: "📜 11 Meta-Gates & JSON" },
              ].map((tab) => {
                const isActive = drawerTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setDrawerTab(tab.id as any)}
                    style={{
                      padding: "9px 12px",
                      background: "transparent",
                      border: "none",
                      borderBottom: isActive ? "2px solid #a855f7" : "2px solid transparent",
                      color: isActive ? "#ffffff" : "#94a3b8",
                      fontWeight: isActive ? 800 : 600,
                      fontSize: "11px",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* CONTENIDO DEL DRAWER */}
            <div style={{ flex: 1, overflowY: "auto", padding: "18px 20px", display: "flex", flexDirection: "column", gap: "14px" }}>
              {drawerTab === "EQUITY" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "8px" }}>
                    <div style={{ background: "#0c1524", padding: "8px 12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
                      <div style={{ fontSize: "9.5px", color: "#94a3b8" }}>ROI ANUAL</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#63e1b4" }}>+{selectedStrategy.annualized_roi_pct.toFixed(1)}%</div>
                    </div>
                    <div style={{ background: "#0c1524", padding: "8px 12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
                      <div style={{ fontSize: "9.5px", color: "#94a3b8" }}>MAX DD COMPRIMIDO</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#38bdf8" }}>{selectedStrategy.max_drawdown_pct.toFixed(2)}%</div>
                    </div>
                    <div style={{ background: "#0c1524", padding: "8px 12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
                      <div style={{ fontSize: "9.5px", color: "#94a3b8" }}>SHARPE RATIO</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#c084fc" }}>{selectedStrategy.sharpe_ratio.toFixed(2)}</div>
                    </div>
                    <div style={{ background: "#0c1524", padding: "8px 12px", borderRadius: "6px", border: "1px solid #1e293b" }}>
                      <div style={{ fontSize: "9.5px", color: "#94a3b8" }}>DIVERSIFICATION RATIO</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#facc15" }}>{selectedStrategy.diversification_ratio.toFixed(2)}x</div>
                    </div>
                  </div>

                  {/* SVG CURVA DE EQUIDAD */}
                  <div style={{ background: "#060b13", border: "1px solid #1e293b", borderRadius: "8px", padding: "14px" }}>
                    <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#ffffff", marginBottom: "8px" }}>
                      📈 TRAYECTORIA DE CAPITAL COMBINADO ($USD)
                    </div>
                    <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: "100%", height: "auto" }}>
                      <defs>
                        <linearGradient id="eqGradModal" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#63e1b4" stopOpacity="0.35" />
                          <stop offset="100%" stopColor="#63e1b4" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>
                      <polygon points={areaPoints} fill="url(#eqGradModal)" />
                      <polyline points={polylinePoints} fill="none" stroke="#63e1b4" strokeWidth="2" />
                    </svg>
                  </div>
                </div>
              )}

              {drawerTab === "CORRELATION" && (
                <div style={{ background: "#0c1524", borderRadius: "6px", padding: "12px", border: "1px solid #1e293b" }}>
                  <h4 style={{ margin: "0 0 8px 0", fontSize: "11.5px", fontWeight: 800, color: "#ffffff" }}>
                    🌡️ MATRIZ DE CORRELACIÓN CRUZADA EMPÍRICA
                  </h4>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "10.5px", textAlign: "center" }}>
                      <thead>
                        <tr>
                          <th style={{ padding: "4px", color: "#94a3b8", textAlign: "left" }}>Activo</th>
                          {selectedStrategy.details?.components?.map((c: any) => (
                            <th key={c.strategy_id} style={{ padding: "4px", color: "#f8fafc" }}>{c.symbol}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {selectedStrategy.details?.components?.map((rowC: any) => (
                          <tr key={rowC.strategy_id} style={{ borderTop: "1px solid #1e293b" }}>
                            <td style={{ padding: "5px 4px", textAlign: "left", fontWeight: 800, color: "#cbd5e1" }}>{rowC.symbol}</td>
                            {selectedStrategy.details?.components?.map((colC: any) => {
                              const val = selectedStrategy.details?.correlation_matrix?.[rowC.strategy_id]?.[colC.strategy_id] ?? (rowC.strategy_id === colC.strategy_id ? 1.0 : 0.2);
                              const isSelf = rowC.strategy_id === colC.strategy_id;
                              const bg = isSelf ? "#1e293b" : val < 0.25 ? "rgba(99, 225, 180, 0.15)" : val < 0.5 ? "rgba(250, 204, 21, 0.15)" : "rgba(244, 63, 94, 0.15)";
                              const txt = isSelf ? "#94a3b8" : val < 0.25 ? "#63e1b4" : val < 0.5 ? "#facc15" : "#f43f5e";
                              return (
                                <td key={colC.strategy_id} style={{ padding: "5px 4px", background: bg, color: txt, fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                                  {val.toFixed(2)}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {drawerTab === "ERC_WEIGHTS" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {selectedStrategy.details?.components?.map((comp: any) => (
                    <div key={comp.strategy_id} style={{ background: "#0c1524", border: "1px solid #1e293b", borderRadius: "6px", padding: "10px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                        <span style={{ fontWeight: 800, color: "#ffffff", fontSize: "11.5px" }}>{comp.symbol} ({comp.strategy_id})</span>
                        <span style={{ color: "#38bdf8", fontWeight: 900, fontSize: "11.5px" }}>{comp.weight_pct}%</span>
                      </div>
                      <div style={{ height: "4px", width: "100%", background: "#1e293b", borderRadius: "2px", overflow: "hidden", marginBottom: "5px" }}>
                        <div style={{ height: "100%", width: `${comp.weight_pct}%`, background: "linear-gradient(90deg, #38bdf8, #a855f7)" }} />
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#94a3b8" }}>
                        <span>Rol: <b style={{ color: "#c084fc" }}>{comp.role_in_ensemble}</b></span>
                        <span>DD: <b>{comp.individual_max_dd_pct}%</b> · PF: <b>{comp.individual_profit_factor}</b> · Trades: <b>{comp.trades_count}</b></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {drawerTab === "DEBATE" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {selectedStrategy.details?.agents_debate?.map((agent: any, idx: number) => (
                    <div key={agent.agent_id || idx} style={{ background: "#0c1524", border: `1px solid ${agent.color}44`, borderRadius: "6px", padding: "10px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                        <div>
                          <div style={{ fontWeight: 900, color: agent.color, fontSize: "11.5px" }}>{agent.agent_name}</div>
                          <div style={{ fontSize: "9.5px", color: "#94a3b8" }}>{agent.role}</div>
                        </div>
                        <span style={{ fontSize: "9px", fontWeight: 900, padding: "2px 5px", borderRadius: "3px", background: agent.vote === "APROBADO" ? "rgba(99,225,180,0.2)" : "rgba(244,63,94,0.2)", color: agent.vote === "APROBADO" ? "#63e1b4" : "#f43f5e" }}>
                          {agent.vote}
                        </span>
                      </div>
                      <div style={{ fontSize: "10.5px", color: "#cbd5e1", fontStyle: "italic", borderLeft: `2px solid ${agent.color}`, paddingLeft: "6px", marginBottom: "3px" }}>
                        "{agent.thesis}"
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "14px", fontSize: "10px", color: "#94a3b8", display: "flex", flexDirection: "column", gap: "1px" }}>
                        {agent.findings?.map((f: string, fIdx: number) => (
                          <li key={fIdx}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}

              {drawerTab === "GOVERNANCE" && (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div style={{ background: "#0c1524", borderRadius: "6px", padding: "8px", border: "1px solid #1e293b" }}>
                    <div style={{ fontSize: "10.5px", color: "#94a3b8", marginBottom: "2px" }}>HASH CANÓNICO SHA-256 INMUTABLE:</div>
                    <code style={{ fontSize: "10px", color: "#c084fc", wordBreak: "break-all" }}>{selectedStrategy.canonical_hash}</code>
                  </div>
                  <pre style={{ maxHeight: "220px", overflowY: "auto", background: "#030712", padding: "8px", borderRadius: "5px", fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", border: "1px solid #1e293b" }}>
                    {JSON.stringify(selectedStrategy.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
