"use client";

import React, { useState } from "react";
import {
  FileText,
  CheckCircle2,
  XCircle,
  Database,
  ExternalLink,
  ShieldCheck,
  Lock,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { WebRutaEspec } from "@/app/api/plan/route";

interface EspecificacionWebVisualProps {
  rutas: WebRutaEspec[];
  onOpenDoc?: (docName: string, title: string) => void;
}

export default function EspecificacionWebVisual({ rutas, onOpenDoc }: EspecificacionWebVisualProps) {
  const [filter, setFilter] = useState<string>("TODAS");
  const [expandedRoutes, setExpandedRoutes] = useState<Set<string>>(new Set(["/", "/estrategias"]));

  const toggleExpand = (ruta: string) => {
    setExpandedRoutes((prev) => {
      const next = new Set(prev);
      if (next.has(ruta)) next.delete(ruta);
      else next.add(ruta);
      return next;
    });
  };

  const filtered = rutas.filter((r) => {
    if (filter === "TODAS") return true;
    return r.estado === filter;
  });

  const getStatusBadge = (estado: WebRutaEspec["estado"]) => {
    switch (estado) {
      case "IMPLEMENTADA":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)]">
            <CheckCircle2 className="w-3 h-3" />
            IMPLEMENTADA
          </span>
        );
      case "PARCIAL":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-2)]">
            PARCIAL
          </span>
        );
      case "APARCADA":
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)]">
            <Lock className="w-3 h-3" />
            APARCADA
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)]">
            EN REVISIÓN
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 font-sans text-xs">
      {/* Cabecera del Catálogo */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[var(--profit)]" />
            <h2 className="text-sm sm:text-base font-bold text-[var(--text-1)] tracking-tight">
              Especificación Visual de la Web — Contrato Página a Página
            </h2>
          </div>
          <p className="text-[12px] text-[var(--text-2)] mt-0.5 font-sans">
            La web solo enseña lo que funciona. Cada página responde a una pregunta concreta con datos físicos reales.
          </p>
        </div>

        <div className="flex items-center gap-1.5 font-mono text-xs shrink-0">
          {(["TODAS", "IMPLEMENTADA", "PARCIAL"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setFilter(st)}
              className={`px-2.5 py-1 rounded-md border transition cursor-pointer ${
                filter === st
                  ? "bg-[var(--surface-2)] border-[var(--profit)] text-[var(--text-1)] font-bold"
                  : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-2)]"
              }`}
            >
              {st}
            </button>
          ))}
          {onOpenDoc && (
            <button
              onClick={() => onOpenDoc("especificacion_web", "Especificación de la Web")}
              className="px-2 py-1 rounded-md border border-[var(--border)] bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer flex items-center gap-1"
              title="Ver archivo ESPECIFICACION_WEB.md en disco"
            >
              <FileText className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Ver MD</span>
            </button>
          )}
        </div>
      </div>

      {/* Lista de Tarjetas de Rutas */}
      <div className="space-y-3">
        {filtered.map((r) => {
          const isExpanded = expandedRoutes.has(r.ruta);
          return (
            <div
              key={r.ruta}
              className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 hover:border-[var(--border-strong)] transition"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5 flex-wrap">
                  <code className="text-xs font-mono font-bold text-[var(--profit)] bg-[var(--surface-2)] px-2 py-0.5 rounded border border-[var(--border)]">
                    {r.ruta}
                  </code>
                  <span className="text-sm font-bold text-[var(--text-1)] font-sans">{r.nombre}</span>
                  <span className="text-[11px] font-mono text-[var(--text-3)]">({r.modulo})</span>
                </div>
                <div className="flex items-center gap-2">
                  {getStatusBadge(r.estado)}
                  <button
                    onClick={() => toggleExpand(r.ruta)}
                    className="p-1 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-1)] transition cursor-pointer"
                    title={isExpanded ? "Plegar contrato" : "Desplegar contrato"}
                  >
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <p className="text-[12px] text-[var(--text-2)] font-sans leading-relaxed">
                <strong>Propósito:</strong> {r.proposito}
              </p>

              {isExpanded && (
                <div className="space-y-3 pt-3 border-t border-[var(--border)] font-mono text-[11px]">
                  {/* Fuente de Datos */}
                  <div className="flex items-start gap-2 text-[var(--text-3)]">
                    <Database className="w-3.5 h-3.5 text-[var(--profit)] shrink-0 mt-0.5" />
                    <span>
                      <strong className="text-[var(--text-2)]">Fuente Real:</strong> {r.fuente_datos}
                    </span>
                  </div>

                  {/* Dos Columnas: Qué Muestra vs Qué NUNCA Muestra */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                    <div className="bg-[var(--surface-2)] p-3 rounded border border-[var(--border)] space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[var(--profit)] font-bold text-[10px] uppercase">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Qué Muestra</span>
                      </div>
                      <ul className="space-y-1 text-[var(--text-1)]">
                        {r.muestra.map((item, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-[var(--text-3)]">›</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-[var(--surface-2)] p-3 rounded border border-[var(--border)] space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[var(--loss)] font-bold text-[10px] uppercase">
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Qué NUNCA Muestra (Zero-Mocks)</span>
                      </div>
                      <ul className="space-y-1 text-[var(--text-2)]">
                        {r.nunca_muestra.map((item, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-[var(--loss)]">✕</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Sección de Conceptos Clave: Autenticación Firebase Real */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono">
        <div className="flex items-center gap-2 border-b border-[var(--border)] pb-2">
          <ShieldCheck className="w-4 h-4 text-[var(--profit)]" />
          <h3 className="text-xs font-bold text-[var(--text-1)] uppercase tracking-wide">
            Concepto Arquitectónico: Autenticación Firebase Real (02 ULTRAFONDEO)
          </h3>
        </div>
        <p className="text-[12px] text-[var(--text-2)] font-sans leading-relaxed">
          La web opera bajo un **único proyecto de Firebase unificado** (<code className="text-[var(--text-1)]">traderbot-josfer</code>, #358873317228). Queda terminantemente prohibido usar datos de usuario pre-rellenados o superadmins simulados:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-[11px]">
          <div className="bg-[var(--surface-2)] p-2.5 rounded border border-[var(--border)]">
            <div className="text-[var(--profit)] font-bold">Google Auth Real</div>
            <div className="text-[var(--text-3)] mt-1 font-sans">Login directo con OAuth en dominios autorizados (localhost, VPS).</div>
          </div>
          <div className="bg-[var(--surface-2)] p-2.5 rounded border border-[var(--border)]">
            <div className="text-[var(--profit)] font-bold">RTDB con Reglas Estrictas</div>
            <div className="text-[var(--text-3)] mt-1 font-sans">Cada usuario lee y escribe exclusivamente su propia ficha; el superadmin autoriza.</div>
          </div>
          <div className="bg-[var(--surface-2)] p-2.5 rounded border border-[var(--border)]">
            <div className="text-[var(--profit)] font-bold">Superadmin por Email</div>
            <div className="text-[var(--text-3)] mt-1 font-sans">josferestudio@gmail.com como único administrador verificado.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
