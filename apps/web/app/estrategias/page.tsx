"use client";

/**
 * apps/web/app/estrategias/page.tsx — Página maestra de Estrategias.
 *
 * Mandato de Emilio (2026-09-02): "el usuario no quiere ver las estrategias
 * fallidas, solo quiere ver las estrategias que ya funcionan y todos los
 * datos para poder usarlas y llevarlas al proceso de ejecución en el trading
 * desk de FONDEO". Esta página muestra SOLO lo que cumple la definición
 * sellada de "válida" (criterio 1.1 + regla #26); todo lo demás queda un
 * clic más allá, en /candidatos, para uso interno.
 *
 * REAL-ONLY: cada cifra sale de la API o de la ruta de telemetría en disco;
 * nada hardcodeado. Estilo: docs/19_UI_STYLE_SPEC.md (monocromo; el color
 * solo para dinero o estado crítico).
 */

import React, { useCallback, useEffect, useState } from "react";
import {
  getCandidatosCanonicos,
  getCertifiedMetaStrategies,
  getCertifiedStrategies,
  getDiscoveryStatus,
  getStrategyLabOverview,
  getStrategyLabSQXStatus,
  type CandidatoCanonico,
  type CertifiedMetaStrategy,
  type CertifiedStrategy,
} from "@/lib/api";
import {
  BotonCopiar,
  acortar,
  contarGatesConEvidencia,
  esValidaFondeo,
  formatoPct,
  resumenUltimaCampana,
  type CampanaTelemetria,
  type RespuestaTelemetria,
} from "./_bloques/comun";

interface SqxResultado {
  status?: string;
  projects?: string[];
}

interface TarjetaModulo {
  href: string;
  numero: string;
  titulo: string;
  descripcion: string;
  estado: string;
  ok: boolean | null;
}

export default function PaginaEstrategias() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [candidatos, setCandidatos] = useState<CandidatoCanonico[]>([]);
  const [certificadas, setCertificadas] = useState<CertifiedStrategy[]>([]);
  const [metas, setMetas] = useState<CertifiedMetaStrategy[]>([]);
  const [extraidas, setExtraidas] = useState<number | null>(null);
  const [sqxOnline, setSqxOnline] = useState<boolean | null>(null);
  const [campanas, setCampanas] = useState<CampanaTelemetria[]>([]);
  const [cargando, setCargando] = useState(true);
  const [copiadoId, setCopiadoId] = useState<string | null>(null);

  const copiar = useCallback((texto: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(texto);
      setCopiadoId(texto);
      setTimeout(() => setCopiadoId(null), 1500);
    }
  }, []);

  const cargar = useCallback(async () => {
    setCargando(true);
    setApiError(null);
    try {
      const [disc, cands, certs, metaList, overview, sqx, telemetria] = await Promise.all([
        getDiscoveryStatus(),
        getCandidatosCanonicos(1000).catch(() => []),
        getCertifiedStrategies().catch(() => []),
        getCertifiedMetaStrategies().catch(() => []),
        getStrategyLabOverview().catch(() => null),
        getStrategyLabSQXStatus().catch(() => null),
        fetch("/estrategias/api-telemetria", { cache: "no-store" }).then((r) => (r.ok ? (r.json() as Promise<RespuestaTelemetria>) : null)).catch(() => null),
      ]);
      setEngineVersion(disc.current_engine_version);
      setCandidatos(cands);
      setCertificadas(certs);
      setMetas(metaList);
      setExtraidas(overview?.pipeline?.extracted ?? null);
      const resultado = sqx?.result as SqxResultado | undefined;
      setSqxOnline(sqx?.status === "SUCCESS" && resultado?.status === "ONLINE");
      setCampanas(telemetria?.campanas ?? []);
    } catch (e) {
      setApiError(e instanceof Error ? e.message : "No se pudo conectar con la API.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const apiOk = !apiError && Boolean(engineVersion);
  const validas = certificadas.filter((c) => esValidaFondeo(c, engineVersion));

  // Certificaciones que existen pero NO cumplen la definición sellada — el
  // porqué exacto, calculado en cliente, nunca supuesto (regla REAL-ONLY).
  const antiguas = certificadas.filter((c) => c.status === "APPROVED_CURRENT_ENGINE" && !esValidaFondeo(c, engineVersion));
  const rutaIncorrecta = antiguas.filter((c) => c.route !== "FONDEO").length;
  const motorDesactualizado = antiguas.filter((c) => c.engine_version !== engineVersion).length;
  const antiguasPocasOperaciones = antiguas.filter((c) => !(c.total_trades >= 200));
  const pocasOperaciones = antiguasPocasOperaciones.length;
  const pfBajo = antiguas.filter((c) => !(c.oos_profit_factor >= 1.25)).length;
  const gatesIncompletos = antiguas.filter((c) => contarGatesConEvidencia(c) !== 11).length;
  const tradesAntiguas = antiguasPocasOperaciones.map((c) => c.total_trades).filter((n) => Number.isFinite(n));
  const rangoTrades = tradesAntiguas.length > 0 ? `${Math.min(...tradesAntiguas)}–${Math.max(...tradesAntiguas)}` : null;

  const totalCandidatos = candidatos.length;
  const noPasaron = Math.max(0, totalCandidatos - validas.length);

  const tarjetas: TarjetaModulo[] = [
    {
      href: "/estrategias/generacion",
      numero: "1",
      titulo: "Generación",
      descripcion: "StrategyQuant X fabrica ideas de estrategia en bruto.",
      estado: sqxOnline === null ? "comprobando…" : sqxOnline ? `Conectado · ${extraidas ?? "sin evidencia"} extraídas` : "Sin conectar",
      ok: sqxOnline,
    },
    {
      href: "/estrategias/mejora",
      numero: "2",
      titulo: "Mejora",
      descripcion: "Un bucle prueba cada idea y descarta lo que no tiene ventaja real.",
      estado: campanas.length > 0 ? resumenUltimaCampana(campanas) : "En construcción · sin campañas recientes",
      ok: null,
    },
    {
      href: "/estrategias/valoracion",
      numero: "3",
      titulo: "Valoración para Fondeo",
      descripcion: "Examina si una estrategia certificada aprobaría el examen de una prop firm.",
      estado: `${validas.length} lista(s) · necesita ≥ 1`,
      ok: validas.length > 0,
    },
    {
      href: "/estrategias/meta",
      numero: "4",
      titulo: "Meta",
      descripcion: "Combina varias estrategias certificadas para bajar el riesgo conjunto.",
      estado: `${validas.length} lista(s) · necesita ≥ 2`,
      ok: validas.length >= 2,
    },
  ];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", color: "var(--text-1)", padding: "16px", fontFamily: "ui-sans-serif, system-ui, sans-serif" }}>
      <div style={{ maxWidth: "1100px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "20px" }}>

        {/* CABECERA */}
        <header style={{ display: "flex", flexDirection: "column", gap: "6px", borderBottom: "1px solid var(--border)", paddingBottom: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "8px" }}>
            <div>
              <h1 style={{ fontSize: "19px", fontWeight: 700, margin: 0 }}>Estrategias</h1>
              <p style={{ fontSize: "13px", color: "var(--text-2)", margin: "4px 0 0 0" }}>
                Las estrategias que ya han demostrado ventaja real y están listas para llevar a cuentas de fondeo.
              </p>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: "12px", fontFamily: "monospace" }}>
              <span style={{ display: "flex", alignItems: "center", gap: "5px" }}>
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: apiOk ? "var(--profit)" : "var(--loss)" }} />
                <span style={{ color: apiOk ? "var(--text-2)" : "var(--loss)" }}>{apiOk ? "API conectada" : "API sin conexión"}</span>
              </span>
              <span style={{ color: "var(--text-3)" }}>Motor: {engineVersion || "sin evidencia"}</span>
              <button onClick={() => void cargar()} disabled={cargando} style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--text-1)", padding: "3px 10px", borderRadius: "3px", fontSize: "11px", cursor: "pointer" }}>
                {cargando ? "…" : "Actualizar"}
              </button>
            </div>
          </div>
          {apiError && (
            <div style={{ padding: "6px 10px", background: "var(--loss-dim)", border: "1px solid var(--loss)", color: "var(--loss)", fontSize: "12px", borderRadius: "3px" }}>
              No se pudo conectar con la API: {apiError}
            </div>
          )}
        </header>

        {/* BLOQUE 1: LISTAS PARA FONDEO */}
        <section style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <h2 style={{ fontSize: "14px", fontWeight: 700, margin: 0, color: "var(--text-1)" }}>Listas para FONDEO</h2>

          {validas.length === 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", padding: "16px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "6px" }}>
              <p style={{ margin: 0, fontSize: "14px", color: "var(--text-1)" }}>
                Hoy no hay ninguna estrategia lista para llevar a una cuenta de fondeo.
              </p>
              <p style={{ margin: 0, fontSize: "12.5px", color: "var(--text-2)", lineHeight: 1.6 }}>
                Para contar como <strong>válida</strong>, una estrategia tiene que cumplir las cinco condiciones a la
                vez: operar la ruta FONDEO, al menos <strong>200 operaciones</strong> comprobadas fuera de la muestra
                de entrenamiento, un factor de beneficio de al menos <strong>1,25</strong> en esas operaciones, pasar
                las <strong>11 comprobaciones</strong> con evidencia real (no solo la etiqueta), y estar certificada
                con el motor de cálculo vigente ({engineVersion || "sin evidencia"}).
              </p>
              {antiguas.length > 0 && (
                <p style={{ margin: 0, fontSize: "12.5px", color: "var(--text-2)", lineHeight: 1.6 }}>
                  Hay <strong>{antiguas.length}</strong> certificación(es) antigua(s) en la base que no cuentan: {" "}
                  {rutaIncorrecta > 0 && <>{rutaIncorrecta} no operan la ruta FONDEO · </>}
                  {motorDesactualizado > 0 && <>{motorDesactualizado} usan un motor distinto al vigente · </>}
                  {pocasOperaciones > 0 && <>{pocasOperaciones} tienen menos de 200 operaciones fuera de muestra{rangoTrades ? ` (entre ${rangoTrades})` : ""} · </>}
                  {pfBajo > 0 && <>{pfBajo} tienen un factor de beneficio por debajo de 1,25 · </>}
                  {gatesIncompletos > 0 && <>{gatesIncompletos} no tienen las 11 comprobaciones con evidencia</>}
                </p>
              )}
              <p style={{ margin: 0, fontSize: "12.5px", color: "var(--text-3)" }}>
                Qué se está haciendo ahora mismo: {resumenUltimaCampana(campanas)}
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto", border: "1px solid var(--border)", borderRadius: "6px", background: "var(--surface-1)" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
                <thead>
                  <tr style={{ background: "var(--surface-2)", borderBottom: "1px solid var(--border)" }}>
                    {["Nombre", "Mercado / TF", "PF OOS", "Ops OOS", "Caída máx.", "Rend. mensual", "Rend. anual", "Ledger", "Gates", "Motor", "Identificador", "Dataset", ""].map((h) => (
                      <th key={h} style={{ padding: "7px 8px", textAlign: h === "PF OOS" || h === "Ops OOS" || h === "Caída máx." || h === "Rend. mensual" || h === "Rend. anual" ? "right" : "left", fontSize: "10.5px", textTransform: "uppercase", color: "var(--text-2)" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {validas.map((c) => {
                    const gates = contarGatesConEvidencia(c);
                    return (
                      <tr key={c.strategy_id} style={{ borderBottom: "1px solid var(--border)" }}>
                        <td style={{ padding: "7px 8px", fontWeight: 600 }}>{c.name}</td>
                        <td style={{ padding: "7px 8px", color: "var(--text-2)" }}>{c.symbol} · {c.timeframe}</td>
                        <td style={{ padding: "7px 8px", textAlign: "right", fontFamily: "monospace" }}>{c.oos_profit_factor.toFixed(2)}</td>
                        <td style={{ padding: "7px 8px", textAlign: "right", fontFamily: "monospace" }}>{c.total_trades}</td>
                        <td style={{ padding: "7px 8px", textAlign: "right", fontFamily: "monospace", color: "var(--loss)" }}>{c.max_drawdown_pct.toFixed(2)}%</td>
                        <td style={{ padding: "7px 8px", textAlign: "right", fontFamily: "monospace", color: c.monthly_return === null ? "var(--text-3)" : c.monthly_return >= 0 ? "var(--profit)" : "var(--loss)" }}>{formatoPct(c.monthly_return)}</td>
                        <td style={{ padding: "7px 8px", textAlign: "right", fontFamily: "monospace", color: c.annual_return === null ? "var(--text-3)" : c.annual_return >= 0 ? "var(--profit)" : "var(--loss)" }}>{formatoPct(c.annual_return)}</td>
                        <td style={{ padding: "7px 8px", color: c.ledger_verified ? "var(--profit)" : "var(--loss)" }}>{c.ledger_verified ? "Sí" : "No"}</td>
                        <td style={{ padding: "7px 8px", fontFamily: "monospace", color: gates === 11 ? "var(--profit)" : "var(--text-2)" }}>{gates}/11</td>
                        <td style={{ padding: "7px 8px", color: "var(--text-2)" }}>{c.engine_version}</td>
                        <td style={{ padding: "7px 8px", fontFamily: "monospace", color: "var(--text-2)" }}>
                          {acortar(c.strategy_id, 12)}
                          <BotonCopiar texto={c.strategy_id} activo={copiadoId === c.strategy_id} onCopiar={copiar} />
                        </td>
                        <td style={{ padding: "7px 8px", fontFamily: "monospace", color: "var(--text-2)" }}>
                          {acortar(c.dataset_hash, 10)}
                          <BotonCopiar texto={c.dataset_hash} activo={copiadoId === c.dataset_hash} onCopiar={copiar} />
                        </td>
                        <td style={{ padding: "7px 8px" }}>
                          <a href="/trading-desk/estrategias" style={{ display: "inline-block", padding: "4px 10px", background: "var(--surface-3)", border: "1px solid var(--border-strong)", borderRadius: "3px", color: "var(--text-1)", fontSize: "11.5px", textDecoration: "none", whiteSpace: "nowrap" }}>
                            Llevar al Trading Desk
                          </a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* BLOQUE 2: CÓMO SE FABRICA UNA ESTRATEGIA */}
        <section style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <h2 style={{ fontSize: "14px", fontWeight: 700, margin: 0, color: "var(--text-1)" }}>Cómo se fabrica una estrategia</h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: "10px" }}>
            {tarjetas.map((t) => (
              <a key={t.href} href={t.href} style={{ display: "flex", flexDirection: "column", gap: "6px", padding: "14px", background: "var(--surface-1)", border: "1px solid var(--border)", borderRadius: "6px", textDecoration: "none", color: "inherit" }}>
                <span style={{ fontSize: "11px", color: "var(--text-3)", fontFamily: "monospace" }}>Módulo {t.numero}</span>
                <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--text-1)" }}>{t.titulo}</span>
                <span style={{ fontSize: "12px", color: "var(--text-2)", lineHeight: 1.4 }}>{t.descripcion}</span>
                <span style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "11px", marginTop: "4px" }}>
                  {t.ok !== null && <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: t.ok ? "var(--profit)" : "var(--text-3)" }} />}
                  <span style={{ color: "var(--text-3)" }}>{t.estado}</span>
                </span>
              </a>
            ))}
          </div>
        </section>

        {/* PIE DISCRETO */}
        <footer style={{ borderTop: "1px solid var(--border)", paddingTop: "10px" }}>
          <a href="/candidatos" style={{ fontSize: "11.5px", color: "var(--text-3)", textDecoration: "none" }}>
            Archivo técnico: {totalCandidatos > 0 ? noPasaron : "sin evidencia"} candidata(s) evaluada(s) que no han pasado (para uso interno) →
          </a>
        </footer>

      </div>
    </div>
  );
}
