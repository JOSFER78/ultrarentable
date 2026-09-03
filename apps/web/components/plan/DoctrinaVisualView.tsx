"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  Award,
  Cpu,
  Archive,
  HardDrive,
  Gauge,
  CheckCircle2,
  AlertTriangle,
  Lock,
  FileText,
} from "lucide-react";
import type { DoctrinaRegla } from "@/app/api/plan/route";

interface DoctrinaVisualViewProps {
  doctrina: DoctrinaRegla[];
  onOpenDoc?: (docName: string, title: string) => void;
}

const ONCE_GATES = [
  { id: "G01", name: "Fricción & Comisiones", desc: "Comisión real por símbolo (MES $0.60 vs ES $2.50) + slippage." },
  { id: "G02", name: "Muestra Mínima OOS", desc: "≥ 200 operaciones fuera de muestra obligatorias." },
  { id: "G03", name: "Factor de Beneficio OOS", desc: "PF OOS ≥ 1.25 estricto en holdout ciego." },
  { id: "G04", name: "Consistencia OOS/IS", desc: "Ratio PF OOS / PF IS ≥ 0.50 sin degradación catastrófica." },
  { id: "G05", name: "Deflated Sharpe Ratio (DSR)", desc: "DSR positivo penalizando por número de pruebas ensayadas." },
  { id: "G06", name: "Persistencia por Mitades", desc: "Holdout dividido en dos mitades: ambas deben ser rentables." },
  { id: "G07", name: "Stress Testing & Ruido", desc: "Resistencia a perturbaciones aleatorias de precios y spread." },
  { id: "G08", name: "Monte Carlo Trade Shuffle", desc: "Permutación de trades: 95% de las simulaciones sin quiebra." },
  { id: "G09", name: "Reglas Prop Barra a Barra", desc: "Cálculo de trailing drawdown intradía sobre equity flotante." },
  { id: "G10", name: "Límite Diario de Pérdida", desc: "DLL simulado tick a tick sin tocar el corte de cuenta." },
  { id: "G11", name: "Linaje Criptográfico", desc: "Hash inmutable de AST + dataset verificado con SHA-256." },
];

export default function DoctrinaVisualView({ doctrina, onOpenDoc }: DoctrinaVisualViewProps) {
  const [activeTab, setActiveTab] = useState<"reglas" | "gates">("reglas");

  const getIcon = (icono: string) => {
    switch (icono) {
      case "ShieldCheck":
        return <ShieldCheck className="w-5 h-5 text-[var(--profit)]" />;
      case "Award":
        return <Award className="w-5 h-5 text-[var(--profit)]" />;
      case "Cpu":
        return <Cpu className="w-5 h-5 text-[var(--profit)]" />;
      case "HardDrive":
        return <HardDrive className="w-5 h-5 text-[var(--profit)]" />;
      case "Archive":
        return <Archive className="w-5 h-5 text-[var(--profit)]" />;
      case "Gauge":
        return <Gauge className="w-5 h-5 text-[var(--profit)]" />;
      default:
        return <ShieldCheck className="w-5 h-5 text-[var(--profit)]" />;
    }
  };

  return (
    <div className="space-y-4 font-sans text-xs">
      {/* Cabecera Doctrinal */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[var(--profit)]" />
            <h2 className="text-sm sm:text-base font-bold text-[var(--text-1)] tracking-tight">
              Doctrina & Reglas Invariantes del Sistema
            </h2>
          </div>
          <p className="text-[12px] text-[var(--text-2)] mt-0.5 font-sans">
            Leyes arquitectónicas selladas: Cero simulación, Criterio 1.1 institucional, gobernanza y versionado honesto.
          </p>
        </div>

        <div className="flex items-center gap-1.5 font-mono text-xs shrink-0">
          <button
            onClick={() => setActiveTab("reglas")}
            className={`px-2.5 py-1.5 rounded-md border transition cursor-pointer ${
              activeTab === "reglas"
                ? "bg-[var(--surface-2)] border-[var(--profit)] text-[var(--text-1)] font-bold"
                : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-2)]"
            }`}
          >
            6 Leyes Invariantes
          </button>
          <button
            onClick={() => setActiveTab("gates")}
            className={`px-2.5 py-1.5 rounded-md border transition cursor-pointer ${
              activeTab === "gates"
                ? "bg-[var(--surface-2)] border-[var(--profit)] text-[var(--text-1)] font-bold"
                : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-2)]"
            }`}
          >
            Los 11 Gates Sellados
          </button>
          {onOpenDoc && (
            <button
              onClick={() => onOpenDoc("plan_maestro", "Plan Maestro v4")}
              className="px-2 py-1.5 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer flex items-center gap-1"
              title="Ver archivo REGLAS_INVARIANTES.md en disco"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Ver MD</span>
            </button>
          )}
        </div>
      </div>

      {/* Vista 1: Las 6 Leyes Invariantes en Cuadrícula Visual */}
      {activeTab === "reglas" && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono">
          {doctrina.map((regla) => (
            <div
              key={regla.id}
              className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 flex flex-col justify-between space-y-3 hover:border-[var(--border-strong)] transition"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                    REGLA #{regla.numero}
                  </span>
                  <div className="p-1 rounded bg-[var(--surface-2)] border border-[var(--border)]">
                    {getIcon(regla.icono)}
                  </div>
                </div>
                <h3 className="text-xs sm:text-sm font-bold text-[var(--text-1)] font-sans">
                  {regla.titulo}
                </h3>
                <p className="text-[11px] text-[var(--text-2)] font-sans leading-relaxed">
                  {regla.descripcion}
                </p>
              </div>

              <div className="pt-2 border-t border-[var(--border)] text-[10px] text-[var(--text-3)] uppercase flex items-center justify-between">
                <span>ESTADO: VIGENTE</span>
                <span className="text-[var(--profit)]">INNEGOCIABLE</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Vista 2: Los 11 Gates de Certificación Institucional */}
      {activeTab === "gates" && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
          <div className="border-b border-[var(--border)] pb-2 flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-[var(--text-1)] uppercase tracking-wide">
              Matriz de los 11 Gates del Criterio 1.1 (Evidencia Física Individual Obligatoria)
            </span>
            <span className="text-[11px] font-mono text-[var(--profit)]">CERO GATES SINTÉTICOS</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5 font-mono">
            {ONCE_GATES.map((g) => (
              <div
                key={g.id}
                className="bg-[var(--surface-2)] border border-[var(--border)] rounded-md p-3 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--profit)]">{g.id}</span>
                  <span className="text-[10px] text-[var(--text-3)] uppercase">Gate Obligatorio</span>
                </div>
                <div className="text-xs font-bold text-[var(--text-1)] font-sans">{g.name}</div>
                <p className="text-[11px] text-[var(--text-3)] font-sans leading-relaxed">{g.desc}</p>
              </div>
            ))}
          </div>

          <div className="text-[11px] font-mono text-[var(--text-3)] pt-2 border-t border-[var(--border)]">
            * Cada estrategia debe registrar <code className="text-[var(--text-2)]">passed === true</code> en cada uno de estos 11 gates para figurar como certificada en la Maestra de Estrategias.
          </div>
        </div>
      )}
    </div>
  );
}
