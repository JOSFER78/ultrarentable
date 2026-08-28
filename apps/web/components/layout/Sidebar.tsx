"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Zap,
  Database,
  ShieldCheck,
  PieChart,
  GitFork,
  Flame,
  Building2,
  BookOpen,
  Activity,
  Radio,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface NavGroup {
  title: string;
  items: NavItem[];
}

interface NavItem {
  code: string;
  label: string;
  subtitle: string;
  href: string;
  altHrefs?: string[];
  icon: React.ComponentType<{ style?: React.CSSProperties; className?: string }>;
  badge?: string;
  accent?: string;
}

const NAVIGATION_GROUPS: NavGroup[] = [
  {
    title: "LABORATORIO CORE",
    items: [
      {
        code: "STRAT",
        label: "Strategy Lab",
        subtitle: "Descubrimiento & AST Canónico",
        href: "/estrategias",
        altHrefs: ["/estrategias", "/strategies"],
        icon: Zap,
        badge: "LAB",
        accent: "#38bdf8",
      },
      {
        code: "CAND",
        label: "Candidatos SQLite",
        subtitle: "Base de Datos WAL & Hash",
        href: "/candidatos",
        icon: Database,
        badge: "SQLITE",
        accent: "#818cf8",
      },
      {
        code: "GATES",
        label: "11 Evidence Gates",
        subtitle: "Holdout Ciego OOS Anti-Fit",
        href: "/gates",
        icon: ShieldCheck,
        badge: "11/11",
        accent: "#34d399",
      },
      {
        code: "PORT",
        label: "Portafolio Studio",
        subtitle: "Paridad de Riesgo Multiactivo",
        href: "/portfolio",
        icon: PieChart,
        badge: "RISK",
        accent: "#c084fc",
      },
    ],
  },
  {
    title: "RUTAS DE OPERACIÓN",
    items: [
      {
        code: "BIF",
        label: "Bifurcación Master",
        subtitle: "Selector Dual de Arquitectura",
        href: "/bifurcacion",
        icon: GitFork,
        badge: "DUAL",
        accent: "#f59e0b",
      },
      {
        code: "ULTRA",
        label: "Track ULTRA",
        subtitle: "BingX Perps & Asimetría",
        href: "/ultra",
        altHrefs: ["/ultra", "/bifurcacion/ultrarentable"],
        icon: Flame,
        badge: "BINGX",
        accent: "#ec4899",
      },
      {
        code: "FONDEO",
        label: "Track FONDEO",
        subtitle: "CME Futures & DD Estricto",
        href: "/fondeo",
        altHrefs: ["/fondeo", "/bifurcacion/fondeo"],
        icon: Building2,
        badge: "CME",
        accent: "#10b981",
      },
    ],
  },
  {
    title: "ECOSISTEMA & EJECUCIÓN",
    items: [
      {
        code: "TSFERA",
        label: "Portal Tradesfera",
        subtitle: "18 Módulos & Psicotrading",
        href: "/tradesfera",
        icon: BookOpen,
        badge: "DOSSIER",
        accent: "#fbbf24",
      },
      {
        code: "PROPS",
        label: "70 Prop Firms CME",
        subtitle: "Matriz Comparativa & Reglas",
        href: "/prop-firms",
        icon: Building2,
        badge: "70 TIERS",
        accent: "#38bdf8",
      },
      {
        code: "DESK",
        label: "Trading Desk CME",
        subtitle: "Mesa en Vivo & Brackets",
        href: "/trading-desk",
        altHrefs: ["/trading-desk/posiciones", "/trading-desk/estrategias", "/trading-desk/riesgo", "/trading-desk/auditoria", "/trading-desk/configuracion"],
        icon: Activity,
        badge: "LIVE",
        accent: "#10b981",
      },
    ],
  },
  {
    title: "INFRAESTRUCTURA",
    items: [
      {
        code: "SIST",
        label: "Telemetría 24/7",
        subtitle: "SystemSupervisor & Daemons",
        href: "/sistema",
        icon: Radio,
        badge: "SUPERVISOR",
        accent: "#64748b",
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname() || "/";
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);

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

  const isItemActive = (item: NavItem): boolean => {
    if (pathname === item.href) return true;
    if (item.altHrefs && item.altHrefs.some((alt) => pathname === alt || pathname.startsWith(alt + "/"))) {
      return true;
    }
    if (item.href !== "/" && pathname.startsWith(item.href)) {
      return true;
    }
    return false;
  };

  return (
    <aside
      suppressHydrationWarning
      style={{
        width: collapsed ? "64px" : "240px",
        minWidth: collapsed ? "64px" : "240px",
        maxWidth: collapsed ? "64px" : "240px",
        height: "100vh",
        background: "#070a10",
        borderRight: "1px solid rgba(255, 255, 255, 0.07)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        transition: "width 0.2s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        position: "sticky",
        top: 0,
        zIndex: 110,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* 1. CABECERA SIDEBAR: LOGO + TOGGLE */}
      <div
        style={{
          height: "44px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "0" : "0 14px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        {!collapsed ? (
          <Link
            href="/"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              textDecoration: "none",
            }}
          >
            <div
              style={{
                width: "24px",
                height: "24px",
                borderRadius: "5px",
                background: "linear-gradient(135deg, #0ea5e9 0%, #10b981 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 900,
                fontSize: "11px",
                color: "#ffffff",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              UR
            </div>
            <div>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#f8fafc", letterSpacing: "0.4px" }}>
                ULTRARENTABLE
              </div>
              <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                QUANT LAB
              </div>
            </div>
          </Link>
        ) : (
          <Link
            href="/"
            title="Ultrarentable Quant Lab"
            style={{
              width: "24px",
              height: "24px",
              borderRadius: "5px",
              background: "linear-gradient(135deg, #0ea5e9 0%, #10b981 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "11px",
              color: "#ffffff",
              textDecoration: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            UR
          </Link>
        )}

        <button
          onClick={toggleCollapse}
          title={collapsed ? "Expandir menú" : "Colapsar menú"}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "22px",
            height: "22px",
            borderRadius: "4px",
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            color: "#94a3b8",
            cursor: "pointer",
          }}
        >
          {collapsed ? <ChevronRight style={{ width: "13px", height: "13px" }} /> : <ChevronLeft style={{ width: "13px", height: "13px" }} />}
        </button>
      </div>

      {/* 2. LISTA DE NAVEGACIÓN AGRUPADA */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "10px 8px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        {NAVIGATION_GROUPS.map((group, groupIdx) => (
          <div key={groupIdx}>
            {!collapsed && (
              <div
                style={{
                  fontSize: "9px",
                  fontWeight: 700,
                  color: "#475569",
                  letterSpacing: "0.8px",
                  padding: "0 8px 5px 8px",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {group.title}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              {group.items.map((item) => {
                const active = isItemActive(item);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    title={collapsed ? `${item.label} — ${item.subtitle}` : undefined}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "9px",
                      padding: collapsed ? "7px 0" : "6px 9px",
                      justifyContent: collapsed ? "center" : "flex-start",
                      borderRadius: "5px",
                      textDecoration: "none",
                      background: active ? "rgba(255, 255, 255, 0.07)" : "transparent",
                      border: active ? "1px solid rgba(255, 255, 255, 0.12)" : "1px solid transparent",
                      color: active ? "#f8fafc" : "#94a3b8",
                      transition: "all 0.1s ease",
                    }}
                  >
                    <Icon
                      style={{
                        width: "15px",
                        height: "15px",
                        color: active ? (item.accent || "#38bdf8") : "#64748b",
                        flexShrink: 0,
                      }}
                    />

                    {!collapsed && (
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div
                          style={{
                            fontSize: "11.5px",
                            fontWeight: active ? 600 : 500,
                            color: active ? "#f8fafc" : "#cbd5e1",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {item.label}
                        </div>
                      </div>
                    )}

                    {!collapsed && item.badge && (
                      <span
                        style={{
                          fontSize: "8.5px",
                          fontFamily: "var(--font-mono, monospace)",
                          fontWeight: 600,
                          padding: "1px 4px",
                          borderRadius: "3px",
                          background: active ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.04)",
                          color: active ? "#38bdf8" : "#64748b",
                          border: active ? "1px solid rgba(56, 189, 248, 0.25)" : "1px solid rgba(255, 255, 255, 0.05)",
                        }}
                      >
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

      {/* 3. PIE DE PÁGINA SOBRIO: SÓLO DOCTRINA REAL-ONLY */}
      <div
        style={{
          padding: collapsed ? "8px 0" : "8px 12px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          background: "rgba(0, 0, 0, 0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
        }}
      >
        {!collapsed ? (
          <div>
            <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              DOCTRINA
            </div>
            <div style={{ fontSize: "10px", color: "#10b981", fontWeight: 600, fontFamily: "var(--font-mono, monospace)" }}>
              ZERO-MOCKS · REAL-ONLY
            </div>
          </div>
        ) : (
          <div
            title="Zero-Mocks Real-Only"
            style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 5px #10b981" }}
          />
        )}
      </div>
    </aside>
  );
}
