"use client";

import React, { useState } from "react";
import { Copy, Check, ExternalLink } from "lucide-react";

interface BuyButtonWithCouponProps {
  affiliateUrl: string;
  couponCode: string;
  discountPercent?: number;
  buttonText?: string;
  variant?: "primary" | "compact" | "table-row";
}

export function BuyButtonWithCoupon({
  affiliateUrl,
  couponCode,
  discountPercent,
  buttonText,
  variant = "primary",
}: BuyButtonWithCouponProps) {
  const [copied, setCopied] = useState(false);

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(couponCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
    window.open(affiliateUrl, "_blank", "noopener,noreferrer");
  };

  const handleCopyOnly = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(couponCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  if (variant === "table-row") {
    return (
      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
        <button
          onClick={handleCopyOnly}
          title={`Copiar cupón: ${couponCode}`}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            padding: "4px 8px",
            borderRadius: "6px",
            fontSize: "11px",
            fontWeight: 800,
            fontFamily: "var(--font-mono, monospace)",
            background: copied ? "rgba(34, 197, 94, 0.2)" : "rgba(15, 23, 42, 0.9)",
            color: copied ? "#4ade80" : "#38bdf8",
            border: copied ? "1px solid rgba(34, 197, 94, 0.5)" : "1px solid rgba(56, 189, 248, 0.3)",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          <span>{copied ? "¡Copiado!" : couponCode}</span>
        </button>

        <a
          href={affiliateUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => {
            navigator.clipboard.writeText(couponCode);
            setCopied(true);
            setTimeout(() => setCopied(false), 3000);
          }}
          title="Abrir página oficial de compra"
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "4px 7px",
            borderRadius: "6px",
            background: "rgba(56, 189, 248, 0.15)",
            color: "#38bdf8",
            border: "1px solid rgba(56, 189, 248, 0.4)",
            cursor: "pointer",
            textDecoration: "none",
            fontSize: "11px",
          }}
        >
          <ExternalLink size={12} />
        </a>
      </div>
    );
  }

  if (variant === "compact") {
    return (
      <button
        onClick={handleClick}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "6px",
          padding: "6px 10px",
          borderRadius: "8px",
          fontSize: "11.5px",
          fontWeight: 800,
          fontFamily: "var(--font-mono, monospace)",
          background: copied
            ? "linear-gradient(135deg, #15803d, #16a34a)"
            : "linear-gradient(135deg, #0284c7, #0369a1)",
          color: "#ffffff",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          cursor: "pointer",
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
          transition: "all 0.15s ease",
        }}
      >
        {copied ? <Check size={13} /> : <ExternalLink size={13} />}
        <span>{copied ? "✓ ¡Cupón Copiado!" : buttonText || `Comprar con ${couponCode} ↗`}</span>
      </button>
    );
  }

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "6px", width: "100%" }}>
      <button
        onClick={handleClick}
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
          padding: "9px 14px",
          borderRadius: "10px",
          fontSize: "12px",
          fontWeight: 800,
          fontFamily: "var(--font-mono, monospace)",
          background: copied
            ? "linear-gradient(135deg, #16a34a, #22c55e)"
            : "linear-gradient(135deg, #06b6d4, #0284c7)",
          color: copied ? "#ffffff" : "#020617",
          border: "none",
          cursor: "pointer",
          boxShadow: "0 3px 12px rgba(6, 182, 212, 0.25)",
          transition: "all 0.15s ease",
        }}
      >
        {copied ? <Check size={14} /> : <ExternalLink size={14} />}
        <span>{copied ? "✓ Cupón Copiado en Portapapeles" : buttonText || `🔥 Comprar con Cupón ${couponCode} ↗`}</span>
      </button>

      <button
        onClick={handleCopyOnly}
        title="Solo copiar código"
        style={{
          padding: "9px 12px",
          borderRadius: "10px",
          background: "rgba(255, 255, 255, 0.05)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          color: "#94a3b8",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Copy size={14} />
      </button>
    </div>
  );
}
