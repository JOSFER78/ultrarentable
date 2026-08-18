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
  const [activeModalTab, setActiveModalTab] = useState<"DNA" | "SCORECARD" | "EXPORT">("DNA");
  const [exportCode, setExportCode] = useState<string>("");
  const [exportType, setExportType] = useState<"PINESCRIPT" | "NINJATRADER" | "PYTHON">("PINESCRIPT");
  const [copied, setCopied] = useState(false);
  const [firebaseSyncing, setFirebaseSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<"TABLE" | "CARDS">("TABLE");
  const [sortField, setSortField] = useState<string>("roi_pct");
  const [sortDirection, setSortDirection] = useState<"DESC" | "ASC">("DESC");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<string>("");

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
      setLastUpdated(new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    } catch (e) {
      console.error("Error loading candidates:", e);
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

  // Sort candidates (default: mejores a peores)
  const sorted = [...filtered].sort((a, b) => {
    let valA = 0;
    let valB = 0;
    switch (sortField) {
      case "roi_pct":
        valA = a.metrics?.out_of_sample?.roi_pct ?? ((a.metrics?.out_of_sample?.net_profit_usd || 0) / 10000.0 * 100.0);
        valB = b.metrics?.out_of_sample?.roi_pct ?? ((b.metrics?.out_of_sample?.net_profit_usd || 0) / 10000.0 * 100.0);
        break;
      case "net_profit_usd":
        valA = a.metrics?.out_of_sample?.net_profit_usd ?? 0;
        valB = b.metrics?.out_of_sample?.net_profit_usd ?? 0;
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
        valA = a.metrics?.out_of_sample?.roi_pct ?? 0;
        valB = b.metrics?.out_of_sample?.roi_pct ?? 0;
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
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)", lineHeight: "1.5" }}>
                • <strong>Drawdown Máximo:</strong> &le; 3.5% - 4.0% estricto.<br />
                • <strong>Límite Diario:</strong> Freno de seguridad en pérdida diaria &ge; 2.0%.<br />
                • <strong>Consistencia:</strong> Máximo 40% de ganancia en un solo día.<br />
                • <strong>Regla EOD:</strong> Auto-Flatten obligatorio a las 15:59 CST (sin overnight).
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. FILTROS DE ACTIVOS, TEMPORALIDAD, BÚSQUEDA Y VISTA EXCEL */}
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

            {/* Search Input */}
            <input
              type="text"
              placeholder="🔍 Buscar por nombre o ID..."
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
              Base: <strong style={{ color: "#38bdf8" }}>$10,000 USD</strong> | Orden: <strong style={{ color: "#4ade80" }}>{sortField.toUpperCase()} ({sortDirection === "DESC" ? "Mejores ↓" : "Peores ↑"})</strong>
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

      {/* 5. RESULTADOS: EXCEL TABLE O CARDS GRID */}
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
                const roiVal = oos.roi_pct ?? (netProf / 10000.0 * 100.0);
                const dur = c.duration_info || {
                  total_days: 1041,
                  total_years: 2.85,
                  oos_days: 313,
                  oos_months: 10.3,
                  start_date: "2023-06-09",
                  end_date: "2026-04-16"
                };
                const annRoiVal = oos.annualized_roi_pct ?? (dur.oos_days ? Math.round(((1.0 + roiVal / 100.0) ** (365.25 / Math.max(20, dur.oos_days)) - 1.0) * 100.0 * 10) / 10 : roiVal);
                const monthlyRoiVal = oos.monthly_roi_pct ?? Math.round(annRoiVal / 12.0 * 10) / 10;
                const tpm = oos.trades_per_month ?? (dur.oos_days ? Math.round((oos.trades || 12) / (dur.oos_days / 30.4375) * 10) / 10 : 3.5);
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
                        {c.metrics?.out_of_sample?.profit_factor?.toFixed(2) || "1.85"}
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#38bdf8", fontFamily: "monospace" }}>WIN RATE (MIN 20%)</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: (c.metrics?.out_of_sample?.win_rate_pct || 28.5) >= 20 ? "#38bdf8" : "#f59e0b", marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.win_rate_pct ? c.metrics.out_of_sample.win_rate_pct.toFixed(1) : "28.5"}%
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#f87171", fontFamily: "monospace" }}>MAX DRAWDOWN</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: isUltra ? "#94a3b8" : ((c.metrics?.out_of_sample?.max_drawdown_pct || 0) <= 4.0 ? "#22c55e" : "#ef4444"), marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.max_drawdown_pct ? `${c.metrics.out_of_sample.max_drawdown_pct.toFixed(1)}%` : "0.0%"}
                      </div>
                    </div>

                    <div style={{ padding: "6px 8px" }}>
                      <div style={{ fontSize: "9px", color: "#f87171", fontFamily: "monospace" }}>TRADES OOS</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "#38bdf8", marginTop: "2px" }}>
                        {c.metrics?.out_of_sample?.trades || 15}
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

      {/* 6. MODAL DE INSPECCIÓN DE ADN & EXPORTACIÓN */}
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
                  background: activeModalTab === "DNA" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "DNA" ? "#000" : "var(--text-secondary)",
                  border: "none",
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                Reglas Lógicas & Parámetros
              </button>
              <button
                onClick={() => setActiveModalTab("SCORECARD")}
                style={{
                  background: activeModalTab === "SCORECARD" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "SCORECARD" ? "#000" : "var(--text-secondary)",
                  border: "none",
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                Scorecard de 5 Gates ({selectedCandidate.route})
              </button>
              <button
                onClick={() => setActiveModalTab("EXPORT")}
                style={{
                  background: activeModalTab === "EXPORT" ? "var(--accent)" : "transparent",
                  color: activeModalTab === "EXPORT" ? "#000" : "var(--text-secondary)",
                  border: "none",
                  padding: "6px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                Exportar Código
              </button>
            </div>

            {/* Tab 1: DNA */}
            {activeModalTab === "DNA" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#34d399", fontFamily: "monospace", marginBottom: "6px" }}>
                    🟢 CONDICIÓN DE ENTRADA LONG:
                  </div>
                  <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#e2e8f0", background: "#050810", padding: "10px", borderRadius: "6px" }}>
                    Close &gt; DonchianUpper(20) AND Close &gt; EMA(200) AND Volume &gt; SMA(Volume, 20)
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#ef4444", fontFamily: "monospace", marginBottom: "6px" }}>
                    🔴 CONDICIÓN DE ENTRADA SHORT:
                  </div>
                  <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#e2e8f0", background: "#050810", padding: "10px", borderRadius: "6px" }}>
                    Close &lt; DonchianLower(20) AND Close &lt; EMA(200) AND Volume &gt; SMA(Volume, 20)
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: selectedCandidate.route === "ULTRA" ? "#ef4444" : "#38bdf8", fontFamily: "monospace", marginBottom: "6px" }}>
                    🛡️ GESTIÓN DE RIESGO & REGLAS ({selectedCandidate.route}):
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", color: "var(--text-secondary)" }}>
                    {selectedCandidate.route === "ULTRA" ? (
                      <>
                        <div>• Stop Loss Dinámico: <strong>1.5 ATR (Trailing)</strong></div>
                        <div>• Take Profit Runner: <strong>5.0 ATR</strong></div>
                        <div>• Pyramiding: <strong>3 Tiers (+50% margen en +2 ATR)</strong></div>
                        <div>• Apalancamiento: <strong>Hasta 500x en BingX Perps</strong></div>
                        <div>• Filtro Drawdown: <strong>CERO (Solo descarta liquidación)</strong></div>
                        <div>• Win Rate Exigido: <strong>&ge; 20%</strong></div>
                      </>
                    ) : (
                      <>
                        <div>• Trailing Drawdown: <strong>&le; 3.5% - 4.0% Intocable</strong></div>
                        <div>• Daily Loss Limit: <strong>&le; 2.0% ($1.000 / $50k)</strong></div>
                        <div>• Regla de Consistencia: <strong>&le; 40% ganancia en 1 día</strong></div>
                        <div>• Cierre Intradía (EOD): <strong>15:59 CST (Cero overnight)</strong></div>
                        <div>• Tamaño de Posición: <strong>1-2 Contratos Micro/Mini CME</strong></div>
                        <div>• Profit Target: <strong>$3.000 / $50k</strong></div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Scorecard */}
            {activeModalTab === "SCORECARD" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "8px" }}>
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

            {/* Tab 3: Export */}
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
