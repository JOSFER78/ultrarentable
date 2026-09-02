"use client";

/**
 * apps/web/app/estrategias/valoracion/page.tsx — Módulo 3 (M3): Valoración
 * para Fondeo. Convierte una estrategia certificada en una decisión: ¿con
 * qué firma de fondeo, en qué horario, con qué tamaño y con qué probabilidad
 * real de aprobar el examen y no reventar la cuenta?
 */

import React, { useCallback, useEffect, useState } from "react";
import { getCertifiedStrategies, getDiscoveryStatus, type CertifiedStrategy } from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import { Caja, EncabezadoSubpagina, PuntoEstado, esValidaFondeo } from "../_bloques/comun";

export default function PaginaValoracion() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [certificadas, setCertificadas] = useState<CertifiedStrategy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [disc, certs] = await Promise.all([getDiscoveryStatus(), getCertifiedStrategies()]);
      setEngineVersion(disc.current_engine_version);
      setCertificadas(certs);
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

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-1)", padding: "16px", fontFamily: "ui-sans-serif, system-ui, sans-serif" }}>
      <div style={{ maxWidth: "1000px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "14px" }}>
        <EncabezadoSubpagina titulo="3. Valoración para Fondeo" tagline="El examen: comprueba si una estrategia certificada aprobaría las reglas exactas de una prop firm y con qué probabilidad sobrevive después." />
        <NavBloques activo="valoracion" />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
          <PuntoEstado ok={!error} label={error ? `Sin conexión: ${error}` : "API conectada"} />
          <span style={{ fontSize: "12px", color: "var(--text-3)" }}>Motor vigente: {engineVersion || "sin evidencia"}</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
          <Caja titulo="Qué hace">
            Reproduce las reglas exactas de cada firma de fondeo (límite de pérdida diaria, límite de pérdida total, días mínimos, tamaño máximo) sobre las operaciones reales de la estrategia, con la cuenta en tiempo real (no solo al cierre del día). De ahí saca: probabilidad de aprobar el examen, probabilidad de reventar la cuenta en 6 meses, mejor horario y tamaño recomendado.
          </Caja>
          <Caja titulo="Qué necesita">
            Al menos una estrategia certificada con motor vigente (necesita ≥1; hoy hay {validas.length}).
          </Caja>
          <Caja titulo="Objetivo sellado">
            <div style={{ display: "flex", flexDirection: "column", gap: "2px", fontFamily: "monospace", fontSize: "12px" }}>
              <span>Rendimiento mensual objetivo: <strong>≥ 20 % (mediana)</strong></span>
              <span>Probabilidad de reventar la cuenta en 6 meses: <strong>≤ 20 %</strong></span>
              <span>Duración del examen: <strong>3 a 8 días</strong></span>
            </div>
          </Caja>
          <Caja titulo="Estado hoy">
            {cargando
              ? "Cargando…"
              : validas.length === 0
                ? "Sin candidatas que valorar: no hay ninguna estrategia que cumpla hoy la definición de válida para FONDEO (ver /estrategias)."
                : `${validas.length} estrategia(s) lista(s) para pasar por el examen.`}
          </Caja>
        </div>

        <div style={{ fontSize: "11px", color: "var(--text-3)", borderTop: "1px solid var(--border)", paddingTop: "8px" }}>
          Ruta hermana en ULTRA (envolvente de balas, examen de convexidad): en construcción.
        </div>
      </div>
    </div>
  );
}
