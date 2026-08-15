"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

const PHASES = [
  {
    n: 1,
    icon: "[1]",
    title: "Búsqueda Conservadora y Consistente",
    desc: "StrategyQuant busca estrategias con bajo drawdown y curva de equidad uniforme para prop firms.",
    status: "ACTIVO",
    href: "/?mode=fondeo",
    tone: "accent",
  },
  {
    n: 2,
    icon: "[2]",
    title: "Selección de Empresa de Fondeo",
    desc: "Candidatas verificadas: FundedNext Rapid Pro (bots permitidos) o Bulenox / Apex (trial / evaluación).",
    status: "DISPONIBLE",
    href: "/prop-firms",
    tone: "info",
  },
  {
    n: 3,
    icon: "[3]",
    title: "Adaptación a las Reglas de Evaluación",
    desc: "Evaluación estricta de límites de pérdida diaria, trailing drawdown, consistente > 85% y horarios.",
    status: "EN COLAS",
    href: "/prop-firms",
    tone: "warning",
  },
  {
    n: 4,
    icon: "[4]",
    title: "Simulación de Evaluación Histórica",
    desc: "Verificación de aprobación del examen en simulación con comisiones y slippage realistas.",
    status: "EN COLAS",
    href: "/backtest",
    tone: "neutral",
  },
  {
    n: 5,
    icon: "[5]",
    title: "Seguimiento Diario Autónomo con Alertas",
    desc: "Monitor de equity en vivo. Si el drawdown alcanza el 80% del límite de la prop firm, se activa Kill Switch.",
    status: "EN COLAS",
    href: "/panel",
    tone: "neutral",
  },
];

export default function FondeoPage() {
  const [rentable, setRentable] = useState<any[]>([]);
  const [launching, setLaunching] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSQXRentable(5, "fondeo")
      .then((res) => setRentable(res.strategies || []))
      .catch(() => setRentable([]));
  }, []);

  const handleAutoLaunchFondeo = async () => {
    setLaunching(true);
    setStatusMsg("Conectando con SQX para iniciar búsqueda de Fondeo…");
    try {
      // 1. Guardar config fondeo predeterminada
      await api.createSearchConfig({
        name: `Auto Fondeo ${new Date().toLocaleTimeString()}`,
        mode: "fondeo",
        project: "Ultra_Auto_Pilot",
        databank: "Results",
        symbol: "BTC-USDT",
        interval: "1h",
        population: 24,
        max_drawdown_pct: 10,
        consistency_target: 85,
        techniques: ["trend", "mean_reversion"],
      });
      // 2. Iniciar SQX project
      await api.runSQXProject("Ultra_Auto_Pilot");
      setStatusMsg("Búsqueda de Fondeo activada en SQX. Redirigiendo al panel en vivo…");
      setTimeout(() => {
        window.location.href = "/?mode=fondeo&auto=true";
      }, 1500);
    } catch (err: any) {
      setStatusMsg(`[ERROR] ${err.message || "No se pudo lanzar la búsqueda"}`);
      setLaunching(false);
    }
  };

  return (
    <div className="stagger">
      {/* HERO */}
      <div className="page-header animate-in" style={{ marginBottom: 20 }}>
        <div className="bifurc-hero-badge" style={{ borderColor: "rgba(59,130,246,0.4)", color: "#bfdbfe" }}>
          <span className="bifurc-hero-badge-dot" style={{ background: "var(--info)", boxShadow: "0 0 10px var(--info)" }} />
          PASO 2A · MÓDULO DE DESPLIEGUE A FONDEO (PROP FIRMS / FUTUROS)
        </div>
        <h1 className="page-title" style={{ fontSize: 26, marginTop: 8 }}>
          Paso 2A: Evaluación y Despliegue en Prop Firms
        </h1>
        <p className="page-desc" style={{ maxWidth: 700, marginTop: 6 }}>
          Estrategias adaptadas para <strong>pasar evaluaciones de cuentas financiadas</strong>.
          La IA evalúa y audita el comportamiento según las reglas exactas de cada empresa de fondeo (drawdown, límites diarios y consistencia).
        </p>
      </div>

      {/* REGLAS DE CONTROL RÁPIDO */}
      <div
        className="card animate-in"
        style={{
          padding: 18,
          marginBottom: 20,
          background: "linear-gradient(135deg, rgba(59,130,246,0.12), rgba(30,58,138,0.05))",
          border: "1px solid rgba(59,130,246,0.35)",
        }}
      >
        <div style={{ fontWeight: 800, marginBottom: 12, color: "#60a5fa", fontSize: 14, textTransform: "uppercase", letterSpacing: "0.5px", fontFamily: "monospace" }}>
          [CONTROL DE CALIDAD] FILTROS ANTI-REGLAS DE PROP FIRMS ACTIVOS
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px,1fr))", gap: 10, marginBottom: 14 }}>
          {[
            ["Drawdown Máximo Permitido", "≤ 10%"],
            ["Consistencia por Día/Trade", "≥ 85%"],
            ["Objetivo de Beneficio Exam", "8% - 10%"],
            ["Protección en Tiempo Real", "Kill Switch @ 80% DD"],
          ].map(([k, v]) => (
            <div
              key={k}
              style={{
                padding: 10,
                background: "rgba(0,0,0,0.3)",
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.04em" }}>{k}</div>
              <div style={{ fontSize: 15, fontWeight: 800, color: "#fff", marginTop: 2, fontFamily: "monospace" }}>{v}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace" }}>
            [OK] REGLAS VERIFICADAS POR CONTRATO &nbsp; [OK] AUDITORÍA CONTINUA &nbsp; [OK] CONTROL DE APALANCAMIENTO
          </span>
          <button
            onClick={handleAutoLaunchFondeo}
            disabled={launching}
            className="btn btn-primary"
            style={{ background: "#2563eb", borderColor: "#3b82f6", fontWeight: 700 }}
          >
            {launching ? "INICIANDO BÚSQUEDA..." : "LANZAR BÚSQUEDA FONDEO (1-CLIC)"}
          </button>
        </div>
        {statusMsg && (
          <div style={{ marginTop: 12, fontSize: 12, color: "#93c5fd", fontWeight: 600, fontFamily: "monospace" }}>
            {statusMsg}
          </div>
        )}
      </div>

      {/* PIPELINE DE FASES */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          PIPELINE DEL PROCESO DE FONDEO
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }} className="animate-in">
          {PHASES.map((p, i) => (
            <div key={p.n} style={{ display: "flex", gap: 12, alignItems: "stretch" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 36 }}>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "4px",
                    display: "grid",
                    placeItems: "center",
                    background: "var(--bg-panel)",
                    border: `1.5px solid ${
                      p.tone === "accent"
                        ? "var(--accent)"
                        : p.tone === "info"
                        ? "var(--info)"
                        : p.tone === "warning"
                        ? "var(--warning)"
                        : p.tone === "danger"
                        ? "var(--danger)"
                        : "var(--border)"
                    }`,
                    fontSize: 11,
                    fontWeight: 800,
                    fontFamily: "monospace",
                    flexShrink: 0,
                  }}
                >
                  {p.icon}
                </div>
                {i < PHASES.length - 1 && (
                  <div style={{ flex: 1, width: 2, background: "var(--border)", margin: "4px 0" }} />
                )}
              </div>

              <Link
                href={p.href}
                className="card"
                style={{
                  flex: 1,
                  textDecoration: "none",
                  color: "inherit",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  gap: 12,
                  borderColor: p.status === "ACTIVO" ? "rgba(59,130,246,0.45)" : "var(--border)",
                  background: p.status === "ACTIVO" ? "var(--bg-panel-2)" : "var(--bg-panel)",
                  padding: "12px 16px",
                }}
              >
                <div>
                  <div style={{ fontSize: 9, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 800, letterSpacing: "0.05em", fontFamily: "monospace" }}>
                    FASE {p.n}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 800, color: "var(--text-primary)", marginTop: 2 }}>{p.title}</div>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2, lineHeight: 1.5 }}>{p.desc}</div>
                </div>
                <span
                  className="badge"
                  style={{
                    flexShrink: 0,
                    background:
                      p.status === "ACTIVO"
                        ? "var(--success-dim)"
                        : p.status === "DISPONIBLE"
                        ? "var(--info-dim)"
                        : "var(--bg-3)",
                    color:
                      p.status === "ACTIVO"
                        ? "var(--success)"
                        : p.status === "DISPONIBLE"
                        ? "var(--info)"
                        : "var(--text-muted)",
                    borderColor: "transparent",
                    fontFamily: "monospace",
                    fontSize: 10,
                  }}
                >
                  [{p.status}]
                </span>
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* CANDIDATAS */}
      <div className="card animate-in" style={{ marginBottom: 20, background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(56, 189, 248, 0.3)" }}>
        <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h2 className="card-title" style={{ fontSize: 16, color: "#f8fafc" }}>Catálogo Dinámico de Prop-Firms Evaluadas</h2>
            <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 2 }}>
              Investigación exhaustiva actualizada. Reglas reales, promociones y compatibilidad SQX.
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <Link href="/prop-firms" className="btn btn-primary" style={{ background: "#2563eb", textDecoration: "none", fontSize: 11, padding: "6px 10px", fontWeight: 700 }}>
              Acceder a la Base de Datos
            </Link>
          </div>
        </div>
      </div>

      {/* CAMBIO DE CAMINO */}
      <div className="bifurc-assist animate-in" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div className="bifurc-assist-text" style={{ flex: 1, minWidth: 240 }}>
          <strong style={{ color: "var(--text-primary)" }}>¿Prefieres gestionar tu propio capital?</strong> Opere sin límites de drawdown externo en BingX.
        </div>
        <Link href="/ultra" className="btn btn-primary" style={{ textDecoration: "none" }}>
          Paso 2B: Ir al Modo Ultra
        </Link>
      </div>
    </div>
  );
}
