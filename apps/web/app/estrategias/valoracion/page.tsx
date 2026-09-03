"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  ArrowRight,
} from "lucide-react";
import { getCertifiedStrategies, getDiscoveryStatus, type CertifiedStrategy } from "@/lib/api";
import NavBloques from "../_bloques/NavBloques";
import { esValidaFondeo } from "../_bloques/comun";

interface GateSpec {
  num: string;
  slug: string;
  name: string;
  condition: string;
  purpose: string;
}

const ONCE_GATES: GateSpec[] = [
  {
    num: "G01",
    slug: "gate-1-data-ingest",
    name: "Integridad OHLCV & Ingesta Continua",
    condition: "100% datos continuos sin huecos (gap <= 2%), sellado SHA-256 de contratos CME",
    purpose: "Garantiza que el dataset físico está auditado y libre de lookahead bias.",
  },
  {
    num: "G02",
    slug: "gate-2-cost-backtest",
    name: "Costes Reales & Fricción de Mercado",
    condition: "Net Profit OOS > 0 tras comisiones ($0.60/lado MES) y 1 tick slippage",
    purpose: "Comprueba que la ventaja matemática sobrevive a los costes del broker y del exchange.",
  },
  {
    num: "G03",
    slug: "gate-3-trade-significance",
    name: "Muestra Estadística Significativa",
    condition: "Total Trades OOS >= 200 operaciones",
    purpose: "Elimina la suerte o el sesgo de supervivencia derivado de muestras pequeñas.",
  },
  {
    num: "G04",
    slug: "gate-4-walk-forward",
    name: "Eficiencia Walk-Forward (WFE)",
    condition: "WFE >= 50% en al menos 5 ventanas de optimización / retesteo",
    purpose: "Certifica que los parámetros conservan consistencia fuera de la ventana de diseño.",
  },
  {
    num: "G05",
    slug: "gate-5-monte-carlo",
    name: "Monte Carlo 1,000x & Tasa de Ruina",
    condition: "Max Drawdown en percentil 95 <= límite prop ($1,800 en cuenta 50K)",
    purpose: "Simula 1,000 permutaciones aleatorias de trades para evitar quiebras por rachas.",
  },
  {
    num: "G06",
    slug: "gate-6-stress-slippage",
    name: "Estrés a Slippage & Latencia (3x)",
    condition: "Profit Factor >= 1.10 al triplicar la fricción habitual de ejecución",
    purpose: "Asegura la supervivencia del algoritmo en aperturas de alta volatilidad o slippage adverso.",
  },
  {
    num: "G07",
    slug: "gate-7-regime-coverage",
    name: "Cobertura Multiciclo de Regímenes",
    condition: "Rentabilidad positiva en periodos alcistas, bajistas y de rango (2008-2026)",
    purpose: "Evita que un régimen de mercado unidireccional enmascare debilidades estructurales.",
  },
  {
    num: "G08",
    slug: "gate-8-dsr-ratio",
    name: "Deflated Sharpe Ratio (DSR)",
    condition: "DSR > 0 penalizado por número total de pruebas realizadas (López de Prado)",
    purpose: "Protege contra la minería masiva y el sesgo de selección en backtesting.",
  },
  {
    num: "G09",
    slug: "gate-9-novelty-antifit",
    name: "Novedad Estructural & Grados de Libertad",
    condition: "Árbol AST con <= 4 bloques condicionales; no-colinealidad con estrategias previas",
    purpose: "Impide la memorización de datos por exceso de parámetros o sobre-optimización.",
  },
  {
    num: "G10",
    slug: "gate-10-debate-agentes",
    name: "Auditoría Semántica & Cero Martingala",
    condition: "Validación por comité multi-agente: cero rejillas (grid) y cero promediar pérdidas",
    purpose: "Descarta sistemas suicidas de aumento de contratos tras operaciones perdedoras.",
  },
  {
    num: "G11",
    slug: "gate-11-nautilus-event",
    name: "Simulación de Eventos NautilusCore",
    condition: "Aprobación sobre motor event-driven intra-barra con trailing drawdown flotante",
    purpose: "Garantiza que la lógica soporta la regla de trailing intradía de las firmas CME.",
  },
];

export default function PaginaValoracion() {
  const [engineVersion, setEngineVersion] = useState<string | null>(null);
  const [certificadas, setCertificadas] = useState<CertifiedStrategy[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [disc, certs] = await Promise.all([
        getDiscoveryStatus().catch(() => null),
        getCertifiedStrategies().catch(() => []),
      ]);
      setEngineVersion(disc?.current_engine_version ?? null);
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
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
                <span>M3: Valoración para Fondeo & Criterio 1.1 Sellado</span>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                  11 GATES
                </span>
              </h1>
              <p className="text-xs text-[var(--text-2)] font-mono">
                Evaluación algorítmica sobre equity flotante en tiempo real: ¿aprobaría la estrategia una cuenta de fondeo CME?
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
      <NavBloques activo="valoracion" />

      {/* KPI Strip del Módulo M3 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono">
        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Válidas Fondeo Actual</span>
          <div className="text-xl font-bold text-[var(--profit)]">{validas.length} Certificadas</div>
          <span className="text-[11px] text-[var(--text-3)] block">
            {validas.length === 0 ? "Criterio 1.1 sellado (0 mocks)" : "Listas para ejecución"}
          </span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Puertas de Validación</span>
          <div className="text-xl font-bold text-[var(--text-1)]">11 Gates</div>
          <span className="text-[11px] text-[var(--text-3)] block">Exigencia institucional 100%</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Motor de Fondeo</span>
          <div className="text-xl font-bold text-[var(--profit)]">5.15.0+ Flotante</div>
          <span className="text-[11px] text-[var(--text-3)] block">Simulación intra-barra realista</span>
        </div>

        <div className="p-3.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1">
          <span className="text-[10px] text-[var(--text-3)] block uppercase font-semibold">Criterio Cero-Mocks</span>
          <div className="text-xl font-bold text-[var(--text-1)]">Activo</div>
          <span className="text-[11px] text-[var(--text-3)] block">Sin estrategias de juguete</span>
        </div>
      </div>

      {/* Matriz de los 11 Gates Institucionales con enlaces directos a sus páginas */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
          <div>
            <h2 className="text-sm font-bold text-[var(--text-1)]">
              Los 11 Gates del Criterio 1.1 Sellado (Regla #26 Invariable)
            </h2>
            <p className="text-xs text-[var(--text-3)] font-mono">
              Para que una estrategia se considere "Válida para Fondeo" debe superar simultáneamente los 11 puntos sin excepción.
            </p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0 text-xs font-mono text-[var(--profit)]">
            <ShieldCheck className="w-4 h-4" />
            <span>11 Subpáginas Dedicadas en M3</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5 font-mono text-xs">
          {ONCE_GATES.map((gate) => (
            <Link
              key={gate.num}
              href={`/estrategias/valoracion/${gate.slug}`}
              className="p-3 rounded-lg bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] hover:border-[var(--profit)]/50 transition space-y-1 font-sans group block"
            >
              <div className="flex items-center justify-between font-mono">
                <span className="text-[11px] font-bold text-[var(--profit)] px-1.5 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border)]">
                  {gate.num}
                </span>
                <span className="text-xs font-bold text-[var(--text-1)] group-hover:text-[var(--profit)] transition flex items-center gap-1">
                  <span>{gate.name}</span>
                  <ArrowRight className="w-3 h-3 text-[var(--text-3)] group-hover:text-[var(--profit)] transition" />
                </span>
              </div>
              <div className="text-[11px] text-[var(--text-2)] font-mono font-semibold">
                Condición: <span className="text-[var(--text-1)]">{gate.condition}</span>
              </div>
              <p className="text-[11px] text-[var(--text-3)]">{gate.purpose}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
