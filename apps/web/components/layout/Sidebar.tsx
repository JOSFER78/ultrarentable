"use client";

/**
 * apps/web/components/layout/Sidebar.tsx
 * Reescrito 2026-09-01 (AG-11, T2 del contrato de poda web) conforme a
 * docs/19_UI_STYLE_SPEC.md §3 (Sidebar) y al plan de obra de
 * orchestration/reviews/investigacion_I5_web.md (paso 1): 8 entradas de la
 * misión FONDEO + Ultra, atenuada, siempre visible. Ningún enlace apunta a
 * una ruta puesta en cuarentena (ver cuarentena/web_poda_20260901/MOTIVO.md).
 */

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home,
  Zap,
  Database,
  ShieldCheck,
  Building2,
  Layers,
  ClipboardList,
  Radio,
  Flame,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface NavItem {
  code: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ style?: React.CSSProperties; className?: string }>;
}

/** Las 8 entradas de la misión FONDEO (decisión sellada, ver docs/19 §3). */
const NAV_ITEMS: NavItem[] = [
  { code: "HOME", label: "Inicio", href: "/", icon: Home },
  { code: "STRAT", label: "Estrategias", href: "/estrategias", icon: Zap },
  { code: "CAND", label: "Candidatos", href: "/candidatos", icon: Database },
  { code: "GATES", label: "Gates", href: "/gates", icon: ShieldCheck },
  { code: "FONDEO", label: "Fondeo", href: "/fondeo", icon: Building2 },
  { code: "PROPS", label: "Prop-firms", href: "/prop-firms", icon: Layers },
  { code: "PLAN", label: "Plan", href: "/plan", icon: ClipboardList },
  { code: "SIST", label: "Sistema", href: "/sistema", icon: Radio },
];

/** Ultra: mandato explícito de Emilio — nunca se retira, nunca se esconde. */
const ULTRA_ITEM: NavItem = { code: "ULTRA", label: "Ultra — EN CONSTRUCCIÓN", href: "/ultra", icon: Flame };

export default function Sidebar() {
  const pathname = usePathname() || "/";
  const [collapsed, setCollapsed] = useState<boolean>(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("ur_sidebar_collapsed");
      if (saved !== null) setCollapsed(saved === "true");
    } catch {
      /* localStorage no disponible (SSR/privado): se mantiene el valor por defecto */
    }
  }, []);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    try {
      localStorage.setItem("ur_sidebar_collapsed", String(next));
    } catch {
      /* noop */
    }
  };

  const isActive = (href: string): boolean => {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(href + "/");
  };

  return (
    <aside
      suppressHydrationWarning
      style={{
        width: collapsed ? "60px" : "220px",
        minWidth: collapsed ? "60px" : "220px",
        maxWidth: collapsed ? "60px" : "220px",
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

      {/* LAS 8 ENTRADAS DE LA MISIÓN */}
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
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={collapsed ? item.label : undefined}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "9px",
                padding: collapsed ? "8px 0" : "7px 9px",
                justifyContent: collapsed ? "center" : "flex-start",
                borderRadius: "6px",
                textDecoration: "none",
                background: active ? "var(--surface-3)" : "transparent",
                color: active ? "var(--text-1)" : "var(--text-2)",
                fontWeight: active ? 600 : 500,
                fontSize: "12.5px",
                transition: "background 0.1s ease, color 0.1s ease",
              }}
            >
              <Icon style={{ width: "15px", height: "15px", flexShrink: 0, color: active ? "var(--text-1)" : "var(--text-2)" }} />
              {!collapsed && <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.label}</span>}
            </Link>
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
            background: isActive(ULTRA_ITEM.href) ? "var(--surface-2)" : "transparent",
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
