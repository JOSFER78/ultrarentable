"use client";

import { useEffect, useState } from "react";
import { Database, RefreshCw, ShieldCheck, Workflow, AlertTriangle, Search } from "lucide-react";
import {
  extractStrategyLabProject,
  getStrategyLabOverview,
  getStrategyLabSQXStatus,
  getStrategyLabStrategies,
  StrategyLabOverview,
  StrategyLabRecord,
  StrategyLabSQXStatus,
} from "@/lib/api";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

const stageCopy = [
  ["EXTRACTED", "Estrategias extraídas de SQX con origen y hash del contenido fuente."],
  ["STRUCTURALLY_VERIFIED", "Representación canónica comprobada; sin afirmar que sea rentable."],
  ["BACKTEST_VERIFIED", "Backtest ejecutado con dataset real y motor canónico."],
  ["CERTIFIED_CURRENT", "Evidencia completa y vigente bajo la versión actual."],
] as const;

function fmt(value: number | null | undefined) {
  return value === null || value === undefined ? "NO EVIDENCE" : value.toLocaleString("es-ES");
}

export default function StrategiesPage() {
  const [overview, setOverview] = useState<StrategyLabOverview | null>(null);
  const [strategies, setStrategies] = useState<StrategyLabRecord[]>([]);
  const [sqx, setSqx] = useState<StrategyLabSQXStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [project, setProject] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setMessage(null);
    try {
      const [ov, list, source] = await Promise.all([
        getStrategyLabOverview(),
        getStrategyLabStrategies(100),
        getStrategyLabSQXStatus(),
      ]);
      setOverview(ov);
      setStrategies(list.strategies);
      setSqx(source);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo consultar el laboratorio.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function extract() {
    if (!project.trim()) {
      setMessage("Escribe el nombre real del proyecto SQX.");
      return;
    }
    setExtracting(true);
    setMessage(null);
    try {
      const result = await extractStrategyLabProject(project.trim());
      setMessage(`Extracción real completada: ${result.inserted} nuevas, ${result.unchanged} sin cambios, ${result.quarantined} en cuarentena.`);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "La extracción real no pudo completarse.");
    } finally {
      setExtracting(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 px-3 py-5 md:px-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <EstrategiasHeaderNav />

        <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.25em] text-emerald-400">Strategy Lab · Real-Only</div>
              <h1 className="mt-2 text-3xl font-extrabold tracking-tight md:text-5xl">Extraer → comprobar → mejorar orgánicamente</h1>
              <p className="mt-3 max-w-3xl text-slate-300">
                Esta página ya no confunde una estrategia extraída con una estrategia validada. Cada etapa necesita su propia evidencia y ningún valor faltante se rellena.
              </p>
            </div>
            <button onClick={() => void refresh()} disabled={loading} className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700 disabled:opacity-50">
              <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Actualizar
            </button>
          </div>
        </section>

        <section className="grid gap-3 md:grid-cols-5">
          {[
            ["Extraídas", overview?.pipeline.extracted],
            ["Estructural", overview?.pipeline.structurally_verified],
            ["Backtest real", overview?.pipeline.backtest_verified],
            ["Certificadas actuales", overview?.pipeline.certified_current],
            ["Datasets aprobados", overview?.pipeline.approved_datasets],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
              <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
              <div className="mt-2 text-2xl font-bold">{value === undefined ? "NO EVIDENCE" : fmt(Number(value))}</div>
            </div>
          ))}
        </section>

        <section className="grid gap-4 lg:grid-cols-4">
          {stageCopy.map(([stage, description], index) => (
            <div key={stage} className="rounded-xl border border-slate-800 bg-slate-900 p-5">
              <div className="flex items-center gap-2">
                {index === 0 ? <Database className="h-5 w-5 text-sky-400" /> : index === 1 ? <ShieldCheck className="h-5 w-5 text-emerald-400" /> : index === 2 ? <Workflow className="h-5 w-5 text-amber-400" /> : <ShieldCheck className="h-5 w-5 text-violet-400" />}
                <span className="font-semibold">{stage}</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
            </div>
          ))}
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-xl font-bold">Extracción desde StrategyQuant</h2>
              <p className="mt-1 text-sm text-slate-400">Sólo guarda la estrategia y su evidencia de origen. No crea backtests artificiales.</p>
            </div>
            <div className="flex gap-2">
              <input value={project} onChange={(event) => setProject(event.target.value)} placeholder="Proyecto SQX real" className="min-w-64 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none" />
              <button onClick={() => void extract()} disabled={extracting} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold hover:bg-emerald-500 disabled:opacity-50">
                {extracting ? "Extrayendo…" : "Extraer"}
              </button>
            </div>
          </div>
          <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-sm">
            <span className="text-slate-500">SQX:</span>{" "}
            <span className={sqx?.status === "SUCCESS" ? "text-emerald-400" : "text-amber-400"}>{sqx?.status ?? "NO EVIDENCE"}</span>
          </div>
        </section>

        {message && (
          <section className="flex items-start gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm text-slate-300">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
            <span>{message}</span>
          </section>
        )}

        <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5 text-sky-400" />
            <h2 className="text-xl font-bold">Catálogo extraído</h2>
          </div>
          <p className="mt-1 text-sm text-slate-400">No se muestran PF, ROI, CAGR o DD aquí porque la extracción todavía no es un backtest canónico.</p>

          {strategies.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-500">NO EVIDENCE · No hay estrategias extraídas en el catálogo canónico.</div>
          ) : (
            <div className="mt-5 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-800 text-left text-slate-500">
                  <tr>
                    <th className="px-3 py-3">Estrategia</th>
                    <th className="px-3 py-3">Símbolo</th>
                    <th className="px-3 py-3">TF</th>
                    <th className="px-3 py-3">Estado</th>
                    <th className="px-3 py-3">Dataset</th>
                    <th className="px-3 py-3">Hash</th>
                  </tr>
                </thead>
                <tbody>
                  {strategies.map((strategy) => (
                    <tr key={strategy.strategy_id} className="border-b border-slate-900/80">
                      <td className="px-3 py-3 font-medium text-white">{strategy.name}</td>
                      <td className="px-3 py-3">{strategy.symbol ?? "NO EVIDENCE"}</td>
                      <td className="px-3 py-3">{strategy.timeframe ?? "NO EVIDENCE"}</td>
                      <td className="px-3 py-3"><span className="rounded-full border border-slate-700 px-2 py-1 text-xs">{strategy.validation_status}</span></td>
                      <td className="px-3 py-3">{strategy.dataset_id ?? "PENDING REAL DATASET"}</td>
                      <td className="px-3 py-3 font-mono text-xs text-slate-500">{strategy.strategy_hash.slice(0, 16)}…</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
