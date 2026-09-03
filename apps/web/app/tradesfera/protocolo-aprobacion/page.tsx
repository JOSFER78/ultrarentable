"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  AlertOctagon,
  Flame,
  Target,
  Clock,
  Layers,
  ArrowRight,
  Calculator,
} from "lucide-react";

export default function ProtocoloAprobacionPage() {
  const [instrument, setInstrument] = useState<"MES" | "MNQ">("MNQ");
  const [stopLossTicks, setStopLossTicks] = useState<number>(40); // 40 ticks = 10 puntos en NQ ($20/micro)
  const [maxRiskUsd, setMaxRiskUsd] = useState<number>(80); // $80 de riesgo max
  const [accountTier, setAccountTier] = useState<"25K" | "50K" | "100K" | "150K">("50K");

  // Parámetros por Tier
  const tierConfig = {
    "25K": { target: 1500, dd: 1500, maxMinis: 2, maxMicros: 20 },
    "50K": { target: 3000, dd: 2000, maxMinis: 4, maxMicros: 30 },
    "100K": { target: 6000, dd: 3000, maxMinis: 8, maxMicros: 50 },
    "150K": { target: 9000, dd: 4500, maxMinis: 12, maxMicros: 80 },
  }[accountTier];

  // Cálculo de contratos recomendados
  const tickValue = instrument === "MES" ? 1.25 : 0.50; // $1.25 por tick en MES (5 por punto), $0.50 en MNQ (2 por punto)
  const riskPerContract = stopLossTicks * tickValue;
  const recommendedMicros = Math.max(1, Math.floor(maxRiskUsd / Math.max(1, riskPerContract)));
  const totalRiskCalculated = recommendedMicros * riskPerContract;
  const percentOfDd = (totalRiskCalculated / tierConfig.dd) * 100;

  // Checklist de Aprobación
  const [checklist, setChecklist] = useState<Record<string, boolean>>({
    noNews: false,
    killSwitch: false,
    twoLossMax: false,
    noTilt: false,
    minTradingDays: false,
    flatBeforeClose: false,
  });

  const toggleCheck = (id: string) => {
    setChecklist((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const completedCount = Object.values(checklist).filter(Boolean).length;

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Protocolo Inteligente de Aprobación de Cuentas</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulos M04 & M16
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Dimensionamiento de microcontratos (MES/MNQ) · Riesgo estricto &lt; 3% del Drawdown · Checklist pre-mercado
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Columna Izquierda: Calculadora de Sizing de Microcontratos */}
        <div className="lg:col-span-6 space-y-4 font-mono text-xs">
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-[11px] tracking-wide flex items-center gap-1.5">
                <Calculator className="w-3.5 h-3.5 text-[var(--profit)]" />
                <span>Dimensionador de Microcontratos</span>
              </span>
              <span className="text-[10px] text-[var(--text-3)]">CME Futures</span>
            </div>

            {/* Selector de Cuenta */}
            <div>
              <label className="block text-[10px] text-[var(--text-3)] mb-1">Tamaño de Cuenta (Tier):</label>
              <div className="grid grid-cols-4 gap-1.5">
                {(["25K", "50K", "100K", "150K"] as const).map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setAccountTier(tier)}
                    className={`py-1.5 rounded text-xs font-bold border transition cursor-pointer ${
                      accountTier === tier
                        ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)]"
                        : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)]"
                    }`}
                  >
                    {tier}
                  </button>
                ))}
              </div>
            </div>

            {/* Instrumento */}
            <div>
              <label className="block text-[10px] text-[var(--text-3)] mb-1">Instrumento a Operar:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setInstrument("MNQ")}
                  className={`py-2 px-3 rounded-md border text-left transition cursor-pointer ${
                    instrument === "MNQ"
                      ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)]"
                      : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)]"
                  }`}
                >
                  <div className="font-bold">Micro Nasdaq (MNQ)</div>
                  <div className="text-[10px] text-[var(--text-3)]">$0.50/tick · $2.00/punto</div>
                </button>
                <button
                  onClick={() => setInstrument("MES")}
                  className={`py-2 px-3 rounded-md border text-left transition cursor-pointer ${
                    instrument === "MES"
                      ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)]"
                      : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)]"
                  }`}
                >
                  <div className="font-bold">Micro S&P (MES)</div>
                  <div className="text-[10px] text-[var(--text-3)]">$1.25/tick · $5.00/punto</div>
                </button>
              </div>
            </div>

            {/* Stop Loss en Ticks */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Distancia de Stop Loss:</label>
                <span className="font-bold text-[var(--text-1)]">
                  {stopLossTicks} ticks ({instrument === "MNQ" ? `${stopLossTicks / 4} pts` : `${stopLossTicks / 4} pts`})
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="120"
                step="2"
                value={stopLossTicks}
                onChange={(e) => setStopLossTicks(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
            </div>

            {/* Riesgo Máximo en Dólares */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Riesgo Máximo Aceptado por Trade:</label>
                <span className="font-bold text-[var(--profit)]">${maxRiskUsd} USD</span>
              </div>
              <input
                type="range"
                min="30"
                max="250"
                step="5"
                value={maxRiskUsd}
                onChange={(e) => setMaxRiskUsd(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
            </div>

            {/* Resultado de Sizing */}
            <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[var(--text-3)] uppercase font-bold">
                  Posición Máxima Sugerida:
                </span>
                <span className="text-lg font-black text-[var(--profit)]">
                  {recommendedMicros} {instrument}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-[11px] pt-1 border-t border-[var(--border)]">
                <div>
                  <span className="text-[var(--text-3)] block">Riesgo Real:</span>
                  <span className="font-bold text-[var(--text-1)]">${totalRiskCalculated.toFixed(2)} USD</span>
                </div>
                <div>
                  <span className="text-[var(--text-3)] block">% del Drawdown:</span>
                  <span className={`font-bold ${percentOfDd > 4 ? "text-[var(--loss)]" : "text-[var(--profit)]"}`}>
                    {percentOfDd.toFixed(2)}% ({percentOfDd <= 4 ? "SEGURO" : "ALTO"})
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Columna Derecha: Checklist Operativo Pre-Mercado (M16) */}
        <div className="lg:col-span-6 space-y-4 font-mono text-xs">
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-[11px] tracking-wide flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)]" />
                <span>Checklist de Disciplina Pre-Mercado (M16)</span>
              </span>
              <span className={`text-[10px] font-bold ${completedCount === 6 ? "text-[var(--profit)]" : "text-[var(--text-3)]"}`}>
                {completedCount}/6 completados
              </span>
            </div>

            <div className="space-y-2">
              {[
                { id: "noNews", label: "Calendario Económico verificado (Cero entradas 2 min antes/después de CPI/FOMC/NFP)" },
                { id: "killSwitch", label: "Kill Switch configurado en Rithmic / Tradovate con pérdida máxima del día fijada" },
                { id: "twoLossMax", label: "Regla de 2 Pérdidas: si fallo 2 veces consecutivas en la sesión, cierro la plataforma" },
                { id: "noTilt", label: "Estado psicológico neutral: sin urgencia de recuperar pérdidas pasadas" },
                { id: "minTradingDays", label: "Respeto al mínimo de días de trading sin intentar pasar el examen en 1 solo disparo" },
                { id: "flatBeforeClose", label: "Posiciones cerradas (Flat) antes de las 16:55 ET para evitar liquidación forzosa" },
              ].map((item) => (
                <div
                  key={item.id}
                  onClick={() => toggleCheck(item.id)}
                  className={`p-2.5 rounded-md border transition cursor-pointer flex items-start gap-2.5 ${
                    checklist[item.id]
                      ? "bg-[var(--surface-2)] border-[var(--border-strong)] text-[var(--text-1)]"
                      : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-2)] hover:bg-[var(--surface-2)]"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={checklist[item.id]}
                    onChange={() => {}}
                    className="mt-0.5 accent-[var(--profit)] cursor-pointer"
                  />
                  <span className="text-[11px] leading-snug font-sans">{item.label}</span>
                </div>
              ))}
            </div>

            {completedCount === 6 ? (
              <div className="p-2.5 rounded bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-center text-xs font-bold">
                ¡PROTOCOLO PRE-MERCADO SUPERADO! PUEDES ABRIR TRADING DESK
              </div>
            ) : (
              <div className="p-2.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)] text-center text-[11px]">
                Completa todos los puntos del checklist antes de enviar órdenes al mercado.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
