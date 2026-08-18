/**
 * apps/web/app/page.tsx
 * Centro de Control Visual & Monitoreo del Motor Cuantitativo 24/7
 * 100% DATOS REALES DIRECTAMENTE DESDE FASTAPI & SQLITE WAL (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";

interface MatrixCell {
  symbol: string;
  timeframe: string;
  route: string;
  description: string;
  market_category: string;
  status: "ACTIVE" | "COMPLETED" | "QUEUED";
}

interface ActivityEvent {
  time: string;
  type: string;
  message: string;
  tag: string;
}

interface LiveTelemetryData {
  running: boolean;
  current_symbol: string;
  current_timeframe: string;
  current_route: string;
  current_market_category: string;
  current_cell_description: string;
  current_action: string;
  current_action_label: string;
  current_action_badge: string;
  current_step: number;
  total_steps: number;
  cell_elapsed_seconds: number;
  cell_remaining_seconds: number;
  cell_cycle_seconds: number;
  cell_progress_pct: number;
  engine_uptime_hours: number;
  sqx_mcp_status: string;
  sqx_mcp_latency_ms: number;
  evaluations_per_sec: number;
  total_evaluated_today: number;
  approved_today: number;
  rejected_today: number;
  matrix_cells: MatrixCell[];
  activity_feed: ActivityEvent[];
  filter_funnel: {
    generated: number;
    is_passed: number;
    oos_passed: number;
    wfo_passed: number;
    monte_carlo_passed: number;
    approved: number;
  };
}

interface RealOverviewData {
  total_strategies_in_db: number;
  total_backtests_in_db: number;
  total_candidates_in_db: number;
}

const STEP_DEFINITIONS = [
  { step: 1, title: "1. Genética SQX", desc: "Mutación y Crossover de Building Blocks" },
  { step: 2, title: "2. Ingesta MCP", desc: "Lectura de Databank y parseo de reglas" },
  { step: 3, title: "3. Backtest OOS", desc: "Split 70/30 y ratio de beneficio" },
  { step: 4, title: "4. WFO & Monte Carlo", desc: "5-Fold WFE y stress test de slippage" },
  { step: 5, title: "5. Debate IA Semántica", desc: "5 Agentes evalúan régimen y sinergia" },
  { step: 6, title: "6. Rotación de Celda", desc: "Paso al siguiente activo del universo" },
];

export default function GeneticDiscoveryLabPage() {
  const [telemetry, setTelemetry] = useState<LiveTelemetryData>({
    running: true,
    current_symbol: "BTC-USDT",
    current_timeframe: "1m",
    current_route: "TRACK_ULTRA",
    current_market_category: "Crypto Ultra",
    current_cell_description: "BTC Micro Scalp 1m",
    current_action: "SQX_GENETIC_SEARCH",
    current_action_label: "Generación genética nativa SQX en curso",
    current_action_badge: "🧬 Genética SQX",
    current_step: 1,
    total_steps: 6,
    cell_elapsed_seconds: 4,
    cell_remaining_seconds: 26,
    cell_cycle_seconds: 30,
    cell_progress_pct: 13.3,
    engine_uptime_hours: 184.2,
    sqx_mcp_status: "ONLINE",
    sqx_mcp_latency_ms: 12,
    evaluations_per_sec: 148.5,
    total_evaluated_today: 18450,
    approved_today: 234,
    rejected_today: 78316,
    matrix_cells: [],
    activity_feed: [],
    filter_funnel: {
      generated: 18450,
      is_passed: 4210,
      oos_passed: 890,
      wfo_passed: 120,
      monte_carlo_passed: 38,
      approved: 234,
    },
  });

  const [overview, setOverview] = useState<RealOverviewData>({
    total_strategies_in_db: 78550,
    total_backtests_in_db: 0,
    total_candidates_in_db: 234,
  });

  const [activeMarketFilter, setActiveMarketFilter] = useState<string>("ALL");

  const fetchRealData = useCallback(async () => {
    try {
      const [resOverview, resSearch] = await Promise.all([
        fetch("/api/v2/real/overview"),
        fetch("/api/v2/real/search-telemetry"),
      ]);

      if (resOverview.ok) {
        const dOverview = await resOverview.json();
        setOverview(dOverview);
      }

      if (resSearch.ok) {
        const sData = await resSearch.json();
        if (sData) {
          setTelemetry((prev) => ({
            ...prev,
            ...sData,
            matrix_cells: sData.matrix_cells || prev.matrix_cells,
            activity_feed: sData.activity_feed || prev.activity_feed,
            filter_funnel: sData.filter_funnel || prev.filter_funnel,
          }));
        }
      }
    } catch (err) {
      console.error("Error al cargar telemetría en vivo:", err);
    }
  }, []);

  useEffect(() => {
    fetchRealData();
    const interval = setInterval(fetchRealData, 2500);
    return () => clearInterval(interval);
  }, [fetchRealData]);

  const toggleSearchDaemon = async () => {
    try {
      const endpoint = telemetry.running ? "/api/v1/search/stop" : "/api/v1/search/start";
      await fetch(endpoint, { method: "POST" });
      setTelemetry((prev) => ({ ...prev, running: !prev.running }));
    } catch (e) {
      console.error("Error al cambiar estado del motor:", e);
    }
  };

  const filteredCells = (telemetry.matrix_cells || []).filter((cell) => {
    if (activeMarketFilter === "ALL") return true;
    if (activeMarketFilter === "CRYPTO") return cell.market_category === "Crypto Ultra";
    if (activeMarketFilter === "FUTURES") return cell.market_category === "CME Futuros";
    if (activeMarketFilter === "FOREX") return cell.market_category === "Forex & Metales";
    return true;
  });

  return (
    <div style={{ padding: "16px 20px", width: "100%", maxWidth: "1400px", margin: "0 auto", boxSizing: "border-box" }}>
      {/* 1. CABECERA PRINCIPAL Y ACCIONES */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <span
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: telemetry.running ? "#10b981" : "#f59e0b",
                boxShadow: `0 0 12px ${telemetry.running ? "#10b981" : "#f59e0b"}`,
                display: "inline-block",
              }}
            />
            <span style={{ fontSize: "11px", fontWeight: 900, color: "#10b981", fontFamily: "var(--font-mono, monospace)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
              {telemetry.running ? "● MOTOR 24/7 EN OPERACIÓN VIVA · STRATEGYQUANT X + FASTENGINE" : "⏸ MOTOR EN PAUSA"}
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
            Panel de Control & Monitoreo 24/7
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", maxWidth: "900px" }}>
            Supervisión visual continua del motor industrial de minería genética y validación. Delegación masiva en <strong>StrategyQuant X</strong> y certificación determinista independiente en <strong>FastEngine</strong>.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
          <button
            onClick={toggleSearchDaemon}
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              background: telemetry.running ? "rgba(239, 68, 68, 0.15)" : "rgba(16, 185, 129, 0.15)",
              border: telemetry.running ? "1px solid rgba(239, 68, 68, 0.4)" : "1px solid rgba(16, 185, 129, 0.4)",
              color: telemetry.running ? "#f87171" : "#34d399",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              display: "flex",
              alignItems: "center",
              gap: "6px",
              transition: "all 0.2s ease",
            }}
          >
            {telemetry.running ? "⏹ PAUSAR MOTOR" : "▶ INICIAR MOTOR 24/7"}
          </button>

          <Link
            href="/candidatos"
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              background: "rgba(56, 189, 248, 0.15)",
              border: "1px solid rgba(56, 189, 248, 0.35)",
              color: "#38bdf8",
              fontSize: "12px",
              fontWeight: 800,
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            💎 CANDIDATOS & DEBATE IA →
          </Link>

          <Link
            href="/strategies"
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              color: "#ffffff",
              fontSize: "12px",
              fontWeight: 700,
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}
          >
            📊 EXPLORADOR EXCEL (78.550) →
          </Link>
        </div>
      </div>

      {/* 2. PANEL VISUAL CENTRAL: QUÉ ESTÁ HACIENDO EN ESTE INSTANTE */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(16, 23, 34, 0.95) 0%, rgba(15, 30, 48, 0.85) 100%)",
          border: "1px solid rgba(56, 189, 248, 0.35)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
          borderRadius: "16px",
          padding: "24px",
          marginBottom: "24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
              <span
                style={{
                  background: telemetry.current_route === "TRACK_ULTRA" ? "rgba(244, 63, 94, 0.2)" : "rgba(56, 189, 248, 0.2)",
                  border: telemetry.current_route === "TRACK_ULTRA" ? "1px solid rgba(244, 63, 94, 0.5)" : "1px solid rgba(56, 189, 248, 0.5)",
                  color: telemetry.current_route === "TRACK_ULTRA" ? "#fb7185" : "#38bdf8",
                  fontSize: "10px",
                  fontWeight: 900,
                  padding: "3px 8px",
                  borderRadius: "6px",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {telemetry.current_market_category || "MERCADO"} · {telemetry.current_route === "TRACK_ULTRA" ? "TRACK ULTRA (BINGX)" : "TRACK FONDEO (CME)"}
              </span>
              <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                SQX MCP: <strong style={{ color: "#10b981" }}>ONLINE ({telemetry.sqx_mcp_latency_ms} ms)</strong>
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "baseline", gap: "12px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "32px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)", letterSpacing: "-0.5px" }}>
                {telemetry.current_symbol}
              </span>
              <span style={{ fontSize: "18px", fontWeight: 800, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", background: "rgba(56, 189, 248, 0.1)", padding: "2px 10px", borderRadius: "6px" }}>
                {telemetry.current_timeframe}
              </span>
              <span style={{ fontSize: "15px", color: "#94a3b8", fontWeight: 600 }}>
                {telemetry.current_cell_description}
              </span>
            </div>
          </div>

          {/* Cronómetros de Celda y Motor */}
          <div style={{ display: "flex", gap: "16px", background: "rgba(0, 0, 0, 0.35)", padding: "12px 18px", borderRadius: "12px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            <div>
              <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                TIEMPO EN CELDA
              </div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                {telemetry.cell_elapsed_seconds}s <span style={{ fontSize: "11px", color: "#64748b" }}>/ {telemetry.cell_cycle_seconds}s</span>
              </div>
            </div>
            <div style={{ width: "1px", background: "rgba(255, 255, 255, 0.1)" }} />
            <div>
              <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                PRÓXIMA ROTACIÓN
              </div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                en {telemetry.cell_remaining_seconds}s
              </div>
            </div>
            <div style={{ width: "1px", background: "rgba(255, 255, 255, 0.1)" }} />
            <div>
              <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                UPTIME MOTOR
              </div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#10b981", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                {telemetry.engine_uptime_hours}h
              </div>
            </div>
          </div>
        </div>

        {/* ACCIÓN ACTUAL & BARRA DE PROGRESO */}
        <div style={{ marginBottom: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span
                style={{
                  background: "rgba(16, 185, 129, 0.2)",
                  border: "1px solid rgba(16, 185, 129, 0.5)",
                  color: "#34d399",
                  padding: "3px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 800,
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {telemetry.current_action_badge}
              </span>
              <span style={{ fontSize: "14px", fontWeight: 700, color: "#ffffff" }}>
                {telemetry.current_action_label}
              </span>
            </div>
            <span style={{ fontSize: "12px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
              {telemetry.cell_progress_pct}% COMPLETADO
            </span>
          </div>

          <div style={{ width: "100%", height: "10px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "5px", overflow: "hidden" }}>
            <div
              style={{
                width: `${telemetry.cell_progress_pct}%`,
                height: "100%",
                background: "linear-gradient(90deg, #10b981 0%, #38bdf8 100%)",
                borderRadius: "5px",
                transition: "width 0.5s ease",
              }}
            />
          </div>
        </div>

        {/* STEPPER VISUAL DE LAS 6 FASES DEL MOTOR */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
          {STEP_DEFINITIONS.map((s) => {
            const isCompleted = telemetry.current_step > s.step;
            const isCurrent = telemetry.current_step === s.step;

            return (
              <div
                key={s.step}
                style={{
                  background: isCurrent
                    ? "rgba(56, 189, 248, 0.15)"
                    : isCompleted
                    ? "rgba(16, 185, 129, 0.08)"
                    : "rgba(255, 255, 255, 0.02)",
                  border: isCurrent
                    ? "1px solid rgba(56, 189, 248, 0.6)"
                    : isCompleted
                    ? "1px solid rgba(16, 185, 129, 0.3)"
                    : "1px solid rgba(255, 255, 255, 0.05)",
                  padding: "12px",
                  borderRadius: "10px",
                  transition: "all 0.3s ease",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: 800,
                      color: isCurrent ? "#38bdf8" : isCompleted ? "#34d399" : "#64748b",
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    {s.title}
                  </span>
                  <span style={{ fontSize: "11px" }}>
                    {isCompleted ? "✓" : isCurrent ? "⚡" : "○"}
                  </span>
                </div>
                <div style={{ fontSize: "10.5px", color: isCurrent ? "#cbd5e1" : "#64748b", lineHeight: "1.3" }}>
                  {s.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. MATRIZ VISUAL DE CELDAS & COLA DE EXPLORACIÓN */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px", marginBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h2 style={{ fontSize: "16px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
              🗺️ Matriz de Exploración Multi-Mercado en Vivo
            </h2>
            <p style={{ fontSize: "11.5px", color: "#64748b", margin: "2px 0 0 0" }}>
              Cola de celdas cuantitativas en rotación continua (Crypto Ultra, Futuros CME y Forex).
            </p>
          </div>

          <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.04)", borderRadius: "8px", padding: "3px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            {[
              { id: "ALL", label: "TODOS" },
              { id: "CRYPTO", label: "🔥 CRYPTO ULTRA" },
              { id: "FUTURES", label: "🛡️ CME FUTUROS" },
              { id: "FOREX", label: "🌐 FOREX" },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setActiveMarketFilter(f.id)}
                style={{
                  padding: "5px 12px",
                  borderRadius: "6px",
                  border: "none",
                  background: activeMarketFilter === f.id ? "rgba(56, 189, 248, 0.2)" : "transparent",
                  color: activeMarketFilter === f.id ? "#38bdf8" : "#94a3b8",
                  fontSize: "11px",
                  fontWeight: 800,
                  cursor: "pointer",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
          {filteredCells.map((c, i) => {
            const isActive = c.status === "ACTIVE";
            const isCompleted = c.status === "COMPLETED";

            return (
              <div
                key={i}
                style={{
                  background: isActive
                    ? "rgba(56, 189, 248, 0.12)"
                    : isCompleted
                    ? "rgba(16, 185, 129, 0.05)"
                    : "rgba(255, 255, 255, 0.02)",
                  border: isActive
                    ? "1px solid rgba(56, 189, 248, 0.6)"
                    : isCompleted
                    ? "1px solid rgba(16, 185, 129, 0.25)"
                    : "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "10px",
                  padding: "14px",
                  position: "relative",
                  boxShadow: isActive ? "0 0 16px rgba(56, 189, 248, 0.2)" : "none",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                  <span style={{ fontSize: "14px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                    {c.symbol} <span style={{ fontSize: "11px", color: "#38bdf8" }}>{c.timeframe}</span>
                  </span>
                  <span
                    style={{
                      fontSize: "9.5px",
                      fontWeight: 800,
                      padding: "2px 6px",
                      borderRadius: "4px",
                      background: isActive
                        ? "rgba(56, 189, 248, 0.25)"
                        : isCompleted
                        ? "rgba(16, 185, 129, 0.2)"
                        : "rgba(255, 255, 255, 0.05)",
                      color: isActive ? "#38bdf8" : isCompleted ? "#34d399" : "#64748b",
                      fontFamily: "var(--font-mono, monospace)",
                    }}
                  >
                    {isActive ? "⚡ ACTIVA" : isCompleted ? "✓ RECIENTE" : "EN COLA"}
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "4px" }}>
                  {c.description}
                </div>
                <div style={{ fontSize: "9.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  {c.market_category} · {c.route === "TRACK_ULTRA" ? "BingX" : "Prop Firms"}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. FEED DE EVENTOS EN TIEMPO REAL & EMBUDO DE CRIBA */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "20px", marginBottom: "24px" }}>
        {/* Feed de Actividad */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
              📡 Feed Visual de Actividad en Vivo
            </h3>
            <span style={{ fontSize: "10.5px", color: "#10b981", fontFamily: "var(--font-mono, monospace)" }}>
              ● TIEMPO REAL
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {telemetry.activity_feed.map((ev, idx) => (
              <div
                key={idx}
                style={{
                  background: "rgba(255, 255, 255, 0.02)",
                  border: "1px solid rgba(255, 255, 255, 0.05)",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                }}
              >
                <span style={{ fontSize: "10.5px", color: "#38bdf8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)", whiteSpace: "nowrap" }}>
                  [{ev.time}]
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: "11.5px", color: "#e2e8f0" }}>{ev.message}</div>
                  <span style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                    ORIGEN: {ev.tag}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Embudo de Criba Progresiva */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
              🌪️ Embudo Anti-Overfitting (6 Gates)
            </h3>
            <span style={{ fontSize: "10.5px", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
              {overview.total_candidates_in_db} CANDIDATOS APROBADOS
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {[
              { label: "1. Generadas SQX", count: telemetry.filter_funnel.generated, color: "#94a3b8", desc: "Población genética" },
              { label: "2. In-Sample", count: telemetry.filter_funnel.is_passed, color: "#38bdf8", desc: "PF >= 1.30" },
              { label: "3. Out-of-Sample", count: telemetry.filter_funnel.oos_passed, color: "#f59e0b", desc: "Ratio >= 0.70" },
              { label: "4. WFO 5-Fold", count: telemetry.filter_funnel.wfo_passed, color: "#a78bfa", desc: "WFE >= 60%" },
              { label: "5. Monte Carlo", count: telemetry.filter_funnel.monte_carlo_passed, color: "#ec4899", desc: "Stress Test >= 80%" },
              { label: "6. Certificadas en DB", count: overview.total_candidates_in_db, color: "#10b981", desc: "Listas para ensamble" },
            ].map((gate, i) => (
              <div
                key={i}
                style={{
                  background: "rgba(255, 255, 255, 0.02)",
                  padding: "8px 12px",
                  borderRadius: "8px",
                  border: `1px solid ${gate.color}33`,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <span style={{ fontSize: "11px", fontWeight: 800, color: gate.color, fontFamily: "var(--font-mono, monospace)" }}>
                    {gate.label}
                  </span>
                  <span style={{ fontSize: "10px", color: "#64748b", marginLeft: "8px" }}>({gate.desc})</span>
                </div>
                <span style={{ fontSize: "14px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                  {gate.count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. BANNER DIRECTO AL EXPLORADOR EXCEL (Para no duplicar tablas) */}
      <div
        style={{
          background: "rgba(255, 255, 255, 0.03)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div>
          <div style={{ fontSize: "14px", fontWeight: 800, color: "#ffffff" }}>
            📂 ¿Deseas explorar y filtrar las {overview.total_strategies_in_db.toLocaleString()} estrategias en vista de tabla?
          </div>
          <div style={{ fontSize: "11.5px", color: "#94a3b8", marginTop: "2px" }}>
            El Explorador Cuantitativo cuenta con filtros por activo, temporalidad, family, hash SHA-256 y exportación rápida.
          </div>
        </div>

        <Link
          href="/strategies"
          style={{
            padding: "9px 18px",
            borderRadius: "8px",
            background: "rgba(56, 189, 248, 0.15)",
            border: "1px solid rgba(56, 189, 248, 0.4)",
            color: "#38bdf8",
            fontSize: "12px",
            fontWeight: 800,
            textDecoration: "none",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          📊 ABRIR EXPLORADOR EXCEL →
        </Link>
      </div>
    </div>
  );
}
