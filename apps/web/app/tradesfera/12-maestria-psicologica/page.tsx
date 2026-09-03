"use client";

import React, { useState } from "react";
import {
  Brain,
  Activity,
  ShieldCheck,
  Zap,
  CheckCircle2,
  Clock,
  Flame,
  Award,
  Heart,
  Sliders,
} from "lucide-react";

export default function MaestriaPsicologicaPage() {
  const [heartRateLevel, setHeartRateLevel] = useState<number>(65);
  const [displayMode, setDisplayMode] = useState<"TICKS" | "POINTS" | "USD">("TICKS");

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Maestría Psicológica & Neurociencia Operativa</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M12
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Protocolos clínicos avanzados de Víctor Corrales (@Elpsicologodeltrading) para erradicar el secuestro de la amígdala.
            </p>
          </div>
        </div>
      </div>

      {/* 3 Protocolos Neuroconductuales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-[var(--profit)]">
            <span className="font-bold">PROTOCOLO 01</span>
            <Heart className="w-4 h-4" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)] font-sans">
            Respiración Diafragmática 4-7-8
          </div>
          <p className="text-xs text-[var(--text-3)] font-sans">
            Inhalar en 4s, retener en 7s, exhalar en 8s. Activa el nervio vago y desactiva el sistema simpático 10 minutos antes de la campana de apertura (15:30 CET).
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-[var(--profit)]">
            <span className="font-bold">PROTOCOLO 02</span>
            <Sliders className="w-4 h-4" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)] font-sans">
            Desensibilización del PnL
          </div>
          <p className="text-xs text-[var(--text-3)] font-sans">
            Ocultar los dígitos en $ y euros en la pantalla. Operar exclusivamente midiendo R (riesgo) y ticks. El dinero activa centros cerebrales del dolor físico.
          </p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-[var(--profit)]">
            <span className="font-bold">PROTOCOLO 03</span>
            <Clock className="w-4 h-4" />
          </div>
          <div className="text-sm font-bold text-[var(--text-1)] font-sans">
            Regla de los 30 Minutos Post-Stop
          </div>
          <p className="text-xs text-[var(--text-3)] font-sans">
            Tras saltar un stop loss, está biológicamente prohibido ejecutar una nueva orden antes de 30 minutos. La dopamina tarda 25 minutos en estabilizarse.
          </p>
        </div>
      </div>

      {/* Simulador Interactivo de Desensibilización al PnL */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
          <div>
            <h2 className="text-sm font-bold text-[var(--text-1)]">
              Simulador Clínico: Formato de Lectura de PnL en Pantalla
            </h2>
            <p className="text-xs text-[var(--text-3)] font-mono">
              Comprueba el impacto de ver el resultado en Ticks vs Puntos vs Dólares en un trade de 10 puntos en NQ.
            </p>
          </div>
          <div className="flex items-center gap-1 font-mono text-xs">
            {(["TICKS", "POINTS", "USD"] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setDisplayMode(mode)}
                className={`px-2.5 py-1 rounded border transition cursor-pointer ${
                  displayMode === mode
                    ? "bg-[var(--surface-2)] border-[var(--profit)] text-[var(--profit)] font-bold"
                    : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-3)]"
                }`}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg p-4 space-y-2 font-mono">
            <span className="text-[10px] text-[var(--text-3)] uppercase">Lectura en Terminal NinjaTrader</span>
            <div className="text-2xl font-bold text-[var(--profit)]">
              {displayMode === "TICKS" && "+40 Ticks (1.5 R)"}
              {displayMode === "POINTS" && "+10.00 Puntos NQ"}
              {displayMode === "USD" && "+$200.00 USD"}
            </div>
            <div className="text-[11px] text-[var(--text-2)] font-sans">
              {displayMode === "TICKS" && "✅ Modo Recomendado: Cero impacto emocional. El cerebro procesa una unidad geométrica abstracta."}
              {displayMode === "POINTS" && "⚠️ Modo Intermedio: Comprensión técnica de rangos de volatilidad."}
              {displayMode === "USD" && "❌ Modo Peligroso: El cerebro asocia $200 a 'facturas, compras o pérdidas', disparando cortisol o euforia."}
            </div>
          </div>

          <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg p-4 space-y-2 font-sans">
            <span className="text-xs font-bold text-[var(--text-1)]">Veredicto del Psicólogo del Trading</span>
            <p className="text-xs text-[var(--text-3)]">
              "El operador rentable en fondeo no cuenta dinero mientras opera, igual que un cirujano no piensa en la factura del paciente mientras opera en quirófano. La atención debe estar 100% en la precisión del proceso."
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
