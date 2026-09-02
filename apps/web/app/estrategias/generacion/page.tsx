"use client";

/**
 * apps/web/app/estrategias/generacion/page.tsx — Módulo 1 (M1): Generación.
 * StrategyQuant X fabrica estrategias en bruto; aquí se ve si está conectado,
 * cuántas ha entregado ya y las últimas extracciones. Los controles técnicos
 * (proyecto/databank/extraer/source/bind-dataset) viven plegados abajo.
 */

import React, { useCallback, useEffect, useState } from "react";
import { getDiscoveryStatus, getStrategyLabOverview, getStrategyLabSQXStatus, getStrategyLabStrategies, type StrategyLabOverview, type StrategyLabRecord } from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import { Caja, EncabezadoSubpagina, PuntoEstado, cajaEstiloTabla, celda, celdaCabecera, formatoFechaIso } from "../_bloques/comun";
import SQXToolsPanel from "../SQXToolsPanel";

interface SqxResultado {
  status?: string;
  base_url?: string;
  projects?: string[];
}

export default function PaginaGeneracion() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [sqxOnline, setSqxOnline] = useState<boolean | null>(null);
  const [sqxDetalle, setSqxDetalle] = useState("comprobando…");
  const [proyectos, setProyectos] = useState<string[]>([]);
  const [overview, setOverview] = useState<StrategyLabOverview | null>(null);
  const [extracciones, setExtracciones] = useState<StrategyLabRecord[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [disc, ov, sqx, ext] = await Promise.all([
        getDiscoveryStatus().catch(() => null),
        getStrategyLabOverview().catch(() => null),
        getStrategyLabSQXStatus().catch(() => null),
        getStrategyLabStrategies(5).catch(() => null),
      ]);
      setEngineVersion(disc?.current_engine_version ?? null);
      setOverview(ov);
      setExtracciones(ext?.strategies ?? []);

      const resultado = sqx?.result as SqxResultado | undefined;
      const online = sqx?.status === "SUCCESS" && resultado?.status === "ONLINE";
      setSqxOnline(Boolean(online));
      setSqxDetalle(online ? (resultado?.base_url || "conectado") : sqx?.error || "no conectado");
      setProyectos(Array.isArray(resultado?.projects) ? (resultado!.projects as string[]) : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al consultar la API.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const extraidas = overview?.pipeline?.extracted;
  const verificadas = overview?.pipeline?.structurally_verified;
  const pendientesVerificar = typeof extraidas === "number" && typeof verificadas === "number" ? Math.max(0, extraidas - verificadas) : null;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-1)", padding: "16px", fontFamily: "ui-sans-serif, system-ui, sans-serif" }}>
      <div style={{ maxWidth: "1000px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "14px" }}>
        <EncabezadoSubpagina titulo="1. Generación" tagline="StrategyQuant X (SQX) fabrica ideas de estrategia en bruto. Este módulo las extrae, les da identidad propia y las entrega al siguiente paso." />
        <NavBloques activo="generacion" />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
          <PuntoEstado ok={!error} label={error ? `API sin conexión: ${error}` : "API conectada"} />
          <span style={{ fontSize: "12px", color: "var(--text-3)" }}>Motor vigente: {engineVersion || "sin evidencia"}</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
          <Caja titulo="Qué hace">
            SQX genera automáticamente miles de combinaciones de reglas de entrada y salida sobre un mercado y una temporalidad. Nosotros no las escribimos a mano: las extraemos, comprobamos su estructura y las metemos en el catálogo con su procedencia (proyecto, banco de datos, fecha).
          </Caja>
          <Caja titulo="Qué necesita">
            SQX corriendo (localmente) con al menos un proyecto que tenga un banco de estrategias (&quot;databank&quot;) generado. La extracción guarda cada estrategia con su huella (hash) para que nunca se pierda de dónde salió.
          </Caja>
          <Caja titulo="Estado hoy">
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              <PuntoEstado ok={sqxOnline === true} label={sqxOnline === null ? "comprobando…" : sqxOnline ? `SQX conectado (${sqxDetalle})` : `SQX sin conectar (${sqxDetalle})`} />
              <span>Proyectos vistos por SQX: {proyectos.length > 0 ? proyectos.join(", ") : "sin evidencia"}</span>
              <span>Estrategias crudas extraídas hasta hoy: <strong>{extraidas ?? "sin evidencia"}</strong></span>
            </div>
          </Caja>
          <Caja titulo="Qué falta">
            {pendientesVerificar === null
              ? "Sin evidencia de cuántas faltan por verificar estructuralmente."
              : pendientesVerificar === 0
                ? "Todas las extraídas ya pasaron la comprobación estructural (el siguiente paso, Mejora, decide si sobreviven al backtest)."
                : `${pendientesVerificar} extraídas todavía no han pasado la comprobación estructural (de ${extraidas} extraídas, ${verificadas} verificadas).`}
          </Caja>
        </div>

        <section style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "12px", color: "var(--text-2)", fontWeight: 600 }}>Últimas 5 extracciones</span>
          <div style={cajaEstiloTabla}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={celdaCabecera}>Estrategia</th>
                  <th style={celdaCabecera}>Proyecto</th>
                  <th style={celdaCabecera}>Banco de datos</th>
                  <th style={celdaCabecera}>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {cargando && extracciones.length === 0 && (
                  <tr><td colSpan={4} style={{ ...celda, textAlign: "center", color: "var(--text-3)" }}>Cargando…</td></tr>
                )}
                {!cargando && extracciones.length === 0 && (
                  <tr><td colSpan={4} style={{ ...celda, textAlign: "center", color: "var(--text-3)" }}>Sin evidencia de extracciones en disco.</td></tr>
                )}
                {extracciones.map((e) => (
                  <tr key={e.strategy_id}>
                    <td style={celda}>{e.name || e.strategy_id}</td>
                    <td style={{ ...celda, color: "var(--text-2)" }}>{e.source_project || "sin evidencia"}</td>
                    <td style={{ ...celda, color: "var(--text-2)" }}>{e.source_databank || "sin evidencia"}</td>
                    <td style={{ ...celda, color: "var(--text-3)" }}>{formatoFechaIso(e.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <details style={{ border: "1px solid var(--border)", borderRadius: "4px", background: "var(--surface-1)" }}>
          <summary style={{ padding: "8px 12px", fontSize: "12px", color: "var(--text-2)", cursor: "pointer" }}>Herramientas técnicas (uso interno)</summary>
          <div style={{ padding: "0 12px 12px 12px" }}>
            <SQXToolsPanel onExtraccion={() => void cargar()} />
          </div>
        </details>
      </div>
    </div>
  );
}
