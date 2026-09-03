"use client";

import React, { useState } from "react";
import {
  DollarSign,
  Scale,
  Calendar,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  TrendingDown,
  ArrowRight,
  Calculator,
} from "lucide-react";

export default function ArbitrajePromosFiscalidadPage() {
  const [resetCost, setResetCost] = useState<number>(85); // Reset típico $85
  const [newAccountRegular, setNewAccountRegular] = useState<number>(170); // Precio regular 50K
  const [discountPct, setDiscountPct] = useState<number>(75); // 75% descuento promo

  const discountedNewAccountCost = newAccountRegular * (1 - discountPct / 100);
  const savingsBuyingNew = resetCost - discountedNewAccountCost;
  const shouldBuyNew = savingsBuyingNew > 0;

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <DollarSign className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Arbitraje de Negocio, Promos & Fiscalidad de Retiros</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M15
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Estrategia de costes: reseteos vs cuentas nuevas, estacionalidad y marco fiscal institucional de cobros.
            </p>
          </div>
        </div>
      </div>

      {/* Calculadora de Arbitraje: ¿Resetear o Comprar Cuenta Nueva? */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        <div className="border-b border-[var(--border)] pb-2">
          <h2 className="text-sm font-bold text-[var(--text-1)]">
            Calculadora de Arbitraje: ¿Resetear ($) vs Comprar Nueva con Promo ($)?
          </h2>
          <p className="text-xs text-[var(--text-3)] font-mono">
            Las prop firms cobran precios abusivos por el reseteo. Comprar una cuenta nueva con cupón activo suele ser más barato.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          <div className="space-y-3">
            <div>
              <label className="text-[var(--text-2)] block mb-1">Coste del Reseteo ($ USD):</label>
              <input
                type="number"
                value={resetCost}
                onChange={(e) => setResetCost(Number(e.target.value) || 0)}
                className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded px-3 py-1.5 text-[var(--text-1)]"
              />
            </div>
            <div>
              <label className="text-[var(--text-2)] block mb-1">Precio Regular de la Cuenta ($):</label>
              <input
                type="number"
                value={newAccountRegular}
                onChange={(e) => setNewAccountRegular(Number(e.target.value) || 0)}
                className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded px-3 py-1.5 text-[var(--text-1)]"
              />
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-[var(--text-2)] block mb-1">Descuento Activo en Cuenta Nueva:</label>
              <div className="flex gap-2">
                {[50, 70, 75, 80].map((pct) => (
                  <button
                    key={pct}
                    onClick={() => setDiscountPct(pct)}
                    className={`flex-1 py-1 rounded border transition cursor-pointer ${
                      discountPct === pct
                        ? "bg-[var(--surface-3)] border-[var(--profit)] text-[var(--profit)] font-bold"
                        : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-3)]"
                    }`}
                  >
                    {pct}%
                  </button>
                ))}
              </div>
            </div>

            <div className="p-3 rounded bg-[var(--surface-2)] border border-[var(--border)]">
              <span className="text-[10px] text-[var(--text-3)] uppercase block mb-1">
                Coste Cuenta Nueva con Cupón:
              </span>
              <div className="text-xl font-bold text-[var(--text-1)]">
                ${discountedNewAccountCost.toFixed(2)} USD
              </div>
            </div>
          </div>

          <div
            className={`p-4 rounded-lg border flex flex-col justify-center ${
              shouldBuyNew
                ? "bg-[var(--surface-2)] border-[var(--profit)]"
                : "bg-[var(--surface-2)] border-[var(--border)]"
            }`}
          >
            <span className="text-[10px] uppercase font-bold text-[var(--profit)]">
              {shouldBuyNew ? "DECISIÓN ÓPTIMA: COMPRAR NUEVA" : "DECISIÓN ÓPTIMA: RESETEAR"}
            </span>
            <div className="text-lg font-bold text-[var(--text-1)] mt-1">
              {shouldBuyNew
                ? `Ahorro de $${savingsBuyingNew.toFixed(2)} USD`
                : `Ahorro de $${Math.abs(savingsBuyingNew).toFixed(2)} USD`}
            </div>
            <p className="text-[11px] text-[var(--text-3)] font-sans mt-1">
              {shouldBuyNew
                ? "Nunca pagues el reseteo. Adquiere una nueva cuenta con código promocional y cancela la suscripción anterior."
                : "En este caso el reseteo es ligeramente más económico que abrir una nueva cuenta."}
            </p>
          </div>
        </div>
      </div>

      {/* Guía Fiscal de Retiros de Fondeo */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-[var(--text-1)]">
              Marco Fiscal & Pasarelas de Cobro de Prop Firms
            </h2>
            <p className="text-xs text-[var(--text-3)] font-mono">
              Doctrina legal: Tributación en España y Unión Europea para retiros de futuros regulados.
            </p>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)]">
            Auditoría Legal 2026
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-sans text-xs">
          <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
            <span className="text-[10px] font-mono uppercase text-[var(--profit)] font-bold">Naturaleza Jurídica</span>
            <div className="text-xs font-bold text-[var(--text-1)]">Prestación de Servicios</div>
            <p className="text-[11px] text-[var(--text-3)]">
              El trader NO tributa como ganancias patrimoniales de capital mobiliario porque opera capital demo de la empresa. Los payouts son honorarios por servicios de simulación/consultoría financiera.
            </p>
          </div>

          <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
            <span className="text-[10px] font-mono uppercase text-[var(--profit)] font-bold">Pasarelas Oficiales</span>
            <div className="text-xs font-bold text-[var(--text-1)]">Deel, Rise & Plane</div>
            <p className="text-[11px] text-[var(--text-3)]">
              Las prop firms institucionales gestionan contratos de contratista independiente (W-8BEN) a través de Deel o Rise, emitiendo facturas automáticas y transferencias directas a cuenta bancaria.
            </p>
          </div>

          <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 space-y-1.5">
            <span className="text-[10px] font-mono uppercase text-[var(--profit)] font-bold">Estructura Óptima</span>
            <div className="text-xs font-bold text-[var(--text-1)]">Autónomo vs Sociedad (SL)</div>
            <p className="text-[11px] text-[var(--text-3)]">
              Para cobros acumulados &lt; 40.000 €/año, alta de autónomo en epígrafe de servicios. A partir de 60.000 €/año en retiros recurrentes, se recomienda constituir SL para limitar tipos impositivos al 25% (IS).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
