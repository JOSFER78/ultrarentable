"use client";

import React, { useState, useMemo } from "react";
import { Sparkles, Check, Copy, ExternalLink, ShieldCheck, DollarSign, Bot, Activity } from "lucide-react";
import { PropFirmAccount } from "@/lib/prop-firms";

interface SmartFinderProps {
  allAccounts: PropFirmAccount[];
  onSelectAccount?: (account: PropFirmAccount) => void;
}

export default function Smart3ClickFinder({ allAccounts }: SmartFinderProps) {
  const [budgetStep, setBudgetStep] = useState<string>("MID"); // LOW (<$50), MID ($50-$100), HIGH (>$100)
  const [algoStep, setAlgoStep] = useState<string>("YES"); // YES (Bots permitidos), ANY
  const [ddStep, setDdStep] = useState<string>("EOD"); // EOD (Fin de día), STATIC (Fijo), ANY

  const [copiedCoupon, setCopiedCoupon] = useState<string | null>(null);

  const handleCopyCoupon = (coupon: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(coupon);
      setCopiedCoupon(coupon);
      setTimeout(() => setCopiedCoupon(null), 2000);
    }
  };

  const recommendedAccounts = useMemo(() => {
    return allAccounts
      .filter((acc) => {
        const price = acc.exam_price_promo_usd || acc.exam_price_regular_usd || 50;
        if (budgetStep === "LOW" && price > 60) return false;
        if (budgetStep === "MID" && (price < 40 || price > 130)) return false;
        if (budgetStep === "HIGH" && price < 100) return false;

        if (algoStep === "YES" && acc.bot_policy === "PROHIBITED") return false;

        if (ddStep === "EOD" && acc.drawdown_type !== "EOD_TRAILING" && acc.drawdown_type !== "STATIC") return false;
        if (ddStep === "STATIC" && acc.drawdown_type !== "STATIC") return false;

        return true;
      })
      .slice(0, 3);
  }, [allAccounts, budgetStep, algoStep, ddStep]);

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-amber-950/30 rounded-2xl border border-amber-500/40 p-5 md:p-6 shadow-2xl space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Sparkles className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-black text-white tracking-tight">
              Asistente Rápido en 3 Clics — Encuentra tu Cuenta Ideal
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Filtra entre 70 cuentas según tu presupuesto, permiso de robots algorítmicos y tipo de límite de pérdida.
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-[11px] font-bold font-mono bg-amber-500/10 text-amber-300 border border-amber-500/30 self-start sm:self-auto">
          RECOMENDADOR INTELIGENTE
        </span>
      </div>

      {/* 3 Steps Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Step 1: Budget */}
        <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <DollarSign className="w-4 h-4 text-emerald-400" />
            1. ¿Cuánto quieres invertir?
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {[
              { key: "LOW", label: "$30 - $60", desc: "Económica" },
              { key: "MID", label: "$60 - $120", desc: "Estándar $50K" },
              { key: "HIGH", label: "+$120", desc: "Pro $100K+" },
            ].map((b) => (
              <button
                key={b.key}
                onClick={() => setBudgetStep(b.key)}
                className={`p-2 rounded-lg text-center transition border text-xs font-bold ${
                  budgetStep === b.key
                    ? "bg-emerald-950 text-emerald-300 border-emerald-500 shadow-sm"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
              >
                <span className="block">{b.label}</span>
                <span className="text-[9px] font-normal text-slate-500 block">{b.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Bots / Algo */}
        <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <Bot className="w-4 h-4 text-indigo-400" />
            2. ¿Usarás Robots / Bots?
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {[
              { key: "YES", label: "Sí (Permitidos)", desc: "100% Automatizado" },
              { key: "ANY", label: "Cualquiera", desc: "Manual / Híbrido" },
            ].map((a) => (
              <button
                key={a.key}
                onClick={() => setAlgoStep(a.key)}
                className={`p-2 rounded-lg text-center transition border text-xs font-bold ${
                  algoStep === a.key
                    ? "bg-indigo-950 text-indigo-300 border-indigo-500 shadow-sm"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
              >
                <span className="block">{a.label}</span>
                <span className="text-[9px] font-normal text-slate-500 block">{a.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Drawdown Type */}
        <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <Activity className="w-4 h-4 text-amber-400" />
            3. Tipo de Límite (Drawdown)
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {[
              { key: "EOD", label: "Fin de Día", desc: "Más Seguro" },
              { key: "STATIC", label: "Estático", desc: "Fijo Inamovible" },
              { key: "ANY", label: "Todos", desc: "Sin Filtro" },
            ].map((d) => (
              <button
                key={d.key}
                onClick={() => setDdStep(d.key)}
                className={`p-2 rounded-lg text-center transition border text-xs font-bold ${
                  ddStep === d.key
                    ? "bg-amber-950 text-amber-300 border-amber-500 shadow-sm"
                    : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
                }`}
              >
                <span className="block">{d.label}</span>
                <span className="text-[9px] font-normal text-slate-500 block">{d.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 3 Best Recommendations */}
      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2 font-mono">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          Las Mejores Opciones Encontradas ({recommendedAccounts.length}):
        </h3>

        {recommendedAccounts.length === 0 ? (
          <div className="py-8 text-center text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800">
            No se encontraron cuentas con esta combinación exacta. Prueba seleccionando &ldquo;Todos&rdquo; en el tipo de límite.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recommendedAccounts.map((acc, idx) => {
              const hasActivationFee = (acc.activation_fee_usd || 0) > 0;
              return (
                <div
                  key={acc.id || idx}
                  className="p-4 bg-slate-950 rounded-xl border border-slate-800/90 space-y-3 flex flex-col justify-between hover:border-amber-500/60 transition duration-150 shadow-lg"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-300">{acc.firm_name}</span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-mono font-bold text-slate-300">
                        ${acc.account_size_usd.toLocaleString()}
                      </span>
                    </div>

                    <h4 className="text-sm font-extrabold text-white">{acc.program_name}</h4>

                    <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-1">
                      <div>
                        <span className="text-[10px] text-slate-500 block">Precio Evaluación:</span>
                        <span className="font-bold text-emerald-400">${acc.exam_price_promo_usd || acc.exam_price_regular_usd}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-500 block">Activación:</span>
                        <span className={`font-bold ${hasActivationFee ? "text-amber-400" : "text-emerald-400"}`}>
                          {hasActivationFee ? `$${acc.activation_fee_usd}` : "$0 GRATIS"}
                        </span>
                      </div>
                    </div>

                    <div className="text-[11px] text-slate-400 space-y-1 pt-1 border-t border-slate-900">
                      <div className="flex items-center justify-between">
                        <span>Target:</span>
                        <span className="text-slate-200 font-bold font-mono">${acc.profit_target_usd?.toLocaleString()}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>Límite (DD):</span>
                        <span className="text-slate-200 font-bold font-mono">${acc.max_drawdown_usd?.toLocaleString()} ({acc.drawdown_type})</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 pt-2 border-t border-slate-900">
                    {acc.active_coupon_code && (
                      <button
                        onClick={() => handleCopyCoupon(acc.active_coupon_code || "")}
                        className="w-full py-1.5 px-2.5 rounded-lg bg-amber-950/60 hover:bg-amber-900/60 border border-amber-800/60 text-amber-300 text-[11px] font-mono font-bold flex items-center justify-center gap-1.5 transition"
                      >
                        {copiedCoupon === acc.active_coupon_code ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span>¡Cupón {acc.active_coupon_code} Copiado!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Cupón: {acc.active_coupon_code} (-{acc.discount_percentage}%)</span>
                          </>
                        )}
                      </button>
                    )}

                    {acc.affiliate_url && (
                      <a
                        href={acc.affiliate_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-amber-600 to-emerald-600 hover:from-amber-500 hover:to-emerald-500 text-slate-950 font-black text-xs uppercase tracking-wider flex items-center justify-center gap-1.5 transition shadow"
                      >
                        <span>Comprar con Descuento</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
