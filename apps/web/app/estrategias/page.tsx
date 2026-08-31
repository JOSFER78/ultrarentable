"use client";

/**
 * Página de Estrategias — catálogo canónico verificado.
 *
 * Reescrita el 2026-08-31 tras auditar lo que mostraba la versión anterior
 * (respaldada en cuarentena/web_paginas_anteriores/estrategias_page_ANTES.tsx).
 *
 * Qué estaba mal y se corrige aquí:
 *  1. Leía de /api/v2/strategy-lab (extracciones crudas de SQX), no del catálogo canónico.
 *     Resultado: mostraba 0 estrategias certificadas cuando la base tenía 27.
 *  2. Los símbolos de esa fuente están corruptos: de 525 registros, 267 etiquetados
 *     "AUDUSD_H1", 92 como "AUTO" y 11 como "ULTRA" — que no son símbolos.
 *  3. Renderizaba cualquier número tal cual, incluidos beneficios de 9,79e+26 USD,
 *     drawdowns del 100 % y profit factors > 50.
 *
 * Ahora: fuente canónica (/api/v1/candidates, contrastada fila a fila contra SQLite) y
 * cada cifra pasa por la auditoría de ./verificacion antes de pintarse.
 */

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Database,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { getCandidatosCanonicos, CandidatoCanonico } from "@/lib/api";
import { auditarCandidata, mostrar, AuditoriaCandidata } from "./verificacion";

const CERTIFICADA = "APPROVED_CURRENT_ENGINE";

/** Estados que significan "esta medición ya no vale", con su explicación. */
const ESTADOS_INVALIDADOS: Record<string, string> = {
  LEGACY_MOTOR_SIN_POINT_VALUE:
    "Medida con el motor anterior al 31-ago-2026, que no aplicaba el multiplicador de contrato. Su P&L en futuros era ~50x menor de lo real.",
  LEGACY_MOTOR_SENAL_SIN_CRUCE:
    "Certificada con el motor 5.4.0, que evaluaba CROSS_ABOVE como comparación de estado (ema_rápida > ema_lenta) en lugar de evento de cruce. La estrategia estaba casi siempre en mercado y generaba el doble de operaciones. No comparable con el motor 5.5.0.",
};

interface Fila {
  c: CandidatoCanonico;
  a: AuditoriaCandidata;
}

function Metrica({
  etiqueta,
  texto,
  problema,
}: {
  etiqueta: string;
  texto: string;
  problema?: boolean;
}) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] uppercase tracking-wider text-slate-500">{etiqueta}</span>
      <span
        className={
          problema
            ? "text-sm font-semibold text-amber-400"
            : texto === "SIN DATOS"
            ? "text-sm text-slate-500"
            : "text-sm font-semibold text-slate-100"
        }
      >
        {texto}
      </span>
    </div>
  );
}

export default function PaginaEstrategias() {
  const [filas, setFilas] = useState<Fila[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [soloCertificadas, setSoloCertificadas] = useState(true);
  const [ocultarNoPlausibles, setOcultarNoPlausibles] = useState(false);
  const [seleccion, setSeleccion] = useState<Fila | null>(null);

  async function refrescar() {
    setCargando(true);
    setError(null);
    try {
      const datos = await getCandidatosCanonicos(1000);
      const auditadas = datos.map((c) => ({ c, a: auditarCandidata(c as unknown as Record<string, unknown>) }));
      setFilas(auditadas);
      setSeleccion(auditadas.find((f) => f.c.status === CERTIFICADA) ?? auditadas[0] ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo consultar el catálogo canónico.");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    void refrescar();
  }, []);

  const resumen = useMemo(() => {
    const total = filas.length;
    const certificadas = filas.filter((f) => f.c.status === CERTIFICADA);
    const invalidadas = filas.filter((f) => f.c.status in ESTADOS_INVALIDADOS).length;
    const conProblemas = filas.filter((f) => f.a.tieneProblemas).length;
    const certConProblemas = certificadas.filter((f) => f.a.tieneProblemas).length;
    return { total, certificadas: certificadas.length, invalidadas, conProblemas, certConProblemas };
  }, [filas]);

  const visibles = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return filas
      .filter((f) => (soloCertificadas ? f.c.status === CERTIFICADA : true))
      .filter((f) => (ocultarNoPlausibles ? !f.a.tieneProblemas : true))
      .filter((f) =>
        q
          ? `${f.c.name} ${f.c.symbol} ${f.c.timeframe} ${f.c.route}`.toLowerCase().includes(q)
          : true
      )
      .sort((a, b) => (b.a.profitFactor.valor ?? 0) - (a.a.profitFactor.valor ?? 0));
  }, [filas, busqueda, soloCertificadas, ocultarNoPlausibles]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      <header className="space-y-2">
        <div className="flex items-center gap-3">
          <Database className="h-6 w-6 text-cyan-400" />
          <h1 className="text-2xl font-bold">Estrategias — catálogo canónico</h1>
          <button
            onClick={() => void refrescar()}
            className="ml-auto flex items-center gap-2 rounded-md border border-slate-700 px-3 py-1.5 text-sm hover:bg-slate-800"
          >
            <RefreshCw className={`h-4 w-4 ${cargando ? "animate-spin" : ""}`} />
            Actualizar
          </button>
        </div>
        <p className="text-sm text-slate-400">
          Fuente: <code className="text-cyan-400">/api/v1/candidates</code> — tabla{" "}
          <code>candidates</code> de la base canónica. Cada cifra pasa una auditoría de
          plausibilidad antes de mostrarse: lo que no la supera aparece como{" "}
          <span className="text-amber-400 font-semibold">NO PLAUSIBLE</span>, nunca como un número.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-red-800 bg-red-950/40 p-4 text-sm">
          <div className="flex items-center gap-2 font-semibold text-red-300">
            <XCircle className="h-4 w-4" /> ERROR
          </div>
          <p className="mt-1 text-red-200">{error}</p>
          <p className="mt-1 text-red-300/70">
            No se muestran datos en caché ni valores por defecto: si la fuente no responde, no hay dato.
          </p>
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
        {[
          { t: "En catálogo", v: resumen.total, c: "text-slate-100" },
          { t: "Certificadas 11/11", v: resumen.certificadas, c: "text-emerald-400" },
          { t: "Invalidadas por motor", v: resumen.invalidadas, c: "text-amber-400" },
          { t: "Con cifras no plausibles", v: resumen.conProblemas, c: "text-amber-400" },
          { t: "Certificadas con problemas", v: resumen.certConProblemas, c: resumen.certConProblemas ? "text-red-400" : "text-emerald-400" },
        ].map((k) => (
          <div key={k.t} className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
            <div className="text-[11px] uppercase tracking-wider text-slate-500">{k.t}</div>
            <div className={`mt-1 text-2xl font-bold ${k.c}`}>{cargando ? "…" : k.v}</div>
          </div>
        ))}
      </section>

      {!cargando && resumen.conProblemas > 0 && (
        <div className="rounded-lg border border-amber-800/60 bg-amber-950/20 p-4 text-sm">
          <div className="flex items-center gap-2 font-semibold text-amber-300">
            <AlertTriangle className="h-4 w-4" />
            {resumen.conProblemas} candidatas del catálogo tienen cifras imposibles
          </div>
          <p className="mt-1 text-amber-200/80">
            Beneficios que desbordan la composición, drawdowns del 100 % (cuenta liquidada) o
            profit factors por división entre cero. Se listan y se marcan, no se ocultan — pero sus
            números <strong>no se presentan como válidos</strong>.
            {resumen.certConProblemas === 0 && (
              <> Ninguna de las <strong>{resumen.certificadas} certificadas</strong> está afectada.</>
            )}
          </p>
        </div>
      )}

      <section className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar por nombre, activo, temporalidad o ruta…"
            className="w-full rounded-md border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-sm outline-none focus:border-cyan-600"
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={soloCertificadas} onChange={(e) => setSoloCertificadas(e.target.checked)} />
          Solo certificadas 11/11
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={ocultarNoPlausibles} onChange={(e) => setOcultarNoPlausibles(e.target.checked)} />
          <Filter className="h-3.5 w-3.5" /> Ocultar no plausibles
        </label>
        <span className="text-sm text-slate-500">{visibles.length} mostradas</span>
      </section>

      <section className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-sm">
          <thead className="bg-slate-900/80 text-left text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-3 py-2">Estrategia</th>
              <th className="px-3 py-2">Ruta</th>
              <th className="px-3 py-2">Activo</th>
              <th className="px-3 py-2">TF</th>
              <th className="px-3 py-2 text-right">PF OOS</th>
              <th className="px-3 py-2 text-right">DD OOS</th>
              <th className="px-3 py-2 text-right">Operaciones</th>
              <th className="px-3 py-2 text-right">Gates</th>
              <th className="px-3 py-2">Estado</th>
            </tr>
          </thead>
          <tbody>
            {cargando && (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                  Consultando el catálogo canónico…
                </td>
              </tr>
            )}
            {!cargando && visibles.length === 0 && (
              <tr>
                <td colSpan={9} className="px-3 py-8 text-center text-slate-500">
                  SIN DATOS con los filtros actuales.
                </td>
              </tr>
            )}
            {visibles.map((f) => {
              const cert = f.c.status === CERTIFICADA;
              return (
                <tr
                  key={f.c.candidate_id}
                  onClick={() => setSeleccion(f)}
                  className={`cursor-pointer border-t border-slate-800/70 hover:bg-slate-900/60 ${
                    seleccion?.c.candidate_id === f.c.candidate_id ? "bg-slate-900" : ""
                  }`}
                >
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      {f.a.tieneProblemas && <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-400" />}
                      {cert && !f.a.tieneProblemas && <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" />}
                      <span className="font-medium">{f.c.name}</span>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-slate-400">{f.c.route}</td>
                  <td className="px-3 py-2">
                    {f.c.icon ? `${f.c.icon} ` : ""}
                    {f.c.symbol}
                  </td>
                  <td className="px-3 py-2 text-slate-400">{f.c.timeframe}</td>
                  <td className={`px-3 py-2 text-right ${f.a.profitFactor.veredicto === "NO_PLAUSIBLE" ? "text-amber-400" : ""}`}>
                    {mostrar(f.a.profitFactor)}
                  </td>
                  <td className={`px-3 py-2 text-right ${f.a.drawdown.veredicto === "NO_PLAUSIBLE" ? "text-amber-400" : ""}`}>
                    {mostrar(f.a.drawdown, " %")}
                  </td>
                  <td className={`px-3 py-2 text-right ${f.a.muestra.veredicto === "NO_PLAUSIBLE" ? "text-amber-400" : ""}`}>
                    {mostrar(f.a.muestra, "", 0)}
                  </td>
                  <td className="px-3 py-2 text-right text-slate-400">
                    {f.c.gates_passed_count ?? "—"}/11
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded px-2 py-0.5 text-[11px] ${
                        cert
                          ? "bg-emerald-950 text-emerald-300"
                          : f.c.status in ESTADOS_INVALIDADOS
                          ? "bg-amber-950 text-amber-300"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {f.c.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {seleccion && (
        <section className="rounded-lg border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-cyan-400" />
            <h2 className="text-lg font-semibold">{seleccion.c.name}</h2>
            <span className="text-sm text-slate-500">
              {seleccion.c.route} · {seleccion.c.symbol} · {seleccion.c.timeframe}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Metrica etiqueta="Profit factor OOS" texto={mostrar(seleccion.a.profitFactor)} problema={seleccion.a.profitFactor.veredicto === "NO_PLAUSIBLE"} />
            <Metrica etiqueta="Drawdown OOS" texto={mostrar(seleccion.a.drawdown, " %")} problema={seleccion.a.drawdown.veredicto === "NO_PLAUSIBLE"} />
            <Metrica etiqueta="Beneficio neto OOS" texto={mostrar(seleccion.a.beneficio, " USD")} problema={seleccion.a.beneficio.veredicto === "NO_PLAUSIBLE"} />
            <Metrica etiqueta="Operaciones OOS" texto={mostrar(seleccion.a.muestra, "", 0)} problema={seleccion.a.muestra.veredicto === "NO_PLAUSIBLE"} />
          </div>

          {seleccion.a.problemas.length > 0 && (
            <div className="rounded-md border border-amber-800/60 bg-amber-950/20 p-3">
              <div className="flex items-center gap-2 text-sm font-semibold text-amber-300">
                <AlertTriangle className="h-4 w-4" /> Por qué estas cifras no se dan por válidas
              </div>
              <ul className="mt-2 space-y-1 text-sm text-amber-200/80">
                {seleccion.a.problemas.map((p, i) => (
                  <li key={i}>· {p}</li>
                ))}
              </ul>
            </div>
          )}

          {seleccion.c.status in ESTADOS_INVALIDADOS && (
            <div className="rounded-md border border-amber-800/60 bg-amber-950/20 p-3 text-sm text-amber-200/80">
              <strong className="text-amber-300">Medición invalidada.</strong>{" "}
              {ESTADOS_INVALIDADOS[seleccion.c.status]}
            </div>
          )}

          <div className="grid gap-2 text-sm md:grid-cols-2">
            <div>
              <span className="text-slate-500">Motivo del estado: </span>
              <span className="text-slate-300">{seleccion.c.status_reason ?? "SIN DATOS"}</span>
            </div>
            <div>
              <span className="text-slate-500">Arquetipo: </span>
              <span className="text-slate-300">{seleccion.c.archetype ?? "SIN DATOS"}</span>
            </div>
            <div>
              <span className="text-slate-500">Dataset: </span>
              <span className="text-slate-300">{seleccion.c.dataset_id ?? "SIN DATOS"}</span>
            </div>
            <div>
              <span className="text-slate-500">Hash de estrategia: </span>
              <code className="text-cyan-400/80">
                {seleccion.c.strategy_sha256 ? `${seleccion.c.strategy_sha256.slice(0, 16)}…` : "SIN DATOS"}
              </code>
            </div>
            <div>
              <span className="text-slate-500">Apta para prop firm: </span>
              <span className="text-slate-300">
                {seleccion.c.prop_firm_eligible === null || seleccion.c.prop_firm_eligible === undefined
                  ? "SIN DATOS"
                  : seleccion.c.prop_firm_eligible
                  ? `Sí — ${seleccion.c.prop_firm_venues ?? "sin venue declarado"}`
                  : "No"}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Tier: </span>
              <span className="text-slate-300">{seleccion.c.tier_label ?? seleccion.c.tier ?? "SIN DATOS"}</span>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
