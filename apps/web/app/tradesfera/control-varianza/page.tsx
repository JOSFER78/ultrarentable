"use client";

import React, { useState } from "react";
import {
  TrendingDown,
  AlertTriangle,
  ShieldCheck,
  Zap,
  Info,
  Sliders,
  Layers,
  CheckCircle2,
} from "lucide-react";

export default function ControlVarianzaPage() {
  const [maxDd, setMaxDd] = useState<number>(2000); // $2,000 drawdown en 50K
  const [riskPerTrade, setRiskPerTrade] = useState<number>(80); // $80 por trade en micro
  const [winRatePct, setWinRatePct] = useState<number>(50); // 50% win rate
  const [rrRatio, setRrRatio] = useState<number>(1.5); // Risk Reward 1:1.5
  const [numTrades, setNumTrades] = useState<number>(60); // 60 trades en la muestra

  // Cálculos de varianza
  const lossRate = (100 - winRatePct) / 100;
  const maxConsecutiveLossesTolerated = Math.floor(maxDd / Math.max(1, riskPerTrade));

  // Probabilidad de sufrir racha de 5 pérdidas consecutivas
  const prob5Losses = Math.min(1, 1 - Math.pow(1 - Math.pow(lossRate, 5), Math.max(1, numTrades / 5)));
  // Probabilidad de sufrir racha de 8 pérdidas consecutivas
  const prob8Losses = Math.min(1, 1 - Math.pow(1 - Math.pow(lossRate, 8), Math.max(1, numTrades / 8)));

  // Probabilidad aproximada de ruina bajo EOD vs Intraday
  const riskPctOfDd = (riskPerTrade / maxDd) * 100;
  const ruinEodApprox = Math.min(99, Math.max(1, riskPctOfDd * 1.8 * (1 - winRatePct / 100)));
  const ruinIntradayApprox = Math.min(99, ruinEodApprox * 3.4);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-1)]">
            <TrendingDown className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Simulador de Varianza & Trailing Drawdown</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M03
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Modelado de drawdown intra-trade vs EOD · Probabilidad de rachas consecutivas y mitigación de ruina absoluta
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Panel Izquierdo: Parámetros */}
        <div className="lg:col-span-5 space-y-4 font-mono text-xs">
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-[11px] tracking-wide">
                Parámetros de Riesgo
              </span>
              <span className="text-[10px] text-[var(--text-3)]">Microestructura</span>
            </div>

            {/* Drawdown Total */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Colchón de Drawdown Máximo:</label>
                <span className="font-bold text-[var(--text-1)]">${maxDd.toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="1000"
                max="5000"
                step="250"
                value={maxDd}
                onChange={(e) => setMaxDd(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$1,000 (25K)</span>
                <span>$2,000 (50K)</span>
                <span>$5,000 (150K)</span>
              </div>
            </div>

            {/* Riesgo por Trade */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Riesgo Monetario por Trade ($):</label>
                <span className={`font-bold ${riskPctOfDd > 5 ? "text-[var(--loss)]" : "text-[var(--profit)]"}`}>
                  ${riskPerTrade} USD ({riskPctOfDd.toFixed(1)}% del DD)
                </span>
              </div>
              <input
                type="range"
                min="30"
                max="300"
                step="5"
                value={riskPerTrade}
                onChange={(e) => setRiskPerTrade(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$30 (1 Micro)</span>
                <span>$80 (2 Micros Óptimo)</span>
                <span>$300 (Peligro)</span>
              </div>
            </div>

            {/* Win Rate */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Win Rate Operativo (%):</label>
                <span className="font-bold text-[var(--text-1)]">{winRatePct}%</span>
              </div>
              <input
                type="range"
                min="35"
                max="70"
                step="1"
                value={winRatePct}
                onChange={(e) => setWinRatePct(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
            </div>

            {/* Número de trades */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Muestra de Operaciones:</label>
                <span className="font-bold text-[var(--text-1)]">{numTrades} trades</span>
              </div>
              <input
                type="range"
                min="20"
                max="120"
                step="10"
                value={numTrades}
                onChange={(e) => setNumTrades(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
            </div>
          </div>

          {/* Advertencia de Intraday Peak */}
          <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-1.5 text-xs">
            <div className="flex items-center gap-1.5 text-[var(--text-2)] font-mono text-[11px] font-bold uppercase">
              <AlertTriangle className="w-3.5 h-3.5 text-[var(--text-2)]" />
              <span>La Trampa del Drawdown Intraday</span>
            </div>
            <p className="text-[11px] text-[var(--text-3)] leading-relaxed font-sans">
              En empresas con trailing intradía (Apex/Bulenox), el flotante no realizado sube tu umbral de liquidación en tiempo real trade a trade. Si no aseguras con microcontratos o profit targets rápidos, la varianza devora la cuenta en retrocesos normales.
            </p>
          </div>
        </div>

        {/* Panel Derecho: Comparativa Forense & Rachas */}
        <div className="lg:col-span-7 space-y-4 font-mono text-xs">
          {/* Tarjetas de Ruina */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-[var(--text-1)] uppercase">
                  Drawdown EOD (Al Cierre)
                </span>
                <span className="px-2 py-0.5 rounded bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-[10px] font-bold">
                  RECOMENDADO
                </span>
              </div>
              <span className="text-2xl font-bold text-[var(--text-1)]">
                {ruinEodApprox.toFixed(1)}%
              </span>
              <p className="text-[10px] text-[var(--text-3)] font-sans">
                Riesgo estimado de quiebra. MFFU, Tradeify, TradeDay. El drawdown se fija únicamente al finalizar la sesión a las 17:00 ET.
              </p>
            </div>

            <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-[var(--text-1)] uppercase">
                  Drawdown Intraday Peak
                </span>
                <span className="px-2 py-0.5 rounded bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)] text-[10px] font-bold">
                  +340% RIESGO
                </span>
              </div>
              <span className="text-2xl font-bold text-[var(--loss)]">
                {ruinIntradayApprox.toFixed(1)}%
              </span>
              <p className="text-[10px] text-[var(--text-3)] font-sans">
                Riesgo estimado de quiebra. Apex, Bulenox (Standard). El flotante persigue el precio al tick.
              </p>
            </div>
          </div>

          {/* Matriz de Rachas Adversas Esperadas */}
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-xs">
                Matriz de Supervivencia a Rachas Adversas
              </span>
              <span className="text-[10px] text-[var(--text-3)]">Muestra de {numTrades} trades</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-center">
              <div className="p-2.5 bg-[var(--surface-2)] border border-[var(--border)] rounded-md">
                <span className="text-[10px] text-[var(--text-3)] block uppercase">Pérdidas Soportadas</span>
                <span className="text-lg font-bold text-[var(--profit)]">
                  {maxConsecutiveLossesTolerated} trades
                </span>
                <span className="text-[9.5px] text-[var(--text-3)] block mt-0.5">antes de liquidación</span>
              </div>

              <div className="p-2.5 bg-[var(--surface-2)] border border-[var(--border)] rounded-md">
                <span className="text-[10px] text-[var(--text-3)] block uppercase">Racha de 5 Seguidas</span>
                <span className="text-lg font-bold text-[var(--text-1)]">
                  {(prob5Losses * 100).toFixed(1)}%
                </span>
                <span className="text-[9.5px] text-[var(--text-3)] block mt-0.5">probabilidad de ocurrir</span>
              </div>

              <div className="p-2.5 bg-[var(--surface-2)] border border-[var(--border)] rounded-md">
                <span className="text-[10px] text-[var(--text-3)] block uppercase">Racha de 8 Seguidas</span>
                <span className="text-lg font-bold text-[var(--text-1)]">
                  {(prob8Losses * 100).toFixed(1)}%
                </span>
                <span className="text-[9.5px] text-[var(--text-3)] block mt-0.5">probabilidad de ocurrir</span>
              </div>
            </div>

            {/* Checklist de Blindaje */}
            <div className="pt-2 border-t border-[var(--border)] space-y-1.5 font-sans text-xs">
              <span className="font-bold font-mono text-[11px] text-[var(--text-1)] block uppercase">
                Reglas de Blindaje Operativo M03:
              </span>
              <div className="flex items-start gap-2 text-[var(--text-2)] text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)] shrink-0 mt-0.5" />
                <span>Riesgo por trade nunca superior al 4% del colchón de drawdown disponible (${(maxDd * 0.04).toFixed(0)} USD).</span>
              </div>
              <div className="flex items-start gap-2 text-[var(--text-2)] text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)] shrink-0 mt-0.5" />
                <span>Si sufres 2 pérdidas en la misma sesión, apaga la pantalla (Kill Switch preventivo).</span>
              </div>
              <div className="flex items-start gap-2 text-[var(--text-2)] text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)] shrink-0 mt-0.5" />
                <span>Usa microcontratos (MES en vez de ES) para fraccionar salidas y no tragar retrocesos enteros.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
