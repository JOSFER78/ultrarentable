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
  Award,
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
    accentColor: "#38bdf8", // Sky
  },
  {
    id: 1,
    num: "01",
    label: "Motor 24/7 en Vivo",
    shortLabel: "Motor en Vivo",
    badge: "24/7 LIVE",
    href: "/estrategias/1-motor-en-vivo",
    icon: Activity,
    accentColor: "#10b981", // Emerald
  },
  {
    id: 2,
    num: "02",
    label: "Explorador Excel WAL",
    shortLabel: "Explorador Excel",
    badge: "EXCEL WAL",
    href: "/estrategias/2-explorador-excel",
    icon: Table,
    accentColor: "#818cf8", // Indigo
  },
  {
    id: 3,
    num: "03",
    label: "Pipeline 11 Gates",
    shortLabel: "11 Gates",
    badge: "11 GATES",
    href: "/estrategias/3-pipeline-11-gates",
    icon: ShieldCheck,
    accentColor: "#facc15", // Amber
  },
  {
    id: 4,
    num: "04",
    label: "Panel Investigador",
    shortLabel: "Research Lab",
    badge: "RESEARCH",
    href: "/estrategias/4-panel-investigador",
    icon: FlaskConical,
    accentColor: "#ec4899", // Pink
  },
  {
    id: 5,
    num: "05",
    label: "Estrategias Aprobadas",
    shortLabel: "Certificadas Hub",
    badge: "CERTIFICADAS",
    href: "/estrategias/5-estrategias-aprobadas",
    icon: Award,
    accentColor: "#22c55e", // Green
  },
  {
    id: 6,
    num: "06",
    label: "Meta-Estrategias Studio",
    shortLabel: "Portfolio Studio",
    badge: "PORTFOLIO",
    href: "/estrategias/6-meta-estrategia",
    icon: PieChart,
    accentColor: "#06b6d4", // Cyan
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
    if (pathname.includes("5-estrategias-aprobadas")) return 5;
    if (pathname.includes("6-meta-estrategia") || pathname.includes("portfolio")) return 6;
    return 0;
  }, [currentPhase, pathname]);

  return (
    <nav
      aria-label="Fases cuantitativas del Strategy Lab"
      className="w-full rounded-2xl border border-white/[0.08] bg-[#090d16]/90 p-2 shadow-xl backdrop-blur-xl"
    >
      <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent py-0.5">
        <div className="hidden lg:flex items-center gap-1.5 px-3 border-r border-white/[0.08] font-mono text-[10px] font-black uppercase tracking-wider text-slate-500 flex-shrink-0">
          <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
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
                  ? "border border-cyan-500/50 bg-gradient-to-r from-cyan-500/15 via-slate-900 to-indigo-500/15 text-cyan-200 shadow-[0_0_15px_rgba(56,189,248,0.2)]"
                  : "border border-transparent text-slate-400 hover:border-slate-800 hover:bg-slate-800/60 hover:text-slate-200"
              }`}
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-lg text-[11px] font-black transition-colors ${
                  isActive
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                    : "bg-slate-900/80 text-slate-500 border border-slate-800 group-hover:text-slate-300"
                }`}
              >
                <Icon className="h-3 w-3" />
              </span>

              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] font-bold ${isActive ? "text-cyan-400" : "text-slate-600"}`}>
                  {p.num}
                </span>
                <span className={`font-semibold ${isActive ? "text-white font-bold" : "text-slate-300"}`}>
                  {p.shortLabel}
                </span>
              </div>

              <span
                className={`hidden xl:inline-block rounded-md px-1.5 py-0.5 text-[9px] font-bold border transition-colors ${
                  isActive
                    ? "bg-cyan-950/60 border-cyan-500/40 text-cyan-300"
                    : "bg-slate-950/60 border-slate-800 text-slate-500 group-hover:text-slate-400"
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
