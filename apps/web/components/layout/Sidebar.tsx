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
    group: "ESTRATEGIAS (6 FASES DETERMINISTAS)",
    items: [
      { code: "1", icon: "⚡", label: "1. Motor 24/7 en Vivo", href: "/sistema", badge: "24/7", highlight: true },
      { code: "2", icon: "📊", label: "2. Explorador Cuantitativo Excel", href: "/strategies", badge: "230 CAND" },
      { code: "3", icon: "🧬", label: "3. Pipeline 11 Pasos (FSM)", href: "/candidatos", badge: "11-GATES" },
      { code: "4", icon: "🔬", label: "4. Panel Investigador Semántico", href: "/research", badge: "LAB I+D" },
      { code: "5", icon: "🏆", label: "5. Estrategias Aprobadas (11/11)", href: "/gates", badge: "CERTIFICADAS" },
      { code: "6", icon: "🧩", label: "6. Meta-Estrategia Ensamblada", href: "/portfolio", badge: "PORTFOLIO" },
    ],
  },
  {
    group: "RUTAS DE TRADING DUAL",
    items: [
      { code: "ULT", icon: "🔥", label: "Ultra Lab (BingX 500x)", href: "/ultra", badge: "BALA" },
      { code: "FND", icon: "🛡️", label: "Track Fondeo (CME)", href: "/fondeo", badge: "DD 4%" },
      { code: "PF", icon: "🏛️", label: "Catálogo 34 Prop Firms", href: "/prop-firms", badge: "APEX/TOP" },
    ],
  },
  {
    group: "EJECUCIÓN & INFRAESTRUCTURA",
    items: [
      { code: "PPR", icon: "📦", label: "Paper Sandbox (14d)", href: "/ejecucion", badge: "LIVE" },
      { code: "NTX", icon: "💎", label: "NautilusTrader Core", href: "/gates/gate-11-nautilus-trader", badge: "EVENT" },
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
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside
      style={{
        width: collapsed ? "68px" : "230px",
        minWidth: collapsed ? "68px" : "230px",
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
          href="/"
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
                V2 QUANT LAB
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
                    key={item.href}
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
                              background: item.highlight
                                ? "rgba(99, 225, 180, 0.1)"
                                : "rgba(255, 255, 255, 0.04)",
                              color: item.highlight ? "#63e1b4" : "#64748b",
                              border: "1px solid rgba(255, 255, 255, 0.06)",
                              fontFamily: "var(--font-mono, monospace)",
                              flexShrink: 0,
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

      {/* FOOTER & TOGGLE BUTTON */}
      <div
        style={{
          padding: collapsed ? "10px 0" : "10px 12px",
          borderTop: "1px solid rgba(255, 255, 255, 0.08)",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          flexShrink: 0,
        }}
      >
        {!collapsed ? (
          <>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "#34d399",
                  boxShadow: "0 0 6px #34d399",
                }}
              />
              <span
                style={{
                  fontSize: "9px",
                  color: "#64748b",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                REAL-ONLY
              </span>
            </div>

            <button
              onClick={toggleCollapse}
              title="Plegar menú lateral (Modo Compacto)"
              style={{
                background: "rgba(255, 255, 255, 0.04)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "5px",
                color: "#94a3b8",
                padding: "3px 7px",
                cursor: "pointer",
                fontSize: "10px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              ◀ Plegar
            </button>
          </>
        ) : (
          <button
            onClick={toggleCollapse}
            title="Desplegar menú lateral"
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "6px",
              color: "#63e1b4",
              width: "32px",
              height: "28px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              fontSize: "11px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            ▶
          </button>
        )}
      </div>
    </aside>
  );
}
