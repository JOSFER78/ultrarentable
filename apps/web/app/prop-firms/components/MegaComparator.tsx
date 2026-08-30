"use client";

import React, { useState, useMemo } from "react";
import {
  X,
  Sparkles,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  Filter,
  Scale,
  Layers,
  Flame,
  TrafficCone,
  ExternalLink,
} from "lucide-react";
import {
  PropFirmAccount,
  AccountSize,
  ALL_PROP_FIRM_ACCOUNTS,
  generateCriticalDifferencesReport,
} from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";

type SectorKey =
  | "IDENTIFICATION"
  | "COSTS_COUPONS"
  | "RISK_DRAWDOWN"
  | "PAYOUTS_EXTRACTION"
  | "MICROSTRUCTURE_RULES";

interface ColumnDefinition {
  id: string;
  label: string;
  sector: SectorKey;
  tooltip: string;
  format: (acc: PropFirmAccount) => React.ReactNode;
  getRawValue: (acc: PropFirmAccount) => string | number | boolean;
  evaluateSemaphore?: (acc: PropFirmAccount) => "GREEN" | "YELLOW" | "RED";
}

const ALL_COLUMNS: ColumnDefinition[] = [
  // SECTOR 1: IDENTIFICACIÓN
  {
    id: "firm_name",
    label: "Firma de Fondeo",
    sector: "IDENTIFICATION",
    tooltip: "Entidad oficial de fondeo y contratos CME.",
    format: (acc) => (
      <div>
        <span className="font-black text-white text-xs">{acc.firm_name}</span>
        <div className="text-[11px] text-sky-400 font-mono mt-0.5">{acc.program_name}</div>
      </div>
    ),
    getRawValue: (acc) => acc.firm_name,
  },
  {
    id: "program_name",
    label: "Programa / Modalidad",
    sector: "IDENTIFICATION",
    tooltip: "Plan (Rapid, Growth, Static, Lightning, Combine, TCP, etc.)",
    format: (acc) => <span className="text-sky-400 font-bold text-xs">{acc.program_name}</span>,
    getRawValue: (acc) => acc.program_name,
  },
  {
    id: "account_size_usd",
    label: "Tamaño de Balance",
    sector: "IDENTIFICATION",
    tooltip: "Balance simulado o nominal de la cuenta.",
    format: (acc) => (
      <span className="font-mono font-black text-slate-100 bg-slate-950/80 px-2 py-0.5 rounded border border-slate-800 text-xs">
        ${(acc.account_size_usd / 1000).toFixed(0)}K USD
      </span>
    ),
    getRawValue: (acc) => acc.account_size_usd,
  },
  {
    id: "market_type",
    label: "Mercado Operado",
    sector: "IDENTIFICATION",
    tooltip: "Activos CME (ES, NQ, MES, MNQ, YM, CL, GC).",
    format: (acc) => <span className="text-slate-400 font-mono text-xs">{acc.market_type}</span>,
    getRawValue: (acc) => acc.market_type,
  },

  // SECTOR 2: COSTES & CUPONES
  {
    id: "exam_price_regular_usd",
    label: "Precio Regular ($)",
    sector: "COSTS_COUPONS",
    tooltip: "Coste base sin cupón aplicado.",
    format: (acc) => <span className="font-mono text-slate-500 line-through text-xs">${acc.exam_price_regular_usd.toFixed(2)}</span>,
    getRawValue: (acc) => acc.exam_price_regular_usd,
  },
  {
    id: "active_coupon_code",
    label: "Cupón Activo & Descuento",
    sector: "COSTS_COUPONS",
    tooltip: "Código de descuento verificado con compra directa.",
    format: (acc) => (
      <BuyButtonWithCoupon
        affiliateUrl={acc.affiliate_url}
        couponCode={acc.active_coupon_code}
        discountPercent={acc.discount_percentage}
        variant="table-row"
      />
    ),
    getRawValue: (acc) => acc.active_coupon_code,
  },
  {
    id: "exam_price_promo_usd",
    label: "Precio Final con Descuento",
    sector: "COSTS_COUPONS",
    tooltip: "Precio neto a pagar al contratar la evaluación.",
    format: (acc) => <span className="font-mono font-black text-emerald-400 text-xs">${acc.exam_price_promo_usd.toFixed(2)}</span>,
    getRawValue: (acc) => acc.exam_price_promo_usd,
    evaluateSemaphore: (acc) => (acc.exam_price_promo_usd <= 60 ? "GREEN" : acc.exam_price_promo_usd <= 120 ? "YELLOW" : "RED"),
  },
  {
    id: "activation_fee_usd",
    label: "Cuota de Activación (Pass Fee)",
    sector: "COSTS_COUPONS",
    tooltip: "Cobro obligatorio al aprobar antes de dar la cuenta fondeada.",
    format: (acc) => (
      acc.activation_fee_usd === 0 ? (
        <span className="font-mono font-black text-sky-400 bg-sky-500/10 px-2 py-0.5 rounded border border-sky-500/30 text-xs">
          $0 USD (GRATIS)
        </span>
      ) : (
        <span className="font-mono font-black text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30 text-xs">
          ${acc.activation_fee_usd} USD
        </span>
      )
    ),
    getRawValue: (acc) => acc.activation_fee_usd,
    evaluateSemaphore: (acc) => (acc.activation_fee_usd === 0 ? "GREEN" : acc.activation_fee_usd <= 130 ? "YELLOW" : "RED"),
  },
  {
    id: "total_pass_cost_usd",
    label: "Coste Total de Pase (TCO)",
    sector: "COSTS_COUPONS",
    tooltip: "Inversión real total (Examen con Promo + Activación).",
    format: (acc) => <span className="font-mono font-black text-white text-xs">${acc.total_pass_cost_usd.toFixed(2)} USD</span>,
    getRawValue: (acc) => acc.total_pass_cost_usd,
    evaluateSemaphore: (acc) => (acc.total_pass_cost_usd <= 90 ? "GREEN" : acc.total_pass_cost_usd <= 180 ? "YELLOW" : "RED"),
  },
  {
    id: "reset_fee_usd",
    label: "Coste de Reset",
    sector: "COSTS_COUPONS",
    tooltip: "Tarifa para reiniciar la cuenta en evaluación.",
    format: (acc) => <span className="font-mono text-slate-300 text-xs">${acc.reset_fee_usd.toFixed(2)}</span>,
    getRawValue: (acc) => acc.reset_fee_usd,
  },
  {
    id: "monthly_renewal_usd",
    label: "Cuota Mensual de Renovación",
    sector: "COSTS_COUPONS",
    tooltip: "Cobro recurrente si no se aprueba en 30 días.",
    format: (acc) => (
      acc.monthly_renewal_usd === 0 ? (
        <span className="text-sky-400 font-bold text-xs">Pago Único ($0)</span>
      ) : (
        <span className="font-mono text-slate-300 text-xs">${acc.monthly_renewal_usd.toFixed(2)}/mes</span>
      )
    ),
    getRawValue: (acc) => acc.monthly_renewal_usd,
    evaluateSemaphore: (acc) => (acc.monthly_renewal_usd === 0 ? "GREEN" : "YELLOW"),
  },
  {
    id: "data_fee_funded_monthly_usd",
    label: "Cuota de Datos en Fondeo",
    sector: "COSTS_COUPONS",
    tooltip: "Coste mensual de datos CME Level 2 en fondeo.",
    format: (acc) => (
      acc.data_fee_funded_monthly_usd === 0 ? (
        <span className="text-emerald-400 font-black text-xs">$0 USD (Gratis)</span>
      ) : (
        <span className="text-rose-400 font-black font-mono text-xs">${acc.data_fee_funded_monthly_usd}/mes</span>
      )
    ),
    getRawValue: (acc) => acc.data_fee_funded_monthly_usd,
    evaluateSemaphore: (acc) => (acc.data_fee_funded_monthly_usd === 0 ? "GREEN" : "RED"),
  },

  // SECTOR 3: RIESGO & DRAWDOWN
  {
    id: "max_drawdown_usd",
    label: "Max Drawdown Total ($ y %)",
    sector: "RISK_DRAWDOWN",
    tooltip: "Pérdida máxima acumulada tolerada.",
    format: (acc) => (
      <span className="font-mono font-black text-rose-400 text-xs">
        ${acc.max_drawdown_usd.toLocaleString()} ({acc.max_drawdown_pct}%)
      </span>
    ),
    getRawValue: (acc) => acc.max_drawdown_usd,
  },
  {
    id: "drawdown_type",
    label: "Tipo de Drawdown",
    sector: "RISK_DRAWDOWN",
    tooltip: "Mecanismo de cálculo del umbral de pérdida.",
    format: (acc) => {
      if (acc.drawdown_type === "STATIC") {
        return <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-xs font-black">Estático Puro</span>;
      }
      if (acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL") {
        return <span className="bg-sky-500/10 text-sky-400 border border-sky-500/30 px-2 py-0.5 rounded text-xs font-black">EOD Trailing (Cierre)</span>;
      }
      return <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded text-xs font-black">Intraday Peak</span>;
    },
    getRawValue: (acc) => acc.drawdown_type,
    evaluateSemaphore: (acc) => (acc.drawdown_type === "STATIC" || acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL" ? "GREEN" : "RED"),
  },
  {
    id: "freeze_level_description",
    label: "Freeze Level (Congelación)",
    sector: "RISK_DRAWDOWN",
    tooltip: "Momento exacto en que el trailing se detiene.",
    format: (acc) => <span className="text-slate-300 text-xs">{acc.freeze_level_description}</span>,
    getRawValue: (acc) => acc.freeze_level_description,
  },
  {
    id: "daily_loss_limit_usd",
    label: "Daily Loss Limit (DLL)",
    sector: "RISK_DRAWDOWN",
    tooltip: "Límite diario de pérdida.",
    format: (acc) => {
      if (acc.daily_loss_limit_type === "NONE") {
        return <span className="text-emerald-400 font-black text-xs">Sin DLL (Libre)</span>;
      }
      if (acc.daily_loss_limit_type === "SOFT_BREACH") {
        return <span className="text-amber-400 font-mono font-bold text-xs">${acc.daily_loss_limit_usd} (Soft Lock)</span>;
      }
      return <span className="text-rose-400 font-mono font-black text-xs">${acc.daily_loss_limit_usd} (HARD BREACH 💀)</span>;
    },
    getRawValue: (acc) => acc.daily_loss_limit_type,
    evaluateSemaphore: (acc) => (acc.daily_loss_limit_type === "NONE" ? "GREEN" : acc.daily_loss_limit_type === "SOFT_BREACH" ? "YELLOW" : "RED"),
  },
  {
    id: "target_to_drawdown_ratio",
    label: "Ratio Target / Drawdown",
    sector: "RISK_DRAWDOWN",
    tooltip: "Dificultad: profit requerido por cada $1 de drawdown.",
    format: (acc) => <span className="font-mono font-black text-slate-100 text-xs">{acc.target_to_drawdown_ratio.toFixed(2)}x</span>,
    getRawValue: (acc) => acc.target_to_drawdown_ratio,
    evaluateSemaphore: (acc) => (acc.target_to_drawdown_ratio <= 1.2 ? "GREEN" : acc.target_to_drawdown_ratio <= 1.6 ? "YELLOW" : "RED"),
  },

  // SECTOR 4: RETIROS & EXTRACCIÓN
  {
    id: "profit_target_usd",
    label: "Profit Target ($ y %)",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Objetivo de ganancia para aprobar la evaluación.",
    format: (acc) => <span className="font-mono font-black text-white text-xs">${acc.profit_target_usd.toLocaleString()} ({acc.profit_target_pct}%)</span>,
    getRawValue: (acc) => acc.profit_target_usd,
  },
  {
    id: "min_trading_days_eval",
    label: "Días Mínimos en Examen",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Días de operativa obligatorios antes de aprobar.",
    format: (acc) => (
      acc.min_trading_days_eval === 0 ? (
        <span className="text-emerald-400 font-black text-xs">0 días (Pase Día 1)</span>
      ) : (
        <span className="font-mono text-slate-300 text-xs">{acc.min_trading_days_eval} días</span>
      )
    ),
    getRawValue: (acc) => acc.min_trading_days_eval,
    evaluateSemaphore: (acc) => (acc.min_trading_days_eval <= 1 ? "GREEN" : acc.min_trading_days_eval <= 5 ? "YELLOW" : "RED"),
  },
  {
    id: "min_trading_days_payout",
    label: "Días Fondeo para Retirar",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Días requeridos en fondeo antes del primer cobro.",
    format: (acc) => (
      acc.min_trading_days_payout === 0 ? (
        <span className="text-emerald-400 font-black text-xs">Día 1 (Inmediato)</span>
      ) : (
        <span className="font-mono text-slate-300 text-xs">{acc.min_trading_days_payout} días</span>
      )
    ),
    getRawValue: (acc) => acc.min_trading_days_payout,
    evaluateSemaphore: (acc) => (acc.min_trading_days_payout === 0 ? "GREEN" : acc.min_trading_days_payout <= 5 ? "YELLOW" : "RED"),
  },
  {
    id: "safety_buffer_usd",
    label: "Safety Buffer Retenido",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Colchón de seguridad que la firma retiene permanentemente.",
    format: (acc) => <span className="font-mono font-black text-amber-400 text-xs">${acc.safety_buffer_usd.toLocaleString()} USD</span>,
    getRawValue: (acc) => acc.safety_buffer_usd,
  },
  {
    id: "capital_required_first_payout_1k",
    label: "Capital para 1er Retiro ($1K)",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Target + Safety Buffer + $1,000 netos: El esfuerzo real.",
    format: (acc) => <span className="font-mono font-black text-sky-400 text-xs">${acc.capital_required_first_payout_1k.toLocaleString()} USD</span>,
    getRawValue: (acc) => acc.capital_required_first_payout_1k,
    evaluateSemaphore: (acc) => (acc.capital_required_first_payout_1k <= 5500 ? "GREEN" : acc.capital_required_first_payout_1k <= 6500 ? "YELLOW" : "RED"),
  },
  {
    id: "payout_frequency",
    label: "Frecuencia de Retiro",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Rapidez y periodicidad de transferencias.",
    format: (acc) => <span className="text-sky-400 font-black text-xs">{acc.payout_frequency_label}</span>,
    getRawValue: (acc) => acc.payout_frequency,
    evaluateSemaphore: (acc) => (acc.payout_frequency === "DAY_1_ON_DEMAND" || acc.payout_frequency === "SAME_DAY_BUSINESS" || acc.payout_frequency === "EVERY_3_DAYS" ? "GREEN" : acc.payout_frequency === "WEEKLY" ? "YELLOW" : "RED"),
  },
  {
    id: "payout_split_tier_1",
    label: "Profit Split Tier 1",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Porcentaje de ganancia asignado al trader.",
    format: (acc) => <span className="font-mono font-black text-emerald-400 text-xs">{acc.payout_split_tier_1}</span>,
    getRawValue: (acc) => acc.payout_split_tier_1,
  },
  {
    id: "payout_split_tier_2",
    label: "Profit Split Tier 2",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Reparto posterior a largo plazo.",
    format: (acc) => <span className="font-mono text-slate-300 text-xs">{acc.payout_split_tier_2}</span>,
    getRawValue: (acc) => acc.payout_split_tier_2,
  },
  {
    id: "payout_first_3m_cap_usd",
    label: "Tope Máximo Primeros 3 Meses",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Límite máximo permitido de extracción.",
    format: (acc) => (
      acc.payout_first_3m_cap_usd === 0 ? (
        <span className="text-emerald-400 font-black text-xs">Sin Límite ($0 Tope)</span>
      ) : (
        <span className="text-rose-400 font-mono font-black text-xs">${acc.payout_first_3m_cap_usd} máx</span>
      )
    ),
    getRawValue: (acc) => acc.payout_first_3m_cap_usd,
    evaluateSemaphore: (acc) => (acc.payout_first_3m_cap_usd === 0 ? "GREEN" : "RED"),
  },

  // SECTOR 5: MICROESTRUCTURA & REGLAS
  {
    id: "max_contracts_minis",
    label: "Apalancamiento Máx (Minis/Micros)",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Contratos simultáneos permitidos CME.",
    format: (acc) => (
      <span className="font-mono font-black text-slate-100 text-xs">
        {acc.max_contracts_minis} Minis ({acc.max_contracts_micros} Micros)
      </span>
    ),
    getRawValue: (acc) => acc.max_contracts_minis,
  },
  {
    id: "scaling_plan_required",
    label: "Plan de Escalado",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "¿Obligan a comenzar con pocos contratos?",
    format: (acc) => (
      acc.scaling_plan_required ? (
        <span className="text-rose-400 font-bold text-xs">Obligatorio (Restringido)</span>
      ) : (
        <span className="text-emerald-400 font-black text-xs">Libre desde el Día 1</span>
      )
    ),
    getRawValue: (acc) => acc.scaling_plan_required,
    evaluateSemaphore: (acc) => (!acc.scaling_plan_required ? "GREEN" : "RED"),
  },
  {
    id: "consistency_rule_pct",
    label: "Regla de Consistencia (%)",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Porcentaje máximo de profit de un solo día.",
    format: (acc) => (
      acc.consistency_rule_pct === 0 ? (
        <span className="text-emerald-400 font-black text-xs">Sin Regla (0%)</span>
      ) : (
        <span className="font-mono text-amber-400 font-bold text-xs">{acc.consistency_rule_pct}% Máximo</span>
      )
    ),
    getRawValue: (acc) => acc.consistency_rule_pct,
    evaluateSemaphore: (acc) => (acc.consistency_rule_pct === 0 ? "GREEN" : acc.consistency_rule_pct >= 40 ? "YELLOW" : "RED"),
  },
  {
    id: "trade_duration_10s_rule",
    label: "Regla de 10s por Trade",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Obligación de durar al menos 10 segundos.",
    format: (acc) => (
      acc.trade_duration_10s_rule ? (
        <span className="text-rose-400 font-bold text-xs">Sí (Mín 10s en 50%+ trades)</span>
      ) : (
        <span className="text-emerald-400 font-black text-xs">Sin Restricción de Tiempo</span>
      )
    ),
    getRawValue: (acc) => acc.trade_duration_10s_rule,
    evaluateSemaphore: (acc) => (!acc.trade_duration_10s_rule ? "GREEN" : "RED"),
  },
  {
    id: "news_trading_restricted",
    label: "Restricción de Noticias (CPI/FOMC)",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Prohibición de operar comunicados macro.",
    format: (acc) => (
      acc.news_trading_restricted ? (
        <span className="text-rose-400 font-bold text-xs">Prohibido (±2 min)</span>
      ) : (
        <span className="text-emerald-400 font-black text-xs">100% Permitido Operar Noticias</span>
      )
    ),
    getRawValue: (acc) => acc.news_trading_restricted,
    evaluateSemaphore: (acc) => (!acc.news_trading_restricted ? "GREEN" : "RED"),
  },
  {
    id: "session_close_mandatory_time",
    label: "Hora de Cierre Forzoso CME",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Hora límite diaria de liquidación.",
    format: (acc) => <span className="font-mono text-slate-300 text-xs">{acc.session_close_mandatory_time}</span>,
    getRawValue: (acc) => acc.session_close_mandatory_time,
  },
  {
    id: "bot_policy",
    label: "Política de Bots & EAs",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Permisividad para sistemas automatizados.",
    format: (acc) => {
      if (acc.bot_policy === "ALLOWED_100") {
        return <span className="text-emerald-400 font-black text-xs">✅ 100% EAs/VPS</span>;
      }
      if (acc.bot_policy === "PROHIBITED") {
        return <span className="text-rose-400 font-black text-xs">❌ 100% PROHIBIDO</span>;
      }
      return <span className="text-amber-400 font-bold text-xs">⚠️ Restringido (Local)</span>;
    },
    getRawValue: (acc) => acc.bot_policy,
    evaluateSemaphore: (acc) => (acc.bot_policy === "ALLOWED_100" ? "GREEN" : acc.bot_policy === "ALLOWED_LOCAL_ONLY" ? "YELLOW" : "RED"),
  },
  {
    id: "data_gateway",
    label: "Pasarela de Datos CME",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Proveedor de enrutamiento.",
    format: (acc) => <span className="font-mono font-black text-sky-400 text-xs">{acc.data_gateway}</span>,
    getRawValue: (acc) => acc.data_gateway,
  },
  {
    id: "platforms_supported",
    label: "Plataformas Soportadas",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Software compatible.",
    format: (acc) => (
      <div className="flex flex-wrap gap-1">
        {acc.platforms_supported.map((p) => (
          <span key={p} className="bg-slate-950/80 text-slate-300 px-1.5 py-0.5 rounded text-[10px] border border-slate-800 font-mono">
            {p}
          </span>
        ))}
      </div>
    ),
    getRawValue: (acc) => acc.platforms_supported.join(", "),
  },
];

const SECTORS_META: Record<SectorKey, { title: string; icon: string }> = {
  IDENTIFICATION: { title: "1. Identificación & Balance", icon: "🏛️" },
  COSTS_COUPONS: { title: "2. Costes Reales, Cupones & Activación", icon: "💰" },
  RISK_DRAWDOWN: { title: "3. Riesgo, Tolerancia & Reglas de Drawdown", icon: "🛡️" },
  PAYOUTS_EXTRACTION: { title: "4. Retiros, Colchón Intocable & Extracción", icon: "⚡" },
  MICROSTRUCTURE_RULES: { title: "5. Microestructura, Bots & Letra Pequeña", icon: "🤖" },
};

export function MegaComparator() {
  const [firmFilter, setFirmFilter] = useState<string>("ALL");
  const [sizeFilter, setSizeFilter] = useState<AccountSize | "ALL">("ALL");
  const [viewMode, setViewMode] = useState<"FULL_MATRIX" | "ONLY_DIFFERENCES">("FULL_MATRIX");
  const [enableSemaphore, setEnableSemaphore] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Selected accounts (2 to 6)
  const [selectedIds, setSelectedIds] = useState<string[]>([
    "mffu-rapid-50k",
    "tradeify-growth-50k",
    "topstep-combine-50k",
    "blusky-static-50k",
  ]);

  const [expandedSectors, setExpandedSectors] = useState<Record<SectorKey, boolean>>({
    IDENTIFICATION: true,
    COSTS_COUPONS: true,
    RISK_DRAWDOWN: true,
    PAYOUTS_EXTRACTION: true,
    MICROSTRUCTURE_RULES: true,
  });

  const availableAccounts = useMemo(() => {
    return ALL_PROP_FIRM_ACCOUNTS.filter((acc) => {
      if (firmFilter !== "ALL" && acc.firm_slug !== firmFilter) return false;
      if (sizeFilter !== "ALL" && acc.account_size_usd !== sizeFilter) return false;
      return true;
    });
  }, [firmFilter, sizeFilter]);

  const selectedAccounts = useMemo(() => {
    return selectedIds
      .map((id) => ALL_PROP_FIRM_ACCOUNTS.find((a) => a.id === id)!)
      .filter(Boolean);
  }, [selectedIds]);

  const handleAddSlot = (id: string) => {
    if (!selectedIds.includes(id) && selectedIds.length < 6) {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleRemoveSlot = (id: string) => {
    if (selectedIds.length > 2) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    }
  };

  const toggleSector = (sector: SectorKey) => {
    setExpandedSectors((prev) => ({ ...prev, [sector]: !prev[sector] }));
  };

  const isRowDifferent = (col: ColumnDefinition): boolean => {
    if (selectedAccounts.length <= 1) return false;
    const firstVal = String(col.getRawValue(selectedAccounts[0]));
    return selectedAccounts.some((acc) => String(col.getRawValue(acc)) !== firstVal);
  };

  const filteredColumns = useMemo(() => {
    return ALL_COLUMNS.filter((col) => {
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesLabel = col.label.toLowerCase().includes(query);
        const matchesTooltip = col.tooltip.toLowerCase().includes(query);
        if (!matchesLabel && !matchesTooltip) return false;
      }
      if (viewMode === "ONLY_DIFFERENCES") {
        return isRowDifferent(col);
      }
      return true;
    });
  }, [viewMode, searchQuery, selectedAccounts]);

  const uniqueFirms = useMemo(() => {
    const map = new Map<string, string>();
    ALL_PROP_FIRM_ACCOUNTS.forEach((a) => map.set(a.firm_slug, a.firm_name));
    return Array.from(map.entries());
  }, []);

  return (
    <div className="w-full space-y-6">
      {/* 1. PANEL SUPERIOR */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-black text-white tracking-tight flex items-center gap-2">
              <Scale className="w-5 h-5 text-amber-400" />
              <span>Mega-Comparador Multi-Cuenta ({ALL_PROP_FIRM_ACCOUNTS.length} Cuentas · 36 Columnas)</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Compara de 2 a 6 cuentas simultáneamente con botones directos de compra, semáforo inteligente y auditoría forense.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={firmFilter}
              onChange={(e) => setFirmFilter(e.target.value)}
              className="bg-slate-950 text-white border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs font-mono font-bold focus:border-amber-500 focus:outline-none"
            >
              <option value="ALL">Todas las Firmas ({uniqueFirms.length})</option>
              {uniqueFirms.map(([slug, name]) => (
                <option key={slug} value={slug}>{name}</option>
              ))}
            </select>

            <select
              value={sizeFilter}
              onChange={(e) => setSizeFilter(e.target.value === "ALL" ? "ALL" : (Number(e.target.value) as AccountSize))}
              className="bg-slate-950 text-white border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs font-mono font-bold focus:border-amber-500 focus:outline-none"
            >
              <option value="ALL">Todos los Tamaños ($9K - $300K)</option>
              <option value={9000}>$9,000 USD</option>
              <option value={10000}>$10,000 USD</option>
              <option value={25000}>$25,000 USD</option>
              <option value={50000}>$50,000 USD (Estándar)</option>
              <option value={75000}>$75,000 USD</option>
              <option value={100000}>$100,000 USD</option>
              <option value={150000}>$150,000 USD</option>
              <option value={200000}>$200,000 USD</option>
              <option value={250000}>$250,000 USD</option>
              <option value={300000}>$300,000 USD</option>
            </select>
          </div>
        </div>

        {/* Selected Slots Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-800/80">
          {selectedAccounts.map((acc, idx) => (
            <div
              key={acc.id}
              className="bg-slate-950/90 border border-sky-500/30 rounded-xl p-3 relative flex flex-col justify-between space-y-2 group shadow-sm"
            >
              <button
                onClick={() => handleRemoveSlot(acc.id)}
                disabled={selectedAccounts.length <= 2}
                className="absolute top-2 right-2 text-slate-500 hover:text-rose-400 disabled:opacity-20 transition"
                title="Eliminar de la comparativa"
              >
                <X className="w-3.5 h-3.5" />
              </button>
              <div>
                <span className="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider block truncate pr-4">
                  Slot {idx + 1} · {acc.firm_name}
                </span>
                <div className="text-xs font-black text-white truncate mt-0.5">
                  {acc.program_name}
                </div>
                <div className="text-[11px] font-mono text-slate-400 mt-1 flex items-center justify-between">
                  <span className="font-bold text-slate-200">${(acc.account_size_usd / 1000).toFixed(0)}K</span>
                  <span className="text-emerald-400 font-bold">${acc.exam_price_promo_usd.toFixed(0)}</span>
                </div>
              </div>
              <div className="pt-2">
                <BuyButtonWithCoupon
                  affiliateUrl={acc.affiliate_url}
                  couponCode={acc.active_coupon_code}
                  discountPercent={acc.discount_percentage}
                  variant="compact"
                  buttonText={`Comprar $${acc.exam_price_promo_usd.toFixed(0)}`}
                />
              </div>
            </div>
          ))}

          {selectedAccounts.length < 6 && (
            <div className="bg-slate-950/40 border border-dashed border-slate-800 rounded-xl p-3 flex flex-col justify-center items-center gap-2">
              <span className="text-[11px] font-mono text-slate-400">+ Slot ({selectedAccounts.length}/6)</span>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddSlot(e.target.value);
                    e.target.value = "";
                  }
                }}
                className="w-full bg-[#030712] text-sky-400 border border-sky-500/40 rounded-lg p-1.5 text-xs font-mono font-bold focus:outline-none"
                defaultValue=""
              >
                <option value="" disabled>Añadir...</option>
                {availableAccounts.filter((a) => !selectedIds.includes(a.id)).map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.firm_name} — {acc.program_name} (${(acc.account_size_usd / 1000).toFixed(0)}K)
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* 2. TABLA MATRICIAL DE 36 COLUMNAS */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl overflow-x-auto shadow-2xl">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="bg-slate-950/95 border-b border-slate-800 sticky top-0 z-10">
              <th className="py-3.5 px-4 w-64 text-slate-400 text-[11px] font-bold uppercase tracking-wider">
                Atributo Técnico Forense (36 Columnas)
              </th>
              {selectedAccounts.map((acc) => (
                <th key={acc.id} className="py-3.5 px-4 min-w-[200px] border-l border-slate-800/80">
                  <div className="text-[10px] font-bold text-sky-400 uppercase tracking-wider">{acc.firm_name}</div>
                  <div className="text-sm font-black text-white mt-0.5">{acc.program_name}</div>
                  <div className="text-[11px] text-slate-400 font-sans mt-0.5">
                    ${(acc.account_size_usd / 1000).toFixed(0)}K · {acc.market_type}
                  </div>
                  <div className="mt-2">
                    <BuyButtonWithCoupon
                      affiliateUrl={acc.affiliate_url}
                      couponCode={acc.active_coupon_code}
                      discountPercent={acc.discount_percentage}
                      variant="compact"
                      buttonText="Comprar ↗"
                    />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {(["IDENTIFICATION", "COSTS_COUPONS", "RISK_DRAWDOWN", "PAYOUTS_EXTRACTION", "MICROSTRUCTURE_RULES"] as SectorKey[]).map((sectorKey) => {
              const sectorColumns = filteredColumns.filter((col) => col.sector === sectorKey);
              if (sectorColumns.length === 0) return null;
              const meta = SECTORS_META[sectorKey];
              const isExpanded = expandedSectors[sectorKey];

              return (
                <React.Fragment key={sectorKey}>
                  <tr
                    onClick={() => toggleSector(sectorKey)}
                    className="bg-slate-950/80 border-t border-slate-800 cursor-pointer hover:bg-slate-900/60 transition select-none"
                  >
                    <td colSpan={selectedAccounts.length + 1} className="py-2.5 px-4 text-emerald-400 font-black text-xs uppercase tracking-wider">
                      <div className="flex justify-between items-center">
                        <span>{meta.icon} {meta.title} ({sectorColumns.length} Atributos)</span>
                        <span>{isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}</span>
                      </div>
                    </td>
                  </tr>

                  {isExpanded && sectorColumns.map((col) => (
                    <tr key={col.id} className="hover:bg-slate-900/40 transition">
                      <td className="py-3 px-4 text-slate-300">
                        <div className="font-bold text-white text-xs">{col.label}</div>
                        <div className="text-[10px] text-slate-500 font-sans leading-tight mt-0.5">{col.tooltip}</div>
                      </td>
                      {selectedAccounts.map((acc) => (
                        <td key={acc.id} className="py-3 px-4 border-l border-slate-800/80 align-top">
                          {col.format(acc)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
