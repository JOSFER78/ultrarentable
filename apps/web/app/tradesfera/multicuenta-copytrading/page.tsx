"use client";

import React, { useState } from "react";
import {
  Layers,
  Copy,
  ShieldCheck,
  CheckCircle2,
  DollarSign,
  Info,
  Server,
  TrendingUp,
} from "lucide-react";

export default function MulticuentaCopytradingPage() {
  const [numAccounts, setNumAccounts] = useState<number>(5);
  const [microsPerAccount, setMicrosPerAccount] = useState<number>(2); // 2 micros por cuenta
  const [targetPointsPerDay, setTargetPointsPerDay] = useState<number>(15); // 15 puntos en NQ
  const [firmsDistribution, setFirmsDistribution] = useState<string[]>([
    "MyFundedFutures",
    "Tradeify",
    "TradeDay",
    "Topstep",
    "BluSky",
  ]);

  // Cálculos consolidados
  const totalMicrosExecuted = numAccounts * microsPerAccount;
  const valuePerPointPerMicro = 2.0; // $2 por punto en MNQ
  const dollarPerPointConsolidated = totalMicrosExecuted * valuePerPointPerMicro;
  const dailyProfitProjected = dollarPerPointConsolidated * targetPointsPerDay;
  const monthlyProfitProjected = dailyProfitProjected * 20; // 20 sesiones

  // Diversificación de riesgo
  const maxFirmSharePct = firmsDistribution.length > 0 ? (1 / firmsDistribution.length) * 100 : 100;

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Arquitectura Multicuenta & Copytrading Institucional</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M05
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Replicación determinista Tradovate / NinjaTrader · Diversificación inter-firma y límites consolidados CME
            </p>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Parámetros de la Flota */}
        <div className="lg:col-span-5 space-y-4 font-mono text-xs">
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <span className="font-bold text-[var(--text-1)] uppercase text-[11px] tracking-wide flex items-center gap-1.5">
                <Server className="w-3.5 h-3.5 text-[var(--text-2)]" />
                <span>Configuración de la Flota</span>
              </span>
              <span className="text-[10px] text-[var(--text-3)]">Copy Trading</span>
            </div>

            {/* Número de Cuentas */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Cuentas en Replicación Activa:</label>
                <span className="font-bold text-[var(--profit)]">{numAccounts} cuentas</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                step="1"
                value={numAccounts}
                onChange={(e) => setNumAccounts(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-[var(--text-3)] mt-0.5">
                <span>1 cuenta</span>
                <span>5 (Recomendado)</span>
                <span>20 (Flota Máxima)</span>
              </div>
            </div>

            {/* Contratos por Cuenta */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Micros MNQ por Cuenta Master:</label>
                <span className="font-bold text-[var(--text-1)]">{microsPerAccount} micros</span>
              </div>
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                value={microsPerAccount}
                onChange={(e) => setMicrosPerAccount(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
            </div>

            {/* Puntos Objetivo al Día */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <label className="text-[var(--text-2)]">Puntos Objetivo en NQ por Sesión:</label>
                <span className="font-bold text-[var(--text-1)]">{targetPointsPerDay} pts (NQ)</span>
              </div>
              <input
                type="range"
                min="5"
                max="40"
                step="1"
                value={targetPointsPerDay}
                onChange={(e) => setTargetPointsPerDay(Number(e.target.value))}
                className="w-full accent-[var(--profit)] cursor-pointer"
              />
            </div>

            {/* Firmas en la Canasta */}
            <div className="pt-2 border-t border-[var(--border)]">
              <label className="block text-[10px] text-[var(--text-3)] mb-1 uppercase">
                Canasta de Firmas para Reducción de Riesgo de Contraparte:
              </label>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {["MyFundedFutures", "Tradeify", "TradeDay", "Topstep", "BluSky"].map((f) => (
                  <span
                    key={f}
                    className="px-2 py-1 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[10.5px] text-[var(--text-1)]"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Panel de Resultados Consolidados */}
        <div className="lg:col-span-7 space-y-4 font-mono text-xs">
          {/* Métricas Consolidadas */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Micros Totales</span>
              <span className="text-xl font-bold text-[var(--text-1)]">{totalMicrosExecuted}</span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">en el mercado</span>
            </div>
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">$/Punto Flota</span>
              <span className="text-xl font-bold text-[var(--profit)]">
                ${dollarPerPointConsolidated.toFixed(0)}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">por cada punto NQ</span>
            </div>
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Sesión Estimada</span>
              <span className="text-xl font-bold text-[var(--text-1)]">
                ${dailyProfitProjected.toLocaleString()}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">con {targetPointsPerDay} pts</span>
            </div>
            <div className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Mensual Proyectado</span>
              <span className="text-xl font-bold text-[var(--profit)]">
                ${monthlyProfitProjected.toLocaleString()}
              </span>
              <span className="text-[10px] text-[var(--text-3)] block mt-0.5">20 sesiones</span>
            </div>
          </div>

          {/* Análisis de Resiliencia Institucional */}
          <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3 font-sans text-xs">
            <div className="flex items-center gap-2 font-mono text-sm font-bold text-[var(--text-1)] border-b border-[var(--border)] pb-2">
              <ShieldCheck className="w-4 h-4 text-[var(--profit)]" />
              <span>Por qué el Modelo Multicuenta vence a la Cuenta Individual</span>
            </div>
            <div className="space-y-2 text-[11px] text-[var(--text-2)] leading-relaxed">
              <p>
                1. <strong>Mitigación de la fatiga emocional:</strong> En vez de arriesgar $500 en una sola cuenta grande para buscar $1,500, operas 2 microcontratos cómodamente arriesgando $60 por cuenta. La presión mental es idéntica a una cuenta pequeña, pero el resultado se multiplica por {numAccounts}.
              </p>
              <p>
                2. <strong>Blindaje ante impagos o cambios de reglas:</strong> Al repartir las cuentas en firmas independientes ({firmsDistribution.join(", ")}), ninguna quiebra o cambio repentino de política puede comprometer más del {maxFirmSharePct.toFixed(0)}% de tu flujo de retiros.
              </p>
              <p>
                3. <strong>Retiros escalonados continuos:</strong> Una firma paga semanalmente, otra quincenalmente y otra on-demand tras 5 días. Esto produce un flujo de caja semanal constante sin depender del calendario de una sola empresa.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
