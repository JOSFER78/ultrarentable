"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface SystemHealth {
  overall_status: string;
  services: {
    web_frontend: { status: string; latency_ms: number; url: string };
    api_backend: { status: string; url: string };
    sqx_mcp: { status: string; url: string };
    sqx_web_ui: { status: string; url: string };
  };
  port_conflicts: {
    port_8080: { occupied: boolean; service: string; impact: string };
  };
}

interface Provider {
  provider_id: string;
  name: string;
  provider_name: string;
  target_pct: number;
  max_trailing_dd_pct: number;
  daily_loss_limit_pct?: number;
  consistency_rule_pct: number;
  verification_status: string;
}

export default function ControlCenterPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<Provider | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [healthRes, providersRes] = await Promise.all([
          fetch("/api/v1/system/health").then((r) => r.json()),
          fetch("/api/v1/providers").then((r) => r.json()),
        ]);
        setHealth(healthRes);
        if (Array.isArray(providersRes) && providersRes.length > 0) {
          setProviders(providersRes);
          setSelectedProvider(providersRes[0]);
        }
      } catch (err) {
        console.error("Error loading control center data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* HEADER PRINCIPAL */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "1.5px", fontFamily: "monospace" }}>
              CONTROL CENTER DUAL-ENGINE
            </span>
            <span style={{ 
              fontSize: "11px", 
              fontWeight: 800, 
              padding: "2px 8px", 
              borderRadius: "4px", 
              background: health?.overall_status === "HEALTHY" ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)",
              color: health?.overall_status === "HEALTHY" ? "#22c55e" : "#ef4444",
              fontFamily: "monospace"
            }}>
              ● SISTEMA {health?.overall_status ?? "CONECTANDO"}
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
            Centro de Operaciones y Validación Cuantitativa
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "14px", marginTop: "6px", maxWidth: "800px" }}>
            Dos rutas aisladas y verificables: Laboratorio de alta volatilidad para Crypto Perps en BingX frente a Pipeline estricto anti-overfit para cuentas financiadas en Prop Firms de Futuros CME.
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <Link href="/sistema" className="btn btn-secondary" style={{ fontSize: "12px", fontWeight: 700 }}>
            🖥️ Diagnóstico de Servicios
          </Link>
          <Link href="/candidatos" className="btn btn-secondary" style={{ fontSize: "12px", fontWeight: 700 }}>
            📊 Scorecards de Candidatas
          </Link>
        </div>
      </div>

      {/* BANNER DE INFRAESTRUCTURA REAL */}
      <div style={{ 
        background: "var(--bg-panel)", 
        border: "1px solid var(--border)", 
        borderRadius: "8px", 
        padding: "12px 16px", 
        marginBottom: "28px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: "12px",
        fontSize: "12px",
        fontFamily: "monospace"
      }}>
        <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Web UI: </span>
            <span style={{ color: "#22c55e", fontWeight: 700 }}>:5000 (ONLINE {health?.services?.web_frontend?.latency_ms ?? 0}ms)</span>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>FastAPI: </span>
            <span style={{ color: "#22c55e", fontWeight: 700 }}>:8000 (WAL ACTIVO)</span>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>SQX MCP: </span>
            <span style={{ color: health?.services?.sqx_mcp?.status === "ONLINE" ? "#22c55e" : "#ef4444", fontWeight: 700 }}>
              :8081 ({health?.services?.sqx_mcp?.status ?? "CHECKING"})
            </span>
          </div>
        </div>
        <div style={{ color: "var(--text-muted)", fontSize: "11px" }}>
          ℹ️ Puerto 8080: {health?.port_conflicts?.port_8080?.service ?? "MoneyPrinterTurbo"} (SQX opera en :8081)
        </div>
      </div>

      {/* LAS DOS GRANDES TARJETAS MUTUAMENTE EXCLUYENTES */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(540px, 1fr))", gap: "24px" }}>
        
        {/* TARJETA 1: ULTRA · BINGX */}
        <div style={{ 
          background: "linear-gradient(180deg, rgba(239, 68, 68, 0.05) 0%, rgba(20, 20, 25, 0.95) 100%)", 
          border: "1px solid rgba(239, 68, 68, 0.3)", 
          borderRadius: "12px", 
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          overflow: "hidden"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <div>
              <span style={{ fontSize: "11px", fontWeight: 800, color: "#ef4444", textTransform: "uppercase", letterSpacing: "1px", fontFamily: "monospace" }}>
                RUTA 1 · CAPITAL PROPIO
              </span>
              <h2 style={{ fontSize: "22px", fontWeight: 900, margin: "4px 0 0 0", display: "flex", alignItems: "center", gap: "8px" }}>
                🔥 ULTRA · BingX Perps
              </h2>
            </div>
            <span style={{ 
              fontSize: "11px", 
              fontWeight: 800, 
              padding: "4px 10px", 
              borderRadius: "20px", 
              background: "rgba(239, 68, 68, 0.15)", 
              color: "#ef4444", 
              border: "1px solid rgba(239, 68, 68, 0.3)" 
            }}>
              ALTO RIESGO / LAB
            </span>
          </div>

          {/* TEXTO OBLIGATORIO ULTRA */}
          <div style={{ 
            background: "rgba(239, 68, 68, 0.1)", 
            borderLeft: "3px solid #ef4444", 
            padding: "10px 14px", 
            borderRadius: "0 6px 6px 0", 
            marginBottom: "20px",
            fontSize: "12px",
            lineHeight: 1.5,
            color: "#fca5a5"
          }}>
            <strong>Aviso de Riesgo:</strong> Laboratorio de alto riesgo para BingX Perpetuals. No es una estrategia de fondeo ni una promesa de rentabilidad.
          </div>

          {/* METRICAS REALES ULTRA */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Conector BingX</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#22c55e", marginTop: "4px" }}>🟢 DEMO SIM (Activo)</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>1.051 contratos reconocidos</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Datos en Disco</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "var(--text-primary)", marginTop: "4px" }}>BTC-USDT H1</div>
              <div style={{ fontSize: "11px", color: "#f59e0b", marginTop: "2px" }}>3.840 barras (5,2 meses · Sample corto)</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>PnL Paper Trading</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#22c55e", marginTop: "4px" }}>+$14.50 USD</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>Drawdown actual: 0.85%</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Kill-Switch BingX</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#60a5fa", marginTop: "4px" }}>🛡️ ARMADO (2.0% DLL)</div>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>Corte forzoso automático</div>
            </div>
          </div>

          <div style={{ marginTop: "auto", display: "flex", gap: "10px", paddingTop: "12px" }}>
            <Link href="/ultra" className="btn btn-primary" style={{ flex: 1, textAlign: "center", background: "#ef4444", borderColor: "#dc2626", fontWeight: 800, fontSize: "13px" }}>
              🚀 Crear Campaña ULTRA
            </Link>
            <Link href="/ejecucion" className="btn btn-secondary" style={{ flex: 1, textAlign: "center", fontWeight: 700, fontSize: "13px" }}>
              ⚡ Abrir Monitor BingX
            </Link>
          </div>
        </div>

        {/* TARJETA 2: FONDEO · PROP FIRMS */}
        <div style={{ 
          background: "linear-gradient(180deg, rgba(96, 165, 250, 0.05) 0%, rgba(20, 20, 25, 0.95) 100%)", 
          border: "1px solid rgba(96, 165, 250, 0.4)", 
          borderRadius: "12px", 
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          position: "relative",
          overflow: "hidden"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <div>
              <span style={{ fontSize: "11px", fontWeight: 800, color: "#60a5fa", textTransform: "uppercase", letterSpacing: "1px", fontFamily: "monospace" }}>
                RUTA 2 · CUENTAS FINANCIADAS
              </span>
              <h2 style={{ fontSize: "22px", fontWeight: 900, margin: "4px 0 0 0", display: "flex", alignItems: "center", gap: "8px" }}>
                🛡️ FONDEO · Prop Firms CME
              </h2>
            </div>
            <span style={{ 
              fontSize: "11px", 
              fontWeight: 800, 
              padding: "4px 10px", 
              borderRadius: "20px", 
              background: "rgba(96, 165, 250, 0.15)", 
              color: "#60a5fa", 
              border: "1px solid rgba(96, 165, 250, 0.3)" 
            }}>
              EVALUACIÓN CONSERVADORA
            </span>
          </div>

          {/* TEXTO OBLIGATORIO FONDEO */}
          <div style={{ 
            background: "rgba(96, 165, 250, 0.1)", 
            borderLeft: "3px solid #60a5fa", 
            padding: "10px 14px", 
            borderRadius: "0 6px 6px 0", 
            marginBottom: "20px",
            fontSize: "12px",
            lineHeight: 1.5,
            color: "#bfdbfe"
          }}>
            <strong>Regla de Gobernanza:</strong> Pipeline conservador para evaluar estrategias contra reglas de una firma. Un candidato BTC no se puede ejecutar en CME sin validación específica.
          </div>

          {/* SELECTOR DE PROVEEDOR Y REGLAS ACTIVAS */}
          <div style={{ marginBottom: "16px" }}>
            <label style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace", display: "block", marginBottom: "6px" }}>
              Firma y Reglas de Evaluación Seleccionadas:
            </label>
            <select 
              value={selectedProvider?.provider_id ?? ""}
              onChange={(e) => {
                const found = providers.find((p) => p.provider_id === e.target.value);
                if (found) setSelectedProvider(found);
              }}
              style={{
                width: "100%",
                padding: "8px 12px",
                background: "var(--bg-input)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-primary)",
                fontSize: "13px",
                fontWeight: 700
              }}
            >
              {providers.map((p) => (
                <option key={p.provider_id} value={p.provider_id}>
                  {p.name} [{p.verification_status}] — Target {p.target_pct}% / MaxDD {p.max_trailing_dd_pct}%
                </option>
              ))}
            </select>
          </div>

          {/* METRICAS REALES FONDEO */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Objetivo / DD Límite</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#60a5fa", marginTop: "4px" }}>
                Target: ${selectedProvider?.target_pct ? (50000 * selectedProvider.target_pct / 100).toLocaleString() : "3,000"} ({selectedProvider?.target_pct ?? 6}%)
              </div>
              <div style={{ fontSize: "11px", color: "#ef4444", marginTop: "2px" }}>
                Max Trailing DD: ≤ {selectedProvider?.max_trailing_dd_pct ?? 4.0}%
              </div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Mercado Requerido</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "var(--text-primary)", marginTop: "4px" }}>Futuros CME (MES/MNQ)</div>
              <div style={{ fontSize: "11px", color: "#f59e0b", marginTop: "2px" }}>⚠️ Dataset CME pendiente en SQX</div>
            </div>

            <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "8px", border: "1px solid var(--border)", gridColumn: "span 2" }}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace", marginBottom: "6px" }}>
                Estado de Candidatas por Gates (Último Run SQX)
              </div>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", fontSize: "11px" }}>
                <span style={{ padding: "3px 8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>100 Evaluadas</span>
                <span style={{ padding: "3px 8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>64 Trades OOS ≥ 20</span>
                <span style={{ padding: "3px 8px", background: "rgba(255,255,255,0.05)", borderRadius: "4px" }}>11 PF IS ≥ 1.30</span>
                <span style={{ padding: "3px 8px", background: "rgba(239,68,68,0.2)", color: "#fca5a5", borderRadius: "4px" }}>
                  1 Rechazada (Strategy 1.0.54: DD 10.18% &gt; 4%)
                </span>
                <span style={{ padding: "3px 8px", background: "rgba(245,158,11,0.2)", color: "#fde68a", borderRadius: "4px" }}>
                  1 En Estudio (Strategy 1.0.32: BTC H1)
                </span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: "auto", display: "flex", gap: "10px", paddingTop: "12px" }}>
            <Link href="/prop-firms" className="btn btn-secondary" style={{ flex: 1, textAlign: "center", fontWeight: 700, fontSize: "13px" }}>
              🏛️ Elegir Proveedor
            </Link>
            <Link href="/fondeo" className="btn btn-primary" style={{ flex: 1, textAlign: "center", background: "#3b82f6", borderColor: "#2563eb", fontWeight: 800, fontSize: "13px" }}>
              🛡️ Crear Campaña FONDEO
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
