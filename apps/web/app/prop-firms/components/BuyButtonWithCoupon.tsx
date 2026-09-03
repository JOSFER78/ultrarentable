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
    if (navigator.clipboard) {
      navigator.clipboard.writeText(couponCode);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
    window.open(affiliateUrl, "_blank", "noopener,noreferrer");
  };

  const handleCopyOnly = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(couponCode);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  if (variant === "table-row") {
    return (
      <div className="inline-flex items-center gap-1.5">
        <button
          onClick={handleCopyOnly}
          title={`Copiar cupón: ${couponCode}`}
          className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-mono font-bold transition-all ${
            copied
              ? "bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 shadow-sm shadow-emerald-500/20"
              : "bg-slate-900/90 text-amber-300 hover:text-amber-200 border border-slate-700/80 hover:border-amber-500/40"
          }`}
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-amber-400" />}
          <span>{copied ? "¡Copiado!" : couponCode}</span>
        </button>

        <a
          href={affiliateUrl}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => {
            if (navigator.clipboard) {
              navigator.clipboard.writeText(couponCode);
            }
            setCopied(true);
            setTimeout(() => setCopied(false), 3000);
          }}
          title="Abrir página oficial de compra"
          className="inline-flex items-center justify-center p-1.5 rounded-lg bg-sky-950/60 hover:bg-sky-900/80 text-sky-400 border border-sky-700/50 hover:border-sky-500 transition-all text-xs"
        >
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    );
  }

  if (variant === "compact") {
    return (
      <button
        onClick={handleClick}
        className={`w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono font-bold transition-all shadow-md ${
          copied
            ? "bg-emerald-600 text-white shadow-emerald-600/20"
            : "bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 shadow-amber-500/20"
        }`}
      >
        {copied ? <Check className="w-3.5 h-3.5" /> : <ExternalLink className="w-3.5 h-3.5" />}
        <span>{copied ? "✓ ¡Cupón Copiado!" : buttonText || `Comprar con ${couponCode} ↗`}</span>
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1.5 w-full">
      <button
        onClick={handleClick}
        className={`flex-1 flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono font-black transition-all shadow-md ${
          copied
            ? "bg-gradient-to-r from-emerald-600 to-emerald-500 text-white shadow-emerald-500/20"
            : "bg-gradient-to-r from-amber-500 via-amber-400 to-amber-500 hover:brightness-110 text-slate-950 shadow-amber-500/20"
        }`}
      >
        {copied ? <Check className="w-4 h-4" /> : <ExternalLink className="w-4 h-4" />}
        <span>
          {copied ? "✓ Cupón Copiado en Portapapeles" : buttonText || `🔥 Comprar con Cupón ${couponCode} ↗`}
        </span>
      </button>

      <button
        onClick={handleCopyOnly}
        title="Solo copiar código"
        className={`p-2 rounded-xl border transition-all flex items-center justify-center ${
          copied
            ? "bg-emerald-950/80 border-emerald-500/50 text-emerald-300"
            : "bg-slate-900/90 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
        }`}
      >
        {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
      </button>
    </div>
  );
}
