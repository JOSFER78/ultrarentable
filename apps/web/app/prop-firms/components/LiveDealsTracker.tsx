"use client";

import React, { useState } from "react";
import { LIVE_COUPONS_DATABASE } from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";
import { ShieldCheck, Percent, Flame, Sparkles, Tag, CheckCircle2 } from "lucide-react";

export function LiveDealsTracker() {
  const [filterType, setFilterType] = useState<"ALL" | "ZERO_FEE" | "HIGH_DISCOUNT">("ALL");

  const filteredDeals = LIVE_COUPONS_DATABASE.filter((deal) => {
    if (filterType === "ZERO_FEE") return deal.waivesActivationFee;
    if (filterType === "HIGH_DISCOUNT") return deal.discountPercent >= 50;
    return true;
  });

  return (
    <div className="w-full space-y-6">
      {/* Cabecera & Filtros */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
              <span>Rastreador de Ofertas & Cupones Flash en Vivo</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-mono font-black border border-emerald-500/30">
                ACTIVO
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Códigos de descuento verificados con 1-Click Copy, enlaces directos de compra y cálculo de Coste Total de Adquisición (TCO).
            </p>
          </div>
        </div>

        {/* Botones de Filtro */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setFilterType("ALL")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
              filterType === "ALL"
                ? "bg-amber-500 text-slate-950 font-black shadow-md shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            Todos ({LIVE_COUPONS_DATABASE.length})
          </button>
          <button
            onClick={() => setFilterType("ZERO_FEE")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
              filterType === "ZERO_FEE"
                ? "bg-sky-500 text-slate-950 font-black shadow-md shadow-sky-500/20"
                : "bg-slate-900 text-sky-400 hover:text-sky-300 border border-sky-900/40"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>$0 Activación</span>
          </button>
          <button
            onClick={() => setFilterType("HIGH_DISCOUNT")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
              filterType === "HIGH_DISCOUNT"
                ? "bg-emerald-500 text-slate-950 font-black shadow-md shadow-emerald-500/20"
                : "bg-slate-900 text-emerald-400 hover:text-emerald-300 border border-emerald-900/40"
            }`}
          >
            <Percent className="w-3.5 h-3.5" />
            <span>≥50% OFF</span>
          </button>
        </div>
      </div>

      {/* Grid de Ofertas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDeals.map((deal) => (
          <div
            key={deal.id}
            className="bg-[#090d16]/90 border border-white/[0.08] hover:border-amber-500/30 backdrop-blur-xl rounded-2xl p-5 shadow-lg hover:shadow-xl hover:shadow-amber-500/5 transition-all flex flex-col justify-between relative overflow-hidden group"
          >
            {/* Top Ribbon */}
            <div className="absolute top-0 right-0 bg-gradient-to-l from-amber-500 to-amber-600 text-slate-950 font-black font-mono text-[11px] px-3 py-1 rounded-bl-xl shadow-md">
              {deal.discountPercent}% OFF
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-black text-amber-400 uppercase tracking-wide">
                    {deal.firmName}
                  </span>
                </div>
                <h3 className="text-sm font-bold text-white mt-1 pr-16 leading-snug">
                  {deal.highlightText}
                </h3>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {deal.waivesActivationFee && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10px] font-mono font-bold">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>$0 Pass Fee</span>
                  </span>
                )}
                <span className="px-2 py-0.5 rounded-md bg-slate-950/80 text-slate-300 border border-slate-800 text-[10px] font-mono">
                  {deal.recurrence === "LIFETIME_RECURRING"
                    ? "Recurrente de por vida"
                    : deal.recurrence === "ONE_TIME"
                    ? "Pago Único"
                    : "1ª Cuota"}
                </span>
                <span className="px-2 py-0.5 rounded-md bg-slate-950/80 text-slate-400 border border-slate-800 text-[10px] font-mono">
                  {deal.applicableTiers}
                </span>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80">
              <BuyButtonWithCoupon
                affiliateUrl={deal.affiliateUrl}
                couponCode={deal.code}
                discountPercent={deal.discountPercent}
                variant="primary"
                buttonText={`🔥 Comprar con ${deal.code} ↗`}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
