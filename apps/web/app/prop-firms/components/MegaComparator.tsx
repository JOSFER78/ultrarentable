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
        <span style={{ fontWeight: 900, color: "#ffffff", fontSize: "12.5px" }}>{acc.firm_name}</span>
        <div style={{ fontSize: "10.5px", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>{acc.program_name}</div>
      </div>
    ),
    getRawValue: (acc) => acc.firm_name,
  },
  {
    id: "program_name",
    label: "Programa / Modalidad",
    sector: "IDENTIFICATION",
    tooltip: "Plan (Rapid, Growth, Static, Lightning, Combine, TCP, etc.)",
    format: (acc) => <span style={{ color: "#38bdf8", fontWeight: 700 }}>{acc.program_name}</span>,
    getRawValue: (acc) => acc.program_name,
  },
  {
    id: "account_size_usd",
    label: "Tamaño de Balance",
    sector: "IDENTIFICATION",
    tooltip: "Balance simulado o nominal de la cuenta.",
    format: (acc) => (
      <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#f1f5f9", background: "#06090e", padding: "2px 6px", borderRadius: "4px", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
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
    format: (acc) => <span style={{ color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", fontSize: "11px" }}>{acc.market_type}</span>,
    getRawValue: (acc) => acc.market_type,
  },

  // SECTOR 2: COSTES & CUPONES
  {
    id: "exam_price_regular_usd",
    label: "Precio Regular ($)",
    sector: "COSTS_COUPONS",
    tooltip: "Coste base sin cupón aplicado.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#64748b", textDecoration: "line-through" }}>${acc.exam_price_regular_usd.toFixed(2)}</span>,
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
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 900, color: "#4ade80", fontSize: "13px" }}>${acc.exam_price_promo_usd.toFixed(2)}</span>,
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
        <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
          $0 USD (GRATIS)
        </span>
      ) : (
        <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#fb7185", background: "rgba(244, 63, 94, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
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
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 900, color: "#ffffff", fontSize: "13px" }}>${acc.total_pass_cost_usd.toFixed(2)} USD</span>,
    getRawValue: (acc) => acc.total_pass_cost_usd,
    evaluateSemaphore: (acc) => (acc.total_pass_cost_usd <= 90 ? "GREEN" : acc.total_pass_cost_usd <= 180 ? "YELLOW" : "RED"),
  },
  {
    id: "reset_fee_usd",
    label: "Coste de Reset",
    sector: "COSTS_COUPONS",
    tooltip: "Tarifa para reiniciar la cuenta en evaluación.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>${acc.reset_fee_usd.toFixed(2)}</span>,
    getRawValue: (acc) => acc.reset_fee_usd,
  },
  {
    id: "monthly_renewal_usd",
    label: "Cuota Mensual de Renovación",
    sector: "COSTS_COUPONS",
    tooltip: "Cobro recurrente si no se aprueba en 30 días.",
    format: (acc) => (
      acc.monthly_renewal_usd === 0 ? (
        <span style={{ color: "#38bdf8", fontWeight: 700 }}>Pago Único ($0)</span>
      ) : (
        <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>${acc.monthly_renewal_usd.toFixed(2)}/mes</span>
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
        <span style={{ color: "#4ade80", fontWeight: 800 }}>$0 USD (Gratis)</span>
      ) : (
        <span style={{ color: "#fb7185", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>${acc.data_fee_funded_monthly_usd}/mes</span>
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
      <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#fb7185" }}>
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
        return <span style={{ background: "rgba(34, 197, 94, 0.15)", color: "#4ade80", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>Estático Puro</span>;
      }
      if (acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL") {
        return <span style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>EOD Trailing (Cierre)</span>;
      }
      return <span style={{ background: "rgba(244, 63, 94, 0.15)", color: "#fb7185", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>Intraday Peak</span>;
    },
    getRawValue: (acc) => acc.drawdown_type,
    evaluateSemaphore: (acc) => (acc.drawdown_type === "STATIC" || acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL" ? "GREEN" : "RED"),
  },
  {
    id: "freeze_level_description",
    label: "Freeze Level (Congelación)",
    sector: "RISK_DRAWDOWN",
    tooltip: "Momento exacto en que el trailing se detiene.",
    format: (acc) => <span style={{ color: "#cbd5e1", fontSize: "11px" }}>{acc.freeze_level_description}</span>,
    getRawValue: (acc) => acc.freeze_level_description,
  },
  {
    id: "daily_loss_limit_usd",
    label: "Daily Loss Limit (DLL)",
    sector: "RISK_DRAWDOWN",
    tooltip: "Límite diario de pérdida.",
    format: (acc) => {
      if (acc.daily_loss_limit_type === "NONE") {
        return <span style={{ color: "#4ade80", fontWeight: 800 }}>Sin DLL (Libre)</span>;
      }
      if (acc.daily_loss_limit_type === "SOFT_BREACH") {
        return <span style={{ color: "#fbbf24", fontFamily: "var(--font-mono, monospace)", fontWeight: 700 }}>${acc.daily_loss_limit_usd} (Soft Lock)</span>;
      }
      return <span style={{ color: "#fb7185", fontFamily: "var(--font-mono, monospace)", fontWeight: 800 }}>${acc.daily_loss_limit_usd} (HARD BREACH 💀)</span>;
    },
    getRawValue: (acc) => acc.daily_loss_limit_type,
    evaluateSemaphore: (acc) => (acc.daily_loss_limit_type === "NONE" ? "GREEN" : acc.daily_loss_limit_type === "SOFT_BREACH" ? "YELLOW" : "RED"),
  },
  {
    id: "target_to_drawdown_ratio",
    label: "Ratio Target / Drawdown",
    sector: "RISK_DRAWDOWN",
    tooltip: "Dificultad: profit requerido por cada $1 de drawdown.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#f1f5f9" }}>{acc.target_to_drawdown_ratio.toFixed(2)}x</span>,
    getRawValue: (acc) => acc.target_to_drawdown_ratio,
    evaluateSemaphore: (acc) => (acc.target_to_drawdown_ratio <= 1.2 ? "GREEN" : acc.target_to_drawdown_ratio <= 1.6 ? "YELLOW" : "RED"),
  },

  // SECTOR 4: RETIROS & EXTRACCIÓN
  {
    id: "profit_target_usd",
    label: "Profit Target ($ y %)",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Objetivo de ganancia para aprobar la evaluación.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#ffffff" }}>${acc.profit_target_usd.toLocaleString()} ({acc.profit_target_pct}%)</span>,
    getRawValue: (acc) => acc.profit_target_usd,
  },
  {
    id: "min_trading_days_eval",
    label: "Días Mínimos en Examen",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Días de operativa obligatorios antes de aprobar.",
    format: (acc) => (
      acc.min_trading_days_eval === 0 ? (
        <span style={{ color: "#4ade80", fontWeight: 800 }}>0 días (Pase Día 1)</span>
      ) : (
        <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>{acc.min_trading_days_eval} días</span>
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
        <span style={{ color: "#4ade80", fontWeight: 800 }}>Día 1 (Inmediato)</span>
      ) : (
        <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>{acc.min_trading_days_payout} días</span>
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
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#fbbf24" }}>${acc.safety_buffer_usd.toLocaleString()} USD</span>,
    getRawValue: (acc) => acc.safety_buffer_usd,
  },
  {
    id: "capital_required_first_payout_1k",
    label: "Capital para 1er Retiro ($1K)",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Target + Safety Buffer + $1,000 netos: El esfuerzo real.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 900, color: "#38bdf8" }}>${acc.capital_required_first_payout_1k.toLocaleString()} USD</span>,
    getRawValue: (acc) => acc.capital_required_first_payout_1k,
    evaluateSemaphore: (acc) => (acc.capital_required_first_payout_1k <= 5500 ? "GREEN" : acc.capital_required_first_payout_1k <= 6500 ? "YELLOW" : "RED"),
  },
  {
    id: "payout_frequency",
    label: "Frecuencia de Retiro",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Rapidez y periodicidad de transferencias.",
    format: (acc) => <span style={{ color: "#38bdf8", fontWeight: 800 }}>{acc.payout_frequency_label}</span>,
    getRawValue: (acc) => acc.payout_frequency,
    evaluateSemaphore: (acc) => (acc.payout_frequency === "DAY_1_ON_DEMAND" || acc.payout_frequency === "SAME_DAY_BUSINESS" || acc.payout_frequency === "EVERY_3_DAYS" ? "GREEN" : acc.payout_frequency === "WEEKLY" ? "YELLOW" : "RED"),
  },
  {
    id: "payout_split_tier_1",
    label: "Profit Split Tier 1",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Porcentaje de ganancia asignado al trader.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#4ade80" }}>{acc.payout_split_tier_1}</span>,
    getRawValue: (acc) => acc.payout_split_tier_1,
  },
  {
    id: "payout_split_tier_2",
    label: "Profit Split Tier 2",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Reparto posterior a largo plazo.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>{acc.payout_split_tier_2}</span>,
    getRawValue: (acc) => acc.payout_split_tier_2,
  },
  {
    id: "payout_first_3m_cap_usd",
    label: "Tope Máximo Primeros 3 Meses",
    sector: "PAYOUTS_EXTRACTION",
    tooltip: "Límite máximo permitido de extracción.",
    format: (acc) => (
      acc.payout_first_3m_cap_usd === 0 ? (
        <span style={{ color: "#4ade80", fontWeight: 800 }}>Sin Límite ($0 Tope)</span>
      ) : (
        <span style={{ color: "#fb7185", fontFamily: "var(--font-mono, monospace)", fontWeight: 800 }}>${acc.payout_first_3m_cap_usd} máx</span>
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
      <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#f1f5f9" }}>
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
        <span style={{ color: "#fb7185", fontWeight: 700 }}>Obligatorio (Restringido)</span>
      ) : (
        <span style={{ color: "#4ade80", fontWeight: 800 }}>Libre desde el Día 1</span>
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
        <span style={{ color: "#4ade80", fontWeight: 800 }}>Sin Regla (0%)</span>
      ) : (
        <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#fbbf24", fontWeight: 700 }}>{acc.consistency_rule_pct}% Máximo</span>
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
        <span style={{ color: "#fb7185", fontWeight: 700 }}>Sí (Mín 10s en 50%+ trades)</span>
      ) : (
        <span style={{ color: "#4ade80", fontWeight: 800 }}>Sin Restricción de Tiempo</span>
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
        <span style={{ color: "#fb7185", fontWeight: 700 }}>Prohibido (±2 min)</span>
      ) : (
        <span style={{ color: "#4ade80", fontWeight: 800 }}>100% Permitido Operar Noticias</span>
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
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>{acc.session_close_mandatory_time}</span>,
    getRawValue: (acc) => acc.session_close_mandatory_time,
  },
  {
    id: "bot_policy",
    label: "Política de Bots & EAs",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Permisividad para sistemas automatizados.",
    format: (acc) => {
      if (acc.bot_policy === "ALLOWED_100") {
        return <span style={{ color: "#4ade80", fontWeight: 800 }}>✅ 100% EAs/VPS</span>;
      }
      if (acc.bot_policy === "PROHIBITED") {
        return <span style={{ color: "#fb7185", fontWeight: 900 }}>❌ 100% PROHIBIDO</span>;
      }
      return <span style={{ color: "#fbbf24", fontWeight: 700 }}>⚠️ Restringido (Local)</span>;
    },
    getRawValue: (acc) => acc.bot_policy,
    evaluateSemaphore: (acc) => (acc.bot_policy === "ALLOWED_100" ? "GREEN" : acc.bot_policy === "ALLOWED_LOCAL_ONLY" ? "YELLOW" : "RED"),
  },
  {
    id: "data_gateway",
    label: "Pasarela de Datos CME",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Proveedor de enrutamiento.",
    format: (acc) => <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#38bdf8" }}>{acc.data_gateway}</span>,
    getRawValue: (acc) => acc.data_gateway,
  },
  {
    id: "platforms_supported",
    label: "Plataformas Soportadas",
    sector: "MICROSTRUCTURE_RULES",
    tooltip: "Software compatible.",
    format: (acc) => (
      <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
        {acc.platforms_supported.map((p) => (
          <span key={p} style={{ background: "#06090e", color: "#cbd5e1", padding: "1px 5px", borderRadius: "3px", fontSize: "9.5px", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
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
  const [searchQuery, setSearchQuery] = useState<string>("" );

  // Cuentas seleccionadas (de 2 a 6)
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

  const analysisReport = useMemo(() => {
    return generateCriticalDifferencesReport(selectedAccounts);
  }, [selectedAccounts]);

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
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
      {/* 1. PANEL SUPERIOR */}
      <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", padding: "20px", display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
          <div>
            <h2 style={{ fontSize: "17px", fontWeight: 900, color: "#ffffff", margin: 0 }}>
              ⚖️ Mega-Comparador Multi-Cuenta ({ALL_PROP_FIRM_ACCOUNTS.length} Cuentas · 36 Columnas)
            </h2>
            <p style={{ fontSize: "11.5px", color: "#94a3b8", margin: "2px 0 0 0" }}>
              Compara de 2 a 6 cuentas de cualquier firma y tamaño con botones directos de compra, semáforo inteligente y auditoría forense.
            </p>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <select
              value={firmFilter}
              onChange={(e) => setFirmFilter(e.target.value)}
              style={{ background: "#06090e", color: "#ffffff", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "6px 10px", fontSize: "11.5px", fontWeight: 700 }}
            >
              <option value="ALL">Todas las Firmas ({uniqueFirms.length})</option>
              {uniqueFirms.map(([slug, name]) => (
                <option key={slug} value={slug}>{name}</option>
              ))}
            </select>

            <select
              value={sizeFilter}
              onChange={(e) => setSizeFilter(e.target.value === "ALL" ? "ALL" : (Number(e.target.value) as AccountSize))}
              style={{ background: "#06090e", color: "#ffffff", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "6px 10px", fontSize: "11.5px", fontWeight: 700 }}
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

        {/* Ranuras Seleccionadas */}
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(6, selectedAccounts.length + (selectedAccounts.length < 6 ? 1 : 0))}, 1fr)`, gap: "10px", borderTop: "1px solid rgba(148, 163, 184, 0.12)", paddingTop: "14px" }}>
          {selectedAccounts.map((acc, idx) => (
            <div key={acc.id} style={{ background: "#06090e", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "10px", padding: "10px", position: "relative", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
              <button
                onClick={() => handleRemoveSlot(acc.id)}
                disabled={selectedAccounts.length <= 2}
                style={{ position: "absolute", top: "6px", right: "6px", background: "transparent", border: "none", color: "#64748b", cursor: "pointer" }}
                title="Eliminar de la comparativa"
              >
                <X size={12} />
              </button>
              <div>
                <div style={{ fontSize: "9.5px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase" }}>
                  Ranura {idx + 1} · {acc.firm_name}
                </div>
                <div style={{ fontSize: "12px", fontWeight: 800, color: "#ffffff", marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {acc.program_name}
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px", display: "flex", gap: "6px" }}>
                  <span style={{ fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#fff" }}>${(acc.account_size_usd / 1000).toFixed(0)}K</span>
                  <span style={{ color: "#4ade80", fontWeight: 800 }}>${acc.exam_price_promo_usd.toFixed(0)}</span>
                </div>
              </div>
              <div style={{ marginTop: "8px" }}>
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
            <div style={{ background: "rgba(15, 23, 42, 0.4)", border: "1px dashed rgba(148, 163, 184, 0.3)", borderRadius: "10px", padding: "10px", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "10.5px", color: "#94a3b8" }}>+ Añadir Ranura ({selectedAccounts.length}/6)</span>
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddSlot(e.target.value);
                    e.target.value = "";
                  }
                }}
                style={{ width: "100%", background: "#06090e", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.4)", borderRadius: "6px", padding: "4px", fontSize: "10.5px", fontWeight: 700 }}
                defaultValue=""
              >
                <option value="" disabled>Seleccionar...</option>
                {availableAccounts.filter((a) => !selectedIds.includes(a.id)).map((acc) => (
                  <option key={acc.id} value={acc.id}>{acc.firm_name} — {acc.program_name} (${(acc.account_size_usd / 1000).toFixed(0)}K)</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* 2. TABLA MATRICIAL DE 36 COLUMNAS */}
      <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", overflowX: "auto", boxShadow: "0 8px 30px rgba(0,0,0,0.4)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11.5px", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "rgba(6, 9, 14, 0.98)", borderBottom: "1px solid rgba(148, 163, 184, 0.2)", position: "sticky", top: 0, zIndex: 10 }}>
              <th style={{ padding: "14px 16px", width: "260px", color: "#94a3b8", fontSize: "10.5px", fontWeight: 800, textTransform: "uppercase" }}>
                Atributo Técnico Forense (36 Columnas)
              </th>
              {selectedAccounts.map((acc) => (
                <th key={acc.id} style={{ padding: "14px", minWidth: "200px", borderLeft: "1px solid rgba(148, 163, 184, 0.12)" }}>
                  <div style={{ fontSize: "10px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase" }}>{acc.firm_name}</div>
                  <div style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff" }}>{acc.program_name}</div>
                  <div style={{ fontSize: "10.5px", color: "#94a3b8" }}>${(acc.account_size_usd / 1000).toFixed(0)}K · {acc.market_type}</div>
                  <div style={{ marginTop: "6px" }}>
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
          <tbody>
            {(["IDENTIFICATION", "COSTS_COUPONS", "RISK_DRAWDOWN", "PAYOUTS_EXTRACTION", "MICROSTRUCTURE_RULES"] as SectorKey[]).map((sectorKey) => {
              const sectorColumns = filteredColumns.filter((col) => col.sector === sectorKey);
              if (sectorColumns.length === 0) return null;
              const meta = SECTORS_META[sectorKey];
              const isExpanded = expandedSectors[sectorKey];

              return (
                <React.Fragment key={sectorKey}>
                  <tr
                    onClick={() => toggleSector(sectorKey)}
                    style={{ background: "rgba(6, 9, 14, 0.8)", borderTop: "1px solid rgba(148, 163, 184, 0.2)", borderBottom: "1px solid rgba(148, 163, 184, 0.15)", cursor: "pointer", userSelect: "none" }}
                  >
                    <td colSpan={selectedAccounts.length + 1} style={{ padding: "10px 16px", color: "#63e1b4", fontWeight: 900, fontSize: "11.5px", textTransform: "uppercase" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span>{meta.icon} {meta.title} ({sectorColumns.length} Atributos)</span>
                        <span>{isExpanded ? "▲" : "▼"}</span>
                      </div>
                    </td>
                  </tr>

                  {isExpanded && sectorColumns.map((col) => (
                    <tr key={col.id} style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.06)" }}>
                      <td style={{ padding: "10px 16px", color: "#cbd5e1" }}>
                        <div style={{ fontWeight: 700, color: "#ffffff" }}>{col.label}</div>
                        <div style={{ fontSize: "10px", color: "#64748b", lineHeight: "1.3" }}>{col.tooltip}</div>
                      </td>
                      {selectedAccounts.map((acc) => (
                        <td key={acc.id} style={{ padding: "10px 14px", borderLeft: "1px solid rgba(148, 163, 184, 0.08)", verticalAlign: "top" }}>
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
