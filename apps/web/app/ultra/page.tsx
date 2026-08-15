"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

const PHASES = [
  {
    n: 1,
    icon: "[1]",
    title: "Búsqueda de Estrategias Agresivas",
    desc: "StrategyQuant genera candidatos de retorno acelerado priorizando el multiplicador de capital.",
    status: "ACTIVO",
    href: "/?mode=ultra",
    tone: "accent",
  },
  {
    n: 2,
    icon: "[2]",
    title: "Validación Independiente BingX",
    desc: "FastEngine repite el backtest con comisiones taker 0.05%, funding rates y precio de liquidación BingX.",
    status: "EN COLAS",
    href: "/backtest",
    tone: "info",
  },
  {
    n: 3,
    icon: "[3]",
    title: "Selección de Portafolio Multiplicador",
    desc: "Selección de estrategias con retorno terminal esperado > 1000% tras costes.",
    status: "EN COLAS",
    href: "/leaderboard",
    tone: "warning",
  },
  {
    n: 4,
    icon: "[4]",
    title: "Simulación Paper / Shadow",
    desc: "Ejecución paralela en tiempo real sin arriesgar capital.",
    status: "EN COLAS",
    href: "/campaigns",
    tone: "neutral",
  },
  {
    n: 5,
    icon: "[5]",
    title: "Ejecución Live BingX Autorizada",
    desc: "Micro-live con tu confirmación explícita (1 contrato/símbolo). Nunca automático sin OK.",
    status: "REQUIERE TU OK",
    href: "/robots",
    tone: "danger",
  },
];

export default function UltraPage() {
  const [rentable, setRentable] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSQXRentable(5, "ultra")
      .then((res) => setRentable(res.strategies || []))
      .catch(() => setRentable([]));
  }, []);

  const handleAutoLaunchUltra = async () => {
    setLaunching(true);
    setStatusMsg("Conectando con SQX para iniciar búsqueda UltraRentable…");
    try {
      // 1. Guardar config ultra predeterminada
      await api.createSearchConfig({
        name: `Auto Ultra ${new Date().toLocaleTimeString()}`,
        mode: "ultra",
        project: "Ultra_Auto_Pilot",
        databank: "Results",
        symbol: "BTC-USDT",
        interval: "1h",
        population: 24,
        target_multiplier: 1000,
        techniques: ["breakout", "trend"],
      });
      // 2. Iniciar SQX project
      await api.runSQXProject("Ultra_Auto_Pilot");
      setStatusMsg("Búsqueda UltraRentable activada en SQX. Redirigiendo al panel en vivo…");
      setTimeout(() => {
        window.location.href = "/?mode=ultra&auto=true";
      }, 1500);
    } catch (err: any) {
      setStatusMsg(`Error: ${err.message || "No se pudo lanzar la búsqueda"}`);
      setLaunching(false);
    }
  };

  return (
    <div className="stagger">
      {/* HERO */}
      <div className="page-header animate-in" style={{ marginBottom: 20 }}>
        <div className="bifurc-hero-badge">
          <span className="bifurc-hero-badge-dot" />
          PASO 2B · MÓDULO DE DESPLIEGUE ULTRARENTABLE (CAPITAL PROPIO / BINGX)
        </div>
        <h1 className="page-title" style={{ fontSize: 26, marginTop: 8 }}>
          Paso 2B: Multiplicación de Capital Propio en BingX
        </h1>
        <p className="page-desc" style={{ maxWidth: 700, marginTop: 6 }}>
          Estrategias agresivas diseñadas para <strong>multiplicar tu capital en BingX</strong> (objetivo ≥1000%).
          Modo Multiplicación Acelerada: optimización del retorno terminal tras comisiones y costes de financiamiento.
        </p>
      </div>

      {/* ACTION CARD */}
      <div
        className="card animate-in"
        style={{
          padding: 20,
          marginBottom: 20,
          background: "linear-gradient(135deg, rgba(99,225,180,0.1), rgba(16,185,129,0.03))",
          border: "1.5px solid var(--accent)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.5px", fontFamily: "monospace" }}>
              [AUTO] EJECUCIÓN AUTÓNOMA MODO ULTRA
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 4, maxWidth: 540 }}>
              Pulsa para configurar SQX con parámetros de multiplicador extremo, arrancar la generación de candidatos y seguir la evolución en directo.
            </div>
          </div>
          <button
            onClick={handleAutoLaunchUltra}
            disabled={launching}
            className="btn btn-primary btn-lg"
            style={{ boxShadow: "0 0 24px rgba(99,225,180,0.3)", fontWeight: 700 }}
          >
            {launching ? "INICIANDO BÚSQUEDA..." : "LANZAR BÚSQUEDA ULTRA (1-CLIC)"}
          </button>
        </div>
        {statusMsg && (
          <div style={{ marginTop: 12, fontSize: 12, color: "var(--accent)", fontWeight: 600, fontFamily: "monospace" }}>
            {statusMsg}
          </div>
        )}
      </div>

      {/* PIPELINE DE FASES */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 800, marginBottom: 12, color: "var(--text-primary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          PIPELINE DEL PROCESO ULTRARENTABLE
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
                  borderColor: p.status === "ACTIVO" ? "var(--border-active)" : "var(--border)",
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
                        : p.status === "EN COLAS"
                        ? "var(--info-dim)"
                        : p.status === "REQUIERE TU OK"
                        ? "var(--danger-dim)"
                        : "var(--bg-3)",
                    color:
                      p.status === "ACTIVO"
                        ? "var(--success)"
                        : p.status === "EN COLAS"
                        ? "var(--info)"
                        : p.status === "REQUIERE TU OK"
                        ? "var(--danger)"
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

      {/* CANDIDATOS / ESTRATEGIAS LISTAS */}
      <div className="card animate-in" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h2 className="card-title" style={{ fontSize: 16 }}>Estrategias Rentables Listas ({rentable.length})</h2>
          <Link href="/leaderboard" className="btn btn-sm btn-secondary" style={{ textDecoration: "none", fontSize: 11 }}>
            Ver tabla completa →
          </Link>
        </div>
        {rentable.length === 0 ? (
          <div style={{ padding: "26px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            Cargando candidatos validados... Pulsa <strong>Lanzar Búsqueda Ultra</strong> para generar nuevos candidatos.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {rentable.map((s: any) => (
              <div
                key={s.strategyId}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: 12,
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--border)",
                  background: "var(--bg-2)",
                  flexWrap: "wrap",
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ fontWeight: 800, fontSize: 14 }}>{s.name}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2, fontFamily: "monospace" }}>
                    Retorno OS: +{Number(s.netReturnOosPct || s.netReturnPct || 0).toFixed(1)}% · PF OS: {Number(s.profitFactorOos || s.profitFactor || 0).toFixed(2)} · Trades: {s.tradesCount}
                  </div>
                </div>
                <Link href={`/strategies?id=${s.strategyId}`} className="btn btn-sm btn-primary" style={{ textDecoration: "none", fontSize: 11, fontWeight: 700 }}>
                  Ver Ficha Estrategia
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* CAMBIO DE CAMINO */}
      <div className="bifurc-assist animate-in" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <div className="bifurc-assist-text" style={{ flex: 1, minWidth: 240 }}>
          <strong style={{ color: "var(--text-primary)" }}>¿Prefieres preparar cuentas de fondeo?</strong> Si tu objetivo es pasar evaluaciones de prop-firms con drawdown estricto.
        </div>
        <Link href="/fondeo" className="btn btn-primary" style={{ textDecoration: "none", fontWeight: 700 }}>
          Paso 2A: Ir al Modo Fondeo →
        </Link>
      </div>
    </div>
  );
}
