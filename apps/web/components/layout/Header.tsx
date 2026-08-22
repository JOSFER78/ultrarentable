/**
 * apps/web/components/layout/Header.tsx
 * Barra de estado superior compacta (Bloomberg / Trading Terminal Style)
 * 100% DATOS REALES DIRECTAMENTE DESDE FASTAPI & SQLITE WAL (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { useEngineVersion } from "@/hooks/useEngineVersion";
import { WorkerId } from "@/types/telemetry";

export default function Header() {
  const { workers, systemMetrics, reconnect } = useTelemetryStream();
  const { version, versionName, gitCommitShort, gitBranch, gitMessage, codeDrift } = useEngineVersion();
  const [timeDisplay, setTimeDisplay] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      const localStr = d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      const utcStr = d.toISOString().substring(11, 19) + " UTC";
      setTimeDisplay(`${localStr} (${utcStr})`);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header
      suppressHydrationWarning
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "0 16px",
        height: "44px",
        background: "rgba(10, 14, 22, 0.95)",
        backdropFilter: "blur(18px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* 1. LEFT: LIVE STATUS INDICATORS */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px", fontSize: "11px", fontFamily: "var(--font-mono, monospace)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: codeDrift ? "#fbbf24" : "#34d399",
              boxShadow: codeDrift ? "0 0 6px #fbbf24" : "0 0 6px #34d399",
            }}
          />
          <span style={{ color: "#ffffff", fontWeight: 700 }}>ULTRARENTABLE</span>
          <span
            style={{
              fontSize: "9px",
              fontWeight: 800,
              padding: "1px 5px",
              borderRadius: "4px",
              background: "rgba(52, 211, 153, 0.15)",
              color: "#34d399",
              border: "1px solid rgba(52, 211, 153, 0.4)",
              cursor: "pointer",
            }}
            title={versionName || `Motor Cuantitativo v${version} (Zero-Simulation Forensic)`}
          >
            v{version}
          </span>
          <span
            style={{
              fontSize: "9px",
              fontWeight: 700,
              padding: "1px 5px",
              borderRadius: "4px",
              background: "rgba(56, 189, 248, 0.12)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              cursor: "pointer",
            }}
            title={`Git Commit: ${gitCommitShort} (${gitBranch}) — ${gitMessage || "Control de versiones activo"}`}
          >
            git:{gitCommitShort || "HEAD"}
          </span>
        </div>

        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>

        <div>
          <span style={{ color: "#64748b" }}>EJECUCIÓN: </span>
          <strong style={{ color: Object.values(workers).some(w => w.status === "ACTIVE") ? "#34d399" : (systemMetrics.sseConnected ? "#94a3b8" : "#f43f5e") }}>
            {Object.keys(workers).length > 0
              ? `${Object.values(workers).filter(w => w.status === "ACTIVE").length}/${Object.keys(workers).length} Workers Activos`
              : (systemMetrics.sseConnected ? "0 Workers (Standby)" : "CONTROL PLANE OFFLINE")}
          </strong>
        </div>

        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>

        <div>
          <span style={{ color: "#64748b" }}>SQX BRIDGE: </span>
          <strong style={{ color: systemMetrics.sqxBridgeConnected ? "#34d399" : "#64748b" }}>
            {systemMetrics.sqxBridgeConnected ? "CONECTADO" : "STANDBY (8081)"}
          </strong>
        </div>

        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>

        <div>
          <span style={{ color: "#64748b" }}>TELEMETRÍA 24/7: </span>
          <strong style={{ color: systemMetrics.sseConnected ? "#34d399" : "#f43f5e" }}>
            {systemMetrics.sseConnected ? "ACTIVO" : "RECONECTANDO"}
          </strong>
        </div>
      </div>

      {/* 2. RIGHT: SSE BADGE & DUAL TIME CLOCK */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {/* SSE STATUS CHIP */}
        <div
          onClick={reconnect}
          title="Streaming Server-Sent Events (SSE) :8000. Haz clic para forzar reconexión."
          style={{
            display: "flex",
            alignItems: "center",
            gap: "5px",
            fontSize: "10px",
            fontFamily: "var(--font-mono, monospace)",
            padding: "2px 8px",
            borderRadius: "4px",
            background: systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.1)" : "rgba(251, 191, 36, 0.1)",
            color: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
            border: `1px solid ${systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
            cursor: "pointer",
          }}
        >
          <span
            style={{
              width: "5px",
              height: "5px",
              borderRadius: "50%",
              backgroundColor: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
              boxShadow: `0 0 5px ${systemMetrics.sseConnected ? "#34d399" : "#fbbf24"}`,
            }}
          />
          <span>SSE {systemMetrics.connectionState}</span>
        </div>

        {/* DUAL CLOCK: LOCAL + UTC */}
        <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", fontWeight: 700 }}>
          ⏱️ {timeDisplay || "LIVE"}
        </span>
      </div>
    </header>
  );
}
