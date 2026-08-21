"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface Candidate {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  status: string;
  tier?: string;
  gates_passed_count?: number;
  overall_score?: number;
  metrics?: {
    out_of_sample?: {
      profit_factor?: number;
      roi_pct?: number;
      max_drawdown_pct?: number;
      trades?: number;
    };
  };
}

const GATES_REQUIREMENTS = [
  { id: 1, name: "DATA_INGEST", desc: "Saneamiento de velas OHLCV, gaps <= 0.05% y verificación de ticks/spread real.", threshold: "100% Integridad" },
  { id: 2, name: "BACKTEST_COSTES", desc: "Costes CME/FX/Crypto reales (comisión taker + slippage base).", threshold: "PF OOS >= 1.10 (Ultra) / 1.15 (Fondeo)" },
  { id: 3, name: "TRADE_SIGNIFICANCE", desc: "Muestra estadística fuera de muestra suficiente sin dependencia de outliers.", threshold: "Trades OOS >= 10 (Ultra) / 20 (Fondeo)" },
  { id: 4, name: "WALK_FORWARD", desc: "Eficiencia Walk-Forward (WFE) y consistencia temporal inter-ventanas.", threshold: "WFE >= 0.40 & Consistencia >= 40%" },
  { id: 5, name: "MONTE_CARLO", desc: "1.000 simulaciones de remuestreo geométrico multiplicativo.", threshold: "Ruina == 0.0% (DD < 85% Ultra / 4.0% Fondeo)" },
  { id: 6, name: "STRESS_SLIPPAGE", desc: "Resistencia a estrés de libro con 3x slippage y latencia de ejecución.", threshold: "PF Bajo Estrés >= 0.90 (Ultra) / 1.05 (Fondeo)" },
  { id: 7, name: "REGIME_COVERAGE", desc: "Supervivencia en múltiples regímenes macro (alcista, bajista, lateral).", threshold: "Retorno positivo en >= 2 de 3 regímenes" },
  { id: 8, name: "DEFLATED_SHARPE", desc: "Deflated Sharpe Ratio (DSR de Bailey & López de Prado) ajustado por número de trials.", threshold: "DSR >= 1.0 (Sin sobreajuste estadístico)" },
  { id: 9, name: "NOVELTY_ANTIFIT", desc: "Estabilidad de vecindario paramétrico (+-10%, +-20%) y ausencia en Failure-DB.", threshold: "Estabilidad Paramétrica >= 50%" },
  { id: 10, name: "DEBATE_AGENTES", desc: "Consenso formal del comité de 5 Agentes IA sin objeción crítica de riesgo.", threshold: "Consenso >= 70/100" },
  { id: 11, name: "NAUTILUS_TRADER", desc: "Backtest event-driven barra a barra en motor NautilusTrader con ejecución de fills real.", threshold: "Reconciliación de PnL y DD <= 5% discrepancia" },
];

export default function ApprovedStrategiesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch("/api/v1/candidates")
      .then((r) => (r.ok ? r.json() : { candidates: [] }))
      .then((d) => setCandidates(d.candidates || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const approvedStrategies = candidates.filter(
    (c) => (c.tier === "TIER_1_CERTIFIED" || c.gates_passed_count === 11) && c.status === "APPROVED"
  );
  const tier2Count = candidates.filter((c) => c.tier === "TIER_2_NEAR_CERTIFIED" || (c.gates_passed_count != null && c.gates_passed_count >= 9 && c.gates_passed_count <= 10)).length;
  const tier3Count = candidates.filter((c) => c.tier === "TIER_3_INCUBATOR" || (c.gates_passed_count != null && c.gates_passed_count >= 7 && c.gates_passed_count <= 8)).length;

  return (
    <div style={{ padding: "24px", maxWidth: "1500px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#10b981", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            PUNTO 5 · ESTRATEGIAS APROBADAS & CERTIFICADAS (11/11 GATES)
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          🏆 Registro Oficial de Estrategias Aprobadas (Tier 1)
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Estrategias que han superado el 100% de los 11 Evidence Gates con verificación determinista en disco (Zero-Mocks & Real-Only).
        </p>
      </div>

      {/* 2. BANNER DE ESTADO FORENSE */}
      <div style={{ background: "rgba(16, 23, 34, 0.8)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "14px", padding: "18px 22px", marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ fontSize: "11px", fontWeight: 900, color: "#10b981", fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.8px" }}>
            ESTADO DE CERTIFICACIÓN MATEMÁTICA EN DISCO
          </div>
          <div style={{ fontSize: "15px", fontWeight: 800, color: "#ffffff", marginTop: "3px" }}>
            {approvedStrategies.length > 0
              ? `✓ ${approvedStrategies.length} ESTRATEGIAS 100% CERTIFICADAS EN PRODUCCIÓN`
              : "0 ESTRATEGIAS CERTIFICADAS 11/11 (DOCTRINA FORENSE ESTRICTA)"}
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
            Existen <strong style={{ color: "#38bdf8" }}>{tier2Count} Diamantes en Bruto (9-10 Gates)</strong> y <strong style={{ color: "#facc15" }}>{tier3Count} en Incubadora (7-8 Gates)</strong> listos para refinamiento cuantitativo.
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <Link
            href="/research"
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              background: "rgba(250, 204, 21, 0.2)",
              border: "1px solid rgba(250, 204, 21, 0.4)",
              color: "#facc15",
              fontSize: "12px",
              fontWeight: 800,
              textDecoration: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🔬 Refinar Diamantes en Lab (Punto 4) →
          </Link>
          <Link
            href="/candidatos"
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#38bdf8",
              fontSize: "12px",
              fontWeight: 800,
              textDecoration: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            🧬 Ver Pipeline 11 Pasos (Punto 3) →
          </Link>
        </div>
      </div>

      {/* 3. MATRIZ DE REQUISITOS DE LOS 11 GATES */}
      <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px", marginBottom: "24px" }}>
        <div style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)", marginBottom: "14px" }}>
          📋 ESPECIFICACIÓN DE AUDITORÍA: 11 COMPUERTAS DE EVIDENCIA INMUTABLES
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "10px" }}>
          {GATES_REQUIREMENTS.map((g) => (
            <div key={g.id} style={{ background: "rgba(0,0,0,0.35)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "11.5px", fontWeight: 800, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                  Gate #{g.id}: {g.name}
                </span>
                <span style={{ fontSize: "9.5px", color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>
                  INMUTABLE
                </span>
              </div>
              <p style={{ fontSize: "11px", color: "#94a3b8", margin: "6px 0", lineHeight: "1.4" }}>{g.desc}</p>
              <div style={{ fontSize: "10px", color: "#cbd5e1", fontFamily: "var(--font-mono, monospace)" }}>
                <strong>Umbral Mínimo:</strong> <span style={{ color: "#fbbf24" }}>{g.threshold}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
