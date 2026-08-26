"use client";

import React, { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  Clock,
  ChevronDown,
  Layers,
  Sparkles,
  Zap,
  Building2,
  ShieldCheck,
  Award,
  BarChart2,
} from "lucide-react";

export default function Header() {
  const pathname = usePathname();
  const router = useRouter();

  const [timeUtc, setTimeUtc] = useState<string>("");
  const [timeLocal, setTimeLocal] = useState<string>("");
  const [mounted, setMounted] = useState<boolean>(false);
  const [viewMenuOpen, setViewMenuOpen] = useState<boolean>(false);

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

  const getCurrentStepLabel = () => {
    if (!pathname) return "Centro de Mando";
    if (pathname.includes("/strategies") || pathname.includes("1-motor-en-vivo")) return "01 · Motor 24/7";
    if (pathname.includes("/candidatos") || pathname.includes("2-explorador-excel")) return "02 · Catálogo SQLite";
    if (pathname.includes("/gates") || pathname.includes("3-pipeline-11-gates")) return "03 · Pipeline 11 Gates";
    if (pathname.includes("/portfolio") || pathname.includes("6-meta-estrategia")) return "04 · Portafolios";
    if (pathname.includes("/prop-firms")) return "05 · Fondeo CME 70 Tiers";
    if (pathname.includes("5-estrategias-aprobadas")) return "Bóveda Aprobadas";
    if (pathname.includes("4-panel-investigador")) return "Panel I+D";
    return "Ultrarentable Quant Lab";
  };

  const navShortcuts = [
    { label: "1. Motor & Backtest", href: "/strategies", icon: Zap, color: "#38bdf8" },
    { label: "2. Catálogo de Candidatos", href: "/candidatos", icon: Layers, color: "#818cf8" },
    { label: "3. Pipeline 11 Gates", href: "/gates", icon: ShieldCheck, color: "#10b981" },
    { label: "4. Portafolio Studio", href: "/portfolio", icon: BarChart2, color: "#c084fc" },
    { label: "5. Catálogo 70 Prop Firms", href: "/prop-firms", icon: Building2, color: "#f59e0b" },
    { label: "Bóveda Certificadas (11/11)", href: "/estrategias/5-estrategias-aprobadas", icon: Award, color: "#10b981" },
  ];

  return (
    <header
      suppressHydrationWarning
      style={{
        height: "50px",
        background: "rgba(8, 12, 20, 0.94)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 16px",
        position: "sticky",
        top: 0,
        zIndex: 100,
        boxSizing: "border-box",
      }}
    >
      {/* 1. SECCIÓN IZQUIERDA: SELECTOR RÁPIDO DE VISTA */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", position: "relative" }}>
        <button
          onClick={() => setViewMenuOpen(!viewMenuOpen)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "7px",
            background: "rgba(255, 255, 255, 0.05)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            padding: "5px 10px",
            borderRadius: "7px",
            cursor: "pointer",
            color: "#f8fafc",
            fontSize: "12px",
            fontWeight: 700,
            fontFamily: "var(--font-mono, monospace)",
            transition: "all 0.15s ease",
          }}
        >
          <span
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              backgroundColor: "#10b981",
              boxShadow: "0 0 8px #10b981",
            }}
          />
          <span>{getCurrentStepLabel()}</span>
          <ChevronDown style={{ width: "13px", height: "13px", color: "#94a3b8" }} />
        </button>

        {viewMenuOpen && (
          <div
            style={{
              position: "absolute",
              top: "38px",
              left: 0,
              width: "240px",
              background: "rgba(10, 15, 26, 0.98)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: "10px",
              boxShadow: "0 12px 32px rgba(0, 0, 0, 0.6)",
              padding: "6px",
              display: "flex",
              flexDirection: "column",
              gap: "2px",
              zIndex: 300,
            }}
            onMouseLeave={() => setViewMenuOpen(false)}
          >
            <div
              style={{
                fontSize: "9px",
                fontWeight: 800,
                color: "#64748b",
                letterSpacing: "0.8px",
                padding: "4px 8px",
                textTransform: "uppercase",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              ACCESO DIRECTO EMBUDO
            </div>
            {navShortcuts.map((item) => (
              <button
                key={item.href}
                onClick={() => {
                  router.push(item.href);
                  setViewMenuOpen(false);
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "7px 9px",
                  borderRadius: "6px",
                  background: pathname === item.href ? "rgba(255, 255, 255, 0.08)" : "transparent",
                  border: "none",
                  color: "#cbd5e1",
                  fontSize: "11.5px",
                  textAlign: "left",
                  cursor: "pointer",
                  transition: "background 0.1s ease",
                }}
              >
                <item.icon style={{ width: "14px", height: "14px", color: item.color }} />
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 2. SECCIÓN DERECHA: RELOJ INSTITUCIONAL DUAL Y ESTADO SSE */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {/* RELOJ DUAL LOCAL / UTC */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(0, 0, 0, 0.4)",
            border: "1px solid rgba(255, 255, 255, 0.06)",
            padding: "4px 10px",
            borderRadius: "6px",
            fontSize: "11px",
            fontFamily: "var(--font-mono, monospace)",
            color: "#94a3b8",
          }}
        >
          <Clock style={{ width: "12px", height: "12px", color: "#64748b" }} />
          <span style={{ color: "#e2e8f0", fontWeight: 700 }}>{mounted ? timeUtc : "--:--:-- UTC"}</span>
          <span style={{ color: "#475569" }}>|</span>
          <span>{mounted ? timeLocal : "--:--:-- LOC"}</span>
        </div>

        {/* ESTADO BACKEND & DOCTRINA */}
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <button
            onClick={() => router.push("/sistema")}
            title="Ver Telemetría 24/7 y SystemSupervisor"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "5px",
              padding: "3px 8px",
              borderRadius: "5px",
              background: "rgba(16, 185, 129, 0.08)",
              border: "1px solid rgba(16, 185, 129, 0.2)",
              fontSize: "10px",
              fontFamily: "var(--font-mono, monospace)",
              color: "#10b981",
              fontWeight: 700,
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <Activity style={{ width: "11px", height: "11px" }} />
            <span>FASTAPI :8000 LIVE</span>
          </button>
        </div>
      </div>
    </header>
  );
}
