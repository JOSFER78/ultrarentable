"use client";

import React, { useState, useMemo } from "react";
import {
  Sparkles,
  Bot,
  DollarSign,
  Activity,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  ArrowRight,
  Scale,
  ExternalLink,
  Copy,
  Check,
} from "lucide-react";
import {
  PropFirmAccount,
  calculateBotSuitabilityScore,
  getBotSuitabilityTier,
} from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";

interface SmartFinderProps {
  allAccounts: PropFirmAccount[];
  onSelectForComparison?: (account: PropFirmAccount) => void;
  onGoToComparator?: () => void;
}

export type BotStrategyType =
  | "SCALPER_EOD"
  | "STATIC_SWING"
  | "ZERO_ACTIVATION"
  | "LOW_COST"
  | "MULTI_BOT";

export default function Smart3ClickFinder({
  allAccounts,
  onSelectForComparison,
  onGoToComparator,
}: SmartFinderProps) {
  const [strategyStep, setStrategyStep] = useState<BotStrategyType>("SCALPER_EOD");
  const [budgetStep, setBudgetStep] = useState<"LOW" | "MID" | "HIGH" | "ANY">("ANY");
  const [platformStep, setPlatformStep] = useState<"TRADOVATE" | "NINJA" | "ANY">("ANY");

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
      .map((acc) => {
        const botScore = calculateBotSuitabilityScore(acc);
        let matchScore = botScore;

        // Custom weightings based on strategy
        if (strategyStep === "SCALPER_EOD") {
          if (acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL") matchScore += 15;
          if (acc.trade_duration_10s_rule) matchScore -= 20;
          if (acc.bot_policy === "ALLOWED_100") matchScore += 10;
        } else if (strategyStep === "STATIC_SWING") {
          if (acc.drawdown_type === "STATIC") matchScore += 30;
          else matchScore -= 25;
        } else if (strategyStep === "ZERO_ACTIVATION") {
          if (acc.activation_fee_usd === 0) matchScore += 25;
          else matchScore -= 30;
        } else if (strategyStep === "LOW_COST") {
          if (acc.total_pass_cost_usd <= 75) matchScore += 25;
          else if (acc.total_pass_cost_usd <= 100) matchScore += 10;
          else matchScore -= 20;
        } else if (strategyStep === "MULTI_BOT") {
          if (acc.account_size_usd >= 100000) matchScore += 20;
          if (acc.bot_policy === "ALLOWED_100") matchScore += 10;
        }

        // Budget filters
        const totalCost = acc.total_pass_cost_usd;
        if (budgetStep === "LOW" && totalCost > 75) return null;
        if (budgetStep === "MID" && (totalCost < 60 || totalCost > 140)) return null;
        if (budgetStep === "HIGH" && totalCost < 120) return null;

        // Platform filters
        if (platformStep === "TRADOVATE" && !acc.platforms_supported.some((p) => p.includes("Tradovate") || p.includes("TradingView"))) {
          return null;
        }
        if (platformStep === "NINJA" && !acc.platforms_supported.some((p) => p.includes("NinjaTrader"))) {
          return null;
        }

        // Exclude strictly prohibited bots from recommendations
        if (acc.bot_policy === "PROHIBITED") return null;

        return {
          account: acc,
          matchScore: Math.min(100, Math.max(0, matchScore)),
        };
      })
      .filter((item): item is { account: PropFirmAccount; matchScore: number } => Boolean(item))
      .sort((a, b) => b.matchScore - a.matchScore)
      .slice(0, 3);
  }, [allAccounts, strategyStep, budgetStep, platformStep]);

  return (
    <div className="bg-gradient-to-br from-slate-900 via-slate-900/90 to-indigo-950/30 rounded-2xl border border-indigo-500/30 p-5 md:p-6 shadow-2xl space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-black text-white tracking-tight">
              Asistente Rápido en 3 Clics — Selector Cuantitativo para Bots
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Encuentra la cuenta perfecta según el estilo de tu robot (EOD, Estático, Low Cost, API), tu presupuesto real y plataforma de ejecución.
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-[11px] font-bold font-mono bg-indigo-500/10 text-indigo-300 border border-indigo-500/30 self-start sm:self-auto">
          MOTOR DE APTITUD BOTS
        </span>
      </div>

      {/* 3 Steps Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Step 1: Strategy / Bot Type */}
        <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <Bot className="w-4 h-4 text-indigo-400" />
            1. Perfil / Estrategia del Bot
          </label>
          <div className="space-y-1.5">
            {[
              {
                key: "SCALPER_EOD",
                title: "Scalper Intradía (EOD)",
                desc: "Drawdown solo al cierre, sin penalizar mechas en sesión.",
              },
              {
                key: "STATIC_SWING",
                title: "Máxima Seguridad (Drawdown Estático)",
                desc: "Drawdown fijo que nunca persigue las ganancias (BluSky).",
              },
              {
                key: "ZERO_ACTIVATION",
                title: "Aprobación Directa ($0 Activación)",
                desc: "Sin cuota diferida al aprobar (MFFU Rapid, TradeDay, Tradeify).",
              },
              {
                key: "LOW_COST",
                title: "Low-Cost Total Pass (<$80 All-in)",
                desc: "Mínimo coste total real de evaluación + activación.",
              },
              {
                key: "MULTI_BOT",
                title: "Portafolios Multi-Bot ($100K+)",
                desc: "Cuentas grandes para canastas de algoritmos y apalancamiento.",
              },
            ].map((s) => (
              <button
                key={s.key}
                onClick={() => setStrategyStep(s.key as BotStrategyType)}
                className={`w-full text-left p-2 rounded-lg transition border text-xs ${
                  strategyStep === s.key
                    ? "bg-indigo-950 text-indigo-200 border-indigo-500 shadow-sm"
                    : "bg-slate-900 text-slate-400 border-slate-800/80 hover:text-slate-200"
                }`}
              >
                <div className="font-bold">{s.title}</div>
                <div className="text-[10px] text-slate-500 line-clamp-1">{s.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Total Real Budget */}
        <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <DollarSign className="w-4 h-4 text-emerald-400" />
            2. Presupuesto Total Real (Eval + Act)
          </label>
          <div className="space-y-1.5">
            {[
              { key: "LOW", title: "Económico (<$75 Total)", desc: "Entrada ultra-reducida sin peaje de fondeo." },
              { key: "MID", title: "Estándar ($75 - $140 Total)", desc: "El rango óptimo para cuentas de $50K y $100K." },
              { key: "HIGH", title: "Pro / Institucional (+$140)", desc: "Cuentas de $100K a $300K de alta capacidad." },
              { key: "ANY", title: "Cualquier Presupuesto", desc: "Ver las opciones más eficientes sin límite." },
            ].map((b) => (
              <button
                key={b.key}
                onClick={() => setBudgetStep(b.key as any)}
                className={`w-full text-left p-2.5 rounded-lg transition border text-xs ${
                  budgetStep === b.key
                    ? "bg-emerald-950 text-emerald-300 border-emerald-500 shadow-sm"
                    : "bg-slate-900 text-slate-400 border-slate-800/80 hover:text-slate-200"
                }`}
              >
                <div className="font-bold">{b.title}</div>
                <div className="text-[10px] text-slate-500">{b.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Platform & Gateway */}
        <div className="p-3.5 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
          <label className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase font-mono">
            <Activity className="w-4 h-4 text-amber-400" />
            3. Plataforma & Gateway del Bot
          </label>
          <div className="space-y-1.5">
            {[
              {
                key: "TRADOVATE",
                title: "Tradovate / TradingView (Webhooks / API)",
                desc: "Ideal para alertas directas de TradingView y APIs REST/WebSocket.",
              },
              {
                key: "NINJA",
                title: "NinjaTrader 8 (C# / Strategy Analyzer)",
                desc: "Automatización local, VPS y sistemas complejos de StrategyQuant.",
              },
              {
                key: "ANY",
                title: "Cualquier Plataforma (Tradovate / Rithmic / NT8)",
                desc: "Muestra todas las firmas compatibles con EAs.",
              },
            ].map((p) => (
              <button
                key={p.key}
                onClick={() => setPlatformStep(p.key as any)}
                className={`w-full text-left p-3 rounded-lg transition border text-xs ${
                  platformStep === p.key
                    ? "bg-amber-950 text-amber-300 border-amber-500 shadow-sm"
                    : "bg-slate-900 text-slate-400 border-slate-800/80 hover:text-slate-200"
                }`}
              >
                <div className="font-bold">{p.title}</div>
                <div className="text-[10px] text-slate-500">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between pt-2">
        <h3 className="text-sm font-bold uppercase font-mono text-slate-200 flex items-center gap-2">
          <span>🏆 Top 3 Cuentas Recomendadas para tu Configuración</span>
          <span className="text-xs text-indigo-400 font-normal">({recommendedAccounts.length} encontradas)</span>
        </h3>
        {onGoToComparator && (
          <button
            onClick={onGoToComparator}
            className="text-xs font-mono font-bold text-amber-400 hover:text-amber-300 flex items-center gap-1 transition"
          >
            <span>Ver en Comparador Completo ↗</span>
          </button>
        )}
      </div>

      {/* Top 3 Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {recommendedAccounts.map(({ account, matchScore }, index) => {
          const tier = getBotSuitabilityTier(matchScore);
          const isEodOrStatic =
            account.drawdown_type === "EOD_TRAILING" || account.drawdown_type === "STATIC";

          return (
            <div
              key={account.id}
              className="bg-slate-950 rounded-xl border border-slate-800 hover:border-indigo-500/50 p-4 space-y-3 transition flex flex-col justify-between relative shadow-lg"
            >
              {/* Badge Rank */}
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  RECOMENDACIÓN #{index + 1}
                </span>
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${tier.badgeClass}`}>
                  {matchScore}% Match
                </span>
              </div>

              {/* Title & Size */}
              <div>
                <h4 className="text-base font-black text-white">{account.firm_name}</h4>
                <div className="text-xs text-indigo-300 font-mono">{account.program_name}</div>
                <div className="text-xs font-mono font-bold text-amber-400 mt-1">
                  ${account.account_size_usd.toLocaleString()} USD
                </div>
              </div>

              {/* Price Breakdown */}
              <div className="p-2.5 bg-slate-900/90 rounded-lg border border-slate-800/80 space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">Coste Total de Pase:</span>
                  <span className="text-sm font-black text-emerald-400 font-mono">
                    ${account.total_pass_cost_usd.toFixed(2)} USD
                  </span>
                </div>
                <div className="flex justify-between items-center text-[10.5px] text-slate-500 font-mono">
                  <span>Examen con Promo:</span>
                  <span>${account.exam_price_promo_usd.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center text-[10.5px] font-mono">
                  <span className="text-slate-500">Cuota de Activación:</span>
                  <span className={account.activation_fee_usd === 0 ? "text-emerald-400 font-bold" : "text-rose-400"}>
                    {account.activation_fee_usd === 0 ? "$0 (Gratis)" : `$${account.activation_fee_usd}`}
                  </span>
                </div>
              </div>

              {/* Key Features */}
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-mono text-slate-400">Drawdown:</span>
                  <span className={`font-bold ${isEodOrStatic ? "text-cyan-300" : "text-rose-400"}`}>
                    ${account.max_drawdown_usd.toLocaleString()} ({account.drawdown_type_label || account.drawdown_type})
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-mono text-slate-400">Permiso Bots:</span>
                  <span className="text-emerald-400 font-bold">✓ {account.bot_policy}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[11px] font-mono text-slate-400">Retiros:</span>
                  <span className="text-amber-300 font-bold">{account.payout_frequency_label}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 space-y-2">
                <BuyButtonWithCoupon
                  affiliateUrl={account.affiliate_url}
                  couponCode={account.active_coupon_code}
                  discountPercent={account.discount_percentage}
                  variant="primary"
                />

                {onSelectForComparison && (
                  <button
                    onClick={() => onSelectForComparison(account)}
                    className="w-full py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 text-[11px] font-mono font-bold transition flex items-center justify-center gap-1.5"
                  >
                    <Scale className="w-3 h-3 text-amber-400" />
                    <span>Añadir a Comparador Cara a Cara</span>
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
