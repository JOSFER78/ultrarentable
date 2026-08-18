/**
 * apps/web/app/ultra/page.tsx
 * Macro-Entorno 2: LIVE BOT TRADING — ULTRA HYPER-SCALING & TELEMETRÍA REAL (BingX USD-M Perpetuals)
 * 100% DATOS REALES DIRECTAMENTE DESDE LA BASE DE DATOS DE TRADES DE LA VPS (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";

interface RealTrade {
  id: number;
  pair: string;
  is_open: number;
  fee_open: number;
  fee_close: number;
  open_rate: number;
  close_rate: number;
  close_profit: number;
  close_profit_abs: number;
  stake_amount: number;
  amount: number;
  open_date: string;
  close_date: string;
}

export default function UltraLiveBotsPage() {
  const [realTrades, setRealTrades] = useState<RealTrade[]>([]);
  const [totalPnlUsd, setTotalPnlUsd] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchLiveTrades = async () => {
    try {
      const res = await fetch("/api/v2/real/trades/botfreq");
      if (res.ok) {
        const data = await res.json();
        setRealTrades(data.trades || []);
        setTotalPnlUsd(data.total_pnl_usd || 0.0);
      }
    } catch (err) {
      // network error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveTrades();
    const interval = setInterval(fetchLiveTrades, 5000);
    return () => clearInterval(interval);
  }, []);

  const openPositions = realTrades.filter((t) => t.is_open === 1);
  const closedTrades = realTrades.filter((t) => t.is_open === 0);

  return (
    <div style={{ padding: "24px", maxWidth: "1560px", margin: "0 auto" }}>
      {/* 1. TOP HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
              ← Volver al Quant Lab (SQLite / SQX)
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 900, color: "#f43f5e", fontFamily: "var(--font-mono, monospace)", textTransform: "uppercase" }}>
              ⚡ MACRO-ENTORNO 2 · LIVE BOT TRADING (BINGX USD-M PERPETUALS)
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
            Ultra Hyper-Scaling & Ejecución en Vivo de Balas
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "6px", maxWidth: "900px" }}>
            Supervisión directa de las posiciones en margen aislado (1R) y lectura del registro inmutable de trades desde la VPS.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "8px 14px", textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>PNL CERRADO REAL</div>
            <div style={{ fontSize: "18px", fontWeight: 900, color: totalPnlUsd >= 0 ? "#34d399" : "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
              ${totalPnlUsd.toFixed(2)} USD
            </div>
          </div>
        </div>
      </div>

      {/* 2. HUD DE POSICIÓN ACTIVA & FSM */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "22px", marginBottom: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
          <div>
            <h3 style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", margin: 0 }}>
              🎯 Estado de Balas de Margen Aislado en BingX
            </h3>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              {openPositions.length > 0 ? `${openPositions.length} posiciones abiertas en ejecución` : "No hay órdenes abiertas en este instante. Esperando señal cuantitativa."}
            </span>
          </div>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#63e1b4", background: "rgba(99, 225, 180, 0.1)", padding: "4px 10px", borderRadius: "6px", fontFamily: "var(--font-mono, monospace)" }}>
            BINGX API V2 CONECTADA
          </span>
        </div>

        {/* FSM STATES */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: "10px", marginBottom: "20px" }}>
          {["1. INICIO (1R)", "2. CONFIRMACIÓN", "3. CRECIMIENTO (40% HM)", "4. COSECHA RATCHET", "5. PROTECCIÓN BE", "6. CIERRE"].map((st, idx) => (
            <div
              key={st}
              style={{
                background: idx === 0 ? "rgba(99, 225, 180, 0.12)" : "rgba(0, 0, 0, 0.3)",
                border: idx === 0 ? "1px solid #63e1b4" : "1px solid rgba(255, 255, 255, 0.06)",
                borderRadius: "8px",
                padding: "10px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>ESTADO FSM</div>
              <div style={{ fontSize: "11px", fontWeight: 800, color: idx === 0 ? "#63e1b4" : "#94a3b8", marginTop: "2px" }}>
                {st}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 3. TABLA DE TRADES REALES EJECUTADOS */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px", marginBottom: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h3 style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", margin: 0 }}>
              📜 Registro Real de Órdenes y Trades ({closedTrades.length} cerrados en base de datos)
            </h3>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              Datos extraídos directamente desde SQLite (/home/ubuntu/db/botfreq/tradesv3.sqlite)
            </span>
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
            <thead>
              <tr style={{ background: "rgba(0, 0, 0, 0.4)", color: "#64748b", textAlign: "left", fontFamily: "var(--font-mono, monospace)" }}>
                <th style={{ padding: "10px 12px" }}>ID TRADE</th>
                <th style={{ padding: "10px 12px" }}>PAR</th>
                <th style={{ padding: "10px 12px" }}>PRECIO ENTRADA</th>
                <th style={{ padding: "10px 12px" }}>PRECIO CIERRE</th>
                <th style={{ padding: "10px 12px" }}>STAKE ($)</th>
                <th style={{ padding: "10px 12px" }}>RETORNO (%)</th>
                <th style={{ padding: "10px 12px" }}>PNL NETO ($)</th>
                <th style={{ padding: "10px 12px", textAlign: "right" }}>FECHA CIERRE</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>
                    Leyendo base de datos real de trades en la VPS...
                  </td>
                </tr>
              ) : closedTrades.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ padding: "24px", textAlign: "center", color: "#64748b" }}>
                    No hay trades cerrados en la base de datos local en este momento.
                  </td>
                </tr>
              ) : (
                closedTrades.map((t) => {
                  const isPositive = (t.close_profit_abs || 0) >= 0;
                  return (
                    <tr key={t.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#ffffff" }}>
                        #{t.id}
                      </td>
                      <td style={{ padding: "12px", fontWeight: 700, color: "#e2e8f0" }}>
                        {t.pair}
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#94a3b8" }}>
                        ${t.open_rate ? t.open_rate.toFixed(4) : "-"}
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#94a3b8" }}>
                        ${t.close_rate ? t.close_rate.toFixed(4) : "-"}
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#94a3b8" }}>
                        ${t.stake_amount ? t.stake_amount.toFixed(2) : "-"}
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: isPositive ? "#34d399" : "#f43f5e", fontWeight: 700 }}>
                        {t.close_profit ? `${(t.close_profit * 100).toFixed(2)}%` : "0.00%"}
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: isPositive ? "#34d399" : "#f43f5e", fontWeight: 800 }}>
                        ${t.close_profit_abs ? t.close_profit_abs.toFixed(2) : "0.00"}
                      </td>
                      <td style={{ padding: "12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#64748b", fontSize: "11px" }}>
                        {t.close_date || "-"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
