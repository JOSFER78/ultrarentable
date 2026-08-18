"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

const WORKER_NAMES: Record<WorkerId, string> = {
  DataWorker: "1. Data Pipeline Worker",
  SQXWorker: "2. StrategyQuant X Bridge",
  FastBacktestWorker: "3. Fast Backtester Engine",
  ValidationWorker: "4. Quant Validation Fabric",
  MonteCarloWorker: "5. Monte Carlo & Robustness",
  SemanticAIWorker: "6. Semantic Quant Engine",
  PortfolioWorker: "7. Portfolio Multi-Asset",
  PaperTradingWorker: "8. Paper Sandbox 14-Day",
};

const FORBIDDEN_GOVERNANCE_RULES = [
  "Bypass manual o forzado de compuertas QVF (Evidence Gate)",
  "Relajación arbitraria de umbrales cuantitativos (DSR < 2.0 / DD > 4.5%)",
  "Apertura de posiciones reales sin completar 14 días de incubación en Paper Sandbox",
  "Uso de datos futuros o manipulación de particiones IS/OOS",
];

export default function SistemaSupervisionPage() {
  const { workers, logs, systemMetrics, isPaused, togglePause, clearLogs, reconnect } = useTelemetryStream();
  const [filterQuery, setFilterQuery] = useState<string>("");

  const filteredLogs = logs.filter((ev) => {
    if (!filterQuery) return true;
    return (
      ev.eventType.toLowerCase().includes(filterQuery.toLowerCase()) ||
      ev.id.toLowerCase().includes(filterQuery.toLowerCase()) ||
      ev.message.toLowerCase().includes(filterQuery.toLowerCase())
    );
  });

  const isConnected = systemMetrics.connectionState === "CONNECTED";

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            TELEMETRY & SUPERVISION · 8 WORKERS POOL
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          Centro de Supervisión, Resiliencia & Telemetría SSE
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Monitorización distribuida de los 8 workers asíncronos, consola de eventos SSE y gobernanza inmutable.
        </p>
      </div>

      {/* 2. POOL DE 8 WORKERS MONITOR */}
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
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            POOL DISTRIBUIDO DE 8 WORKERS ASÍNCRONOS (HEALTH SCORE: {systemMetrics.systemHealthScore}%)
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: isConnected ? "#34d399" : "#f43f5e" }} />
            <span style={{ fontSize: "11px", fontWeight: 800, color: isConnected ? "#34d399" : "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
              {systemMetrics.connectionState}
            </span>
            <button
              onClick={reconnect}
              style={{
                padding: "3px 8px",
                borderRadius: "4px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "#cbd5e1",
                fontSize: "10px",
                cursor: "pointer",
              }}
            >
              Reconectar
            </button>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "12px" }}>
          {Object.entries(workers).map(([wId, info]) => {
            const friendlyName = WORKER_NAMES[wId as WorkerId] || wId;
            const isHealthy = info.status === "RUNNING" || info.status === "BUSY";

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
                    {friendlyName}
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
                    ● {info.status}
                  </span>
                </div>

                <div style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                  Tareas completadas: <strong style={{ color: "#38bdf8" }}>{info.tasksCompleted}</strong> · {info.opsPerSec} ops/s
                </div>
                <div style={{ fontSize: "10px", color: "#64748b", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                  Tarea: {info.currentTaskName}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. CONSOLA CANÓNICA DE EVENTOS SSE */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "24px" }}>
        {/* LEFT: CONSOLA DE STREAMING */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
              Consola de Eventos en Tiempo Real (AsyncEventBus SSE)
            </h3>

            <div style={{ display: "flex", gap: "8px" }}>
              <input
                type="text"
                placeholder="Filtrar eventos..."
                value={filterQuery}
                onChange={(e) => setFilterQuery(e.target.value)}
                style={{
                  background: "rgba(0, 0, 0, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "6px",
                  padding: "4px 8px",
                  color: "#fff",
                  fontSize: "11px",
                  fontFamily: "var(--font-mono, monospace)",
                  outline: "none",
                }}
              />
              <button
                onClick={togglePause}
                style={{
                  padding: "4px 10px",
                  borderRadius: "6px",
                  background: isPaused ? "rgba(245, 158, 11, 0.2)" : "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  color: isPaused ? "#f59e0b" : "#cbd5e1",
                  fontSize: "11px",
                  cursor: "pointer",
                }}
              >
                {isPaused ? "▶ Reanudar" : "⏸ Pausar"}
              </button>
              <button
                onClick={clearLogs}
                style={{
                  padding: "4px 10px",
                  borderRadius: "6px",
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  color: "#94a3b8",
                  fontSize: "11px",
                  cursor: "pointer",
                }}
              >
                Limpiar
              </button>
            </div>
          </div>

          <div
            style={{
              flex: 1,
              background: "#080c14",
              border: "1px solid rgba(255, 255, 255, 0.06)",
              borderRadius: "8px",
              padding: "14px",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: "11px",
              maxHeight: "380px",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
            }}
          >
            {filteredLogs.length === 0 ? (
              <div style={{ color: "#64748b", textAlign: "center", padding: "40px 0" }}>
                Escuchando eventos en el bus SSE...
              </div>
            ) : (
              filteredLogs.map((ev, i) => (
                <div
                  key={`${ev.id}-${i}`}
                  style={{
                    padding: "8px 10px",
                    borderRadius: "6px",
                    background: "rgba(255, 255, 255, 0.02)",
                    border: "1px solid rgba(255, 255, 255, 0.04)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b", fontSize: "10px" }}>
                    <span style={{ color: "#38bdf8", fontWeight: 800 }}>{ev.eventType}</span>
                    <span>{new Date(ev.timestampMs).toISOString().slice(11, 23)}</span>
                  </div>
                  <div style={{ color: "#cbd5e1", marginTop: "2px", fontSize: "11px" }}>
                    ID: {ev.id} · {ev.message}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* RIGHT: GOBERNANZA & PROTOCOLO ZERO-TRUST */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#f43f5e", fontFamily: "var(--font-mono, monospace)", marginBottom: "4px" }}>
            GOBERNANZA QUANT ZERO-TRUST
          </div>
          <h3 style={{ fontSize: "14px", fontWeight: 900, color: "#fff", margin: "0 0 12px 0" }}>
            Candados y Acciones Prohibidas
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px", flex: 1 }}>
            {FORBIDDEN_GOVERNANCE_RULES.map((rule, idx) => (
              <div
                key={idx}
                style={{
                  background: "rgba(244, 63, 94, 0.06)",
                  border: "1px solid rgba(244, 63, 94, 0.15)",
                  borderRadius: "8px",
                  padding: "10px 12px",
                  fontSize: "11px",
                  color: "#fda4af",
                }}
              >
                <strong style={{ color: "#f43f5e" }}>🔒 CANDADO #{idx + 1}:</strong> {rule}
              </div>
            ))}
          </div>

          <div style={{ marginTop: "14px", background: "rgba(0, 0, 0, 0.3)", borderRadius: "8px", padding: "10px", fontSize: "10px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
            Self-Healing Monitor: <strong style={{ color: "#34d399" }}>0 fallos no recuperados</strong>
          </div>
        </div>
      </div>
    </div>
  );
}
