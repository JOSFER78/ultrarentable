"use client";

import ModuleMap from "@/components/ModuleMap";

export default function SeguridadPage() {
  return (
    <div className="page" style={{ padding: "32px", maxWidth: 1000, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, color: "var(--text-primary)" }}>
        Ajustes y Seguridad del Sistema
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 8 }}>
        Permisos por nivel, kill switch global y configuración de seguridad.
      </p>

      <ModuleMap />

      <div
        style={{
          marginTop: 16,
          padding: 16,
          background: "var(--bg-panel)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          color: "var(--text-muted)",
          fontSize: 14,
        }}
      >
        Esqueleto: niveles de permiso (VER → CONFIGURAR → AUTORIZAR → ACTIVAR → EJECUTAR) · kill
        switch global · auditoría · límites diarios. Base para un sistema de permisos serio.
      </div>
    </div>
  );
}
