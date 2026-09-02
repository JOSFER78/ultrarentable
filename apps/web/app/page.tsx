"use client";

/**
 * apps/web/app/page.tsx
 * Portada — versión mínima y sobria (mandato de Emilio, 2026-09-02: la portada anterior con
 * tarjetas M1-M4 y "Secciones de la Misión" queda descartada por grandilocuente).
 *
 * Solo tres datos reales, un párrafo construido a partir de ellos (sin cifras escritas a mano)
 * y enlaces a páginas que existen. Cero valores por defecto: si la API falla, se dice y punto.
 *
 * Cumple docs/19_UI_STYLE_SPEC.md (monocromo, color solo para dinero/estado crítico, sin
 * animaciones) y REAL-ONLY (nada hardcodeado; ausencia = "NO DATA" en gris, nunca un 0 inventado).
 */

import React, { useEffect, useMemo, useState, useCallback } from "react";
import Link from "next/link";
import { getCandidatosCanonicos, type CandidatoCanonico } from "@/lib/api";
import { useEngineVersion } from "@/hooks/useEngineVersion";

/**
 * `lib/api.ts` no declara `engine_version` en `CandidatoCanonico` (es de otra sesión y no se
 * toca), pero la API sí lo devuelve por fila — verificado 2026-09-02 contra /api/v1/candidates.
 * Se extiende localmente en vez de tocar el fichero compartido.
 */
type CandidatoConMotor = CandidatoCanonico & { engine_version?: string | null };

/**
 * Contrato real de /estrategias/api-telemetria (verificado 2026-09-02 contra
 * app/estrategias/api-telemetria/route.ts, líneas 49-65 y 139): SIEMPRE
 * `{status:"OK"|"NO DATA", campanas: CampanaResumenApi[]}`, ordenado por fecha
 * descendente (la campaña más reciente de cada símbolo/temporalidad/perfil es
 * `campanas[0]`). No es un objeto plano de nivel superior: no hay que leer
 * `mercado`/`timeframe`/`configuraciones_evaluadas` en la raíz, sino dentro de
 * cada elemento del array.
 */
interface CampanaResumenApi {
  track?: string;
  symbol: string;
  timeframe: string;
  profile?: string;
  generado_utc: string;
  engine_version?: string;
  evaluadas: number;
  muertas_is?: number;
  pasan_is?: number;
  [k: string]: unknown;
}
interface TelemetriaResumenApi {
  status?: string;
  campanas?: CampanaResumenApi[];
}

function formatearFecha(iso: string | null): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  try {
    return d.toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return iso;
  }
}

const tileStyle: React.CSSProperties = {
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  borderRadius: "8px",
  padding: "20px 22px",
  display: "flex",
  flexDirection: "column",
  gap: "8px",
};
const labelStyle: React.CSSProperties = {
  fontSize: "11.5px",
  textTransform: "uppercase",
  letterSpacing: "0.4px",
  color: "var(--text-3)",
};
const numberStyle: React.CSSProperties = {
  fontSize: "34px",
  fontWeight: 700,
  color: "var(--text-1)",
  fontFamily: "var(--font-mono, monospace)",
  lineHeight: 1.1,
};
const captionStyle: React.CSSProperties = {
  fontSize: "12.5px",
  color: "var(--text-3)",
  lineHeight: 1.4,
};
const linkStyle: React.CSSProperties = {
  padding: "9px 16px",
  borderRadius: "6px",
  background: "var(--surface-1)",
  border: "1px solid var(--border)",
  color: "var(--text-1)",
  fontSize: "13px",
  textDecoration: "none",
};

export default function HomePage() {
  const { version: engineVersion, loading: engineLoading, error: engineError } = useEngineVersion();

  const [candidatos, setCandidatos] = useState<CandidatoConMotor[]>([]);
  const [candidatosLoading, setCandidatosLoading] = useState(true);

  const [telemetria, setTelemetria] = useState<TelemetriaResumenApi | null>(null);
  const [telemetriaLoading, setTelemetriaLoading] = useState(true);

  const cargarCandidatos = useCallback(async () => {
    setCandidatosLoading(true);
    try {
      const rows = await getCandidatosCanonicos(1000);
      setCandidatos(Array.isArray(rows) ? (rows as CandidatoConMotor[]) : []);
    } catch {
      setCandidatos([]);
    } finally {
      setCandidatosLoading(false);
    }
  }, []);

  const cargarTelemetria = useCallback(async () => {
    setTelemetriaLoading(true);
    try {
      const res = await fetch("/estrategias/api-telemetria", { cache: "no-store" });
      if (!res.ok) throw new Error(String(res.status));
      const data = (await res.json()) as unknown;
      setTelemetria(data && typeof data === "object" ? (data as TelemetriaResumenApi) : null);
    } catch {
      setTelemetria(null);
    } finally {
      setTelemetriaLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargarCandidatos();
    void cargarTelemetria();
  }, [cargarCandidatos, cargarTelemetria]);

  const apiConectada = !engineLoading && !engineError && Boolean(engineVersion);

  // Definición sellada (criterio 1.1 + regla #26): ruta FONDEO, motor vigente, >=200 ops OOS,
  // PF OOS >=1.25, 11/11 gates. Es la ÚNICA forma en la que la portada puede llamar "lista" a
  // una estrategia. Verificado 2026-09-02 contra la API: hoy da 0 (las 5 APPROVED_CURRENT_ENGINE
  // que hay en la base son de ruta ULTRA, motor 5.13.0/5.16.0 — no el vigente — y 25-68 ops OOS).
  const listasParaFondeo = useMemo(
    () =>
      candidatos.filter((c) => {
        const ruta = (c.route || "").toUpperCase();
        const motorVigente = Boolean(engineVersion) && c.engine_version === engineVersion;
        return (
          ruta === "FONDEO" &&
          c.status === "APPROVED_CURRENT_ENGINE" &&
          motorVigente &&
          typeof c.trades_oos === "number" &&
          c.trades_oos >= 200 &&
          typeof c.profit_factor_oos === "number" &&
          c.profit_factor_oos >= 1.25 &&
          c.gates_passed_count === 11
        );
      }),
    [candidatos, engineVersion]
  );

  const aprobadasEnBase = useMemo(
    () => candidatos.filter((c) => c.status === "APPROVED_CURRENT_ENGINE").length,
    [candidatos]
  );
  const aprobadasQueNoCuentan = Math.max(aprobadasEnBase - listasParaFondeo.length, 0);

  // La API devuelve un array de campañas (una por símbolo/temporalidad/perfil), ya ordenado
  // por fecha descendente: campanas[0] es la más reciente de todas.
  const ultimaCampana = telemetria?.campanas?.[0] ?? null;
  const tMercado = ultimaCampana?.symbol ?? null;
  const tTf = ultimaCampana?.timeframe ?? null;
  const tFechaRaw = ultimaCampana?.generado_utc ?? null;
  const tConfigs = typeof ultimaCampana?.evaluadas === "number" ? ultimaCampana.evaluadas : null;
  // "pasan_is" = configuraciones - muertas en la etapa IS = supervivientes de la primera fase.
  const tPasaron = typeof ultimaCampana?.pasan_is === "number" ? ultimaCampana.pasan_is : null;
  const hayTelemetria = Boolean(tMercado && tTf && typeof tConfigs === "number");
  const tFechaTxt = formatearFecha(tFechaRaw);

  const lineaTelemetria = hayTelemetria
    ? `${tMercado} ${tTf}${tFechaTxt ? ` · ${tFechaTxt}` : ""} · ${
        typeof tPasaron === "number" ? `${tPasaron} pasaron la primera fase` : "sin dato de cuántas pasaron"
      }`
    : "Sin datos de campañas todavía";

  const parrafo = useMemo(() => {
    if (candidatosLoading || telemetriaLoading || engineLoading) return "Cargando datos…";
    if (!apiConectada) return "No se puede evaluar el estado del proyecto: la API no responde.";
    const partes: string[] = [];
    partes.push(
      listasParaFondeo.length === 0
        ? "Hoy no hay ninguna estrategia lista para FONDEO."
        : `Hoy hay ${listasParaFondeo.length} estrategia${listasParaFondeo.length === 1 ? "" : "s"} lista${
            listasParaFondeo.length === 1 ? "" : "s"
          } para FONDEO, con toda la evidencia exigida.`
    );
    partes.push(
      hayTelemetria
        ? `La última búsqueda probó ${tConfigs} configuraciones en ${tMercado} ${tTf}${
            tFechaTxt ? ` (${tFechaTxt})` : ""
          } y ${typeof tPasaron === "number" ? (tPasaron === 0 ? "ninguna pasó la primera fase" : `${tPasaron} pasaron la primera fase`) : "no se registró cuántas pasaron la primera fase"}.`
        : "Aún no hay datos registrados de la última búsqueda."
    );
    if (aprobadasQueNoCuentan > 0) {
      partes.push(
        `Las ${aprobadasQueNoCuentan} aprobaciones antiguas de la base no cuentan: son de otra ruta, de un motor anterior, o no llegan a las operaciones mínimas exigidas.`
      );
    }
    return partes.join(" ");
  }, [
    candidatosLoading,
    telemetriaLoading,
    engineLoading,
    apiConectada,
    listasParaFondeo.length,
    hayTelemetria,
    tConfigs,
    tMercado,
    tTf,
    tFechaTxt,
    tPasaron,
    aprobadasQueNoCuentan,
  ]);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        color: "var(--text-1)",
        padding: "32px 24px",
        display: "flex",
        flexDirection: "column",
        gap: "28px",
        maxWidth: "980px",
        margin: "0 auto",
        width: "100%",
      }}
    >
      <header style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <h1 style={{ fontSize: "26px", fontWeight: 700, margin: 0, letterSpacing: "-0.02em" }}>Ultrarentable</h1>
        <p style={{ margin: 0, fontSize: "13px", fontFamily: "var(--font-mono, monospace)" }}>
          {engineLoading ? (
            <span style={{ color: "var(--text-3)" }}>Comprobando conexión con la API…</span>
          ) : apiConectada ? (
            <span style={{ color: "var(--text-2)" }}>API conectada · Motor {engineVersion}</span>
          ) : (
            <span style={{ color: "var(--loss)" }}>API sin conexión</span>
          )}
        </p>
      </header>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "14px",
        }}
      >
        <Link href="/estrategias" style={{ ...tileStyle, textDecoration: "none" }}>
          <span style={labelStyle}>Estrategias listas para FONDEO</span>
          <span style={numberStyle}>{candidatosLoading ? "…" : listasParaFondeo.length}</span>
          <span style={captionStyle}>
            Ruta FONDEO, motor vigente, 200 o más operaciones fuera de muestra, factor de beneficio ≥ 1,25 y los 11
            controles de calidad superados.
          </span>
        </Link>

        <Link href="/estrategias" style={{ ...tileStyle, textDecoration: "none" }}>
          <span style={labelStyle}>Última campaña de búsqueda</span>
          <span style={numberStyle}>{telemetriaLoading ? "…" : hayTelemetria ? tConfigs : "NO DATA"}</span>
          <span style={{ ...captionStyle, color: hayTelemetria ? "var(--text-3)" : "var(--text-3)" }}>
            {telemetriaLoading ? "Cargando…" : lineaTelemetria}
          </span>
        </Link>

        <Link href="/candidatos" style={{ ...tileStyle, textDecoration: "none" }}>
          <span style={labelStyle}>Candidatas evaluadas</span>
          <span style={numberStyle}>{candidatosLoading ? "…" : candidatos.length}</span>
          <span style={captionStyle}>Guardadas en el archivo técnico.</span>
        </Link>
      </section>

      <section
        style={{
          background: "var(--surface-1)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "18px 22px",
        }}
      >
        <div style={{ fontSize: "12px", textTransform: "uppercase", letterSpacing: "0.4px", color: "var(--text-3)", marginBottom: "8px" }}>
          Dónde estamos
        </div>
        <p style={{ margin: 0, fontSize: "14px", color: "var(--text-2)", lineHeight: 1.6 }}>{parrafo}</p>
      </section>

      <nav style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
        <Link
          href="/estrategias"
          style={{ ...linkStyle, background: "var(--surface-3)", border: "1px solid var(--border-strong)", fontWeight: 600 }}
        >
          Ver estrategias
        </Link>
        <Link href="/trading-desk" style={linkStyle}>
          Trading Desk
        </Link>
        <Link href="/prop-firms" style={linkStyle}>
          Prop Firms
        </Link>
        <Link href="/sistema" style={linkStyle}>
          Sistema
        </Link>
      </nav>

      <section style={{ borderTop: "1px solid var(--border)", paddingTop: "18px" }}>
        <Link
          href="/ultra"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "8px",
            textDecoration: "none",
            color: "var(--text-3)",
            opacity: 0.75,
            fontSize: "12.5px",
          }}
        >
          <span>
            Track ULTRA{" "}
            <span
              style={{
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "10px",
                padding: "2px 6px",
                borderRadius: "4px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                marginLeft: "6px",
              }}
            >
              EN CONSTRUCCIÓN
            </span>
          </span>
          <span>Ver track ULTRA →</span>
        </Link>
      </section>
    </div>
  );
}
