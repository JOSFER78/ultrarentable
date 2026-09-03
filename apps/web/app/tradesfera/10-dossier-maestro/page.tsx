"use client";

import React from "react";
import Link from "next/link";
import {
  BookOpen,
  FileText,
  Award,
  ShieldCheck,
  TrendingUp,
  ExternalLink,
  Layers,
  ChevronRight,
  Calculator,
  Flame,
  CheckCircle2,
} from "lucide-react";

export default function DossierMaestroPage() {
  const DOSSIER_DIMENSIONS = [
    {
      num: "I",
      title: "El Ecosistema Tradesfera & Las 4 Puertas",
      desc: "Modelo asimétrico de negocio, economía de Ticks, canal privado anti-ruido y el Hub 24/7.",
      route: "/tradesfera/01-ecosistema",
    },
    {
      num: "II",
      title: "Matemática de Bankroll & Capital Munición (M02)",
      desc: "Formulación binomial P(Cobro >= 1) = 1 - (1-p)^N. Esperanza matemática y regla de cosecha 80/20.",
      route: "/tradesfera/02-matematica-bankroll",
    },
    {
      num: "III",
      title: "Teoría de Varianza & Control de Drawdown (M03)",
      desc: "Distribución de rachas negativas, drawdown EOD vs Intraday y micro-lotes salvavidas.",
      route: "/tradesfera/03-teoria-varianza",
    },
    {
      num: "IV",
      title: "Protocolo Inteligente de Aprobación (M04)",
      desc: "Dimensionamiento algorítmico, límites de pérdidas diarias y cálculo de contratos MES/MNQ.",
      route: "/tradesfera/04-protocolo-aprobacion",
    },
    {
      num: "V",
      title: "Arquitectura Multicuenta & Copytrading (M05)",
      desc: "Diversificación institucional en 5+ cuentas de fondeo, sincronización de órdenes y blindaje cruzado.",
      route: "/tradesfera/05-sistema-multicuenta",
    },
    {
      num: "VI",
      title: "Ciclo Óptimo de Retiros & Cosecha (M06)",
      desc: "Preservación del colchón de seguridad, tramos de cobro (100% primeros 10K, luego 90/10) y reinversión.",
      route: "/tradesfera/06-ciclo-retiros",
    },
    {
      num: "VII",
      title: "Psicotrading Clínico & Gestión Conductual (M07)",
      desc: "Protocolos neuropsicológicos de Víctor Corrales (@Elpsicologodeltrading) para erradicar el FOMO y revenge trading.",
      route: "/tradesfera/07-psicologia-fondeo",
    },
    {
      num: "VIII",
      title: "Catálogo & Comparativa de Prop Firms CME (M08)",
      desc: "Auditoría exhaustiva de 9 firmas reguladas, modelos de trailing drawdown y políticas de EAs.",
      route: "/tradesfera/08-comparativa-prop-firms",
    },
  ];

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Dossier Maestro: Tratado Integral de Fondeo</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M10
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Compendio enciclopédico de 70 KB: metodología cuantitativa de extracción de capital en futuros CME.
            </p>
          </div>
        </div>
      </div>

      {/* Métricas Globales del Dossier */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <span className="text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">Tasa de Pase Auditada</span>
          <div className="text-xl font-bold text-[var(--profit)] font-mono">26.6%</div>
          <p className="text-[11px] text-[var(--text-3)]">vs 2.5% promedio de la industria general.</p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <span className="text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">Total Retiros Verificados</span>
          <div className="text-xl font-bold text-[var(--text-1)] font-mono">167.839 €</div>
          <p className="text-[11px] text-[var(--text-3)]">En 198 transferencias reales auditadas.</p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <span className="text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">Módulos del Tratado</span>
          <div className="text-xl font-bold text-[var(--text-1)] font-mono">16 Módulos</div>
          <p className="text-[11px] text-[var(--text-3)]">Más de 600 KB de documentación técnica.</p>
        </div>

        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-1">
          <span className="text-[10px] font-mono text-[var(--text-3)] uppercase font-semibold">Regla Invariable</span>
          <div className="text-xl font-bold text-[var(--profit)] font-mono">80 / 20</div>
          <p className="text-[11px] text-[var(--text-3)]">80% patrimonio seguro, 20% reinversión.</p>
        </div>
      </div>

      {/* Índice de Dimensiones del Dossier */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-3">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-mono text-xs">
          <span className="font-bold text-[var(--text-1)] uppercase">
            Índice de Dimensiones del Tratado Canónico
          </span>
          <Link
            href="/tradesfera/modulos"
            className="text-[var(--profit)] hover:underline flex items-center gap-1"
          >
            <span>Ver Biblioteca Técnica Completa</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          {DOSSIER_DIMENSIONS.map((dim) => (
            <Link
              key={dim.num}
              href={dim.route}
              className="p-3.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] hover:border-[var(--profit)] transition block group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[var(--profit)] border border-[var(--border)]">
                  Dimensión {dim.num}
                </span>
                <ChevronRight className="w-3.5 h-3.5 text-[var(--text-3)] group-hover:text-[var(--profit)] transition" />
              </div>
              <div className="text-xs font-bold text-[var(--text-1)] group-hover:text-[var(--profit)] transition">
                {dim.title}
              </div>
              <p className="text-[11px] text-[var(--text-3)] mt-1 line-clamp-2">
                {dim.desc}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
