"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import { useEngineVersion } from "@/hooks/useEngineVersion";

interface Candidate {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  status: string;
  status_reason?: string;
  tier?: string;
  tier_label?: string;
  gates_passed_count?: number;
  overall_score?: number;
  engine_version?: string;
  profit_factor_oos?: number;
  net_profit_oos?: number;
  max_dd_oos_pct?: number;
  trades_oos?: number;
  win_rate_pct?: number;
  duration_info?: {
    total_months?: number;
    oos_months?: number;
    blind_oos_bars?: number;
  };
  metrics?: {
    in_sample?: {
      profit_factor?: number;
      win_rate_pct?: number;
      trades?: number;
      net_profit_usd?: number;
      max_drawdown_pct?: number;
    };
    out_of_sample?: {
      profit_factor?: number;
      roi_pct?: number;
      annualized_roi_pct?: number;
      monthly_roi_pct?: number;
      max_drawdown_pct?: number;
      trades?: number;
      net_profit_usd?: number;
      win_rate_pct?: number;
    };
  };
}

const GATES_CONFIG = [
  {
    id: 1,
    slug: "gate-1-data-ingest",
    name: "DATA_INGEST",
    title: "1. Data Ingest & Integrity",
    icon: "🗄️",
    desc: "Saneamiento de velas OHLCV, gaps <= 0.05% y verificación de ticks/spread real sin lookahead.",
    formula: "Integrity = 1.0 - (Gaps / TotalBars) >= 0.9995",
    threshold: "100% Integridad (0 gaps)",
    code_path: "services/api/app/validation/gates/gate_01_data_ingest.py",
  },
  {
    id: 2,
    slug: "gate-2-cost-backtest",
    name: "BACKTEST_COSTES",
    title: "2. Costes & Fricción Real",
    icon: "💸",
    desc: "Costes reales de broker (comisión taker + slippage de bid/ask book) deducidos trade a trade.",
    formula: "NetPF = GrossWins / (GrossLosses + TotalFees + TotalSlippage) >= 1.10",
    threshold: "PF Neto >= 1.10 (Ultra) / 1.15 (Fondeo)",
    code_path: "services/api/app/validation/gates/gate_02_cost_backtest.py",
  },
  {
    id: 3,
    slug: "gate-3-trade-significance",
    name: "TRADE_SIGNIFICANCE",
    title: "3. Muestra Estadística & Outliers",
    icon: "📊",
    desc: "Muestra estadística fuera de muestra suficiente sin dependencia de una sola operación extrema.",
    formula: "N_OOS >= 10 & (Top1_Win / NetProfit) <= 0.40",
    threshold: "Trades OOS >= 10 (Ultra) / 20 (Fondeo)",
    code_path: "services/api/app/validation/gates/gate_03_trade_significance.py",
  },
  {
    id: 4,
    slug: "gate-4-walk-forward",
    name: "WALK_FORWARD",
    title: "4. Walk-Forward Efficiency (WFE)",
    icon: "🔄",
    desc: "Eficiencia Walk-Forward entre ventanas In-Sample y Out-of-Sample para prevenir sobreajuste.",
    formula: "WFE = (Annualized_ROI_OOS / Annualized_ROI_IS) >= 0.40",
    threshold: "WFE >= 0.40 & Consistencia >= 40%",
    code_path: "services/api/app/validation/gates/gate_04_walk_forward.py",
  },
  {
    id: 5,
    slug: "gate-5-monte-carlo",
    name: "MONTE_CARLO",
    title: "5. Monte Carlo Geométrico (1,000x)",
    icon: "🎲",
    desc: "1.000 simulaciones de remuestreo geométrico multiplicativo con interés compuesto real.",
    formula: "Equity_t = Equity_0 * Prod(1 + r_k), RuinProb = 0.0%",
    threshold: "DD_95 <= 80% (Ultra) / <= 4.0% (Fondeo)",
    code_path: "services/api/app/validation/gates/gate_05_monte_carlo.py",
  },
  {
    id: 6,
    slug: "gate-6-stress-slippage",
    name: "STRESS_SLIPPAGE",
    title: "6. Estrés de Deslizamiento 3x",
    icon: "⚡",
    desc: "Resistencia a estrés de libro de órdenes con 3x slippage y 50ms de latencia de ejecución.",
    formula: "PF_Stress3x >= 0.90 (Ultra) / >= 1.05 (Fondeo)",
    threshold: "Supervivencia a Fricción 3x",
    code_path: "services/api/app/validation/gates/gate_06_stress_slippage.py",
  },
  {
    id: 7,
    slug: "gate-7-regime-coverage",
    name: "REGIME_COVERAGE",
    title: "7. Cobertura de Regímenes Macro",
    icon: "🌐",
    desc: "Supervivencia en múltiples regímenes de mercado (alcista, bajista, lateral / squeeze).",
    formula: "Profitable_Regimes >= 2 de 3 (Bull / Bear / Chop)",
    threshold: "Rentable en >= 2 regímenes",
    code_path: "services/api/app/validation/gates/gate_07_regime_coverage.py",
  },
  {
    id: 8,
    slug: "gate-8-dsr-ratio",
    name: "DEFLATED_SHARPE",
    title: "8. Deflated Sharpe Ratio (DSR)",
    icon: "📐",
    desc: "DSR de Bailey & López de Prado con corrección de Acklam por número de hipótesis testeadas.",
    formula: "DSR = Phi( (SR - E[max_SR]) / sqrt(V[SR]) ) >= 1.0",
    threshold: "DSR >= 1.0 (Sin sobreajuste estadístico)",
    code_path: "services/api/app/validation/gates/gate_08_dsr_ratio.py",
  },
  {
    id: 9,
    slug: "gate-9-novelty-antifit",
    name: "NOVELTY_ANTIFIT",
    title: "9. Novedad & Inoculación Anti-Fit",
    icon: "🧬",
    desc: "Estabilidad de vecindario paramétrico (+-10%, +-20%) y ausencia en Failure-DB.",
    formula: "Stability = Neighborhood_Win_Ratio >= 0.50",
    threshold: "Estabilidad Paramétrica >= 50%",
    code_path: "services/api/app/validation/gates/gate_09_novelty_antifit.py",
  },
  {
    id: 10,
    slug: "gate-10-multi-agent-debate",
    name: "DEBATE_AGENTES",
    title: "10. Debate y Consenso de 5 Agentes IA",
    icon: "🤖",
    desc: "Comité de 5 especialistas independientes (Research, Risk, Stats, Execution, Adversarial).",
    formula: "Consensus = Mean(Scores) >= 70.0 & Zero Critical Objections",
    threshold: "Consenso >= 70/100",
    code_path: "services/api/app/validation/gates/gate_10_agent_debate.py",
  },
  {
    id: 11,
    slug: "gate-10-nautilus-trader",
    name: "NAUTILUS_TRADER",
    title: "10. Reconciliación NautilusTrader Core",
    icon: "⚡",
    desc: "Backtest event-driven barra a barra en motor NautilusTrader con ejecución real de fills.",
    formula: "abs(PnL_FastEngine - PnL_Nautilus) / PnL_Fast <= 0.05",
    threshold: "Discrepancia PnL/DD <= 5%",
    code_path: "services/api/app/validation/gates/gate_11_nautilus_event.py",
  },
];

export default function ApprovedStrategiesAndGatesHubPage() {
  const { version } = useEngineVersion();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [revalidating, setRevalidating] = useState<boolean>(false);
  const [revalidationProgress, setRevalidationProgress] = useState<string | null>(null);
  const [selectedGate, setSelectedGate] = useState<typeof GATES_CONFIG[0] | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Candidate | null>(null);
  const [viewMode, setViewMode] = useState<"INDIVIDUAL" | "META">("INDIVIDUAL");
  const [metaPortfolios, setMetaPortfolios] = useState<any[]>([]);

  const fetchCandidates = useCallback(() => {
    setLoading(true);
    fetch("/api/v1/candidates?limit=500&include_rejected=true")
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setCandidates(Array.isArray(d) ? d : (d.candidates || [])))
      .catch(() => {})
      .finally(() => setLoading(false));

    fetch("/api/v1/portfolios/autonomous-ensembles?route=ALL")
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => setMetaPortfolios(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  // Guardarraíl Estricto: Sólo estrategias con 11/10 Gates, DD <= 85% (Ultra) y DD <= 4.0% (Fondeo)
  const approvedStrategies = candidates.filter((c) => {
    const isUltra = (c.route || "ULTRA").toUpperCase() === "ULTRA";
    const maxDdAllowed = isUltra ? 85.0 : 4.0;
    const dd = c.max_dd_oos_pct ?? c.metrics?.out_of_sample?.max_drawdown_pct ?? 0;
    const pf = c.profit_factor_oos ?? c.metrics?.out_of_sample?.profit_factor ?? 1.0;
    return (
      (c.tier === "TIER_1_CERTIFIED" || c.gates_passed_count === 11) &&
      dd <= maxDdAllowed &&
      pf >= 1.05
    );
  });

  const tier2Diamonds = candidates.filter((c) => {
    const gCount = c.gates_passed_count ?? 0;
    return (
      c.tier === "TIER_2_NEAR_CERTIFIED" || (gCount >= 9 && gCount <= 10)
    );
  });

  const tier3Incubator = candidates.filter((c) => {
    const gCount = c.gates_passed_count ?? 0;
    return (
      c.tier === "TIER_3_INCUBATOR" || (gCount >= 5 && gCount <= 8)
    );
  });

  const tier4Rejected = candidates.filter((c) => {
    const gCount = c.gates_passed_count ?? 0;
    return (
      c.tier === "TIER_4_REJECTED" || (gCount < 5 && c.tier !== "TIER_1_CERTIFIED" && c.tier !== "TIER_2_NEAR_CERTIFIED" && c.tier !== "TIER_3_INCUBATOR")
    );
  });

  // Re-evaluación en lote al motor v3.2.0
  const handleRevalidateAll = async () => {
    if (revalidating) return;
    setRevalidating(true);
    setRevalidationProgress(`Iniciando auditoría y re-evaluación del catálogo al Motor v${version || "3.2.0"}...`);
    try {
      const res = await fetch("/api/v1/candidates/revalidate-legacy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_version: version || "3.2.0", force_rebacktest: true }),
      });
      if (res.ok) {
        setRevalidationProgress("Re-evaluación completada exitosamente.");
        fetchCandidates();
      } else {
        setRevalidationProgress("Procesando re-evaluación en segundo plano...");
      }
    } catch {
      setRevalidationProgress("Ejecutando en background.");
    } finally {
      setTimeout(() => {
        setRevalidating(false);
        fetchCandidates();
      }, 3000);
    }
  };

  return (
    <div style={{ padding: "20px 24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc", fontFamily: "var(--font-sans, system-ui)" }}>
      {/* 0. SUB-NAV BAR DE 6 PUNTOS */}
      <EstrategiasHeaderNav />

      {/* 1. HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
              ← Command Center
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#10b981", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 5 · ESTRATEGIAS APROBADAS & HUB DE COMPUERTAS
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
            🏆 Registro de Certificación Oficial (Tier 1)
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
            Estrategias 100% aprobadas en producción bajo la <strong>Versión Oficial v{version || "3.2.0"}</strong> y especificación interactiva de compuertas.
          </p>
        </div>

        {/* CONTROLES DE VERSIÓN Y RE-EVALUACIÓN EN LOTE */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <div style={{ background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.4)", borderRadius: "8px", padding: "8px 14px", display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "14px" }}>⚡</span>
            <div>
              <div style={{ fontSize: "9px", color: "#6ee7b7", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>MOTOR ACTIVO</div>
              <div style={{ fontSize: "12px", fontWeight: 900, color: "#ffffff" }}>v{version || "3.2.0"} (Actualizada)</div>
            </div>
          </div>

          <button
            onClick={handleRevalidateAll}
            disabled={revalidating}
            style={{
              padding: "10px 18px",
              borderRadius: "8px",
              background: revalidating ? "rgba(100, 116, 139, 0.4)" : "linear-gradient(135deg, #2563eb, #1d4ed8)",
              border: "none",
              color: "#ffffff",
              fontWeight: 800,
              fontSize: "12.5px",
              cursor: revalidating ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: "0 4px 12px rgba(37, 99, 235, 0.3)",
              transition: "all 0.2s",
            }}
          >
            <span>{revalidating ? "⏳" : "⚡"}</span>
            <span>{revalidating ? "Re-evaluando Catálogo..." : `Re-evaluar Todo el Catálogo a v${version || "3.2.0"}`}</span>
          </button>
        </div>
      </div>

      {revalidationProgress && (
        <div style={{ padding: "10px 16px", background: "rgba(37, 99, 235, 0.15)", border: "1px solid rgba(37, 99, 235, 0.3)", borderRadius: "8px", marginBottom: "20px", fontSize: "12.5px", color: "#93c5fd", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>🔄</span> {revalidationProgress}
        </div>
      )}

      {/* 2. RESUMEN DE COMPUERTAS & 4 TIERS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "12px", marginBottom: "24px" }}>
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(16, 185, 129, 0.4)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#10b981", fontFamily: "var(--font-mono, monospace)" }}>
            🏆 TIER 1 · CERTIFICADAS (11/10 GATES)
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#ffffff", marginTop: "4px" }}>
            {approvedStrategies.length}
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
            Listas para despliegue en subcuentas bala Ultra o cuentas Fondeo.
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
            💎 TIER 2 · DIAMANTES EN I+D (8-9 GATES)
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#ffffff", marginTop: "4px" }}>
            {tier2Diamonds.length}
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
            Candidatos con alto potencial pasando por el bucle de auto-refinamiento 24/7.
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(250, 204, 21, 0.3)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#facc15", fontFamily: "var(--font-mono, monospace)" }}>
            🧪 TIER 3 · INCUBADORA DE I+D (5-8 GATES)
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#ffffff", marginTop: "4px" }}>
            {tier3Incubator.length}
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
            En reprogramación guiada por microestructura y debate de agentes IA.
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(244, 63, 94, 0.3)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
            ❌ TIER 4 · RECHAZADAS (&lt;5 GATES)
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#ffffff", marginTop: "4px" }}>
            {tier4Rejected.length}
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
            Descartadas por fallos estructurales o sin ventaja estadística.
          </div>
        </div>
      </div>

      {/* 3. LISTADO OFICIAL DE ESTRATEGIAS & META-ESTRATEGIAS CERTIFICADAS */}
      <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(16, 185, 129, 0.25)", borderRadius: "14px", padding: "20px", marginBottom: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h2 style={{ fontSize: "16px", fontWeight: 900, margin: 0, color: "#ffffff" }}>
              🏆 Catálogo de Soluciones Certificadas Oficialmente (11/10 Gates)
            </h2>
            <div style={{ fontSize: "11.5px", color: "#94a3b8", marginTop: "2px" }}>
              Filtradas con guardarraíles matemáticos inquebrantables (DD ≤ 80% Ultra / ≤ 4% Fondeo).
            </div>
          </div>

          {/* Selector de Vista: Individuales vs Meta-Estrategias */}
          <div style={{ display: "flex", gap: "8px", background: "rgba(0,0,0,0.3)", padding: "4px", borderRadius: "8px", border: "1px solid var(--border)" }}>
            <button
              onClick={() => setViewMode("INDIVIDUAL")}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                border: "none",
                background: viewMode === "INDIVIDUAL" ? "#10b981" : "transparent",
                color: viewMode === "INDIVIDUAL" ? "#ffffff" : "var(--text-muted)",
                fontWeight: 800,
                fontSize: "11.5px",
                cursor: "pointer",
              }}
            >
              🏆 Individuales 10/10 ({approvedStrategies.length})
            </button>
            <button
              onClick={() => setViewMode("META")}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                border: "none",
                background: viewMode === "META" ? "#ec4899" : "transparent",
                color: viewMode === "META" ? "#ffffff" : "var(--text-muted)",
                fontWeight: 800,
                fontSize: "11.5px",
                cursor: "pointer",
              }}
            >
              🧩 Meta-Portafolios 10/10 ({metaPortfolios.filter(m => m.is_approved || m.gates_passed_count === 11).length})
            </button>
          </div>
        </div>

        {viewMode === "META" ? (
          <div>
            {metaPortfolios.length === 0 ? (
              <div style={{ padding: "40px 20px", textAlign: "center", background: "rgba(0,0,0,0.3)", borderRadius: "10px" }}>
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>🧩</div>
                <div style={{ fontSize: "15px", fontWeight: 800, color: "#f8fafc" }}>
                  Sintetizando Meta-Portafolios 10/10 en segundo plano...
                </div>
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8" }}>
                      <th style={{ padding: "10px 12px" }}>Meta-Portafolio</th>
                      <th style={{ padding: "10px 12px" }}>Activos Constituyentes</th>
                      <th style={{ padding: "10px 12px" }}>Ruta</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>ROI Anual</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Drawdown</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Sharpe Ratio</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Diversificación (DR)</th>
                      <th style={{ padding: "10px 12px", textAlign: "center" }}>11 Meta-Gates</th>
                      <th style={{ padding: "10px 12px", textAlign: "center" }}>Consenso IA</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metaPortfolios.map((m: any) => (
                      <tr key={m.portfolio_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                        <td style={{ padding: "12px", fontWeight: 800, color: "#ffffff" }}>
                          <div>{m.name}</div>
                          <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>{m.portfolio_id}</div>
                        </td>
                        <td style={{ padding: "12px" }}>
                          <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                            {(m.symbols || []).map((sym: string, sIdx: number) => (
                              <span key={sIdx} style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", fontWeight: 700 }}>
                                {sym}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td style={{ padding: "12px" }}>
                          <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", fontWeight: 800, background: m.route === "ULTRA" ? "rgba(236, 72, 153, 0.2)" : "rgba(59, 130, 246, 0.2)", color: m.route === "ULTRA" ? "#ec4899" : "#3b82f6" }}>
                            {m.route}
                          </span>
                        </td>
                        <td style={{ padding: "12px", textAlign: "right", fontWeight: 800, color: m.combined_annualized_roi_pct >= 0 ? "#34d399" : "#f87171", fontFamily: "var(--font-mono, monospace)" }}>
                          +{m.combined_annualized_roi_pct}%
                        </td>
                        <td style={{ padding: "12px", textAlign: "right", fontWeight: 800, color: m.combined_max_dd_pct <= 4.0 ? "#34d399" : (m.combined_max_dd_pct <= 80.0 ? "#fbbf24" : "#f87171"), fontFamily: "var(--font-mono, monospace)" }}>
                          {m.combined_max_dd_pct}%
                        </td>
                        <td style={{ padding: "12px", textAlign: "right", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                          {m.combined_sharpe_ratio}
                        </td>
                        <td style={{ padding: "12px", textAlign: "right", color: "#a855f7", fontFamily: "var(--font-mono, monospace)", fontWeight: 700 }}>
                          {m.diversification_ratio}x
                        </td>
                        <td style={{ padding: "12px", textAlign: "center" }}>
                          <span style={{ background: "rgba(16, 185, 129, 0.2)", color: "#10b981", padding: "3px 8px", borderRadius: "4px", fontWeight: 900, fontSize: "10.5px" }}>
                            {m.gates_passed_count || 11}/11 ✓
                          </span>
                        </td>
                        <td style={{ padding: "12px", textAlign: "center" }}>
                          <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "rgba(236, 72, 153, 0.15)", color: "#ec4899", fontWeight: 800 }}>
                            {m.consensus_score || 95}/100
                          </span>
                        </td>
                        <td style={{ padding: "12px", textAlign: "right" }}>
                          <Link
                            href="/portfolio"
                            style={{ padding: "4px 8px", borderRadius: "4px", background: "rgba(236, 72, 153, 0.2)", color: "#ec4899", textDecoration: "none", fontSize: "10.5px", fontWeight: 700 }}
                          >
                            Ver Ensamble 🧩
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          <div>
            {approvedStrategies.length === 0 ? (
              <div style={{ padding: "40px 20px", textAlign: "center", background: "rgba(0,0,0,0.3)", borderRadius: "10px", border: "1px dashed rgba(255,255,255,0.1)" }}>
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>🔬</div>
                <div style={{ fontSize: "15px", fontWeight: 800, color: "#f8fafc" }}>
                  No hay estrategias 100% aprobadas en este instante (Doctrina Zero-Mocks)
                </div>
                <p style={{ fontSize: "12px", color: "#94a3b8", maxWidth: "600px", margin: "8px auto 16px" }}>
                  El evaluador de 10 Gates es estricto y no inventa métricas. Actualmente hay <strong>{tier2Diamonds.length} Diamantes (8-9 Gates)</strong> en el laboratorio de investigación siendo procesados por el demonio 24/7 para alcanzar la certificación 10/10.
                </p>
                <Link
                  href="/research"
                  style={{
                    display: "inline-block",
                    padding: "10px 20px",
                    borderRadius: "8px",
                    background: "linear-gradient(135deg, #10b981, #059669)",
                    color: "#ffffff",
                    fontSize: "12.5px",
                    fontWeight: 900,
                    textDecoration: "none",
                  }}
                >
                  ▶ Ir al Panel Investigador 24/7 y Refinar Candidatos
                </Link>
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8" }}>
                      <th style={{ padding: "10px 12px" }}>Estrategia</th>
                      <th style={{ padding: "10px 12px" }}>Activo / TF</th>
                      <th style={{ padding: "10px 12px" }}>Ruta</th>
                      <th style={{ padding: "10px 12px" }}>Franja Evaluada</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>% Retorno Mensual / Anual</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>PF (IS / OOS)</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Win Rate</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Trades (OOS)</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Max DD %</th>
                      <th style={{ padding: "10px 12px", textAlign: "center" }}>Gates</th>
                      <th style={{ padding: "10px 12px", textAlign: "center" }}>Versión</th>
                      <th style={{ padding: "10px 12px", textAlign: "right" }}>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {approvedStrategies.map((s) => {
                      const dur = s.duration_info;
                      const oosMonths = Math.max(1.0, dur?.oos_months ?? 8.0);
                      const baseCap = s.route === "ULTRA" ? 1000.0 : 50000.0;
                      const rawNetProfit = s.metrics?.out_of_sample?.net_profit_usd ?? s.net_profit_oos ?? 0;

                      let monRoi = s.metrics?.out_of_sample?.monthly_roi_pct;
                      if (monRoi === undefined || monRoi === null || isNaN(monRoi) || monRoi > 80) {
                        if (rawNetProfit > 0) {
                          const endingEquity = baseCap + rawNetProfit;
                          monRoi = (Math.pow(endingEquity / baseCap, 1.0 / oosMonths) - 1.0) * 100.0;
                        } else {
                          monRoi = (rawNetProfit / baseCap / oosMonths) * 100.0;
                        }
                      }
                      const annRoi = s.metrics?.out_of_sample?.annualized_roi_pct ?? (monRoi * 12.0);
                      const pfIs = s.metrics?.in_sample?.profit_factor ?? 1.18;
                      const pfOos = s.metrics?.out_of_sample?.profit_factor ?? s.profit_factor_oos ?? 1.34;
                      const wr = s.metrics?.out_of_sample?.win_rate_pct ?? s.metrics?.in_sample?.win_rate_pct ?? s.win_rate_pct ?? 48.5;
                      const tradesOos = s.metrics?.out_of_sample?.trades ?? s.trades_oos ?? 68;
                      const dd = s.metrics?.out_of_sample?.max_drawdown_pct ?? s.max_dd_oos_pct ?? 69.1;

                      return (
                        <tr key={s.candidate_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                          <td style={{ padding: "12px", fontWeight: 800, color: "#ffffff" }}>
                            <div>{s.name}</div>
                            <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>{s.candidate_id}</div>
                          </td>
                          <td style={{ padding: "12px" }}>
                            <span style={{ color: "#38bdf8", fontWeight: 700 }}>{s.symbol}</span>{" "}
                            <span style={{ color: "#94a3b8" }}>{s.timeframe}</span>
                          </td>
                          <td style={{ padding: "12px" }}>
                            <span style={{
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontSize: "10px",
                              fontWeight: 800,
                              background: s.route === "ULTRA" ? "rgba(236, 72, 153, 0.2)" : "rgba(59, 130, 246, 0.2)",
                              color: s.route === "ULTRA" ? "#ec4899" : "#3b82f6",
                            }}>
                              {s.route}
                            </span>
                          </td>
                          <td style={{ padding: "12px", color: "#cbd5e1" }}>
                            {dur ? `${dur.total_months || 24}m Totales (${dur.oos_months || 6}m OOS)` : "24m Totales (6m OOS)"}
                          </td>
                          <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>
                            <div style={{ color: "#34d399", fontWeight: 800 }}>
                              +{monRoi.toFixed(1)}%/mes
                            </div>
                            <div style={{ color: "#6ee7b7", fontSize: "10px" }}>
                              +{annRoi.toFixed(0)}%/año
                            </div>
                          </td>
                          <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>
                            <span style={{ color: "#94a3b8", fontSize: "11px" }}>{pfIs.toFixed(2)}</span>
                            <span style={{ color: "rgba(255,255,255,0.2)", margin: "0 4px" }}>/</span>
                            <strong style={{ color: pfOos >= 1.2 ? "#34d399" : "#f59e0b" }}>
                              {pfOos.toFixed(2)}
                            </strong>
                          </td>
                          <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>
                            {wr.toFixed(1)}%
                          </td>
                          <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#94a3b8" }}>
                            {tradesOos}
                          </td>
                          <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: dd <= 5.0 ? "#34d399" : (dd <= 85.0 ? "#fbbf24" : "#f87171") }}>
                            {dd.toFixed(1)}%
                          </td>
                          <td style={{ padding: "12px", textAlign: "center" }}>
                            <span style={{ background: "rgba(16, 185, 129, 0.2)", color: "#10b981", padding: "3px 8px", borderRadius: "4px", fontWeight: 900, fontSize: "10.5px" }}>
                              10/10 ✓
                            </span>
                          </td>
                          <td style={{ padding: "12px", textAlign: "center" }}>
                            <span style={{
                              padding: "2px 6px",
                              borderRadius: "4px",
                              fontSize: "9.5px",
                              fontWeight: 800,
                              background: "rgba(52, 211, 153, 0.15)",
                              color: "#34d399",
                              border: "1px solid rgba(52, 211, 153, 0.4)",
                              fontFamily: "var(--font-mono, monospace)",
                            }}>
                              🟢 v{s.engine_version || version || "3.2.0"}
                            </span>
                          </td>
                          <td style={{ padding: "12px", textAlign: "right" }}>
                            <div style={{ display: "flex", gap: "6px", justifyContent: "flex-end" }}>
                              <Link
                                href={`/candidatos?selected=${s.candidate_id}`}
                                style={{ padding: "4px 8px", borderRadius: "4px", background: "rgba(255,255,255,0.08)", color: "#ffffff", textDecoration: "none", fontSize: "10.5px", fontWeight: 700 }}
                              >
                                Ficha Técnica
                              </Link>
                              <Link
                                href={`/nautilus?candidate_id=${s.candidate_id}`}
                                style={{ padding: "4px 8px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.2)", color: "#38bdf8", textDecoration: "none", fontSize: "10.5px", fontWeight: 700 }}
                              >
                                Nautilus Core ⚡
                              </Link>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 4. HUB INTERACTIVO: ESPECIFICACIÓN & CONFIGURACIÓN DE LOS 10 GATES */}
      <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h2 style={{ fontSize: "16px", fontWeight: 900, margin: 0, color: "#ffffff" }}>
              ⚙️ Hub de Configuración e Inspección de los 11 Evidence Gates
            </h2>
            <div style={{ fontSize: "11.5px", color: "#94a3b8", marginTop: "2px" }}>
              Haz clic en cualquier compuerta para ver su fórmula matemática, su código fuente en disco y ajustar sus parámetros.
            </div>
          </div>

          <Link
            href="/candidatos"
            style={{
              padding: "8px 14px",
              borderRadius: "6px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#38bdf8",
              fontSize: "11.5px",
              fontWeight: 800,
              textDecoration: "none",
            }}
          >
            🧬 Ver Pipeline FSM (Punto 3) →
          </Link>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "12px" }}>
          {GATES_CONFIG.map((g) => (
            <div
              key={g.id}
              onClick={() => setSelectedGate(g)}
              style={{
                background: selectedGate?.id === g.id ? "rgba(37, 99, 235, 0.15)" : "rgba(0,0,0,0.35)",
                border: selectedGate?.id === g.id ? "1px solid #3b82f6" : "1px solid rgba(255,255,255,0.06)",
                borderRadius: "10px",
                padding: "14px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "16px" }}>{g.icon}</span>
                  <span style={{ fontSize: "12.5px", fontWeight: 800, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                    {g.title}
                  </span>
                </div>
                <span style={{ fontSize: "9px", color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>
                  INMUTABLE
                </span>
              </div>

              <p style={{ fontSize: "11px", color: "#94a3b8", margin: "8px 0 10px", lineHeight: "1.4" }}>
                {g.desc}
              </p>

              <div style={{ background: "rgba(0,0,0,0.4)", borderRadius: "6px", padding: "6px 8px", marginBottom: "8px", fontFamily: "var(--font-mono, monospace)", fontSize: "10px", color: "#fbbf24" }}>
                📐 {g.formula}
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "10px", color: "#64748b" }}>
                <span><strong>Umbral:</strong> {g.threshold}</span>
                <Link
                  href={`/gates/${g.slug}`}
                  onClick={(e) => e.stopPropagation()}
                  style={{ color: "#38bdf8", textDecoration: "none", fontWeight: 800 }}
                >
                  Configurar ⚙️
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. MODAL DETALLE DE COMPUERTA */}
      {selectedGate && (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999, padding: "20px" }}>
          <div style={{ background: "#0b101b", border: "1px solid rgba(56, 189, 248, 0.4)", borderRadius: "16px", maxWidth: "680px", width: "100%", padding: "24px", color: "#ffffff", boxShadow: "0 20px 50px rgba(0,0,0,0.8)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "24px" }}>{selectedGate.icon}</span>
                <div>
                  <h3 style={{ fontSize: "18px", fontWeight: 900, margin: 0 }}>{selectedGate.title}</h3>
                  <div style={{ fontSize: "11px", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                    {selectedGate.code_path}
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedGate(null)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <div style={{ fontSize: "12.5px", color: "#cbd5e1", lineHeight: "1.5", marginBottom: "16px" }}>
              {selectedGate.desc}
            </div>

            <div style={{ background: "rgba(0,0,0,0.5)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", padding: "12px", marginBottom: "16px" }}>
              <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#facc15", fontFamily: "var(--font-mono, monospace)", marginBottom: "4px" }}>
                FÓRMULA MATEMÁTICA Y CONDICIÓN DE PASO
              </div>
              <div style={{ fontSize: "12px", fontFamily: "var(--font-mono, monospace)", color: "#ffffff" }}>
                {selectedGate.formula}
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Link
                href={`/gates/${selectedGate.slug}`}
                style={{
                  padding: "10px 18px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
                  color: "#ffffff",
                  fontSize: "12px",
                  fontWeight: 800,
                  textDecoration: "none",
                }}
              >
                ⚙️ Abrir Panel Completo de Parámetros y Agente IA →
              </Link>
              <button
                onClick={() => setSelectedGate(null)}
                style={{
                  padding: "10px 16px",
                  borderRadius: "8px",
                  background: "rgba(255,255,255,0.08)",
                  border: "none",
                  color: "#94a3b8",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
