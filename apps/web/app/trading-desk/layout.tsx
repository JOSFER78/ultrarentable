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
    <div className="w-full flex flex-col gap-4">
      {/* TRADING DESK SUB-NAVIGATION TABS */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-white/[0.07] bg-slate-950/40 p-1.5 rounded-xl">
        {DESK_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = pathname === tab.href;

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all duration-150 ${
                isActive
                  ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-[0_0_12px_rgba(16,185,129,0.15)] font-bold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-emerald-400" : "text-slate-500"}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${
                    isActive
                      ? "bg-emerald-500/30 text-emerald-200"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      <div className="w-full">{children}</div>
    </div>
  );
}
