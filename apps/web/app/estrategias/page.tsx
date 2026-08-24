"use client";

import React, { useState, useEffect, Suspense, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PRODUCT_PHASES, QUANT_PIPELINE_PHASES } from "@/lib/strategyPhases";

interface SearchTelemetryData {
  status: string;
  engine_version: string;
  git_commit_sha: string;
  total_evaluations_count: number;
  total_candidates: number;
  filter_funnel?: {
    total_evaluated: number;
    approved: number;
  };
  datasets_inventory?: Array<{
    symbol: string;
    interval: string;
    bars: number;
    status: string;
  }>;
}

function EstrategiasHubContent() {
  const router = useRouter();
  const [telemetry, setTelemetry] = useState<SearchTelemetryData | null>(null);
  const [candidateStats, setCandidateStats] = useState<{ total: number; approved: number }>({ total: 0, approved: 0 });
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

      // 1. Fetch real-only telemetry
      const res = await fetch("/api/v2/real/search-telemetry", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setTelemetry(data);
      }

      // 2. Fetch candidates count from SQLite WAL
      const candRes = await fetch("/api/v1/candidates?limit=500&include_rejected=true", { cache: "no-store" });
      if (candRes.ok) {
        const cands = await candRes.json();
        const list = Array.isArray(cands) ? cands : (cands.candidates || []);
        const appCount = list.filter((c: { status?: string; tier?: string }) => 
          c.status === "APPROVED_CURRENT_ENGINE" || 
          c.status === "CERTIFIED_PASS" || 
          c.status === "ULTRA_CERTIFIED"
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
  }, [telemetry]);

  useEffect(() => {
    fetchTelemetry();
  }, [fetchTelemetry]);

  const funnel = telemetry?.filter_funnel;
  const totalEvaluated = funnel?.total_evaluated ?? telemetry?.total_evaluations_count ?? 0;
  const totalCandidates = candidateStats.total || telemetry?.total_candidates || 0;
  const totalApproved = candidateStats.approved || funnel?.approved || 0;
  const datasetList = telemetry?.datasets_inventory || [];
  const totalBars = datasetList.length > 0
    ? datasetList.reduce((acc, d) => acc + (d?.bars || 0), 0)
    : 0;

  return (
    <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "24px 32px", display: "flex", flexDirection: "column", gap: "24px" }}>
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
              }}
            >
              SSOT v5.4.0
            </span>
          </div>
          <p style={{ margin: 0, fontSize: "13px", color: "#94a3b8", maxWidth: "900px", lineHeight: "1.5" }}>
            Centro de mando unificado y auditoría matemática de 6 fases. Doctrina Zero-Mocks: cada cifra deriva de un{" "}
            <code style={{ color: "#63e1b4", background: "rgba(99,225,180,0.1)", padding: "2px 6px", borderRadius: "4px" }}>CanonicalExecutionLedger</code> real.
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <button
            onClick={() => fetchTelemetry(true)}
            disabled={isRefreshing}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: isRefreshing ? "rgba(99, 225, 180, 0.2)" : "rgba(15, 23, 42, 0.8)",
              border: "1px solid rgba(99, 225, 180, 0.4)",
              color: "#63e1b4",
              borderRadius: "8px",
              padding: "8px 16px",
              fontSize: "12px",
              fontWeight: 700,
              cursor: isRefreshing ? "wait" : "pointer",
            }}
          >
            <span>🔄</span>
            {isRefreshing ? "Actualizando..." : "Sincronizar"}
          </button>
        </div>
      </div>

      {/* 2. KPI STATUS STRIP */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
        <div style={{ background: "rgba(15, 23, 42, 0.7)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "16px 20px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>Evaluaciones Realizadas</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#ffffff", marginTop: "4px" }}>
            {loading ? "..." : totalEvaluated.toLocaleString()}
          </div>
        </div>

        <div style={{ background: "rgba(15, 23, 42, 0.7)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "16px 20px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>Candidatos Registrados</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#38bdf8", marginTop: "4px" }}>
            {loading ? "..." : totalCandidates.toLocaleString()}
          </div>
        </div>

        <div style={{ background: "rgba(15, 23, 42, 0.7)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "16px 20px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>Aprobadas Motor Actual</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#10b981", marginTop: "4px" }}>
            {loading ? "..." : totalApproved.toLocaleString()}
          </div>
        </div>

        <div style={{ background: "rgba(15, 23, 42, 0.7)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "16px 20px" }}>
          <div style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase" }}>Barras Históricas Validadas</div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#facc15", marginTop: "4px" }}>
            {loading ? "..." : totalBars.toLocaleString()}
          </div>
        </div>
      </div>

      {/* 3. LAS 6 FASES DEL PRODUCTO (PRODUCT_PHASES) */}
      <div>
        <h2 style={{ fontSize: "16px", fontWeight: 800, color: "#e2e8f0", marginBottom: "16px", letterSpacing: "-0.2px" }}>
          🗺️ EXPLORADOR DE LAS 6 FASES SINCRONIZADAS (PRODUCT_PHASES)
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "16px" }}>
          {PRODUCT_PHASES.filter(p => p.id > 0).map((phase) => (
            <div
              key={phase.id}
              onClick={() => router.push(phase.canonicalRoute)}
              style={{
                background: "rgba(15, 23, 42, 0.75)",
                border: `1px solid rgba(255,255,255,0.08)`,
                borderRadius: "14px",
                padding: "20px 24px",
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
                e.currentTarget.style.boxShadow = `0 6px 24px ${phase.color}22`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
                e.currentTarget.style.transform = "none";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "20px" }}>{phase.icon}</span>
                    <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#ffffff", margin: 0 }}>{phase.name}</h3>
                  </div>
                  <span
                    style={{
                      fontSize: "9px",
                      fontWeight: 800,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: `${phase.color}22`,
                      color: phase.color,
                      border: `1px solid ${phase.color}44`,
                    }}
                  >
                    {phase.badge}
                  </span>
                </div>
                <p style={{ fontSize: "12.5px", color: "#94a3b8", lineHeight: "1.5", margin: 0 }}>
                  {phase.description}
                </p>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px" }}>
                <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  {phase.canonicalRoute}
                </span>
                <span style={{ fontSize: "12px", color: phase.color, fontWeight: 700 }}>
                  Acceder →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. PIPELINE CUANTITATIVO INTERNO (QUANT_PIPELINE_PHASES) */}
      <div style={{ background: "rgba(10, 16, 28, 0.8)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "14px", padding: "20px 24px" }}>
        <h2 style={{ fontSize: "15px", fontWeight: 800, color: "#e2e8f0", marginBottom: "14px" }}>
          ⚙️ PIPELINE CUANTITATIVO INTERNO DE CERTIFICACIÓN (QUANT_PIPELINE_PHASES)
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
          {QUANT_PIPELINE_PHASES.map((stage) => (
            <div key={stage.stageNumber} style={{ background: "rgba(15, 23, 42, 0.6)", borderRadius: "8px", padding: "12px 16px", border: "1px solid rgba(255,255,255,0.05)" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#38bdf8", marginBottom: "4px" }}>
                {stage.name}
              </div>
              <div style={{ fontSize: "11.5px", color: "#94a3b8", marginBottom: "6px" }}>
                {stage.description}
              </div>
              <div style={{ fontSize: "10.5px", color: "#63e1b4", fontFamily: "var(--font-mono, monospace)" }}>
                Exigencia: {stage.evidenceGateRequirement}
              </div>
            </div>
          ))}
        </div>
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
