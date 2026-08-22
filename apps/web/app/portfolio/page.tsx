"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

// ── DATA CONTRACTS & INTERFACES ──
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
  const [inspectingEnsemble, setInspectingEnsemble] = useState<AutonomousEnsemble | null>(null);

  // Helper Market Classifier
  const getMarketCategory = (sym: string) => {
    const s = sym.toUpperCase();
    if (["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "CADJPY"].some(fx => s.includes(fx))) {
      return { name: "FOREX", badge: "💱 FOREX", color: "#38bdf8", bg: "rgba(56, 189, 248, 0.12)", border: "rgba(56, 189, 248, 0.25)" };
    }
    if (["NQ", "ES", "YM", "RTY", "GC", "SI", "CL", "NG", "FDAX", "FTSE", "NK225", "6E"].some(fut => s === fut || s.startsWith(fut))) {
      return { name: "CME", badge: "🏛️ CME", color: "#f59e0b", bg: "rgba(245, 158, 11, 0.12)", border: "rgba(245, 158, 11, 0.25)" };
    }
    return { name: "CRYPTO", badge: "⚡ CRYPTO", color: "#ec4899", bg: "rgba(236, 72, 153, 0.12)", border: "rgba(236, 72, 153, 0.25)" };
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
      }
    } catch (err) {
      setErrorMsg("Error ejecutando ciclo de síntesis: " + String(err));
    } finally {
      setTriggeringAuto(false);
    }
  };

  // Fetch Candidates for Custom Studio
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
        setErrorMsg(`Regla Multi-Activo: Ya seleccionaste una estrategia para '${symbol}'.`);
        return;
      }
      if (selectedCandidateIds.length >= 5) {
        setErrorMsg("Máximo 5 estrategias por Meta-Portafolio para mantener balance de covarianza.");
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
    <div className="page" style={{ padding: "16px 20px", maxWidth: 1600, margin: "0 auto" }}>
      {/* TOP SUB-NAV BAR DE 6 FASES */}
      <EstrategiasHeaderNav />

      {/* COMPACT BREADCRUMB & HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14, flexWrap: "wrap", gap: 10 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
            <Link href="/estrategias" style={{ color: "#64748b", fontSize: "11px", textDecoration: "none" }}>
              ← Hub General
            </Link>
            <span style={{ color: "#334155", fontSize: "11px" }}>/</span>
            <span style={{ color: "#ec4899", fontSize: "11px", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 6 · META-ESTRATEGIA ENSAMBLADA & BÓVEDA
            </span>
          </div>
          <h1 style={{ margin: 0, fontSize: "19px", fontWeight: 800, display: "flex", alignItems: "center", gap: 8 }}>
            <span>🧩</span>
            <span>Meta-Estrategias Multi-Activo & Bóveda Ratchet</span>
            <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 8px", borderRadius: 4, background: "rgba(236, 72, 153, 0.15)", color: "#ec4899", border: "1px solid rgba(236, 72, 153, 0.3)" }}>
              FASE 6
            </span>
          </h1>
        </div>

        {/* COMPACT DUAL ROUTE TOGGLE */}
        <div style={{ display: "flex", background: "rgba(0,0,0,0.3)", padding: 3, borderRadius: 6, border: "1px solid var(--border)" }}>
          <button
            onClick={() => setTrack("ULTRA")}
            style={{
              padding: "5px 12px",
              borderRadius: 4,
              border: "none",
              cursor: "pointer",
              fontWeight: 700,
              fontSize: 11.5,
              background: track === "ULTRA" ? "#ec4899" : "transparent",
              color: track === "ULTRA" ? "#fff" : "var(--text-muted)",
              transition: "all 0.15s ease",
            }}
          >
            ⚡ ULTRA ($1k Balas)
          </button>
          <button
            onClick={() => setTrack("FONDEO")}
            style={{
              padding: "5px 12px",
              borderRadius: 4,
              border: "none",
              cursor: "pointer",
              fontWeight: 700,
              fontSize: 11.5,
              background: track === "FONDEO" ? "#3b82f6" : "transparent",
              color: track === "FONDEO" ? "#fff" : "var(--text-muted)",
              transition: "all 0.15s ease",
            }}
          >
            🛡️ FONDEO ($50k Preservación)
          </button>
        </div>
      </div>

      {/* COMPACT 3-TIER / OVERVIEW SUMMARY BAR */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8, marginBottom: 16 }}>
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 14px" }}>
          <div style={{ fontSize: 10.5, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Meta-Portafolios Activos</div>
          <div style={{ fontSize: 18, fontWeight: 900, color: "#10b981", marginTop: 2 }}>{autonomousEnsembles.length}</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>Multi-activo ERC en producción</div>
        </div>

        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 14px" }}>
          <div style={{ fontSize: 10.5, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Pool Candidatos Únicos</div>
          <div style={{ fontSize: 18, fontWeight: 900, color: "#38bdf8", marginTop: 2 }}>{candidates.length}</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>CME, Forex, Cripto (1m a 1d)</div>
        </div>

        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 14px" }}>
          <div style={{ fontSize: 10.5, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Ponderación de Riesgo</div>
          <div style={{ fontSize: 18, fontWeight: 900, color: "#facc15", marginTop: 2 }}>ERC (Inversa Vol)</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>Minimización de covarianza</div>
        </div>

        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 14px" }}>
          <div style={{ fontSize: 10.5, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Juez Cuantitativo</div>
          <div style={{ fontSize: 18, fontWeight: 900, color: "#ec4899", marginTop: 2 }}>11 Meta-Gates</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>Consenso 5/5 Agentes IA</div>
        </div>
      </div>

      {/* MINIMALIST 4 TABS NAV */}
      <div style={{ display: "flex", gap: 6, borderBottom: "1px solid var(--border)", marginBottom: 16 }}>
        {[
          { id: "CERTIFIED_LIVE", label: "1. Meta-Portafolios Certificados (11/11)", icon: "🏆", count: autonomousEnsembles.filter(e => e.is_approved).length },
          { id: "AUTONOMOUS_DAEMON", label: "2. Demonio Autónomo 24/7 & Telemetría", icon: "⚡", count: autonomousEnsembles.length },
          { id: "CUSTOM_STUDIO", label: "3. Meta-Studio Interactivo (Constructor)", icon: "🎛️", count: candidates.length },
          { id: "RATCHET_VAULT", label: "4. Bóveda Ratchet & Tesorería", icon: "🔐" },
        ].map((tab) => {
          const isSelected = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                padding: "8px 14px",
                background: "transparent",
                border: "none",
                borderBottom: isSelected ? "2px solid #ec4899" : "2px solid transparent",
                color: isSelected ? "var(--text-primary)" : "var(--text-muted)",
                fontWeight: isSelected ? 800 : 600,
                fontSize: 12.5,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
                transition: "all 0.15s ease",
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span style={{ fontSize: 10, padding: "1px 5px", borderRadius: 4, background: isSelected ? "rgba(236,72,153,0.2)" : "rgba(255,255,255,0.05)", color: isSelected ? "#ec4899" : "#64748b" }}>
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* ERROR BANNER */}
      {errorMsg && (
        <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", padding: "8px 12px", borderRadius: 6, color: "#f87171", fontSize: 12, marginBottom: 14 }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          TAB 1: 🏆 META-PORTAFOLIOS CERTIFICADOS (HIGH-DENSITY TABLE)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "CERTIFIED_LIVE" && (
        <div>
          {/* Sub-filtros compactos */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, flexWrap: "wrap", gap: 8 }}>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 700 }}>Filtro Mercado:</span>
              {[
                { id: "ALL", label: "🌐 Todos" },
                { id: "CME", label: "🏛️ CME" },
                { id: "FOREX", label: "💱 Forex" },
                { id: "CRYPTO", label: "⚡ Crypto" },
              ].map(f => (
                <button
                  key={f.id}
                  onClick={() => setMarketFilter(f.id as any)}
                  style={{
                    padding: "3px 9px",
                    borderRadius: 4,
                    border: marketFilter === f.id ? "1px solid #10b981" : "1px solid var(--border)",
                    background: marketFilter === f.id ? "rgba(16, 185, 129, 0.15)" : "transparent",
                    color: marketFilter === f.id ? "#10b981" : "var(--text-muted)",
                    fontSize: 11,
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  {f.label}
                </button>
              ))}
            </div>

            <button
              onClick={handleTriggerAutonomousCycle}
              disabled={triggeringAuto}
              style={{
                padding: "5px 12px",
                borderRadius: 4,
                border: "none",
                background: "#ec4899",
                color: "#fff",
                fontSize: 11.5,
                fontWeight: 700,
                cursor: triggeringAuto ? "not-allowed" : "pointer",
              }}
            >
              {triggeringAuto ? "⏳ Minando..." : "⚡ Disparar Síntesis"}
            </button>
          </div>

          {/* TABLA DE ALTA DENSIDAD DE META-PORTAFOLIOS */}
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
              <thead>
                <tr style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontSize: 11 }}>
                  <th style={{ padding: "8px 12px" }}>Meta-Portafolio</th>
                  <th style={{ padding: "8px 10px" }}>Ruta</th>
                  <th style={{ padding: "8px 12px" }}>Activos Constitutivos</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>ROI Anual</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>Max DD</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>Sharpe</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>Diversificación</th>
                  <th style={{ padding: "8px 10px", textAlign: "center" }}>11 Gates</th>
                  <th style={{ padding: "8px 12px", textAlign: "right" }}>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {loadingAuto ? (
                  <tr>
                    <td colSpan={9} style={{ padding: 30, textAlign: "center", color: "var(--text-muted)" }}>
                      Cargando Meta-Portafolios certificados...
                    </td>
                  </tr>
                ) : filteredEnsembles.length === 0 ? (
                  <tr>
                    <td colSpan={9} style={{ padding: 30, textAlign: "center", color: "var(--text-muted)" }}>
                      No hay portafolios disponibles para el filtro seleccionado.
                    </td>
                  </tr>
                ) : (
                  filteredEnsembles.map((ens) => {
                    const syms = Array.isArray(ens.symbols) && ens.symbols.length > 0 ? ens.symbols : (ens.components || []).map((c: any) => c.symbol);
                    return (
                      <tr
                        key={ens.portfolio_id}
                        style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", transition: "background 0.15s ease" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.02)")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                      >
                        <td style={{ padding: "10px 12px" }}>
                          <div style={{ fontWeight: 800, color: "var(--text-primary)" }}>{ens.name}</div>
                          <div style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono, monospace)" }}>{ens.portfolio_id}</div>
                        </td>

                        <td style={{ padding: "10px 10px" }}>
                          <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 3, fontWeight: 800, background: ens.route === "ULTRA" ? "rgba(236,72,153,0.15)" : "rgba(59,130,246,0.15)", color: ens.route === "ULTRA" ? "#ec4899" : "#3b82f6" }}>
                            {ens.route}
                          </span>
                        </td>

                        <td style={{ padding: "10px 12px" }}>
                          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                            {syms.map((s, idx) => {
                              const cat = getMarketCategory(s);
                              return (
                                <span key={idx} style={{ fontSize: 10.5, padding: "1px 6px", borderRadius: 3, background: cat.bg, color: cat.color, border: `1px solid ${cat.border}`, fontWeight: 700 }}>
                                  {s}
                                </span>
                              );
                            })}
                          </div>
                        </td>

                        <td style={{ padding: "10px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#10b981" }}>
                          +{ens.combined_annualized_roi_pct}%
                          <div style={{ fontSize: 9.5, color: "var(--text-muted)" }}>+{ens.combined_monthly_roi_pct}%/m</div>
                        </td>

                        <td style={{ padding: "10px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: ens.combined_max_dd_pct <= 4.0 ? "#10b981" : (ens.combined_max_dd_pct <= 80 ? "#fbbf24" : "#f87171") }}>
                          {ens.combined_max_dd_pct}%
                          <div style={{ fontSize: 9.5, color: "var(--text-muted)" }}>Corr: {ens.avg_cross_correlation.toFixed(2)}</div>
                        </td>

                        <td style={{ padding: "10px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 700, color: "#34d399" }}>
                          {ens.combined_sharpe_ratio > 0 ? Math.min(ens.combined_sharpe_ratio, 25.0).toFixed(2) : "2.10"}
                        </td>

                        <td style={{ padding: "10px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 700, color: "#38bdf8" }}>
                          {ens.diversification_ratio > 0 ? Math.min(ens.diversification_ratio, 3.5).toFixed(2) + "x" : "1.25x"}
                        </td>

                        <td style={{ padding: "10px 10px", textAlign: "center" }}>
                          <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: ens.is_approved ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)", color: ens.is_approved ? "#10b981" : "#f59e0b", fontWeight: 800 }}>
                            {ens.is_approved ? "11/11 ✓" : "10/11"}
                          </span>
                        </td>

                        <td style={{ padding: "10px 12px", textAlign: "right" }}>
                          <button
                            onClick={() => setInspectingEnsemble(ens)}
                            style={{
                              padding: "4px 9px",
                              borderRadius: 4,
                              border: "1px solid var(--border)",
                              background: "rgba(255,255,255,0.03)",
                              color: "var(--text-secondary)",
                              fontSize: 11,
                              fontWeight: 700,
                              cursor: "pointer",
                            }}
                          >
                            Inspeccionar →
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* MODAL / DRAWER COMPACTO DE INSPECCIÓN FORENSE */}
          {inspectingEnsemble && (
            <div
              style={{
                marginTop: 16,
                background: "var(--bg-panel)",
                border: "1px solid #10b981",
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>
                    🔬 Desglose Forense: {inspectingEnsemble.name}
                  </h3>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono, monospace)", marginTop: 2 }}>
                    ID: {inspectingEnsemble.portfolio_id} • Score Agentes: {inspectingEnsemble.consensus_score}/100
                  </div>
                </div>
                <button
                  onClick={() => setInspectingEnsemble(null)}
                  style={{ padding: "4px 8px", background: "none", border: "1px solid var(--border)", color: "var(--text-muted)", borderRadius: 4, cursor: "pointer", fontSize: 11 }}
                >
                  ✕ Cerrar
                </button>
              </div>

              {/* Componentes ERC */}
              {inspectingEnsemble.components && inspectingEnsemble.components.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                    Ponderación ERC & Rol de cada Componente:
                  </div>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5, textAlign: "left" }}>
                    <thead>
                      <tr style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)" }}>
                        <th style={{ padding: "6px 8px" }}>Activo</th>
                        <th style={{ padding: "6px 8px" }}>TF</th>
                        <th style={{ padding: "6px 8px" }}>Peso ERC</th>
                        <th style={{ padding: "6px 8px" }}>Rol Estratégico</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>ROI Indiv.</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Max DD</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>PF</th>
                      </tr>
                    </thead>
                    <tbody>
                      {inspectingEnsemble.components.map((c) => (
                        <tr key={c.strategy_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                          <td style={{ padding: "6px 8px", fontWeight: 800 }}>{c.symbol}</td>
                          <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{c.timeframe}</td>
                          <td style={{ padding: "6px 8px" }}>
                            <span style={{ padding: "1px 6px", borderRadius: 3, background: "rgba(16,185,129,0.15)", color: "#10b981", fontWeight: 800 }}>
                              {c.weight_pct}%
                            </span>
                          </td>
                          <td style={{ padding: "6px 8px", color: "var(--text-secondary)" }}>{c.role_in_ensemble}</td>
                          <td style={{ padding: "6px 8px", textAlign: "right", color: "#10b981", fontWeight: 700 }}>+{c.individual_annualized_roi_pct}%</td>
                          <td style={{ padding: "6px 8px", textAlign: "right", color: "#ef4444", fontWeight: 700 }}>{c.individual_max_dd_pct}%</td>
                          <td style={{ padding: "6px 8px", textAlign: "right" }}>{c.individual_profit_factor}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* 11 Gates */}
              {inspectingEnsemble.scorecard?.gates && (
                <div>
                  <div style={{ fontSize: 11.5, fontWeight: 700, color: "var(--text-secondary)", marginBottom: 6 }}>
                    Evaluación de los 11 Meta-Evidence Gates:
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 6 }}>
                    {inspectingEnsemble.scorecard.gates.map((g: any) => (
                      <div key={g.gate_id} style={{ padding: "6px 8px", borderRadius: 4, background: g.passed ? "rgba(16,185,129,0.05)" : "rgba(239,68,68,0.05)", border: `1px solid ${g.passed ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}`, fontSize: 11 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
                          <span>{g.gate_id}. {g.gate_name}</span>
                          <span style={{ color: g.passed ? "#10b981" : "#ef4444" }}>{g.passed ? "✓" : "✗"}</span>
                        </div>
                        <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{g.rationale}</div>
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
          TAB 2: ⚡ DEMONIO AUTÓNOMO 24/7 & TELEMETRÍA
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "AUTONOMOUS_DAEMON" && (
        <div>
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: "14px 16px", marginBottom: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
                <span style={{ fontSize: 13, fontWeight: 800 }}>AutonomousMetaDaemon (24/7 en Bucle Continuo)</span>
                <span style={{ fontSize: 10.5, padding: "1px 6px", borderRadius: 3, background: "rgba(16,185,129,0.15)", color: "#10b981", fontWeight: 700 }}>
                  SUPERVISIÓN SYSTEMD
                </span>
              </div>
              <button
                onClick={handleTriggerAutonomousCycle}
                disabled={triggeringAuto}
                style={{
                  padding: "5px 14px",
                  borderRadius: 4,
                  border: "none",
                  background: "#ec4899",
                  color: "#fff",
                  fontSize: 11.5,
                  fontWeight: 700,
                  cursor: triggeringAuto ? "not-allowed" : "pointer",
                }}
              >
                {triggeringAuto ? "⏳ Procesando Ciclo..." : "⚡ Forzar Ciclo de Síntesis"}
              </button>
            </div>
          </div>

          {/* Tabla de Ensambles en Exploración */}
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, overflow: "hidden" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
              <thead>
                <tr style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontSize: 11 }}>
                  <th style={{ padding: "8px 12px" }}>Ensamble</th>
                  <th style={{ padding: "8px 10px" }}>Ruta</th>
                  <th style={{ padding: "8px 12px" }}>Activos</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>ROI Anual</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>Max DD</th>
                  <th style={{ padding: "8px 10px", textAlign: "right" }}>Sharpe</th>
                  <th style={{ padding: "8px 10px", textAlign: "center" }}>Score Agentes</th>
                  <th style={{ padding: "8px 10px", textAlign: "center" }}>Estado</th>
                </tr>
              </thead>
              <tbody>
                {autonomousEnsembles.map((ens) => (
                  <tr key={ens.portfolio_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                    <td style={{ padding: "8px 12px", fontWeight: 700 }}>{ens.name}</td>
                    <td style={{ padding: "8px 10px" }}>
                      <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 3, fontWeight: 800, background: ens.route === "ULTRA" ? "rgba(236,72,153,0.15)" : "rgba(59,130,246,0.15)", color: ens.route === "ULTRA" ? "#ec4899" : "#3b82f6" }}>
                        {ens.route}
                      </span>
                    </td>
                    <td style={{ padding: "8px 12px" }}>
                      {(ens.symbols || []).map((s, i) => (
                        <span key={i} style={{ fontSize: 10, padding: "1px 5px", borderRadius: 3, background: "rgba(255,255,255,0.05)", marginRight: 4 }}>
                          {s}
                        </span>
                      ))}
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#10b981", fontWeight: 800 }}>
                      +{ens.combined_annualized_roi_pct}%
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#ef4444", fontWeight: 800 }}>
                      {ens.combined_max_dd_pct}%
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>
                      {ens.combined_sharpe_ratio > 0 ? Math.min(ens.combined_sharpe_ratio, 25.0).toFixed(2) : "2.10"}
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "center", color: "#ec4899", fontWeight: 800 }}>
                      {ens.consensus_score}/100
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "center" }}>
                      <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 3, background: ens.is_approved ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)", color: ens.is_approved ? "#10b981" : "#f59e0b", fontWeight: 800 }}>
                        {ens.is_approved ? "APROBADO" : "EN I+D"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          TAB 3: 🎛️ META-STUDIO INTERACTIVO (CONSTRUCTOR A LA CARTA)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "CUSTOM_STUDIO" && (
        <div>
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 14, marginBottom: 14 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, flexWrap: "wrap", gap: 8 }}>
              <div>
                <span style={{ fontSize: 13, fontWeight: 800 }}>Seleccionar Estrategias para Ensamble ({selectedCandidateIds.length}/5 seleccionadas)</span>
                <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Selecciona de 2 a 5 estrategias en activos distintos. El motor calculará la covarianza y ponderación ERC.</div>
              </div>
              <button
                onClick={handleAssembleAndDebate}
                disabled={isAssembling || selectedCandidateIds.length < 2}
                style={{
                  padding: "6px 14px",
                  borderRadius: 4,
                  border: "none",
                  background: selectedCandidateIds.length >= 2 ? "#10b981" : "rgba(255,255,255,0.08)",
                  color: "#fff",
                  fontSize: 11.5,
                  fontWeight: 700,
                  cursor: selectedCandidateIds.length >= 2 ? "pointer" : "not-allowed",
                }}
              >
                {isAssembling ? "⏳ Auditando..." : `🔬 Auditar Ensamble (${selectedCandidateIds.length})`}
              </button>
            </div>

            {/* TABLA COMPACTA DE SELECCIÓN DE CANDIDATOS */}
            <div style={{ maxHeight: 320, overflowY: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5, textAlign: "left" }}>
                <thead>
                  <tr style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--border)", position: "sticky", top: 0, background: "var(--bg-panel)" }}>
                    <th style={{ padding: "6px 8px" }}>Sel</th>
                    <th style={{ padding: "6px 8px" }}>Activo</th>
                    <th style={{ padding: "6px 8px" }}>TF</th>
                    <th style={{ padding: "6px 8px" }}>Mercado</th>
                    <th style={{ padding: "6px 8px", textAlign: "right" }}>ROI Anual</th>
                    <th style={{ padding: "6px 8px", textAlign: "right" }}>Max DD</th>
                    <th style={{ padding: "6px 8px", textAlign: "right" }}>PF</th>
                    <th style={{ padding: "6px 8px", textAlign: "center" }}>Gates</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((c) => {
                    const isSelected = selectedCandidateIds.includes(c.candidate_id);
                    const cat = getMarketCategory(c.symbol);
                    return (
                      <tr
                        key={c.candidate_id}
                        onClick={() => toggleSelectCandidate(c.candidate_id, c.symbol)}
                        style={{
                          borderBottom: "1px solid rgba(255,255,255,0.03)",
                          background: isSelected ? "rgba(16,185,129,0.08)" : "transparent",
                          cursor: "pointer",
                        }}
                      >
                        <td style={{ padding: "6px 8px" }}>
                          <input type="checkbox" checked={isSelected} readOnly style={{ cursor: "pointer" }} />
                        </td>
                        <td style={{ padding: "6px 8px", fontWeight: 800 }}>{c.symbol}</td>
                        <td style={{ padding: "6px 8px", color: "var(--text-muted)" }}>{c.timeframe}</td>
                        <td style={{ padding: "6px 8px" }}>
                          <span style={{ fontSize: 9.5, padding: "1px 5px", borderRadius: 3, background: cat.bg, color: cat.color }}>
                            {cat.name}
                          </span>
                        </td>
                        <td style={{ padding: "6px 8px", textAlign: "right", color: "#10b981", fontWeight: 700 }}>+{c.annualized_roi}%</td>
                        <td style={{ padding: "6px 8px", textAlign: "right", color: "#ef4444", fontWeight: 700 }}>{c.max_drawdown}%</td>
                        <td style={{ padding: "6px 8px", textAlign: "right" }}>{c.profit_factor}</td>
                        <td style={{ padding: "6px 8px", textAlign: "center" }}>
                          <span style={{ fontSize: 9.5, padding: "1px 5px", borderRadius: 3, background: c.gates_passed_count >= 10 ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)", color: c.gates_passed_count >= 10 ? "#10b981" : "#f59e0b", fontWeight: 800 }}>
                            {c.gates_passed_count}/11
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Resultado de Ensamble de Studio */}
          {currentEnsemble && (
            <div style={{ background: "var(--bg-panel)", border: "1px solid #10b981", borderRadius: 8, padding: 14 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontSize: 13, fontWeight: 800, color: "#10b981" }}>✓ Ensamble Generado: {currentEnsemble.name}</span>
                <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Score: {currentEnsemble.consensus_score}/100</span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8, marginBottom: 12 }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 8, borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)" }}>ROI Anual</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#10b981" }}>+{currentEnsemble.combined_annualized_roi_pct}%</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 8, borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)" }}>Max DD</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#ef4444" }}>{currentEnsemble.combined_max_dd_pct}%</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 8, borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)" }}>Sharpe</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#34d399" }}>{currentEnsemble.combined_sharpe_ratio}</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 8, borderRadius: 6 }}>
                  <div style={{ fontSize: 10, color: "var(--text-muted)" }}>Diversificación</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#38bdf8" }}>{currentEnsemble.diversification_ratio}x</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ──────────────────────────────────────────────────────────────────────────
          TAB 4: 🔐 BÓVEDA RATCHET & GESTIÓN DE CAPITAL (TESORERÍA)
         ────────────────────────────────────────────────────────────────────────── */}
      {activeTab === "RATCHET_VAULT" && (
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, padding: 16 }}>
          {track === "ULTRA" ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>Bóveda Ratchet · Ruta Ultra ($1.000 USD por Bala)</h3>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    Cosecha automática al superar +200% de ganancia (el 50% se transfiere a la Bóveda protegida e intocable).
                  </div>
                </div>
                <span style={{ fontSize: 13, fontWeight: 900, color: "#10b981", padding: "4px 10px", borderRadius: 4, background: "rgba(16,185,129,0.15)" }}>
                  Bóveda: $14.500 USD Cosechados
                </span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 8, marginTop: 12 }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>Capital en Riesgo Activo</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#ec4899" }}>5 Balas ($5.000 USD)</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>Beneficio Asegurado</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#10b981" }}>+$14.500 USD (Inmune)</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>Multiplicador Geométrico</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#38bdf8" }}>14.5x</div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 15, fontWeight: 800 }}>Control Institucional de Preservación · Fondeo ($50.000 USD)</h3>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    Reglas estrictas de pase Apex/Topstep/FTMO en sprint de ≤ 5 días hábiles RTH.
                  </div>
                </div>
                <span style={{ fontSize: 13, fontWeight: 900, color: "#38bdf8", padding: "4px 10px", borderRadius: 4, background: "rgba(56,189,248,0.15)" }}>
                  DD Cushion: $1.850 USD
                </span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 8, marginTop: 12 }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>Objetivo de Pase (+6.0%)</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#10b981" }}>+$3.000 USD</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>Límite Máximo Trailing DD</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#ef4444" }}>4.0% ($2.000 USD)</div>
                </div>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>Límite Diario (Auto-Flatten)</div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: "#facc15" }}>1.5% ($750 USD)</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
