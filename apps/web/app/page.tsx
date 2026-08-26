"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getCandidates, getCertifiedMetaStrategies, getCertifiedStrategies, getDiscoveryStatus, type CandidateStrategy, type CertifiedMetaStrategy, type CertifiedStrategy, type DiscoveryStatus } from "@/lib/api";

export default function HomePage() {
  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [certified, setCertified] = useState<CertifiedStrategy[]>([]);
  const [meta, setMeta] = useState<CertifiedMetaStrategy[]>([]);
  const [discovery, setDiscovery] = useState<DiscoveryStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [candidateResult, certifiedResult, metaResult, discoveryResult] = await Promise.all([
        getCandidates({ limit: 100 }),
        getCertifiedStrategies(),
        getCertifiedMetaStrategies(),
        getDiscoveryStatus(),
      ]);
      setCandidates(candidateResult);
      setCertified(certifiedResult);
      setMeta(metaResult);
      setDiscovery(discoveryResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo conectar con la API real.");
      setCandidates([]);
      setCertified([]);
      setMeta([]);
      setDiscovery(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const avgPf = certified.length
    ? (certified.reduce((sum, item) => sum + item.profit_factor, 0) / certified.length).toFixed(2)
    : "NO_EVIDENCE";

  return (
    <div className="min-h-full space-y-6">
      <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-widest text-emerald-400">ULTRARENTABLE · REAL-ONLY</p>
            <h1 className="mt-2 text-3xl font-bold text-white">Quant Control Center</h1>
            <p className="mt-2 max-w-3xl text-sm text-slate-400">
              Esta interfaz sólo presenta datos entregados por la API canónica. Candidatos, certificaciones y meta-estrategias no se promocionan ni se fabrican en la UI.
            </p>
          </div>
          <button
            onClick={() => void refresh()}
            disabled={loading}
            className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-200 disabled:opacity-50"
          >
            {loading ? "Actualizando…" : "Actualizar"}
          </button>
        </div>

        {error ? (
          <div className="mt-5 rounded-xl border border-amber-700/50 bg-amber-950/20 p-4 text-sm text-amber-200">
            API no disponible / sin evidencia: {error}
          </div>
        ) : null}
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Kpi title="Candidatos" value={loading ? "…" : String(candidates.length)} />
        <Kpi title="Certificadas actuales" value={loading ? "…" : String(certified.length)} />
        <Kpi title="Meta-estrategias" value={loading ? "…" : String(meta.length)} />
        <Kpi title="PF medio certificado" value={loading ? "…" : avgPf} />
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-semibold text-white">Estado del descubrimiento</h2>
          <div className="mt-4 space-y-2 text-sm">
            <Row label="Estado" value={discovery?.status ?? "NO_EVIDENCE"} />
            <Row label="Workers" value={discovery ? String(discovery.active_workers) : "NO_EVIDENCE"} />
            <Row label="Trials" value={discovery ? String(discovery.total_trials) : "NO_EVIDENCE"} />
            <Row label="SQX" value={discovery ? (discovery.sqx_bridge_connected ? "CONNECTED" : "DISCONNECTED") : "NO_EVIDENCE"} />
            <Row label="Engine" value={discovery?.current_engine_version ?? "NO_EVIDENCE"} />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-semibold text-white">Navegación operativa</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <NavCard href="/strategies" title="Motor & Backtest" />
            <NavCard href="/candidatos" title="Candidatos" />
            <NavCard href="/gates" title="11 Gates" />
            <NavCard href="/portfolio" title="Portfolio" />
          </div>
        </div>
      </section>

      <p className="text-xs text-slate-500">
        Regla de evidencia: cero datos cuantitativos locales, cero fallback candidato→certificado y cero simulación para declarar éxito.
      </p>
    </div>
  );
}

function Kpi({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">{title}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-800/70 py-2 last:border-b-0">
      <span className="text-slate-500">{label}</span>
      <span className="font-mono text-slate-200">{value}</span>
    </div>
  );
}

function NavCard({ href, title }: { href: string; title: string }) {
  return (
    <Link href={href} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4 text-sm font-medium text-slate-200 transition hover:border-slate-600 hover:bg-slate-900">
      {title}
    </Link>
  );
}
