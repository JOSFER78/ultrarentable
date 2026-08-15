"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";

interface Candidate {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  dataset_id: string;
  status: string;
  status_reason: string;
  metrics: {
    in_sample: {
      net_profit_usd: number;
      trades: number;
      profit_factor: number;
      max_drawdown_pct: number;
    };
    out_of_sample: {
      net_profit_usd: number;
      trades: number;
      profit_factor: number;
      max_drawdown_pct: number;
    };
    anti_overfit: {
      ratio_oos_is: number;
      wfo_pass_pct?: number;
      monte_carlo_score?: number;
    };
  };
  created_at: string;
}

interface VerificationGate {
  gate_id: string;
  name: string;
  passed: boolean;
  threshold: string;
  measured_value: string;
  detail: string;
}

interface VerificationReport {
  candidate_id: string;
  name: string;
  route: string;
  total_score_pct: number;
  is_approved_for_live: boolean;
  status_verdict: string;
  gates: VerificationGate[];
}

interface SearchStatus {
  is_running: boolean;
  stats: {
    total_evaluated: number;
    total_accepted: number;
    current_cell: string;
    start_time: string | null;
    last_candidate_found: string | null;
  };
  supported_timeframes: string[];
  supported_asset_classes: string[];
}

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  
  // Filter States
  const [routeFilter, setRouteFilter] = useState<string>("ALL");
  const [symbolFilter, setSymbolFilter] = useState<string>("ALL");
  const [timeframeFilter, setTimeframeFilter] = useState<string>("ALL");

  // Search Engine States
  const [searchStatus, setSearchStatus] = useState<SearchStatus | null>(null);
  const [triggeringSearch, setTriggeringSearch] = useState(false);

  // Verification and Export States
  const [verifying, setVerifying] = useState(false);
  const [verificationReport, setVerificationReport] = useState<VerificationReport | null>(null);
  const [exportModal, setExportModal] = useState<{ title: string; language: string; filename: string; code: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const loadCandidates = useCallback(() => {
    let url = "/api/v1/candidates";
    const params = new URLSearchParams();
    if (routeFilter !== "ALL") params.append("route", routeFilter);
    if (symbolFilter !== "ALL") params.append("symbol", symbolFilter);
    if (timeframeFilter !== "ALL") params.append("timeframe", timeframeFilter);
    
    const qs = params.toString();
    if (qs) url += `?${qs}`;

    fetch(url)
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCandidates(data);
          if (data.length > 0) {
            setSelectedCandidate((prev) => {
              if (prev && data.some(d => d.candidate_id === prev.candidate_id)) return prev;
              return data[0];
            });
          } else {
            setSelectedCandidate(null);
          }
        }
      })
      .catch((err) => console.error("Error loading candidates:", err));
  }, [routeFilter, symbolFilter, timeframeFilter]);

  const loadSearchStatus = useCallback(() => {
    fetch("/api/v1/search/status")
      .then((r) => r.json())
      .then((data) => setSearchStatus(data))
      .catch((err) => console.error("Error loading search status:", err));
  }, []);

  useEffect(() => {
    loadCandidates();
    loadSearchStatus();
    const interval = setInterval(() => {
      loadSearchStatus();
      loadCandidates();
    }, 4000);
    return () => clearInterval(interval);
  }, [loadCandidates, loadSearchStatus]);

  const handleTriggerSearch = async (tfs?: string[]) => {
    setTriggeringSearch(true);
    try {
      await fetch("/api/v1/search/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          timeframes: tfs || ["1m", "5m", "15m", "1h", "4h"],
          max_variations_per_cell: 16
        })
      });
      loadSearchStatus();
    } catch (err) {
      console.error("Error triggering search:", err);
    } finally {
      setTriggeringSearch(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RECHAZADA_FONDEO_DD":
        return { bg: "rgba(239, 68, 68, 0.2)", color: "#fca5a5", border: "1px solid #ef4444", text: "RECHAZADA (DD > 4%)" };
      case "INVESTIGACION_BTC":
        return { bg: "rgba(245, 158, 11, 0.2)", color: "#fde68a", border: "1px solid #f59e0b", text: "INVESTIGACIÓN BTC" };
      case "CANDIDATA_FONDEO":
        return { bg: "rgba(34, 197, 94, 0.2)", color: "#86efac", border: "1px solid #22c55e", text: "CANDIDATA FONDEO" };
      case "CANDIDATA_ULTRA":
        return { bg: "rgba(168, 85, 247, 0.2)", color: "#d8b4fe", border: "1px solid #a855f7", text: "CANDIDATA ULTRA" };
      default:
        return { bg: "rgba(255, 255, 255, 0.1)", color: "var(--text-muted)", border: "1px solid var(--border)", text: status };
    }
  };

  const getTimeframeBadge = (tf: string) => {
    switch (tf) {
      case "1m":
        return { bg: "rgba(236, 72, 153, 0.2)", color: "#f472b6", border: "1px solid #ec4899" };
      case "5m":
        return { bg: "rgba(6, 182, 212, 0.2)", color: "#67e8f9", border: "1px solid #06b6d4" };
      case "15m":
        return { bg: "rgba(59, 130, 246, 0.2)", color: "#93c5fd", border: "1px solid #3b82f6" };
      case "1h":
        return { bg: "rgba(245, 158, 11, 0.2)", color: "#fcd34d", border: "1px solid #f59e0b" };
      case "4h":
        return { bg: "rgba(16, 185, 129, 0.2)", color: "#6ee7b7", border: "1px solid #10b981" };
      default:
        return { bg: "rgba(255, 255, 255, 0.1)", color: "var(--text-muted)", border: "1px solid var(--border)" };
    }
  };

  const handleVerifyRobustness = async () => {
    if (!selectedCandidate) return;
    setVerifying(true);
    setVerificationReport(null);
    try {
      const res = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/verify-robustness`, {
        method: "POST"
      });
      const data = await res.json();
      setVerificationReport(data);
    } catch (err) {
      console.error("Error verifying robustness:", err);
    } finally {
      setVerifying(false);
    }
  };

  const handleExportTradingView = async () => {
    if (!selectedCandidate) return;
    try {
      const res = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/export/tradingview`);
      const data = await res.json();
      setExportModal({
        title: `📈 Pine Script v5 para TradingView — ${selectedCandidate.name}`,
        language: data.language,
        filename: data.filename,
        code: data.code
      });
    } catch (err) {
      console.error("Error exporting TradingView:", err);
    }
  };

  const handleExportNinjaTrader = async () => {
    if (!selectedCandidate) return;
    try {
      const res = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/export/ninjatrader`);
      const data = await res.json();
      setExportModal({
        title: `⚙️ C# NinjaScript para NinjaTrader 8 — ${selectedCandidate.name}`,
        language: data.language,
        filename: data.filename,
        code: data.code
      });
    } catch (err) {
      console.error("Error exporting NinjaTrader:", err);
    }
  };

  const handleCopyCode = () => {
    if (exportModal?.code) {
      navigator.clipboard.writeText(exportModal.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1440px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", fontFamily: "monospace" }}>
              MULTI-MARKET STRATEGY MATRIX
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
            🧭 Explorador Cuantitativo Multi-Mercado & Anti-Overfit
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Búsqueda exhaustiva y validación Zero-Trust (5 Gates) en Forex, Índices y Cripto en temporalidades <strong style={{ color: "#f472b6" }}>1m</strong>, <strong style={{ color: "#67e8f9" }}>5m</strong>, <strong style={{ color: "#93c5fd" }}>15m</strong>, <strong style={{ color: "#fcd34d" }}>1h</strong> y <strong style={{ color: "#6ee7b7" }}>4h</strong>.
          </p>
        </div>

        {/* SEARCH TRIGGER BUTTONS */}
        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <button
            onClick={() => handleTriggerSearch()}
            disabled={triggeringSearch || searchStatus?.is_running}
            style={{
              padding: "10px 18px",
              borderRadius: "8px",
              fontWeight: 800,
              fontSize: "13px",
              cursor: searchStatus?.is_running ? "not-allowed" : "pointer",
              background: searchStatus?.is_running ? "rgba(99, 102, 241, 0.2)" : "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
              color: "#ffffff",
              border: "1px solid rgba(255,255,255,0.2)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 4px 14px rgba(99, 102, 241, 0.35)"
            }}
          >
            {searchStatus?.is_running ? "⚡ Explorando Universo..." : "🚀 Lanzar Búsqueda en Todo el Universo"}
          </button>
        </div>
      </div>

      {/* UNIVERSE SEARCH TELEMETRY CARD */}
      <div style={{
        background: "rgba(15, 23, 42, 0.65)",
        border: searchStatus?.is_running ? "1px solid #6366f1" : "1px solid var(--border)",
        borderRadius: "10px",
        padding: "14px 18px",
        marginBottom: "20px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "16px"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{
            width: "12px",
            height: "12px",
            borderRadius: "50%",
            background: searchStatus?.is_running ? "#22c55e" : "#94a3b8",
            boxShadow: searchStatus?.is_running ? "0 0 10px #22c55e" : "none"
          }} />
          <div>
            <div style={{ fontSize: "12px", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              {searchStatus?.is_running ? `🔍 PROCESANDO: ${searchStatus.stats.current_cell}` : "🟢 MOTOR DE DESCUBRIMIENTO LISTO"}
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              {searchStatus?.stats.last_candidate_found ? `Última candidata guardada: ${searchStatus.stats.last_candidate_found}` : "19 celdas canónicas configuradas (BTC, ETH, SOL, EURUSD, GBPUSD, NQ, ES)"}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "20px", alignItems: "center" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>EVALUADAS</div>
            <div style={{ fontSize: "16px", fontWeight: 900, fontFamily: "monospace", color: "#93c5fd" }}>
              {searchStatus?.stats.total_evaluated || 0}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>GUARDADAS EN DB</div>
            <div style={{ fontSize: "16px", fontWeight: 900, fontFamily: "monospace", color: "#86efac" }}>
              {searchStatus?.stats.total_accepted || candidates.length}
            </div>
          </div>
        </div>
      </div>

      {/* FILTROS MULTI-DIMENSIONALES */}
      <div style={{
        background: "var(--bg-panel)",
        border: "1px solid var(--border)",
        borderRadius: "10px",
        padding: "14px 16px",
        marginBottom: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px"
      }}>
        {/* FILTRO DE RUTA */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", minWidth: "90px", textTransform: "uppercase" }}>
            Ruta:
          </span>
          {["ALL", "ULTRA", "FONDEO"].map((r) => (
            <button
              key={r}
              onClick={() => setRouteFilter(r)}
              style={{
                padding: "4px 12px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer",
                background: routeFilter === r ? (r === "ULTRA" ? "#a855f7" : r === "FONDEO" ? "#3b82f6" : "var(--accent)") : "rgba(255,255,255,0.05)",
                color: routeFilter === r ? "#ffffff" : "var(--text-muted)",
                border: routeFilter === r ? "none" : "1px solid var(--border)"
              }}
            >
              {r === "ALL" ? "Todas las Rutas" : r === "ULTRA" ? "🚀 ULTRA (Crypto Perps)" : "🏦 FONDEO (CME / Prop)"}
            </button>
          ))}
        </div>

        {/* FILTRO DE TEMPORALIDAD */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", minWidth: "90px", textTransform: "uppercase" }}>
            Temporalidad:
          </span>
          {["ALL", "1m", "5m", "15m", "1h", "4h"].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframeFilter(tf)}
              style={{
                padding: "4px 12px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 800,
                fontFamily: "monospace",
                cursor: "pointer",
                background: timeframeFilter === tf ? "var(--text-main)" : "rgba(255,255,255,0.05)",
                color: timeframeFilter === tf ? "#000000" : "var(--text-muted)",
                border: timeframeFilter === tf ? "none" : "1px solid var(--border)"
              }}
            >
              {tf === "ALL" ? "Todas" : tf}
            </button>
          ))}
        </div>

        {/* FILTRO DE ACTIVO */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", minWidth: "90px", textTransform: "uppercase" }}>
            Activo:
          </span>
          {["ALL", "BTC", "ETH", "SOL", "EURUSD", "GBPUSD", "NQ", "ES"].map((sym) => (
            <button
              key={sym}
              onClick={() => setSymbolFilter(sym)}
              style={{
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer",
                background: symbolFilter === sym ? "#6366f1" : "rgba(255,255,255,0.05)",
                color: symbolFilter === sym ? "#ffffff" : "var(--text-muted)",
                border: symbolFilter === sym ? "none" : "1px solid var(--border)"
              }}
            >
              {sym === "ALL" ? "Todos los Activos" : sym}
            </button>
          ))}
        </div>
      </div>

      {/* GRID CON LISTA Y DETALLE */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 480px", gap: "24px" }}>
        
        {/* TABLA DE ESTRATEGIAS */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)", background: "rgba(0,0,0,0.2)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "12px", fontWeight: 800, fontFamily: "monospace" }}>ESTRATEGIAS CANDIDATAS ({candidates.length})</span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Ordenadas por fecha reciente</span>
          </div>

          <div style={{ overflowX: "auto", maxHeight: "650px", overflowY: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", background: "rgba(255,255,255,0.02)", position: "sticky", top: 0, zIndex: 5 }}>
                  <th style={{ padding: "10px 14px" }}>Estrategia</th>
                  <th style={{ padding: "10px 14px" }}>Ruta</th>
                  <th style={{ padding: "10px 14px" }}>TF</th>
                  <th style={{ padding: "10px 14px" }}>IS PF (Trades)</th>
                  <th style={{ padding: "10px 14px" }}>OOS PF (Trades)</th>
                  <th style={{ padding: "10px 14px" }}>Ratio OOS/IS</th>
                  <th style={{ padding: "10px 14px" }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ padding: "30px", textAlign: "center", color: "var(--text-muted)" }}>
                      No se encontraron estrategias con los filtros seleccionados. Haz clic en <strong>🚀 Lanzar Búsqueda</strong> para explorar nuevos candidatos.
                    </td>
                  </tr>
                ) : (
                  candidates.map((c) => {
                    const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
                    const badge = getStatusBadge(c.status);
                    const tfBadge = getTimeframeBadge(c.timeframe);
                    const ratio = c.metrics.anti_overfit.ratio_oos_is || 0;
                    return (
                      <tr
                        key={c.candidate_id}
                        onClick={() => {
                          setSelectedCandidate(c);
                          setVerificationReport(null);
                        }}
                        style={{
                          borderBottom: "1px solid var(--border)",
                          cursor: "pointer",
                          background: isSelected ? "rgba(99, 102, 241, 0.15)" : "transparent",
                          transition: "background 0.15s"
                        }}
                      >
                        <td style={{ padding: "10px 14px", fontWeight: 700 }}>
                          <div>{c.name}</div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>{c.symbol}</div>
                        </td>
                        <td style={{ padding: "10px 14px" }}>
                          <span style={{
                            fontSize: "10px",
                            fontWeight: 800,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: c.route === "ULTRA" ? "rgba(168, 85, 247, 0.2)" : "rgba(59, 130, 246, 0.2)",
                            color: c.route === "ULTRA" ? "#c084fc" : "#93c5fd",
                            border: c.route === "ULTRA" ? "1px solid #a855f7" : "1px solid #3b82f6"
                          }}>
                            {c.route}
                          </span>
                        </td>
                        <td style={{ padding: "10px 14px" }}>
                          <span style={{
                            fontSize: "10px",
                            fontWeight: 800,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: tfBadge.bg,
                            color: tfBadge.color,
                            border: tfBadge.border,
                            fontFamily: "monospace"
                          }}>
                            {c.timeframe}
                          </span>
                        </td>
                        <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 700 }}>
                          {c.metrics.in_sample.profit_factor.toFixed(2)}{" "}
                          <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 400 }}>({c.metrics.in_sample.trades})</span>
                        </td>
                        <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 700 }}>
                          {c.metrics.out_of_sample.profit_factor.toFixed(2)}{" "}
                          <span style={{ fontSize: "10px", color: "var(--text-muted)", fontWeight: 400 }}>({c.metrics.out_of_sample.trades})</span>
                        </td>
                        <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 800, color: ratio >= 0.70 ? "#22c55e" : ratio >= 0.50 ? "#f59e0b" : "#ef4444" }}>
                          {ratio.toFixed(2)}x
                        </td>
                        <td style={{ padding: "10px 14px" }}>
                          <span style={{
                            fontSize: "10px",
                            fontWeight: 800,
                            padding: "3px 8px",
                            borderRadius: "4px",
                            background: badge.bg,
                            color: badge.color,
                            border: badge.border,
                            fontFamily: "monospace",
                            whiteSpace: "nowrap"
                          }}>
                            {badge.text}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* DETALLE Y ACCIONES DE LA ESTRATEGIA SELECCIONADA */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {selectedCandidate ? (
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "14px" }}>
                <div>
                  <span style={{
                    fontSize: "10px",
                    fontWeight: 800,
                    padding: "2px 6px",
                    borderRadius: "4px",
                    background: selectedCandidate.route === "ULTRA" ? "rgba(168, 85, 247, 0.2)" : "rgba(59, 130, 246, 0.2)",
                    color: selectedCandidate.route === "ULTRA" ? "#c084fc" : "#93c5fd",
                    border: selectedCandidate.route === "ULTRA" ? "1px solid #a855f7" : "1px solid #3b82f6"
                  }}>
                    {selectedCandidate.route}
                  </span>
                  <h3 style={{ fontSize: "16px", fontWeight: 800, margin: "6px 0 2px 0" }}>{selectedCandidate.name}</h3>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                    ID: {selectedCandidate.candidate_id}
                  </div>
                </div>
                <span style={{
                  fontSize: "10px",
                  fontWeight: 800,
                  padding: "3px 8px",
                  borderRadius: "4px",
                  background: getStatusBadge(selectedCandidate.status).bg,
                  color: getStatusBadge(selectedCandidate.status).color,
                  border: getStatusBadge(selectedCandidate.status).border,
                  fontFamily: "monospace"
                }}>
                  {getStatusBadge(selectedCandidate.status).text}
                </span>
              </div>

              {/* ACTION TOOLBAR: VERIFICAR Y EXPORTAR CÓDIGO */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "16px" }}>
                <button
                  onClick={handleVerifyRobustness}
                  disabled={verifying}
                  style={{
                    padding: "10px 12px",
                    borderRadius: "6px",
                    background: "rgba(99, 102, 241, 0.2)",
                    border: "1px solid #6366f1",
                    color: "#a5b4fc",
                    fontWeight: 700,
                    fontSize: "11px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  {verifying ? "⏳ Evaluando..." : "🛡️ Verificar 5 Gates"}
                </button>
                <button
                  onClick={handleExportTradingView}
                  style={{
                    padding: "10px 12px",
                    borderRadius: "6px",
                    background: "rgba(34, 197, 94, 0.15)",
                    border: "1px solid #22c55e",
                    color: "#86efac",
                    fontWeight: 700,
                    fontSize: "11px",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  📈 Pine Script (TV v5)
                </button>
              </div>

              <button
                onClick={handleExportNinjaTrader}
                style={{
                  width: "100%",
                  padding: "9px 12px",
                  marginBottom: "16px",
                  borderRadius: "6px",
                  background: "rgba(245, 158, 11, 0.15)",
                  border: "1px solid #f59e0b",
                  color: "#fde68a",
                  fontWeight: 700,
                  fontSize: "11px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "6px"
                }}
              >
                ⚙️ Exportar NinjaTrader 8 (C#)
              </button>

              {/* REPORT CARD MODAL SI SE HA VERIFICADO */}
              {verificationReport && (
                <div style={{
                  background: "rgba(0,0,0,0.4)",
                  border: verificationReport.is_approved_for_live ? "1px solid #22c55e" : "1px solid #ef4444",
                  borderRadius: "8px",
                  padding: "14px",
                  marginBottom: "16px"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <span style={{ fontSize: "12px", fontWeight: 800 }}>RESULTADO 5 GATES</span>
                    <span style={{
                      fontSize: "12px",
                      fontWeight: 900,
                      color: verificationReport.is_approved_for_live ? "#22c55e" : "#ef4444",
                      fontFamily: "monospace"
                    }}>
                      {verificationReport.total_score_pct}% PUNTOS
                    </span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {verificationReport.gates.map((g) => (
                      <div key={g.gate_id} style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "4px" }}>
                        <div>
                          <span>{g.passed ? "✅" : "❌"} {g.name}</span>
                          <div style={{ fontSize: "9px", color: "var(--text-muted)" }}>{g.detail}</div>
                        </div>
                        <span style={{ fontFamily: "monospace", fontWeight: 700 }}>{g.measured_value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* METRICS DETAIL */}
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                <div style={{ background: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#93c5fd", marginBottom: "8px" }}>
                    IN-SAMPLE (70% HISTÓRICO)
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Net Profit:</span>{" "}
                      <strong style={{ color: selectedCandidate.metrics.in_sample.net_profit_usd >= 0 ? "#22c55e" : "#ef4444", fontFamily: "monospace" }}>
                        +${selectedCandidate.metrics.in_sample.net_profit_usd.toLocaleString()}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Profit Factor:</span>{" "}
                      <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.in_sample.profit_factor.toFixed(2)}</strong>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Trades:</span>{" "}
                      <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.in_sample.trades}</strong>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Max DD:</span>{" "}
                      <strong style={{ color: "#ef4444", fontFamily: "monospace" }}>{selectedCandidate.metrics.in_sample.max_drawdown_pct.toFixed(2)}%</strong>
                    </div>
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#86efac", marginBottom: "8px" }}>
                    OUT-OF-SAMPLE (30% CIEGO)
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Net Profit:</span>{" "}
                      <strong style={{ color: selectedCandidate.metrics.out_of_sample.net_profit_usd >= 0 ? "#22c55e" : "#ef4444", fontFamily: "monospace" }}>
                        ${selectedCandidate.metrics.out_of_sample.net_profit_usd.toLocaleString()}
                      </strong>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Profit Factor:</span>{" "}
                      <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.out_of_sample.profit_factor.toFixed(2)}</strong>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Trades:</span>{" "}
                      <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.out_of_sample.trades}</strong>
                    </div>
                    <div>
                      <span style={{ color: "var(--text-muted)" }}>Max DD:</span>{" "}
                      <strong style={{ color: "#ef4444", fontFamily: "monospace" }}>{selectedCandidate.metrics.out_of_sample.max_drawdown_pct.toFixed(2)}%</strong>
                    </div>
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.2)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#fcd34d", marginBottom: "8px" }}>
                    ANTI-OVERFITTING & ROBUSTEZ
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                    <span style={{ color: "var(--text-muted)" }}>Ratio OOS / IS:</span>
                    <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.anti_overfit.ratio_oos_is.toFixed(2)}x</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                    <span style={{ color: "var(--text-muted)" }}>WFO Passing Score:</span>
                    <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.anti_overfit.wfo_pass_pct || 75}%</strong>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px" }}>
                    <span style={{ color: "var(--text-muted)" }}>Monte Carlo Score:</span>
                    <strong style={{ fontFamily: "monospace" }}>{selectedCandidate.metrics.anti_overfit.monte_carlo_score || 85}%</strong>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "40px 20px", textAlign: "center", color: "var(--text-muted)" }}>
              Selecciona una estrategia de la lista para ver su análisis detallado.
            </div>
          )}
        </div>
      </div>

      {/* CODE EXPORT MODAL */}
      {exportModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: "rgba(0,0,0,0.75)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 100,
          padding: "20px"
        }}>
          <div style={{
            background: "#0f172a",
            border: "1px solid #334155",
            borderRadius: "12px",
            width: "100%",
            maxWidth: "800px",
            maxHeight: "85vh",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            boxShadow: "0 25px 50px -12px rgba(0,0,0,0.8)"
          }}>
            <div style={{ padding: "16px 20px", borderBottom: "1px solid #334155", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontSize: "14px", fontWeight: 800, margin: 0, color: "#f8fafc" }}>{exportModal.title}</h3>
              <button
                onClick={() => setExportModal(null)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: "16px 20px", flex: 1, overflowY: "auto", background: "#090d16" }}>
              <pre style={{
                margin: 0,
                fontSize: "12px",
                fontFamily: "monospace",
                color: "#38bdf8",
                whiteSpace: "pre-wrap",
                lineHeight: "1.5"
              }}>
                {exportModal.code}
              </pre>
            </div>

            <div style={{ padding: "14px 20px", borderTop: "1px solid #334155", display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0f172a" }}>
              <span style={{ fontSize: "11px", color: "#64748b" }}>Archivo: {exportModal.filename}</span>
              <button
                onClick={handleCopyCode}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  background: copied ? "#22c55e" : "#6366f1",
                  border: "none",
                  color: "#ffffff",
                  fontWeight: 700,
                  fontSize: "12px",
                  cursor: "pointer"
                }}
              >
                {copied ? "✓ Copiado al portapapeles" : "📋 Copiar Código"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
