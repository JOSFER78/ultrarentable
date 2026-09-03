"use client";

import React, { useState } from "react";
import {
  Cpu,
  Layers,
  Award,
  Zap,
  ArrowRight,
  ArrowDown,
  CheckCircle2,
  AlertTriangle,
  Server,
  Activity,
  FileCheck,
  ExternalLink,
  ChevronRight,
} from "lucide-react";
import type { ModuloPipeline } from "@/app/api/plan/route";

interface PipelineEstrategiasM1M4Props {
  modulos: ModuloPipeline[];
}

export default function PipelineEstrategiasM1M4({ modulos }: PipelineEstrategiasM1M4Props) {
  const [selectedId, setSelectedId] = useState<string>("M1");

  const activeModulo = modulos.find((m) => m.id === selectedId) || modulos[0];

  const getStatusBadge = (estado: ModuloPipeline["estado"], label: string) => {
    switch (estado) {
      case "ACTIVO_VPS":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--profit)] animate-pulse" />
            {label}
          </span>
        );
      case "EN_CURSO":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-1)]">
            <Activity className="w-3 h-3 text-[var(--profit)] animate-spin" />
            {label}
          </span>
        );
      case "LISTO_CONTRATO":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
            <CheckCircle2 className="w-3 h-3 text-[var(--profit)]" />
            {label}
          </span>
        );
      case "BLOQUEADO_POR_DATOS":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)]">
            <AlertTriangle className="w-3 h-3 text-[var(--loss)]" />
            {label}
          </span>
        );
      case "IMPLEMENTADO":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-bold bg-[var(--surface-2)] border border-[var(--profit)] text-[var(--profit)]">
            <CheckCircle2 className="w-3 h-3 text-[var(--profit)]" />
            {label}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 font-sans text-xs">
      {/* 1. Cabecera Explicativa del Pipeline */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-[var(--profit)]" />
            <h2 className="text-sm sm:text-base font-bold text-[var(--text-1)] tracking-tight">
              Pipeline Modular de Estrategias CME: De StrategyQuant X al Fondeo Real
            </h2>
          </div>
          <span className="font-mono text-[11px] text-[var(--text-3)]">
            Fábrica de Trading Institucional · Fricción Real Barra a Barra
          </span>
        </div>
        <p className="text-[12px] text-[var(--text-2)] leading-relaxed font-sans">
          Cada módulo es independiente y está conectado exclusivamente mediante <strong>contratos criptográficos verificados</strong> (AST, <code className="font-mono text-[var(--text-1)]">strategy_hash</code>, <code className="font-mono text-[var(--text-1)]">dataset_hash</code>). Prohibido el acoplamiento directo o las simulaciones complacientes.
        </p>
      </div>

      {/* 2. Diagrama de Flujo Visual Horizontal de los 5 Módulos */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5 font-mono">
        {modulos.map((m, idx) => {
          const isSelected = m.id === selectedId;
          return (
            <div
              key={m.id}
              onClick={() => setSelectedId(m.id)}
              className={`p-3.5 rounded-lg border transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
                isSelected
                  ? "bg-[var(--surface-2)] border-[var(--profit)] shadow-lg"
                  : "bg-[var(--surface-1)] border-[var(--border)] hover:border-[var(--border-strong)] hover:bg-[var(--surface-2)]"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border)] text-[var(--profit)]">
                  {m.id}
                </span>
                <span className="text-[10px] text-[var(--text-3)]">Paso {idx + 1}/{modulos.length}</span>
              </div>

              <div>
                <h3 className="text-sm font-bold text-[var(--text-1)] font-sans">{m.nombre}</h3>
                <p className="text-[11px] text-[var(--text-3)] font-sans mt-0.5 truncate">
                  {m.subtitulo}
                </p>
              </div>

              <div>
                {getStatusBadge(m.estado, m.estado_label)}
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Panel de Detalle del Módulo Seleccionado */}
      {activeModulo && (
        <div className="bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-lg p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[var(--border)] gap-2">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-[var(--surface-2)] border border-[var(--profit)] text-[var(--profit)]">
                  Módulo {activeModulo.id}
                </span>
                <h3 className="text-base font-bold text-[var(--text-1)]">
                  {activeModulo.nombre} — {activeModulo.subtitulo}
                </h3>
              </div>
              <div className="font-mono text-[11px] text-[var(--text-3)] mt-1">
                Motor / Herramienta: <strong className="text-[var(--text-2)]">{activeModulo.motor_o_herramienta}</strong>
              </div>
            </div>

            <div>
              {getStatusBadge(activeModulo.estado, activeModulo.estado_label)}
            </div>
          </div>

          {/* Misión y Especificación */}
          <div className="space-y-2">
            <span className="text-[11px] font-mono uppercase text-[var(--text-3)] font-semibold">
              Misión Operativa
            </span>
            <p className="text-[12px] text-[var(--text-2)] leading-relaxed bg-[var(--surface-2)] p-3 rounded-md border border-[var(--border)]">
              {activeModulo.mision}
            </p>
          </div>

          {/* Métricas y Reglas Clave */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase text-[var(--text-3)] font-semibold">
                Capacidades & Métricas Verificadas
              </span>
              <ul className="space-y-1.5">
                {activeModulo.metricas_clave.map((metrica, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-1)] font-mono">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)] shrink-0 mt-0.5" />
                    <span>{metrica}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase text-[var(--text-3)] font-semibold">
                Salida de Contrato Criptográfico
              </span>
              <div className="bg-[var(--surface-2)] p-3 rounded-md border border-[var(--border)] font-mono text-[11px] text-[var(--text-2)] space-y-1.5">
                <div className="text-[var(--text-3)]">// Contrato inmutable emitido:</div>
                <div className="text-[var(--text-1)]">{activeModulo.salida_contrato}</div>
              </div>
            </div>
          </div>

          {/* Enlace al Módulo en /estrategias */}
          <div className="pt-2 border-t border-[var(--border)] flex items-center justify-between text-xs font-mono">
            <span className="text-[var(--text-3)]">
              Página oficial en la web: <code className="text-[var(--text-2)]">/estrategias/{activeModulo.id === "M1" ? "generacion" : activeModulo.id === "M2" ? "mejora" : activeModulo.id === "M3" ? "valoracion" : "meta"}</code>
            </span>
            <a
              href={`/estrategias/${activeModulo.id === "M1" ? "generacion" : activeModulo.id === "M2" ? "mejora" : activeModulo.id === "M3" ? "valoracion" : "meta"}`}
              className="inline-flex items-center gap-1 text-[var(--profit)] hover:text-white transition font-semibold"
            >
              <span>Abrir subpágina de {activeModulo.id}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
