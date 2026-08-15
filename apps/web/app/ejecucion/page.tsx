"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Session {
  session_id: string;
  route: string;
  environment: string;
  candidate_id: string;
  symbol: string;
  status: string;
  current_pnl_usd: number;
  daily_pnl_usd: number;
  current_drawdown_pct: number;
  peak_equity_usd: number;
  heartbeat_last_at: string;
  last_signal: string;
  last_order: string;
  open_positions: any[];
  kill_switch_active: boolean;
  kill_switch_reason?: string;
}

export default function ExecutionPage() {
  const [activeTab, setActiveTab] = useState<"BINGX" | "PROP_FIRM">("BINGX");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showKillModal, setShowKillModal] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [killReason, setKillReason] = useState("Corte manual preventivo por parte del operador");

  const loadSessions = () => {
    fetch("/api/v1/execution/sessions")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setSessions(data);
      })
      .catch((err) => console.error("Error loading sessions:", err));
  };

  useEffect(() => {
    loadSessions();
    const interval = setInterval(loadSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerKillSwitch = async () => {
    if (!selectedSessionId) return;
    try {
      await fetch(`/api/v1/execution/sessions/${selectedSessionId}/kill-switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: killReason }),
      });
      setShowKillModal(false);
      loadSessions();
    } catch (err) {
      console.error("Error triggering kill switch:", err);
    }
  };

  const handleResumeSession = async (sessionId: string) => {
    try {
      await fetch(`/api/v1/execution/sessions/${sessionId}/resume`, {
        method: "POST",
      });
      loadSessions();
    } catch (err) {
      console.error("Error resuming session:", err);
    }
  };

  const bingxSessions = sessions.filter((s) => s.route === "ULTRA" || s.environment.includes("BINGX"));
  const propFirmSessions = sessions.filter((s) => s.route === "FONDEO" || s.environment.includes("PROP_FIRM"));

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", fontFamily: "monospace" }}>
              CONSOLA DE EJECUCIÓN
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
            ⚡ Ejecución en Vivo, Telemetría y Kill-Switches
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Monitoreo en tiempo real con aislamiento estricto entre BingX Perpetuals y Evaluaciones de Prop Firms.
          </p>
        </div>

        {/* TABS DE SELECCION */}
        <div style={{ display: "flex", gap: "8px", background: "var(--bg-panel)", padding: "4px", borderRadius: "8px", border: "1px solid var(--border)" }}>
          <button
            onClick={() => setActiveTab("BINGX")}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: "none",
              background: activeTab === "BINGX" ? "rgba(239, 68, 68, 0.2)" : "transparent",
              color: activeTab === "BINGX" ? "#ef4444" : "var(--text-muted)",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            🔥 BingX (Paper / Live)
          </button>
          <button
            onClick={() => setActiveTab("PROP_FIRM")}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: "none",
              background: activeTab === "PROP_FIRM" ? "rgba(96, 165, 250, 0.2)" : "transparent",
              color: activeTab === "PROP_FIRM" ? "#60a5fa" : "var(--text-muted)",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            🛡️ Prop Firms (Paper / Eval)
          </button>
        </div>
      </div>

      {/* CONTENIDO TAB BINGX */}
      {activeTab === "BINGX" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {bingxSessions.map((s) => (
            <div key={s.session_id} style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "20px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "16px", fontWeight: 800 }}>Sesión: {s.session_id}</span>
                    <span style={{ 
                      fontSize: "11px", 
                      fontWeight: 800, 
                      padding: "2px 8px", 
                      borderRadius: "4px", 
                      background: s.status === "RUNNING" ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
                      color: s.status === "RUNNING" ? "#22c55e" : "#ef4444",
                      fontFamily: "monospace"
                    }}>
                      ● {s.status}
                    </span>
                    <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>
                      ({s.environment})
                    </span>
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                    Estrategia Asignada: <strong>{s.candidate_id}</strong> · Activo: <strong>{s.symbol}</strong>
                  </div>
                </div>

                <div style={{ display: "flex", gap: "10px" }}>
                  {s.kill_switch_active ? (
                    <button
                      onClick={() => handleResumeSession(s.session_id)}
                      className="btn btn-primary"
                      style={{ fontSize: "12px", fontWeight: 800, background: "#22c55e", borderColor: "#16a34a" }}
                    >
                      🟢 Reanudar Sesión
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setSelectedSessionId(s.session_id);
                        setShowKillModal(true);
                      }}
                      className="btn btn-secondary"
                      style={{ fontSize: "12px", fontWeight: 800, color: "#ef4444", borderColor: "#ef4444" }}
                    >
                      🚨 ACTIVAR KILL-SWITCH
                    </button>
                  )}
                </div>
              </div>

              {/* METRICAS DE SESION */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", marginBottom: "16px" }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>PnL ACUMULADO</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.current_pnl_usd >= 0 ? "#22c55e" : "#ef4444", marginTop: "2px" }}>
                    {s.current_pnl_usd >= 0 ? `+$${s.current_pnl_usd.toFixed(2)}` : `-$${Math.abs(s.current_pnl_usd).toFixed(2)}`} USD
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>PnL DEL DÍA</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.daily_pnl_usd >= 0 ? "#22c55e" : "#ef4444", marginTop: "2px" }}>
                    +${s.daily_pnl_usd.toFixed(2)} USD
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>DRAWDOWN ACTUAL</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.current_drawdown_pct > 2.0 ? "#ef4444" : "var(--text-primary)", marginTop: "2px" }}>
                    {s.current_drawdown_pct.toFixed(2)}%
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>ESTADO KILL-SWITCH</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.kill_switch_active ? "#ef4444" : "#22c55e", marginTop: "2px" }}>
                    {s.kill_switch_active ? "🚨 DISPARADO" : "🛡️ ARMADO (2.0%)"}
                  </div>
                </div>
              </div>

              {/* TELEMETRIA Y ORDENES */}
              <div style={{ background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "6px", fontFamily: "monospace", fontSize: "11px", display: "flex", flexDirection: "column", gap: "6px" }}>
                <div><strong style={{ color: "var(--accent)" }}>Última Señal:</strong> {s.last_signal ?? "Sin señales recientes"}</div>
                <div><strong style={{ color: "#60a5fa" }}>Última Orden:</strong> {s.last_order ?? "Sin órdenes recientes"}</div>
                {s.kill_switch_reason && (
                  <div style={{ color: "#fca5a5" }}><strong>Causa Kill-Switch:</strong> {s.kill_switch_reason}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CONTENIDO TAB PROP FIRM */}
      {activeTab === "PROP_FIRM" && (
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "30px", textAlign: "center" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🛡️</div>
          <h2 style={{ fontSize: "20px", fontWeight: 800, margin: 0 }}>Módulo de Evaluación de Prop Firms</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", maxWidth: "600px", margin: "10px auto 20px auto" }}>
            Para ejecutar una sesión de evaluación de futuros (Topstep / Apex / TradeDay), primero se debe completar la fase de búsqueda sobre dataset CME y exportar el script a la plataforma autorizada.
          </p>
          <div style={{ display: "flex", gap: "10px", justifyContent: "center" }}>
            <Link href="/fondeo" className="btn btn-primary" style={{ fontSize: "12px", fontWeight: 700 }}>
              Ir al Wizard de Fondeo →
            </Link>
            <Link href="/prop-firms" className="btn btn-secondary" style={{ fontSize: "12px", fontWeight: 700 }}>
              Ver Catálogo de Proveedores
            </Link>
          </div>
        </div>
      )}

      {/* MODAL KILL-SWITCH */}
      {showKillModal && (
        <div style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.8)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 999,
          padding: "20px"
        }}>
          <div style={{ background: "var(--bg-panel)", border: "2px solid #ef4444", borderRadius: "10px", padding: "24px", maxWidth: "480px", width: "100%" }}>
            <h3 style={{ color: "#ef4444", fontSize: "18px", fontWeight: 900, margin: "0 0 10px 0" }}>
              🚨 ACTIVACIÓN DE KILL-SWITCH DE EMERGENCIA
            </h3>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", lineHeight: 1.5 }}>
              Esta acción forzará el <strong>cierre inmediato a mercado (flatten)</strong> de todas las posiciones abiertas y bloqueará la generación de nuevas órdenes.
            </p>
            <div style={{ marginTop: "14px" }}>
              <label style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", fontFamily: "monospace", display: "block", marginBottom: "4px" }}>
                Motivo de la parada:
              </label>
              <input
                type="text"
                value={killReason}
                onChange={(e) => setKillReason(e.target.value)}
                style={{ width: "100%", padding: "8px 12px", background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: "6px", color: "var(--text-primary)", fontSize: "12px" }}
              />
            </div>
            <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
              <button
                onClick={() => setShowKillModal(false)}
                className="btn btn-secondary"
                style={{ flex: 1, fontSize: "12px" }}
              >
                Cancelar
              </button>
              <button
                onClick={handleTriggerKillSwitch}
                className="btn btn-primary"
                style={{ flex: 1, background: "#ef4444", borderColor: "#dc2626", fontWeight: 800, fontSize: "12px" }}
              >
                Confirmar Parada
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
