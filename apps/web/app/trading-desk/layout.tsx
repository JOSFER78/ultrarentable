"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bot,
  ShieldAlert,
  FileText,
  Sliders,
} from "lucide-react";

const DESK_TABS = [
  { label: "Terminal & DOM", href: "/trading-desk", icon: Activity, badge: "DOM" },
  { label: "Posiciones & Brackets", href: "/trading-desk/posiciones", icon: BarChart3, badge: "LIVE" },
  { label: "Estrategias Activas", href: "/trading-desk/estrategias", icon: Bot, badge: "11 GATES" },
  { label: "Sentinel de Riesgo", href: "/trading-desk/riesgo", icon: ShieldAlert, badge: "DD GUARD" },
  { label: "Auditoría Forense", href: "/trading-desk/auditoria", icon: FileText, badge: "WAL" },
  { label: "Conexión Gateway", href: "/trading-desk/configuracion", icon: Sliders, badge: "CONFIG" },
];

export default function TradingDeskLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* BARRA DE PESTAÑAS INSTITUCIONAL TRADING DESK */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          background: "#0a0e17",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "8px",
          padding: "6px 8px",
          overflowX: "auto",
        }}
      >
        {DESK_TABS.map((tab) => {
          const isActive = pathname === tab.href;
          const Icon = tab.icon;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 12px",
                borderRadius: "5px",
                fontSize: "12px",
                fontWeight: isActive ? 600 : 500,
                color: isActive ? "#38bdf8" : "#94a3b8",
                background: isActive ? "rgba(56, 189, 248, 0.12)" : "transparent",
                border: isActive ? "1px solid rgba(56, 189, 248, 0.25)" : "1px solid transparent",
                textDecoration: "none",
                whiteSpace: "nowrap",
                transition: "all 0.12s ease",
              }}
            >
              <Icon style={{ width: "14px", height: "14px", color: isActive ? "#38bdf8" : "#64748b" }} />
              <span>{tab.label}</span>
              <span
                style={{
                  fontSize: "9px",
                  fontFamily: "var(--font-mono, monospace)",
                  padding: "1px 4px",
                  borderRadius: "3px",
                  background: isActive ? "rgba(56, 189, 248, 0.2)" : "rgba(255, 255, 255, 0.05)",
                  color: isActive ? "#38bdf8" : "#64748b",
                }}
              >
                {tab.badge}
              </span>
            </Link>
          );
        })}
      </div>

      <div>{children}</div>
    </div>
  );
}
