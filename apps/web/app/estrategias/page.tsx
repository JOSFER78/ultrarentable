"use client";

/**
 * apps/web/app/estrategias/page.tsx
 * Página Maestra M1·M2·M3·M4 de Inteligencia Cuantitativa.
 *
 * Cumple estrictamente con:
 * - docs/18_STRATEGIES_PAGE_SPEC.md (identidad, estados, separación de venues/cuentas, NO EVIDENCE)
 * - docs/19_UI_STYLE_SPEC.md (tokens exactos, monocromo, solo verde profit y rojo loss)
 * - orchestration/reviews/diseno_pagina_estrategias_2026-09-01.md
 * - orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md
 *
 * ZERO-MOCKS · REAL-ONLY · SIN DATOS INVENTADOS
 */

import React, { useEffect, useMemo, useState, useCallback } from "react";
import Link from "next/link";
import {
  Search,
  RefreshCw,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Cpu,
  GitBranch,
  Building2,
  Layers,
  ShieldCheck,
  Flame,
  XCircle,
  Database,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
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

function isCertified(status: string): boolean {
  return CERTIFIED_STATUSES.has(status);
}

function isRejected(status: string): boolean {
  return REJECTED_PREFIXES.some((p) => status.startsWith(p));
}

interface FilaCandidato {
  c: CandidatoCanonico;
  a: AuditoriaCandidata;
}

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

const databankName = (d: { name: string } | string): string => (typeof d === "string" ? d : d.name);

export default function PaginaEstrategiasMaestra() {
  // Datos principales
  const [candidatos, setCandidatos] = useState<FilaCandidato[]>([]);
  const [overview, setOverview] = useState<StrategyLabOverview | null>(null);
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdatedUtc, setLastUpdatedUtc] = useState<string | null>(null);

  // Filtros de catálogo
  const [busqueda, setBusqueda] = useState("");
  const [filtroRuta, setFiltroRuta] = useState<string>("ALL");
  const [filtroEstado, setFiltroEstado] = useState<string>("ALL");
  const [filtroTf, setFiltroTf] = useState<string>("ALL");
  const [soloPlausibles, setSoloPlausibles] = useState(false);

  // Ordenación de catálogo
  const [ordenCampo, setOrdenCampo] = useState<string>("gates_passed_count");
  const [ordenAsc, setOrdenAsc] = useState<boolean>(false);

  // Selección activa
  const [seleccion, setSeleccion] = useState<FilaCandidato | null>(null);
  const [copiadoId, setCopiadoId] = useState<string | null>(null);

  // Sección modular activa
  const [moduloActivo, setModuloActivo] = useState<TabModulo>("M1");

  // Estado M1 (SQX)
  const [sqxHealth, setSqxHealth] = useState<"ONLINE" | "OFFLINE" | "NO EVIDENCE" | "CHECKING">("CHECKING");
  const [sqxDetail, setSqxDetail] = useState<string>("");
  const [sqxProject, setSqxProject] = useState("");
  const [sqxDatabanks, setSqxDatabanks] = useState<string[] | null>(null);
  const [sqxDatabank, setSqxDatabank] = useState("");
  const [sqxSource, setSqxSource] = useState<SourceResponse | null>(null);
  const [sqxBinding, setSqxBinding] = useState<BindingResponse | null>(null);
  const [sqxDatasetId, setSqxDatasetId] = useState("");
  const [sqxMsg, setSqxMsg] = useState<string | null>(null);
  const [sqxBusy, setSqxBusy] = useState(false);
  const [sqxExtractions, setSqxExtractions] = useState<StrategyLabRecord[]>([]);

  // Estado M2 (Mejora / Linaje)
  const [lineageTree, setLineageTree] = useState<LineageTreeResponse | null>(null);
  const [lineageLoading, setLineageLoading] = useState(false);
  const [lineageError, setLineageError] = useState<string | null>(null);

  const copiarTexto = useCallback((texto: string, label: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(texto);
      setCopiadoId(label);
      setTimeout(() => setCopiadoId(null), 1800);
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

      const auditadas = candData.map((c) => ({
        c,
        a: auditarCandidata(c as unknown as Record<string, unknown>),
      }));
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
    setSqxDetail("");
    try {
      const r = await getStrategyLabSQXStatus();
      if (r?.status === "ONLINE" || (typeof r?.result === "object" && (r.result as { status?: string })?.status === "ONLINE")) {
        setSqxHealth("ONLINE");
        setSqxDetail(r.source || "SQX MCP Bridge activo");
      } else {
        setSqxHealth("OFFLINE");
        setSqxDetail(r?.error || "SQX MCP Bridge no conectado");
      }
    } catch (e) {
      setSqxHealth("NO EVIDENCE");
      setSqxDetail(e instanceof Error ? e.message : "Endpoint no accesible");
    }
  }, []);

  const cargarDatabanksSqx = useCallback(async () => {
    const p = sqxProject.trim();
    if (!p) {
      setSqxMsg("Indica un proyecto SQX real para listar databanks.");
      return;
    }
    setSqxBusy(true);
    setSqxMsg(null);
    try {
      const r = await api.get<{ databanks: Array<{ name: string } | string> }>(
        `/api/v1/sqx/projects/${encodeURIComponent(p)}/databanks`
      );
      const names = Array.isArray(r?.databanks) ? r.databanks.map(databankName).filter(Boolean) : [];
      setSqxDatabanks(names);
      setSqxDatabank(names[0] ?? "");
      setSqxMsg(names.length ? `Databanks reales encontrados: ${names.join(", ")}` : "Proyecto sin databanks expuestos.");
    } catch (e) {
      setSqxDatabanks([]);
      setSqxDatabank("");
      setSqxMsg(`NO DATA · ${e instanceof Error ? e.message : "motor SQX no responde"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [sqxProject]);

  const extraerDatabankSqx = useCallback(async () => {
    const p = sqxProject.trim();
    const db = sqxDatabank.trim();
    if (!p) {
      setSqxMsg("Indica un proyecto SQX real para extraer.");
      return;
    }
    setSqxBusy(true);
    setSqxMsg(null);
    try {
      const r = await extractStrategyLabProject(p, db || undefined);
      setSqxMsg(
        r?.status === "SUCCESS"
          ? `Extracción real: ${r.found} encontradas (${r.databank}) · ${r.inserted} nuevas · ${r.unchanged} sin cambios · ${r.quarantined} en cuarentena.`
          : `Extracción: ${r?.status ?? "NO DATA"}`
      );
      void refrescarPrincipal();
    } catch (e) {
      setSqxMsg(`NO DATA (extract) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [sqxProject, sqxDatabank, refrescarPrincipal]);

  const obtenerSourceSqx = useCallback(async () => {
    const p = sqxProject.trim();
    const db = sqxDatabank.trim();
    const name = seleccion?.c.name || "";
    if (!p || !name) {
      setSqxMsg("Se requieren proyecto y nombre de estrategia para /source.");
      return;
    }
    setSqxBusy(true);
    setSqxMsg(null);
    try {
      const r = await api.get<SourceResponse>(
        `/api/v2/strategy-lab/source/${encodeURIComponent(p)}/${encodeURIComponent(name)}${
          db ? `?databank=${encodeURIComponent(db)}` : ""
        }`
      );
      setSqxSource(r);
      setSqxMsg(r?.status === "SUCCESS" ? `Source real obtenida · sha256 ${r.source_sha256?.slice(0, 16)}…` : "Source: NO DATA");
    } catch (e) {
      setSqxSource(null);
      setSqxMsg(`NO DATA (source) · ${e instanceof Error ? e.message : "error"}`);
    } finally {
      setSqxBusy(false);
    }
  }, [sqxProject, sqxDatabank, seleccion]);

  const vincularDatasetSqx = useCallback(async () => {
    if (!seleccion?.c.candidate_id) {
      setSqxMsg("Selecciona una estrategia del catálogo.");
      return;
    }
    if (!sqxDatasetId.trim()) {
      setSqxMsg("Indica un dataset_id aprobado.");
      return;
    }
    setSqxBusy(true);
    setSqxMsg(null);
    try {
      const r = await api.post<BindingResponse>(
        `/api/v2/strategy-lab/strategies/${encodeURIComponent(seleccion.c.candidate_id)}/bind-dataset`,
        { dataset_id: sqxDatasetId.trim() }
      );
      setSqxBinding(r);
      setSqxMsg(r?.status === "BOUND" ? `Binding real asociado · dataset ${r.dataset_id}` : "Binding: NO DATA");
    } catch (e) {
      setSqxBinding(null);
      setSqxMsg(`NO DATA (bind-dataset) · ${e instanceof Error ? e.message : "error"}`);
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
      setLineageError(e instanceof Error ? e.message : "No se pudo obtener el árbol de linaje.");
    } finally {
      setLineageLoading(false);
    }
  }, []);

  useEffect(() => {
    void refrescarPrincipal();
    void comprobarSaludSqx();
    getStrategyLabStrategies(10)
      .then((res) => setSqxExtractions(res?.strategies || []))
      .catch(() => setSqxExtractions([]));
  }, [refrescarPrincipal, comprobarSaludSqx]);

  useEffect(() => {
    if (seleccion?.c.candidate_id && moduloActivo === "M2") {
      void consultarLinajeM2(seleccion.c.candidate_id);
    }
  }, [seleccion, moduloActivo, consultarLinajeM2]);

  // Estrategias certificadas de FONDEO
  const certificadasFondeoCount = useMemo(() => {
    return candidatos.filter((f) => isCertified(f.c.status) && f.c.route?.toUpperCase() === "FONDEO").length;
  }, [candidatos]);

  // Lista filtrada y ordenada
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
        if (q) {
          const combo = `${f.c.candidate_id} ${f.c.name} ${f.c.symbol} ${f.c.archetype || ""} ${f.c.route} ${f.c.status}`.toLowerCase();
          if (!combo.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        let valA: number | string | null = null;
        let valB: number | string | null = null;

        if (ordenCampo === "candidate_id") {
          valA = a.c.candidate_id;
          valB = b.c.candidate_id;
        } else if (ordenCampo === "symbol") {
          valA = a.c.symbol;
          valB = b.c.symbol;
        } else if (ordenCampo === "timeframe") {
          valA = a.c.timeframe;
          valB = b.c.timeframe;
        } else if (ordenCampo === "route") {
          valA = a.c.route;
          valB = b.c.route;
        } else if (ordenCampo === "status") {
          valA = a.c.status;
          valB = b.c.status;
        } else if (ordenCampo === "gates_passed_count") {
          valA = a.c.gates_passed_count ?? -1;
          valB = b.c.gates_passed_count ?? -1;
        } else if (ordenCampo === "profit_factor_oos") {
          valA = a.c.profit_factor_oos ?? -1;
          valB = b.c.profit_factor_oos ?? -1;
        } else if (ordenCampo === "trades_oos") {
          valA = a.c.trades_oos ?? -1;
          valB = b.c.trades_oos ?? -1;
        } else if (ordenCampo === "max_dd_oos_pct") {
          valA = a.c.max_dd_oos_pct ?? 9999;
          valB = b.c.max_dd_oos_pct ?? 9999;
        }

        if (valA === null && valB === null) return 0;
        if (valA === null) return ordenAsc ? 1 : -1;
        if (valB === null) return ordenAsc ? -1 : 1;

        if (typeof valA === "number" && typeof valB === "number") {
          return ordenAsc ? valA - valB : valB - valA;
        }
        return ordenAsc
          ? String(valA).localeCompare(String(valB))
          : String(valB).localeCompare(String(valA));
      });
  }, [candidatos, busqueda, filtroRuta, filtroEstado, filtroTf, soloPlausibles, ordenCampo, ordenAsc]);

  const cambiarOrden = (campo: string) => {
    if (ordenCampo === campo) {
      setOrdenAsc(!ordenAsc);
    } else {
      setOrdenCampo(campo);
      setOrdenAsc(false);
    }
  };

  const apiConectada = !error && Boolean(engineVersion);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg)",
        color: "var(--text-1)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
      }}
    >
      {/* 1. CABECERA HONESTA (docs/19 §4 & diseno_pagina_estrategias) */}
      <header
        style={{
          borderBottom: "1px solid var(--border)",
          paddingBottom: "16px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "28px",
                height: "28px",
                borderRadius: "8px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--text-1)",
              }}
            >
              <Database style={{ width: "16px", height: "16px" }} />
            </div>
            <div>
              <h1 style={{ fontSize: "20px", fontWeight: 700, margin: 0, letterSpacing: "-0.02em" }}>
                Estrategias
              </h1>
              <span style={{ fontSize: "12px", color: "var(--text-2)" }}>
                Página Maestra M1·M2·M3·M4 · Catálogo de Inteligencia Cuantitativa
              </span>
            </div>
          </div>

          {/* LÍNEA DE ESTADO HONESTA */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "14px",
              fontSize: "12px",
              fontFamily: "var(--font-mono, monospace)",
              flexWrap: "wrap",
            }}
          >
            {/* Estado API */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 8px",
                borderRadius: "6px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: apiConectada ? "var(--profit)" : "var(--loss)",
                }}
              />
              <span style={{ color: apiConectada ? "var(--text-1)" : "var(--loss)" }}>
                API {apiConectada ? "OPERATIVA" : "SIN CONEXIÓN"}
              </span>
            </div>

            {/* Versión Dinámica de Motor */}
            <div
              style={{
                padding: "4px 8px",
                borderRadius: "6px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                color: engineVersion ? "var(--text-1)" : "var(--text-3)",
              }}
            >
              {engineVersion ? `Motor ${engineVersion}` : "MOTOR: NO DISPONIBLE"}
            </div>

            {/* Contador de Certificadas FONDEO */}
            <div
              style={{
                padding: "4px 8px",
                borderRadius: "6px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                color: "var(--text-2)",
              }}
            >
              Certificadas FONDEO: <strong style={{ color: "var(--text-1)" }}>{certificadasFondeoCount}</strong>
            </div>

            {/* Botón de Actualizar */}
            <button
              onClick={() => void refrescarPrincipal()}
              disabled={loading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "5px 10px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                color: "var(--text-1)",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              <RefreshCw
                style={{
                  width: "13px",
                  height: "13px",
                  animation: loading ? "spin 1s linear infinite" : "none",
                }}
              />
              <span>Actualizar</span>
            </button>
          </div>
        </div>

        {lastUpdatedUtc && (
          <div style={{ fontSize: "11px", color: "var(--text-3)", fontFamily: "var(--font-mono, monospace)" }}>
            Última campaña / actualización: {lastUpdatedUtc} · Fuente: <code>/api/v1/candidates</code>
          </div>
        )}
      </header>

      {/* ERROR DE API (FAIL-CLOSED) */}
      {error && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "8px",
            background: "var(--loss-dim)",
            border: "1px solid var(--loss)",
            color: "var(--text-1)",
            fontSize: "13px",
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
          }}
        >
          <XCircle style={{ width: "18px", height: "18px", color: "var(--loss)", flexShrink: 0, marginTop: "2px" }} />
          <div>
            <div style={{ fontWeight: 600, color: "var(--loss)" }}>Error de conexión con la API</div>
            <div style={{ marginTop: "2px", color: "var(--text-2)", fontFamily: "var(--font-mono, monospace)", fontSize: "12px" }}>
              {error}
            </div>
            <div style={{ marginTop: "4px", fontSize: "11px", color: "var(--text-3)" }}>
              Principio Zero-Mocks: sin fallbacks sintéticos ni datos en caché no verificados.
            </div>
          </div>
        </div>
      )}

      {/* 2. EMBUDO DE ESTADOS (SPEC 18 HECHO BARRA) */}
      <section
        style={{
          background: "var(--surface-1)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          padding: "14px 18px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)", fontWeight: 600, letterSpacing: "0.5px" }}>
          Embudo de Validación
        </div>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            flexWrap: "wrap",
            fontFamily: "var(--font-mono, monospace)",
            fontSize: "12px",
          }}
        >
          {/* EXTRACTED */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--text-2)" }}>EXTRACTED</span>
            <span style={{ fontWeight: 700, color: "var(--text-1)" }}>
              {overview?.pipeline?.extracted !== undefined ? overview.pipeline.extracted : "NO EVIDENCE"}
            </span>
          </div>

          <span style={{ color: "var(--text-3)" }}>→</span>

          {/* STRUCTURALLY_VERIFIED */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--text-2)" }}>STRUCTURALLY_VERIFIED</span>
            <span style={{ fontWeight: 700, color: "var(--text-1)" }}>
              {overview?.pipeline?.structurally_verified !== undefined
                ? overview.pipeline.structurally_verified
                : "NO EVIDENCE"}
            </span>
          </div>

          <span style={{ color: "var(--text-3)" }}>→</span>

          {/* BACKTEST_VERIFIED */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--text-2)" }}>BACKTEST_VERIFIED</span>
            <span style={{ fontWeight: 700, color: "var(--text-1)" }}>
              {overview?.pipeline?.backtest_verified !== undefined
                ? overview.pipeline.backtest_verified
                : "NO EVIDENCE"}
            </span>
          </div>

          <span style={{ color: "var(--text-3)" }}>→</span>

          {/* CERTIFIED_CURRENT */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: "var(--text-2)" }}>CERTIFIED_CURRENT</span>
            <span
              style={{
                fontWeight: 700,
                color:
                  overview?.pipeline?.certified_current && overview.pipeline.certified_current > 0
                    ? "var(--profit)"
                    : "var(--text-3)",
              }}
            >
              {overview?.pipeline?.certified_current !== undefined ? overview.pipeline.certified_current : 0}
            </span>
          </div>
        </div>
      </section>

      {/* 3. CATÁLOGO PRINCIPAL (TABLA CANÓNICA) */}
      <section style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {/* FILTROS Y BÚSQUEDA */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          {/* Búsqueda libre */}
          <div
            style={{
              position: "relative",
              flex: "1 1 240px",
              minWidth: "220px",
            }}
          >
            <Search
              style={{
                position: "absolute",
                left: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                width: "14px",
                height: "14px",
                color: "var(--text-3)",
              }}
            />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar por ID, nombre, símbolo, arquetipo…"
              style={{
                width: "100%",
                padding: "7px 10px 7px 32px",
                fontSize: "12.5px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-1)",
              }}
            />
          </div>

          {/* Selectores Nativos */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <select
              value={filtroRuta}
              onChange={(e) => setFiltroRuta(e.target.value)}
              style={{
                padding: "6px 10px",
                fontSize: "12px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-1)",
              }}
            >
              <option value="ALL">Todas las rutas</option>
              <option value="FONDEO">Ruta FONDEO</option>
              <option value="ULTRA">Ruta ULTRA (En construcción)</option>
            </select>

            <select
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
              style={{
                padding: "6px 10px",
                fontSize: "12px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-1)",
              }}
            >
              <option value="ALL">Todos los estados</option>
              <option value="CERTIFIED">Solo Certificadas</option>
              <option value="REJECTED">Rechazadas / Falladas</option>
              <option value="LEGACY">Invalidadas (Legacy)</option>
              <option value="OTHER">Otras (En evaluación)</option>
            </select>

            <select
              value={filtroTf}
              onChange={(e) => setFiltroTf(e.target.value)}
              style={{
                padding: "6px 10px",
                fontSize: "12px",
                background: "var(--surface-1)",
                border: "1px solid var(--border)",
                borderRadius: "6px",
                color: "var(--text-1)",
              }}
            >
              <option value="ALL">Todos los TF</option>
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="4h">4h</option>
            </select>

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontSize: "12px",
                color: "var(--text-2)",
                cursor: "pointer",
                userSelect: "none",
                marginLeft: "4px",
              }}
            >
              <input
                type="checkbox"
                checked={soloPlausibles}
                onChange={(e) => setSoloPlausibles(e.target.checked)}
              />
              <span>Solo plausibles</span>
            </label>

            <span style={{ fontSize: "12px", color: "var(--text-3)", marginLeft: "6px" }}>
              {candidatasVisibles.length} / {candidatos.length}
            </span>
          </div>
        </div>

        {/* TABLA DE ESTRATEGIAS */}
        <div
          style={{
            overflowX: "auto",
            borderRadius: "8px",
            border: "1px solid var(--border)",
            background: "var(--surface-1)",
          }}
        >
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--border)",
                  background: "var(--surface-2)",
                  color: "var(--text-2)",
                  fontSize: "11px",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                }}
              >
                <th
                  onClick={() => cambiarOrden("candidate_id")}
                  style={{ padding: "10px 12px", textAlign: "left", cursor: "pointer" }}
                >
                  Identificador {ordenCampo === "candidate_id" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th
                  onClick={() => cambiarOrden("symbol")}
                  style={{ padding: "10px 12px", textAlign: "left", cursor: "pointer" }}
                >
                  Símbolo · TF {ordenCampo === "symbol" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th style={{ padding: "10px 12px", textAlign: "left" }}>Arquetipo</th>
                <th
                  onClick={() => cambiarOrden("route")}
                  style={{ padding: "10px 12px", textAlign: "left", cursor: "pointer" }}
                >
                  Ruta {ordenCampo === "route" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th
                  onClick={() => cambiarOrden("status")}
                  style={{ padding: "10px 12px", textAlign: "left", cursor: "pointer" }}
                >
                  Estado {ordenCampo === "status" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th
                  onClick={() => cambiarOrden("gates_passed_count")}
                  style={{ padding: "10px 12px", textAlign: "right", cursor: "pointer" }}
                >
                  Gates {ordenCampo === "gates_passed_count" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th
                  onClick={() => cambiarOrden("profit_factor_oos")}
                  style={{ padding: "10px 12px", textAlign: "right", cursor: "pointer" }}
                >
                  PF OOS {ordenCampo === "profit_factor_oos" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th
                  onClick={() => cambiarOrden("trades_oos")}
                  style={{ padding: "10px 12px", textAlign: "right", cursor: "pointer" }}
                >
                  Ops OOS {ordenCampo === "trades_oos" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th
                  onClick={() => cambiarOrden("max_dd_oos_pct")}
                  style={{ padding: "10px 12px", textAlign: "right", cursor: "pointer" }}
                >
                  DD OOS {ordenCampo === "max_dd_oos_pct" ? (ordenAsc ? "↑" : "↓") : ""}
                </th>
                <th style={{ padding: "10px 12px", textAlign: "left" }}>Hash</th>
                <th style={{ padding: "10px 12px", textAlign: "left" }}>Dataset</th>
              </tr>
            </thead>
            <tbody>
              {loading && candidatos.length === 0 && (
                <tr>
                  <td colSpan={11} style={{ padding: "28px", textAlign: "center", color: "var(--text-3)" }}>
                    Cargando catálogo canónico de estrategias…
                  </td>
                </tr>
              )}

              {!loading && candidatasVisibles.length === 0 && (
                <tr>
                  <td colSpan={11} style={{ padding: "28px", textAlign: "center", color: "var(--text-3)" }}>
                    NO EVIDENCE con los filtros actuales.
                  </td>
                </tr>
              )}

              {candidatasVisibles.map((fila) => {
                const c = fila.c;
                const a = fila.a;
                const esCert = isCertified(c.status);
                const esRech = isRejected(c.status);
                const esUltra = c.route?.toUpperCase() === "ULTRA";
                const isSelected = seleccion?.c.candidate_id === c.candidate_id;

                // Color de Estado según spec 19 §3
                const colorEstado = esCert ? "var(--profit)" : esRech ? "var(--loss)" : "var(--text-2)";

                // Formato PF OOS
                const pfVal = c.profit_factor_oos;
                const colorPf =
                  pfVal === null || pfVal === undefined
                    ? "var(--text-3)"
                    : pfVal >= 1.0
                    ? "var(--profit)"
                    : "var(--loss)";

                // Formato Gates: null != 0
                const gatesDisplay =
                  c.gates_passed_count !== null && c.gates_passed_count !== undefined
                    ? `${c.gates_passed_count}/11`
                    : "NO EVIDENCE";
                const colorGates =
                  c.gates_passed_count === null || c.gates_passed_count === undefined
                    ? "var(--text-3)"
                    : "var(--text-2)";

                return (
                  <tr
                    key={c.candidate_id}
                    onClick={() => setSeleccion(fila)}
                    style={{
                      borderBottom: "1px solid var(--border)",
                      cursor: "pointer",
                      background: isSelected ? "var(--surface-3)" : esUltra ? "var(--surface-1)" : "transparent",
                      opacity: esUltra ? 0.75 : 1,
                      transition: "background 0.1s ease",
                    }}
                  >
                    {/* 1. Identificador */}
                    <td
                      style={{
                        padding: "8px 12px",
                        fontFamily: "var(--font-mono, monospace)",
                        fontSize: "12px",
                        color: "var(--text-1)",
                      }}
                      title={c.candidate_id}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span>
                          {c.candidate_id.length > 18
                            ? `${c.candidate_id.slice(0, 14)}…`
                            : c.candidate_id}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copiarTexto(c.candidate_id, c.candidate_id);
                          }}
                          title="Copiar ID completo"
                          style={{
                            padding: "2px",
                            color: copiadoId === c.candidate_id ? "var(--profit)" : "var(--text-3)",
                            cursor: "pointer",
                          }}
                        >
                          {copiadoId === c.candidate_id ? (
                            <Check style={{ width: "11px", height: "11px" }} />
                          ) : (
                            <Copy style={{ width: "11px", height: "11px" }} />
                          )}
                        </button>
                      </div>
                    </td>

                    {/* 2. Símbolo · TF */}
                    <td style={{ padding: "8px 12px", color: "var(--text-2)" }}>
                      <span style={{ fontWeight: 600, color: "var(--text-1)" }}>{c.symbol}</span>
                      <span style={{ color: "var(--text-3)", marginLeft: "4px" }}>· {c.timeframe}</span>
                    </td>

                    {/* 3. Arquetipo */}
                    <td
                      style={{
                        padding: "8px 12px",
                        color: c.archetype ? "var(--text-2)" : "var(--text-3)",
                      }}
                    >
                      {c.archetype || "NO EVIDENCE"}
                    </td>

                    {/* 4. Ruta */}
                    <td style={{ padding: "8px 12px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span style={{ color: "var(--text-2)" }}>{c.route}</span>
                        {esUltra && (
                          <span
                            style={{
                              fontSize: "9.5px",
                              fontFamily: "var(--font-mono, monospace)",
                              padding: "1px 5px",
                              borderRadius: "4px",
                              background: "var(--surface-2)",
                              border: "1px solid var(--border)",
                              color: "var(--text-3)",
                            }}
                          >
                            EN CONSTRUCCIÓN
                          </span>
                        )}
                      </div>
                    </td>

                    {/* 5. Estado */}
                    <td
                      style={{
                        padding: "8px 12px",
                        color: colorEstado,
                        fontWeight: esCert ? 600 : 400,
                      }}
                    >
                      {c.status}
                    </td>

                    {/* 6. Gates */}
                    <td
                      style={{
                        padding: "8px 12px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono, monospace)",
                        fontVariantNumeric: "tabular-nums",
                        color: colorGates,
                      }}
                    >
                      {gatesDisplay}
                    </td>

                    {/* 7. PF OOS */}
                    <td
                      style={{
                        padding: "8px 12px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono, monospace)",
                        fontVariantNumeric: "tabular-nums",
                        color: colorPf,
                        fontWeight: pfVal !== null && pfVal !== undefined ? 600 : 400,
                      }}
                    >
                      {pfVal !== null && pfVal !== undefined ? pfVal.toFixed(2) : "NO EVIDENCE"}
                    </td>

                    {/* 8. Ops OOS */}
                    <td
                      style={{
                        padding: "8px 12px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono, monospace)",
                        fontVariantNumeric: "tabular-nums",
                        color: c.trades_oos !== null && c.trades_oos !== undefined ? "var(--text-2)" : "var(--text-3)",
                      }}
                    >
                      {c.trades_oos !== null && c.trades_oos !== undefined ? c.trades_oos : "NO EVIDENCE"}
                    </td>

                    {/* 9. DD OOS */}
                    <td
                      style={{
                        padding: "8px 12px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono, monospace)",
                        fontVariantNumeric: "tabular-nums",
                        color: c.max_dd_oos_pct !== null && c.max_dd_oos_pct !== undefined ? "var(--loss)" : "var(--text-3)",
                      }}
                    >
                      {c.max_dd_oos_pct !== null && c.max_dd_oos_pct !== undefined
                        ? `${c.max_dd_oos_pct.toFixed(2)} %`
                        : "NO EVIDENCE"}
                    </td>

                    {/* 10. Hash */}
                    <td
                      style={{
                        padding: "8px 12px",
                        fontFamily: "var(--font-mono, monospace)",
                        fontSize: "11.5px",
                        color: c.strategy_sha256 ? "var(--text-2)" : "var(--text-3)",
                      }}
                    >
                      {c.strategy_sha256 ? (
                        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                          <span>{c.strategy_sha256.slice(0, 8)}</span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (c.strategy_sha256) copiarTexto(c.strategy_sha256, c.strategy_sha256);
                            }}
                            title="Copiar Hash SHA-256"
                            style={{
                              padding: "2px",
                              color: copiadoId === c.strategy_sha256 ? "var(--profit)" : "var(--text-3)",
                              cursor: "pointer",
                            }}
                          >
                            {copiadoId === c.strategy_sha256 ? (
                              <Check style={{ width: "11px", height: "11px" }} />
                            ) : (
                              <Copy style={{ width: "11px", height: "11px" }} />
                            )}
                          </button>
                        </div>
                      ) : (
                        "NO EVIDENCE"
                      )}
                    </td>

                    {/* 11. Dataset */}
                    <td
                      style={{
                        padding: "8px 12px",
                        fontFamily: "var(--font-mono, monospace)",
                        fontSize: "11.5px",
                        color: c.dataset_id ? "var(--text-2)" : "var(--text-3)",
                      }}
                      title={c.dataset_id || undefined}
                    >
                      {c.dataset_id ? (
                        c.dataset_id.length > 14 ? `${c.dataset_id.slice(0, 12)}…` : c.dataset_id
                      ) : (
                        "NO EVIDENCE"
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* DETALLE / AUDITORÍA DE LA CANDIDATA SELECCIONADA */}
        {seleccion && (
          <div
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "16px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "8px",
                borderBottom: "1px solid var(--border)",
                paddingBottom: "10px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <ShieldCheck style={{ width: "16px", height: "16px", color: "var(--text-2)" }} />
                <span style={{ fontWeight: 600, color: "var(--text-1)" }}>{seleccion.c.name}</span>
                <span style={{ fontSize: "12px", color: "var(--text-3)" }}>
                  ({seleccion.c.candidate_id}) · {seleccion.c.symbol} · {seleccion.c.timeframe} · {seleccion.c.route}
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <button
                  onClick={() => {
                    setModuloActivo("M2");
                    void consultarLinajeM2(seleccion.c.candidate_id);
                  }}
                  style={{
                    padding: "4px 8px",
                    borderRadius: "6px",
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    color: "var(--text-1)",
                    fontSize: "11px",
                    cursor: "pointer",
                  }}
                >
                  Inspeccionar Linaje (M2) →
                </button>
              </div>
            </div>

            {/* MÉTRICAS DE LA CANDIDATA */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "12px",
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)" }}>
                  Profit Factor OOS
                </span>
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color:
                      seleccion.a.profitFactor.veredicto === "NO_PLAUSIBLE"
                        ? "var(--loss)"
                        : "var(--text-1)",
                  }}
                >
                  {mostrar(seleccion.a.profitFactor)}
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)" }}>
                  Drawdown OOS
                </span>
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color:
                      seleccion.a.drawdown.veredicto === "NO_PLAUSIBLE"
                        ? "var(--loss)"
                        : "var(--loss)",
                  }}
                >
                  {mostrar(seleccion.a.drawdown, " %")}
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)" }}>
                  Beneficio Neto OOS
                </span>
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color:
                      seleccion.a.beneficio.veredicto === "NO_PLAUSIBLE"
                        ? "var(--loss)"
                        : "var(--text-1)",
                  }}
                >
                  {mostrar(seleccion.a.beneficio, " USD")}
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span style={{ fontSize: "11px", textTransform: "uppercase", color: "var(--text-3)" }}>
                  Operaciones OOS
                </span>
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color:
                      seleccion.a.muestra.veredicto === "NO_PLAUSIBLE"
                        ? "var(--text-3)"
                        : "var(--text-1)",
                  }}
                >
                  {mostrar(seleccion.a.muestra, "", 0)}
                </span>
              </div>
            </div>

            {/* PROBLEMAS DE AUDITORÍA (SI LOS HAY) */}
            {seleccion.a.problemas.length > 0 && (
              <div
                style={{
                  padding: "10px 14px",
                  borderRadius: "6px",
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  fontSize: "12px",
                }}
              >
                <div style={{ fontWeight: 600, color: "var(--text-2)" }}>
                  Auditoría de Plausibilidad (Cifras no consolidadas como hechos válidos):
                </div>
                <ul style={{ marginTop: "6px", paddingLeft: "16px", color: "var(--text-3)", margin: "6px 0 0" }}>
                  {seleccion.a.problemas.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* IDENTIDAD Y PROVENANCE */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: "8px",
                fontSize: "12px",
              }}
            >
              <div>
                <span style={{ color: "var(--text-3)" }}>Motivo de estado: </span>
                <span style={{ color: "var(--text-2)" }}>{seleccion.c.status_reason || "NO EVIDENCE"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-3)" }}>Arquetipo: </span>
                <span style={{ color: "var(--text-2)" }}>{seleccion.c.archetype || "NO EVIDENCE"}</span>
              </div>
              <div>
                <span style={{ color: "var(--text-3)" }}>Dataset ID: </span>
                <span style={{ color: "var(--text-2)", fontFamily: "var(--font-mono, monospace)" }}>
                  {seleccion.c.dataset_id || "NO EVIDENCE"}
                </span>
              </div>
              <div>
                <span style={{ color: "var(--text-3)" }}>SHA-256: </span>
                <span style={{ color: "var(--text-2)", fontFamily: "var(--font-mono, monospace)" }}>
                  {seleccion.c.strategy_sha256 || "NO EVIDENCE"}
                </span>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* 4. LAS CUATRO SECCIONES MODULARES (M1 · M2 · M3 · M4) */}
      <section
        style={{
          borderTop: "1px solid var(--border)",
          paddingTop: "20px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        {/* SELECTOR DE PESTAÑAS MODULARES */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            borderBottom: "1px solid var(--border)",
            paddingBottom: "8px",
            flexWrap: "wrap",
          }}
        >
          {[
            { id: "M1", label: "M1 Generación (Strategy One / SQX)", icon: Cpu },
            { id: "M2", label: "M2 Mejora (Loop Iterativo)", icon: GitBranch },
            { id: "M3", label: "M3 Valoración Fondeo (Examen Prop Firm)", icon: Building2 },
            { id: "M4", label: "M4 Meta (Composición Multiactivo)", icon: Layers },
          ].map((tab) => {
            const Icon = tab.icon;
            const activo = moduloActivo === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setModuloActivo(tab.id as TabModulo)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  background: activo ? "var(--surface-3)" : "transparent",
                  border: activo ? "1px solid var(--border-strong)" : "1px solid transparent",
                  color: activo ? "var(--text-1)" : "var(--text-2)",
                  fontSize: "12px",
                  fontWeight: activo ? 600 : 500,
                  cursor: "pointer",
                }}
              >
                <Icon style={{ width: "14px", height: "14px", color: activo ? "var(--text-1)" : "var(--text-3)" }} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* CONTENIDO M1: GENERACIÓN (SQX) */}
        {moduloActivo === "M1" && (
          <div
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "10px" }}>
              <div>
                <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--text-1)" }}>
                  M1 — Generación: StrategyQuant X Bridge
                </h3>
                <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--text-2)" }}>
                  Extracción de hipótesis, inspección de código fuente y enlace determinista de datasets.
                </p>
              </div>

              {/* Salud SQX */}
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "4px 8px",
                    borderRadius: "6px",
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    fontSize: "11.5px",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  <span
                    style={{
                      width: "6px",
                      height: "6px",
                      borderRadius: "50%",
                      background:
                        sqxHealth === "ONLINE"
                          ? "var(--profit)"
                          : sqxHealth === "OFFLINE"
                          ? "var(--loss)"
                          : "var(--text-3)",
                    }}
                  />
                  <span
                    style={{
                      color:
                        sqxHealth === "ONLINE"
                          ? "var(--text-1)"
                          : sqxHealth === "OFFLINE"
                          ? "var(--loss)"
                          : "var(--text-3)",
                    }}
                  >
                    SQX {sqxHealth}
                  </span>
                </div>

                <button
                  onClick={() => void comprobarSaludSqx()}
                  disabled={sqxBusy}
                  style={{
                    padding: "4px 8px",
                    borderRadius: "6px",
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    color: "var(--text-1)",
                    fontSize: "11.5px",
                    cursor: "pointer",
                  }}
                >
                  Revisar
                </button>
              </div>
            </div>

            {/* Aviso Deuda M1 */}
            <div
              style={{
                padding: "8px 12px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                fontSize: "11.5px",
                color: "var(--text-3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "6px",
              }}
            >
              <span>Métrica de caudal por hora de CPU: <strong>NO DISPONIBLE</strong> (pendiente de endpoint en backend).</span>
              <span>{sqxDetail}</span>
            </div>

            {sqxMsg && (
              <div
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono, monospace)",
                  color: "var(--text-1)",
                }}
              >
                {sqxMsg}
              </div>
            )}

            {/* Controles de Proyecto y Databank */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "10px",
              }}
            >
              <input
                type="text"
                value={sqxProject}
                onChange={(e) => setSqxProject(e.target.value)}
                placeholder="Proyecto SQX real (ej. Futures_Portfolio)"
                style={{
                  padding: "7px 10px",
                  fontSize: "12px",
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--text-1)",
                }}
              />

              <select
                value={sqxDatabank}
                onChange={(e) => setSqxDatabank(e.target.value)}
                style={{
                  padding: "7px 10px",
                  fontSize: "12px",
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--text-1)",
                }}
              >
                {sqxDatabanks === null ? (
                  <option value="">Databank…</option>
                ) : sqxDatabanks.length === 0 ? (
                  <option value="">NO EVIDENCE</option>
                ) : (
                  sqxDatabanks.map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))
                )}
              </select>

              <div style={{ display: "flex", gap: "6px" }}>
                <button
                  onClick={() => void cargarDatabanksSqx()}
                  disabled={sqxBusy}
                  style={{
                    flex: 1,
                    padding: "7px 10px",
                    borderRadius: "6px",
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    color: "var(--text-1)",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  Listar Bancos
                </button>
                <button
                  onClick={() => void extraerDatabankSqx()}
                  disabled={sqxBusy}
                  style={{
                    flex: 1,
                    padding: "7px 10px",
                    borderRadius: "6px",
                    background: "var(--surface-3)",
                    border: "1px solid var(--border-strong)",
                    color: "var(--text-1)",
                    fontSize: "12px",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Extraer
                </button>
                <button
                  onClick={() => void obtenerSourceSqx()}
                  disabled={sqxBusy}
                  style={{
                    padding: "7px 10px",
                    borderRadius: "6px",
                    background: "var(--surface-2)",
                    border: "1px solid var(--border)",
                    color: "var(--text-2)",
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  /source
                </button>
              </div>
            </div>

            {/* Controles de Binding */}
            <div
              style={{
                display: "flex",
                gap: "10px",
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <input
                type="text"
                value={sqxDatasetId}
                onChange={(e) => setSqxDatasetId(e.target.value)}
                placeholder="dataset_id aprobado (ej. NQ_1M_CANONICAL)"
                style={{
                  flex: "1 1 240px",
                  padding: "7px 10px",
                  fontSize: "12px",
                  background: "var(--surface-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  color: "var(--text-1)",
                }}
              />
              <button
                onClick={() => void vincularDatasetSqx()}
                disabled={sqxBusy}
                style={{
                  padding: "7px 14px",
                  borderRadius: "6px",
                  background: "var(--surface-3)",
                  border: "1px solid var(--border-strong)",
                  color: "var(--text-1)",
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                /bind-dataset
              </button>
            </div>

            {/* Payload Source inspeccionado */}
            {sqxSource && (
              <div style={{ marginTop: "6px" }}>
                <div style={{ fontSize: "11px", color: "var(--text-3)", marginBottom: "4px" }}>
                  Payload de /source:
                </div>
                <pre
                  style={{
                    maxHeight: "140px",
                    overflow: "auto",
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    padding: "10px",
                    fontSize: "11px",
                    fontFamily: "var(--font-mono, monospace)",
                    color: "var(--text-2)",
                  }}
                >
                  {JSON.stringify(sqxSource, null, 2)}
                </pre>
              </div>
            )}

            {/* Extracciones crudas recientes */}
            {sqxExtractions.length > 0 && (
              <div style={{ marginTop: "6px" }}>
                <div style={{ fontSize: "11.5px", color: "var(--text-2)", fontWeight: 600, marginBottom: "6px" }}>
                  Extracciones recientes en disco ({sqxExtractions.length} registros):
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                  {sqxExtractions.slice(0, 5).map((ext) => (
                    <div
                      key={ext.strategy_id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "6px 10px",
                        borderRadius: "6px",
                        background: "var(--surface-2)",
                        fontSize: "11.5px",
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      <span style={{ color: "var(--text-1)" }}>{ext.name || ext.strategy_id}</span>
                      <span style={{ color: "var(--text-3)" }}>
                        {ext.source_project || "NO DATA"} · {ext.source_databank || "NO DATA"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* CONTENIDO M2: MEJORA */}
        {moduloActivo === "M2" && (
          <div
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--text-1)" }}>
                M2 — Mejora: Loop Iterativo de Hipótesis
              </h3>
              <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--text-2)" }}>
                Máquina de estados: CRUDA → EVALUADA (gates) → EN_MEJORA(iter n) → RE-EVALUADA → CERTIFICADA | AGOTADA.
              </p>
            </div>

            {/* Aviso Deuda M2 */}
            <div
              style={{
                padding: "10px 14px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                fontSize: "12px",
                color: "var(--text-2)",
              }}
            >
              <strong>Estado del servicio:</strong> <code>services/improvement/</code> EN CONSTRUCCIÓN (se sella tras el benchmark I2).
              Cero simulaciones: no se falsea la ejecución de un loop en tiempo real.
            </div>

            {/* Árbol de Linaje */}
            <div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "8px" }}>
                <span style={{ fontSize: "12px", fontWeight: 600, color: "var(--text-1)" }}>
                  Árbol de Linaje para {seleccion?.c.name || "Estrategia seleccionada"}:
                </span>
                {seleccion?.c.candidate_id && (
                  <button
                    onClick={() => void consultarLinajeM2(seleccion.c.candidate_id)}
                    disabled={lineageLoading}
                    style={{
                      padding: "4px 8px",
                      borderRadius: "6px",
                      background: "var(--surface-2)",
                      border: "1px solid var(--border)",
                      color: "var(--text-1)",
                      fontSize: "11px",
                      cursor: "pointer",
                    }}
                  >
                    {lineageLoading ? "Consultando…" : "Actualizar Linaje"}
                  </button>
                )}
              </div>

              {lineageError && (
                <div style={{ fontSize: "12px", color: "var(--text-3)", padding: "8px 0" }}>
                  Linaje: {lineageError} (No hay registro de mutaciones previas en la base canónica).
                </div>
              )}

              {lineageTree ? (
                <div
                  style={{
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    padding: "12px",
                    fontSize: "12px",
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  <div style={{ color: "var(--text-2)", marginBottom: "6px" }}>
                    Nodos en el árbol: {lineageTree.total_nodes} · Generación máxima: {lineageTree.max_generation}
                  </div>
                  <pre style={{ margin: 0, color: "var(--text-1)", maxHeight: "160px", overflow: "auto" }}>
                    {JSON.stringify(lineageTree.nodes, null, 2)}
                  </pre>
                </div>
              ) : (
                !lineageLoading && (
                  <div style={{ fontSize: "12px", color: "var(--text-3)", padding: "12px", background: "var(--bg)", borderRadius: "6px" }}>
                    NO EVIDENCE de linaje registrado para este candidato. Selecciona otra estrategia o ejecuta una mutación certificada.
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* CONTENIDO M3: VALORACIÓN FONDEO */}
        {moduloActivo === "M3" && (
          <div
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--text-1)" }}>
                M3 — Valoración para Fondeo: Examen contra Prop Firms Reales
              </h3>
              <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--text-2)" }}>
                Puntaje determinista de estrategias certificadas contra reglas exactas (Apex, Topstep, MFFU, TradeDay).
              </p>
            </div>

            {/* Objetivo sellado */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "10px",
                fontFamily: "var(--font-mono, monospace)",
                fontSize: "12px",
              }}
            >
              <div style={{ padding: "10px", background: "var(--surface-2)", borderRadius: "6px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--text-3)" }}>Retorno Objetivo</div>
                <div style={{ fontWeight: 700, color: "var(--text-1)", marginTop: "2px" }}>≥ 20% mensual (mediana)</div>
              </div>
              <div style={{ padding: "10px", background: "var(--surface-2)", borderRadius: "6px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--text-3)" }}>P(Ruina) Máxima</div>
                <div style={{ fontWeight: 700, color: "var(--text-1)", marginTop: "2px" }}>≤ 20% en 6 meses</div>
              </div>
              <div style={{ padding: "10px", background: "var(--surface-2)", borderRadius: "6px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "10px", textTransform: "uppercase", color: "var(--text-3)" }}>Horizonte Examen</div>
                <div style={{ fontWeight: 700, color: "var(--text-1)", marginTop: "2px" }}>3 a 8 días de trading</div>
              </div>
            </div>

            {/* Estado Real M3 */}
            <div
              style={{
                padding: "14px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                fontSize: "12.5px",
                color: "var(--text-2)",
              }}
            >
              <div style={{ fontWeight: 600, color: "var(--text-1)" }}>
                Estado de la valoración: Sin candidatas que valorar (requiere ≥1 estrategia certificada; actualmente hay 0).
              </div>
              <p style={{ margin: "6px 0 0", color: "var(--text-3)", fontSize: "12px" }}>
                El módulo de valoración se activa automáticamente en cuanto el catálogo registre la primera estrategia con 11/11 Evidence Gates y validación OOS aprobada.
              </p>
            </div>

            {/* Nota de Deuda y Gemelo ULTRA */}
            <div style={{ fontSize: "11.5px", color: "var(--text-3)", display: "flex", flexDirection: "column", gap: "4px" }}>
              <div>⚠ Catálogo de firmas: datos 08-2026 sin re-verificar (se servirá por API desde I4).</div>
              <div>
                Ruta hermana: F05 Envolvente de balas ULTRA (piramidación y margen aislado) — <strong>EN CONSTRUCCIÓN</strong> (ver <code>state/PUNTO_GUARDADO_ULTRA.md</code>).
              </div>
            </div>
          </div>
        )}

        {/* CONTENIDO M4: METAESTRATEGIAS */}
        {moduloActivo === "M4" && (
          <div
            style={{
              background: "var(--surface-1)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "16px",
            }}
          >
            <div>
              <h3 style={{ margin: 0, fontSize: "14px", fontWeight: 700, color: "var(--text-1)" }}>
                M4 — Metaestrategias: Composición y Reducción de Varianza
              </h3>
              <p style={{ margin: "2px 0 0", fontSize: "12px", color: "var(--text-2)" }}>
                Ensamblado multiactivo con correlación temporal verificada y examen conjunto de la meta.
              </p>
            </div>

            {/* Marcador Real */}
            <div
              style={{
                padding: "14px",
                borderRadius: "6px",
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                fontSize: "12.5px",
                color: "var(--text-2)",
              }}
            >
              <div style={{ fontWeight: 600, color: "var(--text-1)" }}>
                Marcador de composición: 0 / 2 certificadas necesarias
              </div>
              <p style={{ margin: "6px 0 0", color: "var(--text-3)", fontSize: "12px" }}>
                La construcción de meta-estrategias requiere al menos 2 estrategias certificadas independientes con ledgers reales y solape temporal suficiente.
              </p>
            </div>

            {/* Gemelo ULTRA */}
            <div style={{ fontSize: "11.5px", color: "var(--text-3)" }}>
              Ruta hermana: F06 Meta-Router ULTRA — <strong>EN CONSTRUCCIÓN</strong> (ver <code>state/PUNTO_GUARDADO_ULTRA.md</code>).
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
