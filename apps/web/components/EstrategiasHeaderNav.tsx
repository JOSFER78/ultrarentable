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
    href: "/sistema",
    altHrefs: ["/estrategias/motor-en-vivo", "/sistema"],
    icon: "⚡",
    badge: "24/7",
    color: "#34d399",
  },
  {
    step: 2,
    label: "2. Explorador Cuantitativo Excel",
    shortLabel: "Explorador Excel",
    href: "/strategies",
    altHrefs: ["/estrategias/explorador-excel", "/strategies"],
    icon: "📊",
    badge: "230 CAND",
    color: "#38bdf8",
  },
  {
    step: 3,
    label: "3. Pipeline 11 Pasos (FSM)",
    shortLabel: "Pipeline 11-G",
    href: "/candidatos",
    altHrefs: ["/estrategias/pipeline-11-gates", "/candidatos"],
    icon: "🧬",
    badge: "11 GATES",
    color: "#818cf8",
  },
  {
    step: 4,
    label: "4. Panel Investigador Semántico",
    shortLabel: "Lab Investigador",
    href: "/research",
    altHrefs: ["/estrategias/panel-investigador", "/research"],
    icon: "🔬",
    badge: "LAB I+D",
    color: "#facc15",
  },
  {
    step: 5,
    label: "5. Estrategias Aprobadas (11/11)",
    shortLabel: "Aprobadas 11/11",
    href: "/gates",
    altHrefs: ["/estrategias/estrategias-aprobadas", "/gates"],
    icon: "🏆",
    badge: "CERTIFICADAS",
    color: "#10b981",
  },
  {
    step: 6,
    label: "6. Meta-Estrategia Ensamblada",
    shortLabel: "Meta-Estrategia",
    href: "/portfolio",
    altHrefs: ["/estrategias/meta-estrategia", "/portfolio"],
    icon: "🧩",
    badge: "SINERGIA",
    color: "#ec4899",
  },
];

export default function EstrategiasHeaderNav() {
  const pathname = usePathname();

  const isTabActive = (tab: EstrategiaTab) => {
    return tab.altHrefs.some((h) => pathname === h || pathname.startsWith(h));
  };

  return (
    <div
      style={{
        background: "rgba(10, 14, 22, 0.95)",
        backdropFilter: "blur(18px)",
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        padding: "8px 16px",
        marginBottom: "20px",
        borderRadius: "12px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: "10px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span style={{ fontSize: "16px" }}>🎯</span>
        <span
          style={{
            fontSize: "11px",
            fontWeight: 900,
            color: "#ffffff",
            fontFamily: "var(--font-mono, monospace)",
            letterSpacing: "1px",
            textTransform: "uppercase",
          }}
        >
          ESTRATEGIAS
        </span>
        <span
          style={{
            fontSize: "9px",
            color: "#94a3b8",
            background: "rgba(255, 255, 255, 0.06)",
            padding: "2px 6px",
            borderRadius: "4px",
            fontFamily: "var(--font-mono, monospace)",
          }}
        >
          6 FASES DETERMINISTAS
        </span>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
        {ESTRATEGIAS_TABS.map((tab) => {
          const active = isTabActive(tab);
          return (
            <Link
              key={tab.step}
              href={tab.href}
              style={{
                textDecoration: "none",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "8px",
                background: active ? `rgba(${tab.color === "#34d399" ? "52, 211, 153" : tab.color === "#38bdf8" ? "56, 189, 248" : tab.color === "#818cf8" ? "129, 140, 248" : tab.color === "#facc15" ? "250, 204, 21" : tab.color === "#10b981" ? "16, 185, 129" : "236, 72, 153"}, 0.18)` : "rgba(255, 255, 255, 0.03)",
                border: active ? `1px solid ${tab.color}` : "1px solid rgba(255, 255, 255, 0.08)",
                color: active ? "#ffffff" : "#94a3b8",
                fontSize: "11.5px",
                fontWeight: active ? 800 : 600,
                transition: "all 0.15s ease",
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.shortLabel}</span>
              <span
                style={{
                  fontSize: "8.5px",
                  fontWeight: 900,
                  padding: "1px 5px",
                  borderRadius: "4px",
                  background: active ? tab.color : "rgba(255, 255, 255, 0.08)",
                  color: active ? "#000000" : "#cbd5e1",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {tab.badge}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
