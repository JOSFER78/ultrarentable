"use client";

import React, { useState } from "react";
import { LIVE_COUPONS_DATABASE } from "@/lib/prop-firms";
import { BuyButtonWithCoupon } from "./BuyButtonWithCoupon";
import { ShieldCheck, Percent, Flame } from "lucide-react";

export function LiveDealsTracker() {
  const [filterType, setFilterType] = useState<"ALL" | "ZERO_FEE" | "HIGH_DISCOUNT">("ALL");

  const filteredDeals = LIVE_COUPONS_DATABASE.filter((deal) => {
    if (filterType === "ZERO_FEE") return deal.waivesActivationFee;
    if (filterType === "HIGH_DISCOUNT") return deal.discountPercent >= 50;
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
      {/* Cabecera & Filtros */}
      <div style={{ background: "rgba(11, 16, 24, 0.95)", border: "1px solid rgba(148, 163, 184, 0.15)", borderRadius: "14px", padding: "18px 20px", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Flame size={20} color="#f59e0b" />
            <h2 style={{ fontSize: "17px", fontWeight: 800, color: "#ffffff", margin: 0 }}>Rastreador de Ofertas & Cupones Flash en Vivo</h2>
          </div>
          <p style={{ fontSize: "11.5px", color: "#94a3b8", margin: "2px 0 0 0" }}>
            Códigos de descuento verificados diariamente con 1-Click Copy, enlaces directos de compra y cálculo de Coste Total de Adquisición (TCO).
          </p>
        </div>

        {/* Botones de Filtro */}
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            onClick={() => setFilterType("ALL")}
            style={{
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "11.5px",
              fontWeight: 800,
              cursor: "pointer",
              background: filterType === "ALL" ? "#63e1b4" : "#06090e",
              color: filterType === "ALL" ? "#06090e" : "#cbd5e1",
              border: filterType === "ALL" ? "1px solid #63e1b4" : "1px solid rgba(148, 163, 184, 0.2)",
            }}
          >
            Todos ({LIVE_COUPONS_DATABASE.length})
          </button>
          <button
            onClick={() => setFilterType("ZERO_FEE")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "11.5px",
              fontWeight: 800,
              cursor: "pointer",
              background: filterType === "ZERO_FEE" ? "#38bdf8" : "#06090e",
              color: filterType === "ZERO_FEE" ? "#06090e" : "#38bdf8",
              border: filterType === "ZERO_FEE" ? "1px solid #38bdf8" : "1px solid rgba(56, 189, 248, 0.3)",
            }}
          >
            <ShieldCheck size={13} />
            <span>$0 Activación</span>
          </button>
          <button
            onClick={() => setFilterType("HIGH_DISCOUNT")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "11.5px",
              fontWeight: 800,
              cursor: "pointer",
              background: filterType === "HIGH_DISCOUNT" ? "#f59e0b" : "#06090e",
              color: filterType === "HIGH_DISCOUNT" ? "#06090e" : "#f59e0b",
              border: filterType === "HIGH_DISCOUNT" ? "1px solid #f59e0b" : "1px solid rgba(245, 158, 11, 0.3)",
            }}
          >
            <Percent size={13} />
            <span>≥50% OFF</span>
          </button>
        </div>
      </div>

      {/* Grid de Ofertas */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px" }}>
        {filteredDeals.map((deal) => (
          <div
            key={deal.id}
            style={{
              background: "rgba(11, 16, 24, 0.95)",
              border: "1px solid rgba(148, 163, 184, 0.15)",
              borderRadius: "12px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div style={{ position: "absolute", top: 0, right: 0, background: "linear-gradient(135deg, #06b6d4, #0284c7)", color: "#06090e", fontWeight: 900, fontSize: "11px", padding: "3px 10px", borderBottomLeftRadius: "8px" }}>
              {deal.discountPercent}% OFF
            </div>

            <div>
              <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase" }}>{deal.firmName}</div>
              <div style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff", marginTop: "4px", paddingRight: "50px", lineHeight: "1.4" }}>
                {deal.highlightText}
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", margin: "10px 0" }}>
                {deal.waivesActivationFee && (
                  <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8" }}>
                    ✓ $0 Pass Fee
                  </span>
                )}
                <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "#06090e", color: "#94a3b8", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  {deal.recurrence === "LIFETIME_RECURRING" ? "Recurrente de por vida" : deal.recurrence === "ONE_TIME" ? "Pago Único" : "1ª Cuota"}
                </span>
                <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "#06090e", color: "#94a3b8", border: "1px solid rgba(148, 163, 184, 0.15)" }}>
                  {deal.applicableTiers}
                </span>
              </div>
            </div>

            <div style={{ marginTop: "12px", borderTop: "1px solid rgba(148, 163, 184, 0.1)", paddingTop: "12px" }}>
              <BuyButtonWithCoupon
                affiliateUrl={deal.affiliateUrl}
                couponCode={deal.code}
                discountPercent={deal.discountPercent}
                variant="primary"
                buttonText="🔥 Comprar con Oferta ↗"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
