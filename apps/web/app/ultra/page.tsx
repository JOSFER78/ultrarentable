"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";

const BALA_STATES = [
  { key: "INICIO", label: "1. INICIO", desc: "Sembrada con 1R margen aislado", color: "#94a3b8" },
  { key: "CONFIRMACION", label: "2. CONFIRMACION", desc: "+1.0R alcanzado · SL a Breakeven+", color: "#38bdf8" },
  { key: "CRECIMIENTO_RECYCLING", label: "3. CRECIMIENTO", desc: "+1.8R · Capas 40% House Money (Free-Risk)", color: "#63e1b4" },
  { key: "COSECHA_VAULT", label: "4. COSECHA_VAULT", desc: "Milestones Ratchet (2x/3x/5x/10x) a Bóveda", color: "#a78bfa" },
  { key: "PROTECCION", label: "5. PROTECCION", desc: "Trailing SL dinámico protegiendo cola", color: "#f59e0b" },
  { key: "CIERRE", label: "6. CIERRE", desc: "Consolidación contable inmutable", color: "#34d399" },
];

export default function UltraLabPage() {
  const [currentR, setCurrentR] = useState<number>(3.5);
  const [bulletMarginUsd, setBulletMarginUsd] = useState<number>(100);
  const [vaultBalanceUsd, setVaultBalanceUsd] = useState<number>(1240.0);
  const [activeBalaState, setActiveBalaState] = useState<string>("COSECHA_VAULT");
  const [burstSimulation, setBurstSimulation] = useState<{ id: number; r: number; pnl: number; isLiquidated: boolean }[]>([]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Calcular estado de la bala en base a R
  useEffect(() => {
    if (currentR < 1.0) setActiveBalaState("INICIO");
    else if (currentR >= 1.0 && currentR < 1.8) setActiveBalaState("CONFIRMACION");
    else if (currentR >= 1.8 && currentR < 3.0) setActiveBalaState("CRECIMIENTO_RECYCLING");
    else if (currentR >= 3.0 && currentR < 5.0) setActiveBalaState("COSECHA_VAULT");
    else setActiveBalaState("PROTECCION");
  }, [currentR]);

  // Generar ráfaga de 20 balas
  const runBurstSimulation = () => {
    const burst = [];
    let cumulativePnl = 0;
    for (let i = 1; i <= 20; i++) {
      let r = -1.0;
      let isLiq = true;
      if (i === 4) { r = 8.5; isLiq = false; }
      else if (i === 11) { r = 14.2; isLiq = false; }
      else if (i === 17) { r = 4.0; isLiq = false; }
      else if (i % 3 === 0) { r = 0.5; isLiq = false; }

      const pnl = r * bulletMarginUsd;
      cumulativePnl += pnl;
      burst.push({ id: i, r, pnl, isLiquidated: isLiq });
    }
    setBurstSimulation(burst);
  };

  useEffect(() => {
    runBurstSimulation();
  }, [bulletMarginUsd]);

  // Dibujar curva 2D de Bóveda Ratchet Monotónica en Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Fondo grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
    ctx.lineWidth = 1;
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y < canvas.height; y += 30) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(canvas.width, y);
      ctx.stroke();
    }

    // Curva de Bóveda Ratchet Monotónica (escalonada ascendente, nunca desciende)
    ctx.strokeStyle = "#63e1b4";
    ctx.lineWidth = 3;
    ctx.beginPath();

    const points = [
      { x: 20, y: 150 },
      { x: 80, y: 150 },
      { x: 120, y: 120 },
      { x: 180, y: 120 },
      { x: 230, y: 80 },
      { x: 300, y: 80 },
      { x: 350, y: 40 },
      { x: 420, y: 40 },
    ];

    points.forEach((pt, i) => {
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    });
    ctx.stroke();

    // Puntos de Cosecha
    points.forEach((pt) => {
      ctx.fillStyle = "#34d399";
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

  }, [currentR]);

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#63e1b4", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            TRACK_ULTRA · ASYMMETRIC HYPER-SCALING LAB
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          Ultra Lab: FSM de la Bala & Bóveda Ratchet Monotónica
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Explotación extrema para BingX USD-M Perpetuals: Margen aislado 1R, piramidación Free-Risk con 40% House Money y Bóveda intocable.
        </p>
      </div>

      {/* 2. HUD INTERACTIVO DE LA BALA (6 ESTADOS) */}
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
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            MÁQUINA DE ESTADOS FINITOS DE LA BALA (6 ESTADOS DISCRETOS)
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>Control de R Flotante:</span>
            <input
              type="range"
              min="-1.0"
              max="12.0"
              step="0.1"
              value={currentR}
              onChange={(e) => setCurrentR(parseFloat(e.target.value))}
              style={{ width: "160px", accentColor: "#63e1b4" }}
            />
            <span style={{ fontSize: "14px", fontWeight: 900, color: currentR >= 0 ? "#63e1b4" : "#f43f5e", fontFamily: "var(--font-mono, monospace)" }}>
              {currentR >= 0 ? `+${currentR.toFixed(1)}R` : `${currentR.toFixed(1)}R`}
            </span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
          {BALA_STATES.map((st) => {
            const isActive = activeBalaState === st.key;
            return (
              <div
                key={st.key}
                style={{
                  background: isActive ? `${st.color}25` : "rgba(255, 255, 255, 0.02)",
                  border: isActive ? `1px solid ${st.color}` : "1px solid rgba(255, 255, 255, 0.05)",
                  borderRadius: "10px",
                  padding: "14px",
                  transition: "all 0.15s ease",
                }}
              >
                <div style={{ fontSize: "11px", fontWeight: 900, color: st.color, fontFamily: "var(--font-mono, monospace)" }}>
                  {st.label}
                </div>
                <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "4px" }}>
                  {st.desc}
                </div>
                {isActive && (
                  <div style={{ fontSize: "9px", fontWeight: 800, color: st.color, marginTop: "8px", fontFamily: "var(--font-mono, monospace)" }}>
                    ● ESTADO ACTIVO
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. BÓVEDA RATCHET MONOTÓNICA & CANVAS WIDGET */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
        {/* LEFT: CANVAS 2D DE COSECHA MONOTÓNICA */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(99, 225, 180, 0.2)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
              Curva Monotónica de la Bóveda (d(Vault)/dt ≥ 0)
            </h3>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
              BALANCE: ${vaultBalanceUsd.toFixed(2)} USD
            </span>
          </div>

          <canvas
            ref={canvasRef}
            width={450}
            height={180}
            style={{ width: "100%", height: "180px", background: "#06080d", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)" }}
          />

          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginTop: "14px", textAlign: "center" }}>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
              <div style={{ fontSize: "9px", color: "#64748b" }}>2x (+2R)</div>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#63e1b4" }}>50% Lock</div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
              <div style={{ fontSize: "9px", color: "#64748b" }}>3x (+3R)</div>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#63e1b4" }}>65% Lock</div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
              <div style={{ fontSize: "9px", color: "#64748b" }}>5x (+5R)</div>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#63e1b4" }}>75% Lock</div>
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "8px", borderRadius: "6px" }}>
              <div style={{ fontSize: "9px", color: "#64748b" }}>10x (+10R)</div>
              <div style={{ fontSize: "12px", fontWeight: 800, color: "#63e1b4" }}>85% Lock</div>
            </div>
          </div>
        </div>

        {/* RIGHT: PIRAMIDACIÓN FREE-RISK EXPLICADA */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: "0 0 12px 0" }}>
            Mecánica de Piramidación Free-Risk (House Money)
          </h3>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "12px", color: "#cbd5e1" }}>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)" }}>
              <strong style={{ color: "#38bdf8" }}>1. Siembra de Bala (1R):</strong> Riesgo inicial confinado a $100 USD (margen aislado). Nunca se compromete la cuenta nodriza.
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)" }}>
              <strong style={{ color: "#63e1b4" }}>2. Desplazamiento a Breakeven+:</strong> Al superar +1.0R, el SL salta por encima del precio de entrada ($0R$ de riesgo de principal).
            </div>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)" }}>
              <strong style={{ color: "#a78bfa" }}>3. Inyección 40% House Money:</strong> Al alcanzar +1.8R, se añade una capa con el 40% del profit flotante, recalculando el SL para garantizar SL Free-Risk &ge; +0.5R.
            </div>
          </div>
        </div>
      </div>

      {/* 4. SIMULADOR DE RÁFAGAS EN MARGEN AISLADO (20 BALAS) */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
              Simulador de Ráfaga Cuantitativa (20 Balas Consecutivas)
            </h3>
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              Demostración de asimetría positiva: 2 balas de cola compensan 15 balas liquidadas de 1R.
            </span>
          </div>

          <button
            onClick={runBurstSimulation}
            style={{
              padding: "6px 14px",
              borderRadius: "6px",
              background: "rgba(99, 225, 180, 0.15)",
              border: "1px solid rgba(99, 225, 180, 0.4)",
              color: "#63e1b4",
              fontWeight: 800,
              fontSize: "11px",
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            ↻ RECALCULAR RÁFAGA
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: "10px" }}>
          {burstSimulation.map((b) => (
            <div
              key={b.id}
              style={{
                background: b.r > 0 ? "rgba(52, 211, 153, 0.12)" : "rgba(244, 63, 94, 0.12)",
                border: b.r > 0 ? "1px solid rgba(52, 211, 153, 0.3)" : "1px solid rgba(244, 63, 94, 0.3)",
                borderRadius: "8px",
                padding: "10px",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                BALA #{b.id}
              </div>
              <div style={{ fontSize: "14px", fontWeight: 900, color: b.r > 0 ? "#34d399" : "#f43f5e", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                {b.r > 0 ? `+${b.r}R` : `${b.r}R`}
              </div>
              <div style={{ fontSize: "10px", color: b.pnl > 0 ? "#34d399" : "#f43f5e", marginTop: "2px" }}>
                {b.pnl > 0 ? `+$${b.pnl}` : `-$${Math.abs(b.pnl)}`}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
