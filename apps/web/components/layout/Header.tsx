"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

const ROUTE_INFO: Record<string, { title: string; subtitle: string; trackBadge?: string }> = {
  "/": { title: "Command Center Dual", subtitle: "Supervisión Cuantitativa & Registro Canónico de Estrategias", trackBadge: "DUAL TRACK" },
  "/ultra": { title: "Ruta ULTRA (BingX)", subtitle: "Margen Aislado 1R · Piramidación Free-Risk (40% HM) · Bóveda Ratchet", trackBadge: "TRACK_ULTRA" },
  "/fondeo": { title: "Ruta FONDEO (CME Prop Firms)", subtitle: "Preservación Institucional · DSR ≥ 2.0 · DLL 0 Violaciones", trackBadge: "TRACK_FONDEO" },
  "/candidatos": { title: "Candidatos FSM", subtitle: "Máquina de Estados de 10 Estados Discretos & Trazabilidad SHA-256", trackBadge: "10-STATE FSM" },
  "/bifurcacion": { title: "Bifurcación QVF", subtitle: "Quant Validation Fabric · Evidence Gate Desacoplado", trackBadge: "QVF FABRIC" },
  "/research": { title: "IA Semántica & Failure-DB", subtitle: "Memoria de Fallos · Mutación Genética Anti-Overfit · 5 Agentes", trackBadge: "SEMANTIC AI" },
  "/ejecucion": { title: "Paper Sandbox & Ejecución", subtitle: "Incubación 14 Días · Latencia 50ms · Detección de Drift ≤ 30%", trackBadge: "SANDBOX 14D" },
  "/sistema": { title: "Supervisión & Telemetría", subtitle: "SystemSupervisor · Pool de 8 Workers · Resiliencia SSE", trackBadge: "SUPERVISOR" },
};

const WORKER_SHORT_LABELS: Record<WorkerId, string> = {
  DataWorker: "Data",
  SQXWorker: "SQX",
  FastBacktestWorker: "FastBT",
  ValidationWorker: "QVF",
  MonteCarloWorker: "MC",
  SemanticAIWorker: "AI",
  PortfolioWorker: "Port",
  PaperTradingWorker: "Paper",
};

export default function Header() {
  const pathname = usePathname();
  const current = ROUTE_INFO[pathname] || { title: "Ultrarentable Lab", subtitle: "Plataforma Cuantitativa V2", trackBadge: "REAL-ONLY" };
  const { workers, systemMetrics, reconnect } = useTelemetryStream();

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "0 24px",
        height: "64px",
        background: "rgba(12, 16, 23, 0.85)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* Left: Section Header & Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 900,
                color: "#63e1b4",
                letterSpacing: "1.2px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              ULTRARENTABLE V2
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px" }}>/</span>
            <h1
              style={{
                margin: 0,
                fontSize: "15px",
                fontWeight: 800,
                color: "#ffffff",
                letterSpacing: "-0.2px",
              }}
            >
              {current.title}
            </h1>
            {current.trackBadge && (
              <span
                style={{
                  fontSize: "9px",
                  fontWeight: 800,
                  padding: "2px 6px",
                  borderRadius: "4px",
                  background: current.trackBadge.includes("ULTRA") ? "rgba(99, 225, 180, 0.15)" : current.trackBadge.includes("FONDEO") ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.08)",
                  color: current.trackBadge.includes("ULTRA") ? "#63e1b4" : current.trackBadge.includes("FONDEO") ? "#38bdf8" : "#94a3b8",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {current.trackBadge}
              </span>
            )}
          </div>
          <span style={{ fontSize: "11px", color: "#64748b", marginTop: "1px" }}>
            {current.subtitle}
          </span>
        </div>
      </div>

      {/* Right: Real-time 8 Workers HUD & Connection Status */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        {/* 8 Workers Status Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            background: "rgba(16, 23, 34, 0.7)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "10px",
            padding: "4px 10px",
          }}
        >
          <span
            style={{
              fontSize: "10px",
              fontWeight: 800,
              color: "#64748b",
              marginRight: "4px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            WORKERS:
          </span>

          {(Object.keys(workers) as WorkerId[]).map((wId) => {
            const w = workers[wId];
            const isOk = w.status === "RUNNING" || w.status === "ACTIVE" || w.status === "IDLE";
            const isError = w.status === "ERROR" || w.status === "FAILED";
            const dotColor = isOk ? "#34d399" : isError ? "#f43f5e" : "#fbbf24";
            const shortName = WORKER_SHORT_LABELS[wId] || wId;

            return (
              <div
                key={wId}
                title={`${wId}: ${w.status} | Tareas OK: ${w.tasksCompleted} | Fallos: ${w.tasksFailed}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "6px",
                  padding: "3px 6px",
                  fontSize: "10px",
                  fontFamily: "var(--font-mono, monospace)",
                  cursor: "pointer",
                }}
              >
                <span
                  style={{
                    width: "5px",
                    height: "5px",
                    borderRadius: "50%",
                    backgroundColor: dotColor,
                    boxShadow: `0 0 6px ${dotColor}`,
                  }}
                />
                <span style={{ color: "#e2e8f0", fontWeight: 700 }}>{shortName}</span>
                <span style={{ color: "#64748b", fontSize: "9px" }}>{w.tasksCompleted}</span>
              </div>
            );
          })}
        </div>

        {/* SSE Streaming Pill */}
        <div
          onClick={reconnect}
          title="Canal de Streaming SSE (/api/v2/telemetry/stream). Clic para reconectar."
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            background: systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.1)" : "rgba(251, 191, 36, 0.1)",
            border: `1px solid ${systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
            borderRadius: "8px",
            padding: "5px 10px",
            cursor: "pointer",
            fontSize: "10px",
            fontFamily: "var(--font-mono, monospace)",
            fontWeight: 800,
            color: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
              boxShadow: `0 0 8px ${systemMetrics.sseConnected ? "#34d399" : "#fbbf24"}`,
            }}
          />
          <span>SSE {systemMetrics.connectionState}</span>
        </div>

        {/* Link directo a Supervisión */}
        <Link
          href="/sistema"
          style={{
            background: "rgba(99, 225, 180, 0.1)",
            border: "1px solid rgba(99, 225, 180, 0.3)",
            color: "#63e1b4",
            fontSize: "11px",
            fontWeight: 800,
            padding: "5px 12px",
            borderRadius: "8px",
            textDecoration: "none",
            display: "flex",
            alignItems: "center",
            gap: "5px",
          }}
        >
          ⚡ Supervisor
        </Link>
      </div>
    </header>
  );
}
