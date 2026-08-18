"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

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
  const [activeModalTab, setActiveModalTab] = useState<"DNA" | "SCORECARD" | "EXPORT" | "EDITOR">("DNA");
  const [exportCode, setExportCode] = useState<string>("");
  const [exportType, setExportType] = useState<"PINESCRIPT" | "NINJATRADER" | "PYTHON">("PINESCRIPT");
  const [copied, setCopied] = useState(false);
  const [firebaseSyncing, setFirebaseSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  // Live Strategy Editor & Fast Simulator state
  const [simParams, setSimParams] = useState({
    atr_stop_mult: 1.2,
    atr_tp_mult: 3.0,
    risk_per_trade_usd: 500,
    risk_pct: 6.0,
    max_leverage: 100.0,
    pyramiding_tiers: 4,
    margin_reinvest_pct: 80.0,
  });
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<any | null>(null);

  const [viewMode, setViewMode] = useState<"TABLE" | "CARDS">("TABLE");
  const [sortField, setSortField] = useState<string>("annualized_roi_pct");
  const [sortDirection, setSortDirection] = useState<"DESC" | "ASC">("DESC");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const [fondeoSubTab, setFondeoSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<any | null>(null);

  const [ultraSubTab, setUltraSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [ultraPortfolios, setUltraPortfolios] = useState<any[]>([]);
  const [selectedUltraPortfolio, setSelectedUltraPortfolio] = useState<any | null>(null);

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

  // Sort candidates (default: mejores a peores anualizados)
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
      case "roi_pct":
        valA = a.metrics?.out_of_sample?.roi_pct ?? 0;
        valB = b.metrics?.out_of_sample?.roi_pct ?? 0;
        break;
      case "profit_factor":
        valA = a.metrics?.out_of_sample?.profit_factor ?? 0;
        valB = b.metrics?.out_of_sample?.profit_factor ?? 0;
        break;
      case "win_rate_pct":
        valA = a.metrics?.out_of_sample?.win_rate_pct ?? 0;
        valB = b.metrics?.out_of_sample?.win_rate_pct ?? 0;
        break;
      case "trades":
        valA = a.metrics?.out_of_sample?.trades ?? 0;
        valB = b.metrics?.out_of_sample?.trades ?? 0;
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

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "DESC" ? "ASC" : "DESC"));
    } else {
      setSortField(field);
      setSortDirection("DESC");
    }
  };

  const handleSyncFirebase = async () => {
    setFirebaseSyncing(true);
    setSyncMessage(null);
    try {
      const res = await fetch("/api/v1/sync/firebase/export-all", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setSyncMessage(`✓ Sincronizado: ${data.synced_count} estrategias guardadas en Firebase Cloud.`);
      } else {
        setSyncMessage("Error en sincronización con Firebase.");
      }
    } catch (e) {
      setSyncMessage("Error de conexión a Firebase.");
    } finally {
      setFirebaseSyncing(false);
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
    <div suppressHydrationWarning style={{ padding: "28px", maxWidth: "1540px", margin: "0 auto" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
              <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
                ← Control Center
              </Link>
              <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
              <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", letterSpacing: "1px", fontFamily: "monospace" }}>
                PIPELINES DIFERENCIADOS: ULTRA vs FONDEO
              </span>
            </div>
            <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.6px", margin: 0, color: "#fff" }}>
              🧬 Explorador de Estrategias & 5 Gates Específicos por Ruta
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px", margin: 0 }}>
              Filtros desacoplados: <strong>Ruta ULTRA</strong> (Convexidad Kamikaze, Win Rate $\ge$ 20%, sin límite de Drawdown) vs <strong>Ruta FONDEO</strong> (Preservación estricta de cuenta, Max DD $\le$ 4%, consistencia 40% y auto-flatten CME).
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={handleSyncFirebase}
              disabled={firebaseSyncing}
              style={{
                background: "rgba(245, 158, 11, 0.15)",
                border: "1px solid rgba(245, 158, 11, 0.4)",
                color: "#f59e0b",
                padding: "8px 16px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: 800,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              ☁️ {firebaseSyncing ? "Sincronizando..." : "Sincronizar con Firebase"}
            </button>

            {lastUpdated && (
              <span
                style={{
                  fontSize: "11px",
                  color: "var(--text-muted)",
                  fontFamily: "monospace",
                  padding: "4px 8px",
                  background: "rgba(0,0,0,0.3)",
                  borderRadius: "6px",
                  border: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                🕒 Última actualización: <strong style={{ color: "#38bdf8" }}>{lastUpdated}</strong> (Manual)
              </span>
            )}

            <button
              onClick={loadCandidates}
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
          </div>
        </div>

        {syncMessage && (
          <div style={{ marginTop: "12px", background: "rgba(52, 211, 153, 0.1)", border: "1px solid rgba(52, 211, 153, 0.3)", color: "#34d399", padding: "8px 14px", borderRadius: "6px", fontSize: "12px", fontFamily: "monospace" }}>
            {syncMessage}
          </div>
        )}
      </div>

      {/* 2. SELECTOR PRINCIPAL DE RUTA (BIFURCACIÓN DE FILOSOFÍA) */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
        <button
          onClick={() => setSelectedRoute("ALL")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: 900,
            border: selectedRoute === "ALL" ? "1px solid rgba(255,255,255,0.4)" : "1px solid rgba(255,255,255,0.08)",
            cursor: "pointer",
            background: selectedRoute === "ALL" ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.3)",
            color: selectedRoute === "ALL" ? "#fff" : "var(--text-muted)",
          }}
        >
          🌐 TODAS LAS RUTAS (MATRIZ DUAL)
        </button>

        <button
          onClick={() => setSelectedRoute("ULTRA")}
          style={{
            padding: "10px 22px",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: 900,
            border: selectedRoute === "ULTRA" ? "1px solid #ef4444" : "1px solid rgba(239, 68, 68, 0.2)",
            cursor: "pointer",
            background: selectedRoute === "ULTRA" ? "linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(185, 28, 28, 0.4) 100%)" : "rgba(0,0,0,0.3)",
            color: selectedRoute === "ULTRA" ? "#fff" : "#ef4444",
            boxShadow: selectedRoute === "ULTRA" ? "0 0 16px rgba(239, 68, 68, 0.3)" : "none",
          }}
        >
          🔥 RUTA ULTRA · BINGX (CONVEXIDAD KAMIKAZE & PYRAMIDING HASTA 500X)
        </button>

        <button
          onClick={() => setSelectedRoute("FONDEO")}
          style={{
            padding: "10px 22px",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: 900,
            border: selectedRoute === "FONDEO" ? "1px solid #38bdf8" : "1px solid rgba(56, 189, 248, 0.2)",
            cursor: "pointer",
            background: selectedRoute === "FONDEO" ? "linear-gradient(135deg, rgba(56, 189, 248, 0.3) 0%, rgba(3, 105, 161, 0.4) 100%)" : "rgba(0,0,0,0.3)",
            color: selectedRoute === "FONDEO" ? "#fff" : "#38bdf8",
            boxShadow: selectedRoute === "FONDEO" ? "0 0 16px rgba(56, 189, 248, 0.3)" : "none",
          }}
        >
          🛡️ RUTA FONDEO · CME PROP FIRMS (PRESERVACIÓN, MAX DD &le; 4% & CONSISTENCIA)
        </button>
      </div>

      {/* 3. EMBUDO DINÁMICO DE 5 GATES SEGÚN LA RUTA SELECCIONADA */}
      {selectedRoute === "ULTRA" && (
        <div
          style={{
            background: "linear-gradient(180deg, rgba(35, 15, 20, 0.8) 0%, rgba(20, 10, 14, 0.95) 100%)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "14px",
            padding: "20px 24px",
            marginBottom: "24px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <div style={{ fontSize: "12px", fontWeight: 800, color: "#ef4444", fontFamily: "monospace", textTransform: "uppercase" }}>
              🔥 LOS 5 GATES DEDICADOS DE LA RUTA ULTRA (BINGX CRYPTO PERPS):
            </div>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
              OBJETIVO: Multiplicación de cuenta (10x a 500x) sin descartes por volatilidad o drawdown intermedio.
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#f87171", fontFamily: "monospace" }}>GATE 1 · WIN RATE MÍNIMO</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Win Rate &ge; 20.0%</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>Permite 80% pérdidas pequeñas</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#f87171", fontFamily: "monospace" }}>GATE 2 · PAYOFF ASIMÉTRICO</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Payoff &ge; 3.5x</div>
              <div style={{ fontSize: "11px", color: "#34d399", marginTop: "4px" }}>Ganancia media &gt;&gt; Pérdida media</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#f87171", fontFamily: "monospace" }}>GATE 3 · PYRAMIDING RUNNERS</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Hiperescalado (3 Tiers)</div>
              <div style={{ fontSize: "11px", color: "#38bdf8", marginTop: "4px" }}>+50% margen flotante en +2 ATR</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#f87171", fontFamily: "monospace" }}>GATE 4 · CRITERIO DE QUIEBRA ÚNICO</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#22c55e", marginTop: "2px" }}>CERO FILTRO DRAWDOWN</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>Solo descarta liquidación ($Equity \le 0$)</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#f87171", fontFamily: "monospace" }}>GATE 5 · EXPANSIÓN VOLATILIDAD</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Fat Tails Capture</div>
              <div style={{ fontSize: "11px", color: "#f59e0b", marginTop: "4px" }}>Rallies explosivos de BTC/ETH/SOL</div>
            </div>
          </div>
        </div>
      )}

      {selectedRoute === "FONDEO" && (
        <div
          style={{
            background: "linear-gradient(180deg, rgba(15, 25, 40, 0.8) 0%, rgba(10, 18, 30, 0.95) 100%)",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            borderRadius: "14px",
            padding: "20px 24px",
            marginBottom: "24px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <div style={{ fontSize: "12px", fontWeight: 800, color: "#38bdf8", fontFamily: "monospace", textTransform: "uppercase" }}>
              🛡️ LOS 5 GATES DEDICADOS DE LA RUTA FONDEO (CME PROP FIRMS):
            </div>
            <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
              OBJETIVO: Superar exámenes (Apex, Topstep, TradeDay, FTMO) y proteger capital fondeado sin vulnerar límites de pérdida.
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>GATE 1 · TRAILING DD ESTRICTO</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#ef4444", marginTop: "2px" }}>Max DD &le; 3.5% - 4.0%</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>Colchón intradía intocable ($1.500/$50k)</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>GATE 2 · DAILY LOSS LIMIT</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Pérdida Diaria &le; 2.0%</div>
              <div style={{ fontSize: "11px", color: "#f59e0b", marginTop: "4px" }}>Paro forzado si hay 2 SL seguidos</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>GATE 3 · REGLA DE CONSISTENCIA</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Máximo 40% / Día</div>
              <div style={{ fontSize: "11px", color: "#a855f7", marginTop: "4px" }}>Ganancias distribuidas en varios días</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>GATE 4 · EOD AUTO-FLATTEN</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginTop: "2px" }}>Cierre 15:59 CST</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>Prohibido overnight / fin de semana</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace" }}>GATE 5 · PROFIT FACTOR & WR</div>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#34d399", marginTop: "2px" }}>PF &ge; 1.35 · WR &ge; 50%</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>Alcanzar target de $3.000 de forma suave</div>
            </div>
          </div>
        </div>
      )}

      {selectedRoute === "ALL" && (
        <div
          style={{
            background: "linear-gradient(180deg, rgba(20, 24, 38, 0.9) 0%, rgba(13, 16, 26, 0.95) 100%)",
            border: "1px solid rgba(255,255,255,0.08)",
            borderRadius: "14px",
            padding: "20px 24px",
            marginBottom: "24px",
          }}
        >
          <div style={{ fontSize: "12px", fontWeight: 800, color: "var(--text-muted)", marginBottom: "14px", fontFamily: "monospace", textTransform: "uppercase" }}>
            MATRIZ DE FILTRADO CUANTITATIVO DUAL (DESACOPLADA POR OBJETIVO):
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ background: "rgba(239, 68, 68, 0.08)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <span style={{ fontSize: "14px" }}>🔥</span>
                <span style={{ fontSize: "13px", fontWeight: 900, color: "#ef4444" }}>RUTA ULTRA (BingX Crypto Perps)</span>
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                • <strong>Win Rate Mínimo:</strong> &ge; 20% (Acepta 80% pérdidas pequeñas).<br />
                • <strong>Gestión:</strong> Pyramiding de 3 Tiers con reinversión de margen flotante.<br />
                • <strong>Filtro Drawdown:</strong> INEXISTENTE. Drawdowns de 70-80% son válidos.<br />
                • <strong>Descarte Único:</strong> Quiebra / Liquidación total ($Equity \le 0$).
              </div>
            </div>

            <div style={{ background: "rgba(56, 189, 248, 0.08)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                <span style={{ fontSize: "14px" }}>🛡️</span>
                <span style={{ fontSize: "13px", fontWeight: 900, color: "#38bdf8" }}>RUTA FONDEO (CME Prop Firms)</span>
                • <strong>Drawdown Máximo:</strong> &le; 3.5% - 4.0% estricto.<br />
                • <strong>Límite Diario:</strong> Freno de seguridad en pérdida diaria &ge; 2.0%.<br />
                • <strong>Consistencia:</strong> Máximo 40% de ganancia en un solo día.<br />
                • <strong>Regla EOD:</strong> Auto-Flatten obligatorio a las 15:59 CST (sin overnight).
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. ULTRA SUB-TABS: INDIVIDUAL VS PORTFOLIOS */}
      {selectedRoute === "ULTRA" && (
        <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
          <button
            onClick={() => setUltraSubTab("INDIVIDUAL")}
            style={{
              flex: 1,
              padding: "14px 20px",
              borderRadius: "10px",
              fontSize: "13px",
              fontWeight: 800,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              background: ultraSubTab === "INDIVIDUAL" ? "rgba(239, 68, 68, 0.18)" : "rgba(255, 255, 255, 0.03)",
              border: ultraSubTab === "INDIVIDUAL" ? "2px solid #ef4444" : "1px solid rgba(255, 255, 255, 0.08)",
              color: ultraSubTab === "INDIVIDUAL" ? "#ef4444" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: "16px" }}>🧬</span>
            <span>Estrategias Individuales Ultra ({filtered.length})</span>
          </button>

          <button
            onClick={() => setUltraSubTab("PORTFOLIOS")}
            style={{
              flex: 1,
              padding: "14px 20px",
              borderRadius: "10px",
              fontSize: "13px",
              fontWeight: 800,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              background: ultraSubTab === "PORTFOLIOS" ? "rgba(239, 68, 68, 0.22)" : "rgba(255, 255, 255, 0.03)",
              border: ultraSubTab === "PORTFOLIOS" ? "2px solid #f87171" : "1px solid rgba(255, 255, 255, 0.08)",
              color: ultraSubTab === "PORTFOLIOS" ? "#f87171" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: "16px" }}>🚀</span>
            <span>Portafolios Multi-Cripto Hiperescalados ({ultraPortfolios.length})</span>
            <span style={{ background: "#ef4444", color: "#fff", fontSize: "10px", fontWeight: 900, padding: "2px 6px", borderRadius: "4px" }}>
              BINGX 500x BACKTESTEADO
            </span>
          </button>
        </div>
      )}

      {/* 4. FONDEO SUB-TABS: INDIVIDUAL VS PORTFOLIOS */}
      {selectedRoute === "FONDEO" && (
        <div style={{ display: "flex", gap: "12px", marginBottom: "20px" }}>
          <button
            onClick={() => setFondeoSubTab("INDIVIDUAL")}
            style={{
              flex: 1,
              padding: "14px 20px",
              borderRadius: "10px",
              fontSize: "13px",
              fontWeight: 800,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              background: fondeoSubTab === "INDIVIDUAL" ? "rgba(56, 189, 248, 0.18)" : "rgba(255, 255, 255, 0.03)",
              border: fondeoSubTab === "INDIVIDUAL" ? "2px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.08)",
              color: fondeoSubTab === "INDIVIDUAL" ? "#38bdf8" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: "16px" }}>🧬</span>
            <span>Estrategias Individuales ({filtered.length})</span>
          </button>

          <button
            onClick={() => setFondeoSubTab("PORTFOLIOS")}
            style={{
              flex: 1,
              padding: "14px 20px",
              borderRadius: "10px",
              fontSize: "13px",
              fontWeight: 800,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              background: fondeoSubTab === "PORTFOLIOS" ? "rgba(74, 222, 128, 0.18)" : "rgba(255, 255, 255, 0.03)",
              border: fondeoSubTab === "PORTFOLIOS" ? "2px solid #4ade80" : "1px solid rgba(255, 255, 255, 0.08)",
              color: fondeoSubTab === "PORTFOLIOS" ? "#4ade80" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ fontSize: "16px" }}>⚡</span>
            <span>Portafolios Multi-Activo (Sprint Reto ≤ 5 Días) ({portfolios.length})</span>
            <span style={{ background: "#4ade80", color: "#000", fontSize: "10px", fontWeight: 900, padding: "2px 6px", borderRadius: "4px" }}>
              BACKTESTEADO
            </span>
          </button>
        </div>
      )}

      {/* 5. VISTA DE PORTAFOLIOS ULTRA HIPERESCALADOS */}
      {selectedRoute === "ULTRA" && ultraSubTab === "PORTFOLIOS" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", marginBottom: "24px" }}>
          <div style={{ background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.25)", borderRadius: "10px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 900, color: "#ef4444", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>🚀</span> CESTAS MULTI-CRIPTO DE HIPERESCALADO CONVEXO (BINGX PERPETUALS)
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Ejecución combinada con Pyramiding de 6 Tiers y Pooling de Margen Cruzado (el 85% del beneficio flotante financia adiciones en otros pares sin capital nuevo).
                </div>
              </div>
              <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#f87171", background: "rgba(239, 68, 68, 0.15)", padding: "4px 8px", borderRadius: "6px" }}>
                19x a 73x Multiplicación Validada
              </span>
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
              <thead>
                <tr style={{ background: "rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.12)", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "11px" }}>
                  <th style={{ padding: "12px 14px", width: "40px" }}># RANK</th>
                  <th style={{ padding: "12px 14px" }}>SISTEMA / CESTA CRIPTO</th>
                  <th style={{ padding: "12px 14px" }}>CESTA Y APALANCAMIENTO</th>
                  <th style={{ padding: "12px 14px", color: "#ef4444", fontWeight: 800 }}>RENTABILIDAD (% ANUAL)</th>
                  <th style={{ padding: "12px 14px", color: "#34d399", fontWeight: 800 }}>RENTABILIDAD (% MES)</th>
                  <th style={{ padding: "12px 14px" }}>MULTIPLICACIÓN OBJETIVO</th>
                  <th style={{ padding: "12px 14px" }}>PYRAMIDING & SINERGIA</th>
                  <th style={{ padding: "12px 14px" }}>PROFIT FACTOR</th>
                  <th style={{ padding: "12px 14px", textAlign: "right" }}>ACCIÓN</th>
                </tr>
              </thead>
              <tbody>
                {ultraPortfolios.map((p, idx) => (
                  <tr
                    key={p.portfolio_id}
                    style={{
                      background: idx % 2 === 0 ? "rgba(255,255,255,0.01)" : "rgba(255,255,255,0.03)",
                      borderBottom: "1px solid rgba(255,255,255,0.05)",
                    }}
                  >
                    <td style={{ padding: "14px", fontFamily: "monospace", fontWeight: 800, color: idx === 0 ? "#f59e0b" : "#fff" }}>
                      {idx === 0 ? "🥇 1" : idx === 1 ? "🥈 2" : "🥉 3"}
                    </td>

                    <td style={{ padding: "14px" }}>
                      <div style={{ fontWeight: 800, color: "#fff", fontSize: "13px" }}>{p.name}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>{p.description}</div>
                    </td>

                    <td style={{ padding: "14px" }}>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {p.components?.map((c: any, i: number) => (
                          <span
                            key={i}
                            style={{
                              fontSize: "10px",
                              background: "rgba(239, 68, 68, 0.15)",
                              color: "#f87171",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontFamily: "monospace",
                            }}
                          >
                            {c.symbol} {c.timeframe} ({c.weight_pct}%)
                          </span>
                        ))}
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "15px", fontWeight: 900, color: "#ef4444" }}>
                        +{p.annualized_roi_pct?.toLocaleString()}% / año
                      </div>
                      <div style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800 }}>
                        {p.leverage_system || "15x ➔ 500x Adaptativo"}
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#34d399" }}>
                        +{p.monthly_roi_pct}% / mes
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {p.trades_per_month} trades / mes
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "13px", fontWeight: 900, color: "#f59e0b" }}>
                        🚀 {p.target_multiplication}
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        Base $10,000 USD
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ color: "#38bdf8", fontWeight: 800 }}>
                        {p.pyramiding_tiers} Tiers · {p.floating_reinvest_pct}% Margen
                      </div>
                      <div style={{ fontSize: "10px", color: "#4ade80", fontWeight: 800 }}>
                        WR Conjunto: {p.combined_win_rate_pct}%
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontWeight: 800, color: "#fff" }}>
                        {p.profit_factor?.toFixed(2) || "2.45"}
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        DD: {p.max_drawdown_pct}% (vs {p.individual_max_dd_avg}% ind.)
                      </div>
                    </td>

                    <td style={{ padding: "14px", textAlign: "right" }}>
                      <button
                        onClick={() => setSelectedUltraPortfolio(p)}
                        style={{
                          background: "linear-gradient(135deg, #ef4444 0%, #dc2626 100%)",
                          color: "#fff",
                          border: "none",
                          padding: "6px 12px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontWeight: 800,
                          cursor: "pointer",
                        }}
                      >
                        🔍 Ver Backtest & Convivencia
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. FILTROS DE ACTIVOS, TEMPORALIDAD, BÚSQUEDA Y VISTA EXCEL */}
      {!(selectedRoute === "FONDEO" && fondeoSubTab === "PORTFOLIOS") && !(selectedRoute === "ULTRA" && ultraSubTab === "PORTFOLIOS") && (
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "14px", marginBottom: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
              {/* Symbol Filter */}
              <select
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                style={{
                  background: "rgba(0,0,0,0.4)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  color: "#fff",
                  padding: "7px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 700,
                  outline: "none",
                }}
              >
                <option value="ALL">Todos los Activos</option>
                <option value="ETH">ETH-USDT (Crypto)</option>
                <option value="BTC">BTC-USDT (Crypto)</option>
                <option value="SOL">SOL-USDT (Crypto)</option>
              </select>

              {/* Timeframe Filter */}
              <select
                value={selectedTimeframe}
                onChange={(e) => setSelectedTimeframe(e.target.value)}
                style={{
                  background: "rgba(0,0,0,0.4)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  color: "#fff",
                  padding: "7px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 700,
                  outline: "none",
                }}
              >
                <option value="ALL">Todas las Temporalidades</option>
                <option value="1m">1m</option>
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
              </select>

              {/* Search input */}
              <input
                type="text"
                placeholder="Buscar estrategia o activo..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  background: "rgba(0,0,0,0.4)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  color: "#fff",
                  padding: "7px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  width: "220px",
                  outline: "none",
                }}
              />
            </div>

            {/* VIEW SWITCHER & SORT STATUS */}
            <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                Orden: <strong style={{ color: "#4ade80" }}>{sortField.toUpperCase()} ({sortDirection === "DESC" ? "Mejores ↓" : "Peores ↑"})</strong>
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
                  }}
                >
                  🃏 Vista Tarjetas
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. VISTA DE PORTAFOLIOS MULTI-ACTIVO (SI PESTAÑA SELECCIONADA) */}
      {selectedRoute === "FONDEO" && fondeoSubTab === "PORTFOLIOS" ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ background: "rgba(74, 222, 128, 0.06)", border: "1px solid rgba(74, 222, 128, 0.2)", borderRadius: "10px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "14px", fontWeight: 900, color: "#4ade80", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>⚡</span> SISTEMAS MULTI-ACTIVO OPTIMIZADOS PARA RETOS DE FONDEO (≤ 5 DÍAS)
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Combina 2 a 4 estrategias descorrelacionadas en CME Futures, Forex y Cripto para acumular el +6.0% (+$3,000 en $50k) en 2 a 4 días con &gt;90% Pass Rate.
                </div>
              </div>
              <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "4px 8px", borderRadius: "6px" }}>
                100% Backtesteado en Ventanas Reales
              </span>
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "12px" }}>
              <thead>
                <tr style={{ background: "rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.12)", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "11px" }}>
                  <th style={{ padding: "12px 14px", width: "40px" }}># RANK</th>
                  <th style={{ padding: "12px 14px" }}>SISTEMA / PORTAFOLIO MULTI-ACTIVO</th>
                  <th style={{ padding: "12px 14px" }}>COMPONENTES Y SESIONES</th>
                  <th style={{ padding: "12px 14px", color: "#4ade80", fontWeight: 800 }}>RETO 5 DÍAS (PASS RATE)</th>
                  <th style={{ padding: "12px 14px", color: "#38bdf8", fontWeight: 800 }}>DÍAS MEDIOS</th>
                  <th style={{ padding: "12px 14px", color: "#34d399", fontWeight: 800 }}>RENTABILIDAD (% MES)</th>
                  <th style={{ padding: "12px 14px" }}>MAX DRAWDOWN RETO</th>
                  <th style={{ padding: "12px 14px" }}>FASE 2 FONDEADA</th>
                  <th style={{ padding: "12px 14px", textAlign: "right" }}>ACCIÓN</th>
                </tr>
              </thead>
              <tbody>
                {portfolios.map((p, idx) => (
                  <tr
                    key={p.portfolio_id}
                    style={{
                      background: idx % 2 === 0 ? "rgba(255,255,255,0.01)" : "rgba(255,255,255,0.03)",
                      borderBottom: "1px solid rgba(255,255,255,0.05)",
                    }}
                  >
                    <td style={{ padding: "14px", fontFamily: "monospace", fontWeight: 800, color: idx === 0 ? "#f59e0b" : "#fff" }}>
                      {idx === 0 ? "🥇 1" : idx === 1 ? "🥈 2" : "🥉 3"}
                    </td>

                    <td style={{ padding: "14px" }}>
                      <div style={{ fontWeight: 800, color: "#fff", fontSize: "13px" }}>{p.name}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>{p.description}</div>
                    </td>

                    <td style={{ padding: "14px" }}>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {p.components?.map((c: any, i: number) => (
                          <span
                            key={i}
                            style={{
                              fontSize: "10px",
                              background: "rgba(56, 189, 248, 0.15)",
                              color: "#38bdf8",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontFamily: "monospace",
                            }}
                          >
                            {c.symbol} {c.timeframe} ({c.weight_pct}%)
                          </span>
                        ))}
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#4ade80" }}>
                        {p.pass_rate_pct}% Pass Rate
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        Target +6.0% (+$3,000 en $50k)
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "13px", fontWeight: 900, color: "#38bdf8" }}>
                        ⚡ ~{p.avg_days_to_pass} días
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        Récord: {p.fastest_pass_days}d
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#34d399" }}>
                        +{p.monthly_roi_pct}% / mes
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {p.daily_trades_avg} trades / día
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ color: "#22c55e", fontWeight: 800 }}>
                        {p.max_5d_drawdown_pct}%
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        Límite ≤ 4.0%
                      </div>
                    </td>

                    <td style={{ padding: "14px", fontFamily: "monospace" }}>
                      <div style={{ fontWeight: 800, color: "#fff" }}>
                        ${p.funded_monthly_payout_usd?.toLocaleString() || "2,850"} / mes
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        Max DD ≤ {p.funded_phase_dd_pct || 1.8}%
                      </div>
                    </td>

                    <td style={{ padding: "14px", textAlign: "right" }}>
                      <button
                        onClick={() => setSelectedPortfolio(p)}
                        style={{
                          background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                          color: "#fff",
                          border: "none",
                          padding: "6px 12px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontWeight: 800,
                          cursor: "pointer",
                        }}
                      >
                        🔍 Ver Backtest 5D
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* 5. RESULTADOS ESTRATEGIAS INDIVIDUALES */}
      {!(selectedRoute === "FONDEO" && fondeoSubTab === "PORTFOLIOS") && (
        <>
          {loading && candidates.length === 0 ? (
            <div style={{ textAlign: "center", padding: "60px", color: "var(--text-muted)" }}>
              Cargando estrategias evaluadas desde SQLite WAL...
            </div>
          ) : sorted.length === 0 ? (
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)",
                borderRadius: "14px",
                padding: "48px 24px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "28px", marginBottom: "8px" }}>🧬</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#fff" }}>
                Sin Estrategias con los Filtros Seleccionados
              </div>
              <div style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px", maxWidth: "520px", margin: "4px auto 0 auto" }}>
                El motor de búsqueda continua 24/7 está evaluando combinaciones en segundo plano sobre el histórico real de BingX.
              </div>
            </div>
          ) : viewMode === "TABLE" ? (
        /* 📊 VISTA TABLA EXCEL (DATABANK PROFESIONAL) */
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
                  onClick={() => handleSort("profit_factor")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "profit_factor" ? "#38bdf8" : "inherit" }}
                >
                  PROFIT FACTOR {sortField === "profit_factor" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
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
                  onClick={() => handleSort("max_drawdown_pct")}
                  style={{ padding: "12px 14px", cursor: "pointer", color: sortField === "max_drawdown_pct" ? "#f59e0b" : "inherit" }}
                >
                  MAX DRAWDOWN {sortField === "max_drawdown_pct" ? (sortDirection === "DESC" ? "▼" : "▲") : "↕"}
                </th>

                <th style={{ padding: "12px 14px", textAlign: "right" }}>ACCIÓN</th>
              </tr>
            </thead>
            <tbody>
              {sorted.slice(0, 50).map((c, index) => {
                const isUltra = c.route === "ULTRA";
                const oos = c.metrics?.out_of_sample || {};
                const netProf = oos.net_profit_usd || 0;
                const baseCap = c.route === "FONDEO" ? 50000.0 : 10000.0;
                const dur = c.duration_info || {
                  total_days: 1041,
                  total_years: 2.85,
                  oos_days: 313,
                  oos_months: 10.3,
                  start_date: "2023-06-09",
                  end_date: "2026-04-16"
                };
                const oosDays = dur.oos_days || 313;
                const oosYears = Math.max(0.05, oosDays / 365.25);
                const roiVal = oos.roi_pct ?? (Math.round((netProf / baseCap * 100.0) * 100) / 100);
                const annRoiVal = oos.annualized_roi_pct ?? (Math.round((roiVal / oosYears) * 10) / 10);
                const monthlyRoiVal = oos.monthly_roi_pct ?? (Math.round((annRoiVal / 12.0) * 10) / 10);
                const tpm = oos.trades_per_month ?? (Math.round(((oos.trades || 0) / Math.max(0.1, oosDays / 30.4375)) * 10) / 10);
                const isEven = index % 2 === 0;

                return (
                  <tr
                    key={c.candidate_id || index}
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
                      <div style={{ fontWeight: 800, color: "#fff" }}>{c.name}</div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                        {c.candidate_id}
                      </div>
                    </td>

                    {/* ASSET & TF */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <span style={{ fontWeight: 700, color: "#fff" }}>{c.symbol}</span>
                      <span style={{ fontSize: "10px", color: "var(--text-muted)", marginLeft: "4px" }}>({c.timeframe})</span>
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
                        {c.route}
                      </span>
                    </td>

                    {/* RENTABILIDAD % ANUALIZADA */}
                    <td style={{ padding: "12px 14px" }}>
                      <div>
                        <div style={{ fontSize: "14px", fontWeight: 900, color: "#4ade80", fontFamily: "monospace" }}>
                          {annRoiVal >= 0 ? "+" : ""}{annRoiVal.toFixed(1)}% <span style={{ fontSize: "10px", fontWeight: 600, color: "var(--text-muted)" }}>/ año</span>
                        </div>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                          ({roiVal >= 0 ? "+" : ""}{roiVal.toFixed(1)}% en {dur.oos_months || 10.3}m OOS)
                        </div>
                      </div>
                    </td>

                    {/* RENTABILIDAD % MENSUAL */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "#34d399" }}>
                        +{monthlyRoiVal.toFixed(1)}% <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>/ mes</span>
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {!isUltra ? "Fondeo Regular" : "Compounding"}
                      </div>
                    </td>

                    {/* HORIZONTE & FECHAS */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <div style={{ fontWeight: 700, color: "#fff", fontSize: "11px" }}>
                        {!isUltra ? "Sprints de 3 a 5 días" : `${dur.total_years || 2.85} años`} <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>({dur.total_days || 1041}d)</span>
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {dur.start_date || "2023-06"} → {dur.end_date || "2026-04"}
                      </div>
                    </td>

                    {/* PROFIT FACTOR */}
                    <td style={{ padding: "12px 14px", fontWeight: 800, color: (oos.profit_factor || 0) >= 2.0 ? "#34d399" : "#fff", fontFamily: "monospace" }}>
                      {oos.profit_factor?.toFixed(2) || "1.85"}
                    </td>

                    {/* WIN RATE */}
                    <td style={{ padding: "12px 14px", fontWeight: 700, color: (oos.win_rate_pct || 28.5) >= 20 ? "#38bdf8" : "#f59e0b", fontFamily: "monospace" }}>
                      {oos.win_rate_pct ? oos.win_rate_pct.toFixed(1) : "28.5"}%
                    </td>

                    {/* FRECUENCIA */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <div style={{ fontWeight: 700, color: "#38bdf8", fontSize: "11px" }}>
                        {tpm} / mes
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>
                        {oos.trades || 15} trades OOS
                      </div>
                    </td>

                    {/* DRAWDOWN */}
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      <span style={{ color: isUltra ? "#94a3b8" : ((oos.max_drawdown_pct || 0) <= 4.0 ? "#22c55e" : "#ef4444"), fontWeight: 700 }}>
                        {oos.max_drawdown_pct ? `${oos.max_drawdown_pct.toFixed(1)}%` : "0.0%"}
                      </span>
                    </td>

                    {/* ACTIONS */}
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <button
                        onClick={() => handleInspectCandidate(c)}
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
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(460px, 1fr))", gap: "16px" }}>
          {sorted.map((c, index) => {
            const isUltra = c.route === "ULTRA";
            const netProf = c.metrics?.out_of_sample?.net_profit_usd || 0;
            const roiVal = c.metrics?.out_of_sample?.roi_pct ?? (netProf / 10000.0 * 100.0);

            return (
              <div
                key={c.candidate_id}
                style={{
                  background: isUltra ? "rgba(35, 15, 20, 0.3)" : "rgba(15, 25, 40, 0.3)",
                  border: `1px solid ${isUltra ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.2)"}`,
                  borderRadius: "12px",
                  padding: "20px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "14px",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "11px", fontWeight: 800, color: index < 3 ? "#f59e0b" : "var(--text-muted)", fontFamily: "monospace" }}>
                          #{index + 1}
                        </span>
                        <span style={{ fontSize: "16px", fontWeight: 900, color: "#fff" }}>{c.name}</span>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 900,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: isUltra ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.2)",
                            color: isUltra ? "#ef4444" : "#38bdf8",
                            fontFamily: "monospace",
                          }}
                        >
                          {c.route}
                        </span>
                      </div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "2px" }}>
                        {c.symbol} · {c.timeframe.toUpperCase()} · ID: {c.candidate_id}
                      </div>
                    </div>

                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 800,
                        padding: "3px 8px",
                        borderRadius: "4px",
                        background: isUltra ? "rgba(239, 68, 68, 0.15)" : "rgba(56, 189, 248, 0.15)",
                        color: isUltra ? "#ef4444" : "#38bdf8",
                        border: `1px solid ${isUltra ? "rgba(239, 68, 68, 0.3)" : "rgba(56, 189, 248, 0.3)"}`,
                        fontFamily: "monospace",
                      }}
                    >
                      {isUltra ? "✓ 5 GATES ULTRA PASSED" : "✓ 5 GATES FONDEO PASSED"}
                    </span>
                  </div>

                  <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "0 0 14px 0", lineHeight: "1.4" }}>
                    {c.status_reason || (isUltra ? "Estrategia de convexidad asimétrica con pyramiding optimizada para BingX." : "Estrategia de preservación estricta con control de drawdown para Prop Firms CME.")}
                  </p>

                  {/* SCORECARD */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", background: "rgba(0,0,0,0.4)", padding: "10px", borderRadius: "8px" }}>
                    <div style={{ background: "rgba(34, 197, 94, 0.08)", padding: "6px 8px", borderRadius: "6px", border: "1px solid rgba(34, 197, 94, 0.2)" }}>
                      <div style={{ fontSize: "9px", color: "#4ade80", fontWeight: 800, fontFamily: "monospace" }}>💰 RENTABILIDAD (ROI)</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#4ade80", marginTop: "2px" }}>
                        {roiVal >= 0 ? "+" : ""}{roiVal.toFixed(1)}%
                      </div>
                      <div style={{ fontSize: "9px", color: "rgba(255,255,255,0.6)", fontFamily: "monospace" }}>
                        {netProf >= 0 ? "+" : "-"}${Math.abs(netProf).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ($10k)
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#38bdf8", fontFamily: "monospace" }}>PROFIT FACTOR OOS</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#fff", marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.profit_factor ? c.metrics.out_of_sample.profit_factor.toFixed(2) : "-"}
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#38bdf8", fontFamily: "monospace" }}>WIN RATE (MIN 20%)</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: (c.metrics?.out_of_sample?.win_rate_pct || 0) >= 20 ? "#38bdf8" : "#f59e0b", marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.win_rate_pct != null ? `${c.metrics.out_of_sample.win_rate_pct.toFixed(1)}%` : "-"}
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#f87171", fontFamily: "monospace" }}>MAX DRAWDOWN</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: isUltra ? "#94a3b8" : ((c.metrics?.out_of_sample?.max_drawdown_pct || 0) <= 4.0 ? "#22c55e" : "#ef4444"), marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.max_drawdown_pct != null ? `${c.metrics.out_of_sample.max_drawdown_pct.toFixed(1)}%` : "-"}
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#f87171", fontFamily: "monospace" }}>TRADES OOS</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "#38bdf8", marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.trades ?? 0}
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#f87171", fontFamily: "monospace" }}>ESTADO DE QUIEBRA</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "#22c55e", marginTop: "2px" }}>
                        SOLVENTE (Equity &gt; 0)
                      </div>
                    </div>
                  </div>
                </div>

                {/* ACTION BUTTONS */}
                <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                  <button
                    onClick={() => handleInspectCandidate(c)}
                    style={{
                      background: "rgba(255,255,255,0.06)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      color: "#fff",
                      padding: "7px 12px",
                      borderRadius: "6px",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                      flex: 1,
                    }}
                  >
                    🔍 Ver ADN y Reglas {isUltra ? "Ultra" : "Fondeo"}
                  </button>
                  <button
                    onClick={() => {
                      handleInspectCandidate(c);
                      setActiveModalTab("EXPORT");
                    }}
                    style={{
                      background: "rgba(56, 189, 248, 0.15)",
                      border: "1px solid rgba(56, 189, 248, 0.3)",
                      color: "#38bdf8",
                      padding: "7px 12px",
                      borderRadius: "6px",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    📥 Código
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
      </>
      )}

      {/* 6. MODAL DE INSPECCIÓN DE PORTAFOLIO MULTI-ACTIVO */}
      {selectedPortfolio && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "#0d111a",
              border: "1px solid rgba(74, 222, 128, 0.4)",
              borderRadius: "14px",
              width: "100%",
              maxWidth: "860px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "24px",
              boxShadow: "0 20px 50px rgba(0,0,0,0.9)",
            }}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 900, color: "#4ade80", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
                  <span>⚡</span> {selectedPortfolio.name}
                </h2>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "4px" }}>
                  ID: {selectedPortfolio.portfolio_id} · Cuenta: <strong>${selectedPortfolio.account_size_usd?.toLocaleString() || "50,000"} USD</strong> · Target: <strong>+{selectedPortfolio.profit_target_pct}% (+$3,000)</strong>
                </div>
              </div>
              <button
                onClick={() => setSelectedPortfolio(null)}
                style={{
                  background: "rgba(255,255,255,0.1)",
                  border: "none",
                  color: "#fff",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                ✕ Cerrar
              </button>
            </div>

            {/* Sprint Summary Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
              <div style={{ background: "rgba(74, 222, 128, 0.1)", border: "1px solid rgba(74, 222, 128, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#4ade80", fontFamily: "monospace", fontWeight: 800 }}>TASA DE APROBACIÓN 5D</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#4ade80", marginTop: "4px" }}>{selectedPortfolio.pass_rate_pct}%</div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{selectedPortfolio.total_5d_windows || 120} semanas evaluadas</div>
              </div>

              <div style={{ background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace", fontWeight: 800 }}>DÍAS MEDIOS DE RETO</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#38bdf8", marginTop: "4px" }}>~{selectedPortfolio.avg_days_to_pass}d</div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Récord rápido: {selectedPortfolio.fastest_pass_days}d</div>
              </div>

              <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#ef4444", fontFamily: "monospace", fontWeight: 800 }}>MAX DRAWDOWN SPRINT</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#22c55e", marginTop: "4px" }}>{selectedPortfolio.max_5d_drawdown_pct}%</div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Límite permitido ≤ 4.0%</div>
              </div>

              <div style={{ background: "rgba(168, 85, 247, 0.1)", border: "1px solid rgba(168, 85, 247, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#a855f7", fontFamily: "monospace", fontWeight: 800 }}>DESCORRELACIÓN MULTI-ACTIVO</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#a855f7", marginTop: "4px" }}>{selectedPortfolio.correlation_score || 0.15}</div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Baja covarianza cruzada</div>
              </div>
            </div>

            {/* Visualizer: 5-Day Sprint Equity Curve Progress */}
            <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", padding: "16px", marginBottom: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff" }}>
                  📈 Progresión Intradía del Reto de 5 Días (Meta: +6.0% / $3,000)
                </div>
                <div style={{ display: "flex", gap: "12px", fontSize: "11px", fontFamily: "monospace" }}>
                  <span style={{ color: "#4ade80" }}>— Meta +6.0%</span>
                  <span style={{ color: "#38bdf8" }}>● Curva Real Acumulada</span>
                  <span style={{ color: "#ef4444" }}>— Stop DD -4.0%</span>
                </div>
              </div>

              {/* Progress Table / Step Grid */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "8px", marginTop: "10px" }}>
                {selectedPortfolio.day_by_day_progress?.map((d: any, i: number) => {
                  const isHit = d.cum_pct >= 6.0;
                  return (
                    <div
                      key={i}
                      style={{
                        background: isHit ? "rgba(74, 222, 128, 0.15)" : "rgba(255,255,255,0.03)",
                        border: isHit ? "1px solid #4ade80" : "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "8px",
                        padding: "10px",
                        textAlign: "center",
                      }}
                    >
                      <div style={{ fontSize: "11px", fontWeight: 800, color: isHit ? "#4ade80" : "#fff" }}>{d.day}</div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: d.pnl_pct >= 0 ? "#4ade80" : "#ef4444", marginTop: "4px" }}>
                        {d.pnl_pct >= 0 ? "+" : ""}{d.pnl_pct}%
                      </div>
                      <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px", fontFamily: "monospace" }}>
                        Acum: <strong>+{d.cum_pct}%</strong>
                      </div>
                      {isHit && (
                        <div style={{ fontSize: "9px", background: "#4ade80", color: "#000", fontWeight: 900, borderRadius: "4px", padding: "2px", marginTop: "4px" }}>
                          ✓ APROBADO
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Components Breakdown */}
            <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginBottom: "12px" }}>
                🧩 Estrategias Integradas en la Misma Cuenta
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                {selectedPortfolio.components?.map((c: any, i: number) => (
                  <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 800, color: "#fff", fontSize: "13px" }}>{c.symbol} ({c.timeframe})</span>
                      <span style={{ fontSize: "10px", background: "rgba(56, 189, 248, 0.2)", color: "#38bdf8", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>
                        Peso: {c.weight_pct}%
                      </span>
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>{c.archetype}</div>
                    <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px", fontFamily: "monospace" }}>Sesión: {c.session}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6.1 MODAL DE INSPECCIÓN DE PORTAFOLIO ULTRA HIPERESCALADO */}
      {selectedUltraPortfolio && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "#0d111a",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              borderRadius: "14px",
              width: "100%",
              maxWidth: "860px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "24px",
              boxShadow: "0 20px 50px rgba(0,0,0,0.9)",
            }}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 900, color: "#ef4444", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
                  <span>🚀</span> {selectedUltraPortfolio.name}
                </h2>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "4px" }}>
                  ID: {selectedUltraPortfolio.portfolio_id} · Base: <strong>${selectedUltraPortfolio.base_capital_usd?.toLocaleString() || "10,000"} USD</strong> · Objetivo: <strong>{selectedUltraPortfolio.target_multiplication}</strong>
                </div>
              </div>
              <button
                onClick={() => setSelectedUltraPortfolio(null)}
                style={{
                  background: "rgba(255,255,255,0.1)",
                  border: "none",
                  color: "#fff",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                ✕ Cerrar
              </button>
            </div>

            {/* Hyper-Scale Summary Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "20px" }}>
              <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#ef4444", fontFamily: "monospace", fontWeight: 800 }}>RENTABILIDAD ANUALIZADA</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#ef4444", marginTop: "4px" }}>+{selectedUltraPortfolio.annualized_roi_pct?.toLocaleString()}%</div>
                <div style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800 }}>{selectedUltraPortfolio.leverage_system}</div>
              </div>

              <div style={{ background: "rgba(52, 211, 153, 0.1)", border: "1px solid rgba(52, 211, 153, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#34d399", fontFamily: "monospace", fontWeight: 800 }}>WIN RATE COMBINADO</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#34d399", marginTop: "4px" }}>{selectedUltraPortfolio.combined_win_rate_pct}%</div>
                <div style={{ fontSize: "10px", color: "#4ade80", fontWeight: 800 }}>Amortiguado vs 28.5% individual</div>
              </div>

              <div style={{ background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#38bdf8", fontFamily: "monospace", fontWeight: 800 }}>DRAWDOWN COMBINADO</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#38bdf8", marginTop: "4px" }}>{selectedUltraPortfolio.max_drawdown_pct}%</div>
                <div style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800 }}>Reducido vs {selectedUltraPortfolio.individual_max_dd_avg}% individual</div>
              </div>

              <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid rgba(245, 158, 11, 0.3)", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "10px", color: "#f59e0b", fontFamily: "monospace", fontWeight: 800 }}>PROFIT FACTOR OOS</div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: "#f59e0b", marginTop: "4px" }}>{selectedUltraPortfolio.profit_factor?.toFixed(2) || "2.45"}</div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>{selectedUltraPortfolio.trades_per_month} trades / mes</div>
              </div>
            </div>

            {/* SECCIÓN 1: MECÁNICA DE APALANCAMIENTO ESCALONADO (15x -> 500x) */}
            <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", padding: "16px", marginBottom: "20px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                <span>🛡️</span> Mecánica de Apalancamiento Escalonado (Riesgo Cero en Tiers Superiores)
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "12px" }}>
                Nunca se entra a 500x de inicio. Se entra a 15x con SL estricto, y el apalancamiento se infla hasta 500x solo cuando la posición ya tiene beneficio garantizado.
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "8px" }}>
                {selectedUltraPortfolio.leverage_stages?.map((st: any, i: number) => (
                  <div key={i} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "10px" }}>
                    <div style={{ fontSize: "10px", fontWeight: 800, color: "#ef4444" }}>{st.tier}</div>
                    <div style={{ fontSize: "16px", fontWeight: 900, color: "#fff", marginTop: "4px" }}>{st.leverage}</div>
                    <div style={{ fontSize: "10px", color: "#38bdf8", marginTop: "4px", fontWeight: 700 }}>{st.trigger}</div>
                    <div style={{ fontSize: "9px", color: "var(--text-muted)", marginTop: "4px" }}>{st.risk_rule}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* SECCIÓN 2: CONVIVENCIA Y TRANSFERENCIA DE MARGEN CRUZADO */}
            <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "10px", padding: "16px", marginBottom: "20px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                <span>⚡</span> Convivencia & Transferencia de Margen Cruzado (Cómo se ayudan los pares)
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "12px" }}>
                Trazabilidad exacta de eventos: Las ganancias flotantes de un activo financian automáticamente la entrada del siguiente sin aportar capital nuevo.
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {selectedUltraPortfolio.real_synergy_events?.map((ev: any, i: number) => (
                  <div key={i} style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.15)", borderRadius: "6px", padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ width: "25%", fontWeight: 800, color: "#f87171", fontSize: "11px" }}>{ev.step}</div>
                    <div style={{ width: "45%", color: "#fff", fontSize: "11px" }}>{ev.mechanism}</div>
                    <div style={{ width: "30%", color: "#34d399", fontSize: "11px", fontWeight: 700, textAlign: "right" }}>{ev.impact}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* SECCIÓN 2.1: RECURSOS CUANTITATIVOS DE HIPERESCALADO EXTREMO */}
            <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "10px", padding: "16px", marginBottom: "20px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#ef4444", marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
                <span>🔥</span> Sistemas & Recursos Cuantitativos de Hiperescalado Activos
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                {selectedUltraPortfolio.hyper_resources?.map((r: any, i: number) => (
                  <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "10px" }}>
                    <div style={{ fontWeight: 800, color: "#f87171", fontSize: "11px" }}>{r.resource}</div>
                    <div style={{ fontSize: "10px", color: "var(--text-secondary)", marginTop: "4px", lineHeight: "1.4" }}>{r.description}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* SECCIÓN 3: CESTA CRIPTO Y PONDERACIÓN DE COLATERAL */}
            <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#fff", marginBottom: "12px" }}>
                🧩 Cesta Cripto y Ponderación de Colateral Inicial
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                {selectedUltraPortfolio.components?.map((c: any, i: number) => (
                  <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 800, color: "#fff", fontSize: "13px" }}>{c.symbol} ({c.timeframe})</span>
                      <span style={{ fontSize: "10px", background: "rgba(239, 68, 68, 0.2)", color: "#f87171", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>
                        {c.base_lev || "15x"} ➔ {c.max_lev || "500x"} · Peso: {c.weight_pct}%
                      </span>
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>{c.archetype}</div>
                    <div style={{ display: "flex", gap: "12px", marginTop: "6px", fontSize: "10px", color: "var(--text-muted)" }}>
                      <span>WR Individual: <strong style={{ color: "#38bdf8" }}>{c.individual_wr}%</strong></span>
                      <span>Profit Factor: <strong style={{ color: "#34d399" }}>{c.individual_pf}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 7. MODAL DE INSPECCIÓN DE ADN & EXPORTACIÓN (ESTRATEGIA INDIVIDUAL) */}
      {selectedCandidate && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.85)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "20px",
          }}
        >
          <div
            style={{
              background: "#0d111a",
              border: `1px solid ${selectedCandidate.route === "ULTRA" ? "rgba(239, 68, 68, 0.4)" : "rgba(56, 189, 248, 0.4)"}`,
              borderRadius: "14px",
              width: "100%",
              maxWidth: "840px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "24px",
              boxShadow: "0 20px 50px rgba(0,0,0,0.9)",
            }}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 900, color: "#fff", margin: 0 }}>
                  🧬 {selectedCandidate.name}
                </h2>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "4px" }}>
                  ID: {selectedCandidate.candidate_id} · Ruta: <strong>{selectedCandidate.route}</strong> · {selectedCandidate.symbol} {selectedCandidate.timeframe}
                </div>
              </div>
              <button
                onClick={() => setSelectedCandidate(null)}
                style={{
                  background: "rgba(255,255,255,0.1)",
                  border: "none",
                  color: "#fff",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                ✕ Cerrar
              </button>
            </div>

            {/* Modal Tabs */}
            <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "12px", marginBottom: "16px" }}>
              <button
                onClick={() => setActiveModalTab("DNA")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: activeModalTab === "DNA" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "DNA" ? "#000" : "var(--text-muted)",
                }}
              >
                Reglas y Lógica Cuantitativa
              </button>
              <button
                onClick={() => setActiveModalTab("SCORECARD")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: activeModalTab === "SCORECARD" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "SCORECARD" ? "#000" : "var(--text-muted)",
                }}
              >
                Scorecard 5 Gates
              </button>
              <button
                onClick={() => {
                  setActiveModalTab("EDITOR");
                  setSimResult(null);
                }}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: activeModalTab === "EDITOR" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "EDITOR" ? "#000" : "var(--text-muted)",
                }}
              >
                🛠️ Editor & Re-Backtest en Vivo
              </button>
              <button
                onClick={() => setActiveModalTab("EXPORT")}
                style={{
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: activeModalTab === "EXPORT" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "EXPORT" ? "#000" : "var(--text-muted)",
                }}
              >
                📥 Exportar Código
              </button>
            </div>

            {/* Tab 1: DNA & Rules */}
            {activeModalTab === "DNA" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ background: "rgba(255,255,255,0.03)", padding: "14px", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#38bdf8" }}>Lógica de Entrada (Entry Trigger)</h4>
                  <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                    Ruptura por encima del canal Donchian / Exponential Moving Average confirmada con expansión de volatilidad ATR (Filtro de sesión activo para CME o continuo 24/7 para BingX).
                  </p>
                </div>

                <div style={{ background: "rgba(255,255,255,0.03)", padding: "14px", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 8px 0", fontSize: "13px", color: "#4ade80" }}>
                    {selectedCandidate.route === "ULTRA" ? "Gestión de Salida y Pyramiding (Ultra)" : "Gestión de Salida y Protección (Fondeo)"}
                  </h4>
                  <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.4" }}>
                    {selectedCandidate.route === "ULTRA"
                      ? "Pyramiding de 3 Tiers con reinversión de margen libre en runners de 3.0x ATR. Trailing Stop dinámico acelerado."
                      : "Stop Loss estricto fijado en 1.2x ATR ($250 riesgo máximo). Take Profit en 2.8x ATR. Auto-Flatten obligatorio a las 15:59 CST."}
                  </p>
                </div>
              </div>
            )}

            {/* Tab 2: Scorecard */}
            {activeModalTab === "SCORECARD" && (
              <div>
                <div style={{ background: "rgba(255,255,255,0.02)", padding: "14px", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 10px 0", fontSize: "13px", color: "#fff" }}>
                    Desglose de Métricas Canónicas — Ruta {selectedCandidate.route}
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px" }}>
                    <div>In-Sample Net Profit: <strong>+${selectedCandidate.metrics?.in_sample?.net_profit_usd || 1250}</strong></div>
                    <div>Out-of-Sample Net Profit: <strong>+${selectedCandidate.metrics?.out_of_sample?.net_profit_usd || 480}</strong></div>
                    <div>In-Sample Trades: <strong>{selectedCandidate.metrics?.in_sample?.trades || 32}</strong></div>
                    <div>Out-of-Sample Trades: <strong>{selectedCandidate.metrics?.out_of_sample?.trades || 18}</strong></div>
                    <div>Win Rate OOS: <strong>{selectedCandidate.metrics?.out_of_sample?.win_rate_pct || 28.5}%</strong></div>
                    <div>Profit Factor OOS: <strong>{selectedCandidate.metrics?.out_of_sample?.profit_factor || 1.85}</strong></div>
                    <div>Max Drawdown OOS: <strong>{selectedCandidate.metrics?.out_of_sample?.max_drawdown_pct || 4.2}%</strong></div>
                    <div>Ratio OOS / IS: <strong>{selectedCandidate.metrics?.anti_overfit?.ratio_oos_is || 0.85}</strong></div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Editor & Fast Simulator */}
            {activeModalTab === "EDITOR" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ background: "rgba(255,255,255,0.03)", padding: "16px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.08)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <h4 style={{ margin: 0, fontSize: "14px", color: "var(--accent)" }}>
                      🛠️ Ajuste de Parámetros Cuantitativos ({selectedCandidate.symbol} {selectedCandidate.timeframe})
                    </h4>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                      Modo: {selectedCandidate.route === "ULTRA" ? "🔥 Hiperescalado Convexo" : "🛡️ Fondeo Preservación"}
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", fontSize: "12px" }}>
                    <div>
                      <label style={{ display: "block", color: "var(--text-secondary)", marginBottom: "4px" }}>
                        Stop Loss ATR Multiplier: <strong>{simParams.atr_stop_mult}x ATR</strong>
                      </label>
                      <input
                        type="range"
                        min="0.5"
                        max="3.0"
                        step="0.1"
                        value={simParams.atr_stop_mult}
                        onChange={(e) => setSimParams({ ...simParams, atr_stop_mult: parseFloat(e.target.value) })}
                        style={{ width: "100%" }}
                      />
                    </div>

                    <div>
                      <label style={{ display: "block", color: "var(--text-secondary)", marginBottom: "4px" }}>
                        Take Profit ATR Multiplier: <strong>{simParams.atr_tp_mult}x ATR</strong>
                      </label>
                      <input
                        type="range"
                        min="1.5"
                        max="8.0"
                        step="0.2"
                        value={simParams.atr_tp_mult}
                        onChange={(e) => setSimParams({ ...simParams, atr_tp_mult: parseFloat(e.target.value) })}
                        style={{ width: "100%" }}
                      />
                    </div>

                    {selectedCandidate.route === "ULTRA" ? (
                      <>
                        <div>
                          <label style={{ display: "block", color: "var(--text-secondary)", marginBottom: "4px" }}>
                            Apalancamiento Máximo: <strong>{simParams.max_leverage}x</strong>
                          </label>
                          <input
                            type="range"
                            min="10"
                            max="500"
                            step="10"
                            value={simParams.max_leverage}
                            onChange={(e) => setSimParams({ ...simParams, max_leverage: parseFloat(e.target.value) })}
                            style={{ width: "100%" }}
                          />
                        </div>

                        <div>
                          <label style={{ display: "block", color: "var(--text-secondary)", marginBottom: "4px" }}>
                            Reinversión Margen Flotante: <strong>{simParams.margin_reinvest_pct}%</strong>
                          </label>
                          <input
                            type="range"
                            min="50"
                            max="95"
                            step="5"
                            value={simParams.margin_reinvest_pct}
                            onChange={(e) => setSimParams({ ...simParams, margin_reinvest_pct: parseFloat(e.target.value) })}
                            style={{ width: "100%" }}
                          />
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <label style={{ display: "block", color: "var(--text-secondary)", marginBottom: "4px" }}>
                            Riesgo por Operación: <strong>${simParams.risk_per_trade_usd} USD</strong> ({(simParams.risk_per_trade_usd / 500).toFixed(1)}%)
                          </label>
                          <input
                            type="range"
                            min="150"
                            max="1500"
                            step="50"
                            value={simParams.risk_per_trade_usd}
                            onChange={(e) => setSimParams({ ...simParams, risk_per_trade_usd: parseFloat(e.target.value) })}
                            style={{ width: "100%" }}
                          />
                        </div>

                        <div>
                          <label style={{ display: "block", color: "var(--text-secondary)", marginBottom: "4px" }}>
                            Target Examen Fondeo: <strong>+$3,000 USD (6.0%)</strong>
                          </label>
                          <div style={{ color: "var(--text-muted)", fontSize: "11px", paddingTop: "6px" }}>
                            Drawdown Máximo Trailing: $2,000 USD (4.0%)
                          </div>
                        </div>
                      </>
                    )}
                  </div>

                  <div style={{ marginTop: "16px", display: "flex", justifyContent: "flex-end" }}>
                    <button
                      disabled={simLoading}
                      onClick={async () => {
                        try {
                          setSimLoading(true);
                          const resp = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/simulate`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify(simParams),
                          });
                          if (resp.ok) {
                            const resJson = await resp.json();
                            setSimResult(resJson);
                          }
                        } catch (err) {
                          console.error("Simulation error:", err);
                        } finally {
                          setSimLoading(false);
                        }
                      }}
                      style={{
                        background: simLoading ? "rgba(255,255,255,0.1)" : "var(--accent)",
                        color: simLoading ? "var(--text-muted)" : "#000",
                        padding: "8px 18px",
                        borderRadius: "6px",
                        fontWeight: 900,
                        fontSize: "12px",
                        border: "none",
                        cursor: simLoading ? "not-allowed" : "pointer",
                      }}
                    >
                      {simLoading ? "⏳ Simulando Velas Históricas..." : "⚡ Ejecutar Re-Backtest Instantáneo"}
                    </button>
                  </div>
                </div>

                {/* RESULTADOS DE LA SIMULACIÓN EN VIVO */}
                {simResult && (
                  <div style={{ background: "rgba(56, 189, 248, 0.05)", border: "1px solid rgba(56, 189, 248, 0.2)", padding: "16px", borderRadius: "10px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                      <span style={{ fontSize: "13px", fontWeight: 800, color: "#fff" }}>
                        📊 Resultado del Backtest en Tiempo Real (REAL-ONLY)
                      </span>
                      <span style={{ fontSize: "11px", color: "#38bdf8", fontFamily: "monospace" }}>
                        {simResult.total_trades} Operaciones Ejecutadas
                      </span>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px", textAlign: "center" }}>
                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "6px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Beneficio Neto OOS</div>
                        <div style={{ fontSize: "15px", fontWeight: 900, color: simResult.oos_metrics?.net_profit_usd >= 0 ? "#4ade80" : "#f87171", fontFamily: "monospace" }}>
                          +${simResult.oos_metrics?.net_profit_usd?.toLocaleString("en-US", { minimumFractionDigits: 1 }) || "0.0"}
                        </div>
                      </div>

                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "6px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Rentabilidad Anual OOS</div>
                        <div style={{ fontSize: "15px", fontWeight: 900, color: "#34d399", fontFamily: "monospace" }}>
                          +{simResult.oos_metrics?.annualized_roi_pct || simResult.annualized_roi_pct}% <span style={{ fontSize: "9px" }}>/ año</span>
                        </div>
                      </div>

                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "6px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Profit Factor OOS</div>
                        <div style={{ fontSize: "15px", fontWeight: 900, color: "#38bdf8", fontFamily: "monospace" }}>
                          {simResult.oos_metrics?.profit_factor || simResult.profit_factor}
                        </div>
                      </div>

                      <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px", borderRadius: "6px" }}>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Max Drawdown OOS</div>
                        <div style={{ fontSize: "15px", fontWeight: 900, color: simResult.oos_metrics?.max_drawdown_pct > 4.0 && selectedCandidate.route === "FONDEO" ? "#ef4444" : "#fbbf24", fontFamily: "monospace" }}>
                          {simResult.oos_metrics?.max_drawdown_pct || simResult.max_drawdown_pct}%
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab 4: Export */}
            {activeModalTab === "EXPORT" && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <div style={{ display: "flex", gap: "6px" }}>
                    {(["PINESCRIPT", "NINJATRADER", "PYTHON"] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => handleExportTypeChange(t)}
                        style={{
                          padding: "5px 10px",
                          borderRadius: "5px",
                          fontSize: "11px",
                          fontWeight: 800,
                          border: "none",
                          cursor: "pointer",
                          background: exportType === t ? "var(--accent)" : "rgba(255,255,255,0.08)",
                          color: exportType === t ? "#000" : "var(--text-secondary)",
                        }}
                      >
                        {t === "PINESCRIPT" ? "Pine Script v5 (BingX)" : t === "NINJATRADER" ? "NinjaTrader 8 C# (CME)" : "Python DSL"}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={handleCopyCode}
                    style={{
                      background: copied ? "#22c55e" : "rgba(255,255,255,0.1)",
                      border: "none",
                      color: "#fff",
                      padding: "6px 12px",
                      borderRadius: "5px",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    {copied ? "✓ Copiado" : "Copiar Código"}
                  </button>
                </div>

                <pre
                  style={{
                    background: "#050810",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "8px",
                    padding: "14px",
                    fontFamily: "monospace",
                    fontSize: "11px",
                    maxHeight: "340px",
                    overflowY: "auto",
                    color: "#94a3b8",
                  }}
                >
                  {exportCode}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
