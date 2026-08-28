"use client";

import React, { useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import SistemaSupervisorPage from "../../sistema/page";
import StrategiesExplorerPage from "../2-explorador-excel/page";
import CandidatosFSMPage from "../../candidatos/page";
import ResearchLabPage from "../../research/page";
import ApprovedStrategiesAndGatesHubPage from "../../gates/page";
import PortfolioStudioPage from "../../portfolio/page";
import EstrategiasHubPage from "../page";

// Mapeo exhaustivo de slugs a fases numéricas (0 a 6)
function parseFaseFromSlug(slug: string): number {
  if (!slug) return 0;
  const s = slug.toLowerCase();

  // Fase 1: Motor 24/7 / Supervisor / Telemetría
  if (s.startsWith("1") || s.includes("motor") || s.includes("supervisor") || s.includes("telemetria") || s.includes("autopilot")) {
    return 1;
  }
  // Fase 2: Catálogo de Estrategias / Familias
  if (s.startsWith("2") || s.includes("catalogo") || s.includes("familias") || s.includes("strategies")) {
    return 2;
  }
  // Fase 3: Candidatos / Pipeline / 10 Gates / 11 Gates / FSM
  if (s.startsWith("3") || s.includes("candidat") || s.includes("pipeline") || s.includes("fsm") || s.includes("11-gates") || s.includes("10-gates")) {
    return 3;
  }
  // Fase 4: Panel Investigación / Research Lab / Fallos
  if (s.startsWith("4") || s.includes("research") || s.includes("investig") || s.includes("lab") || s.includes("fallos")) {
    return 4;
  }
  // Fase 5: Estrategias Aprobadas / Quality Gates Hub / Certificadas
  if (s.startsWith("5") || s.includes("aprobada") || s.includes("gates") || s.includes("certificad")) {
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

  // Barra de navegación de retorno rápido al Hub y cambio de fase
  const phaseNames: Record<number, { title: string; badge: string; color: string }> = {
    0: { title: "Portada General de Estrategias", badge: "PORTADA", color: "#63e1b4" },
    1: { title: "Fase 1: Motor 24/7 & Supervisor", badge: "24/7 LIVE", color: "#10b981" },
    2: { title: "Fase 2: Catálogo Canónico de Estrategias", badge: "CATÁLOGO", color: "#38bdf8" },
    3: { title: "Fase 3: Candidatos & Máquina de Estados FSM", badge: "CANDIDATOS", color: "#818cf8" },
    4: { title: "Fase 4: Research Lab & Memoria de Fallos", badge: "RESEARCH LAB", color: "#ec4899" },
    5: { title: "Fase 5: Quality Gates Hub & Aprobadas", badge: "11 GATES", color: "#facc15" },
    6: { title: "Fase 6: Portfolio Studio & Meta-Estrategias", badge: "PORTFOLIO", color: "#63e1b4" },
  };

  const currentInfo = phaseNames[fase] || phaseNames[0];

  return (
    <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc" }}>
      {/* Sub-Header de Ruta Canónica */}
      <div
        style={{
          background: "rgba(10, 15, 26, 0.95)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          padding: "10px 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "12px",
          fontFamily: "var(--font-mono, monospace)",
          position: "sticky",
          top: 0,
          zIndex: 40,
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Link
            href="/estrategias"
            style={{
              textDecoration: "none",
              color: "#38bdf8",
              fontWeight: 800,
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 8px",
              borderRadius: "6px",
              background: "rgba(56, 189, 248, 0.1)",
              border: "1px solid rgba(56, 189, 248, 0.2)",
            }}
          >
            <span>◀</span>
            <span>Hub Maestro</span>
          </Link>
          <span style={{ color: "#475569" }}>/</span>
          <span style={{ color: "#94a3b8", fontWeight: 600 }}>estrategias</span>
          <span style={{ color: "#475569" }}>/</span>
          <span style={{ color: currentInfo.color, fontWeight: 800 }}>{slug || `fase-${fase}`}</span>
          <span
            style={{
              fontSize: "10px",
              fontWeight: 900,
              padding: "2px 6px",
              borderRadius: "4px",
              background: `${currentInfo.color}22`,
              color: currentInfo.color,
              border: `1px solid ${currentInfo.color}44`,
            }}
          >
            {currentInfo.badge}
          </span>
        </div>

        {/* Selector rápido de las 6 Fases */}
        <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
          {[
            { id: 0, label: "HUB" },
            { id: 1, label: "F1: Motor" },
            { id: 2, label: "F2: Catálogo" },
            { id: 3, label: "F3: Candidatos" },
            { id: 4, label: "F4: Research" },
            { id: 5, label: "F5: Gates" },
            { id: 6, label: "F6: Portfolio" },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 0) router.push("/estrategias");
                else if (item.id === 1) router.push("/estrategias/1-motor-24-7");
                else if (item.id === 2) router.push("/estrategias/2-catalogo");
                else if (item.id === 3) router.push("/estrategias/3-pipeline-11-gates");
                else if (item.id === 4) router.push("/estrategias/4-research");
                else if (item.id === 5) router.push("/estrategias/5-estrategias-aprobadas");
                else if (item.id === 6) router.push("/estrategias/6-meta-estrategias");
              }}
              style={{
                background: fase === item.id ? "rgba(99, 225, 180, 0.2)" : "rgba(255, 255, 255, 0.04)",
                border: fase === item.id ? "1px solid #63e1b4" : "1px solid rgba(255, 255, 255, 0.06)",
                color: fase === item.id ? "#63e1b4" : "#94a3b8",
                padding: "3px 8px",
                borderRadius: "4px",
                fontSize: "10.5px",
                fontWeight: fase === item.id ? 800 : 500,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Renderizado de la fase correspondiente */}
      <div>
        {fase === 0 && <EstrategiasHubPage />}
        {fase === 1 && <SistemaSupervisorPage />}
        {fase === 2 && <StrategiesExplorerPage />}
        {fase === 3 && <CandidatosFSMPage />}
        {fase === 4 && <ResearchLabPage />}
        {fase === 5 && <ApprovedStrategiesAndGatesHubPage />}
        {fase === 6 && <PortfolioStudioPage />}
      </div>
    </div>
  );
}
