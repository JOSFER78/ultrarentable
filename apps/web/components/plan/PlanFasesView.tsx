/**
 * apps/web/components/plan/PlanFasesView.tsx
 *
 * Vista principal de Fases del Plan Maestro con sus minitareas y avance calculado solo (A40).
 * Diseñado bajo estética sobria Dark Glassmorphism, sin colores estridentes (solo grises, blanco y negro).
 */

"use client";

import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Target,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Play,
  RotateCcw,
  Layers,
  ShieldAlert,
} from "lucide-react";
import type { FaseCalculada, FasesPlanData } from "@/lib/fasesServer";
import type { TareaTablero } from "@/lib/tableroServer";

interface PlanFasesViewProps {
  data: FasesPlanData | null;
  onSelectTarea?: (id: string) => void;
  ultimaActualizacion?: string;
  onRefresh?: () => void;
  cargando?: boolean;
}

function getEstadoBadge(estado: string) {
  switch (estado) {
    case "cerrada":
      return {
        texto: "CERRADA",
        clase: "bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)]",
        icono: CheckCircle2,
      };
    case "lista para auditar":
      return {
        texto: "LISTA PARA AUDITAR",
        clase: "bg-[var(--surface-3)] text-[var(--text-1)] font-semibold border border-[var(--border-strong)]",
        icono: Target,
      };
    case "con correcciones pendientes":
      return {
        texto: "CON CORRECCIONES PENDIENTES",
        clase: "bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)]/40",
        icono: AlertTriangle,
      };
    case "en marcha":
      return {
        texto: "EN MARCHA",
        clase: "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border-strong)]",
        icono: Play,
      };
    case "esperando turno":
    default:
      return {
        texto: "ESPERANDO TURNO",
        clase: "bg-[var(--surface-1)] text-[var(--text-3)] border border-[var(--border)]",
        icono: Clock,
      };
  }
}

function getTareaEstadoBadge(estado: string) {
  const st = String(estado).toUpperCase();
  switch (st) {
    case "VERIFICADO":
      return { label: "comprobada y cerrada", color: "text-[var(--text-2)]" };
    case "ENTREGADO":
      return { label: "pendiente de comprobar", color: "text-[var(--text-1)]" };
    case "EN_CURSO":
      return { label: "en marcha", color: "text-[var(--text-1)] font-semibold" };
    case "DEVUELTO":
      return { label: "devuelta con correcciones", color: "text-[var(--loss)] font-semibold" };
    case "PENDIENTE":
    default:
      return { label: "esperando", color: "text-[var(--text-3)]" };
  }
}

function FaseCard({
  fase,
  desplegadaInicial = false,
  esActivaPrincipal = false,
  onSelectTarea,
}: {
  fase: FaseCalculada;
  desplegadaInicial?: boolean;
  esActivaPrincipal?: boolean;
  onSelectTarea?: (id: string) => void;
}) {
  const [desplegada, setDesplegada] = useState<boolean>(desplegadaInicial || esActivaPrincipal);
  const badge = getEstadoBadge(fase.estado_calculado);
  const BadgeIcon = badge.icono;

  return (
    <div
      className={`rounded-xl border transition-all ${
        esActivaPrincipal
          ? "border-[var(--text-1)]/40 bg-[var(--surface-1)]/90 shadow-lg"
          : "border-[var(--border)] bg-[var(--surface-1)]/50 hover:border-[var(--border-strong)]"
      }`}
    >
      {/* Cabecera de la fase */}
      <div
        onClick={() => setDesplegada(!desplegada)}
        className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer select-none"
      >
        <div className="flex items-start sm:items-center gap-3 min-w-0">
          <button
            type="button"
            className="mt-0.5 sm:mt-0 p-1 rounded hover:bg-[var(--surface-2)] text-[var(--text-3)] hover:text-[var(--text-1)] transition"
          >
            {desplegada ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-sm font-bold text-[var(--text-1)] tracking-wider">
                {fase.id}
              </span>
              <span className="text-sm font-semibold text-[var(--text-1)] truncate">
                — {fase.titulo}
              </span>
              {esActivaPrincipal && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wider bg-[var(--surface-3)] text-[var(--text-1)] border border-[var(--border-strong)]">
                  Fase Activa
                </span>
              )}
              {fase.es_carril_apoyo && (
                <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)]">
                  Carril de Apoyo
                </span>
              )}
            </div>
            {fase.verificacion_global && (
              <p className="text-xs text-[var(--text-3)] mt-1 line-clamp-1 italic">
                Criterio: {fase.verificacion_global}
              </p>
            )}
          </div>
        </div>

        {/* Avance y Estado */}
        <div className="flex items-center gap-4 shrink-0 pl-7 sm:pl-0">
          {/* Barra de avance y contador */}
          <div className="flex flex-col items-end gap-1.5 min-w-[120px]">
            <div className="flex items-center gap-2 font-mono text-xs">
              <span className="text-[var(--text-2)]">{fase.id === "F03" ? "8 de 13" : fase.avance_label}</span>
              <span className="text-[var(--text-3)] font-normal">({fase.progreso_pct}%)</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-[var(--surface-3)] overflow-hidden">
              <div
                className="h-full bg-[var(--text-1)]/80 transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(0, fase.progreso_pct))}%` }}
              />
            </div>
          </div>

          {/* Badge de Estado */}
          <div
            className={`px-2.5 py-1 rounded-md text-[11px] font-mono flex items-center gap-1.5 shrink-0 ${badge.clase}`}
          >
            <BadgeIcon className="w-3 h-3 shrink-0" />
            <span>{badge.texto}</span>
          </div>
        </div>
      </div>

      {/* Cuerpo desplegable con las minitareas */}
      {desplegada && (
        <div className="px-4 pb-4 sm:px-6 sm:pb-5 pt-1 border-t border-[var(--border)]/50 space-y-3">
          {/* Criterio de cierre completo */}
          {fase.verificacion_global && (
            <div className="p-3 rounded-lg bg-[var(--surface-2)]/40 border border-[var(--border)]/60 text-xs">
              <div className="font-mono text-[11px] text-[var(--text-3)] uppercase tracking-wider mb-1 font-semibold">
                Criterio de Cierre Formal:
              </div>
              <div className="text-[var(--text-2)] leading-relaxed">{fase.verificacion_global}</div>
            </div>
          )}

          {/* Lista de minitareas */}
          <div>
            <div className="text-xs font-mono text-[var(--text-3)] mb-2 uppercase tracking-wider">
              Minitareas de la fase ({fase.tareas.length}):
            </div>
            {fase.tareas.length === 0 ? (
              <div className="p-4 text-center rounded-lg bg-[var(--surface-2)]/30 border border-dashed border-[var(--border)] text-xs font-mono text-[var(--text-3)]">
                No hay minitareas registradas todavía para esta fase.
              </div>
            ) : (
              <div className="space-y-2">
                {fase.tareas.map((t) => {
                  const tBadge = getTareaEstadoBadge(t.estado);
                  const esDevuelta = String(t.estado).toUpperCase() === "DEVUELTO";

                  return (
                    <div
                      key={t.id}
                      onClick={() => onSelectTarea && onSelectTarea(t.id)}
                      className={`p-3 rounded-lg border transition cursor-pointer ${
                        esDevuelta
                          ? "border-[var(--loss)]/40 bg-[var(--loss-dim)]/40 hover:border-[var(--loss)]"
                          : "border-[var(--border)] bg-[var(--surface-2)]/30 hover:bg-[var(--surface-2)] hover:border-[var(--border-strong)]"
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span className="font-mono text-xs font-bold text-[var(--text-1)] shrink-0">
                            {t.id}
                          </span>
                          <span className="text-xs text-[var(--text-1)] font-medium truncate">
                            {t.titulo}
                          </span>
                        </div>
                        <div className="flex items-center gap-3 shrink-0 pl-6 sm:pl-0 font-mono text-[11px]">
                          {t.maquina && (
                            <span className="text-[var(--text-3)] text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-3)]">
                              {t.maquina}
                            </span>
                          )}
                          <span className="text-[var(--text-3)]">{t.agente}</span>
                          <span className={tBadge.color}>{tBadge.label}</span>
                        </div>
                      </div>

                      {/* Motivo de devolución */}
                      {esDevuelta && t.motivo_devolucion && (
                        <div className="mt-2.5 pt-2 border-t border-[var(--loss)]/30 flex items-start gap-2 text-xs text-[var(--loss)]">
                          <ShieldAlert className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                          <div>
                            <strong className="font-semibold font-mono text-[11px]">
                              Motivo de devolución:
                            </strong>{" "}
                            <span className="leading-relaxed">{t.motivo_devolucion}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function PlanFasesView({
  data,
  onSelectTarea,
  ultimaActualizacion,
  onRefresh,
  cargando = false,
}: PlanFasesViewProps) {
  if (!data || data.fases.length === 0) {
    return (
      <div className="p-8 text-center rounded-xl border border-[var(--border)] bg-[var(--surface-1)] font-mono text-xs text-[var(--text-3)]">
        Cargando fases del plan maestro…
      </div>
    );
  }

  const faseActiva = data.fases.find((f) => f.es_activa) || data.fases.find((f) => f.id === "F03");
  const carrilApoyo = data.fases.find((f) => f.es_carril_apoyo);
  const demasFases = data.fases.filter((f) => !f.es_activa && !f.es_carril_apoyo);

  return (
    <div className="space-y-6">
      {/* Barra de control y estado de actualización */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl border border-[var(--border)] bg-[var(--surface-1)]/60 text-xs font-mono text-[var(--text-3)]">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-[var(--text-2)]" />
          <span>
            Total: <strong className="text-[var(--text-1)]">{data.total_fases} fases</strong> · Fase
            activa: <strong className="text-[var(--text-1)]">{data.fase_activa}</strong>
          </span>
        </div>
        <div className="flex items-center gap-3">
          {ultimaActualizacion && (
            <span>
              Última actualización: <span className="text-[var(--text-2)]">{ultimaActualizacion}</span>
            </span>
          )}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={cargando}
              className="p-1.5 rounded hover:bg-[var(--surface-2)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer disabled:opacity-50"
              title="Refrescar fases"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${cargando ? "animate-spin" : ""}`} />
            </button>
          )}
        </div>
      </div>

      {/* 1. FASE ACTIVA DESTACADA ARRIBA */}
      {faseActiva && (
        <div className="space-y-2">
          <div className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--text-1)] flex items-center gap-2">
            <Target className="w-4 h-4 text-[var(--text-1)]" />
            <span>Fase Activa en Curso</span>
          </div>
          <FaseCard
            fase={faseActiva}
            desplegadaInicial={true}
            esActivaPrincipal={true}
            onSelectTarea={onSelectTarea}
          />
        </div>
      )}

      {/* 2. DEMÁS FASES DEL PLAN */}
      <div className="space-y-2">
        <div className="text-xs font-mono uppercase tracking-wider text-[var(--text-3)] flex items-center gap-2">
          <Layers className="w-4 h-4" />
          <span>Fases del Plan Maestro</span>
        </div>
        <div className="space-y-3">
          {demasFases.map((f) => (
            <FaseCard key={f.id} fase={f} onSelectTarea={onSelectTarea} />
          ))}
        </div>
      </div>

      {/* 3. CARRIL DE APOYO PERMANENTE (F10) */}
      {carrilApoyo && (
        <div className="space-y-2 pt-2 border-t border-[var(--border)]">
          <div className="text-xs font-mono uppercase tracking-wider text-[var(--text-3)] flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>Carril de Apoyo Permanente (Infraestructura y Operaciones)</span>
          </div>
          <FaseCard fase={carrilApoyo} onSelectTarea={onSelectTarea} />
        </div>
      )}
    </div>
  );
}
