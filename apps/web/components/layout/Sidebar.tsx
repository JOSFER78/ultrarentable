"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  code: string;
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
    group: "CENTRO DE CONTROL & SQX",
    items: [
      { code: "CMD", label: "Panel Maestro Aprobadas", href: "/", badge: "MASTER", highlight: true },
      { code: "SQX", label: "Servidor StrategyQuant X", href: "/strategyquant", badge: "MCP 8081" },
      { code: "XLS", label: "Explorador Masivo Excel", href: "/strategies", badge: "BRUTO" },
    ],
  },
  {
    group: "DOCTRINA DUAL & CARTERAS",
    items: [
      { code: "ULT", label: "Ultra Lab (BingX · 500x)", href: "/ultra", badge: "1R · PYRAMID" },
      { code: "FND", label: "Track Fondeo (CME Props)", href: "/fondeo", badge: "MAX DD 4%" },
    ],
  },
  {
    group: "PIPELINE & IA CUANTITATIVA",
    items: [
      { code: "FSM", label: "Ciclo de Vida (10 Estados)", href: "/candidatos", badge: "PIPELINE" },
      { code: "QVF", label: "Bifurcación Evidence Gates", href: "/bifurcacion", badge: "EVIDENCE" },
      { code: "SEM", label: "IA Semántica & Failure-DB", href: "/research", badge: "5 AGENTS" },
    ],
  },
  {
    group: "EJECUCIÓN & SISTEMA",
    items: [
      { code: "BOX", label: "Paper Sandbox (14d)", href: "/ejecucion", badge: "SANDBOX" },
      { code: "SUP", label: "Supervisión & Workers", href: "/sistema", badge: "8 WORKERS" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.7)",
            backdropFilter: "blur(4px)",
            zIndex: 199,
          }}
        />
      )}

      <aside
        style={{
          width: collapsed ? "72px" : "240px",
          minWidth: collapsed ? "72px" : "240px",
          height: "100vh",
          background: "rgba(8, 12, 18, 0.95)",
          backdropFilter: "blur(20px)",
          borderRight: "1px solid rgba(255, 255, 255, 0.08)",
          display: "flex",
          flexDirection: "column",
          position: "sticky",
          top: 0,
          transition: "width 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
          zIndex: 200,
          boxSizing: "border-box",
        }}
      >
        {/* LOGO & TITLE */}
        <div
          onClick={() => setCollapsed(!collapsed)}
          style={{
            height: "64px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            padding: "0 18px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            cursor: "pointer",
          }}
        >
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #63e1b4 0%, #38bdf8 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "14px",
              color: "#06080d",
              fontFamily: "var(--font-mono, monospace)",
              boxShadow: "0 0 16px rgba(99, 225, 180, 0.3)",
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
                  fontSize: "9px",
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
        </div>

        {/* NAVIGATION GROUPS */}
        <nav style={{ flex: 1, padding: "16px 10px", overflowY: "auto" }}>
          {NAVIGATION.map((group) => (
            <div key={group.group} style={{ marginBottom: "20px" }}>
              {!collapsed && (
                <div
                  style={{
                    fontSize: "9px",
                    fontWeight: 800,
                    color: "#475569",
                    letterSpacing: "1px",
                    padding: "0 8px",
                    marginBottom: "8px",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  {group.group}
                </div>
              )}

              <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
                {group.items.map((item) => {
                  const active = isActive(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileOpen(false)}
                      title={collapsed ? item.label : undefined}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "10px",
                        padding: collapsed ? "9px 0" : "8px 12px",
                        justifyContent: collapsed ? "center" : "flex-start",
                        borderRadius: "8px",
                        background: active
                          ? "rgba(99, 225, 180, 0.12)"
                          : "transparent",
                        border: active
                          ? "1px solid rgba(99, 225, 180, 0.25)"
                          : "1px solid transparent",
                        textDecoration: "none",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: 900,
                          fontFamily: "var(--font-mono, monospace)",
                          padding: "2px 5px",
                          borderRadius: "4px",
                          background: active
                            ? "#63e1b4"
                            : item.highlight
                            ? "rgba(99, 225, 180, 0.15)"
                            : "rgba(255, 255, 255, 0.06)",
                          color: active
                            ? "#06080d"
                            : item.highlight
                            ? "#63e1b4"
                            : "#94a3b8",
                          flexShrink: 0,
                        }}
                      >
                        {item.code}
                      </span>

                      {!collapsed && (
                        <>
                          <span
                            style={{
                              fontSize: "12px",
                              fontWeight: active ? 700 : 500,
                              color: active ? "#ffffff" : "#cbd5e1",
                              flex: 1,
                              whiteSpace: "nowrap",
                            }}
                          >
                            {item.label}
                          </span>

                          {item.badge && (
                            <span
                              style={{
                                fontSize: "9px",
                                fontWeight: 700,
                                padding: "2px 5px",
                                borderRadius: "4px",
                                background: item.highlight
                                  ? "rgba(99, 225, 180, 0.1)"
                                  : "rgba(255, 255, 255, 0.04)",
                                color: item.highlight ? "#63e1b4" : "#64748b",
                                border: "1px solid rgba(255, 255, 255, 0.06)",
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

        {/* FOOTER */}
        <div
          style={{
            padding: "14px",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: collapsed ? "center" : "space-between",
          }}
        >
          {!collapsed && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "#34d399",
                  boxShadow: "0 0 8px #34d399",
                }}
              />
              <span
                style={{
                  fontSize: "10px",
                  color: "#64748b",
                  fontWeight: 700,
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                REAL-ONLY · ZERO-MOCK
              </span>
            </div>
          )}

          <button
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Expandir Sidebar" : "Colapsar Sidebar"}
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "6px",
              color: "#94a3b8",
              padding: "4px 8px",
              cursor: "pointer",
              fontSize: "11px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            {collapsed ? "→" : "←"}
          </button>
        </div>
      </aside>
    </>
  );
}
