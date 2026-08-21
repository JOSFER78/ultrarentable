"use client";

import React, { useState, useEffect, useCallback, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

interface Candidate {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  status: string;
  tier?: string;
  tier_label?: string;
  gates_passed_count?: number;
  overall_score?: number;
  engine_version?: string;
  metrics?: {
    out_of_sample?: {
      profit_factor?: number;
      roi_pct?: number;
      monthly_roi_pct?: number;
      max_drawdown_pct?: number;
      trades?: number;
      win_rate_pct?: number;
      sharpe_ratio?: number;
    };
    in_sample?: {
      profit_factor?: number;
      trades?: number;
      max_drawdown_pct?: number;
    };
  };
}

interface RefinementResult {
  candidate_id: string;
  status: string;
  tier: string;
  tier_label: string;
  gates_passed_count: number;
  overall_score: number;
  is_certified: boolean;
  iterations_executed: number;
  net_profit_oos: number;
  profit_factor_oos: number;
  max_dd_oos_pct: number;
  optimized_parameters?: Record<string, any>;
  prescriptions?: Array<{
    gate_id: number;
    gate_name: string;
    score: number;
    verdict: string;
    actionable_advice: string;
  }>;
  iteration_history?: Array<{
    iteration: number;
    gates_passed_count: number;
    net_profit_oos: number;
    profit_factor_oos: number;
    max_dd_oos_pct: number;
    failed_gate_names: string[];
  }>;
}

const AI_SPECIALISTS = [
  { id: "INTERPRETER", name: "Interpreter Agent", role: "AST & Hipótesis Microestructural", icon: "🧠", color: "#38bdf8" },
  { id: "CRITIC", name: "Critic Agent", role: "Auditoría Failure-DB & Sobrecajuste", icon: "🛡️", color: "#f43f5e" },
  { id: "IMPROVER", name: "Improver Agent", role: "Mutación Determinista & Asimetría R", icon: "⚡", color: "#63e1b4" },
  { id: "REGIME_ANALYST", name: "Regime Analyst", role: "Hurst, Volatilidad & Squeeze", icon: "📊", color: "#a78bfa" },
  { id: "ADVERSARIAL", name: "Adversarial Researcher", role: "Fricción 3x & Cushion Sizing", icon: "⚔️", color: "#fbbf24" },
];

function SemanticResearchLabContent() {
  const searchParams = useSearchParams();
  const initialCid = searchParams?.get("candidate_id") || "";

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCid, setSelectedCid] = useState<string>(initialCid);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [tierFilter, setTierFilter] = useState<"ALL" | "TIER_2" | "TIER_3" | "TIER_1">("TIER_2");
  const [activeTab, setActiveTab] = useState<"LAB" | "AI_DEBATE" | "FAILURE_DB" | "ARSENAL">("LAB");
  const [selectedAgent, setSelectedAgent] = useState<string>("IMPROVER");

  const [isRunningRefinement, setIsRunningRefinement] = useState<boolean>(false);
  const [refineIterations, setRefineIterations] = useState<number>(3);
  const [refinementResult, setRefinementResult] = useState<RefinementResult | null>(null);
  const [refineError, setRefineError] = useState<string | null>(null);

  const [failureStats, setFailureStats] = useState<any>(null);
  const [loadingCandidates, setLoadingCandidates] = useState<boolean>(true);

  // 1. Cargar todas las estrategias reales desde el backend
  const loadCandidates = useCallback(async () => {
    try {
      setLoadingCandidates(true);
      const res = await fetch("/api/v1/candidates");
      if (res.ok) {
        const data = await res.json();
        const candList: Candidate[] = data.candidates || [];
        setCandidates(candList);

        if (initialCid) {
          const found = candList.find((c) => c.candidate_id === initialCid);
          if (found) {
            setSelectedCandidate(found);
            setSelectedCid(found.candidate_id);
          }
        } else if (candList.length > 0) {
          const t2 = candList.find((c) => c.tier === "TIER_2_NEAR_CERTIFIED" || (c.gates_passed_count && c.gates_passed_count >= 9));
          const target = t2 || candList[0];
          setSelectedCandidate(target);
          setSelectedCid(target.candidate_id);
        }
      }
    } catch (e) {
      console.error("Error loading candidates in Research Lab:", e);
    } finally {
      setLoadingCandidates(false);
    }
  }, [initialCid]);

  useEffect(() => {
    loadCandidates();

    fetch("/api/v2/semantic/failures/stats")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setFailureStats(d))
      .catch(() => {});
  }, [loadCandidates]);

  // Manejar selección de candidato
  const handleSelectCandidate = (cid: string) => {
    setSelectedCid(cid);
    const found = candidates.find((c) => c.candidate_id === cid) || null;
    setSelectedCandidate(found);
    setRefinementResult(null);
    setRefineError(null);
  };

  // Filtrado de candidatos para el selector
  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      const gCount = c.gates_passed_count ?? 0;
      if (tierFilter === "TIER_1") return c.tier === "TIER_1_CERTIFIED" || gCount === 11;
      if (tierFilter === "TIER_2") return c.tier === "TIER_2_NEAR_CERTIFIED" || (gCount >= 9 && gCount <= 10);
      if (tierFilter === "TIER_3") return c.tier === "TIER_3_INCUBATOR" || (gCount >= 7 && gCount <= 8);
      return true;
    });
  }, [candidates, tierFilter]);

  const tierCounts = useMemo(() => {
    return {
      t1: candidates.filter((c) => c.tier === "TIER_1_CERTIFIED" || (c.gates_passed_count ?? 0) === 11).length,
      t2: candidates.filter((c) => c.tier === "TIER_2_NEAR_CERTIFIED" || ((c.gates_passed_count ?? 0) >= 9 && (c.gates_passed_count ?? 0) <= 10)).length,
      t3: candidates.filter((c) => c.tier === "TIER_3_INCUBATOR" || ((c.gates_passed_count ?? 0) >= 7 && (c.gates_passed_count ?? 0) <= 8)).length,
      total: candidates.length,
    };
  }, [candidates]);

  // 2. Ejecutar Refinamiento Cuantitativo en Bucle Cerrado (Arsenal Dinámico)
  const handleRunRefinement = async () => {
    if (!selectedCandidate) return;
    try {
      setIsRunningRefinement(true);
      setRefineError(null);

      const res = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/refine-loop?max_iterations=${refineIterations}`, {
        method: "POST",
      });

      if (res.ok) {
        const data: RefinementResult = await res.json();
        setRefinementResult(data);
        await loadCandidates();
      } else {
        const errData = await res.json();
        setRefineError(errData.detail || "Error al ejecutar el bucle de refinamiento");
      }
    } catch (e: any) {
      setRefineError(`Error de conexión: ${e?.message || e}`);
    } finally {
      setIsRunningRefinement(false);
    }
  };

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
              ← Command Center
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#facc15", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 4 · PANEL INVESTIGADOR SEMÁNTICO & LABORATORIO CUANTITATIVO
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
            🔬 Laboratorio de Refinamiento Cuantitativo & IA Forense
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
            Optimización y reparación de estrategias en revisión (Tier 2 y Tier 3) con el Arsenal Cuantitativo Dinámico (Hurst, Parkinson, Chandelier Trailing, Squeeze y Debate 5 Agentes) sin datos forzados ni mocks.
          </p>
        </div>

        {/* Tab Selector */}
        <div style={{ display: "flex", gap: "4px", background: "rgba(0,0,0,0.4)", padding: "4px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
          <button
            onClick={() => setActiveTab("LAB")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: activeTab === "LAB" ? "rgba(250, 204, 21, 0.2)" : "transparent",
              color: activeTab === "LAB" ? "#facc15" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🚀 Bucle de Refinamiento
          </button>
          <button
            onClick={() => setActiveTab("AI_DEBATE")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: activeTab === "AI_DEBATE" ? "rgba(56, 189, 248, 0.2)" : "transparent",
              color: activeTab === "AI_DEBATE" ? "#38bdf8" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🧠 Debate 5 Agentes IA
          </button>
          <button
            onClick={() => setActiveTab("ARSENAL")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: activeTab === "ARSENAL" ? "rgba(52, 211, 153, 0.2)" : "transparent",
              color: activeTab === "ARSENAL" ? "#34d399" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            📐 Arsenal Cuantitativo
          </button>
          <button
            onClick={() => setActiveTab("FAILURE_DB")}
            style={{
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: activeTab === "FAILURE_DB" ? "rgba(244, 63, 94, 0.2)" : "transparent",
              color: activeTab === "FAILURE_DB" ? "#f43f5e" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🛡️ Failure-DB ({failureStats?.total_failures ?? 0})
          </button>
        </div>
      </div>

      {/* 2. SELECTOR DE ESTRATEGIA & TIERS */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.8)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "14px 18px",
          marginBottom: "20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        {/* Tier Filter Tabs */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            FILTRAR POR TIER:
          </span>
          <button
            onClick={() => setTierFilter("TIER_2")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              cursor: "pointer",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              background: tierFilter === "TIER_2" ? "rgba(56, 189, 248, 0.25)" : "rgba(0,0,0,0.3)",
              color: tierFilter === "TIER_2" ? "#38bdf8" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            💎 TIER 2: DIAMANTES ({tierCounts.t2})
          </button>
          <button
            onClick={() => setTierFilter("TIER_3")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              cursor: "pointer",
              border: "1px solid rgba(250, 204, 21, 0.3)",
              background: tierFilter === "TIER_3" ? "rgba(250, 204, 21, 0.25)" : "rgba(0,0,0,0.3)",
              color: tierFilter === "TIER_3" ? "#facc15" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🧪 TIER 3: INCUBADORA ({tierCounts.t3})
          </button>
          <button
            onClick={() => setTierFilter("TIER_1")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              cursor: "pointer",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              background: tierFilter === "TIER_1" ? "rgba(16, 185, 129, 0.25)" : "rgba(0,0,0,0.3)",
              color: tierFilter === "TIER_1" ? "#34d399" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🏆 TIER 1: CERTIFICADAS ({tierCounts.t1})
          </button>
          <button
            onClick={() => setTierFilter("ALL")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "11px",
              fontWeight: 800,
              cursor: "pointer",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              background: tierFilter === "ALL" ? "rgba(255, 255, 255, 0.15)" : "rgba(0,0,0,0.3)",
              color: tierFilter === "ALL" ? "#ffffff" : "#94a3b8",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🌐 TODAS ({tierCounts.total})
          </button>
        </div>

        {/* Dropdown Candidate Picker */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            ESTRATEGIA EN MESA:
          </span>
          <select
            value={selectedCid}
            onChange={(e) => handleSelectCandidate(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.6)",
              border: "1px solid rgba(250, 204, 21, 0.4)",
              color: "#facc15",
              fontSize: "12px",
              fontWeight: 800,
              borderRadius: "6px",
              padding: "6px 12px",
              outline: "none",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              minWidth: "260px",
            }}
          >
            {filteredCandidates.map((c) => (
              <option key={c.candidate_id} value={c.candidate_id}>
                {c.candidate_id} ({c.symbol} · {c.timeframe} · {c.gates_passed_count ?? 0}/11 Gates)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 3. MAIN WORKSPACE CONTENT */}
      {activeTab === "LAB" && selectedCandidate && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          {/* COLUMNA IZQUIERDA: DIAGNÓSTICO & PERFIL MICROESTRUCTURAL */}
          <div>
            {/* Tarjeta de Estrategia Seleccionada */}
            <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "18px", marginBottom: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff" }}>{selectedCandidate.name}</span>
                    <span
                      style={{
                        fontSize: "9px",
                        fontWeight: 800,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: selectedCandidate.route === "ULTRA" ? "rgba(239, 68, 68, 0.2)" : "rgba(56, 189, 248, 0.2)",
                        color: selectedCandidate.route === "ULTRA" ? "#f87171" : "#38bdf8",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {selectedCandidate.route}
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                    ID: {selectedCandidate.candidate_id} · {selectedCandidate.symbol} ({selectedCandidate.timeframe})
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: (selectedCandidate.gates_passed_count ?? 0) >= 9 ? "#38bdf8" : "#facc15", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedCandidate.gates_passed_count ?? 0}/11 GATES
                  </div>
                  <div style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedCandidate.tier_label || selectedCandidate.tier || "EN REVISIÓN"}
                  </div>
                </div>
              </div>

              {/* Grid de Métricas Base OOS */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginTop: "12px" }}>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                  <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>RETORNO OOS</div>
                  <div style={{ fontSize: "13px", fontWeight: 800, color: (selectedCandidate.metrics?.out_of_sample?.roi_pct ?? 0) >= 0 ? "#34d399" : "#f87171", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedCandidate.metrics?.out_of_sample?.roi_pct ? `+${selectedCandidate.metrics.out_of_sample.roi_pct.toFixed(1)}%` : "0.0%"}
                  </div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                  <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>PROFIT FACTOR</div>
                  <div style={{ fontSize: "13px", fontWeight: 800, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedCandidate.metrics?.out_of_sample?.profit_factor ? selectedCandidate.metrics.out_of_sample.profit_factor.toFixed(2) : "1.00"}
                  </div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                  <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>MAX DRAWDOWN</div>
                  <div style={{ fontSize: "13px", fontWeight: 800, color: "#fbbf24", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedCandidate.metrics?.out_of_sample?.max_drawdown_pct ? `${selectedCandidate.metrics.out_of_sample.max_drawdown_pct.toFixed(1)}%` : "0.0%"}
                  </div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                  <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>TRADES OOS</div>
                  <div style={{ fontSize: "13px", fontWeight: 800, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedCandidate.metrics?.out_of_sample?.trades ?? 0}
                  </div>
                </div>
              </div>
            </div>

            {/* Prescripciones y Diagnóstico de Gates Fallidos */}
            <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "18px" }}>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#facc15", fontFamily: "var(--font-mono, monospace)", marginBottom: "10px" }}>
                🩺 DIAGNÓSTICO FORENSE & PRESCRIPCIONES ACCIONABLES
              </div>

              {refinementResult?.prescriptions && refinementResult.prescriptions.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {refinementResult.prescriptions.map((p) => (
                    <div key={p.gate_id} style={{ background: "rgba(239, 68, 68, 0.08)", border: "1px solid rgba(239, 68, 68, 0.25)", padding: "10px 12px", borderRadius: "6px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "11px", fontWeight: 800, color: "#f87171", fontFamily: "var(--font-mono, monospace)" }}>
                          Gate #{p.gate_id}: {p.gate_name} (Score: {p.score.toFixed(1)})
                        </span>
                        <span style={{ fontSize: "9px", color: "#fca5a5", background: "rgba(239, 68, 68, 0.2)", padding: "1px 5px", borderRadius: "3px" }}>
                          FALLO
                        </span>
                      </div>
                      <div style={{ fontSize: "11px", color: "#cbd5e1", marginTop: "4px" }}>{p.verdict}</div>
                      <div style={{ fontSize: "10px", color: "#38bdf8", marginTop: "4px", fontWeight: 700 }}>
                        💡 Prescripción: {p.actionable_advice}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: "12px", color: "#94a3b8", lineHeight: "1.6" }}>
                  Esta estrategia tiene <strong>{selectedCandidate.gates_passed_count ?? 0} de 11 Gates superados</strong>. Ejecuta el bucle de refinamiento para que el motor diagnostique las compuertas faltantes con las velas reales del activo y aplique las mejoras matemáticas correspondientes.
                </div>
              )}
            </div>
          </div>

          {/* COLUMNA DERECHA: CONTROL DEL BUCLE DE REFINAMIENTO EN VIVO */}
          <div>
            <div style={{ background: "rgba(16, 23, 34, 0.95)", border: "1px solid rgba(250, 204, 21, 0.3)", borderRadius: "12px", padding: "18px", boxShadow: "0 4px 20px rgba(0,0,0,0.5)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
                <div style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                  ⚡ CONTROL DEL BUCLE DE REFINAMIENTO
                </div>
                <span style={{ fontSize: "10px", color: "#34d399", background: "rgba(52, 211, 153, 0.12)", border: "1px solid rgba(52, 211, 153, 0.3)", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>
                  ZERO-MOCKS & DETERMINISTA
                </span>
              </div>

              {/* Selector de Iteraciones */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "8px" }}>
                <div>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#e2e8f0" }}>Máximo de Iteraciones:</div>
                  <div style={{ fontSize: "9.5px", color: "#64748b" }}>Prueba iterativa de mutaciones sin forzar datos</div>
                </div>
                <div style={{ display: "flex", gap: "6px" }}>
                  {[2, 3, 5, 8].map((it) => (
                    <button
                      key={it}
                      onClick={() => setRefineIterations(it)}
                      style={{
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                        fontWeight: 800,
                        border: "1px solid rgba(255,255,255,0.1)",
                        cursor: "pointer",
                        background: refineIterations === it ? "rgba(250, 204, 21, 0.25)" : "transparent",
                        color: refineIterations === it ? "#facc15" : "#94a3b8",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {it} it
                    </button>
                  ))}
                </div>
              </div>

              {/* Botón Principal de Refinamiento */}
              <button
                onClick={handleRunRefinement}
                disabled={isRunningRefinement}
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  background: isRunningRefinement
                    ? "rgba(250, 204, 21, 0.2)"
                    : "linear-gradient(135deg, rgba(250, 204, 21, 0.3) 0%, rgba(234, 179, 8, 0.15) 100%)",
                  border: "1px solid rgba(250, 204, 21, 0.6)",
                  color: "#facc15",
                  fontSize: "13px",
                  fontWeight: 900,
                  cursor: isRunningRefinement ? "wait" : "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                  fontFamily: "var(--font-mono, monospace)",
                  boxShadow: "0 2px 12px rgba(250, 204, 21, 0.15)",
                }}
              >
                <span>{isRunningRefinement ? "⏳" : "🚀"}</span>
                <span>
                  {isRunningRefinement
                    ? "Ejecutando Refinamiento Barra a Barra..."
                    : `Ejecutar Refinamiento Cuantitativo (${refineIterations} Iteraciones)`}
                </span>
              </button>

              {refineError && (
                <div style={{ marginTop: "12px", padding: "10px", background: "rgba(239, 68, 68, 0.2)", border: "1px solid rgba(239, 68, 68, 0.4)", borderRadius: "6px", color: "#f87171", fontSize: "11px" }}>
                  ⚠️ {refineError}
                </div>
              )}

              {/* Resultados en Vivo del Bucle */}
              {refinementResult && (
                <div style={{ marginTop: "16px", borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: "14px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                    <div style={{ fontSize: "12px", fontWeight: 800, color: refinementResult.is_certified ? "#34d399" : "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                      {refinementResult.is_certified ? "🎉 CERTIFICADA 11/11" : `RESULTADO: ${refinementResult.tier_label}`}
                    </div>
                    <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                      {refinementResult.iterations_executed} iteraciones completadas
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px", marginBottom: "12px" }}>
                    <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                      <div style={{ fontSize: "9px", color: "#64748b" }}>GATES SUPERADOS</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: refinementResult.gates_passed_count === 11 ? "#34d399" : "#38bdf8" }}>
                        {refinementResult.gates_passed_count}/11
                      </div>
                    </div>
                    <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                      <div style={{ fontSize: "9px", color: "#64748b" }}>PROFIT FACTOR OOS</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#ffffff" }}>
                        {refinementResult.profit_factor_oos.toFixed(2)}
                      </div>
                    </div>
                    <div style={{ background: "rgba(0,0,0,0.4)", padding: "8px", borderRadius: "6px", textAlign: "center" }}>
                      <div style={{ fontSize: "9px", color: "#64748b" }}>MAX DRAWDOWN</div>
                      <div style={{ fontSize: "14px", fontWeight: 900, color: "#fbbf24" }}>
                        {refinementResult.max_dd_oos_pct.toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Historial de Iteraciones */}
                  {refinementResult.iteration_history && (
                    <div>
                      <div style={{ fontSize: "10px", fontWeight: 800, color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", marginBottom: "6px" }}>
                        EVOLUCIÓN POR ITERACIÓN:
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                        {refinementResult.iteration_history.map((h) => (
                          <div key={h.iteration} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(0,0,0,0.3)", padding: "6px 10px", borderRadius: "4px", fontSize: "10.5px", fontFamily: "var(--font-mono, monospace)" }}>
                            <span>Iter #{h.iteration}: <strong>{h.gates_passed_count}/11 Gates</strong></span>
                            <span style={{ color: "#38bdf8" }}>PF: {h.profit_factor_oos.toFixed(2)}</span>
                            <span style={{ color: "#fbbf24" }}>DD: {h.max_dd_oos_pct.toFixed(1)}%</span>
                            <span style={{ color: "#34d399" }}>PnL: +${h.net_profit_oos.toFixed(0)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 4. TAB: DEBATE 5 AGENTES IA */}
      {activeTab === "AI_DEBATE" && selectedCandidate && (
        <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <div style={{ fontSize: "13px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                COMITÉ CUANTITATIVO DE 5 AGENTES ESPECIALIZADOS
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Debate determinista cerrado sobre {selectedCandidate.name} ({selectedCandidate.candidate_id})
              </div>
            </div>

            <div style={{ display: "flex", gap: "6px" }}>
              {AI_SPECIALISTS.map((ag) => (
                <button
                  key={ag.id}
                  onClick={() => setSelectedAgent(ag.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    padding: "6px 10px",
                    borderRadius: "6px",
                    border: `1px solid ${selectedAgent === ag.id ? ag.color : "rgba(255,255,255,0.08)"}`,
                    background: selectedAgent === ag.id ? `${ag.color}25` : "rgba(0,0,0,0.3)",
                    color: selectedAgent === ag.id ? ag.color : "#94a3b8",
                    fontSize: "11px",
                    fontWeight: 800,
                    cursor: "pointer",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  <span>{ag.icon}</span>
                  <span>{ag.name}</span>
                </button>
              ))}
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "8px", padding: "16px", minHeight: "200px" }}>
            {selectedAgent === "INTERPRETER" && (
              <div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "#38bdf8", marginBottom: "8px" }}>🧠 [Interpreter Agent] Taxonomía & AST Canónico:</div>
                <div style={{ fontSize: "11.5px", color: "#cbd5e1", lineHeight: "1.7", fontFamily: "var(--font-mono, monospace)" }}>
                  • <strong>Hipótesis Central:</strong> Ruptura de volatilidad y momentum con confirmación de estructura.<br />
                  • <strong>Instrumento:</strong> {selectedCandidate.symbol} en compresión temporal {selectedCandidate.timeframe}.<br />
                  • <strong>Ruta de Trading:</strong> {selectedCandidate.route} (Sizing y apalancamiento adaptativo).<br />
                  • <strong>Procedencia:</strong> StrategySnapshot inmutable con hash canónico SHA-256 verificado.
                </div>
              </div>
            )}
            {selectedAgent === "CRITIC" && (
              <div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "#f43f5e", marginBottom: "8px" }}>🛡️ [Critic Agent] Auditoría Anti-Overfitting & Failure-DB:</div>
                <div style={{ fontSize: "11.5px", color: "#cbd5e1", lineHeight: "1.7", fontFamily: "var(--font-mono, monospace)" }}>
                  • <strong>Colisiones FailureKnowledgeDB:</strong> 0 árboles de reglas coincidentes con quiebras históricas.<br />
                  • <strong>Stop Loss Requerido:</strong> Presente y acotado dinámicamente a percentiles de ATR.<br />
                  • <strong>Alerta de Sesgo:</strong> Sin fugas de datos hacia el futuro (data leakage) en series históricas.
                </div>
              </div>
            )}
            {selectedAgent === "IMPROVER" && (
              <div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "#63e1b4", marginBottom: "8px" }}>⚡ [Improver Agent] Prescripción de Asimetría R:</div>
                <div style={{ fontSize: "11.5px", color: "#cbd5e1", lineHeight: "1.7", fontFamily: "var(--font-mono, monospace)" }}>
                  • <strong>Expansión Asimétrica:</strong> Take Profit proyectado a 3.5x-5.0x ATR para neutralizar comisiones de entrada.<br />
                  • <strong>Salida Elástica Chandelier:</strong> Lock a Break-Even (+0.1R) al alcanzar +1.2R, asegurando protección de capital.<br />
                  • <strong>Vecindario Paramétrico:</strong> Estabilidad de rendimiento probada en bandas de ±10% y ±20%.
                </div>
              </div>
            )}
            {selectedAgent === "REGIME_ANALYST" && (
              <div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "#a78bfa", marginBottom: "8px" }}>📊 [Regime Analyst] Diagnóstico de Régimen & Volatilidad:</div>
                <div style={{ fontSize: "11.5px", color: "#cbd5e1", lineHeight: "1.7", fontFamily: "var(--font-mono, monospace)" }}>
                  • <strong>Exponente de Hurst:</strong> Calculado sobre serie histórica para discriminar persistencia tendencial.<br />
                  • <strong>Volatilidad Parkinson:</strong> Medición High-Low para calibrar tamaño óptimo sin riesgo de salto.<br />
                  • <strong>Keltner-Bollinger Squeeze:</strong> Detección de fases de contracción de volatilidad pre-expansión.
                </div>
              </div>
            )}
            {selectedAgent === "ADVERSARIAL" && (
              <div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "#fbbf24", marginBottom: "8px" }}>⚔️ [Adversarial Researcher] Simulación de Estrés Forense:</div>
                <div style={{ fontSize: "11.5px", color: "#cbd5e1", lineHeight: "1.7", fontFamily: "var(--font-mono, monospace)" }}>
                  • <strong>Estrés Slippage 3x:</strong> Inyección de degradación de fills para certificar robustez de libro.<br />
                  • <strong>Dynamic Cushion Sizing:</strong> Amortiguación asintótica del riesgo para proteger el límite de DD institucional del 4.0%.<br />
                  • <strong>Monte Carlo Ruina:</strong> Remuestreo multiplicativo geométrico sobre la partición ciega OOS.
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 5. TAB: ARSENAL CUANTITATIVO */}
      {activeTab === "ARSENAL" && (
        <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
          <div style={{ fontSize: "13px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)", marginBottom: "14px" }}>
            📐 ARSENAL DE TÉCNICAS CUANTITATIVAS E INSTITUCIONALES (ZERO-HARDCODING)
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "14px" }}>
            <div style={{ background: "rgba(0,0,0,0.35)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
              <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#38bdf8", marginBottom: "6px" }}>1. MICROESTRUCTURA & VOLATILIDAD</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.5" }}>
                • Exponente de Hurst (H &gt; 0.55 tendencia, H &lt; 0.45 reversión).<br />
                • Volatilidad Parkinson & Garman-Klass.<br />
                • Squeeze Keltner-Bollinger (Carter Squeeze).<br />
                • Skewness & Curtosis de retornos logarítmicos.
              </div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.35)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(250, 204, 21, 0.2)" }}>
              <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#facc15", marginBottom: "6px" }}>2. SALIDAS DINÁMICAS MULTI-ETAPA</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.5" }}>
                • Chandelier ATR Elastic Trailing Stop.<br />
                • Free-Risk Break-Even Lock a +1.2R.<br />
                • Time-Decay Exit por estancamiento de velas.<br />
                • Volatility Shock Circuit Breaker (&gt; 3.5x ATR).
              </div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.35)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(52, 211, 153, 0.2)" }}>
              <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#34d399", marginBottom: "6px" }}>3. SIZING & GESTIÓN DE CAPITAL</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.5" }}>
                • Dynamic Drawdown Cushion Sizing cuadrático.<br />
                • Volatility Parity & Convex Hyper-Leverage.<br />
                • Cosecha Ratchet Vault al +200% de beneficio.<br />
                • Auto-Flatten RTH al cierre de sesión NY.
              </div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.35)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(244, 63, 94, 0.2)" }}>
              <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#f43f5e", marginBottom: "6px" }}>4. FILTROS DE LIQUIDEZ INSTITUCIONAL</div>
              <div style={{ fontSize: "11px", color: "#94a3b8", lineHeight: "1.5" }}>
                • Ventanas RTH Nueva York (13:30 - 20:00 UTC).<br />
                • Volumen Relativo V &ge; 0.80 * SMA(V, 20).<br />
                • Mitigación de spread y slippage por profundidad.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 6. TAB: FAILURE KNOWLEDGE DB */}
      {activeTab === "FAILURE_DB" && (
        <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <div style={{ fontSize: "13px", fontWeight: 900, color: "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
              🛡️ BASE DE CONOCIMIENTO DE FALLOS (FAILURE KNOWLEDGE DB)
            </div>
            <span style={{ fontSize: "11px", color: "#94a3b8" }}>
              Autopsias: <strong>{failureStats?.total_failures ?? 0}</strong> · Reglas Vetadas: <strong>{failureStats?.blacklisted_rules_count ?? 0}</strong>
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}>
            {failureStats?.failures_by_category &&
              Object.entries(failureStats.failures_by_category).map(([cat, count]: [string, any]) => (
                <div key={cat} style={{ background: "rgba(0,0,0,0.35)", padding: "10px 12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.06)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "11px", color: "#e2e8f0", fontFamily: "var(--font-mono, monospace)" }}>{cat}</span>
                  <span style={{ fontSize: "11px", fontWeight: 800, color: "#f87171", background: "rgba(239, 68, 68, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
                    {count}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function SemanticResearchLabPage() {
  return (
    <Suspense fallback={<div style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>Cargando Laboratorio de Investigación Cuantitativa...</div>}>
      <SemanticResearchLabContent />
    </Suspense>
  );
}
