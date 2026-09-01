"use client";

import React from "react";
import {
  CheckCircle2,
  Circle,
  AlertTriangle,
  Lock,
  ShieldCheck,
  Loader2,
  ArrowRight,
  ArrowLeft,
} from "lucide-react";

export interface PlanBloque {
  id: string;
  titulo: string;
  estado: string;
  depende_de: string[];
  desbloquea: string[];
  verificacion_global: string;
  actualizado: string;
  archivo: string;
}

const ESTADO_STYLE: Record<string, { label: string; badge: string; icon: React.ReactNode }> = {
  PENDIENTE: {
    label: "Pendiente",
    badge: "bg-slate-500/10 border-slate-500/30 text-slate-400",
    icon: <Circle className="w-3.5 h-3.5" />,
  },
  EN_CURSO: {
    label: "En curso",
    badge: "bg-sky-500/10 border-sky-500/30 text-sky-400",
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
  },
  PARCIAL: {
    label: "Parcial",
    badge: "bg-amber-500/10 border-amber-500/30 text-amber-400",
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
  },
  HECHO: {
    label: "Hecho",
    badge: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
  },
  BLOQUEADO: {
    label: "Bloqueado",
    badge: "bg-rose-500/10 border-rose-500/30 text-rose-400",
    icon: <Lock className="w-3.5 h-3.5" />,
  },
  VIGENTE: {
    label: "Vigente",
    badge: "bg-violet-500/10 border-violet-500/30 text-violet-400",
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
  },
};

function estadoStyle(estado: string) {
  return (
    ESTADO_STYLE[estado] ?? {
      label: estado || "Desconocido",
      badge: "bg-slate-500/10 border-slate-500/30 text-slate-400",
      icon: <Circle className="w-3.5 h-3.5" />,
    }
  );
}

function DepChip({ id, dir }: { id: string; dir: "in" | "out" }) {
  return (
    <a
      href={`#bloque-${id}`}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md border border-white/[0.08] bg-white/[0.03] text-[11px] font-mono text-slate-300 hover:border-white/20 hover:text-white transition-colors"
    >
      {dir === "in" ? <ArrowLeft className="w-3 h-3 text-slate-500" /> : <ArrowRight className="w-3 h-3 text-slate-500" />}
      {id}
    </a>
  );
}

/**
 * Grafo de fases del plan maestro: cada bloque F00_*.md..F09_*.md renderizado
 * como nodo con su estado real (leído del frontmatter YAML por /api/plan) y
 * sus aristas depende_de / desbloquea como chips enlazados por ancla al nodo
 * correspondiente. Presentación pura — no hace fetch ni conoce la API.
 */
export default function PlanGraph({ bloques }: { bloques: PlanBloque[] }) {
  const porId = new Map(bloques.map((b) => [b.id, b]));

  return (
    <div className="relative">
      <div
        className="absolute left-[15px] top-2 bottom-2 w-px bg-gradient-to-b from-white/[0.12] via-white/[0.08] to-transparent"
        aria-hidden
      />
      <div className="space-y-4">
        {bloques.map((bloque) => {
          const style = estadoStyle(bloque.estado);
          return (
            <div key={bloque.id} id={`bloque-${bloque.id}`} className="relative pl-10 scroll-mt-24">
              <div
                className={`absolute left-0 top-4 w-8 h-8 rounded-full border flex items-center justify-center ${style.badge}`}
                aria-hidden
              >
                {style.icon}
              </div>

              <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-4 md:p-5 hover:border-white/[0.16] transition-colors">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[11px] text-slate-500">{bloque.id}</span>
                      <h3 className="text-sm md:text-base font-bold text-white tracking-tight">{bloque.titulo}</h3>
                    </div>
                  </div>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-[11px] font-mono uppercase tracking-wide shrink-0 ${style.badge}`}
                  >
                    {style.icon}
                    {style.label}
                  </span>
                </div>

                {bloque.verificacion_global && (
                  <p className="mt-3 text-[13px] leading-relaxed text-slate-400">
                    <span className="text-slate-500 font-mono text-[11px] uppercase mr-1.5">Verificación —</span>
                    {bloque.verificacion_global}
                  </p>
                )}

                <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px]">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-slate-500 font-mono uppercase">Depende de</span>
                    {bloque.depende_de.length === 0 ? (
                      <span className="text-slate-600 font-mono">—</span>
                    ) : (
                      bloque.depende_de.map((id) => <DepChip key={id} id={id} dir="in" />)
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-slate-500 font-mono uppercase">Desbloquea</span>
                    {bloque.desbloquea.length === 0 ? (
                      <span className="text-slate-600 font-mono">—</span>
                    ) : (
                      bloque.desbloquea.map((id) => <DepChip key={id} id={id} dir="out" />)
                    )}
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[10px] font-mono text-slate-600">
                  <span>{bloque.archivo}</span>
                  <span>Actualizado {bloque.actualizado || "—"}</span>
                </div>

                {bloque.depende_de.some((id) => !porId.has(id)) && (
                  <p className="mt-2 text-[10px] font-mono text-amber-500/80">
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
