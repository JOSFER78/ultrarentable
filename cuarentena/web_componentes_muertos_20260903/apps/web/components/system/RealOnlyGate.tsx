import Link from "next/link";

type RealOnlyGateProps = {
  title: string;
  description: string;
  required: string[];
};

export default function RealOnlyGate({
  title,
  description,
  required,
}: RealOnlyGateProps) {
  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">{title}</h1>
        <p className="page-desc">{description}</p>
      </div>

      <section className="card animate-in" style={{ padding: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <span className="badge badge-danger">REAL_ONLY_BLOCKED</span>
          <strong>Función desactivada hasta disponer de implementación real</strong>
        </div>
        <p style={{ color: "var(--text-muted)", marginBottom: 16 }}>
          Esta pantalla no muestra ejemplos, resultados de muestra ni procesos ficticios.
          Se habilitará únicamente cuando el backend entregue datos persistidos y artefactos verificables.
        </p>
        <h3 style={{ marginBottom: 10 }}>Requisitos para activarla</h3>
        <ul style={{ display: "grid", gap: 8, paddingLeft: 20, color: "var(--text-secondary)" }}>
          {required.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <div style={{ marginTop: 20 }}>
          <Link href="/data" className="btn btn-primary">
            Ver datos públicos reales de BingX
          </Link>
        </div>
      </section>
    </div>
  );
}
