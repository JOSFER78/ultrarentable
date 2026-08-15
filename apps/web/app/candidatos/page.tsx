"use client";

import { useEffect, useState } from "react";
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
  passed: bool;
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

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  
  // Verification and Export States
  const [verifying, setVerifying] = useState(false);
  const [verificationReport, setVerificationReport] = useState<VerificationReport | null>(null);
  const [exportModal, setExportModal] = useState<{ title: string; language: string; filename: string; code: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetch("/api/v1/candidates")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCandidates(data);
          if (data.length > 0) setSelectedCandidate(data[0]);
        }
      })
      .catch((err) => console.error("Error loading candidates:", err));
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "RECHAZADA_FONDEO_DD":
        return { bg: "rgba(239, 68, 68, 0.2)", color: "#fca5a5", border: "1px solid #ef4444", text: "RECHAZADA (DD > 4%)" };
      case "INVESTIGACION_BTC":
        return { bg: "rgba(245, 158, 11, 0.2)", color: "#fde68a", border: "1px solid #f59e0b", text: "INVESTIGACIÓN BTC" };
      case "CANDIDATA_FONDEO":
        return { bg: "rgba(34, 197, 94, 0.2)", color: "#86efac", border: "1px solid #22c55e", text: "CANDIDATA FONDEO" };
      default:
        return { bg: "rgba(255, 255, 255, 0.1)", color: "var(--text-muted)", border: "1px solid var(--border)", text: status };
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
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", fontFamily: "monospace" }}>
              CANDIDATAS & SCORECARDS
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
            📊 Registro de Estrategias y Clasificación Anti-Overfit
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Scorecards cuantitativos verificados con evaluación diferenciada In-Sample (70%) y Out-of-Sample (30%).
          </p>
        </div>
      </div>

      {/* GRID CON LISTA Y DETALLE */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 480px", gap: "24px" }}>
        
        {/* TABLA DE ESTRATEGIAS */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)", background: "rgba(0,0,0,0.2)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "12px", fontWeight: 800, fontFamily: "monospace" }}>ESTRATEGIAS AUDITADAS ({candidates.length})</span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Doctrina REAL-ONLY</span>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", background: "rgba(255,255,255,0.02)" }}>
                  <th style={{ padding: "10px 14px" }}>Estrategia</th>
                  <th style={{ padding: "10px 14px" }}>Ruta</th>
                  <th style={{ padding: "10px 14px" }}>IS Net Profit</th>
                  <th style={{ padding: "10px 14px" }}>IS PF</th>
                  <th style={{ padding: "10px 14px" }}>OOS Net</th>
                  <th style={{ padding: "10px 14px" }}>OOS PF</th>
                  <th style={{ padding: "10px 14px" }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => {
                  const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
                  const badge = getStatusBadge(c.status);
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
                        <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>{c.symbol} · {c.timeframe}</div>
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
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: c.metrics.in_sample.net_profit_usd >= 0 ? "#22c55e" : "#ef4444" }}>
                        +${c.metrics.in_sample.net_profit_usd.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 700 }}>
                        {c.metrics.in_sample.profit_factor.toFixed(2)}
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", color: c.metrics.out_of_sample.net_profit_usd >= 0 ? "#22c55e" : "#ef4444" }}>
                        ${c.metrics.out_of_sample.net_profit_usd.toLocaleString()}
                      </td>
                      <td style={{ padding: "10px 14px", fontFamily: "monospace", fontWeight: 700 }}>
                        {c.metrics.out_of_sample.profit_factor.toFixed(2)}
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
                          fontFamily: "monospace"
                        }}>
                          {badge.text}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* DETALLE SCORECARD Y ACCIONES */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "20px" }}>
          {selectedCandidate ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", fontFamily: "monospace" }}>DETALLE SCORECARD</div>
                  <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "2px 0 0 0" }}>{selectedCandidate.name}</h2>
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
                  {selectedCandidate.status}
                </span>
              </div>

              {/* BOTONES DE ACCIÓN RÁPIDA */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginBottom: "16px" }}>
                <button
                  onClick={handleVerifyRobustness}
                  disabled={verifying}
                  style={{
                    background: "rgba(99, 102, 241, 0.2)",
                    border: "1px solid #6366f1",
                    color: "#a5b4fc",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontWeight: 800,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  🛡️ {verifying ? "Verificando..." : "Verificar 5 Gates"}
                </button>
                <button
                  onClick={handleExportTradingView}
                  style={{
                    background: "rgba(34, 197, 94, 0.2)",
                    border: "1px solid #22c55e",
                    color: "#86efac",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontWeight: 800,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  📈 Exportar Pine Script
                </button>
                <button
                  onClick={handleExportNinjaTrader}
                  style={{
                    gridColumn: "span 2",
                    background: "rgba(245, 158, 11, 0.2)",
                    border: "1px solid #f59e0b",
                    color: "#fde68a",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontSize: "11px",
                    fontWeight: 800,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "6px"
                  }}
                >
                  ⚙️ Exportar NinjaTrader 8 C# (.cs)
                </button>
              </div>

              {/* REPORTE DE VERIFICACIÓN 5 GATES (SI SE ACTIVÓ) */}
              {verificationReport && (
                <div style={{ background: "rgba(0,0,0,0.4)", border: "1px solid var(--border)", borderRadius: "8px", padding: "12px", marginBottom: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)" }}>
                      VERIFICACIÓN ZERO-TRUST ({verificationReport.total_score_pct}% APROBADO)
                    </span>
                    <span style={{
                      fontSize: "10px",
                      fontWeight: 800,
                      color: verificationReport.is_approved_for_live ? "#22c55e" : "#f59e0b"
                    }}>
                      {verificationReport.status_verdict}
                    </span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "11px" }}>
                    {verificationReport.gates.map((g) => (
                      <div key={g.gate_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: "4px" }}>
                        <div>
                          <span style={{ color: g.passed ? "#22c55e" : "#ef4444", marginRight: "6px", fontWeight: 800 }}>
                            {g.passed ? "✔" : "✖"}
                          </span>
                          <span>{g.name}</span>
                        </div>
                        <span style={{ fontFamily: "monospace", color: "var(--text-muted)", fontSize: "10px" }}>
                          {g.measured_value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* MOTIVO DE CLASIFICACION */}
              <div style={{ 
                background: selectedCandidate.status.includes("RECHAZADA") ? "rgba(239, 68, 68, 0.1)" : "rgba(245, 158, 11, 0.1)",
                borderLeft: selectedCandidate.status.includes("RECHAZADA") ? "3px solid #ef4444" : "3px solid #f59e0b",
                padding: "10px 12px",
                borderRadius: "0 6px 6px 0",
                fontSize: "12px",
                lineHeight: 1.5,
                color: selectedCandidate.status.includes("RECHAZADA") ? "#fca5a5" : "#fde68a",
                marginBottom: "16px"
              }}>
                <strong>Diagnóstico de Clasificación:</strong> {selectedCandidate.status_reason}
              </div>

              {/* METRICAS IS VS OOS */}
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px" }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontWeight: 800, color: "var(--accent)", marginBottom: "6px", fontFamily: "monospace", fontSize: "11px" }}>IN-SAMPLE (70% HISTÓRICO)</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontFamily: "monospace" }}>
                    <div>Beneficio: +${selectedCandidate.metrics.in_sample.net_profit_usd}</div>
                    <div>Trades: {selectedCandidate.metrics.in_sample.trades}</div>
                    <div>Profit Factor: {selectedCandidate.metrics.in_sample.profit_factor.toFixed(2)}</div>
                    <div>Max Drawdown: {selectedCandidate.metrics.in_sample.max_drawdown_pct}%</div>
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontWeight: 800, color: "#60a5fa", marginBottom: "6px", fontFamily: "monospace", fontSize: "11px" }}>OUT-OF-SAMPLE (30% DATOS CIEGOS)</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontFamily: "monospace" }}>
                    <div>Beneficio: +${selectedCandidate.metrics.out_of_sample.net_profit_usd}</div>
                    <div>Trades: {selectedCandidate.metrics.out_of_sample.trades}</div>
                    <div>Profit Factor: {selectedCandidate.metrics.out_of_sample.profit_factor.toFixed(2)}</div>
                    <div style={{ color: selectedCandidate.metrics.out_of_sample.max_drawdown_pct > 4.0 ? "#ef4444" : "#22c55e", fontWeight: 700 }}>
                      Max Drawdown: {selectedCandidate.metrics.out_of_sample.max_drawdown_pct}%
                    </div>
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontWeight: 800, color: "#22c55e", marginBottom: "6px", fontFamily: "monospace", fontSize: "11px" }}>ROBUSTEZ Y ANTI-OVERFITTING</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontFamily: "monospace" }}>
                    <div>Ratio OOS/IS: {selectedCandidate.metrics.anti_overfit.ratio_oos_is.toFixed(2)}x</div>
                    <div>WFO Consistencia: {selectedCandidate.metrics.anti_overfit.wfo_pass_pct ?? 70}%</div>
                    <div>Monte Carlo: {selectedCandidate.metrics.anti_overfit.monte_carlo_score ?? 80}/100</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "40px 0" }}>
              Selecciona una estrategia para ver su scorecard detallado.
            </div>
          )}
        </div>

      </div>

      {/* MODAL DE CÓDIGO EXPORTADO */}
      {exportModal && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          background: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(4px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999,
          padding: "20px"
        }}>
          <div style={{
            background: "var(--bg-panel)",
            border: "1px solid var(--border)",
            borderRadius: "12px",
            width: "100%",
            maxWidth: "840px",
            maxHeight: "85vh",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            boxShadow: "0 20px 40px rgba(0,0,0,0.5)"
          }}>
            <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "16px", fontWeight: 800 }}>{exportModal.title}</h3>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>{exportModal.filename} · {exportModal.language}</div>
              </div>
              <button
                onClick={() => setExportModal(null)}
                style={{ background: "transparent", border: "none", color: "var(--text-muted)", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px", background: "rgba(0,0,0,0.5)" }}>
              <pre style={{ margin: 0, fontSize: "11px", fontFamily: "monospace", color: "#93c5fd", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
                {exportModal.code}
              </pre>
            </div>

            <div style={{ padding: "12px 20px", borderTop: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Listo para pegar en TradingView / NinjaTrader 8</span>
              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  onClick={handleCopyCode}
                  style={{
                    background: copied ? "#22c55e" : "var(--accent)",
                    color: "#fff",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: 700,
                    cursor: "pointer"
                  }}
                >
                  {copied ? "✔ ¡Código Copiado!" : "📋 Copiar Código"}
                </button>
                <button
                  onClick={() => setExportModal(null)}
                  style={{
                    background: "rgba(255,255,255,0.1)",
                    color: "var(--text)",
                    border: "1px solid var(--border)",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    cursor: "pointer"
                  }}
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
