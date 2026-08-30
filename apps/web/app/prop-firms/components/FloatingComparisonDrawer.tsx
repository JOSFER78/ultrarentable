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
    <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-4xl bg-[#090d16]/95 border border-amber-500/50 rounded-2xl p-3 px-5 shadow-2xl shadow-black/60 backdrop-blur-xl flex flex-col sm:flex-row items-center justify-between gap-3 transition-all animate-in fade-in slide-in-from-bottom-5 duration-300">
      {/* Slots Summary */}
      <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
        <div className="flex items-center gap-1.5 mr-2 text-xs font-mono font-black text-amber-400 shrink-0">
          <Scale className="w-4 h-4 text-amber-400" />
          <span>Comparar ({selectedAccounts.length}/4):</span>
        </div>

        {selectedAccounts.map((acc) => (
          <div
            key={acc.id}
            className="flex items-center gap-2 bg-[#030712] px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono shrink-0 shadow-sm"
          >
            <span className="font-black text-white">{acc.firm_name}</span>
            <span className="text-amber-400 font-bold">${(acc.account_size_usd / 1000).toFixed(0)}K</span>
            <span className="text-[11px] text-emerald-400 font-black">${acc.total_pass_cost_usd.toFixed(2)}</span>
            <button
              onClick={() => onRemoveSlot(acc.id)}
              className="text-slate-500 hover:text-rose-400 ml-1 p-0.5 rounded transition"
              title="Quitar"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
        <button
          onClick={onClearAll}
          className="p-2 rounded-xl text-xs font-mono text-slate-400 hover:text-rose-300 hover:bg-slate-800/80 transition"
          title="Limpiar todas las ranuras"
        >
          <Trash2 className="w-4 h-4" />
        </button>

        <button
          onClick={onOpenComparator}
          className="px-4 py-2 rounded-xl text-xs font-mono font-black bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-lg shadow-amber-500/20 transition flex items-center gap-2"
        >
          <span>Ver Cara a Cara</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
