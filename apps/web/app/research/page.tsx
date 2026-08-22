"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

interface CandidateQueueItem {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  status: string;
  tier: string;
  initial_gates: number;
  current_gates: number;
  score: number;
  profit_factor: number;
  net_profit_usd: number;
}

interface RefinementHistoryItem {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  initial_gates: number;
  final_gates: number;
  gate_delta: number;
  is_certified: boolean;
  profit_factor: number;
  net_profit_usd: number;
  timestamp: string;
}

interface LiveLogEntry {
  timestamp: string;
  date_display?: string;
  full_time_display?: string;
  iso_time: string;
  level: string;
  event_type?: string;
  message: string;
  step: string;
  candidate_id?: string | null;
  symbol?: string | null;
  timeframe?: string | null;
  route?: string | null;
  initial_gates?: number | null;
  current_gates?: number | null;
  gate_delta?: number | null;
  profit_factor?: number | null;
  net_profit_usd?: number | null;
  math?: Record<string, any>;
}

interface ResearchDaemonStatus {
  is_running: boolean;
  current_processing: {
    candidate_id: string | null;
    name: string | null;
    symbol: string | null;
    timeframe: string | null;
    route: string | null;
    tier?: string | null;
    step: string;
    iteration: number;
    max_iterations: number;
    progress_pct: number;
    math_telemetry: Record<string, any>;
  } | null;
  stats: {
    total_processed: number;
    total_improved: number;
    total_certified: number;
    total_cycles: number;
    generation_round?: number;
    started_at: string;
  };
  queue_summary: {
    total_in_queue: number;
    pending_count: number;
    processed_count: number;
    tier_1_count?: number;
    tier_2_count: number;
    tier_3_count: number;
    tier_4_count?: number;
  };
  queue: CandidateQueueItem[];
  recent_history: RefinementHistoryItem[];
  live_logs: LiveLogEntry[];
}

export default function ResearchLabPage() {
  const [status, setStatus] = useState<ResearchDaemonStatus>({
    is_running: false,
    current_processing: null,
    stats: { total_processed: 0, total_improved: 0, total_certified: 0, total_cycles: 0, generation_round: 1, started_at: "" },
    queue_summary: { total_in_queue: 0, pending_count: 0, processed_count: 0, tier_1_count: 0, tier_2_count: 0, tier_3_count: 0, tier_4_count: 0 },
    queue: [],
    recent_history: [],
    live_logs: [],
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [candidateDetail, setCandidateDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [filterTier, setFilterTier] = useState<"ALL" | "TIER_1" | "TIER_2" | "TIER_3" | "TIER_4">("ALL");
  const [logFilter, setLogFilter] = useState<"ALL" | "CERT" | "IMPROVED" | "ITER" | "MICRO">("ALL");
  const [autoScroll, setAutoScroll] = useState<boolean>(true);

  const logsFeedRef = useRef<HTMLDivElement>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/research/status");
      if (res.ok) {
        const data: ResearchDaemonStatus = await res.json();
        setStatus(data);
        if (!selectedCandidateId && data.queue.length > 0) {
          setSelectedCandidateId(data.queue[0].candidate_id);
        }
      }
    } catch (err) {
      console.error("Error fetching research status:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCandidateId]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 1500);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Auto-scroll log feed
  useEffect(() => {
    if (autoScroll && logsFeedRef.current) {
      logsFeedRef.current.scrollTop = logsFeedRef.current.scrollHeight;
    }
  }, [status.live_logs, autoScroll]);

  // Fetch detail for selected candidate
  const loadCandidateDetail = useCallback(async (cid: string) => {
    try {
      setDetailLoading(true);
      const res = await fetch(`/api/v1/candidates/${cid}`);
      if (res.ok) {
        const d = await res.json();
        setCandidateDetail(d);
      }
    } catch {
      setCandidateDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCandidateId) {
      loadCandidateDetail(selectedCandidateId);
    }
  }, [selectedCandidateId, loadCandidateDetail]);

  const handleToggleDaemon = async () => {
    try {
      setActionLoading(true);
      const endpoint = status.is_running ? "/api/v1/research/pause" : "/api/v1/research/start";
      const res = await fetch(endpoint, { method: "POST" });
      if (res.ok) {
        const d = await res.json();
        setActionMsg(d.message);
        await fetchStatus();
      }
    } catch {
      setActionMsg("Error al cambiar estado del demonio.");
    } finally {
      setActionLoading(false);
      setTimeout(() => setActionMsg(null), 4000);
    }
  };

  const handleProcessNext = async () => {
    try {
      setActionLoading(true);
      const res = await fetch("/api/v1/research/process-next", { method: "POST" });
      if (res.ok) {
        const d = await res.json();
        setActionMsg(`⚡ Procesando candidato: ${d.candidate_id}`);
        await fetchStatus();
      }
    } catch {
      setActionMsg("Error al procesar el siguiente candidato.");
    } finally {
      setActionLoading(false);
      setTimeout(() => setActionMsg(null), 4000);
    }
  };

  const handleRefineSpecific = async (cid: string) => {
    try {
      setActionLoading(true);
      setActionMsg(`🔬 Refinando candidato ${cid}...`);
      const res = await fetch(`/api/v1/research/refine/${cid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_iterations: 3 }),
      });
      if (res.ok) {
        const d = await res.json();
        setActionMsg(`✓ Refinamiento completado: ${d.gates_passed_count}/11 Gates superados.`);
        await fetchStatus();
        if (selectedCandidateId === cid) {
          loadCandidateDetail(cid);
        }
      }
    } catch {
      setActionMsg("Error durante el refinamiento.");
    } finally {
      setActionLoading(false);
      setTimeout(() => setActionMsg(null), 5000);
    }
  };

  const filteredQueue = status.queue.filter((q) => {
    if (filterTier === "TIER_1") return q.tier === "TIER_1_CERTIFIED" || q.current_gates === 11;
    if (filterTier === "TIER_2") return q.tier === "TIER_2_NEAR_CERTIFIED" || (q.current_gates >= 9 && q.current_gates <= 10);
    if (filterTier === "TIER_3") return q.tier === "TIER_3_INCUBATOR" || (q.current_gates >= 5 && q.current_gates <= 8);
    if (filterTier === "TIER_4") return q.tier === "TIER_4_REJECTED" || q.current_gates < 5;
    return true;
  });

  const filteredLogs = status.live_logs.filter((log) => {
    if (logFilter === "CERT") return log.event_type === "CERTIFICACION" || log.message.includes("CERTIFICADA") || log.level === "SUCCESS";
    if (logFilter === "IMPROVED") return log.event_type === "MEJORA_GATE" || log.event_type === "TIER_UPGRADE" || (log.gate_delta && log.gate_delta > 0);
    if (logFilter === "ITER") return log.event_type === "OPTIMIZACION_ITERACION" || log.step.startsWith("ITERACION");
    if (logFilter === "MICRO") return log.event_type === "MICROESTRUCTURA" || log.math !== undefined;
    return true;
  });

  return (
    <div style={{ padding: "20px 24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 0. ESTRATEGIAS TOP SUB-NAV BAR */}
      <EstrategiasHeaderNav />

      {/* 1. TOP HEADER & CONTROLS */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px", flexWrap: "wrap", gap: "14px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "11px", textDecoration: "none" }}>
              ← Command Center
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "10px", fontWeight: 800, color: "#facc15", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
              PUNTO 4 · PANEL INVESTIGADOR SEMÁNTICO & LABORATORIO CUANTITATIVO
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
            🔬 Laboratorio de Refinamiento Cuantitativo & Bucle Autónomo 24/7
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "12.5px", marginTop: "4px", margin: 0, maxWidth: "1050px" }}>
            Bucle generacional ininterrumpido 24/7 que toma todas las estrategias del catálogo (Tier 4, Tier 3, Tier 2 y Tier 1), ejecuta backtests sobre velas físicas, calcula el perfil Hurst/Parkinson y aplica mutaciones cuantitativas para escalar compuertas.
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          <button
            onClick={handleToggleDaemon}
            disabled={actionLoading}
            style={{
              padding: "9px 18px",
              borderRadius: "8px",
              background: status.is_running ? "rgba(16, 185, 129, 0.15)" : "rgba(250, 204, 21, 0.15)",
              border: `1px solid ${status.is_running ? "rgba(16, 185, 129, 0.5)" : "rgba(250, 204, 21, 0.5)"}`,
              color: status.is_running ? "#34d399" : "#facc15",
              fontSize: "12px",
              fontWeight: 900,
              fontFamily: "var(--font-mono, monospace)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              boxShadow: status.is_running ? "0 0 15px rgba(16, 185, 129, 0.25)" : "none",
            }}
          >
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: status.is_running ? "#34d399" : "#facc15", display: "inline-block" }} />
            {status.is_running ? "🟢 Bucle 24/7 ACTIVO" : "⏸ Bucle PAUSADO (Click para Iniciar)"}
          </button>

          <button
            onClick={handleProcessNext}
            disabled={actionLoading}
            style={{
              padding: "9px 15px",
              borderRadius: "8px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              color: "#38bdf8",
              fontSize: "11.5px",
              fontWeight: 800,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            ⚡ Procesar Siguiente
          </button>

          <button
            onClick={fetchStatus}
            style={{
              padding: "9px 14px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#cbd5e1",
              fontSize: "12px",
              cursor: "pointer",
            }}
            title="Refrescar estado"
          >
            🔄
          </button>
        </div>
      </div>

      {actionMsg && (
        <div style={{ background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56, 189, 248, 0.35)", borderRadius: "8px", padding: "10px 14px", color: "#38bdf8", fontSize: "12px", marginBottom: "16px" }}>
          {actionMsg}
        </div>
      )}

      {/* 2. STATS SUMMARY BAR (CON GENERACIÓN Y DISTRIBUCIÓN POR TIERS) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", marginBottom: "20px" }}>
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>ESTADO DEL MOTOR</div>
          <div style={{ fontSize: "15px", fontWeight: 900, color: status.is_running ? "#34d399" : "#facc15", marginTop: "2px" }}>
            {status.is_running ? "🟢 ACTIVO 24/7" : "⏸ PAUSADO"}
          </div>
          <div style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800, marginTop: "2px" }}>
            Generación #{status.stats.generation_round || 1} (Ciclo {status.stats.total_cycles})
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>EN COLA TOTAL</div>
          <div style={{ fontSize: "18px", fontWeight: 900, color: "#38bdf8", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
            {status.queue_summary.total_in_queue || status.queue.length}
          </div>
          <div style={{ fontSize: "9px", color: "#94a3b8" }}>
            {status.queue_summary.pending_count} pendientes · {status.queue_summary.processed_count} procesadas
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>PROCESADAS HOY</div>
          <div style={{ fontSize: "18px", fontWeight: 900, color: "#ffffff", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
            {status.stats.total_processed}
          </div>
          <div style={{ fontSize: "9px", color: "#64748b" }}>Iteraciones físicas en disco</div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(16, 185, 129, 0.25)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>MEJORADAS (+GATES)</div>
          <div style={{ fontSize: "18px", fontWeight: 900, color: "#34d399", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
            {status.stats.total_improved}
          </div>
          <div style={{ fontSize: "9px", color: "#34d399" }}>Scorecard persistido en SQLite</div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(236, 72, 153, 0.25)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#ec4899", fontFamily: "var(--font-mono, monospace)" }}>CERTIFICADAS (11/11)</div>
          <div style={{ fontSize: "18px", fontWeight: 900, color: "#ec4899", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
            {status.stats.total_certified}
          </div>
          <div style={{ fontSize: "9px", color: "#ec4899" }}>Tier 1 Aprobadas Oficiales</div>
        </div>
      </div>

      {/* 3. LIVE VISOR HUD: CANDIDATO EN EJECUCIÓN ACTIVA */}
      <div style={{ background: "rgba(16, 23, 34, 0.95)", border: "1px solid rgba(250, 204, 21, 0.35)", borderRadius: "14px", padding: "18px 20px", marginBottom: "20px", boxShadow: "0 4px 25px rgba(0,0,0,0.4)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: status.current_processing ? "#34d399" : "#64748b", boxShadow: status.current_processing ? "0 0 12px #34d399" : "none", display: "inline-block" }} />
            <div>
              <div style={{ fontSize: "10.5px", fontWeight: 900, color: "#facc15", fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.5px" }}>
                📡 VISOR DE EJECUCIÓN EN VIVO DEL MOTOR DE REFINAMIENTO
              </div>
              <div style={{ fontSize: "15px", fontWeight: 900, color: "#ffffff", marginTop: "2px" }}>
                {status.current_processing ? (
                  <span>
                    Procesando: <strong style={{ color: "#38bdf8" }}>{status.current_processing.candidate_id}</strong> ({status.current_processing.symbol} {status.current_processing.timeframe}) · {status.current_processing.step}
                  </span>
                ) : (
                  <span style={{ color: "#94a3b8" }}>
                    Motor en espera · Selecciona una estrategia o inicia el bucle 24/7 para procesar la cola
                  </span>
                )}
              </div>
            </div>
          </div>

          {status.current_processing && (
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <span style={{ fontSize: "11px", fontWeight: 800, padding: "3px 8px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.2)", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                Iteración {status.current_processing.iteration}/{status.current_processing.max_iterations}
              </span>
              <span style={{ fontSize: "11px", fontWeight: 800, padding: "3px 8px", borderRadius: "4px", background: "rgba(250, 204, 21, 0.2)", color: "#facc15", fontFamily: "var(--font-mono, monospace)" }}>
                {Math.round(status.current_processing.progress_pct)}%
              </span>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {status.current_processing && (
          <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden", marginBottom: "14px" }}>
            <div style={{ width: `${status.current_processing.progress_pct}%`, height: "100%", background: "linear-gradient(90deg, #38bdf8, #facc15, #34d399)", transition: "width 0.3s ease" }} />
          </div>
        )}

        {/* Real-Time Math Chips */}
        {status.current_processing?.math_telemetry && Object.keys(status.current_processing.math_telemetry).length > 0 && (
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "10px" }}>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              Hurst: <strong style={{ color: "#34d399" }}>{typeof status.current_processing.math_telemetry.hurst === "number" ? status.current_processing.math_telemetry.hurst.toFixed(3) : status.current_processing.math_telemetry.hurst_exponent}</strong> ({status.current_processing.math_telemetry.regime || status.current_processing.math_telemetry.dominant_regime})
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              Parkinson Vol: <strong style={{ color: "#38bdf8" }}>{typeof status.current_processing.math_telemetry.parkinson_vol === "number" ? status.current_processing.math_telemetry.parkinson_vol.toFixed(5) : status.current_processing.math_telemetry.parkinson_volatility}</strong>
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              Squeeze: <strong style={{ color: status.current_processing.math_telemetry.squeeze_active || status.current_processing.math_telemetry.is_squeeze_active ? "#facc15" : "#64748b" }}>{status.current_processing.math_telemetry.squeeze_active || status.current_processing.math_telemetry.is_squeeze_active ? "ACTIVO" : "INACTIVO"}</strong>
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              SL / TP Óptimo: <strong style={{ color: "#cbd5e1" }}>Adaptive ATR Dynamic</strong>
            </span>
          </div>
        )}
      </div>

      {/* 4. DUAL PANE: COLA DE ESTRATEGIAS VS FEED VISUAL DE LOGS (FORMATO FRONT PREMIUM) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.05fr 0.95fr", gap: "16px", marginBottom: "24px" }}>
        
        {/* LEFT: TABLA DE COLA DE REVISIÓN CON 4 TIERS */}
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "16px", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
            <div style={{ fontSize: "12px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
              📋 COLA DE REFINAMIENTO CONTINUO ({filteredQueue.length})
            </div>
            
            {/* Filter buttons for 4 Tiers */}
            <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
              <button
                onClick={() => setFilterTier("ALL")}
                style={{
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "10px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: filterTier === "ALL" ? "#38bdf8" : "rgba(255,255,255,0.05)",
                  color: filterTier === "ALL" ? "#000000" : "#94a3b8",
                }}
              >
                Todas ({status.queue.length})
              </button>
              <button
                onClick={() => setFilterTier("TIER_2")}
                style={{
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "10px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: filterTier === "TIER_2" ? "#38bdf8" : "rgba(255,255,255,0.05)",
                  color: filterTier === "TIER_2" ? "#000000" : "#38bdf8",
                }}
              >
                💎 T2 ({status.queue_summary.tier_2_count})
              </button>
              <button
                onClick={() => setFilterTier("TIER_3")}
                style={{
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "10px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: filterTier === "TIER_3" ? "#facc15" : "rgba(255,255,255,0.05)",
                  color: filterTier === "TIER_3" ? "#000000" : "#facc15",
                }}
              >
                🧪 T3 ({status.queue_summary.tier_3_count})
              </button>
              <button
                onClick={() => setFilterTier("TIER_4")}
                style={{
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "10px",
                  fontWeight: 800,
                  border: "none",
                  cursor: "pointer",
                  background: filterTier === "TIER_4" ? "#f87171" : "rgba(255,255,255,0.05)",
                  color: filterTier === "TIER_4" ? "#000000" : "#f87171",
                }}
              >
                ❌ T4 ({status.queue_summary.tier_4_count || 0})
              </button>
            </div>
          </div>

          <div style={{ overflowX: "auto", maxHeight: "460px", overflowY: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#64748b", textAlign: "left" }}>
                  <th style={{ padding: "6px 8px" }}>ESTRATEGIA</th>
                  <th style={{ padding: "6px 8px" }}>ACTIVO</th>
                  <th style={{ padding: "6px 8px" }}>TIER / GATES</th>
                  <th style={{ padding: "6px 8px" }}>PF OOS</th>
                  <th style={{ padding: "6px 8px" }}>ESTADO</th>
                  <th style={{ padding: "6px 8px", textAlign: "right" }}>ACCIÓN</th>
                </tr>
              </thead>
              <tbody>
                {filteredQueue.map((item) => {
                  const isSelected = selectedCandidateId === item.candidate_id;
                  const isProc = status.current_processing?.candidate_id === item.candidate_id;

                  const isT1 = item.current_gates === 11;
                  const isT2 = item.current_gates >= 9 && item.current_gates <= 10;
                  const isT3 = item.current_gates >= 5 && item.current_gates <= 8;

                  return (
                    <tr
                      key={item.candidate_id}
                      onClick={() => setSelectedCandidateId(item.candidate_id)}
                      style={{
                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                        background: isProc ? "rgba(56, 189, 248, 0.12)" : isSelected ? "rgba(255,255,255,0.05)" : "transparent",
                        cursor: "pointer",
                      }}
                    >
                      <td style={{ padding: "6px 8px", fontWeight: 800, color: "#fff" }}>
                        <div>{item.name}</div>
                        <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>{item.candidate_id}</div>
                      </td>
                      <td style={{ padding: "6px 8px", color: "#38bdf8" }}>
                        {item.symbol} <span style={{ color: "#64748b" }}>({item.timeframe})</span>
                      </td>
                      <td style={{ padding: "6px 8px" }}>
                        <span
                          style={{
                            fontSize: "9.5px",
                            fontWeight: 800,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: isT1 ? "rgba(245, 158, 11, 0.2)" : isT2 ? "rgba(56, 189, 248, 0.18)" : isT3 ? "rgba(250, 204, 21, 0.18)" : "rgba(248, 113, 113, 0.15)",
                            color: isT1 ? "#f59e0b" : isT2 ? "#38bdf8" : isT3 ? "#facc15" : "#f87171",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {item.current_gates}/11 GATES
                        </span>
                      </td>
                      <td style={{ padding: "6px 8px", fontFamily: "var(--font-mono, monospace)", color: item.profit_factor >= 1.2 ? "#34d399" : "#cbd5e1" }}>
                        {item.profit_factor ? item.profit_factor.toFixed(2) : "1.00"}
                      </td>
                      <td style={{ padding: "6px 8px" }}>
                        <span
                          style={{
                            fontSize: "8.5px",
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: isProc ? "rgba(56, 189, 248, 0.2)" : item.status === "CERTIFICADA" ? "rgba(16, 185, 129, 0.2)" : item.status === "MEJORADA" ? "rgba(52, 211, 153, 0.2)" : "rgba(255,255,255,0.06)",
                            color: isProc ? "#38bdf8" : item.status === "CERTIFICADA" ? "#10b981" : item.status === "MEJORADA" ? "#34d399" : "#94a3b8",
                            fontWeight: 800,
                          }}
                        >
                          {isProc ? "⚡ PROCESANDO" : item.status}
                        </span>
                      </td>
                      <td style={{ padding: "6px 8px", textAlign: "right" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRefineSpecific(item.candidate_id);
                          }}
                          disabled={actionLoading}
                          style={{
                            padding: "4px 8px",
                            borderRadius: "4px",
                            background: "rgba(250, 204, 21, 0.15)",
                            border: "1px solid rgba(250, 204, 21, 0.35)",
                            color: "#facc15",
                            fontSize: "10px",
                            fontWeight: 800,
                            cursor: "pointer",
                          }}
                        >
                          Refinar
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT: CONSOLA VISUAL DE LOGS (FORMATO FRONT PREMIUM · ZERO TERMINAL CRUDO) */}
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "16px", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", flexWrap: "wrap", gap: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "12px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                📡 FEED DE TELEMETRÍA & LOGS EN VIVO
              </span>
              <span style={{ fontSize: "9px", padding: "2px 6px", borderRadius: "4px", background: "rgba(16, 185, 129, 0.2)", color: "#34d399", fontWeight: 800 }}>
                ● STREAM 24/7
              </span>
            </div>

            <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
              <button
                onClick={() => setAutoScroll(!autoScroll)}
                style={{
                  fontSize: "9.5px",
                  fontWeight: 800,
                  padding: "3px 8px",
                  borderRadius: "4px",
                  border: "none",
                  cursor: "pointer",
                  background: autoScroll ? "rgba(56, 189, 248, 0.2)" : "rgba(255, 255, 255, 0.05)",
                  color: autoScroll ? "#38bdf8" : "#64748b",
                }}
              >
                {autoScroll ? "📌 Scroll Auto: ON" : "Scroll: Manual"}
              </button>
            </div>
          </div>

          {/* Log Category Filters */}
          <div style={{ display: "flex", gap: "4px", marginBottom: "10px", flexWrap: "wrap" }}>
            <button
              onClick={() => setLogFilter("ALL")}
              style={{
                fontSize: "9.5px",
                fontWeight: 700,
                padding: "3px 7px",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                background: logFilter === "ALL" ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.03)",
                color: logFilter === "ALL" ? "#fff" : "#94a3b8",
              }}
            >
              Todos ({status.live_logs.length})
            </button>
            <button
              onClick={() => setLogFilter("CERT")}
              style={{
                fontSize: "9.5px",
                fontWeight: 700,
                padding: "3px 7px",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                background: logFilter === "CERT" ? "rgba(245, 158, 11, 0.25)" : "rgba(255,255,255,0.03)",
                color: logFilter === "CERT" ? "#f59e0b" : "#94a3b8",
              }}
            >
              🏆 Certificaciones
            </button>
            <button
              onClick={() => setLogFilter("IMPROVED")}
              style={{
                fontSize: "9.5px",
                fontWeight: 700,
                padding: "3px 7px",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                background: logFilter === "IMPROVED" ? "rgba(16, 185, 129, 0.25)" : "rgba(255,255,255,0.03)",
                color: logFilter === "IMPROVED" ? "#34d399" : "#94a3b8",
              }}
            >
              🟢 Mejoras (+Gates)
            </button>
            <button
              onClick={() => setLogFilter("ITER")}
              style={{
                fontSize: "9.5px",
                fontWeight: 700,
                padding: "3px 7px",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                background: logFilter === "ITER" ? "rgba(56, 189, 248, 0.25)" : "rgba(255,255,255,0.03)",
                color: logFilter === "ITER" ? "#38bdf8" : "#94a3b8",
              }}
            >
              ⚡ Iteraciones
            </button>
            <button
              onClick={() => setLogFilter("MICRO")}
              style={{
                fontSize: "9.5px",
                fontWeight: 700,
                padding: "3px 7px",
                borderRadius: "4px",
                border: "none",
                cursor: "pointer",
                background: logFilter === "MICRO" ? "rgba(168, 85, 247, 0.25)" : "rgba(255,255,255,0.03)",
                color: logFilter === "MICRO" ? "#c084fc" : "#94a3b8",
              }}
            >
              🔬 Microestructura
            </button>
          </div>

          {/* VISUAL CARDS FEED */}
          <div
            ref={logsFeedRef}
            style={{
              background: "rgba(5, 8, 14, 0.9)",
              borderRadius: "10px",
              padding: "10px",
              height: "420px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            {filteredLogs && filteredLogs.length > 0 ? (
              filteredLogs.map((log, idx) => {
                const isCert = log.event_type === "CERTIFICACION" || log.level === "SUCCESS" && log.message.includes("CERTIFICACIÓN");
                const isImprove = log.event_type === "MEJORA_GATE" || log.event_type === "TIER_UPGRADE" || (log.gate_delta && log.gate_delta > 0);
                const isMicro = log.event_type === "MICROESTRUCTURA";
                const isWarn = log.level === "WARN" || log.level === "WARNING";
                const isErr = log.level === "ERROR";

                let cardBorder = "rgba(255, 255, 255, 0.06)";
                let cardBg = "rgba(16, 23, 34, 0.75)";
                let badgeLabel = log.event_type || log.level;
                let badgeBg = "rgba(255, 255, 255, 0.08)";
                let badgeColor = "#94a3b8";
                let badgeIcon = "ℹ️";

                if (isCert) {
                  cardBorder = "rgba(245, 158, 11, 0.45)";
                  cardBg = "rgba(245, 158, 11, 0.08)";
                  badgeLabel = "🏆 CERTIFICADA 11/11";
                  badgeBg = "rgba(245, 158, 11, 0.25)";
                  badgeColor = "#f59e0b";
                  badgeIcon = "🏆";
                } else if (isImprove) {
                  cardBorder = "rgba(16, 185, 129, 0.4)";
                  cardBg = "rgba(16, 185, 129, 0.07)";
                  badgeLabel = `🟢 MEJORA (+${log.gate_delta || 1} GATES)`;
                  badgeBg = "rgba(16, 185, 129, 0.25)";
                  badgeColor = "#34d399";
                  badgeIcon = "🟢";
                } else if (isMicro) {
                  cardBorder = "rgba(168, 85, 247, 0.35)";
                  cardBg = "rgba(168, 85, 247, 0.06)";
                  badgeLabel = "🔬 MICROESTRUCTURA";
                  badgeBg = "rgba(168, 85, 247, 0.2)";
                  badgeColor = "#c084fc";
                  badgeIcon = "🔬";
                } else if (isWarn) {
                  cardBorder = "rgba(250, 204, 21, 0.35)";
                  cardBg = "rgba(250, 204, 21, 0.06)";
                  badgeLabel = "⚠️ AVISO";
                  badgeBg = "rgba(250, 204, 21, 0.2)";
                  badgeColor = "#facc15";
                  badgeIcon = "⚠️";
                } else if (isErr) {
                  cardBorder = "rgba(248, 113, 113, 0.35)";
                  cardBg = "rgba(248, 113, 113, 0.08)";
                  badgeLabel = "❌ ERROR";
                  badgeBg = "rgba(248, 113, 113, 0.2)";
                  badgeColor = "#f87171";
                  badgeIcon = "❌";
                } else if (log.step.startsWith("ITERACION")) {
                  badgeLabel = `⚡ ${log.step}`;
                  badgeBg = "rgba(56, 189, 248, 0.18)";
                  badgeColor = "#38bdf8";
                  badgeIcon = "⚡";
                }

                return (
                  <div
                    key={idx}
                    style={{
                      background: cardBg,
                      border: `1px solid ${cardBorder}`,
                      borderRadius: "8px",
                      padding: "10px 12px",
                      transition: "transform 0.15s ease",
                    }}
                  >
                    {/* CARD HEADER */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px", flexWrap: "wrap", gap: "6px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span
                          style={{
                            fontSize: "9px",
                            fontWeight: 900,
                            padding: "2px 7px",
                            borderRadius: "4px",
                            background: badgeBg,
                            color: badgeColor,
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "4px",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {badgeIcon} {badgeLabel}
                        </span>

                        {log.candidate_id && (
                          <span
                            style={{
                              fontSize: "9.5px",
                              fontWeight: 800,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(56, 189, 248, 0.12)",
                              color: "#38bdf8",
                              border: "1px solid rgba(56, 189, 248, 0.2)",
                            }}
                          >
                            {log.symbol || log.candidate_id} {log.timeframe ? `· ${log.timeframe}` : ""} {log.route ? `(${log.route})` : ""}
                          </span>
                        )}
                      </div>

                      {/* DATE & TIME BADGE */}
                      <span
                        style={{
                          fontSize: "9.5px",
                          fontWeight: 700,
                          color: "#94a3b8",
                          background: "rgba(255, 255, 255, 0.05)",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          fontFamily: "var(--font-mono, monospace)",
                        }}
                      >
                        📅 {log.date_display || "22 Ago"} · {log.timestamp}
                      </span>
                    </div>

                    {/* MESSAGE TEXT */}
                    <div style={{ fontSize: "11px", color: "#f1f5f9", lineHeight: "1.45" }}>
                      {log.message}
                    </div>

                    {/* QUANTITATIVE METRICS PILLS */}
                    {(log.current_gates !== undefined && log.current_gates !== null || log.profit_factor !== undefined && log.profit_factor !== null || log.math) && (
                      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginTop: "6px", paddingTop: "6px", borderTop: "1px solid rgba(255, 255, 255, 0.04)" }}>
                        {log.current_gates !== undefined && log.current_gates !== null && (
                          <span
                            style={{
                              fontSize: "9.5px",
                              fontWeight: 800,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: (log.gate_delta || 0) > 0 ? "rgba(16, 185, 129, 0.2)" : "rgba(255, 255, 255, 0.05)",
                              color: (log.gate_delta || 0) > 0 ? "#34d399" : "#cbd5e1",
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            Gates: {log.initial_gates !== undefined && log.initial_gates !== null ? `${log.initial_gates}/11 → ` : ""}{log.current_gates}/11 {(log.gate_delta || 0) > 0 ? `(+${log.gate_delta})` : ""}
                          </span>
                        )}
                        {log.profit_factor !== undefined && log.profit_factor !== null && log.profit_factor > 0 && (
                          <span
                            style={{
                              fontSize: "9.5px",
                              fontWeight: 800,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(56, 189, 248, 0.15)",
                              color: "#38bdf8",
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            PF OOS: {log.profit_factor.toFixed(2)}
                          </span>
                        )}
                        {log.math?.hurst && (
                          <span
                            style={{
                              fontSize: "9.5px",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(168, 85, 247, 0.15)",
                              color: "#c084fc",
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            Hurst: {log.math.hurst.toFixed(3)} ({log.math.regime || "Normal"})
                          </span>
                        )}
                        {log.math?.parkinson_vol && (
                          <span
                            style={{
                              fontSize: "9.5px",
                              fontWeight: 700,
                              padding: "2px 6px",
                              borderRadius: "4px",
                              background: "rgba(255, 255, 255, 0.04)",
                              color: "#94a3b8",
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            Vol: {log.math.parkinson_vol.toFixed(5)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div style={{ color: "#64748b", textAlign: "center", marginTop: "160px", fontSize: "12px" }}>
                El bucle 24/7 está evaluando candidatos. Los eventos visuales aparecerán aquí en vivo...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 5. HISTORIAL RECIENTE DE MEJORAS & CANDIDATO EN DETALLE */}
      {status.recent_history && status.recent_history.length > 0 && (
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "16px", marginBottom: "24px" }}>
          <div style={{ fontSize: "12px", fontWeight: 900, color: "#ffffff", marginBottom: "10px", fontFamily: "var(--font-mono, monospace)" }}>
            🏆 HISTORIAL FORENSE DE REFINAMIENTOS COMPLETADOS
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "10px" }}>
            {status.recent_history.map((rec, i) => (
              <div key={i} style={{ background: "rgba(0,0,0,0.35)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: "11.5px", fontWeight: 800, color: "#fff" }}>{rec.name}</span>
                  <span style={{ fontSize: "9px", color: "#64748b" }}>{rec.timestamp}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "6px" }}>
                  <span style={{ fontSize: "10.5px", color: "#38bdf8" }}>{rec.symbol} {rec.timeframe} ({rec.route})</span>
                  <span style={{ fontSize: "10.5px", fontWeight: 900, color: rec.gate_delta > 0 ? "#34d399" : "#cbd5e1" }}>
                    {rec.initial_gates}/11 → {rec.final_gates}/11 Gates ({rec.gate_delta >= 0 ? `+${rec.gate_delta}` : rec.gate_delta})
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
