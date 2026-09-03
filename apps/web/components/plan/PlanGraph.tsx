"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  Circle,
  AlertTriangle,
  Lock,
  ShieldCheck,
  Loader2,
  ArrowRight,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react";

export type { PlanBloque } from "@/app/api/plan/route";
import type { PlanBloque } from "@/app/api/plan/route";

const ESTADO_STYLE: Record<string, { label: string; badge: string; icon: React.ReactNode }> = {
  PENDIENTE: {
    label: "Pendiente",
    badge: "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-2)]",
    icon: <Circle className="w-3.5 h-3.5" />,
  },
  EN_CURSO: {
    label: "En curso",
    badge: "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)]",
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
  },
  PARCIAL: {
    label: "Parcial",
    badge: "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)]",
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
  HECHO: {
    label: "Hecho",
    badge: "bg-[var(--profit-dim)] border-[var(--profit)] text-[var(--profit)]",
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
  },
  BLOQUEADO: {
    label: "Bloqueado",
    badge: "bg-[var(--loss-dim)] border-[var(--loss)] text-[var(--loss)]",
    icon: <Lock className="w-3.5 h-3.5" />,
  },
  VIGENTE: {
    label: "Vigente",
    badge: "bg-[var(--surface-2)] border-[var(--border)] text-[var(--text-2)]",
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
  },
};

function estadoStyle(estado: string) {
  return (
    ESTADO_STYLE[estado] ?? {
      label: estado || "Desconocido",
      badge: "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-2)]",
      icon: <Circle className="w-3.5 h-3.5" />,
    }
  );
}

function DepChip({ id, dir }: { id: string; dir: "in" | "out" }) {
  return (
    <a
      href={`#bloque-${id}`}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-white/[0.08] bg-white/[0.03] text-[11px] font-mono text-[var(--text-1)] hover:border-white/20 hover:text-[var(--text-1)] transition-colors"
    >
      {dir === "in" ? <ArrowLeft className="w-3 h-3 text-[var(--text-3)]" /> : <ArrowRight className="w-3 h-3 text-[var(--text-3)]" />}
      {id}
    </a>
  );
}

interface PlanGraphProps {
  bloques: PlanBloque[];
  onSelectBloque?: (bloque: PlanBloque) => void;
}

export default function PlanGraph({ bloques, onSelectBloque }: PlanGraphProps) {
  const porId = new Map(bloques.map((b) => [b.id, b]));
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="relative">
      <div
        className="absolute left-[15px] top-2 bottom-2 w-px bg-[var(--border)]"
        aria-hidden
      />
      <div className="space-y-3">
        {bloques.map((bloque) => {
          const style = estadoStyle(bloque.estado);
          const isExpanded = expandedIds.has(bloque.id);

          return (
            <div key={bloque.id} id={`bloque-${bloque.id}`} className="relative pl-10 scroll-mt-24">
              <div
                className={`absolute left-0 top-3.5 w-8 h-8 rounded-full border flex items-center justify-center ${style.badge}`}
                aria-hidden
              >
                {style.icon}
              </div>

              <div
                className={`bg-[var(--surface-1)] border rounded-lg p-3.5 md:p-4 transition-colors ${
                  bloque.aparcado
                    ? "border-[var(--border)] opacity-70 hover:opacity-100"
                    : "border-[var(--border)] hover:border-[var(--border-strong)]"
                }`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[11px] text-[var(--text-3)]">{bloque.id}</span>
                      <h3 className="text-sm md:text-base font-bold text-[var(--text-1)] tracking-tight">{bloque.titulo}</h3>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {bloque.aparcado && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-1)] text-[11px] font-mono uppercase tracking-wide">
                        <Lock className="w-3 h-3" />
                        Aparcado
                      </span>
                    )}
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-mono uppercase tracking-wide ${style.badge}`}
                    >
                      {style.icon}
                      {style.label}
                    </span>
                  </div>
                </div>

                {bloque.aparcado && bloque.motivo_aparcado && (
                  <p className="mt-3 text-[12px] leading-relaxed text-[var(--text-2)] border-l-2 border-[var(--border)] pl-3">
                    {bloque.motivo_aparcado}
                  </p>
                )}

                {bloque.verificacion_global && (
                  <p className="mt-3 text-[13px] leading-relaxed text-[var(--text-2)]">
                    <span className="text-[var(--text-3)] font-mono text-[11px] uppercase mr-1.5">Verificación —</span>
                    {bloque.verificacion_global}
                  </p>
                )}

                {bloque.tareas_totales > 1 && (
                  <div className="mt-3 space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-3)]">
                      <span>Progreso de tareas ({bloque.tareas_completadas}/{bloque.tareas_totales})</span>
                      <span>{Math.round((bloque.tareas_completadas / bloque.tareas_totales) * 100)}%</span>
                    </div>
                    <div className="w-full bg-[var(--surface-3)] h-1.5 rounded-full overflow-hidden">
                      <div
                        className="bg-[var(--profit)] h-full transition-all duration-300 rounded-full"
                        style={{ width: `${Math.round((bloque.tareas_completadas / bloque.tareas_totales) * 100)}%` }}
                      />
                    </div>
                  </div>
                )}

                <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px]">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[var(--text-3)] font-mono uppercase">Depende de</span>
                    {bloque.depende_de.length === 0 ? (
                      <span className="text-[var(--text-3)] font-mono">—</span>
                    ) : (
                      bloque.depende_de.map((id) => <DepChip key={id} id={id} dir="in" />)
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[var(--text-3)] font-mono uppercase">Desbloquea</span>
                    {bloque.desbloquea.length === 0 ? (
                      <span className="text-[var(--text-3)] font-mono">—</span>
                    ) : (
                      bloque.desbloquea.map((id) => <DepChip key={id} id={id} dir="out" />)
                    )}
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-[var(--text-3)]">
                  <div className="flex items-center gap-3">
                    <span>{bloque.archivo}</span>
                    <span>Actualizado {bloque.actualizado || "—"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {bloque.content && (
                      <button
                        onClick={() => toggleExpand(bloque.id)}
                        className="inline-flex items-center gap-1 text-[var(--text-2)] hover:text-[var(--text-1)] px-2 py-0.5 rounded border border-[var(--border)] bg-[var(--surface-2)] cursor-pointer"
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp className="w-3 h-3" />
                            <span>Plegar documento</span>
                          </>
                        ) : (
                          <>
                            <ChevronDown className="w-3 h-3" />
                            <span>Desplegar texto completo</span>
                          </>
                        )}
                      </button>
                    )}
                    {onSelectBloque && (
                      <button
                        onClick={() => onSelectBloque(bloque)}
                        className="inline-flex items-center gap-1 text-[var(--profit)] hover:text-white px-2 py-0.5 rounded border border-[var(--border)] bg-[var(--surface-2)] cursor-pointer"
                      >
                        <FileText className="w-3 h-3" />
                        <span>Abrir en visor</span>
                      </button>
                    )}
                  </div>
                </div>

                {isExpanded && bloque.content && (
                  <div className="mt-3.5 p-3.5 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-xs font-mono text-[var(--text-1)] leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
                    {bloque.content}
                  </div>
                )}

                {bloque.depende_de.some((id) => !porId.has(id)) && (
                  <p className="mt-2 text-[10px] font-mono text-[var(--text-3)]">
                    Referencia a fase no encontrada en disco entre las dependencias.
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
