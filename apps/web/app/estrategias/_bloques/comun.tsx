"use client";

/**
 * apps/web/app/estrategias/_bloques/comun.tsx
 *
 * Piezas compartidas entre la página maestra de Estrategias y sus 4 subpáginas
 * (generación · mejora · valoración · meta): tipos, helpers de formato y
 * componentes de presentación sobrios (docs/19_UI_STYLE_SPEC.md).
 *
 * REAL-ONLY: nada aquí inventa cifras. Los helpers solo dan forma a datos que
 * ya vinieron de la API o de la ruta de telemetría.
 */

import React from "react";
import type { CertifiedStrategy } from "@/lib/api";

/** Una estrategia certificada cuenta como "lista para FONDEO" solo si cumple
 * las CINCO condiciones de la definición sellada (criterio 1.1 + regla #26):
 * ruta FONDEO, estado aprobado, motor vigente, muestra OOS suficiente, PF OOS
 * suficiente y las 11 comprobaciones con evidencia real (no derivadas del
 * estado). engineVersion null (API caída) invalida cualquier fila. */
export function esValidaFondeo(cert: CertifiedStrategy, engineVersion: string | null): boolean {
  if (!engineVersion) return false;
  if (cert.route !== "FONDEO") return false;
  if (cert.status !== "APPROVED_CURRENT_ENGINE") return false;
  if (cert.engine_version !== engineVersion) return false;
  if (!(cert.total_trades >= 200)) return false;
  if (!(cert.oos_profit_factor >= 1.25)) return false;
  return contarGatesConEvidencia(cert) === 11;
}

/** Cuenta SOLO gates con evidencia real (`passed === true` dentro de
 * `certified.gates`), nunca un número derivado del status (regla REAL-ONLY b). */
export function contarGatesConEvidencia(cert: CertifiedStrategy): number {
  const gates = cert.gates;
  if (!gates || typeof gates !== "object") return 0;
  return Object.values(gates).filter((g) => g && g.passed === true).length;
}

/** Acorta un hash/id largo para tablas, conservando el valor completo en title. */
export function acortar(valor: string | null | undefined, largo = 10): string {
  if (!valor) return "sin evidencia";
  return valor.length > largo ? `${valor.slice(0, largo)}…` : valor;
}

/** "20260902T182722Z" (formato de las telemetrías en disco) -> "02-09-2026 18:27". */
export function formatoGeneradoUtc(valor: string | null | undefined): string {
  if (!valor) return "sin evidencia";
  const m = /^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z$/.exec(valor);
  if (!m) return valor;
  const [, y, mo, d, h, mi] = m;
  return `${d}-${mo}-${y} ${h}:${mi}`;
}

/** Fecha ISO estándar (created_at, certified_at_utc) -> "02-09-2026 18:27". */
export function formatoFechaIso(valor: string | null | undefined): string {
  if (!valor) return "sin evidencia";
  const d = new Date(valor);
  if (Number.isNaN(d.getTime())) return valor;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getUTCDate())}-${pad(d.getUTCMonth() + 1)}-${d.getUTCFullYear()} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

export function formatoPct(valor: number | null | undefined, decimales = 1): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return "sin evidencia";
  return `${valor >= 0 ? "+" : ""}${valor.toFixed(decimales)}%`;
}

/** Forma reducida que devuelve nuestra propia ruta interna de telemetría
 * (apps/web/app/estrategias/api-telemetria/route.ts). Duplicada a propósito
 * en el route handler: son dos ficheros compilados por separado y ambos deben
 * poder leerse sin depender el uno del otro en tiempo de ejecución. */
export interface CampanaTelemetria {
  track: string;
  symbol: string;
  timeframe: string;
  profile: string;
  generado_utc: string;
  engine_version: string;
  espacio_total: number;
  truncado: boolean;
  evaluadas: number;
  muertas_is: number;
  pasan_is: number;
  sin_ventaja_bruta: number;
  sin_ventaja_por_coste: number;
  pocas_operaciones: number;
  por_familia: Record<string, { total: number; sin_ventaja_bruta: number; sin_ventaja_por_coste: number; pocas_operaciones: number }>;
}

export interface RespuestaTelemetria {
  status: "OK" | "NO DATA";
  campanas: CampanaTelemetria[];
}

/** Una línea en llano describiendo la campaña más reciente, para la tarjeta
 * de M2 y para el estado vacío del bloque FONDEO. Nunca inventa: si no hay
 * campañas, dice que no hay evidencia. */
export function resumenUltimaCampana(campanas: CampanaTelemetria[]): string {
  if (campanas.length === 0) return "Sin evidencia de campañas en disco.";
  const c = campanas[0];
  return `${c.symbol} ${c.timeframe} (${c.profile}) · ${formatoGeneradoUtc(c.generado_utc)} · ${c.evaluadas} configuraciones evaluadas · ${c.pasan_is} pasan el primer filtro.`;
}

// ---------------------------------------------------------------------------
// Componentes de presentación
// ---------------------------------------------------------------------------

export function BotonCopiar({ texto, activo, onCopiar }: { texto: string; activo: boolean; onCopiar: (texto: string) => void }) {
  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onCopiar(texto);
      }}
      title={texto}
      style={{
        marginLeft: "4px",
        background: "none",
        border: "none",
        color: activo ? "var(--profit)" : "var(--text-3)",
        cursor: "pointer",
        fontSize: "10px",
        padding: 0,
      }}
    >
      {activo ? "copiado" : "copiar"}
    </button>
  );
}

/** Panel gris con título, para agrupar contenido dentro de una subpágina. */
export function Caja({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "4px", padding: "12px" }}>
      <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-2)", textTransform: "uppercase", letterSpacing: "0.02em" }}>{titulo}</span>
      <div style={{ fontSize: "13px", color: "var(--text-1)", lineHeight: 1.5 }}>{children}</div>
    </div>
  );
}

/** Cabecera común de las 4 subpáginas: título en llano + una frase. */
export function EncabezadoSubpagina({ titulo, tagline }: { titulo: string; tagline: string }) {
  return (
    <header style={{ display: "flex", flexDirection: "column", gap: "4px", borderBottom: "1px solid var(--border)", paddingBottom: "10px" }}>
      <h1 style={{ fontSize: "17px", fontWeight: 700, margin: 0, color: "var(--text-1)" }}>{titulo}</h1>
      <p style={{ fontSize: "13px", color: "var(--text-2)", margin: 0 }}>{tagline}</p>
    </header>
  );
}

/** Punto de estado (API / motor) reutilizado en cada página. */
export function PuntoEstado({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "12px", fontFamily: "monospace" }}>
      <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: ok ? "var(--profit)" : "var(--loss)" }} />
      <span style={{ color: ok ? "var(--text-2)" : "var(--loss)" }}>{label}</span>
    </span>
  );
}

export const cajaEstiloTabla: React.CSSProperties = { overflowX: "auto", border: "1px solid var(--border)", borderRadius: "4px", background: "var(--surface-1)" };
export const celdaCabecera: React.CSSProperties = { padding: "6px 8px", textAlign: "left", fontSize: "10.5px", textTransform: "uppercase", color: "var(--text-2)", background: "var(--surface-2)", borderBottom: "1px solid var(--border)" };
export const celda: React.CSSProperties = { padding: "6px 8px", fontSize: "12px", borderBottom: "1px solid var(--border)", color: "var(--text-1)" };
