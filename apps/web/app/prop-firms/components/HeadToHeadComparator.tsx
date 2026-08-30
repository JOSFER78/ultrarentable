"use client";

import React, { useState, useMemo } from "react";
import {
  X,
  Plus,
  Sparkles,
  Scale,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Bot,
  DollarSign,
  Activity,
  Zap,
  ExternalLink,
  Copy,
  Check,
  Info,
} from "lucide-react";
import {
  PropFirmAccount,
  ALL_PROP_FIRM_ACCOUNTS,
  calculateBotSuitabilityScore,
  getBotSuitabilityTier,
  evaluateDrawdownRisk,
} from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";

interface HeadToHeadComparatorProps {
  allAccounts?: PropFirmAccount[];
  selectedIds?: string[];
  onSelectIdsChange?: (ids: string[]) => void;
}

export default function HeadToHeadComparator({
  allAccounts = ALL_PROP_FIRM_ACCOUNTS,
  selectedIds: externalSelectedIds,
  onSelectIdsChange,
}: HeadToHeadComparatorProps) {
  const [internalSelectedIds, setInternalSelectedIds] = useState<string[]>([
    "mffu-rapid-50k",
    "tradeify-growth-50k",
    "tradeday-fp-50k",
    "blusky-static-50k",
  ]);

  const selectedIds = externalSelectedIds || internalSelectedIds;

  const setSelectedIds = (newIds: string[]) => {
    if (onSelectIdsChange) {
      onSelectIdsChange(newIds);
    } else {
      setInternalSelectedIds(newIds);
    }
  };

  const [onlyDifferences, setOnlyDifferences] = useState<boolean>(false);
  const [selectorSlotIndex, setSelectorSlotIndex] = useState<number | null>(null);

  const selectedAccounts = useMemo(() => {
    return selectedIds
      .map((id) => allAccounts.find((a) => a.id === id))
      .filter((a): a is PropFirmAccount => Boolean(a));
  }, [selectedIds, allAccounts]);

  const handleRemoveAccount = (id: string) => {
    if (selectedIds.length > 2) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    }
  };

  const handleReplaceAccount = (slotIndex: number, newId: string) => {
    const updated = [...selectedIds];
    updated[slotIndex] = newId;
    setSelectedIds(updated);
    setSelectorSlotIndex(null);
  };

  const handleAddSlot = () => {
    if (selectedIds.length < 4) {
      const unselected = allAccounts.find((a) => !selectedIds.includes(a.id));
      if (unselected) {
        setSelectedIds([...selectedIds, unselected.id]);
      }
    }
  };

  const comparisonSections = [
    {
      id: "COSTS",
      title: "1. Costes Reales & Transparencia (TCO)",
      icon: <DollarSign className="w-4 h-4 text-emerald-400" />,
      rows: [
        {
          label: "Coste Total de Pase (TCO)",
          tooltip: "Inversión real total obligatoria: Examen con Promo + Cuota de Activación.",
          render: (acc: PropFirmAccount) => {
            const isZero = acc.activation_fee_usd === 0;
            return (
              <div>
                <div className="text-base font-black text-emerald-400 font-mono">
                  ${acc.total_pass_cost_usd.toFixed(2)} USD
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5 font-mono">
                  (${acc.exam_price_promo_usd.toFixed(2)} eval + ${acc.activation_fee_usd} act)
                </div>
                {isZero ? (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 mt-1">
                    ✓ $0 Activación
                  </span>
                ) : (
                  <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-800 mt-1">
                    ⚠️ Peaje +${acc.activation_fee_usd}
                  </span>
                )}
              </div>
            );
          },
          getValue: (acc: PropFirmAccount) => acc.total_pass_cost_usd,
        },
        {
          label: "Precio Examen con Cupón",
          tooltip: "Coste neto a pagar al registrar la evaluación con el cupón activo.",
          render: (acc: PropFirmAccount) => (
            <div>
              <span className="text-sm font-bold text-white font-mono">
                ${acc.exam_price_promo_usd.toFixed(2)}
              </span>
              {acc.discount_percentage > 0 && (
                <span className="text-[10px] text-amber-400 font-bold ml-1.5">
                  (-{acc.discount_percentage}%)
                </span>
              )}
              {acc.exam_price_regular_usd > acc.exam_price_promo_usd && (
                <div className="text-[10px] text-slate-500 line-through">
                  ${acc.exam_price_regular_usd.toFixed(2)}
                </div>
              )}
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.exam_price_promo_usd,
        },
        {
          label: "Cuota de Activación (Pass Fee)",
          tooltip: "Cobro obligatorio al superar la prueba antes de entregar la cuenta financiada.",
          render: (acc: PropFirmAccount) => (
            <div>
              {acc.activation_fee_usd === 0 ? (
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 font-bold text-xs border border-emerald-800">
                  $0 USD (GRATIS)
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 font-bold text-xs border border-rose-800">
                  ${acc.activation_fee_usd} USD
                </span>
              )}
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.activation_fee_usd,
        },
        {
          label: "Renovación Mensual / Reset",
          tooltip: "Coste de mantenimiento si no se aprueba en 30 días y coste de reinicio.",
          render: (acc: PropFirmAccount) => (
            <div className="text-xs text-slate-300">
              <div>
                Renovación:{" "}
                <span className="font-mono font-bold">
                  {acc.monthly_renewal_usd === 0 ? "Pago Único ($0)" : `$${acc.monthly_renewal_usd}/mes`}
                </span>
              </div>
              <div className="text-[11px] text-slate-400">
                Reset: <span className="font-mono">${acc.reset_fee_usd}</span>
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => `${acc.monthly_renewal_usd}-${acc.reset_fee_usd}`,
        },
      ],
    },
    {
      id: "BOTS",
      title: "2. Compatibilidad con Bots & Trading Algorítmico",
      icon: <Bot className="w-4 h-4 text-indigo-400" />,
      rows: [
        {
          label: "Idoneidad para Bots (Score)",
          tooltip: "Puntuación algorítmica de 0 a 100 basada en tipo de drawdown, APIs, DLL y reglas.",
          render: (acc: PropFirmAccount) => {
            const score = calculateBotSuitabilityScore(acc);
            const tier = getBotSuitabilityTier(score);
            return (
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-black font-mono text-white">{score}/100</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${tier.badgeClass}`}>
                    {tier.badgeText}
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden mt-1.5 max-w-[120px]">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${score}%`,
                      backgroundColor: tier.dotColor,
                    }}
                  />
                </div>
              </div>
            );
          },
          getValue: (acc: PropFirmAccount) => calculateBotSuitabilityScore(acc),
        },
        {
          label: "Política Oficial de Bots / EAs",
          tooltip: "Permiso de ejecución de sistemas automáticos en NinjaTrader, Tradovate y VPS.",
          render: (acc: PropFirmAccount) => (
            <div>
              {acc.bot_policy === "ALLOWED_100" && (
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-xs font-bold border border-emerald-800">
                  ✓ 100% Permitido / Automatizado
                </span>
              )}
              {acc.bot_policy === "ALLOWED_LOCAL_ONLY" && (
                <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 text-xs font-bold border border-amber-800">
                  ⚠️ Solo Ejecución Local / PC
                </span>
              )}
              {acc.bot_policy === "RESTRICTED" && (
                <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 text-xs font-bold border border-amber-800">
                  ⚠️ Con Restricciones
                </span>
              )}
              {acc.bot_policy === "PROHIBITED" && (
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 text-xs font-bold border border-rose-800">
                  ❌ Prohibido (Solo Manual)
                </span>
              )}
              <p className="text-[10.5px] text-slate-400 mt-1">{acc.bot_policy_description}</p>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.bot_policy,
        },
        {
          label: "Plataformas & Gateways",
          tooltip: "Entornos compatibles para conectar robots y scripts.",
          render: (acc: PropFirmAccount) => (
            <div className="flex flex-wrap gap-1">
              {acc.platforms_supported.map((p) => (
                <span
                  key={p}
                  className="px-1.5 py-0.5 bg-slate-900 text-slate-300 rounded text-[10px] font-mono border border-slate-800"
                >
                  {p}
                </span>
              ))}
              <div className="text-[10px] text-indigo-400 w-full mt-0.5 font-mono">
                Gateway: {acc.data_gateway}
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.platforms_supported.join(", "),
        },
      ],
    },
    {
      id: "RISK",
      title: "3. Riesgo, Drawdown & Microestructura",
      icon: <ShieldCheck className="w-4 h-4 text-cyan-400" />,
      rows: [
        {
          label: "Tipo de Drawdown & Mecánica",
          tooltip: "Cómo se calcula la pérdida máxima permitida.",
          render: (acc: PropFirmAccount) => (
            <div>
              {acc.drawdown_type === "STATIC" && (
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 text-xs font-bold border border-emerald-800">
                  🛡️ Estático Puro (Inamovible)
                </span>
              )}
              {(acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL") && (
                <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 text-xs font-bold border border-cyan-800">
                  ⚡ EOD Trailing (Al Cierre)
                </span>
              )}
              {acc.drawdown_type === "INTRADAY_TRAILING" && (
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 text-xs font-bold border border-rose-800">
                  ⚠️ Intraday Peak (Tick a Tick)
                </span>
              )}
              <div className="text-[10.5px] text-slate-400 mt-1">
                {acc.freeze_level_description}
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.drawdown_type,
        },
        {
          label: "Drawdown Máximo & Target",
          tooltip: "Límite total de pérdida versus objetivo de ganancia para aprobar.",
          render: (acc: PropFirmAccount) => (
            <div className="text-xs font-mono">
              <div className="text-rose-400 font-bold">
                Max DD: ${acc.max_drawdown_usd.toLocaleString()} ({acc.max_drawdown_pct}%)
              </div>
              <div className="text-emerald-400 font-bold">
                Target: ${acc.profit_target_usd.toLocaleString()} ({acc.profit_target_pct}%)
              </div>
              <div className="text-[10.5px] text-slate-400">
                Ratio Target/DD: {acc.target_to_drawdown_ratio.toFixed(2)}x
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => `${acc.max_drawdown_usd}-${acc.profit_target_usd}`,
        },
        {
          label: "Daily Loss Limit (Límite Diario)",
          tooltip: "Regla de pérdida intradía.",
          render: (acc: PropFirmAccount) => (
            <div>
              {acc.daily_loss_limit_type === "NONE" && (
                <span className="text-emerald-400 font-bold text-xs">✓ Sin Límite Diario (Libre)</span>
              )}
              {acc.daily_loss_limit_type === "SOFT_BREACH" && (
                <span className="text-amber-400 font-bold text-xs font-mono">
                  ${acc.daily_loss_limit_usd} (Soft Lock - No quema cuenta)
                </span>
              )}
              {acc.daily_loss_limit_type === "HARD_BREACH" && (
                <span className="text-rose-400 font-bold text-xs font-mono">
                  ${acc.daily_loss_limit_usd} (Hard Breach 💀 Quema cuenta)
                </span>
              )}
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.daily_loss_limit_type,
        },
        {
          label: "Regla de Consistencia & 10s",
          tooltip: "Máximo % de beneficio en un solo día y restricción de duración de trades.",
          render: (acc: PropFirmAccount) => (
            <div className="text-xs text-slate-300">
              <div>
                Consistencia:{" "}
                <span className="font-bold text-amber-300">
                  {acc.consistency_rule_pct === 0 ? "Sin límite" : `Máx ${acc.consistency_rule_pct}% por día`}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">
                Regla 10s:{" "}
                {acc.trade_duration_10s_rule ? (
                  <span className="text-rose-400 font-bold">Sí (Trades &gt; 10s obligatorios)</span>
                ) : (
                  <span className="text-emerald-400 font-bold">No (Scalping libre)</span>
                )}
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => `${acc.consistency_rule_pct}-${acc.trade_duration_10s_rule}`,
        },
      ],
    },
    {
      id: "PAYOUTS",
      title: "4. Retiros, Colchón & Frecuencia",
      icon: <Zap className="w-4 h-4 text-amber-400" />,
      rows: [
        {
          label: "Frecuencia de Retiros",
          tooltip: "Periodicidad con la que se pueden solicitar los beneficios.",
          render: (acc: PropFirmAccount) => (
            <div>
              <span className="text-xs font-bold text-amber-300 font-mono">
                {acc.payout_frequency_label}
              </span>
              <div className="text-[10.5px] text-slate-400 mt-0.5">
                Días mínimos fondeo: {acc.min_trading_days_payout === 0 ? "Día 1" : `${acc.min_trading_days_payout} días`}
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.payout_frequency,
        },
        {
          label: "Colchón de Seguridad (Buffer)",
          tooltip: "Beneficio que la empresa retiene en la cuenta fondeada antes de liberar pagos.",
          render: (acc: PropFirmAccount) => (
            <div className="text-xs font-mono">
              <div className="text-amber-400 font-bold">
                ${acc.safety_buffer_usd.toLocaleString()} USD
              </div>
              <div className="text-[10px] text-slate-500">
                Retirable sobre: ${(acc.account_size_usd + acc.safety_buffer_usd).toLocaleString()}
              </div>
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.safety_buffer_usd,
        },
        {
          label: "Profit Split & Reparto",
          tooltip: "Porcentaje de beneficios entregado al trader.",
          render: (acc: PropFirmAccount) => (
            <div className="text-xs font-mono font-bold text-emerald-400">
              {acc.payout_split_tier_1}
            </div>
          ),
          getValue: (acc: PropFirmAccount) => acc.payout_split_tier_1,
        },
      ],
    },
  ];

  return (
    <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-4 md:p-6 shadow-2xl space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Scale className="w-5 h-5" />
            </span>
            <h2 className="text-lg font-black text-white tracking-tight">
              Comparador Cara a Cara (Head-to-Head) — Estilo Propinex
            </h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Compara de 2 a 4 cuentas cara a cara con transparencia total en Coste Total de Pase (Evaluación + Activación), permisos de bots y letra pequeña.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setOnlyDifferences(!onlyDifferences)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition flex items-center gap-1.5 border ${
              onlyDifferences
                ? "bg-amber-500/20 text-amber-300 border-amber-500"
                : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
            }`}
          >
            <span>{onlyDifferences ? "✓ Solo Diferencias" : "Mostrar Todo"}</span>
          </button>

          {selectedIds.length < 4 && (
            <button
              onClick={handleAddSlot}
              className="px-3 py-1.5 rounded-xl text-xs font-bold font-mono bg-indigo-950 text-indigo-300 border border-indigo-700 hover:bg-indigo-900 transition flex items-center gap-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Añadir Ranura ({selectedIds.length}/4)</span>
            </button>
          )}
        </div>
      </div>

      {/* Account Selector Modal / Dropdown if active */}
      {selectorSlotIndex !== null && (
        <div className="p-4 bg-slate-950 rounded-xl border border-amber-500/40 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase font-mono text-amber-400">
              Seleccionar cuenta para la columna {selectorSlotIndex + 1}:
            </span>
            <button
              onClick={() => setSelectorSlotIndex(null)}
              className="text-xs text-slate-500 hover:text-slate-200"
            >
              ✕ Cerrar
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 max-h-60 overflow-y-auto pr-1">
            {allAccounts.map((acc) => {
              const isSelected = selectedIds.includes(acc.id);
              return (
                <button
                  key={acc.id}
                  disabled={isSelected}
                  onClick={() => handleReplaceAccount(selectorSlotIndex, acc.id)}
                  className={`p-2 rounded-lg text-left text-xs border transition ${
                    isSelected
                      ? "opacity-40 bg-slate-900 border-slate-800 cursor-not-allowed"
                      : "bg-slate-900 hover:bg-slate-800 border-slate-800 hover:border-amber-500/50"
                  }`}
                >
                  <div className="font-bold text-white truncate">{acc.firm_name}</div>
                  <div className="text-[11px] text-amber-300 font-mono">
                    ${(acc.account_size_usd / 1000).toFixed(0)}K · ${acc.total_pass_cost_usd.toFixed(2)} Total
                  </div>
                  <div className="text-[10px] text-slate-500 truncate">{acc.program_name}</div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Comparison Grid */}
      <div className="overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse font-sans text-xs min-w-[700px]">
          {/* Header row with accounts */}
          <thead>
            <tr className="bg-slate-950 border-b border-slate-800">
              <th className="p-3 text-slate-400 font-mono text-[11px] w-1/4 uppercase tracking-wider">
                Métrica / Atributo
              </th>
              {selectedAccounts.map((acc, index) => {
                return (
                  <th
                    key={acc.id}
                    className="p-3 border-l border-slate-800/80 bg-slate-950/90 relative align-top"
                    style={{ width: `${75 / selectedAccounts.length}%` }}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                          Columna #{index + 1}
                        </span>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => setSelectorSlotIndex(index)}
                            className="p-1 text-[10px] text-slate-400 hover:text-white bg-slate-900 rounded border border-slate-800 hover:border-slate-700"
                            title="Cambiar cuenta"
                          >
                            Cambiar
                          </button>
                          {selectedAccounts.length > 2 && (
                            <button
                              onClick={() => handleRemoveAccount(acc.id)}
                              className="p-1 text-slate-500 hover:text-rose-400 rounded hover:bg-slate-900"
                              title="Quitar ranura"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="text-sm font-black text-white">{acc.firm_name}</div>
                        <div className="text-[11px] text-indigo-300 font-mono">{acc.program_name}</div>
                        <div className="text-xs font-mono font-bold text-amber-400 mt-0.5">
                          ${acc.account_size_usd.toLocaleString()} USD
                        </div>
                      </div>

                      {/* Buy Button */}
                      <BuyButtonWithCoupon
                        affiliateUrl={acc.affiliate_url}
                        couponCode={acc.active_coupon_code}
                        discountPercent={acc.discount_percentage}
                        variant="compact"
                      />
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>

          {/* Body with categories */}
          <tbody className="divide-y divide-slate-800/50 bg-slate-950/40">
            {comparisonSections.map((sec) => (
              <React.Fragment key={sec.id}>
                {/* Section Header */}
                <tr className="bg-slate-900/90 font-mono font-bold text-xs border-y border-slate-800 text-slate-200">
                  <td colSpan={selectedAccounts.length + 1} className="p-2.5 px-3 flex items-center gap-2">
                    {sec.icon}
                    <span className="uppercase tracking-wider font-black text-amber-300">{sec.title}</span>
                  </td>
                </tr>

                {/* Section Rows */}
                {sec.rows.map((row) => {
                  const values = selectedAccounts.map((a) => String(row.getValue(a)));
                  const isDifferent = new Set(values).size > 1;

                  if (onlyDifferences && !isDifferent) return null;

                  return (
                    <tr
                      key={row.label}
                      className={`hover:bg-slate-900/40 transition ${
                        isDifferent ? "bg-amber-500/[0.02]" : ""
                      }`}
                    >
                      <td className="p-3 font-medium text-slate-300 align-top">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-white">{row.label}</span>
                          {isDifferent && (
                            <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800/60">
                              ≠ Dif
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-500 mt-0.5">{row.tooltip}</p>
                      </td>

                      {selectedAccounts.map((acc) => (
                        <td
                          key={acc.id}
                          className="p-3 border-l border-slate-800/60 align-top text-xs"
                        >
                          {row.render(acc)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
