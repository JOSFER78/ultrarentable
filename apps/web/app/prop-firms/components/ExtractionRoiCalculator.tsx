"use client";

import React, { useState, useMemo } from "react";
import { ALL_PROP_FIRM_ACCOUNTS } from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";
import { Calculator, Sparkles, ShieldCheck } from "lucide-react";

export function ExtractionRoiCalculator() {
  const [selectedSize, setSelectedSize] = useState<number>(50000);
  const [monthsToPass, setMonthsToPass] = useState<number>(1);
  const [targetCapital, setTargetCapital] = useState<number>(10000);

  const simulationResults = useMemo(() => {
    return ALL_PROP_FIRM_ACCOUNTS
      .filter((acc) => acc.account_size_usd === selectedSize)
      .map((acc) => {
        const examCost = acc.exam_price_promo_usd;
        const monthlyRecurrence = acc.monthly_renewal_usd;
        const recurringCost = monthsToPass > 1 ? (monthsToPass - 1) * monthlyRecurrence : 0;
        const activationFee = acc.activation_fee_usd;
        const totalInvested = examCost + recurringCost + activationFee;
        const safetyBuffer = acc.safety_buffer_usd;
        const netCashExtracted = Math.max(0, targetCapital - safetyBuffer);
        const netProfit = netCashExtracted - totalInvested;
        const trueRoiMultiple = totalInvested > 0 ? netCashExtracted / totalInvested : 0;
        const requiredGrossProfit = targetCapital + (acc.profit_target_usd * (monthsToPass > 1 ? 1 : 1));

        return {
          account: acc,
          examCost,
          recurringCost,
          activationFee,
          totalInvested,
          safetyBuffer,
          netCashExtracted,
          netProfit,
          trueRoiMultiple,
          requiredGrossProfit,
        };
      })
      .sort((a, b) => b.trueRoiMultiple - a.trueRoiMultiple);
  }, [selectedSize, monthsToPass, targetCapital]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
      {/* 1. CONTROLES DEL SIMULADOR */}
      <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", padding: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Calculator size={20} color="#63e1b4" />
            <h2 style={{ fontSize: "17px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
              Calculadora Cuantitativa de Coste Real de Extracción & ROI
            </h2>
          </div>
          <p style={{ fontSize: "11.5px", color: "#94a3b8", margin: "2px 0 0 0" }}>
            Modela el capital total desembolsado (Examen con Promo + Activación + Buffer) y el retorno neto real al extraer tus primeros ${targetCapital.toLocaleString()} USD.
          </p>
        </div>

        {/* Sliders */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px" }}>
          {/* Tamaño */}
          <div style={{ background: "#06090e", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "10px", padding: "12px" }}>
            <label style={{ fontSize: "10.5px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
              Tamaño de Cuenta
            </label>
            <select
              value={selectedSize}
              onChange={(e) => setSelectedSize(Number(e.target.value))}
              style={{ width: "100%", background: "#0b1018", color: "#ffffff", border: "1px solid rgba(148, 163, 184, 0.25)", borderRadius: "6px", padding: "6px 8px", fontSize: "12px", fontWeight: 700 }}
            >
              <option value={25000}>$25,000 USD (Micro)</option>
              <option value={50000}>$50,000 USD (Estándar)</option>
              <option value={100000}>$100,000 USD (Avanzado)</option>
              <option value={150000}>$150,000 USD (Master)</option>
            </select>
          </div>

          {/* Meses */}
          <div style={{ background: "#06090e", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "10px", padding: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", marginBottom: "6px" }}>
              <span>Tiempo Estimado:</span>
              <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>{monthsToPass} {monthsToPass === 1 ? "mes (1 Cuota)" : "meses"}</span>
            </div>
            <input
              type="range"
              min={1}
              max={4}
              value={monthsToPass}
              onChange={(e) => setMonthsToPass(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#38bdf8" }}
            />
          </div>

          {/* Beneficio Objetivo */}
          <div style={{ background: "#06090e", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "10px", padding: "12px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10.5px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase", marginBottom: "6px" }}>
              <span>Ganancia a Extraer:</span>
              <span style={{ color: "#63e1b4", fontFamily: "var(--font-mono, monospace)" }}>${targetCapital.toLocaleString()} USD</span>
            </div>
            <input
              type="range"
              min={2000}
              max={25000}
              step={1000}
              value={targetCapital}
              onChange={(e) => setTargetCapital(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#63e1b4" }}
            />
          </div>
        </div>
      </div>

      {/* 2. TABLA DE RESULTADOS DE ROI */}
      <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", overflowX: "auto", boxShadow: "0 8px 30px rgba(0,0,0,0.4)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "rgba(6, 9, 14, 0.95)", borderBottom: "1px solid rgba(148, 163, 184, 0.15)", color: "#94a3b8", fontSize: "10.5px", fontWeight: 800, textTransform: "uppercase" }}>
              <th style={{ padding: "12px 16px" }}># Ranking ROI</th>
              <th style={{ padding: "12px 14px" }}>Inversión Total ($TCO$)</th>
              <th style={{ padding: "12px 14px" }}>Buffer Retenido</th>
              <th style={{ padding: "12px 14px" }}>Extracción Neta Real</th>
              <th style={{ padding: "12px 14px", color: "#63e1b4", fontWeight: 900 }}>Múltiplo ROI Cuantitativo</th>
              <th style={{ padding: "12px 14px" }}>Retiros</th>
              <th style={{ padding: "12px 16px", textAlign: "right" }}>Comprar con Oferta</th>
            </tr>
          </thead>
          <tbody>
            {simulationResults.map((item, idx) => (
              <tr key={item.account.id} style={{ borderBottom: "1px solid rgba(148, 163, 184, 0.08)" }}>
                <td style={{ padding: "12px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontWeight: 900, color: idx === 0 ? "#63e1b4" : "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                      #{idx + 1}
                    </span>
                    <div>
                      <div style={{ color: "#ffffff", fontWeight: 800 }}>{item.account.firm_name}</div>
                      <div style={{ color: "#38bdf8", fontSize: "11px" }}>{item.account.program_name}</div>
                    </div>
                  </div>
                </td>

                <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#ffffff" }}>
                  ${item.totalInvested.toFixed(2)} USD
                </td>

                <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", color: "#fbbf24" }}>
                  ${item.safetyBuffer.toLocaleString()} USD
                </td>

                <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", fontWeight: 800, color: "#4ade80" }}>
                  ${item.netCashExtracted.toLocaleString()} USD
                </td>

                <td style={{ padding: "12px 14px", fontFamily: "var(--font-mono, monospace)", fontWeight: 900, fontSize: "14px", color: idx === 0 ? "#63e1b4" : "#ffffff" }}>
                  {item.trueRoiMultiple.toFixed(1)}x
                </td>

                <td style={{ padding: "12px 14px", fontSize: "11px", color: "#94a3b8" }}>
                  {item.account.payout_frequency_label}
                </td>

                <td style={{ padding: "12px 16px", textAlign: "right" }}>
                  <BuyButtonWithCoupon
                    affiliateUrl={item.account.affiliate_url}
                    couponCode={item.account.active_coupon_code}
                    discountPercent={item.account.discount_percentage}
                    variant="table-row"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
