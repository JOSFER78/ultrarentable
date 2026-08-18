"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useState } from "react";

interface NavItem {
  code?: string;
  label: string;
  href: string;
  badge?: string;
  isPhase?: boolean;
}

const NAV_SECTIONS: { label: string; items: NavItem[] }[] = [
  {
    label: "CENTRO DE CONTROL",
    items: [
      { code: "CC", label: "Control Center", href: "/" },
    ],
  },
  {
    label: "RUTAS DE TRADING",
    items: [
      { code: "BX", label: "ULTRA · BingX", href: "/ultra", badge: "500X" },
      { code: "FD", label: "FONDEO · Prop Firms", href: "/fondeo", badge: "CME" },
    ],
  },
  {
    label: "ESTRATEGIAS & ANÁLISIS",
    items: [
      { code: "DNA", label: "Explorador 5 Gates", href: "/strategies", badge: "GATES" },
      { code: "LB", label: "Leaderboard Canónico", href: "/leaderboard", badge: "RANK" },
      { code: "RUN", label: "Ejecución & Bots", href: "/ejecucion", badge: "LIVE" },
      { code: "PF", label: "Proveedores & Reglas", href: "/prop-firms", badge: "REGLAS" },
    ],
  },
  {
    label: "DATOS & RESEARCH",
    items: [
      { code: "DAT", label: "Catálogo de Datos", href: "/data", badge: "OHLCV" },
      { code: "RES", label: "Research Inbox", href: "/research", badge: "IDEAS" },
      { code: "SYS", label: "Sistema & Salud", href: "/sistema", badge: "8081" },
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
          className="sidebar-overlay"
          onClick={() => setMobileOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.6)",
            zIndex: 199,
            display: "none",
          }}
        />
      )}
      <button
        className="mobile-menu-btn"
        onClick={() => setMobileOpen(!mobileOpen)}
        style={{
          position: "fixed",
          top: 12,
          left: 12,
          zIndex: 300,
          display: "none",
          background: "var(--bg-panel)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          color: "var(--text-primary)",
          padding: "8px 12px",
          cursor: "pointer",
          fontSize: "12px",
          fontWeight: 700,
          letterSpacing: "1px",
        }}
      >
        MENU
      </button>

      <aside
        className={`sidebar ${collapsed ? "collapsed" : ""} ${
          mobileOpen ? "mobile-open" : ""
        }`}
      >
        <div className="sidebar-logo" onClick={() => setCollapsed(!collapsed)}>
          <div className="sidebar-logo-icon">UR</div>
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-title">ULTRARENTABLE</span>
            <span className="sidebar-logo-subtitle">AUTOMATED TRADING LAB</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_SECTIONS.map((section) => (
            <div key={section.label} style={{ marginBottom: 16 }}>
              <div
                className="nav-section-label"
                style={{
                  fontSize: "9px",
                  letterSpacing: "1px",
                  fontWeight: 800,
                  opacity: 0.6,
                  color: "var(--text-muted)",
                  marginBottom: 6,
                  paddingLeft: 8,
                }}
              >
                {section.label}
              </div>
              {section.items.map((item) => {
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href + item.label}
                    href={item.href}
                    className={`nav-item ${active ? "active" : ""}`}
                    onClick={() => setMobileOpen(false)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      padding: "7px 10px",
                      borderRadius: "4px",
                      marginBottom: 2,
                      fontSize: "12px",
                      fontWeight: item.isPhase ? 700 : 500,
                    }}
                  >
                    {item.code && (
                      <span
                        style={{
                          fontSize: "10px",
                          fontFamily: "monospace",
                          fontWeight: 800,
                          padding: "2px 5px",
                          borderRadius: "3px",
                          background: active
                            ? "var(--accent)"
                            : item.isPhase
                            ? "rgba(255, 255, 255, 0.08)"
                            : "transparent",
                          color: active ? "#000" : "var(--text-muted)",
                        }}
                      >
                        {item.code}
                      </span>
                    )}
                    <span className="nav-label" style={{ flex: 1 }}>{item.label}</span>
                    {item.badge && (
                      <span
                        className="nav-badge"
                        style={{
                          fontSize: "9px",
                          fontWeight: 700,
                          padding: "1px 5px",
                          borderRadius: "2px",
                          background: "rgba(255, 255, 255, 0.06)",
                          color: "var(--text-muted)",
                          border: "1px solid var(--border)",
                        }}
                      >
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className="status-dot" />
            <span
              className="sidebar-footer-text"
              style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}
            >
              REAL-ONLY MODE
            </span>
          </div>
          <button
            className="sidebar-collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
          >
            <span
              style={{
                transform: collapsed ? "rotate(180deg)" : "none",
                transition: "transform 200ms",
                fontSize: 10,
              }}
            >
              [&lt;]
            </span>
            <span className="sidebar-footer-text">Colapsar</span>
          </button>
        </div>
      </aside>

      <style jsx global>{`
        @media (max-width: 768px) {
          .sidebar-overlay { display: block !important; }
          .mobile-menu-btn { display: block !important; }
        }
      `}</style>
    </>
  );
}


