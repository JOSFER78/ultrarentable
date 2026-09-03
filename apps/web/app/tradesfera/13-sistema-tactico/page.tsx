"use client";

import React, { useState } from "react";
import {
  Zap,
  DollarSign,
  ShieldCheck,
  Calendar,
  Layers,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
} from "lucide-react";

interface ExtractionProfile {
  firm: string;
  badge: string;
  capexExam: string;
  activationFee: string;
  drawdownModel: string;
  bufferRequired: string;
  payoutCycle: string;
  tactic: string;
}

const PROFILES: ExtractionProfile[] = [
  {
    firm: "MyFundedFutures (MFFU Rapid)",
    badge: "MÁXIMA VELOCIDAD",
    capexExam: "$39.50 USD (50K cupón 300K)",
    activationFee: "$0 USD (Totalmente gratis)",
    drawdownModel: "EOD Trailing (Se congela al fondear)",
    bufferRequired: "$52,100 ($2,100 de colchón)",
    payoutCycle: "Día 1 On-Demand (24h - 48h)",
    tactic: "Operar 2 micros MNQ buscando $200-$300 por sesión hasta superar $52,100. Retirar inmediatamente el excedente en el día 1.",
  },
  {
    firm: "Tradeify (Growth 50K)",
    badge: "$0 ACTIVACIÓN",
    capexExam: "$58.20 USD (50K cupón TNT)",
    activationFee: "$0 USD",
    drawdownModel: "EOD Trailing (Soft Breach en DLL)",
    bufferRequired: "$52,000 ($2,000 de colchón)",
    payoutCycle: "A los 5 días de trading",
    tactic: "Aprovechar que el DLL es Soft Breach (no pierdes la cuenta si tocas el límite diario, solo se cierra el día).",
  },
  {
    firm: "BluSky Trading (Static 50K)",
    badge: "100% ESTÁTICO",
    capexExam: "$110.00 USD (50K cupón BLU25)",
    activationFee: "$0 USD",
    drawdownModel: "100% Estático (Fijado en $48,500)",
    bufferRequired: "$51,500 ($1,500 de colchón)",
    payoutCycle: "Semanal On-Demand tras 8 días",
    tactic: "Ideal para swings o dejar correr operaciones: el drawdown jamás sube aunque ganes $10,000.",
  },
  {
    firm: "TradeDay (Day Trader 50K)",
    badge: "INSTITUCIONAL",
    capexExam: "$59.00 USD (50K cupón FLASH55)",
    activationFee: "$0 USD",
    drawdownModel: "EOD Trailing",
    bufferRequired: "$52,000 ($2,000 de colchón)",
    payoutCycle: "Mismo Día Hábil (Dorman Trading)",
    tactic: "Conexión directa a FCM regulado. Los retiros se pagan el mismo día a tu cuenta bancaria o Wise sin retrasos.",
  },
];

export default function SistemaTacticoPage() {
  const [selectedProfile, setSelectedProfile] = useState<number>(0);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Zap className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Sistema Táctico de Máxima Extracción por Empresa</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] font-mono">
                Módulo M13
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">
              Protocolos específicos de extracción rápida de liquidez adaptados a los términos y condiciones de cada firma
            </p>
          </div>
        </div>
      </div>

      {/* Tarjetas de Firmas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 font-mono text-xs">
        {PROFILES.map((p, idx) => (
          <div
            key={idx}
            onClick={() => setSelectedProfile(idx)}
            className={`p-3.5 rounded-lg border transition cursor-pointer flex flex-col justify-between ${
              selectedProfile === idx
                ? "bg-[var(--surface-3)] border-[var(--border-strong)] shadow-sm"
                : "bg-[var(--surface-1)] border-[var(--border)] hover:bg-[var(--surface-2)]"
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-start justify-between gap-1">
                <span className="text-[9.5px] px-1.5 py-0.2 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)] font-bold">
                  {p.badge}
                </span>
                <span className="text-[10px] text-[var(--text-3)]">#0{idx + 1}</span>
              </div>
              <h3 className="text-xs font-bold text-[var(--text-1)] tracking-tight">
                {p.firm}
              </h3>
              <div className="space-y-1 text-[11px] text-[var(--text-2)] pt-1">
                <div className="flex justify-between">
                  <span className="text-[var(--text-3)]">Coste Examen:</span>
                  <span className="text-[var(--text-1)] font-bold">{p.capexExam.split(" ")[0]}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[var(--text-3)]">Activación:</span>
                  <span className="text-[var(--profit)] font-bold">{p.activationFee.split(" ")[0]}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detalle de la Estrategia Táctica Seleccionada */}
      {PROFILES[selectedProfile] && (
        <div className="p-5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3.5 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-2.5">
            <div>
              <span className="text-[10px] text-[var(--profit)] font-bold uppercase block">
                Manual Táctico Específico:
              </span>
              <h2 className="text-base font-bold text-[var(--text-1)] mt-0.5">
                {PROFILES[selectedProfile].firm}
              </h2>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
              {PROFILES[selectedProfile].payoutCycle}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Modelo Drawdown</span>
              <span className="font-bold text-[var(--text-1)] block mt-0.5">
                {PROFILES[selectedProfile].drawdownModel}
              </span>
            </div>
            <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Colchón Requerido</span>
              <span className="font-bold text-[var(--text-1)] block mt-0.5">
                {PROFILES[selectedProfile].bufferRequired}
              </span>
            </div>
            <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-md">
              <span className="text-[10px] text-[var(--text-3)] block uppercase">Frecuencia de Retiro</span>
              <span className="font-bold text-[var(--profit)] block mt-0.5">
                {PROFILES[selectedProfile].payoutCycle}
              </span>
            </div>
          </div>

          <div className="p-3.5 bg-[var(--surface-2)] border border-[var(--border)] rounded-md space-y-1.5 font-sans">
            <span className="font-mono text-[10px] font-bold text-[var(--text-3)] uppercase block">
              Instrucción de Operativa de Extracción:
            </span>
            <p className="text-[11px] text-[var(--text-2)] leading-relaxed">
              {PROFILES[selectedProfile].tactic}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
