"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Target,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Scale,
  Copy,
  Check,
  ArrowRight,
  Sparkles,
  Layers,
  Activity,
  ChevronRight,
  Info,
} from "lucide-react";
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
  const [copiedHash, setCopiedHash] = useState<boolean>(false);

  // Form parameters for Fondeo (ZERO-MOCKS: initialized as null)
  const [fondeoDsr, setFondeoDsr] = useState<number | null>(null);
  const [fondeoMaxDd, setFondeoMaxDd] = useState<number | null>(null);
  const [fondeoOutlierPct, setFondeoOutlierPct] = useState<number | null>(null);
  const [fondeoWfe, setFondeoWfe] = useState<number | null>(null);
  const [fondeoDllBreaches, setFondeoDllBreaches] = useState<number | null>(null);

  // Form parameters for Ultra (ZERO-MOCKS: initialized as null)
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

  const handleCopySignature = (hash: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(hash);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    }
  };

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
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-24 text-slate-100">
      {/* 1. HEADER */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link href="/" className="text-xs text-slate-400 hover:text-white transition">
                ← Command Center
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider">
                QUANT VALIDATION FABRIC (QVF) · EVIDENCE GATE DUAL
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Bifurcación de Validación & Compuertas de Evidencia
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Auditoría matemática independiente: Compuerta institucional para CME Prop Firms vs Compuerta de asimetría extrema para BingX.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <Link
              href="/bifurcacion/fondeo"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-bold bg-sky-950/80 text-sky-300 border border-sky-700/60 hover:bg-sky-900 transition"
            >
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>Ver Dashboard Fondeo</span>
            </Link>
            <Link
              href="/bifurcacion/ultrarentable"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 hover:bg-emerald-900 transition"
            >
              <Zap className="w-4 h-4 text-emerald-400" />
              <span>Ver Dashboard Ultra</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. DUAL TRACK SELECTOR TABS */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => {
            setActiveTrack("TRACK_FONDEO");
            resetMetrics();
            const fondeoCand = candidatesList.find((c: any) => c.route === "FONDEO" || c.track === "TRACK_FONDEO");
            if (fondeoCand) {
              setStrategyId(fondeoCand.candidate_id || fondeoCand.strategy_id);
            }
          }}
          className={`p-5 rounded-2xl text-left transition-all border backdrop-blur-xl ${
            activeTrack === "TRACK_FONDEO"
              ? "bg-sky-950/30 border-sky-500 shadow-lg shadow-sky-500/10 ring-1 ring-sky-500/30"
              : "bg-[#090d16]/90 border-white/[0.08] hover:border-sky-500/30"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-black text-sky-400 font-mono flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" />
              <span>1. TRACK_FONDEO (CME Prop Firms)</span>
            </span>
            <span className="text-[10px] font-black font-mono px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/40">
              INSTITUCIONAL
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Preservación estricta de capital: Deflated Sharpe DSR ≥ 2.0 · Max DD ≤ 4.5% · 0 violaciones DLL · Dependencia de Outliers &lt; 15%.
          </p>
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
          className={`p-5 rounded-2xl text-left transition-all border backdrop-blur-xl ${
            activeTrack === "TRACK_ULTRA"
              ? "bg-emerald-950/30 border-emerald-500 shadow-lg shadow-emerald-500/10 ring-1 ring-emerald-500/30"
              : "bg-[#090d16]/90 border-white/[0.08] hover:border-emerald-500/30"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-black text-emerald-400 font-mono flex items-center gap-2">
              <Zap className="w-4 h-4" />
              <span>2. TRACK_ULTRA (BingX Perpetuals)</span>
            </span>
            <span className="text-[10px] font-black font-mono px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              ALTA ASIMETRÍA
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Margen aislado 1R con piramidación al 40% House Money: Payoff ≥ 3.0 · Tail Gain ≥ 60% · E(Bala) ≥ +0.20R · Supervivencia MC ≥ 95%.
          </p>
        </button>
      </div>

      {/* 3. EVALUATION AUDITOR PANEL */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT: CRITERIA GAUGES & PARAMS */}
        <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-base font-black text-white flex items-center gap-2">
              <Target className="w-4 h-4 text-sky-400" />
              <span>Parámetros Cuantitativos de Auditoría</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">
              {activeTrack === "TRACK_FONDEO" ? "CME Standard" : "Convex Standard"}
            </span>
          </div>

          {/* Strategy Selection */}
          <div className="space-y-2">
            <label className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
              ID DE LA ESTRATEGIA A AUDITAR:
            </label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={strategyId}
                placeholder="Seleccione o ingrese ID..."
                onChange={(e) => {
                  setStrategyId(e.target.value);
                  resetMetrics();
                }}
                className="flex-1 bg-[#030712] border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-mono font-bold text-white focus:border-sky-500 focus:outline-none"
              />
              {candidatesList.length > 0 && (
                <select
                  value={strategyId}
                  onChange={(e) => {
                    setStrategyId(e.target.value);
                    resetMetrics();
                  }}
                  className="bg-[#030712] border border-slate-700/80 rounded-xl px-3 py-2 text-xs font-mono text-sky-400 focus:border-sky-500 focus:outline-none max-w-xs"
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

          {/* Parameter Sliders / Indicators */}
          {activeTrack === "TRACK_FONDEO" ? (
            <div className="space-y-4 pt-2">
              {/* DSR */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Deflated Sharpe Ratio (DSR):</span>
                  {fondeoDsr !== null ? (
                    <span className={`font-black ${fondeoDsr >= 2.0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {fondeoDsr.toFixed(2)} (Mín 2.00)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-sky-400 cursor-pointer disabled:opacity-30"
                />
              </div>

              {/* Max DD */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Max Drawdown Histórico:</span>
                  {fondeoMaxDd !== null ? (
                    <span className={`font-black ${fondeoMaxDd <= 4.5 ? "text-emerald-400" : "text-rose-400"}`}>
                      {fondeoMaxDd.toFixed(1)}% (Máx 4.5%)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-sky-400 cursor-pointer disabled:opacity-30"
                />
              </div>

              {/* Outliers */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Dependencia de Outliers Top-2:</span>
                  {fondeoOutlierPct !== null ? (
                    <span className={`font-black ${fondeoOutlierPct < 15.0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {fondeoOutlierPct.toFixed(1)}% (&lt; 15%)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-sky-400 cursor-pointer disabled:opacity-30"
                />
              </div>

              {/* WFE */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Walk-Forward Efficiency (WFE):</span>
                  {fondeoWfe !== null ? (
                    <span className={`font-black ${fondeoWfe >= 0.60 ? "text-emerald-400" : "text-rose-400"}`}>
                      {(fondeoWfe * 100).toFixed(0)}% (Mín 60%)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-sky-400 cursor-pointer disabled:opacity-30"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4 pt-2">
              {/* Payoff Ratio */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Payoff Ratio (Ganancia / Pérdida):</span>
                  {ultraPayoff !== null ? (
                    <span className={`font-black ${ultraPayoff >= 3.0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {ultraPayoff.toFixed(1)}x (Mín 3.0x)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-emerald-400 cursor-pointer disabled:opacity-30"
                />
              </div>

              {/* Tail Gain */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Tail Gain Ratio (Beneficio Cola ≥ 3R):</span>
                  {ultraTailGain !== null ? (
                    <span className={`font-black ${ultraTailGain >= 60.0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {ultraTailGain.toFixed(1)}% (Mín 60%)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-emerald-400 cursor-pointer disabled:opacity-30"
                />
              </div>

              {/* Expectativa E(Bala) */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Expectativa Matemática E(Bala):</span>
                  {ultraExpBala !== null ? (
                    <span className={`font-black ${ultraExpBala >= 0.20 ? "text-emerald-400" : "text-rose-400"}`}>
                      {ultraExpBala >= 0 ? "+" : ""}{ultraExpBala.toFixed(2)}R (Mín +0.20R)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-emerald-400 cursor-pointer disabled:opacity-30"
                />
              </div>

              {/* Supervivencia Monte Carlo */}
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 space-y-1.5">
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="text-slate-400">Supervivencia Monte Carlo (20 Balas):</span>
                  {ultraMcSurvival !== null ? (
                    <span className={`font-black ${ultraMcSurvival >= 95.0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {ultraMcSurvival.toFixed(1)}% (Mín 95%)
                    </span>
                  ) : (
                    <span className="text-slate-500 text-[11px]">SIN DATOS / NO EVIDENCE</span>
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
                  className="w-full accent-emerald-400 cursor-pointer disabled:opacity-30"
                />
              </div>
            </div>
          )}

          {/* Evaluate Action Button */}
          <button
            onClick={handleEvaluate}
            disabled={evaluating || !strategyId}
            className={`w-full py-3 px-4 rounded-xl text-xs font-mono font-black transition-all shadow-lg flex items-center justify-center gap-2 ${
              activeTrack === "TRACK_ULTRA"
                ? "bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-slate-950 shadow-emerald-500/20"
                : "bg-gradient-to-r from-sky-500 to-sky-600 hover:from-sky-400 hover:to-sky-500 text-slate-950 shadow-sky-500/20"
            } ${evaluating || !strategyId ? "opacity-60 cursor-not-allowed" : ""}`}
          >
            {evaluating ? (
              <span>EJECUTANDO EVIDENCE GATE AUDITOR...</span>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>⚡ EVALUAR CANDIDATO EN QVF</span>
              </>
            )}
          </button>
        </div>

        {/* RIGHT: GATE DECISION AUDIT CARD */}
        <div
          className={`bg-[#090d16]/90 border backdrop-blur-xl rounded-2xl p-6 shadow-xl flex flex-col justify-between space-y-6 transition-all ${
            result
              ? result.is_approved
                ? "border-emerald-500/50 shadow-emerald-500/10"
                : "border-rose-500/50 shadow-rose-500/10"
              : "border-white/[0.08]"
          }`}
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-black text-white flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Veredicto de la Compuerta EvidenceGate</span>
              </h3>
              {result && (
                <span className="text-xs font-mono text-slate-500">
                  {new Date(result.evaluated_at_utc_ms).toLocaleTimeString()}
                </span>
              )}
            </div>

            {!result ? (
              <div className="flex flex-col items-center justify-center text-center p-12 text-slate-500 space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-2xl">
                  🛡️
                </div>
                <div className="text-sm font-bold text-slate-400">Compuerta en Standby</div>
                <p className="text-xs text-slate-500 max-w-xs">
                  Selecciona una estrategia y pulsa &quot;EVALUAR CANDIDATO EN QVF&quot; para ejecutar la auditoría matemática en el backend.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Result Hero Pill */}
                <div
                  className={`p-4 rounded-2xl border flex items-center justify-between gap-4 ${
                    result.is_approved
                      ? "bg-emerald-950/30 border-emerald-500/40"
                      : "bg-rose-950/30 border-rose-500/40"
                  }`}
                >
                  <div>
                    <span
                      className={`text-[10px] font-mono font-bold uppercase tracking-wider block ${
                        result.is_approved ? "text-emerald-400" : "text-rose-400"
                      }`}
                    >
                      VEREDICTO EVIDENCE GATE
                    </span>
                    <div className="text-lg font-black text-white mt-0.5">
                      {result.is_approved ? "✓ APROBADO PARA CANDIDATO" : "✕ RECHAZADO"}
                    </div>
                  </div>
                  <div
                    className={`text-2xl font-black font-mono tabular-nums ${
                      result.is_approved ? "text-emerald-400" : "text-rose-400"
                    }`}
                  >
                    {result.score_pct}%
                  </div>
                </div>

                {/* Rejection Reasons if Any */}
                {result.rejection_reasons.length > 0 && (
                  <div className="bg-rose-950/20 border border-rose-500/30 rounded-xl p-4 space-y-2">
                    <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider block">
                      Violaciones Detectadas:
                    </span>
                    <ul className="pl-4 list-disc space-y-1 text-xs text-rose-300">
                      {result.rejection_reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Gate Metrics Breakdown */}
                <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-4 space-y-2">
                  <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider block">
                    Métricas de Compuerta:
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    {Object.entries(result.gate_metrics).map(([k, v]) => (
                      <div key={k} className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
                        <span className="text-slate-500 text-[10px] block">{k}</span>
                        <span className="font-bold text-white">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Provenance SHA-256 Hash */}
                <div className="bg-slate-950/90 rounded-xl border border-slate-800 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      Firma Criptográfica Inmutable (SHA-256):
                    </span>
                    <button
                      onClick={() => handleCopySignature(result.provenance_signature_sha256)}
                      className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-sky-400 hover:text-sky-300 transition"
                    >
                      {copiedHash ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedHash ? "Copiado" : "Copiar"}</span>
                    </button>
                  </div>
                  <code className="text-xs text-sky-400 font-mono block overflow-x-auto p-2.5 bg-[#030712] rounded-lg border border-slate-800 break-all">
                    {result.provenance_signature_sha256}
                  </code>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Footer Link */}
          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">Zero-Mocks Deterministic Ledger</span>
            <Link
              href="/ejecucion"
              className="text-sky-400 hover:text-sky-300 font-bold inline-flex items-center gap-1 transition"
            >
              <span>Ir a Ejecución Live</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
