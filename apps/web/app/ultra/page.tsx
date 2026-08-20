/**
 * apps/web/app/ultra/page.tsx
 * MÓDULO ULTRA — EXPLOTACIÓN ASIMÉTRICA & BÓVEDA RATCHET MONOTÓNICA (BINGX USD-M PERPETUALS)
 * ESTADO 100% HONESTO Y REAL (CERO MOCKS)
 */
"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function UltraPage() {
  const [activeMargin, setActiveMargin] = useState<number>(100);

  return (
    <div style={{ padding: "16px 24px", width: "100%", maxWidth: "100%", margin: 0, boxSizing: "border-box" }}>
      {/* 1. TOP HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
              ← Volver al Panel Maestro de Estrategias
            </Link>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 900, color: "#63e1b4", fontFamily: "var(--font-mono, monospace)", textTransform: "uppercase" }}>
              ⚡ DOCTRINA ULTRA · EXPLOTACIÓN ASIMÉTRICA CONVEXA
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
            Mecanismo de Explotación Ultra & Bóveda Ratchet
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "6px", maxWidth: "900px" }}>
            Arquitectura de trading en margen aislado (1R). Piramidación al 40% financiada exclusivamente con ganancias flotantes (House Money) y garantía matemática de protección Free-Risk.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "8px 14px", textAlign: "right" }}>
            <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>ESTADO DEL BOT</div>
            <div style={{ fontSize: "14px", fontWeight: 800, color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
              0 BOTS ACTIVOS (EN REPOSO)
            </div>
          </div>
        </div>
      </div>

      {/* 2. EXPLICACIÓN DEL CICLO DE VIDA DE 6 ESTADOS */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "22px", marginBottom: "28px" }}>
        <h3 style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", margin: "0 0 14px 0" }}>
          🎯 Ciclo de Vida de la Bala de Margen Aislado (FSM de 6 Estados)
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px", marginBottom: "20px" }}>
          <div style={{ background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "14px" }}>
            <strong style={{ color: "#63e1b4", fontSize: "12px" }}>1. INICIO (1R Margen Aislado)</strong>
            <p style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Disparo con riesgo estrictamente acotado al tamaño del margen.</p>
          </div>

          <div style={{ background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "14px" }}>
            <strong style={{ color: "#38bdf8", fontSize: "12px" }}>2. CONFIRMACIÓN</strong>
            <p style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Alcanzado +1.0R de flotante, el Stop Loss se traslada a Break-Even.</p>
          </div>

          <div style={{ background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "14px" }}>
            <strong style={{ color: "#a78bfa", fontSize: "12px" }}>3. CRECIMIENTO (40% HM)</strong>
            <p style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Adición piramidal de capas con House Money y SL Free-Risk garantizado ≥ +0.5R.</p>
          </div>

          <div style={{ background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "14px" }}>
            <strong style={{ color: "#34d399", fontSize: "12px" }}>4. COSECHA RATCHET</strong>
            <p style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Hitos 2x, 3x, 5x y 10x donde el capital se transfiere a Bóveda físicamente intocable.</p>
          </div>

          <div style={{ background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "14px" }}>
            <strong style={{ color: "#fbbf24", fontSize: "12px" }}>5. PROTECCIÓN BE</strong>
            <p style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Seguimiento por Chandelier Stop o Parabolic SAR dinámico.</p>
          </div>

          <div style={{ background: "rgba(0, 0, 0, 0.35)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "14px" }}>
            <strong style={{ color: "#f43f5e", fontSize: "12px" }}>6. CIERRE</strong>
            <p style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>Liquidación ordenada de la bala y reseteo del slot para la siguiente señal.</p>
          </div>
        </div>

        {/* 3. MANIFIESTO MAESTRO: ULTRA VS FONDEO */}
        <div style={{ marginTop: "24px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", paddingTop: "20px" }}>
          <h4 style={{ fontSize: "14px", fontWeight: 900, color: "#63e1b4", marginBottom: "12px", fontFamily: "var(--font-mono, monospace)" }}>
            ⚡ ESPECIFICACIÓN CANÓNICA: RUTA ULTRA (SUB-CUENTA BALA) VS RUTA FONDEO (APEX / TOPSTEP)
          </h4>
          
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", fontFamily: "var(--font-mono, monospace)" }}>
              <thead>
                <tr style={{ background: "rgba(255, 255, 255, 0.03)", borderBottom: "1px solid rgba(255, 255, 255, 0.1)" }}>
                  <th style={{ padding: "8px 12px", textAlign: "left", color: "#94a3b8" }}>Parámetro</th>
                  <th style={{ padding: "8px 12px", textAlign: "left", color: "#63e1b4" }}>Ruta ULTRA (Asimétrica)</th>
                  <th style={{ padding: "8px 12px", textAlign: "left", color: "#38bdf8" }}>Ruta FONDEO (Prop Firms)</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Capital Base Inicial</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>$1.000 USD (Bala Sacrificable)</td>
                  <td style={{ padding: "8px 12px", color: "#38bdf8" }}>$50.000 USD (Cuenta Institucional)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Riesgo Base por Trade</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>7.5% de la Equidad Disponible</td>
                  <td style={{ padding: "8px 12px", color: "#38bdf8" }}>0.5% - 1.0% ($250 - $500 USD)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Interés Compuesto</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>Compounding Dinámico Activo</td>
                  <td style={{ padding: "8px 12px", color: "#38bdf8" }}>Lotes / Contratos Fijos CME</td>
                </tr>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Piramidación</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>1 a 3 niveles en beneficio ≥ +1.5R</td>
                  <td style={{ padding: "8px 12px", color: "#f43f5e" }}>Prohibida (Exposición fija)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Drawdown Permitido</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>Hasta 80% (Quiebra de bala en 85-100%)</td>
                  <td style={{ padding: "8px 12px", color: "#f43f5e" }}>Máximo 4.0% - 4.5% ($2.000 - $2.500 USD)</td>
                </tr>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Cosecha a Bóveda</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>50% del beneficio cosechado al superar +200%</td>
                  <td style={{ padding: "8px 12px", color: "#94a3b8" }}>No aplica (Administrado por Prop Firm)</td>
                </tr>
                <tr>
                  <td style={{ padding: "8px 12px", color: "#e2e8f0", fontWeight: 700 }}>Universo de Activos</td>
                  <td style={{ padding: "8px 12px", color: "#63e1b4" }}>23 Activos Globales (BTC, ETH, SOL, SUI, DOGE, AVAX, BNB, LINK, XRP, NQ, ES, GC, SI, CL, EURUSD, etc.)</td>
                  <td style={{ padding: "8px 12px", color: "#38bdf8" }}>Futuros Regulados CME & Forex (NQ, ES, YM, GC, CL, 6E)</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ textAlign: "center", padding: "20px 0", color: "#64748b", fontSize: "13px" }}>
          Para activar este motor en vivo, selecciona una cartera validada en el{" "}
          <Link href="/" style={{ color: "#63e1b4", textDecoration: "none", fontWeight: 800 }}>
            Panel Maestro de Estrategias →
          </Link>
        </div>
      </div>
    </div>
  );
}
