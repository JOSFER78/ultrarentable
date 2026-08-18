"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface PaperIncubationItem {
  strategy_id: string;
  track: string;
  symbol: string;
  timeframe: string;
  days_in_incubation: number;
  total_days_required: number;
  backtest_sharpe: number;
  paper_sharpe: number;
  backtest_max_dd_pct: number;
  paper_max_dd_pct: number;
  fills_count: number;
  avg_slippage_bps: number;
  status: "OBSERVING" | "PROMOTED_LIVE" | "ABORTED_DRIFT";
}

export default function PaperSandboxPage() {
  const [incubationList, setIncubationList] = useState<PaperIncubationItem[]>([
    {
      strategy_id: "UR-FONDEO-NQ-H1",
      track: "TRACK_FONDEO",
      symbol: "NQ",
      timeframe: "1h",
      days_in_incubation: 11,
      total_days_required: 14,
      backtest_sharpe: 2.35,
      paper_sharpe: 2.18,
      backtest_max_dd_pct: 3.2,
      paper_max_dd_pct: 3.5,
      fills_count: 28,
      avg_slippage_bps: 2.8,
      status: "OBSERVING",
    },
    {
      strategy_id: "UR-ULTRA-SOL-H1",
      track: "TRACK_ULTRA",
      symbol: "SOL-USDT",
      timeframe: "1h",
      days_in_incubation: 14,
      total_days_required: 14,
      backtest_sharpe: 2.80,
      paper_sharpe: 2.65,
      backtest_max_dd_pct: 4.1,
      paper_max_dd_pct: 3.9,
      fills_count: 42,
      avg_slippage_bps: 3.1,
      status: "OBSERVING",
    },
  ]);

  const [simulatingTick, setSimulatingTick] = useState<boolean>(false);
  const [lastFillLog, setLastFillLog] = useState<string | null>(null);

  const handleSimulateFill = () => {
    setSimulatingTick(true);
    setTimeout(() => {
      const now = new Date().toISOString().slice(11, 19);
      setLastFillLog(`[${now}] FILL SIMULADO: BUY 1 NQ @ 20,412.50 (Slippage: +2.5 bps, Latencia: 48ms, Margen: Aislado 1R)`);
      setSimulatingTick(false);
    }, 400);
  };

  const handlePromote = (strategyId: string) => {
    setIncubationList((prev) =>
      prev.map((item) =>
        item.strategy_id === strategyId ? { ...item, status: "PROMOTED_LIVE" } : item
      )
    );
  };

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            PAPER SANDBOX · INCUBATION 14 DÍAS
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          Sandbox de Incubación en Tiempo Real (14 Días)
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Observación estricta contra datos en vivo: Detección de drift de Sharpe, control de latencia (50ms) y promoción determinista a LIVE_ACTIVE.
        </p>
      </div>

      {/* 2. SUMMARY METRICS */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginBottom: "24px" }}>
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            EN INCUBACIÓN PAPER
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {incubationList.filter((i) => i.status === "OBSERVING").length} Estrategias
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            Observación de 14 días activa
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            MODELADO DE LATENCIA
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#34d399", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            50 ms
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            Slippage Dinámico: +3 bps
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            UMBRAL DE ABORTO POR DRIFT
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#f43f5e", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            &gt; 30% Sharpe Drift
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            o Max DD &gt; 1.25x Backtest
          </div>
        </div>
      </div>

      {/* 3. INCUBATION CANDIDATES TABLE */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
            Estrategias en Periodo de Observación (Incubation Pipeline)
          </h2>

          <button
            onClick={handleSimulateFill}
            disabled={simulatingTick}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              color: "#38bdf8",
              fontWeight: 800,
              fontSize: "11px",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            {simulatingTick ? "SIMULANDO FILL..." : "⚡ SIMULAR TICK DE MERCADO"}
          </button>
        </div>

        {lastFillLog && (
          <div style={{ background: "#080c14", border: "1px solid rgba(56, 189, 248, 0.2)", borderRadius: "6px", padding: "10px 14px", fontFamily: "var(--font-mono, monospace)", fontSize: "11px", color: "#38bdf8", marginBottom: "16px" }}>
            {lastFillLog}
          </div>
        )}

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", textAlign: "left", color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                <th style={{ padding: "10px 12px" }}>ESTRATEGIA</th>
                <th style={{ padding: "10px 12px" }}>PROGRESO (14 DÍAS)</th>
                <th style={{ padding: "10px 12px" }}>SHARPE (BT vs PAPER)</th>
                <th style={{ padding: "10px 12px" }}>MAX DD (BT vs PAPER)</th>
                <th style={{ padding: "10px 12px" }}>FILLS / SLIPPAGE</th>
                <th style={{ padding: "10px 12px", textAlign: "right" }}>ESTADO FSM</th>
              </tr>
            </thead>
            <tbody>
              {incubationList.map((item) => {
                const progressPct = Math.min(100, (item.days_in_incubation / item.total_days_required) * 100);
                const sharpeDriftPct = Math.abs((item.paper_sharpe - item.backtest_sharpe) / item.backtest_sharpe) * 100;
                const isReadyForPromotion = item.days_in_incubation >= item.total_days_required && item.status === "OBSERVING";

                return (
                  <tr key={item.strategy_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                    <td style={{ padding: "14px 12px" }}>
                      <div style={{ fontWeight: 800, color: "#fff", fontFamily: "var(--font-mono, monospace)" }}>
                        {item.strategy_id}
                      </div>
                      <div style={{ fontSize: "10px", color: "#64748b" }}>
                        {item.symbol} · {item.timeframe} · {item.track}
                      </div>
                    </td>

                    <td style={{ padding: "14px 12px", minWidth: "160px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", marginBottom: "4px" }}>
                        <span>Día {item.days_in_incubation} de {item.total_days_required}</span>
                        <strong style={{ color: "#38bdf8" }}>{progressPct.toFixed(0)}%</strong>
                      </div>
                      <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
                        <div style={{ width: `${progressPct}%`, height: "100%", background: "#38bdf8", borderRadius: "3px" }} />
                      </div>
                    </td>

                    <td style={{ padding: "14px 12px", fontFamily: "var(--font-mono, monospace)" }}>
                      <div>BT: {item.backtest_sharpe.toFixed(2)} → Paper: {item.paper_sharpe.toFixed(2)}</div>
                      <div style={{ fontSize: "10px", color: sharpeDriftPct < 30 ? "#34d399" : "#f43f5e" }}>
                        Drift: {sharpeDriftPct.toFixed(1)}% ({sharpeDriftPct < 30 ? "Estable" : "Degradado"})
                      </div>
                    </td>

                    <td style={{ padding: "14px 12px", fontFamily: "var(--font-mono, monospace)" }}>
                      <div>BT: {item.backtest_max_dd_pct}% → Paper: {item.paper_max_dd_pct}%</div>
                    </td>

                    <td style={{ padding: "14px 12px", fontFamily: "var(--font-mono, monospace)" }}>
                      <div>{item.fills_count} fills</div>
                      <div style={{ fontSize: "10px", color: "#64748b" }}>+{item.avg_slippage_bps} bps slippage</div>
                    </td>

                    <td style={{ padding: "14px 12px", textAlign: "right" }}>
                      {item.status === "PROMOTED_LIVE" ? (
                        <span style={{ fontSize: "11px", fontWeight: 800, color: "#34d399", background: "rgba(52, 211, 153, 0.15)", padding: "4px 8px", borderRadius: "6px", border: "1px solid #34d399" }}>
                          ● LIVE_ACTIVE
                        </span>
                      ) : isReadyForPromotion ? (
                        <button
                          onClick={() => handlePromote(item.strategy_id)}
                          style={{
                            padding: "6px 12px",
                            borderRadius: "6px",
                            background: "linear-gradient(135deg, #34d399 0%, #059669 100%)",
                            border: "none",
                            color: "#06080d",
                            fontWeight: 900,
                            fontSize: "11px",
                            cursor: "pointer",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          PROMOVER A LIVE →
                        </button>
                      ) : (
                        <span style={{ fontSize: "11px", fontWeight: 800, color: "#f59e0b", background: "rgba(245, 158, 11, 0.15)", padding: "4px 8px", borderRadius: "6px" }}>
                          INCUBATION_PAPER
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
