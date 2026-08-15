"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";

const ROUTE_NAMES: Record<string, string> = {
  "/": "Paso 1: Buscador de Estrategias SQX",
  "/dashboard": "Dashboard General del Sistema",
  "/strategies": "Laboratorio de Estrategias",
  "/ultra": "Paso 2B: Modo Ultrarentable (BingX)",
  "/fondeo": "Paso 2A: Modo Fondeo (Prop Firms)",
  "/robots": "Paso 3: Monitor de Bots en Vivo",
  "/portfolio": "Métricas de Portfolio y Riesgo",
  "/alertas": "Alertas y Telemetría",
  "/seguridad": "Ajustes de Seguridad",
  "/strategyquant": "Servidor StrategyQuant X (MCP)",
  "/panel": "Estado del Sistema",
  "/data": "Gestión de Datos",
  "/backtest": "Motor de Backtesting",
  "/campaigns": "Campañas Autónomas",
  "/leaderboard": "Leaderboard de Calidad",
  "/research": "Investigación",
  "/bifurcacion": "Bifurcación de Despliegue",
  "/prop-firms": "Catálogo de Empresas de Fondeo (34 Firmas)",
  "/pasos": "Guía del Proceso Paso a Paso",
};

export default function Header() {
  const pathname = usePathname();
  const currentPage = ROUTE_NAMES[pathname] ?? "Módulo Operativo";

  return (
    <header
      className="header"
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
      }}
    >
      {/* Left: Breadcrumb */}
      <div className="breadcrumb" style={{ fontSize: 12, fontWeight: 600, display: "flex", alignItems: "center", whiteSpace: "nowrap" }}>
        <span className="breadcrumb-item" style={{ color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.8px", fontSize: 10, fontFamily: "monospace", fontWeight: 700 }}>
          ULTRARENTABLE TRADING LAB
        </span>
        <span className="breadcrumb-sep" style={{ margin: "0 8px", color: "var(--border)" }}>/</span>
        <span className="breadcrumb-item current" style={{ color: "var(--text-primary)", fontWeight: 700 }}>
          {currentPage}
        </span>
      </div>

      {/* Right: Clean Step Navigation */}
      <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap", justifyContent: "flex-end", padding: "6px 0" }}>
        <Link
          href="/"
          style={{
            padding: "4px 10px",
            borderRadius: "4px",
            background: pathname === "/" ? "var(--accent-dim)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${pathname === "/" ? "var(--accent)" : "var(--border)"}`,
            color: pathname === "/" ? "var(--accent)" : "var(--text-secondary)",
            fontSize: 10,
            fontWeight: 800,
            textDecoration: "none",
            fontFamily: "monospace",
          }}
        >
          [01] BUSCADOR SQX
        </Link>
        <Link
          href="/fondeo"
          style={{
            padding: "4px 10px",
            borderRadius: "4px",
            background: pathname === "/fondeo" ? "var(--accent-dim)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${pathname === "/fondeo" ? "var(--accent)" : "var(--border)"}`,
            color: pathname === "/fondeo" ? "var(--accent)" : "var(--text-secondary)",
            fontSize: 10,
            fontWeight: 800,
            textDecoration: "none",
            fontFamily: "monospace",
          }}
        >
          [02A] FONDEO
        </Link>
        <Link
          href="/ultra"
          style={{
            padding: "4px 10px",
            borderRadius: "4px",
            background: pathname === "/ultra" ? "var(--accent-dim)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${pathname === "/ultra" ? "var(--accent)" : "var(--border)"}`,
            color: pathname === "/ultra" ? "var(--accent)" : "var(--text-secondary)",
            fontSize: 10,
            fontWeight: 800,
            textDecoration: "none",
            fontFamily: "monospace",
          }}
        >
          [02B] ULTRA
        </Link>
        <Link
          href="/robots"
          style={{
            padding: "4px 10px",
            borderRadius: "4px",
            background: pathname === "/robots" ? "var(--accent-dim)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${pathname === "/robots" ? "var(--accent)" : "var(--border)"}`,
            color: pathname === "/robots" ? "var(--accent)" : "var(--text-secondary)",
            fontSize: 10,
            fontWeight: 800,
            textDecoration: "none",
            fontFamily: "monospace",
          }}
        >
          [03] MONITOR BOTS
        </Link>
        <Link
          href="/prop-firms"
          style={{
            padding: "4px 10px",
            borderRadius: "4px",
            background: pathname === "/prop-firms" ? "var(--accent-dim)" : "rgba(255,255,255,0.03)",
            border: `1px solid ${pathname === "/prop-firms" ? "var(--accent)" : "var(--border)"}`,
            color: pathname === "/prop-firms" ? "var(--accent)" : "var(--text-secondary)",
            fontSize: 10,
            fontWeight: 800,
            textDecoration: "none",
            fontFamily: "monospace",
          }}
        >
          [DB] PROP FIRMS
        </Link>
      </div>
    </header>
  );
}



