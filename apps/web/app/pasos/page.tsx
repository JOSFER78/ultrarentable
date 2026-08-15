"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

const STEPS = [
  {
    number: 1,
    title: "1. Sincronización de Datos Reales BingX",
    description: "Verifica e ingesta los datos de velas históricas en SQLite WAL para ETH-USDT (1m, 5m, 15m, 1h).",
    badge: "Paso Fundamental",
    actionText: "Ir a Data Pipeline ->",
    actionHref: "/data",
    icon: "[DATA]",
    details: [
      "No se simulan datos sintéticos ni mockups.",
      "Se almacenan en data/db.sqlite3 con WAL habilitado.",
      "Verificación de gaps y huella SHA256 de integridad."
    ]
  },
  {
    number: 2,
    title: "2. Búsqueda y Generación de Estrategias con SQX MCP",
    description: "Conecta con la aplicación StrategyQuant X en puerto 8080 para importar los candidatos a estrategias.",
    badge: "Fábrica SQX",
    actionText: "Ver Conector SQX ->",
    actionHref: "/strategyquant",
    icon: "[SQX]",
    details: [
      "Servidor Jetty HTTP SSE escuchando en http://127.0.0.1:8080/mcp.",
      "Importación neutra a formato StrategySpec (YAML/Pydantic).",
      "Filtrado primario de databanks activos."
    ]
  },
  {
    number: 3,
    title: "3. Backtest y Validación Anti-Sobreajuste",
    description: "Ejecuta el motor determinista FastEngine para certificar cada estrategia fuera de SQX.",
    badge: "Validación 100%",
    actionText: "Ir a Backtester ->",
    actionHref: "/backtest",
    icon: "[TEST]",
    details: [
      "Simulación exacta de comisiones (Taker/Maker), funding rates y spread.",
      "Modelado de margen aislado/cruzado y precios de liquidación BingX.",
      "Evita el sesgo de lookahead y overfitting mediante validación cruzada."
    ]
  },
  {
    number: 4,
    title: "4. Selección de Línea: Fondeo vs. Ultra Extremo",
    description: "Distribuye las estrategias validadas según el objetivo de negocio y perfil de riesgo.",
    badge: "Cuentas Prop",
    actionText: "Ver Tabla Prop Firms ->",
    actionHref: "/prop-firms",
    icon: "[PROP]",
    details: [
      "Línea Fondeo: Cumple drawdown estricto (trailing/static), límites diarios y consistencia.",
      "Línea Ultra Extremo: Apalancamiento dinámico hasta 500x con interés compuesto y harvest.",
      "Clasificación automática en el Leaderboard."
    ]
  },
  {
    number: 5,
    title: "5. Orquestación y Autopiloto Autónomo",
    description: "Hermes Agent supervisa la ejecución, telemetría y degradación de estrategias en vivo.",
    badge: "Autopiloto Live",
    actionText: "Iniciar Autopiloto ->",
    actionHref: "/",
    icon: "[AUTO]",
    details: [
      "Ejecución en modo REAL-ONLY sin Docker.",
      "Supervisión continua de latencia, slippage y salud del API BingX.",
      "Retiro automático de estrategias si sufren degradación de curva."
    ]
  }
];

export default function WizardPasoAPasoPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const [sqxStatus, setSqxStatus] = useState<string>("Cargando...");
  const [backendStatus, setBackendStatus] = useState<string>("Cargando...");

  useEffect(() => {
    api
      .getSQXStatus()
      .then((data) => {
        setBackendStatus("ONLINE");
        setSqxStatus(data.status || "OFFLINE");
      })
      .catch(() => {
        setBackendStatus("OFFLINE");
        setSqxStatus("OFFLINE");
      });
  }, []);

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
          <h1 className="page-title" style={{ margin: 0, fontSize: 26 }}>Guía Paso a Paso — Flujo del Sistema UltraRentable</h1>
        </div>
        <p className="page-desc">
          Construcción y despliegue modular por etapas. Sigue cada paso para pasar desde los datos crudos hasta la ejecución autónoma.
        </p>
      </div>

      {/* SYSTEM STATUS CARDS */}
      <div className="grid grid-3 animate-in" style={{ marginBottom: 24 }}>
        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "1px" }}>1. Backend FastAPI</div>
          <div style={{ fontSize: 15, fontWeight: 800, marginTop: 4, fontFamily: "monospace", color: backendStatus === "RUNNING" || backendStatus === "ONLINE" ? "var(--success)" : "var(--danger)" }}>
            {backendStatus === "RUNNING" || backendStatus === "ONLINE" ? "[ONLINE] 127.0.0.1:8000" : "[OFFLINE] DISCONNECTED"}
          </div>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "1px" }}>2. StrategyQuant X MCP</div>
          <div style={{ fontSize: 15, fontWeight: 800, marginTop: 4, fontFamily: "monospace", color: sqxStatus === "ONLINE" ? "var(--success)" : "var(--warning)" }}>
            {sqxStatus === "ONLINE" ? "[ONLINE] PUERTO 8080" : "[STANDBY] APERTURA REQUERIDA"}
          </div>
        </div>

        <div className="card" style={{ padding: 16 }}>
          <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: "1px" }}>3. Modo de Operación</div>
          <div style={{ fontSize: 15, fontWeight: 800, marginTop: 4, fontFamily: "monospace", color: "var(--accent)" }}>
            [MODE] LOCAL REAL-ONLY
          </div>
        </div>
      </div>

      {/* STEPPER NAV BAR */}
      <div className="card animate-in" style={{ padding: 16, marginBottom: 24, background: "var(--bg-2)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
          {STEPS.map((step) => {
            const isActive = currentStep === step.number;
            const isCompleted = currentStep > step.number;
            return (
              <button
                key={step.number}
                onClick={() => setCurrentStep(step.number)}
                style={{
                  flex: 1,
                  minWidth: 140,
                  padding: "12px 14px",
                  borderRadius: "var(--radius-md)",
                  border: isActive ? "2px solid var(--accent)" : "1px solid var(--border)",
                  background: isActive ? "rgba(53, 216, 232, 0.1)" : isCompleted ? "rgba(72, 218, 145, 0.05)" : "var(--bg-panel)",
                  color: isActive ? "var(--accent)" : isCompleted ? "var(--success)" : "var(--text-secondary)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.2s"
                }}
              >
                <div style={{ fontSize: 10, fontWeight: 800, opacity: 0.8, marginBottom: 2, fontFamily: "monospace" }}>
                  PASO {step.number} {isCompleted ? "[OK]" : ""}
                </div>
                <div style={{ fontSize: 12, fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {step.icon} {step.badge}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* SELECTED STEP DETAIL CARD */}
      {(() => {
        const active = STEPS.find(s => s.number === currentStep)!;
        return (
          <div className="card animate-in" style={{ padding: 28, borderLeft: "5px solid var(--accent)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <span className="badge badge-cyan" style={{ fontSize: 11, padding: "4px 10px", fontFamily: "monospace" }}>
                {active.badge}
              </span>
              <span style={{ fontSize: 12, color: "var(--text-muted)", fontFamily: "monospace" }}>
                PASO {active.number} DE {STEPS.length}
              </span>
            </div>

            <h2 style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>
              {active.title}
            </h2>

            <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 20, lineHeight: 1.6 }}>
              {active.description}
            </p>

            <div style={{ background: "var(--bg-3)", padding: 18, borderRadius: "var(--radius-md)", marginBottom: 24 }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: "var(--text-primary)", marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                Requisitos y Especificaciones Técnicas:
              </div>
              <ul style={{ paddingLeft: 20, margin: 0, fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7 }}>
                {active.details.map((detail, idx) => (
                  <li key={idx}>{detail}</li>
                ))}
              </ul>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <button
                className="btn btn-secondary"
                onClick={() => setCurrentStep(Math.max(1, currentStep - 1))}
                disabled={currentStep === 1}
                style={{ opacity: currentStep === 1 ? 0.5 : 1, fontSize: 12 }}
              >
                &lt; Paso Anterior
              </button>

              <Link href={active.actionHref} className="btn btn-primary" style={{ padding: "8px 18px", fontSize: 13 }}>
                {active.actionText}
              </Link>

              <button
                className="btn btn-secondary"
                onClick={() => setCurrentStep(Math.min(STEPS.length, currentStep + 1))}
                disabled={currentStep === STEPS.length}
                style={{ opacity: currentStep === STEPS.length ? 0.5 : 1, fontSize: 12 }}
              >
                Paso Siguiente &gt;
              </button>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

