"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Database,
  FlaskConical,
  Hash,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Workflow,
  Download,
  Copy,
  Check,
  Table as TableIcon,
  ExternalLink,
  ChevronRight,
  Filter,
  SlidersHorizontal,
  type LucideIcon,
} from "lucide-react";
import {
  getStrategyLabOverview,
  getStrategyLabSQXStatus,
  getStrategyLabStrategies,
  extractStrategyLabProject,
  StrategyLabOverview,
  StrategyLabRecord,
  StrategyLabSQXStatus,
} from "@/lib/api";
import EvidenceLink from "@/components/EvidenceLink";
import SQXToolsPanel from "./SQXToolsPanel";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import { statusLabel, statusRank, statusTone } from "@/lib/status-map";

const STAGES = [
  ["01", "ORIGEN & HIPÓTESIS", "EXTRACTED_UNVERIFIED", "Hipótesis recibida con procedencia verificable y hash SHA-256 inmutable."],
  ["02", "ESTRUCTURA & AST", "STRUCTURALLY_VERIFIED", "Árbol sintáctico AST y componentes ejecutables comprobados."],
  ["03", "INVESTIGACIÓN REAL", "BACKTEST_VERIFIED", "Backtest real sobre motor canónico tick-a-tick con fricción."],
  ["04", "EVIDENCIA CERTIFICADA", "CERTIFIED_CURRENT", "Supervivencia completa a las 11 compuertas de evidencia."],
] as const;

const tone = (s: string) => statusTone(s);
const fmt = (v: number | null | undefined) => (v == null ? "NO EVIDENCE" : v.toLocaleString("es-ES"));
const hash = (v: string | null | undefined) => (v ? `${v.slice(0, 10)}…${v.slice(-8)}` : "NO EVIDENCE");

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
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  async function refresh() {
    setBusy(true);
    setMessage(null);
    try {
      const [ov, list, source] = await Promise.all([
        getStrategyLabOverview(),
        getStrategyLabStrategies(250),
        getStrategyLabSQXStatus(),
      ]);
      setOverview(ov);
      setItems(list.strategies);
      setSqx(source);
      setSelected((current) =>
        current ? list.strategies.find((x) => x.strategy_id === current.strategy_id) ?? null : list.strategies[0] ?? null
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo consultar el catálogo real.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  const assets = useMemo(
    () => Array.from(new Set(items.map((x) => x.symbol).filter((s): s is string => Boolean(s)))).sort(),
    [items]
  );
  const statuses = useMemo(
    () =>
      Array.from(new Set(items.map((x) => x.validation_status).filter((s): s is string => Boolean(s)))).sort(
        (a, b) => statusRank(a) - statusRank(b)
      ),
    [items]
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items
      .filter((x) => {
        const haystack = [
          x.name,
          x.strategy_id,
          x.symbol ?? "",
          x.timeframe ?? "",
          x.source_project ?? "",
          x.source_strategy_name ?? "",
        ]
          .join(" ")
          .toLowerCase();
        return (
          (status === "ALL" || x.validation_status === status) &&
          (asset === "ALL" || x.symbol === asset) &&
          (!q || haystack.includes(q))
        );
      })
      .sort((a, b) => {
        const ra = statusRank(a.validation_status);
        const rb = statusRank(b.validation_status);
        return (ra < 0 ? 99 : ra) - (rb < 0 ? 99 : rb) || a.name.localeCompare(b.name);
      });
  }, [asset, items, query, status]);

  async function extract() {
    if (!project.trim()) {
      setMessage("Indica un proyecto SQX real.");
      return;
    }
    setExtracting(true);
    setMessage(null);
    try {
      const r = await extractStrategyLabProject(project.trim());
      setMessage(`Extracción real: ${r.inserted} nuevas · ${r.unchanged} sin cambios · ${r.quarantined} cuarentena.`);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "La extracción real falló.");
    } finally {
      setExtracting(false);
    }
  }

  const copyText = (txt: string, key: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(txt);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    }
  };

  const exportFilteredCSV = () => {
    if (filtered.length === 0) return;
    const headers = [
      "strategy_id",
      "name",
      "symbol",
      "timeframe",
      "validation_status",
      "source_project",
      "dataset_id",
      "strategy_hash",
      "dataset_hash",
      "created_at",
    ];
    const rows = filtered.map((x) => [
      `"${x.strategy_id}"`,
      `"${x.name.replace(/"/g, '""')}"`,
      `"${x.symbol || "NO EVIDENCE"}"`,
      `"${x.timeframe || "NO EVIDENCE"}"`,
      `"${x.validation_status}"`,
      `"${x.source_project || x.source_engine || "NO EVIDENCE"}"`,
      `"${x.dataset_id || "NO EVIDENCE"}"`,
      `"${x.strategy_hash || ""}"`,
      `"${x.dataset_hash || ""}"`,
      `"${x.created_at || ""}"`,
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encoded = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encoded);
    link.setAttribute("download", `catalogo_canónico_estrategias_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <main className="min-h-screen bg-[#030712] px-3 py-5 text-slate-100 md:px-6">
      <div className="mx-auto max-w-[1600px] space-y-5">
        {/* SUB-NAV: 7 FASES CUANTITATIVAS CANÓNICAS */}
        <EstrategiasHeaderNav currentPhase={0} />

        {/* HERO STORYTELLING & CONTROL BANNER */}
        <section className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-gradient-to-br from-[#090d16] via-slate-900/90 to-slate-950 p-6 shadow-2xl backdrop-blur-xl">
          <div className="relative z-10 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-4xl space-y-2">
              <div className="flex items-center gap-2 font-mono text-xs font-black uppercase tracking-[0.25em] text-cyan-400">
                <Sparkles className="h-4 w-4" /> Strategy Intelligence · Catálogo Canónico
              </div>
              <h1 className="text-3xl font-black tracking-tight text-white md:text-4xl">
                Bóveda de Estrategias & Hipótesis
              </h1>
              <p className="text-xs leading-relaxed text-slate-300 md:text-sm max-w-3xl">
                Catálogo único de hipótesis y estrategias cuantitativas. La estrategia se identifica por su estructura AST inmutable y evidencia verificable; el venue de ejecución y las cuentas viven desacoplados de esta bóveda.
              </p>
            </div>
            <div className="flex flex-wrap gap-2.5 items-center font-mono">
              <button
                onClick={() => void refresh()}
                disabled={busy}
                className="inline-flex items-center rounded-xl border border-white/[0.1] bg-slate-900/90 px-3.5 py-2 text-xs font-bold text-slate-200 shadow-md transition hover:bg-slate-800 active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw className={`mr-2 h-3.5 w-3.5 ${busy ? "animate-spin text-cyan-400" : "text-slate-400"}`} />
                Actualizar Catálogo
              </button>
              <button
                onClick={exportFilteredCSV}
                disabled={filtered.length === 0}
                className="inline-flex items-center rounded-xl border border-white/[0.1] bg-slate-900/90 px-3.5 py-2 text-xs font-bold text-slate-200 shadow-md transition hover:bg-slate-800 active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                <Download className="mr-2 h-3.5 w-3.5 text-sky-400" />
                Exportar CSV
              </button>
              <Link
                href="/estrategias/2-explorador-excel"
                className="inline-flex items-center rounded-xl border border-cyan-500/50 bg-gradient-to-r from-cyan-600 to-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-cyan-950/40 transition hover:from-cyan-500 hover:to-indigo-500 active:scale-95 cursor-pointer"
              >
                <TableIcon className="mr-2 h-3.5 w-3.5" />
                Explorador Excel WAL →
              </Link>
            </div>
          </div>
        </section>

        {/* PIPELINE METRIC CARDS (5 CONTADORES CON TABULAR-NUMS) */}
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {([
            ["Extraídas", overview?.pipeline.extracted, Database, "text-sky-400", "border-sky-500/20", "from-sky-500/10 to-transparent"],
            ["Estructural AST", overview?.pipeline.structurally_verified, ShieldCheck, "text-indigo-400", "border-indigo-500/20", "from-indigo-500/10 to-transparent"],
            ["Backtest Real", overview?.pipeline.backtest_verified, Workflow, "text-amber-400", "border-amber-500/20", "from-amber-500/10 to-transparent"],
            ["Certificadas (11/11)", overview?.pipeline.certified_current, ShieldCheck, "text-emerald-400", "border-emerald-500/20", "from-emerald-500/10 to-transparent"],
            ["Datasets Aprobados", overview?.pipeline.approved_datasets, Database, "text-purple-400", "border-purple-500/20", "from-purple-500/10 to-transparent"],
          ] as [string, number | null | undefined, LucideIcon, string, string, string][]).map(
            ([label, value, Icon, colorClass, borderClass, bgGrad]) => (
              <div
                key={String(label)}
                className={`rounded-2xl border bg-gradient-to-b ${bgGrad} bg-[#090d16]/90 p-4 shadow-lg backdrop-blur-xl transition hover:border-slate-700 ${borderClass}`}
              >
                <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-slate-400">
                  <Icon className={`h-4 w-4 ${colorClass}`} />
                  {label}
                </div>
                <div className="mt-2 font-mono text-2xl font-black tabular-nums text-white">
                  {value == null ? "NO EVIDENCE" : fmt(Number(value))}
                </div>
              </div>
            )
          )}
        </section>

        {/* 4 STAGES DE MADURACIÓN CUANTITATIVA */}
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {STAGES.map(([n, title, s, description]) => (
            <div
              key={s}
              className="rounded-2xl border border-white/[0.08] bg-[#090d16]/90 p-4 shadow-lg backdrop-blur-xl transition hover:border-slate-700"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-black tracking-widest text-slate-500">{n}</span>
                <span className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold ${tone(s)}`}>
                  {statusLabel(s)}
                </span>
              </div>
              <div className="mt-2.5 text-xs font-black text-white font-mono">{title}</div>
              <p className="mt-1 text-[11px] leading-relaxed text-slate-400">{description}</p>
            </div>
          ))}
        </section>

        {/* CATÁLOGO CANÓNICO & BUSCADOR MULTI-FILTRO */}
        <section className="rounded-2xl border border-white/[0.08] bg-[#090d16]/90 p-5 shadow-xl backdrop-blur-xl space-y-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black text-white">Inventario Canónico de Estrategias</h2>
                <span className="rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 font-mono text-[10px] font-bold text-cyan-300">
                  {filtered.length} registradas
                </span>
              </div>
              <p className="mt-0.5 text-xs text-slate-400">
                Filtrado multi-criterio. Los registros muestran evidencia determinista según el estándar Zero-Mocks.
              </p>
            </div>

            <div className="grid gap-2 sm:grid-cols-3 xl:min-w-[720px] font-mono">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Buscar estrategia o hash…"
                  className="w-full rounded-xl border border-white/[0.08] bg-[#050811] px-8 py-2 text-xs text-slate-100 outline-none placeholder-slate-500 focus:border-cyan-500"
                />
              </div>
              <select
                value={asset}
                onChange={(e) => setAsset(e.target.value)}
                className="rounded-xl border border-white/[0.08] bg-[#050811] px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 cursor-pointer"
              >
                <option value="ALL">Todos los activos ({assets.length})</option>
                {assets.map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="rounded-xl border border-white/[0.08] bg-[#050811] px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 cursor-pointer"
              >
                <option value="ALL">Todos los estados</option>
                {statuses.map((x) => (
                  <option key={x} value={x}>
                    {statusLabel(x)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="overflow-auto rounded-xl border border-white/[0.08] bg-[#050811]/70 max-h-[520px]">
            <table className="min-w-full font-mono text-xs">
              <thead className="sticky top-0 z-10 border-b border-white/[0.08] bg-[#050811] text-left text-[10.5px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3 font-bold">Estrategia</th>
                  <th className="px-4 py-3 font-bold">Activo</th>
                  <th className="px-4 py-3 font-bold text-center">TF</th>
                  <th className="px-4 py-3 font-bold text-center">Estado</th>
                  <th className="px-4 py-3 font-bold">Origen</th>
                  <th className="px-4 py-3 font-bold">Dataset</th>
                  <th className="px-4 py-3 font-bold">Strategy Hash</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {busy ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-16 text-center text-slate-500">
                      <RefreshCw className="mx-auto mb-2 h-6 w-6 animate-spin text-cyan-400" />
                      Cargando catálogo real desde backend...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-16 text-center text-slate-500">
                      NO EVIDENCE · Sin resultados para los filtros seleccionados.
                    </td>
                  </tr>
                ) : (
                  filtered.map((x) => (
                    <tr
                      key={x.strategy_id}
                      onClick={() => setSelected(x)}
                      className={`cursor-pointer transition hover:bg-white/[0.04] ${
                        selected?.strategy_id === x.strategy_id
                          ? "border-l-2 border-l-cyan-400 bg-cyan-950/30"
                          : ""
                      }`}
                    >
                      <td className="px-4 py-3">
                        <div className="font-sans font-bold text-slate-100">{x.name}</div>
                        <div className="mt-0.5 text-[10px] text-slate-500">{x.strategy_id}</div>
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-200">{x.symbol ?? "NO EVIDENCE"}</td>
                      <td className="px-4 py-3 text-center text-slate-400">{x.timeframe ?? "NO EVIDENCE"}</td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-block rounded-full border px-2.5 py-0.5 text-[10px] font-bold ${tone(x.validation_status)}`}>
                          {statusLabel(x.validation_status)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">{x.source_project ?? x.source_engine ?? "NO EVIDENCE"}</td>
                      <td className="px-4 py-3 text-slate-400">{x.dataset_id ?? "NO EVIDENCE"}</td>
                      <td className="px-4 py-3 text-slate-500">
                        <EvidenceLink strategyHash={x.strategy_hash} datasetHash={x.dataset_hash} engineVersion={null} commitSha={null}>
                          <span className="hover:text-cyan-300">{hash(x.strategy_hash)}</span>
                        </EvidenceLink>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* MEJORA E INVESTIGACIÓN SQX & FICHA CANÓNICA */}
        <section className="grid gap-5 xl:grid-cols-[1fr_420px]">
          <div className="rounded-2xl border border-white/[0.08] bg-[#090d16]/90 p-5 shadow-xl backdrop-blur-xl space-y-4">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-5 w-5 text-amber-400" />
              <h2 className="text-lg font-black text-white">Extracción de Hipótesis SQX</h2>
            </div>
            <p className="text-xs leading-relaxed text-slate-400">
              Extrae hipótesis reales de StrategyQuant X para su posterior investigación, optimización y validación en las fases del pipeline.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row font-mono">
              <input
                value={project}
                onChange={(e) => setProject(e.target.value)}
                placeholder="Nombre de proyecto SQX real (ej. Futures_Trend)"
                className="min-w-0 flex-1 rounded-xl border border-white/[0.08] bg-[#050811] px-3 py-2 text-xs text-slate-100 outline-none placeholder-slate-500 focus:border-cyan-500"
              />
              <button
                onClick={() => void extract()}
                disabled={extracting}
                className="rounded-xl bg-emerald-700 hover:bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-md transition active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                {extracting ? "Extrayendo…" : "Extraer"}
              </button>
            </div>
            <div className="flex items-center gap-2 font-mono text-xs text-slate-500 pt-1">
              <span>Estado SQX MCP:</span>
              <span className={`font-bold ${sqx?.status === "ONLINE" ? "text-emerald-400" : "text-slate-300"}`}>
                {sqx?.status ?? "NO EVIDENCE"}
              </span>
            </div>
          </div>

          <aside className="rounded-2xl border border-white/[0.08] bg-[#090d16]/90 p-5 shadow-xl backdrop-blur-xl">
            {selected ? (
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3 border-b border-white/[0.08] pb-3">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-wider text-slate-500">Ficha Canónica</div>
                    <h2 className="mt-0.5 text-base font-black text-white">{selected.name}</h2>
                  </div>
                  <span className={`rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-bold ${tone(selected.validation_status)}`}>
                    {statusLabel(selected.validation_status)}
                  </span>
                </div>

                <div className="space-y-2 font-mono text-xs max-h-[340px] overflow-y-auto pr-1">
                  {([
                    ["Activo", selected.symbol, "sym"],
                    ["Timeframe", selected.timeframe, "tf"],
                    ["Origen", selected.source_project ?? selected.source_engine, "orig"],
                    ["Dataset ID", selected.dataset_id, "data_id"],
                    ["Dataset Hash", selected.dataset_hash, "data_hash"],
                    ["Strategy Hash", selected.strategy_hash, "strat_hash"],
                    ["Artifact Hash", selected.source_artifact_sha256, "art_hash"],
                    ["Fecha Registro", selected.created_at, "created"],
                  ] as [string, string | null | undefined, string][]).map(([k, v, key]) => (
                    <div key={key} className="rounded-xl border border-white/[0.06] bg-[#050811] p-2.5 flex items-center justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">{k}</div>
                        <div className="mt-0.5 break-all text-slate-300 text-[11px]">
                          {k && k.includes("Hash") ? (
                            <EvidenceLink strategyHash={selected.strategy_hash} datasetHash={selected.dataset_hash} engineVersion={null} commitSha={null}>
                              <span className="hover:text-cyan-300 font-bold">{v || "NO EVIDENCE"}</span>
                            </EvidenceLink>
                          ) : (
                            v || "NO EVIDENCE"
                          )}
                        </div>
                      </div>
                      {v && (
                        <button
                          onClick={() => copyText(String(v), String(key))}
                          className="p-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition flex-shrink-0 cursor-pointer"
                          title="Copiar valor"
                        >
                          {copiedKey === key ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        </button>
                      )}
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/[0.08]">
                  <Link
                    href="/estrategias/2-explorador-excel"
                    className="rounded-xl border border-white/[0.1] bg-slate-900/90 px-3 py-2 text-center text-xs font-bold text-slate-200 transition hover:bg-slate-800 active:scale-95"
                  >
                    Explorador Excel
                  </Link>
                  <Link
                    href="/estrategias/3-pipeline-11-gates"
                    className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-3 py-2 text-center text-xs font-bold text-cyan-300 transition hover:bg-cyan-500/20 active:scale-95"
                  >
                    11 Gates Hub →
                  </Link>
                </div>
              </div>
            ) : (
              <div className="py-16 text-center text-xs text-slate-500 font-mono">
                Selecciona una estrategia del catálogo.
              </div>
            )}
          </aside>
        </section>

        {message && (
          <section className="flex items-start gap-3 rounded-2xl border border-amber-900/60 bg-amber-950/20 p-4 text-xs font-mono text-amber-200 shadow-lg">
            <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{message}</span>
          </section>
        )}

        <SQXToolsPanel selected={selected} />

        <footer className="flex flex-wrap items-center gap-3 border-t border-white/[0.08] pt-4 font-mono text-xs text-slate-500">
          <span className="inline-flex items-center gap-1">
            <Hash className="h-3.5 w-3.5 text-cyan-400" /> Hash = identidad criptográfica inmutable.
          </span>
          <span>·</span>
          <span>Strategy ≠ venue.</span>
          <span>·</span>
          <span>NO EVIDENCE = ausencia física de datos.</span>
        </footer>
      </div>
    </main>
  );
}
