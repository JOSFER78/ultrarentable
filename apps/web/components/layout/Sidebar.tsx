"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  code: string;
  icon: string;
  label: string;
  href: string;
  badge?: string;
  highlight?: boolean;
}

interface NavGroup {
  group: string;
  items: NavItem[];
}

const NAVIGATION: NavGroup[] = [
  {
    group: "ESTRATEGIAS & GATES",
    items: [
      { code: "HUB", icon: "🧬", label: "Catálogo de Estrategias", href: "/strategies", badge: "PORTADA", highlight: true },
      { code: "GAT", icon: "💎", label: "Pipeline 10 Gates (Certificadas)", href: "/gates", badge: "10-GATES", highlight: true },
      { code: "PORT", icon: "🧩", label: "Meta-Estrategias & Portfolio", href: "/portfolio", badge: "PORTFOLIO" },
    ],
  },
  {
    group: "RUTAS DE TRADING & FONDEO",
    items: [
      { code: "PF", icon: "🏛️", label: "Catálogo 70 Prop Firms CME", href: "/prop-firms", badge: "70 TIERS", highlight: true },
      { code: "FND", icon: "🛡️", label: "Reglas & Parámetros Fondeo", href: "/prop-firms", badge: "CME GUARD" },
      { code: "STU", icon: "📊", label: "Portfolio Studio & Weights", href: "/portfolio", badge: "STUDIO" },
    ],
  },
  {
    group: "VALIDACIÓN & MOTOR FÍSICO",
    items: [
      { code: "ENG", icon: "⚡", label: "FastEngine Backtest Físico", href: "/strategies", badge: "FASTENGINE" },
      { code: "LED", icon: "🏆", label: "Matriz 11 Gates & Merkle Lock", href: "/gates", badge: "v5.3.0" },
      { code: "MET", icon: "📈", label: "Portafolios Multiactivo v5.3.0", href: "/portfolio", badge: "100% REAL" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("ur_sidebar_collapsed");
    if (saved !== null) {
      setCollapsed(saved === "true");
    }
  }, []);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("ur_sidebar_collapsed", String(next));
  };

  const isActive = (href: string) => {
    if (!pathname) return false;
    if (href === "/strategies") return pathname === "/strategies" || pathname === "/";
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <aside
      suppressHydrationWarning
      style={{
        width: mounted && collapsed ? "68px" : "230px",
        minWidth: mounted && collapsed ? "68px" : "230px",
        height: "100vh",
        background: "rgba(8, 12, 18, 0.96)",
        backdropFilter: "blur(20px)",
        borderRight: "1px solid rgba(255, 255, 255, 0.08)",
        display: "flex",
        flexDirection: "column",
        position: "sticky",
        top: 0,
        transition: "width 0.18s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.18s cubic-bezier(0.4, 0, 0.2, 1)",
        zIndex: 200,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* BRAND & TOGGLE HEADER */}
      <div
        style={{
          height: "54px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "0" : "0 14px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          flexShrink: 0,
        }}
      >
        <Link
          href="/strategies"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            textDecoration: "none",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: "30px",
              height: "30px",
              borderRadius: "7px",
              background: "linear-gradient(135deg, #63e1b4 0%, #38bdf8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "13px",
              color: "#06080d",
              fontFamily: "var(--font-mono, monospace)",
              boxShadow: "0 0 14px rgba(99, 225, 180, 0.35)",
              flexShrink: 0,
            }}
          >
            UR
          </div>
          {!collapsed && (
            <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>
              <span
                style={{
                  fontWeight: 900,
                  fontSize: "13px",
                  color: "#ffffff",
                  letterSpacing: "0.5px",
                  whiteSpace: "nowrap",
                }}
              >
                ULTRARENTABLE
              </span>
              <span
                style={{
                  fontSize: "8.5px",
                  color: "#63e1b4",
                  fontWeight: 800,
                  letterSpacing: "0.8px",
                  fontFamily: "var(--font-mono, monospace)",
                  whiteSpace: "nowrap",
                }}
              >
                QUANT LAB V5.3 (REAL-ONLY)
              </span>
            </div>
          )}
        </Link>

        {!collapsed && (
          <button
            onClick={toggleCollapse}
            title="Plegar menú lateral"
            style={{
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "6px",
              color: "#94a3b8",
              width: "24px",
              height: "24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              fontSize: "10px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            ◀
          </button>
        )}
      </div>

      {/* NAVIGATION GROUPS */}
      <nav style={{ flex: 1, padding: collapsed ? "12px 6px" : "12px 8px", overflowY: "auto", overflowX: "hidden" }}>
        {NAVIGATION.map((group) => (
          <div key={group.group} style={{ marginBottom: "14px" }}>
            {!collapsed && (
              <div
                style={{
                  fontSize: "8.5px",
                  fontWeight: 800,
                  color: "#475569",
                  letterSpacing: "0.8px",
                  padding: "0 6px",
                  marginBottom: "6px",
                  fontFamily: "var(--font-mono, monospace)",
                  textTransform: "uppercase",
                }}
              >
                {group.group}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {group.items.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    title={collapsed ? `${item.label} (${item.badge || ""})` : undefined}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "9px",
                      padding: collapsed ? "9px 0" : "7px 10px",
                      justifyContent: collapsed ? "center" : "flex-start",
                      borderRadius: "7px",
                      background: active
                        ? "rgba(99, 225, 180, 0.12)"
                        : "transparent",
                      border: active
                        ? "1px solid rgba(99, 225, 180, 0.25)"
                        : "1px solid transparent",
                      textDecoration: "none",
                      transition: "all 0.12s ease",
                      position: "relative",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "11px",
                        width: collapsed ? "32px" : "auto",
                        textAlign: "center",
                        fontWeight: 800,
                        fontFamily: "var(--font-mono, monospace)",
                        padding: collapsed ? "4px 0" : "2px 5px",
                        borderRadius: "4px",
                        background: active
                          ? "#63e1b4"
                          : item.highlight
                          ? "rgba(99, 225, 180, 0.15)"
                          : "rgba(255, 255, 255, 0.05)",
                        color: active
                          ? "#06080d"
                          : item.highlight
                          ? "#63e1b4"
                          : "#94a3b8",
                        flexShrink: 0,
                      }}
                    >
                      {collapsed ? item.icon : item.code}
                    </span>

                    {!collapsed && (
                      <>
                        <span
                          style={{
                            fontSize: "11.5px",
                            fontWeight: active ? 700 : 500,
                            color: active ? "#ffffff" : "#cbd5e1",
                            flex: 1,
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {item.label}
                        </span>

                        {item.badge && (
                          <span
                            style={{
                              fontSize: "8.5px",
                              fontWeight: 700,
                              padding: "1px 4px",
                              borderRadius: "3px",
                              background: active ? "rgba(99, 225, 180, 0.2)" : "rgba(255, 255, 255, 0.05)",
                              color: active ? "#63e1b4" : "#64748b",
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
