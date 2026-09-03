"use client";

import React, { useState } from "react";
import {
  DollarSign,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";

interface FirmPayoutRule {
  firm: string;
  bufferReq50k: number; // Colchón requerido en cuenta de 50K
  payoutSpeed: string;
  first10kPct: number; // 100% de los primeros 10K
  subsequentPct: number; // 90%
  minDaysToPayout: number;
  notes: string;
}

const FIRM_RULES: Record<string, FirmPayoutRule> = {
  mffu: {
    firm: "MyFundedFutures (Rapid)",
    bufferReq50k: 52100,
    payoutSpeed: "24h - 48h (Día 1 On-Demand)",
    first10kPct: 100,
    subsequentPct: 90,
    minDaysToPayout: 1,
    notes: "El trailing drawdown se congela en $50,100. Cualquier balance por encima de $52,100 es retirable en su totalidad.",
  },
  tradeify: {
    firm: "Tradeify (Growth)",
    bufferReq50k: 52000,
    payoutSpeed: "5 Días On-Demand",
    first10kPct: 100,
    subsequentPct: 90,
    minDaysToPayout: 5,
    notes: "Requiere 5 días de trading reales. $0 cuota de activación. 90% split.",
  },
  tradeday: {
    firm: "TradeDay (Day Trader)",
    bufferReq50k: 52000,
    payoutSpeed: "Mismo Día Hábil (Dorman Trading)",
    first10kPct: 100,
    subsequentPct: 90,
    minDaysToPayout: 5,
    notes: "Conexión a broker FCM institucional real. Procesamiento el mismo día sin comisiones ocultas.",
  },
  blusky: {
    firm: "BluSky Trading",
    bufferReq50k: 51500,
    payoutSpeed: "Semanal On-Demand",
    first10kPct: 90,
    subsequentPct: 90,
    minDaysToPayout: 8,
    notes: "Drawdown 100% estático fijado en $48,500. Jamás sube con las ganancias acumuladas.",
  },
  topstep: {
    firm: "Topstep (Express Funded)",
    bufferReq50k: 52000,
    payoutSpeed: "Diario tras 5 días de profit > $200",
    first10kPct: 100,
    subsequentPct: 90,
    minDaysToPayout: 5,
    notes: "50% de las ganancias retirables por solicitud hasta completar 30 días de trading con la empresa.",
  },
};

export default function CicloRetirosPage() {
  const [selectedFirmKey, setSelectedFirmKey] = useState<string>("mffu");
  const [currentBalance, setCurrentBalance] = useState<number>(53400); // $53,400 en cuenta de 50K
  const [accumulatedProfitsThisYear, setAccumulatedProfitsThisYear] = useState<number>(4000);

  const rule = FIRM_RULES[selectedFirmKey];
  const bufferRequired = rule.bufferReq50k;
  const maxWithdrawable = Math.max(0, currentBalance - bufferRequired);

  // Split calculation
  const isWithinFirst10k = accumulatedProfitsThisYear + maxWithdrawable <= 10000;
  const netPayoutEstimate = isWithinFirst10k
    ? maxWithdrawable * (rule.first10kPct / 100)
    : maxWithdrawable * (rule.subsequentPct / 100);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <DollarSign className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Optimizador de Retiros, Buffer & Payouts</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M06
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Cálculo del colchón de seguridad retenido obligatorio · Reparto 100/90 y calendario de liquidación
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Columna Izquierda: Parámetros */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-[11px] tracking-wide">
                Configuración del Payout
              </span>
              <span className="text-[10px] text-[var(--text-3)]">Cuenta 50K</span>
            </div>

            {/* Selector de Empresa */}
            <div>
              <label className="block text-[10px] text-[var(--text-3)] mb-1">Empresa de Fondeo:</label>
              <select
                value={selectedFirmKey}
                onChange={(e) => setSelectedFirmKey(e.target.value)}
                className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded-md px-2.5 py-1.5 text-[var(--text-1)] focus:outline-none"
              >
                {Object.entries(FIRM_RULES).map(([k, v]) => (
                  <option key={k} value={k}>{v.firm}</option>
                ))}
              </select>
            </div>

            {/* Balance Actual */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Balance Actual en Cuenta 50K:</label>
                <span className="font-bold text-[var(--text-1)]">${currentBalance.toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="50000"
                max="60000"
                step="100"
                value={currentBalance}
                onChange={(e) => setCurrentBalance(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$50,000</span>
                <span>$55,000</span>
                <span>$60,000</span>
              </div>
            </div>

            {/* Beneficios Históricos Retirados */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Retiros Previos este Año:</label>
                <span className="font-bold text-[var(--text-1)]">${accumulatedProfitsThisYear.toLocaleString()} USD</span>
              </div>
              <input
                type="range"
                min="0"
                max="20000"
                step="500"
                value={accumulatedProfitsThisYear}
                onChange={(e) => setAccumulatedProfitsThisYear(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>$0 (Primer Retiro)</span>
                <span>$10,000 (Corte 100%)</span>
                <span>$20,000</span>
              </div>
            </div>
          </div>

          {/* Reglas de la Firma */}
          <div className="p-3.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2 text-[11px]">
            <span className="font-bold text-[var(--text-1)] block uppercase">
              Condiciones de {rule.firm}:
            </span>
            <p className="text-[var(--text-3)] leading-relaxed font-sans">
              {rule.notes}
            </p>
          </div>
        </div>

        {/* Columna Derecha: Liquidación y Desglose */}
        <div className="lg:col-span-7 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Colchón Retenido</span>
              <span className="text-xl font-bold text-[var(--text-1)]">
                ${bufferRequired.toLocaleString()}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">balance mínimo intacto</span>
            </div>

            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Retiro Bruto Posible</span>
              <span className={`text-xl font-bold ${maxWithdrawable > 0 ? "text-[var(--profit)]" : "text-[var(--loss)]"}`}>
                ${maxWithdrawable.toLocaleString()}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">
                {maxWithdrawable > 0 ? "Disponible hoy" : "Colchón no alcanzado"}
              </span>
            </div>

            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Neto en tu Banco</span>
              <span className="text-xl font-bold text-[var(--profit)]">
                ${netPayoutEstimate.toLocaleString()}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">
                {isWithinFirst10k ? "100% de los primeros $10K" : "90% split posterior"}
              </span>
            </div>
          </div>

          {/* Desglose de Frecuencia y Transferencia */}
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3 font-sans text-xs">
            <div className="flex items-center justify-between font-mono border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-xs flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[var(--profit)]" />
                <span>Velocidad de Transferencia y Protocolo</span>
              </span>
              <span className="text-[11px] text-[var(--profit)] font-bold">{rule.payoutSpeed}</span>
            </div>

            <div className="space-y-2 text-[11px] text-[var(--text-2)] leading-relaxed">
              <div className="flex justify-between border-b border-[var(--border)] pb-1.5 font-mono">
                <span className="text-[var(--text-3)]">Días mínimos de trading requeridos:</span>
                <span className="text-[var(--text-1)] font-bold">{rule.minDaysToPayout} días</span>
              </div>
              <div className="flex justify-between border-b border-[var(--border)] pb-1.5 font-mono">
                <span className="text-[var(--text-3)]">Balance restante en cuenta tras retiro:</span>
                <span className="text-[var(--text-1)] font-bold">${bufferRequired.toLocaleString()} USD</span>
              </div>
              <div className="flex justify-between font-mono">
                <span className="text-[var(--text-3)]">Destino recomendado (Regla 80/20):</span>
                <span className="text-[var(--profit)] font-bold">
                  ${(netPayoutEstimate * 0.8).toFixed(0)} a Banco / ${(netPayoutEstimate * 0.2).toFixed(0)} a Bóveda Exámenes
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
