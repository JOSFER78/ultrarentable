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
// CATÁLOGO DE LAS 11 CLASES DE FALLO CUANTITATIVO (taxonomía documentada)
// Los conteos por clase salen de la consulta real failed-candidates; si el backend
// no entrega esa agregación, se muestra NO_EVIDENCE (nunca un número inventado).
// ============================================================================
const FAILURE_CATEGORIES = [
  { id: "LOOKAHEAD_BIAS", name: "Sesgo de Anticipación (Lookahead)", desc: "Uso de precios futuros o Close[0] no cerrado." },
  { id: "OVERFITTING_CURVE_FITTING", name: "Sobreajuste Paramétrico (Overfitting)", desc: "Pérdida de rendimiento en Out-of-Sample." },
  { id: "OUTLIER_DEPENDENCY", name: "Dependencia de Outliers", desc: "Los 2 mejores trades concentran > 20% del PnL." },
  { id: "ASYMMETRIC_SLIPPAGE_EROSION", name: "Erosión por Slippage / Fricción", desc: "Colapso ante comisiones taker y spreads dinámicos." },
  { id: "REGIME_FRAGILITY", name: "Fragilidad de Régimen Macro", desc: "Ruptura al cambiar de tendencia a rango o alta volatilidad." },
  { id: "MARTINGALE_UNBOUNDED_RISK", name: "Riesgo No Acotado / Promediación", desc: "Aumento de tamaño sin Stop Loss estricto." },
  { id: "OVERNIGHT_GAP_EXPOSURE", name: "Riesgo de Gap Nocturno (CME)", desc: "Posiciones abiertas en cierre de mercado (infracción Prop)." },
  { id: "DRAWDOWN_TRAILING_VIOLATION", name: "Violación de Trailing DD / DLL", desc: "Infracción del límite de pérdida diaria intra-trade." },
  { id: "LOW_SAMPLE_SIGNIFICANCE", name: "Muestra Insuficiente (DSR Bajo)", desc: "Menos de 30-100 trades estadísticamente válidos." },
  { id: "EXECUTION_LATENCY_SENSITIVITY", name: "Sensibilidad a Latencia HFT", desc: "Estrategias dependientes de fills perfectos sin slippage." },
  { id: "NEGATIVE_CONVEXITY_FAT_TAIL", name: "Convexidad Negativa", desc: "Relación riesgo/beneficio invertida (SL >> TP)." },
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

  // Trials reales del registro de investigación (estado de campañas)
  const [trialsData, setTrialsData] = useState<any>(null);

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

  // 1b. Trials reales registrados (campañas/fases de investigación)
  const fetchTrials = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/research/trials?limit=200", { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        setTrialsData(data);
      } else {
        setTrialsData({ unavailable: true });
      }
    } catch (e) {
      setTrialsData({ unavailable: true });
      console.error("Error al obtener trials de investigación:", e);
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
    fetchTrials();
  }, [fetchDaemonStatus, fetchFailed, fetchTrials]);

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
        // El backend devuelve {success, candidate_id, engine_version, mode,
        // certification_owned_by, research_result}; NO existe "upgraded_candidate".
        setImprovementResult(data);
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

  // Claves reales del estado del daemon (continuous_research_daemon.get_status):
  // is_running, interval_seconds, last_run_timestamp, queue, queue_summary.total_in_queue,
  // stats{cycles_executed, repaired_count, debates_conducted_count}, last_error,
  // engine_version, mode. (NO existen current_processing/live_logs/recent_history.)
  const qSummary = daemonStatus?.queue_summary;
  const daemonQueue: any[] = Array.isArray(daemonStatus?.queue) ? daemonStatus.queue : [];

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
            ⚡ Bucle 24/7 en Vivo ({qSummary?.total_in_queue ?? "NO EVIDENCE"})
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
                      const pf = cand.profit_factor_oos;
                      const dd = cand.max_dd_oos_pct;
                      const annual = cand.annual_return_pct;
                      const trades = cand.trades_oos;
                      const diagReason = cand.failure_diagnosis?.primary_failure_reason || "NO EVIDENCE";

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
                              {cand.symbol || "NO EVIDENCE"}
                            </span>
                            <span style={{ fontSize: "10.5px", color: "#94a3b8", marginLeft: "6px" }}>({cand.timeframe || "NO EVIDENCE"})</span>
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
                              color: pf === undefined ? "#64748b" : pf >= 1.3 ? "#63e1b4" : pf >= 1.15 ? "#facc15" : "#f87171",
                            }}
                          >
                            {pf === undefined ? "NO EVIDENCE" : pf.toFixed(2)}
                          </td>

                          {/* Max DD */}
                          <td
                            style={{
                              padding: "8px 12px",
                              borderRight: "1px solid #1e293b",
                              textAlign: "right",
                              fontWeight: 800,
                              color: dd === undefined ? "#64748b" : (isFondeo && dd <= 4.5) || (!isFondeo && dd <= 60) ? "#63e1b4" : "#f87171",
                            }}
                          >
                            {dd === undefined ? "NO EVIDENCE" : `${dd.toFixed(1)}%`}
                          </td>

                          {/* ROI */}
                          <td
                            style={{
                              padding: "8px 12px",
                              borderRight: "1px solid #1e293b",
                              textAlign: "right",
                              fontWeight: 700,
                              color: annual === undefined ? "#64748b" : annual >= 0 ? "#38bdf8" : "#f87171",
                            }}
                          >
                            {annual === undefined ? "NO EVIDENCE" : annual >= 0 ? `+${annual.toFixed(1)}%` : `${annual.toFixed(1)}%`}
                          </td>

                          {/* Trades */}
                          <td style={{ padding: "8px 12px", borderRight: "1px solid #1e293b", textAlign: "right", color: "#cbd5e1" }}>
                            {trades === undefined ? "NO EVIDENCE" : trades}
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
                    <div style={{ fontSize: "15px", fontWeight: 900, color: selectedCandidate.profit_factor_oos === undefined ? "#64748b" : selectedCandidate.profit_factor_oos >= 1.3 ? "#63e1b4" : "#f87171", marginTop: "2px" }}>
                      {selectedCandidate.profit_factor_oos === undefined ? "NO EVIDENCE" : selectedCandidate.profit_factor_oos.toFixed(2)}
                    </div>
                  </div>

                  <div style={{ background: "#0c1524", borderRadius: "6px", padding: "10px", border: "1px solid #1e293b" }}>
                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: 700 }}>MAX DRAWDOWN OOS</div>
                    <div style={{ fontSize: "15px", fontWeight: 900, color: "#f87171", marginTop: "2px" }}>
                      {selectedCandidate.max_dd_oos_pct === undefined ? "NO EVIDENCE" : `${selectedCandidate.max_dd_oos_pct.toFixed(1)}%`}
                    </div>
                  </div>

                  <div style={{ background: "#0c1524", borderRadius: "6px", padding: "10px", border: "1px solid #1e293b" }}>
                    <div style={{ fontSize: "9px", color: "#94a3b8", fontWeight: 700 }}>MUESTRA DE TRADES</div>
                    <div style={{ fontSize: "15px", fontWeight: 900, color: "#38bdf8", marginTop: "2px" }}>
                      {selectedCandidate.trades_oos === undefined ? "NO EVIDENCE" : `${selectedCandidate.trades_oos} trades`}
                    </div>
                  </div>
                </div>

                {/* CAJA DE ANOMALÍAS DETECTADAS */}
                <div style={{ background: "rgba(239, 68, 68, 0.06)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "6px", padding: "10px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#f87171", marginBottom: "4px" }}>
                    🚨 ANOMALÍAS DETECTADAS EN QUALITY GATES:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "11px", color: "#cbd5e1", lineHeight: "1.4" }}>
                    {(selectedCandidate.failure_diagnosis?.diagnostics || ["NO EVIDENCE"]).map((d: string, i: number) => (
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

                {/* RESULTADO REAL DEL BUCLE CERRADO (claves devueltas por research_router) */}
                {improvementResult && (
                  <div style={{ background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.4)", borderRadius: "8px", padding: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ fontSize: "14px" }}>{improvementResult.success ? "✅" : "⚠️"}</span>
                        <h3 style={{ fontSize: "12px", fontWeight: 900, color: improvementResult.success ? "#10b981" : "#f59e0b", margin: 0 }}>
                          {improvementResult.success ? "EJECUCIÓN DE BUCLE CERRADO COMPLETADA" : "BUCLE CERRADO SIN ÉXITO (VER ESTADO REAL)"}
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
                        Ver en Gates →
                      </Link>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "6px", fontSize: "10.5px" }}>
                      <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ESTADO REAL (research_result)</div>
                        <div style={{ fontSize: "11px", fontWeight: 900, color: "#10b981", marginTop: "3px" }}>
                          {improvementResult.research_result?.status || "NO EVIDENCE"}
                        </div>
                      </div>
                      <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ENGINE VERSION</div>
                        <div style={{ fontSize: "11px", fontWeight: 900, color: "#38bdf8", marginTop: "3px" }}>
                          {improvementResult.engine_version || "NO EVIDENCE"}
                        </div>
                      </div>
                      <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                        <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>CERTIFICACIÓN PROPIEDAD DE</div>
                        <div style={{ fontSize: "11px", fontWeight: 900, color: "#a855f7", marginTop: "3px" }}>
                          {improvementResult.certification_owned_by || "NO EVIDENCE"}
                        </div>
                      </div>
                    </div>
                    <div style={{ fontSize: "9.5px", color: "#64748b", marginTop: "6px" }}>
                      Las métricas antes/después solo se muestran cuando el pipeline de certificación las emite con evidencia; aquí no se derivan en cliente.
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

          {/* ESTADO REAL DEL DAEMON (claves de continuous_research_daemon.get_status) */}
          <div style={{ background: "#080e18", border: "1px solid #1e293b", borderRadius: "10px", padding: "16px 20px" }}>
            <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, marginBottom: "10px" }}>ESTADO REAL DEL DAEMON</div>
            {daemonStatus ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "8px", fontSize: "10.5px", fontFamily: "var(--font-mono, monospace)" }}>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>IS_RUNNING</div>
                  <div style={{ fontWeight: 900, color: daemonStatus.is_running ? "#10b981" : "#f87171" }}>{String(daemonStatus.is_running)}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>COLA PENDIENTE</div>
                  <div style={{ fontWeight: 900, color: "#38bdf8" }}>{qSummary?.total_in_queue ?? "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>CICLOS EJECUTADOS</div>
                  <div style={{ fontWeight: 900, color: "#e2e8f0" }}>{daemonStatus.stats?.cycles_executed ?? "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>REPARADAS</div>
                  <div style={{ fontWeight: 900, color: "#e2e8f0" }}>{daemonStatus.stats?.repaired_count ?? daemonStatus.repaired_count ?? "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>DEBATES</div>
                  <div style={{ fontWeight: 900, color: "#e2e8f0" }}>{daemonStatus.stats?.debates_conducted_count ?? daemonStatus.debates_conducted_count ?? "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ÚLTIMA EJECUCIÓN (UTC)</div>
                  <div style={{ fontWeight: 900, color: "#e2e8f0" }}>{daemonStatus.last_run_timestamp || "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ENGINE / MODO</div>
                  <div style={{ fontWeight: 900, color: "#a855f7" }}>
                    {daemonStatus.engine_version || "NO EVIDENCE"} · {daemonStatus.mode || "NO EVIDENCE"}
                  </div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ÚLTIMO ERROR</div>
                  <div style={{ fontWeight: 900, color: daemonStatus.last_error ? "#f87171" : "#10b981" }}>{daemonStatus.last_error || "NINGUNO"}</div>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: "11px", color: "#64748b" }}>NO EVIDENCE — el endpoint del daemon no ha respondido todavía.</div>
            )}

            {/* COLA REAL DESDE SQLite (daemon.queue) */}
            <div style={{ marginTop: "12px" }}>
              <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 700, marginBottom: "6px" }}>COLA REAL ({daemonQueue.length})</div>
              {daemonQueue.length === 0 ? (
                <div style={{ fontSize: "10.5px", color: "#64748b" }}>Cola vacía según el daemon (dato real, no estimación).</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px", fontSize: "10px", fontFamily: "var(--font-mono, monospace)" }}>
                  {daemonQueue.slice(0, 10).map((item: any, idx: number) => (
                    <div key={idx} style={{ background: "#030712", padding: "5px 8px", borderRadius: "4px", color: "#c084fc" }}>
                      {JSON.stringify(item)}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* TRIALS REALES REGISTRADOS (Registry de investigación) */}
          <div style={{ background: "#080e18", border: "1px solid #1e293b", borderRadius: "10px", padding: "16px 20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700 }}>TRIALS DE INVESTIGACIÓN REGISTRADOS (GET /api/v1/research/trials)</div>
              <button
                onClick={fetchTrials}
                style={{ padding: "4px 10px", borderRadius: "5px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8", fontSize: "10px", fontWeight: 800, cursor: "pointer" }}
              >
                Refrescar trials
              </button>
            </div>
            {trialsData?.unavailable ? (
              <div style={{ fontSize: "11px", color: "#64748b" }}>NO EVIDENCE — el endpoint de trials no está disponible.</div>
            ) : trialsData ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "8px", fontSize: "10.5px", fontFamily: "var(--font-mono, monospace)" }}>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>TRIALS EN REGISTRO</div>
                  <div style={{ fontWeight: 900, color: "#10b981" }}>{trialsData.count ?? "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>ENGINE VERSION</div>
                  <div style={{ fontWeight: 900, color: "#a855f7" }}>{trialsData.engine_version || "NO EVIDENCE"}</div>
                </div>
                <div style={{ background: "#030712", padding: "6px 8px", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8.5px", color: "#94a3b8" }}>MODO</div>
                  <div style={{ fontWeight: 900, color: "#38bdf8" }}>{trialsData.mode || "NO EVIDENCE"}</div>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: "11px", color: "#64748b" }}>Cargando trials reales…</div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. PESTAÑA: MEMORIA DE FALLOS (11 CLASES)                                 */}
      {/* ========================================================================= */}
      {activeTab === "FAILURES" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          <div style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
            Candidatos fallidos cargados de la consulta real: <span style={{ color: "#ec4899", fontWeight: 800 }}>{routeCounts.all}</span>
            {" · "}Los conteos por clase se muestran solo con evidencia del backend (hoy: NO EVIDENCE).
          </div>
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
                  NO EVIDENCE
                </span>
              </div>
              <div style={{ fontSize: "10.5px", color: "#94a3b8", lineHeight: "1.4" }}>
                {cat.desc}
              </div>
            </div>
          ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. PESTAÑA: 3 AGENTES IA                                                  */}
      {/* ========================================================================= */}
      {activeTab === "AGENTS" && (
        <div style={{ background: "#080e18", border: "1px solid #1e293b", borderRadius: "10px", padding: "20px" }}>
          <div style={{ fontWeight: 800, fontSize: "13px", color: "#ffffff", marginBottom: "8px" }}>Agentes IA: NO EVIDENCE</div>
          <div style={{ fontSize: "11.5px", color: "#94a3b8", lineHeight: "1.5" }}>
            Este módulo no expone hoy un endpoint de agentes IA en el backend. El flujo real disponible es:
            diagnóstico del candidato fallido (failed-candidates), ejecución de bucle cerrado
            (POST /api/v1/research/improve/&#123;id&#125;) y supervisión del daemon 24/7. Cualquier
            descripción de agentes se publicará aquí únicamente cuando exista un endpoint real que la respalde
            (doctrina EVIDENCE-GATED: sin dato, NO_EVIDENCE).
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
