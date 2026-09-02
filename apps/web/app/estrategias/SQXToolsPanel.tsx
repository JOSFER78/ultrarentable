"use client";

/**
 * apps/web/app/estrategias/SQXToolsPanel.tsx
 *
 * Controles técnicos reales de StrategyQuant X (proyecto, databank, extraer,
 * /source, /bind-dataset). Uso interno: vive dentro de un <details> plegado
 * en /estrategias/generacion, nunca en la página maestra (mandato de Emilio
 * 2026-09-02: "no es intuitivo, no se entiende nada" sobre el panel técnico).
 *
 * REAL-ONLY: cada botón llama a la API real; sin esa llamada no hay mensaje.
 */

import { useCallback, useState } from "react";
import { api, extractStrategyLabProject } from "@/lib/api";

interface SourceResponse {
  status: string;
  source_sha256?: string;
  error?: string;
}

interface BindingResponse {
  status: string;
  dataset_id?: string;
  error?: string;
}

const databankName = (d: { name: string } | string): string => (typeof d === "string" ? d : d.name);

export default function SQXToolsPanel({ onExtraccion }: { onExtraccion?: () => void }) {
  const [proyecto, setProyecto] = useState("");
  const [databanks, setDatabanks] = useState<string[] | null>(null);
  const [databank, setDatabank] = useState("");
  const [estrategiaSource, setEstrategiaSource] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [candidataId, setCandidataId] = useState("");
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const cargarDatabanks = useCallback(async () => {
    const p = proyecto.trim();
    if (!p) return setMensaje("Indica un proyecto SQX real.");
    setOcupado(true);
    try {
      const r = await api.get<{ databanks: Array<{ name: string } | string> }>(
        `/api/v1/sqx/projects/${encodeURIComponent(p)}/databanks`
      );
      const nombres = Array.isArray(r?.databanks) ? r.databanks.map(databankName).filter(Boolean) : [];
      setDatabanks(nombres);
      setDatabank(nombres[0] ?? "");
      setMensaje(nombres.length ? `Databanks: ${nombres.join(", ")}` : "Sin databanks.");
    } catch (e) {
      setDatabanks([]);
      setMensaje(`sin evidencia · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setOcupado(false);
    }
  }, [proyecto]);

  const extraer = useCallback(async () => {
    const p = proyecto.trim();
    if (!p) return setMensaje("Indica un proyecto SQX real.");
    setOcupado(true);
    try {
      const r = await extractStrategyLabProject(p, databank.trim() || undefined);
      setMensaje(
        r?.status === "SUCCESS"
          ? `Extracción: ${r.found} encontradas · ${r.inserted} nuevas · ${r.quarantined} en cuarentena.`
          : `Extracción: ${r?.status ?? "sin evidencia"}`
      );
      onExtraccion?.();
    } catch (e) {
      setMensaje(`sin evidencia (extraer) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setOcupado(false);
    }
  }, [proyecto, databank, onExtraccion]);

  const obtenerSource = useCallback(async () => {
    const p = proyecto.trim();
    const nombre = estrategiaSource.trim();
    if (!p || !nombre) return setMensaje("Se requieren proyecto y nombre de estrategia para /source.");
    setOcupado(true);
    try {
      const db = databank.trim();
      const r = await api.get<SourceResponse>(
        `/api/v2/strategy-lab/source/${encodeURIComponent(p)}/${encodeURIComponent(nombre)}${db ? `?databank=${encodeURIComponent(db)}` : ""}`
      );
      setMensaje(r?.status === "SUCCESS" ? `Source obtenida · sha256 ${(r.source_sha256 || "").slice(0, 16)}…` : "Source: sin evidencia.");
    } catch (e) {
      setMensaje(`sin evidencia (source) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setOcupado(false);
    }
  }, [proyecto, databank, estrategiaSource]);

  const vincularDataset = useCallback(async () => {
    const cid = candidataId.trim();
    const did = datasetId.trim();
    if (!cid || !did) return setMensaje("Indica candidate_id y dataset_id.");
    setOcupado(true);
    try {
      const r = await api.post<BindingResponse>(`/api/v2/strategy-lab/strategies/${encodeURIComponent(cid)}/bind-dataset`, { dataset_id: did });
      setMensaje(r?.status === "BOUND" ? `Binding asociado · dataset ${r.dataset_id}` : "Binding: sin evidencia.");
    } catch (e) {
      setMensaje(`sin evidencia (bind) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setOcupado(false);
    }
  }, [candidataId, datasetId]);

  const estiloInput: React.CSSProperties = { padding: "4px 7px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "3px", color: "var(--text-1)", fontSize: "12px" };
  const estiloBoton: React.CSSProperties = { padding: "4px 9px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "3px", color: "var(--text-1)", fontSize: "12px", cursor: "pointer" };
  const estiloBotonPrimario: React.CSSProperties = { ...estiloBoton, background: "var(--surface-3)", border: "1px solid var(--border-strong)", fontWeight: 600 };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
        <input type="text" value={proyecto} onChange={(e) => setProyecto(e.target.value)} placeholder="Proyecto SQX (ej. Ultra_Matrix)" style={{ ...estiloInput, minWidth: "200px" }} />
        <select value={databank} onChange={(e) => setDatabank(e.target.value)} style={estiloInput}>
          {databanks === null ? <option value="">Databank…</option> : databanks.length === 0 ? <option value="">sin evidencia</option> : databanks.map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
        <button onClick={() => void cargarDatabanks()} disabled={ocupado} style={estiloBoton}>Cargar databanks</button>
        <button onClick={() => void extraer()} disabled={ocupado} style={estiloBotonPrimario}>Extraer</button>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
        <input type="text" value={estrategiaSource} onChange={(e) => setEstrategiaSource(e.target.value)} placeholder="Nombre de estrategia (para /source)" style={{ ...estiloInput, minWidth: "220px" }} />
        <button onClick={() => void obtenerSource()} disabled={ocupado} style={estiloBoton}>/source</button>
      </div>

      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center" }}>
        <input type="text" value={candidataId} onChange={(e) => setCandidataId(e.target.value)} placeholder="candidate_id" style={estiloInput} />
        <input type="text" value={datasetId} onChange={(e) => setDatasetId(e.target.value)} placeholder="dataset_id" style={estiloInput} />
        <button onClick={() => void vincularDataset()} disabled={ocupado} style={estiloBotonPrimario}>/bind-dataset</button>
      </div>

      {mensaje && <div style={{ fontSize: "11.5px", fontFamily: "monospace", color: "var(--text-2)" }}>{mensaje}</div>}
    </div>
  );
}
