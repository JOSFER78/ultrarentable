"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Terminal, RefreshCw, AlertCircle, ArrowUpRight } from "lucide-react";

export interface TareaTablero {
  id: string;
  titulo: string;
  agente: string;
  estado: string;
  prioridad: string;
  maquina: string;
  ambito: string[];
  depende_de: string[];
  estimado: string;
  creado: string;
  actualizado: string;
  archivo: string;
  tiene_parte: boolean;
  tiene_verificacion: boolean;
  resumen: string;
}

export interface TableroApi {
  total: number;
  sin_verificar: number;
  tareas: TareaTablero[];
  por_estado: Record<string, number>;
  ilegibles: Array<{ archivo: string; error: string }>;
}

interface TableroAgentesProps {
  onSelectTarea: (id: string, titulo: string) => void;
  onOpenDoc: (docName: string, title?: string) => void;
  tableroData?: TableroApi | null;
  onRefresh?: () => void;
}

const COLUMNAS_ORDEN = [
  { id: "PENDIENTE", label: "PENDIENTE", sublabel: "listas para coger" },
  { id: "EN_CURSO", label: "EN CURSO", sublabel: "en ejecución" },
  { id: "ENTREGADO", label: "ENTREGADO", sublabel: "esperando verificación" },
  { id: "VERIFICADO", label: "VERIFICADO", sublabel: "completadas y auditadas" },
] as const;

export default function TableroAgentes({
  onSelectTarea,
  onOpenDoc,
  tableroData,
  onRefresh,
}: TableroAgentesProps) {
  const [data, setData] = useState<TableroApi | null>(tableroData ?? null);
  const [loading, setLoading] = useState<boolean>(!tableroData);
  const [error, setError] = useState<string | null>(null);

  const fetchTablero = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/tablero", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as TableroApi;
      setData(json);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar tablero");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tableroData) {
      setData(tableroData);
      setLoading(false);
    } else {
      void fetchTablero();
    }
  }, [tableroData, fetchTablero]);

  const handleManualRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      void fetchTablero();
    }
  };

  const tareas = data?.tareas ?? [];

  // Tareas fuera del flujo estándar (BLOQUEADO y DEVUELTO)
  const tareasAtencion = tareas.filter(
    (t) => t.estado === "BLOQUEADO" || t.estado === "DEVUELTO"
  );

  return (
    <div className="space-y-4 font-sans text-xs">
      {/* 1. Barra de información y enlaces al protocolo */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs leading-relaxed">
        <div className="text-[var(--text-2)]">
          Tablero de orquestación. Un fichero por tarea en{" "}
          <code className="font-mono text-[var(--text-1)]">orchestration/tablero/</code>, leído en vivo: el
          orquestador escribe la tarea y la verifica, AGY la ejecuta y deja su parte de entrega en el mismo
          fichero.{" "}
          <span className="inline-flex items-center gap-1.5 ml-1 font-mono">
            <button
              onClick={() => onOpenDoc("protocolo_tablero", "Cómo funciona el tablero")}
              className="underline text-[var(--text-1)] hover:text-[var(--profit)] cursor-pointer transition"
            >
              Cómo funciona
            </button>
            <span className="text-[var(--text-3)]">·</span>
            <button
              onClick={() => onOpenDoc("agy_empieza_aqui", "AGY: empieza aquí")}
              className="underline text-[var(--text-1)] hover:text-[var(--profit)] cursor-pointer transition"
            >
              Instrucciones de AGY
            </button>
            <span className="text-[var(--text-3)]">·</span>
            <button
              onClick={() => onOpenDoc("buzon", "Buzón orquestador / AGY")}
              className="underline text-[var(--text-1)] hover:text-[var(--profit)] cursor-pointer transition"
            >
              Buzón
            </button>
          </span>
        </div>

        <button
          onClick={handleManualRefresh}
          disabled={loading}
          className="self-start md:self-auto px-2.5 py-1.5 rounded border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5 font-mono text-[11px] shrink-0"
          title="Refrescar estado del tablero en disco"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refrescar</span>
        </button>
      </div>

      {/* 2. Estados de carga o error */}
      {loading && !data && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-8 text-center text-xs font-mono text-[var(--text-3)]">
          <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-[var(--text-3)]" />
          Leyendo tareas del tablero en disco…
        </div>
      )}

      {error && !data && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-8 text-center text-xs font-mono text-[var(--text-3)]">
          sin tareas en el tablero
        </div>
      )}

      {data && tareas.length === 0 && (
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-8 text-center text-xs font-mono text-[var(--text-3)]">
          sin tareas en el tablero
        </div>
      )}

      {/* 3. Cuatro columnas del flujo estándar */}
      {data && tareas.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 items-start">
          {COLUMNAS_ORDEN.map((col) => {
            const tareasEnColumna = tareas.filter((t) => t.estado === col.id);
            const esVerificado = col.id === "VERIFICADO";

            return (
              <div
                key={col.id}
                className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col"
              >
                {/* Cabecera de la Columna */}
                <div
                  className={`px-3.5 py-2.5 border-b border-[var(--border)] flex items-center justify-between ${
                    esVerificado ? "bg-[var(--surface-2)]/90" : "bg-[var(--surface-2)]/60"
                  }`}
                >
                  <div className="flex flex-col">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`font-mono text-xs font-bold uppercase tracking-wider ${
                          esVerificado ? "text-[var(--profit)]" : "text-[var(--text-1)]"
                        }`}
                      >
                        {col.label}
                      </span>
                      <span
                        className={`text-[11px] font-mono px-1.5 py-0.2 rounded font-semibold ${
                          esVerificado
                            ? "bg-[var(--profit)]/15 text-[var(--profit)]"
                            : "bg-[var(--surface-3)] text-[var(--text-2)]"
                        }`}
                      >
                        {tareasEnColumna.length}
                      </span>
                    </div>
                    <span className="text-[10px] text-[var(--text-3)] leading-tight mt-0.5">
                      {col.sublabel}
                    </span>
                  </div>
                </div>

                {/* Lista de Tarjetas */}
                <div className="p-2.5 space-y-2.5 min-h-[140px]">
                  {tareasEnColumna.length === 0 ? (
                    <div className="text-center py-8 text-[11px] text-[var(--text-3)] font-mono">
                      sin tareas
                    </div>
                  ) : (
                    tareasEnColumna.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => onSelectTarea(t.id, t.titulo)}
                        className="w-full text-left bg-[var(--surface-2)]/40 hover:bg-[var(--surface-2)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-lg p-3 transition group cursor-pointer flex flex-col gap-2"
                      >
                        {/* ID y Metadatos superiores */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`font-mono text-base font-extrabold tracking-tight ${
                                esVerificado
                                  ? "text-[var(--profit)]"
                                  : "text-[var(--text-1)] group-hover:text-[var(--text-1)]"
                              }`}
                            >
                              {t.id}
                            </span>
                            {t.prioridad && (
                              <span className="px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[10px] font-mono text-[var(--text-3)] border border-[var(--border)]">
                                {t.prioridad}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <span className="px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[10px] font-mono text-[var(--text-2)] border border-[var(--border)]">
                              {t.agente}
                            </span>
                            <ArrowUpRight className="w-3.5 h-3.5 text-[var(--text-3)] group-hover:text-[var(--text-1)] transition" />
                          </div>
                        </div>

                        {/* Título */}
                        <p className="text-xs font-semibold text-[var(--text-1)] leading-snug">
                          {t.titulo}
                        </p>

                        {/* Dependencias (si existen) */}
                        {t.depende_de && t.depende_de.length > 0 && (
                          <div className="text-[10px] font-mono text-[var(--text-2)] bg-[var(--surface-3)] border border-[var(--border)] px-2 py-0.5 rounded">
                            Depende de: <span className="text-[var(--text-1)]">{t.depende_de.join(", ")}</span>
                          </div>
                        )}

                        {/* Footer de la Tarjeta */}
                        <div className="pt-1 border-t border-[var(--border)]/60 flex items-center justify-between text-[10px] font-mono text-[var(--text-3)]">
                          <span>{t.maquina ? `máq: ${t.maquina}` : ""}</span>
                          {t.actualizado && (
                            <span>{t.actualizado.replace(" UTC", "")}</span>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 4. Franja inferior para Tareas con Atención Requerida (BLOQUEADO / DEVUELTO) */}
      {tareasAtencion.length > 0 && (
        <div className="p-4 rounded-lg border border-amber-500/30 bg-[var(--surface-1)] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-1)]">
                Tareas con Atención Requerida ({tareasAtencion.length})
              </span>
            </div>
            <span className="text-[11px] text-[var(--text-3)] font-mono">
              BLOQUEADO / DEVUELTO
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {tareasAtencion.map((t) => (
              <button
                key={t.id}
                onClick={() => onSelectTarea(t.id, t.titulo)}
                className="text-left p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/60 hover:bg-[var(--surface-2)] hover:border-amber-500/40 transition cursor-pointer space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-base font-extrabold text-[var(--text-1)]">
                      {t.id}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10.5px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      {t.estado}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-[var(--text-3)]">
                    Agente: {t.agente}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-1)] font-semibold leading-snug">
                  {t.titulo}
                </p>
                {t.resumen && (
                  <p className="text-[11px] text-[var(--text-3)] italic line-clamp-2">
                    {t.resumen}
                  </p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 5. Ficheros ilegibles (si los hubiera) */}
      {data && data.ilegibles && data.ilegibles.length > 0 && (
        <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-lg p-3 text-[11px] font-mono text-[var(--text-2)]">
          {data.ilegibles.length} fichero(s) del tablero no legibles:{" "}
          {data.ilegibles.map((i) => `${i.archivo} (${i.error})`).join(" · ")}
        </div>
      )}
    </div>
  );
}
