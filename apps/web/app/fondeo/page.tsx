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
  const [currentEquity, setCurrentEquity] = useState<number>(51850.0);
  const [peakEquity, setPeakEquity] = useState<number>(52100.0);
  const [todayPnl, setTodayPnl] = useState<number>(450.0);
  const [daysTraded, setDaysTraded] = useState<number>(3);
  const [bestDayPnl, setBestDayPnl] = useState<number>(750.0);

  // Cálculos de cumplimiento
  const totalProfit = currentEquity - selectedFirm.account_size;
  const targetProgress = Math.min(100, Math.max(0, (totalProfit / selectedFirm.profit_target) * 100));
  const currentDd = peakEquity - currentEquity;
  const ddBuffer = Math.max(0, selectedFirm.max_trailing_dd - currentDd);
  const ddUsagePct = Math.min(100, (currentDd / selectedFirm.max_trailing_dd) * 100);
  const consistencyPct = totalProfit > 0 ? (bestDayPnl / totalProfit) * 100 : 0;
  const isConsistencyOk = consistencyPct <= selectedFirm.consistency_max_pct;
  const isDllOk = todayPnl > -selectedFirm.daily_loss_limit;

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
            EQUITY DE LA CUENTA
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: "#fff", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            ${currentEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: "11px", color: "#34d399", marginTop: "4px" }}>
            Beneficio Neto: +${totalProfit.toLocaleString("en-US", { minimumFractionDigits: 2 })}
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

        {/* Regla de Consistencia */}
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "18px" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            REGLA DE CONSISTENCIA ({selectedFirm.consistency_max_pct}%)
          </div>
          <div style={{ fontSize: "24px", fontWeight: 900, color: isConsistencyOk ? "#34d399" : "#f43f5e", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {consistencyPct.toFixed(1)}%
          </div>
          <div style={{ fontSize: "11px", color: isConsistencyOk ? "#34d399" : "#f43f5e", marginTop: "4px" }}>
            {isConsistencyOk ? "✓ Dentro del límite" : "✕ Supera límite permitido"}
          </div>
        </div>
      </div>

      {/* 4. CME SESSION TIMER & AUTO-FLATTEN MONITOR */}
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
            GUARD ACTIVO · 0 VIOLACIONES
          </div>
        </div>
      </div>
    </div>
  );
}
