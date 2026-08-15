"use client";

import ModuleMap from "@/components/ModuleMap";

export default function AlertasPage() {
  return (
    <div className="page" style={{ padding: "32px", maxWidth: 1000, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, color: "var(--text-primary)" }}>
        Alertas y Telemetría del Sistema
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 8 }}>
        Seguimiento de estado, alertas al llegar a límites y log de auditoría.
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
        Esqueleto: Equity · PnL diario · drawdown vs trailing · distancia al límite · días ganadores ·
        trades/día · alertas (Telegram/correo) al 80% del límite · log de auditoría.
      </div>
    </div>
  );
}
