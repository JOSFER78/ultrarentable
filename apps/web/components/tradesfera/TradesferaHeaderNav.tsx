"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  ArrowLeft,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  BookOpen,
} from "lucide-react";

export interface TradesferaModuleNavItem {
  id: string;
  number: string;
  title: string;
  slug: string;
  href: string;
}

export const TRADESFERA_MODULES_NAV: TradesferaModuleNavItem[] = [
  { id: "01", number: "M01", title: "Ecosistema & 4 Puertas", slug: "01-ecosistema", href: "/tradesfera/01-ecosistema" },
  { id: "02", number: "M02", title: "Matemática Bankroll", slug: "02-matematica-bankroll", href: "/tradesfera/02-matematica-bankroll" },
  { id: "03", number: "M03", title: "Teoría Varianza", slug: "03-teoria-varianza", href: "/tradesfera/03-teoria-varianza" },
  { id: "04", number: "M04", title: "Protocolo Aprobación", slug: "04-protocolo-aprobacion", href: "/tradesfera/04-protocolo-aprobacion" },
  { id: "05", number: "M05", title: "Sistema Multicuenta", slug: "05-sistema-multicuenta", href: "/tradesfera/05-sistema-multicuenta" },
  { id: "06", number: "M06", title: "Ciclo Retiros", slug: "06-ciclo-retiros", href: "/tradesfera/06-ciclo-retiros" },
  { id: "07", number: "M07", title: "Psicología Fondeo", slug: "07-psicologia-fondeo", href: "/tradesfera/07-psicologia-fondeo" },
  { id: "08", number: "M08", title: "Comparativa Prop Firms", slug: "08-comparativa-prop-firms", href: "/tradesfera/08-comparativa-prop-firms" },
  { id: "09", number: "M09", title: "Infra NinjaTrader", slug: "09-infraestructura-ninjatrader", href: "/tradesfera/09-infraestructura-ninjatrader" },
  { id: "10", number: "M10", title: "Dossier Maestro", slug: "10-dossier-maestro", href: "/tradesfera/10-dossier-maestro" },
  { id: "11", number: "M11", title: "Estrategias & Horarios", slug: "11-estrategias-horarios", href: "/tradesfera/11-estrategias-horarios" },
  { id: "12", number: "M12", title: "Maestría Psicológica", slug: "12-maestria-psicologica", href: "/tradesfera/12-maestria-psicologica" },
  { id: "13", number: "M13", title: "Sistema Táctico", slug: "13-sistema-tactico", href: "/tradesfera/13-sistema-tactico" },
  { id: "14", number: "M14", title: "Hacks & Reglas Rápidas", slug: "14-hacks-reglas-rapidas", href: "/tradesfera/14-hacks-reglas-rapidas" },
  { id: "15", number: "M15", title: "Arbitraje & Fiscalidad", slug: "15-arbitraje-promos-fiscalidad", href: "/tradesfera/15-arbitraje-promos-fiscalidad" },
  { id: "16", number: "M16", title: "Playbook Diario", slug: "16-playbook-diario", href: "/tradesfera/16-playbook-diario" },
];

export default function TradesferaHeaderNav() {
  const pathname = usePathname() || "/tradesfera";

  const currentIndex = TRADESFERA_MODULES_NAV.findIndex(
    (m) => pathname === m.href || pathname.startsWith(m.href + "/")
  );
  const currentModule = currentIndex >= 0 ? TRADESFERA_MODULES_NAV[currentIndex] : null;
  const prevModule = currentIndex > 0 ? TRADESFERA_MODULES_NAV[currentIndex - 1] : null;
  const nextModule =
    currentIndex >= 0 && currentIndex < TRADESFERA_MODULES_NAV.length - 1
      ? TRADESFERA_MODULES_NAV[currentIndex + 1]
      : null;

  return (
    <div className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-3 space-y-2.5 font-mono text-xs shadow-sm">
      {/* 1. BARRA SUPERIOR: RETORNO AL ÍNDICE + ANTERIOR / SIGUIENTE */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1 pb-2 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <Link
            href="/tradesfera"
            className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs transition ${
              pathname === "/tradesfera"
                ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)] font-bold"
                : "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-3)]"
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>Índice Tradesfera</span>
          </Link>

          {currentModule && (
            <div className="hidden sm:flex items-center gap-2 pl-2 border-l border-[var(--border)]">
              <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border-strong)] text-[var(--text-1)] font-bold text-[11px]">
                {currentModule.number}
              </span>
              <span className="text-[var(--text-1)] font-bold truncate max-w-[260px]">
                {currentModule.title}
              </span>
            </div>
          )}
        </div>

        {/* NAVEGACIÓN ANTERIOR / SIGUIENTE */}
        <div className="flex items-center gap-1.5 ml-auto">
          {prevModule ? (
            <Link
              href={prevModule.href}
              title={`Ir al módulo anterior: ${prevModule.number} - ${prevModule.title}`}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-3)] transition"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Anterior:</span>
              <span className="font-bold">{prevModule.number}</span>
            </Link>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-3)] opacity-40 cursor-not-allowed">
              <ChevronLeft className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Anterior</span>
            </span>
          )}

          {nextModule ? (
            <Link
              href={nextModule.href}
              title={`Ir al siguiente módulo: ${nextModule.number} - ${nextModule.title}`}
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-3)] transition"
            >
              <span className="hidden md:inline">Siguiente:</span>
              <span className="font-bold">{nextModule.number}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-3)] opacity-40 cursor-not-allowed">
              <span className="hidden md:inline">Siguiente</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </span>
          )}
        </div>
      </div>

      {/* 2. PÍLDORAS HORIZONTALES DE LOS 16 MÓDULOS */}
      <div className="flex items-center gap-1 overflow-x-auto no-scrollbar py-0.5">
        {TRADESFERA_MODULES_NAV.map((mod) => {
          const isActive = pathname === mod.href || pathname.startsWith(mod.href + "/");
          return (
            <Link
              key={mod.id}
              href={mod.href}
              title={`${mod.number}: ${mod.title}`}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-all whitespace-nowrap shrink-0 border text-[11px] ${
                isActive
                  ? "bg-[var(--surface-3)] border-[var(--border-strong)] text-[var(--text-1)] font-bold shadow-sm"
                  : "bg-[var(--surface-2)] border-transparent text-[var(--text-2)] hover:bg-[var(--surface-3)] hover:text-[var(--text-1)]"
              }`}
            >
              <span className="font-bold">{mod.number}</span>
              <span className="hidden lg:inline text-[var(--text-3)] text-[10px]">
                {mod.title.split("&")[0].split(":")[0].trim().slice(0, 14)}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
