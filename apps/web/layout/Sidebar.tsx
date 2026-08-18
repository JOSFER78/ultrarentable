"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState } from "react";

interface NavItem {
  code?: string;
  label: string;
  href: string;
  badge?: string;
  accent?: string;
}

const NAV_SECTIONS: { label: string; items: NavItem[] }[] = [
  {
    label: "CENTRO DE CONTROL",
    items: [
      { code: "CC", label: "Command Center V2", href: "/", badge: "MASTER" },
    ],
  },
  {
    label: "RUTAS DE TRADING DUAL",
    items: [
      { code: "BX", label: "ULTRA · BingX Perps", href: "/ultra", badge: "VAULT", accent: "#ef4444" },
      { code: "FD", label: "FONDEO · CME Prop", href: "/fondeo", badge: "50K", accent: "#3b82f6" },
      { code: "PF", label: "Catálogo 34 Firmas", href: "/prop-firms", badge: "PROP" },
    ],
  },
  {
    label: "VALIDACIÓN & GOBERNANZA",
    items: [
      { code: "QVF", label: "Validation Fabric Dual", href: "/bifurcacion", badge: "DSR" },
      { code: "FSM", label: "Candidate Registry (10 St)", href: "/candidatos", badge: "DAG" },
      { code: "IA", label: "Semantic AI & Failure-DB", href: "/research", badge: "MEM" },
    ],
  },
  {
    label: "EJECUCIÓN & SISTEMA",
    items: [
      { code: "PPR", label: "Paper Sandbox (14d)", href: "/ejecucion", badge: "LIVE" },
      { code: "PTF", label: "Portfolio Multi-Activo", href: "/portfolio", badge: "HRP" },
      { code: "SYS", label: "Supervisor & 8 Workers", href: "/sistema", badge: "SSE", accent: "#34d399" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside
      style={{
        width: collapsed ? "64px" : "240px",
        minHeight: "100vh",
        background: "rgba(8, 12, 20, 0.95)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        transition: "width 0.2s ease",
        zIndex: 90,
        position: "sticky",
        top: 0,
        boxSizing: "border-box",
      }}
    >
      <div>
        {/* Logo / Title */}
        <div style={{ padding: "16px 18px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          {!collapsed && (
            <Link href="/" style={{ textDecoration: "none", color: "inherit", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 18 }}>⚡</span>
              <div>
                <div style={{ fontSize: 13, fontWeight: 900, fontFamily: "var(--font-mono)", color: "var(--accent)" }}>ULTRARENTABLE</div>
                <div style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>V2.2.0 CANONICAL</div>
              </div>
            </Link>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: 12 }}
          >
            {collapsed ? "▶" : "◀"}
          </button>
        </div>

        {/* Navigation Sections */}
        <div style={{ padding: "12px 8px" }}>
          {NAV_SECTIONS.map((sec, idx) => (
            <div key={idx} style={{ marginBottom: "16px" }}>
              {!collapsed && (
                <div style={{ fontSize: 9, fontWeight: 800, color: "var(--text-muted)", fontFamily: "var(--font-mono)", padding: "4px 10px", textTransform: "uppercase", letterSpacing: "0.8px" }}>
                  {sec.label}
                </div>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 4 }}>
                {sec.items.map((item) => {
                  const active = isActive(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: collapsed ? "center" : "space-between",
                        padding: "8px 10px",
                        borderRadius: "8px",
                        textDecoration: "none",
                        fontSize: 12,
                        fontWeight: active ? 700 : 500,
                        background: active ? "rgba(99, 225, 180, 0.12)" : "transparent",
                        color: active ? (item.accent || "var(--accent)") : "var(--text-secondary)",
                        border: active ? `1px solid ${item.accent || "var(--accent)"}` : "1px solid transparent",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 10, fontFamily: "var(--font-mono)", fontWeight: 800, opacity: 0.8 }}>
                          {item.code}
                        </span>
                        {!collapsed && <span>{item.label}</span>}
                      </div>
                      {!collapsed && item.badge && (
                        <span style={{ fontSize: 9, fontFamily: "var(--font-mono)", padding: "2px 5px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", color: "var(--text-muted)" }}>
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer System Pill */}
      {!collapsed && (
        <div style={{ padding: "12px 14px", borderTop: "1px solid var(--border)", fontSize: 10, fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#34d399" }} />
            <span style={{ color: "#34d399", fontWeight: 700 }}>8 WORKERS ACTIVE</span>
          </div>
          <div>Cero mocks · Real-Only</div>
        </div>
      )}
    </aside>
  );
}
