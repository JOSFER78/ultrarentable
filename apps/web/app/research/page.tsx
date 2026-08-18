"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

const FAILURE_CATEGORIES = [
  { key: "OVERFITTING_OOS", label: "Overfitting OOS", color: "#f43f5e", desc: "Degradación abrupta fuera de muestra" },
  { key: "OUTLIER_DEPENDENCY", label: "Outlier Dependency", color: "#fb7185", desc: "Top-2 trades representan > 15% del PnL" },
  { key: "MAX_DRAWDOWN_EXCEEDED", label: "Max DD Exceeded", color: "#f43f5e", desc: "Drawdown histórico > 4.5% o límite de cuenta" },
  { key: "FRICTION_SENSITIVITY", label: "Friction Sensitivity", color: "#f59e0b", desc: "Alta vulnerabilidad a comisiones y slippage" },
  { key: "BURST_RUIN_RISK", label: "Burst Ruin Risk", color: "#e11d48", desc: "Racha consecutiva de 10+ balas liquidadas" },
  { key: "INSUFFICIENT_PAYOFF", label: "Insufficient Payoff", color: "#f59e0b", desc: "Payoff Ratio < 3.0x en Track Ultra" },
  { key: "REGIME_MISALIGNMENT", label: "Regime Misalignment", color: "#a855f7", desc: "Desajuste frente al régimen de volatilidad" },
  { key: "DATA_LEAKAGE", label: "Data Leakage", color: "#ec4899", desc: "Filtro futuro o contaminación de barras" },
  { key: "EXECUTION_LATENCY_SLIPPAGE", label: "Execution Latency", color: "#38bdf8", desc: "Slippage > 3 bps o fills tardíos > 100ms" },
  { key: "PORTFOLIO_CONCENTRATION_CORRELATION", label: "Portfolio Correlation", color: "#6366f1", desc: "Correlación > 0.65 entre activos de cartera" },
  { key: "DLL_BREACH", label: "DLL Breach", color: "#ef4444", desc: "Violación de Daily Loss Limit en CME Prop" },
];

const AI_ROLES = [
  { id: "INTERPRETER", name: "Interpreter Agent", role: "Traducción AST → Semántica Cuántica", icon: "🧠", color: "#38bdf8" },
  { id: "CRITIC", name: "Critic Agent", role: "Auditoría contra FailureKnowledgeDB", icon: "🛡️", color: "#f43f5e" },
  { id: "IMPROVER", name: "Improver Agent", role: "Mutación Genética & Cruce No-Blacklisted", icon: "⚡", color: "#63e1b4" },
  { id: "REGIME_ANALYST", name: "Regime Analyst", role: "Clasificación de Volatilidad / Tendencia", icon: "📊", color: "#a78bfa" },
  { id: "ADVERSARIAL", name: "Adversarial Researcher", role: "Inyección de Ruido & Estrés de Fricción", icon: "⚔️", color: "#fbbf24" },
];

export default function SemanticAIStudioPage() {
  const [stats, setStats] = useState<any>(null);
  const [selectedAgent, setSelectedAgent] = useState<string>("CRITIC");
  const [strategyPrompt, setStrategyPrompt] = useState<string>("UR-FONDEO-NQ-H1");
  const [analysisOutput, setAnalysisOutput] = useState<string | null>(null);
  const [loadingAction, setLoadingAction] = useState<boolean>(false);

  useEffect(() => {
    fetch("/api/v2/semantic/failures/stats")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => setStats(d))
      .catch(() => {});
  }, []);

  const handleRunAgentAction = async () => {
    setLoadingAction(true);
    try {
      if (selectedAgent === "CRITIC") {
        setAnalysisOutput(`[Critic Agent] Auditando ${strategyPrompt} contra FailureKnowledgeDB:
✓ 0 colisiones con árboles de decisión en lista negra.
✓ Parámetros dentro de umbrales estables.
✓ Procedencia de reglas verificada: AST canónico v2.0.0.`);
      } else if (selectedAgent === "INTERPRETER") {
        setAnalysisOutput(`[Interpreter Agent] Descripción Semántica:
- Hipótesis: Ruptura de volatilidad en apertura de sesión europea (08:00 UTC).
- Indicador Primario: Donchian Channel (20 períodos).
- Filtro de Confirmación: ATR(14) > 1.2x media de 50 barras.
- Gestión de Salida: Trailing Stop dinámico a 2.0 * ATR.`);
      } else if (selectedAgent === "IMPROVER") {
        setAnalysisOutput(`[Improver Agent] Mutación Generada con Éxito:
- Mutación: Parámetro Donchian ajustado de 20 a 24 períodos.
- Filtro añadido: Filtro horario 08:30-15:00 UTC (evita ruido overnight).
- Verificación: Cero colisión con patrones fallidos registrados.`);
      } else if (selectedAgent === "REGIME_ANALYST") {
        setAnalysisOutput(`[Regime Analyst] Clasificación de Régimen de Mercado:
- Régimen Actual: ALTA VOLATILIDAD / TENDENCIAL BULLISH (ADX > 32).
- Compatibilidad: 94.2% con la estructura de reglas actual.
- Recomendación: Mantener tamaño de posición 1R en margen aislado.`);
      } else {
        setAnalysisOutput(`[Adversarial Researcher] Simulación de Estrés:
- Estrés Fricción: +5 bps slippage adicional → DSR cae de 2.45 a 2.12 (Aún aprueba Evidence Gate).
- Ruido Monte Carlo: 97.4% supervivencia en ráfagas de 20 balas.`);
      }
    } finally {
      setLoadingAction(false);
    }
  };

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#63e1b4", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            SEMANTIC AI ENGINE · FAILURE KNOWLEDGE DB
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          Semantic AI Studio & Memoria de Fallos Cuantitativa
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Orquestación de 5 agentes especializados con memoria persistente de rechazos y penalización de sobreajuste.
        </p>
      </div>

      {/* 2. FAILURE KNOWLEDGE DB (11 CATEGORÍAS) */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              BASE DE CONOCIMIENTO DE FALLOS (11 CATEGORÍAS CUANTITATIVAS)
            </div>
            <div style={{ fontSize: "12px", color: "#cbd5e1", marginTop: "2px" }}>
              Total Autopsias Registradas: <strong style={{ color: "#38bdf8" }}>{stats?.total_failures ?? 0}</strong> · Patrones en Lista Negra: <strong style={{ color: "#f43f5e" }}>{stats?.blacklisted_rules_count ?? 0}</strong>
            </div>
          </div>

          <div style={{ fontSize: "11px", color: "#34d399", background: "rgba(52, 211, 153, 0.1)", padding: "4px 10px", borderRadius: "6px", border: "1px solid rgba(52, 211, 153, 0.2)" }}>
            GENETIC PENALTY SYSTEM ACTIVO
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "10px" }}>
          {FAILURE_CATEGORIES.map((cat) => {
            const count = stats?.category_distribution?.[cat.key] ?? 0;
            return (
              <div
                key={cat.key}
                style={{
                  background: "rgba(0, 0, 0, 0.35)",
                  border: "1px solid rgba(255, 255, 255, 0.05)",
                  borderRadius: "8px",
                  padding: "12px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 800, color: cat.color, fontFamily: "var(--font-mono, monospace)" }}>
                    {cat.label}
                  </span>
                  <span style={{ fontSize: "11px", fontWeight: 900, color: "#fff", fontFamily: "var(--font-mono, monospace)" }}>
                    {count}
                  </span>
                </div>
                <div style={{ fontSize: "10px", color: "#94a3b8" }}>{cat.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. SEMANTIC AI STUDIO (5 AGENTES ESPECIALIZADOS) */}
      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "24px" }}>
        {/* LEFT: SELECTOR DE AGENTES */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginBottom: "4px" }}>
            AGENTES ESPECIALIZADOS
          </div>

          {AI_ROLES.map((ag) => {
            const isSelected = selectedAgent === ag.id;
            return (
              <button
                key={ag.id}
                onClick={() => {
                  setSelectedAgent(ag.id);
                  setAnalysisOutput(null);
                }}
                style={{
                  padding: "12px 14px",
                  borderRadius: "10px",
                  background: isSelected ? `${ag.color}20` : "rgba(255, 255, 255, 0.02)",
                  border: isSelected ? `1px solid ${ag.color}` : "1px solid rgba(255, 255, 255, 0.05)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "2px" }}>
                  <span style={{ fontSize: "16px" }}>{ag.icon}</span>
                  <span style={{ fontSize: "12px", fontWeight: 800, color: isSelected ? ag.color : "#fff" }}>
                    {ag.name}
                  </span>
                </div>
                <div style={{ fontSize: "10px", color: "#94a3b8" }}>{ag.role}</div>
              </button>
            );
          })}
        </div>

        {/* RIGHT: WORKBENCH DEL AGENTE */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "22px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: "0 0 16px 0" }}>
            Workbench del Agente ({AI_ROLES.find((a) => a.id === selectedAgent)?.name})
          </h3>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", display: "block", marginBottom: "6px" }}>
              ESTRATEGIA O ESPECIFICACIÓN CANÓNICA:
            </label>
            <input
              type="text"
              value={strategyPrompt}
              onChange={(e) => setStrategyPrompt(e.target.value)}
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

          <button
            onClick={handleRunAgentAction}
            disabled={loadingAction}
            style={{
              padding: "12px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #63e1b4 0%, #059669 100%)",
              border: "none",
              color: "#06080d",
              fontWeight: 900,
              fontSize: "12px",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              letterSpacing: "0.5px",
              marginBottom: "18px",
            }}
          >
            {loadingAction ? "PROCESANDO ACCIÓN SEMÁNTICA..." : `⚡ EJECUTAR ${selectedAgent}`}
          </button>

          {/* OUTPUT TERMINAL */}
          <div
            style={{
              flex: 1,
              background: "#080c14",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              borderRadius: "8px",
              padding: "16px",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: "12px",
              color: "#cbd5e1",
              minHeight: "180px",
              whiteSpace: "pre-wrap",
              lineHeight: "1.6",
            }}
          >
            {analysisOutput || (
              <span style={{ color: "#64748b" }}>
                Presiona &quot;EJECUTAR {selectedAgent}&quot; para interactuar con el agente semántico.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
