"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";

interface BreadcrumbMap {
  [key: string]: { section: string; title: string };
}

const ROUTE_METADATA: BreadcrumbMap = {
  "/": { section: "Inicio", title: "Centro de Mando Cuantitativo" },
  "/estrategias": { section: "Laboratorio Core", title: "Strategy Lab & Descubrimiento" },
  "/strategies": { section: "Laboratorio Core", title: "Strategy Lab" },
  "/candidatos": { section: "Laboratorio Core", title: "Explorador de Candidatos SQLite WAL" },
  "/gates": { section: "Laboratorio Core", title: "Pipeline de 11 Evidence Gates" },
  "/portfolio": { section: "Laboratorio Core", title: "Portafolio Studio & Paridad de Riesgo" },
  "/bifurcacion": { section: "Rutas de Operación", title: "Bifurcación Dual Master" },
  "/bifurcacion/ultrarentable": { section: "Rutas de Operación", title: "Track ULTRA (BingX Perps)" },
  "/bifurcacion/fondeo": { section: "Rutas de Operación", title: "Track FONDEO (CME Futures)" },
  "/ultra": { section: "Rutas de Operación", title: "Track ULTRA (BingX Perps)" },
  "/fondeo": { section: "Rutas de Operación", title: "Track FONDEO (CME Futures)" },
  "/tradesfera": { section: "Ecosistema", title: "Portal Tradesfera V2 (18 Módulos)" },
  "/prop-firms": { section: "Ecosistema", title: "Catálogo 70 Prop Firms CME" },
  "/trading-desk": { section: "Ecosistema", title: "Trading Desk CME en Vivo" },
  "/trading-desk/posiciones": { section: "Trading Desk", title: "Posiciones & Brackets" },
  "/trading-desk/estrategias": { section: "Trading Desk", title: "Estrategias Activas" },
  "/trading-desk/riesgo": { section: "Trading Desk", title: "Sentinel de Riesgo" },
  "/trading-desk/auditoria": { section: "Trading Desk", title: "Auditoría Forense WAL" },
  "/trading-desk/configuracion": { section: "Trading Desk", title: "Conexión Gateway" },
  "/sistema": { section: "Infraestructura", title: "Telemetría & Pulso 24/7" },
};

export default function Header() {
  const pathname = usePathname() || "/";
  const [timeUtc, setTimeUtc] = useState<string>("");
  const [timeLocal, setTimeLocal] = useState<string>("");
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    setMounted(true);
    const updateClocks = () => {
      const now = new Date();
      setTimeUtc(
        now.toLocaleTimeString("en-GB", {
          timeZone: "UTC",
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }) + " UTC"
      );
      setTimeLocal(
        now.toLocaleTimeString("es-ES", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }) + " LOC"
      );
    };

    updateClocks();
    const interval = setInterval(updateClocks, 1000);
    return () => clearInterval(interval);
  }, []);

  const meta = ROUTE_METADATA[pathname] || {
    section: "Plataforma",
    title: pathname.replace(/^\//, "").replace(/-/g, " ").toUpperCase() || "General",
  };

  return (
    <header
      suppressHydrationWarning
      style={{
        height: "44px",
        background: "#080c14",
        borderBottom: "1px solid rgba(255, 255, 255, 0.07)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 18px",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* 1. BREADCRUMBS JERÁRQUICOS DISCRETOS */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", fontFamily: "var(--font-mono, monospace)" }}>
        <Link
          href="/"
          style={{
            color: "#64748b",
            textDecoration: "none",
            fontWeight: 600,
            transition: "color 0.15s",
          }}
        >
          ULTRARENTABLE
        </Link>
        <ChevronRight style={{ width: "12px", height: "12px", color: "#334155" }} />
        <span style={{ color: "#94a3b8", fontWeight: 500 }}>{meta.section}</span>
        <ChevronRight style={{ width: "12px", height: "12px", color: "#334155" }} />
        <span style={{ color: "#f8fafc", fontWeight: 600, letterSpacing: "0.2px" }}>{meta.title}</span>
      </div>

      {/* 2. ESTADO DEL MOTOR & RELOJES (SIN ELEMENTOS REDUNDANTES) */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            background: "rgba(16, 185, 129, 0.08)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            padding: "2px 8px",
            borderRadius: "4px",
            fontSize: "10.5px",
            fontFamily: "var(--font-mono, monospace)",
            color: "#34d399",
            fontWeight: 600,
          }}
        >
          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 6px #10b981" }} />
          <span>v5.4.0 REAL-ONLY</span>
        </div>

        {mounted && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "11px",
              fontFamily: "var(--font-mono, monospace)",
              color: "#64748b",
            }}
          >
            <span>{timeUtc}</span>
            <span style={{ color: "#334155" }}>|</span>
            <span>{timeLocal}</span>
          </div>
        )}
      </div>
    </header>
  );
}
