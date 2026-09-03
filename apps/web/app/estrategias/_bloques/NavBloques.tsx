"use client";

/**
 * apps/web/app/estrategias/_bloques/NavBloques.tsx
 *
 * Barra de navegación común a las 5 subpáginas del catálogo de estrategias
 * (Generación · Mejora · Valoración · Meta · Candidatos) más la vuelta a la página maestra.
 */

import Link from "next/link";

export type BloqueId = "generacion" | "mejora" | "valoracion" | "meta" | "candidatos";

const BLOQUES: Array<{ id: BloqueId; href: string; label: string }> = [
  { id: "generacion", href: "/estrategias/generacion", label: "1. Generación" },
  { id: "mejora", href: "/estrategias/mejora", label: "2. Mejora" },
  { id: "valoracion", href: "/estrategias/valoracion", label: "3. Valoración" },
  { id: "candidatos", href: "/estrategias/candidatos", label: "4. Candidatos" },
  { id: "meta", href: "/estrategias/meta", label: "5. Meta-Estrategias" },
];

export default function NavBloques({ activo }: { activo: BloqueId }) {
  return (
    <nav style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px", paddingBottom: "8px", borderBottom: "1px solid var(--border)" }}>
      <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
        {BLOQUES.map((b) => {
          const esActivo = b.id === activo;
          return (
            <Link
              key={b.id}
              href={b.href}
              style={{
                padding: "4px 10px",
                borderRadius: "4px",
                fontSize: "12px",
                fontWeight: esActivo ? 600 : 400,
                background: esActivo ? "var(--surface-3)" : "transparent",
                border: esActivo ? "1px solid var(--border-strong)" : "1px solid transparent",
                color: esActivo ? "var(--text-1)" : "var(--text-2)",
                textDecoration: "none",
              }}
            >
              {b.label}
            </Link>
          );
        })}
      </div>
      <Link href="/estrategias" style={{ fontSize: "12px", color: "var(--text-3)", textDecoration: "none" }}>
        ← Volver a Estrategias
      </Link>
    </nav>
  );
}
