"use client";

import React, { useCallback, useEffect, useState, useMemo } from "react";
import {
  Cpu,
  RefreshCw,
  Server,
  Database,
  Layers,
  Clock,
  Zap,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import {
  getM1Rejilla,
  type RejillaM1Response,
  type CeldaRejillaM1,
} from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";

const TF_ORDEN = ["1m", "5m", "15m", "1h", "4h"];

interface ActivoDetalle {
  simbolo: string;
  nombre: string;
  contrato_grande?: string | null;
  datos?: {
    tf_base: string;
    desde: string;
    hasta: string;
    dias: number;
    velas_base: number;
  } | null;
  costes?: {
    spread?: number;
    slippage?: number;
    comision?: number;
  } | null;
  celdasPorTf: Record<string, CeldaRejillaM1>;
}

export default function PaginaGeneracion() {
  const [rejilla, setRejilla] = useState<RejillaM1Response | null>(null);
  const [cargando, setCargando] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const data = await getM1Rejilla();
      setRejilla(data);
      setError(null);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (e: any) {
      setRejilla(null);
      setError(e.message || "El servicio no responde ahora mismo. Se está reintentando solo.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
    // Refresco automático cada 30 segundos (mandato: igual que /plan)
    const interval = setInterval(cargar, 30000);
    return () => clearInterval(interval);
  }, [cargar]);

  // Agrupación dinámica de celdas por activo
  const activos = useMemo<ActivoDetalle[]>(() => {
    if (!rejilla?.celdas || rejilla.celdas.length === 0) return [];
    const mapa = new Map<string, ActivoDetalle>();

    for (const c of rejilla.celdas) {
      let act = mapa.get(c.simbolo);
      if (!act) {
        act = {
          simbolo: c.simbolo,
          nombre: c.nombre,
          contrato_grande: c.contrato_grande,
          datos: c.datos,
          costes: c.costes,
          celdasPorTf: {},
        };
        mapa.set(c.simbolo, act);
      }
      if (!act.datos && c.datos) {
        act.datos = c.datos;
      }
      if (!act.costes && c.costes) {
        act.costes = c.costes;
      }
      act.celdasPorTf[c.tf_etiqueta] = c;
    }

    return Array.from(mapa.values());
  }, [rejilla]);

  // Buscar celda actualmente en curso para el KPI superior
  const celdaEnCurso = useMemo(() => {
    if (!rejilla?.celdas) return null;
    return (
      rejilla.celdas.find(
        (c) =>
          c.estado === "EN_CURSO" ||
          (rejilla.bucle?.celda_en_curso &&
            c.proyecto === rejilla.bucle.celda_en_curso)
      ) ?? null
    );
  }, [rejilla]);

  const sqxActivo = Boolean(rejilla?.disponible && rejilla?.bucle?.activo);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
                <span>M1: Generación y Rejilla de Celdas (StrategyQuant X)</span>
                {rejilla?.resumen && (
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)]">
                    {rejilla.resumen.celdas} celdas en manifiesto
                  </span>
                )}
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono">
                Rejilla leída en tiempo real del servidor. Estado de construcción, caudales por celda y bancos de estrategias.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {lastUpdated && (
              <span className="text-xs font-mono text-[var(--text-3)] hidden md:inline">
                Actualizado: {lastUpdated}
              </span>
            )}
            <button
              onClick={() => void cargar()}
              disabled={cargando}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] font-mono text-xs hover:bg-[var(--surface-3)] transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${cargando ? "animate-spin" : ""}`} />
              <span>Actualizar</span>
            </button>
          </div>
        </div>
      </div>

      {/* Navegación Modular M1–M5 */}
      <NavBloques activo="generacion" />

      {/* Si el servicio no está disponible, mostrar aviso sobrio en gris */}
      {rejilla && !rejilla.disponible && (
        <div className="p-4 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg text-xs font-mono text-[var(--text-2)] flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--text-3)] shrink-0 animate-pulse" />
          <span>{rejilla.motivo_no_disponible || "El servicio no responde ahora mismo. Se está reintentando solo."}</span>
        </div>
      )}

      {error && !rejilla && (
        <div className="p-4 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg text-xs font-mono text-[var(--text-2)] flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--text-3)] shrink-0 animate-pulse" />
            <span>El servicio no responde ahora mismo. Se está reintentando solo.</span>
          </div>
          <button
            onClick={() => void cargar()}
            className="px-3 py-1 bg-[var(--surface-3)] hover:bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-1)] rounded text-xs font-semibold"
          >
            Reintentar ahora
          </button>
        </div>
      )}

      {/* 2. CUATRO CIFRAS CLAVE DEL RESUMEN Y DEL BUCLE */}
      {rejilla && rejilla.disponible && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
          {/* Cifra 1: Celdas con datos */}
          <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">
              Celdas con Datos
            </span>
            <div className="text-xl font-bold text-[var(--text-1)]">
              {rejilla.resumen?.con_datos ?? 0}
              <span className="text-xs font-normal text-[var(--text-3)] ml-1">
                / {rejilla.resumen?.celdas ?? 0}
              </span>
            </div>
            <span className="text-[11px] text-[var(--text-3)] block">
              {rejilla.resumen && rejilla.resumen.celdas - rejilla.resumen.con_datos > 0
                ? `${rejilla.resumen.celdas - rejilla.resumen.con_datos} sin datos todavía`
                : "100% cargadas"}
            </span>
          </div>

          {/* Cifra 2: Celdas con proyecto */}
          <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">
              Proyectos Creados
            </span>
            <div className="text-xl font-bold text-[var(--text-1)]">
              {rejilla.resumen?.con_proyecto ?? 0}
              <span className="text-xs font-normal text-[var(--text-3)] ml-1">
                / {rejilla.resumen?.celdas ?? 0}
              </span>
            </div>
            <span className="text-[11px] text-[var(--text-3)] block">
              En StrategyQuant X
            </span>
          </div>

          {/* Cifra 3: Estrategias en bancos */}
          <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">
              Estrategias en Bancos
            </span>
            <div className="text-xl font-bold text-[var(--profit)]">
              {rejilla.resumen?.estrategias_en_bancos?.toLocaleString() ?? 0}
            </div>
            <span className="text-[11px] text-[var(--text-3)] block">
              Acumuladas en todas las celdas
            </span>
          </div>

          {/* Cifra 4: Celda en construcción ahora mismo */}
          <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">
                En Construcción Ahora
              </span>
              <span
                className={`w-2 h-2 rounded-full ${
                  sqxActivo ? "bg-[var(--profit)] animate-pulse" : "bg-[var(--text-3)]"
                }`}
              />
            </div>
            <div className="text-sm font-bold text-[var(--text-1)] truncate">
              {rejilla.bucle?.celda_en_curso || "Ninguna"}
            </div>
            <span className="text-[11px] text-[var(--text-3)] block truncate">
              {celdaEnCurso
                ? `${celdaEnCurso.por_hora || 0}/h · ${celdaEnCurso.tiempo || "en curso"}`
                : sqxActivo
                ? `Ronda ${rejilla.bucle?.ronda ?? 1} (${rejilla.bucle?.horas_por_celda ?? 1} h/celda)`
                : "Bucle en reposo"}
            </span>
          </div>
        </div>
      )}

      {/* 3. LA REJILLA DE CELDAS: MATRIZ DINÁMICA ACTIVO X TEMPORALIDAD */}
      {rejilla && rejilla.disponible && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden space-y-3 p-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
            <div>
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Layers className="w-4 h-4 text-[var(--text-2)]" />
                <span>Rejilla de Generación M1 (40 Celdas Reales)</span>
              </h2>
              <p className="text-xs text-[var(--text-3)] font-mono mt-0.5">
                Una fila por activo y una columna por temporalidad. Los datos y el estado se actualizan en vivo desde el servidor.
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-3)]">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--profit)] animate-pulse" />
                <span>En curso</span>
              </span>
              <span>·</span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[var(--text-3)]" />
                <span>Pendiente</span>
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse font-mono text-xs">
              <thead>
                <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]/50 text-[var(--text-2)] text-[11px] uppercase tracking-wider">
                  <th className="py-2.5 px-3 min-w-[200px]">Activo / Contrato</th>
                  {TF_ORDEN.map((tf) => (
                    <th key={tf} className="py-2.5 px-3 text-center min-w-[130px]">
                      {tf}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]/60">
                {activos.map((act) => {
                  const tieneDatos = Boolean(act.datos);

                  return (
                    <tr key={act.simbolo} className="hover:bg-[var(--surface-2)]/30 transition">
                      {/* Cabecera de Fila: Activo */}
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-[var(--text-1)]">
                            {act.simbolo}
                          </span>
                          {act.contrato_grande && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)]">
                              micro de {act.contrato_grande}
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-[var(--text-3)] truncate max-w-[220px]">
                          {act.nombre}
                        </div>
                      </td>

                      {/* Cruces por Temporalidad */}
                      {TF_ORDEN.map((tf) => {
                        const celda = act.celdasPorTf[tf];

                        if (!celda) {
                          return (
                            <td key={tf} className="py-3 px-3 text-center text-[var(--text-3)] text-[11px]">
                              -
                            </td>
                          );
                        }

                        const esEnCurso =
                          celda.estado === "EN_CURSO" ||
                          (rejilla.bucle?.celda_en_curso &&
                            celda.proyecto === rejilla.bucle.celda_en_curso);
                        const esHecha = celda.estado === "HECHA";
                        const sinDatos = !celda.datos;

                        return (
                          <td key={tf} className="py-2.5 px-2.5">
                            <div
                              className={`p-2 rounded border text-center transition flex flex-col justify-center min-h-[58px] ${
                                esEnCurso
                                  ? "bg-[var(--profit)]/10 border-[var(--profit)] shadow-[0_0_10px_rgba(16,185,129,0.15)]"
                                  : sinDatos
                                  ? "bg-[var(--surface-2)]/20 border-dashed border-[var(--border)] text-[var(--text-3)] opacity-70"
                                  : "bg-[var(--surface-2)]/40 border-[var(--border)] hover:border-[var(--border-strong)]"
                              }`}
                            >
                              {sinDatos ? (
                                <span className="text-[10px] text-[var(--text-3)] italic">
                                  sin datos todavía
                                </span>
                              ) : esEnCurso ? (
                                <div className="space-y-0.5">
                                  <span className="text-[10px] font-bold text-[var(--profit)] uppercase tracking-wider flex items-center justify-center gap-1">
                                    <Zap className="w-2.5 h-2.5 animate-pulse" />
                                    <span>EN CURSO</span>
                                  </span>
                                  <div className="text-[11px] font-bold text-[var(--text-1)]">
                                    {celda.generadas !== null && celda.generadas !== undefined
                                      ? `${celda.generadas.toLocaleString()} gen.`
                                      : "trabajando"}
                                  </div>
                                  {celda.por_hora && (
                                    <div className="text-[9.5px] text-[var(--text-2)]">
                                      {celda.por_hora}/h
                                    </div>
                                  )}
                                </div>
                              ) : esHecha ? (
                                <div className="space-y-0.5">
                                  <span className="text-[10px] font-bold text-[var(--profit)] uppercase">
                                    HECHA
                                  </span>
                                  <div className="text-[11px] text-[var(--text-1)]">
                                    {celda.en_banco ?? 0} en banco
                                  </div>
                                </div>
                              ) : (
                                <div className="space-y-0.5">
                                  <span className="text-[10px] text-[var(--text-3)] uppercase font-semibold">
                                    {celda.estado || "PENDIENTE"}
                                  </span>
                                  <div className="text-[10px] text-[var(--text-3)]">
                                    {celda.en_banco !== null && celda.en_banco !== undefined && celda.en_banco > 0
                                      ? `${celda.en_banco} en banco`
                                      : "esperando turno"}
                                  </div>
                                </div>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. DETALLE POR ACTIVO (Datasets reales y costes supuestos de manifiesto) */}
      {rejilla && rejilla.disponible && activos.length > 0 && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
          <div className="border-b border-[var(--border)] pb-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Database className="w-4 h-4 text-[var(--text-2)]" />
                <span>Detalle de Cobertura y Fricciones por Activo</span>
              </h2>
              <p className="text-[11px] text-[var(--text-3)] mt-0.5">
                Velas de 1 minuto cargadas en el servidor y costes de fricción modelados en StrategyQuant.
              </p>
            </div>
            <span className="text-[10.5px] text-[var(--text-3)]">
              Costes marcados como <strong>supuesto</strong> en el manifiesto oficial
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {activos.map((act) => {
              const d = act.datos;
              const c = act.costes;

              return (
                <div
                  key={act.simbolo}
                  className="p-3 bg-[var(--surface-2)]/30 border border-[var(--border)] rounded-lg space-y-2"
                >
                  <div className="flex items-center justify-between border-b border-[var(--border)]/50 pb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-[var(--text-1)]">
                        {act.simbolo}
                      </span>
                      <span className="text-xs text-[var(--text-2)] font-sans">
                        {act.nombre}
                      </span>
                    </div>
                    {act.contrato_grande && (
                      <span className="text-[10px] text-[var(--text-3)]">
                        grande: {act.contrato_grande}
                      </span>
                    )}
                  </div>

                  {/* Cobertura de Datos */}
                  <div className="text-[11px] space-y-1">
                    <div className="flex justify-between text-[var(--text-2)]">
                      <span className="text-[var(--text-3)]">Datos base (M1):</span>
                      {d ? (
                        <span className="text-[var(--text-1)] font-semibold">
                          {d.desde} → {d.hasta} ({d.dias} días)
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)] italic">Sin datos todavía (descarga en curso)</span>
                      )}
                    </div>

                    <div className="flex justify-between text-[var(--text-2)]">
                      <span className="text-[var(--text-3)]">Velas 1 min:</span>
                      <span>
                        {d?.velas_base ? d.velas_base.toLocaleString() : "0"}
                      </span>
                    </div>

                    {/* Costes Supuestos */}
                    <div className="flex justify-between text-[var(--text-2)] pt-1 border-t border-[var(--border)]/40">
                      <span className="text-[var(--text-3)]">Fricción supuesta:</span>
                      <span>
                        Spread {c?.spread ?? 1} tick · Slip {c?.slippage ?? 2} ticks · Com. ${c?.comision ?? 2.0}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
