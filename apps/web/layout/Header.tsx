"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState, useEffect } from "react";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { WorkerId } from "@/types/telemetry";

const ROUTE_NAMES: Record<string, string> = {
  "/": "Command Center V2 · Mission Control",
  "/ultra": "Track ULTRA · BingX Perpetuals & Bóveda Ratchet",
  "/fondeo": "Track FONDEO · CME Prop Firms Challenge",
  "/candidatos": "Candidate Registry · FSM 10 Estados",
  "/bifurcacion": "Quant Validation Fabric (QVF) Dual",
  "/research": "Semantic AI Studio & FailureKnowledgeDB",
  "/ejecucion": "Paper Trading Sandbox · 14 Días",
  "/sistema": "System Supervisor & 8 Workers Pool",
  "/prop-firms": "Catálogo de 34 Firmas Prop CME",
  "/portfolio": "Portfolio Multi-Activo (HRP / ERC)",
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
  const [utcTime, setUtcTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setUtcTime(d.toISOString().substring(11, 19) + " UTC");
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
            ULTRARENTABLE V2
          </span>
        </Link>
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

      {/* Right: SSE Badge, Health & Clock */}
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

        {/* UTC Clock */}
        <div style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--text-muted)", fontWeight: 600 }}>
          {utcTime || "UTC LIVE"}
        </div>

        {/* Link Supervisor */}
        <Link
          href="/sistema"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 5,
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            fontWeight: 700,
            padding: "5px 10px",
            borderRadius: "6px",
            background: "rgba(56, 189, 248, 0.15)",
            color: "#38bdf8",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            textDecoration: "none",
          }}
        >
          <span>🚀</span>
          <span>SUPERVISOR</span>
        </Link>
      </div>
    </header>
  );
}
