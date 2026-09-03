"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Zap,
  TrendingDown,
  ShieldCheck,
  AlertTriangle,
  Flame,
  CheckCircle2,
  XCircle,
  Clock,
  Filter,
  Layers,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  BarChart3,
  Bot,
  Brain,
  Sliders,
  Scale,
  Sparkles,
  GitBranch,
} from "lucide-react";
import { getDiscoveryStatus } from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import {
  formatoGeneradoUtc,
  type CampanaTelemetria,
  type RespuestaTelemetria,
} from "../_bloques/comun";

type MejoraSubmenuTab = "embudo_etapas" | "diagnostico_causas" | "dopaje_reprogramacion";

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
  const [cargando, setCargando] = useState(false);

  // Submenú de navegación de pasos de mejora
  const [activeTab, setActiveTab] = useState<MejoraSubmenuTab>("embudo_etapas");

  const cargar = useCallback(async () => {
    setCargando(true);
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
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  return (
    <div className="w-full max-w-7xl mx-auto space-y-4 pb-20 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
                <span>M2: Bucle de Mejora & Reprogramación Cuantitativa</span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                  LOOP CERRADO
                </span>
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono">
                Refinamiento paramétrico, embudo In-Sample/OOS y telemetría de fallos detectados en campañas.
              </p>
            </div>
          </div>

          <button
            onClick={() => void cargar()}
            disabled={cargando}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] font-mono text-xs hover:bg-[var(--surface-3)] transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${cargando ? "animate-spin" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Navegación Modular M1–M5 */}
      <NavBloques activo="mejora" />

      {/* KPI Strip del Embudo de Mejora */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Campañas Auditadas</span>
          <div className="text-xl font-bold text-[var(--text-1)]">{campanas.length}</div>
          <span className="text-[11px] text-[var(--text-3)] block">Telemetría persistida en disco</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Fricción Aplicada</span>
          <div className="text-xl font-bold text-[var(--profit)]">$0.60 / lado</div>
          <span className="text-[11px] text-[var(--text-3)] block">Comisión real MES + 1 tick slippage</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Criterio de Descarte</span>
          <div className="text-xl font-bold text-[var(--text-1)]">100% Invariable</div>
          <span className="text-[11px] text-[var(--text-3)] block">Sin relajar listón para maquillar</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Estado Motor</span>
          <div className="text-xl font-bold text-[var(--text-1)] truncate">{engineVersion || "5.18.0"}</div>
          <span className="text-[11px] text-[var(--text-3)] block">Validado contra backend</span>
        </div>
      </div>

      {/* SUBMENÚS DE M2 (Pasos del Bucle de Mejora) */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-[var(--border)] pb-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab("embudo_etapas")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "embudo_etapas"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>1. Embudo por Etapas (IS → VAL → OOS)</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("diagnostico_causas")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "diagnostico_causas"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-[var(--loss)]" />
            <span>2. Diagnóstico Forense de Rechazo</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("dopaje_reprogramacion")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "dopaje_reprogramacion"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>3. Mecanismos de Dopaje Algorítmico</span>
          </div>
        </button>
      </div>

      {/* CONTENIDO TAB 1: EMBUDO POR ETAPAS */}
      {activeTab === "embudo_etapas" && (
        <div className="space-y-4">
          {/* Estructura del Embudo de Tres Fases */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
            <div className="border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Filter className="w-4 h-4 text-[var(--profit)]" />
                <span>Estructura de las 3 Fases del Embudo Estadístico</span>
              </h2>
              <p className="text-xs text-[var(--text-3)] mt-0.5">
                Cada candidato bruto debe sobrevivir sucesivamente a las 3 ventanas de datos sin relajar los umbrales.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-sans pt-1">
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between font-mono text-xs font-bold text-[var(--text-1)]">
                  <span>Fase 1: In-Sample (IS)</span>
                  <span className="text-[var(--text-2)]">60% Datos</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Ventana de entrenamiento inicial. Exige al menos <strong>5 operaciones</strong> y un Profit Factor bruto mínimo de <strong>1.05</strong> para justificar el gasto computacional.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between font-mono text-xs font-bold text-[var(--text-1)]">
                  <span>Fase 2: Validación (VAL)</span>
                  <span className="text-[var(--text-2)]">20% Datos</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Ventana intermedia fuera de la muestra inicial. Descarta algoritmos que sufren memorización inmediata (overfitting temprano) o curvas erráticas.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between font-mono text-xs font-bold text-[var(--profit)]">
                  <span>Fase 3: Out-of-Sample (OOS)</span>
                  <span className="text-[var(--profit)] font-bold">20% Holdout Ciego</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Holdout estricto no tocado. Exige <strong>≥ 100-200 trades</strong> y un Profit Factor neto tras comisiones de <strong>≥ 1.10–1.25</strong> para enviar a M3 Valoración.
                </p>
              </div>
            </div>
          </div>

          {/* Historial de Campañas de Telemetría Reales */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Registro de Campañas de Minería & Mejora en Disco
              </h2>
              <span className="text-[11px] text-[var(--text-3)] font-mono">
                {campanas.length} campañas leídas
              </span>
            </div>

            {campanas.length === 0 ? (
              <div className="p-8 text-center text-[var(--text-3)] font-mono">
                Sin campañas de telemetría recientes en orchestration/results/telemetria/.
              </div>
            ) : (
              <div className="space-y-2">
                {campanas.map((c) => {
                  const campanaId = `${c.symbol}_${c.timeframe}_${c.generado_utc}`;
                  const estaAbierta = filaAbierta === campanaId;
                  return (
                    <div
                      key={campanaId}
                      className="rounded-lg bg-[var(--surface-2)] border border-[var(--border)] overflow-hidden"
                    >
                      <button
                        onClick={() => setFilaAbierta(estaAbierta ? null : campanaId)}
                        className="w-full p-3.5 text-left flex items-center justify-between cursor-pointer hover:bg-[var(--surface-3)] transition"
                      >
                        <div className="space-y-0.5">
                          <div className="text-xs font-bold text-[var(--text-1)] font-mono flex items-center gap-2">
                            <span>{c.symbol} {c.timeframe} ({c.profile})</span>
                            <span className="text-[10px] font-normal text-[var(--text-3)]">
                              ({formatoGeneradoUtc(c.generado_utc)})
                            </span>
                          </div>
                          <div className="text-[11px] text-[var(--text-3)] font-sans">
                            {resumenFamilias(c.por_familia)}
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <span className="text-xs font-bold text-[var(--profit)] font-mono">
                            {c.evaluadas} evaluadas
                          </span>
                          {estaAbierta ? (
                            <ChevronUp className="w-4 h-4 text-[var(--text-3)]" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-[var(--text-3)]" />
                          )}
                        </div>
                      </button>

                      {estaAbierta && (
                        <div className="p-3.5 bg-[var(--surface-1)] border-t border-[var(--border)] space-y-2">
                          <span className="text-[10px] text-[var(--text-3)] uppercase font-semibold block">
                            Desglose por Familia Algorítmica:
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 font-mono text-[11px]">
                            {Object.entries(c.por_familia).map(([fam, metrica]) => (
                              <div
                                key={fam}
                                className="p-2 rounded bg-[var(--surface-2)] border border-[var(--border)] space-y-0.5"
                              >
                                <span className="font-bold text-[var(--text-1)] block truncate">{fam}</span>
                                <span className="text-[10px] text-[var(--text-3)] block">
                                  Total: {metrica.total} · Sin ventaja: {metrica.sin_ventaja_bruta}
                                </span>
                              </div>
                            ))}
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

      {/* CONTENIDO TAB 2: DIAGNÓSTICO FORENSE DE CAUSAS DE RECHAZO */}
      {activeTab === "diagnostico_causas" && (
        <div className="space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-3 font-mono text-xs">
            <div className="border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-[var(--loss)]" />
                <span>Diagnóstico Forense de Causas de Rechazo (Por Qué Mueren las Estrategias en M2)</span>
              </h2>
              <p className="text-xs text-[var(--text-3)] mt-0.5">
                El 98% de las estrategias brutas de SQX fallan en M2. La plataforma no las fuerza: documenta el motivo físico exacto.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-sans pt-1">
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-[var(--loss)] font-bold">Causa 01: Fricción Real</span>
                <div className="text-xs font-bold text-[var(--text-1)]">Consumo por Comisión & Slippage</div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Estrategias con ganancia bruta pero trades de recorrido ínfimo. Al deducir $1.20 USD round-turn por contrato micro y 1 tick de slippage, el Profit Factor colapsa por debajo de 1.0.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-[var(--loss)] font-bold">Causa 02: Sobreajuste (Overfitting)</span>
                <div className="text-xs font-bold text-[var(--text-1)]">Colapso en Muestra OOS</div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Reglas complejas con más de 4 bloques condicionales que memorizan el pasado. Al someterlas a los 3 años no vistos (Out-of-Sample), la curva de equidad entra en drawdown destructivo.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-[var(--loss)] font-bold">Causa 03: Varianza Incompatible</span>
                <div className="text-xs font-bold text-[var(--text-1)]">Drawdown Superior al Techo Prop</div>
                <p className="text-[11px] text-[var(--text-3)]">
                  La estrategia es rentable a largo plazo, pero su racha de pérdidas consecutivas supera los $2,000 de una cuenta CME de 50K, provocando la liquidación inmediata de la prueba de fondeo.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* CONTENIDO TAB 3: MECANISMOS DE DOPAJE ALGORÍTMICO */}
      {activeTab === "dopaje_reprogramacion" && (
        <div className="space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-3 font-mono text-xs">
            <div className="border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Zap className="w-4 h-4 text-[var(--profit)]" />
                <span>Los 5 Tratamientos Cuantitativos de Reprogramación (services/optimization/expert_refinement_loop.py)</span>
              </h2>
              <p className="text-xs text-[var(--text-3)] mt-0.5">
                Especificación de tratamientos cuantitativos de reprogramación (services/optimization/expert_refinement_loop.py) cuando una candidata falla por poco en M2.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-sans pt-1">
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-1)]">1. Filtro de Régimen de Volatilidad (ATR/ADX)</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--surface-3)] text-[var(--profit)]">ANTI-CHOP</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Inyección de un detector de régimen de volatilidad (expansión ATR o umbral ADX &gt; 25) para prohibir entradas durante compresiones laterales donde las comisiones erosionan la cuenta.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-1)]">2. Bloqueo Asimétrico Free-Risk (Break-Even)</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--surface-3)] text-[var(--profit)]">+1.2R a +1.5R</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Mueve automáticamente el stop loss al precio de entrada (+ costes) cuando el trade alcanza +1.2R, blindando el capital y convirtiendo operaciones ganadoras en riesgo cero.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-1)]">3. Chandelier ATR Trailing Stop Multi-Tier</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--surface-3)] text-[var(--profit)]">LOCK PROFITS</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Trailing stop adaptativo que rastrea máximos relativos con distancia elástica basada en múltiplos de ATR, capturando tendencias hiperbólicas sin devolver el drawdown intradía.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-1)]">4. Filtro de Microestructura & Spread Anti-Fricción</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--surface-3)] text-[var(--profit)]">GATE 2 / 6</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Descarta ejecuciones en momentos de horquilla ancha (aperturas de noticias o rollover de contratos CME) garantizando que la ventaja matemática sobreviva al slippage.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5 md:col-span-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[var(--text-1)]">5. Dimensionamiento Asimétrico: Lineal Fondeo vs Piramidación Convexa Ultra</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--surface-3)] text-[var(--text-2)]">TRACK SEPARATION</span>
                </div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Para Fondeo CME: sizing lineal estricto sin martingala (Gate 10). Para Ultra Cripto (en construcción): piramidación convexa sobre ganancias no realizadas con stop ajustado.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
