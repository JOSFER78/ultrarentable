/**
 * apps/web/layout/Header.tsx
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { useEngineVersion } from "@/hooks/useEngineVersion";
import { WorkerId } from "@/types/telemetry";

const ROUTE_NAMES: Record<string, string> = {
  "/": "Centro Operativo",
  "/dashboard": "Dashboard",
  "/sistema": "1. Motor en Vivo",
  "/strategies": "2. Explorador Excel",
  "/candidatos": "3. Pipeline 11 Pasos",
  "/research": "4. Panel Investigador",
  "/gates": "5. Estrategias Aprobadas",
  "/portfolio": "6. Meta-Estrategia",
  "/fondeo": "Track Fondeo",
  "/ultra": "Track Ultra",
  "/nautilus": "Nautilus Core",
  "/campaigns": "Campañas de Minería",
};

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
  const currentPage = ROUTE_NAMES[pathname] ?? "Centro Operativo";
  const { workers, systemMetrics, reconnect } = useTelemetryStream();
  const { version, versionName, gitCommitShort } = useEngineVersion();
  const [timeDisplay, setTimeDisplay] = useState("");

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
      style={{
        padding: "0 24px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 16,
        minHeight: "56px",
        height: "auto",
        borderBottom: "1px solid var(--border)",
        background: "rgba(10, 15, 26, 0.95)",
        backdropFilter: "blur(12px)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
        flexWrap: "wrap",
      }}
    >
      {/* Left: Breadcrumb & Current Route */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
        <Link href="/" style={{ textDecoration: "none", color: "inherit", display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 14 }}>⚡</span>
          <span style={{ color: "var(--accent)", fontWeight: 800, fontFamily: "var(--font-mono)", letterSpacing: "0.5px" }}>
            ULTRARENTABLE
          </span>
        </Link>
        <span
          style={{
            fontSize: "9px",
            fontWeight: 800,
            padding: "1px 5px",
            borderRadius: "4px",
            background: "rgba(52, 211, 153, 0.15)",
            color: "#34d399",
            border: "1px solid rgba(52, 211, 153, 0.4)",
          }}
        >
          v{version}
        </span>
        <span style={{ color: "var(--border)" }}>/</span>
        <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>
          {currentPage}
        </span>
      </div>

      {/* Center: 8 Workers Mini-HUD */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, background: "rgba(0,0,0,0.3)", padding: "4px 10px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
        <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontWeight: 700 }}>
          WORKERS:
        </span>
        <div style={{ display: "flex", gap: 6 }}>
          {(Object.keys(workers) as WorkerId[]).map((wId) => {
            const w = workers[wId];
            const isOk = w.status === "ACTIVE" || w.status === "IDLE";
            return (
              <div
                key={wId}
                title={`${wId}: ${w.status} | Ops: ${w.opsPerSec}/s`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 3,
                  fontSize: 10,
                  fontFamily: "var(--font-mono)",
                  padding: "2px 5px",
                  borderRadius: "4px",
                  background: isOk ? "rgba(52, 211, 153, 0.1)" : "rgba(244, 63, 94, 0.15)",
                  color: isOk ? "#34d399" : "#f43f5e",
                  border: isOk ? "1px solid rgba(52, 211, 153, 0.2)" : "1px solid rgba(244, 63, 94, 0.3)",
                }}
              >
                <span style={{ width: 5, height: 5, borderRadius: "50%", background: isOk ? "#34d399" : "#f43f5e" }} />
                <span>{WORKER_SHORT[wId]}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: SSE Badge, Health & Dual Clock */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {/* SSE Streaming Badge */}
        <div
          onClick={reconnect}
          title="Streaming Server-Sent Events (SSE) :8000. Haz clic para reconectar."
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            padding: "4px 8px",
            borderRadius: "6px",
            background: systemMetrics.connectionState === "CONNECTED" ? "rgba(52, 211, 153, 0.1)" : "rgba(251, 191, 36, 0.1)",
            color: systemMetrics.connectionState === "CONNECTED" ? "#34d399" : "#fbbf24",
            border: `1px solid ${systemMetrics.connectionState === "CONNECTED" ? "rgba(52, 211, 153, 0.3)" : "rgba(251, 191, 36, 0.3)"}`,
            cursor: "pointer",
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: "50%", background: systemMetrics.connectionState === "CONNECTED" ? "#34d399" : "#fbbf24" }} />
          <span>SSE {systemMetrics.connectionState}</span>
        </div>

        {/* Dual Clock: Local + UTC */}
        <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontWeight: 600 }}>
          ⏱️ {timeDisplay || "LIVE"}
        </div>

        {/* Link Supervisor */}
        <Link
          href="/sistema"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            padding: "4px 8px",
            borderRadius: "6px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
            textDecoration: "none",
          }}
        >
          <span>Control ⚙️</span>
        </Link>
      </div>
    </header>
  );
}
