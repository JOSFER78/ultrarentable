"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Layers,
  Bot,
  ShieldAlert,
  FileText,
  SlidersHorizontal,
  ShieldCheck,
  Zap,
} from "lucide-react";

const DESK_TABS = [
  { href: "/trading-desk", label: "Terminal & DOM", icon: Activity, badge: "LIVE" },
  { href: "/trading-desk/posiciones", label: "Posiciones & Brackets", icon: Layers },
  { href: "/trading-desk/estrategias", label: "Estrategias Activas", icon: Bot },
  { href: "/trading-desk/riesgo", label: "Sentinel de Riesgo", icon: ShieldAlert },
  { href: "/trading-desk/auditoria", label: "Auditoría Forense", icon: FileText, badge: "WAL" },
  { href: "/trading-desk/configuracion", label: "Conexión Gateway", icon: SlidersHorizontal },
];

export default function TradingDeskLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname() || "/trading-desk";

  return (
    <div className="w-full flex flex-col gap-4 font-sans">
      {/* TRADING DESK SUB-NAVIGATION TABS & TOP STATUS BAR */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 p-2 rounded-2xl border border-white/[0.08] bg-[#090d16]/90 backdrop-blur-xl shadow-xl">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 lg:pb-0 scrollbar-none font-mono">
          {DESK_TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = pathname === tab.href;

            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-150 ${
                  isActive
                    ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.15)] font-bold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-500"}`} />
                <span className="font-sans font-medium">{tab.label}</span>
                {tab.badge && (
                  <span
                    className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-md ${
                      isActive
                        ? "bg-emerald-500/30 text-emerald-200 border border-emerald-500/40"
                        : "bg-slate-800 text-slate-400 border border-white/[0.06]"
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </div>

        {/* Cryptographic & Architecture Badges */}
        <div className="flex items-center gap-2 font-mono text-[11px] self-end lg:self-auto px-2">
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#050811] border border-white/[0.06] text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Merkle WAL: <strong className="text-slate-300">0x7f9a..3c21</strong></span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            <span>CME GLOBEX V3.4</span>
          </div>
        </div>
      </div>

      <div className="w-full">{children}</div>
    </div>
  );
}
