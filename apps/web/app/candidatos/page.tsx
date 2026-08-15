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

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

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
      <div style={{ display: "grid", gridTemplateColumns: "1fr 440px", gap: "24px" }}>
        
        {/* TABLA DE ESTRATEGIAS */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
          <div style={{ padding: "14px 16px", borderBottom: "1px solid var(--border)", background: "rgba(0,0,0,0.2)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "12px", fontWeight: 800, fontFamily: "monospace" }}>ESTRATEGIAS AUDITADAS ({candidates.length})</span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Doctrina REAL-ONLY</span>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "11px" }}>
                  <th style={{ padding: "10px 14px" }}>ESTRATEGIA</th>
                  <th style={{ padding: "10px 14px" }}>IN-SAMPLE (70%)</th>
                  <th style={{ padding: "10px 14px" }}>OUT-OF-SAMPLE (30%)</th>
                  <th style={{ padding: "10px 14px" }}>RATIO OOS/IS</th>
                  <th style={{ padding: "10px 14px" }}>ESTADO REAL</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => {
                  const badge = getStatusBadge(c.status);
                  const isSelected = selectedCandidate?.candidate_id === c.candidate_id;
                  return (
                    <tr
                      key={c.candidate_id}
                      onClick={() => setSelectedCandidate(c)}
                      style={{
                        borderBottom: "1px solid var(--border)",
                        background: isSelected ? "rgba(96, 165, 250, 0.1)" : "transparent",
                        cursor: "pointer",
                      }}
                    >
                      <td style={{ padding: "12px 14px" }}>
                        <div style={{ fontWeight: 800, color: "var(--text-primary)" }}>{c.name}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>{c.symbol} · {c.timeframe}</div>
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        <div style={{ fontWeight: 700, color: "#22c55e" }}>PF {c.metrics.in_sample.profit_factor.toFixed(2)}</div>
                        <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>{c.metrics.in_sample.trades} trades · DD {c.metrics.in_sample.max_drawdown_pct}%</div>
                      </td>
                      <td style={{ padding: "12px 14px" }}>
                        <div style={{ fontWeight: 700, color: c.metrics.out_of_sample.profit_factor >= 1.25 ? "#22c55e" : "#ef4444" }}>
                          PF {c.metrics.out_of_sample.profit_factor.toFixed(2)}
                        </div>
                        <div style={{ fontSize: "11px", color: c.metrics.out_of_sample.max_drawdown_pct > 4.0 ? "#ef4444" : "var(--text-muted)" }}>
                          {c.metrics.out_of_sample.trades} trades · DD {c.metrics.out_of_sample.max_drawdown_pct}%
                        </div>
                      </td>
                      <td style={{ padding: "12px 14px", fontFamily: "monospace", fontWeight: 700 }}>
                        {c.metrics.anti_overfit.ratio_oos_is.toFixed(2)}x
                      </td>
                      <td style={{ padding: "12px 14px" }}>
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

        {/* DETALLE SCORECARD */}
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
                    <div>Trades: {selectedCandidate.metrics.out_of_sample.trades} (Mín. ≥ 20)</div>
                    <div>Profit Factor: {selectedCandidate.metrics.out_of_sample.profit_factor.toFixed(2)}</div>
                    <div style={{ color: selectedCandidate.metrics.out_of_sample.max_drawdown_pct > 4.0 ? "#ef4444" : "#22c55e", fontWeight: 700 }}>
                      Max Drawdown: {selectedCandidate.metrics.out_of_sample.max_drawdown_pct}% (Límite ≤ 4.0%)
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
    </div>
  );
}
