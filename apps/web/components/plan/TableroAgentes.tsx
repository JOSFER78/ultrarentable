"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Terminal, RefreshCw, AlertCircle, ArrowUpRight, User, Bot, Cpu } from "lucide-react";

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
  motivo_devolucion?: string;
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
  { id: "DEVUELTO", label: "DEVUELTA", sublabel: "devuelta con correcciones", badgeClass: "bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)]" },
  { id: "PENDIENTE", label: "ESPERANDO", sublabel: "listas para coger", badgeClass: "bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border)]" },
  { id: "EN_CURSO", label: "EN MARCHA", sublabel: "en ejecución activa", badgeClass: "bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border-strong)]" },
  { id: "ENTREGADO", label: "ENTREGADA", sublabel: "pendiente de comprobar", badgeClass: "bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)]" },
  { id: "VERIFICADO", label: "COMPROBADA Y CERRADA", sublabel: "auditadas y verificadas", badgeClass: "bg-[var(--profit)]/15 text-[var(--profit)] border border-[var(--profit)]/30" },
  { id: "BLOQUEADO", label: "BLOQUEADA", sublabel: "bloqueadas", badgeClass: "bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)]" },
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
  const [filtroAgente, setFiltroAgente] = useState<string>("TODOS");

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

  const todasTareas = data?.tareas ?? [];
  const tareas = filtroAgente === "TODOS"
    ? todasTareas
    : todasTareas.filter((t) => t.agente?.toUpperCase() === filtroAgente);

  const totalAgy = todasTareas.filter((t) => t.agente?.toUpperCase() === "AGY").length;
  const totalEmilio = todasTareas.filter((t) => t.agente?.toUpperCase() === "EMILIO").length;
  const totalOrq = todasTareas.filter((t) => t.agente?.toUpperCase() === "ORQ").length;

  return (
    <div className="space-y-4 font-sans text-xs w-full">
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

      {/* 2. Filtro por Agente Responsable (Distinción inmediata AGY / Emilio / ORQ) */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg px-3 py-2">
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-[var(--text-3)] font-mono mr-1">Filtrar por responsable:</span>
          <button
            onClick={() => setFiltroAgente("TODOS")}
            className={`px-2.5 py-1 rounded text-xs font-mono transition cursor-pointer ${
              filtroAgente === "TODOS"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-2)]"
            }`}
          >
            Todos ({todasTareas.length})
          </button>
          <button
            onClick={() => setFiltroAgente("AGY")}
            className={`px-2.5 py-1 rounded text-xs font-mono transition cursor-pointer flex items-center gap-1.5 ${
              filtroAgente === "AGY"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-2)]"
            }`}
          >
            <Bot className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>AGY ({totalAgy})</span>
          </button>
          <button
            onClick={() => setFiltroAgente("EMILIO")}
            className={`px-2.5 py-1 rounded text-xs font-mono transition cursor-pointer flex items-center gap-1.5 border ${
              filtroAgente === "EMILIO"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border-[var(--border-strong)] shadow-sm"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-2)] border-[var(--border)]"
            }`}
          >
            <User className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>Mis Tareas (Emilio: {totalEmilio})</span>
          </button>
          <button
            onClick={() => setFiltroAgente("ORQ")}
            className={`px-2.5 py-1 rounded text-xs font-mono transition cursor-pointer flex items-center gap-1.5 border ${
              filtroAgente === "ORQ"
                ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border-[var(--border-strong)]"
                : "text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-[var(--surface-2)] border-transparent"
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>Orquestador ({totalOrq})</span>
          </button>
        </div>

        <div className="text-[11px] font-mono text-[var(--text-3)]">
          {data?.sin_verificar ?? 0} tareas pendientes de auditoría o resolución
        </div>
      </div>

      {/* 3. Estados de carga o error */}
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
          {filtroAgente === "TODOS" ? "sin tareas en el tablero" : `sin tareas para el responsable ${filtroAgente}`}
        </div>
      )}

      {/* 4. SEIS COLUMNAS DEL TABLERO KANBAN (DEVUELTO primero, BLOQUEADO al final) */}
      {data && tareas.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 items-start w-full">
          {COLUMNAS_ORDEN.map((col) => {
            const tareasEnColumna = tareas.filter((t) => t.estado === col.id);
            const esDevuelto = col.id === "DEVUELTO";
            const esVerificado = col.id === "VERIFICADO";
            const esBloqueado = col.id === "BLOQUEADO";

            return (
              <div
                key={col.id}
                className={`bg-[var(--surface-1)] border rounded-lg overflow-hidden flex flex-col ${
                  esDevuelto
                    ? "border-[var(--loss)] shadow-sm"
                    : esBloqueado
                    ? "border-[var(--border)] opacity-80"
                    : "border-[var(--border)]"
                }`}
              >
                {/* Cabecera de la Columna */}
                <div
                  className={`px-3 py-2.5 border-b border-[var(--border)] flex items-center justify-between ${
                    esDevuelto
                      ? "bg-[var(--surface-2)]"
                      : esVerificado
                      ? "bg-[var(--surface-2)]"
                      : "bg-[var(--surface-2)]/60"
                  }`}
                >
                  <div className="flex flex-col min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`font-mono text-xs font-bold uppercase tracking-wider truncate ${
                          esDevuelto
                            ? "text-[var(--loss)]"
                            : esVerificado
                            ? "text-[var(--profit)]"
                            : "text-[var(--text-1)]"
                        }`}
                      >
                        {col.label}
                      </span>
                      <span
                        className={`text-[11px] font-mono px-1.5 py-0.2 rounded font-semibold shrink-0 ${col.badgeClass}`}
                      >
                        {tareasEnColumna.length}
                      </span>
                    </div>
                    <span className="text-[10px] text-[var(--text-3)] leading-tight mt-0.5 truncate">
                      {col.sublabel}
                    </span>
                  </div>
                </div>

                {/* Lista de Tarjetas */}
                <div className="p-2 space-y-2.5 min-h-[140px]">
                  {tareasEnColumna.length === 0 ? (
                    <div className="text-center py-8 text-[11px] text-[var(--text-3)] font-mono">
                      sin tareas
                    </div>
                  ) : (
                    tareasEnColumna.map((t) => {
                      const esEmilio = t.agente?.toUpperCase() === "EMILIO";
                      const esOrq = t.agente?.toUpperCase() === "ORQ";
                      const esAgy = t.agente?.toUpperCase() === "AGY";

                      return (
                        <button
                          key={t.id}
                          onClick={() => onSelectTarea(t.id, t.titulo)}
                          className={`w-full text-left border rounded-lg p-2.5 transition group cursor-pointer flex flex-col gap-2 ${
                            esEmilio
                              ? "bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border-[var(--border-strong)] shadow-sm"
                              : esDevuelto
                              ? "bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border-[var(--loss)]/50 hover:border-[var(--loss)]"
                              : "bg-[var(--surface-2)]/40 hover:bg-[var(--surface-2)] border-[var(--border)] hover:border-[var(--border-strong)]"
                          }`}
                        >
                          {/* ID y Responsable */}
                          <div className="flex items-start justify-between gap-1.5">
                            <div className="flex items-center gap-1.5">
                              <span
                                className={`font-mono text-sm font-extrabold tracking-tight ${
                                  esDevuelto
                                    ? "text-[var(--loss)]"
                                    : esVerificado
                                    ? "text-[var(--profit)]"
                                    : "text-[var(--text-1)]"
                                }`}
                              >
                                {t.id}
                              </span>
                              {t.prioridad && (
                                <span className="px-1 py-0.2 rounded bg-[var(--surface-3)] text-[9.5px] font-mono text-[var(--text-3)] border border-[var(--border)]">
                                  {t.prioridad}
                                </span>
                              )}
                            </div>

                            {/* Badge de Responsable y Máquina */}
                            <div className="flex items-center gap-1 shrink-0">
                              {t.maquina && (
                                <span className="px-1.5 py-0.5 rounded font-mono text-[9.5px] uppercase bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)]">
                                  {t.maquina}
                                </span>
                              )}
                              {esEmilio ? (
                                <span className="px-1.5 py-0.5 rounded font-mono text-[10px] font-bold bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border-strong)] flex items-center gap-1">
                                  <User className="w-2.5 h-2.5 text-[var(--text-2)]" />
                                  <span>EMILIO</span>
                                </span>
                              ) : esOrq ? (
                                <span className="px-1.5 py-0.5 rounded font-mono text-[10px] font-bold bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)] flex items-center gap-1">
                                  <Cpu className="w-2.5 h-2.5 text-[var(--text-3)]" />
                                  <span>ORQ</span>
                                </span>
                              ) : (
                                <span className="px-1.5 py-0.5 rounded font-mono text-[10px] font-bold bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border)] flex items-center gap-1">
                                  <Bot className="w-2.5 h-2.5 text-[var(--profit)]" />
                                  <span>AGY</span>
                                </span>
                              )}
                              <ArrowUpRight className="w-3 h-3 text-[var(--text-3)] group-hover:text-[var(--text-1)] transition" />
                            </div>
                          </div>

                          {/* Título de la tarea */}
                          <p className="text-[11.5px] font-semibold text-[var(--text-1)] leading-snug">
                            {t.titulo}
                          </p>

                          {/* En DEVUELTO: Motivo de la Devolución a Simple Vista */}
                          {esDevuelto && t.motivo_devolucion && (
                            <div className="text-[10.5px] font-mono text-[var(--loss)] bg-[var(--loss-dim)] border border-[var(--loss)] p-2 rounded leading-snug">
                              <div className="flex items-center gap-1 font-bold mb-0.5">
                                <AlertCircle className="w-3 h-3 shrink-0" />
                                <span>Por qué volvió:</span>
                              </div>
                              <p className="line-clamp-3 text-[var(--text-1)]">{t.motivo_devolucion}</p>
                            </div>
                          )}

                          {/* Dependencias (si existen) */}
                          {t.depende_de && t.depende_de.length > 0 && (
                            <div className="text-[9.5px] font-mono text-[var(--text-2)] bg-[var(--surface-3)] border border-[var(--border)] px-1.5 py-0.5 rounded truncate">
                              Dep: <span className="text-[var(--text-1)]">{t.depende_de.join(", ")}</span>
                            </div>
                          )}

                          {/* Footer de la Tarjeta */}
                          <div className="pt-1 border-t border-[var(--border)]/60 flex items-center justify-between text-[9.5px] font-mono text-[var(--text-3)]">
                            <span>{t.maquina ? `máq: ${t.maquina}` : ""}</span>
                            {t.actualizado && (
                              <span>{t.actualizado.replace(" UTC", "")}</span>
                            )}
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            );
          })}
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
