"use client";

import React, { useState, useMemo } from "react";
import { ALL_PROP_FIRM_ACCOUNTS } from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";
import { Calculator, Sparkles, ShieldCheck, DollarSign, TrendingUp, ArrowUpRight } from "lucide-react";

export function ExtractionRoiCalculator() {
  const [selectedSize, setSelectedSize] = useState<number>(50000);
  const [monthsToPass, setMonthsToPass] = useState<number>(1);
  const [targetCapital, setTargetCapital] = useState<number>(10000);

  const simulationResults = useMemo(() => {
    return ALL_PROP_FIRM_ACCOUNTS
      .filter((acc) => acc.account_size_usd === selectedSize)
      .map((acc) => {
        const examCost = acc.exam_price_promo_usd;
        const monthlyRecurrence = acc.monthly_renewal_usd;
        const recurringCost = monthsToPass > 1 ? (monthsToPass - 1) * monthlyRecurrence : 0;
        const activationFee = acc.activation_fee_usd;
        const totalInvested = examCost + recurringCost + activationFee;
        const safetyBuffer = acc.safety_buffer_usd;
        const netCashExtracted = Math.max(0, targetCapital - safetyBuffer);
        const netProfit = netCashExtracted - totalInvested;
        const trueRoiMultiple = totalInvested > 0 ? netCashExtracted / totalInvested : 0;
        const requiredGrossProfit = targetCapital + acc.profit_target_usd;

        return {
          account: acc,
          examCost,
          recurringCost,
          activationFee,
          totalInvested,
          safetyBuffer,
          netCashExtracted,
          netProfit,
          trueRoiMultiple,
          requiredGrossProfit,
        };
      })
      .sort((a, b) => b.trueRoiMultiple - a.trueRoiMultiple);
  }, [selectedSize, monthsToPass, targetCapital]);

  const topAccount = simulationResults.length > 0 ? simulationResults[0] : null;

  return (
    <div className="w-full space-y-6">
      {/* 1. CONTROLES DEL SIMULADOR */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-white tracking-tight">
                Calculadora Cuantitativa de Coste Real de Extracción & ROI
              </h2>
              <p className="text-xs text-slate-400">
                Modela la inversión real desembolsada (Examen con Promo + Activación + Buffer) y el retorno neto real al extraer tus primeros ${targetCapital.toLocaleString()} USD.
              </p>
            </div>
          </div>
          {topAccount && (
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 text-xs font-mono font-bold shrink-0">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>Máx. ROI: {topAccount.trueRoiMultiple.toFixed(1)}x ({topAccount.account.firm_name})</span>
            </div>
          )}
        </div>

        {/* Sliders and Selects */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Tamaño */}
          <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 space-y-2">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono block">
              1. Tamaño de Cuenta
            </label>
            <select
              value={selectedSize}
              onChange={(e) => setSelectedSize(Number(e.target.value))}
              className="w-full bg-[#030712] text-white border border-slate-700/80 rounded-lg px-3 py-2 text-xs font-bold font-mono focus:border-emerald-500 focus:outline-none"
            >
              <option value={25000}>$25,000 USD (Micro / Starter)</option>
              <option value={50000}>$50,000 USD (Estándar Recomendado)</option>
              <option value={100000}>$100,000 USD (Avanzado)</option>
              <option value={150000}>$150,000 USD (Master / Whale)</option>
            </select>
            <span className="text-[10px] text-slate-500 block font-mono">
              Filtra entre las 70 cuentas auditadas
            </span>
          </div>

          {/* Meses para pasar */}
          <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
              <span>2. Tiempo para Aprobar:</span>
              <span className="text-sky-400">{monthsToPass} {monthsToPass === 1 ? "mes (1 Cuota)" : "meses (Renovaciones)"}</span>
            </div>
            <input
              type="range"
              min={1}
              max={4}
              value={monthsToPass}
              onChange={(e) => setMonthsToPass(Number(e.target.value))}
              className="w-full accent-sky-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>1 mes (Flash)</span>
              <span>2 meses</span>
              <span>3 meses</span>
              <span>4 meses</span>
            </div>
          </div>

          {/* Ganancia a Extraer */}
          <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 space-y-2">
            <div className="flex justify-between items-center text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">
              <span>3. Beneficio Objetivo:</span>
              <span className="text-emerald-400">${targetCapital.toLocaleString()} USD</span>
            </div>
            <input
              type="range"
              min={2500}
              max={25000}
              step={500}
              value={targetCapital}
              onChange={(e) => setTargetCapital(Number(e.target.value))}
              className="w-full accent-emerald-400 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>$2,500</span>
              <span>$10,000</span>
              <span>$25,000</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. TABLA DE RESULTADOS DE RETORNO Y EXTRACCIÓN */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-black text-white tracking-tight flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Ranking de Eficiencia Financiera (${(selectedSize / 1000).toFixed(0)}K)</span>
            </h3>
            <p className="text-xs text-slate-400">
              Ordenado de mayor a menor múltiplo de ROI real sobre el capital total invertido.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-500">
            {simulationResults.length} Cuentas Comparadas
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                <th className="py-3 px-3">Firma / Modalidad</th>
                <th className="py-3 px-3 text-right">Inversión Total (TCO)</th>
                <th className="py-3 px-3 text-right">Colchón Buffer</th>
                <th className="py-3 px-3 text-right">Cash Neto Extraído</th>
                <th className="py-3 px-3 text-right">Múltiplo ROI</th>
                <th className="py-3 px-3 text-center">Acción Directa</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {simulationResults.map((item, idx) => {
                const isBest = idx === 0;
                return (
                  <tr
                    key={item.account.id}
                    className={`transition-colors ${
                      isBest ? "bg-emerald-950/20 hover:bg-emerald-950/30" : "hover:bg-slate-900/40"
                    }`}
                  >
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        {isBest && (
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-black border border-emerald-500/40">
                            #1 TOP
                          </span>
                        )}
                        <div>
                          <span className="font-bold text-white text-sm">{item.account.firm_name}</span>
                          <div className="text-[11px] text-slate-400 font-sans">
                            {item.account.program_name} · {item.account.drawdown_type}
                          </div>
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-3 text-right tabular-nums">
                      <div className="font-bold text-white text-sm">
                        ${item.totalInvested.toFixed(2)}
                      </div>
                      <div className="text-[10px] text-slate-500">
                        Exam: ${item.examCost.toFixed(2)} + Act: ${item.activationFee.toFixed(2)}
                      </div>
                    </td>

                    <td className="py-3 px-3 text-right tabular-nums">
                      <span className="text-slate-300">
                        ${item.safetyBuffer.toLocaleString()}
                      </span>
                      <div className="text-[10px] text-slate-500">
                        Retención inicial
                      </div>
                    </td>

                    <td className="py-3 px-3 text-right tabular-nums">
                      <div className="font-bold text-emerald-400 text-sm">
                        ${item.netCashExtracted.toLocaleString()}
                      </div>
                      <div className="text-[10px] text-emerald-500/80">
                        Beneficio neto: +${item.netProfit.toFixed(2)}
                      </div>
                    </td>

                    <td className="py-3 px-3 text-right tabular-nums">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-lg font-black text-xs ${
                          item.trueRoiMultiple >= 100
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : item.trueRoiMultiple >= 50
                            ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                            : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                        }`}
                      >
                        {item.trueRoiMultiple.toFixed(1)}x
                      </span>
                    </td>

                    <td className="py-3 px-3 text-center">
                      <BuyButtonWithCoupon
                        affiliateUrl={item.account.affiliate_url}
                        couponCode={item.account.active_coupon_code}
                        variant="compact"
                        buttonText={`Comprar ${item.account.active_coupon_code} ↗`}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
