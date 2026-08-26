"use client";

import React from "react";
import { Scale, X, ArrowRight, Trash2 } from "lucide-react";
import { PropFirmAccount } from "@/lib/prop-firms";

interface FloatingDrawerProps {
  selectedAccounts: PropFirmAccount[];
  onRemoveSlot: (id: string) => void;
  onClearAll: () => void;
  onOpenComparator: () => void;
}

export default function FloatingComparisonDrawer({
  selectedAccounts,
  onRemoveSlot,
  onClearAll,
  onOpenComparator,
}: FloatingDrawerProps) {
  if (selectedAccounts.length === 0) return null;

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-4xl bg-slate-900/95 border border-amber-500/40 rounded-2xl p-3 px-4 shadow-2xl backdrop-blur-md flex flex-col sm:flex-row items-center justify-between gap-3">
      {/* Slots Summary */}
      <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
        <div className="flex items-center gap-1.5 mr-2 text-xs font-mono font-bold text-amber-400">
          <Scale className="w-4 h-4 text-amber-400" />
          <span>Comparar ({selectedAccounts.length}/4):</span>
        </div>

        {selectedAccounts.map((acc) => (
          <div
            key={acc.id}
            className="flex items-center gap-1.5 bg-slate-950 px-2.5 py-1 rounded-xl border border-slate-800 text-xs font-mono shrink-0"
          >
            <span className="font-bold text-white">{acc.firm_name}</span>
            <span className="text-amber-400">${(acc.account_size_usd / 1000).toFixed(0)}K</span>
            <span className="text-[11px] text-emerald-400 font-bold">${acc.total_pass_cost_usd.toFixed(2)}</span>
            <button
              onClick={() => onRemoveSlot(acc.id)}
              className="text-slate-500 hover:text-rose-400 ml-1"
              title="Quitar"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
        <button
          onClick={onClearAll}
          className="px-2.5 py-1.5 rounded-xl text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
          title="Limpiar todas las ranuras"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={onOpenComparator}
          className="px-4 py-1.5 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20 transition flex items-center gap-1.5"
        >
          <span>Ver Cara a Cara</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
