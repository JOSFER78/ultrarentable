"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { STRATEGY_PHASES, StrategyPhase } from "@/lib/strategyPhases";

// Derivado del catálogo canónico: si cambia una fase, badge o ruta, cambia aquí automáticamente.
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

const ESTRATEGIAS_TABS: EstrategiaTab[] = STRATEGY_PHASES.filter(
  (p: StrategyPhase) => p.id > 0 && p.route
).map((p) => ({
  step: p.id,
  label: p.label || p.name || "",
  shortLabel: p.shortLabel || "",
  href: p.route as string,
  altHrefs: [...(p.legacyRoutes ?? []), p.route as string],
  icon: p.icon,
  badge: p.badge,
  color: p.color,
}));

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
