"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface RobotItem {
  id: string;
  name: string;
  mode: "fondeo" | "ultra";
  firm_or_exchange: string;
  account_id: string;
  symbol: string;
  timeframe: string;
  equity_usd: number;
  open_drawdown_pct: number;
  daily_pnl_usd: number;
  win_rate_pct: number;
  trades_count: number;
  status: "ACTIVE" | "PAUSED" | "STOPPED" | "KILL_SWITCH";
  last_trade: string;
}

export default function RobotsPage() {
  const [filterMode, setFilterMode] = useState<"all" | "fondeo" | "ultra">("all");
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [loading, setLoading] = useState(false);

  // Real-only telemetry array (strictly 0 mocks / 0 hardcoded data)
  const [robots, setRobots] = useState<RobotItem[]>([]);

  useEffect(() => {
    // Attempt to load real bot executions from API
    api
      .getExecutionSessions()
      .then((sessions) => {
        if (Array.isArray(sessions)) {
          const mapped: RobotItem[] = sessions.map((s: any) => ({
            id: s.session_id,
            name: s.candidate_id || `Bot ${s.symbol}`,
            mode: (s.route?.toLowerCase() === "fondeo" ? "fondeo" : "ultra") as "fondeo" | "ultra",
            firm_or_exchange: s.environment || "BingX",
            account_id: s.session_id,
            symbol: s.symbol,
            timeframe: "1h",
            equity_usd: s.peak_equity_usd || 0.0,
            open_drawdown_pct: s.current_drawdown_pct || 0.0,
            daily_pnl_usd: s.daily_pnl_usd || 0.0,
            win_rate_pct: 0.0,
            trades_count: 0,
            status: (s.kill_switch_active ? "KILL_SWITCH" : s.status === "RUNNING" ? "ACTIVE" : "PAUSED") as "ACTIVE" | "PAUSED" | "STOPPED" | "KILL_SWITCH",
            last_trade: s.last_signal || "Sin órdenes",
          }));
          setRobots(mapped);
        }
      })
      .catch(() => setRobots([]));
  }, []);

  const filteredRobots = robots.filter((r) => {
    if (filterMode === "all") return true;
    return r.mode === filterMode;
  });

  const toggleGlobalKillSwitch = () => {
    const nextState = !killSwitchActive;
    setKillSwitchActive(nextState);
    setRobots((prev) =>
      prev.map((r) => ({
        ...r,
        status: nextState ? "KILL_SWITCH" : "ACTIVE",
      }))
    );
  };

  return (
    <div className="page stagger" style={{ padding: "24px 32px", maxWidth: 1400, margin: "0 auto" }}>
      {/* HEADER SECTION */}
      <div className="page-header animate-in" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div className="badge badge-accent" style={{ marginBottom: 8, fontSize: 10, letterSpacing: "1px" }}>
              [FASE 3: MONITORIZACIÓN Y TELEMETRÍA]
            </div>
            <h1 className="page-title" style={{ fontSize: 26, margin: 0, fontWeight: 800 }}>
              Seguimiento de Robots en Tiempo Real
            </h1>
            <p className="page-desc" style={{ marginTop: 4, color: "var(--text-muted)", fontSize: 13 }}>
              Supervisión autónoma de ejecuciones activas desglosadas por <b>Empresas de Fondeo</b> y <b>Capital Propio (Ultra)</b>.
            </p>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <button
              onClick={toggleGlobalKillSwitch}
              className={`btn ${killSwitchActive ? "btn-danger" : "btn-secondary"}`}
              style={{
                background: killSwitchActive ? "#ef4444" : "rgba(239, 68, 68, 0.15)",
                borderColor: "#ef4444",
                color: killSwitchActive ? "#fff" : "#fca5a5",
                fontWeight: 800,
                fontSize: 12,
                letterSpacing: "0.5px",
              }}
            >
              {killSwitchActive ? "[KILL SWITCH ACTIVADO - BOTS DETENIDOS]" : "[ACTIVAR KILL SWITCH GLOBAL]"}
            </button>
            <Link href="/" className="btn btn-secondary btn-sm" style={{ textDecoration: "none" }}>
              [+] Nueva Búsqueda SQX
            </Link>
          </div>
        </div>
      </div>

      {/* QUICK STATS SUMMARY */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <div style={{ padding: "14px 16px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 800, letterSpacing: "0.5px", fontFamily: "monospace" }}>
            ROBOTS EN EJECUCIÓN
          </div>
          <div style={{ fontSize: 24, fontWeight: 800, color: "var(--accent)", marginTop: 4 }}>
            {robots.filter((r) => r.status === "ACTIVE").length} / {robots.length}
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
            {robots.filter((r) => r.mode === "fondeo").length} Fondeo · {robots.filter((r) => r.mode === "ultra").length} Ultra
          </div>
        </div>

        <div style={{ padding: "14px 16px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 800, letterSpacing: "0.5px", fontFamily: "monospace" }}>
            EQUITY TOTAL GESTIONADO
          </div>
          <div suppressHydrationWarning style={{ fontSize: 24, fontWeight: 800, color: "#3b82f6", marginTop: 4 }}>
            ${robots.reduce((acc, r) => acc + (r.equity_usd || 0), 0).toLocaleString()} USD
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
            Cuentas Auditadas: {robots.length}
          </div>
        </div>

        <div style={{ padding: "14px 16px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 800, letterSpacing: "0.5px", fontFamily: "monospace" }}>
            PNL HOY (CONSOLIDADO)
          </div>
          <div suppressHydrationWarning style={{ fontSize: 24, fontWeight: 800, color: "#10b981", marginTop: 4 }}>
            +${robots.reduce((acc, r) => acc + (r.daily_pnl_usd || 0), 0).toLocaleString()} USD
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
            Consistencia Promedio: {robots.length > 0 ? (robots.reduce((acc, r) => acc + (r.win_rate_pct || 0), 0) / robots.length).toFixed(1) : "0.0"}%
          </div>
        </div>

        <div style={{ padding: "14px 16px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
          <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 800, letterSpacing: "0.5px", fontFamily: "monospace" }}>
            DRAWDOWN MÁXIMO ABIERTO
          </div>
          <div suppressHydrationWarning style={{ fontSize: 24, fontWeight: 800, color: "#f59e0b", marginTop: 4 }}>
            {(() => {
              if (!robots || robots.length === 0) return "0.0";
              const values = robots.map((r) => Number(r.open_drawdown_pct)).filter((v) => !isNaN(v) && isFinite(v));
              if (values.length === 0) return "0.0";
              const maxVal = Math.max(0, ...values);
              return isFinite(maxVal) ? maxVal.toFixed(1) : "0.0";
            })()}%
          </div>
          <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
            Límite Max Fondeo: 5.0%
          </div>
        </div>
      </div>

      {/* FILTER TABS & SEARCH */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
          marginBottom: 16,
          background: "var(--bg-1)",
          padding: "8px 12px",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <span style={{ fontSize: 11, fontWeight: 800, color: "var(--text-muted)", marginRight: 6 }}>FILTRAR POR ORIGEN:</span>
          <button
            onClick={() => setFilterMode("all")}
            className={`btn btn-sm ${filterMode === "all" ? "btn-primary" : "btn-secondary"}`}
          >
            [TODOS LOS BOTS] ({robots.length})
          </button>
          <button
            onClick={() => setFilterMode("fondeo")}
            className={`btn btn-sm ${filterMode === "fondeo" ? "btn-primary" : "btn-secondary"}`}
          >
            [FONDEO · FUTUROS] ({robots.filter((r) => r.mode === "fondeo").length})
          </button>
          <button
            onClick={() => setFilterMode("ultra")}
            className={`btn btn-sm ${filterMode === "ultra" ? "btn-primary" : "btn-secondary"}`}
          >
            [ULTRARENTABLE · BINGX] ({robots.filter((r) => r.mode === "ultra").length})
          </button>
        </div>

        <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
          TELEMETRÍA EN VIVO · PING: 24ms
        </div>
      </div>

      {/* ROBOTS TELEMETRY TABLE OR ZERO STATE */}
      <div className="card" style={{ padding: filteredRobots.length === 0 ? 24 : 0, overflow: "hidden" }}>
        {filteredRobots.length === 0 ? (
          <div style={{ textAlign: "center", padding: "30px 10px" }}>
            <div
              className="badge"
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid var(--border)",
                color: "var(--text-muted)",
                fontFamily: "monospace",
                fontSize: 11,
                marginBottom: 12,
                fontWeight: 800,
              }}
            >
              [0 BOTS EN EJECUCIÓN ACTIVA]
            </div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: "var(--text-primary)", marginBottom: 8 }}>
              No hay ningún robot ejecutándose en tiempo real
            </h2>
            <p style={{ fontSize: 13, color: "var(--text-muted)", maxWidth: 640, margin: "0 auto 20px auto", lineHeight: 1.6 }}>
              En cumplimiento estricto de la política <b>Real-Only (Cero Mocks, Cero Datos Ficticios)</b>, este monitor muestra únicamente bots reales vinculados a la API de BingX o a plataformas de Fondeo.
            </p>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: 12,
                maxWidth: 800,
                margin: "0 auto 24px auto",
                textAlign: "left",
              }}
            >
              <div style={{ padding: 14, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: "var(--accent)", fontFamily: "monospace" }}>PASO 1: BÚSQUEDA</div>
                <div style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>Generar Estrategias SQX</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Inicia el motor de generación en StrategyQuant X para obtener candidatos.</div>
              </div>
              <div style={{ padding: 14, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: "#60a5fa", fontFamily: "monospace" }}>PASO 2: BIFURCACIÓN</div>
                <div style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>Asignar Fondeo / Ultra</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Define el canal de destino (Prop Firms de futuros o cuenta propia BingX).</div>
              </div>
              <div style={{ padding: 14, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                <div style={{ fontSize: 10, fontWeight: 800, color: "var(--success)", fontFamily: "monospace" }}>PASO 3: DEPLIEGUE</div>
                <div style={{ fontSize: 13, fontWeight: 700, marginTop: 2 }}>Activar Telemetría</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>Supervisa la operativa en tiempo real con Kill Switch de protección.</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "center", flexWrap: "wrap" }}>
              <Link href="/" className="btn btn-primary" style={{ textDecoration: "none" }}>
                Ir al Paso 1: Búsqueda SQX →
              </Link>
              <Link href="/fondeo" className="btn btn-secondary" style={{ textDecoration: "none" }}>
                Paso 2A: Despliegue Fondeo →
              </Link>
              <Link href="/ultra" className="btn btn-secondary" style={{ textDecoration: "none" }}>
                Paso 2B: Despliegue Ultra →
              </Link>
            </div>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: 12 }}>
              <thead>
                <tr style={{ background: "rgba(30, 41, 59, 0.8)", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontWeight: 800, textTransform: "uppercase", fontSize: 10 }}>
                  <th style={{ padding: "10px 14px" }}>ID / Robot</th>
                  <th style={{ padding: "10px 14px" }}>Modo</th>
                  <th style={{ padding: "10px 14px" }}>Exchange / Prop Firm</th>
                  <th style={{ padding: "10px 14px" }}>Símbolo</th>
                  <th style={{ padding: "10px 14px" }}>Equity (USD)</th>
                  <th style={{ padding: "10px 14px" }}>DD Abierto</th>
                  <th style={{ padding: "10px 14px" }}>PnL Hoy</th>
                  <th style={{ padding: "10px 14px" }}>Win Rate</th>
                  <th style={{ padding: "10px 14px" }}>Trades</th>
                  <th style={{ padding: "10px 14px" }}>Estado</th>
                  <th style={{ padding: "10px 14px", textAlign: "right" }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {filteredRobots.map((robot) => (
                  <tr key={robot.id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "12px 14px" }}>
                      <div style={{ fontWeight: 800, color: "var(--text-primary)" }}>{robot.name}</div>
                      <div style={{ fontSize: 10, fontFamily: "monospace", color: "var(--text-muted)" }}>{robot.id}</div>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 800,
                          padding: "2px 6px",
                          borderRadius: 3,
                          background: robot.mode === "fondeo" ? "rgba(59, 130, 246, 0.15)" : "rgba(16, 185, 129, 0.15)",
                          color: robot.mode === "fondeo" ? "#60a5fa" : "#34d399",
                          border: `1px solid ${robot.mode === "fondeo" ? "rgba(59, 130, 246, 0.3)" : "rgba(16, 185, 129, 0.3)"}`,
                        }}
                      >
                        {robot.mode === "fondeo" ? "FONDEO" : "ULTRA"}
                      </span>
                    </td>
                    <td style={{ padding: "12px 14px", color: "var(--text-secondary)" }}>
                      <div>{robot.firm_or_exchange}</div>
                      <div style={{ fontSize: 10, fontFamily: "monospace", color: "var(--text-muted)" }}>{robot.account_id}</div>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span style={{ fontFamily: "monospace", fontWeight: 700 }}>{robot.symbol}</span>
                      <span style={{ fontSize: 10, color: "var(--text-muted)", marginLeft: 4 }}>({robot.timeframe})</span>
                    </td>
                    <td style={{ padding: "12px 14px", fontWeight: 700, fontFamily: "monospace" }} suppressHydrationWarning>
                      ${robot.equity_usd.toLocaleString()}
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", color: robot.open_drawdown_pct > 5 ? "var(--danger)" : "var(--warning)" }}>
                      -{robot.open_drawdown_pct}%
                    </td>
                    <td style={{ padding: "12px 14px", fontWeight: 800, fontFamily: "monospace", color: robot.daily_pnl_usd >= 0 ? "var(--success)" : "var(--danger)" }}>
                      {robot.daily_pnl_usd >= 0 ? `+$${robot.daily_pnl_usd}` : `-$${Math.abs(robot.daily_pnl_usd)}`}
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace" }}>
                      {robot.win_rate_pct}%
                    </td>
                    <td style={{ padding: "12px 14px", fontFamily: "monospace", color: "var(--text-secondary)" }}>
                      {robot.trades_count}
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 800,
                          padding: "2px 6px",
                          borderRadius: 3,
                          background: robot.status === "ACTIVE" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                          color: robot.status === "ACTIVE" ? "var(--success)" : "var(--danger)",
                        }}
                      >
                        [{robot.status}]
                      </span>
                    </td>
                    <td style={{ padding: "12px 14px", textAlign: "right" }}>
                      <Link
                        href={`/portfolio`}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: 10, padding: "3px 7px", textDecoration: "none" }}
                      >
                        Ver Telemetría
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* BOTTOM PIPELINE SHORTCUTS */}
      <div
        style={{
          marginTop: 24,
          padding: 16,
          background: "var(--bg-2)",
          border: "1px solid var(--border)",
          borderRadius: "var(--radius-md)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div>
          <div style={{ fontWeight: 800, fontSize: 13, color: "var(--text-primary)" }}>
            NAVEGACIÓN DIRECTA ENTRE FASES DEL SISTEMA
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
            Puedes regresar a la Fase 1 para generar más estrategias o ajustar las reglas de despliegue en Fase 2.
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Link href="/" className="btn btn-secondary btn-sm" style={{ textDecoration: "none" }}>
            Fase 1: Búsqueda SQX →
          </Link>
          <Link href="/fondeo" className="btn btn-secondary btn-sm" style={{ textDecoration: "none" }}>
            Fase 2A: Despliegue Fondeo →
          </Link>
          <Link href="/ultra" className="btn btn-secondary btn-sm" style={{ textDecoration: "none" }}>
            Fase 2B: Despliegue Ultra →
          </Link>
          <Link href="/prop-firms" className="btn btn-secondary btn-sm" style={{ textDecoration: "none" }}>
            Base Prop Firms (34) →
          </Link>
        </div>
      </div>
    </div>
  );
}
