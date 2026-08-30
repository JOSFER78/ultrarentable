"use client";

import React, { useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import SistemaSupervisorPage from "../../sistema/page";
import CandidatesExcelExplorer from "@/components/candidatos/CandidatesExcelExplorer";
import CandidatosFSMPage from "../../candidatos/page";
import ResearchLabPage from "../../research/page";
import GatesPage from "../../gates/page";
import PortfolioStudioPage from "../../portfolio/page";
import EstrategiasHubPage from "../page";
import { CANONICAL_PHASES } from "@/components/EstrategiasHeaderNav";
import { ChevronRight, Sparkles } from "lucide-react";

// Mapeo exhaustivo de slugs a fases numéricas (0 a 6)
function parseFaseFromSlug(slug: string): number {
  if (!slug) return 0;
  const s = slug.toLowerCase();

  // Fase 1: Motor 24/7 / Supervisor / Telemetría
  if (s.startsWith("1") || s.includes("motor") || s.includes("supervisor") || s.includes("telemetria") || s.includes("autopilot")) {
    return 1;
  }
  // Fase 2: Explorador Excel / Catálogo de Candidatos / Familias
  if (s.startsWith("2") || s.includes("excel") || s.includes("explorador") || s.includes("catalogo") || s.includes("familias")) {
    return 2;
  }
  // Fase 3: Pipeline 11 Gates / 10 Gates / FSM / Candidatos
  if (s.startsWith("3") || s.includes("gates") || s.includes("pipeline") || s.includes("11-gates") || s.includes("10-gates") || s.includes("fsm")) {
    return 3;
  }
  // Fase 4: Panel Investigación / Research Lab / Fallos
  if (s.startsWith("4") || s.includes("research") || s.includes("investig") || s.includes("lab") || s.includes("fallos")) {
    return 4;
  }
  // Fase 5: Estrategias Aprobadas / Quality Gates Hub / Certificadas
  if (s.startsWith("5") || s.includes("aprobada") || s.includes("certificad")) {
    return 5;
  }
  // Fase 6: Meta-Estrategias / Portfolio Studio / Ensembles
  if (s.startsWith("6") || s.includes("meta") || s.includes("portfolio") || s.includes("ensemble")) {
    return 6;
  }
  // Fase 0: Portada general
  return 0;
}

export default function DynamicEstrategiasSlugPage() {
  const params = useParams();
  const router = useRouter();
  const slug = typeof params?.slug === "string" ? params.slug : (Array.isArray(params?.slug) ? params.slug[0] : "");

  const fase = useMemo(() => parseFaseFromSlug(slug), [slug]);
  const currentPhaseMeta = CANONICAL_PHASES[fase] || CANONICAL_PHASES[0];

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 font-sans p-3 md:p-6 space-y-5">
      <div className="max-w-[1600px] mx-auto space-y-5">
        {/* BREADCRUMB & HEADER NAV */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3 font-mono text-xs">
          <div className="flex items-center gap-2">
            <Link
              href="/estrategias"
              className="flex items-center gap-1.5 rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 font-bold text-cyan-300 shadow-sm transition hover:bg-cyan-500/20 active:scale-95 cursor-pointer"
            >
              <span>◀</span>
              <span>Hub Estrategias</span>
            </Link>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="text-slate-400 font-semibold">estrategias</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
            <span className="font-extrabold text-white" style={{ color: currentPhaseMeta.accentColor }}>
              {currentPhaseMeta.label}
            </span>
            <span
              className="rounded-full border px-2 py-0.5 text-[10px] font-black"
              style={{
                backgroundColor: `${currentPhaseMeta.accentColor}18`,
                color: currentPhaseMeta.accentColor,
                borderColor: `${currentPhaseMeta.accentColor}40`,
              }}
            >
              {currentPhaseMeta.badge}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-[11px]">Ruta: /estrategias/{slug}</span>
          </div>
        </div>

        {/* Cohesive 7-Phase Nav */}

        {/* Renderizado dinámico de la fase correspondiente */}
        <div className="pt-2">
          {fase === 0 && <EstrategiasHubPage />}
          {fase === 1 && <SistemaSupervisorPage />}
          {fase === 2 && <CandidatesExcelExplorer />}
          {fase === 3 && <GatesPage />}
          {fase === 4 && <ResearchLabPage />}
          {fase === 5 && <GatesPage />}
          {fase === 6 && <PortfolioStudioPage />}
        </div>
      </div>
    </div>
  );
}
