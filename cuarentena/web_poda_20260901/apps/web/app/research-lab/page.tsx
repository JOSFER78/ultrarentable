"use client";

import { useEffect, useState } from "react";

interface Trial {
  trial_id: string;
  run_id: string;
  generation: number;
  parent_trial_id: string | null;
  symbol: string;
  timeframe: string;
  route: string;
  archetype: string;
  parameters_json: string;
  dataset_id: string;
  dataset_sha256: string;
  discovery_engine: string;
  in_sample_pf: number;
  in_sample_dd_pct: number;
}

interface TrialsResponse {
  status: string;
  mode: string;
  engine_version: string;
  count: number;
  trials: Trial[];
}

interface DaemonStatus {
  is_running: boolean;
  interval_seconds: number;
  last_run_timestamp: string | null;
  repaired_count: number;
  debates_conducted_count: number;
  last_error: string | null;
  queue_summary: { total_in_queue: number };
  engine_version: string;
  mode: string;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${response.status} ${path}`);
  return response.json() as Promise<T>;
}

export default function ResearchLabPage() {
  const [trials, setTrials] = useState<TrialsResponse | null>(null);
  const [daemon, setDaemon] = useState<DaemonStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      const [trialData, daemonData] = await Promise.all([
        getJson<TrialsResponse>("/api/v1/research/trials?limit=200"),
        getJson<DaemonStatus>("/api/v1/research/daemon/status"),
      ]);
      setTrials(trialData);
      setDaemon(daemonData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Research Lab disconnected");
    }
  }

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <div className="text-xs font-semibold uppercase tracking-[0.25em] text-violet-400">Research Lab · Real-Only</div>
          <h1 className="mt-2 text-3xl font-extrabold md:text-5xl">Descubrir → debatir → mutar → volver a probar</h1>
          <p className="mt-3 max-w-4xl text-slate-400">
            Esta vista muestra únicamente trials registrados físicamente. Una propuesta de investigación no equivale a una estrategia rentable ni a una certificación.
          </p>
        </header>

        {error && <div className="rounded-xl border border-rose-900/60 bg-rose-950/30 p-4 text-sm text-rose-300">ERROR / DESCONECTADO · {error}</div>}

        <section className="grid gap-3 md:grid-cols-5">
          <Metric label="Trials registrados" value={trials ? String(trials.count) : "NO EVIDENCE"} />
          <Metric label="Generaciones visibles" value={trials ? String(new Set(trials.trials.map((t) => t.generation)).size) : "NO EVIDENCE"} />
          <Metric label="Daemon" value={daemon ? (daemon.is_running ? "RUNNING" : "STOPPED") : "NO EVIDENCE"} />
          <Metric label="Cola real" value={daemon ? String(daemon.queue_summary.total_in_queue) : "NO EVIDENCE"} />
          <Metric label="Motor" value={trials?.engine_version ?? daemon?.engine_version ?? "NO EVIDENCE"} />
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-xl font-bold">Estado de investigación</h2>
              <p className="mt-1 text-sm text-slate-500">La columna Generation/Parent permite seguir la evolución real de una hipótesis.</p>
            </div>
            <div className="text-sm text-slate-500">
              Último ciclo: {daemon?.last_run_timestamp ?? "NO EVIDENCE"}
            </div>
          </div>

          {trials?.trials?.length ? (
            <div className="mt-5 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="border-b border-slate-800 text-left text-slate-500">
                  <tr>
                    <th className="px-3 py-3">Trial</th>
                    <th className="px-3 py-3">Gen.</th>
                    <th className="px-3 py-3">Parent</th>
                    <th className="px-3 py-3">Familia</th>
                    <th className="px-3 py-3">Activo</th>
                    <th className="px-3 py-3">TF</th>
                    <th className="px-3 py-3">IS PF</th>
                    <th className="px-3 py-3">IS DD</th>
                    <th className="px-3 py-3">Dataset</th>
                  </tr>
                </thead>
                <tbody>
                  {trials.trials.map((trial) => (
                    <tr key={trial.trial_id} className="border-b border-slate-900/80">
                      <td className="px-3 py-3 font-mono text-xs text-white">{trial.trial_id}</td>
                      <td className="px-3 py-3">G{trial.generation}</td>
                      <td className="px-3 py-3 font-mono text-xs text-slate-500">{trial.parent_trial_id ?? "SEED"}</td>
                      <td className="px-3 py-3">{trial.archetype}</td>
                      <td className="px-3 py-3">{trial.symbol}</td>
                      <td className="px-3 py-3">{trial.timeframe}</td>
                      <td className="px-3 py-3">{Number.isFinite(trial.in_sample_pf) ? trial.in_sample_pf.toFixed(2) : "NO EVIDENCE"}</td>
                      <td className="px-3 py-3">{Number.isFinite(trial.in_sample_dd_pct) ? `${trial.in_sample_dd_pct.toFixed(2)}%` : "NO EVIDENCE"}</td>
                      <td className="px-3 py-3 max-w-xs truncate font-mono text-xs text-slate-500">{trial.dataset_id}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="mt-5 rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-500">NO EVIDENCE · No research trials registered.</div>
          )}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <Info title="Regla de promoción" body="Los trials sirven para investigar. Blind OOS y los 11 Evidence Gates siguen siendo la autoridad de certificación." />
          <Info title="Regla de evolución" body="Toda mutación debe conservar parent_trial_id, parámetros, dataset y hash. Si no puede reproducirse, queda bloqueada." />
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-bold">{value}</div>
    </div>
  );
}

function Info({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-400">{body}</p>
    </div>
  );
}
