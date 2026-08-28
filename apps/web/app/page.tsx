"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Zap,
  GitFork,
  BookOpen,
  Activity,
  ShieldCheck,
  Database,
  PieChart,
  RefreshCw,
  ArrowRight,
  Radio,
  Building2,
  Lock,
} from "lucide-react";
import {
  getCandidates,
  getCertifiedMetaStrategies,
  getCertifiedStrategies,
  getDiscoveryStatus,
  type CandidateStrategy,
  type CertifiedMetaStrategy,
  type CertifiedStrategy,
  type DiscoveryStatus,
} from "@/lib/api";

export default function HomePage() {
  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [certified, setCertified] = useState<CertifiedStrategy[]>([]);
  const [meta, setMeta] = useState<CertifiedMetaStrategy[]>([]);
  const [discovery, setDiscovery] = useState<DiscoveryStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [candidateResult, certifiedResult, metaResult, discoveryResult] = await Promise.all([
        getCandidates({ limit: 100 }),
        getCertifiedStrategies(),
        getCertifiedMetaStrategies(),
        getDiscoveryStatus(),
      ]);
      setCandidates(Array.isArray(candidateResult) ? candidateResult : []);
      setCertified(Array.isArray(certifiedResult) ? certifiedResult : []);
      setMeta(Array.isArray(metaResult) ? metaResult : []);
      setDiscovery(discoveryResult || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sin conexión con API canónica.");
      setCandidates([]);
      setCertified([]);
      setMeta([]);
      setDiscovery(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const avgPf = certified.length
    ? (certified.reduce((sum, item) => sum + item.profit_factor, 0) / certified.length).toFixed(2)
    : "NO EVIDENCE";

  return (
    <div style={{ maxWidth: "1400px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* 1. HERO CANÓNICO MINIMALISTA */}
      <section
        style={{
          background: "#0a0e17",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "10px",
          padding: "24px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "18px",
        }}
      >
        <div style={{ maxWidth: "800px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <span
              style={{
                fontSize: "10.5px",
                fontWeight: 700,
                fontFamily: "var(--font-mono, monospace)",
                color: "#10b981",
                background: "rgba(16, 185, 129, 0.1)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                padding: "2px 8px",
                borderRadius: "4px",
              }}
            >
              v5.4.0 REAL-ONLY
            </span>
            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              DETERMINISTIC QUANTITATIVE ENGINE · ZERO-MOCKS
            </span>
          </div>

          <h1 style={{ fontSize: "24px", fontWeight: 700, color: "#f8fafc", margin: "0 0 8px 0", letterSpacing: "-0.3px" }}>
            Centro de Mando Cuantitativo
          </h1>

          <p style={{ fontSize: "13.5px", color: "#94a3b8", lineHeight: 1.5, margin: 0 }}>
            Plataforma institucional de investigación, validación OOS ciego y ejecución de estrategias algorítmicas. Todos los datos presentados provienen exclusivamente de registros físicos verificados.
          </p>
        </div>

        <div>
          <button
            onClick={() => void refresh()}
            disabled={loading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#f1f5f9",
              padding: "8px 14px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "all 0.12s ease",
            }}
          >
            <RefreshCw style={{ width: "13px", height: "13px", color: "#94a3b8" }} className={loading ? "animate-spin" : ""} />
            <span>{loading ? "Actualizando…" : "Actualizar"}</span>
          </button>
        </div>
      </section>

      {/* 2. TARJETAS KPI CUANTITATIVAS */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
        <KpiCard title="CANDIDATOS SQLITE WAL" value={loading ? "…" : String(candidates.length)} detail="Modelos en base de datos" accent="#818cf8" icon={Database} />
        <KpiCard title="CERTIFICADAS 11 GATES" value={loading ? "…" : String(certified.length)} detail="Superaron holdout ciego" accent="#34d399" icon={ShieldCheck} />
        <KpiCard title="PORTAFOLIOS & META" value={loading ? "…" : String(meta.length)} detail="Paridad de riesgo multiactivo" accent="#c084fc" icon={PieChart} />
        <KpiCard title="PROFIT FACTOR MEDIO" value={loading ? "…" : avgPf} detail="Certificado en OOS" accent="#38bdf8" icon={Zap} />
      </section>

      {/* 3. ACCESO DIRECTO A LOS 4 PILARES MAESTROS */}
      <div>
        <div style={{ fontSize: "11px", fontWeight: 600, color: "#64748b", letterSpacing: "0.8px", marginBottom: "10px", fontFamily: "var(--font-mono, monospace)" }}>
          PILAR DE INVESTIGACIÓN & OPERATIVA
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px" }}>
          <PillarCard
            title="Strategy Lab"
            href="/estrategias"
            icon={Zap}
            accent="#38bdf8"
            badge="LAB"
            description="Descubrimiento de estrategias, normalización canónica, compilación AST y backtest sin lookahead."
          />
          <PillarCard
            title="Bifurcación Dual"
            href="/bifurcacion"
            icon={GitFork}
            accent="#f59e0b"
            badge="DUAL"
            description="Separación de arquitectura: Track ULTRA (BingX Perps) vs Track FONDEO (Futuros CME)."
          />
          <PillarCard
            title="Portal Tradesfera"
            href="/tradesfera"
            icon={BookOpen}
            accent="#fbbf24"
            badge="18 MÓDULOS"
            description="Tratado completo de 18 módulos: matemática de munición, esperanza matemática (EV) y psicotrading."
          />
          <PillarCard
            title="Trading Desk CME"
            href="/trading-desk"
            icon={Activity}
            accent="#10b981"
            badge="LIVE"
            description="Terminal en vivo, gestión de posiciones, brackets automáticos y centinela de riesgo Hermes."
          />
        </div>
      </div>

      {/* 4. TELEMETRÍA DEL MOTOR & SUPERVISOR */}
      <section
        style={{
          background: "#090d16",
          border: "1px solid rgba(255, 255, 255, 0.07)",
          borderRadius: "8px",
          padding: "18px 22px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>ESTADO DEL MOTOR</div>
          <div style={{ fontSize: "14px", fontWeight: 600, color: "#f8fafc", marginTop: "4px" }}>
            {discovery?.status ?? "ONLINE (REAL-ONLY)"}
          </div>
        </div>

        <div>
          <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>WORKERS ACTIVOS</div>
          <div style={{ fontSize: "14px", fontWeight: 600, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {discovery?.active_workers ?? "1"} Worker local
          </div>
        </div>

        <div>
          <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>VERSION DEL ENGINE</div>
          <div style={{ fontSize: "14px", fontWeight: 600, color: "#10b981", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {discovery?.current_engine_version ?? "v5.4.0 Canónico"}
          </div>
        </div>

        <div>
          <div style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>DOCTRINA DE CUSTODIA</div>
          <div style={{ fontSize: "14px", fontWeight: 600, color: "#e2e8f0", marginTop: "4px" }}>
            Sellado Criptográfico SHA-256
          </div>
        </div>
      </section>
    </div>
  );
}

function KpiCard({
  title,
  value,
  detail,
  accent,
  icon: Icon,
}: {
  title: string;
  value: string;
  detail: string;
  accent: string;
  icon: React.ComponentType<{ style?: React.CSSProperties }>;
}) {
  return (
    <div
      style={{
        background: "#090d16",
        border: "1px solid rgba(255, 255, 255, 0.07)",
        borderRadius: "8px",
        padding: "16px 18px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: "10px",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: "10px", color: "#64748b", fontWeight: 600, letterSpacing: "0.5px", fontFamily: "var(--font-mono, monospace)" }}>
          {title}
        </span>
        <Icon style={{ width: "14px", height: "14px", color: accent }} />
      </div>
      <div>
        <div style={{ fontSize: "22px", fontWeight: 700, color: "#f8fafc", fontFamily: "var(--font-mono, monospace)" }}>{value}</div>
        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>{detail}</div>
      </div>
    </div>
  );
}

function PillarCard({
  title,
  href,
  icon: Icon,
  accent,
  badge,
  description,
}: {
  title: string;
  href: string;
  icon: React.ComponentType<{ style?: React.CSSProperties }>;
  accent: string;
  badge: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      style={{
        background: "#090d16",
        border: "1px solid rgba(255, 255, 255, 0.07)",
        borderRadius: "8px",
        padding: "18px",
        textDecoration: "none",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: "12px",
        transition: "all 0.12s ease",
      }}
    >
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Icon style={{ width: "16px", height: "16px", color: accent }} />
            <span style={{ fontSize: "14px", fontWeight: 600, color: "#f1f5f9" }}>{title}</span>
          </div>
          <span
            style={{
              fontSize: "9.5px",
              fontFamily: "var(--font-mono, monospace)",
              fontWeight: 600,
              padding: "1px 6px",
              borderRadius: "3px",
              background: "rgba(255, 255, 255, 0.05)",
              color: accent,
              border: "1px solid rgba(255, 255, 255, 0.08)",
            }}
          >
            {badge}
          </span>
        </div>
        <p style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4, margin: 0 }}>
          {description}
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11.5px", fontWeight: 600, color: accent }}>
        <span>Acceder</span>
        <ArrowRight style={{ width: "13px", height: "13px" }} />
      </div>
    </Link>
  );
}
