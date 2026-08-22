"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import ModuleMap from "@/components/ModuleMap";

interface Candidate {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  annualized_roi: number;
  max_drawdown: number;
  profit_factor: number;
  win_rate: number;
  total_trades: number;
  is_certified?: boolean;
}

interface MetaComponent {
  strategy_id: string;
  symbol: string;
  timeframe: string;
  route: string;
  weight_pct: number;
  individual_annualized_roi_pct: number;
  individual_max_dd_pct: number;
  individual_win_rate_pct: number;
  individual_profit_factor: number;
  role_in_ensemble: string;
  trades_count: number;
}

interface AgentDebate {
  agent: string;
  role: string;
  color?: string;
  findings: string[];
  [key: string]: unknown;
}

interface MetaEnsemble {
  ensemble_id: string;
  name: string;
  route: string;
  total_capital_usd: number;
  components: MetaComponent[];
  correlation_matrix: Record<string, Record<string, number>>;
  avg_cross_correlation: number;
  max_cross_correlation: number;
  combined_annualized_roi_pct: number;
  combined_monthly_roi_pct: number;
  combined_max_dd_pct: number;
  combined_profit_factor: number;
  combined_sharpe_ratio: number;
  diversification_ratio: number;
  combined_equity_curve: number[];
  agents_debate: AgentDebate[];
  consensus_verdict: string;
  consensus_score: number;
  canonical_hash: string;
}

interface CanonicalPortfolio {
  portfolio_id: string;
  name: string;
  description: string;
  target_route: string;
  account_size_usd?: number;
  base_capital_usd?: number;
  annualized_roi_pct: number;
  monthly_roi_pct: number;
  max_5d_drawdown_pct?: number;
  max_drawdown_pct?: number;
  profit_factor?: number;
  components: Array<{ symbol: string; timeframe: string; weight_pct?: number; allocation_pct?: number; role?: string; base_multiplier?: string }>;
  pass_rate_pct?: number;
}

interface AutonomousEnsemble {
  portfolio_id: string;
  name: string;
  route: string;
  symbols: string[];
  components_count: number;
  combined_annualized_roi_pct: number;
  combined_monthly_roi_pct: number;
  combined_max_dd_pct: number;
  combined_sharpe_ratio: number;
  combined_profit_factor: number;
  diversification_ratio: number;
  avg_cross_correlation: number;
  consensus_score: number;
  consensus_verdict: string;
  is_approved: boolean;
  created_at_utc: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function PortfolioStudioPage() {
  const [track, setTrack] = useState<"ULTRA" | "FONDEO">("ULTRA");
  const [activeTab, setActiveTab] = useState<"AUTONOMOUS_DAEMON" | "CUSTOM_STUDIO" | "CANONICAL_PRESETS">("AUTONOMOUS_DAEMON");
  
  // Autonomous Daemon State
  const [autonomousEnsembles, setAutonomousEnsembles] = useState<AutonomousEnsemble[]>([]);
  const [loadingAuto, setLoadingAuto] = useState(false);
  const [triggeringAuto, setTriggeringAuto] = useState(false);

  // Custom Studio State
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [isAssembling, setIsAssembling] = useState(false);
  const [currentEnsemble, setCurrentEnsemble] = useState<MetaEnsemble | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Presets State
  const [canonicalPresets, setCanonicalPresets] = useState<CanonicalPortfolio[]>([]);
  const [loadingPresets, setLoadingPresets] = useState(false);

  // Fetch autonomous ensembles
  const loadAutonomousEnsembles = async () => {
    setLoadingAuto(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/portfolios/autonomous-ensembles?route=${track}`);
      if (res.ok) {
        const data = await res.json();
        setAutonomousEnsembles(data);
      }
    } catch (err) {
      console.error("Error loading autonomous ensembles:", err);
    } finally {
      setLoadingAuto(false);
    }
  };

  useEffect(() => {
    loadAutonomousEnsembles();
  }, [track]);

  const handleTriggerAutonomousCycle = async () => {
    setTriggeringAuto(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/portfolios/trigger-autonomous-cycle?route=${track}`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok && data.status === "SUCCESS") {
        setAutonomousEnsembles(data.ensembles || []);
      }
    } catch (err) {
      setErrorMsg("Error ejecutando ciclo de síntesis: " + String(err));
    } finally {
      setTriggeringAuto(false);
    }
  };

  // Fetch available candidates
  useEffect(() => {
    async function loadCandidates() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/portfolios/available-candidates?route=${track}`);
        if (res.ok) {
          const data = await res.json();
          setCandidates(data);
          // Pre-select first 3 distinct symbol candidates if available
          const seen = new Set<string>();
          const initial: string[] = [];
          for (const c of data) {
            if (!seen.has(c.symbol) && initial.length < 3) {
              seen.add(c.symbol);
              initial.push(c.candidate_id);
            }
          }
          setSelectedCandidateIds(initial);
        }
      } catch (err) {
        console.error("Error loading candidates:", err);
      }
    }
    loadCandidates();
  }, [track]);

  // Fetch canonical presets
  useEffect(() => {
    async function loadPresets() {
      setLoadingPresets(true);
      try {
        const endpoint = track === "FONDEO" 
          ? `${API_BASE}/api/v1/portfolios/fondeo-sprints`
          : `${API_BASE}/api/v1/portfolios/ultra-hyperscale`;
        const res = await fetch(endpoint);
        if (res.ok) {
          const data = await res.json();
          setCanonicalPresets(data);
        }
      } catch (err) {
        console.error("Error loading presets:", err);
      } finally {
        setLoadingPresets(false);
      }
    }
    if (activeTab === "CANONICAL_PRESETS") {
      loadPresets();
    }
  }, [track, activeTab]);

  const selectedCandidates = useMemo(() => {
    return candidates.filter((c) => selectedCandidateIds.includes(c.candidate_id));
  }, [candidates, selectedCandidateIds]);

  const toggleSelectCandidate = (candidateId: string, symbol: string) => {
    setErrorMsg(null);
    if (selectedCandidateIds.includes(candidateId)) {
      setSelectedCandidateIds(selectedCandidateIds.filter((id) => id !== candidateId));
    } else {
      // Rule: Only 1 strategy per asset symbol
      const existingSymbol = selectedCandidates.find((c) => c.symbol === symbol);
      if (existingSymbol) {
        setErrorMsg(`Regla Multi-Activo: Ya seleccionaste una estrategia para '${symbol}'. Solo se permite 1 estrategia por activo.`);
        return;
      }
      setSelectedCandidateIds([...selectedCandidateIds, candidateId]);
    }
  };

  const handleAssembleAndDebate = async () => {
    if (selectedCandidateIds.length < 2) {
      setErrorMsg("Debes seleccionar al menos 2 estrategias en activos distintos para construir el Meta-Portafolio.");
      return;
    }
    setIsAssembling(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/portfolios/assemble-debate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: selectedCandidateIds,
          ensemble_name: `Meta-${track} Asymmetric Ensemble (${selectedCandidateIds.length} Activos)`,
          target_route: track,
          total_capital_usd: track === "ULTRA" ? selectedCandidateIds.length * 1000 : 50000,
        }),
      });
      const json = await res.json();
      if (res.ok && json.status === "SUCCESS") {
        setCurrentEnsemble(json.meta_ensemble);
      } else {
        setErrorMsg(json.detail || "Error ensamblando el Meta-Portafolio.");
      }
    } catch (err) {
      setErrorMsg("Error de conexión con el backend: " + String(err));
    } finally {
      setIsAssembling(false);
    }
  };

  return (
    <div className="page" style={{ padding: "20px 24px", maxWidth: 1600, margin: "0 auto" }}>
      {/* 0. ESTRATEGIAS TOP SUB-NAV BAR */}
      <EstrategiasHeaderNav />

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "11px", textDecoration: "none" }}>
              ← Command Center
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "10px", fontWeight: 800, color: "#ec4899", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 6 · META-ESTRATEGIA ENSAMBLADA & SINERGIA MULTI-ACTIVO
            </span>
          </div>
          <h1 style={{ fontSize: 28, fontWeight: 800, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 10 }}>
            <span>🧩 Meta-Estrategia Ensamblada (Portfolio de Portfolios)</span>
            <span style={{ fontSize: 13, padding: "4px 10px", borderRadius: 20, background: "rgba(236, 72, 153, 0.15)", color: "#ec4899", border: "1px solid rgba(236, 72, 153, 0.3)", fontFamily: "var(--font-mono, monospace)" }}>
              Sinergia Multi-Activo
            </span>
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 4 }}>
            Combina múltiples estrategias de <b>distintos activos descorrelacionados</b> (Cripto Perpetuos, CME Futuros, Forex) mediante Paridad de Riesgo Inversa y debate forense de 5 agentes para amortiguar drawdowns y maximizar rentabilidad conjunta.
          </p>
        </div>

        {/* Track Switcher */}
        <div style={{ display: "flex", background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 10, padding: 4, gap: 4 }}>
          <button
            onClick={() => { setTrack("ULTRA"); setCurrentEnsemble(null); }}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontWeight: 700,
              fontSize: 13,
              background: track === "ULTRA" ? "linear-gradient(135deg, #10b981, #059669)" : "transparent",
              color: track === "ULTRA" ? "#fff" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            🔥 TRACK ULTRA ($1k Balas)
          </button>
          <button
            onClick={() => { setTrack("FONDEO"); setCurrentEnsemble(null); }}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontWeight: 700,
              fontSize: 13,
              background: track === "FONDEO" ? "linear-gradient(135deg, #3b82f6, #2563eb)" : "transparent",
              color: track === "FONDEO" ? "#fff" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            🛡️ TRACK FONDEO ($50k Preservación)
          </button>
        </div>
      </div>

      <ModuleMap />

      {/* Tabs */}
      <div style={{ display: "flex", gap: 12, borderBottom: "1px solid var(--border)", marginTop: 24, marginBottom: 20 }}>
        <button
          onClick={() => setActiveTab("AUTONOMOUS_DAEMON")}
          style={{
            padding: "10px 18px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "AUTONOMOUS_DAEMON" ? "2px solid #ec4899" : "2px solid transparent",
            color: activeTab === "AUTONOMOUS_DAEMON" ? "var(--text-primary)" : "var(--text-muted)",
            fontWeight: activeTab === "AUTONOMOUS_DAEMON" ? 700 : 500,
            cursor: "pointer",
            fontSize: 14,
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>🤖 Síntesis Autónoma 24/7 (Sinergia Multi-Activo)</span>
          <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "10px", background: "rgba(236, 72, 153, 0.2)", color: "#ec4899", fontWeight: 800 }}>
            {autonomousEnsembles.length} COMB
          </span>
        </button>
        <button
          onClick={() => setActiveTab("CUSTOM_STUDIO")}
          style={{
            padding: "10px 18px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "CUSTOM_STUDIO" ? "2px solid #10b981" : "2px solid transparent",
            color: activeTab === "CUSTOM_STUDIO" ? "var(--text-primary)" : "var(--text-muted)",
            fontWeight: activeTab === "CUSTOM_STUDIO" ? 700 : 500,
            cursor: "pointer",
            fontSize: 14,
          }}
        >
          🎛️ Meta-Portfolio Studio Interactivo
        </button>
        <button
          onClick={() => setActiveTab("CANONICAL_PRESETS")}
          style={{
            padding: "10px 18px",
            background: "none",
            border: "none",
            borderBottom: activeTab === "CANONICAL_PRESETS" ? "2px solid #3b82f6" : "2px solid transparent",
            color: activeTab === "CANONICAL_PRESETS" ? "var(--text-primary)" : "var(--text-muted)",
            fontWeight: activeTab === "CANONICAL_PRESETS" ? 700 : 500,
            cursor: "pointer",
            fontSize: 14,
          }}
        >
          📦 Portafolios Canónicos Certificados
        </button>
      </div>

      {errorMsg && (
        <div style={{ padding: 12, borderRadius: 8, background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)", color: "#ef4444", marginBottom: 16, fontSize: 13 }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {activeTab === "AUTONOMOUS_DAEMON" && (
        <div>
          {/* Action and Daemon Header */}
          <div
            style={{
              background: "linear-gradient(135deg, rgba(236, 72, 153, 0.1), rgba(16, 185, 129, 0.05))",
              border: "1px solid rgba(236, 72, 153, 0.3)",
              borderRadius: 14,
              padding: "20px 24px",
              marginBottom: 24,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 16,
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#ec4899", boxShadow: "0 0 10px #ec4899" }} />
                <span style={{ fontSize: 13, fontWeight: 900, color: "#ec4899", letterSpacing: "1px", fontFamily: "var(--font-mono, monospace)" }}>
                  DEMONIO 24/7 MULTI-AGENTE AUTÓNOMO ACTIVO
                </span>
              </div>
              <h2 style={{ fontSize: 20, fontWeight: 800, margin: "0 0 4px", color: "var(--text-primary)" }}>
                Explorador de Ensambles & Sinergias Multi-Activo
              </h2>
              <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, maxWidth: 850 }}>
                El motor analiza de forma continua combinaciones de 2 a 5 submáquinas en activos ortogonales distintos (Cripto, CME Futuros, Forex), calcula la matriz de covarianza real, pondera por Paridad de Riesgo Inversa y somete cada combinación al veredicto de los 5 agentes.
              </p>
            </div>

            <button
              onClick={handleTriggerAutonomousCycle}
              disabled={triggeringAuto}
              style={{
                padding: "12px 22px",
                borderRadius: 10,
                border: "none",
                background: triggeringAuto ? "rgba(255,255,255,0.1)" : "linear-gradient(135deg, #ec4899, #be185d)",
                color: "#ffffff",
                fontWeight: 800,
                fontSize: 13,
                cursor: triggeringAuto ? "not-allowed" : "pointer",
                boxShadow: "0 4px 14px rgba(236, 72, 153, 0.35)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span>{triggeringAuto ? "⏳ Minando Combinaciones..." : "⚡ Disparar Ciclo de Exploración Multi-Agente"}</span>
            </button>
          </div>

          {/* Autonomous Results Grid */}
          {loadingAuto ? (
            <div style={{ padding: 60, textAlign: "center", color: "var(--text-muted)" }}>
              Cargando Meta-Portafolios explorados por el demonio autónomo...
            </div>
          ) : autonomousEnsembles.length === 0 ? (
            <div style={{ padding: 40, textAlign: "center", background: "var(--bg-panel)", borderRadius: 12, border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🧩</div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>No hay ensambles calculados para la ruta {track}</div>
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
                Haz clic en el botón superior para que el comité de 5 agentes explore y sintetice combinaciones óptimas.
              </p>
              <button
                onClick={handleTriggerAutonomousCycle}
                style={{ padding: "10px 20px", borderRadius: 8, background: "#ec4899", border: "none", color: "#fff", fontWeight: 700, cursor: "pointer" }}
              >
                ⚡ Iniciar Exploración Ahora
              </button>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 18 }}>
              {autonomousEnsembles.map((ens) => (
                <div
                  key={ens.portfolio_id}
                  style={{
                    background: "var(--bg-panel)",
                    border: `1px solid ${ens.is_approved ? "rgba(16, 185, 129, 0.4)" : "var(--border)"}`,
                    borderRadius: 12,
                    padding: 20,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    position: "relative",
                  }}
                >
                  <div>
                    {/* Header */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                      <div>
                        <div style={{ fontWeight: 800, fontSize: 16, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 6 }}>
                          <span>{ens.name}</span>
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono, monospace)", marginTop: 2 }}>
                          {ens.portfolio_id}
                        </div>
                      </div>
                      <span
                        style={{
                          fontSize: 10.5,
                          padding: "3px 8px",
                          borderRadius: 6,
                          background: ens.is_approved ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                          color: ens.is_approved ? "#10b981" : "#f59e0b",
                          fontWeight: 800,
                          border: `1px solid ${ens.is_approved ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
                        }}
                      >
                        {ens.is_approved ? "✅ CON SENSO 5/5" : "⚠️ REVISIÓN"}
                      </span>
                    </div>

                    {/* Metric Cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, background: "rgba(255,255,255,0.02)", padding: 12, borderRadius: 8, marginBottom: 14 }}>
                      <div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ROI Anual Combinado</div>
                        <div style={{ fontSize: 17, fontWeight: 800, color: ens.combined_annualized_roi_pct >= 0 ? "#10b981" : "#f87171", fontFamily: "var(--font-mono, monospace)" }}>
                          {ens.combined_annualized_roi_pct >= 0 ? `+${ens.combined_annualized_roi_pct}%` : `${ens.combined_annualized_roi_pct}%`}
                        </div>
                        <div style={{ fontSize: 10, color: "#6ee7b7" }}>
                          +{ens.combined_monthly_roi_pct}%/mes
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Drawdown Combinado</div>
                        <div style={{ fontSize: 17, fontWeight: 800, color: ens.combined_max_dd_pct <= 5.0 ? "#10b981" : (ens.combined_max_dd_pct <= 80.0 ? "#fbbf24" : "#f87171"), fontFamily: "var(--font-mono, monospace)" }}>
                          {ens.combined_max_dd_pct}%
                        </div>
                        <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                          Correlación: {ens.avg_cross_correlation.toFixed(2)}
                        </div>
                      </div>
                    </div>

                    {/* Secondary Metrics */}
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-muted)", background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: 6, marginBottom: 14 }}>
                      <span>Ratio Diversificación: <strong style={{ color: "#38bdf8" }}>{ens.diversification_ratio.toFixed(2)}x</strong></span>
                      <span>Sharpe Ratio: <strong style={{ color: "#34d399" }}>{ens.combined_sharpe_ratio}</strong></span>
                      <span>Score Agentes: <strong style={{ color: "#ec4899" }}>{ens.consensus_score}/100</strong></span>
                    </div>

                    {/* Symbols Tags */}
                    <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                      Activos Ortogonales:
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
                      {ens.symbols.map((sym, sIdx) => (
                        <span key={sIdx} style={{ fontSize: 10.5, padding: "2px 8px", borderRadius: 4, background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)", fontWeight: 700 }}>
                          💎 {sym}
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      // Switch to custom studio and assemble this combination
                      setActiveTab("CUSTOM_STUDIO");
                    }}
                    style={{
                      width: "100%",
                      padding: "10px",
                      borderRadius: 8,
                      border: "1px solid rgba(236, 72, 153, 0.4)",
                      background: "rgba(236, 72, 153, 0.1)",
                      color: "#ec4899",
                      fontWeight: 800,
                      fontSize: 12.5,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 6,
                    }}
                  >
                    <span>🔬 Inspeccionar y Ajustar en Studio Interactivo</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "CUSTOM_STUDIO" && (
        <div>
          {/* Step 1: Strategy Selection */}
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, marginBottom: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
                  1. Selección de Submáquinas (Regla: Máximo 1 por Activo)
                </h3>
                <p style={{ fontSize: 13, color: "var(--text-muted)", margin: "4px 0 0" }}>
                  Selecciona de 2 a 6 activos descorrelacionados para amortiguar drawdowns mutuos.
                </p>
              </div>
              <button
                onClick={handleAssembleAndDebate}
                disabled={isAssembling || selectedCandidateIds.length < 2}
                style={{
                  padding: "10px 20px",
                  borderRadius: 8,
                  border: "none",
                  background: selectedCandidateIds.length >= 2 ? "linear-gradient(135deg, #10b981, #059669)" : "var(--border)",
                  color: "#fff",
                  fontWeight: 700,
                  fontSize: 14,
                  cursor: selectedCandidateIds.length >= 2 ? "pointer" : "not-allowed",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  boxShadow: selectedCandidateIds.length >= 2 ? "0 4px 12px rgba(16, 185, 129, 0.3)" : "none",
                }}
              >
                {isAssembling ? "⏳ Ejecutando Backtests y Debate..." : `⚡ Ensamblar & Debatir (${selectedCandidateIds.length} Activos)`}
              </button>
            </div>

            {/* Candidates Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
              {candidates.map((c) => {
                const isSelected = selectedCandidateIds.includes(c.candidate_id);
                return (
                  <div
                    key={c.candidate_id}
                    onClick={() => toggleSelectCandidate(c.candidate_id, c.symbol)}
                    style={{
                      padding: 14,
                      borderRadius: 10,
                      border: isSelected ? "2px solid #10b981" : "1px solid var(--border)",
                      background: isSelected ? "rgba(16, 185, 129, 0.08)" : "rgba(255, 255, 255, 0.02)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <span style={{ fontWeight: 800, fontSize: 15, color: "var(--text-primary)" }}>{c.symbol}</span>
                      <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 12, background: "rgba(255, 255, 255, 0.08)", color: "var(--text-muted)" }}>
                        {c.timeframe}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)", marginBottom: 8, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {c.name}
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, fontSize: 12 }}>
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>ROI: </span>
                        <span style={{ fontWeight: 700, color: "#10b981" }}>+{c.annualized_roi?.toFixed(0)}%</span>
                      </div>
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>Max DD: </span>
                        <span style={{ fontWeight: 700, color: "#ef4444" }}>{c.max_drawdown?.toFixed(1)}%</span>
                      </div>
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>Profit Factor: </span>
                        <span style={{ fontWeight: 700 }}>{c.profit_factor?.toFixed(2)}</span>
                      </div>
                      <div>
                        <span style={{ color: "var(--text-muted)" }}>Win Rate: </span>
                        <span style={{ fontWeight: 700 }}>{c.win_rate?.toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Step 2: Debate & Portfolio Performance Output */}
          {currentEnsemble && (
            <div>
              {/* Scorecard Header */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14, marginBottom: 24 }}>
                <div style={{ padding: 16, background: "var(--bg-panel)", borderRadius: 10, border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>ROI Anual Combinado</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: "#10b981", marginTop: 4 }}>
                    +{currentEnsemble.combined_annualized_roi_pct}%
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    ROI Mensual: +{currentEnsemble.combined_monthly_roi_pct}%
                  </div>
                </div>

                <div style={{ padding: 16, background: "var(--bg-panel)", borderRadius: 10, border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Drawdown Combinado (OOS)</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: "#ef4444", marginTop: 4 }}>
                    {currentEnsemble.combined_max_dd_pct}%
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    vs ~{((currentEnsemble.components.reduce((acc, c) => acc + c.individual_max_dd_pct, 0)) / currentEnsemble.components.length).toFixed(1)}% promedio individual
                  </div>
                </div>

                <div style={{ padding: 16, background: "var(--bg-panel)", borderRadius: 10, border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Correlación Cruzada Media</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: currentEnsemble.avg_cross_correlation < 0.35 ? "#10b981" : "#f59e0b", marginTop: 4 }}>
                    {currentEnsemble.avg_cross_correlation.toFixed(2)}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    Ratio Diversificación: {currentEnsemble.diversification_ratio.toFixed(2)}x
                  </div>
                </div>

                <div style={{ padding: 16, background: "var(--bg-panel)", borderRadius: 10, border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Veredicto Consenso Agentes</div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: "#10b981", marginTop: 6, display: "flex", alignItems: "center", gap: 6 }}>
                    <span>✅ {currentEnsemble.consensus_verdict}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                    Score: {currentEnsemble.consensus_score} / 100
                  </div>
                </div>
              </div>

              {/* Component Allocation Table */}
              <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, marginBottom: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 14px" }}>
                  📊 Ponderación por Paridad de Riesgo Inversa (HRP)
                </h3>
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead>
                      <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left", color: "var(--text-muted)" }}>
                        <th style={{ padding: "8px 12px" }}>Activo</th>
                        <th style={{ padding: "8px 12px" }}>Timeframe</th>
                        <th style={{ padding: "8px 12px" }}>Peso Asignado</th>
                        <th style={{ padding: "8px 12px" }}>Rol Estructural</th>
                        <th style={{ padding: "8px 12px" }}>ROI Indiv.</th>
                        <th style={{ padding: "8px 12px" }}>Max DD Indiv.</th>
                        <th style={{ padding: "8px 12px" }}>Profit Factor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {currentEnsemble.components.map((comp) => (
                        <tr key={comp.strategy_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.05)" }}>
                          <td style={{ padding: "10px 12px", fontWeight: 700 }}>{comp.symbol}</td>
                          <td style={{ padding: "10px 12px", color: "var(--text-muted)" }}>{comp.timeframe}</td>
                          <td style={{ padding: "10px 12px" }}>
                            <span style={{ padding: "2px 8px", borderRadius: 6, background: "rgba(16, 185, 129, 0.15)", color: "#10b981", fontWeight: 700 }}>
                              {comp.weight_pct}%
                            </span>
                          </td>
                          <td style={{ padding: "10px 12px", color: "var(--text-secondary)" }}>{comp.role_in_ensemble}</td>
                          <td style={{ padding: "10px 12px", color: "#10b981", fontWeight: 600 }}>+{comp.individual_annualized_roi_pct}%</td>
                          <td style={{ padding: "10px 12px", color: "#ef4444", fontWeight: 600 }}>{comp.individual_max_dd_pct}%</td>
                          <td style={{ padding: "10px 12px" }}>{comp.individual_profit_factor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* 5-Agent Debate Panel */}
              <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, marginBottom: 24 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 16px", display: "flex", alignItems: "center", gap: 8 }}>
                  <span>🧠 Auditoría y Debate Forense de 5 Agentes de IA</span>
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 14 }}>
                  {currentEnsemble.agents_debate.map((agentData, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: 16,
                        borderRadius: 10,
                        border: "1px solid var(--border)",
                        background: "rgba(255, 255, 255, 0.02)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                        <span style={{ fontWeight: 800, fontSize: 14, color: agentData.color || "var(--text-primary)" }}>
                          {agentData.agent}
                        </span>
                        <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{agentData.role}</span>
                      </div>
                      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                        {agentData.findings.map((f, fIdx) => (
                          <li key={fIdx}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "CANONICAL_PRESETS" && (
        <div>
          {loadingPresets ? (
            <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>
              Cargando portafolios canónicos pre-certificados...
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 18 }}>
              {canonicalPresets.map((p) => (
                <div
                  key={p.portfolio_id}
                  style={{
                    background: "var(--bg-panel)",
                    border: "1px solid var(--border)",
                    borderRadius: 12,
                    padding: 20,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <span style={{ fontWeight: 800, fontSize: 17, color: "var(--text-primary)" }}>{p.name}</span>
                      <span style={{ fontSize: 11, padding: "3px 10px", borderRadius: 12, background: "rgba(16, 185, 129, 0.15)", color: "#10b981", fontWeight: 700 }}>
                        {p.target_route}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 14 }}>{p.description}</p>
                    
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, background: "rgba(255, 255, 255, 0.02)", padding: 12, borderRadius: 8, marginBottom: 14 }}>
                      <div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ROI Anual Proyectado</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: "#10b981" }}>+{p.annualized_roi_pct}%</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Max Drawdown</div>
                        <div style={{ fontSize: 18, fontWeight: 800, color: "#ef4444" }}>
                          {p.max_5d_drawdown_pct || p.max_drawdown_pct || 3.5}%
                        </div>
                      </div>
                    </div>

                    <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                      Componentes Multi-Activo:
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 14 }}>
                      {p.components.map((comp, idx) => (
                        <span key={idx} style={{ fontSize: 11, padding: "2px 8px", borderRadius: 6, background: "rgba(255, 255, 255, 0.06)", border: "1px solid var(--border)" }}>
                          <b>{comp.symbol}</b> ({comp.timeframe}) {comp.weight_pct ? `• ${comp.weight_pct}%` : ""}
                        </span>
                      ))}
                    </div>
                  </div>

                  <button
                    style={{
                      width: "100%",
                      padding: "10px",
                      borderRadius: 8,
                      border: "1px solid #10b981",
                      background: "rgba(16, 185, 129, 0.1)",
                      color: "#10b981",
                      fontWeight: 700,
                      fontSize: 13,
                      cursor: "pointer",
                    }}
                    onClick={() => {
                      setActiveTab("CUSTOM_STUDIO");
                    }}
                  >
                    🔍 Inspeccionar en Studio
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
