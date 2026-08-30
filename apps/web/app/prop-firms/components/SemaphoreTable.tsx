"use client";

import React, { useState, useMemo } from "react";
import {
  Search,
  ExternalLink,
  Copy,
  Check,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Bot,
  DollarSign,
  ShieldCheck,
  Scale,
  Sparkles,
  Zap,
} from "lucide-react";
import {
  PropFirmAccount,
  calculateBotSuitabilityScore,
  getBotSuitabilityTier,
} from "@/lib/prop-firms";

interface SemaphoreTableProps {
  accounts: PropFirmAccount[];
  selectedComparisonIds?: string[];
  onToggleComparisonAccount?: (account: PropFirmAccount) => void;
  onGoToComparator?: () => void;
}

export default function SemaphoreTable({
  accounts,
  selectedComparisonIds = [],
  onToggleComparisonAccount,
  onGoToComparator,
}: SemaphoreTableProps) {
  const [search, setSearch] = useState("");
  const [filterFirm, setFilterFirm] = useState("ALL");
  const [filterSize, setFilterSize] = useState("ALL");

  // Quick Chip Filters
  const [chipOnlyZeroActivation, setChipOnlyZeroActivation] = useState(false);
  const [chipOnlyBotsAllowed, setChipOnlyBotsAllowed] = useState(false);
  const [chipOnlySafeDrawdown, setChipOnlySafeDrawdown] = useState(false);
  const [chipOnlyNoDllHard, setChipOnlyNoDllHard] = useState(false);
  const [chipOnlyFastPayout, setChipOnlyFastPayout] = useState(false);

  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Sorting state (default: Total Pass Cost ascending)
  const [sortField, setSortField] = useState<string>("total_pass_cost_usd");
  const [sortAsc, setSortAsc] = useState<boolean>(true);

  const firms = useMemo(() => {
    const set = new Set(accounts.map((a) => a.firm_name));
    return ["ALL", ...Array.from(set)];
  }, [accounts]);

  const sizes = useMemo(() => {
    const set = new Set(accounts.map((a) => `$${a.account_size_usd.toLocaleString()}`));
    return ["ALL", ...Array.from(set)];
  }, [accounts]);

  const handleCopy = (code: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(code);
      setCopiedCode(code);
      setTimeout(() => setCopiedCode(null), 2000);
    }
  };

  const filtered = useMemo(() => {
    return accounts.filter((a) => {
      // Text Search
      const matchSearch =
        search === "" ||
        a.firm_name.toLowerCase().includes(search.toLowerCase()) ||
        a.program_name.toLowerCase().includes(search.toLowerCase()) ||
        a.platforms_supported.some((p) => p.toLowerCase().includes(search.toLowerCase())) ||
        a.drawdown_type.toLowerCase().includes(search.toLowerCase());

      // Dropdown filters
      const matchFirm = filterFirm === "ALL" || a.firm_name === filterFirm;
      const matchSize = filterSize === "ALL" || `$${a.account_size_usd.toLocaleString()}` === filterSize;

      // Chip filters
      if (chipOnlyZeroActivation && a.activation_fee_usd !== 0) return false;
      if (chipOnlyBotsAllowed && a.bot_policy !== "ALLOWED_100") return false;
      if (
        chipOnlySafeDrawdown &&
        a.drawdown_type !== "STATIC" &&
        a.drawdown_type !== "EOD_TRAILING" &&
        a.drawdown_type !== "LOCKED_INITIAL"
      ) {
        return false;
      }
      if (chipOnlyNoDllHard && a.daily_loss_limit_type === "HARD_BREACH") return false;
      if (
        chipOnlyFastPayout &&
        a.payout_frequency !== "DAY_1_ON_DEMAND" &&
        a.payout_frequency !== "SAME_DAY_BUSINESS" &&
        a.payout_frequency !== "EVERY_3_DAYS"
      ) {
        return false;
      }

      return matchSearch && matchFirm && matchSize;
    });
  }, [
    accounts,
    search,
    filterFirm,
    filterSize,
    chipOnlyZeroActivation,
    chipOnlyBotsAllowed,
    chipOnlySafeDrawdown,
    chipOnlyNoDllHard,
    chipOnlyFastPayout,
  ]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a: any, b: any) => {
      let valA: any;
      let valB: any;

      if (sortField === "bot_score") {
        valA = calculateBotSuitabilityScore(a);
        valB = calculateBotSuitabilityScore(b);
      } else if (sortField === "total_pass_cost_usd") {
        valA = a.total_pass_cost_usd ?? (a.exam_price_promo_usd + a.activation_fee_usd);
        valB = b.total_pass_cost_usd ?? (b.exam_price_promo_usd + b.activation_fee_usd);
      } else if (sortField === "exam_price_promo_usd") {
        valA = a.exam_price_promo_usd || a.exam_price_regular_usd || 0;
        valB = b.exam_price_promo_usd || b.exam_price_regular_usd || 0;
      } else {
        valA = a[sortField];
        valB = b[sortField];
      }

      if (typeof valA === "string") {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortAsc ? Number(valA) - Number(valB) : Number(valB) - Number(valA);
    });
  }, [filtered, sortField, sortAsc]);

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const renderSortIndicator = (field: string) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 inline-block ml-1 text-slate-600" />;
    }
    return sortAsc ? (
      <ArrowUp className="w-3 h-3 inline-block ml-1 text-amber-400 font-bold" />
    ) : (
      <ArrowDown className="w-3 h-3 inline-block ml-1 text-amber-400 font-bold" />
    );
  };

  return (
    <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-4 md:p-6 space-y-5 shadow-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-black uppercase tracking-wider text-slate-100 font-mono">
              Tabla Comparativa Multidimensional CME (70 Cuentas)
            </h2>
            <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
              Zero-Mocks Certificado
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Ordena por <strong className="text-emerald-400">Coste Total de Pase (Evaluación + Activación)</strong>, idoneidad de bots, drawdown y límites diarios.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {onGoToComparator && selectedComparisonIds.length >= 2 && (
            <button
              onClick={onGoToComparator}
              className="px-3 py-1 rounded-xl text-xs font-bold font-mono bg-indigo-950 text-indigo-300 border border-indigo-700 hover:bg-indigo-900 transition flex items-center gap-1.5"
            >
              <Scale className="w-3.5 h-3.5" />
              <span>Ver Comparador ({selectedComparisonIds.length}/4) ↗</span>
            </button>
          )}
          <span className="text-xs font-mono font-bold text-amber-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
            {sorted.length} Cuentas Visibles
          </span>
        </div>
      </div>

      {/* Quick Chip Filters */}
      <div className="flex flex-wrap items-center gap-1.5 pt-1">
        <span className="text-xs text-slate-400 font-mono font-bold flex items-center gap-1 mr-1">
          <Filter className="w-3.5 h-3.5 text-amber-400" /> Filtros Rápidos:
        </span>

        <button
          onClick={() => setChipOnlyZeroActivation(!chipOnlyZeroActivation)}
          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition border flex items-center gap-1 ${
            chipOnlyZeroActivation
              ? "bg-emerald-950 text-emerald-300 border-emerald-500 shadow-sm"
              : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
          }`}
        >
          <DollarSign className="w-3 h-3" />
          <span>$0 Activación</span>
        </button>

        <button
          onClick={() => setChipOnlyBotsAllowed(!chipOnlyBotsAllowed)}
          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition border flex items-center gap-1 ${
            chipOnlyBotsAllowed
              ? "bg-indigo-950 text-indigo-300 border-indigo-500 shadow-sm"
              : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
          }`}
        >
          <Bot className="w-3 h-3" />
          <span>100% Bot Friendly</span>
        </button>

        <button
          onClick={() => setChipOnlySafeDrawdown(!chipOnlySafeDrawdown)}
          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition border flex items-center gap-1 ${
            chipOnlySafeDrawdown
              ? "bg-cyan-950 text-cyan-300 border-cyan-500 shadow-sm"
              : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
          }`}
        >
          <ShieldCheck className="w-3 h-3" />
          <span>EOD / Estático</span>
        </button>

        <button
          onClick={() => setChipOnlyFastPayout(!chipOnlyFastPayout)}
          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition border flex items-center gap-1 ${
            chipOnlyFastPayout
              ? "bg-amber-950 text-amber-300 border-amber-500 shadow-sm"
              : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
          }`}
        >
          <Zap className="w-3 h-3" />
          <span>Retiros Día 1 / 24h</span>
        </button>

        <button
          onClick={() => setChipOnlyNoDllHard(!chipOnlyNoDllHard)}
          className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition border flex items-center gap-1 ${
            chipOnlyNoDllHard
              ? "bg-purple-950 text-purple-300 border-purple-500 shadow-sm"
              : "bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200"
          }`}
        >
          <span>Sin DLL Hard Breach</span>
        </button>
      </div>

      {/* Search & Dropdown Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Buscar firma, plan, plataforma..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:border-amber-500 focus:outline-none font-mono"
          />
        </div>

        <select
          value={filterFirm}
          onChange={(e) => setFilterFirm(e.target.value)}
          className="py-1.5 px-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none font-mono"
        >
          {firms.map((f) => (
            <option key={f} value={f}>
              {f === "ALL" ? "Todas las Firmas (17 CME)" : f}
            </option>
          ))}
        </select>

        <select
          value={filterSize}
          onChange={(e) => setFilterSize(e.target.value)}
          className="py-1.5 px-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-200 focus:border-amber-500 focus:outline-none font-mono"
        >
          {sizes.map((s) => (
            <option key={s} value={s}>
              {s === "ALL" ? "Todos los Tamaños ($9K a $300K)" : s}
            </option>
          ))}
        </select>
      </div>

      {/* Main Table */}
      <div className="overflow-x-auto max-h-[640px] rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse font-sans text-xs min-w-[1050px]">
          <thead className="bg-slate-950 sticky top-0 z-10 border-b border-slate-800 text-slate-400 text-[11px] font-mono select-none">
            <tr>
              <th onClick={() => toggleSort("firm_name")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Firma & Plan {renderSortIndicator("firm_name")}
              </th>
              <th onClick={() => toggleSort("account_size_usd")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Tamaño {renderSortIndicator("account_size_usd")}
              </th>
              <th
                onClick={() => toggleSort("total_pass_cost_usd")}
                className="py-2.5 px-3 cursor-pointer text-emerald-400 font-black hover:text-emerald-300 bg-emerald-950/20"
                title="Coste total de examen + cuota obligatoria de activación"
              >
                Coste Total Pase (TCO) {renderSortIndicator("total_pass_cost_usd")}
              </th>
              <th onClick={() => toggleSort("exam_price_promo_usd")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Precio Eval. {renderSortIndicator("exam_price_promo_usd")}
              </th>
              <th onClick={() => toggleSort("activation_fee_usd")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Activación {renderSortIndicator("activation_fee_usd")}
              </th>
              <th onClick={() => toggleSort("max_drawdown_usd")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Max DD (Tipo) {renderSortIndicator("max_drawdown_usd")}
              </th>
              <th onClick={() => toggleSort("bot_score")} className="py-2.5 px-3 cursor-pointer hover:text-white text-center">
                Score Bots {renderSortIndicator("bot_score")}
              </th>
              <th onClick={() => toggleSort("profit_target_usd")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Target {renderSortIndicator("profit_target_usd")}
              </th>
              <th className="py-2.5 px-3">DLL Diario</th>
              <th className="py-2.5 px-3">Consistencia</th>
              <th className="py-2.5 px-3 text-center">Cupón</th>
              <th className="py-2.5 px-3 text-center">Acción</th>
              {onToggleComparisonAccount && (
                <th className="py-2.5 px-3 text-center">Comparar</th>
              )}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-800/60 bg-slate-950/60 font-mono text-xs">
            {sorted.map((acc) => {
              const price = acc.exam_price_promo_usd || acc.exam_price_regular_usd || 0;
              const actFee = acc.activation_fee_usd || 0;
              const totalCost = acc.total_pass_cost_usd ?? (price + actFee);
              const botScore = calculateBotSuitabilityScore(acc);
              const botTier = getBotSuitabilityTier(botScore);
              const isEodOrStatic =
                acc.drawdown_type === "STATIC" ||
                acc.drawdown_type === "EOD_TRAILING" ||
                acc.drawdown_type === "LOCKED_INITIAL";

              const isCompared = selectedComparisonIds.includes(acc.id);

              return (
                <tr key={acc.id} className="hover:bg-slate-800/40 transition">
                  {/* Firm & Program */}
                  <td className="py-2 px-3">
                    <div className="font-bold text-white text-xs">{acc.firm_name}</div>
                    <div className="text-[10px] text-indigo-300 truncate max-w-[140px]">
                      {acc.program_name}
                    </div>
                  </td>

                  {/* Size */}
                  <td className="py-2 px-3 font-bold text-amber-300">
                    ${(acc.account_size_usd / 1000).toFixed(0)}K
                  </td>

                  {/* Total Pass Cost (TCO) */}
                  <td className="py-2 px-3 bg-emerald-950/10 font-bold">
                    <div className="text-emerald-400 font-black text-sm">
                      ${totalCost.toFixed(2)}
                    </div>
                    <div className="text-[9px] text-slate-400">
                      (${price.toFixed(2)} + ${actFee})
                    </div>
                  </td>

                  {/* Promo Price */}
                  <td className="py-2 px-3 text-slate-200">
                    ${price.toFixed(2)}
                  </td>

                  {/* Activation Fee */}
                  <td className="py-2 px-3">
                    {actFee === 0 ? (
                      <span className="text-emerald-400 font-bold text-[11px] bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-900">
                        $0 (Gratis)
                      </span>
                    ) : (
                      <span className="text-rose-400 font-bold text-[11px]">
                        ${actFee}
                      </span>
                    )}
                  </td>

                  {/* Max Drawdown */}
                  <td className="py-2 px-3">
                    <div className={`font-bold ${isEodOrStatic ? "text-cyan-300" : "text-rose-400"}`}>
                      ${acc.max_drawdown_usd.toLocaleString()}
                    </div>
                    <div className="text-[9.5px] text-slate-400">
                      {acc.drawdown_type === "STATIC" ? "Estático" : acc.drawdown_type === "EOD_TRAILING" ? "EOD Cierre" : "Intraday"}
                    </div>
                  </td>

                  {/* Bot Score */}
                  <td className="py-2 px-3 text-center">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${botTier.badgeClass}`}>
                      {botScore}/100
                    </span>
                  </td>

                  {/* Target */}
                  <td className="py-2 px-3 text-slate-300">
                    ${acc.profit_target_usd?.toLocaleString()}
                  </td>

                  {/* Daily Loss Limit */}
                  <td className="py-2 px-3 text-[11px]">
                    {acc.daily_loss_limit_type === "NONE" ? (
                      <span className="text-emerald-400">Sin límite</span>
                    ) : acc.daily_loss_limit_type === "SOFT_BREACH" ? (
                      <span className="text-amber-400 font-bold">${acc.daily_loss_limit_usd} (Soft)</span>
                    ) : (
                      <span className="text-rose-400 font-bold">${acc.daily_loss_limit_usd} (Hard)</span>
                    )}
                  </td>

                  {/* Consistency */}
                  <td className="py-2 px-3 text-[11px] text-slate-300">
                    {acc.consistency_rule_pct === 0 ? "Libre" : `${acc.consistency_rule_pct}%`}
                  </td>

                  {/* Coupon */}
                  <td className="py-2 px-3 text-center">
                    {acc.active_coupon_code ? (
                      <button
                        onClick={() => handleCopy(acc.active_coupon_code || "")}
                        className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 text-[10px] font-bold transition flex items-center gap-1 mx-auto"
                        title="Copiar cupón"
                      >
                        <span>{copiedCode === acc.active_coupon_code ? "✓ Copiado" : acc.active_coupon_code}</span>
                      </button>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>

                  {/* Direct Buy Link */}
                  <td className="py-2 px-3 text-center">
                    {acc.affiliate_url && (
                      <a
                        href={acc.affiliate_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 text-[10px] font-bold transition"
                      >
                        <span>Comprar</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </td>

                  {/* Add to Comparison */}
                  {onToggleComparisonAccount && (
                    <td className="py-2 px-3 text-center">
                      <button
                        onClick={() => onToggleComparisonAccount(acc)}
                        className={`px-2 py-1 rounded text-[10px] font-mono font-bold transition border ${
                          isCompared
                            ? "bg-indigo-950 text-indigo-300 border-indigo-500"
                            : "bg-slate-950 text-slate-400 border-slate-800 hover:text-white hover:border-slate-700"
                        }`}
                        title={isCompared ? "Quitar de comparación" : "Añadir a comparación"}
                      >
                        {isCompared ? "✓ Ranura" : "+ Comp"}
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
