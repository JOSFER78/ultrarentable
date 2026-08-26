"use client";

import React, { useState, useMemo } from "react";
import { Search, ExternalLink, Copy, Check, Filter } from "lucide-react";
import { PropFirmAccount } from "@/lib/prop-firms";

interface SemaphoreTableProps {
  accounts: PropFirmAccount[];
}

export default function SemaphoreTable({ accounts }: SemaphoreTableProps) {
  const [search, setSearch] = useState("");
  const [filterFirm, setFilterFirm] = useState("ALL");
  const [filterSize, setFilterSize] = useState("ALL");
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const [sortField, setSortField] = useState<string>("exam_price_promo_usd");
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
      const matchSearch =
        search === "" ||
        a.firm_name.toLowerCase().includes(search.toLowerCase()) ||
        a.program_name.toLowerCase().includes(search.toLowerCase());
      const matchFirm = filterFirm === "ALL" || a.firm_name === filterFirm;
      const matchSize = filterSize === "ALL" || `$${a.account_size_usd.toLocaleString()}` === filterSize;
      return matchSearch && matchFirm && matchSize;
    });
  }, [accounts, search, filterFirm, filterSize]);

  const sorted = useMemo(() => {
    return [...filtered].sort((a: any, b: any) => {
      let valA = a[sortField];
      let valB = b[sortField];
      if (sortField === "exam_price_promo_usd") {
        valA = a.exam_price_promo_usd || a.exam_price_regular_usd || 0;
        valB = b.exam_price_promo_usd || b.exam_price_regular_usd || 0;
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

  return (
    <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-4 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-3">
        <div>
          <h2 className="text-sm font-black uppercase tracking-wider text-slate-200 font-mono">
            Tabla Comparativa 70 Cuentas CME con Semáforo de Riesgo
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            🟢 Verde = Condiciones favorables | 🟡 Amarillo = Moderado | 🔴 Rojo = Alta fricción o coste oculto
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-amber-400 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 self-start sm:self-auto">
          {sorted.length} Cuentas Visibles
        </span>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Buscar firma o cuenta..."
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
              {f === "ALL" ? "Todas las Firmas (17)" : f}
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
              {s === "ALL" ? "Todos los Tamaños" : s}
            </option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-[640px] rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse font-mono text-xs">
          <thead className="bg-slate-950 sticky top-0 z-10 border-b border-slate-800 text-slate-400 text-[11px] select-none">
            <tr>
              <th className="py-2.5 px-3">Firma</th>
              <th className="py-2.5 px-3">Tamaño</th>
              <th onClick={() => toggleSort("exam_price_promo_usd")} className="py-2.5 px-3 cursor-pointer hover:text-white">
                Precio Eval. ↕
              </th>
              <th className="py-2.5 px-3">Activación</th>
              <th className="py-2.5 px-3">Target</th>
              <th className="py-2.5 px-3">Max DD (Tipo)</th>
              <th className="py-2.5 px-3 text-center">Bots</th>
              <th className="py-2.5 px-3 text-center">Cupón</th>
              <th className="py-2.5 px-3 text-center">Enlace</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 bg-slate-950/60">
            {sorted.map((acc) => {
              const price = acc.exam_price_promo_usd || acc.exam_price_regular_usd || 0;
              const actFee = acc.activation_fee_usd || 0;
              const isEod = acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "STATIC";

              const priceColor = price <= 50 ? "text-emerald-400" : price <= 100 ? "text-amber-400" : "text-rose-400";
              const actColor = actFee === 0 ? "text-emerald-400" : actFee <= 100 ? "text-amber-400" : "text-rose-400";
              const ddColor = isEod ? "text-emerald-400" : "text-rose-400";

              return (
                <tr key={acc.id} className="hover:bg-slate-800/40 transition">
                  <td className="py-2 px-3 font-bold text-slate-200">{acc.firm_name}</td>
                  <td className="py-2 px-3 text-amber-300 font-bold">${acc.account_size_usd.toLocaleString()}</td>
                  <td className={`py-2 px-3 font-bold ${priceColor}`}>${price}</td>
                  <td className={`py-2 px-3 font-bold ${actColor}`}>
                    {actFee === 0 ? "$0 (Gratis)" : `$${actFee}`}
                  </td>
                  <td className="py-2 px-3 text-slate-300">${acc.profit_target_usd?.toLocaleString()}</td>
                  <td className={`py-2 px-3 font-bold ${ddColor}`}>
                    ${acc.max_drawdown_usd?.toLocaleString()} ({acc.drawdown_type})
                  </td>
                  <td className="py-2 px-3 text-center">
                    {acc.bot_policy !== "PROHIBITED" ? (
                      <span className="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 text-[10px]">SÍ</span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded bg-rose-950 text-rose-300 text-[10px]">NO</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-center">
                    {acc.active_coupon_code ? (
                      <button
                        onClick={() => handleCopy(acc.active_coupon_code || "")}
                        className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 text-[10px] font-bold transition"
                        title="Copiar cupón"
                      >
                        {copiedCode === acc.active_coupon_code ? "✓ Copiado" : acc.active_coupon_code}
                      </button>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>
                  <td className="py-2 px-3 text-center">
                    {acc.affiliate_url && (
                      <a
                        href={acc.affiliate_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-amber-600 hover:bg-amber-500 text-slate-950 text-[10px] font-bold transition"
                      >
                        <span>Comprar</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
