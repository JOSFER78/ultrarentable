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
      <div className="text-xs font-mono font-semibold text-[var(--text-1)]">
        {formatted}
      </div>
      <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono text-[var(--text-2)]">
        <span className="px-1 py-0.2 rounded border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-1)]">
          {campo.source.confidence}
        </span>
        {campo.source.captured_at ? (
          <span className="text-[var(--text-3)]">{campo.source.captured_at}</span>
        ) : null}
        {campo.source.url ? (
          <a
            href={campo.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-0.5 text-[var(--text-2)] hover:text-[var(--text-1)] underline decoration-[var(--border-strong)] transition"
          >
            <span>[Fuente]</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
        ) : null}
      </div>
      {campo.source.note ? (
        <p className="text-[10px] text-[var(--text-2)] leading-tight">
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
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-24 text-[var(--text-1)]">
      {/* Banner D7 Retiro de Datos Comerciales */}
      <div className="p-3.5 px-4 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-xs font-mono text-[var(--text-1)] flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Info className="w-4 h-4 text-[var(--text-2)] shrink-0" />
          <span>Aviso D7: cupones y afiliados retirados hasta re-verificación (D7)</span>
        </div>
        <span className="text-[10px] text-[var(--text-3)] uppercase tracking-wider shrink-0">
          Directiva REAL-ONLY · Zero-Mocks
        </span>
      </div>

      {/* Encabezado y Línea de Estado Honesta */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-[var(--surface-1)] border border-[var(--border)] flex items-center justify-center text-[var(--text-1)] shrink-0">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-[var(--text-1)]">
                  Catálogo Maestro Prop Firms v2
                </h1>
                <p className="text-xs font-mono text-[var(--text-2)] mt-0.5">
                  Catálogo v2 · {firmas.length} firmas · fuentes verificadas: {datosVerificados} de {totalDatos} datos
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={cargarDatos}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-medium bg-[var(--surface-1)] hover:bg-[var(--surface-1)] text-[var(--text-1)] border border-[var(--border)] transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
              <span>Actualizar</span>
            </button>
            <Link
              href="/fondeo"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-medium bg-[var(--surface-1)] hover:bg-[var(--surface-1)] text-[var(--text-1)] border border-[var(--border)] transition"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Trading Desk</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] text-xs font-mono space-y-1" style={{ borderColor: "var(--loss)" }}>
          <div className="flex items-center gap-2 font-bold" style={{ color: "var(--loss)" }}>
            <AlertTriangle className="w-4 h-4" />
            <span>ERROR DE CONEXIÓN CON LA API (Fail-Closed)</span>
          </div>
          <p className="text-[var(--text-2)] pl-6">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {loading && !error && (
        <div className="p-12 text-center text-xs font-mono text-[var(--text-2)] space-y-2">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto text-[var(--text-3)]" />
          <p>Consultando catálogo canónico v2 con SourceRef...</p>
        </div>
      )}

      {/* Main Content */}
      {!loading && !error && (
        <div className="space-y-6">
          {/* Barra de Filtro y Búsqueda */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-[var(--text-3)]" />
              <input
                type="text"
                placeholder="Filtrar firma por nombre..."
                value={filtroTexto}
                onChange={(e) => setFiltroTexto(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs font-mono rounded-xl bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-1)] placeholder-[var(--text-3)] focus:outline-none focus:border-[var(--border)] transition"
              />
            </div>
            <div className="text-xs font-mono text-[var(--text-3)]">
              Mostrando {firmasFiltradas.length} de {firmas.length} firmas
            </div>
          </div>

          {/* Tabla Maestra Firma × Campos */}
          <div className="border border-[var(--border)] rounded-2xl overflow-hidden bg-[var(--surface-1)]">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--border)] bg-[var(--surface-1)] text-[11px] font-mono text-[var(--text-2)] uppercase tracking-wider">
                    <th className="p-3.5 px-4 sticky left-0 bg-[var(--surface-1)] z-10">Firma</th>
                    {METRICAS.map((m) => (
                      <th key={m.key} className="p-3.5 px-4 min-w-[200px]">
                        {m.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {firmasFiltradas.map((firma) => (
                    <tr
                      key={firma.id}
                      onClick={() => setSelectedFirmId(firma.id)}
                      className={`hover:bg-[var(--surface-1)] transition cursor-pointer ${
                        selectedFirmId === firma.id ? "bg-[var(--surface-1)]" : ""
                      }`}
                    >
                      <td className="p-3.5 px-4 font-bold text-[var(--text-1)] sticky left-0 bg-[var(--surface-1)] z-10 border-r border-[var(--border)]">
                        <div className="flex items-center gap-2">
                          <Shield className="w-3.5 h-3.5 text-[var(--text-2)]" />
                          <span>{firma.nombre}</span>
                        </div>
                        <span className="text-[10px] font-mono font-normal text-[var(--text-3)] block mt-0.5">
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
                      <td colSpan={METRICAS.length + 1} className="p-8 text-center text-xs font-mono text-[var(--text-3)]">
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
            <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
                <div className="space-y-0.5">
                  <h2 className="text-lg font-bold text-[var(--text-1)] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-[var(--text-2)]" />
                    <span>Auditoría de Fuentes: {selectedFirm.nombre}</span>
                  </h2>
                  <p className="text-xs font-mono text-[var(--text-2)]">
                    Desglose detallado de los 11 parámetros y sus referencias primarias oficiales
                  </p>
                </div>
                <span className="text-xs font-mono px-2 py-1 rounded bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-1)]">
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
                      className="p-3.5 rounded-xl border border-[var(--border)] bg-[var(--surface-1)] space-y-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[11px] font-mono text-[var(--text-2)] uppercase tracking-wider">
                          {m.label}
                        </span>
                        <span
                          className="text-[10px] font-mono px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-2)]"
                        >
                          {campo.source.confidence}
                        </span>
                      </div>

                      <div className="text-sm font-mono font-bold text-[var(--text-1)]">
                        {isVerified ? formatValue(m.key, campo.valor) : (
                          <span style={{ color: "var(--text-3)" }}>NO EVIDENCE</span>
                        )}
                      </div>

                      {campo.source.note ? (
                        <p className="text-[11px] text-[var(--text-2)] leading-relaxed border-t border-[var(--border)] pt-1.5">
                          {campo.source.note}
                        </p>
                      ) : null}

                      {campo.source.url ? (
                        <div className="pt-1">
                          <a
                            href={campo.source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-mono text-[var(--text-2)] hover:text-[var(--text-1)] underline decoration-[var(--border-strong)] transition"
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
