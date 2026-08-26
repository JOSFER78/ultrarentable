"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Zap,
  Database,
  ShieldCheck,
  PieChart,
  Building2,
  Award,
  FlaskConical,
  Compass,
  ChevronLeft,
  ChevronRight,
  Activity,
  BarChart3,
  Bot,
  FileText,
  ShieldAlert,
  Sliders,
  AlertOctagon,
  TrendingUp,
  Layers,
  ChevronDown,
} from "lucide-react";

export interface NavItem {
  step: string;
  code: string;
  label: string;
  subtitle: string;
  href: string;
  altHrefs: string[];
  icon: React.ReactNode;
  badge: string;
  color: string;
  highlight?: boolean;
}

const FUNNEL_ITEMS: NavItem[] = [
  {
    step: "01",
    code: "ENG",
    label: "1. Motor & Backtest 24/7",
    subtitle: "Descubrimiento & Backtest Real",
    href: "/strategies",
    altHrefs: ["/strategies", "/estrategias/1-motor-en-vivo"],
    icon: <Zap className="w-4 h-4" />,
    badge: "FASTENGINE",
    color: "#38bdf8",
    highlight: true,
  },
  {
    step: "02",
    code: "CAND",
    label: "2. Catálogo de Candidatos",
    subtitle: "Explorador Excel SQLite WAL",
    href: "/candidatos",
    altHrefs: ["/candidatos", "/estrategias/2-explorador-excel"],
    icon: <Database className="w-4 h-4" />,
    badge: "SQLITE",
    color: "#818cf8",
  },
  {
    step: "03",
    code: "GAT",
    label: "3. Pipeline 11 Gates (FSM)",
    subtitle: "11 Pruebas de Estrés Anti-Fit",
    href: "/gates",
    altHrefs: ["/gates", "/estrategias/3-pipeline-11-gates"],
    icon: <ShieldCheck className="w-4 h-4" />,
    badge: "11-GATES",
    color: "#10b981",
    highlight: true,
  },
  {
    step: "04",
    code: "PORT",
    label: "4. Portafolio Studio",
    subtitle: "Ensamblado & Paridad de Riesgo",
    href: "/portfolio",
    altHrefs: ["/portfolio", "/estrategias/6-meta-estrategia"],
    icon: <PieChart className="w-4 h-4" />,
    badge: "PORTFOLIO",
    color: "#c084fc",
  },
  {
    step: "05",
    code: "PF",
    label: "5. Catálogo 70 Prop Firms CME",
    subtitle: "Cuentas Fondeo & Descuentos",
    href: "/prop-firms",
    altHrefs: ["/prop-firms"],
    icon: <Building2 className="w-4 h-4" />,
    badge: "70 TIERS",
    color: "#f59e0b",
    highlight: true,
  },
  {
    step: "06",
    code: "DESK",
    label: "6. Trading Desk CME",
    subtitle: "Mesa de Operaciones en Vivo",
    href: "/trading-desk",
    altHrefs: [
      "/trading-desk",
      "/trading-desk/posiciones",
      "/trading-desk/estrategias",
      "/trading-desk/auditoria",
      "/trading-desk/riesgo",
      "/trading-desk/configuracion",
    ],
    icon: <Activity className="w-4 h-4" />,
    badge: "LIVE CME",
    color: "#10b981",
    highlight: true,
  },
];

const TRADING_DESK_SUBPAGES = [
  {
    label: "Terminal en Vivo & DOM",
    href: "/trading-desk",
    icon: Activity,
    badge: "DOM",
    color: "#10b981",
  },
  {
    label: "Posiciones & Brackets",
    href: "/trading-desk/posiciones",
    icon: BarChart3,
    badge: "BRACKETS",
    color: "#38bdf8",
  },
  {
    label: "Estrategias en Ejecución",
    href: "/trading-desk/estrategias",
    icon: Bot,
    badge: "11 GATES",
    color: "#c084fc",
  },
  {
    label: "Auditoría Forense",
    href: "/trading-desk/auditoria",
    icon: FileText,
    badge: "WAL",
    color: "#22d3ee",
  },
  {
    label: "Hermes Risk Sentinel",
    href: "/trading-desk/riesgo",
    icon: ShieldAlert,
    badge: "DD GUARD",
    color: "#f43f5e",
  },
  {
    label: "Conexión Broker & API",
    href: "/trading-desk/configuracion",
    icon: Sliders,
    badge: "CONFIG",
    color: "#f59e0b",
  },
];

const SECONDARY_ITEMS: NavItem[] = [
  {
    step: "HUB",
    code: "HUB",
    label: "Guía Visual & Portada",
    subtitle: "Centro de Mando 6 Pasos",
    href: "/estrategias",
    altHrefs: ["/estrategias", "/"],
    icon: <Compass className="w-4 h-4" />,
    badge: "GUÍA",
    color: "#38bdf8",
  },
  {
    step: "LED",
    code: "LED",
    label: "Estrategias Aprobadas (11/11)",
    subtitle: "Bóveda TIER 1 Producción",
    href: "/estrategias/5-estrategias-aprobadas",
    altHrefs: ["/estrategias/5-estrategias-aprobadas"],
    icon: <Award className="w-4 h-4" />,
    badge: "TIER 1",
    color: "#10b981",
  },
  {
    step: "LAB",
    code: "LAB",
    label: "Panel Investigador I+D",
    subtitle: "Incubadora de Fallos & AST",
    href: "/estrategias/4-panel-investigador",
    altHrefs: ["/estrategias/4-panel-investigador", "/research"],
    icon: <FlaskConical className="w-4 h-4" />,
    badge: "LAB I+D",
    color: "#a855f7",
  },
  {
    step: "SYS",
    code: "SYS",
    label: "Telemetría & Pulso 24/7",
    subtitle: "SystemSupervisor & Workers",
    href: "/sistema",
    altHrefs: ["/sistema"],
    icon: <Activity className="w-4 h-4" />,
    badge: "24/7 LIVE",
    color: "#10b981",
    highlight: true,
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [mounted, setMounted] = useState<boolean>(false);
  const [isFlattenModalOpen, setIsFlattenModalOpen] = useState<boolean>(false);
  const [isFlattening, setIsFlattening] = useState<boolean>(false);

  const [accountStatus, setAccountStatus] = useState({
    account_id: "DEMO1279346",
    broker: "Tradovate Demo",
    base_capital_usd: 50000.0,
    daily_pnl_usd: 0.0,
    open_positions_count: 0,
    last_ping_latency_ms: 68.4,
  });

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/status");
      if (res.ok) {
        const data = await res.json();
        setAccountStatus(data);
      }
    } catch {}
  }, []);

  useEffect(() => {
    setMounted(true);
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    try {
      const saved = localStorage.getItem("ur_sidebar_collapsed");
      if (saved !== null) {
        setCollapsed(saved === "true");
      }
    } catch {}
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    try {
      localStorage.setItem("ur_sidebar_collapsed", String(next));
    } catch {}
  };

  const isItemActive = (item: NavItem): boolean => {
    if (!pathname) return false;
    if (pathname === item.href) return true;
    return item.altHrefs.some((alt) => pathname === alt || (alt !== "/" && pathname.startsWith(alt + "/")));
  };

  const isTradingDeskActive = pathname?.startsWith("/trading-desk");

  const handleExecuteFlatten = async () => {
    setIsFlattening(true);
    try {
      await fetch("/api/v1/gateways/pickmytrade/flatten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: "ALL",
          account: accountStatus.account_id,
          token: "3VxOjkjylyJKkt3oN4Jydg",
          reason: "SIDEBAR_KILL_SWITCH",
        }),
      });
      fetchStatus();
    } catch {}
    finally {
      setIsFlattening(false);
      setIsFlattenModalOpen(false);
    }
  };

  const sidebarWidth = mounted && collapsed ? "68px" : "268px";

  return (
    <aside
      suppressHydrationWarning
      style={{
        width: sidebarWidth,
        minWidth: sidebarWidth,
        height: "100vh",
        background: "rgba(8, 12, 20, 0.98)",
        backdropFilter: "blur(24px)",
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
      {/* 1. BRAND & COLLAPSE HEADER */}
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
          href="/estrategias"
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
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #10b981 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: "13px",
              color: "#040812",
              fontFamily: "var(--font-mono, monospace)",
              boxShadow: "0 0 16px rgba(16, 185, 129, 0.35)",
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
                  letterSpacing: "0.75px",
                  whiteSpace: "nowrap",
                }}
              >
                ULTRARENTABLE
              </span>
              <span
                style={{
                  fontSize: "8.5px",
                  color: "#10b981",
                  fontWeight: 800,
                  letterSpacing: "0.8px",
                  fontFamily: "var(--font-mono, monospace)",
                  whiteSpace: "nowrap",
                }}
              >
                QUANT LAB · v5.4.0 (REAL-ONLY)
              </span>
            </div>
          )}
        </Link>

        {!collapsed && (
          <button
            onClick={toggleCollapse}
            title="Plegar barra lateral"
            aria-label="Plegar barra lateral"
            style={{
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "6px",
              color: "#94a3b8",
              width: "26px",
              height: "26px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
            }}
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* 2. NAVIGATION SCROLL AREA */}
      <nav
        style={{
          flex: 1,
          padding: collapsed ? "12px 6px" : "12px 8px",
          overflowY: "auto",
          overflowX: "hidden",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {/* EL EMBUDO CUANTITATIVO (6 PASOS INCLUYENDO TRADING DESK) */}
        <div>
          {!collapsed && (
            <div
              style={{
                fontSize: "9px",
                fontWeight: 800,
                color: "#64748b",
                letterSpacing: "1px",
                padding: "0 8px",
                marginBottom: "6px",
                fontFamily: "var(--font-mono, monospace)",
                textTransform: "uppercase",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <span>EMBUDO CUANTITATIVO</span>
              <span style={{ color: "#10b981", background: "rgba(16, 185, 129, 0.12)", padding: "1px 5px", borderRadius: "3px" }}>
                6 PASOS
              </span>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            {FUNNEL_ITEMS.map((item) => {
              const active = isItemActive(item);
              const isDesk = item.step === "06";

              return (
                <div key={item.step} style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                  <Link
                    href={item.href}
                    title={collapsed ? `${item.label} [${item.badge}]` : item.subtitle}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "9px",
                      padding: collapsed ? "9px 0" : "8px 9px",
                      justifyContent: collapsed ? "center" : "flex-start",
                      borderRadius: "8px",
                      background: active
                        ? `linear-gradient(135deg, ${item.color}1c 0%, rgba(15, 23, 42, 0.85) 100%)`
                        : "transparent",
                      border: active
                        ? `1px solid ${item.color}55`
                        : "1px solid transparent",
                      textDecoration: "none",
                      transition: "all 0.12s ease",
                      position: "relative",
                    }}
                  >
                    <div
                      style={{
                        width: collapsed ? "32px" : "26px",
                        height: "26px",
                        borderRadius: "6px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "10.5px",
                        fontWeight: 800,
                        fontFamily: "var(--font-mono, monospace)",
                        background: active
                          ? item.color
                          : "rgba(255, 255, 255, 0.05)",
                        color: active
                          ? "#040812"
                          : item.highlight
                          ? item.color
                          : "#94a3b8",
                        border: active
                          ? "none"
                          : `1px solid ${item.highlight ? `${item.color}40` : "rgba(255, 255, 255, 0.06)"}`,
                        flexShrink: 0,
                      }}
                    >
                      {collapsed ? item.icon : item.step}
                    </div>

                    {!collapsed && (
                      <>
                        <div style={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0, overflow: "hidden" }}>
                          <span
                            style={{
                              fontSize: "11.5px",
                              fontWeight: active ? 700 : 500,
                              color: active ? "#ffffff" : "#cbd5e1",
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {item.label}
                          </span>
                          <span
                            style={{
                              fontSize: "8.5px",
                              color: active ? "#94a3b8" : "#64748b",
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                            }}
                          >
                            {item.subtitle}
                          </span>
                        </div>

                        {item.badge && (
                          <span
                            style={{
                              fontSize: "8.5px",
                              fontWeight: 800,
                              padding: "2px 5px",
                              borderRadius: "4px",
                              background: active ? `${item.color}28` : "rgba(255, 255, 255, 0.05)",
                              color: active ? item.color : "#64748b",
                              fontFamily: "var(--font-mono, monospace)",
                              border: `1px solid ${active ? `${item.color}50` : "rgba(255, 255, 255, 0.06)"}`,
                              flexShrink: 0,
                            }}
                          >
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}
                  </Link>

                  {/* SUBMENÚ EXPANDIDO DEL TRADING DESK EN EL MENÚ EXISTENTE */}
                  {isDesk && isTradingDeskActive && !collapsed && (
                    <div
                      style={{
                        marginLeft: "18px",
                        paddingLeft: "10px",
                        borderLeft: "2px solid rgba(16, 185, 129, 0.3)",
                        display: "flex",
                        flexDirection: "column",
                        gap: "2px",
                        marginTop: "2px",
                        marginBottom: "4px",
                      }}
                    >
                      {TRADING_DESK_SUBPAGES.map((sub) => {
                        const isSubActive = pathname === sub.href;
                        const SubIcon = sub.icon;

                        return (
                          <Link
                            key={sub.href}
                            href={sub.href}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              padding: "5px 8px",
                              borderRadius: "6px",
                              textDecoration: "none",
                              fontSize: "11px",
                              fontWeight: isSubActive ? 700 : 500,
                              color: isSubActive ? "#ffffff" : "#94a3b8",
                              background: isSubActive ? "rgba(16, 185, 129, 0.15)" : "transparent",
                              border: isSubActive ? "1px solid rgba(16, 185, 129, 0.3)" : "1px solid transparent",
                              transition: "all 0.1s ease",
                            }}
                            className="hover:text-white hover:bg-slate-800/50"
                          >
                            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                              <SubIcon style={{ width: "13px", height: "13px", color: isSubActive ? sub.color : "#64748b" }} />
                              <span style={{ whiteSpace: "nowrap" }}>{sub.label}</span>
                            </div>
                            <span
                              style={{
                                fontSize: "8px",
                                fontFamily: "var(--font-mono, monospace)",
                                color: isSubActive ? sub.color : "#64748b",
                                fontWeight: 800,
                              }}
                            >
                              {sub.badge}
                            </span>
                          </Link>
                        );
                      })}

                      {/* EMERGENCY FLATTEN BUTTON IN SIDEBAR */}
                      <button
                        onClick={() => setIsFlattenModalOpen(true)}
                        style={{
                          marginTop: "4px",
                          padding: "5px 8px",
                          borderRadius: "6px",
                          background: "rgba(220, 38, 38, 0.2)",
                          border: "1px solid rgba(239, 68, 68, 0.4)",
                          color: "#f87171",
                          fontSize: "10.5px",
                          fontWeight: 800,
                          fontFamily: "var(--font-mono, monospace)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          gap: "5px",
                          cursor: "pointer",
                        }}
                        className="hover:bg-red-600 hover:text-white transition"
                      >
                        <AlertOctagon style={{ width: "12px", height: "12px" }} />
                        <span>FLATTEN ALL</span>
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* VALIDACIÓN & HERRAMIENTAS ADICIONALES */}
        <div>
          {!collapsed && (
            <div
              style={{
                fontSize: "9px",
                fontWeight: 800,
                color: "#64748b",
                letterSpacing: "1px",
                padding: "0 8px",
                marginBottom: "6px",
                fontFamily: "var(--font-mono, monospace)",
                textTransform: "uppercase",
              }}
            >
              MÓDULOS DE SOPORTE
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            {SECONDARY_ITEMS.map((item) => {
              const active = isItemActive(item);
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  title={collapsed ? `${item.label} [${item.badge}]` : item.subtitle}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "9px",
                    padding: collapsed ? "9px 0" : "7px 9px",
                    justifyContent: collapsed ? "center" : "flex-start",
                    borderRadius: "8px",
                    background: active
                      ? `linear-gradient(135deg, ${item.color}18 0%, rgba(15, 23, 42, 0.8) 100%)`
                      : "transparent",
                    border: active
                      ? `1px solid ${item.color}44`
                      : "1px solid transparent",
                    textDecoration: "none",
                    transition: "all 0.12s ease",
                  }}
                >
                  <div
                    style={{
                      width: collapsed ? "32px" : "26px",
                      height: "26px",
                      borderRadius: "6px",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      background: active ? `${item.color}25` : "rgba(255, 255, 255, 0.04)",
                      color: active ? item.color : "#94a3b8",
                      border: `1px solid ${active ? `${item.color}50` : "rgba(255, 255, 255, 0.06)"}`,
                      flexShrink: 0,
                    }}
                  >
                    {item.icon}
                  </div>

                  {!collapsed && (
                    <>
                      <div style={{ display: "flex", flexDirection: "column", flex: 1, minWidth: 0, overflow: "hidden" }}>
                        <span
                          style={{
                            fontSize: "11.5px",
                            fontWeight: active ? 700 : 500,
                            color: active ? "#ffffff" : "#cbd5e1",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {item.label}
                        </span>
                        <span
                          style={{
                            fontSize: "8.5px",
                            color: active ? "#94a3b8" : "#64748b",
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {item.subtitle}
                        </span>
                      </div>

                      {item.badge && (
                        <span
                          style={{
                            fontSize: "8.5px",
                            fontWeight: 800,
                            padding: "2px 5px",
                            borderRadius: "4px",
                            background: active ? `${item.color}25` : "rgba(255, 255, 255, 0.05)",
                            color: active ? item.color : "#64748b",
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
      </nav>

      {/* 3. FOOTER STATUS BAR */}
      <div
        style={{
          padding: collapsed ? "10px 6px" : "10px 12px",
          borderTop: "1px solid rgba(255, 255, 255, 0.08)",
          background: "rgba(4, 8, 16, 0.6)",
          flexShrink: 0,
        }}
      >
        {collapsed ? (
          <button
            onClick={toggleCollapse}
            title="Expandir menú lateral"
            aria-label="Expandir menú lateral"
            style={{
              width: "100%",
              height: "30px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(255, 255, 255, 0.04)",
              borderRadius: "6px",
              color: "#94a3b8",
              cursor: "pointer",
            }}
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyItems: "space-between", justifyContent: "space-between" }}>
              <span
                style={{
                  fontSize: "8.5px",
                  fontWeight: 800,
                  fontFamily: "var(--font-mono, monospace)",
                  color: "#64748b",
                  letterSpacing: "0.5px",
                }}
              >
                DOCTRINA
              </span>
              <span
                style={{
                  fontSize: "8.5px",
                  fontWeight: 800,
                  fontFamily: "var(--font-mono, monospace)",
                  color: "#10b981",
                  background: "rgba(16, 185, 129, 0.12)",
                  padding: "1px 5px",
                  borderRadius: "3px",
                  border: "1px solid rgba(16, 185, 129, 0.25)",
                }}
              >
                ZERO-MOCKS
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "1px" }}>
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "#10b981",
                  boxShadow: "0 0 6px #10b981",
                  flexShrink: 0,
                }}
              />
              <span
                style={{
                  fontSize: "9px",
                  color: "#94a3b8",
                  fontFamily: "var(--font-mono, monospace)",
                  whiteSpace: "nowrap",
                }}
              >
                SQLite WAL · v5.4.0
              </span>
            </div>
          </div>
        )}
      </div>

      {/* FLATTEN MODAL */}
      {isFlattenModalOpen && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", zIndex: 9999, display: "flex", alignItems: "center", justifyContent: "center", padding: "16px" }}>
          <div style={{ background: "#0b111e", border: "2px solid #ef4444", borderRadius: "16px", padding: "20px", maxWidth: "400px", width: "100%", color: "#fff" }}>
            <h3 style={{ fontWeight: 900, fontSize: "16px", color: "#ef4444", marginBottom: "8px" }}>¿CONFIRMAR FLATTEN TOTAL?</h3>
            <p style={{ fontSize: "12px", color: "#cbd5e1", marginBottom: "16px" }}>Se enviará una orden de liquidación a mercado para todas las posiciones abiertas en Tradovate Demo.</p>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
              <button onClick={() => setIsFlattenModalOpen(false)} style={{ padding: "8px 14px", borderRadius: "8px", background: "#1e293b", color: "#cbd5e1", fontSize: "12px", fontWeight: 700 }}>Cancelar</button>
              <button onClick={handleExecuteFlatten} disabled={isFlattening} style={{ padding: "8px 14px", borderRadius: "8px", background: "#ef4444", color: "#fff", fontSize: "12px", fontWeight: 900 }}>
                {isFlattening ? "Liquidando..." : "SÍ, LIQUIDAR"}
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
