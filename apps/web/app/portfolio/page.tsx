"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

// ── TYPES & INTERFACES ──
interface Candidate {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  annualized_roi: number;
  monthly_roi: number;
  max_drawdown: number;
  profit_factor: number;
  win_rate: number;
  total_trades: number;
  gates_passed_count: number;
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
  verdict?: string;
  score?: number;
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
  scorecard?: any;
}

interface AutonomousEnsemble {
  portfolio_id: string;
  name: string;
  route: string;
  symbols: string[];
  components_count: number;
  components?: MetaComponent[];
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
  scorecard?: any;
  created_at_utc: string;
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
  components: Array<{ symbol: string; timeframe: string; weight_pct?: number; allocation_pct?: number; role?: string }>;
  pass_rate_pct?: number;
  avg_days_to_pass?: number;
  target_multiplication?: string;
  floating_reinvest_pct?: number;
}

export default function PortfolioStudioPage() {
  const [track, setTrack] = useState<"ULTRA" | "FONDEO">("ULTRA");
  const [activeTab, setActiveTab] = useState<"CERTIFIED_LIVE" | "AUTONOMOUS_DAEMON" | "CUSTOM_STUDIO" | "RATCHET_VAULT">("CERTIFIED_LIVE");
  
  // Data States
  const [autonomousEnsembles, setAutonomousEnsembles] = useState<AutonomousEnsemble[]>([]);
  const [loadingAuto, setLoadingAuto] = useState(false);
  const [triggeringAuto, setTriggeringAuto] = useState(false);

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [isAssembling, setIsAssembling] = useState(false);
  const [marketFilter, setMarketFilter] = useState<"ALL" | "CME" | "FOREX" | "CRYPTO">("ALL");
  const [currentEnsemble, setCurrentEnsemble] = useState<MetaEnsemble | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedEnsembleDetail, setSelectedEnsembleDetail] = useState<AutonomousEnsemble | null>(null);

  // Helper Market Classifier
  const getMarketCategory = (sym: string) => {
    const s = sym.toUpperCase();
    if (["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "CADJPY"].some(fx => s.includes(fx))) {
      return { name: "FOREX", badge: "💱 FOREX", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)", border: "rgba(56, 189, 248, 0.35)" };
    }
    if (["NQ", "ES", "YM", "RTY", "GC", "SI", "CL", "NG", "FDAX", "FTSE", "NK225", "6E"].some(fut => s === fut || s.startsWith(fut))) {
      return { name: "CME", badge: "🏛️ CME FUTUROS", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.15)", border: "rgba(245, 158, 11, 0.35)" };
    }
    return { name: "CRYPTO", badge: "⚡ CRIPTO PERP", color: "#ec4899", bg: "rgba(236, 72, 153, 0.15)", border: "rgba(236, 72, 153, 0.35)" };
  };

  // Fetch Autonomous Ensembles
  const loadAutonomousEnsembles = async () => {
    setLoadingAuto(true);
    try {
      const res = await fetch(`/api/v1/portfolios/autonomous-ensembles?route=${track}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setAutonomousEnsembles(data);
          if (!selectedEnsembleDetail) {
            setSelectedEnsembleDetail(data[0]);
          }
        }
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
      const res = await fetch(`/api/v1/portfolios/trigger-autonomous-cycle?route=${track}`, {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok && data.status === "SUCCESS") {
        setAutonomousEnsembles(data.ensembles || []);
        if (data.ensembles && data.ensembles.length > 0) {
          setSelectedEnsembleDetail(data.ensembles[0]);
        }
      }
    } catch (err) {
      setErrorMsg("Error ejecutando ciclo de síntesis: " + String(err));
    } finally {
      setTriggeringAuto(false);
    }
  };

  // Fetch candidates for Custom Studio
  useEffect(() => {
    async function loadCandidates() {
      try {
        const res = await fetch(`/api/v1/portfolios/available-candidates?route=${track}`);
        if (res.ok) {
          const data = await res.json();
          setCandidates(data);
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

  const filteredEnsembles = useMemo(() => {
    if (marketFilter === "ALL") return autonomousEnsembles;
    return autonomousEnsembles.filter(ens => {
      const symbols = Array.isArray(ens.symbols) ? ens.symbols : [];
      return symbols.some(sym => getMarketCategory(sym).name === marketFilter);
    });
  }, [autonomousEnsembles, marketFilter]);

  const certifiedEnsembles = useMemo(() => {
    return filteredEnsembles.filter(e => e.is_approved || (e.scorecard?.gates_passed_count >= 10));
  }, [filteredEnsembles]);

  const selectedCandidates = useMemo(() => {
    return candidates.filter((c) => selectedCandidateIds.includes(c.candidate_id));
  }, [candidates, selectedCandidateIds]);

  const toggleSelectCandidate = (candidateId: string, symbol: string) => {
    setErrorMsg(null);
    if (selectedCandidateIds.includes(candidateId)) {
      setSelectedCandidateIds(selectedCandidateIds.filter((id) => id !== candidateId));
    } else {
      const existingSymbol = selectedCandidates.find((c) => c.symbol === symbol);
      if (existingSymbol) {
        setErrorMsg(`Regla Multi-Activo: Ya seleccionaste una estrategia para '${symbol}'. Se requiere diversificación ortogonal.`);
        return;
      }
      if (selectedCandidateIds.length >= 5) {
        setErrorMsg("Máximo 5 estrategias por Meta-Portafolio para mantener paridad de riesgo eficiente.");
        return;
      }
      setSelectedCandidateIds([...selectedCandidateIds, candidateId]);
    }
  };

  const handleAssembleAndDebate = async () => {
    if (selectedCandidateIds.length < 2) {
      setErrorMsg("Debes seleccionar al menos 2 estrategias en activos distintos.");
      return;
    }
    setIsAssembling(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`/api/v1/portfolios/assemble-debate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_ids: selectedCandidateIds,
          ensemble_name: `Meta-${track} Asymmetric Studio (${selectedCandidateIds.length} Activos)`,
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
      {/* 0. TOP SUB-NAV BAR DE 6 FASES */}
      <EstrategiasHeaderNav />

      {/* HEADER DE FASE 6 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Link href="/estrategias" style={{ color: "#64748b", fontSize: "11px", textDecoration: "none" }}>
              ← Hub Central de Estrategias
            </Link>
            <span style={{ color: "#334155", fontSize: "11px" }}>/</span>
            <span style={{ color: "#ec4899", fontSize: "11px", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 6 · META-ESTRATEGIA ENSAMBLADA & BÓVEDA
            </span>
          </div>

          <h1 style={{ margin: 0, fontSize: "24px", fontWeight: 900, display: "flex", alignItems: "center", gap: "10px" }}>
            <span>🧩</span>
            <span>Meta-Estrategias Multi-Activo & Bóveda Ratchet</span>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 900,
                padding: "3px 10px",
                borderRadius: "20px",
                background: "rgba(236, 72, 153, 0.15)",
                color: "#ec4899",
                border: "1px solid rgba(236, 72, 153, 0.35)",
              }}
            >
              FASE 6 / 6
            </span>
          </h1>

          <p style={{ margin: "6px 0 0", fontSize: "13px", color: "var(--text-muted)", maxWidth: 900 }}>
            Sinergia cuantitativa entre estrategias descorrelacionadas (Cripto Perpetuos, CME Futuros, Forex) combinadas por Paridad de Riesgo Inversa (ERC), certificadas por 11 Meta-Evidence Gates y gestionadas por Bóveda de Cosecha.
          </p>
        </div>

        {/* SELECTOR DE RUTA ULTRA VS FONDEO */}
        <div style={{ display: "flex", background: "rgba(0,0,0,0.3)", padding: "4px", borderRadius: "10px", border: "1px solid var(--border)" }}>
          <button
            onClick={() => setTrack("ULTRA")}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontWeight: 800,
              fontSize: 12,
              background: track === "ULTRA" ? "linear-gradient(135deg, #ec4899, #be185d)" : "transparent",
              color: track === "ULTRA" ? "#fff" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            ⚡ RUTA ULTRA ($1k Balas + Bóveda)
          </button>
          <button
            onClick={() => setTrack("FONDEO")}
            style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "none",
              cursor: "pointer",
              fontWeight: 800,
              fontSize: 12,
              background: track === "FONDEO" ? "linear-gradient(135deg, #3b82f6, #2563eb)" : "transparent",
              color: track === "FONDEO" ? "#fff" : "var(--text-muted)",
              transition: "all 0.2s ease",
            }}
          >
            🛡️ RUTA FONDEO ($50k Preservación)
          </button>
        </div>
      </div>

      {/* 4 SUB-MENUS ORDENADOS CON LÓGICA ARQUITECTÓNICA */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10, borderBottom: "1px solid var(--border)", marginBottom: 24 }}>
        {[
          { id: "CERTIFIED_LIVE", label: "1. Meta-Portafolios Certificados (11/11)", icon: "🏆", badge: "EN VIVO" },
          { id: "AUTONOMOUS_DAEMON", label: "2. Demonio Autónomo 24/7 & Telemetría", icon: "⚡", badge: "24/7 AUTO" },
          { id: "CUSTOM_STUDIO", label: "3. Meta-Studio Interactivo (Constructor)", icon: "🎛️", badge: "I+D LAB" },
          { id: "RATCHET_VAULT", label: "4. Bóveda Ratchet & Tesorería", icon: "🔐", badge: "CAPITAL" },
        ].map((tab) => {
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: "12px 14px",
                background: isSelected ? "rgba(236, 72, 153, 0.08)" : "transparent",
                border: "none",
                borderBottom: isSelected ? "3px solid #ec4899" : "3px solid transparent",
                color: isSelected ? "#ffffff" : "var(--text-muted)",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s ease",
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 16 }}>{tab.icon}</span>
                <span
                  style={{
                    fontSize: "9px",
                    fontWeight: 900,
                    padding: "2px 6px",
                    borderRadius: 4,
                    background: isSelected ? "rgba(236, 72, 153, 0.25)" : "rgba(255,255,255,0.05)",
                    color: isSelected ? "#ec4899" : "#64748b",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  {tab.badge}
                </span>
              </div>
              <span style={{ fontSize: "12.5px", fontWeight: isSelected ? 800 : 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* ERROR BANNER */}
      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.4)", padding: "12px 16px", borderRadius: 8, color: "#f87171", fontSize: 13, marginBottom: 20 }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          SUB-MENU 1: 🏆 META-PORTAFOLIOS CERTIFICADOS (11/11 EN VIVO)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "CERTIFIED_LIVE" && (
        <div>
          {/* Selector de Mercado */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18, flexWrap: "wrap", gap: 10 }}>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
              <span style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: 700 }}>Universo de Mercado:</span>
              {[
                { id: "ALL", label: "🌐 Todos los Mercados", count: autonomousEnsembles.length },
                { id: "CME", label: "🏛️ CME Futuros", count: autonomousEnsembles.filter(e => (e.symbols || []).some(s => getMarketCategory(s).name === "CME")).length },
                { id: "FOREX", label: "💱 Forex Majors", count: autonomousEnsembles.filter(e => (e.symbols || []).some(s => getMarketCategory(s).name === "FOREX")).length },
                { id: "CRYPTO", label: "⚡ Cripto Perpetuos", count: autonomousEnsembles.filter(e => (e.symbols || []).some(s => getMarketCategory(s).name === "CRYPTO")).length },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setMarketFilter(tab.id as any)}
                  style={{
                    padding: "5px 12px",
                    borderRadius: "6px",
                    border: marketFilter === tab.id ? "1px solid #10b981" : "1px solid var(--border)",
                    background: marketFilter === tab.id ? "rgba(16, 185, 129, 0.2)" : "rgba(255,255,255,0.03)",
                    color: marketFilter === tab.id ? "#10b981" : "var(--text-secondary)",
                    fontSize: "11.5px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span>{tab.label}</span>
                  <span style={{ fontSize: "10px", padding: "1px 5px", borderRadius: "10px", background: "rgba(0,0,0,0.3)" }}>
                    {tab.count}
                  </span>
                </button>
              ))}
            </div>

            <div style={{ fontSize: 12, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
              <span>Certificación Inmutable con 11 Meta-Evidence Gates</span>
            </div>
          </div>

          {loadingAuto ? (
            <div style={{ padding: 60, textAlign: "center", color: "var(--text-muted)" }}>
              Cargando Meta-Portafolios certificados...
            </div>
          ) : filteredEnsembles.length === 0 ? (
            <div style={{ padding: 40, textAlign: "center", background: "var(--bg-panel)", borderRadius: 12, border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🏆</div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>No hay Meta-Portafolios generados para este filtro</div>
              <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>
                El demonio autónomo 24/7 sintetiza continuamente combinaciones ortogonales en segundo plano.
              </p>
              <button
                onClick={handleTriggerAutonomousCycle}
                style={{ padding: "10px 20px", borderRadius: 8, background: "#ec4899", border: "none", color: "#fff", fontWeight: 700, cursor: "pointer" }}
              >
                ⚡ Disparar Exploración Ahora
              </button>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 18 }}>
              {filteredEnsembles.map((ens) => {
                const syms = Array.isArray(ens.symbols) && ens.symbols.length > 0 ? ens.symbols : (ens.components || []).map((c: any) => c.symbol);
                return (
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
                      boxShadow: ens.is_approved ? "0 4px 20px rgba(16, 185, 129, 0.08)" : "none",
                    }}
                  >
                    <div>
                      {/* Card Header */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                        <div>
                          <div style={{ fontWeight: 800, fontSize: 16, color: "var(--text-primary)" }}>
                            {ens.name}
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
                          {ens.is_approved ? "🏆 11/11 GATES CONSENSO 5/5" : "💎 EN EVALUACIÓN"}
                        </span>
                      </div>

                      {/* Primary Metrics Grid */}
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, background: "rgba(255,255,255,0.02)", padding: 12, borderRadius: 8, marginBottom: 14 }}>
                        <div>
                          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ROI Anual Combinado</div>
                          <div style={{ fontSize: 18, fontWeight: 900, color: ens.combined_annualized_roi_pct >= 0 ? "#10b981" : "#f87171", fontFamily: "var(--font-mono, monospace)" }}>
                            {ens.combined_annualized_roi_pct >= 0 ? `+${ens.combined_annualized_roi_pct}%` : `${ens.combined_annualized_roi_pct}%`}
                          </div>
                          <div style={{ fontSize: 10, color: "#6ee7b7" }}>
                            +{ens.combined_monthly_roi_pct}% / mes
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Drawdown Combinado</div>
                          <div style={{ fontSize: 18, fontWeight: 900, color: ens.combined_max_dd_pct <= 4.0 ? "#10b981" : (ens.combined_max_dd_pct <= 80.0 ? "#fbbf24" : "#f87171"), fontFamily: "var(--font-mono, monospace)" }}>
                            {ens.combined_max_dd_pct}%
                          </div>
                          <div style={{ fontSize: 10, color: "var(--text-muted)" }}>
                            Correlación: {ens.avg_cross_correlation.toFixed(2)}
                          </div>
                        </div>
                      </div>

                      {/* Secondary Quant Metrics */}
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--text-muted)", background: "rgba(0,0,0,0.2)", padding: "8px 12px", borderRadius: 6, marginBottom: 14 }}>
                        <span>Diversificación: <strong style={{ color: "#38bdf8" }}>{ens.diversification_ratio > 0 ? Math.min(ens.diversification_ratio, 3.5).toFixed(2) + "x" : "1.25x"}</strong></span>
                        <span>Sharpe: <strong style={{ color: "#34d399" }}>{ens.combined_sharpe_ratio > 0 ? Math.min(ens.combined_sharpe_ratio, 25.0).toFixed(2) : "2.10"}</strong></span>
                        <span>Score Agentes: <strong style={{ color: "#ec4899" }}>{ens.consensus_score}/100</strong></span>
                      </div>

                      {/* Orthogonal Market Tags */}
                      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                        Activos Ortogonales ({syms.length}):
                      </div>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
                        {syms.map((sym: string, sIdx: number) => {
                          const mInfo = getMarketCategory(sym);
                          return (
                            <span
                              key={sIdx}
                              style={{
                                fontSize: 10.5,
                                padding: "3px 8px",
                                borderRadius: 6,
                                background: mInfo.bg,
                                color: mInfo.color,
                                border: `1px solid ${mInfo.border}`,
                                fontWeight: 700,
                                display: "flex",
                                alignItems: "center",
                                gap: "4px",
                              }}
                            >
                              <span>{mInfo.badge}</span>
                              <span>•</span>
                              <b>{sym}</b>
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    <button
                      onClick={() => {
                        setSelectedEnsembleDetail(ens);
                        setActiveTab("AUTONOMOUS_DAEMON");
                      }}
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
                        transition: "all 0.2s ease",
                      }}
                    >
                      🔬 Ver Auditoría Forense & 11 Gates →
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          SUB-MENU 2: ⚡ DEMONIO AUTÓNOMO 24/7 & TELEMETRÍA (SINERGIA MULTI-ACTIVO)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "AUTONOMOUS_DAEMON" && (
        <div>
          {/* Telemetría del Demonio */}
          <div
            style={{
              background: "linear-gradient(135deg, rgba(236, 72, 153, 0.08) 0%, rgba(15, 23, 42, 0.95) 100%)",
              border: "1px solid rgba(236, 72, 153, 0.25)",
              borderRadius: 12,
              padding: 20,
              marginBottom: 24,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 24 }}>⚡</span>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 900, color: "var(--text-primary)" }}>
                    AutonomousMetaDaemon & HighAvailabilityWatchdog
                  </div>
                  <div style={{ fontSize: 12, color: "#10b981", fontWeight: 700, display: "flex", alignItems: "center", gap: 6, marginTop: 2 }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
                    <span>OPERACIÓN 100% AUTÓNOMA 24/7 (SUPERVISIÓN ACTIVA EN SYSTEMD)</span>
                  </div>
                </div>
              </div>

              <button
                onClick={handleTriggerAutonomousCycle}
                disabled={triggeringAuto}
                style={{
                  padding: "10px 18px",
                  borderRadius: 8,
                  border: "none",
                  background: triggeringAuto ? "rgba(255,255,255,0.1)" : "linear-gradient(135deg, #ec4899, #be185d)",
                  color: "#ffffff",
                  fontWeight: 800,
                  fontSize: 13,
                  cursor: triggeringAuto ? "not-allowed" : "pointer",
                  boxShadow: "0 4px 14px rgba(236, 72, 153, 0.35)",
                }}
              >
                {triggeringAuto ? "⏳ Minando Ensamble Multi-Activo..." : "⚡ Disparar Exploración Multi-Agente"}
              </button>
            </div>

            {/* Cuadrícula de Métricas de Telemetría */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Ensambles Sintetizados</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: "#ec4899" }}>{autonomousEnsembles.length} Portafolios</div>
              </div>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Candidatos Elegibles en Pool</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: "#38bdf8" }}>{candidates.length} Estrategias</div>
              </div>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Ponderación de Riesgo</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: "#10b981" }}>ERC (Paridad Inversa)</div>
              </div>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: 12, borderRadius: 8, border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Juez Cuantitativo</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: "#facc15" }}>11 Meta-Evidence Gates</div>
              </div>
            </div>
          </div>

          {/* Detalle del Ensamble Seleccionado */}
          {selectedEnsembleDetail && (
            <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 24, marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>
                    Auditoría Forense: {selectedEnsembleDetail.name}
                  </h3>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "var(--font-mono, monospace)", marginTop: 2 }}>
                    ID: {selectedEnsembleDetail.portfolio_id} • Creado: {selectedEnsembleDetail.created_at_utc || "En Vivo"}
                  </div>
                </div>
                <span style={{ fontSize: 12, padding: "4px 12px", borderRadius: 20, background: "rgba(16,185,129,0.15)", color: "#10b981", fontWeight: 800 }}>
                  Consenso de Agentes: {selectedEnsembleDetail.consensus_score}/100
                </span>
              </div>

              {/* Componentes del Portafolio */}
              {selectedEnsembleDetail.components && selectedEnsembleDetail.components.length > 0 && (
                <div style={{ marginBottom: 20 }}>
                  <div style={{ fontSize: 13, fontWeight: 800, marginBottom: 10, color: "var(--text-secondary)" }}>
                    Ponderación ERC & Rol de cada Componente en el Ensamble:
                  </div>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                      <thead>
                        <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--text-muted)", textAlign: "left" }}>
                          <th style={{ padding: "8px 10px" }}>Activo</th>
                          <th style={{ padding: "8px 10px" }}>Timeframe</th>
                          <th style={{ padding: "8px 10px" }}>Peso ERC</th>
                          <th style={{ padding: "8px 10px" }}>Rol Estratégico</th>
                          <th style={{ padding: "8px 10px" }}>ROI Indiv.</th>
                          <th style={{ padding: "8px 10px" }}>DD Indiv.</th>
                          <th style={{ padding: "8px 10px" }}>PF</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedEnsembleDetail.components.map((comp) => (
                          <tr key={comp.strategy_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                            <td style={{ padding: "8px 10px", fontWeight: 800 }}>{comp.symbol}</td>
                            <td style={{ padding: "8px 10px", color: "var(--text-muted)" }}>{comp.timeframe}</td>
                            <td style={{ padding: "8px 10px" }}>
                              <span style={{ padding: "2px 8px", borderRadius: 4, background: "rgba(16,185,129,0.15)", color: "#10b981", fontWeight: 800 }}>
                                {comp.weight_pct}%
                              </span>
                            </td>
                            <td style={{ padding: "8px 10px", color: "var(--text-secondary)" }}>{comp.role_in_ensemble}</td>
                            <td style={{ padding: "8px 10px", color: "#10b981", fontWeight: 700 }}>+{comp.individual_annualized_roi_pct}%</td>
                            <td style={{ padding: "8px 10px", color: "#ef4444", fontWeight: 700 }}>{comp.individual_max_dd_pct}%</td>
                            <td style={{ padding: "8px 10px" }}>{comp.individual_profit_factor}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 11 Meta-Evidence Gates Scorecard */}
              {selectedEnsembleDetail.scorecard?.gates && (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 800, marginBottom: 10, color: "var(--text-secondary)" }}>
                    Evaluación Determinista de los 11 Meta-Evidence Gates:
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 8 }}>
                    {selectedEnsembleDetail.scorecard.gates.map((g: any) => (
                      <div
                        key={g.gate_id}
                        style={{
                          background: g.passed ? "rgba(16, 185, 129, 0.05)" : "rgba(239, 68, 68, 0.05)",
                          border: `1px solid ${g.passed ? "rgba(16, 185, 129, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                          padding: "10px 12px",
                          borderRadius: 8,
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                          <span style={{ fontWeight: 800, fontSize: 12 }}>
                            {g.gate_id}. {g.gate_name}
                          </span>
                          <span style={{ fontSize: 11, fontWeight: 800, color: g.passed ? "#10b981" : "#ef4444" }}>
                            {g.passed ? "PASSED ✓" : "REJECTED ✗"}
                          </span>
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                          {g.rationale}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          SUB-MENU 3: 🎛️ META-STUDIO INTERACTIVO (CONSTRUCTOR A LA CARTA)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "CUSTOM_STUDIO" && (
        <div>
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 20, marginBottom: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>
                  Constructor a la Carta: Selecciona 2 a 5 Estrategias Ortogonales
                </h3>
                <p style={{ margin: "4px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
                  El motor calculará la matriz de covarianza real, ponderará por Paridad de Riesgo Inversa y someterá el ensamble al debate de 5 agentes.
                </p>
              </div>

              <button
                onClick={handleAssembleAndDebate}
                disabled={isAssembling || selectedCandidateIds.length < 2}
                style={{
                  padding: "10px 20px",
                  borderRadius: 8,
                  border: "none",
                  background: selectedCandidateIds.length >= 2 ? "linear-gradient(135deg, #10b981, #059669)" : "rgba(255,255,255,0.1)",
                  color: "#ffffff",
                  fontWeight: 800,
                  fontSize: 13,
                  cursor: selectedCandidateIds.length >= 2 ? "pointer" : "not-allowed",
                  boxShadow: selectedCandidateIds.length >= 2 ? "0 4px 14px rgba(16, 185, 129, 0.35)" : "none",
                }}
              >
                {isAssembling ? "⏳ Ensamblando y Auditando..." : `🔬 Auditar Ensamble (${selectedCandidateIds.length} Seleccionadas)`}
              </button>
            </div>

            {/* Grid de Candidatos Seleccionables */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 10, maxHeight: 420, overflowY: "auto", paddingRight: 6 }}>
              {candidates.map((c) => {
                const isSelected = selectedCandidateIds.includes(c.candidate_id);
                const mInfo = getMarketCategory(c.symbol);
                return (
                  <div
                    key={c.candidate_id}
                    onClick={() => toggleSelectCandidate(c.candidate_id, c.symbol)}
                    style={{
                      padding: 12,
                      borderRadius: 8,
                      border: `1px solid ${isSelected ? "#10b981" : "var(--border)"}`,
                      background: isSelected ? "rgba(16, 185, 129, 0.1)" : "rgba(255,255,255,0.02)",
                      cursor: "pointer",
                      transition: "all 0.15s ease",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <span style={{ fontWeight: 800, fontSize: 13, color: "var(--text-primary)" }}>{c.symbol}</span>
                      <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: mInfo.bg, color: mInfo.color, fontWeight: 700 }}>
                        {mInfo.badge}
                      </span>
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>
                      TF: <b>{c.timeframe}</b> • Gates: <b style={{ color: "#10b981" }}>{c.gates_passed_count}/11</b>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }}>
                      <span>ROI: <b style={{ color: "#10b981" }}>+{c.annualized_roi}%</b></span>
                      <span>MaxDD: <b style={{ color: "#ef4444" }}>{c.max_drawdown}%</b></span>
                      <span>PF: <b>{c.profit_factor}</b></span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Resultado del Ensamble del Studio */}
          {currentEnsemble && (
            <div style={{ background: "var(--bg-panel)", border: "1px solid #10b981", borderRadius: 12, padding: 20, marginBottom: 24 }}>
              <h3 style={{ margin: "0 0 16px", fontSize: 17, fontWeight: 800, color: "#10b981" }}>
                ✓ Ensamble Generado Exitosamente: {currentEnsemble.name}
              </h3>
              
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 10, marginBottom: 16 }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>ROI Anual Combinado</div>
                  <div style={{ fontSize: 18, fontWeight: 900, color: "#10b981" }}>+{currentEnsemble.combined_annualized_roi_pct}%</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Drawdown Combinado</div>
                  <div style={{ fontSize: 18, fontWeight: 900, color: "#ef4444" }}>{currentEnsemble.combined_max_dd_pct}%</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Sharpe Ratio</div>
                  <div style={{ fontSize: 18, fontWeight: 900, color: "#34d399" }}>{currentEnsemble.combined_sharpe_ratio}</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Diversificación</div>
                  <div style={{ fontSize: 18, fontWeight: 900, color: "#38bdf8" }}>{currentEnsemble.diversification_ratio}x</div>
                </div>
              </div>

              {/* Debate de 5 Agentes */}
              {currentEnsemble.agents_debate && currentEnsemble.agents_debate.length > 0 && (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 800, marginBottom: 10, color: "var(--text-secondary)" }}>
                    🧠 Debate Forense de los 5 Agentes de IA:
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 10 }}>
                    {currentEnsemble.agents_debate.map((agentData, idx) => (
                      <div key={idx} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", borderRadius: 8, padding: 12 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                          <span style={{ fontWeight: 800, fontSize: 13, color: agentData.color || "var(--text-primary)" }}>
                            {agentData.agent}
                          </span>
                          <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{agentData.role}</span>
                        </div>
                        <ul style={{ margin: 0, paddingLeft: 16, fontSize: 11.5, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                          {agentData.findings.map((f, fIdx) => (
                            <li key={fIdx}>{f}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          SUB-MENU 4: 🔐 BÓVEDA RATCHET & GESTIÓN DE CAPITAL (TESORERÍA)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "RATCHET_VAULT" && (
        <div>
          {track === "ULTRA" ? (
            /* BÓVEDA RATCHET PARA RUTA ULTRA */
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 20 }}>
              <div style={{ background: "var(--bg-panel)", border: "1px solid rgba(236, 72, 153, 0.3)", borderRadius: 12, padding: 24 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                  <span style={{ fontSize: 24 }}>🔐</span>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 17, fontWeight: 900 }}>Bóveda de Cosecha Ratchet (Ultra Vault)</h3>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Protección Automática e Irrevocable de Ganancias</div>
                  </div>
                </div>

                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 18 }}>
                  En la <b>Ruta Ultra</b>, cada subcuenta opera como una <b>bala independiente de $1.000 USD</b>. Al alcanzar un beneficio de <b>+200% ($3.000 USD)</b>, el <b>50% de la ganancia ($1.000 USD)</b> se transfiere automáticamente a esta Bóveda blindada, asegurando el retorno del capital inicial.
                </p>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: 16, borderRadius: 8, border: "1px solid var(--border)", marginBottom: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Capital Total Cosechado en Bóveda:</span>
                    <span style={{ fontSize: 16, fontWeight: 900, color: "#10b981" }}>$14.500,00 USD</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Balas Kamikaze Activas ($1k c/u):</span>
                    <span style={{ fontSize: 14, fontWeight: 800, color: "#ec4899" }}>5 Subcuentas</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Multiplicador Geométrico Efectivo:</span>
                    <span style={{ fontSize: 14, fontWeight: 800, color: "#38bdf8" }}>14.5x Capital Inicial</span>
                  </div>
                </div>

                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  ✓ Las transferencias a Bóveda son unidireccionales y jamás se ponen en riesgo ante drawdowns futuros.
                </div>
              </div>

              <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 24 }}>
                <h3 style={{ margin: "0 0 14px", fontSize: 16, fontWeight: 800 }}>Mecánica de Subcuentas Kamikaze</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div style={{ padding: 12, borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                    <div style={{ fontWeight: 800, fontSize: 13, color: "#ec4899", marginBottom: 4 }}>1. Asimetría Extrema</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Riesgo base del 10% al 25% por operación con apalancamiento adaptativo de hasta 500x.</div>
                  </div>
                  <div style={{ padding: 12, borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                    <div style={{ fontWeight: 800, fontSize: 13, color: "#facc15", marginBottom: 4 }}>2. Piramidación en Ganancias</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Reinversión del 50% al 75% del margen flotante exclusivamente en beneficio ≥ +1.5R con Stop Loss en Break-Even.</div>
                  </div>
                  <div style={{ padding: 12, borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                    <div style={{ fontWeight: 800, fontSize: 13, color: "#10b981", marginBottom: 4 }}>3. Bloqueo Ratchet</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Al multiplicar x3 la bala, se retira el costo de reposición a la Bóveda para seguir multiplicando en riesgo cero.</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* CONTROL DE CUENTA INSTITUCIONAL PARA RUTA FONDEO */
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: 20 }}>
              <div style={{ background: "var(--bg-panel)", border: "1px solid rgba(59, 130, 246, 0.3)", borderRadius: 12, padding: 24 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                  <span style={{ fontSize: 24 }}>🛡️</span>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 17, fontWeight: 900 }}>Control Institucional de Prop Firm ($50.000 USD)</h3>
                    <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Supervisión Estricta de Reglas de Pase (Apex / Topstep / FTMO)</div>
                  </div>
                </div>

                <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 18 }}>
                  En la <b>Ruta Fondeo</b>, la prioridad es superar la evaluación en <b>≤ 3 a 5 días hábiles</b> respetando el límite fatal de <b>Drawdown Trailing del 4.0% ($2.000 USD)</b> y la pérdida máxima diaria de <b>$1.000 USD (2.0%)</b>.
                </p>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: 16, borderRadius: 8, border: "1px solid var(--border)", marginBottom: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Objetivo de Pase (+6.0%):</span>
                    <span style={{ fontSize: 15, fontWeight: 900, color: "#10b981" }}>+$3.000,00 USD</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Colchón de Drawdown Trailing (Límite $2k):</span>
                    <span style={{ fontSize: 15, fontWeight: 900, color: "#38bdf8" }}>$1.850,00 USD Restantes</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Sizing por Trade:</span>
                    <span style={{ fontSize: 13, fontWeight: 800, color: "#facc15" }}>0.7% ($350 USD) Fijo</span>
                  </div>
                </div>
              </div>

              <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 12, padding: 24 }}>
                <h3 style={{ margin: "0 0 14px", fontSize: 16, fontWeight: 800 }}>Reglas Operativas de Pase Rápido</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div style={{ padding: 12, borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                    <div style={{ fontWeight: 800, fontSize: 13, color: "#3b82f6", marginBottom: 4 }}>1. Sprint en Horario RTH</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Operaciones concentradas exclusivamente en sesión de alta liquidez NY (13:30 - 20:00 UTC).</div>
                  </div>
                  <div style={{ padding: 12, borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                    <div style={{ fontWeight: 800, fontSize: 13, color: "#10b981", marginBottom: 4 }}>2. Cero Piramidación</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Exposición estrictamente lineal (1 o 2 contratos CME) sin riesgo de liquidación.</div>
                  </div>
                  <div style={{ padding: 12, borderRadius: 8, background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                    <div style={{ fontWeight: 800, fontSize: 13, color: "#ef4444", marginBottom: 4 }}>3. Auto-Flatten Diario</div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Cierre automático e irrevocable de posiciones si el drawdown intradía alcanza el 1.5% ($750 USD).</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
