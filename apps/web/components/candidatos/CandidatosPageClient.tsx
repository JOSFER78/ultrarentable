"use client";

import React, { useState, useEffect } from "react";
import { Database, Sparkles, Cpu, Table, FileSpreadsheet } from "lucide-react";
import NavBloques from "../../app/estrategias/_bloques/NavBloques";
import CandidatesExcelExplorer from "@/components/candidatos/CandidatesExcelExplorer";
import SQXCensusExplorer from "@/components/candidatos/SQXCensusExplorer";
import EstrategiasComparativaTable from "@/components/estrategias/EstrategiasComparativaTable";
import { CensoServerData } from "@/lib/censoServer";
import { api } from "@/lib/api";

type TrackTab = "COMPARATIVA" | "SQX_CENSUS" | "FONDEO" | "ULTRA";

interface Props {
  initialCenso: CensoServerData;
}

export default function CandidatosPageClient({ initialCenso }: Props) {
  const [track, setTrack] = useState<TrackTab>("COMPARATIVA");
  const [censo, setCenso] = useState<CensoServerData>(initialCenso);

  useEffect(() => {
    void api
      .get<CensoServerData>("/api/v2/candidates/censo?limite=1000")
      .then((data) => {
        if (data?.status === "SUCCESS") {
          setCenso(data);
        }
      })
      .catch(() => {});
  }, []);

  const celdasConEstrategias =
    censo?.detalle_celdas.filter((c) => c.extraidas_en_censo > 0) || [];

  return (
    <div className="w-full max-w-7xl mx-auto space-y-4 pb-20 text-neutral-100 font-sans">
      {/* Header Banner */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-200">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-neutral-100 flex flex-wrap items-center gap-2">
                <span>M4: Candidatos y Censo de Estrategias</span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-neutral-800 border border-neutral-700 text-neutral-200">
                  {censo && censo.fondeo_total > 0
                    ? `${censo.fondeo_total.toLocaleString()} ESTRATEGIAS FONDEO CME`
                    : "CENSO SQLITE REAL"}
                </span>
              </h1>
              <p className="text-xs text-neutral-400 font-mono">
                Censo completo de estrategias de StrategyQuant X con periodo probado, OOS y métricas en dólares reales.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
            <div className="px-2.5 py-1 rounded bg-neutral-950 border border-neutral-800 text-neutral-300">
              <span className="text-neutral-500 mr-1">Celdas activas:</span>
              <span className="font-semibold text-neutral-200">
                {celdasConEstrategias.length} de {censo?.detalle_celdas.length || 30}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Navegación Modular M1–M5 */}
      <NavBloques activo="candidatos" />

      {/* Pestañas de Track */}
      <div className="flex items-center justify-between border-b border-neutral-800 pb-2 font-mono text-xs">
        <div className="flex flex-wrap items-center gap-2">
          {/* Pestaña 1: Comparativa Tipo Excel (por defecto) */}
          <button
            type="button"
            onClick={() => setTrack("COMPARATIVA")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "COMPARATIVA"
                ? "bg-neutral-800 text-neutral-100 font-bold border border-neutral-700 shadow-sm"
                : "text-neutral-400 hover:bg-neutral-800/60 border border-transparent"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5 text-neutral-200" />
              <span>Comparativa Tipo Excel ({censo?.estrategias?.length || censo?.fondeo_total || 0})</span>
            </div>
          </button>

          {/* Pestaña 2: Censo SQX */}
          <button
            type="button"
            onClick={() => setTrack("SQX_CENSUS")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "SQX_CENSUS"
                ? "bg-neutral-800 text-neutral-100 font-bold border border-neutral-700 shadow-sm"
                : "text-neutral-400 hover:bg-neutral-800/60 border border-transparent"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-neutral-300" />
              <span>Desglose por Celdas ({censo ? censo.fondeo_total.toLocaleString() : "1.651"})</span>
            </div>
          </button>

          {/* Pestaña 3: Candidatos Evaluados */}
          <button
            type="button"
            onClick={() => setTrack("FONDEO")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "FONDEO"
                ? "bg-neutral-800 text-neutral-100 font-bold border border-neutral-700 shadow-sm"
                : "text-neutral-400 hover:bg-neutral-800/60 border border-transparent"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-neutral-300" />
              <span>Candidatos Fondeo CME ({censo ? censo.candidatos_evaluados : "728"} Evaluados)</span>
            </div>
          </button>

          {/* Pestaña 4: Ultra */}
          <button
            type="button"
            onClick={() => setTrack("ULTRA")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "ULTRA"
                ? "bg-neutral-800 text-neutral-100 font-bold border border-neutral-700 shadow-sm"
                : "text-neutral-400 hover:bg-neutral-800/60 border border-transparent opacity-80"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-neutral-400" />
              <span>Candidatos Ultra Cripto (En Construcción)</span>
            </div>
          </button>
        </div>

        <span className="text-[11px] text-neutral-500 hidden md:inline font-mono">
          Datos físicos de SQLite con métricas reales IS/OOS
        </span>
      </div>

      {/* Contenido según track */}
      {track === "COMPARATIVA" ? (
        <div className="mt-2">
          <EstrategiasComparativaTable
            estrategias={censo?.estrategias || []}
            totalDisponibles={censo?.fondeo_total}
          />
        </div>
      ) : track === "SQX_CENSUS" ? (
        <div className="mt-2">
          <SQXCensusExplorer />
        </div>
      ) : track === "FONDEO" ? (
        <div className="mt-2">
          <CandidatesExcelExplorer />
        </div>
      ) : (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 space-y-4 font-mono text-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-300">
              <Sparkles className="w-5 h-5 text-neutral-400" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-neutral-100 font-sans">
                Ruta Ultra Cripto — Envolvente Asimétrica (EN CONSTRUCCIÓN)
              </h2>
              <p className="text-[11px] text-neutral-500">
                Estado congelado en state/PUNTO_GUARDADO_ULTRA.md según la directiva sellada de arquitectura #24.
              </p>
            </div>
          </div>
          <div className="p-4 rounded bg-neutral-950 border border-neutral-800 space-y-2 font-sans text-xs text-neutral-300">
            <p>
              <strong>Doctrina Ultrarentable:</strong> Ultra no se destruye ni se maquilla. Permanece estructurado de forma transparente.
              Los activos cripto para futuros candidatos individuales incluyen <strong>BTCUSDT, ETHUSDT, SOLUSDT, SUIUSDT y LINKUSDT</strong> en temporalidades de 5m a 4h sobre BingX Swap.
            </p>
            <p className="text-[11px] text-neutral-500 font-mono">
              Cuando el canal de datos de futuros CME esté 100% certificado en M3, se habilitará la ingesta de velas cripto sin modificar la lógica del explorador.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
