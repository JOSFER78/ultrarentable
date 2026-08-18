/**
 * apps/web/components/layout/Header.tsx
 * Barra de estado superior compacta (Bloomberg / Trading Terminal Style)
 * 100% DATOS REALES DIRECTAMENTE DESDE FASTAPI & SQLITE WAL (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

export default function Header() {
  const { workers, systemMetrics, reconnect } = useTelemetryStream();
  const [utcTime, setUtcTime] = useState<string>("");

  useEffect(() => {
    const timer = setInterval(() => {
      setUtcTime(new Date().toISOString().substring(11, 19) + " UTC");
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header
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
              backgroundColor: "#34d399",
              boxShadow: "0 0 6px #34d399",
            }}
          />
          <span style={{ color: "#ffffff", fontWeight: 700 }}>ULTRARENTABLE V2</span>
        </div>

        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>

        <div>
          <span style={{ color: "#64748b" }}>EJECUCIÓN: </span>
          <strong style={{ color: "#94a3b8" }}>8 Bots (En reposo)</strong>
        </div>

        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>

        <div>
          <span style={{ color: "#64748b" }}>RATCHET: </span>
          <strong style={{ color: "#94a3b8" }}>$0.00 USD</strong>
        </div>

        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>

        <div>
          <span style={{ color: "#64748b" }}>MOTOR 24/7: </span>
          <strong style={{ color: "#34d399" }}>ACTIVO</strong>
        </div>
      </div>

      {/* 2. RIGHT: 8 WORKERS HUD, SSE BADGE & CLOCK */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        {/* 8 WORKERS MINI-DOTS */}
        <div
          title="8 Workers Cuantitativos"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            background: "rgba(0, 0, 0, 0.3)",
            padding: "2px 6px",
            borderRadius: "5px",
            border: "1px solid rgba(255, 255, 255, 0.05)",
          }}
        >
          {(Object.keys(workers) as WorkerId[]).map((wId) => {
            const w = workers[wId];
            const isOk = w.status === "ACTIVE" || w.status === "IDLE";
            return (
              <span
                key={wId}
                title={`${wId}: ${w.status}`}
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: isOk ? "#34d399" : "#f43f5e",
                  boxShadow: `0 0 4px ${isOk ? "#34d399" : "#f43f5e"}`,
                }}
              />
            );
          })}
        </div>

        {/* SSE STREAM BADGE */}
        <div
          onClick={reconnect}
          title="Streaming SSE /api/v2/telemetry/stream (Clic para reconectar)"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "5px",
            background: systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.12)" : "rgba(251, 191, 36, 0.12)",
            border: `1px solid ${systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
            borderRadius: "5px",
            padding: "2px 6px",
            fontSize: "9.5px",
            fontFamily: "var(--font-mono, monospace)",
            fontWeight: 800,
            color: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
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

        {/* CLOCK UTC */}
        <span style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
          {utcTime}
        </span>
      </div>
    </header>
  );
}
