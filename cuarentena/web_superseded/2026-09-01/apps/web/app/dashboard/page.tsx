"use client";

import Link from "next/link";

const MODULES = [
  {
    href: "/",
    icon: "[01]",
    title: "Búsqueda y Evaluación SQX",
    desc: "Buscar, crear, validar y editar estrategias con StrategyQuant X.",
    tag: "Fase 1",
  },
  {
    href: "/ultra",
    icon: "[02B]",
    title: "Ultrarentable (Capital Propio)",
    desc: "Estrategias para multiplicar tu cuenta en BingX API.",
    tag: "Fase 2B",
  },
  {
    href: "/fondeo",
    icon: "[02A]",
    title: "Fondeo (Prop Firms)",
    desc: "Estrategias adaptadas a prop firms con control de drawdown estricto.",
    tag: "Fase 2A",
  },
  {
    href: "/robots",
    icon: "[03]",
    title: "Seguimiento de Robots",
    desc: "Capa de ejecución y telemetría en tiempo real: Fondeo y Ultra.",
    tag: "Fase 3",
  },
  {
    href: "/portfolio",
    icon: "[04]",
    title: "Métricas de Portfolio",
    desc: "Riesgo consolidado y estrategias desplegadas en varias cuentas.",
    tag: "Métrica",
  },
  {
    href: "/prop-firms",
    icon: "[DB]",
    title: "Base de Datos Prop Firms",
    desc: "Matriz comparativa de 34 empresas de fondeo de futuros.",
    tag: "Catálogo",
  },
  {
    href: "/strategyquant",
    icon: "[SQX]",
    title: "Servidor StrategyQuant X",
    desc: "Estado del servidor SQX, proyectos y banco de datos de resultados.",
    tag: "Servidor",
  },
  {
    href: "/panel",
    icon: "[PNL]",
    title: "Estado del Sistema",
    desc: "Supervisión autónoma del Autopilot y logs de decisiones.",
    tag: "Sistema",
  },
];

export default function DashboardPage() {
  return (
    <div className="page" style={{ padding: "32px", maxWidth: 1100, margin: "0 auto" }}>
      <h1 style={{ fontSize: 26, fontWeight: 800, marginBottom: 4, color: "var(--text-primary)" }}>
        Dashboard General
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 28, fontSize: 15 }}>
        Plataforma modular: salta entre módulos en cualquier momento sin perder el contexto.
      </p>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))",
          gap: 20,
        }}
      >
        {MODULES.map((m) => (
          <Link key={m.href} href={m.href} style={{ textDecoration: "none" }}>
            <div
              className="bifurc-panel"
              style={{
                padding: 24,
                background: "var(--bg-panel)",
                border: "1px solid var(--border)",
                borderRadius: "var(--radius-lg)",
                minHeight: 150,
                display: "flex",
                flexDirection: "column",
                gap: 10,
                transition: "transform 200ms, box-shadow 200ms",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-4px)";
                e.currentTarget.style.boxShadow = "0 12px 30px rgba(0,0,0,0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <span style={{ fontSize: 34 }}>{m.icon}</span>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: "0.08em",
                  textTransform: "uppercase",
                  color: "var(--accent)",
                }}
              >
                {m.tag}
              </span>
              <span style={{ fontSize: 19, fontWeight: 700, color: "var(--text-primary)" }}>
                {m.title}
              </span>
              <span style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5 }}>
                {m.desc}
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
