"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";

const ROUTE_NAMES: Record<string, { title: string; subtitle: string }> = {
  "/": { title: "Command Center", subtitle: "Operaciones Cuantitativas & Resumen Real" },
  "/ultra": { title: "Ruta ULTRA", subtitle: "BingX Crypto Perps (Apalancamiento hasta 500x & Pyramiding)" },
  "/fondeo": { title: "Ruta FONDEO", subtitle: "Futuros CME (Exámenes & Cuentas Fondeadas Prop Firms)" },
  "/candidatos": { title: "Candidatos & Scorecards", subtitle: "Auditoría Anti-Overfit 9D & Exportación de Código" },
  "/ejecucion": { title: "Ejecución & Telemetría", subtitle: "Gestión de Sesiones, Kill-Switches y Logs" },
  "/prop-firms": { title: "Base de Datos Prop Firms", subtitle: "Reglas de Exámenes y Cuentas Fondeadas" },
  "/sistema": { title: "Diagnóstico de Infraestructura", subtitle: "Estado de SQX, FastAPI, DB y Puertos" },
};

export default function Header() {
  const pathname = usePathname();
  const current = ROUTE_NAMES[pathname] ?? { title: "Módulo Operativo", subtitle: "Ultrarentable Lab" };

  const [health, setHealth] = useState<{
    overall_status: string;
    services?: {
      api_backend?: { status: string };
      sqx_mcp?: { status: string };
      web_frontend?: { latency_ms?: number };
    };
    database?: { tables?: { candidates?: number } };
  } | null>(null);

  useEffect(() => {
    let mounted = true;
    const fetchHealth = () => {
      fetch("/api/v1/system/health")
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (mounted && data) setHealth(data);
        })
        .catch(() => {});
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const isSqxOnline = health?.services?.sqx_mcp?.status === "ONLINE";
  const candidateCount = health?.database?.tables?.candidates ?? 0;
  const latency = health?.services?.web_frontend?.latency_ms ?? 0;

  return (
    <header
      className="header"
      suppressHydrationWarning
      style={{
        padding: "0 28px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        minHeight: "60px",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        background: "rgba(11, 15, 25, 0.85)",
        backdropFilter: "blur(16px)",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* Left: Breadcrumb & Title */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", letterSpacing: "1px", fontFamily: "monospace" }}>
              ULTRARENTABLE
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "12px" }}>/</span>
            <span style={{ color: "#fff", fontWeight: 800, fontSize: "14px", letterSpacing: "-0.2px" }}>
              {current.title}
            </span>
          </div>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "1px" }}>
            {current.subtitle}
          </span>
        </div>
      </div>

      {/* Right: Real-time System Telemetry & Quick Navigation */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        {/* Live Pulse Badges */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
            borderRadius: "20px",
            padding: "4px 14px",
            fontSize: "11px",
            fontFamily: "monospace",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#22c55e", boxShadow: "0 0 8px #22c55e" }} />
            <span style={{ color: "#94a3b8" }}>API :8000</span>
          </div>

          <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>

          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                background: isSqxOnline ? "#22c55e" : "#ef4444",
                boxShadow: isSqxOnline ? "0 0 8px #22c55e" : "0 0 8px #ef4444",
              }}
            />
            <span style={{ color: isSqxOnline ? "#e2e8f0" : "#fca5a5" }}>SQX :8081</span>
          </div>

          <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>

          <div style={{ color: "#38bdf8" }}>
            {candidateCount} <span style={{ color: "#64748b" }}>candidatos</span>
          </div>

          <span style={{ color: "rgba(255,255,255,0.15)" }}>|</span>

          <div style={{ color: "#a855f7" }}>
            {latency}ms
          </div>
        </div>

        {/* Quick Nav Shortcut */}
        <Link
          href="/candidatos"
          style={{
            background: "rgba(56, 189, 248, 0.1)",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            color: "#38bdf8",
            fontSize: "11px",
            fontWeight: 700,
            padding: "5px 12px",
            borderRadius: "6px",
            textDecoration: "none",
            transition: "all 0.2s ease",
          }}
        >
          📊 Ver Scorecards
        </Link>
      </div>
    </header>
  );
}



