"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface PropFirmChallenge {
  id: string;
  name: string;
  account_size: number;
  profit_target: number;
  max_trailing_dd: number;
  daily_loss_limit: number;
  min_trading_days: number;
  consistency_max_pct: number;
  auto_flatten_time: string;
}

const PROP_CATALOG: PropFirmChallenge[] = [
  { id: "topstep_50k", name: "Topstep 50K Combine", account_size: 50000, profit_target: 3000, max_trailing_dd: 2000, daily_loss_limit: 1000, min_trading_days: 2, consistency_max_pct: 50, auto_flatten_time: "15:59 CST" },
  { id: "mffu_50k", name: "MyFundedFutures 50K Starter", account_size: 50000, profit_target: 3000, max_trailing_dd: 2000, daily_loss_limit: 1200, min_trading_days: 1, consistency_max_pct: 40, auto_flatten_time: "15:59 CST" },
  { id: "tradeify_50k", name: "Tradeify 50K Growth", account_size: 50000, profit_target: 2500, max_trailing_dd: 1500, daily_loss_limit: 1000, min_trading_days: 3, consistency_max_pct: 40, auto_flatten_time: "15:59 CST" },
  { id: "apex_50k", name: "Apex Trader Funding 50K", account_size: 50000, profit_target: 3000, max_trailing_dd: 2500, daily_loss_limit: 0, min_trading_days: 1, consistency_max_pct: 30, auto_flatten_time: "15:59 CST" },
];

export default function TrackFondeoCMEPage() {
  const [selectedFirm, setSelectedFirm] = useState<PropFirmChallenge>(PROP_CATALOG[0]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Carga de sesiones reales
  useEffect(() => {
    fetch("/api/v1/execution/sessions?route=FONDEO")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setSessions(Array.isArray(data) ? data : []);
      })
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  const activeSession = sessions.length > 0 ? sessions[0] : null;

  const currentEquity = activeSession ? (selectedFirm.account_size + activeSession.current_pnl_usd) : selectedFirm.account_size;
  const peakEquity = activeSession ? activeSession.peak_equity_usd : selectedFirm.account_size;
  const todayPnl = activeSession ? activeSession.daily_pnl_usd : 0.0;
  const totalProfit = currentEquity - selectedFirm.account_size;
  const targetProgress = Math.min(100, Math.max(0, (totalProfit / selectedFirm.profit_target) * 100));
  const currentDd = Math.max(0, peakEquity - currentEquity);
  const ddBuffer = Math.max(0, selectedFirm.max_trailing_dd - currentDd);
  const ddUsagePct = Math.min(100, (currentDd / selectedFirm.max_trailing_dd) * 100);
  const isDllOk = selectedFirm.daily_loss_limit === 0 || todayPnl > -selectedFirm.daily_loss_limit;

  return (
    <div style={{ padding: "16px 24px", width: "100%", maxWidth: "100%", margin: 0, color: "#f8fafc", boxSizing: "border-box" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            TRACK_FONDEO · INSTITUTIONAL CME PROP FIRMS
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          Dashboard de Fondeo CME & Compliance Guard
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Supervisión estricta de cuentas de evaluación y fondeadas: Trailing DD intra-trade, Daily Loss Limit y regla de consistencia.
        </p>
      </div>

      {/* 2. SELECTOR DE EMPRESA DE FONDEO */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "24px", flexWrap: "wrap" }}>
        {PROP_CATALOG.map((firm) => {
          const isSelected = selectedFirm.id === firm.id;
          return (
            <button
              key={firm.id}
              onClick={() => setSelectedFirm(firm)}
              style={{
                flex: 1,
                minWidth: "220px",
                padding: "14px 16px",
                borderRadius: "10px",
                background: isSelected ? "rgba(56, 189, 248, 0.15)" : "rgba(16, 23, 34, 0.75)",
                border: isSelected ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.08)",
                cursor: "pointer",
                textAlign: "left",
                transition: "all 0.15s ease",
              }}
            >
              <div style={{ fontSize: "12px", fontWeight: 800, color: isSelected ? "#38bdf8" : "#fff" }}>
                {firm.name}
              </div>
              <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>
                Target: ${firm.profit_target} · Max DD: ${firm.max_trailing_dd}
              </div>
            </button>
          );
        })}
      </div>

      {/* 3. MASTER COMPLIANCE METRICS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginBottom: "24px" }}>
        {/* Equity Actual */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            EQUITY REAL DE LA CUENTA
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#fff", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            ${currentEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: "11px", color: totalProfit >= 0 ? "#34d399" : "#f43f5e", marginTop: "4px" }}>
            Beneficio: {totalProfit >= 0 ? `+$${totalProfit.toFixed(2)}` : `-$${Math.abs(totalProfit).toFixed(2)}`} USD
          </div>
        </div>

        {/* Trailing Drawdown Buffer */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            COLCHÓN TRAILING DRAWDOWN
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: ddBuffer > 800 ? "#34d399" : "#f43f5e", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            ${ddBuffer.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            Uso: {ddUsagePct.toFixed(1)}% de ${selectedFirm.max_trailing_dd}
          </div>
        </div>

        {/* Target Progress */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            PROGRESO HACIA TARGET (${selectedFirm.profit_target})
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {targetProgress.toFixed(1)}%
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            Faltan: ${Math.max(0, selectedFirm.profit_target - totalProfit).toFixed(2)}
          </div>
        </div>

        {/* Límite Pérdida Diaria */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            ESTADO DAILY LOSS LIMIT ({selectedFirm.daily_loss_limit > 0 ? `$${selectedFirm.daily_loss_limit}` : "SIN DLL"})
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: isDllOk ? "#34d399" : "#f43f5e", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {isDllOk ? "DENTRO DE LÍMITE" : "🚨 VIOLACIÓN"}
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            PnL Hoy: ${todayPnl.toFixed(2)} USD
          </div>
        </div>
      </div>

      {/* 4. ACTIVE SESSIONS TABLE OR CALL TO ACTION */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px", marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
            Sesiones de Fondeo Registradas en SQLite
          </h2>
          <Link
            href="/ejecucion"
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid #38bdf8",
              color: "#38bdf8",
              fontWeight: 800,
              fontSize: "11px",
              textDecoration: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            ⚡ IR AL CENTRO DE EJECUCIÓN →
          </Link>
        </div>

        {sessions.length === 0 ? (
          <div style={{ padding: "20px", textAlign: "center", color: "#94a3b8", fontSize: "12px" }}>
            No hay sesiones de fondeo activas en este momento. Despliega una estrategia en <Link href="/ejecucion" style={{ color: "#38bdf8" }}>Ejecución</Link> o conecta NinjaTrader 8.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", textAlign: "left", color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                  <th style={{ padding: "8px" }}>SESIÓN</th>
                  <th style={{ padding: "8px" }}>ESTRATEGIA</th>
                  <th style={{ padding: "8px" }}>SÍMBOLO</th>
                  <th style={{ padding: "8px" }}>ESTADO</th>
                  <th style={{ padding: "8px" }}>PNL HOY</th>
                  <th style={{ padding: "8px" }}>PEAK EQUITY</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.session_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "10px 8px", fontFamily: "var(--font-mono, monospace)", color: "#38bdf8" }}>{s.session_id}</td>
                    <td style={{ padding: "10px 8px" }}>{s.candidate_id}</td>
                    <td style={{ padding: "10px 8px", fontWeight: 700 }}>{s.symbol}</td>
                    <td style={{ padding: "10px 8px" }}>
                      <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: s.status === "RUNNING" ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)", color: s.status === "RUNNING" ? "#34d399" : "#f43f5e" }}>
                        {s.status}
                      </span>
                    </td>
                    <td style={{ padding: "10px 8px", color: s.daily_pnl_usd >= 0 ? "#34d399" : "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
                      {s.daily_pnl_usd >= 0 ? `+$${s.daily_pnl_usd.toFixed(2)}` : `-$${Math.abs(s.daily_pnl_usd).toFixed(2)}`}
                    </td>
                    <td style={{ padding: "10px 8px", fontFamily: "var(--font-mono, monospace)" }}>
                      ${s.peak_equity_usd?.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. CME SESSION TIMER & AUTO-FLATTEN MONITOR */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(56, 189, 248, 0.08) 0%, rgba(16, 23, 34, 0.85) 100%)",
          border: "1px solid rgba(56, 189, 248, 0.25)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "20px" }}>⏱️</span>
            <div>
              <div style={{ fontSize: "14px", fontWeight: 800, color: "#fff" }}>
                Temporizador Mandatorio de Auto-Flatten CME ({selectedFirm.auto_flatten_time})
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "2px" }}>
                Todas las posiciones abiertas se cerrarán automáticamente 10 minutos antes del corte diario para evitar sanciones por overnight.
              </div>
            </div>
          </div>

          <div
            style={{
              padding: "6px 14px",
              borderRadius: "8px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              color: "#38bdf8",
              fontFamily: "var(--font-mono, monospace)",
              fontSize: "12px",
              fontWeight: 800,
            }}
          >
            GUARD ACTIVO · 0 OVERNIGHT
          </div>
        </div>
      </div>
    </div>
  );
}
