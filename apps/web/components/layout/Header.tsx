/**
 * apps/web/components/layout/Header.tsx
 * Persistent TopBar con estado 100% honesto y real (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

export default function Header() {
  const pathname = usePathname();
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
        padding: "0 20px",
        height: "60px",
        background: "rgba(10, 14, 22, 0.95)",
        backdropFilter: "blur(18px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* 1. LEFT: LOGO & BRAND */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: "8px" }}>
          <div
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "6px",
              background: "linear-gradient(135deg, #63e1b4, #38bdf8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "12px",
              color: "#06080d",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            UR
          </div>
          <span style={{ fontWeight: 900, fontSize: "14px", color: "#ffffff", letterSpacing: "0.5px" }}>
            ULTRARENTABLE <span style={{ color: "#63e1b4", fontSize: "10px", fontWeight: 800 }}>V2</span>
          </span>
        </Link>
      </div>

      {/* 2. CENTER: ESTADO REAL Y HONESTO DEL SISTEMA */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "14px",
          background: "rgba(16, 23, 34, 0.75)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "8px",
          padding: "4px 14px",
          fontSize: "11px",
          fontFamily: "var(--font-mono, monospace)",
        }}
      >
        <div>
          <span style={{ color: "#64748b" }}>ESTADO DE EJECUCIÓN: </span>
          <strong style={{ color: "#94a3b8" }}>0 Bots Activos (En reposo)</strong>
        </div>
        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>
        <div>
          <span style={{ color: "#64748b" }}>BÓVEDA RATCHET: </span>
          <strong style={{ color: "#94a3b8" }}>$0.00 USD (Inactiva)</strong>
        </div>
        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>
        <div>
          <span style={{ color: "#64748b" }}>MOTOR: </span>
          <strong style={{ color: "#34d399" }}>AUTOMÁTICO ASISTIDO</strong>
        </div>
      </div>

      {/* 3. RIGHT: 8 WORKERS MINI-HUD & SSE STATUS */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        {/* 8 WORKERS HUD */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "4px",
            background: "rgba(0, 0, 0, 0.3)",
            padding: "3px 8px",
            borderRadius: "6px",
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
                  width: "7px",
                  height: "7px",
                  borderRadius: "50%",
                  backgroundColor: isOk ? "#34d399" : "#f43f5e",
                  boxShadow: `0 0 5px ${isOk ? "#34d399" : "#f43f5e"}`,
                }}
              />
            );
          })}
        </div>

        {/* SSE STREAM BADGE */}
        <div
          onClick={reconnect}
          title="Streaming SSE /api/v2/telemetry/stream."
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            background: systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.12)" : "rgba(251, 191, 36, 0.12)",
            border: `1px solid ${systemMetrics.sseConnected ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
            borderRadius: "6px",
            padding: "4px 8px",
            fontSize: "10px",
            fontFamily: "var(--font-mono, monospace)",
            fontWeight: 800,
            color: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
            cursor: "pointer",
          }}
        >
          <span
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              backgroundColor: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
              boxShadow: `0 0 6px ${systemMetrics.sseConnected ? "#34d399" : "#fbbf24"}`,
            }}
          />
          <span>SSE {systemMetrics.connectionState}</span>
        </div>

        {/* CLOCK UTC */}
        <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
          {utcTime}
        </span>
      </div>
    </header>
  );
}
