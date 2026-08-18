"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

const WORKER_NAMES: Record<WorkerId, string> = {
  DataWorker: "Ingesta de Datos & Detección de Gaps",
  SQXWorker: "StrategyQuant X MCP Bridge (:8081)",
  FastBacktestWorker: "FastEngine Determinista (1R Margen)",
  ValidationWorker: "Quant Validation Fabric & Evidence Gate",
  MonteCarloWorker: "Monte Carlo 5D & Permutaciones (10k)",
  SemanticAIWorker: "Semantic AI Loop & Failure Knowledge DB",
  PortfolioWorker: "Portfolio Multi-Activo & Bóveda Ratchet",
  PaperTradingWorker: "Paper Trading Sandbox & Incubación (14d)",
};

const FORBIDDEN_GOVERNANCE_RULES = [
  "RELAX_EVIDENCE_GATE: Prohibido rebajar umbrales de validación automáticamente ante fallos.",
  "ALTER_BACKTEST_METRICS: Prohibido modificar retrospectivamente métricas de backtest o logs de trades.",
  "OVERWRITE_DATASET_SNAPSHOT: Prohibido sobreescribir snapshots inmutables verificados con hash SHA-256.",
  "BYPASS_14_DAY_INCUBATION: Prohibido promocionar a LIVE_ACTIVE antes de completar 14 días sin drift.",
];

export default function SistemaSupervisorPage() {
  const { workers, logs, systemMetrics, isPaused, togglePause, clearLogs, reconnect } = useTelemetryStream();
  const [filterQuery, setFilterQuery] = useState<string>("");

  const filteredLogs = logs.filter((l) => {
    if (!filterQuery) return true;
    return l.message.toLowerCase().includes(filterQuery.toLowerCase()) || l.eventType.toLowerCase().includes(filterQuery.toLowerCase());
  });

  return (
    <div style={{ padding: "24px", maxWidth: "1560px", margin: "0 auto" }}>
      {/* 1. TOP HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
              ← Volver al Quant Lab
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#34d399", textTransform: "uppercase", fontFamily: "var(--font-mono, monospace)" }}>
              SYSTEM SUPERVISOR · 8 ASYNC WORKERS POOL
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
            Centro de Supervisión, Resiliencia & Telemetría SSE
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "6px", maxWidth: "900px" }}>
            Pool de 8 workers de proceso desacoplado con política de Self-Healing estricta (prohibido relajar compuertas o alterar métricas).
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "8px 14px", textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>CANAL SSE STREAM</div>
            <div style={{ fontSize: "14px", fontWeight: 800, color: systemMetrics.sseConnected ? "#34d399" : "#fbbf24", fontFamily: "var(--font-mono, monospace)" }}>
              {systemMetrics.connectionState}
            </div>
          </div>
          <button
            onClick={reconnect}
            style={{ padding: "8px 14px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#ffffff", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}
          >
            Reconectar SSE
          </button>
        </div>
      </div>

      {/* 2. 8 WORKERS GRID */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px", marginBottom: "28px" }}>
        <h3 style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", margin: "0 0 14px 0" }}>
          ⚙️ Estado del Pool de 8 Workers Asíncronos
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
          {(Object.keys(workers) as WorkerId[]).map((wId) => {
            const w = workers[wId];
            const isHealthy = w.status === "ACTIVE" || w.status === "IDLE" || w.status === "BUSY";

            return (
              <div
                key={wId}
                style={{
                  background: "rgba(0, 0, 0, 0.35)",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "10px",
                  padding: "14px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <span style={{ fontSize: "12px", fontWeight: 800, color: "#fff" }}>
                    {WORKER_NAMES[wId]}
                  </span>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 800,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: isHealthy ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)",
                      color: isHealthy ? "#34d399" : "#f43f5e",
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    ● {w.status}
                  </span>
                </div>

                <div style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                  Tareas completadas: <strong style={{ color: "#38bdf8" }}>{w.tasksCompleted}</strong> · {w.opsPerSec} ops/s
                </div>
                <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                  Tarea: {w.currentTaskName}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. CONSOLA SSE & GOBERNANZA ZERO-TRUST */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "24px" }}>
        <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
              Consola de Eventos en Tiempo Real (AsyncEventBus SSE)
            </h3>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={togglePause}
                style={{ padding: "4px 10px", borderRadius: "6px", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#cbd5e1", fontSize: "11px", cursor: "pointer" }}
              >
                {isPaused ? "▶ Reanudar" : "⏸ Pausar"}
              </button>
              <button
                onClick={clearLogs}
                style={{ padding: "4px 10px", borderRadius: "6px", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", color: "#94a3b8", fontSize: "11px", cursor: "pointer" }}
              >
                Limpiar
              </button>
            </div>
          </div>

          <div style={{ background: "#080c14", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "14px", fontFamily: "var(--font-mono, monospace)", fontSize: "11px", maxHeight: "360px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "6px" }}>
            {filteredLogs.length === 0 ? (
              <div style={{ color: "#64748b", textAlign: "center", padding: "30px 0" }}>
                Escuchando eventos en el bus SSE...
              </div>
            ) : (
              filteredLogs.map((ev, i) => (
                <div key={`${ev.id}-${i}`} style={{ padding: "6px 8px", borderRadius: "4px", background: "rgba(255, 255, 255, 0.02)", display: "flex", justifyContent: "space-between" }}>
                  <div>
                    <span style={{ color: "#38bdf8", fontWeight: 800 }}>[{ev.eventType}]</span> <span style={{ color: "#e2e8f0" }}>{ev.message}</span>
                  </div>
                  <span style={{ color: "#64748b", fontSize: "10px" }}>{new Date(ev.timestampMs).toISOString().slice(11, 19)}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* GOBERNANZA */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#f43f5e", fontFamily: "var(--font-mono, monospace)", marginBottom: "4px" }}>
            GOBERNANZA QUANT ZERO-TRUST
          </div>
          <h3 style={{ fontSize: "14px", fontWeight: 900, color: "#fff", margin: "0 0 12px 0" }}>
            Candados y Acciones Prohibidas
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {FORBIDDEN_GOVERNANCE_RULES.map((rule, idx) => (
              <div key={idx} style={{ background: "rgba(244, 63, 94, 0.06)", border: "1px solid rgba(244, 63, 94, 0.15)", borderRadius: "8px", padding: "10px 12px", fontSize: "11px", color: "#fda4af" }}>
                <strong style={{ color: "#f43f5e" }}>🔒 CANDADO #{idx + 1}:</strong> {rule}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
