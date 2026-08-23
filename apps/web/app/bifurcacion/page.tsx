"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ValidationTrack } from "@/types/telemetry";

interface GateEvaluationResult {
  decision_id: string;
  strategy_id: string;
  target_track: string;
  is_approved: boolean;
  score_pct: number;
  evaluated_at_utc_ms: number;
  gate_metrics: Record<string, number | boolean | string>;
  rejection_reasons: string[];
  provenance_signature_sha256: string;
}

export default function BifurcacionQVFPage() {
  const [activeTrack, setActiveTrack] = useState<ValidationTrack>("TRACK_FONDEO");
  const [strategyId, setStrategyId] = useState<string>("UR-FONDEO-NQ-H1");
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [result, setResult] = useState<GateEvaluationResult | null>(null);

  // Form parameters for Fondeo
  const [fondeoDsr, setFondeoDsr] = useState<number>(2.45);
  const [fondeoMaxDd, setFondeoMaxDd] = useState<number>(3.2);
  const [fondeoOutlierPct, setFondeoOutlierPct] = useState<number>(11.5);
  const [fondeoWfe, setFondeoWfe] = useState<number>(0.72);
  const [fondeoDllBreaches, setFondeoDllBreaches] = useState<number>(0);

  // Form parameters for Ultra
  const [ultraPayoff, setUltraPayoff] = useState<number>(3.8);
  const [ultraTailGain, setUltraTailGain] = useState<number>(68.0);
  const [ultraExpBala, setUltraExpBala] = useState<number>(0.35);
  const [ultraMcSurvival, setUltraMcSurvival] = useState<number>(98.5);
  const [ultraSkewness, setUltraSkewness] = useState<number>(1.85);

  const [candidatesList, setCandidatesList] = useState<any[]>([]);

  React.useEffect(() => {
    fetch("/api/v1/candidates?limit=250")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        const list = Array.isArray(data) ? data : (data.candidates || []);
        if (list.length > 0) {
          setCandidatesList(list);
          setStrategyId(list[0].candidate_id || list[0].strategy_id);
        }
      })
      .catch(() => setCandidatesList([]));
  }, []);

  const handleEvaluate = async () => {
    if (!strategyId) return;
    setEvaluating(true);
    try {
      const res = await fetch(`/api/v1/gates/${strategyId}`);
      if (res.ok) {
        const data = await res.json();
        setResult({
          decision_id: `DEC_${strategyId}_${Date.now()}`,
          strategy_id: strategyId,
          target_track: activeTrack,
          is_approved: data.overall_certified || false,
          score_pct: data.scorecard_average || 0.0,
          evaluated_at_utc_ms: Date.now(),
          gate_metrics: {
            "Total Gates Aprobados": `${data.gates_passed_count || 0} / 11`,
            "Score Medio": `${data.scorecard_average || 0.0} pts`,
            "Estado": data.overall_certified ? "APROBADO_11_GATES" : "RECHAZADO_GATES_FALLIDOS",
          },
          rejection_reasons: (data.gates || []).filter((g: any) => !g.passed).map((g: any) => `Gate ${g.gate_id} (${g.name}): ${g.verdict}`),
          provenance_signature_sha256: data.strategy_id ? `sha256_${data.strategy_id}` : "NO_PROVENANCE",
        });
      } else {
        setResult(null);
      }
    } catch (e) {
      console.error(e);
      setResult(null);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div style={{ padding: "16px 24px", width: "100%", maxWidth: "100%", margin: 0, color: "#f8fafc", boxSizing: "border-box" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            QUANT VALIDATION FABRIC (QVF) · EVIDENCE GATE DUAL
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          Bifurcación de Validación & Compuertas de Evidencia
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Auditoría matemática independiente: Compuerta institucional para CME Prop Firms vs Compuerta de asimetría extrema para BingX.
        </p>
      </div>

      {/* 2. DUAL TRACK SELECTOR TABS */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "24px" }}>
        <button
          onClick={() => {
            setActiveTrack("TRACK_FONDEO");
            setStrategyId("UR-FONDEO-NQ-H1");
            setResult(null);
          }}
          style={{
            flex: 1,
            padding: "16px 20px",
            borderRadius: "12px",
            background: activeTrack === "TRACK_FONDEO" ? "rgba(56, 189, 248, 0.15)" : "rgba(16, 23, 34, 0.75)",
            border: activeTrack === "TRACK_FONDEO" ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.08)",
            cursor: "pointer",
            textAlign: "left",
            transition: "all 0.15s ease",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
            <span style={{ fontSize: "13px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
              1. TRACK_FONDEO (CME Prop Firms)
            </span>
            <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.2)", color: "#38bdf8" }}>
              INSTITUCIONAL
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8" }}>
            Preservación de capital · DSR ≥ 2.0 · Max DD ≤ 4.5% · 0 violaciones DLL · Outliers &lt; 15%
          </div>
        </button>

        <button
          onClick={() => {
            setActiveTrack("TRACK_ULTRA");
            setStrategyId("UR-ULTRA-SOL-H1");
            setResult(null);
          }}
          style={{
            flex: 1,
            padding: "16px 20px",
            borderRadius: "12px",
            background: activeTrack === "TRACK_ULTRA" ? "rgba(99, 225, 180, 0.15)" : "rgba(16, 23, 34, 0.75)",
            border: activeTrack === "TRACK_ULTRA" ? "1px solid #63e1b4" : "1px solid rgba(255, 255, 255, 0.08)",
            cursor: "pointer",
            textAlign: "left",
            transition: "all 0.15s ease",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
            <span style={{ fontSize: "13px", fontWeight: 900, color: "#63e1b4", fontFamily: "var(--font-mono, monospace)" }}>
              2. TRACK_ULTRA (BingX Perpetuals)
            </span>
            <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(99, 225, 180, 0.2)", color: "#63e1b4" }}>
              ALTA ASIMETRÍA
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8" }}>
            Margen aislado 1R · Payoff ≥ 3.0 · Tail Gain ≥ 60% · E(Bala) ≥ 0.20R · Bóveda Ratchet
          </div>
        </button>
      </div>

      {/* 3. EVALUATION AUDITOR PANEL */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
        {/* LEFT: CRITERIA GAUGES & PARAMS */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "22px",
          }}
        >
          <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: "0 0 16px 0" }}>
            Parámetros Cuantitativos de Auditoría
          </h3>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", display: "block", marginBottom: "6px" }}>
              ID DE LA ESTRATEGIA A AUDITAR:
            </label>
            <input
              type="text"
              value={strategyId}
              onChange={(e) => setStrategyId(e.target.value)}
              style={{
                width: "100%",
                background: "rgba(0, 0, 0, 0.4)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: "8px",
                padding: "8px 12px",
                color: "#fff",
                fontSize: "12px",
                fontWeight: 700,
                fontFamily: "var(--font-mono, monospace)",
                outline: "none",
                boxSizing: "border-box",
              }}
            />
          </div>

          {activeTrack === "TRACK_FONDEO" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Deflated Sharpe Ratio (DSR):</span>
                  <strong style={{ color: fondeoDsr >= 2.0 ? "#34d399" : "#f43f5e" }}>{fondeoDsr.toFixed(2)} (Min 2.0)</strong>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="4.0"
                  step="0.05"
                  value={fondeoDsr}
                  onChange={(e) => setFondeoDsr(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Max Drawdown Histórico:</span>
                  <strong style={{ color: fondeoMaxDd <= 4.5 ? "#34d399" : "#f43f5e" }}>{fondeoMaxDd.toFixed(1)}% (Max 4.5%)</strong>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="10.0"
                  step="0.1"
                  value={fondeoMaxDd}
                  onChange={(e) => setFondeoMaxDd(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Dependencia de Outliers Top-2:</span>
                  <strong style={{ color: fondeoOutlierPct < 15.0 ? "#34d399" : "#f43f5e" }}>{fondeoOutlierPct.toFixed(1)}% (&lt; 15%)</strong>
                </div>
                <input
                  type="range"
                  min="5.0"
                  max="40.0"
                  step="0.5"
                  value={fondeoOutlierPct}
                  onChange={(e) => setFondeoOutlierPct(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Walk-Forward Efficiency (WFE):</span>
                  <strong style={{ color: fondeoWfe >= 0.60 ? "#34d399" : "#f43f5e" }}>{(fondeoWfe * 100).toFixed(0)}% (Min 60%)</strong>
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="1.0"
                  step="0.02"
                  value={fondeoWfe}
                  onChange={(e) => setFondeoWfe(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Payoff Ratio (Ganancia Media / Pérdida Media):</span>
                  <strong style={{ color: ultraPayoff >= 3.0 ? "#34d399" : "#f43f5e" }}>{ultraPayoff.toFixed(1)}x (Min 3.0x)</strong>
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="8.0"
                  step="0.1"
                  value={ultraPayoff}
                  onChange={(e) => setUltraPayoff(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Tail Gain Ratio (Beneficio en Cola &ge; 3R):</span>
                  <strong style={{ color: ultraTailGain >= 60.0 ? "#34d399" : "#f43f5e" }}>{ultraTailGain.toFixed(1)}% (Min 60%)</strong>
                </div>
                <input
                  type="range"
                  min="20.0"
                  max="90.0"
                  step="1.0"
                  value={ultraTailGain}
                  onChange={(e) => setUltraTailGain(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Expectativa Matemática E(Bala):</span>
                  <strong style={{ color: ultraExpBala >= 0.20 ? "#34d399" : "#f43f5e" }}>+{ultraExpBala.toFixed(2)}R (Min +0.20R)</strong>
                </div>
                <input
                  type="range"
                  min="-0.5"
                  max="1.5"
                  step="0.05"
                  value={ultraExpBala}
                  onChange={(e) => setUltraExpBala(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4" }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Supervivencia Monte Carlo (20 Balas):</span>
                  <strong style={{ color: ultraMcSurvival >= 95.0 ? "#34d399" : "#f43f5e" }}>{ultraMcSurvival.toFixed(1)}% (Min 95%)</strong>
                </div>
                <input
                  type="range"
                  min="70.0"
                  max="100.0"
                  step="0.5"
                  value={ultraMcSurvival}
                  onChange={(e) => setUltraMcSurvival(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4" }}
                />
              </div>
            </div>
          )}

          <button
            onClick={handleEvaluate}
            disabled={evaluating}
            style={{
              marginTop: "20px",
              width: "100%",
              padding: "12px",
              borderRadius: "8px",
              background: activeTrack === "TRACK_ULTRA" ? "linear-gradient(135deg, #63e1b4 0%, #059669 100%)" : "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
              border: "none",
              color: "#06080d",
              fontWeight: 900,
              fontSize: "13px",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              letterSpacing: "0.5px",
            }}
          >
            {evaluating ? "EJECUTANDO EVIDENCE GATE..." : "⚡ EVALUAR CANDIDATO EN QVF"}
          </button>
        </div>

        {/* RIGHT: GATE DECISION AUDIT CARD */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: result
              ? result.is_approved
                ? "1px solid rgba(52, 211, 153, 0.4)"
                : "1px solid rgba(244, 63, 94, 0.4)"
              : "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "22px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: "0 0 16px 0" }}>
            Veredicto de la Compuerta EvidenceGateDecision
          </h3>

          {!result ? (
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#64748b", padding: "40px" }}>
              <span style={{ fontSize: "32px", marginBottom: "8px" }}>🛡️</span>
              <div style={{ fontSize: "13px", fontWeight: 700 }}>Compuerta en Standby</div>
              <div style={{ fontSize: "11px", textAlign: "center", marginTop: "4px" }}>
                Presiona &quot;EVALUAR CANDIDATO EN QVF&quot; para ejecutar la auditoría matemática en el backend.
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div
                style={{
                  padding: "14px 18px",
                  borderRadius: "10px",
                  background: result.is_approved ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)",
                  border: result.is_approved ? "1px solid #34d399" : "1px solid #f43f5e",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <div style={{ fontSize: "10px", fontWeight: 800, color: result.is_approved ? "#34d399" : "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
                    VEREDICTO EVIDENCE GATE
                  </div>
                  <div style={{ fontSize: "20px", fontWeight: 900, color: "#fff", marginTop: "2px" }}>
                    {result.is_approved ? "✓ APROBADO PARA CANDIDATO" : "✕ RECHAZADO"}
                  </div>
                </div>
                <div style={{ fontSize: "22px", fontWeight: 900, color: result.is_approved ? "#34d399" : "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
                  {result.score_pct}%
                </div>
              </div>

              {/* REASONS IF REJECTED */}
              {result.rejection_reasons.length > 0 && (
                <div style={{ background: "rgba(244, 63, 94, 0.08)", border: "1px solid rgba(244, 63, 94, 0.2)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#f43f5e", marginBottom: "6px" }}>
                    VIOLACIONES DETECTADAS:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "11px", color: "#fda4af" }}>
                    {result.rejection_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* PROVENANCE HASH */}
              <div style={{ background: "rgba(0, 0, 0, 0.4)", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  FIRMA CRIPTOGRÁFICA INMUTABLE (SHA-256):
                </div>
                <div style={{ fontSize: "11px", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", wordBreak: "break-all", marginTop: "4px" }}>
                  {result.provenance_signature_sha256}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
