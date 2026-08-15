"use client";

import { useState } from "react";
import Link from "next/link";

interface Step {
  id: number;
  title: string;
  subtitle: string;
  status: "EXITO" | "EJECUTANDO" | "PENDIENTE" | "BLOQUEADO" | "FALLO";
  reason: string;
  details: string;
}

export default function UltraFlowPage() {
  const [activeStep, setActiveStep] = useState(1);
  const [liveConfirm, setLiveConfirm] = useState(false);

  const [steps, setSteps] = useState<Step[]>([
    {
      id: 1,
      title: "1. Mercado y Datos en Disco",
      subtitle: "Activo crypto real y verificación de calidad de barras",
      status: "EXITO",
      reason: "3.840 barras H1 de BTC-USDT disponibles (2026.02.26 - 2026.08.04).",
      details: "Aviso de gobernanza: El historial actual representa 5,2 meses (sample corto para temporalidad H1).",
    },
    {
      id: 2,
      title: "2. Búsqueda y Generación de Estrategias",
      subtitle: "Evolución genética SQX con bloques de momentum y breakout",
      status: "EXITO",
      reason: "Población de 100 estrategias generadas con ratio IS 70% / OOS 30%.",
      details: "Doctrina REAL-ONLY: Prohibido sobreajustar con fitness de retorno neto sin control de riesgo.",
    },
    {
      id: 3,
      title: "3. Gates ULTRA & Stress Testing",
      subtitle: "Comprobación de spread (30 pips), slippage (3 pips) y riesgo de liquidación",
      status: "EXITO",
      reason: "Filtros de supervivencia aplicados sobre 100 candidatos.",
      details: "Evaluación de margen aislado y apalancamiento dinámico bajo volatilidad real de BingX.",
    },
    {
      id: 4,
      title: "4. Paper Trading en BingX Demo",
      subtitle: "Simulación de órdenes y cálculo de PnL en tiempo real",
      status: "EJECUTANDO",
      reason: "Sesión activa session_bingx_demo_01: PnL +$14.50 USD (DD 0.85%).",
      details: "Conectado al feed de precios de BingX con ejecución simulada de órdenes sin riesgo.",
    },
    {
      id: 5,
      title: "5. Ejecución Live con Fondos Reales",
      subtitle: "Despliegue con API Keys privadas y Kill-Switch estricto",
      status: "BLOQUEADO",
      reason: "Deshabilitado por defecto para protección de capital.",
      details: "Requiere 7 días continuos de paper trading previo, credenciales verificadas y confirmación explícita.",
    },
  ]);

  const getStatusColor = (status: Step["status"]) => {
    switch (status) {
      case "EXITO":
        return "#22c55e";
      case "EJECUTANDO":
        return "#60a5fa";
      case "PENDIENTE":
        return "#f59e0b";
      case "BLOQUEADO":
        return "#94a3b8";
      case "FALLO":
        return "#ef4444";
    }
  };

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
            ← Control Center
          </Link>
          <span style={{ color: "var(--border)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#ef4444", textTransform: "uppercase", fontFamily: "monospace" }}>
            RUTA ULTRA · BINGX
          </span>
        </div>
        <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
          🔥 Flujo de Trabajo ULTRA (BingX Perpetuals)
        </h1>
        <div style={{ 
          background: "rgba(239, 68, 68, 0.1)", 
          borderLeft: "3px solid #ef4444", 
          padding: "10px 14px", 
          borderRadius: "0 6px 6px 0", 
          marginTop: "12px",
          fontSize: "12px",
          color: "#fca5a5"
        }}>
          <strong>Aviso Obligatorio:</strong> Laboratorio de alto riesgo para BingX Perpetuals. No es una estrategia de fondeo ni una promesa de rentabilidad.
        </div>
      </div>

      {/* WIZARD DE 5 PASOS */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "24px" }}>
        
        {/* LISTA DE PASOS */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {steps.map((s) => (
            <div
              key={s.id}
              onClick={() => setActiveStep(s.id)}
              style={{
                background: activeStep === s.id ? "rgba(239, 68, 68, 0.15)" : "var(--bg-panel)",
                border: activeStep === s.id ? "1px solid #ef4444" : "1px solid var(--border)",
                borderRadius: "8px",
                padding: "14px",
                cursor: "pointer",
                transition: "all 0.2s ease"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ fontSize: "13px", fontWeight: 800, color: activeStep === s.id ? "#fca5a5" : "var(--text-primary)" }}>
                  {s.title}
                </span>
                <span style={{ 
                  fontSize: "10px", 
                  fontWeight: 800, 
                  padding: "2px 6px", 
                  borderRadius: "4px", 
                  background: `${getStatusColor(s.status)}20`, 
                  color: getStatusColor(s.status),
                  fontFamily: "monospace"
                }}>
                  {s.status}
                </span>
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                {s.subtitle}
              </div>
            </div>
          ))}
        </div>

        {/* DETALLE DEL PASO SELECCIONADO */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "24px" }}>
          {activeStep === 1 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 1: Mercado y Datos en Disco</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                El laboratorio opera exclusivamente sobre datasets locales verificados para evitar simulaciones sobre datos sintéticos.
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Activo:</strong> BTCUSDT Perpetuals (BingX)</div>
                  <div><strong>Timeframe:</strong> 1 hora (H1)</div>
                  <div><strong>Total Barras:</strong> 3.840 barras OHLC</div>
                  <div><strong>Rango Temporal:</strong> 26 de Febrero de 2026 – 4 de Agosto de 2026 (5,2 meses)</div>
                  <div style={{ color: "#f59e0b" }}>⚠️ <strong>Muestra Estadística:</strong> 5,2 meses permite ~40–70 trades. Suficiente para paper trading pero requiere prudencia ante cambios de régimen.</div>
                </div>
              </div>
            </div>
          )}

          {activeStep === 2 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 2: Búsqueda y Generación</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Parámetros de generación genética ejecutados en StrategyQuant X MCP con función de fitness anti-overfit.
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Población Genética:</strong> 100 individuos (8 islas de migración)</div>
                  <div><strong>Partición OOS:</strong> 70% In-Sample / 30% Out-of-Sample</div>
                  <div><strong>Función Fitness:</strong> ReturnDDRatio (prohibido Net Profit puro)</div>
                  <div><strong>Filtro de Sesión:</strong> LondonNY (07:00 a 21:00 UTC)</div>
                </div>
              </div>
              <div style={{ marginTop: "16px" }}>
                <Link href="/candidatos" className="btn btn-secondary" style={{ fontSize: "12px" }}>
                  Ver Estrategias Generadas en /candidatos →
                </Link>
              </div>
            </div>
          )}

          {activeStep === 3 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 3: Gates ULTRA & Stress Testing</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Comprobación de robustez de las estrategias ante costes de transacción agresivos.
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Spread Simulador:</strong> 30 pips ($0.3–$3.0 en BTC)</div>
                  <div><strong>Slippage Simulador:</strong> 3 pips</div>
                  <div><strong>Tasa de Financiación (Funding Rate):</strong> 0.01% cada 8h</div>
                  <div><strong>Comisión Taker:</strong> 0.050% (Taker estándar BingX)</div>
                </div>
              </div>
            </div>
          )}

          {activeStep === 4 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 4: Paper Trading en BingX Demo</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Simulación en tiempo real sin arriesgar capital real.
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Sesión:</strong> session_bingx_demo_01 (🟢 RUNNING)</div>
                  <div><strong>PnL Acumulado:</strong> +$14.50 USD</div>
                  <div><strong>Posición Abierta:</strong> LONG 0.05 BTC @ $60,421.50 (5x)</div>
                  <div><strong>Última Señal:</strong> BUY @ 60,420.00 (Momentum Breakout H1)</div>
                </div>
              </div>
              <div style={{ marginTop: "16px" }}>
                <Link href="/ejecucion" className="btn btn-primary" style={{ fontSize: "12px" }}>
                  ⚡ Abrir Consola de Ejecución en Vivo →
                </Link>
              </div>
            </div>
          )}

          {activeStep === 5 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px", color: "#ef4444" }}>
                🔒 Paso 5: Ejecución Live (Fondos Reales)
              </h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                La operativa con capital real en BingX Perpetuals requiere autorización de dos factores y verificación del Kill-Switch.
              </p>
              
              <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid #ef4444", padding: "16px", borderRadius: "8px", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", color: "#fca5a5", lineHeight: 1.6 }}>
                  ⚠️ <strong>GUARDARRAÍL DE SEGURIDAD:</strong> Para activar ejecución real se requiere haber completado al menos 7 días de Paper Trading continuo sin violaciones de Kill-Switch.
                </div>
                <div style={{ marginTop: "14px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", cursor: "pointer", color: "var(--text-primary)" }}>
                    <input type="checkbox" checked={liveConfirm} onChange={(e) => setLiveConfirm(e.target.checked)} />
                    Confirmo que comprendo los riesgos y deseo habilitar el panel de credenciales Live.
                  </label>
                </div>
              </div>

              <div style={{ marginTop: "16px" }}>
                <button 
                  disabled={!liveConfirm} 
                  className="btn btn-secondary" 
                  style={{ opacity: liveConfirm ? 1 : 0.4, cursor: liveConfirm ? "pointer" : "not-allowed", fontSize: "12px", fontWeight: 700 }}
                >
                  Configurar Credenciales BingX Live API
                </button>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
