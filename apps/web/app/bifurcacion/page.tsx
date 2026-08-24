"use client";

import React, { useState, useEffect } from "react";
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
  const [strategyId, setStrategyId] = useState<string>("");
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [result, setResult] = useState<GateEvaluationResult | null>(null);

  // Form parameters for Fondeo (ZERO-MOCKS: sin defaults hardcodeados, inicializados en null)
  const [fondeoDsr, setFondeoDsr] = useState<number | null>(null);
  const [fondeoMaxDd, setFondeoMaxDd] = useState<number | null>(null);
  const [fondeoOutlierPct, setFondeoOutlierPct] = useState<number | null>(null);
  const [fondeoWfe, setFondeoWfe] = useState<number | null>(null);
  const [fondeoDllBreaches, setFondeoDllBreaches] = useState<number | null>(null);

  // Form parameters for Ultra (ZERO-MOCKS: sin defaults hardcodeados, inicializados en null)
  const [ultraPayoff, setUltraPayoff] = useState<number | null>(null);
  const [ultraTailGain, setUltraTailGain] = useState<number | null>(null);
  const [ultraExpBala, setUltraExpBala] = useState<number | null>(null);
  const [ultraMcSurvival, setUltraMcSurvival] = useState<number | null>(null);
  const [ultraSkewness, setUltraSkewness] = useState<number | null>(null);

  const [candidatesList, setCandidatesList] = useState<any[]>([]);

  const resetMetrics = () => {
    setFondeoDsr(null);
    setFondeoMaxDd(null);
    setFondeoOutlierPct(null);
    setFondeoWfe(null);
    setFondeoDllBreaches(null);
    setUltraPayoff(null);
    setUltraTailGain(null);
    setUltraExpBala(null);
    setUltraMcSurvival(null);
    setUltraSkewness(null);
    setResult(null);
  };

  useEffect(() => {
    fetch("/api/v1/candidates?limit=250")
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        const list = Array.isArray(data) ? data : (data.candidates || []);
        if (list.length > 0) {
          setCandidatesList(list);
          const firstCand = list.find((c: any) => 
            activeTrack === "TRACK_FONDEO" 
              ? (c.route === "FONDEO" || c.track === "TRACK_FONDEO")
              : (c.route === "ULTRA" || c.track === "TRACK_ULTRA")
          ) || list[0];
          setStrategyId(firstCand.candidate_id || firstCand.strategy_id || "");
        }
      })
      .catch(() => setCandidatesList([]));
  }, [activeTrack]);

  const handleEvaluate = async () => {
    if (!strategyId) return;
    setEvaluating(true);
    try {
      // 1. Consultar telemetría real del candidato desde backend
      const res = await fetch(`/api/v1/candidates/${strategyId}`);
      if (res.ok) {
        const data = await res.json();
        const sc = typeof data.scorecard_json === "string" 
          ? JSON.parse(data.scorecard_json || "{}") 
          : (data.scorecard_json || {});
        
        const isM = data.metrics?.in_sample || sc.is_metrics || {};
        const oosM = data.metrics?.out_of_sample || sc.oos_metrics || {};
        const antiOverfit = data.metrics?.anti_overfit || sc.anti_overfit || {};

        // Extraer métricas cuantitativas empíricas reales
        const realDsr = typeof sc.dsr === "number" 
          ? sc.dsr 
          : (typeof antiOverfit.dsr_score === "number" 
            ? antiOverfit.dsr_score 
            : (typeof data.dsr === "number" ? data.dsr : null));

        const realMaxDd = typeof data.max_dd_realized_pct === "number" 
          ? data.max_dd_realized_pct 
          : (typeof oosM.max_drawdown_pct === "number" 
            ? oosM.max_drawdown_pct 
            : (typeof data.max_dd_oos_pct === "number" ? data.max_dd_oos_pct : null));

        const realOutlierPct = typeof sc.top2_outlier_pct === "number" 
          ? sc.top2_outlier_pct 
          : (typeof oosM.outlier_pct === "number" ? oosM.outlier_pct : null);

        const realWfe = typeof antiOverfit.wfe_pct === "number" 
          ? antiOverfit.wfe_pct / 100 
          : (typeof data.wfe_pct === "number" 
            ? data.wfe_pct / 100 
            : (typeof antiOverfit.ratio_oos_is === "number" ? antiOverfit.ratio_oos_is : null));

        const realPayoff = typeof oosM.payoff_ratio === "number" 
          ? oosM.payoff_ratio 
          : (typeof sc.payoff_ratio === "number" 
            ? sc.payoff_ratio 
            : (oosM.profit_factor ? Number(oosM.profit_factor) : null));

        const realTailGain = typeof sc.tail_gain_pct === "number" 
          ? sc.tail_gain_pct 
          : (typeof oosM.tail_gain_pct === "number" ? oosM.tail_gain_pct : null);

        const realExpBala = typeof sc.expected_r === "number" 
          ? sc.expected_r 
          : (typeof oosM.expected_r === "number" ? oosM.expected_r : null);

        const realMcSurvival = typeof antiOverfit.monte_carlo_score === "number" 
          ? antiOverfit.monte_carlo_score 
          : (typeof data.monte_carlo_score === "number" ? data.monte_carlo_score : null);

        const realSkewness = typeof sc.skewness === "number" 
          ? sc.skewness 
          : (typeof oosM.skewness === "number" ? oosM.skewness : null);

        // Actualizar parámetros empíricos reales en React
        if (realDsr !== null) setFondeoDsr(realDsr);
        if (realMaxDd !== null) setFondeoMaxDd(realMaxDd);
        if (realOutlierPct !== null) setFondeoOutlierPct(realOutlierPct);
        if (realWfe !== null) setFondeoWfe(realWfe);
        if (realPayoff !== null) setUltraPayoff(realPayoff);
        if (realTailGain !== null) setUltraTailGain(realTailGain);
        if (realExpBala !== null) setUltraExpBala(realExpBala);
        if (realMcSurvival !== null) setUltraMcSurvival(realMcSurvival);
        if (realSkewness !== null) setUltraSkewness(realSkewness);

        // Lectura criptográfica real: bundle_signature_sha256 del EvidenceBundle o de la API
        const realProvenance = data.bundle_signature_sha256 
          || data.evidence_bundle?.bundle_signature_sha256 
          || sc.bundle_signature_sha256 
          || sc.bundle_hash 
          || data.sha256 
          || data.strategy_sha256 
          || "SIN_EVIDENCIA_FIRMA";

        const isApproved = Boolean(
          data.status?.includes("APPROVED") || 
          data.status?.includes("CERTIFIED") || 
          sc.overall_certified === true
        );

        const score = typeof data.scorecard_average === "number" 
          ? data.scorecard_average 
          : (data.gates_passed_count ? Math.round((data.gates_passed_count / 11) * 100) : (isApproved ? 100 : 0));

        setResult({
          decision_id: `DEC_${strategyId}_${Date.now()}`,
          strategy_id: strategyId,
          target_track: activeTrack,
          is_approved: isApproved,
          score_pct: score,
          evaluated_at_utc_ms: Date.now(),
          gate_metrics: {
            "Total Gates Aprobados": `${data.gates_passed_count || (isApproved ? 11 : 0)} / 11`,
            "Score Medio": `${score} pts`,
            "Estado": isApproved ? "APROBADO_11_GATES" : "RECHAZADO_GATES_FALLIDOS",
          },
          rejection_reasons: data.status_reason 
            ? [data.status_reason] 
            : (!isApproved ? ["Estrategia no superó los 11 gates canónicos o límites de riesgo"] : []),
          provenance_signature_sha256: realProvenance,
        });
      } else {
        // Fallback a compuerta de gates si existe endpoint
        const gatesRes = await fetch(`/api/v1/gates/${strategyId}`);
        if (gatesRes.ok) {
          const gData = await gatesRes.json();
          const realProvenance = gData.bundle_signature_sha256 
            || gData.bundle_signature 
            || gData.sha256 
            || gData.evidence_bundle_signature 
            || "SIN_EVIDENCIA_FIRMA";

          setResult({
            decision_id: `DEC_${strategyId}_${Date.now()}`,
            strategy_id: strategyId,
            target_track: activeTrack,
            is_approved: gData.overall_certified || false,
            score_pct: gData.scorecard_average || 0.0,
            evaluated_at_utc_ms: Date.now(),
            gate_metrics: {
              "Total Gates Aprobados": `${gData.gates_passed_count || 0} / 11`,
              "Score Medio": `${gData.scorecard_average || 0.0} pts`,
              "Estado": gData.overall_certified ? "APROBADO_11_GATES" : "RECHAZADO_GATES_FALLIDOS",
            },
            rejection_reasons: (gData.gates || []).filter((g: any) => !g.passed).map((g: any) => `Gate ${g.gate_id} (${g.name}): ${g.verdict}`),
            provenance_signature_sha256: realProvenance,
          });
        } else {
          setResult(null);
        }
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
            resetMetrics();
            const fondeoCand = candidatesList.find((c: any) => c.route === "FONDEO" || c.track === "TRACK_FONDEO");
            if (fondeoCand) {
              setStrategyId(fondeoCand.candidate_id || fondeoCand.strategy_id);
            }
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
            resetMetrics();
            const ultraCand = candidatesList.find((c: any) => c.route === "ULTRA" || c.track === "TRACK_ULTRA");
            if (ultraCand) {
              setStrategyId(ultraCand.candidate_id || ultraCand.strategy_id);
            }
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
            <div style={{ display: "flex", gap: "8px" }}>
              <input
                type="text"
                value={strategyId}
                placeholder="Seleccione o ingrese ID de estrategia..."
                onChange={(e) => {
                  setStrategyId(e.target.value);
                  resetMetrics();
                }}
                style={{
                  flex: 1,
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
              {candidatesList.length > 0 && (
                <select
                  value={strategyId}
                  onChange={(e) => {
                    setStrategyId(e.target.value);
                    resetMetrics();
                  }}
                  style={{
                    background: "#030712",
                    border: "1px solid rgba(255, 255, 255, 0.12)",
                    borderRadius: "8px",
                    padding: "8px",
                    color: "#38bdf8",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono, monospace)",
                    outline: "none",
                    maxWidth: "180px",
                  }}
                >
                  <option value="">Seleccionar Candidato...</option>
                  {candidatesList.map((c: any) => (
                    <option key={c.candidate_id || c.strategy_id} value={c.candidate_id || c.strategy_id}>
                      {c.candidate_id || c.strategy_id} ({c.symbol})
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          {activeTrack === "TRACK_FONDEO" ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Deflated Sharpe Ratio (DSR):</span>
                  {fondeoDsr !== null ? (
                    <strong style={{ color: fondeoDsr >= 2.0 ? "#34d399" : "#f43f5e" }}>
                      {fondeoDsr.toFixed(2)} (Min 2.0)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="4.0"
                  step="0.05"
                  value={fondeoDsr ?? 2.0}
                  disabled={fondeoDsr === null}
                  onChange={(e) => setFondeoDsr(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8", opacity: fondeoDsr === null ? 0.35 : 1 }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Max Drawdown Histórico:</span>
                  {fondeoMaxDd !== null ? (
                    <strong style={{ color: fondeoMaxDd <= 4.5 ? "#34d399" : "#f43f5e" }}>
                      {fondeoMaxDd.toFixed(1)}% (Max 4.5%)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="10.0"
                  step="0.1"
                  value={fondeoMaxDd ?? 4.5}
                  disabled={fondeoMaxDd === null}
                  onChange={(e) => setFondeoMaxDd(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8", opacity: fondeoMaxDd === null ? 0.35 : 1 }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Dependencia de Outliers Top-2:</span>
                  {fondeoOutlierPct !== null ? (
                    <strong style={{ color: fondeoOutlierPct < 15.0 ? "#34d399" : "#f43f5e" }}>
                      {fondeoOutlierPct.toFixed(1)}% (&lt; 15%)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="5.0"
                  max="40.0"
                  step="0.5"
                  value={fondeoOutlierPct ?? 15.0}
                  disabled={fondeoOutlierPct === null}
                  onChange={(e) => setFondeoOutlierPct(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8", opacity: fondeoOutlierPct === null ? 0.35 : 1 }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Walk-Forward Efficiency (WFE):</span>
                  {fondeoWfe !== null ? (
                    <strong style={{ color: fondeoWfe >= 0.60 ? "#34d399" : "#f43f5e" }}>
                      {(fondeoWfe * 100).toFixed(0)}% (Min 60%)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="0.2"
                  max="1.0"
                  step="0.02"
                  value={fondeoWfe ?? 0.6}
                  disabled={fondeoWfe === null}
                  onChange={(e) => setFondeoWfe(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8", opacity: fondeoWfe === null ? 0.35 : 1 }}
                />
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Payoff Ratio (Ganancia Media / Pérdida Media):</span>
                  {ultraPayoff !== null ? (
                    <strong style={{ color: ultraPayoff >= 3.0 ? "#34d399" : "#f43f5e" }}>
                      {ultraPayoff.toFixed(1)}x (Min 3.0x)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="1.0"
                  max="8.0"
                  step="0.1"
                  value={ultraPayoff ?? 3.0}
                  disabled={ultraPayoff === null}
                  onChange={(e) => setUltraPayoff(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4", opacity: ultraPayoff === null ? 0.35 : 1 }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Tail Gain Ratio (Beneficio en Cola &ge; 3R):</span>
                  {ultraTailGain !== null ? (
                    <strong style={{ color: ultraTailGain >= 60.0 ? "#34d399" : "#f43f5e" }}>
                      {ultraTailGain.toFixed(1)}% (Min 60%)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="20.0"
                  max="90.0"
                  step="1.0"
                  value={ultraTailGain ?? 60.0}
                  disabled={ultraTailGain === null}
                  onChange={(e) => setUltraTailGain(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4", opacity: ultraTailGain === null ? 0.35 : 1 }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Expectativa Matemática E(Bala):</span>
                  {ultraExpBala !== null ? (
                    <strong style={{ color: ultraExpBala >= 0.20 ? "#34d399" : "#f43f5e" }}>
                      {ultraExpBala >= 0 ? "+" : ""}{ultraExpBala.toFixed(2)}R (Min +0.20R)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="-0.5"
                  max="1.5"
                  step="0.05"
                  value={ultraExpBala ?? 0.2}
                  disabled={ultraExpBala === null}
                  onChange={(e) => setUltraExpBala(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4", opacity: ultraExpBala === null ? 0.35 : 1 }}
                />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                  <span style={{ color: "#94a3b8" }}>Supervivencia Monte Carlo (20 Balas):</span>
                  {ultraMcSurvival !== null ? (
                    <strong style={{ color: ultraMcSurvival >= 95.0 ? "#34d399" : "#f43f5e" }}>
                      {ultraMcSurvival.toFixed(1)}% (Min 95%)
                    </strong>
                  ) : (
                    <span style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px" }}>
                      SIN DATOS / NO EVIDENCE
                    </span>
                  )}
                </div>
                <input
                  type="range"
                  min="70.0"
                  max="100.0"
                  step="0.5"
                  value={ultraMcSurvival ?? 95.0}
                  disabled={ultraMcSurvival === null}
                  onChange={(e) => setUltraMcSurvival(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#63e1b4", opacity: ultraMcSurvival === null ? 0.35 : 1 }}
                />
              </div>
            </div>
          )}

          <button
            onClick={handleEvaluate}
            disabled={evaluating || !strategyId}
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
              cursor: (evaluating || !strategyId) ? "not-allowed" : "pointer",
              fontFamily: "var(--font-mono, monospace)",
              letterSpacing: "0.5px",
              opacity: (evaluating || !strategyId) ? 0.6 : 1,
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

              {/* PROVENANCE HASH CRIPTOGRÁFICO REAL */}
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
