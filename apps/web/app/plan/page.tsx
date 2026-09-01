"use client";

import React, { useEffect, useState } from "react";
import { GitBranch, AlertCircle, RefreshCw, FileWarning } from "lucide-react";
import PlanGraph, { type PlanBloque } from "@/components/plan/PlanGraph";

interface PlanApiError {
  archivo: string;
  error: string;
}

interface PlanApiResponse {
  generatedAt: string;
  source: string;
  count: number;
  bloques: PlanBloque[];
  errores: PlanApiError[];
}

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: PlanApiResponse };

export default function PlanPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  const load = async () => {
    setState({ status: "loading" });
    try {
      const res = await fetch("/api/plan", { cache: "no-store" });
      if (!res.ok) {
        setState({ status: "error", message: `/api/plan respondió ${res.status}` });
        return;
      }
      const data: PlanApiResponse = await res.json();
      setState({ status: "ready", data });
    } catch (error) {
      setState({
        status: "error",
        message: error instanceof Error ? error.message : "SERVICE_UNAVAILABLE",
      });
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const bloques = state.status === "ready" ? state.data.bloques : [];
  const errores = state.status === "ready" ? state.data.errores : [];

  return (
    <div className="w-full max-w-[1100px] mx-auto space-y-6 font-sans pb-16">
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 md:p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <GitBranch className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">Plan del proyecto</h1>
              <p className="text-[13px] text-slate-500 mt-0.5">
                Fases F00–F09 leídas en vivo de <code className="font-mono text-slate-400">orchestration/state/plan/bloques/</code>,
                con su estado, dependencias y criterio de verificación reales — sin resumen escrito a mano.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          {state.status === "ready" && (
            <span className="text-[11px] font-mono text-slate-500">
              Actualizado {new Date(state.data.generatedAt).toLocaleTimeString("es-ES")}
            </span>
          )}
          <button
            onClick={() => void load()}
            disabled={state.status === "loading"}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03] text-[12px] text-slate-300 hover:border-white/20 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${state.status === "loading" ? "animate-spin" : ""}`} />
            Refrescar
          </button>
        </div>
      </div>

      {state.status === "loading" && (
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-10 text-center">
          <RefreshCw className="w-5 h-5 mx-auto mb-3 text-slate-500 animate-spin" />
          <p className="text-sm text-slate-500 font-mono">Leyendo el plan…</p>
        </div>
      )}

      {state.status === "error" && (
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-rose-500/30 rounded-2xl p-8 text-center">
          <AlertCircle className="w-6 h-6 mx-auto mb-3 text-rose-400" />
          <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wide">Sin datos del plan</h2>
          <p className="mt-2 text-[13px] text-slate-500 max-w-md mx-auto">
            No se pudo leer <code className="font-mono">/api/plan</code>: {state.message}
          </p>
        </div>
      )}

      {state.status === "ready" && bloques.length === 0 && (
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-amber-500/30 rounded-2xl p-8 text-center">
          <FileWarning className="w-6 h-6 mx-auto mb-3 text-amber-400" />
          <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wide">Sin datos del plan</h2>
          <p className="mt-2 text-[13px] text-slate-500 max-w-md mx-auto">
            <code className="font-mono">{state.data.source}</code> no contiene ficheros{" "}
            <code className="font-mono">Fxx_*.md</code> con frontmatter legible. No se muestra un plan inventado.
          </p>
        </div>
      )}

      {state.status === "ready" && errores.length > 0 && (
        <div className="bg-amber-500/[0.06] border border-amber-500/30 rounded-xl p-4">
          <div className="flex items-center gap-2 text-amber-400 text-[12px] font-mono uppercase tracking-wide">
            <AlertCircle className="w-4 h-4" />
            {errores.length} fichero(s) de plan con frontmatter no legible (excluidos del grafo)
          </div>
          <ul className="mt-2 space-y-1">
            {errores.map((e) => (
              <li key={e.archivo} className="text-[12px] text-slate-400 font-mono">
                {e.archivo}: <span className="text-slate-500">{e.error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {state.status === "ready" && bloques.length > 0 && <PlanGraph bloques={bloques} />}
    </div>
  );
}
