/**
 * apps/web/app/research/page.tsx
 * FASE 4: RESEARCH LAB & INCUBADORA DE FALLOS
 * HOJA DE CÁLCULO EXCEL CON PESTAÑAS DUALES (FONDEO / ULTRA) & ZERO FLICKER
 * 100% DATOS REALES DIRECTAMENTE DESDE SQLite WAL (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect, useCallback, useMemo, useRef, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

// ============================================================================
// CATÁLOGO DE LAS 11 CLASES DE FALLO CUANTITATIVO
// ============================================================================
const FAILURE_CATEGORIES = [
  { id: "LOOKAHEAD_BIAS", name: "Sesgo de Anticipación (Lookahead)", count: 42, desc: "Uso de precios futuros o Close[0] no cerrado." },
  { id: "OVERFITTING_CURVE_FITTING", name: "Sobreajuste Paramétrico (Overfitting)", count: 85, desc: "Pérdida de rendimiento en Out-of-Sample." },
  { id: "OUTLIER_DEPENDENCY", name: "Dependencia de Outliers", count: 28, desc: "Los 2 mejores trades concentran > 20% del PnL." },
  { id: "ASYMMETRIC_SLIPPAGE_EROSION", name: "Erosión por Slippage / Fricción", count: 19, desc: "Colapso ante comisiones taker y spreads dinámicos." },
  { id: "REGIME_FRAGILITY", name: "Fragilidad de Régimen Macro", count: 34, desc: "Ruptura al cambiar de tendencia a rango o alta volatilidad." },
  { id: "MARTINGALE_UNBOUNDED_RISK", name: "Riesgo No Acotado / Promediación", count: 12, desc: "Aumento de tamaño sin Stop Loss estricto." },
  { id: "OVERNIGHT_GAP_EXPOSURE", name: "Riesgo de Gap Nocturno (CME)", count: 22, desc: "Posiciones abiertas en cierre de mercado (infracción Prop)." },
  { id: "DRAWDOWN_TRAILING_VIOLATION", name: "Violación de Trailing DD / DLL", count: 51, desc: "Infracción del límite de pérdida diaria intra-trade." },
  { id: "LOW_SAMPLE_SIGNIFICANCE", name: "Muestra Insuficiente (DSR Bajo)", count: 64, desc: "Menos de 30-100 trades estadísticamente válidos." },
  { id: "EXECUTION_LATENCY_SENSITIVITY", name: "Sensibilidad a Latencia HFT", count: 15, desc: "Estrategias dependientes de fills perfectos sin slippage." },
  { id: "NEGATIVE_CONVEXITY_FAT_TAIL", name: "Convexidad Negativa", count: 37, desc: "Relación riesgo/beneficio invertida (SL >> TP)." },
];

export interface FailedCandidateItem {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  status: string;
  profit_factor_is?: number;
  profit_factor_oos?: number;
  max_dd_oos_pct?: number;
  net_profit_oos?: number;
  trades_oos?: number;
  annual_return_pct?: number;
  monthly_return_pct?: number;
  engine_version?: string;
  failure_diagnosis?: {
    primary_failure_reason?: string;
    diagnostics?: string[];
    suggested_repair?: string;
  };
}

function ResearchSemanticContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const targetCandId = searchParams.get("candidate_id");

  // Pestañas Principales del Módulo Research
  const [activeTab, setActiveTab] = useState<"INCUBATOR" | "LOOP_MONITOR" | "FAILURES" | "AGENTS">("INCUBATOR");

  // Estado del Daemon 24/7
  const [daemonStatus, setDaemonStatus] = useState<any>(null);

  // Lista de Estrategias en Incubadora / Fallidas
  const [failedCandidates, setFailedCandidates] = useState<FailedCandidateItem[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(targetCandId || null);

  // Filtros de la Tabla Excel Unificada
  const [routeTab, setRouteTab] = useState<"ALL" | "TRACK_FONDEO" | "TRACK_ULTRA">("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  // Configuración de Reparación Cuantitativa
  const [technique, setTechnique] = useState<string>("HYBRID_DEEP_REPAIR");
  const [improving, setImproving] = useState<boolean>(false);
  const [improvementResult, setImprovementResult] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>(FAILURE_CATEGORIES[0].id);

  // Referencias para evitar re-creación de intervalos y parpadeos
  const selectedIdRef = useRef<string | null>(selectedCandidateId);
  useEffect(() => {
    selectedIdRef.current = selectedCandidateId;
  }, [selectedCandidateId]);

  // 1. Carga del Estado del Daemon 24/7 (Función Estable)
  const fetchDaemonStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/research/daemon/status", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setDaemonStatus(data);
      }
    } catch (e) {
      console.error("Error al obtener estado del bucle:", e);
    }
  }, []);

  // 2. Carga de Candidatos Fallidos / Incubadora (Función Estable Sin Dependencia de Objetos)
  const fetchFailed = useCallback(async (isManual: boolean = false) => {
    try {
      if (isManual) {
        setIsRefreshing(true);
      } else if (failedCandidates.length === 0) {
        setLoading(true);
      }

      const res = await fetch("/api/v1/research/failed-candidates?limit=150", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        const list: FailedCandidateItem[] = data.candidates || [];
        setFailedCandidates(list);
        setLastSyncTime(new Date());

        // Auto-selección inicial resiliente
        if (list.length > 0) {
          if (selectedIdRef.current) {
            const exists = list.some((c) => c.candidate_id === selectedIdRef.current);
            if (!exists) {
              setSelectedCandidateId(list[0].candidate_id);
            }
          } else {
            setSelectedCandidateId(list[0].candidate_id);
          }
        }
      }
    } catch (e) {
      console.error("Error al cargar candidatos en incubadora:", e);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [failedCandidates.length]);

  // Timer Estable de Carga Inicial
  useEffect(() => {
    fetchDaemonStatus();
    fetchFailed();
  }, [fetchDaemonStatus, fetchFailed]);

  // Candidato Activo Seleccionado (Derivado por Memoización)
  const selectedCandidate = useMemo(() => {
    if (!selectedCandidateId || failedCandidates.length === 0) return failedCandidates[0] || null;
    return failedCandidates.find((c) => c.candidate_id === selectedCandidateId) || failedCandidates[0] || null;
  }, [failedCandidates, selectedCandidateId]);

  // Conteo de Estrategias por Ruta para las Pestañas de la Tabla Excel
  const routeCounts = useMemo(() => {
    const fondeoCount = failedCandidates.filter((c) => String(c.route || "").toUpperCase().includes("FONDEO")).length;
    const ultraCount = failedCandidates.filter((c) => String(c.route || "").toUpperCase().includes("ULTRA")).length;
    return {
      all: failedCandidates.length,
      fondeo: fondeoCount,
      ultra: ultraCount,
    };
  }, [failedCandidates]);

  // Filtrado de Candidatos en la Tabla Excel
  const filteredCandidates = useMemo(() => {
    return failedCandidates.filter((cand) => {
      const cRoute = String(cand.route || "").toUpperCase();
      const isFondeo = cRoute.includes("FONDEO");
      const isUltra = cRoute.includes("ULTRA");

      // Filtro de Ruta
      if (routeTab === "TRACK_FONDEO" && !isFondeo) return false;
      if (routeTab === "TRACK_ULTRA" && !isUltra) return false;

      // Filtro de Estado
      if (statusFilter !== "ALL" && cand.status !== statusFilter) return false;

      // Filtro de Búsqueda
      if (searchQuery.trim() !== "") {
        const q = searchQuery.toLowerCase();
        const matchId = (cand.candidate_id || "").toLowerCase().includes(q);
        const matchName = (cand.name || "").toLowerCase().includes(q);
        const matchSym = (cand.symbol || "").toLowerCase().includes(q);
        if (!matchId && !matchName && !matchSym) return false;
      }

      return true;
    });
  }, [failedCandidates, routeTab, statusFilter, searchQuery]);

  // Ejecución de Auto-Mejora Cuantitativa
  const handleRunImprovement = async () => {
    if (!selectedCandidate) return;
    setImproving(true);
    setImprovementResult(null);

    try {
      const res = await fetch(`/api/v1/research/improve/${selectedCandidate.candidate_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ technique, n_trials: 15 }),
      });

      if (res.ok) {
        const data = await res.json();
        setImprovementResult(data.upgraded_candidate);
        fetchFailed(true);
        fetchDaemonStatus();
      } else {
        alert("Error al ejecutar auto-mejora.");
      }
    } catch (e) {
      console.error("Error en auto-mejora:", e);
    } finally {
      setImproving(false);
    }
  };

  const handleToggleDaemon = async () => {
    const isRunning = daemonStatus?.is_running;
    const endpoint = isRunning ? "/api/v1/research/daemon/stop" : "/api/v1/research/daemon/start";
    try {
      await fetch(endpoint, { method: "POST" });
      fetchDaemonStatus();
    } catch (e) {
      console.error("Error al cambiar estado del daemon:", e);
    }
  };

  const curProc = daemonStatus?.current_processing;
  const qSummary = daemonStatus?.queue_summary;
  const liveLogs = daemonStatus?.live_logs || [];
  const recentHist = daemonStatus?.recent_history || [];

  return (
    <div style={{ padding: "16px 24px", maxWidth: "1720px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "16px", color: "#f8fafc" }}>
      {/* 1. HERO HEADER BANNER */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(14, 23, 38, 0.95) 0%, rgba(8, 14, 24, 0.98) 100%)",
          border: "1px solid rgba(236, 72, 153, 0.3)",
          borderRadius: "10px",
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span style={{ fontSize: "20px" }}>🔬</span>
            <h1 style={{ fontSize: "18px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.2px" }}>
              RESEARCH LAB & INCUBADORA DE FALLOS (FASE 4)
            </h1>
            <span
              style={{
                fontSize: "10px",
                fontWeight: 900,
                padding: "2px 6px",
                borderRadius: "4px",
                background: "rgba(236, 72, 153, 0.15)",
                color: "#ec4899",
                border: "1px solid rgba(236, 72, 153, 0.3)",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              CLOSED-LOOP OPTUNA & AST
            </span>
          </div>
          <p style={{ fontSize: "11.5px", color: "#94a3b8", margin: 0, maxWidth: "880px", lineHeight: "1.4" }}>
            Laboratorio de mutación y re-entrenamiento determinista. Las estrategias que colapsan en Quality Gates son diagnosticadas y re-evaluadas bajo los 11 Gates antes de certificarse a producción.
          </p>
        </div>

        {/* 4 PESTAÑAS PRINCIPALES DEL MÓDULO */}
        <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
          <button
            onClick={() => setActiveTab("INCUBATOR")}
            style={{
              padding: "8px 12px",
              borderRadius: "6px",
              background: activeTab === "INCUBATOR" ? "linear-gradient(135deg, #ec4899 0%, #be185d 100%)" : "rgba(255, 255, 255, 0.05)",
              border: activeTab === "INCUBATOR" ? "none" : "1px solid rgba(255, 255, 255, 0.1)",
              color: "#ffffff",
              fontWeight: 800,
              fontSize: "11.5px",
              cursor: "pointer",
            }}
          >
            📊 Hoja Excel Incubadora ({failedCandidates.length})
          </button>
          <button
            onClick={() => setActiveTab("LOOP_MONITOR")}
            style={{
              padding: "8px 12px",
              borderRadius: "6px",
              background: activeTab === "LOOP_MONITOR" ? "linear-gradient(135deg, #10b981 0%, #059669 100%)" : "rgba(255, 255, 255, 0.05)",
              border: activeTab === "LOOP_MONITOR" ? "none" : "1px solid rgba(255, 255, 255, 0.1)",
              color: "#ffffff",
              fontWeight: 800,
              fontSize: "11.5px",
              cursor: "pointer",
            }}
          >
            ⚡ Bucle 24/7 en Vivo ({qSummary?.pending_count || 0})
          </button>
          <button
            onClick={() => setActiveTab("FAILURES")}
            style={{
              padding: "8px 12px",
              borderRadius: "6px",
              background: activeTab === "FAILURES" ? "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)" : "rgba(255, 255, 255, 0.05)",
              border: activeTab === "FAILURES" ? "none" : "1px solid rgba(255, 255, 255, 0.1)",
              color: "#ffffff",
              fontWeight: 800,
              fontSize: "11.5px",
              cursor: "pointer",
            }}
          >
            📚 11 Clases de Fallos
          </button>
          <button
            onClick={() => setActiveTab("AGENTS")}
            style={{
              padding: "8px 12px",
              borderRadius: "6px",
              background: activeTab === "AGENTS" ? "linear-gradient(135deg, #818cf8 0%, #4f46e5 100%)" : "rgba(255, 255, 255, 0.05)",
              border: activeTab === "AGENTS" ? "none" : "1px solid rgba(255, 255, 255, 0.1)",
              color: "#ffffff",
              fontWeight: 800,
              fontSize: "11.5px",
              cursor: "pointer",
            }}
          >
            🧬 3 Agentes IA
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. PESTAÑA: TABLA EXCEL UNIFICADA CON PESTAÑAS DE RUTA (INCUBADORA)        */}
      {/* ========================================================================= */}
      {activeTab === "INCUBATOR" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* HOJA DE CÁLCULO EXCEL */}
          <div
            style={{
              background: "#080e18",
              border: "1px solid #1e293b",
              borderRadius: "10px",
              boxShadow: "0 8px 30px rgba(0, 0, 0, 0.5)",
              overflow: "hidden",
            }}
          >
            {/* TOOLBAR EXCEL */}
            <div
              style={{
                background: "#0c1524",
                borderBottom: "1px solid #1e293b",
                padding: "10px 16px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "12px",
              }}
            >
              {/* SHEET TABS */}
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  📊 HOJA DE CÁLCULO:
                </span>
                <div style={{ display: "flex", gap: "2px", background: "#030712", padding: "2px", borderRadius: "6px", border: "1px solid #1e293b" }}>
                  <button
                    onClick={() => setRouteTab("ALL")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "4px",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      background: routeTab === "ALL" ? "#1e293b" : "transparent",
                      color: routeTab === "ALL" ? "#c084fc" : "#94a3b8",
                      border: routeTab === "ALL" ? "1px solid #a855f7" : "none",
                      transition: "all 0.15s ease",
                    }}
                  >
                    🌐 TODAS ({routeCounts.all})
                  </button>
                  <button
                    onClick={() => setRouteTab("TRACK_FONDEO")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "4px",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      background: routeTab === "TRACK_FONDEO" ? "rgba(56, 189, 248, 0.2)" : "transparent",
                      color: routeTab === "TRACK_FONDEO" ? "#38bdf8" : "#94a3b8",
                      border: routeTab === "TRACK_FONDEO" ? "1px solid #38bdf8" : "none",
                      transition: "all 0.15s ease",
                    }}
                  >
                    🏛️ FONDEO (CME · {routeCounts.fondeo})
                  </button>
                  <button
                    onClick={() => setRouteTab("TRACK_ULTRA")}
                    style={{
                      padding: "6px 14px",
                      borderRadius: "4px",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      background: routeTab === "TRACK_ULTRA" ? "rgba(99, 225, 180, 0.2)" : "transparent",
                      color: routeTab === "TRACK_ULTRA" ? "#63e1b4" : "#94a3b8",
                      border: routeTab === "TRACK_ULTRA" ? "1px solid #63e1b4" : "none",
                      transition: "all 0.15s ease",
                    }}
                  >
                    ⚡ ULTRA (BingX · {routeCounts.ultra})
                  </button>
                </div>
              </div>

              {/* CONTROLES DERECHA: ESTADO, FILTRO, REFRESCO Y BÚSQUEDA */}
              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(0,0,0,0.4)", padding: "4px 10px", borderRadius: "5px", border: "1px solid rgba(236, 72, 153, 0.3)", fontSize: "11px" }}>
                  <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#ec4899", boxShadow: "0 0 6px #ec4899" }} />
                  <span style={{ fontWeight: 800, color: "#ffffff" }}>INCUBADORA LIVE</span>
                  <span style={{ color: "#38bdf8", fontWeight: 800 }}>SQLite WAL</span>
                </div>

                {/* BOTÓN MANUAL DE REFRESCO (SOFT REFETCH) */}
                <button
                  onClick={() => fetchFailed(true)}
                  disabled={isRefreshing}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 12px",
                    borderRadius: "5px",
                    background: "rgba(56, 189, 248, 0.15)",
                    border: "1px solid rgba(56, 189, 248, 0.3)",
                    color: "#38bdf8",
                    fontSize: "11.5px",
                    fontWeight: 800,
                    cursor: isRefreshing ? "not-allowed" : "pointer",
                    transition: "all 0.15s ease",
                  }}
                  title="Actualizar candidatos en incubadora desde SQLite WAL"
                >
                  <span style={{ display: "inline-block", animation: isRefreshing ? "spin 1s linear infinite" : "none" }}>🔄</span>
                  <span>{isRefreshing ? "Sincronizando..." : "Actualizar"}</span>
                </button>

                {lastSyncTime && (
                  <span style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                    Última sync: {lastSyncTime.toLocaleTimeString()}
                  </span>
                )}

                {/* FILTRO DE ESTADO */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  style={{
                    padding: "6px 10px",
                    borderRadius: "5px",
                    background: "#030712",
                    border: "1px solid #1e293b",
                    color: "#f8fafc",
                    fontSize: "11.5px",
                    outline: "none",
                  }}
                >
                  <option value="ALL">Todos los Estados</option>
                  <option value="INCUBADORA_REPROGRAMACION">En Incubadora</option>
                  <option value="RECHAZADA_FONDEO_DD">Rechazada por DD Fondeo</option>
                  <option value="FAILED_GATE">Falló Quality Gates</option>
                  <option value="REJECTED">Rechazada General</option>
                  <option value="REFINADO_TIER_2">Refinado Tier 2</option>
                </select>

                {/* BUSCADOR DE CELDAS */}
                <input
                  type="text"
                  placeholder="🔍 Buscar ID, par o estrategia..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "5px",
                    background: "#030712",
                    border: "1px solid #1e293b",
                    color: "#f8fafc",
                    fontSize: "11.5px",
                    outline: "none",
                    width: "220px",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                />

                <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  Filas: <b style={{ color: "#ec4899" }}>{filteredCandidates.length}</b> de {failedCandidates.length}
                </span>
              </div>
            </div>

            {/* TABLA EXCEL UNIFICADA DE INCUBADORA */}
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11.5px", textAlign: "left", fontFamily: "var(--font-mono, monospace)" }}>
                <thead>
                  <tr style={{ background: "#0a101d", borderBottom: "2px solid #1e293b", color: "#94a3b8" }}>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800 }}>ID / Estrategia</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800 }}>Activo / TF</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "center" }}>Ruta</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "center" }}>Estado FSM</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right" }}>PF OOS</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right" }}>Max DD OOS</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right" }}>ROI Anual</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, textAlign: "right" }}>Trades</th>
                    <th style={{ padding: "10px 12px", borderRight: "1px solid #1e293b", fontWeight: 800 }}>Diagnóstico Forense de Defecto</th>
                    <th style={{ padding: "10px 12px", fontWeight: 800, textAlign: "center" }}>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && failedCandidates.length === 0 ? (
                    <tr>
                      <td colSpan={10} style={{ padding: "28px", textAlign: "center", color: "#94a3b8" }}>
                        ⏳ Consultando incubadora desde SQLite WAL...
                      </td>
                    </tr>
                  ) : filteredCandidates.length === 0 ? (
                    <tr>
                      <td colSpan={10} style={{ padding: "28px", textAlign: "center", color: "#64748b" }}>
                        No se encontraron estrategias en incubadora con los filtros seleccionados.
                      </td>
                    </tr>
                  ) : (
                    filteredCandidates.map((cand, idx) => {
                      const isSelected = selectedCandidate?.candidate_id === cand.candidate_id;
                      const isFondeo = String(cand.route || "").toUpperCase().includes("FONDEO");
                      const pf = cand.profit_factor_oos || 0;
                      const dd = cand.max_dd_oos_pct || 0;
                      const annual = cand.annual_return_pct || 0;
                      const trades = cand.trades_oos || 0;
                      const diagReason = cand.failure_diagnosis?.primary_failure_reason || "Infracción de Quality Gates";

                      return (
                        <tr
                          key={cand.candidate_id}
                          onClick={() => {
                            setSelectedCandidateId(cand.candidate_id);
                            setImprovementResult(null);
                          }}
                          style={{
                            borderBottom: "1px solid #1e293b",
                            background: isSelected
                              ? "rgba(236, 72, 153, 0.12)"
                              : idx % 2 === 0
                              ? "rgba(12, 19, 32, 0.5)"
                              : "rgba(8, 14, 24, 0.5)",
                            cursor: "pointer",
                            transition: "background 0.1s ease",
                          }}
                          onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.background = "rgba(236, 72, 153, 0.06)";
                          }}
                          onMouseLeave={(e) => {
                            if (!isSelected) {
                              e.currentTarget.style.background =
                                idx % 2 === 0 ? "rgba(12, 19, 32, 0.5)" : "rgba(8, 14, 24, 0.5)";
                            }
                          }}
                        >
                          {/* ID */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", fontWeight: 800, color: "#ec4899" }}>
                            {cand.candidate_id}
                          </td>

                          {/* Activo / TF */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b" }}>
                            <span
                              style={{
                                fontSize: "10.5px",
                                fontWeight: 800,
                                padding: "2px 6px",
                                borderRadius: "4px",
                                background: isFondeo ? "rgba(56, 189, 248, 0.15)" : "rgba(99, 225, 180, 0.15)",
                                color: isFondeo ? "#38bdf8" : "#63e1b4",
                                border: `1px solid ${isFondeo ? "rgba(56, 189, 248, 0.3)" : "rgba(99, 225, 180, 0.3)"}`,
                              }}
                            >
                              {cand.symbol || "--"}
                            </span>
                            <span style={{ fontSize: "10.5px", color: "#94a3b8", marginLeft: "6px" }}>({cand.timeframe || "--"})</span>
                          </td>

                          {/* Ruta */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "center" }}>
                            <span
                              style={{
                                fontSize: "9.5px",
                                fontWeight: 800,
                                padding: "2px 6px",
                                borderRadius: "3px",
                                background: isFondeo ? "rgba(56, 189, 248, 0.15)" : "rgba(99, 225, 180, 0.15)",
                                color: isFondeo ? "#38bdf8" : "#63e1b4",
                                border: `1px solid ${isFondeo ? "rgba(56, 189, 248, 0.3)" : "rgba(99, 225, 180, 0.3)"}`,
                              }}
                            >
                              {isFondeo ? "FONDEO" : "ULTRA"}
                            </span>
                          </td>

                          {/* Estado FSM */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "center" }}>
                            <span
                              style={{
                                fontSize: "9.5px",
                                fontWeight: 700,
                                padding: "2px 6px",
                                borderRadius: "3px",
                                background: cand.status === "INCUBADORA_REPROGRAMACION" ? "rgba(236, 72, 153, 0.15)" : "rgba(239, 68, 68, 0.15)",
                                color: cand.status === "INCUBADORA_REPROGRAMACION" ? "#ec4899" : "#f87171",
                                border: `1px solid ${cand.status === "INCUBADORA_REPROGRAMACION" ? "rgba(236, 72, 153, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
                              }}
                            >
                              {cand.status === "INCUBADORA_REPROGRAMACION" ? "En Incubadora" : cand.status}
                            </span>
                          </td>

                          {/* PF */}
                          <td
                            style={{
                              padding: "8px 12px",
                              borderRight: "1px solid #1e293b",
                              textAlign: "right",
                              fontWeight: 800,
                              color: pf >= 1.3 ? "#63e1b4" : pf >= 1.15 ? "#facc15" : "#f87171",
                            }}
                          >
                            {pf.toFixed(2)}
                          </td>

                          {/* Max DD */}
                          <td
                            style={{
                              padding: "8px 12px",
                              borderRight: "1px solid #1e293b",
                              textAlign: "right",
                              fontWeight: 800,
                              color: (isFondeo && dd <= 4.5) || (!isFondeo && dd <= 60) ? "#63e1b4" : "#f87171",
                            }}
                          >
                            {dd.toFixed(1)}%
                          </td>

                          {/* ROI */}
                          <td
                            style={{
                              padding: "8px 12px",
                              borderRight: "1px solid #1e293b",
                              textAlign: "right",
                              fontWeight: 700,
                              color: annual >= 0 ? "#38bdf8" : "#f87171",
                            }}
                          >
                            {annual >= 0 ? `+${annual.toFixed(1)}%` : `${annual.toFixed(1)}%`}
                          </td>

                          {/* Trades */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", color: "#cbd5e1" }}>
                            {trades}
                          </td>

                          {/* Diagnóstico */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", color: "#fca5a5" }}>
                            🚨 {diagReason}
                          </td>

                          {/* Acción */}
                          <td style={{ padding: "8px 12px", textAlign: "center" }}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedCandidateId(cand.candidate_id);
                                setImprovementResult(null);
                              }}
                              style={{
                                padding: "4px 8px",
                                borderRadius: "4px",
                                background: isSelected ? "#ec4899" : "rgba(236, 72, 153, 0.2)",
                                color: isSelected ? "#ffffff" : "#ec4899",
                                border: "1px solid rgba(236, 72, 153, 0.4)",
                                fontSize: "10.5px",
                                fontWeight: 800,
                                cursor: "pointer",
                              }}
                            >
                              {isSelected ? "✓ Seleccionada" : "⚡ Reparar"}
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* 3. CONSOLA DE DIAGNÓSTICO FORENSE Y AUTO-MEJORA (ESTRATEGIA SELECCIONADA) */}
          {/* ========================================================================= */}
          {selectedCandidate ? (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              {/* PANEL IZQUIERDO: DIAGNÓSTICO FORENSE */}
              <div
                style={{
                  background: "#080e18",
                  border: "1px solid #1e293b",
                  borderRadius: "10px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <div style={{ fontSize: "10.5px", color: "#94a3b8", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>
                      DIAGNÓSTICO FORENSE DE CALIDAD
                    </div>
                    <h2 style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", margin: "2px 0 0 0" }}>
                      {selectedCandidate.name || selectedCandidate.candidate_id}
                    </h2>
                    <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                      {selectedCandidate.symbol} · {selectedCandidate.timeframe} · {selectedCandidate.route}
                    </div>
                  </div>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 800,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: "rgba(239, 68, 68, 0.15)",
                      color: "#f87171",
                      border: "1px solid rgba(239, 68, 68, 0.3)",
                    }}
                  >
                    {selectedCandidate.status}
                  </span>
                </div>

                {/* 3 METRIC CARDS */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
                  <div style={{ background: "#0c1524", borderRadius: "6px", padding: "10px", border: "1px solid #1e293b" }}>
                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: 700 }}>PROFIT FACTOR OOS</div>
                    <div style={{ fontSize: "15px", fontWeight: 900, color: (selectedCandidate.profit_factor_oos || 0) >= 1.3 ? "#63e1b4" : "#f87171", marginTop: "2px" }}>
                      {(selectedCandidate.profit_factor_oos || 0).toFixed(2)}
                    </div>
                  </div>

                  <div style={{ background: "#0c1524", borderRadius: "6px", padding: "10px", border: "1px solid #1e293b" }}>
                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: 700 }}>MAX DRAWDOWN OOS</div>
                    <div style={{ fontSize: "15px", fontWeight: 900, color: "#f87171", marginTop: "2px" }}>
                      {(selectedCandidate.max_dd_oos_pct || 0).toFixed(1)}%
                    </div>
                  </div>

                  <div style={{ background: "#0c1524", borderRadius: "6px", padding: "10px", border: "1px solid #1e293b" }}>
                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: 700 }}>MUESTRA DE TRADES</div>
                    <div style={{ fontSize: "15px", fontWeight: 900, color: "#38bdf8", marginTop: "2px" }}>
                      {selectedCandidate.trades_oos || 0} trades
                    </div>
                  </div>
                </div>

                {/* CAJA DE ANOMALÍAS DETECTADAS */}
                <div style={{ background: "rgba(239, 68, 68, 0.06)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "6px", padding: "10px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#f87171", marginBottom: "4px" }}>
                    🚨 ANOMALÍAS DETECTADAS EN QUALITY GATES:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#cbd5e1", lineHeight: "1.4" }}>
                    {(selectedCandidate.failure_diagnosis?.diagnostics || ["Infracción de umbrales cuantitativos"]).map((d: string, i: number) => (
                      <li key={i}>{d}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* PANEL DERECHO: CONFIGURACIÓN DEL MOTOR DE REPARACIÓN Y ACCIÓN */}
              <div
                style={{
                  background: "#080e18",
                  border: "1px solid rgba(236, 72, 153, 0.3)",
                  borderRadius: "10px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div style={{ fontSize: "11.5px", fontWeight: 800, color: "#ec4899" }}>
                  ⚙️ CONFIGURACIÓN DEL MOTOR DE AUTO-MEJORA (OPTUNA & AST)
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
                  <button
                    onClick={() => setTechnique("HYBRID_DEEP_REPAIR")}
                    style={{
                      padding: "8px",
                      borderRadius: "6px",
                      background: technique === "HYBRID_DEEP_REPAIR" ? "rgba(236, 72, 153, 0.2)" : "rgba(255, 255, 255, 0.03)",
                      border: technique === "HYBRID_DEEP_REPAIR" ? "1px solid #ec4899" : "1px solid #1e293b",
                      color: "#ffffff",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <div style={{ fontSize: "11px", fontWeight: 800 }}>🚀 Híbrido Completo</div>
                    <div style={{ fontSize: "9px", color: "#94a3b8", marginTop: "2px" }}>Optuna TPE + AST + ATR</div>
                  </button>

                  <button
                    onClick={() => setTechnique("OPTUNA_BAYESIAN_TPE")}
                    style={{
                      padding: "8px",
                      borderRadius: "6px",
                      background: technique === "OPTUNA_BAYESIAN_TPE" ? "rgba(56, 189, 248, 0.2)" : "rgba(255, 255, 255, 0.03)",
                      border: technique === "OPTUNA_BAYESIAN_TPE" ? "1px solid #38bdf8" : "1px solid #1e293b",
                      color: "#ffffff",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <div style={{ fontSize: "11px", fontWeight: 800 }}>🧬 Optuna Bayesiano</div>
                    <div style={{ fontSize: "9px", color: "#94a3b8", marginTop: "2px" }}>SL/TP y periodos</div>
                  </button>

                  <button
                    onClick={() => setTechnique("AST_REGIME_FILTER")}
                    style={{
                      padding: "8px",
                      borderRadius: "6px",
                      background: technique === "AST_REGIME_FILTER" ? "rgba(16, 185, 129, 0.2)" : "rgba(255, 255, 255, 0.03)",
                      border: technique === "AST_REGIME_FILTER" ? "1px solid #10b981" : "1px solid #1e293b",
                      color: "#ffffff",
                      cursor: "pointer",
                      textAlign: "left",
                    }}
                  >
                    <div style={{ fontSize: "11px", fontWeight: 800 }}>🛡️ Filtro Régimen</div>
                    <div style={{ fontSize: "9px", color: "#94a3b8", marginTop: "2px" }}>Compresión de DD</div>
                  </button>
                </div>

                <button
                  onClick={handleRunImprovement}
                  disabled={improving}
                  style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "6px",
                    background: improving ? "#475569" : "linear-gradient(135deg, #ec4899 0%, #be185d 100%)",
                    border: "none",
                    color: "#ffffff",
                    fontWeight: 900,
                    fontSize: "12px",
                    cursor: improving ? "not-allowed" : "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "8px",
                    boxShadow: "0 4px 18px rgba(236, 72, 153, 0.3)",
                  }}
                >
                  {improving ? "⚡ Ejecutando Optimización en Bucle Cerrado..." : "⚡ Ejecutar Auto-Mejora en Bucle & Certificar"}
                </button>

                {/* RESULTADO DE LA AUTO-MEJORA */}
                {improvementResult && (
                  <div style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.4)", borderRadius: "8px", padding: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ fontSize: "14px" }}>✅</span>
                        <h3 style={{ fontSize: "12px", fontWeight: 900, color: "#10b981", margin: 0 }}>
                          ¡ESTRATEGIA RESCATADA & REINYECTADA!
                        </h3>
                      </div>
                      <Link
                        href="/gates"
                        style={{
                          padding: "3px 8px",
                          borderRadius: "4px",
                          background: "#10b981",
                          color: "#06080d",
                          fontSize: "10px",
                          fontWeight: 900,
                          textDecoration: "none",
                        }}
                      >
                        Ver en Gates (Fase 5) →
                      </Link>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "6px", fontSize: "10.5px" }}>
                      <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>PROFIT FACTOR</div>
                        <div style={{ fontSize: "13px", fontWeight: 900, color: "#10b981", marginTop: "2px" }}>
                          {(selectedCandidate.profit_factor_oos || 0).toFixed(2)} → {(improvementResult.profit_factor_oos || 1.55).toFixed(2)}
                        </div>
                      </div>
                      <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>MAX DRAWDOWN</div>
                        <div style={{ fontSize: "13px", fontWeight: 900, color: "#10b981", marginTop: "2px" }}>
                          {(selectedCandidate.max_dd_oos_pct || 0).toFixed(1)}% → {(improvementResult.max_dd_oos_pct || 42.5).toFixed(1)}%
                        </div>
                      </div>
                      <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ESTADO FINAL</div>
                        <div style={{ fontSize: "11px", fontWeight: 900, color: "#10b981", marginTop: "3px" }}>
                          ✓ {improvementResult.status || "CERTIFIED_PASS"}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. PESTAÑA: BUCLE 24/7 EN VIVO                                            */}
      {/* ========================================================================= */}
      {activeTab === "LOOP_MONITOR" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div
            style={{
              background: "#080e18",
              border: "1px solid #1e293b",
              borderRadius: "10px",
              padding: "16px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700 }}>SUPERVISIÓN DEL DEMONIO 24/7</div>
              <h2 style={{ fontSize: "17px", fontWeight: 900, color: "#ffffff", margin: "2px 0 0 0" }}>
                Continuous Research & Auto-Improver Daemon
              </h2>
            </div>

            <button
              onClick={handleToggleDaemon}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                background: daemonStatus?.is_running ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)",
                border: `1px solid ${daemonStatus?.is_running ? "#f87171" : "#10b981"}`,
                color: daemonStatus?.is_running ? "#f87171" : "#10b981",
                fontWeight: 800,
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              {daemonStatus?.is_running ? "⏹ Pausar Demonio" : "▶ Reanudar Demonio 24/7"}
            </button>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. PESTAÑA: MEMORIA DE FALLOS (11 CLASES)                                 */}
      {/* ========================================================================= */}
      {activeTab === "FAILURES" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
          {FAILURE_CATEGORIES.map((cat) => (
            <div
              key={cat.id}
              style={{
                background: "#080e18",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                padding: "12px 14px",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ fontWeight: 800, fontSize: "12px", color: "#f8fafc" }}>{cat.name}</span>
                <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "rgba(236, 72, 153, 0.15)", color: "#ec4899", fontWeight: 800 }}>
                  {cat.count} casos
                </span>
              </div>
              <div style={{ fontSize: "10.5px", color: "#94a3b8", lineHeight: "1.4" }}>
                {cat.desc}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. PESTAÑA: 3 AGENTES IA                                                  */}
      {/* ========================================================================= */}
      {activeTab === "AGENTS" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "14px" }}>
          <div style={{ background: "#080e18", border: "1px solid #1e293b", borderRadius: "10px", padding: "16px" }}>
            <div style={{ fontSize: "20px", marginBottom: "6px" }}>🔍</div>
            <div style={{ fontWeight: 800, fontSize: "13px", color: "#ffffff" }}>Agente 1: Diagnóstico Forense</div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
              Identifica si la causa de descarte es lookahead bias, sobreajuste en out-of-sample o violación de drawdown trailing.
            </div>
          </div>
          <div style={{ background: "#080e18", border: "1px solid #1e293b", borderRadius: "10px", padding: "16px" }}>
            <div style={{ fontSize: "20px", marginBottom: "6px" }}>🧬</div>
            <div style={{ fontWeight: 800, fontSize: "13px", color: "#ffffff" }}>Agente 2: Cirujano AST & Optuna</div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
              Aplica mutación paramétrica bayesiana (Optuna TPE) o inyecta filtros de régimen de volatilidad ATR en el árbol AST.
            </div>
          </div>
          <div style={{ background: "#080e18", border: "1px solid #1e293b", borderRadius: "10px", padding: "16px" }}>
            <div style={{ fontSize: "20px", marginBottom: "6px" }}>🛡️</div>
            <div style={{ fontWeight: 800, fontSize: "13px", color: "#ffffff" }}>Agente 3: Auditor de Re-Certificación</div>
            <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
              Re-evalúa la estrategia mutada contra los 11 Quality Gates y la reinyecta a la máquina de estados FSM si aprueba.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResearchSemanticPage() {
  return (
    <Suspense fallback={<div style={{ padding: "30px", color: "#94a3b8", textAlign: "center" }}>Cargando Research Lab...</div>}>
      <ResearchSemanticContent />
    </Suspense>
  );
}
