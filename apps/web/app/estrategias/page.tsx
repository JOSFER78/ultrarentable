"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Database, FlaskConical, Hash, RefreshCw, Search, ShieldCheck, Sparkles, Workflow } from "lucide-react";
import { getStrategyLabOverview, getStrategyLabSQXStatus, getStrategyLabStrategies, extractStrategyLabProject, StrategyLabOverview, StrategyLabRecord, StrategyLabSQXStatus } from "@/lib/api";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

const ORDER = ["CERTIFIED_CURRENT", "BACKTEST_VERIFIED", "STRUCTURALLY_VERIFIED", "EXTRACTED"] as const;
const STATUS: Record<string, string> = {
  CERTIFIED_CURRENT: "CERTIFICADA ACTUAL",
  BACKTEST_VERIFIED: "BACKTEST VERIFICADO",
  STRUCTURALLY_VERIFIED: "ESTRUCTURA VERIFICADA",
  EXTRACTED: "EXTRAÍDA",
};
const STATUS_TONE: Record<string, string> = {
  CERTIFIED_CURRENT: "text-emerald-300 border-emerald-800 bg-emerald-950/30",
  BACKTEST_VERIFIED: "text-sky-300 border-sky-800 bg-sky-950/30",
  STRUCTURALLY_VERIFIED: "text-violet-300 border-violet-800 bg-violet-950/30",
  EXTRACTED: "text-slate-300 border-slate-700 bg-slate-950",
};
const STAGES = [
  ["01", "ORIGEN", "EXTRACTED", "Hipótesis/estrategia recibida con procedencia y hash."],
  ["02", "ESTRUCTURA", "STRUCTURALLY_VERIFIED", "AST y estructura ejecutable comprobados."],
  ["03", "INVESTIGACIÓN", "BACKTEST_VERIFIED", "Backtest real sobre motor canónico."],
  ["04", "EVIDENCIA", "CERTIFIED_CURRENT", "Evidencia completa y vigente."],
] as const;

const fmt = (v: number | null | undefined) => v == null ? "NO EVIDENCE" : v.toLocaleString("es-ES");
const hash = (v: string | null | undefined) => v ? `${v.slice(0, 12)}…${v.slice(-8)}` : "NO EVIDENCE";
const tone = (s: string) => STATUS_TONE[s] ?? "text-amber-300 border-amber-800 bg-amber-950/30";

export default function StrategiesPage() {
  const [overview, setOverview] = useState<StrategyLabOverview | null>(null);
  const [items, setItems] = useState<StrategyLabRecord[]>([]);
  const [sqx, setSqx] = useState<StrategyLabSQXStatus | null>(null);
  const [selected, setSelected] = useState<StrategyLabRecord | null>(null);
  const [query, setQuery] = useState("");
  const [asset, setAsset] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [project, setProject] = useState("");
  const [busy, setBusy] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function refresh() {
    setBusy(true);
    setMessage(null);
    try {
      const [ov, list, source] = await Promise.all([getStrategyLabOverview(), getStrategyLabStrategies(250), getStrategyLabSQXStatus()]);
      setOverview(ov);
      setItems(list.strategies);
      setSqx(source);
      setSelected((current) => current ? list.strategies.find((x) => x.strategy_id === current.strategy_id) ?? null : list.strategies[0] ?? null);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo consultar el catálogo real.");
    } finally { setBusy(false); }
  }
  useEffect(() => { void refresh(); }, []);

  const assets = useMemo(() => Array.from(new Set(items.map((x) => x.symbol).filter(Boolean))).sort(), [items]);
  const statuses = useMemo(() => Array.from(new Set(items.map((x) => x.validation_status).filter(Boolean))).sort((a,b) => (ORDER.indexOf(a as never) + 99) - (ORDER.indexOf(b as never) + 99)), [items]);
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((x) => {
      const haystack = [x.name, x.strategy_id, x.symbol ?? "", x.timeframe ?? "", x.source_project ?? "", x.source_strategy_name ?? ""].join(" ").toLowerCase();
      return (status === "ALL" || x.validation_status === status) && (asset === "ALL" || x.symbol === asset) && (!q || haystack.includes(q));
    }).sort((a,b) => {
      const ra = ORDER.indexOf(a.validation_status as never); const rb = ORDER.indexOf(b.validation_status as never);
      return (ra < 0 ? 99 : ra) - (rb < 0 ? 99 : rb) || a.name.localeCompare(b.name);
    });
  }, [asset, items, query, status]);

  async function extract() {
    if (!project.trim()) { setMessage("Indica un proyecto SQX real."); return; }
    setExtracting(true); setMessage(null);
    try { const r = await extractStrategyLabProject(project.trim()); setMessage(`Extracción real: ${r.inserted} nuevas · ${r.unchanged} sin cambios · ${r.quarantined} cuarentena.`); await refresh(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "La extracción real falló."); }
    finally { setExtracting(false); }
  }

  return <main className="min-h-screen bg-slate-950 px-3 py-5 text-slate-100 md:px-6"><div className="mx-auto max-w-[1600px] space-y-5">
    <EstrategiasHeaderNav />
    <section className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-6 shadow-2xl">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
        <div className="max-w-4xl"><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.28em] text-cyan-400"><Sparkles className="h-4 w-4"/> Strategy Intelligence</div><h1 className="mt-2 text-3xl font-black md:text-5xl">Estrategias</h1><p className="mt-3 text-base leading-7 text-slate-300">Catálogo único de hipótesis y estrategias cuantitativas. La estrategia se identifica por su estructura y evidencia; el venue de ejecución y las cuentas viven fuera de esta pantalla.</p></div>
        <div className="flex flex-wrap gap-2"><button onClick={() => void refresh()} disabled={busy} className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-semibold hover:bg-slate-700 disabled:opacity-50"><RefreshCw className={`mr-2 h-4 w-4 ${busy ? "animate-spin" : ""}`}/>Actualizar</button><Link href="/estrategias/2-explorador-excel" className="rounded-lg bg-cyan-700 px-4 py-2 text-sm font-semibold hover:bg-cyan-600">Explorar candidatos</Link></div>
      </div>
    </section>

    <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">{[["Extraídas", overview?.pipeline.extracted, Database],["Estructural", overview?.pipeline.structurally_verified, ShieldCheck],["Backtest real", overview?.pipeline.backtest_verified, Workflow],["Certificadas", overview?.pipeline.certified_current, ShieldCheck],["Datasets", overview?.pipeline.approved_datasets, Database]].map(([label,value,Icon]) => <div key={String(label)} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500"><Icon className="h-4 w-4"/>{label}</div><div className="mt-2 text-2xl font-black">{value == null ? "NO EVIDENCE" : fmt(Number(value))}</div></div>)}</section>

    <section className="grid gap-3 lg:grid-cols-4">{STAGES.map(([n,title,s,description]) => <div key={s} className="rounded-xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex items-center justify-between"><span className="text-[11px] font-bold tracking-[0.2em] text-slate-600">{n}</span><span className={`rounded-full border px-2 py-1 text-[10px] font-bold ${tone(s)}`}>{s}</span></div><div className="mt-3 font-bold">{title}</div><p className="mt-2 text-sm leading-6 text-slate-400">{description}</p></div>)}</section>

    <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between"><div><h2 className="text-xl font-bold">Catálogo canónico</h2><p className="mt-1 text-sm text-slate-400">Filtrado por activo y estado. No se muestran métricas de rentabilidad hasta que exista backtest canónico asociado.</p></div><div className="grid gap-2 md:grid-cols-3 xl:min-w-[760px]"><div className="relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500"/><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar estrategia…" className="w-full rounded-lg border border-slate-700 bg-slate-950 px-9 py-2 text-sm outline-none"/></div><select value={asset} onChange={(e) => setAsset(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"><option value="ALL">Todos los activos</option>{assets.map((x) => <option key={x} value={x}>{x}</option>)}</select><select value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"><option value="ALL">Todos los estados</option>{statuses.map((x) => <option key={x} value={x}>{STATUS[x] ?? x}</option>)}</select></div></div>
      <div className="mt-5 overflow-auto rounded-xl border border-slate-800"><table className="min-w-full text-sm"><thead className="sticky top-0 bg-slate-950 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Estrategia</th><th className="px-4 py-3">Activo</th><th className="px-4 py-3">TF</th><th className="px-4 py-3">Estado</th><th className="px-4 py-3">Origen</th><th className="px-4 py-3">Dataset</th><th className="px-4 py-3">Strategy hash</th></tr></thead><tbody>{busy ? <tr><td colSpan={7} className="px-4 py-12 text-center text-slate-500">Cargando catálogo real…</td></tr> : filtered.length === 0 ? <tr><td colSpan={7} className="px-4 py-12 text-center text-slate-500">NO EVIDENCE · Sin resultados.</td></tr> : filtered.map((x) => <tr key={x.strategy_id} onClick={() => setSelected(x)} className={`cursor-pointer border-t border-slate-800/80 hover:bg-slate-800/40 ${selected?.strategy_id === x.strategy_id ? "bg-cyan-950/20" : ""}`}><td className="px-4 py-3"><div className="font-semibold">{x.name}</div><div className="mt-1 font-mono text-[10px] text-slate-600">{x.strategy_id}</div></td><td className="px-4 py-3 font-semibold">{x.symbol ?? "NO EVIDENCE"}</td><td className="px-4 py-3">{x.timeframe ?? "NO EVIDENCE"}</td><td className="px-4 py-3"><span className={`rounded-full border px-2 py-1 text-[10px] font-semibold ${tone(x.validation_status)}`}>{STATUS[x.validation_status] ?? x.validation_status}</span></td><td className="px-4 py-3">{x.source_project ?? x.source_engine ?? "NO EVIDENCE"}</td><td className="px-4 py-3 font-mono text-xs">{x.dataset_id ?? "NO EVIDENCE"}</td><td className="px-4 py-3 font-mono text-xs text-slate-500">{hash(x.strategy_hash)}</td></tr>)}</tbody></table></div>
    </section>

    <section className="grid gap-5 xl:grid-cols-[1fr_420px]"><div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex items-center gap-2"><FlaskConical className="h-5 w-5 text-amber-400"/><h2 className="text-xl font-bold">Mejora e investigación</h2></div><p className="mt-1 text-sm text-slate-400">Extrae hipótesis reales de SQX. Después se investigan, optimizan y validan en las fases correspondientes. Esta pantalla no decide rentabilidad por sí sola.</p><div className="mt-4 flex flex-col gap-2 md:flex-row"><input value={project} onChange={(e) => setProject(e.target.value)} placeholder="Proyecto SQX real" className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"/><button onClick={() => void extract()} disabled={extracting} className="rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold disabled:opacity-50">{extracting ? "Extrayendo…" : "Extraer"}</button></div><div className="mt-4 text-xs text-slate-500">SQX: <span className="text-slate-300">{sqx?.status ?? "NO EVIDENCE"}</span></div></div>
      <aside className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5">{selected ? <><div className="flex items-start justify-between gap-3"><div><div className="text-xs uppercase tracking-wide text-slate-500">Ficha canónica</div><h2 className="mt-1 text-xl font-bold">{selected.name}</h2></div><span className={`rounded-full border px-2 py-1 text-[10px] font-bold ${tone(selected.validation_status)}`}>{STATUS[selected.validation_status] ?? selected.validation_status}</span></div><div className="mt-5 space-y-2">{[["Activo",selected.symbol],["Timeframe",selected.timeframe],["Origen",selected.source_project ?? selected.source_engine],["Dataset",selected.dataset_id],["Dataset hash",selected.dataset_hash],["Strategy hash",selected.strategy_hash],["Artifact hash",selected.source_artifact_sha256],["Creada",selected.created_at]].map(([k,v]) => <div key={k} className="rounded-lg border border-slate-800 bg-slate-950/50 p-3"><div className="text-[10px] uppercase tracking-wide text-slate-600">{k}</div><div className="mt-1 break-all font-mono text-xs text-slate-300">{v || "NO EVIDENCE"}</div></div>)}</div><div className="mt-4 grid grid-cols-2 gap-2"><Link href="/estrategias/2-explorador-excel" className="rounded-lg border border-slate-700 px-3 py-2 text-center text-xs font-semibold">Candidatos</Link><Link href="/estrategias/4-panel-investigador" className="rounded-lg border border-slate-700 px-3 py-2 text-center text-xs font-semibold">Investigar</Link></div></> : <div className="py-12 text-center text-slate-500">Selecciona una estrategia.</div>}</aside></section>

    {message && <section className="flex items-start gap-3 rounded-xl border border-amber-900/60 bg-amber-950/20 p-4 text-sm text-amber-200"><AlertTriangle className="mt-0.5 h-4 w-4"/><span>{message}</span></section>}
    <footer className="flex flex-wrap items-center gap-3 border-t border-slate-900 pt-4 text-xs text-slate-600"><span className="inline-flex items-center gap-1"><Hash className="h-3.5 w-3.5"/> Hash = identidad, no marketing.</span><span>Strategy ≠ venue.</span><span>NO EVIDENCE ≠ cero.</span></footer>
  </div></main>;
}
