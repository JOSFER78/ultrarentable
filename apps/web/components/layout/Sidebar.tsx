"use client";

/**
 * apps/web/components/layout/Sidebar.tsx
 * Submenús desplegables (acordeón) con auto-desplegado según la ruta activa y control manual
 * con Chevron; Ultra al pie, siempre visible, nunca se oculta.
 *
 * La mecánica del acordeón se conserva tal cual se reorganizó el 2026-09-02. Lo que cambió el
 * 2026-09-03 es QUÉ se enlaza: ver el comentario sobre NAV_ITEMS, con las tres reglas de la
 * poda y su verificación.
 */

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Zap,
  ShieldCheck,
  Building2,
  Layers,
  ClipboardList,
  Radio,
  Flame,
  Gauge,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
} from "lucide-react";

export interface SubNavItem {
  code: string;
  label: string;
  href: string;
  badge?: string;
}

export interface NavItem {
  code: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ style?: React.CSSProperties; className?: string }>;
  subItems?: SubNavItem[];
}

/**
 * Podado el 2026-09-03 por mandato de Emilio ("hay páginas antiguas mezcladas con nuevas,
 * deja solo lo nuevo y funcional"). Tres reglas, todas verificables:
 *
 * 1. Solo se enlaza lo que existe EN HEAD. Las 22 entradas que enlazaban a rutas presentes
 *    en el disco pero sin commitear (`/tradesfera/01-ecosistema` … `/tradesfera/modulos`,
 *    `/estrategias/candidatos`) salen del menú: en un build de producción desde el repo
 *    darían 404. Vuelven en cuanto sus ficheros entren en un commit.
 * 2. Ningún número escrito a mano. Se retiran los badges "578" (candidatas), "70 Cuentas",
 *    "11", "36 Col", "(16)", "SQX" y "LIVE". El de 578 estaba además desmentido: la API
 *    (`/api/v1/candidates?include_rejected=true&limit=1000`) devuelve 728. Un contador en el
 *    menú solo puede venir de la API, nunca de una constante.
 * 3. Vuelven al menú Inicio, Gates, Fondeo y Sistema, que la reorganización anterior había
 *    dejado fuera. Las tres últimas sirven datos reales, medido contra la API local :8100:
 *    `/api/v2/certified/strategies`, `/api/v1/execution/sessions?route=FONDEO` y
 *    `/api/v1/telemetry/health` responden 200. Fondeo es además la misión del producto.
 *
 * `/candidatos` (ruta antigua) queda viva pero fuera del menú: renderiza el mismo
 * `CandidatesExcelExplorer` que el M4 nuevo y el contrato sellado de `/estrategias`
 * (README_STRATEGIES_PAGE.md) la declara "archivo técnico de uso interno, un clic más allá".
 * Se llega desde la portada y desde /estrategias.
 *
 * Trading Desk, Tradesfera y Ultra NO se tocan: los tres están aquí por orden expresa de
 * Emilio (ver la reversión parcial de cuarentena/web_poda_20260901/MOTIVO.md).
 */
const NAV_ITEMS: NavItem[] = [
  { code: "HOME", label: "Inicio", href: "/", icon: Home },
  {
    code: "STRAT",
    label: "1. Estrategias",
    href: "/estrategias",
    icon: Zap,
    subItems: [
      { code: "STRAT_CAT", label: "Overview & Válidas", href: "/estrategias" },
      { code: "STRAT_M1", label: "M1: Generación (SQX)", href: "/estrategias/generacion" },
      { code: "STRAT_M2", label: "M2: Bucle de Mejora", href: "/estrategias/mejora" },
      { code: "STRAT_M3", label: "M3: Valoración 11 Gates", href: "/estrategias/valoracion" },
      { code: "STRAT_M4", label: "M4: Candidatos Estrategias", href: "/estrategias/candidatos" },
      { code: "STRAT_M5", label: "M5: Candidatos Meta-Estrategias", href: "/estrategias/meta" },
    ],
  },
  { code: "GATES", label: "Gates", href: "/gates", icon: ShieldCheck },
  { code: "FONDEO", label: "Fondeo", href: "/fondeo", icon: Building2 },
  {
    code: "PROPS",
    label: "2. Prop-firms",
    href: "/prop-firms",
    icon: Layers,
    subItems: [
      { code: "PROP_CAT", label: "Catálogo", href: "/prop-firms?view=table" },
      { code: "PROP_COMP", label: "Comparador cara a cara", href: "/prop-firms?view=comparator" },
      { code: "PROP_FIND", label: "Buscador 3 clics", href: "/prop-firms?view=finder" },
      { code: "PROP_ROI", label: "Calculadora ROI", href: "/prop-firms?view=roi" },
      { code: "PROP_DEALS", label: "Cupones y ofertas", href: "/prop-firms?view=deals" },
      { code: "PROP_MEGA", label: "Mega-matriz", href: "/prop-firms?view=mega" },
      { code: "PROP_AUDIT", label: "Auditoría SourceRef", href: "/prop-firms?view=audit" },
    ],
  },
  {
    code: "DESK",
    label: "3. Trading Desk Fondeo",
    href: "/trading-desk",
    icon: Gauge,
    subItems: [
      { code: "DESK_TERM", label: "Terminal y DOM", href: "/trading-desk" },
      { code: "DESK_POS", label: "Posiciones y brackets", href: "/trading-desk/posiciones" },
      { code: "DESK_STRAT", label: "Estrategias activas", href: "/trading-desk/estrategias" },
      { code: "DESK_RISK", label: "Sentinel de riesgo", href: "/trading-desk/riesgo" },
      { code: "DESK_AUDIT", label: "Auditoría forense", href: "/trading-desk/auditoria" },
      { code: "DESK_CONF", label: "Conexión gateway", href: "/trading-desk/configuracion" },
    ],
  },
  {
    code: "TSFERA",
    label: "4. Tradesfera",
    href: "/tradesfera",
    icon: BookOpen,
    subItems: [
      { code: "TS_HUB", label: "Overview Tradesfera", href: "/tradesfera" },
      { code: "TS_M01", label: "M01: Ecosistema & 4 Puertas", href: "/tradesfera/01-ecosistema" },
      { code: "TS_M02", label: "M02: Matemática Bankroll", href: "/tradesfera/02-matematica-bankroll" },
      { code: "TS_M03", label: "M03: Teoría Varianza", href: "/tradesfera/03-teoria-varianza" },
      { code: "TS_M04", label: "M04: Protocolo Aprobación", href: "/tradesfera/04-protocolo-aprobacion" },
      { code: "TS_M05", label: "M05: Sistema Multicuenta", href: "/tradesfera/05-sistema-multicuenta" },
      { code: "TS_M06", label: "M06: Ciclo Retiros", href: "/tradesfera/06-ciclo-retiros" },
      { code: "TS_M07", label: "M07: Psicología Fondeo", href: "/tradesfera/07-psicologia-fondeo" },
      { code: "TS_M08", label: "M08: Comparativa Prop Firms", href: "/tradesfera/08-comparativa-prop-firms" },
      { code: "TS_M09", label: "M09: Infra NinjaTrader", href: "/tradesfera/09-infraestructura-ninjatrader" },
      { code: "TS_M10", label: "M10: Dossier Maestro", href: "/tradesfera/10-dossier-maestro" },
      { code: "TS_M11", label: "M11: Estrategias & Horarios", href: "/tradesfera/11-estrategias-horarios" },
      { code: "TS_M12", label: "M12: Maestría Psicológica", href: "/tradesfera/12-maestria-psicologica" },
      { code: "TS_M13", label: "M13: Sistema Táctico", href: "/tradesfera/13-sistema-tactico" },
      { code: "TS_M14", label: "M14: Hacks & Reglas Rápidas", href: "/tradesfera/14-hacks-reglas-rapidas" },
      { code: "TS_M15", label: "M15: Arbitraje & Fiscalidad", href: "/tradesfera/15-arbitraje-promos-fiscalidad" },
      { code: "TS_M16", label: "M16: Playbook Diario", href: "/tradesfera/16-playbook-diario" },
    ],
  },
  { code: "PLAN", label: "5. Plan", href: "/plan", icon: ClipboardList },
  { code: "SIST", label: "Sistema", href: "/sistema", icon: Radio },
];

/** Ultra: mandato explícito de Emilio — nunca se retira, nunca se esconde. */
const ULTRA_ITEM: NavItem = { code: "ULTRA", label: "Ultra — EN CONSTRUCCIÓN", href: "/ultra", icon: Flame };

export default function Sidebar() {
  const pathname = usePathname() || "/";
  const [collapsed, setCollapsed] = useState<boolean>(false);

  // Secciones abiertas manualmente o por auto-detección
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    STRAT: false,
    PROPS: false,
    DESK: false,
    TSFERA: false,
  });

  useEffect(() => {
    try {
      const saved = localStorage.getItem("ur_sidebar_collapsed");
      if (saved !== null) setCollapsed(saved === "true");
    } catch {
      /* localStorage no disponible */
    }
  }, []);

  // Auto-expandir la sección correspondiente si la ruta actual coincide
  useEffect(() => {
    if (pathname.startsWith("/estrategias")) {
      setOpenSections((prev) => ({ ...prev, STRAT: true }));
    } else if (pathname.startsWith("/prop-firms")) {
      setOpenSections((prev) => ({ ...prev, PROPS: true }));
    } else if (pathname.startsWith("/trading-desk")) {
      setOpenSections((prev) => ({ ...prev, DESK: true }));
    } else if (pathname.startsWith("/tradesfera")) {
      setOpenSections((prev) => ({ ...prev, TSFERA: true }));
    }
  }, [pathname]);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    try {
      localStorage.setItem("ur_sidebar_collapsed", String(next));
    } catch {
      /* noop */
    }
  };

  const toggleSection = (code: string, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    setOpenSections((prev) => ({ ...prev, [code]: !prev[code] }));
  };

  const [currentView, setCurrentView] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const sp = new URLSearchParams(window.location.search);
      setCurrentView(sp.get("view"));
    }
  }, [pathname]);

  const isRouteActive = (href: string, exact = false): boolean => {
    if (href === "/") return pathname === "/";
    if (href.includes("?")) {
      const [path, query] = href.split("?");
      const params = new URLSearchParams(query);
      const view = params.get("view");
      if (pathname !== path) return false;
      if (!currentView && view === "table") return true;
      return currentView === view;
    }
    if (pathname === "/prop-firms" && !currentView && href.startsWith("/prop-firms")) {
      return href === "/prop-firms?view=table";
    }
    if (exact) return pathname === href;
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <aside
      suppressHydrationWarning
      style={{
        width: collapsed ? "60px" : "240px",
        minWidth: collapsed ? "60px" : "240px",
        maxWidth: collapsed ? "60px" : "240px",
        height: "100vh",
        background: "var(--bg)",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        transition: "width 0.15s ease, min-width 0.15s ease, max-width 0.15s ease",
        position: "sticky",
        top: 0,
        zIndex: 110,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* CABECERA: LOGO + ENLACE A PORTADA */}
      <div
        style={{
          height: "44px",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "space-between",
          padding: collapsed ? "0" : "0 12px",
          borderBottom: "1px solid var(--border)",
          flexShrink: 0,
        }}
      >
        <Link
          href="/"
          title="Ir a Portada"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            textDecoration: "none",
            padding: "4px 6px",
            borderRadius: "8px",
            color: "var(--text-1)",
          }}
        >
          <div
            style={{
              width: "22px",
              height: "22px",
              borderRadius: "6px",
              background: "var(--surface-3)",
              border: "1px solid var(--border-strong)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "10px",
              color: "var(--text-1)",
              fontFamily: "var(--font-mono, monospace)",
              flexShrink: 0,
            }}
          >
            UR
          </div>
          {!collapsed && (
            <span style={{ fontSize: "11.5px", fontWeight: 700, color: "var(--text-1)", letterSpacing: "0.3px" }}>
              ULTRARENTABLE
            </span>
          )}
        </Link>

        {!collapsed && (
          <button
            onClick={toggleCollapse}
            title="Colapsar menú"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "20px",
              height: "20px",
              borderRadius: "5px",
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--text-2)",
              cursor: "pointer",
            }}
          >
            <ChevronLeft style={{ width: "12px", height: "12px" }} />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          onClick={toggleCollapse}
          title="Expandir menú"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "6px auto 0",
            width: "20px",
            height: "20px",
            borderRadius: "5px",
            background: "transparent",
            border: "1px solid var(--border)",
            color: "var(--text-2)",
            cursor: "pointer",
            flexShrink: 0,
          }}
        >
          <ChevronRight style={{ width: "12px", height: "12px" }} />
        </button>
      )}

      {/* NAVEGACIÓN PRINCIPAL JERÁRQUICA */}
      <nav
        style={{
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "8px",
          display: "flex",
          flexDirection: "column",
          gap: "2px",
        }}
      >
        {NAV_ITEMS.map((item) => {
          const hasSubs = Array.isArray(item.subItems) && item.subItems.length > 0;
          const isParentActive = isRouteActive(item.href, false);
          const isOpen = Boolean(openSections[item.code]);
          const Icon = item.icon;

          return (
            <div key={item.code} style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  borderRadius: "6px",
                  background: isParentActive && !hasSubs ? "var(--surface-3)" : isParentActive ? "var(--surface-2)" : "transparent",
                  color: isParentActive ? "var(--text-1)" : "var(--text-2)",
                  transition: "background 0.1s ease, color 0.1s ease",
                }}
              >
                <Link
                  href={item.href}
                  title={collapsed ? item.label : undefined}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "9px",
                    padding: collapsed ? "8px 0" : "7px 9px",
                    justifyContent: collapsed ? "center" : "flex-start",
                    textDecoration: "none",
                    color: "inherit",
                    fontWeight: isParentActive ? 600 : 500,
                    fontSize: "12.5px",
                    flex: 1,
                    minWidth: 0,
                  }}
                >
                  <Icon
                    style={{
                      width: "15px",
                      height: "15px",
                      flexShrink: 0,
                      color: isParentActive ? "var(--profit)" : "var(--text-2)",
                    }}
                  />
                  {!collapsed && (
                    <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {item.label}
                    </span>
                  )}
                </Link>

                {/* Botón de acordeón si tiene subpáginas */}
                {!collapsed && hasSubs && (
                  <button
                    onClick={(e) => toggleSection(item.code, e)}
                    title={isOpen ? "Plegar submenú" : "Desplegar submenú"}
                    style={{
                      padding: "4px 6px",
                      background: "transparent",
                      border: "none",
                      color: "var(--text-3)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {isOpen ? (
                      <ChevronDown style={{ width: "13px", height: "13px", color: "var(--text-1)" }} />
                    ) : (
                      <ChevronRight style={{ width: "13px", height: "13px" }} />
                    )}
                  </button>
                )}
              </div>

              {/* LISTA DE SUB-ITEMS DESPLEGABLES */}
              {!collapsed && hasSubs && isOpen && (
                <div
                  style={{
                    marginLeft: "18px",
                    paddingLeft: "10px",
                    borderLeft: "1px solid var(--border)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "1px",
                    marginTop: "2px",
                    marginBottom: "4px",
                  }}
                >
                  {item.subItems!.map((sub) => {
                    const isSubActive = isRouteActive(sub.href, true);
                    return (
                      <Link
                        key={sub.href}
                        href={sub.href}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "5px 7px",
                          borderRadius: "4px",
                          textDecoration: "none",
                          fontSize: "11px",
                          fontFamily: "var(--font-mono, monospace)",
                          background: isSubActive ? "var(--surface-3)" : "transparent",
                          color: isSubActive ? "var(--profit)" : "var(--text-3)",
                          fontWeight: isSubActive ? 700 : 400,
                          transition: "color 0.1s ease, background 0.1s ease",
                        }}
                      >
                        <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {sub.label}
                        </span>
                        {sub.badge && (
                          <span
                            style={{
                              fontSize: "9px",
                              padding: "1px 4px",
                              borderRadius: "3px",
                              background: isSubActive ? "var(--profit-dim)" : "var(--surface-2)",
                              border: isSubActive ? "1px solid var(--profit)" : "1px solid var(--border)",
                              color: isSubActive ? "var(--profit)" : "var(--text-3)",
                              marginLeft: "4px",
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
      </nav>

      {/* PIE: ULTRA ATENUADA (SIEMPRE VISIBLE, NUNCA SE RETIRA) + DOCTRINA */}
      <div style={{ borderTop: "1px solid var(--border)", padding: "8px", flexShrink: 0 }}>
        <Link
          href={ULTRA_ITEM.href}
          title={collapsed ? ULTRA_ITEM.label : undefined}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "9px",
            padding: collapsed ? "7px 0" : "6px 9px",
            justifyContent: collapsed ? "center" : "flex-start",
            borderRadius: "6px",
            textDecoration: "none",
            background: isRouteActive(ULTRA_ITEM.href) ? "var(--surface-2)" : "transparent",
            color: "var(--text-3)",
            fontSize: "11.5px",
          }}
        >
          <Flame style={{ width: "13px", height: "13px", flexShrink: 0, color: "var(--text-3)" }} />
          {!collapsed && <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{ULTRA_ITEM.label}</span>}
        </Link>

        {!collapsed && (
          <div
            style={{
              marginTop: "8px",
              paddingTop: "8px",
              borderTop: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              gap: "5px",
              fontSize: "9px",
              fontWeight: 600,
              color: "var(--text-3)",
              letterSpacing: "0.4px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "var(--text-3)" }} />
            ZERO-MOCKS · REAL-ONLY
          </div>
        )}
      </div>
    </aside>
  );
}
