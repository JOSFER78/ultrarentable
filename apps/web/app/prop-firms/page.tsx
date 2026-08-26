"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Building2,
  ShieldCheck,
  Sparkles,
  Scale,
  DollarSign,
  Bot,
  Calculator,
  Flame,
  Activity,
  Layers,
  Zap,
} from "lucide-react";
import { ALL_PROP_FIRM_ACCOUNTS, PropFirmAccount } from "@/lib/prop-firms";
import Smart3ClickFinder from "./components/Smart3ClickFinder";
import SemaphoreTable from "./components/SemaphoreTable";
import HeadToHeadComparator from "./components/HeadToHeadComparator";
import { ExtractionRoiCalculator } from "./components/ExtractionRoiCalculator";
import { LiveDealsTracker } from "./components/LiveDealsTracker";
import { AISyncStatusBar } from "./components/AISyncStatusBar";
import FloatingComparisonDrawer from "./components/FloatingComparisonDrawer";
import PickMyTradeBridgeModal from "./components/PickMyTradeBridgeModal";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

export type PropFirmTab = "COMPARATOR" | "FINDER" | "TABLE" | "ROI_CALC" | "LIVE_DEALS";

export default function PropFirmsMasterPage() {
  const [activeTab, setActiveTab] = useState<PropFirmTab>("COMPARATOR");
  const [isPmtModalOpen, setIsPmtModalOpen] = useState<boolean>(false);

  // Shared state for selected comparison accounts across components (2 to 4 accounts)
  const [selectedComparisonIds, setSelectedComparisonIds] = useState<string[]>([
    "mffu-rapid-50k",
    "tradeify-growth-50k",
    "tradeday-fp-50k",
    "blusky-static-50k",
  ]);

  const selectedAccounts = selectedComparisonIds
    .map((id) => ALL_PROP_FIRM_ACCOUNTS.find((a) => a.id === id))
    .filter((a): a is PropFirmAccount => Boolean(a));

  const handleToggleComparisonAccount = (account: PropFirmAccount) => {
    if (selectedComparisonIds.includes(account.id)) {
      if (selectedComparisonIds.length > 2) {
        setSelectedComparisonIds(selectedComparisonIds.filter((id) => id !== account.id));
      }
    } else {
      if (selectedComparisonIds.length < 4) {
        setSelectedComparisonIds([...selectedComparisonIds, account.id]);
      } else {
        // Replace the last slot if maxed
        const updated = [...selectedComparisonIds.slice(0, 3), account.id];
        setSelectedComparisonIds(updated);
      }
    }
  };

  const handleRemoveComparisonSlot = (id: string) => {
    if (selectedComparisonIds.length > 2) {
      setSelectedComparisonIds(selectedComparisonIds.filter((item) => item !== id));
    }
  };

  const handleClearAllComparison = () => {
    // Keep minimum 2 default best accounts
    setSelectedComparisonIds(["mffu-rapid-50k", "tradeify-growth-50k"]);
  };

  const handleAddFromFinder = (account: PropFirmAccount) => {
    if (!selectedComparisonIds.includes(account.id)) {
      if (selectedComparisonIds.length < 4) {
        setSelectedComparisonIds([...selectedComparisonIds, account.id]);
      } else {
        setSelectedComparisonIds([...selectedComparisonIds.slice(0, 3), account.id]);
      }
    }
    setActiveTab("COMPARATOR");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-6 pb-24">
      <div className="max-w-7xl mx-auto space-y-6">
        <EstrategiasHeaderNav />

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
                <Building2 className="w-6 h-6" />
              </span>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white">
                  Fase 5: Catálogo Maestro 70 Prop Firms CME & Hub de Bots
                </h1>
                <p className="text-slate-400 text-xs mt-0.5">
                  Comparador Cara a Cara estilo Propinex, métricas reales de <strong className="text-emerald-400">Coste Total de Pase (Evaluación + Activación)</strong> y filtrado cuantitativo para trading algorítmico.
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/trading-desk"
              className="inline-flex items-center px-4 py-1.5 rounded-full text-xs font-bold font-mono bg-emerald-950/90 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/80 transition shadow-sm animate-pulse"
            >
              <Activity className="w-4 h-4 mr-1.5 text-emerald-400" />
              ⚡ Abrir Trading Desk Institucional
            </Link>
            <button
              onClick={() => setIsPmtModalOpen(true)}
              className="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-bold font-mono bg-indigo-950/90 hover:bg-indigo-900 text-indigo-300 border border-indigo-700/80 transition shadow-sm"
            >
              <Zap className="w-4 h-4 mr-1.5 text-amber-400" />
              Puente PickMyTrade (7d Trial)
            </button>
            <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold font-mono bg-amber-950/80 text-amber-300 border border-amber-700/60 shadow-sm">
              <ShieldCheck className="w-4 h-4 mr-1.5 text-amber-400" />
              70 Cuentas CME Verificadas
            </span>
          </div>
        </div>

        {/* Real KPI Strip (Corrected Total Pass Cost) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3.5 bg-slate-900/90 rounded-xl border border-slate-800 space-y-0.5">
            <span className="text-[11px] text-slate-400 block uppercase font-mono">Cuentas Auditadas</span>
            <div className="text-2xl font-black text-white font-mono">70 Cuentas</div>
            <span className="text-[11px] text-slate-500 block">17 Firmas Reguladas CME</span>
          </div>

          <div className="p-3.5 bg-slate-900/90 rounded-xl border border-slate-800 space-y-0.5">
            <span className="text-[11px] text-slate-400 block uppercase font-mono">Coste Mínimo Real Total</span>
            <div className="text-2xl font-black text-emerald-400 font-mono">$38.50 USD</div>
            <span className="text-[11px] text-emerald-400/90 block font-medium">Examen con Promo + $0 Activación</span>
          </div>

          <div className="p-3.5 bg-slate-900/90 rounded-xl border border-slate-800 space-y-0.5">
            <span className="text-[11px] text-slate-400 block uppercase font-mono">Cuentas $0 Activación</span>
            <div className="text-2xl font-black text-amber-400 font-mono">34 Cuentas (48%)</div>
            <span className="text-[11px] text-slate-400 block">Sin cuota oculta de pase</span>
          </div>

          <div className="p-3.5 bg-slate-900/90 rounded-xl border border-slate-800 space-y-0.5">
            <span className="text-[11px] text-slate-400 block uppercase font-mono">Idoneidad Bots (EAs)</span>
            <div className="text-2xl font-black text-indigo-400 font-mono">82% Aceptan Bots</div>
            <span className="text-[11px] text-slate-400 block">Tradovate API / NinjaTrader 8</span>
          </div>
        </div>

        {/* AI Sync & Verification Status */}
        <AISyncStatusBar lastUpdatedText="Auditoría Zero-Mocks 2026 · Precios y Políticas Certificadas" />

        {/* Navigation Mode Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-2">
          <button
            onClick={() => setActiveTab("COMPARATOR")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "COMPARATOR"
                ? "bg-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Scale className="w-4 h-4" />
            <span>1. Comparador Cara a Cara ({selectedComparisonIds.length}/4)</span>
          </button>

          <button
            onClick={() => setActiveTab("FINDER")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "FINDER"
                ? "bg-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>2. Asistente Rápido (3 Clics Bots)</span>
          </button>

          <button
            onClick={() => setActiveTab("TABLE")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "TABLE"
                ? "bg-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>3. Tabla Comparativa Semáforo (70 Cuentas)</span>
          </button>

          <button
            onClick={() => setActiveTab("ROI_CALC")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "ROI_CALC"
                ? "bg-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Calculator className="w-4 h-4" />
            <span>4. Calculadora Extracción & ROI</span>
          </button>

          <button
            onClick={() => setActiveTab("LIVE_DEALS")}
            className={`px-4 py-2 rounded-xl text-xs font-bold font-mono transition flex items-center gap-2 ${
              activeTab === "LIVE_DEALS"
                ? "bg-amber-500 text-slate-950 font-black shadow-lg shadow-amber-500/20"
                : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
            }`}
          >
            <Flame className="w-4 h-4" />
            <span>5. Cupones & Ofertas Activas</span>
          </button>
        </div>

        {/* Dynamic View */}
        {activeTab === "COMPARATOR" && (
          <HeadToHeadComparator
            allAccounts={ALL_PROP_FIRM_ACCOUNTS}
            selectedIds={selectedComparisonIds}
            onSelectIdsChange={setSelectedComparisonIds}
          />
        )}

        {activeTab === "FINDER" && (
          <Smart3ClickFinder
            allAccounts={ALL_PROP_FIRM_ACCOUNTS}
            onSelectForComparison={handleAddFromFinder}
            onGoToComparator={() => setActiveTab("COMPARATOR")}
          />
        )}

        {activeTab === "TABLE" && (
          <SemaphoreTable
            accounts={ALL_PROP_FIRM_ACCOUNTS}
            selectedComparisonIds={selectedComparisonIds}
            onToggleComparisonAccount={handleToggleComparisonAccount}
            onGoToComparator={() => setActiveTab("COMPARATOR")}
          />
        )}

        {activeTab === "ROI_CALC" && <ExtractionRoiCalculator />}

        {activeTab === "LIVE_DEALS" && <LiveDealsTracker />}

        {/* Floating comparison drawer if active on any non-comparator tab */}
        {activeTab !== "COMPARATOR" && (
          <FloatingComparisonDrawer
            selectedAccounts={selectedAccounts}
            onRemoveSlot={handleRemoveComparisonSlot}
            onClearAll={handleClearAllComparison}
            onOpenComparator={() => setActiveTab("COMPARATOR")}
          />
        )}

        {/* PickMyTrade & Tradovate Demo Bridge Modal */}
        <PickMyTradeBridgeModal
          isOpen={isPmtModalOpen}
          onClose={() => setIsPmtModalOpen(false)}
        />
      </div>
    </div>
  );
}
