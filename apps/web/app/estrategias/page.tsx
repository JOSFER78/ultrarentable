"use client";

/**
 * apps/web/app/estrategias/page.tsx
 * Página Maestra M1-M4 de Inteligencia Cuantitativa (Estilo Terminal Orca / Claude Code).
 *
 * ZERO-MOCKS · REAL-ONLY · SIN DATOS INVENTADOS
 * Cumple: docs/18_STRATEGIES_PAGE_SPEC.md, docs/19_UI_STYLE_SPEC.md, Mandato de Emilio (2026-09-02).
 */

import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  getCandidatosCanonicos,
  getStrategyLabOverview,
  getStrategyLabSQXStatus,
  getStrategyLabStrategies,
  extractStrategyLabProject,
  getDiscoveryStatus,
  getLineageTree,
  api,
  type CandidatoCanonico,
  type StrategyLabOverview,
  type StrategyLabRecord,
  type LineageTreeResponse,
} from "@/lib/api";
import { auditarCandidata, mostrar, type AuditoriaCandidata } from "./verificacion";

const CERTIFIED_STATUSES = new Set(["CERTIFIED_CURRENT", "APPROVED_CURRENT_ENGINE"]);
const REJECTED_PREFIXES = ["REJECTED_", "BUSTED", "FAILED"];
const isCertified = (s: string) => CERTIFIED_STATUSES.has(s);
const isRejected = (s: string) => REJECTED_PREFIXES.some((p) => s.startsWith(p));
const databankName = (d: { name: string } | string): string => (typeof d === "string" ? d : d.name);

/**
 * Rendimiento OOS mensual/anual. Solo devuelve numero cuando la API confirma que la duracion
 * OOS es REAL (`oos_months_source === "REAL"`); si la duracion esta estimada, el porcentaje
 * seria una suposicion y aqui vale mas un NO EVIDENCE honesto (docs/19 -4, REAL-ONLY).
 */
const rendimientoOos = (
  c: CandidatoCanonico,
  campo: "monthly_roi_pct" | "annualized_roi_pct",
): number | null => {
  const oos = c.metrics?.out_of_sample;
  if (!oos || oos.oos_months_source !== "REAL") return null;
  const v = oos[campo];
  return typeof v === "number" && Number.isFinite(v) ? v : null;
};

const celdaRendimiento = (v: number | null) => ({
  texto: v === null ? "NO EVIDENCE" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`,
  color: v === null ? "var(--text-3)" : v >= 0 ? "var(--profit)" : "var(--loss)",
});

interface FilaCandidato { c: CandidatoCanonico; a: AuditoriaCandidata }
type TabModulo = "M1" | "M2" | "M3" | "M4";

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

const GATES_LISTA = [
  { id: "G01", n: "Identidad Canónica", c: "AST parseado + SHA-256 inmutable" },
  { id: "G02", n: "Salud Estructural", c: "Reglas acotadas, SL obligatorio, 0 overfit" },
  { id: "G03", n: "Binding Dataset", c: "Dataset verificado con hash SHA-256" },
  { id: "G04", n: "Backtest Canónico", c: "Motor >= 5.17.0 barra a barra" },
  { id: "G05", n: "Política Intradía", c: "Cierre de sesión diario obligatorio (Flat)" },
  { id: "G06", n: "Rendimiento IS", c: "PF IS >= 1.30, ops IS >= 300" },
  { id: "G07", n: "Verificación OOS", c: "Ops OOS >= 200, PF OOS >= 1.25, OOS/IS >= 0.50" },
  { id: "G08", n: "Stress Prop Firm", c: "Simulación de examen flotante, P(pass) >= 60%" },
  { id: "G09", n: "Robustez Monte Carlo", c: "P(ruina) <= 20% en 6 meses" },
  { id: "G10", n: "Diversidad de Cartera", c: "Correlación temporal < 0.60 vs portfolio" },
  { id: "G11", n: "Certificación Activa", c: "11/11 gates aprobados en motor vigente" },
];

export default function PaginaEstrategiasMaestra() {
  const [candidatos, setCandidatos] = useState<FilaCandidato[]>([]);
  const [overview, setOverview] = useState<StrategyLabOverview | null>(null);
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedUtc, setLastUpdatedUtc] = useState<string | null>(null);

  // Filtros y ordenación
  const [busqueda, setBusqueda] = useState("");
  const [filtroRuta, setFiltroRuta] = useState("ALL");
  const [filtroEstado, setFiltroEstado] = useState("ALL");
  const [filtroTf, setFiltroTf] = useState("ALL");
  const [soloPlausibles, setSoloPlausibles] = useState(false);
  const [ordenCampo, setOrdenCampo] = useState("gates_passed_count");
  const [ordenAsc, setOrdenAsc] = useState(false);

  // Selección y tabs
  const [seleccion, setSeleccion] = useState<FilaCandidato | null>(null);
  const [copiadoId, setCopiadoId] = useState<string | null>(null);
  const [moduloActivo, setModuloActivo] = useState<TabModulo>("M1");

  // M1 SQX
  const [sqxHealth, setSqxHealth] = useState<"ONLINE" | "OFFLINE" | "NO EVIDENCE" | "CHECKING">("CHECKING");
  const [sqxDetail, setSqxDetail] = useState("");
  const [sqxProject, setSqxProject] = useState("");
  const [sqxDatabanks, setSqxDatabanks] = useState<string[] | null>(null);
  const [sqxDatabank, setSqxDatabank] = useState("");
  const [sqxDatasetId, setSqxDatasetId] = useState("");
  const [sqxMsg, setSqxMsg] = useState<string | null>(null);
  const [sqxBusy, setSqxBusy] = useState(false);
  const [sqxExtractions, setSqxExtractions] = useState<StrategyLabRecord[]>([]);

  // M2 Linaje
  const [lineageTree, setLineageTree] = useState<LineageTreeResponse | null>(null);
  const [lineageLoading, setLineageLoading] = useState(false);
  const [lineageError, setLineageError] = useState<string | null>(null);

  const copiarTexto = useCallback((texto: string, label: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(texto);
      setCopiadoId(label);
      setTimeout(() => setCopiadoId(null), 1500);
    }
  }, []);

  const refrescarPrincipal = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [candData, overData, discData] = await Promise.all([
        getCandidatosCanonicos(1000),
        getStrategyLabOverview().catch(() => null),
        getDiscoveryStatus().catch(() => null),
      ]);
      const auditadas = candData.map((c) => ({ c, a: auditarCandidata(c as unknown as Record<string, unknown>) }));
      setCandidatos(auditadas);
      setOverview(overData);
      setEngineVersion(discData?.current_engine_version || null);
      setLastUpdatedUtc(new Date().toUTCString());
      if (auditadas.length > 0) {
        setSeleccion((prev) => prev || auditadas.find((f) => isCertified(f.c.status)) || auditadas[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al consultar la API canónica.");
    } finally {
      setLoading(false);
    }
  }, []);

  const comprobarSaludSqx = useCallback(async () => {
    setSqxHealth("CHECKING");
    try {
      const r = await getStrategyLabSQXStatus();
      if (r?.status === "ONLINE" || (typeof r?.result === "object" && (r.result as { status?: string })?.status === "ONLINE")) {
        setSqxHealth("ONLINE");
        setSqxDetail(r.source || "SQX Bridge activo");
      } else {
        setSqxHealth("OFFLINE");
        setSqxDetail(r?.error || "SQX Bridge no conectado");
      }
    } catch (e) {
      setSqxHealth("NO EVIDENCE");
      setSqxDetail(e instanceof Error ? e.message : "Endpoint no accesible");
    }
  }, []);

  const cargarDatabanksSqx = useCallback(async () => {
    const p = sqxProject.trim();
    if (!p) return setSqxMsg("Indica un proyecto SQX real.");
    setSqxBusy(true);
    try {
      const r = await api.get<{ databanks: Array<{ name: string } | string> }>(`/api/v1/sqx/projects/${encodeURIComponent(p)}/databanks`);
      const names = Array.isArray(r?.databanks) ? r.databanks.map(databankName).filter(Boolean) : [];
      setSqxDatabanks(names);
      setSqxDatabank(names[0] ?? "");
      setSqxMsg(names.length ? `Databanks: ${names.join(", ")}` : "Sin databanks.");
    } catch (e) {
      setSqxDatabanks([]);
      setSqxMsg(`NO DATA · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [sqxProject]);

  const extraerDatabankSqx = useCallback(async () => {
    const p = sqxProject.trim();
    if (!p) return setSqxMsg("Indica un proyecto SQX real.");
    setSqxBusy(true);
    try {
      const r = await extractStrategyLabProject(p, sqxDatabank.trim() || undefined);
      setSqxMsg(r?.status === "SUCCESS" ? `Extracción: ${r.found} encontradas · ${r.inserted} nuevas · ${r.quarantined} en cuarentena.` : `Extracción: ${r?.status ?? "NO DATA"}`);
      void refrescarPrincipal();
    } catch (e) {
      setSqxMsg(`NO DATA (extract) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [sqxProject, sqxDatabank, refrescarPrincipal]);

  const obtenerSourceSqx = useCallback(async () => {
    const p = sqxProject.trim();
    const name = seleccion?.c.name || "";
    if (!p || !name) return setSqxMsg("Se requieren proyecto y nombre para /source.");
    setSqxBusy(true);
    try {
      const db = sqxDatabank.trim();
      const r = await api.get<SourceResponse>(`/api/v2/strategy-lab/source/${encodeURIComponent(p)}/${encodeURIComponent(name)}${db ? `?databank=${encodeURIComponent(db)}` : ""}`);
      setSqxMsg(r?.status === "SUCCESS" ? `Source obtenida · sha256 ${r.source_sha256?.slice(0, 16)}...` : "Source: NO DATA");
    } catch (e) {
      setSqxMsg(`NO DATA (source) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [sqxProject, sqxDatabank, seleccion]);

  const vincularDatasetSqx = useCallback(async () => {
    if (!seleccion?.c.candidate_id || !sqxDatasetId.trim()) return setSqxMsg("Selecciona estrategia e indica dataset_id.");
    setSqxBusy(true);
    try {
      const r = await api.post<BindingResponse>(`/api/v2/strategy-lab/strategies/${encodeURIComponent(seleccion.c.candidate_id)}/bind-dataset`, { dataset_id: sqxDatasetId.trim() });
      setSqxMsg(r?.status === "BOUND" ? `Binding asociado · dataset ${r.dataset_id}` : "Binding: NO DATA");
    } catch (e) {
      setSqxMsg(`NO DATA (bind) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [seleccion, sqxDatasetId]);

  const consultarLinajeM2 = useCallback(async (strategyId: string) => {
    if (!strategyId) return;
    setLineageLoading(true);
    setLineageError(null);
    try {
      const data = await getLineageTree(strategyId);
      setLineageTree(data);
    } catch (e) {
      setLineageTree(null);
      setLineageError(e instanceof Error ? e.message : "Error linaje.");
    } finally {
      setLineageLoading(false);
    }
  }, []);

  useEffect(() => {
    void refrescarPrincipal();
    void comprobarSaludSqx();
    getStrategyLabStrategies(10).then((res) => setSqxExtractions(res?.strategies || [])).catch(() => setSqxExtractions([]));
  }, [refrescarPrincipal, comprobarSaludSqx]);

  useEffect(() => {
    if (seleccion?.c.candidate_id && moduloActivo === "M2") void consultarLinajeM2(seleccion.c.candidate_id);
  }, [seleccion, moduloActivo, consultarLinajeM2]);

  const certificadasCount = useMemo(() => candidatos.filter((f) => isCertified(f.c.status)).length, [candidatos]);

  const candidatasVisibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return candidatos
      .filter((f) => {
        if (filtroRuta !== "ALL" && f.c.route?.toUpperCase() !== filtroRuta) return false;
        if (filtroEstado === "CERTIFIED" && !isCertified(f.c.status)) return false;
        if (filtroEstado === "REJECTED" && !isRejected(f.c.status)) return false;
        if (filtroEstado === "LEGACY" && !f.c.status?.startsWith("LEGACY_")) return false;
        if (filtroEstado === "OTHER" && (isCertified(f.c.status) || isRejected(f.c.status) || f.c.status?.startsWith("LEGACY_"))) return false;
        if (filtroTf !== "ALL" && f.c.timeframe !== filtroTf) return false;
        if (soloPlausibles && f.a.tieneProblemas) return false;
        if (q && !`${f.c.candidate_id} ${f.c.name} ${f.c.symbol} ${f.c.archetype || ""} ${f.c.route} ${f.c.status}`.toLowerCase().includes(q)) return false;
        return true;
      })
      .sort((a, b) => {
        if (ordenCampo === "monthly_roi_pct" || ordenCampo === "annualized_roi_pct") {
          // Las filas sin evidencia caen siempre al final, no se cuelan como si fueran 0.
          const rA = rendimientoOos(a.c, ordenCampo);
          const rB = rendimientoOos(b.c, ordenCampo);
          if (rA === null && rB === null) return 0;
          if (rA === null) return 1;
          if (rB === null) return -1;
          return ordenAsc ? rA - rB : rB - rA;
        }
        const vA = a.c[ordenCampo as keyof CandidatoCanonico] ?? (ordenCampo === "max_dd_oos_pct" ? 9999 : -1);
        const vB = b.c[ordenCampo as keyof CandidatoCanonico] ?? (ordenCampo === "max_dd_oos_pct" ? 9999 : -1);
        if (typeof vA === "number" && typeof vB === "number") return ordenAsc ? vA - vB : vB - vA;
        return ordenAsc ? String(vA).localeCompare(String(vB)) : String(vB).localeCompare(String(vA));
      });
  }, [candidatos, busqueda, filtroRuta, filtroEstado, filtroTf, soloPlausibles, ordenCampo, ordenAsc]);

  const alternarOrden = (campo: string) => {
    if (ordenCampo === campo) setOrdenAsc(!ordenAsc);
    else { setOrdenCampo(campo); setOrdenAsc(false); }
  };

  const apiConectada = !error && Boolean(engineVersion);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-1)", padding: "16px", fontFamily: "ui-sans-serif, system-ui, sans-serif", fontSize: "13px" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "14px" }}>

        {/* 1. CABECERA HONESTA */}
        <header style={{ borderBottom: "1px solid var(--border)", paddingBottom: "10px", display: "flex", flexDirection: "column", gap: "6px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <h1 style={{ fontSize: "15px", fontWeight: 700, margin: 0 }}>Estrategias</h1>
              <span style={{ fontSize: "12px", color: "var(--text-3)" }}>Página Maestra M1-M4 · Catálogo Canónico</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", fontFamily: "monospace", flexWrap: "wrap" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                <span style={{ width: "6px", height: "6px", borderRadius: "2px", background: apiConectada ? "var(--profit)" : "var(--loss)" }} />
                <span style={{ color: apiConectada ? "var(--text-2)" : "var(--loss)" }}>API {apiConectada ? "OK" : "ERROR"}</span>
              </span>
              <span style={{ color: "var(--text-3)" }}>·</span>
              <span style={{ color: "var(--text-2)" }}>Certificadas: <strong style={{ color: "var(--text-1)" }}>{certificadasCount}</strong></span>
              <span style={{ color: "var(--text-3)" }}>·</span>
              <span style={{ color: "var(--text-2)" }}>Motor: {engineVersion || "NO DATA"}</span>
              <span style={{ color: "var(--text-3)" }}>·</span>
              <span style={{ color: "var(--text-3)" }}>Última campaña: {lastUpdatedUtc ? lastUpdatedUtc.slice(5, 22) : "NO DATA"}</span>
              <button onClick={() => void refrescarPrincipal()} disabled={loading} style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--text-1)", padding: "2px 8px", borderRadius: "2px", fontSize: "11px", cursor: "pointer" }}>{loading ? "..." : "Recargar"}</button>
            </div>
          </div>
          {error && <div style={{ padding: "4px 8px", background: "var(--loss-dim)", border: "1px solid var(--loss)", color: "var(--loss)", fontSize: "11.5px", fontFamily: "monospace" }}>ERROR API: {error} (Fail-closed · ZERO-MOCKS)</div>}
        </header>

        {/* 2. EMBUDO DE ESTADOS */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px", padding: "6px 10px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "2px", fontSize: "11.5px", fontFamily: "monospace" }}>
          <span style={{ color: "var(--text-3)", textTransform: "uppercase" }}>Embudo</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
            <span>EXTRACTED <strong style={{ color: "var(--text-1)" }}>{overview?.pipeline?.extracted ?? "NO EVIDENCE"}</strong></span>
            <span style={{ color: "var(--text-3)" }}>→</span>
            <span>STRUCTURALLY_VERIFIED <strong style={{ color: "var(--text-1)" }}>{overview?.pipeline?.structurally_verified ?? "NO EVIDENCE"}</strong></span>
            <span style={{ color: "var(--text-3)" }}>→</span>
            <span>BACKTEST_VERIFIED <strong style={{ color: "var(--text-1)" }}>{overview?.pipeline?.backtest_verified ?? "NO EVIDENCE"}</strong></span>
            <span style={{ color: "var(--text-3)" }}>→</span>
            <span>CERTIFIED_CURRENT <strong style={{ color: (overview?.pipeline?.certified_current ?? 0) > 0 ? "var(--profit)" : "var(--text-3)" }}>{overview?.pipeline?.certified_current ?? 0}</strong></span>
          </div>
        </div>

        {/* 3. CATÁLOGO PRINCIPAL (TABLA 1) */}
        <section style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "6px" }}>
            <input type="text" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Filtrar catálogo..." style={{ flex: "1 1 180px", padding: "4px 8px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "12px" }} />
            <div style={{ display: "flex", alignItems: "center", gap: "4px", flexWrap: "wrap" }}>
              <select value={filtroRuta} onChange={(e) => setFiltroRuta(e.target.value)} style={{ padding: "3px 6px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11.5px" }}>
                <option value="ALL">Todas rutas</option><option value="FONDEO">FONDEO</option><option value="ULTRA">ULTRA (EN CONSTRUCCIÓN)</option>
              </select>
              <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)} style={{ padding: "3px 6px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11.5px" }}>
                <option value="ALL">Todos estados</option><option value="CERTIFIED">Certificadas</option><option value="REJECTED">Rechazadas</option><option value="LEGACY">Legacy</option><option value="OTHER">Otras</option>
              </select>
              <select value={filtroTf} onChange={(e) => setFiltroTf(e.target.value)} style={{ padding: "3px 6px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11.5px" }}>
                <option value="ALL">Todos TF</option><option value="1m">1m</option><option value="5m">5m</option><option value="15m">15m</option><option value="1h">1h</option><option value="4h">4h</option>
              </select>
              <label style={{ display: "flex", alignItems: "center", gap: "4px", fontSize: "11.5px", color: "var(--text-2)", cursor: "pointer" }}>
                <input type="checkbox" checked={soloPlausibles} onChange={(e) => setSoloPlausibles(e.target.checked)} /><span>Plausibles</span>
              </label>
              <span style={{ fontSize: "11px", color: "var(--text-3)", fontFamily: "monospace" }}>{candidatasVisibles.length}/{candidatos.length}</span>
            </div>
          </div>

          <div style={{ overflowX: "auto", border: "1px solid var(--border)", background: "var(--surface-1)" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11.5px", textAlign: "left" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--text-2)", fontSize: "10.5px", textTransform: "uppercase" }}>
                  <th onClick={() => alternarOrden("candidate_id")} style={{ padding: "5px 6px", cursor: "pointer" }}>ID {ordenCampo === "candidate_id" ? (ordenAsc ? "^" : "v") : ""}</th>
                  <th onClick={() => alternarOrden("symbol")} style={{ padding: "5px 6px", cursor: "pointer" }}>Símbolo {ordenCampo === "symbol" ? (ordenAsc ? "^" : "v") : ""}</th>
                  <th style={{ padding: "5px 6px" }}>Arquetipo</th>
                  <th onClick={() => alternarOrden("route")} style={{ padding: "5px 6px", cursor: "pointer" }}>Ruta</th>
                  <th onClick={() => alternarOrden("status")} style={{ padding: "5px 6px", cursor: "pointer" }}>Estado</th>
                  <th onClick={() => alternarOrden("gates_passed_count")} style={{ padding: "5px 6px", textAlign: "right", cursor: "pointer" }}>Gates</th>
                  <th onClick={() => alternarOrden("profit_factor_oos")} style={{ padding: "5px 6px", textAlign: "right", cursor: "pointer" }}>PF OOS</th>
                  <th onClick={() => alternarOrden("trades_oos")} style={{ padding: "5px 6px", textAlign: "right", cursor: "pointer" }}>Ops OOS</th>
                  <th onClick={() => alternarOrden("max_dd_oos_pct")} style={{ padding: "5px 6px", textAlign: "right", cursor: "pointer" }}>DD OOS</th>
                  <th onClick={() => alternarOrden("monthly_roi_pct")} title="Rendimiento OOS mensual compuesto (CAGR mensual). NO EVIDENCE si la duración OOS no es real." style={{ padding: "5px 6px", textAlign: "right", cursor: "pointer" }}>Rend. mes {ordenCampo === "monthly_roi_pct" ? (ordenAsc ? "^" : "v") : ""}</th>
                  <th onClick={() => alternarOrden("annualized_roi_pct")} title="Rendimiento OOS anualizado (CAGR). NO EVIDENCE si la duración OOS no es real." style={{ padding: "5px 6px", textAlign: "right", cursor: "pointer" }}>Rend. año {ordenCampo === "annualized_roi_pct" ? (ordenAsc ? "^" : "v") : ""}</th>
                  <th style={{ padding: "5px 6px" }}>Hash</th>
                  <th style={{ padding: "5px 6px" }}>Dataset</th>
                </tr>
              </thead>
              <tbody>
                {loading && candidatos.length === 0 && <tr><td colSpan={13} style={{ padding: "12px", textAlign: "center", color: "var(--text-3)" }}>Cargando catálogo canónico...</td></tr>}
                {!loading && candidatasVisibles.length === 0 && <tr><td colSpan={13} style={{ padding: "12px", textAlign: "center", color: "var(--text-3)" }}>NO EVIDENCE con los filtros actuales.</td></tr>}
                {candidatasVisibles.map((fila) => {
                  const c = fila.c;
                  const esCert = isCertified(c.status);
                  const esRech = isRejected(c.status);
                  const esUltra = c.route?.toUpperCase() === "ULTRA";
                  const isSel = seleccion?.c.candidate_id === c.candidate_id;
                  const colorEstado = esCert ? "var(--profit)" : esRech ? "var(--loss)" : "var(--text-2)";
                  const pfVal = c.profit_factor_oos;
                  const colorPf = pfVal === null || pfVal === undefined ? "var(--text-3)" : pfVal >= 1.0 ? "var(--profit)" : "var(--loss)";
                  const gatesStr = c.gates_passed_count !== null && c.gates_passed_count !== undefined ? `${c.gates_passed_count}/11` : "NO EVIDENCE";
                  const rendMes = rendimientoOos(c, "monthly_roi_pct");
                  const rendAnio = rendimientoOos(c, "annualized_roi_pct");

                  return (
                    <tr key={c.candidate_id} onClick={() => setSeleccion(fila)} style={{ borderBottom: "1px solid var(--border)", background: isSel ? "var(--surface-3)" : "transparent", opacity: esUltra ? 0.7 : 1, cursor: "pointer" }}>
                      <td style={{ padding: "4px 6px", fontFamily: "monospace" }}>
                        <span title={c.candidate_id}>{c.candidate_id.length > 14 ? `${c.candidate_id.slice(0, 12)}...` : c.candidate_id}</span>
                        <button onClick={(e) => { e.stopPropagation(); copiarTexto(c.candidate_id, c.candidate_id); }} style={{ marginLeft: "3px", background: "none", border: "none", color: copiadoId === c.candidate_id ? "var(--profit)" : "var(--text-3)", cursor: "pointer", fontSize: "10px" }}>{copiadoId === c.candidate_id ? "OK" : "cp"}</button>
                      </td>
                      <td style={{ padding: "4px 6px" }}><strong style={{ color: "var(--text-1)" }}>{c.symbol}</strong> <span style={{ color: "var(--text-3)" }}>{c.timeframe}</span></td>
                      <td style={{ padding: "4px 6px", color: c.archetype ? "var(--text-2)" : "var(--text-3)" }}>{c.archetype || "NO EVIDENCE"}</td>
                      <td style={{ padding: "4px 6px", color: "var(--text-2)" }}>{c.route} {esUltra ? <span style={{ color: "var(--text-3)", fontSize: "9.5px" }}>[EN CONSTRUCCIÓN]</span> : null}</td>
                      <td style={{ padding: "4px 6px", color: colorEstado, fontWeight: esCert ? 600 : 400 }}>{c.status}</td>
                      <td style={{ padding: "4px 6px", textAlign: "right", fontFamily: "monospace", color: c.gates_passed_count !== null ? "var(--text-2)" : "var(--text-3)" }}>{gatesStr}</td>
                      <td style={{ padding: "4px 6px", textAlign: "right", fontFamily: "monospace", color: colorPf }}>{pfVal !== null && pfVal !== undefined ? pfVal.toFixed(2) : "NO EVIDENCE"}</td>
                      <td style={{ padding: "4px 6px", textAlign: "right", fontFamily: "monospace", color: c.trades_oos !== null ? "var(--text-2)" : "var(--text-3)" }}>{c.trades_oos ?? "NO EVIDENCE"}</td>
                      <td style={{ padding: "4px 6px", textAlign: "right", fontFamily: "monospace", color: c.max_dd_oos_pct !== null ? "var(--loss)" : "var(--text-3)" }}>{c.max_dd_oos_pct !== null && c.max_dd_oos_pct !== undefined ? `${c.max_dd_oos_pct.toFixed(2)}%` : "NO EVIDENCE"}</td>
                      <td style={{ padding: "4px 6px", textAlign: "right", fontFamily: "monospace", color: celdaRendimiento(rendMes).color }} title={rendMes === null ? "Sin duración OOS real en el scorecard: el porcentaje sería una estimación." : undefined}>{celdaRendimiento(rendMes).texto}</td>
                      <td style={{ padding: "4px 6px", textAlign: "right", fontFamily: "monospace", color: celdaRendimiento(rendAnio).color }} title={rendAnio === null ? "Sin duración OOS real en el scorecard: el porcentaje sería una estimación." : undefined}>{celdaRendimiento(rendAnio).texto}</td>
                      <td style={{ padding: "4px 6px", fontFamily: "monospace", color: c.strategy_sha256 ? "var(--text-2)" : "var(--text-3)" }}>{c.strategy_sha256 ? c.strategy_sha256.slice(0, 8) : "NO EVIDENCE"}</td>
                      <td style={{ padding: "4px 6px", fontFamily: "monospace", color: c.dataset_id ? "var(--text-2)" : "var(--text-3)" }} title={c.dataset_id || undefined}>{c.dataset_id ? (c.dataset_id.length > 12 ? `${c.dataset_id.slice(0, 10)}...` : c.dataset_id) : "NO EVIDENCE"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {seleccion && (
            <div style={{ padding: "8px 10px", background: "var(--surface-1)", border: "1px solid var(--border)", fontSize: "11.5px", display: "flex", flexDirection: "column", gap: "6px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "4px", borderBottom: "1px solid var(--border)", paddingBottom: "4px" }}>
                <span><strong>{seleccion.c.name}</strong> ({seleccion.c.candidate_id}) · {seleccion.c.symbol} {seleccion.c.timeframe} · {seleccion.c.route}</span>
                <span style={{ color: "var(--text-3)", fontFamily: "monospace" }}>Dataset: {seleccion.c.dataset_id || "NO EVIDENCE"} · SHA: {seleccion.c.strategy_sha256 || "NO EVIDENCE"}</span>
              </div>
              <div style={{ display: "flex", gap: "14px", flexWrap: "wrap", fontFamily: "monospace" }}>
                <span>PF OOS: <strong style={{ color: seleccion.a.profitFactor.veredicto === "NO_PLAUSIBLE" ? "var(--loss)" : "var(--text-1)" }}>{mostrar(seleccion.a.profitFactor)}</strong></span>
                <span>DD OOS: <strong style={{ color: "var(--loss)" }}>{mostrar(seleccion.a.drawdown, "%")}</strong></span>
                <span>Beneficio OOS: <strong style={{ color: seleccion.a.beneficio.veredicto === "NO_PLAUSIBLE" ? "var(--loss)" : "var(--text-1)" }}>{mostrar(seleccion.a.beneficio, " USD")}</strong></span>
                <span>Ops OOS: <strong style={{ color: "var(--text-1)" }}>{mostrar(seleccion.a.muestra, "", 0)}</strong></span>
              </div>
              {seleccion.a.problemas.length > 0 && <div style={{ color: "var(--text-3)", fontSize: "10.5px" }}>Auditoría: {seleccion.a.problemas.join(" · ")}</div>}
            </div>
          )}
        </section>

        {/* 4. SECCIONES MODULARES M1-M4 */}
        <section style={{ borderTop: "1px solid var(--border)", paddingTop: "10px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "flex", gap: "4px", borderBottom: "1px solid var(--border)", paddingBottom: "4px", flexWrap: "wrap" }}>
            {(["M1", "M2", "M3", "M4"] as TabModulo[]).map((tab) => {
              const label = tab === "M1" ? "M1 Generación (SQX)" : tab === "M2" ? "M2 Mejora" : tab === "M3" ? "M3 Valoración Fondeo" : "M4 Meta";
              const activo = moduloActivo === tab;
              return (
                <button key={tab} onClick={() => setModuloActivo(tab)} style={{ padding: "3px 8px", background: activo ? "var(--surface-3)" : "transparent", border: activo ? "1px solid var(--border-strong)" : "1px solid transparent", borderRadius: "2px", color: activo ? "var(--text-1)" : "var(--text-2)", fontSize: "11.5px", fontWeight: activo ? 600 : 400, cursor: "pointer" }}>{label}</button>
              );
            })}
          </div>

          {/* M1: SQX */}
          {moduloActivo === "M1" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", background: "var(--surface-1)", border: "1px solid var(--border)", padding: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                <span style={{ fontWeight: 600 }}>M1 — Generación: StrategyQuant X Bridge</span>
                <span style={{ fontSize: "11px", fontFamily: "monospace", color: sqxHealth === "ONLINE" ? "var(--profit)" : sqxHealth === "OFFLINE" ? "var(--loss)" : "var(--text-3)" }}>SQX MCP: {sqxHealth} ({sqxDetail || "sin detalle"})</span>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>Caudal viable por hora de CPU: <strong>NO DISPONIBLE</strong> (pendiente de endpoint de telemetría).</div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", alignItems: "center" }}>
                <input type="text" value={sqxProject} onChange={(e) => setSqxProject(e.target.value)} placeholder="Proyecto SQX" style={{ padding: "3px 6px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11.5px" }} />
                <select value={sqxDatabank} onChange={(e) => setSqxDatabank(e.target.value)} style={{ padding: "3px 6px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11.5px" }}>
                  {sqxDatabanks === null ? <option value="">Databank...</option> : sqxDatabanks.length === 0 ? <option value="">NO EVIDENCE</option> : sqxDatabanks.map((n) => <option key={n} value={n}>{n}</option>)}
                </select>
                <button onClick={() => void cargarDatabanksSqx()} disabled={sqxBusy} style={{ padding: "3px 6px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11px", cursor: "pointer" }}>Bancos</button>
                <button onClick={() => void extraerDatabankSqx()} disabled={sqxBusy} style={{ padding: "3px 6px", background: "var(--surface-3)", border: "1px solid var(--border-strong)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11px", fontWeight: 600, cursor: "pointer" }}>Extraer</button>
                <button onClick={() => void obtenerSourceSqx()} disabled={sqxBusy} style={{ padding: "3px 6px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-2)", fontSize: "11px", cursor: "pointer" }}>/source</button>
                <input type="text" value={sqxDatasetId} onChange={(e) => setSqxDatasetId(e.target.value)} placeholder="dataset_id" style={{ padding: "3px 6px", background: "var(--surface-2)", border: "1px solid var(--border)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11.5px" }} />
                <button onClick={() => void vincularDatasetSqx()} disabled={sqxBusy} style={{ padding: "3px 6px", background: "var(--surface-3)", border: "1px solid var(--border-strong)", borderRadius: "2px", color: "var(--text-1)", fontSize: "11px", cursor: "pointer" }}>/bind-dataset</button>
              </div>
              {sqxMsg && <div style={{ fontSize: "11px", fontFamily: "monospace", color: "var(--text-2)" }}>{sqxMsg}</div>}

              {/* TABLA 2: Extracciones */}
              <div style={{ overflowX: "auto", border: "1px solid var(--border)", marginTop: "4px" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "var(--surface-2)", color: "var(--text-3)", borderBottom: "1px solid var(--border)" }}>
                      <th style={{ padding: "3px 6px" }}>ID / Nombre</th><th style={{ padding: "3px 6px" }}>Proyecto</th><th style={{ padding: "3px 6px" }}>Databank</th><th style={{ padding: "3px 6px" }}>Hash</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sqxExtractions.length === 0 ? <tr><td colSpan={4} style={{ padding: "6px", textAlign: "center", color: "var(--text-3)" }}>NO DATA en disco</td></tr> : (
                      sqxExtractions.slice(0, 5).map((ext) => (
                        <tr key={ext.strategy_id} style={{ borderBottom: "1px solid var(--border)", fontFamily: "monospace" }}>
                          <td style={{ padding: "3px 6px", color: "var(--text-1)" }}>{ext.name || ext.strategy_id}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-2)" }}>{ext.source_project || "NO DATA"}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-2)" }}>{ext.source_databank || "NO DATA"}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-3)" }}>{ext.strategy_hash ? ext.strategy_hash.slice(0, 10) : "NO DATA"}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* M2: MEJORA */}
          {moduloActivo === "M2" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", background: "var(--surface-1)", border: "1px solid var(--border)", padding: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                <span style={{ fontWeight: 600 }}>M2 — Mejora: Loop Iterativo de Hipótesis</span>
                <span style={{ fontSize: "11px", color: "var(--text-3)" }}>services/improvement/ EN CONSTRUCCIÓN (sellado tras I2)</span>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>Linaje para candidata {seleccion?.c.candidate_id || "sin selección"}:</div>
              {lineageLoading && <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>Consultando linaje...</div>}
              {lineageError && <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>{lineageError} (NO EVIDENCE de ancestros).</div>}

              {/* TABLA 3: Linaje */}
              <div style={{ overflowX: "auto", border: "1px solid var(--border)" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "var(--surface-2)", color: "var(--text-3)", borderBottom: "1px solid var(--border)" }}>
                      <th style={{ padding: "3px 6px" }}>Nodo</th><th style={{ padding: "3px 6px" }}>Generación</th><th style={{ padding: "3px 6px" }}>Padre</th><th style={{ padding: "3px 6px" }}>Mutaciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {!lineageTree || !Array.isArray(lineageTree.nodes) || lineageTree.nodes.length === 0 ? (
                      <tr><td colSpan={4} style={{ padding: "6px", textAlign: "center", color: "var(--text-3)" }}>NO EVIDENCE de mutaciones previas en la base canónica.</td></tr>
                    ) : (
                      lineageTree.nodes.map((n, i) => (
                        <tr key={i} style={{ borderBottom: "1px solid var(--border)", fontFamily: "monospace" }}>
                          <td style={{ padding: "3px 6px", color: "var(--text-1)" }}>{String((n as Record<string, unknown>).strategy_id || i)}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-2)" }}>{String((n as Record<string, unknown>).generation ?? "0")}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-3)" }}>{String((n as Record<string, unknown>).parent_id || "raiz")}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-2)" }}>{JSON.stringify((n as Record<string, unknown>).mutations || {})}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* M3: VALORACIÓN FONDEO */}
          {moduloActivo === "M3" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", background: "var(--surface-1)", border: "1px solid var(--border)", padding: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                <span style={{ fontWeight: 600 }}>M3 — Valoración para Fondeo: Examen contra Prop Firms</span>
                <span style={{ fontSize: "11px", color: "var(--text-3)" }}>Requiere &gt;=1 certificada (hoy: {certificadasCount})</span>
              </div>
              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", fontSize: "11.5px", fontFamily: "monospace", padding: "4px 6px", background: "var(--surface-2)" }}>
                <span>Retorno: <strong>&gt;= 20% mensual</strong></span><span>·</span>
                <span>P(ruina): <strong>&lt;= 20% (6m)</strong></span><span>·</span>
                <span>Examen: <strong>3-8 días</strong></span>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--text-2)" }}>Estado: Sin candidatas que valorar (requiere &gt;=1 certificada; actualmente hay {certificadasCount}).</div>

              {/* TABLA 4: 11 Gates */}
              <div style={{ overflowX: "auto", border: "1px solid var(--border)" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ background: "var(--surface-2)", color: "var(--text-3)", borderBottom: "1px solid var(--border)" }}>
                      <th style={{ padding: "3px 6px" }}>Gate ID</th><th style={{ padding: "3px 6px" }}>Nombre</th><th style={{ padding: "3px 6px" }}>Criterio</th><th style={{ padding: "3px 6px", textAlign: "right" }}>Veredicto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {GATES_LISTA.map((g) => {
                      const veredicto = seleccion ? (isCertified(seleccion.c.status) ? "PASA" : "NO DATA") : "NO DATA";
                      return (
                        <tr key={g.id} style={{ borderBottom: "1px solid var(--border)" }}>
                          <td style={{ padding: "3px 6px", fontFamily: "monospace", color: "var(--text-1)" }}>{g.id}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-2)" }}>{g.n}</td>
                          <td style={{ padding: "3px 6px", color: "var(--text-3)" }}>{g.c}</td>
                          <td style={{ padding: "3px 6px", textAlign: "right", fontFamily: "monospace", color: veredicto === "PASA" ? "var(--profit)" : "var(--text-3)" }}>{veredicto}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div style={{ fontSize: "10.5px", color: "var(--text-3)" }}>Ruta hermana: F05 Envolvente de balas ULTRA — EN CONSTRUCCIÓN (state/PUNTO_GUARDADO_ULTRA.md).</div>
            </div>
          )}

          {/* M4: META */}
          {moduloActivo === "M4" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", background: "var(--surface-1)", border: "1px solid var(--border)", padding: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
                <span style={{ fontWeight: 600 }}>M4 — Metaestrategias: Composición y Reducción de Varianza</span>
                <span style={{ fontSize: "11px", color: "var(--text-3)" }}>Marcador: {certificadasCount} / 2 certificadas necesarias</span>
              </div>
              <div style={{ fontSize: "11.5px", color: "var(--text-2)" }}>Composición: Sin datos de portafolio compuesto (requiere &gt;=2 certificadas).</div>
              <div style={{ fontSize: "10.5px", color: "var(--text-3)" }}>Estado: NO DATA de correlación temporal suficiente. Inactivo hasta disponer de al menos 2 estrategias certificadas.</div>
              <div style={{ fontSize: "10.5px", color: "var(--text-3)" }}>Ruta hermana: F06 Meta-Router ULTRA — EN CONSTRUCCIÓN (state/PUNTO_GUARDADO_ULTRA.md).</div>
            </div>
          )}
        </section>

        {/* 5. PIE DE PÁGINA */}
        <footer style={{ borderTop: "1px solid var(--border)", paddingTop: "8px", fontSize: "11px", color: "var(--text-3)", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "4px" }}>
          <span>ULTRARENTABLE · Página Maestra M1-M4 · REAL-ONLY</span>
          <span>Motor {engineVersion || "NO DATA"} · API {apiConectada ? "OPERATIVA" : "SIN CONEXIÓN"}</span>
        </footer>

      </div>
    </div>
  );
}
