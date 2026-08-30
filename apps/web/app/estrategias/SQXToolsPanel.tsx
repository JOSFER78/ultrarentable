"use client";
/**
 * SQXToolsPanel — controles reales SQX para /estrategias (UI-NUEVAbis).
 * ZERO-MOCK: cada control muestra datos reales del backend :8000 o NO DATA honesto.
 *  1) Salud SQX (verde/rojo/NO DATA) vía /api/v2/strategy-lab/sqx/status
 *  2) Selector de databanks vía /api/v1/sqx/projects/{project}/databanks
 *  3) /source vía /api/v2/strategy-lab/source/{project}/{strategy}
 *  4) /bind-dataset vía /api/v2/strategy-lab/strategies/{id}/bind-dataset (+ /binding)
 */
import { useCallback, useEffect, useState } from "react";
import { api, extractStrategyLabProject, StrategyLabRecord } from "@/lib/api";

interface DatabanksResponse { status: string; project: string; count: number; databanks: Array<{ name: string } | string>; }
interface SourceResponse { status: string; source?: string | Record<string, unknown>; source_sha256?: string; error?: string; [k: string]: unknown; }
interface BindingResponse { status: string; binding_id?: string; dataset_id?: string; dataset_hash?: string; [k: string]: unknown; }

const databankName = (d: { name: string } | string): string => typeof d === "string" ? d : d.name;
const short = (v: string | null | undefined) => v ? (v.length > 24 ? `${v.slice(0, 16)}…${v.slice(-6)}` : v) : "NO DATA";

export default function SQXToolsPanel({ selected }: { selected: StrategyLabRecord | null }) {
  const [health, setHealth] = useState<"ONLINE" | "OFFLINE" | "NO DATA" | "CHECKING">("CHECKING");
  const [healthDetail, setHealthDetail] = useState<string>("");
  const [project, setProject] = useState("");
  const [databanks, setDatabanks] = useState<string[] | null>(null);
  const [databank, setDatabank] = useState("");
  const [source, setSource] = useState<SourceResponse | null>(null);
  const [binding, setBinding] = useState<BindingResponse | null>(null);
  const [datasetId, setDatasetId] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const checkHealth = useCallback(async () => {
    setHealth("CHECKING"); setHealthDetail("");
    try {
      const r = await api.get<{ status: string; result?: { status?: string; base_url?: string }; error?: string }>("/api/v2/strategy-lab/sqx/status");
      const inner = r?.result?.status;
      if (inner === "ONLINE") { setHealth("ONLINE"); setHealthDetail(r.result?.base_url ? String(r.result.base_url) : "SQX MCP conectado"); }
      else { setHealth("OFFLINE"); setHealthDetail(r?.error || (typeof inner === "string" ? inner : "SQX MCP no responde")); }
    } catch (e) {
      setHealth("NO DATA");
      setHealthDetail(e instanceof Error ? e.message : "Endpoint sqx-status inaccesible");
    }
  }, []);

  const loadDatabanks = useCallback(async () => {
    const p = project.trim();
    if (!p) { setMsg("Indica un proyecto SQX real para listar databanks."); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await api.get<DatabanksResponse>(`/api/v1/sqx/projects/${encodeURIComponent(p)}/databanks`);
      const names = Array.isArray(r?.databanks) ? r.databanks.map(databankName).filter(Boolean) : [];
      setDatabanks(names); setDatabank(names[0] ?? "");
      setMsg(names.length ? `Databanks reales: ${names.join(", ")}` : "Proyecto real sin databanks expuestos.");
    } catch (e) {
      setDatabanks([]); setDatabank("");
      setMsg(`NO DATA · ${e instanceof Error ? e.message : "motor SQX no responde"}`);
    } finally { setBusy(false); }
  }, [project]);

  const extractDatabank = useCallback(async () => {
    const p = project.trim(); const db = databank.trim();
    if (!p) { setMsg("Indica un proyecto SQX real para extraer."); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await extractStrategyLabProject(p, db || undefined);
      setMsg(r?.status === "SUCCESS" ? `Extracción real: ${r.found} encontradas (${r.databank}) · ${r.inserted} nuevas · ${r.unchanged} sin cambios · ${r.quarantined} cuarentena.` : `Extracción: ${r?.status ?? "NO DATA"}`);
    } catch (e) {
      setMsg(`NO DATA (extract) · ${e instanceof Error ? e.message : "error"}`);
    } finally { setBusy(false); }
  }, [project, databank]);

  const fetchSource = useCallback(async () => {
    const p = project.trim(); const db = databank.trim();
    const name = selected?.source_strategy_name ?? selected?.name ?? "";
    if (!p || !name) { setMsg("Se requieren proyecto y estrategia para /source."); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await api.get<SourceResponse>(`/api/v2/strategy-lab/source/${encodeURIComponent(p)}/${encodeURIComponent(name)}${db ? `?databank=${encodeURIComponent(db)}` : ""}`);
      setSource(r);
      setMsg(r?.status === "SUCCESS" ? `Source real obtenida · sha256 ${short(r.source_sha256)}` : `Source: ${r?.status ?? "NO DATA"}${r?.error ? ` · ${r.error}` : ""}`);
    } catch (e) {
      setSource(null);
      setMsg(`NO DATA (source) · ${e instanceof Error ? e.message : "error"}`);
    } finally { setBusy(false); }
  }, [project, databank, selected]);

  const bindDataset = useCallback(async () => {
    if (!selected?.strategy_id) { setMsg("Selecciona una estrategia real del catálogo."); return; }
    if (!datasetId.trim()) { setMsg("Indica un dataset_id real aprobado."); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await api.post<BindingResponse>(`/api/v2/strategy-lab/strategies/${encodeURIComponent(selected.strategy_id)}/bind-dataset`, { dataset_id: datasetId.trim() });
      setBinding(r);
      setMsg(r?.status === "BOUND" ? `BINDING real · ${r.binding_id} · hash ${short(r.dataset_hash)}` : `Binding: ${r?.status ?? "NO DATA"}`);
    } catch (e) {
      setBinding(null);
      setMsg(`NO DATA (bind-dataset) · ${e instanceof Error ? e.message : "error"}`);
    } finally { setBusy(false); }
  }, [selected, datasetId]);

  const loadBinding = useCallback(async () => {
    if (!selected?.strategy_id) { setMsg("Selecciona una estrategia real del catálogo."); return; }
    setBusy(true); setMsg(null);
    try {
      const r = await api.get<BindingResponse>(`/api/v2/strategy-lab/strategies/${encodeURIComponent(selected.strategy_id)}/binding`);
      setBinding(r);
      setMsg(r?.status === "BOUND" ? `Binding actual: ${r.dataset_id}` : "Binding actual: UNBOUND");
    } catch (e) {
      setBinding(null);
      setMsg(`NO DATA (binding) · ${e instanceof Error ? e.message : "error"}`);
    } finally { setBusy(false); }
  }, [selected]);

  const healthDot = health === "ONLINE" ? "bg-emerald-400" : health === "OFFLINE" ? "bg-red-500" : "bg-slate-500";
  const healthText = health === "ONLINE" ? "text-emerald-300" : health === "OFFLINE" ? "text-red-300" : "text-slate-400";
  useEffect(() => { void checkHealth(); }, [checkHealth]);

  return <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5" data-testid="sqx-tools-panel">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 className="text-xl font-bold">Herramientas SQX reales</h2>
      <div className="flex items-center gap-2" data-testid="sqx-health">
        <span className={`inline-block h-3 w-3 rounded-full ${healthDot}`} />
        <span className={`text-sm font-bold ${healthText}`}>{health === "CHECKING" ? "…" : health}</span>
        <button onClick={() => void checkHealth()} disabled={busy} className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-semibold hover:bg-slate-700 disabled:opacity-50">Comprobar</button>
      </div>
    </div>
    {healthDetail && <p className="mt-1 break-all text-xs text-slate-500">SQX: {healthDetail}</p>}
    <div className="mt-4 flex flex-col gap-2 md:flex-row">
      <input value={project} onChange={(e) => setProject(e.target.value)} placeholder="Proyecto SQX real" className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
      <select value={databank} onChange={(e) => setDatabank(e.target.value)} data-testid="sqx-databank-select" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
        {databanks === null ? <option value="">Databank…</option> : databanks.length === 0 ? <option value="NO DATA">NO DATA</option> : databanks.map((n) => <option key={n} value={n}>{n}</option>)}
      </select>
      <button onClick={() => void loadDatabanks()} disabled={busy} className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold hover:bg-slate-700 disabled:opacity-50">Databanks</button>
      <button onClick={() => void extractDatabank()} disabled={busy} data-testid="sqx-extract-btn" className="rounded-lg bg-emerald-800 px-3 py-2 text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50">Extraer banco</button>
      <button onClick={() => void fetchSource()} disabled={busy} data-testid="sqx-source-btn" className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold hover:bg-slate-700 disabled:opacity-50">/source</button>
    </div>
    <div className="mt-3 flex flex-col gap-2 md:flex-row">
      <input value={datasetId} onChange={(e) => setDatasetId(e.target.value)} placeholder="dataset_id real aprobado" className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
      <button onClick={() => void bindDataset()} disabled={busy} data-testid="sqx-bind-btn" className="rounded-lg bg-emerald-800 px-3 py-2 text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50">/bind-dataset</button>
      <button onClick={() => void loadBinding()} disabled={busy} className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs font-semibold hover:bg-slate-700 disabled:opacity-50">Ver binding</button>
    </div>
    <p className="mt-2 text-xs text-slate-500">Estrategia seleccionada: {selected ? <span className="font-mono text-slate-300">{selected.strategy_id}</span> : "ninguna"}</p>
    {source && <pre className="mt-2 max-h-32 overflow-auto break-all rounded-lg border border-slate-800 bg-slate-950 p-3 text-[10px] text-slate-400">{JSON.stringify(source, null, 2).slice(0, 1200)}</pre>}
    {binding && <pre className="mt-2 max-h-32 overflow-auto break-all rounded-lg border border-slate-800 bg-slate-950 p-3 text-[10px] text-slate-400">{JSON.stringify(binding, null, 2).slice(0, 1200)}</pre>}
  </section>;
}
