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
import { STRATEGY_PHASES } from "@/lib/strategyPhases";

// COMPONENTE: PORTADA GENERAL DE ESTRATEGIAS (PANEL HERO CONSOLIDADO)
function PortadaGeneralOverview({ onSelectFase }: { onSelectFase: (faseId: number) => void }) {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [candidateStats, setCandidateStats] = useState<any>({ total: 0, approved: 0 });
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  const fetchTelemetry = useCallback(async (isManual: boolean = false) => {
    try {
      if (isManual) {
        setIsRefreshing(true);
      } else if (!telemetry) {
        setLoading(true);
      }

      // 1. Fetch search telemetry
      const res = await fetch("/api/v2/real/search-telemetry", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }
      // 2. Fetch candidates real count from SQLite WAL
      const candRes = await fetch("/api/v1/candidates?limit=500&include_rejected=true", { cache: "no-store" });
      if (candRes.ok) {
        const cands = await candRes.json();
        const list = Array.isArray(cands) ? cands : (cands.candidates || []);
        const appCount = list.filter((c: any) => 
          c.status === "CERTIFIED_PASS" || 
          c.status === "ULTRA_CERTIFIED" || 
          c.tier === "TIER_1_CERTIFIED"
        ).length;
        setCandidateStats({ total: list.length, approved: appCount });
      }
      setLastSyncTime(new Date());
    } catch (e) {
      console.error("Error al cargar telemetría de portada:", e);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchTelemetry();
  }, [fetchTelemetry]);

  const funnel = telemetry?.filter_funnel;
  const totalEvaluated = funnel?.total_evaluated ?? telemetry?.total_evaluations_count ?? 0;
  const totalCandidates = candidateStats.total || telemetry?.total_candidates || 0;
  const totalApproved = candidateStats.approved || funnel?.approved || 0;
  const datasetList = telemetry?.datasets_inventory || [];
  const totalBars = datasetList.length > 0
    ? datasetList.reduce((acc: number, d: any) => acc + (d?.bars || 0), 0)
    : 0;

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
              MOTOR v5.3.0 · 6 FASES DETERMINISTAS
            </span>
          </div>
          <p style={{ fontSize: "13px", color: "#94a3b8", margin: 0, maxWidth: "750px", lineHeight: "1.5" }}>
            Centro de mando integral del laboratorio. Supervisa el flujo completo desde la minería autónoma 24/7, el catálogo de candidatos, la validación estricta en 11 Gates, la investigación semántica hasta el portafolio multiactivo.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          {/* BOTÓN MANUAL DE REFRESCO */}
          <button
            onClick={() => fetchTelemetry(true)}
            disabled={isRefreshing}
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#38bdf8",
              fontWeight: 800,
              fontSize: "12px",
              cursor: isRefreshing ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            <span style={{ display: "inline-block", animation: isRefreshing ? "spin 1s linear infinite" : "none" }}>🔄</span>
            <span>{isRefreshing ? "Sincronizando..." : "Actualizar"}</span>
          </button>

          {lastSyncTime && (
            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              Sync: {lastSyncTime.toLocaleTimeString()}
            </span>
          )}

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
            📊 Ver Catálogo Fase 2 →
          </button>
        </div>
      </div>

      {/* 2. 4 KPIS MAESTROS REALES */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
        <div style={{ background: "rgba(10, 16, 26, 0.85)", border: "1px solid #1e293b", borderRadius: "12px", padding: "18px 20px" }}>
          <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, letterSpacing: "0.5px" }}>TOTAL EVALUACIONES DETERMINISTAS</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {totalEvaluated.toLocaleString()}
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            Muestreo OOS continuo sin lookahead
          </div>
        </div>

        <div style={{ background: "rgba(10, 16, 26, 0.85)", border: "1px solid #1e293b", borderRadius: "12px", padding: "18px 20px" }}>
          <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, letterSpacing: "0.5px" }}>CANDIDATOS EN MÁQUINA DE ESTADOS (FSM)</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#a855f7", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {totalCandidates} candidatas
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            Filtradas y clasificadas en SQLite WAL
          </div>
        </div>

        <div style={{ background: "rgba(10, 16, 26, 0.85)", border: "1px solid #1e293b", borderRadius: "12px", padding: "18px 20px" }}>
          <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, letterSpacing: "0.5px" }}>APROBADAS POR 11 QUALITY GATES</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#10b981", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {totalApproved} certificadas
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            Listas para síntesis en Meta-Estrategias
          </div>
        </div>

        <div style={{ background: "rgba(10, 16, 26, 0.85)", border: "1px solid #1e293b", borderRadius: "12px", padding: "18px 20px" }}>
          <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, letterSpacing: "0.5px" }}>INVENTARIO DE BARRAS REALES EN DISCO</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#facc15", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {totalBars.toLocaleString()} velas
          </div>
          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
            1m/5m/15m/1h Parquet CME & BingX
          </div>
        </div>
      </div>

      {/* 3. GRID CON LAS 6 FASES EXPLICADAS CON BOTÓN DIRECTO */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", margin: 0 }}>
              PIPELINE CUANTITATIVO: LAS 6 FASES DEL SISTEMA
            </h2>
            <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "2px" }}>
              Cada fase es un subsistema autónomo interconectado sin fallbacks sintéticos ni datos inventados.
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))", gap: "16px" }}>
          {STRATEGY_PHASES.filter(p => p.id > 0).map((phase) => (
            <div
              key={phase.id}
              onClick={() => onSelectFase(phase.id)}
              style={{
                background: "rgba(10, 16, 26, 0.85)",
                border: "1px solid #1e293b",
                borderRadius: "14px",
                padding: "20px 22px",
                cursor: "pointer",
                transition: "all 0.2s ease",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: "14px",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = phase.color;
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = `0 8px 24px ${phase.color}22`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "#1e293b";
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "22px" }}>{phase.icon}</span>
                    <div>
                      <div style={{ fontSize: "15px", fontWeight: 900, color: "#ffffff" }}>
                        {phase.name}
                      </div>
                      <div style={{ fontSize: "11px", color: phase.color, fontWeight: 700 }}>
                        {phase.badge}
                      </div>
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 800,
                      padding: "3px 8px",
                      borderRadius: "4px",
                      background: `${phase.color}22`,
                      color: phase.color,
                      border: `1px solid ${phase.color}44`,
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    FASE {phase.id}
                  </span>
                </div>

                <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0, lineHeight: "1.5" }}>
                  {phase.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EstrategiasHubContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const faseParam = searchParams.get("fase");
  const initialFase = faseParam !== null ? parseInt(faseParam, 10) : 0;

  const [activeFase, setActiveFase] = useState<number>(
    initialFase >= 0 && initialFase <= 6 ? initialFase : 0
  );

  // Lazy mounting y persistencia de estado para evitar destrucción de componentes
  const [visitedFases, setVisitedFases] = useState<Set<number>>(
    () => new Set([initialFase >= 0 && initialFase <= 6 ? initialFase : 0])
  );

  useEffect(() => {
    if (faseParam !== null) {
      const parsed = parseInt(faseParam, 10);
      if (parsed >= 0 && parsed <= 6 && parsed !== activeFase) {
        setActiveFase(parsed);
        setVisitedFases((prev) => new Set([...Array.from(prev), parsed]));
      }
    }
  }, [faseParam, activeFase]);

  const handleSelectFase = (faseId: number) => {
    setActiveFase(faseId);
    setVisitedFases((prev) => new Set([...Array.from(prev), faseId]));
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
            gridTemplateColumns: "repeat(7, minmax(0, 1fr))",
            gap: "8px",
            width: "100%",
          }}
        >
          {STRATEGY_PHASES.map((phase) => {
            const isSelected = activeFase === phase.id;
            return (
              <button
                key={phase.id}
                onClick={() => handleSelectFase(phase.id)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  background: isSelected
                    ? `linear-gradient(135deg, ${phase.color}22 0%, rgba(16, 24, 38, 0.98) 100%)`
                    : "rgba(255, 255, 255, 0.03)",
                  border: isSelected
                    ? `1px solid ${phase.color}`
                    : "1px solid rgba(255, 255, 255, 0.07)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.18s ease",
                  boxShadow: isSelected ? `0 0 12px ${phase.color}28` : "none",
                  minWidth: 0,
                  width: "100%",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontSize: "14px" }}>{phase.icon}</span>
                  <span
                    style={{
                      fontSize: "8.5px",
                      fontWeight: 800,
                      padding: "1px 5px",
                      borderRadius: "4px",
                      background: isSelected ? `${phase.color}33` : "rgba(255,255,255,0.06)",
                      color: isSelected ? phase.color : "#94a3b8",
                      fontFamily: "var(--font-mono, monospace)",
                      letterSpacing: "0.5px",
                    }}
                  >
                    {phase.badge}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: isSelected ? 800 : 600,
                    color: isSelected ? "#ffffff" : "#cbd5e1",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    width: "100%",
                  }}
                >
                  {phase.shortLabel}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. PERSISTENT VIEWPORTS WITH LAZY MOUNTING (display: block / none) */}
      <div style={{ position: "relative", minHeight: "calc(100vh - 120px)" }}>
        {visitedFases.has(0) && (
          <div style={{ display: activeFase === 0 ? "block" : "none" }}>
            <PortadaGeneralOverview onSelectFase={handleSelectFase} />
          </div>
        )}
        {visitedFases.has(1) && (
          <div style={{ display: activeFase === 1 ? "block" : "none" }}>
            <SistemaSupervisorPage />
          </div>
        )}
        {visitedFases.has(2) && (
          <div style={{ display: activeFase === 2 ? "block" : "none" }}>
            <StrategiesExplorerPage />
          </div>
        )}
        {visitedFases.has(3) && (
          <div style={{ display: activeFase === 3 ? "block" : "none" }}>
            <CandidatosFSMPage />
          </div>
        )}
        {visitedFases.has(4) && (
          <div style={{ display: activeFase === 4 ? "block" : "none" }}>
            <ResearchLabPage />
          </div>
        )}
        {visitedFases.has(5) && (
          <div style={{ display: activeFase === 5 ? "block" : "none" }}>
            <ApprovedStrategiesAndGatesHubPage />
          </div>
        )}
        {visitedFases.has(6) && (
          <div style={{ display: activeFase === 6 ? "block" : "none" }}>
            <PortfolioStudioPage />
          </div>
        )}
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
