"use client";

import React, { useState } from "react";
import {
  Calculator,
  DollarSign,
  TrendingUp,
  ShieldCheck,
  Zap,
  Info,
  ArrowRight,
  PieChart,
  Target,
} from "lucide-react";

export default function CalculadoraBankrollPage() {
  const [bankroll, setBankroll] = useState<number>(1000);
  const [costPerExam, setCostPerExam] = useState<number>(50);
  const [passRatePct, setPassRatePct] = useState<number>(25);
  const [targetPayout, setTargetPayout] = useState<number>(2000);

  // Cálculos matemáticos M02
  const numShots = Math.max(1, Math.floor(bankroll / Math.max(1, costPerExam)));
  const p = Math.min(0.99, Math.max(0.01, passRatePct / 100));
  const cumulativePassProb = 1 - Math.pow(1 - p, numShots);
  const expectedPasses = numShots * p;
  const totalCost = numShots * costPerExam;
  const expectedGrossReturn = expectedPasses * targetPayout;
  const netEV = expectedGrossReturn - totalCost;
  const roiPct = totalCost > 0 ? (netEV / totalCost) * 100 : 0;

  // Regla de cosecha 80/20
  const harvestSafety = targetPayout * 0.8;
  const harvestReinvest = targetPayout * 0.2;

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Calculator className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Calculadora de Bankroll & Capital Munición</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)] font-mono">
                Módulo M02
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Formulación binomial: P(Aprobación &ge; 1) = 1 &minus; (1 &minus; p)<sup>N</sup> · Esperanza matemática positiva (EV)
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid: Controls + Interactive Outputs */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Columna Izquierda: Parámetros de Entrada */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-[11px] tracking-wide">
                Parámetros del Operador
              </span>
              <span className="text-[10px] text-[var(--text-3)]">Regla de Munición</span>
            </div>

            {/* Input 1: Bankroll Total */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Bankroll Total Disponible:</label>
                <span className="font-bold text-[var(--text-1)]">${bankroll.toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="100"
                max="5000"
                step="50"
                value={bankroll}
                onChange={(e) => setBankroll(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$100</span>
                <span>$2,500</span>
                <span>$5,000</span>
              </div>
            </div>

            {/* Input 2: Coste del Examen */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Coste por Examen con Cupón:</label>
                <span className="font-bold text-[var(--text-1)]">${costPerExam} USD</span>
              </div>
              <input
                type="range"
                min="20"
                max="250"
                step="5"
                value={costPerExam}
                onChange={(e) => setCostPerExam(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$20 (Ofertas)</span>
                <span>$50 (Estándar)</span>
                <span>$250 (Full)</span>
              </div>
            </div>

            {/* Input 3: Tasa de Acierto Individual */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Tasa Estimada de Pase (p):</label>
                <span className="font-bold text-[var(--profit)]">{passRatePct}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="60"
                step="1"
                value={passRatePct}
                onChange={(e) => setPassRatePct(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>5% (Principiante)</span>
                <span>25% (Auditado M02)</span>
                <span>60% (Master Quant)</span>
              </div>
            </div>

            {/* Input 4: Payout Objetivo */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Retiro Estimado por Cuenta Aprobada:</label>
                <span className="font-bold text-[var(--text-1)]">${targetPayout.toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="500"
                max="10000"
                step="250"
                value={targetPayout}
                onChange={(e) => setTargetPayout(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$500</span>
                <span>$2,000 (Buffer estándar)</span>
                <span>$10,000</span>
              </div>
            </div>
          </div>

          {/* Caja Teórica M02 */}
          <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2 text-xs">
            <div className="flex items-center gap-1.5 text-[var(--text-2)] font-mono text-[11px] font-bold uppercase">
              <Info className="w-3.5 h-3.5" />
              <span>Doctrina de Extracción Asimétrica</span>
            </div>
            <p className="text-[11px] text-[var(--text-3)] leading-relaxed font-sans">
              Una cuenta de fondeo tiene vida útil finita. Nunca compres un único examen con tu último dinero: la clave reside en disponer de un paquete de munición de al menos 8–10 disparos para que la ley de grandes números absorba la varianza.
            </p>
          </div>
        </div>

        {/* Columna Derecha: Resultados y Métricas Probabilísticas */}
        <div className="lg:col-span-7 space-y-4">
          {/* Métricas Principales */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono">
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Munición</span>
              <span className="text-xl font-bold text-[var(--text-1)]">{numShots}</span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">disparos totales</span>
            </div>
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Prob. Cobro</span>
              <span className={`text-xl font-bold ${cumulativePassProb >= 0.9 ? "text-[var(--profit)]" : "text-[var(--text-1)]"}`}>
                {(cumulativePassProb * 100).toFixed(1)}%
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">P(&ge; 1 cobro)</span>
            </div>
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Aprobados Esperados</span>
              <span className="text-xl font-bold text-[var(--text-1)]">{expectedPasses.toFixed(1)}</span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">cuentas fondeadas</span>
            </div>
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">EV Neto</span>
              <span className={`text-xl font-bold ${netEV >= 0 ? "text-[var(--profit)]" : "text-[var(--loss)]"}`}>
                {netEV >= 0 ? "+" : ""}${netEV.toFixed(0)}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">ROI: {roiPct.toFixed(0)}%</span>
            </div>
          </div>

          {/* Barra Visual de Probabilidad Acumulada */}
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2.5 font-mono">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-2)]">Probabilidad Binomial de Cobrar al menos 1 Cuenta:</span>
              <span className="font-bold text-[var(--profit)]">{(cumulativePassProb * 100).toFixed(2)}%</span>
            </div>
            <div className="w-full h-3 bg-[var(--surface-2)] rounded-full overflow-hidden border border-[var(--border)]">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  cumulativePassProb >= 0.9 ? "bg-[var(--profit)]" : "bg-[var(--text-2)]"
                }`}
                style={{ width: `${Math.min(100, Math.max(2, cumulativePassProb * 100))}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-[var(--text-3)]">
              <span>0% (Riesgo total)</span>
              <span>50% (Moneda al aire)</span>
              <span className="text-[var(--profit)] font-bold">95% (Zona Óptima de Bankroll)</span>
            </div>
          </div>

          {/* Regla de Cosecha 80/20 */}
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3 font-mono text-xs">
            <div className="flex items-center gap-2 text-sm font-bold text-[var(--text-1)] border-b border-[var(--border)] pb-2">
              <PieChart className="w-4 h-4 text-[var(--profit)]" />
              <span>Protocolo de Cosecha de Beneficios 80/20</span>
            </div>
            <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
              Por cada retiro obtenido de una prop firm, el operador cuantitativo divide inmediatamente el capital en dos cestas inquebrantables:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
              <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1">
                <span className="text-[10px] text-[var(--profit)] uppercase font-bold block">
                  80% · Patrimonio Seguro Inmutable
                </span>
                <span className="text-lg font-bold text-[var(--text-1)]">
                  ${harvestSafety.toLocaleString()} USD
                </span>
                <p className="text-[10px] text-[var(--text-3)] font-sans">
                  Transferencia bancaria / cuenta remunerada / indexados. Jamás vuelve al mercado de futuros.
                </p>
              </div>

              <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1">
                <span className="text-[10px] text-[var(--text-2)] uppercase font-bold block">
                  20% · Bóveda de Munición Reinvertible
                </span>
                <span className="text-lg font-bold text-[var(--text-1)]">
                  ${harvestReinvest.toLocaleString()} USD
                </span>
                <p className="text-[10px] text-[var(--text-3)] font-sans">
                  Permite adquirir {Math.floor(harvestReinvest / Math.max(1, costPerExam))} nuevos exámenes para reiniciar el ciclo de extracción.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
