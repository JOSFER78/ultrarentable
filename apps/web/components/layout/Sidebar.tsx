"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
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
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Play,
  Bot,
  LineChart,
  TestTube,
  Anchor,
  Trophy,
  Boxes,
  FlaskConical,
  ClipboardList,
} from "lucide-react";

interface SubNavItem {
  label: string;
  href: string;
  code: string;
  badge?: string;
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
  subItems?: SubNavItem[];
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const NAVIGATION_GROUPS: NavGroup[] = [
  {
    title: "PLAN DEL PROYECTO",
    items: [
      {
        code: "PLAN",
        label: "Plan Maestro",
        subtitle: "Fases & Estado del Proyecto",
        href: "/plan",
        icon: ClipboardList,
        accent: "#f472b6",
      },
    ],
  },
  {
    title: "OPERACIÓN & TRADING DESKS",
    items: [
      {
        code: "FONDEO",
        label: "Trading Desk FONDEO",
        subtitle: "CME Futures & DD Estricto",
        href: "/fondeo",
        altHrefs: [
          "/fondeo",
          "/trading-desk",
          "/trading-desk/posiciones",
          "/trading-desk/estrategias",
          "/trading-desk/riesgo",
          "/trading-desk/auditoria",
          "/trading-desk/configuracion",
        ],
        icon: Building2,
        badge: "CME",
        accent: "#10b981",
        subItems: [
          { label: "Mesa Fondeo & Terminal", href: "/fondeo", code: "FND", badge: "LIVE" },
          { label: "Trading Desk DOM", href: "/trading-desk", code: "DOM" },
          { label: "Posiciones & Brackets", href: "/trading-desk/posiciones", code: "POS" },
          { label: "Sentinel de Riesgo CME", href: "/trading-desk/riesgo", code: "RSK" },
          { label: "Auditoría Forense WAL", href: "/trading-desk/auditoria", code: "AUD" },
        ],
      },
      {
        code: "ULTRA",
        label: "Trading Desk ULTRA",
        subtitle: "BingX Perps & Asimetría",
        href: "/ultra",
        altHrefs: ["/ultra"],
        icon: Flame,
        badge: "BINGX",
        accent: "#ec4899",
        subItems: [
          { label: "Mesa Ultra BingX", href: "/ultra", code: "ULT", badge: "500X" },
        ],
      },
    ],
  },
  {
    title: "STRATEGY LAB & QUANT",
    items: [
      {
        code: "STRAT",
        label: "Strategy Lab",
        subtitle: "Descubrimiento & AST",
        href: "/estrategias",
        icon: Zap,
        badge: "LAB",
        accent: "#38bdf8",
        subItems: [
          { label: "Hub de Estrategias", href: "/estrategias", code: "HUB" },
          { label: "Motor en Vivo", href: "/sistema", code: "SIS" },
          { label: "Candidatos/Excel", href: "/candidatos", code: "CAND" },
          { label: "Gates (11)", href: "/gates", code: "GATE", badge: "11/11" },
          { label: "Investigación", href: "/research", code: "RES" },
          { label: "Portfolio Studio", href: "/portfolio", code: "PORT" },
        ],
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
        subItems: [
          { label: "Matriz de 11 Gates", href: "/gates", code: "MAT" },
          { label: "1. Data Ingest", href: "/gates/gate-1-data-ingest", code: "G1" },
          { label: "2. Costes & Fricción", href: "/gates/gate-2-cost-backtest", code: "G2" },
          { label: "3. Muestra N>=20", href: "/gates/gate-3-trade-significance", code: "G3" },
          { label: "4. Walk-Forward (WFE)", href: "/gates/gate-4-walk-forward", code: "G4" },
          { label: "5. Monte Carlo 1,000x", href: "/gates/gate-5-monte-carlo", code: "G5" },
          { label: "6. Estrés Slippage 3x", href: "/gates/gate-6-stress-slippage", code: "G6" },
          { label: "7. Cobertura Regímenes", href: "/gates/gate-7-regime-coverage", code: "G7" },
          { label: "8. Deflated Sharpe DSR", href: "/gates/gate-8-dsr-ratio", code: "G8" },
          { label: "9. Novedad & AST", href: "/gates/gate-9-novelty-antifit", code: "G9" },
          { label: "10. Debate Multi-Agente", href: "/gates/gate-10-debate-agentes", code: "G10" },
          { label: "11. Nautilus Event-Driven", href: "/gates/gate-11-nautilus-event", code: "G11" },
        ],
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
    title: "ECOSISTEMA & INFORMACIÓN",
    items: [
      {
        code: "PROPS",
        label: "70 Prop Firms CME",
        subtitle: "Matriz Comparativa & Reglas",
        href: "/prop-firms",
        icon: Building2,
        badge: "70 TIERS",
        accent: "#38bdf8",
        subItems: [
          { label: "Comparador Head-to-Head", href: "/prop-firms", code: "CMP" },
          { label: "Buscador Inteligente 3-Clics", href: "/prop-firms?view=finder", code: "FND" },
          { label: "Semáforo & Matriz 70 Tiers", href: "/prop-firms?view=table", code: "TBL" },
          { label: "Calculadora ROI & Munición", href: "/prop-firms?view=roi", code: "ROI" },
          { label: "Ofertas & Descuentos", href: "/prop-firms?view=deals", code: "DLS" },
        ],
      },
      {
        code: "TSFERA",
        label: "Dossier Tradesfera",
        subtitle: "18 Módulos & Psicotrading",
        href: "/tradesfera",
        icon: BookOpen,
        badge: "18 MÓD",
        accent: "#fbbf24",
        subItems: [
          { label: "Dossier Completo", href: "/tradesfera", code: "ALL" },
        ],
      },
      {
        code: "PROV",
        label: "Conectores API/MCP",
        subtitle: "Conectores API & Tokens",
        href: "/proveedores",
        icon: SlidersHorizontal,
        badge: "MCP",
        accent: "#a855f7",
      },
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
  {
    title: "OPERACIÓN & DATOS",
    items: [
      {
        code: "EJEC",
        label: "Ejecución",
        subtitle: "Capa de Ejecución en Vivo",
        href: "/ejecucion",
        icon: Play,
        accent: "#94a3b8",
      },
      {
        code: "ROBOTS",
        label: "Robots",
        subtitle: "Seguimiento de Bots Desplegados",
        href: "/robots",
        icon: Bot,
        accent: "#94a3b8",
      },
      {
        code: "SEGUIM",
        label: "Seguimiento",
        subtitle: "Telemetría de Operación",
        href: "/seguimiento",
        icon: LineChart,
        accent: "#94a3b8",
      },
      {
        code: "CAMP",
        label: "Campañas",
        subtitle: "Campañas de Minería",
        href: "/campaigns",
        icon: GitFork,
        accent: "#94a3b8",
      },
      {
        code: "DATA",
        label: "Datos",
        subtitle: "Datasets Normalizados",
        href: "/data",
        icon: Database,
        accent: "#94a3b8",
      },
      {
        code: "BKTEST",
        label: "Backtest",
        subtitle: "Motor de Backtest Físico",
        href: "/backtest",
        icon: TestTube,
        accent: "#94a3b8",
      },
      {
        code: "NAUT",
        label: "Nautilus",
        subtitle: "Nautilus Trader Event-Driven",
        href: "/nautilus",
        icon: Anchor,
        accent: "#94a3b8",
      },
      {
        code: "LEAD",
        label: "Leaderboard",
        subtitle: "Ranking de Estrategias",
        href: "/leaderboard",
        icon: Trophy,
        accent: "#94a3b8",
      },
      {
        code: "SQX",
        label: "StrategyQuantX",
        subtitle: "Puente SQX Headless",
        href: "/strategyquant",
        icon: Boxes,
        accent: "#94a3b8",
      },
      {
        code: "RLAB",
        label: "Research Lab",
        subtitle: "Trials Evolutivos",
        href: "/research-lab",
        icon: FlaskConical,
        accent: "#94a3b8",
      },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname() || "/";
  const searchParams = useSearchParams();
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    FONDEO: true,
    ULTRA: false,
    STRAT: false,
    GATES: false,
    PROPS: false,
    TSFERA: false,
  });

  useEffect(() => {
    const saved = localStorage.getItem("ur_sidebar_collapsed");
    if (saved !== null) {
      setCollapsed(saved === "true");
    }
  }, []);

  // Auto-expand section if currently on one of its routes
  useEffect(() => {
    NAVIGATION_GROUPS.forEach((group) => {
      group.items.forEach((item) => {
        if (
          item.subItems &&
          (pathname === item.href ||
            (item.altHrefs && item.altHrefs.some((a) => pathname === a || pathname.startsWith(a + "/"))))
        ) {
          setOpenSections((prev) => ({ ...prev, [item.code]: true }));
        }
      });
    });
  }, [pathname]);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("ur_sidebar_collapsed", String(next));
  };

  const toggleSection = (code: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [code]: !prev[code],
    }));
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

  const isSubActive = (sub: SubNavItem): boolean => {
    const [subPath, subQuery] = sub.href.split("?");
    if (subQuery) {
      const currentParam = searchParams.get("view");
      const targetParam = new URLSearchParams(subQuery).get("view");
      return pathname === subPath && currentParam === targetParam;
    }
    return pathname === sub.href;
  };

  return (
    <aside
      suppressHydrationWarning
      style={{
        width: collapsed ? "64px" : "250px",
        minWidth: collapsed ? "64px" : "250px",
        maxWidth: collapsed ? "64px" : "250px",
        height: "100vh",
        background: "#070a10",
        borderRight: "1px solid rgba(255, 255, 255, 0.07)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        transition:
          "width 0.2s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.2s cubic-bezier(0.4, 0, 0.2, 1), max-width 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        position: "sticky",
        top: 0,
        zIndex: 110,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* 1. CABECERA SIDEBAR: LOGO CON ENLACE DIRECTO A PORTADA */}
      <div
        style={{
          height: "46px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "0" : "0 12px",
          borderBottom: "1px solid rgba(255, 255, 255, 0.06)",
        }}
      >
        {!collapsed ? (
          <Link
            href="/"
            title="Ir a Portada Principal (Centro de Mando)"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              textDecoration: "none",
              padding: "4px 6px",
              borderRadius: "6px",
              transition: "background 0.15s ease",
            }}
            className="hover:bg-white/5"
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
                boxShadow: "0 0 10px rgba(14, 165, 233, 0.3)",
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
            title="Ir a Portada Principal"
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

      {/* 2. LISTA DE NAVEGACIÓN AGRUPADA CON SUBPÁGINAS PLEGABLES */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "10px 8px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
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
                const hasSub = !collapsed && item.subItems && item.subItems.length > 0;
                const isSectionOpen = openSections[item.code] || active;

                return (
                  <div key={item.href} style={{ display: "flex", flexDirection: "column" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        borderRadius: "6px",
                        background: active && !hasSub ? "rgba(255, 255, 255, 0.07)" : "transparent",
                        border: active && !hasSub ? "1px solid rgba(255, 255, 255, 0.12)" : "1px solid transparent",
                        transition: "all 0.1s ease",
                      }}
                    >
                      <Link
                        href={item.href}
                        title={collapsed ? `${item.label} — ${item.subtitle}` : undefined}
                        style={{
                          flex: 1,
                          display: "flex",
                          alignItems: "center",
                          gap: "9px",
                          padding: collapsed ? "7px 0" : "6px 9px",
                          justifyContent: collapsed ? "center" : "flex-start",
                          textDecoration: "none",
                          color: active ? "#f8fafc" : "#94a3b8",
                        }}
                      >
                        <Icon
                          style={{
                            width: "15px",
                            height: "15px",
                            color: active ? item.accent || "#38bdf8" : "#64748b",
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
                      </Link>

                      {hasSub && (
                        <button
                          onClick={() => toggleSection(item.code)}
                          style={{
                            background: "transparent",
                            border: "none",
                            padding: "6px 8px",
                            color: "#64748b",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                          }}
                        >
                          <ChevronDown
                            style={{
                              width: "12px",
                              height: "12px",
                              transform: isSectionOpen ? "rotate(0deg)" : "rotate(-90deg)",
                              transition: "transform 0.15s ease",
                            }}
                          />
                        </button>
                      )}
                    </div>

                    {/* SUB-PÁGINAS PLEGABLES EN EL PANEL IZQUIERDO */}
                    {hasSub && isSectionOpen && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "1px",
                          paddingLeft: "10px",
                          marginTop: "2px",
                          marginBottom: "4px",
                          borderLeft: "1px solid rgba(255, 255, 255, 0.08)",
                          marginLeft: "16px",
                        }}
                      >
                        {item.subItems!.map((sub) => {
                          const subActive = isSubActive(sub);
                          return (
                            <Link
                              key={sub.href}
                              href={sub.href}
                              style={{
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "space-between",
                                padding: "4px 8px",
                                borderRadius: "4px",
                                fontSize: "11px",
                                textDecoration: "none",
                                background: subActive ? "rgba(56, 189, 248, 0.12)" : "transparent",
                                color: subActive ? "#38bdf8" : "#94a3b8",
                                fontWeight: subActive ? 600 : 400,
                                transition: "all 0.1s ease",
                              }}
                            >
                              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                {sub.label}
                              </span>
                              {sub.badge && (
                                <span
                                  style={{
                                    fontSize: "8.5px",
                                    padding: "1px 4px",
                                    borderRadius: "3px",
                                    background: subActive ? "rgba(56, 189, 248, 0.2)" : "rgba(255, 255, 255, 0.05)",
                                    color: subActive ? "#38bdf8" : "#64748b",
                                    fontFamily: "var(--font-mono, monospace)",
                                    fontWeight: 700,
                                  }}
                                >
                                  {sub.badge}
                                </span>
                              )}
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* 3. PIE MINIMALISTA: DOCTRINA ZERO-MOCKS */}
      <div
        style={{
          padding: collapsed ? "10px 0" : "10px 14px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          display: "flex",
          flexDirection: "column",
          alignItems: collapsed ? "center" : "flex-start",
          gap: "2px",
          background: "#05070c",
        }}
      >
        {!collapsed ? (
          <>
            <div
              style={{
                fontSize: "8.5px",
                fontWeight: 700,
                color: "#475569",
                letterSpacing: "0.5px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              DOCTRINA
            </div>
            <div
              style={{
                fontSize: "9.5px",
                fontWeight: 700,
                color: "#10b981",
                fontFamily: "var(--font-mono, monospace)",
                display: "flex",
                alignItems: "center",
                gap: "5px",
              }}
            >
              <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#10b981" }} />
              ZERO-MOCKS · REAL-ONLY
            </div>
          </>
        ) : (
          <div
            title="ZERO-MOCKS · REAL-ONLY"
            style={{
              width: "6px",
              height: "6px",
              borderRadius: "50%",
              background: "#10b981",
              boxShadow: "0 0 6px rgba(16,185,129,0.8)",
            }}
          />
        )}
      </div>
    </aside>
  );
}
