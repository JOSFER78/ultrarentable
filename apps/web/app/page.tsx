"use client";

/**
 * apps/web/app/page.tsx
 * Portada y Centro de Mando Cuantitativo FONDEO.
 *
 * Cumple con docs/18_STRATEGIES_PAGE_SPEC.md, docs/19_UI_STYLE_SPEC.md y GO_A12:
 * - Monocromo estricto con tokens de docs/19
 * - Cero colores fuera de tokens (sin hex ni clases tailwind de colores)
 * - Versión de motor 100% dinámica y leída desde la API canónica
 * - Marcador honesto (0 certificadas mostrado con sobriedad en gris)
 * - ULTRA presente como bloque atenuado "EN CONSTRUCCIÓN", nunca borrado
 */

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  Database,
  ShieldCheck,
  Zap,
  Layers,
  Building2,
  Activity,
  ClipboardList,
  Radio,
  Flame,
  RefreshCw,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  XCircle,
  Lock,
} from "lucide-react";
import {
  getCandidatosCanonicos,
  getCertifiedStrategies,
  getCertifiedMetaStrategies,
  getDiscoveryStatus,
  type CandidatoCanonico,
  type CertifiedStrategy,
  type CertifiedMetaStrategy,
  type DiscoveryStatus,
} from "@/lib/api";
import { useEngineVersion } from "@/hooks/useEngineVersion";

export default function HomePage() {
  const { version: hookVersion, error: hookError } = useEngineVersion();
  const [candidatos, setCandidatos] = useState<CandidatoCanonico[]>([]);
  const [certified, setCertified] = useState<CertifiedStrategy[]>([]);
  const [meta, setMeta] = useState<CertifiedMetaStrategy[]>([]);
  const [discovery, setDiscovery] = useState<DiscoveryStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refrescar = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [candRes, certRes, metaRes, discRes] = await Promise.all([
        getCandidatosCanonicos(1000).catch(() => []),
        getCertifiedStrategies().catch(() => []),
        getCertifiedMetaStrategies().catch(() => []),
        getDiscoveryStatus().catch(() => null),
      ]);
      setCandidatos(Array.isArray(candRes) ? candRes : []);
      setCertified(Array.isArray(certRes) ? certRes : []);
      setMeta(Array.isArray(metaRes) ? metaRes : []);
      setDiscovery(discRes);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al conectar con la API canónica.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refrescar();
  }, [refrescar]);

  const engineVersion = discovery?.current_engine_version || hookVersion || null;
  const apiConectada = !error && !hookError && Boolean(engineVersion);

  // REAL-ONLY (2026-09-02): solo cuentan como "certificadas FONDEO" las de ruta FONDEO con el motor
  // vigente. Una certificacion con motor anterior es LEGACY (regla #26) y una de ruta ULTRA no es
  // FONDEO. Antes la tarjeta mostraba certified.length (5 ULTRA con motor 5.13/5.16) como FONDEO.
  const certFondeoVigentes = certified.filter(
    (c) => (c.route || "").toUpperCase() === "FONDEO" && Boolean(engineVersion) && c.engine_version === engineVersion
  );
  const certUltra = certified.filter((c) => (c.route || "").toUpperCase() === "ULTRA").length;
  const certMotorAnterior = certified.filter((c) => Boolean(engineVersion) && c.engine_version !== engineVersion).length;
  const avgPfOos = certFondeoVigentes.length
    ? (certFondeoVigentes.reduce((acc, curr) => acc + (curr.profit_factor || 0), 0) / certFondeoVigentes.length).toFixed(2)
    : "NO EVIDENCE";
  // Meta-portafolios: solo APPROVED_CURRENT_ENGINE es "aprobado". SUPERSEDED y los pendientes de
  // backtest no lo son (antes se mostraba meta.length: 17 "aprobados" que eran 15 sustituidos y 2 pendientes).
  const metaAprobados = meta.filter((m) => String(m.status) === "APPROVED_CURRENT_ENGINE").length;
  const metaSustituidos = meta.filter((m) => String(m.status) === "SUPERSEDED").length;
  const metaPendientes = meta.length - metaAprobados - metaSustituidos;
  const detalleCertificadas = loading
    ? "…"
    : certified.length === 0
      ? "Ninguna certificación en la base"
      : !engineVersion
        ? `${certified.length} en la base · sin versión de motor no se puede validar la regla #26`
        : `${certified.length} en la base: ${certUltra} de ruta ULTRA · ${certMotorAnterior} con motor anterior (LEGACY, regla #26)`;
  const detalleMeta = loading
    ? "…"
    : meta.length === 0
      ? "Ninguna composición en la base"
      : `${meta.length} composiciones en la base: ${metaSustituidos} sustituidas · ${metaPendientes} pendientes de backtest`;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        color: "var(--text-1)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
        maxWidth: "1400px",
        margin: "0 auto",
        width: "100%",
      }}
    >
      {/* 1. CABECERA Y HERO HONESTO */}
      <header
        style={{
          background: "var(--surface-1)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "20px 24px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "var(--surface-2)",
                border: "1px solid var(--border-strong)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-1)",
                fontFamily: "var(--font-mono, monospace)",
                fontWeight: 700,
                fontSize: "13px",
              }}
            >
              UR
            </div>
            <div>
              <h1 style={{ fontSize: "22px", fontWeight: 700, margin: 0, letterSpacing: "-0.02em" }}>
                Centro de Mando Cuantitativo — Track FONDEO
              </h1>
              <p style={{ margin: "2px 0 0", fontSize: "12.5px", color: "var(--text-2)" }}>
                Plataforma institucional de minería algorítmica, 11 Evidence Gates y evaluación de Prop Firms (CME Futures & Forex Majors).
              </p>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: "12px",
              flexWrap: "wrap",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "5px 10px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: apiConectada ? "var(--profit)" : "var(--loss)",
                }}
              />
              <span style={{ color: apiConectada ? "var(--text-1)" : "var(--loss)" }}>
                {apiConectada ? "API CONECTADA" : "API NO DISPONIBLE"}
              </span>
            </div>

            <div
              style={{
                padding: "5px 10px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                color: engineVersion ? "var(--text-1)" : "var(--text-3)",
              }}
            >
              {engineVersion ? `Motor ${engineVersion}` : "MOTOR: NO DISPONIBLE"}
            </div>

            <button
              onClick={() => void refrescar()}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "5px 12px",
                borderRadius: "6px",
                background: "var(--surface-3)",
                border: "1px solid var(--border-strong)",
                color: "var(--text-1)",
                cursor: "pointer",
              }}
            >
              <RefreshCw
                style={{
                  width: "13px",
                  height: "13px",
                  animation: loading ? "spin 1s linear infinite" : "none",
                }}
              />
              <span>Actualizar</span>
            </button>
          </div>
        </div>

        {/* BARRAS DE DOCTRINA */}
        <div
          style={{
            borderTop: "1px solid var(--border)",
            paddingTop: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "10px",
            fontSize: "11.5px",
            color: "var(--text-3)",
            fontFamily: "var(--font-mono, monospace)",
          }}
        >
          <div>ZERO-MOCKS · REAL-ONLY · SIN DATOS SINTÉTICOS · BASE DE DATOS SQLITE WAL</div>
          <div>CRITERIO 1.1: ≥ 200 OPS OOS · PROFIT FACTOR OOS ≥ 1.25 · 11 GATES INMUTABLES</div>
        </div>
      </header>

      {/* ERROR DE API (FAIL-CLOSED) */}
      {error && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "8px",
            background: "var(--loss-dim)",
            border: "1px solid var(--loss)",
            color: "var(--text-1)",
            fontSize: "13px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <XCircle style={{ width: "16px", height: "16px", color: "var(--loss)" }} />
          <span>Error de conexión: {error}</span>
        </div>
      )}

      {/* 2. MARCADOR HONESTO / KPIS CUANTITATIVOS */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "14px",
        }}
      >
        <Link
          href="/candidatos"
          style={{
            background: "var(--surface-1)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            textDecoration: "none",
            color: "inherit",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)", letterSpacing: "0.4px" }}>
              Candidatas en Catálogo
            </span>
            <Database style={{ width: "15px", height: "15px", color: "var(--text-3)" }} />
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--text-1)", fontFamily: "var(--font-mono, monospace)" }}>
            {loading ? "…" : candidatos.length}
          </div>
          <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>Base canónica SQLite WAL</div>
        </Link>

        <Link
          href="/gates"
          style={{
            background: "var(--surface-1)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            textDecoration: "none",
            color: "inherit",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)", letterSpacing: "0.4px" }}>
              Certificadas FONDEO
            </span>
            <ShieldCheck style={{ width: "15px", height: "15px", color: "var(--text-3)" }} />
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--text-2)", fontFamily: "var(--font-mono, monospace)" }}>
            {loading ? "…" : certFondeoVigentes.length}
          </div>
          <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>{detalleCertificadas}</div>
        </Link>

        <Link
          href="/estrategias"
          style={{
            background: "var(--surface-1)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            textDecoration: "none",
            color: "inherit",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)", letterSpacing: "0.4px" }}>
              PF Medio Certificadas (OOS)
            </span>
            <Zap style={{ width: "15px", height: "15px", color: "var(--text-3)" }} />
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--text-3)", fontFamily: "var(--font-mono, monospace)" }}>
            {loading ? "…" : avgPfOos}
          </div>
          <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>Holdout ciego fuera de muestra · solo FONDEO con motor vigente</div>
        </Link>

        <Link
          href="/estrategias"
          style={{
            background: "var(--surface-1)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px 20px",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
            textDecoration: "none",
            color: "inherit",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)", letterSpacing: "0.4px" }}>
              Meta-Portafolios Aprobados
            </span>
            <Layers style={{ width: "15px", height: "15px", color: "var(--text-3)" }} />
          </div>
          <div style={{ fontSize: "26px", fontWeight: 700, color: "var(--text-2)", fontFamily: "var(--font-mono, monospace)" }}>
            {loading ? "…" : metaAprobados}
          </div>
          <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>{detalleMeta}</div>
        </Link>
      </section>

      {/* 3. ARQUITECTURA MODULAR M1-M4 (NAVEGACIÓN A SECCIONES) */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-2)", letterSpacing: "0.3px" }}>
          Pipeline Modular Cuantitativo (M1 — M4)
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "14px",
          }}
        >
          <Link
            href="/estrategias"
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", fontFamily: "var(--font-mono, monospace)", color: "var(--text-3)" }}>
                MÓDULO 01
              </span>
              <ArrowRight style={{ width: "14px", height: "14px", color: "var(--text-3)" }} />
            </div>
            <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-1)" }}>
              M1 — Generación (StrategyQuant X)
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-2)", lineHeight: "1.4" }}>
              Fábrica de hipótesis crudas. Extracción desde databanks, control de configuración y enlace de datasets verificados.
            </p>
          </Link>

          <Link
            href="/estrategias"
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", fontFamily: "var(--font-mono, monospace)", color: "var(--text-3)" }}>
                MÓDULO 02
              </span>
              <ArrowRight style={{ width: "14px", height: "14px", color: "var(--text-3)" }} />
            </div>
            <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-1)" }}>
              M2 — Mejora (Loop Iterativo)
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-2)", lineHeight: "1.4" }}>
              Ciclo continuo de reparación de fallos en gates, árbol de linaje, holdout inviolable y penalización DSR.
            </p>
          </Link>

          <Link
            href="/fondeo"
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", fontFamily: "var(--font-mono, monospace)", color: "var(--text-3)" }}>
                MÓDULO 03
              </span>
              <ArrowRight style={{ width: "14px", height: "14px", color: "var(--text-3)" }} />
            </div>
            <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-1)" }}>
              M3 — Valoración para Fondeo
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-2)", lineHeight: "1.4" }}>
              Simulación barra a barra contra reglas de Prop Firms: P(pasar), P(ruina), control de DD y horarios óptimos.
            </p>
          </Link>

          <Link
            href="/estrategias"
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
              textDecoration: "none",
              color: "inherit",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: "11px", fontFamily: "var(--font-mono, monospace)", color: "var(--text-3)" }}>
                MÓDULO 04
              </span>
              <ArrowRight style={{ width: "14px", height: "14px", color: "var(--text-3)" }} />
            </div>
            <div style={{ fontWeight: 600, fontSize: "14px", color: "var(--text-1)" }}>
              M4 — Metaestrategias
            </div>
            <p style={{ margin: 0, fontSize: "12px", color: "var(--text-2)", lineHeight: "1.4" }}>
              Composición multiactivo para reducción de varianza del examen, matrices de covarianza real y paridad de riesgo.
            </p>
          </Link>
        </div>
      </section>

      {/* 4. ACCESOS DIRECTOS A PÁGINAS DE LA MISIÓN */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-2)", letterSpacing: "0.3px" }}>
          Secciones de la Misión
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "10px",
          }}
        >
          {[
            { label: "Catálogo Canónico", href: "/estrategias", icon: Database, desc: "Búsqueda e inspección de hipótesis" },
            { label: "11 Evidence Gates", href: "/gates", icon: ShieldCheck, desc: "Pipeline inmutable de validación" },
            { label: "Trading Desk FONDEO", href: "/fondeo", icon: Building2, desc: "Ejecución institucional CME" },
            { label: "Catálogo Prop Firms", href: "/prop-firms", icon: Layers, desc: "Reglas oficiales y evaluación" },
            { label: "Plan Maestro", href: "/plan", icon: ClipboardList, desc: "Estado y hoja de ruta" },
            { label: "Sistema & Telemetría", href: "/sistema", icon: Radio, desc: "Supervisor y salud del motor" },
          ].map((sec) => {
            const Icon = sec.icon;
            return (
              <Link
                key={sec.href}
                href={sec.href}
                style={{
                  background: "var(--surface-1)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  padding: "12px 14px",
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  textDecoration: "none",
                  color: "inherit",
                }}
              >
                <Icon style={{ width: "16px", height: "16px", color: "var(--text-3)", flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: "12.5px", fontWeight: 600, color: "var(--text-1)" }}>{sec.label}</div>
                  <div style={{ fontSize: "11px", color: "var(--text-3)" }}>{sec.desc}</div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* 5. BLOQUE ULTRA — ATENUADO, SIEMPRE VISIBLE, NUNCA BORRADO */}
      <section
        style={{
          borderTop: "1px solid var(--border)",
          paddingTop: "20px",
        }}
      >
        <Link
          href="/ultra"
          style={{
            background: "var(--surface-1)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "16px 20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
            textDecoration: "none",
            color: "inherit",
            opacity: 0.8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <Flame style={{ width: "18px", height: "18px", color: "var(--text-3)" }} />
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontWeight: 600, fontSize: "13px", color: "var(--text-2)" }}>
                  Track ULTRA (Asimetría Convexa y Balas Aisladas)
                </span>
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "var(--font-mono, monospace)",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    color: "var(--text-3)",
                  }}
                >
                  EN CONSTRUCCIÓN
                </span>
              </div>
              <p style={{ margin: "3px 0 0", fontSize: "11.5px", color: "var(--text-3)" }}>
                Ruta hermana multi-activo en 5 temporalidades (1m, 5m, 15m, 1h, 4h) congelada en <code>state/PUNTO_GUARDADO_ULTRA.md</code>.
              </p>
            </div>
          </div>

          <div style={{ fontSize: "12px", color: "var(--text-3)", display: "flex", alignItems: "center", gap: "4px" }}>
            <span>Ver Trading Desk ULTRA</span>
            <ArrowRight style={{ width: "12px", height: "12px" }} />
          </div>
        </Link>
      </section>
    </div>
  );
}
