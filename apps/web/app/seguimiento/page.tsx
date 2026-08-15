"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface AuditEvent {
  event_id: string;
  category: string;
  route: string;
  title: string;
  description: string;
  severity: "INFO" | "WARNING" | "CRITICAL" | "SUCCESS";
  created_at: string;
}

export default function SeguimientoPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [filterRoute, setFilterRoute] = useState<string>("ALL");

  useEffect(() => {
    fetch("/api/v1/audit/events")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setEvents(data);
      })
      .catch((err) => console.error("Error loading audit events:", err));
  }, []);

  const filtered = events.filter((e) => {
    if (filterRoute !== "ALL" && e.route !== filterRoute) return false;
    return true;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return { bg: "rgba(239, 68, 68, 0.2)", color: "#fca5a5", border: "1px solid #ef4444" };
      case "WARNING":
        return { bg: "rgba(245, 158, 11, 0.2)", color: "#fde68a", border: "1px solid #f59e0b" };
      case "SUCCESS":
        return { bg: "rgba(34, 197, 94, 0.2)", color: "#86efac", border: "1px solid #22c55e" };
      default:
        return { bg: "rgba(96, 165, 250, 0.2)", color: "#93c5fd", border: "1px solid #3b82f6" };
    }
  };

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", fontFamily: "monospace" }}>
              TIMELINE DE SEGUIMIENTO
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
            📜 Registro de Auditoría y Eventos del Sistema
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Historial inmutable de creación de campañas, reclasificación de gates, exportaciones y disparos de Kill-Switch.
          </p>
        </div>

        <select
          value={filterRoute}
          onChange={(e) => setFilterRoute(e.target.value)}
          style={{ padding: "8px 12px", background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: "6px", color: "var(--text-primary)", fontSize: "12px", fontWeight: 700 }}
        >
          <option value="ALL">Todas las Rutas</option>
          <option value="ULTRA">Ruta ULTRA (BingX)</option>
          <option value="FONDEO">Ruta FONDEO (Prop Firms)</option>
          <option value="SYSTEM">Sistema Global</option>
        </select>
      </div>

      {/* TIMELINE VIEW */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {filtered.map((e) => {
          const badge = getSeverityBadge(e.severity);
          return (
            <div
              key={e.event_id}
              style={{
                background: "var(--bg-panel)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "16px",
                display: "flex",
                gap: "16px",
                alignItems: "flex-start"
              }}
            >
              <span style={{
                fontSize: "10px",
                fontWeight: 800,
                padding: "4px 8px",
                borderRadius: "4px",
                background: badge.bg,
                color: badge.color,
                border: badge.border,
                fontFamily: "monospace",
                whiteSpace: "nowrap"
              }}>
                {e.severity}
              </span>

              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontSize: "14px", fontWeight: 800, color: "var(--text-primary)" }}>{e.title}</span>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                    {new Date(e.created_at).toLocaleString()}
                  </span>
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  {e.description}
                </div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "6px", display: "flex", gap: "10px" }}>
                  <span>ID: {e.event_id}</span>
                  <span>Categoría: {e.category}</span>
                  <span>Ruta: {e.route}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
