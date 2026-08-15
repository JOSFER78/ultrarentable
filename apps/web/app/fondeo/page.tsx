"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Provider {
  provider_id: string;
  name: string;
  provider_name: string;
  platform: string;
  allowed_instruments: string;
  account_size: number;
  target_pct: number;
  max_trailing_dd_pct: number;
  daily_loss_limit_pct?: number;
  consistency_rule_pct: number;
  verification_status: string;
  source_url?: string;
  verified_at?: string;
}

export default function FondeoFlowPage() {
  const [activeStep, setActiveStep] = useState(1);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);

  useEffect(() => {
    fetch("/api/v1/providers")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setProviders(data);
          setSelectedProvider(data[0]);
        }
      })
      .catch((err) => console.error("Error loading providers:", err));
  }, []);

  const steps = [
    { id: 1, title: "1. Seleccionar Proveedor", status: "EXITO", desc: selectedProvider?.name ?? "Cargando..." },
    { id: 2, title: "2. Cuenta y Reglas de Evaluación", status: "EXITO", desc: `Target ${selectedProvider?.target_pct ?? 6}% | MaxDD ${selectedProvider?.max_trailing_dd_pct ?? 4}%` },
    { id: 3, title: "3. Mercado y Dataset Compatible", status: "BLOQUEADO", desc: "⚠️ Requiere dataset Futuros CME (MES/MNQ)" },
    { id: 4, title: "4. Búsqueda SQX Anti-Overfit", status: "EXITO", desc: "Fitness ReturnDDRatio + WFO activo" },
    { id: 5, title: "5. Gates Canónicos de Fondeo", status: "EXITO", desc: "Trades OOS ≥ 20, PF OOS ≥ 1.25, DD ≤ 4%" },
    { id: 6, title: "6. Exportar a NinjaTrader / Tradovate", status: "PENDIENTE", desc: "Generación de script C# / EasyLanguage" },
    { id: 7, title: "7. Paper Trading Pre-Examen", status: "PENDIENTE", desc: "7 días de consistencia en simulador" },
    { id: 8, title: "8. Evaluación en Cuenta Financiada", status: "PENDIENTE", desc: "Paso de examen y cobro de payouts" },
  ];

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
            ← Control Center
          </Link>
          <span style={{ color: "var(--border)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#60a5fa", textTransform: "uppercase", fontFamily: "monospace" }}>
            RUTA FONDEO · PROP FIRMS
          </span>
        </div>
        <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
          🛡️ Flujo de Trabajo FONDEO (Cuentas Financiadas CME)
        </h1>
        <div style={{ 
          background: "rgba(96, 165, 250, 0.1)", 
          borderLeft: "3px solid #60a5fa", 
          padding: "10px 14px", 
          borderRadius: "0 6px 6px 0", 
          marginTop: "12px",
          fontSize: "12px",
          color: "#bfdbfe"
        }}>
          <strong>Regla de Gobernanza:</strong> Pipeline conservador para evaluar estrategias contra reglas de una firma. Un candidato BTC no se puede ejecutar en CME sin validación específica.
        </div>
      </div>

      {/* WIZARD DE 8 PASOS */}
      <div style={{ display: "grid", gridTemplateColumns: "340px 1fr", gap: "24px" }}>
        
        {/* LISTA DE PASOS */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          {steps.map((s) => (
            <div
              key={s.id}
              onClick={() => setActiveStep(s.id)}
              style={{
                background: activeStep === s.id ? "rgba(96, 165, 250, 0.15)" : "var(--bg-panel)",
                border: activeStep === s.id ? "1px solid #60a5fa" : "1px solid var(--border)",
                borderRadius: "8px",
                padding: "12px 14px",
                cursor: "pointer",
                transition: "all 0.2s ease"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                <span style={{ fontSize: "12px", fontWeight: 800, color: activeStep === s.id ? "#93c5fd" : "var(--text-primary)" }}>
                  {s.title}
                </span>
                <span style={{ 
                  fontSize: "9px", 
                  fontWeight: 800, 
                  padding: "2px 5px", 
                  borderRadius: "4px", 
                  background: s.status === "EXITO" ? "rgba(34, 197, 94, 0.2)" : s.status === "BLOQUEADO" ? "rgba(239, 68, 68, 0.2)" : "rgba(255, 255, 255, 0.05)", 
                  color: s.status === "EXITO" ? "#22c55e" : s.status === "BLOQUEADO" ? "#fca5a5" : "var(--text-muted)",
                  fontFamily: "monospace"
                }}>
                  {s.status}
                </span>
              </div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                {s.desc}
              </div>
            </div>
          ))}
        </div>

        {/* DETALLE DEL PASO SELECCIONADO */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "24px" }}>
          
          {activeStep === 1 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 1: Seleccionar Proveedor de Fondeo</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Elige la firma de evaluación con reglas verificadas en la base de datos:
              </p>
              <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "10px" }}>
                {providers.map((p) => (
                  <div
                    key={p.provider_id}
                    onClick={() => setSelectedProvider(p)}
                    style={{
                      padding: "12px",
                      borderRadius: "6px",
                      border: selectedProvider?.provider_id === p.provider_id ? "2px solid #60a5fa" : "1px solid var(--border)",
                      background: selectedProvider?.provider_id === p.provider_id ? "rgba(96, 165, 250, 0.1)" : "rgba(0,0,0,0.2)",
                      cursor: "pointer",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center"
                    }}
                  >
                    <div>
                      <div style={{ fontSize: "13px", fontWeight: 800 }}>{p.name}</div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                        Plataforma: {p.platform} · Instrumentos: {p.allowed_instruments}
                      </div>
                    </div>
                    <span style={{ 
                      fontSize: "10px", 
                      fontWeight: 800, 
                      padding: "2px 6px", 
                      borderRadius: "4px", 
                      background: p.verification_status === "VERIFIED" ? "rgba(34, 197, 94, 0.2)" : "rgba(245, 158, 11, 0.2)", 
                      color: p.verification_status === "VERIFIED" ? "#22c55e" : "#f59e0b" 
                    }}>
                      {p.verification_status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeStep === 2 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 2: Cuenta y Reglas de Evaluación</h2>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Firma:</strong> {selectedProvider?.name}</div>
                  <div><strong>Tamaño de Cuenta:</strong> ${selectedProvider?.account_size.toLocaleString()} USD</div>
                  <div><strong>Profit Target:</strong> ${selectedProvider?.target_pct ? (selectedProvider.account_size * selectedProvider.target_pct / 100).toLocaleString() : "3,000"} ({selectedProvider?.target_pct}%)</div>
                  <div><strong>Límite de Pérdida Diaria (DLL):</strong> {selectedProvider?.daily_loss_limit_pct ? `≤ ${selectedProvider.daily_loss_limit_pct}%` : "No exigido en eval"}</div>
                  <div><strong>Drawdown Máximo Trailing:</strong> ≤ {selectedProvider?.max_trailing_dd_pct}%</div>
                  <div><strong>Regla de Consistencia:</strong> ≤ {selectedProvider?.consistency_rule_pct}% de profit en un solo día</div>
                  <div><strong>Fuente Verificada:</strong> <a href={selectedProvider?.source_url} target="_blank" style={{ color: "#60a5fa" }}>{selectedProvider?.source_url}</a></div>
                </div>
              </div>
            </div>
          )}

          {activeStep === 3 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px", color: "#f59e0b" }}>
                ⚠️ Paso 3: Mercado y Dataset Compatible (Bloqueo Preventivo)
              </h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Las prop firms de futuros operan exclusivamente en contratos regulados de Chicago Mercantile Exchange (CME).
              </p>

              <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid #ef4444", padding: "16px", borderRadius: "8px", marginTop: "16px" }}>
                <div style={{ fontSize: "13px", fontWeight: 800, color: "#fca5a5", marginBottom: "6px" }}>
                  🚫 BLOQUEO ACTIVO DE CAMPAÑA FONDEO:
                </div>
                <div style={{ fontSize: "12px", color: "#fca5a5", lineHeight: 1.6 }}>
                  Actualmente el disco solo contiene el histórico <strong>BTCUSDT H1</strong> (Crypto BingX). No se permite lanzar una campaña de Fondeo certificada sin antes cargar en StrategyQuant X el dataset de futuros CME (ej. <strong>MES</strong> Micro E-mini S&P 500 o <strong>MNQ</strong> Micro E-mini Nasdaq).
                </div>
              </div>

              <div style={{ marginTop: "16px", display: "flex", gap: "10px" }}>
                <Link href="/candidatos" className="btn btn-secondary" style={{ fontSize: "12px" }}>
                  Ver Candidatas en Investigación (BTC) →
                </Link>
              </div>
            </div>
          )}

          {activeStep === 4 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 4: Búsqueda SQX Anti-Overfit</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                El generador XML de StrategyQuant X está configurado con 10/10 filtros de robustez.
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Fitness Function:</strong> ReturnDDRatio (prioriza Sharpe/Calmar y penaliza DD)</div>
                  <div><strong>Walk-Forward Optimization:</strong> 5 folds con exigencia de ≥70% de ejecuciones rentables</div>
                  <div><strong>Monte Carlo Retest:</strong> 20 simulaciones aleatorias de slippage</div>
                  <div><strong>Permutación SPP:</strong> Análisis de meseta paramétrica</div>
                </div>
              </div>
            </div>
          )}

          {activeStep === 5 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Paso 5: Gates Canónicos de Fondeo</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Ninguna estrategia avanza a operativa si no cumple los 5 gates matemáticos:
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div><strong>Gate 1 (Muestra):</strong> Trades IS ≥ 30 y Trades OOS ≥ 20</div>
                  <div><strong>Gate 2 (Calidad IS):</strong> Profit Factor IS ≥ 1.30</div>
                  <div><strong>Gate 3 (Consistencia OOS):</strong> Net Profit OOS &gt; 0</div>
                  <div><strong>Gate 4 (Calidad OOS):</strong> Profit Factor OOS ≥ 1.25</div>
                  <div><strong>Gate 5 (Anti-Overfit):</strong> Ratio PF OOS/IS ≥ 0.70 y Max DD OOS ≤ 4.0%</div>
                </div>
              </div>
              <div style={{ marginTop: "16px" }}>
                <Link href="/candidatos" className="btn btn-secondary" style={{ fontSize: "12px" }}>
                  Consultar Scorecards en /candidatos →
                </Link>
              </div>
            </div>
          )}

          {activeStep >= 6 && (
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, marginBottom: "12px" }}>Pasos 6 a 8: Exportación, Paper y Evaluación</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "13px" }}>
                Una vez validada una candidata sobre datos CME, se exporta el código C# a NinjaTrader 8 o Tradovate para iniciar la fase de evaluación.
              </p>
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)", marginTop: "16px" }}>
                <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                  Estado: Pendiente de carga de dataset CME y validación de primera candidata MES/MNQ.
                </div>
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
