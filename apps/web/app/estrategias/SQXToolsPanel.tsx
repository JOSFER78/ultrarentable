"use client";
/**
 * SQXToolsPanel — Controles reales SQX para /estrategias.
 * ZERO-MOCK: cada control muestra datos reales del backend :8000 o NO DATA honesto.
 *  1) Salud SQX (verde/rojo/NO DATA) vía /api/v2/strategy-lab/sqx/status
 *  2) Selector de databanks vía /api/v1/sqx/projects/{project}/databanks
 *  3) /source vía /api/v2/strategy-lab/source/{project}/{strategy}
 *  4) /bind-dataset vía /api/v2/strategy-lab/strategies/{id}/bind-dataset (+ /binding)
 */
import { useCallback, useEffect, useState } from "react";
import { api, extractStrategyLabProject, StrategyLabRecord } from "@/lib/api";
import { Copy, Check, Terminal, Database, Link as LinkIcon, RefreshCw, Cpu } from "lucide-react";

interface DatabanksResponse {
  status: string;
  project: string;
  count: number;
  databanks: Array<{ name: string } | string>;
}
interface SourceResponse {
  status: string;
  source?: string | Record<string, unknown>;
  source_sha256?: string;
  error?: string;
  [k: string]: unknown;
}
interface BindingResponse {
  status: string;
  binding_id?: string;
  dataset_id?: string;
  dataset_hash?: string;
  [k: string]: unknown;
}

const databankName = (d: { name: string } | string): string => (typeof d === "string" ? d : d.name);
const short = (v: string | null | undefined) => (v ? (v.length > 24 ? `${v.slice(0, 16)}…${v.slice(-6)}` : v) : "NO DATA");

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
  const [copiedRaw, setCopiedRaw] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    setHealth("CHECKING");
    setHealthDetail("");
    try {
      const r = await api.get<{ status: string; result?: { status?: string; base_url?: string }; error?: string }>(
        "/api/v2/strategy-lab/sqx/status"
      );
      const inner = r?.result?.status;
      if (inner === "ONLINE") {
        setHealth("ONLINE");
        setHealthDetail(r.result?.base_url ? String(r.result.base_url) : "SQX MCP conectado");
      } else {
        setHealth("OFFLINE");
        setHealthDetail(r?.error || (typeof inner === "string" ? inner : "SQX MCP no responde"));
      }
    } catch (e) {
      setHealth("NO DATA");
      setHealthDetail(e instanceof Error ? e.message : "Endpoint sqx-status inaccesible");
    }
  }, []);

  const loadDatabanks = useCallback(async () => {
    const p = project.trim();
    if (!p) {
      setMsg("Indica un proyecto SQX real para listar databanks.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.get<DatabanksResponse>(`/api/v1/sqx/projects/${encodeURIComponent(p)}/databanks`);
      const names = Array.isArray(r?.databanks) ? r.databanks.map(databankName).filter(Boolean) : [];
      setDatabanks(names);
      setDatabank(names[0] ?? "");
      setMsg(names.length ? `Databanks reales: ${names.join(", ")}` : "Proyecto real sin databanks expuestos.");
    } catch (e) {
      setDatabanks([]);
      setDatabank("");
      setMsg(`NO DATA · ${e instanceof Error ? e.message : "motor SQX no responde"}`);
    } finally {
      setBusy(false);
    }
  }, [project]);

  const extractDatabank = useCallback(async () => {
    const p = project.trim();
    const db = databank.trim();
    if (!p) {
      setMsg("Indica un proyecto SQX real para extraer.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      const r = await extractStrategyLabProject(p, db || undefined);
      setMsg(
        r?.status === "SUCCESS"
          ? `Extracción real: ${r.found} encontradas (${r.databank}) · ${r.inserted} nuevas · ${r.unchanged} sin cambios · ${r.quarantined} cuarentena.`
          : `Extracción: ${r?.status ?? "NO DATA"}`
      );
    } catch (e) {
      setMsg(`NO DATA (extract) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setBusy(false);
    }
  }, [project, databank]);

  const fetchSource = useCallback(async () => {
    const p = project.trim();
    const db = databank.trim();
    const name = selected?.source_strategy_name ?? selected?.name ?? "";
    if (!p || !name) {
      setMsg("Se requieren proyecto y estrategia para /source.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.get<SourceResponse>(
        `/api/v2/strategy-lab/source/${encodeURIComponent(p)}/${encodeURIComponent(name)}${
          db ? `?databank=${encodeURIComponent(db)}` : ""
        }`
      );
      setSource(r);
      setMsg(
        r?.status === "SUCCESS"
          ? `Source real obtenida · sha256 ${short(r.source_sha256)}`
          : `Source: ${r?.status ?? "NO DATA"}${r?.error ? ` · ${r.error}` : ""}`
      );
    } catch (e) {
      setSource(null);
      setMsg(`NO DATA (source) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setBusy(false);
    }
  }, [project, databank, selected]);

  const bindDataset = useCallback(async () => {
    if (!selected?.strategy_id) {
      setMsg("Selecciona una estrategia real del catálogo.");
      return;
    }
    if (!datasetId.trim()) {
      setMsg("Indica un dataset_id real aprobado.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.post<BindingResponse>(
        `/api/v2/strategy-lab/strategies/${encodeURIComponent(selected.strategy_id)}/bind-dataset`,
        { dataset_id: datasetId.trim() }
      );
      setBinding(r);
      setMsg(r?.status === "BOUND" ? `BINDING real · ${r.binding_id} · hash ${short(r.dataset_hash)}` : `Binding: ${r?.status ?? "NO DATA"}`);
    } catch (e) {
      setBinding(null);
      setMsg(`NO DATA (bind-dataset) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setBusy(false);
    }
  }, [selected, datasetId]);

  const loadBinding = useCallback(async () => {
    if (!selected?.strategy_id) {
      setMsg("Selecciona una estrategia real del catálogo.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      const r = await api.get<BindingResponse>(
        `/api/v2/strategy-lab/strategies/${encodeURIComponent(selected.strategy_id)}/binding`
      );
      setBinding(r);
      setMsg(r?.status === "BOUND" ? `Binding actual: ${r.dataset_id}` : "Binding actual: UNBOUND");
    } catch (e) {
      setBinding(null);
      setMsg(`NO DATA (binding) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setBusy(false);
    }
  }, [selected]);

  const copyJSON = (obj: any, label: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(JSON.stringify(obj, null, 2));
      setCopiedRaw(label);
      setTimeout(() => setCopiedRaw(null), 2000);
    }
  };

  const healthDot = health === "ONLINE" ? "bg-emerald-400" : health === "OFFLINE" ? "bg-rose-500" : "bg-slate-500";
  const healthText = health === "ONLINE" ? "text-emerald-300" : health === "OFFLINE" ? "text-rose-300" : "text-slate-400";
  useEffect(() => {
    void checkHealth();
  }, [checkHealth]);

  return (
    <section
      className="rounded-2xl border border-white/[0.08] bg-[#090d16]/90 p-5 shadow-xl backdrop-blur-xl space-y-4"
      data-testid="sqx-tools-panel"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-black text-white">Integración StrategyQuant X MCP</h2>
            <p className="text-xs text-slate-400">Extracción, inspección de código fuente y enlace determinista de datasets</p>
          </div>
        </div>

        <div className="flex items-center gap-2.5" data-testid="sqx-health">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-[#050811] border border-white/[0.08]">
            <span className="relative flex h-2 w-2">
              {health === "ONLINE" && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${healthDot}`} />
            </span>
            <span className={`font-mono text-xs font-black ${healthText}`}>
              {health === "CHECKING" ? "COMPROBANDO…" : health}
            </span>
          </div>
          <button
            onClick={() => void checkHealth()}
            disabled={busy}
            className="rounded-xl border border-white/[0.1] bg-slate-900/90 px-3 py-1.5 font-mono text-xs font-bold text-slate-200 transition hover:bg-slate-800 active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3 h-3 ${health === "CHECKING" ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {healthDetail && (
        <p className="break-all font-mono text-xs text-slate-400 bg-[#050811] p-2.5 rounded-xl border border-white/[0.06]">
          <span className="text-slate-500 font-bold uppercase mr-1.5">SQX MCP:</span>
          {healthDetail}
        </p>
      )}

      {msg && (
        <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-800/50 text-cyan-200 font-mono text-xs">
          {msg}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-2.5 font-mono">
        <input
          value={project}
          onChange={(e) => setProject(e.target.value)}
          placeholder="Proyecto SQX real (ej. Futures_Portfolio)"
          className="md:col-span-4 rounded-xl border border-white/[0.08] bg-[#050811] px-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-cyan-500 transition"
        />
        <select
          value={databank}
          onChange={(e) => setDatabank(e.target.value)}
          data-testid="sqx-databank-select"
          className="md:col-span-3 rounded-xl border border-white/[0.08] bg-[#050811] px-3 py-2 text-xs text-slate-200 outline-none focus:border-cyan-500 transition cursor-pointer"
        >
          {databanks === null ? (
            <option value="">Databank…</option>
          ) : databanks.length === 0 ? (
            <option value="NO DATA">NO DATA</option>
          ) : (
            databanks.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))
          )}
        </select>
        <button
          onClick={() => void loadDatabanks()}
          disabled={busy}
          className="md:col-span-2 rounded-xl border border-white/[0.1] bg-slate-900 px-3 py-2 font-mono text-xs font-bold text-slate-200 transition hover:bg-slate-800 active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          Listar Bancos
        </button>
        <button
          onClick={() => void extractDatabank()}
          disabled={busy}
          data-testid="sqx-extract-btn"
          className="md:col-span-2 rounded-xl bg-emerald-800 hover:bg-emerald-700 px-3 py-2 font-mono text-xs font-bold text-white shadow-md transition active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          Extraer Banco
        </button>
        <button
          onClick={() => void fetchSource()}
          disabled={busy}
          data-testid="sqx-source-btn"
          className="md:col-span-1 rounded-xl border border-cyan-500/40 bg-cyan-950/40 text-cyan-300 hover:bg-cyan-900/50 px-3 py-2 font-mono text-xs font-bold transition active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          /source
        </button>
      </div>

      <div className="flex flex-col gap-2.5 sm:flex-row font-mono">
        <input
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
          placeholder="dataset_id real aprobado (ej. BTCUSDT_1H_CANONICAL)"
          className="min-w-0 flex-1 rounded-xl border border-white/[0.08] bg-[#050811] px-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-cyan-500 transition"
        />
        <button
          onClick={() => void bindDataset()}
          disabled={busy}
          data-testid="sqx-bind-btn"
          className="rounded-xl bg-emerald-800 hover:bg-emerald-700 px-4 py-2 font-mono text-xs font-bold text-white shadow-md transition active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          /bind-dataset
        </button>
        <button
          onClick={() => void loadBinding()}
          disabled={busy}
          className="rounded-xl border border-white/[0.1] bg-slate-900 px-4 py-2 font-mono text-xs font-bold text-slate-200 transition hover:bg-slate-800 active:scale-95 disabled:opacity-50 cursor-pointer"
        >
          Ver Binding
        </button>
      </div>

      <div className="font-mono text-xs text-slate-500 flex items-center justify-between">
        <div>
          Estrategia seleccionada:{" "}
          {selected ? (
            <span className="font-bold text-cyan-300">{selected.strategy_id}</span>
          ) : (
            <span className="text-slate-600">ninguna</span>
          )}
        </div>
      </div>

      {source && (
        <div className="relative">
          <div className="flex justify-between items-center bg-[#050811] px-3 py-1.5 rounded-t-xl border-t border-x border-white/[0.08] text-[10px] font-mono text-slate-400">
            <span>/source Payload SQX</span>
            <button
              onClick={() => copyJSON(source, "source")}
              className="flex items-center gap-1 text-slate-400 hover:text-white transition cursor-pointer"
            >
              {copiedRaw === "source" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedRaw === "source" ? "Copiado" : "Copiar"}</span>
            </button>
          </div>
          <pre className="max-h-40 overflow-auto break-all rounded-b-xl border border-white/[0.08] bg-[#050811] p-3 font-mono text-[10.5px] text-slate-300 shadow-inner">
            {JSON.stringify(source, null, 2).slice(0, 1200)}
          </pre>
        </div>
      )}

      {binding && (
        <div className="relative">
          <div className="flex justify-between items-center bg-[#050811] px-3 py-1.5 rounded-t-xl border-t border-x border-white/[0.08] text-[10px] font-mono text-slate-400">
            <span>/binding Info</span>
            <button
              onClick={() => copyJSON(binding, "binding")}
              className="flex items-center gap-1 text-slate-400 hover:text-white transition cursor-pointer"
            >
              {copiedRaw === "binding" ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedRaw === "binding" ? "Copiado" : "Copiar"}</span>
            </button>
          </div>
          <pre className="max-h-40 overflow-auto break-all rounded-b-xl border border-white/[0.08] bg-[#050811] p-3 font-mono text-[10.5px] text-slate-300 shadow-inner">
            {JSON.stringify(binding, null, 2).slice(0, 1200)}
          </pre>
        </div>
      )}
    </section>
  );
}
