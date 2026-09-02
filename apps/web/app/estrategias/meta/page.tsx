"use client";

/**
 * apps/web/app/estrategias/meta/page.tsx — Módulo 4 (M4): Metaestrategias.
 * Combina varias estrategias certificadas en una sola compuesta para bajar la
 * varianza del examen de fondeo (en fondeo, la varianza mata más que la
 * media baja).
 */

import React, { useCallback, useEffect, useState } from "react";
import { getCertifiedMetaStrategies, getCertifiedStrategies, getDiscoveryStatus, type CertifiedMetaStrategy, type CertifiedStrategy } from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import { Caja, EncabezadoSubpagina, PuntoEstado, esValidaFondeo } from "../_bloques/comun";

const ETIQUETA_ESTADO: Record<string, string> = {
  SUPERSEDED: "sustituida por una versión más nueva",
  ASSEMBLED_PENDING_PORTFOLIO_BACKTEST: "ensamblada, pendiente de examen",
  APPROVED_LEGACY: "aprobada con motor antiguo",
  REVALIDATION_REQUIRED: "necesita revalidarse",
};

export default function PaginaMeta() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [certificadas, setCertificadas] = useState<CertifiedStrategy[]>([]);
  const [metas, setMetas] = useState<CertifiedMetaStrategy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [disc, certs, metaList] = await Promise.all([getDiscoveryStatus(), getCertifiedStrategies(), getCertifiedMetaStrategies()]);
      setEngineVersion(disc.current_engine_version);
      setCertificadas(certs);
      setMetas(metaList);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al consultar la API.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const validas = certificadas.filter((c) => esValidaFondeo(c, engineVersion));
  const porEstado = new Map<string, number>();
  for (const m of metas) porEstado.set(m.status, (porEstado.get(m.status) ?? 0) + 1);
  const aprobadasActuales = metas.filter((m) => m.status === "APPROVED_CURRENT_ENGINE" && Boolean(engineVersion) && m.engine_version === engineVersion).length;

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-1)", padding: "16px", fontFamily: "ui-sans-serif, system-ui, sans-serif" }}>
      <div style={{ maxWidth: "1000px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "14px" }}>
        <EncabezadoSubpagina titulo="4. Meta" tagline="Junta varias estrategias certificadas en una sola compuesta para bajar la varianza del examen y la probabilidad de reventar la cuenta." />
        <NavBloques activo="meta" />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
          <PuntoEstado ok={!error} label={error ? `Sin conexión: ${error}` : "API conectada"} />
          <span style={{ fontSize: "12px", color: "var(--text-3)" }}>Motor vigente: {engineVersion || "sin evidencia"}</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
          <Caja titulo="Qué hace">
            Reparte capital entre varias estrategias certificadas (por ejemplo, por paridad de riesgo) y examina la combinación como si fuera una sola estrategia más. Si la combinación no mejora a su mejor componente por separado, se descarta: no se usa solo por diversificar.
          </Caja>
          <Caja titulo="Qué necesita">
            Al menos 2 estrategias válidas para FONDEO con solape de fechas suficiente para calcular su correlación real (hoy hay {validas.length}).
          </Caja>
          <Caja titulo="Estado hoy">
            {cargando
              ? "Cargando…"
              : aprobadasActuales > 0
                ? `${aprobadasActuales} metaestrategia(s) aprobada(s) con el motor vigente.`
                : "Sin metaestrategias aprobadas con el motor vigente. No hay evidencia de una combinación lista."}
          </Caja>
          <Caja titulo="Qué falta">
            {validas.length < 2
              ? `Certificar ${2 - validas.length} estrategia(s) más para FONDEO antes de poder ensamblar nada.`
              : "Construir services/meta/ (el actual está retirado por usar cifras de motor antiguo) y ejecutar el examen sobre la combinación."}
          </Caja>
        </div>

        <section style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "12px", color: "var(--text-2)", fontWeight: 600 }}>Composiciones antiguas en la base (no cuentan como válidas)</span>
          {metas.length === 0 && !cargando && (
            <div style={{ padding: "10px", border: "1px solid var(--border)", borderRadius: "4px", background: "var(--surface-1)", color: "var(--text-3)", fontSize: "13px" }}>
              Sin evidencia de composiciones previas.
            </div>
          )}
          {metas.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {Array.from(porEstado.entries()).map(([estado, n]) => (
                <div key={estado} style={{ display: "flex", justifyContent: "space-between", padding: "6px 10px", border: "1px solid var(--border)", borderRadius: "4px", background: "var(--surface-1)", fontSize: "12.5px" }}>
                  <span style={{ color: "var(--text-2)" }}>{ETIQUETA_ESTADO[estado] || estado}</span>
                  <strong style={{ color: "var(--text-3)", fontFamily: "monospace" }}>{n}</strong>
                </div>
              ))}
            </div>
          )}
        </section>

        <div style={{ fontSize: "11px", color: "var(--text-3)", borderTop: "1px solid var(--border)", paddingTop: "8px" }}>
          Ruta hermana en ULTRA (meta-router): en construcción.
        </div>
      </div>
    </div>
  );
}
