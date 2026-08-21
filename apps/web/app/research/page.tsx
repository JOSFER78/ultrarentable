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
  iso_time: string;
  level: string;
  message: string;
  step: string;
  candidate_id: string | null;
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
    started_at: string;
  };
  queue_summary: {
    total_in_queue: number;
    pending_count: number;
    processed_count: number;
    tier_2_count: number;
    tier_3_count: number;
  };
  queue: CandidateQueueItem[];
  recent_history: RefinementHistoryItem[];
  live_logs: LiveLogEntry[];
}

export default function ResearchLabPage() {
  const [status, setStatus] = useState<ResearchDaemonStatus>({
    is_running: false,
    current_processing: null,
    stats: { total_processed: 0, total_improved: 0, total_certified: 0, total_cycles: 0, started_at: "" },
    queue_summary: { total_in_queue: 0, pending_count: 0, processed_count: 0, tier_2_count: 0, tier_3_count: 0 },
    queue: [],
    recent_history: [],
    live_logs: [],
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"VISOR" | "DEBATE" | "ARSENAL" | "FAILURES">("VISOR");
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [candidateDetail, setCandidateDetail] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [filterTier, setFilterTier] = useState<"ALL" | "TIER_2" | "TIER_3">("ALL");

  const terminalRef = useRef<HTMLDivElement>(null);

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
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Auto-scroll terminal on new logs
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [status.live_logs]);

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

  const handleStartDaemon = async () => {
    try {
      setActionLoading(true);
      const res = await fetch("/api/v1/research/start", { method: "POST" });
      if (res.ok) {
        setActionMsg("✓ Bucle Autónomo 24/7 activado. Procesando candidatos en segundo plano.");
        await fetchStatus();
      }
    } catch {
      setActionMsg("Error al iniciar el bucle autónomo.");
    } finally {
      setActionLoading(false);
      setTimeout(() => setActionMsg(null), 4000);
    }
  };

  const handlePauseDaemon = async () => {
    try {
      setActionLoading(true);
      const res = await fetch("/api/v1/research/pause", { method: "POST" });
      if (res.ok) {
        setActionMsg("⏸ Bucle Autónomo pausado.");
        await fetchStatus();
      }
    } catch {
      setActionMsg("Error al pausar.");
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
    if (filterTier === "TIER_2") return q.tier === "TIER_2_NEAR_CERTIFIED" || (q.current_gates >= 9 && q.current_gates <= 10);
    if (filterTier === "TIER_3") return q.tier === "TIER_3_INCUBATOR" || (q.current_gates >= 7 && q.current_gates <= 8);
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
          <p style={{ color: "#94a3b8", fontSize: "12.5px", marginTop: "4px", margin: 0, maxWidth: "1000px" }}>
            Visor en tiempo real del motor de optimización que toma secuencialmente las estrategias en revisión (Tier 2 y Tier 3), ejecuta backtests sobre velas físicas, calcula el perfil Hurst/Parkinson y aplica el debate de 5 agentes IA de forma natural.
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          {status.is_running ? (
            <button
              onClick={handlePauseDaemon}
              disabled={actionLoading}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                background: "rgba(239, 68, 68, 0.18)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
                color: "#f87171",
                fontSize: "12px",
                fontWeight: 800,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              ⏸ Pausar Bucle 24/7
            </button>
          ) : (
            <button
              onClick={handleStartDaemon}
              disabled={actionLoading}
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                background: "rgba(16, 185, 129, 0.2)",
                border: "1px solid rgba(16, 185, 129, 0.5)",
                color: "#34d399",
                fontSize: "12px",
                fontWeight: 800,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              ▶ Iniciar Auto-Refinamiento 24/7
            </button>
          )}

          <button
            onClick={handleProcessNext}
            disabled={actionLoading}
            style={{
              padding: "8px 14px",
              borderRadius: "8px",
              background: "rgba(250, 204, 21, 0.15)",
              border: "1px solid rgba(250, 204, 21, 0.4)",
              color: "#facc15",
              fontSize: "11.5px",
              fontWeight: 800,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            ⚡ Procesar Siguiente Candidato
          </button>

          <button
            onClick={fetchStatus}
            style={{
              padding: "8px 12px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#cbd5e1",
              fontSize: "11.5px",
              cursor: "pointer",
            }}
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

      {/* 2. STATS SUMMARY BAR */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px", marginBottom: "20px" }}>
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>ESTADO DEL DEMONIO</div>
          <div style={{ fontSize: "15px", fontWeight: 900, color: status.is_running ? "#34d399" : "#facc15", marginTop: "2px" }}>
            {status.is_running ? "🟢 ACTIVO 24/7" : "⏸ MANUAL / PAUSADO"}
          </div>
          <div style={{ fontSize: "9px", color: "#64748b" }}>Ciclos completados: {status.stats.total_cycles}</div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>EN COLA DE REVISIÓN</div>
          <div style={{ fontSize: "18px", fontWeight: 900, color: "#38bdf8", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
            {status.queue_summary.total_in_queue}
          </div>
          <div style={{ fontSize: "9px", color: "#38bdf8" }}>
            {status.queue_summary.tier_2_count} Diamantes (T2) · {status.queue_summary.tier_3_count} Incubadora (T3)
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
          <div style={{ fontSize: "9px", color: "#34d399" }}>Scorecard actualizado en SQLite</div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(236, 72, 153, 0.25)", borderRadius: "10px", padding: "12px 14px" }}>
          <div style={{ fontSize: "9.5px", color: "#ec4899", fontFamily: "var(--font-mono, monospace)" }}>CERTIFICADAS (11/11)</div>
          <div style={{ fontSize: "18px", fontWeight: 900, color: "#ec4899", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
            {status.stats.total_certified}
          </div>
          <div style={{ fontSize: "9px", color: "#ec4899" }}>Aprobadas sin relajación</div>
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
              Hurst: <strong style={{ color: "#34d399" }}>{status.current_processing.math_telemetry.hurst_exponent}</strong> ({status.current_processing.math_telemetry.dominant_regime})
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              Parkinson Vol: <strong style={{ color: "#38bdf8" }}>{status.current_processing.math_telemetry.parkinson_volatility}</strong>
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              Squeeze: <strong style={{ color: status.current_processing.math_telemetry.is_squeeze_active ? "#facc15" : "#64748b" }}>{status.current_processing.math_telemetry.is_squeeze_active ? "ACTIVO" : "INACTIVO"}</strong>
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              SL Óptimo: <strong style={{ color: "#cbd5e1" }}>{status.current_processing.math_telemetry.optimal_sl_atr_mult}x ATR</strong>
            </span>
            <span style={{ fontSize: "10.5px", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", padding: "4px 8px", borderRadius: "6px" }}>
              TP Óptimo: <strong style={{ color: "#cbd5e1" }}>{status.current_processing.math_telemetry.optimal_tp_atr_mult}x ATR</strong>
            </span>
          </div>
        )}
      </div>

      {/* 4. DUAL PANE: COLA DE ESTRATEGIAS VS TERMINAL EN VIVO */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "16px", marginBottom: "24px" }}>
        
        {/* LEFT: TABLA DE COLA DE REVISIÓN */}
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "16px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
            <div style={{ fontSize: "12px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
              📋 COLA DE ESTRATEGIAS EN REVISIÓN ({filteredQueue.length})
            </div>
            
            {/* Filter buttons */}
            <div style={{ display: "flex", gap: "4px" }}>
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
                T2 Diamantes ({status.queue_summary.tier_2_count})
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
                T3 Incubadora ({status.queue_summary.tier_3_count})
              </button>
            </div>
          </div>

          <div style={{ overflowX: "auto", maxHeight: "380px", overflowY: "auto" }}>
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
                            background: item.current_gates >= 9 ? "rgba(56, 189, 248, 0.18)" : "rgba(250, 204, 21, 0.18)",
                            color: item.current_gates >= 9 ? "#38bdf8" : "#facc15",
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
                            padding: "1px 5px",
                            borderRadius: "3px",
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

        {/* RIGHT: CONSOLA DE LOGS FÍSICOS EN VIVO */}
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "16px", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <div style={{ fontSize: "12px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
              📡 CONSOLA DE EVENTOS FÍSICOS (LOGS EN VIVO)
            </div>
            <span style={{ fontSize: "9.5px", color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
              ● STREAM ACTIVO
            </span>
          </div>

          <div
            ref={terminalRef}
            style={{
              background: "#05080e",
              borderRadius: "8px",
              padding: "12px",
              height: "380px",
              overflowY: "auto",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: "10.5px",
              lineHeight: "1.5",
              color: "#cbd5e1",
            }}
          >
            {status.live_logs && status.live_logs.length > 0 ? (
              status.live_logs.map((log, idx) => (
                <div key={idx} style={{ marginBottom: "6px", borderBottom: "1px solid rgba(255,255,255,0.03)", paddingBottom: "3px" }}>
                  <span style={{ color: "#64748b", marginRight: "6px" }}>[{log.timestamp}]</span>
                  <span
                    style={{
                      color: log.level === "SUCCESS" ? "#34d399" : log.level === "ERROR" ? "#f87171" : log.level === "WARN" ? "#facc15" : "#38bdf8",
                      fontWeight: 800,
                      marginRight: "6px",
                    }}
                  >
                    [{log.level}]
                  </span>
                  {log.step && <span style={{ color: "#818cf8", marginRight: "6px" }}>[{log.step}]</span>}
                  <span>{log.message}</span>
                </div>
              ))
            ) : (
              <div style={{ color: "#64748b", textAlign: "center", marginTop: "160px" }}>
                Inicia el bucle de refinamiento o procesa un candidato para ver los eventos en vivo...
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
