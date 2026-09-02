"use client";

/**
 * apps/web/app/estrategias/mejora/page.tsx — Módulo 2 (M2): Mejora.
 * El bucle que coge las crudas de Generación, las prueba de verdad y, si no
 * llegan al nivel exigido, no las fuerza: las archiva con el motivo exacto.
 * Esta página muestra las últimas campañas leídas de
 * apps/web/app/estrategias/api-telemetria/route.ts (disco real, sin caché).
 */

import React, { useCallback, useEffect, useState } from "react";
import { getDiscoveryStatus } from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import { Caja, EncabezadoSubpagina, PuntoEstado, cajaEstiloTabla, celda, celdaCabecera, formatoGeneradoUtc, type CampanaTelemetria, type RespuestaTelemetria } from "../_bloques/comun";

function resumenFamilias(por_familia: CampanaTelemetria["por_familia"]): string {
  const entradas = Object.entries(por_familia).sort((a, b) => b[1].total - a[1].total);
  if (entradas.length === 0) return "sin evidencia";
  const MOSTRAR = 3;
  const texto = entradas.slice(0, MOSTRAR).map(([fam, v]) => `${fam} (${v.total})`).join(" · ");
  return entradas.length > MOSTRAR ? `${texto} +${entradas.length - MOSTRAR} más` : texto;
}

export default function PaginaMejora() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [campanas, setCampanas] = useState<CampanaTelemetria[]>([]);
  const [estadoTelemetria, setEstadoTelemetria] = useState<"OK" | "NO DATA" | "CARGANDO">("CARGANDO");
  const [error, setError] = useState<string | null>(null);
  const [filaAbierta, setFilaAbierta] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setError(null);
    try {
      const disc = await getDiscoveryStatus().catch(() => null);
      setEngineVersion(disc?.current_engine_version ?? null);
      const r = await fetch("/estrategias/api-telemetria", { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = (await r.json()) as RespuestaTelemetria;
      setCampanas(data.campanas ?? []);
      setEstadoTelemetria(data.status ?? "NO DATA");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al leer la telemetría.");
      setEstadoTelemetria("NO DATA");
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-1)", padding: "16px", fontFamily: "ui-sans-serif, system-ui, sans-serif" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "14px" }}>
        <EncabezadoSubpagina titulo="2. Mejora" tagline="El bucle que revisa cada estrategia cruda, mide si tiene ventaja real y, si no la tiene, la descarta con el motivo exacto. Nunca relaja el listón para que algo pase." />
        <NavBloques activo="mejora" />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
          <PuntoEstado ok={!error} label={error ? `Sin conexión: ${error}` : "API conectada"} />
          <span style={{ fontSize: "12px", color: "var(--text-3)" }}>Motor vigente: {engineVersion || "sin evidencia"}</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
          <Caja titulo="Qué hace">
            Prueba cada configuración cruda con un backtest honesto y comprueba si tiene ventaja de verdad, antes y después de restar comisiones y deslizamiento. Lo que no la tiene se descarta ahí mismo; lo que sí, sigue a la siguiente fase de prueba (validación y fuera de muestra).
          </Caja>
          <Caja titulo="Qué necesita">
            Configuraciones nuevas de Generación o candidatas casi-válidas de campañas anteriores, y un presupuesto de intentos por estrategia (para no probar infinitas variantes de la misma idea).
          </Caja>
          <Caja titulo="Estado hoy">
            La búsqueda actual prueba cada configuración en tres cribas seguidas (entrenamiento, validación y fuera de muestra), siempre con costes descontados. En las últimas campañas ninguna configuración ha superado la primera criba. El ciclo de mejora iterativa está definido como contrato en el código, pero las campañas de hoy son pasadas únicas sobre la rejilla de arquetipos.
          </Caja>
          <Caja titulo="Qué falta">
            Corregir la fricción del motor (hoy cobra a los micros la comisión del contrato completo; motor 5.19.0 en curso) y repetir la campaña; después, cerrar el ciclo de mejora iterativa (hipótesis → experimento → nueva prueba) sobre las configuraciones que se quedan cerca del listón.
          </Caja>
        </div>

        <section style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "12px", color: "var(--text-2)", fontWeight: 600 }}>Últimas campañas</span>
          {estadoTelemetria === "NO DATA" && campanas.length === 0 && (
            <div style={{ padding: "10px", border: "1px solid var(--border)", borderRadius: "4px", background: "var(--surface-1)", color: "var(--text-3)", fontSize: "13px" }}>
              Sin evidencia de campañas en disco (orchestration/results/telemetria).
            </div>
          )}
          {campanas.length > 0 && (
            <div style={cajaEstiloTabla}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={celdaCabecera}>Mercado</th>
                    <th style={celdaCabecera}>Temporalidad</th>
                    <th style={celdaCabecera}>Perfil</th>
                    <th style={celdaCabecera}>Fecha</th>
                    <th style={{ ...celdaCabecera, textAlign: "right" }}>Probadas</th>
                    <th style={{ ...celdaCabecera, textAlign: "right" }}>Pasan 1ª criba</th>
                    <th style={{ ...celdaCabecera, textAlign: "right" }}>Sin ventaja (bruto)</th>
                    <th style={{ ...celdaCabecera, textAlign: "right" }}>Ventaja que se come el coste</th>
                    <th style={celdaCabecera}>Familias</th>
                  </tr>
                </thead>
                <tbody>
                  {campanas.map((c) => {
                    const clave = `${c.symbol}_${c.timeframe}_${c.profile}_${c.generado_utc}`;
                    const abierta = filaAbierta === clave;
                    return (
                      <React.Fragment key={clave}>
                        <tr onClick={() => setFilaAbierta(abierta ? null : clave)} style={{ cursor: "pointer" }}>
                          <td style={celda}><strong>{c.symbol}</strong></td>
                          <td style={{ ...celda, color: "var(--text-2)" }}>{c.timeframe}</td>
                          <td style={{ ...celda, color: "var(--text-2)" }}>{c.profile}</td>
                          <td style={{ ...celda, color: "var(--text-3)", fontFamily: "monospace" }}>{formatoGeneradoUtc(c.generado_utc)}</td>
                          <td style={{ ...celda, textAlign: "right", fontFamily: "monospace" }}>{c.evaluadas}{c.truncado ? " *" : ""}</td>
                          <td style={{ ...celda, textAlign: "right", fontFamily: "monospace", color: c.pasan_is > 0 ? "var(--profit)" : "var(--text-3)" }}>{c.pasan_is}</td>
                          <td style={{ ...celda, textAlign: "right", fontFamily: "monospace" }}>{c.sin_ventaja_bruta}</td>
                          <td style={{ ...celda, textAlign: "right", fontFamily: "monospace" }}>{c.sin_ventaja_por_coste}</td>
                          <td style={{ ...celda, color: "var(--text-2)" }}>{resumenFamilias(c.por_familia)}</td>
                        </tr>
                        {abierta && (
                          <tr>
                            <td colSpan={9} style={{ ...celda, background: "var(--surface-2)" }}>
                              <div style={{ display: "flex", flexDirection: "column", gap: "3px", fontSize: "11.5px" }}>
                                <span style={{ color: "var(--text-3)" }}>Espacio total de configuraciones: {c.espacio_total}{c.truncado ? " (búsqueda truncada, no se evaluaron todas)" : ""} · Motor: {c.engine_version || "sin evidencia"}</span>
                                {Object.entries(c.por_familia).sort((a, b) => b[1].total - a[1].total).map(([fam, v]) => (
                                  <span key={fam}>
                                    <strong>{fam}</strong>: {v.total} probadas · {v.sin_ventaja_bruta} sin ventaja antes de costes · {v.sin_ventaja_por_coste} con ventaja que se come el coste · {v.pocas_operaciones} con muy pocas operaciones
                                  </span>
                                ))}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <span style={{ fontSize: "10.5px", color: "var(--text-3)" }}>* Búsqueda truncada: no se evaluaron todas las configuraciones posibles del espacio, solo una muestra.</span>
        </section>
      </div>
    </div>
  );
}
