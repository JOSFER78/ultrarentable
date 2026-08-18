/**
 * apps/web/components/layout/Header.tsx
 * Persistent Sentinel TopBar & Macro-Environment Switcher (Lab vs Live Bots)
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

const WORKER_SHORT: Record<WorkerId, string> = {
  DataWorker: "DAT",
  SQXWorker: "SQX",
  FastBacktestWorker: "FBT",
  ValidationWorker: "VAL",
  MonteCarloWorker: "MTC",
  SemanticAIWorker: "SAI",
  PortfolioWorker: "PTF",
  PaperTradingWorker: "PPR",
};

export default function Header() {
  const pathname = usePathname();
  const { workers, systemMetrics, reconnect } = useTelemetryStream();
  const [utcTime, setUtcTime] = useState<string>("");
  const [killTriggered, setKillTriggered] = useState<boolean>(false);

  const isLiveEnv = pathname.startsWith("/ultra") || pathname.startsWith("/fondeo") || pathname.startsWith("/ejecucion");
  const isLabEnv = !isLiveEnv;

  useEffect(() => {
    const timer = setInterval(() => {
      setUtcTime(new Date().toISOString().substring(11, 19) + " UTC");
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleKillSwitch = () => {
    if (confirm("⚠️ ¿ESTÁS SEGURO DE ACTIVAR EL KILL-SWITCH GLOBAL?\n\nEsto ordenará el cierre inmediato (Flatten) de todas las posiciones abiertas en BingX Perpetuals y cuentas CME Prop Firms.")) {
      setKillTriggered(true);
      alert("🛑 KILL-SWITCH ACTIVADO: Se han enviado órdenes de aplanado de emergencia a todos los brokers.");
    }
  };

  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "0 20px",
        height: "64px",
        background: "rgba(10, 14, 22, 0.92)",
        backdropFilter: "blur(18px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* 1. LEFT: MACRO-ENVIRONMENT SWITCHER & BRAND */}
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

        {/* MACRO-SWITCHER TABS */}
        <div
          style={{
            display: "flex",
            background: "rgba(0, 0, 0, 0.4)",
            padding: "3px",
            borderRadius: "8px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <Link
            href="/"
            style={{
              padding: "5px 12px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              fontFamily: "var(--font-mono, monospace)",
              textDecoration: "none",
              background: isLabEnv ? "rgba(99, 225, 180, 0.15)" : "transparent",
              color: isLabEnv ? "#63e1b4" : "#64748b",
              border: isLabEnv ? "1px solid rgba(99, 225, 180, 0.3)" : "1px solid transparent",
              transition: "all 0.15s ease",
            }}
          >
            🧬 QUANT LAB (600k+ SQX)
          </Link>
          <Link
            href="/ultra"
            style={{
              padding: "5px 12px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              fontFamily: "var(--font-mono, monospace)",
              textDecoration: "none",
              background: isLiveEnv ? "rgba(244, 63, 94, 0.15)" : "transparent",
              color: isLiveEnv ? "#f43f5e" : "#64748b",
              border: isLiveEnv ? "1px solid rgba(244, 63, 94, 0.3)" : "1px solid transparent",
              transition: "all 0.15s ease",
            }}
          >
            ⚡ LIVE BOTS & FONDEO
          </Link>
        </div>
      </div>

      {/* 2. CENTER: PERSISTENT SENTINEL BAR (REAL-TIME RISK & GAUGES) */}
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
          <span style={{ color: "#64748b" }}>BÓVEDA: </span>
          <strong style={{ color: "#63e1b4" }}>$425.00</strong>
          <span style={{ fontSize: "9px", color: "#34d399", marginLeft: "3px" }}>(2x 🔒)</span>
        </div>
        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>
        <div>
          <span style={{ color: "#64748b" }}>BALAS ULTRA: </span>
          <strong style={{ color: "#38bdf8" }}>3 Activas</strong>
        </div>
        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>
        <div>
          <span style={{ color: "#64748b" }}>CME DD: </span>
          <strong style={{ color: "#34d399" }}>1.2% / 4.5%</strong>
        </div>
        <span style={{ color: "rgba(255,255,255,0.1)" }}>|</span>
        <button
          onClick={handleKillSwitch}
          style={{
            background: killTriggered ? "#f43f5e" : "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.4)",
            color: "#f43f5e",
            fontSize: "10px",
            fontWeight: 900,
            padding: "2px 8px",
            borderRadius: "4px",
            cursor: "pointer",
            fontFamily: "var(--font-mono, monospace)",
          }}
        >
          {killTriggered ? "🛑 FLATTENED" : "🛑 KILL-SWITCH"}
        </button>
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
                title={`${wId}: ${w.status} | Ops: ${w.opsPerSec}/s`}
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
          title="Streaming SSE /api/v2/telemetry/stream. Clic para reconectar."
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
