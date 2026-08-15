"use client";

import ModuleMap from "@/components/ModuleMap";

export default function PortfolioPage() {
  return (
    <div className="page" style={{ padding: "32px", maxWidth: 1000, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, color: "var(--text-primary)" }}>
        Módulo Métricas de Portfolio
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 8 }}>
        Una estrategia puede desplegarse en <b>varias cuentas y exchanges</b>. Aquí se agrega el
        rendimiento con trazabilidad.
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
        Esqueleto: vistas de cartera Ultra + cartera Fondeo + rendimiento agregado por cuenta/exchange.
        (Se desarrolla cuando los módulos Ultra y Fondeo tengan cuentas reales.)
      </div>
    </div>
  );
}
