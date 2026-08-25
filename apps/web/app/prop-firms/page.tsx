"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Sparkles,
  BarChart3,
  Scale,
  Flame,
  HelpCircle,
  Calculator,
  BookOpen,
  Wifi,
  Bot,
  Check,
  Copy,
  ExternalLink,
  ShieldCheck,
  Zap,
  Filter,
} from "lucide-react";

import { AISyncStatusBar } from "./components/AISyncStatusBar";
import { MegaComparator } from "./components/MegaComparator";
import { LiveDealsTracker } from "./components/LiveDealsTracker";
import { ExtractionRoiCalculator } from "./components/ExtractionRoiCalculator";
import { BuyButtonWithCoupon } from "./components/BuyButtonWithCoupon";
import { ALL_PROP_FIRM_ACCOUNTS, LIVE_COUPONS_DATABASE } from "@/lib/prop-firms";

type ModuleTab =
  | "CATALOGO_50K"
  | "COMPARADOR"
  | "OFERTAS_LIVE"
  | "FIND_PERFECT"
  | "CALCULADORA_ROI"
  | "ENCICLOPEDIA"
  | "GUIAS_CME"
  | "ULTRABOT_AI";

export default function PropFirmsPage() {
  const [activeTab, setActiveTab] = useState<ModuleTab>("CATALOGO_50K");
  const [copiedCoupon, setCopiedCoupon] = useState<string | null>(null);

  // Filtros del Catálogo
  const [catalogFirmFilter, setCatalogFirmFilter] = useState<string>("ALL");
  const [catalogSizeFilter, setCatalogSizeFilter] = useState<number | "ALL">("ALL");
  const [catalogDrawdownFilter, setCatalogDrawdownFilter] = useState<string>("ALL");
  const [catalogZeroFeeOnly, setCatalogZeroFeeOnly] = useState<boolean>(false);
  const [catalogSearch, setCatalogSearch] = useState<string>("");

  // Asistente 'Find My Perfect Account'
  const [wizardBotPref, setWizardBotPref] = useState<"BOTS" | "MANUAL" | "BOTH">("BOTS");
  const [wizardDdPref, setWizardDdPref] = useState<"STATIC" | "EOD" | "ANY">("EOD");
  const [wizardBudget, setWizardBudget] = useState<number>(120);

  // Enciclopedia y Guías
  const [selectedWikiFirm, setSelectedWikiFirm] = useState<string>("topstep");
  const [selectedGuideId, setSelectedGuideId] = useState<string>("rithmic-nt8");

  // Chatbot UltraBot
  const [chatMessages, setChatMessages] = useState<Array<{ role: "user" | "assistant"; text: string }>>([
    {
      role: "assistant",
      text: "¡Hola! Soy **UltraBot AI**, tu asistente cuantitativo de prop firms de futuros CME. Conozco todas las reglas, trampas de trailing drawdown, cupones activos y políticas de retiros de las 17 firmas con más de 65 cuentas indexadas. ¿Qué estrategia o activo deseas operar?",
    },
  ]);
  const [chatInput, setChatInput] = useState<string>("");
  const [isAiReplying, setIsAiReplying] = useState<boolean>(false);

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCoupon(code);
    setTimeout(() => setCopiedCoupon(null), 2500);
  };

  const handleSendChat = async () => {
    if (!chatInput.trim()) return;
    const userMsg = chatInput.trim();
    setChatMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setChatInput("");
    setIsAiReplying(true);

    try {
      const res = await fetch("/api/v1/providers/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
      } else {
        setTimeout(() => {
          let replyText = "";
          const lower = userMsg.toLowerCase();
          if (lower.includes("bot") || lower.includes("ea") || lower.includes("automatizado")) {
            replyText = "🤖 **Análisis de Bots & EAs:**\n\n• **Recomendadas 100%:** **MyFundedFutures (Rapid)**, **Tradeify (Growth)** y **BluSky (Static)** permiten EAs y bots en VPS sin restricciones.\n• ⚠️ **Advertencia:** **Tradeify** y **Elite Trader Funding** exigen que el 50%+ de los trades duren más de 10s en cuenta fondeada.\n• ❌ **PROHIBIDO:** **Apex Trader Funding** y **TickTick Trader** prohíben terminantemente bots en cuenta PA/Fondeada (solo trading manual).";
          } else if (lower.includes("drawdown") || lower.includes("eod") || lower.includes("estatico")) {
            replyText = "🛡️ **Comparativa de Drawdown:**\n\n• **Estático Puro:** **BluSky Static Growth** (el suelo nunca sube, $1,500 de DD fijo) y **UProfit ONE 50K**.\n• **EOD Trailing:** **MFFU Rapid**, **Tradeify Growth** y **TradeDay Fast Pass** (se calcula al cierre 15:50 CT, los picos flotantes intradía no te perjudican).\n• **Intraday Peak (Peligroso):** **Apex Full** y **Bulenox Opción 1** (persiguen la ganancia flotante en tiempo real).";
          } else if (lower.includes("barato") || lower.includes("precio") || lower.includes("cupon") || lower.includes("oferta")) {
            replyText = "💰 **Mejores Ofertas y Coste Real (TCO):**\n\n• **Menor Coste Total:** **TradeDay Fast Pass 50K** ($49 USD con `FLASH55` + $0 activación).\n• **Tradeify Growth 50K:** $58.20 USD con `TNT` (Pago único + $0 activación).\n• **MFFU Rapid 50K:** $78.50 USD con `300K` ($0 activación y payouts en 24h).\n• ⚠️ *Cuidado con Bulenox 90% ($17.50):* cobra $148 USD de cuota de activación al aprobar.";
          } else {
            replyText = `📊 **Dictamen de UltraBot AI:**\n\nPara cuentas estándar de $50K, la combinación más eficiente en costes y flexibilidad es **MyFundedFutures Rapid** ($78.50 con cupón \`300K\`, $0 activación, EOD Trailing y payouts en 24h) o **Tradeify Growth** ($58.20 con cupón \`TNT\`). Si buscas Drawdown 100% Estático, tu mejor opción es **BluSky Static** ($101.25 con \`BLU25\`).`;
          }
          setChatMessages((prev) => [...prev, { role: "assistant", text: replyText }]);
        }, 800);
      }
    } catch {
      setTimeout(() => {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "He consultado la base de datos de las 17 firmas de futuros CME con más de 65 cuentas catalogadas. MFFU Rapid, Tradeify Growth y BluSky Static presentan el menor coste de extracción ($0 cuota de activación y modelo EOD/Estático).",
          },
        ]);
      }, 500);
    } finally {
      setIsAiReplying(false);
    }
  };

  const uniqueFirms = useMemo(() => {
    const map = new Map<string, string>();
    ALL_PROP_FIRM_ACCOUNTS.forEach((a) => map.set(a.firm_slug, a.firm_name));
    return Array.from(map.entries());
  }, []);

  const filteredCatalogAccounts = useMemo(() => {
    return ALL_PROP_FIRM_ACCOUNTS.filter((acc) => {
      if (catalogFirmFilter !== "ALL" && acc.firm_slug !== catalogFirmFilter) return false;
      if (catalogSizeFilter !== "ALL" && acc.account_size_usd !== catalogSizeFilter) return false;
      if (catalogDrawdownFilter !== "ALL" && acc.drawdown_type !== catalogDrawdownFilter) return false;
      if (catalogZeroFeeOnly && acc.activation_fee_usd !== 0) return false;
      if (catalogSearch.trim()) {
        const q = catalogSearch.toLowerCase();
        const matchesFirm = acc.firm_name.toLowerCase().includes(q);
        const matchesProgram = acc.program_name.toLowerCase().includes(q);
        const matchesCoupon = acc.active_coupon_code.toLowerCase().includes(q);
        if (!matchesFirm && !matchesProgram && !matchesCoupon) return false;
      }
      return true;
    });
  }, [catalogFirmFilter, catalogSizeFilter, catalogDrawdownFilter, catalogZeroFeeOnly, catalogSearch]);

  const navTabs = [
    { id: "CATALOGO_50K", label: `1. Mega-Catálogo (${ALL_PROP_FIRM_ACCOUNTS.length} Cuentas)`, icon: "📊" },
    { id: "COMPARADOR", label: "2. Mega-Comparador (36 Cols)", icon: "⚖️" },
    { id: "OFERTAS_LIVE", label: `3. Cupones & Ofertas (${LIVE_COUPONS_DATABASE.length})`, icon: "🔥" },
    { id: "FIND_PERFECT", label: "4. Find My Perfect Firm", icon: "🎯" },
    { id: "CALCULADORA_ROI", label: "5. Calculadora Coste & ROI", icon: "🧮" },
    { id: "ENCICLOPEDIA", label: "6. Enciclopedia (17 Firmas)", icon: "📚" },
    { id: "GUIAS_CME", label: "7. Guías de Conexión", icon: "⚡" },
    { id: "ULTRABOT_AI", label: "8. UltraBot AI RAG", icon: "🤖" },
  ];

  return (
    <div style={{ padding: "16px 24px", width: "100%", maxWidth: "100%", margin: 0, color: "#f8fafc", boxSizing: "border-box", fontFamily: "Inter, sans-serif" }}>
      {/* 1. CABECERA PRINCIPAL */}
      <div style={{ marginBottom: "20px", borderBottom: "1px solid rgba(148, 163, 184, 0.12)", paddingBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
          <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 8px", borderRadius: "20px", background: "rgba(99, 225, 180, 0.12)", color: "#63e1b4", border: "1px solid rgba(99, 225, 180, 0.25)", fontFamily: "var(--font-mono, monospace)" }}>
            CME FUTURES HUB V3.6
          </span>
          <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 8px", borderRadius: "20px", background: "rgba(56, 189, 248, 0.12)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.25)", fontFamily: "var(--font-mono, monospace)" }}>
            17 FIRMAS · {ALL_PROP_FIRM_ACCOUNTS.length} CUENTAS INDEXADAS
          </span>
        </div>

        <h1 style={{ fontSize: "24px", fontWeight: 900, color: "#ffffff", letterSpacing: "-0.5px", margin: "4px 0" }}>
          🏛️ Plataforma Mundial de Fondeo & Futuros CME
        </h1>
        <p style={{ fontSize: "12.5px", color: "#94a3b8", margin: 0, maxWidth: "900px", lineHeight: "1.5" }}>
          Catálogo exhaustivo de todos los programas y tiers ($9K a $300K), auditoría forense de letra pequeña, cálculo cuantitativo de costes reales de extracción (Precio Neto + Activación + Buffer) y enlaces directos de compra con cupones en vivo.
        </p>
      </div>

      {/* 2. BARRA DE SINCRONIZACIÓN CON IA */}
      <AISyncStatusBar />

      {/* 3. PESTAÑAS DE NAVEGACIÓN MODULARES */}
      <div style={{ display: "flex", gap: "6px", overflowX: "auto", paddingBottom: "12px", marginBottom: "20px", borderBottom: "1px solid rgba(148, 163, 184, 0.12)" }}>
        {navTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as ModuleTab)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "8px 14px",
                borderRadius: "9px",
                fontSize: "12px",
                fontWeight: isActive ? 800 : 600,
                whiteSpace: "nowrap",
                cursor: "pointer",
                border: isActive ? "1px solid #63e1b4" : "1px solid rgba(148, 163, 184, 0.15)",
                background: isActive ? "#63e1b4" : "rgba(15, 23, 42, 0.7)",
                color: isActive ? "#06090e" : "#cbd5e1",
                boxShadow: isActive ? "0 2px 10px rgba(99, 225, 180, 0.25)" : "none",
                transition: "all 0.12s ease",
              }}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 1: MEGA-CATÁLOGO MULTI-PROGRAMA CON TODOS LOS TIERS */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "CATALOGO_50K" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Card del Catálogo */}
          <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", overflow: "hidden", boxShadow: "0 8px 30px rgba(0,0,0,0.4)" }}>
            {/* Barra de Filtros */}
            <div style={{ padding: "16px 20px", background: "rgba(6, 9, 14, 0.85)", borderBottom: "1px solid rgba(148, 163, 184, 0.12)", display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "12px" }}>
              <div>
                <div style={{ fontSize: "13px", fontWeight: 800, color: "#ffffff", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>📊</span> Mega-Catálogo de Cuentas & Retos CME ({filteredCatalogAccounts.length} de {ALL_PROP_FIRM_ACCOUNTS.length} Cuentas)
                </div>
                <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                  Todos los tiers individuales con precios de examen, cuota de activación, TCO y enlaces de compra directa.
                </div>
              </div>

              {/* Controles de Filtro */}
              <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px" }}>
                {/* Filtro Empresa */}
                <select
                  value={catalogFirmFilter}
                  onChange={(e) => setCatalogFirmFilter(e.target.value)}
                  style={{ background: "#0b1018", color: "#f1f5f9", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "6px 10px", fontSize: "11.5px", fontWeight: 700, outline: "none", cursor: "pointer" }}
                >
                  <option value="ALL">Todas las Firmas ({uniqueFirms.length})</option>
                  {uniqueFirms.map(([slug, name]) => (
                    <option key={slug} value={slug}>{name}</option>
                  ))}
                </select>

                {/* Filtro Tamaño */}
                <select
                  value={catalogSizeFilter}
                  onChange={(e) => setCatalogSizeFilter(e.target.value === "ALL" ? "ALL" : Number(e.target.value))}
                  style={{ background: "#0b1018", color: "#f1f5f9", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "6px 10px", fontSize: "11.5px", fontWeight: 700, outline: "none", cursor: "pointer" }}
                >
                  <option value="ALL">Todos los Tamaños ($9K - $300K)</option>
                  <option value={9000}>$9,000 USD (Micro)</option>
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

                {/* Filtro Drawdown */}
                <select
                  value={catalogDrawdownFilter}
                  onChange={(e) => setCatalogDrawdownFilter(e.target.value)}
                  style={{ background: "#0b1018", color: "#f1f5f9", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "6px 10px", fontSize: "11.5px", fontWeight: 700, outline: "none", cursor: "pointer" }}
                >
                  <option value="ALL">Todo Tipo Drawdown</option>
                  <option value="STATIC">🛡️ 100% Estático Fijo</option>
                  <option value="EOD_TRAILING">📊 End of Day (EOD)</option>
                  <option value="INTRADAY_TRAILING">⚡ Intraday Trailing Peak</option>
                </select>

                {/* Toggle $0 Activación */}
                <button
                  onClick={() => setCatalogZeroFeeOnly(!catalogZeroFeeOnly)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "5px",
                    padding: "6px 10px",
                    borderRadius: "8px",
                    fontSize: "11.5px",
                    fontWeight: 800,
                    cursor: "pointer",
                    background: catalogZeroFeeOnly ? "rgba(99, 225, 180, 0.18)" : "#0b1018",
                    color: catalogZeroFeeOnly ? "#63e1b4" : "#94a3b8",
                    border: catalogZeroFeeOnly ? "1px solid #63e1b4" : "1px solid rgba(148, 163, 184, 0.2)",
                  }}
                >
                  <ShieldCheck size={13} />
                  <span>$0 Activación</span>
                </button>

                {/* Buscador de Texto */}
                <input
                  type="text"
                  placeholder="Buscar cuenta o cupón..."
                  value={catalogSearch}
                  onChange={(e) => setCatalogSearch(e.target.value)}
                  style={{ background: "#0b1018", color: "#ffffff", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "6px 10px", fontSize: "11.5px", width: "160px", outline: "none" }}
                />
              </div>
            </div>

            {/* Tabla de Datos */}
            <div style={{ overflowX: "auto", width: "100%" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                <thead>
                  <tr style={{ background: "rgba(6, 9, 14, 0.95)", borderBottom: "1px solid rgba(148, 163, 184, 0.15)", color: "#94a3b8", fontSize: "10.5px", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                    <th style={{ padding: "12px 16px" }}># Firma & Programa</th>
                    <th style={{ padding: "12px 14px" }}>Tamaño Balance</th>
                    <th style={{ padding: "12px 14px" }}>Precio Promo</th>
                    <th style={{ padding: "12px 14px" }}>Cuota Activación</th>
                    <th style={{ padding: "12px 14px", color: "#ffffff", fontWeight: 900 }}>Coste Total Pase (TCO)</th>
                    <th style={{ padding: "12px 14px" }}>Profit Target</th>
                    <th style={{ padding: "12px 14px" }}>Max Drawdown & Tipo</th>
                    <th style={{ padding: "12px 14px" }}>Bots / EAs</th>
                    <th style={{ padding: "12px 14px" }}>Retiros</th>
                    <th style={{ padding: "12px 16px", textAlign: "right" }}>Comprar con Cupón</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCatalogAccounts.map((acc, idx) => {
                    const isZeroFee = acc.activation_fee_usd === 0;
                    return (
                      <tr
                        key={acc.id}
                        style={{
                          borderBottom: "1px solid rgba(148, 163, 184, 0.08)",
                          background: idx % 2 === 0 ? "transparent" : "rgba(255, 255, 255, 0.015)",
                          transition: "background 0.12s ease",
                        }}
                      >
                        <td style={{ padding: "12px 16px" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ color: "#475569", fontFamily: "var(--font-mono, monospace)", fontSize: "10.5px", width: "16px" }}>
                              {idx + 1}.
                            </span>
                            <div>
                              <div style={{ color: "#ffffff", fontWeight: 800, fontSize: "12.5px" }}>{acc.firm_name}</div>
                              <div style={{ color: "#38bdf8", fontSize: "11px", fontWeight: 600 }}>{acc.program_name}</div>
                            </div>
                          </div>
                        </td>

                        <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#f1f5f9" }}>
                          ${(acc.account_size_usd / 1000).toFixed(0)}K USD
                        </td>

                        <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", fontWeight: 900, color: "#4ade80", fontSize: "12.5px" }}>
                          ${acc.exam_price_promo_usd.toFixed(2)}
                        </td>

                        <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)" }}>
                          {isZeroFee ? (
                            <span style={{ padding: "2px 6px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", fontWeight: 800, fontSize: "10.5px" }}>
                              $0 USD (GRATIS)
                            </span>
                          ) : (
                            <span style={{ padding: "2px 6px", borderRadius: "4px", background: "rgba(244, 63, 94, 0.15)", color: "#fb7185", fontWeight: 800, fontSize: "10.5px" }}>
                              ${acc.activation_fee_usd} USD
                            </span>
                          )}
                        </td>

                        <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", fontWeight: 900, color: "#ffffff", fontSize: "12.5px", background: "rgba(0,0,0,0.2)" }}>
                          ${acc.total_pass_cost_usd.toFixed(2)} USD
                        </td>

                        <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>
                          ${acc.profit_target_usd.toLocaleString()} ({acc.profit_target_pct}%)
                        </td>

                        <td style={{ padding: "12px 14px" }}>
                          <span style={{
                            fontWeight: 800,
                            fontFamily: "var(--font-mono, monospace)",
                            fontSize: "11px",
                            color: acc.drawdown_type === "STATIC" ? "#4ade80" : (acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL") ? "#38bdf8" : "#fb7185"
                          }}>
                            ${acc.max_drawdown_usd.toLocaleString()} [{acc.drawdown_type === "STATIC" ? "Estático" : (acc.drawdown_type === "EOD_TRAILING" || acc.drawdown_type === "LOCKED_INITIAL") ? "EOD" : "Intraday"}]
                          </span>
                        </td>

                        <td style={{ padding: "12px 14px", fontSize: "11px", fontWeight: 700 }}>
                          {acc.bot_policy === "ALLOWED_100" ? (
                            <span style={{ color: "#4ade80" }}>✅ 100% EAs/VPS</span>
                          ) : acc.bot_policy === "PROHIBITED" ? (
                            <span style={{ color: "#fb7185" }}>❌ Prohibido</span>
                          ) : (
                            <span style={{ color: "#fbbf24" }}>⚠️ Restringido</span>
                          )}
                        </td>

                        <td style={{ padding: "12px 14px", fontSize: "11px", color: "#94a3b8" }}>
                          {acc.payout_frequency_label}
                        </td>

                        <td style={{ padding: "12px 16px", textAlign: "right" }}>
                          <BuyButtonWithCoupon
                            affiliateUrl={acc.affiliate_url}
                            couponCode={acc.active_coupon_code}
                            discountPercent={acc.discount_percentage}
                            variant="table-row"
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 2: MEGA-COMPARADOR MULTI-CUENTA (36 COLUMNAS) */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "COMPARADOR" && (
        <div>
          <MegaComparator />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 3: CUPONES & OFERTAS VIVAS */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "OFERTAS_LIVE" && (
        <div>
          <LiveDealsTracker />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 4: FIND MY PERFECT FIRM */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "FIND_PERFECT" && (
        <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", padding: "24px", maxWidth: "800px", margin: "0 auto" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 800, color: "#ffffff", marginBottom: "4px" }}>
            🎯 Asistente Cuantitativo: Encuentra tu Cuenta Ideal
          </h2>
          <p style={{ fontSize: "12px", color: "#94a3b8", marginBottom: "20px" }}>
            Responde 3 preguntas técnicas y el algoritmo filtrará entre las {ALL_PROP_FIRM_ACCOUNTS.length} cuentas catalogadas la matemáticamente óptima para tu estilo.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* P1 */}
            <div>
              <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                1. ¿Utilizas Bots, EAs algorítmicos o Webhooks automatizados?
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
                {[
                  { id: "BOTS", label: "🤖 Sí, 100% Bots/EAs" },
                  { id: "MANUAL", label: "🖐️ No, Manual" },
                  { id: "BOTH", label: "⚖️ Ambos / Híbrido" },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setWizardBotPref(opt.id as any)}
                    style={{
                      padding: "10px",
                      borderRadius: "8px",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      background: wizardBotPref === opt.id ? "rgba(99, 225, 180, 0.18)" : "#06090e",
                      color: wizardBotPref === opt.id ? "#63e1b4" : "#94a3b8",
                      border: wizardBotPref === opt.id ? "1px solid #63e1b4" : "1px solid rgba(148, 163, 184, 0.15)",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* P2 */}
            <div>
              <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
                2. ¿Qué modelo de Drawdown prefieres para tu gestión de riesgo?
              </label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "8px" }}>
                {[
                  { id: "EOD", label: "📊 End of Day (EOD)" },
                  { id: "STATIC", label: "🛡️ Estático Puro (Fijo)" },
                  { id: "ANY", label: "⚡ Indiferente" },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setWizardDdPref(opt.id as any)}
                    style={{
                      padding: "10px",
                      borderRadius: "8px",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      background: wizardDdPref === opt.id ? "rgba(56, 189, 248, 0.18)" : "#06090e",
                      color: wizardDdPref === opt.id ? "#38bdf8" : "#94a3b8",
                      border: wizardDdPref === opt.id ? "1px solid #38bdf8" : "1px solid rgba(148, 163, 184, 0.15)",
                    }}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* P3 */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", marginBottom: "6px" }}>
                <span>3. Presupuesto Máximo de Entrada (Total Pase TCO):</span>
                <span style={{ color: "#63e1b4", fontFamily: "var(--font-mono, monospace)", fontSize: "13px" }}>${wizardBudget} USD</span>
              </div>
              <input
                type="range"
                min={30}
                max={300}
                step={10}
                value={wizardBudget}
                onChange={(e) => setWizardBudget(Number(e.target.value))}
                style={{ width: "100%", accentColor: "#63e1b4", cursor: "pointer" }}
              />
            </div>

            {/* Recomendaciones */}
            <div style={{ marginTop: "12px", borderTop: "1px solid rgba(148, 163, 184, 0.15)", paddingTop: "16px" }}>
              <div style={{ fontSize: "11px", fontWeight: 800, color: "#63e1b4", textTransform: "uppercase", marginBottom: "12px" }}>
                ✨ Cuentas Recomendadas por el Algoritmo:
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px" }}>
                {ALL_PROP_FIRM_ACCOUNTS.filter((acc) => {
                  if (wizardBotPref === "BOTS" && acc.bot_policy === "PROHIBITED") return false;
                  if (wizardDdPref === "STATIC" && acc.drawdown_type !== "STATIC") return false;
                  if (wizardDdPref === "EOD" && acc.drawdown_type !== "EOD_TRAILING" && acc.drawdown_type !== "LOCKED_INITIAL") return false;
                  if (acc.total_pass_cost_usd > wizardBudget) return false;
                  return true;
                }).slice(0, 4).map((rec) => (
                  <div key={rec.id} style={{ background: "#06090e", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "10px", padding: "12px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase" }}>{rec.firm_name}</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "#ffffff", marginTop: "2px" }}>{rec.program_name}</div>
                      <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
                        Coste Total: <span style={{ color: "#4ade80", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>${rec.total_pass_cost_usd.toFixed(2)}</span> · Retiro: {rec.payout_frequency_label}
                      </div>
                    </div>
                    <div style={{ marginTop: "10px" }}>
                      <BuyButtonWithCoupon
                        affiliateUrl={rec.affiliate_url}
                        couponCode={rec.active_coupon_code}
                        discountPercent={rec.discount_percentage}
                        variant="compact"
                        buttonText={`Comprar con ${rec.active_coupon_code} ↗`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 5: CALCULADORA DE COSTE & ROI */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "CALCULADORA_ROI" && (
        <div>
          <ExtractionRoiCalculator />
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 6: ENCICLOPEDIA (17 FIRMAS) */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "ENCICLOPEDIA" && (
        <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: "16px" }}>
          {/* Lista de Firmas */}
          <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "12px", padding: "12px", display: "flex", flexDirection: "column", gap: "3px", maxHeight: "700px", overflowY: "auto" }}>
            <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#64748b", textTransform: "uppercase", padding: "4px 8px" }}>
              Firmas Auditadas (17)
            </div>
            {uniqueFirms.map(([slug, name]) => (
              <button
                key={slug}
                onClick={() => setSelectedWikiFirm(slug)}
                style={{
                  textAlign: "left",
                  padding: "7px 10px",
                  borderRadius: "7px",
                  fontSize: "11.5px",
                  fontWeight: selectedWikiFirm === slug ? 800 : 600,
                  cursor: "pointer",
                  background: selectedWikiFirm === slug ? "#63e1b4" : "transparent",
                  color: selectedWikiFirm === slug ? "#06090e" : "#cbd5e1",
                  border: "none",
                }}
              >
                {name}
              </button>
            ))}
          </div>

          {/* Ficha de la Firma */}
          <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "12px", padding: "20px" }}>
            {(() => {
              const accountsOfFirm = ALL_PROP_FIRM_ACCOUNTS.filter((a) => a.firm_slug === selectedWikiFirm);
              const first = accountsOfFirm[0] || ALL_PROP_FIRM_ACCOUNTS[0];
              return (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(148, 163, 184, 0.15)", paddingBottom: "12px" }}>
                    <div>
                      <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase" }}>Ficha Oficial</div>
                      <h2 style={{ fontSize: "20px", fontWeight: 900, color: "#ffffff", margin: "2px 0" }}>{first.firm_name}</h2>
                      <div style={{ fontSize: "11.5px", color: "#94a3b8" }}>
                        Plataformas: {first.platforms_supported.join(", ")} · Conexión: {first.data_gateway}
                      </div>
                    </div>
                    <div style={{ width: "220px" }}>
                      <BuyButtonWithCoupon
                        affiliateUrl={first.affiliate_url}
                        couponCode={first.active_coupon_code}
                        discountPercent={first.discount_percentage}
                        variant="compact"
                        buttonText={`🔥 Ver Oferta ${first.active_coupon_code} ↗`}
                      />
                    </div>
                  </div>

                  {/* Tarjetas de Cuentas */}
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "10px" }}>
                    {accountsOfFirm.map((acc) => (
                      <div key={acc.id} style={{ background: "#06090e", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "10px", padding: "12px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div>
                            <div style={{ fontSize: "13px", fontWeight: 800, color: "#ffffff" }}>{acc.program_name}</div>
                            <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 700, fontFamily: "var(--font-mono, monospace)" }}>
                              ${(acc.account_size_usd / 1000).toFixed(0)}K Balance
                            </div>
                          </div>
                          <span style={{ fontSize: "12px", fontWeight: 900, color: "#4ade80", fontFamily: "var(--font-mono, monospace)", background: "rgba(34, 197, 94, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
                            ${acc.exam_price_promo_usd.toFixed(2)}
                          </span>
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "6px", fontSize: "10.5px", color: "#94a3b8", margin: "8px 0", borderTop: "1px solid rgba(148, 163, 184, 0.1)", paddingTop: "6px" }}>
                          <div>Target: <b style={{ color: "#fff" }}>${acc.profit_target_usd.toLocaleString()}</b></div>
                          <div>Drawdown: <b style={{ color: "#fb7185" }}>${acc.max_drawdown_usd.toLocaleString()}</b></div>
                          <div>Activación: <b style={{ color: "#fff" }}>${acc.activation_fee_usd}</b></div>
                          <div>Contratos: <b style={{ color: "#fff" }}>{acc.max_contracts_minis} Minis</b></div>
                        </div>
                        <BuyButtonWithCoupon
                          affiliateUrl={acc.affiliate_url}
                          couponCode={acc.active_coupon_code}
                          discountPercent={acc.discount_percentage}
                          variant="compact"
                          buttonText="Comprar Cuenta ↗"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 7: GUÍAS DE CONEXIÓN */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "GUIAS_CME" && (
        <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", gap: "16px" }}>
          <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "12px", padding: "12px", display: "flex", flexDirection: "column", gap: "3px" }}>
            <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#64748b", textTransform: "uppercase", padding: "4px 8px" }}>
              Protocolos Técnicos CME
            </div>
            {[
              { id: "rithmic-nt8", title: "1. Rithmic ➔ NinjaTrader 8" },
              { id: "tradovate-tv", title: "2. Tradovate ➔ TradingView" },
              { id: "trade-copier", title: "3. Replicanto Copier 1:10" },
              { id: "topstepx-risk", title: "4. TopstepX Cloud & Risk" },
              { id: "vps-sqx", title: "5. Deploy VPS StrategyQuant X" },
              { id: "cme-data-agreements", title: "6. CME Market Data (L1 vs L2)" },
              { id: "payout-buffer", title: "7. Estrategia de Retiros 50/50" },
            ].map((g) => (
              <button
                key={g.id}
                onClick={() => setSelectedGuideId(g.id)}
                style={{
                  textAlign: "left",
                  padding: "7px 10px",
                  borderRadius: "7px",
                  fontSize: "11.5px",
                  fontWeight: selectedGuideId === g.id ? 800 : 600,
                  cursor: "pointer",
                  background: selectedGuideId === g.id ? "#63e1b4" : "transparent",
                  color: selectedGuideId === g.id ? "#06090e" : "#cbd5e1",
                  border: "none",
                }}
              >
                {g.title}
              </button>
            ))}
          </div>

          <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "12px", padding: "20px", fontSize: "12px", lineHeight: "1.6", color: "#cbd5e1" }}>
            {selectedGuideId === "rithmic-nt8" && (
              <div>
                <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#ffffff", marginBottom: "8px" }}>Configuración Multi-Provider Rithmic en NinjaTrader 8</h3>
                <p>Para conectar múltiples cuentas Rithmic simultáneas sin bloqueos de servidor (Error 10006):</p>
                <ol style={{ paddingLeft: "20px" }}>
                  <li>Abre <b>R|Trader Pro</b> e inicia sesión con las credenciales de tu prop firm.</li>
                  <li>Activa la casilla obligatoria <code style={{ color: "#38bdf8", fontWeight: 800 }}>Allow Plug-in: ON</code>.</li>
                  <li>En NinjaTrader 8, ve a <code style={{ color: "#fff" }}>Tools ➔ Options ➔ General</code> y marca <code style={{ color: "#38bdf8" }}>Multi-provider</code>.</li>
                  <li>En <code style={{ color: "#fff" }}>Connections ➔ Configure</code>, crea una conexión seleccionando <em>Rithmic for NinjaTrader (Plug-in Mode)</em> apuntando al host local <code>127.0.0.1</code>.</li>
                </ol>
              </div>
            )}
            {selectedGuideId !== "rithmic-nt8" && (
              <div>
                <h3 style={{ fontSize: "15px", fontWeight: 800, color: "#ffffff", marginBottom: "8px" }}>Protocolo Técnico CME</h3>
                <p>Guía de conectividad de baja latencia y gestión de riesgo en ejecución para prop firms de futuros.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {/* PESTAÑA 8: ULTRABOT AI RAG */}
      {/* ═══════════════════════════════════════════════════════════════════════ */}
      {activeTab === "ULTRABOT_AI" && (
        <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", padding: "20px", maxWidth: "850px", margin: "0 auto" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(148, 163, 184, 0.15)", paddingBottom: "12px", marginBottom: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ padding: "6px", borderRadius: "8px", background: "rgba(99, 225, 180, 0.15)", color: "#63e1b4" }}>
                <Bot size={18} />
              </div>
              <div>
                <h2 style={{ fontSize: "16px", fontWeight: 800, color: "#ffffff", margin: 0 }}>UltraBot AI RAG — Asistente de Prop Firms</h2>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Conectado con las {ALL_PROP_FIRM_ACCOUNTS.length} cuentas de las 17 firmas de futuros CME.</div>
              </div>
            </div>
            <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 8px", borderRadius: "10px", background: "rgba(34, 197, 94, 0.15)", color: "#4ade80" }}>
              ONLINE
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "400px", overflowY: "auto", padding: "12px", background: "#06090e", borderRadius: "10px", marginBottom: "12px" }}>
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  padding: "10px 14px",
                  borderRadius: "10px",
                  fontSize: "12px",
                  lineHeight: "1.5",
                  background: msg.role === "user" ? "rgba(56, 189, 248, 0.15)" : "#0b1018",
                  color: msg.role === "user" ? "#bae6fd" : "#f1f5f9",
                  border: msg.role === "user" ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid rgba(148, 163, 184, 0.12)",
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "85%",
                  whiteSpace: "pre-line",
                }}
              >
                <div style={{ fontSize: "9.5px", fontWeight: 800, color: "#64748b", textTransform: "uppercase", marginBottom: "2px" }}>
                  {msg.role === "user" ? "Tú" : "UltraBot AI"}
                </div>
                {msg.text}
              </div>
            ))}
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <input
              type="text"
              placeholder="Pregunta sobre trailing EOD, cuentas baratas, $0 activación, reglas de bots..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
              style={{ flex: 1, background: "#06090e", color: "#ffffff", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "8px", padding: "10px 14px", fontSize: "12px", outline: "none" }}
            />
            <button
              onClick={handleSendChat}
              disabled={isAiReplying || !chatInput.trim()}
              style={{ padding: "10px 18px", borderRadius: "8px", background: "#63e1b4", color: "#06090e", fontWeight: 800, fontSize: "12px", border: "none", cursor: "pointer" }}
            >
              Enviar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
