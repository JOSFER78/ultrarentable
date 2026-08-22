"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface EstrategiaTab {
  step: number;
  label: string;
  shortLabel: string;
  href: string;
  altHrefs: string[];
  icon: string;
  badge: string;
  color: string;
}

const ESTRATEGIAS_TABS: EstrategiaTab[] = [
  {
    step: 1,
    label: "1. Motor 24/7 en Vivo",
    shortLabel: "Motor 24/7",
    href: "/panel",
    altHrefs: ["/panel", "/sistema", "/panel/motor-en-vivo"],
    icon: "⚡",
    badge: "24/7",
    color: "#34d399",
  },
  {
    step: 2,
    label: "2. Catálogo de Estrategias (230)",
    shortLabel: "Catálogo Estrategias",
    href: "/estrategias",
    altHrefs: ["/estrategias", "/strategies", "/estrategias/explorador-excel"],
    icon: "📊",
    badge: "230 CAND",
    color: "#38bdf8",
  },
  {
    step: 3,
    label: "3. Pipeline 11 Pasos (FSM)",
    shortLabel: "Pipeline 11-G",
    href: "/candidatos",
    altHrefs: ["/candidatos", "/pasos", "/estrategias/pipeline-11-gates"],
    icon: "🧬",
    badge: "11 GATES",
    color: "#818cf8",
  },
  {
    step: 4,
    label: "4. Panel Investigador Semántico",
    shortLabel: "Lab Investigador",
    href: "/research",
    altHrefs: ["/research", "/backtest", "/estrategias/panel-investigador"],
    icon: "🔬",
    badge: "LAB I+D",
    color: "#facc15",
  },
  {
    step: 5,
    label: "5. Estrategias Aprobadas (11/11)",
    shortLabel: "Aprobadas 11/11",
    href: "/gates",
    altHrefs: ["/gates", "/leaderboard", "/estrategias/estrategias-aprobadas"],
    icon: "🏆",
    badge: "CERTIFICADAS",
    color: "#10b981",
  },
  {
    step: 6,
    label: "6. Meta-Estrategia Ensamblada",
    shortLabel: "Meta-Estrategia",
    href: "/portfolio",
    altHrefs: ["/portfolio", "/estrategias/meta-estrategia"],
    icon: "🧩",
    badge: "PORTFOLIO",
    color: "#ec4899",
  },
];

export default function EstrategiasHeaderNav() {
  const pathname = usePathname();

  if (pathname === "/estrategias") {
    return null;
  }

  const isTabActive = (tab: EstrategiaTab): boolean => {
    if (!pathname) return false;
    if (pathname === tab.href) return true;
    return tab.altHrefs.some((alt) => pathname === alt || pathname.startsWith(alt + "/"));
  };

  return (
    <nav
      aria-label="Navegación de las 6 Fases Deterministas de Estrategias"
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        background: "rgba(10, 15, 24, 0.85)",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "12px",
        padding: "6px 10px",
        marginBottom: "20px",
        overflowX: "auto",
        scrollbarWidth: "none",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.4)",
      }}
    >
      {/* BADGE CATEGORÍA */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          padding: "6px 12px",
          background: "rgba(56, 189, 248, 0.08)",
          border: "1px solid rgba(56, 189, 248, 0.2)",
          borderRadius: "8px",
          marginRight: "4px",
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: "13px" }}>🧬</span>
        <span
          style={{
            fontSize: "10px",
            fontWeight: 900,
            letterSpacing: "1px",
            color: "#38bdf8",
            fontFamily: "var(--font-mono, monospace)",
            whiteSpace: "nowrap",
          }}
        >
          ESTRATEGIAS · 6 FASES DETERMINISTAS
        </span>
      </div>

      {/* 6 TABS */}
      {ESTRATEGIAS_TABS.map((tab) => {
        const active = isTabActive(tab);
        return (
          <Link
            key={tab.step}
            href={tab.href}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              padding: "7px 12px",
              borderRadius: "8px",
              textDecoration: "none",
              background: active
                ? `linear-gradient(135deg, ${tab.color}22 0%, rgba(16, 24, 38, 0.9) 100%)`
                : "transparent",
              border: active
                ? `1px solid ${tab.color}66`
                : "1px solid transparent",
              color: active ? "#ffffff" : "#94a3b8",
              fontSize: "12px",
              fontWeight: active ? 800 : 500,
              transition: "all 0.15s ease",
              flexShrink: 0,
              boxShadow: active ? `0 0 12px ${tab.color}22` : "none",
            }}
          >
            <span style={{ fontSize: "13px" }}>{tab.icon}</span>
            <span style={{ whiteSpace: "nowrap" }}>{tab.shortLabel}</span>
            <span
              style={{
                fontSize: "9px",
                fontWeight: 900,
                padding: "2px 5px",
                borderRadius: "4px",
                background: active ? `${tab.color}33` : "rgba(255, 255, 255, 0.05)",
                color: active ? tab.color : "#64748b",
                fontFamily: "var(--font-mono, monospace)",
                letterSpacing: "0.5px",
              }}
            >
              {tab.badge}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
