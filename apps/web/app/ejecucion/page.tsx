"use client";

import { useEffect, useState, useCallback } from "react";
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

interface Candidate {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  status: string;
}

export default function ExecutionPage() {
  const [activeTab, setActiveTab] = useState<"BINGX" | "PROP_FIRM">("BINGX");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showKillModal, setShowKillModal] = useState(false);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [killReason, setKillReason] = useState("Corte preventivo manual del operador");
  const [deployCandidateId, setDeployCandidateId] = useState<string>("");
  const [deployEnvironment, setDeployEnvironment] = useState<string>("BINGX_PAPER");
  const [deploying, setDeploying] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [sessRes, candRes] = await Promise.all([
        fetch("/api/v1/execution/sessions").then((r) => (r.ok ? r.json() : [])),
        fetch("/api/v1/candidates").then((r) => (r.ok ? r.json() : [])),
      ]);
      if (Array.isArray(sessRes)) setSessions(sessRes);
      if (Array.isArray(candRes)) {
        setCandidates(candRes);
        if (candRes.length > 0 && !deployCandidateId) {
          setDeployCandidateId(candRes[0].candidate_id);
        }
      }
    } catch (err) {
      console.error("Error loading execution data:", err);
    } finally {
      setLoading(false);
    }
  }, [deployCandidateId]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleCreateSession = async () => {
    if (!deployCandidateId) return;
    setDeploying(true);
    try {
      const cand = candidates.find((c) => c.candidate_id === deployCandidateId);
      const res = await fetch("/api/v1/execution/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          route: cand?.route || (activeTab === "BINGX" ? "ULTRA" : "FONDEO"),
          environment: deployEnvironment,
          candidate_id: deployCandidateId,
          symbol: cand?.symbol || "BTC-USDT",
        }),
      });
      if (res.ok) {
        await loadData();
      }
    } catch (err) {
      console.error("Error creating session:", err);
    } finally {
      setDeploying(false);
    }
  };

  const handleTriggerKillSwitch = async () => {
    if (!selectedSessionId) return;
    try {
      await fetch(`/api/v1/execution/sessions/${selectedSessionId}/kill-switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: killReason }),
      });
      setShowKillModal(false);
      loadData();
    } catch (err) {
      console.error("Error triggering kill switch:", err);
    }
  };

  const handleResumeSession = async (sessionId: string) => {
    try {
      await fetch(`/api/v1/execution/sessions/${sessionId}/resume`, {
        method: "POST",
      });
      loadData();
    } catch (err) {
      console.error("Error resuming session:", err);
    }
  };

  const bingxSessions = sessions.filter((s) => s.route === "ULTRA" || s.environment.includes("BINGX"));
  const propFirmSessions = sessions.filter((s) => s.route === "FONDEO" || s.environment.includes("PROP_FIRM"));
  const activeSessions = activeTab === "BINGX" ? bingxSessions : propFirmSessions;

  return (
    <div style={{ padding: "28px", maxWidth: "1440px", margin: "0 auto" }}>
      {/* 1. HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", letterSpacing: "1px", fontFamily: "monospace" }}>
              TELEMETRÍA & GOBERNANZA
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0, color: "#fff" }}>
            ⚡ Terminal de Ejecución & Kill-Switches
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px", margin: 0 }}>
            Doctrina REAL-ONLY: Monitoreo en tiempo real de sesiones reales, control de riesgo y corte de emergencia.
          </p>
        </div>

        {/* TABS DE SELECCIÓN */}
        <div style={{ display: "flex", gap: "6px", background: "rgba(0,0,0,0.5)", padding: "4px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.08)" }}>
          <button
            onClick={() => setActiveTab("BINGX")}
            style={{
              padding: "7px 16px",
              borderRadius: "6px",
              border: "none",
              background: activeTab === "BINGX" ? "rgba(239, 68, 68, 0.2)" : "transparent",
              color: activeTab === "BINGX" ? "#ef4444" : "var(--text-muted)",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            🔥 BingX Crypto Perps ({bingxSessions.length})
          </button>
          <button
            onClick={() => setActiveTab("PROP_FIRM")}
            style={{
              padding: "7px 16px",
              borderRadius: "6px",
              border: "none",
              background: activeTab === "PROP_FIRM" ? "rgba(96, 165, 250, 0.2)" : "transparent",
              color: activeTab === "PROP_FIRM" ? "#60a5fa" : "var(--text-muted)",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            🛡️ Prop Firms CME ({propFirmSessions.length})
          </button>
        </div>
      </div>

      {/* 2. SESIONES ACTIVAS O ESTADO VACÍO REAL */}
      {activeSessions.length === 0 ? (
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "36px 24px", marginBottom: "28px", textAlign: "center" }}>
          <div style={{ fontSize: "32px", marginBottom: "10px" }}>⚡</div>
          <h3 style={{ fontSize: "18px", fontWeight: 800, color: "#fff", margin: "0 0 6px 0" }}>
            0 Sesiones Activas en {activeTab === "BINGX" ? "BingX" : "Prop Firms CME"}
          </h3>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", maxWidth: "600px", margin: "0 auto 20px auto", lineHeight: "1.5" }}>
            Doctrina REAL-ONLY verificada: Cero datos mockeados o simulados. Para iniciar una sesión real o en simulador oficial, selecciona una estrategia aprobada a continuación.
          </p>

          {/* DESPLEGADOR DE NUEVA SESIÓN REAL */}
          <div style={{ maxWidth: "600px", margin: "0 auto", background: "rgba(0,0,0,0.4)", padding: "18px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.08)", textAlign: "left" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", fontFamily: "monospace", textTransform: "uppercase", marginBottom: "10px" }}>
              Desplegar Nueva Sesión de Ejecución
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>Estrategia Aprobada en BD:</label>
                <select
                  value={deployCandidateId}
                  onChange={(e) => setDeployCandidateId(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(0,0,0,0.6)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    color: "#fff",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: 700,
                    outline: "none"
                  }}
                >
                  {candidates
                    .filter((c) => (activeTab === "BINGX" ? c.route === "ULTRA" : c.route === "FONDEO"))
                    .map((c) => (
                      <option key={c.candidate_id} value={c.candidate_id} style={{ background: "#111827" }}>
                        {c.name} — {c.symbol} ({c.timeframe || "1h"}) [{c.status}]
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>Entorno de Ejecución:</label>
                <select
                  value={deployEnvironment}
                  onChange={(e) => setDeployEnvironment(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(0,0,0,0.6)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    color: "#fff",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    fontSize: "12px",
                    fontWeight: 700,
                    outline: "none"
                  }}
                >
                  {activeTab === "BINGX" ? (
                    <>
                      <option value="BINGX_PAPER">BingX Demo / Paper Trading (Feed Real)</option>
                      <option value="BINGX_LIVE">BingX Live (Cuenta Real / Capital Propio)</option>
                    </>
                  ) : (
                    <>
                      <option value="PROP_FIRM_EVAL">Prop Firm Combine / Examen (NinjaTrader 8)</option>
                      <option value="PROP_FIRM_FUNDED">Prop Firm Cuenta Fondeada (Preservación)</option>
                    </>
                  )}
                </select>
              </div>

              <button
                onClick={handleCreateSession}
                disabled={deploying}
                style={{
                  marginTop: "6px",
                  background: activeTab === "BINGX" ? "#ef4444" : "#2563eb",
                  color: "#fff",
                  padding: "10px",
                  borderRadius: "6px",
                  fontWeight: 800,
                  fontSize: "12px",
                  border: "none",
                  cursor: "pointer"
                }}
              >
                {deploying ? "Iniciando Sesión..." : `🚀 Iniciar Sesión en ${activeTab === "BINGX" ? "BingX" : "Prop Firm"}`}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", marginBottom: "28px" }}>
          {activeSessions.map((s) => (
            <div key={s.session_id} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "16px", fontWeight: 800, color: "#fff" }}>Sesión: {s.session_id}</span>
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
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                    Estrategia: <strong>{s.candidate_id}</strong> · Activo: <strong>{s.symbol}</strong>
                  </div>
                </div>

                <div>
                  {s.kill_switch_active ? (
                    <button
                      onClick={() => handleResumeSession(s.session_id)}
                      style={{
                        background: "#22c55e",
                        color: "#fff",
                        padding: "8px 16px",
                        borderRadius: "6px",
                        fontWeight: 800,
                        fontSize: "12px",
                        border: "none",
                        cursor: "pointer"
                      }}
                    >
                      🟢 Reanudar Sesión
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setSelectedSessionId(s.session_id);
                        setShowKillModal(true);
                      }}
                      style={{
                        background: "rgba(239,68,68,0.15)",
                        border: "1px solid #ef4444",
                        color: "#ef4444",
                        padding: "8px 16px",
                        borderRadius: "6px",
                        fontWeight: 800,
                        fontSize: "12px",
                        cursor: "pointer"
                      }}
                    >
                      🚨 ACTIVAR KILL-SWITCH
                    </button>
                  )}
                </div>
              </div>

              {/* MÉTRICAS */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", marginBottom: "16px" }}>
                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>PnL ACUMULADO</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.current_pnl_usd >= 0 ? "#22c55e" : "#ef4444", marginTop: "2px" }}>
                    {s.current_pnl_usd >= 0 ? `+$${s.current_pnl_usd.toFixed(2)}` : `-$${Math.abs(s.current_pnl_usd).toFixed(2)}`} USD
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>PnL DEL DÍA</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.daily_pnl_usd >= 0 ? "#22c55e" : "#ef4444", marginTop: "2px" }}>
                    +${s.daily_pnl_usd.toFixed(2)} USD
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>DRAWDOWN ACTUAL</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.current_drawdown_pct > 2.0 ? "#ef4444" : "#fff", marginTop: "2px" }}>
                    {s.current_drawdown_pct.toFixed(2)}%
                  </div>
                </div>

                <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "monospace" }}>ESTADO KILL-SWITCH</div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: s.kill_switch_active ? "#ef4444" : "#22c55e", marginTop: "2px" }}>
                    {s.kill_switch_active ? "🚨 DISPARADO" : "🛡️ ARMADO (2.0%)"}
                  </div>
                </div>
              </div>

              {/* TELEMETRÍA */}
              <div style={{ background: "rgba(0,0,0,0.4)", padding: "14px", borderRadius: "8px", fontFamily: "monospace", fontSize: "11px", display: "flex", flexDirection: "column", gap: "6px" }}>
                <div><strong style={{ color: "var(--accent)" }}>Última Señal:</strong> {s.last_signal ?? "Sin señales registradas"}</div>
                <div><strong style={{ color: "#60a5fa" }}>Última Orden:</strong> {s.last_order ?? "Sin órdenes registradas"}</div>
                {s.kill_switch_reason && (
                  <div style={{ color: "#fca5a5" }}><strong>Causa Kill-Switch:</strong> {s.kill_switch_reason}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 3. MODAL KILL-SWITCH */}
      {showKillModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", backdropFilter: "blur(6px)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
          <div style={{ background: "#10141f", border: "1px solid rgba(239,68,68,0.4)", borderRadius: "12px", width: "100%", maxWidth: "500px", padding: "24px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#ef4444", margin: "0 0 10px 0" }}>
              🚨 Activar Kill-Switch de Emergencia
            </h3>
            <p style={{ color: "var(--text-muted)", fontSize: "13px", margin: "0 0 16px 0" }}>
              Esta acción cerrará inmediatamente todas las posiciones abiertas y detendrá el envío de nuevas órdenes.
            </p>

            <label style={{ fontSize: "11px", color: "var(--text-muted)", display: "block", marginBottom: "4px" }}>Motivo del Corte:</label>
            <input
              type="text"
              value={killReason}
              onChange={(e) => setKillReason(e.target.value)}
              style={{
                width: "100%",
                background: "rgba(0,0,0,0.5)",
                border: "1px solid rgba(255,255,255,0.15)",
                color: "#fff",
                padding: "8px 10px",
                borderRadius: "6px",
                fontSize: "12px",
                marginBottom: "20px",
                outline: "none"
              }}
            />

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
              <button
                onClick={() => setShowKillModal(false)}
                style={{
                  background: "transparent",
                  border: "1px solid rgba(255,255,255,0.15)",
                  color: "var(--text-muted)",
                  padding: "8px 14px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleTriggerKillSwitch}
                style={{
                  background: "#ef4444",
                  border: "none",
                  color: "#fff",
                  padding: "8px 16px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: "pointer"
                }}
              >
                Confirmar Corte de Emergencia
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
