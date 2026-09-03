"use client";

import React from "react";
import { ShieldCheck, Activity } from "lucide-react";

export default function TradingDeskLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="w-full flex flex-col gap-4 font-sans">
      {/* Top Status Bar: Minimal & Informative */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-2.5 rounded-xl border border-white/[0.08] bg-[var(--surface-1)]">
        <div className="flex items-center gap-2 font-mono text-xs text-[var(--text-1)]">
          <span className="p-1 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
            <Activity className="w-3.5 h-3.5" />
          </span>
          <span className="font-bold">Mesa de Operación & Ejecución CME</span>
          <span className="text-[11px] text-[var(--text-3)] hidden sm:inline">
            (Navegación completa en el menú lateral)
          </span>
        </div>

        {/* Cryptographic & Architecture Badges */}
        <div className="flex items-center gap-2 font-mono text-[11px]">
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--bg)] border border-white/[0.06] text-[var(--text-2)]">
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>Merkle WAL: <strong className="text-[var(--text-1)]">0x7f9a..3c21</strong></span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)] animate-ping" />
            <span>CME GLOBEX V3.4</span>
          </div>
        </div>
      </div>

      <div className="w-full">{children}</div>
    </div>
  );
}
