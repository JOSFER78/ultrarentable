import Link from "next/link";

const FLOW = [
  {
    href: "/",
    code: "01",
    label: "Paso 1: Búsqueda",
    desc: "SQX · Generación IA",
  },
  {
    href: "/fondeo",
    code: "02A",
    label: "Paso 2A: Fondeo",
    desc: "Prop Firms · Futuros",
  },
  {
    href: "/ultra",
    code: "02B",
    label: "Paso 2B: Ultra",
    desc: "Capital Propio · BingX",
  },
  {
    href: "/robots",
    code: "03",
    label: "Paso 3: Bots",
    desc: "Ejecución en Vivo",
  },
  {
    href: "/portfolio",
    code: "04",
    label: "Métricas",
    desc: "Portfolio & Equity",
  },
];

export default function ModuleMap() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "stretch",
        flexWrap: "wrap",
        gap: 10,
        margin: "16px 0",
      }}
    >
      {FLOW.map((m, i) => (
        <div key={m.href} style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link
            href={m.href}
            style={{
              textDecoration: "none",
              padding: "12px 14px",
              background: "var(--bg-panel)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              display: "flex",
              flexDirection: "column",
              gap: 4,
              minWidth: 120,
              transition: "transform 150ms",
            }}
          >
            <span style={{ fontSize: 10, fontFamily: "monospace", fontWeight: 800, color: "var(--accent)", background: "rgba(99, 225, 180, 0.1)", padding: "2px 6px", borderRadius: 3, alignSelf: "flex-start" }}>
              [{m.code}]
            </span>
            <span style={{ fontWeight: 700, fontSize: 12, color: "var(--text-primary)" }}>
              {m.label}
            </span>
            <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{m.desc}</span>
          </Link>
          {i < FLOW.length - 1 && (
            <span style={{ color: "var(--text-muted)", fontSize: 14, opacity: 0.5 }}>→</span>
          )}
        </div>
      ))}
    </div>
  );
}
