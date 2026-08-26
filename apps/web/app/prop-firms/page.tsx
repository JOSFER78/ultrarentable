"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Building2,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { ALL_PROP_FIRM_ACCOUNTS } from "@/lib/prop-firms";
import Smart3ClickFinder from "./components/Smart3ClickFinder";
import SemaphoreTable from "./components/SemaphoreTable";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

export default function PropFirmsMasterPage() {
  const [activeTab, setActiveTab] = useState<"FINDER" | "TABLE">("FINDER");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <EstrategiasHeaderNav />

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Building2 className="w-7 h-7 text-amber-400" />
              <h1 className="text-2xl font-bold tracking-tight">Fase 5: Catálogo Maestro 70 Prop Firms CME</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Compara 70 cuentas de futuros CME en 17 firmas de fondeo. Transparencia total en costes de activación ($0 vs $149) y cupones de descuento activos.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950 text-amber-300 border border-amber-800">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              70 Cuentas Verificadas
            </span>
          </div>
        </div>

        {/* KPI Strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block uppercase font-mono">Cuentas Analizadas</span>
            <span className="text-2xl font-black text-white font-mono">70 Cuentas</span>
            <span className="text-[11px] text-slate-500 block">17 Firmas Evaluadas</span>
          </div>

          <div className="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block uppercase font-mono">Precio Más Bajo</span>
            <span className="text-2xl font-black text-emerald-400 font-mono">$39.50</span>
            <span className="text-[11px] text-emerald-400/80 block">Con cupón activo</span>
          </div>

          <div className="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block uppercase font-mono">Coste Oculto Activación</span>
            <span className="text-2xl font-black text-amber-400 font-mono">$0 a $149</span>
            <span className="text-[11px] text-slate-400 block">Desglosado por firma</span>
          </div>

          <div className="p-3.5 bg-slate-900/80 rounded-xl border border-slate-800">
            <span className="text-xs text-slate-400 block uppercase font-mono">Permiso Robots (Algo)</span>
            <span className="text-2xl font-black text-indigo-400 font-mono">82% Aceptan</span>
            <span className="text-[11px] text-slate-400 block">Automatización 100%</span>
          </div>
        </div>

        {/* Navigation Mode Tabs */}
        <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("FINDER")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "FINDER"
                ? "bg-amber-600 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Asistente Rápido (3 Clics)
          </button>

          <button
            onClick={() => setActiveTab("TABLE")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "TABLE"
                ? "bg-amber-600 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Building2 className="w-4 h-4" />
            Tabla Comparativa Semáforo (70 Cuentas)
          </button>
        </div>

        {/* Dynamic View */}
        {activeTab === "FINDER" && <Smart3ClickFinder allAccounts={ALL_PROP_FIRM_ACCOUNTS} />}
        {activeTab === "TABLE" && <SemaphoreTable accounts={ALL_PROP_FIRM_ACCOUNTS} />}
      </div>
    </div>
  );
}
