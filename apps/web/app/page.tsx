"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, Database, RefreshCw, ShieldCheck, Workflow } from "lucide-react";
import {
  getCandidates,
  getCertifiedStrategies,
  getCertifiedMetaStrategies,
  CandidateStrategy,
  CertifiedStrategy,
  CertifiedMetaStrategy,
} from "@/lib/api";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

type LoadState = "LOADING" | "READY" | "NO_EVIDENCE" | "ERROR";

export default function HomePage() {
  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [certified, setCertified] = useState<CertifiedStrategy[]>([]);
  const [meta, setMeta] = useState<CertifiedMetaStrategy[]>([]);
  const [state, setState] = useState<LoadState>("LOADING");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState("LOADING");
    setError(null);

    const results = await Promise.allSettled([
      getCandidates({ limit: 100 }),
      getCertifiedStrategies(),
      getCertifiedMetaStrategies(),
    ]);

    const [candidateResult, certifiedResult, metaResult] = results;
    const errors: string[] = [];

    if (candidateResult.status === "fulfilled") setCandidates(candidateResult.value);
    else errors.push(toMessage(candidateResult.reason));

    if (certifiedResult.status === "fulfilled") setCertified(certifiedResult.value);
    else errors.push(toMessage(certifiedResult.reason));

    if (metaResult.status === "fulfilled") setMeta(metaResult.value);
    else errors.push(toMessage(metaResult.reason));

    if (errors.length === results.length) {
      setState("ERROR");
      setError(errors.join(" | "));
      return;
    }

    const receivedEvidence = candidateResult.status === "fulfilled" || certifiedResult.status === "fulfilled" || metaResult.status === "fulfilled";
    setState(receivedEvidence ? "READY" : "NO_EVIDENCE");
    if (errors.length) setError(`Parte de la telemetría no está disponible: ${errors.join(" | ")}`);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const currentCertified = certified.filter((item) =>
    item.status === "APPROVED_CURRENT_ENGINE" && item.all_gates_pass && item.ledger_verified,
  );
  const currentMeta = meta.filter((item) =>
    item.status === "APPROVED_CURRENT_ENGINE" && item.all_components_approved_current && item.portfolio_ledger_verified,
  );

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-6 md:px-8">
        <EstrategiasHeaderNav />

        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-300">ULTRARENTABLE · REAL-ONLY</div>
              <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-5xl">Laboratorio cuantitativo</h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">
                La web representa únicamente evidencia entregada por la API canónica. No fabrica candidatos, métricas, timestamps, hashes, capital ni certificaciones cuando faltan datos.
              </p>
            </div>
            <button
              onClick={() => void load()}
              disabled={state === "LOADING"}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${state === "LOADING" ? "animate-spin" : ""}`} />
              Actualizar
            </button>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            <StatusBadge ok={state === "READY"} label={state === "ERROR" ? "API ERROR" : `API ${state}`} />
            <StatusBadge ok={currentCertified.length > 0} label={currentCertified.length ? `${currentCertified.length} certificadas CURRENT` : "NO_EVIDENCE · certificadas CURRENT"} />
            <StatusBadge ok={currentMeta.length > 0} label={currentMeta.length ? `${currentMeta.length} meta CURRENT` : "NO_EVIDENCE · meta CURRENT"} />
          </div>
        </section>

        {error && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-200">
            <span className="font-semibold">Advertencia de evidencia:</span> {error}
          </div>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          <Metric icon={<Database />} label="Candidatos" value={String(candidates.length)} />
          <Metric icon={<ShieldCheck />} label="Certificadas actuales" value={currentCertified.length ? String(currentCertified.length) : "NO_EVIDENCE"} />
          <Metric icon={<Workflow />} label="Metaestrategias actuales" value={currentMeta.length ? String(currentMeta.length) : "NO_EVIDENCE"} />
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <Panel title="Certificación CURRENT">
            {currentCertified.length === 0 ? (
              <Empty message="La API no ha aportado una certificación CURRENT que cumpla Gates + ledger." />
            ) : (
              <div className="space-y-3">
                {currentCertified.slice(0, 10).map((strategy) => (
                  <div key={`${strategy.strategy_id}:${strategy.strategy_hash}`} className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">{strategy.name}</div>
                        <div className="mt-1 text-xs text-slate-400">
                          {strategy.symbol} · {strategy.timeframe} · {strategy.strategy_hash.slice(0, 12)}…
                        </div>
                      </div>
                      <StatusBadge ok label="CURRENT" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title="Metaestrategias CURRENT">
            {currentMeta.length === 0 ? (
              <Empty message="No existe una metaestrategia CURRENT demostrable en la API." />
            ) : (
              <div className="space-y-3">
                {currentMeta.slice(0, 10).map((portfolio) => (
                  <div key={portfolio.meta_strategy_id} className="rounded-lg border border-slate-800 bg-slate-950/50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="font-medium">{portfolio.name}</div>
                        <div className="mt-1 text-xs text-slate-400">{portfolio.strategy_count} componentes · {portfolio.meta_strategy_hash.slice(0, 12)}…</div>
                      </div>
                      <StatusBadge ok label="CURRENT" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </section>

        <nav className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Link className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-500/40" href="/strategies">Strategies</Link>
          <Link className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-500/40" href="/candidatos">Candidatos</Link>
          <Link className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-500/40" href="/gates">11 Gates</Link>
          <Link className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 hover:border-sky-500/40" href="/portfolio">Portfolio</Link>
        </nav>
      </div>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <article className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="mb-2 flex items-center gap-2 text-slate-400"><span className="h-5 w-5">{icon}</span><span className="text-sm">{label}</span></div>
      <div className="text-2xl font-semibold">{value}</div>
    </article>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5"><h2 className="mb-4 text-lg font-semibold">{title}</h2>{children}</section>;
}

function StatusBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${ok ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300" : "border-amber-500/30 bg-amber-500/10 text-amber-300"}`}>
      {ok ? <CheckCircle2 className="h-3.5 w-3.5" /> : <AlertTriangle className="h-3.5 w-3.5" />}
      {label}
    </span>
  );
}

function Empty({ message }: { message: string }) {
  return <div className="rounded-lg border border-dashed border-slate-700 p-6 text-sm text-slate-400">{message}</div>;
}

function toMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : String(reason);
}
