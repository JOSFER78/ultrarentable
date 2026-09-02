"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Building2,
  ExternalLink,
  Shield,
  Search,
  RefreshCw,
  AlertTriangle,
  FileText,
  CheckCircle2,
  Info,
} from "lucide-react";
import {
  getPropFirmsV2,
  FirmaV2,
  CampoConFuente,
  Confidence,
} from "@/lib/propFirmsV2";

interface FieldMetric {
  key: keyof Omit<FirmaV2, "id" | "nombre">;
  label: string;
  category: "riesgo" | "economia" | "ejecucion";
}

const METRICAS: FieldMetric[] = [
  { key: "trailing_dd_tipo", label: "Tipo Drawdown", category: "riesgo" },
  { key: "trailing_dd_valor_50k", label: "Drawdown 50K", category: "riesgo" },
  { key: "perdida_diaria_limite_50k", label: "Límite Pérdida Diaria 50K", category: "riesgo" },
  { key: "consistencia_pct", label: "Consistencia", category: "riesgo" },
  { key: "min_dias_trading", label: "Mín. Días Trading", category: "riesgo" },
  { key: "max_micros_50k", label: "Máx. Micros 50K", category: "riesgo" },
  { key: "hora_cierre_obligatoria", label: "Cierre Obligatorio (Flat)", category: "riesgo" },
  { key: "precio_examen_50k", label: "Precio Examen 50K", category: "economia" },
  { key: "coste_activacion_50k", label: "Coste Activación 50K", category: "economia" },
  { key: "payout_split_pct", label: "Split Retiros", category: "economia" },
  { key: "vps_permitido", label: "VPS Permitido", category: "ejecucion" },
];

function formatValue(key: keyof Omit<FirmaV2, "id" | "nombre">, val: unknown): string {
  if (val === null || val === undefined) return "NO EVIDENCE";
  if (typeof val === "boolean") return val ? "Permitido" : "Prohibido";
  if (key === "trailing_dd_valor_50k" || key === "perdida_diaria_limite_50k" || key === "precio_examen_50k" || key === "coste_activacion_50k") {
    return `$${Number(val).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
  }
  if (key === "consistencia_pct" || key === "payout_split_pct") {
    return `${Number(val)}%`;
  }
  if (key === "min_dias_trading") {
    return `${Number(val)} ${Number(val) === 1 ? "día" : "días"}`;
  }
  if (key === "max_micros_50k") {
    return `${Number(val)} micros`;
  }
  return String(val);
}

function renderCellContent(campo: CampoConFuente<unknown>, key: keyof Omit<FirmaV2, "id" | "nombre">) {
  const isPresent = campo.valor !== null && campo.valor !== undefined;
  const isVerified = isPresent && (campo.source.confidence === "fetch" || campo.source.confidence === "ws_official");

  if (!isVerified || !isPresent) {
    return (
      <div className="space-y-1">
        <span className="text-xs font-mono font-bold tracking-wide" style={{ color: "var(--text-3)" }}>
          NO EVIDENCE
        </span>
        {campo.source.note ? (
          <p className="text-[10px] leading-tight line-clamp-2" style={{ color: "var(--text-3)" }}>
            {campo.source.note}
          </p>
        ) : null}
      </div>
    );
  }

  const formatted = formatValue(key, campo.valor);

  return (
    <div className="space-y-1">
      <div className="text-xs font-mono font-semibold text-neutral-100">
        {formatted}
      </div>
      <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono text-neutral-400">
        <span className="px-1 py-0.2 rounded border border-neutral-700 bg-neutral-900 text-neutral-300">
          {campo.source.confidence}
        </span>
        {campo.source.captured_at ? (
          <span className="text-neutral-500">{campo.source.captured_at}</span>
        ) : null}
        {campo.source.url ? (
          <a
            href={campo.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-0.5 text-neutral-400 hover:text-neutral-200 underline decoration-neutral-600 transition"
          >
            <span>[Fuente]</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
        ) : null}
      </div>
      {campo.source.note ? (
        <p className="text-[10px] text-neutral-400 leading-tight">
          {campo.source.note}
        </p>
      ) : null}
    </div>
  );
}

export default function PropFirmsPage() {
  const [firmas, setFirmas] = useState<FirmaV2[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filtroTexto, setFiltroTexto] = useState<string>("");
  const [selectedFirmId, setSelectedFirmId] = useState<string | null>(null);

  const cargarDatos = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPropFirmsV2();
      setFirmas(data);
      if (data.length > 0 && !selectedFirmId) {
        setSelectedFirmId(data[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al conectar con la API";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  // Recuento exacto de datos verificados vs no verificados
  let totalDatos = 0;
  let datosVerificados = 0;

  for (const firma of firmas) {
    for (const metrica of METRICAS) {
      totalDatos += 1;
      const campo = firma[metrica.key] as CampoConFuente<unknown>;
      if (
        campo &&
        campo.valor !== null &&
        campo.valor !== undefined &&
        (campo.source.confidence === "fetch" || campo.source.confidence === "ws_official")
      ) {
        datosVerificados += 1;
      }
    }
  }

  const firmasFiltradas = firmas.filter((f) => {
    const q = filtroTexto.toLowerCase().trim();
    if (!q) return true;
    return f.nombre.toLowerCase().includes(q) || f.id.toLowerCase().includes(q);
  });

  const selectedFirm = firmas.find((f) => f.id === selectedFirmId) || firmas[0] || null;

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-24 text-neutral-100">
      {/* Banner D7 Retiro de Datos Comerciales */}
      <div className="p-3.5 px-4 rounded-xl border border-neutral-800 bg-neutral-900/80 text-xs font-mono text-neutral-300 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-neutral-400 shrink-0" />
          <span>Aviso D7: cupones y afiliados retirados hasta re-verificación (D7)</span>
        </div>
        <span className="text-[10px] text-neutral-500 uppercase tracking-wider shrink-0">
          Directiva REAL-ONLY · Zero-Mocks
        </span>
      </div>

      {/* Encabezado y Línea de Estado Honesta */}
      <div className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-200 shrink-0">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-neutral-100">
                  Catálogo Maestro Prop Firms v2
                </h1>
                <p className="text-xs font-mono text-neutral-400 mt-0.5">
                  Catálogo v2 · {firmas.length} firmas · fuentes verificadas: {datosVerificados} de {totalDatos} datos
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={cargarDatos}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-medium bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Actualizar</span>
            </button>
            <Link
              href="/fondeo"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-medium bg-neutral-800 hover:bg-neutral-700 text-neutral-200 border border-neutral-700 transition"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Trading Desk</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-neutral-800 bg-neutral-900 text-xs font-mono space-y-1" style={{ borderColor: "var(--loss)" }}>
          <div className="flex items-center gap-2 font-bold" style={{ color: "var(--loss)" }}>
            <AlertTriangle className="w-4 h-4" />
            <span>ERROR DE CONEXIÓN CON LA API (Fail-Closed)</span>
          </div>
          <p className="text-neutral-400 pl-6">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {loading && !error && (
        <div className="p-12 text-center text-xs font-mono text-neutral-400 space-y-2">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-neutral-500" />
          <p>Consultando catálogo canónico v2 con SourceRef...</p>
        </div>
      )}

      {/* Main Content */}
      {!loading && !error && (
        <div className="space-y-6">
          {/* Barra de Filtro y Búsqueda */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-neutral-500" />
              <input
                type="text"
                placeholder="Filtrar firma por nombre..."
                value={filtroTexto}
                onChange={(e) => setFiltroTexto(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs font-mono rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-neutral-600 transition"
              />
            </div>
            <div className="text-xs font-mono text-neutral-500">
              Mostrando {firmasFiltradas.length} de {firmas.length} firmas
            </div>
          </div>

          {/* Tabla Maestra Firma × Campos */}
          <div className="border border-neutral-800 rounded-2xl overflow-hidden bg-neutral-900/40">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-neutral-800 bg-neutral-900/90 text-[11px] font-mono text-neutral-400 uppercase tracking-wider">
                    <th className="p-3.5 px-4 sticky left-0 bg-neutral-900 z-10">Firma</th>
                    {METRICAS.map((m) => (
                      <th key={m.key} className="p-3.5 px-4 min-w-[200px]">
                        {m.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-800/80">
                  {firmasFiltradas.map((firma) => (
                    <tr
                      key={firma.id}
                      onClick={() => setSelectedFirmId(firma.id)}
                      className={`hover:bg-neutral-800/40 transition cursor-pointer ${
                        selectedFirmId === firma.id ? "bg-neutral-800/30" : ""
                      }`}
                    >
                      <td className="p-3.5 px-4 font-bold text-neutral-100 sticky left-0 bg-neutral-950/95 z-10 border-r border-neutral-800/60">
                        <div className="flex items-center gap-2">
                          <Shield className="w-3.5 h-3.5 text-neutral-400" />
                          <span>{firma.nombre}</span>
                        </div>
                        <span className="text-[10px] font-mono font-normal text-neutral-500 block mt-0.5">
                          ID: {firma.id}
                        </span>
                      </td>
                      {METRICAS.map((m) => {
                        const campo = firma[m.key] as CampoConFuente<unknown>;
                        return (
                          <td key={m.key} className="p-3.5 px-4 align-top">
                            {renderCellContent(campo, m.key)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                  {firmasFiltradas.length === 0 && (
                    <tr>
                      <td colSpan={METRICAS.length + 1} className="p-8 text-center text-xs font-mono text-neutral-500">
                        No se encontraron firmas con el filtro actual.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Ficha Detallada de Trazabilidad por Firma */}
          {selectedFirm && (
            <div className="bg-neutral-900/60 border border-neutral-800 rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
                <div className="space-y-0.5">
                  <h2 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-neutral-400" />
                    <span>Auditoría de Fuentes: {selectedFirm.nombre}</span>
                  </h2>
                  <p className="text-xs font-mono text-neutral-400">
                    Desglose detallado de los 11 parámetros y sus referencias primarias oficiales
                  </p>
                </div>
                <span className="text-xs font-mono px-2 py-1 rounded bg-neutral-800 border border-neutral-700 text-neutral-300">
                  {selectedFirm.id}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 pt-2">
                {METRICAS.map((m) => {
                  const campo = selectedFirm[m.key] as CampoConFuente<unknown>;
                  const isPresent = campo.valor !== null && campo.valor !== undefined;
                  const isVerified = isPresent && (campo.source.confidence === "fetch" || campo.source.confidence === "ws_official");

                  return (
                    <div
                      key={m.key}
                      className="p-3.5 rounded-xl border border-neutral-800 bg-neutral-900/80 space-y-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-mono text-neutral-400 uppercase tracking-wider">
                          {m.label}
                        </span>
                        <span
                          className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-neutral-700 bg-neutral-950 text-neutral-400"
                        >
                          {campo.source.confidence}
                        </span>
                      </div>

                      <div className="text-sm font-mono font-bold text-neutral-100">
                        {isVerified ? formatValue(m.key, campo.valor) : (
                          <span style={{ color: "var(--text-3)" }}>NO EVIDENCE</span>
                        )}
                      </div>

                      {campo.source.note ? (
                        <p className="text-[11px] text-neutral-400 leading-relaxed border-t border-neutral-800/80 pt-1.5">
                          {campo.source.note}
                        </p>
                      ) : null}

                      {campo.source.url ? (
                        <div className="pt-1">
                          <a
                            href={campo.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-mono text-neutral-400 hover:text-neutral-200 underline decoration-neutral-600 transition"
                          >
                            <ExternalLink className="w-3 h-3 shrink-0" />
                            <span className="truncate max-w-[220px]">{campo.source.url}</span>
                          </a>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
