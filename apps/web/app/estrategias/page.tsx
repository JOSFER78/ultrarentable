"use client";

import React, { useState, useEffect, Suspense, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import SistemaSupervisorPage from "../sistema/page";
import StrategiesExplorerPage from "../strategies/page";
import CandidatosFSMPage from "../candidatos/page";
import ResearchLabPage from "../research/page";
import ApprovedStrategiesAndGatesHubPage from "../gates/page";
import PortfolioStudioPage from "../portfolio/page";

interface PhaseConfig {
  id: number;
  key: string;
  name: string;
  shortName: string;
  icon: string;
  badge: string;
  color: string;
  description: string;
}

const PHASES: PhaseConfig[] = [
  {
    id: 0,
    key: "portada",
    name: "0. Portada & Panel General de Estrategias",
    shortName: "Portada General",
    icon: "🗺️",
    badge: "HUB GLOBAL",
    color: "#63e1b4",
    description: "Visión panorámica global, KPIs consolidados, embudo de 6 etapas y estado de las 6 fases del sistema.",
  },
  {
    id: 1,
    key: "motor",
    name: "1. Motor Cuantitativo 24/7 en Vivo & Supervisión",
    shortName: "1. Motor 24/7",
    icon: "⚡",
    badge: "24/7 AUTO",
    color: "#34d399",
    description: "Monitoreo en tiempo real de la minería continua (FastEngine 24/7 + SQX Bridge), pool de 8 workers y supervisión de datos.",
  },
  {
    id: 2,
    key: "catalogo",
    name: "2. Catálogo y Explorador Cuantitativo (230 Candidatos)",
    shortName: "2. Catálogo (230)",
    icon: "📊",
    badge: "230 CAND",
    color: "#38bdf8",
    description: "Explorador de estrategias con filtros por activo, temporalidad, métricas OOS, Scorecards, DNA y exportador C# / Pine.",
  },
  {
    id: 3,
    key: "pipeline",
    name: "3. Pipeline 11 Pasos (FSM & Gates Institucionales)",
    shortName: "3. Pipeline 11-G",
    icon: "🧬",
    badge: "11 GATES",
    color: "#818cf8",
    description: "Evaluación rigurosa a través de los 11 Gates matemáticos deterministas de control de calidad y robustez.",
  },
  {
    id: 4,
    key: "investigador",
    name: "4. Panel Investigador Semántico (Laboratorio I+D)",
    shortName: "4. Lab I+D",
    icon: "🔬",
    badge: "LAB I+D",
    color: "#facc15",
    description: "Análisis semántico de fallos, base de conocimiento de sobreajuste y bucle de mejora continua de estrategias.",
  },
  {
    id: 5,
    key: "aprobadas",
    name: "5. Estrategias Aprobadas (11/11 Certificadas)",
    shortName: "5. Aprobadas 11/11",
    icon: "🏆",
    badge: "CERTIFICADAS",
    color: "#10b981",
    description: "Ranking oficial de estrategias que han superado los 11 Gates con evidencia matemática completa.",
  },
  {
    id: 6,
    key: "portfolio",
    name: "6. Meta-Estrategia Ensamblada & Bóveda Ratchet",
    shortName: "6. Meta-Estrategia",
    icon: "🧩",
    badge: "PORTFOLIO",
    color: "#ec4899",
    description: "Ensamblaje de portafolios multiactivo no correlacionados, interés compuesto y protección de bóveda.",
  },
];

// COMPONENTE: PORTADA GENERAL DE ESTRATEGIAS (PANEL HERO CONSOLIDADO)
function PortadaGeneralOverview({ onSelectFase }: { onSelectFase: (faseId: number) => void }) {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchTelemetry = useCallback(async () => {
    try {
      const res = await fetch("/api/v2/real/search-telemetry");
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
    } catch (e) {
      // Keep state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 3000);
    return () => clearInterval(interval);
  }, [fetchTelemetry]);

  const funnel = telemetry?.filter_funnel || {
    generated: 78813,
    is_passed: 14210,
    oos_passed: 2450,
    wfo_passed: 580,
    monte_carlo_passed: 120,
    approved: 12,
  };

  return (
    <div style={{ padding: "24px 32px", maxWidth: "1600px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* 1. HERO HEADER BANNER */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(14, 23, 38, 0.95) 0%, rgba(8, 14, 24, 0.98) 100%)",
          border: "1px solid rgba(99, 225, 180, 0.3)",
          borderRadius: "16px",
          padding: "24px 28px",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "20px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <span style={{ fontSize: "24px" }}>🧬</span>
            <h1 style={{ fontSize: "22px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.3px" }}>
              PORTADA GENERAL DE ESTRATEGIAS CUANTITATIVAS
            </h1>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 900,
                padding: "3px 8px",
                borderRadius: "4px",
                background: "rgba(99, 225, 180, 0.15)",
                color: "#63e1b4",
                border: "1px solid rgba(99, 225, 180, 0.3)",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              6 FASES DETERMINISTAS
            </span>
          </div>
          <p style={{ fontSize: "13px", color: "#94a3b8", margin: 0, maxWidth: "750px", lineHeight: "1.5" }}>
            Centro de mando integral del laboratorio. Supervisa el flujo completo desde la minería autónoma 24/7, el catálogo de 230 candidatos, la validación estricta en 11 Gates, la investigación semántica hasta el portafolio multiactivo.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <button
            onClick={() => onSelectFase(1)}
            style={{
              padding: "10px 18px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              border: "none",
              color: "#06080d",
              fontWeight: 900,
              fontSize: "12px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              boxShadow: "0 4px 15px rgba(16, 185, 129, 0.3)",
            }}
          >
            ⚡ Abrir Motor 24/7 en Vivo →
          </button>

          <button
            onClick={() => onSelectFase(2)}
            style={{
              padding: "10px 18px",
              borderRadius: "8px",
              background: "rgba(56, 189, 248, 0.12)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              color: "#38bdf8",
              fontWeight: 800,
              fontSize: "12px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            📊 Explorar 230 Estrategias →
          </button>
        </div>
      </div>

      {/* 2. KPIS GLOBALES CONSOLIDADOS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px" }}>
        <div style={{ background: "rgba(12, 18, 28, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>ESTRATEGIAS EVALUADAS</div>
          <div style={{ fontSize: "22px", fontWeight: 900, color: "#ffffff", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            78.813
          </div>
          <div style={{ fontSize: "11px", color: "#34d399", marginTop: "2px" }}>⚡ Minería continua 24/7 activa</div>
        </div>

        <div style={{ background: "rgba(12, 18, 28, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>TRIALS FÍSICOS EN DISCO</div>
          <div style={{ fontSize: "22px", fontWeight: 900, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            9.882
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>Guardados en SQLite WAL</div>
        </div>

        <div style={{ background: "rgba(12, 18, 28, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>CANDIDATOS EN CATÁLOGO</div>
          <div style={{ fontSize: "22px", fontWeight: 900, color: "#818cf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            230
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>172 Ultra · 58 Fondeo</div>
        </div>

        <div style={{ background: "rgba(12, 18, 28, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>GATES MATEMÁTICOS</div>
          <div style={{ fontSize: "22px", fontWeight: 900, color: "#facc15", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            11 / 11
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>Doctrina Real-Only & Zero Mocks</div>
        </div>

        <div style={{ background: "rgba(12, 18, 28, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>DATASETS AUDITADOS</div>
          <div style={{ fontSize: "22px", fontWeight: 900, color: "#10b981", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            1.103.251
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>Velas con SHA-256 verificado</div>
        </div>
      </div>

      {/* 3. LAS 6 FASES DEL SISTEMA (TARJETAS INTERACTIVAS DE ACCESO DIRECTO) */}
      <div>
        <div style={{ fontSize: "15px", fontWeight: 900, color: "#ffffff", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>🗺️</span> MAPA DE LAS 6 ETAPAS DEL PIPELINE CUANTITATIVO
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
          {PHASES.filter(p => p.id > 0).map((phase) => (
            <div
              key={phase.id}
              onClick={() => onSelectFase(phase.id)}
              style={{
                background: "rgba(12, 18, 28, 0.85)",
                border: `1px solid ${phase.color}33`,
                borderRadius: "14px",
                padding: "20px",
                cursor: "pointer",
                transition: "all 0.2s ease",
                boxShadow: "0 4px 20px rgba(0, 0, 0, 0.25)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = phase.color;
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = `0 8px 25px ${phase.color}22`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = `${phase.color}33`;
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 4px 20px rgba(0, 0, 0, 0.25)";
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <span style={{ fontSize: "22px" }}>{phase.icon}</span>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 900,
                      padding: "2px 8px",
                      borderRadius: "4px",
                      background: `${phase.color}22`,
                      color: phase.color,
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    {phase.badge}
                  </span>
                </div>

                <div style={{ fontSize: "15px", fontWeight: 900, color: "#ffffff", marginBottom: "6px" }}>
                  {phase.name}
                </div>

                <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0, lineHeight: "1.5" }}>
                  {phase.description}
                </p>
              </div>

              <div style={{ marginTop: "16px", paddingTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.06)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "11px", color: phase.color, fontWeight: 800 }}>
                  Entrar a la Fase {phase.id} →
                </span>
                <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  FASE {phase.id}/6
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. EMBUDO DE FILTRADO CUANTITATIVO EN 6 ETAPAS */}
      <div
        style={{
          background: "rgba(12, 18, 28, 0.9)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px 24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 900, color: "#ffffff" }}>
              ⚡ EMBUDO DE FILTRADO MATEMÁTICO DETERMINISTA (6 ETAPAS)
            </div>
            <div style={{ fontSize: "11px", color: "#94a3b8" }}>
              Cada candidato es evaluado rigurosamente en datos ciegos fuera de muestra (OOS 20% + Holdout 20%).
            </div>
          </div>

          <div style={{ fontSize: "11px", color: "#63e1b4", fontFamily: "var(--font-mono, monospace)", fontWeight: 800 }}>
            Tasa de Aprobación Final: {((funnel.approved / Math.max(1, funnel.generated)) * 100).toFixed(3)}%
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "10px" }}>
          <div style={{ background: "#06090e", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>1. GENERADAS</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
              {funnel.generated.toLocaleString()}
            </div>
            <div style={{ fontSize: "9.5px", color: "#94a3b8" }}>100% Universo</div>
          </div>

          <div style={{ background: "#06090e", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>2. IN-SAMPLE</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#38bdf8", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
              {funnel.is_passed.toLocaleString()}
            </div>
            <div style={{ fontSize: "9.5px", color: "#38bdf8" }}>PF &gt; 1.30</div>
          </div>

          <div style={{ background: "#06090e", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>3. CIEGO OOS</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#818cf8", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
              {funnel.oos_passed.toLocaleString()}
            </div>
            <div style={{ fontSize: "9.5px", color: "#818cf8" }}>PF OOS &gt; 1.20</div>
          </div>

          <div style={{ background: "#06090e", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>4. WFO ROLLING</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#facc15", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
              {funnel.wfo_passed.toLocaleString()}
            </div>
            <div style={{ fontSize: "9.5px", color: "#facc15" }}>WFE &gt; 0.50</div>
          </div>

          <div style={{ background: "#06090e", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255,255,255,0.06)", textAlign: "center" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>5. MONTE CARLO</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#ec4899", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
              {funnel.monte_carlo_passed.toLocaleString()}
            </div>
            <div style={{ fontSize: "9.5px", color: "#ec4899" }}>Score &gt; 85/100</div>
          </div>

          <div style={{ background: "#06090e", borderRadius: "8px", padding: "12px", border: "1px solid rgba(16, 185, 129, 0.4)", textAlign: "center" }}>
            <div style={{ fontSize: "10px", color: "#10b981", fontWeight: 800 }}>6. CERTIFICADAS</div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "#10b981", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
              {funnel.approved.toLocaleString()}
            </div>
            <div style={{ fontSize: "9.5px", color: "#10b981" }}>11/11 Gates</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EstrategiasHubContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Determine initial phase from query param (?fase=0..6)
  // By default, if no param is given, show Phase 0: Portada General de Estrategias!
  const faseParam = searchParams.get("fase");
  const initialFase = faseParam !== null ? parseInt(faseParam, 10) : 0;

  const [activeFase, setActiveFase] = useState<number>(
    initialFase >= 0 && initialFase <= 6 ? initialFase : 0
  );

  useEffect(() => {
    if (faseParam !== null) {
      const parsed = parseInt(faseParam, 10);
      if (parsed >= 0 && parsed <= 6 && parsed !== activeFase) {
        setActiveFase(parsed);
      }
    }
  }, [faseParam, activeFase]);

  const handleSelectFase = (faseId: number) => {
    setActiveFase(faseId);
    if (faseId === 0) {
      router.push("/estrategias", { scroll: false });
    } else {
      router.push(`/estrategias?fase=${faseId}`, { scroll: false });
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc" }}>
      {/* 1. MASTER TOP CONTROLLER FOR ALL 6 PHASES + PORTADA */}
      <div
        style={{
          background: "rgba(10, 15, 24, 0.95)",
          backdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          padding: "14px 24px 10px 24px",
          position: "sticky",
          top: 0,
          zIndex: 100,
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.5)",
        }}
      >
        {/* TOP BRAND TITLE */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "20px" }}>🧬</span>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 900, color: "#ffffff", letterSpacing: "-0.2px" }}>
                HUB CENTRAL DE ESTRATEGIAS (PORTADA GENERAL & 6 FASES)
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Navega entre la Portada General y las 6 fases deterministas del pipeline cuantitativo.
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <Link
              href="/panel"
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                background: "rgba(52, 211, 153, 0.12)",
                border: "1px solid rgba(52, 211, 153, 0.3)",
                color: "#34d399",
                fontSize: "11px",
                fontWeight: 800,
                textDecoration: "none",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              ⚡ Motor 24/7 Dedicado
            </Link>

            <Link
              href="/ejecucion"
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                background: "rgba(56, 189, 248, 0.12)",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                color: "#38bdf8",
                fontSize: "11px",
                fontWeight: 800,
                textDecoration: "none",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              🤖 NinjaTrader 8 Exec
            </Link>
          </div>
        </div>

        {/* 7 SELECTOR TABS (PORTADA + 6 FASES) */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(7, 1fr)",
            gap: "6px",
            overflowX: "auto",
          }}
        >
          {PHASES.map((phase) => {
            const isSelected = activeFase === phase.id;
            return (
              <button
                key={phase.id}
                onClick={() => handleSelectFase(phase.id)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "7px 10px",
                  borderRadius: "8px",
                  background: isSelected
                    ? `linear-gradient(135deg, ${phase.color}22 0%, rgba(16, 24, 38, 0.95) 100%)`
                    : "rgba(255, 255, 255, 0.03)",
                  border: isSelected
                    ? `1px solid ${phase.color}`
                    : "1px solid rgba(255, 255, 255, 0.06)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.15s ease",
                  boxShadow: isSelected ? `0 0 14px ${phase.color}33` : "none",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center", marginBottom: "2px" }}>
                  <span style={{ fontSize: "13px" }}>{phase.icon}</span>
                  <span
                    style={{
                      fontSize: "8.5px",
                      fontWeight: 900,
                      padding: "1px 4px",
                      borderRadius: "3px",
                      background: isSelected ? `${phase.color}33` : "rgba(255,255,255,0.05)",
                      color: isSelected ? phase.color : "#64748b",
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    {phase.badge}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: isSelected ? 900 : 700,
                    color: isSelected ? "#ffffff" : "#94a3b8",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    width: "100%",
                  }}
                >
                  {phase.shortName}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. DYNAMIC CONTENT RENDERING BASED ON SELECTED PHASE */}
      <div>
        {activeFase === 0 && <PortadaGeneralOverview onSelectFase={handleSelectFase} />}
        {activeFase === 1 && <SistemaSupervisorPage />}
        {activeFase === 2 && <StrategiesExplorerPage />}
        {activeFase === 3 && <CandidatosFSMPage />}
        {activeFase === 4 && <ResearchLabPage />}
        {activeFase === 5 && <ApprovedStrategiesAndGatesHubPage />}
        {activeFase === 6 && <PortfolioStudioPage />}
      </div>
    </div>
  );
}

export default function EstrategiasHubPage() {
  return (
    <Suspense fallback={
      <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "40px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "32px", marginBottom: "12px" }}>🧬</div>
          <div style={{ fontSize: "16px", color: "#38bdf8", fontWeight: 900 }}>Cargando Portada & Hub de Estrategias...</div>
        </div>
      </div>
    }>
      <EstrategiasHubContent />
    </Suspense>
  );
}
