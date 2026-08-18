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

export default function SistemaSupervisorPage() {
  const { workers, logs, systemMetrics, isPaused, togglePause, clearLogs, reconnect } = useTelemetryStream();
  const [selectedWorker, setSelectedWorker] = useState<WorkerId | "ALL">("ALL");

  return (
    <div style={{ padding: "24px", maxWidth: "1440px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Command Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#34d399", textTransform: "uppercase", fontFamily: "var(--font-mono)" }}>
              SYSTEM SUPERVISOR · 8 ASYNC WORKERS POOL
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "var(--text-primary)", margin: 0 }}>
            Centro de Supervisión, Resiliencia & Telemetría SSE
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "13px", marginTop: "6px" }}>
            Pool de 8 workers de proceso desacoplado con política de Self-Healing estricta (prohibido relajar compuertas o alterar métricas).
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "8px", padding: "8px 14px", textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>CANAL SSE STREAM</div>
            <div style={{ fontSize: "14px", fontWeight: 800, color: systemMetrics.sseConnected ? "#34d399" : "#fbbf24", fontFamily: "var(--font-mono)" }}>
              {systemMetrics.connectionState}
            </div>
          </div>
          <button
            onClick={reconnect}
            style={{ padding: "8px 14px", borderRadius: "8px", background: "var(--bg-2)", border: "1px solid var(--border)", color: "var(--text-primary)", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}
          >
            Reconectar SSE
          </button>
        </div>
      </div>

      {/* 8 WORKERS GRID */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "16px", marginBottom: "28px" }}>
        {(Object.keys(workers) as WorkerId[]).map((wId) => {
          const w = workers[wId];
          const isHealthy = w.status === "ACTIVE" || w.status === "IDLE";
          const isSelected = selectedWorker === wId;
          return (
            <div
              key={wId}
              onClick={() => setSelectedWorker(isSelected ? "ALL" : wId)}
              style={{
                background: isSelected ? "rgba(99, 225, 180, 0.1)" : "var(--bg-panel)",
                border: isSelected ? "1px solid var(--accent)" : "1px solid var(--border)",
                borderRadius: "12px",
                padding: "16px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <span style={{ fontWeight: 800, fontSize: "13px", color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>{wId}</span>
                <span
                  style={{
                    padding: "2px 6px",
                    borderRadius: "4px",
                    fontSize: "10px",
                    fontWeight: 700,
                    background: isHealthy ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)",
                    color: isHealthy ? "#34d399" : "#f43f5e",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {w.status}
                </span>
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "12px" }}>
                {WORKER_NAMES[wId]}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                <div>Tareas OK: <strong style={{ color: "var(--text-primary)" }}>{w.tasksCompleted}</strong></div>
                <div>Fallos: <strong style={{ color: w.tasksFailed > 0 ? "#f43f5e" : "var(--text-muted)" }}>{w.tasksFailed}</strong></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* CONSOLA DE TELEMETRÍA EN VIVO */}
      <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "12px", padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "15px", fontWeight: 800, color: "var(--text-primary)" }}>
              💻 Consola Canónica de Eventos de Dominio ({logs.length} eventos)
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
              Filtrando por: <strong>{selectedWorker}</strong>
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={togglePause}
              style={{ padding: "6px 12px", borderRadius: "6px", background: "var(--bg-2)", border: "1px solid var(--border)", color: "var(--text-primary)", fontSize: "11px", fontWeight: 700, cursor: "pointer" }}
            >
              {isPaused ? "▶ Reanudar" : "⏸ Pausar"}
            </button>
            <button
              onClick={clearLogs}
              style={{ padding: "6px 12px", borderRadius: "6px", background: "var(--bg-2)", border: "1px solid var(--border)", color: "var(--text-muted)", fontSize: "11px", fontWeight: 700, cursor: "pointer" }}
            >
              Limpiar Buffer
            </button>
          </div>
        </div>

        <div style={{ background: "var(--bg-0)", borderRadius: "8px", padding: "12px", maxHeight: "360px", overflowY: "auto", fontFamily: "var(--font-mono)", fontSize: "11px" }}>
          {logs.length === 0 ? (
            <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "30px" }}>
              Esperando eventos del bus asíncrono desde /api/v2/telemetry/stream...
            </div>
          ) : (
            logs.map((l) => (
              <div key={l.id} style={{ padding: "4px 0", borderBottom: "1px solid rgba(255,255,255,0.03)", display: "flex", gap: "10px", alignItems: "baseline" }}>
                <span style={{ color: "var(--text-muted)" }}>{new Date(l.timestampMs).toISOString().substring(11, 19)}</span>
                <span style={{ color: "var(--accent)", fontWeight: 700 }}>[{l.eventType}]</span>
                <span style={{ color: "var(--text-primary)", flex: 1 }}>{l.message}</span>
                <span style={{ color: "var(--text-muted)", fontSize: "10px" }}>{l.provenanceHash.substring(0, 8)}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
