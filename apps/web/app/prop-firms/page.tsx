"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Building2,
  ShieldCheck,
  Sparkles,
  Scale,
  Calculator,
  Flame,
  Activity,
  Zap,
  Grid,
  FileCheck2,
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
import { MegaComparator } from "./components/MegaComparator";
import { getPropFirmsV2, FirmaV2 } from "@/lib/propFirmsV2";

export type PropFirmTab =
  | "TABLE"
  | "COMPARATOR"
  | "FINDER"
  | "ROI_CALC"
  | "LIVE_DEALS"
  | "MEGA"
  | "SOURCE_REF";

const TOOL_METAS: Record<
  PropFirmTab,
  { title: string; badge: string; desc: string; icon: React.ComponentType<{ className?: string }> }
> = {
  TABLE: {
    title: "Catálogo Completo 70 Cuentas CME",
    badge: "70 CUENTAS",
    desc: "Métricas auditadas de Coste Total de Pase (Evaluación + Activación), modelo de drawdown EOD vs Intraday y compatibilidad con bots.",
    icon: Building2,
  },
  COMPARATOR: {
    title: "Comparador Cara a Cara (Head-to-Head)",
    badge: "PROP-METRIC",
    desc: "Compara de 2 a 4 cuentas cara a cara con transparencia total en Coste Total de Pase (TCO), tamaño y reglas intradía.",
    icon: Scale,
  },
  FINDER: {
    title: "Buscador 3-Clics Inteligente",
    badge: "FILTRO RÁPIDO",
    desc: "Encuentra la cuenta ideal por presupuesto, política de bots y modelo de drawdown en solo 3 selecciones.",
    icon: Sparkles,
  },
  ROI_CALC: {
    title: "Calculadora de ROI de Extracción",
    badge: "PAYOUT RETIROS",
    desc: "Modela la esperanza matemática, número de balas y días necesarios para amortizar el coste de evaluación.",
    icon: Calculator,
  },
  LIVE_DEALS: {
    title: "Cupones y Ofertas en Tiempo Real",
    badge: "DESCUENTOS CME",
    desc: "Códigos promocionales verificados y actualizados para reducir el coste de entrada en firmas oficiales.",
    icon: Flame,
  },
  MEGA: {
    title: "Mega-Comparador Multi-Cuenta (36 Columnas)",
    badge: "36 ATRIBUTOS",
    desc: "Matriz comparativa exhaustiva de especificaciones técnicas para hasta 6 cuentas simultáneas.",
    icon: Grid,
  },
  SOURCE_REF: {
    title: "Auditoría Backend SourceRef",
    badge: "DIRECTIVA D6/D7",
    desc: "Trazabilidad forense de endpoints y fuentes de datos canónicas auditadas en backend.",
    icon: FileCheck2,
  },
};

function PropFirmsContent() {
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState<PropFirmTab>("TABLE");
  const [isPmtModalOpen, setIsPmtModalOpen] = useState<boolean>(false);

  // Estado para Catálogo Auditado V2
  const [firmasV2, setFirmasV2] = useState<FirmaV2[]>([]);
  const [loadingV2, setLoadingV2] = useState<boolean>(false);

  useEffect(() => {
    const viewParam = searchParams.get("view");
    if (viewParam === "finder") setActiveTab("FINDER");
    else if (viewParam === "comparator") setActiveTab("COMPARATOR");
    else if (viewParam === "table") setActiveTab("TABLE");
    else if (viewParam === "roi") setActiveTab("ROI_CALC");
    else if (viewParam === "deals") setActiveTab("LIVE_DEALS");
    else if (viewParam === "mega") setActiveTab("MEGA");
    else if (viewParam === "audit") setActiveTab("SOURCE_REF");
    else setActiveTab("TABLE");
  }, [searchParams]);

  useEffect(() => {
    if (activeTab === "SOURCE_REF" && firmasV2.length === 0) {
      setLoadingV2(true);
      getPropFirmsV2()
        .then((res) => setFirmasV2(res))
        .catch(() => setFirmasV2([]))
        .finally(() => setLoadingV2(false));
    }
  }, [activeTab, firmasV2.length]);

  // Cuentas seleccionadas para comparación cara a cara
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
    setSelectedComparisonIds(["mffu-rapid-50k", "tradeify-growth-50k"]);
  };

  const handleAddFromFinder = (account: PropFirmAccount) => {
    if (!selectedComparisonIds.includes(account.id)) {
      if (selectedComparisonIds.length < 4) {
        setSelectedComparisonIds([...selectedComparisonIds, account.id]);
      } else {
        setSelectedComparisonIds([...selectedComparisonIds, account.id]);
      }
    }
    setActiveTab("COMPARATOR");
  };

  const meta = TOOL_METAS[activeTab] || TOOL_METAS.TABLE;
  const ActiveIcon = meta.icon;

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner Sobrio y Dinámico (Sin duplicaciones) */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)] flex items-center justify-center shrink-0">
              <ActiveIcon className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg sm:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
                <span>{meta.title}</span>
                <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                  {meta.badge}
                </span>
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
                {meta.desc}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0 font-mono text-xs">
            <Link
              href="/trading-desk"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border)] transition"
            >
              <Activity className="w-3.5 h-3.5 text-[var(--profit)]" />
              <span>Trading Desk</span>
            </Link>
            <button
              onClick={() => setIsPmtModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border)] transition cursor-pointer"
            >
              <Zap className="w-3.5 h-3.5 text-[var(--profit)]" />
              <span>Puente Tradovate</span>
            </button>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)]">
              <ShieldCheck className="w-3.5 h-3.5 text-[var(--profit)]" />
              <span>CME Verificadas</span>
            </span>
          </div>
        </div>
      </div>

      {/* KPI Strip Compacto */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 font-mono">
        <div className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-0.5">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Cuentas en Catálogo</span>
          <div className="text-lg font-bold text-[var(--text-1)]">70 Cuentas</div>
          <span className="text-[10px] text-[var(--text-3)] block">17 Firmas Reguladas CME</span>
        </div>

        <div className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-0.5">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Coste Mínimo Real Total</span>
          <div className="text-lg font-bold text-[var(--profit)]">$38.50 USD</div>
          <span className="text-[10px] text-[var(--text-3)] block">Examen con Promo + $0 Activación</span>
        </div>

        <div className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-0.5">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Cuentas $0 Activación</span>
          <div className="text-lg font-bold text-[var(--text-1)]">34 Cuentas (48%)</div>
          <span className="text-[10px] text-[var(--text-3)] block">Sin cuota oculta de pase</span>
        </div>

        <div className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-0.5">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Idoneidad Bots (EAs)</span>
          <div className="text-lg font-bold text-[var(--profit)]">82% Aceptan Bots</div>
          <span className="text-[10px] text-[var(--text-3)] block">Tradovate API / NinjaTrader 8</span>
        </div>
      </div>

      {/* Vistas Dinámicas (Directas según selección en Sidebar) */}
      {activeTab === "TABLE" && (
        <SemaphoreTable
          accounts={ALL_PROP_FIRM_ACCOUNTS}
          selectedComparisonIds={selectedComparisonIds}
          onToggleComparisonAccount={handleToggleComparisonAccount}
          onGoToComparator={() => setActiveTab("COMPARATOR")}
        />
      )}

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

      {activeTab === "ROI_CALC" && <ExtractionRoiCalculator />}

      {activeTab === "LIVE_DEALS" && <LiveDealsTracker />}

      {activeTab === "MEGA" && <MegaComparator />}

      {activeTab === "SOURCE_REF" && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
            <div>
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Catálogo Backend con Trazabilidad Primaria (SourceRef)
              </h2>
              <p className="text-xs text-[var(--text-3)]">
                Cada campo cuenta con fuente explícita auditada por el backend en /api/v1/prop-firms/v2.
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-2)] text-[var(--profit)] border border-[var(--border)]">
              Directiva D6/D7
            </span>
          </div>

          {loadingV2 ? (
            <div className="p-8 text-center text-[var(--text-3)]">Consultando catálogo v2 en backend...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[var(--surface-2)] border-b border-[var(--border)] text-[10px] text-[var(--text-3)] uppercase">
                    <th className="p-2.5">Firma</th>
                    <th className="p-2.5">Tipo Drawdown</th>
                    <th className="p-2.5">DD 50K</th>
                    <th className="p-2.5">Pérdida Diaria</th>
                    <th className="p-2.5">Examen 50K</th>
                    <th className="p-2.5">Activación</th>
                    <th className="p-2.5">Split Retiros</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {firmasV2.map((f) => (
                    <tr key={f.id} className="hover:bg-[var(--surface-2)] transition">
                      <td className="p-2.5 font-bold text-[var(--text-1)]">{f.nombre}</td>
                      <td className="p-2.5 text-[var(--text-2)]">{f.trailing_dd_tipo?.valor || "NO EVIDENCE"}</td>
                      <td className="p-2.5 text-[var(--text-1)]">
                        {f.trailing_dd_valor_50k?.valor ? `$${f.trailing_dd_valor_50k.valor}` : "NO EVIDENCE"}
                      </td>
                      <td className="p-2.5 text-[var(--text-2)]">
                        {f.perdida_diaria_limite_50k?.valor ? `$${f.perdida_diaria_limite_50k.valor}` : "NO EVIDENCE"}
                      </td>
                      <td className="p-2.5 text-[var(--profit)] font-bold">
                        {f.precio_examen_50k?.valor ? `$${f.precio_examen_50k.valor}` : "NO EVIDENCE"}
                      </td>
                      <td className="p-2.5 text-[var(--text-2)]">
                        {f.coste_activacion_50k?.valor ? `$${f.coste_activacion_50k.valor}` : "NO EVIDENCE"}
                      </td>
                      <td className="p-2.5 text-[var(--text-1)]">
                        {f.payout_split_pct?.valor ? `${f.payout_split_pct.valor}%` : "NO EVIDENCE"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Floating comparison drawer en pestañas distintas del comparador */}
      {activeTab !== "COMPARATOR" && activeTab !== "MEGA" && (
        <FloatingComparisonDrawer
          selectedAccounts={selectedAccounts}
          onRemoveSlot={handleRemoveComparisonSlot}
          onClearAll={handleClearAllComparison}
          onOpenComparator={() => setActiveTab("COMPARATOR")}
        />
      )}

      {/* Modal Puente Tradovate */}
      <PickMyTradeBridgeModal
        isOpen={isPmtModalOpen}
        onClose={() => setIsPmtModalOpen(false)}
      />
    </div>
  );
}

export default function PropFirmsMasterPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 text-center text-xs font-mono text-[var(--text-3)]">
          Cargando suite de prop firms...
        </div>
      }
    >
      <PropFirmsContent />
    </Suspense>
  );
}
