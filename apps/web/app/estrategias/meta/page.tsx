"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Layers,
  Sparkles,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Scale,
  Zap,
  Grid,
  BarChart3,
  Sliders,
} from "lucide-react";
import {
  getCertifiedMetaStrategies,
  getCertifiedStrategies,
  getDiscoveryStatus,
  type CertifiedMetaStrategy,
  type CertifiedStrategy,
} from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import { esValidaFondeo } from "../_bloques/comun";

type MetaTab = "meta_fondeo" | "meta_ultra" | "correlacion";

const ETIQUETA_ESTADO: Record<string, string> = {
  SUPERSEDED: "Sustituida por versión posterior",
  ASSEMBLED_PENDING_PORTFOLIO_BACKTEST: "Ensamblada · Pendiente de retesteo",
  APPROVED_LEGACY: "Aprobada con motor antiguo",
  REVALIDATION_REQUIRED: "Requiere revalidación",
  APPROVED_CURRENT_ENGINE: "Certificada motor vigente",
};

export default function PaginaMeta() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [certificadas, setCertificadas] = useState<CertifiedStrategy[]>([]);
  const [metas, setMetas] = useState<CertifiedMetaStrategy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  // Submenú solicitado por Emilio
  const [activeTab, setActiveTab] = useState<MetaTab>("meta_fondeo");

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [disc, certs, metaList] = await Promise.all([
        getDiscoveryStatus().catch(() => null),
        getCertifiedStrategies().catch(() => []),
        getCertifiedMetaStrategies().catch(() => []),
      ]);
      setEngineVersion(disc?.current_engine_version ?? null);
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
  const puedeEnsamblar = validas.length >= 2;

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
                <span>M5: Candidatos Meta-Estrategias (Carteras & Portafolios)</span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                  REDUCCIÓN VARIANZA
                </span>
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono">
                Compresión del drawdown mediante la agregación de algoritmos descorrelacionados en futuros CME y Ultra Cripto.
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
      <NavBloques activo="meta" />

      {/* KPI Strip del Módulo M5 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Estrategias Listas M3</span>
          <div className="text-xl font-bold text-[var(--profit)]">{validas.length} / 2 Requeridas</div>
          <span className="text-[11px] text-[var(--text-3)] block">
            {puedeEnsamblar ? "Umbral cumplido para carteras" : "Esperando graduación M3"}
          </span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Meta-Estrategias Censo</span>
          <div className="text-xl font-bold text-[var(--text-1)]">{metas.length}</div>
          <span className="text-[11px] text-[var(--text-3)] block">Registradas en disco</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Objetivo Reducción DD</span>
          <div className="text-xl font-bold text-[var(--profit)]">-35% a -50%</div>
          <span className="text-[11px] text-[var(--text-3)] block">Frente a estrategias individuales</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Motor Vigente</span>
          <div className="text-xl font-bold text-[var(--text-1)] truncate">{engineVersion || "5.18.0"}</div>
          <span className="text-[11px] text-[var(--text-3)] block">Alineación estricta</span>
        </div>
      </div>

      {/* SUBMENÚS DE M5 */}
      <div className="flex flex-wrap items-center gap-1.5 border-b border-[var(--border)] pb-2 font-mono text-xs">
        <button
          onClick={() => setActiveTab("meta_fondeo")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "meta_fondeo"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[var(--profit)]" />
            <span>1. Candidatos Meta-Fondeo CME ({metas.length})</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("meta_ultra")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "meta_ultra"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent opacity-80"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[var(--text-3)]" />
            <span>2. Candidatos Meta-Ultra Cripto (En Construcción)</span>
          </div>
        </button>

        <button
          onClick={() => setActiveTab("correlacion")}
          className={`px-3 py-1.5 rounded transition ${
            activeTab === "correlacion"
              ? "bg-[var(--surface-3)] text-[var(--text-1)] font-bold border border-[var(--border-strong)]"
              : "text-[var(--text-2)] hover:bg-[var(--surface-2)] border border-transparent"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <Grid className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>3. Matriz de Correlación & Solape Temporal</span>
          </div>
        </button>
      </div>

      {/* CONTENIDO TAB 1: META-FONDEO CME */}
      {activeTab === "meta_fondeo" && (
        <div className="space-y-4">
          {/* Doctrina Matemática de las Meta-Estrategias */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
            <div className="border-b border-[var(--border)] pb-2">
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Por Qué en Cuentas de Fondeo la Varianza Mata Más que la Rentabilidad Media
              </h2>
              <p className="text-xs text-[var(--text-3)] font-mono">
                La física del trailing drawdown impone techos de pérdida inamovibles.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="space-y-2">
                <span className="font-bold text-[var(--text-2)] uppercase font-mono text-[11px] block">
                  El Peligro del Algoritmo Único
                </span>
                <p className="text-[var(--text-3)] leading-relaxed font-mono text-[11.5px]">
                  Cualquier estrategia individual, por alto que sea su Sharpe o Profit Factor, atraviesa periódicamente
                  rachas de pérdidas consecutivas (drawdowns de racimo). Si este valle coincide con la fase inicial
                  de una cuenta de fondeo, la cuenta se suspende automáticamente por trailing drawdown.
                </p>
              </div>

              <div className="space-y-2">
                <span className="font-bold text-[var(--profit)] uppercase font-mono text-[11px] block">
                  La Solución Meta-Estrategia
                </span>
                <p className="text-[var(--text-3)] leading-relaxed font-mono text-[11.5px]">
                  Al ensamblar dos o más algoritmos no correlacionados (por ejemplo, momentum en apertura de NQ + reversión
                  a la media en ES sesión tarde), las ganancias de uno amortiguan las pérdidas del otro. El drawdown conjunto
                  se reduce entre un 35% y un 50%, aplanando la curva de riesgo.
                </p>
              </div>
            </div>
          </div>

          {/* Estado del Ensamblador */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Scale className="w-4 h-4 text-[var(--profit)]" />
                <span>Estado del Ensamblador de Carteras Fondeo</span>
              </h2>
              <span className="text-xs font-mono text-[var(--text-3)]">Regla #16 · Cero-Mocks</span>
            </div>

            {!puedeEnsamblar ? (
              <div className="p-6 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] space-y-3 font-mono text-xs">
                <div className="flex items-center gap-2 text-[var(--text-2)] font-bold">
                  <AlertCircle className="w-4 h-4 text-[var(--loss)]" />
                  <span>Ensamblado en Pausa por Falta de Materia Prima Certificada</span>
                </div>
                <p className="text-[var(--text-3)] leading-relaxed">
                  Para crear una Meta-Estrategia institucional que no sea un invento matemático, se requiere un mínimo de{" "}
                  <strong className="text-[var(--text-1)]">2 estrategias certificadas</strong> que hayan superado
                  simultáneamente los 11 Gates del Criterio 1.1 con el motor vigente ({engineVersion || "5.18.0"}).
                </p>
                <div className="flex items-center gap-4 text-[11px] pt-1">
                  <span className="text-[var(--text-3)]">
                    Disponibles hoy: <strong className="text-[var(--loss)]">{validas.length}</strong>
                  </span>
                  <span className="text-[var(--text-3)]">
                    Requeridas: <strong className="text-[var(--profit)]">2</strong>
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-4 rounded-lg bg-[var(--profit-dim)] border border-[var(--profit)] space-y-2 font-mono text-xs">
                <div className="flex items-center gap-2 text-[var(--profit)] font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Condición Cumplida: Hay {validas.length} Estrategias Certificadas Listas</span>
                </div>
                <p className="text-[var(--text-2)]">
                  El motor puede ejecutar la optimización de paridad de riesgo (Risk Parity / Min-Variance) para ensamblar
                  una nueva Meta-Estrategia sobre el ledger real.
                </p>
              </div>
            )}
          </div>

          {/* Inventario de Meta-Estrategias Registradas */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
              <h2 className="text-sm font-bold text-[var(--text-1)]">
                Censo de Meta-Estrategias Registradas en SQLite
              </h2>
              <span className="text-xs font-mono text-[var(--text-3)]">{metas.length} registradas</span>
            </div>

            {metas.length === 0 ? (
              <div className="p-8 text-center text-xs text-[var(--text-3)] font-mono">
                No hay meta-estrategias registradas en la base de datos para la versión vigente.
              </div>
            ) : (
              <div className="space-y-3">
                {metas.map((m) => (
                  <div
                    key={m.meta_strategy_id}
                    className="p-4 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] space-y-3 font-mono text-xs"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-2">
                      <div className="space-y-0.5">
                        <div className="font-bold text-[var(--text-1)] flex items-center gap-2">
                          <span>{m.name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)]">
                            {ETIQUETA_ESTADO[m.status] || m.status}
                          </span>
                        </div>
                        <span className="text-[10px] text-[var(--text-3)]">{m.meta_strategy_id}</span>
                      </div>
                      <div className="text-right">
                        <span className="text-[11px] text-[var(--text-3)] block">Componentes</span>
                        <span className="font-bold text-[var(--profit)]">{m.components.length} algoritmos</span>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <span className="text-[10.5px] uppercase text-[var(--text-3)] font-semibold block">
                        Ponderación de Componentes:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                        {m.components.map((c) => (
                          <div
                            key={c.strategy_id}
                            className="p-2 rounded bg-[var(--surface-1)] border border-[var(--border)] flex items-center justify-between"
                          >
                            <span className="truncate max-w-[150px] text-[var(--text-2)]">{c.strategy_id}</span>
                            <span className="font-bold text-[var(--profit)] font-mono">
                              {(c.weight * 100).toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* CONTENIDO TAB 2: META-ULTRA CRIPTO (EN CONSTRUCCIÓN) */}
      {activeTab === "meta_ultra" && (
        <div className="space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-6 space-y-4 font-mono text-xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-2)]">
                <Sparkles className="w-5 h-5 text-[var(--text-3)]" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-[var(--text-1)] font-sans">
                  Meta-Estrategias Ultra Cripto (EN CONSTRUCCIÓN)
                </h2>
                <p className="text-[11px] text-[var(--text-3)]">
                  Envolvente de cartera asimétrica multi-token congelada en state/PUNTO_GUARDADO_ULTRA.md.
                </p>
              </div>
            </div>

            <div className="p-4 rounded bg-[var(--surface-2)] border border-[var(--border)] space-y-2 font-sans text-xs text-[var(--text-2)]">
              <p>
                <strong>Diseño del Meta-Router Ultra:</strong> En la ruta Ultra (Cripto), las meta-estrategias no buscan replicar el balance plano de futuros CME, sino explotar la <strong>asimetría convexa</strong>:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-[11.5px] text-[var(--text-3)] font-mono">
                <li>Router de asignación de capital dinámico entre BTC, ETH, SOL y tokens de alta beta.</li>
                <li>Piramidación sobre ganancias flotantes sin arriesgar capital base.</li>
                <li>Reciclaje de beneficios hacia reservas frías en USDT.</li>
              </ul>
              <p className="text-[11px] text-[var(--text-3)] font-mono pt-1">
                La arquitectura del código mantiene los contratos y slots de base de datos listos para cuando se reactive el carril cripto.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* CONTENIDO TAB 3: MATRIZ DE CORRELACIÓN & SOLAPE */}
      {activeTab === "correlacion" && (
        <div className="space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-3 font-mono text-xs">
            <div className="border-b border-[var(--border)] pb-2 font-sans">
              <h2 className="text-sm font-bold text-[var(--text-1)] flex items-center gap-2">
                <Grid className="w-4 h-4 text-[var(--profit)]" />
                <span>Metodología de Correlación por Solape Temporal Real (Investigación I3)</span>
              </h2>
              <p className="text-xs text-[var(--text-3)] mt-0.5">
                Cálculo honesto sobre el ledger de operaciones barra a barra para prohibir diversificaciones ilusorias.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans pt-1">
              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-[var(--profit)] font-bold">Criterio de Inclusión</span>
                <div className="text-xs font-bold text-[var(--text-1)]">Correlación de Retornos Diarios &lt; 0.65</div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Dos algoritmos solo pueden combinarse si el coeficiente de Pearson de sus PnL diarios es inferior a 0.65. Si dos estrategias operan en la misma dirección a la misma hora, se descarta la redundante.
                </p>
              </div>

              <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded p-3.5 space-y-1.5">
                <span className="text-[10px] font-mono uppercase text-[var(--profit)] font-bold">Solape Mínimo</span>
                <div className="text-xs font-bold text-[var(--text-1)]">Al Menos 12 Meses de Concurrencia</div>
                <p className="text-[11px] text-[var(--text-3)]">
                  Se exige que ambas estrategias hayan estado activas durante el mismo periodo de tiempo histórico para que la correlación matemática tenga significado estadístico real y no sea un artefacto de cálculo.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
