"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sparkles,
  Activity,
  Table,
  ShieldCheck,
  FlaskConical,
  PieChart,
} from "lucide-react";

export interface PhaseItem {
  id: number;
  num: string;
  label: string;
  shortLabel: string;
  badge: string;
  href: string;
  icon: React.ElementType;
  accentColor: string;
}

export const CANONICAL_PHASES: PhaseItem[] = [
  {
    id: 0,
    num: "00",
    label: "Catálogo Canónico",
    shortLabel: "Catálogo",
    badge: "CANÓNICO",
    href: "/estrategias",
    icon: Sparkles,
    accentColor: "var(--text-2)", // Sky
  },
  {
    id: 1,
    num: "01",
    label: "Motor 24/7 en Vivo",
    shortLabel: "Motor en Vivo",
    badge: "24/7 LIVE",
    href: "/sistema",
    icon: Activity,
    accentColor: "var(--profit)", // Emerald
  },
  {
    id: 2,
    num: "02",
    label: "Candidatos/Excel",
    shortLabel: "Candidatos",
    badge: "EXCEL WAL",
    href: "/candidatos",
    icon: Table,
    accentColor: "var(--text-2)", // Indigo
  },
  {
    id: 3,
    num: "03",
    label: "Pipeline 11 Gates",
    shortLabel: "11 Gates",
    badge: "11 GATES",
    href: "/gates",
    icon: ShieldCheck,
    accentColor: "var(--text-2)", // Amber
  },
  {
    id: 4,
    num: "04",
    label: "Panel Investigador",
    shortLabel: "Research Lab",
    badge: "RESEARCH",
    href: "/research",
    icon: FlaskConical,
    accentColor: "var(--text-2)", // Pink
  },
  {
    id: 6,
    num: "05",
    label: "Meta-Estrategias Studio",
    shortLabel: "Portfolio Studio",
    badge: "PORTFOLIO",
    href: "/portfolio",
    icon: PieChart,
    accentColor: "var(--text-2)", // Cyan
  },
];

interface EstrategiasHeaderNavProps {
  currentPhase?: number;
}

export default function EstrategiasHeaderNav({ currentPhase }: EstrategiasHeaderNavProps) {
  const pathname = usePathname() || "";

  // Auto-detect phase if not explicitly provided
  const activePhase = React.useMemo(() => {
    if (typeof currentPhase === "number") return currentPhase;
    if (pathname === "/estrategias" || pathname === "/estrategias/") return 0;
    if (pathname.includes("1-motor-en-vivo") || pathname.includes("sistema")) return 1;
    if (pathname.includes("2-explorador-excel") || pathname.includes("candidatos")) return 2;
    if (pathname.includes("3-pipeline-11-gates") || (pathname.startsWith("/gates") && !pathname.includes("aprobadas"))) return 3;
    if (pathname.includes("4-panel-investigador") || pathname.includes("research")) return 4;
    if (pathname.includes("6-meta-estrategia") || pathname.includes("portfolio")) return 6;
    return 0;
  }, [currentPhase, pathname]);

  return (
    <nav
      aria-label="Fases cuantitativas del Strategy Lab"
      className="w-full rounded-2xl border border-white/[0.08] bg-[var(--surface-1)] p-2 shadow-xl backdrop-blur-xl"
    >
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent py-0.5">
        <div className="hidden lg:flex items-center gap-1.5 px-3 border-r border-white/[0.08] font-mono text-[10px] font-black uppercase tracking-wider text-[var(--text-3)] flex-shrink-0">
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--text-2)]"></span>
          <span>FASES CUANTITATIVAS:</span>
        </div>

        {CANONICAL_PHASES.map((p) => {
          const isActive = activePhase === p.id;
          const Icon = p.icon;

          return (
            <Link
              key={p.id}
              href={p.href}
              className={`group relative flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-1.5 font-mono text-xs transition-all duration-200 flex-shrink-0 cursor-pointer ${
                isActive
                  ? "border border-[var(--border)] bg-[var(--surface-1)]    text-[var(--text-1)] shadow-[0_0_15px_rgba(255,255,255,0.06)]"
                  : "border border-transparent text-[var(--text-2)] hover:border-[var(--border)] hover:bg-[var(--surface-1)] hover:text-[var(--text-1)]"
              }`}
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-lg text-[11px] font-black transition-colors ${
                  isActive
                    ? "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)]"
                    : "bg-[var(--surface-1)] text-[var(--text-3)] border border-[var(--border)] group-hover:text-[var(--text-1)]"
                }`}
              >
                <Icon className="h-3 w-3" />
              </span>

              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] font-bold ${isActive ? "text-[var(--text-2)]" : "text-[var(--text-3)]"}`}>
                  {p.num}
                </span>
                <span className={`font-semibold ${isActive ? "text-[var(--text-1)] font-bold" : "text-[var(--text-1)]"}`}>
                  {p.shortLabel}
                </span>
              </div>

              <span
                className={`hidden xl:inline-block rounded-md px-1.5 py-0.5 text-[9px] font-bold border transition-colors ${
                  isActive
                    ? "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-1)]"
                    : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-3)] group-hover:text-[var(--text-2)]"
                }`}
              >
                {p.badge}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
