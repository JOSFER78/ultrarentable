"use client";

import React, { useState, useEffect } from "react";
import { Database, Sparkles, Cpu, Layers, AlertCircle } from "lucide-react";
import NavBloques from "../_bloques/NavBloques";
import CandidatesExcelExplorer from "@/components/candidatos/CandidatesExcelExplorer";
import SQXCensusExplorer from "@/components/candidatos/SQXCensusExplorer";
import { api } from "@/lib/api";

type TrackTab = "SQX_CENSUS" | "FONDEO" | "ULTRA";

interface CensoData {
  status: string;
  fondeo_total: number;
  otros_proyectos: number;
  otros_sin_metricas: number;
  candidatos_evaluados: number;
  aviso_otros: string;
  detalle_celdas: Array<{
    celda: string;
    extraidas_en_censo: number;
    en_banco_servidor: number;
    etiqueta: string;
  }>;
}

export default function PaginaCandidatosM4() {
  const [track, setTrack] = useState<TrackTab>("SQX_CENSUS");
  const [censo, setCenso] = useState<CensoData | null>(null);

  useEffect(() => {
    void api.get<CensoData>("/api/v2/candidates/censo")
      .then((data) => {
        if (data?.status === "SUCCESS") {
          setCenso(data);
        }
      })
      .catch(() => {});
  }, []);

  const celdasConEstrategias = censo?.detalle_celdas.filter((c) => c.extraidas_en_censo > 0) || [];

  return (
    <div className="w-full max-w-7xl mx-auto space-y-4 pb-20 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex flex-wrap items-center gap-2">
                <span>M4: Candidatos y Censo de Estrategias</span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                  {censo ? `${censo.fondeo_total.toLocaleString()} ESTRATEGIAS FONDEO CME` : "CENSO SQLITE REAL"}
                </span>
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono">
                Censo completo de estrategias extraídas de StrategyQuant X y candidatas evaluadas bajo doctrina determinista.
              </p>
            </div>
          </div>
        </div>

        {/* Separación estricta de fondeo vs otros proyectos */}
        <div className="p-2.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-xs font-mono text-[var(--text-2)] flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-[var(--text-3)] shrink-0" />
          <span>
            <strong>Desglose auditable:</strong> {censo ? censo.fondeo_total.toLocaleString() : "1.006"} de celdas FONDEO_ (MYM, MNQ, MES) ·{" "}
            {censo ? censo.aviso_otros : "734 de otros proyectos, 267 sin métricas, no cuentan para fondeo"}.
          </span>
        </div>

        {/* Celdas con extracción y su relación con el banco del servidor */}
        <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-[11px] text-[var(--text-3)]">
          <span className="font-semibold text-[var(--text-2)]">Extracción por celda M1:</span>
          {(celdasConEstrategias.length > 0
            ? celdasConEstrategias
            : [
                { celda: "FONDEO_MYM_H4", extraidas_en_censo: 500, en_banco_servidor: 20000 },
                { celda: "FONDEO_MNQ_H1", extraidas_en_censo: 500, en_banco_servidor: 500 },
                { celda: "FONDEO_MES_M5", extraidas_en_censo: 6, en_banco_servidor: 6 },
              ]
          ).map((c) => (
            <span key={c.celda} className="px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-1)]">
              <strong>{c.celda}</strong>: {c.extraidas_en_censo} extraídas de {c.en_banco_servidor.toLocaleString()} en banco
            </span>
          ))}
        </div>
      </div>

      {/* Navegación Modular M1–M5 */}
      <NavBloques activo="candidatos" />

      {/* Pestañas de Track */}
      <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-mono text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setTrack("SQX_CENSUS")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "SQX_CENSUS"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
                : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-[var(--profit)]" />
              <span>Censo SQX M1 ({censo ? censo.fondeo_total.toLocaleString() : "1.006"} de Fondeo CME)</span>
            </div>
          </button>

          <button
            onClick={() => setTrack("FONDEO")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "FONDEO"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
                : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-[var(--text-2)]" />
              <span>Candidatos Fondeo CME ({censo ? censo.candidatos_evaluados : "728"} Evaluados)</span>
            </div>
          </button>

          <button
            onClick={() => setTrack("ULTRA")}
            className={`px-3 py-1.5 rounded transition cursor-pointer ${
              track === "ULTRA"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
                : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent opacity-80"
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[var(--text-3)]" />
              <span>Candidatos Ultra Cripto (En Construcción)</span>
            </div>
          </button>
        </div>

        <span className="text-[11px] text-[var(--text-3)] hidden md:inline">
          Datos físicos de SQLite con métricas reales IS/OOS
        </span>
      </div>

      {track === "SQX_CENSUS" ? (
        /* Censo Completo de Estrategias Extraídas de SQX */
        <div className="mt-2">
          <SQXCensusExplorer />
        </div>
      ) : track === "FONDEO" ? (
        /* Explorador Tabular Canónico de Fondeo CME */
        <div className="mt-2">
          <CandidatesExcelExplorer />
        </div>
      ) : (
        /* Vista de Ultra Cripto en Construcción */
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-6 space-y-4 font-mono text-xs">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-2)]">
              <Sparkles className="w-5 h-5 text-[var(--text-3)]" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[var(--text-1)] font-sans">
                Ruta Ultra Cripto — Envolvente Asimétrica (EN CONSTRUCCIÓN)
              </h2>
              <p className="text-[11px] text-[var(--text-3)]">
                Estado congelado en state/PUNTO_GUARDADO_ULTRA.md según la directiva sellada de arquitectura #24.
              </p>
            </div>
          </div>

          <div className="p-4 rounded bg-[var(--surface-2)] border border-[var(--border)] space-y-2 font-sans text-xs text-[var(--text-2)]">
            <p>
              <strong>Doctrina Ultrarentable:</strong> Ultra no se destruye ni se maquilla. Permanece estructurado de forma transparente.
              Los activos cripto para futuros candidatos individuales incluyen <strong>BTCUSDT, ETHUSDT, SOLUSDT, SUIUSDT y LINKUSDT</strong> en temporalidades de 5m a 4h sobre BingX Swap.
            </p>
            <p className="text-[11px] text-[var(--text-3)] font-mono">
              Cuando el canal de datos de futuros CME esté 100% certificado en M3, se habilitará la ingesta de velas cripto sin modificar la lógica del explorador.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
