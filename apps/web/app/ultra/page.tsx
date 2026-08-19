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
