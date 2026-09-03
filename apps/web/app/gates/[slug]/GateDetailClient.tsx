"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ShieldCheck,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileCode2,
  Database,
  Terminal,
  Layers,
  Scale,
  Activity,
  ExternalLink,
} from "lucide-react";
import { getCertifiedStrategies, getCandidates, type CertifiedStrategy, type CandidateStrategy } from "@/lib/api";
import { useEngineVersion } from "@/hooks/useEngineVersion";

export interface GateCanonicalSpec {
  num: number;
  id: string;
  slug: string;
  name: string;
  short_title: string;
  category: "Data Ingest" | "Fricción & Ejecución" | "Robustez Estadística" | "Anti-Overfit" | "Gobernanza" | "Event-Driven";
  badge: string;
  icon: string;
  pythonFile: string;
  version: string;
  objective: string;
  formula: string;
  riskMitigated: string;
  thresholdsFondeo: Array<{ param: string; value: string; desc: string }>;
  thresholdsUltra: Array<{ param: string; value: string; desc: string }>;
}

export const ALL_GATES: GateCanonicalSpec[] = [
  {
    num: 1,
    id: "G01",
    slug: "gate-1-data-ingest",
    name: "Integridad OHLCV, Continuidad & Checksum SHA-256",
    short_title: "1. Data Ingest",
    category: "Data Ingest",
    badge: "Integridad",
    icon: "💾",
    pythonFile: "services/validation/registry/gates/gate_01.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Garantizar 100% de datos continuos sin huecos, desórdenes temporales ni precios anómalos sobre futuros CME regulados con sellado criptográfico.",
    formula: "Gap_Frac <= 0.02 (2%) ∧ Precios > 0 ∧ Timestamps estrictamente crecientes ∧ Checksum_SHA256(dataset) verificado",
    riskMitigated: "Lookahead bias, datos corrompidos, saltos de sesión mal procesados o datasets sintéticos complacientes.",
    thresholdsFondeo: [
      { param: "max_gap_frac", value: "<= 2.0%", desc: "Fracción máxima admisible de huecos temporales en la serie de velas" },
      { param: "min_bars_1h", value: ">= 200 velas", desc: "Mínimo de velas consecutivas de 1 hora requeridas para auditar" },
      { param: "integrity_check", value: "SHA-256 Sellado", desc: "Hash criptográfico inmutable del archivo fuente de ticks/velas en disco" },
    ],
    thresholdsUltra: [
      { param: "max_gap_frac", value: "<= 3.0%", desc: "Tolerancia ante desconexiones de exchanges de futuros perpetuos" },
      { param: "min_bars_1h", value: ">= 150 velas", desc: "Mínimo de velas 1h para validación en pares cripto de alta liquidez" },
    ],
  },
  {
    num: 2,
    id: "G02",
    slug: "gate-2-cost-backtest",
    name: "Cost Backtest con Comisiones Reales y Fricción",
    short_title: "2. Costes & Fricción",
    category: "Fricción & Ejecución",
    badge: "Costes Reales",
    icon: "💸",
    pythonFile: "services/validation/registry/gates/gate_02.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Comprobar que la ventaja matemática sobrevive a los costes del broker y del exchange descontando comisiones exactas y 1 tick de slippage por operación.",
    formula: "Net_PnL_OOS = Gross_PnL - (N_trades * Comision_Por_Lado * 2) - (N_trades * Slippage_Minimo) > 0 ∧ PF_Net >= 1.10",
    riskMitigated: "Estrategias de alta frecuencia ilusorias que ganan en bruto pero son destruidas por el coste transaccional en CME.",
    thresholdsFondeo: [
      { param: "cme_fee_mes", value: "$0.60 / lado", desc: "Comisión fija por contrato para Micro E-mini S&P 500 (Issue #38)" },
      { param: "cme_fee_es", value: "$2.50 / contrato", desc: "Comisión estándar para contratos E-mini grandes" },
      { param: "min_net_pf", value: ">= 1.10", desc: "Profit Factor neto mínimo tras deducir todas las comisiones y deslizamiento" },
    ],
    thresholdsUltra: [
      { param: "crypto_taker_fee", value: "0.05% (5 bps)", desc: "Comisión de taker en órdenes a mercado sobre futuros BingX/Binance" },
      { param: "min_net_pf", value: ">= 1.10", desc: "Profit Factor neto tras deducir comisiones y financiación" },
    ],
  },
  {
    num: 3,
    id: "G03",
    slug: "gate-3-trade-significance",
    name: "Significancia Estadística de Muestra (N >= 200)",
    short_title: "3. Muestra Estadística",
    category: "Robustez Estadística",
    badge: "N >= 200",
    icon: "📊",
    pythonFile: "services/validation/registry/gates/gate_03.py",
    version: "1.0.0 (Criterio 1.1)",
    objective: "Descartar la suerte muestral exigiendo un volumen de operaciones fuera de muestra estadísticamente representativo (N >= 200 en Criterio 1.1) y ausencia de dependencia de outliers.",
    formula: "N_Trades_OOS >= 200 ∧ Outlier_Dependency_Ratio <= 50.0% (los 2 mejores trades no superan el 50% del PnL total)",
    riskMitigated: "Sesgo de supervivencia por muestras reducidas donde 2 o 3 operaciones afortunadas enmascaran un sistema perdedor.",
    thresholdsFondeo: [
      { param: "min_oos_trades", value: ">= 200 trades", desc: "Regla #26 del Criterio 1.1 sellado para considerar la estrategia válida" },
      { param: "max_outlier_ratio", value: "<= 50.0%", desc: "Porcentaje máximo de beneficio aportado por los dos trades más grandes" },
      { param: "max_drawdown_fondeo", value: "<= 4.0%", desc: "Caída máxima porcentual del equity respecto al límite de cuenta CME" },
    ],
    thresholdsUltra: [
      { param: "min_oos_trades", value: ">= 10 trades", desc: "Umbral mínimo de incubación preliminar para activos convexos" },
      { param: "max_outlier_ratio", value: "<= 85.0%", desc: "Tolerancia adaptada a modelos de tendencia tipo 'fat tail'" },
    ],
  },
  {
    num: 4,
    id: "G04",
    slug: "gate-4-walk-forward",
    name: "Eficiencia Walk-Forward Auténtica (Rolling WFO)",
    short_title: "4. Walk-Forward (WFE)",
    category: "Anti-Overfit",
    badge: "Anti-Overfit",
    icon: "🔄",
    pythonFile: "services/validation/registry/gates/gate_04.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Evaluar la estabilidad paramétrica a través de 5 ventanas rodantes sucesivas (Rolling Walk-Forward) para certificar consistencia temporal.",
    formula: "WFE = (Annualized_Return_OOS / Annualized_Return_IS) >= 50% ∧ Consistencia_Ventanas >= 40%",
    riskMitigated: "Memorización de datos (curvatura) y sobreajuste estático a un único tramo histórico de mercado.",
    thresholdsFondeo: [
      { param: "num_windows", value: "5 ventanas", desc: "Número de sub-periodos rodantes de calibración y prueba OOS" },
      { param: "min_avg_wfe", value: ">= 50.0%", desc: "Eficiencia Walk-Forward promedio exigida para cuentas de fondeo" },
      { param: "min_consistency_pct", value: ">= 40.0%", desc: "Porcentaje de ventanas OOS rodantes con PnL neto positivo" },
    ],
    thresholdsUltra: [
      { param: "num_windows", value: "5 ventanas", desc: "Ventanas móviles adaptadas a ciclos cripto de 4 años" },
      { param: "min_avg_wfe", value: ">= 40.0%", desc: "Eficiencia mínima en entornos de alta volatilidad" },
    ],
  },
  {
    num: 5,
    id: "G05",
    slug: "gate-5-monte-carlo",
    name: "Remuestreo Monte Carlo (1,000x & 0% Ruina)",
    short_title: "5. Monte Carlo 1000x",
    category: "Robustez Estadística",
    badge: "Ruina 0.0%",
    icon: "🎲",
    pythonFile: "services/validation/registry/gates/gate_05.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Simular 1,000 permutaciones bootstrap de trades para calcular la probabilidad empírica de ruina y el Drawdown en el percentil 95.",
    formula: "P(Ruina) = (Simulaciones con DD >= Límite_Fondeo / 1000) <= 0.5% ∧ DD_Percentil_95 <= 4.0%",
    riskMitigated: "Quiebra de cuenta provocada por agrupamiento aleatorio de rachas perdedoras (losing streaks).",
    thresholdsFondeo: [
      { param: "num_simulations", value: "1,000 runs", desc: "Permutaciones independientes mediante muestreo con reemplazo" },
      { param: "max_ruin_prob", value: "<= 0.5%", desc: "Probabilidad máxima de tocar el límite de drawdown de la prop firm" },
      { param: "max_dd95_pct", value: "<= 4.0%", desc: "Máximo drawdown tolerable en el percentil 95 de las 1,000 curvas" },
      { param: "ruin_drawdown_limit", value: "4.5% ($1,800)", desc: "Límite de trailing drawdown absoluto en una cuenta 50k" },
    ],
    thresholdsUltra: [
      { param: "max_ruin_prob", value: "<= 5.0%", desc: "Tolerancia de ruina para asignaciones convexas con 1R aislado" },
      { param: "max_dd95_pct", value: "<= 80.0%", desc: "Límite para carteras spot/perpetuos descorrelacionadas" },
    ],
  },
  {
    num: 6,
    id: "G06",
    slug: "gate-6-stress-slippage",
    name: "Estrés de Fricción, Latencia & Shocks de Liquidez (3x)",
    short_title: "6. Estrés & Slippage",
    category: "Fricción & Ejecución",
    badge: "3x Fricción",
    icon: "⚡",
    pythonFile: "services/validation/registry/gates/gate_06.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Evaluar la rentabilidad residual al triplicar el deslizamiento y las comisiones en escenarios de ensanchamiento de spreads y noticias.",
    formula: "PF_Estres = Gross_Profit / (Gross_Loss + (N_Trades * 3 * Friccion_Base)) >= 1.05 ∧ Supervivencia >= 2 escenarios",
    riskMitigated: "Estrategias de scalping o breakout que se derrumban cuando la volatilidad triplica los spreads reales en apertura americana.",
    thresholdsFondeo: [
      { param: "multiplier_slippage", value: "3.0x", desc: "Factor multiplicador aplicado a los costes habituales de ejecución" },
      { param: "min_survival_pf", value: ">= 1.05", desc: "Profit Factor neto mínimo exigido bajo condiciones de fricción 3x" },
      { param: "required_scenarios", value: ">= 2 escenarios", desc: "Debe resistir escenarios Base, +1-Sigma y +2-Sigma" },
    ],
    thresholdsUltra: [
      { param: "multiplier_slippage", value: "3.0x", desc: "Simulación de mechas de liquidación en exchanges cripto" },
      { param: "min_survival_pf", value: ">= 1.00", desc: "Exigencia de umbral de equilibrio bajo estrés severo" },
    ],
  },
  {
    num: 7,
    id: "G07",
    slug: "gate-7-regime-coverage",
    name: "Cobertura y Desempeño en 4 Regímenes de Mercado",
    short_title: "7. Cobertura Regímenes",
    category: "Robustez Estadística",
    badge: "Multi-Ciclo",
    icon: "🌐",
    pythonFile: "services/validation/registry/gates/gate_07.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Clasificar objetivamente cada periodo histórico en 4 regímenes (Alcista, Bajista, Rango, Volatilidad) cruzando cada trade con la vela activa.",
    formula: "Trades_en_Regimenes >= 2 ∧ PnL_Neto > 0 en al menos 2 regímenes independientes (sin asignaciones sintéticas)",
    riskMitigated: "Sistemas optimizados en mercados alcistas unidireccionales (ej. 2020-2021) que quiebran en mercados de rango o bajistas.",
    thresholdsFondeo: [
      { param: "min_active_regimes", value: ">= 2 regímenes", desc: "Debe operar y mantener ventaja en al menos 2 estados de mercado" },
      { param: "min_candles", value: ">= 50 velas", desc: "Mínimo de velas auditadas por régimen para validar la clasificación" },
      { param: "regimes_classified", value: "BULL, BEAR, CHOP, VOL", desc: "Matriz objetiva de clasificación basada en volatilidad y pendiente" },
    ],
    thresholdsUltra: [
      { param: "min_active_regimes", value: ">= 2 regímenes", desc: "Demostración de resiliencia en ciclos de acumulación y distribución" },
    ],
  },
  {
    num: 8,
    id: "G08",
    slug: "gate-8-dsr-ratio",
    name: "Deflated Sharpe Ratio (DSR de Marcos López de Prado)",
    short_title: "8. Deflated Sharpe (DSR)",
    category: "Anti-Overfit",
    badge: "López de Prado",
    icon: "📐",
    pythonFile: "services/validation/registry/gates/gate_08.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Penalizar el ratio Sharpe en función del número de combinaciones de parámetros probadas para eliminar el sesgo de selección (Data Snooping).",
    formula: "DSR_Prob = Norm_CDF( (SR - SR_Esperado_Maximo(N_ensayos, Varianza)) / SE(SR) ) >= 50.0%",
    riskMitigated: "Estrategias descubiertas por minería masiva donde el resultado positivo es mero ruido estadístico aleatorio.",
    thresholdsFondeo: [
      { param: "min_dsr_prob", value: ">= 50.0%", desc: "Probabilidad mínima de que el ratio Sharpe observado no sea fruto del azar" },
      { param: "min_trades", value: ">= 10 trades", desc: "Mínimo de trades OOS necesarios para calcular asimetría y curtosis" },
      { param: "penalty_model", value: "Bailey & López de Prado", desc: "Formulación institucional sellada en Advances in Financial Machine Learning" },
    ],
    thresholdsUltra: [
      { param: "min_dsr_prob", value: ">= 50.0%", desc: "Mismo estándar estadístico para evitar falsos positivos cripto" },
    ],
  },
  {
    num: 9,
    id: "G09",
    slug: "gate-9-novelty-antifit",
    name: "Distancia AST & Grados de Libertad (Anti-Curvatura)",
    short_title: "9. Novedad & AST",
    category: "Anti-Overfit",
    badge: "DoF >= 15",
    icon: "🧬",
    pythonFile: "services/validation/registry/gates/gate_09.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Evaluar la complejidad estructural del árbol sintáctico (AST) y asegurar un ratio elevado de grados de libertad por parámetro.",
    formula: "DoF = Total_Trades / N_Parametros >= 15.0 ∧ AST_Bloques_Condicionales <= 4 ∧ Param_Stability >= 60%",
    riskMitigated: "Sistemas con decenas de parámetros que memorizan el pasado mediante reglas excesivamente complejas o anidadas.",
    thresholdsFondeo: [
      { param: "min_dof", value: ">= 15.0 DoF", desc: "Ratio de grados de libertad: al menos 15 trades por cada parámetro optimizable" },
      { param: "max_params", value: "<= 8 parámetros", desc: "Número máximo de parámetros configurables admitidos en la lógica" },
      { param: "min_stability_pct", value: ">= 60.0%", desc: "Estabilidad de PnL ante variaciones del +/- 10% en los parámetros" },
    ],
    thresholdsUltra: [
      { param: "min_dof", value: ">= 10.0 DoF", desc: "Grados de libertad adaptados a temporalidades de swing o 4 horas" },
      { param: "min_stability_pct", value: ">= 50.0%", desc: "Estabilidad mínima ante variaciones paramétricas" },
    ],
  },
  {
    num: 10,
    id: "G10",
    slug: "gate-10-debate-agentes",
    name: "Auditoría Semántica Cuantitativa (Cero Martingala/Grid)",
    short_title: "10. Debate Multi-Agente",
    category: "Gobernanza",
    badge: "Cero Martingala",
    icon: "🤖",
    pythonFile: "services/validation/registry/gates/gate_10.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Auditoría determinista del código para prohibir formalmente rejillas (grids), martingalas o promediar a la baja, con veto de riesgo vinculante.",
    formula: "Consenso >= 40.0% ∧ Veto_Riesgo == OK ∧ Has_Martingale == FALSE ∧ Has_Grid == FALSE",
    riskMitigated: "Algoritmos tóxicos que incrementan el tamaño de posición tras pérdidas para ocultar drawdowns hasta la quiebra total.",
    thresholdsFondeo: [
      { param: "prohibited_patterns", value: "MARTINGALA, GRID, PROMEDIAR", desc: "Patrones prohibidos de dimensionamiento que violan la gestión de riesgo" },
      { param: "max_dd_limit", value: "<= 4.0%", desc: "Corte tajante si el drawdown máximo supera el 4% en cuentas de fondeo" },
      { param: "min_consensus_score", value: ">= 40.0%", desc: "Aprobación mínima requerida por los comités cuantitativos de auditoría" },
    ],
    thresholdsUltra: [
      { param: "max_dd_limit", value: "<= 30.0%", desc: "Límite de riesgo para carteras convexas con stop loss estructural" },
    ],
  },
  {
    num: 11,
    id: "G11",
    slug: "gate-11-nautilus-event",
    name: "Simulación de Eventos NautilusCore & Trailing Intradía",
    short_title: "11. NautilusCore Engine",
    category: "Event-Driven",
    badge: "Event-Driven",
    icon: "🛡️",
    pythonFile: "services/validation/registry/gates/gate_11.py",
    version: "1.0.0 (Motor 5.18.0)",
    objective: "Ejecutar una auditoría independiente orden a orden en NautilusCore modelando trailing drawdown flotante intra-vela y verificación de no-liquidación.",
    formula: "Simulacion_Event_Driven_Passed == TRUE ∧ Min_Distancia_Liquidacion >= 20.0% ∧ Cero_Violaciones_Trailing_Intradia",
    riskMitigated: "Discrepancias entre backtests cerrados por vela y la regla de trailing drawdown intradía en tiempo real de Topstep y MFFU.",
    thresholdsFondeo: [
      { param: "event_engine", value: "NautilusCore", desc: "Motor determinista de eventos tick-a-tick con libro de órdenes simulado" },
      { param: "trailing_model", value: "Intraday Equity High", desc: "El drawdown persigue el equity máximo intra-barra (regla estricta CME)" },
      { param: "min_dist_liquidation", value: ">= 20.0%", desc: "Margen de seguridad respecto al umbral de cierre automático de la cuenta" },
    ],
    thresholdsUltra: [
      { param: "min_dist_liquidation", value: ">= 2.0%", desc: "Distancia mínima a la liquidación del margen en futuros perpetuos" },
    ],
  },
];

export default function GateDetailClient() {
  const params = useParams();
  const rawSlug = (params?.slug as string) || "gate-1-data-ingest";
  const { version: engineVersion } = useEngineVersion();

  const currentGate = useMemo(() => {
    return ALL_GATES.find((g) => g.slug === rawSlug) || ALL_GATES[0];
  }, [rawSlug]);

  const [certificadas, setCertificadas] = useState<CertifiedStrategy[]>([]);
  const [candidatas, setCandidatas] = useState<CandidateStrategy[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      const [certs, cands] = await Promise.all([
        getCertifiedStrategies().catch(() => []),
        getCandidates().catch(() => []),
      ]);
      setCertificadas(certs);
      setCandidatas(cands);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al conectar con la API.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargarDatos();
  }, [cargarDatos]);

  // Auditoría real de estrategias evaluadas en este Gate (Zero-Mocks)
  const auditResultados = useMemo(() => {
    const gateNumStr = String(currentGate.num);
    const rows: Array<{
      id: string;
      name: string;
      symbol: string;
      timeframe: string;
      route: string;
      status: string;
      gatePassed: boolean | null;
      gateScore?: number;
      evidenceNote?: string;
    }> = [];

    // Analizar certificadas
    for (const cert of certificadas) {
      const rawGate = cert.gates ? (cert.gates as Record<string, any>)[gateNumStr] : undefined;
      const passed = rawGate ? rawGate.passed === true : null;
      const score = rawGate?.score;
      rows.push({
        id: cert.strategy_id,
        name: cert.name || cert.strategy_id,
        symbol: cert.symbol || "MES",
        timeframe: cert.timeframe || "1h",
        route: cert.route || "FONDEO",
        status: cert.status,
        gatePassed: passed,
        gateScore: score,
        evidenceNote: rawGate?.verdict || (passed ? "Comprobación superada" : "Sin evidencia de paso"),
      });
    }

    return rows;
  }, [certificadas, currentGate.num]);

  const statsGate = useMemo(() => {
    const evaluadas = auditResultados.filter((r) => r.gatePassed !== null);
    const aprobadas = evaluadas.filter((r) => r.gatePassed === true);
    return {
      total: auditResultados.length,
      evaluadas: evaluadas.length,
      aprobadas: aprobadas.length,
      tasaPaso: evaluadas.length > 0 ? ((aprobadas.length / evaluadas.length) * 100).toFixed(1) : "0.0",
    };
  }, [auditResultados]);

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* 1. Header Banner Institucional */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-lg shrink-0">
              {currentGate.icon}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                  {currentGate.id}
                </span>
                <span className="text-xs font-mono text-[var(--text-3)] uppercase tracking-wider">
                  {currentGate.category}
                </span>
                <span className="text-xs font-mono text-[var(--text-3)]">·</span>
                <span className="text-xs font-mono text-[var(--text-2)]">{currentGate.version}</span>
              </div>
              <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] mt-0.5">
                {currentGate.name}
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 font-mono text-xs">
            <Link
              href="/estrategias/valoracion"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] text-[var(--text-2)] hover:text-[var(--text-1)] border border-[var(--border)] transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Volver a M3 Valoración</span>
            </Link>
            <button
              onClick={() => void cargarDatos()}
              disabled={cargando}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-1)] hover:bg-[var(--surface-3)] transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${cargando ? "animate-spin text-[var(--profit)]" : ""}`} />
              <span>Actualizar</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Navegador Modular de los 11 Gates */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-2.5">
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-1 scrollbar-thin">
          <div className="flex items-center gap-1.5 shrink-0">
            {ALL_GATES.map((g) => {
              const isCurrent = g.slug === currentGate.slug;
              return (
                <Link
                  key={g.slug}
                  href={`/estrategias/valoracion/${g.slug}`}
                  className={`px-2.5 py-1 rounded text-xs font-mono transition flex items-center gap-1.5 shrink-0 ${
                    isCurrent
                      ? "bg-[var(--surface-3)] border border-[var(--border-strong)] text-[var(--profit)] font-bold shadow-sm"
                      : "bg-transparent hover:bg-[var(--surface-2)] border border-transparent text-[var(--text-2)] hover:text-[var(--text-1)]"
                  }`}
                >
                  <span>{g.icon}</span>
                  <span>{g.id}</span>
                </Link>
              );
            })}
          </div>
          <Link
            href="/estrategias/valoracion"
            className="text-xs font-mono text-[var(--text-3)] hover:text-[var(--text-1)] shrink-0 px-2 py-1 hover:underline flex items-center gap-1"
          >
            <span>Matriz M3</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* 3. Grid de Especificación y Umbrales Canónicos */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 font-mono text-xs">
        {/* Columna Izquierda: Definición Matemática & Criterio 1.1 */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-sans">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-mono">
              <span className="text-xs font-bold text-[var(--text-1)] flex items-center gap-2">
                <FileCode2 className="w-4 h-4 text-[var(--profit)]" />
                <span>Contrato Canónico de Validación</span>
              </span>
              <span className="text-[11px] text-[var(--text-3)] font-mono">{currentGate.pythonFile}</span>
            </div>

            <div className="space-y-1 font-mono text-xs">
              <span className="text-[10px] text-[var(--text-3)] uppercase font-semibold block">Objetivo Cuantitativo:</span>
              <p className="text-[12px] text-[var(--text-2)] leading-relaxed font-sans">{currentGate.objective}</p>
            </div>

            <div className="space-y-1 font-mono text-xs">
              <span className="text-[10px] text-[var(--text-3)] uppercase font-semibold block">Condición Matemática Exacta:</span>
              <div className="p-2.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)] font-mono text-[11px] leading-relaxed break-all">
                {currentGate.formula}
              </div>
            </div>

            <div className="space-y-1 font-mono text-xs">
              <span className="text-[10px] text-[var(--text-3)] uppercase font-semibold block">Riesgo Mitigado (Por qué es obligatorio):</span>
              <p className="text-[12px] text-[var(--text-2)] leading-relaxed font-sans">{currentGate.riskMitigated}</p>
            </div>
          </div>

          {/* Umbrales Oficiales Fondeo CME */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-mono">
              <span className="text-xs font-bold text-[var(--text-1)] flex items-center gap-2 font-sans">
                <Scale className="w-4 h-4 text-[var(--profit)]" />
                <span>Umbrales Oficiales para Fondeo CME (Regla #26 Invariable)</span>
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-2)] text-[var(--profit)] border border-[var(--border)]">
                ESTRICTO
              </span>
            </div>

            <div className="space-y-2">
              {currentGate.thresholdsFondeo.map((t, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-[var(--surface-2)] border border-[var(--border)] flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div className="space-y-0.5">
                    <span className="font-bold text-[var(--text-1)] text-xs font-mono">{t.param}</span>
                    <p className="text-[11px] text-[var(--text-3)] font-sans">{t.desc}</p>
                  </div>
                  <span className="font-mono text-xs font-bold text-[var(--profit)] px-2 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border)] shrink-0 self-start sm:self-auto">
                    {t.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Columna Derecha: Telemetría Real de la Base de Datos */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-mono">
              <span className="text-xs font-bold text-[var(--text-1)] flex items-center gap-2 font-sans">
                <Activity className="w-4 h-4 text-[var(--profit)]" />
                <span>Telemetría de la Puerta en Motor Vigente</span>
              </span>
              <span className="text-[10px] text-[var(--text-3)] font-mono">{engineVersion || "v5.18.0"}</span>
            </div>

            <div className="grid grid-cols-2 gap-2 font-mono">
              <div className="p-3 rounded bg-[var(--surface-2)] border border-[var(--border)] space-y-1">
                <span className="text-[10px] text-[var(--text-3)] block uppercase">Certificadas Auditadas</span>
                <div className="text-xl font-bold text-[var(--text-1)]">{statsGate.total}</div>
                <span className="text-[10px] text-[var(--text-3)] block">Estrategias en SQLite</span>
              </div>

              <div className="p-3 rounded bg-[var(--surface-2)] border border-[var(--border)] space-y-1">
                <span className="text-[10px] text-[var(--text-3)] block uppercase">Tasa de Aprobación</span>
                <div className="text-xl font-bold text-[var(--profit)]">{statsGate.tasaPaso}%</div>
                <span className="text-[10px] text-[var(--text-3)] block">
                  {statsGate.aprobadas} de {statsGate.evaluadas} con evidencia
                </span>
              </div>
            </div>

            <div className="p-3 rounded bg-[var(--surface-2)] border border-[var(--border)] space-y-1 font-sans">
              <span className="text-[10px] text-[var(--text-3)] uppercase font-semibold font-mono block">
                Doctrina de Validación Zero-Mocks:
              </span>
              <p className="text-[11px] text-[var(--text-2)] leading-relaxed">
                Ninguna estrategia se marca como aprobada por deducción o estado. Solo se certifica si existe un registro físico en base de datos con veredicto determinista e inmutable.
              </p>
            </div>
          </div>

          {/* Tabla de Estrategias Evaluadas en esta Puerta */}
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3 font-sans">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-2 font-mono">
              <span className="text-xs font-bold text-[var(--text-1)] flex items-center gap-2">
                <Database className="w-4 h-4 text-[var(--profit)]" />
                <span>Auditoría de Estrategias en {currentGate.id}</span>
              </span>
              <span className="text-[10px] text-[var(--text-3)]">{auditResultados.length} Registros</span>
            </div>

            {auditResultados.length === 0 ? (
              <div className="p-6 text-center text-xs font-mono text-[var(--text-3)]">
                Sin estrategias certificadas en la base de datos actual.
              </div>
            ) : (
              <div className="space-y-1.5 max-h-[320px] overflow-y-auto pr-1">
                {auditResultados.map((row) => {
                  const hasPassed = row.gatePassed === true;
                  const hasFailed = row.gatePassed === false;
                  return (
                    <div
                      key={row.id}
                      className="p-2.5 rounded bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-between gap-2 font-mono text-xs"
                    >
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5 truncate">
                          <span className="font-bold text-[var(--text-1)] truncate">{row.name}</span>
                          <span className="text-[10px] text-[var(--text-3)] shrink-0">
                            ({row.symbol} · {row.timeframe})
                          </span>
                        </div>
                        <p className="text-[10px] text-[var(--text-3)] truncate mt-0.5">{row.evidenceNote}</p>
                      </div>

                      <div className="shrink-0">
                        {hasPassed ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[var(--profit)] px-2 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border)]">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>PASA</span>
                          </span>
                        ) : hasFailed ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[var(--loss)] px-2 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border)]">
                            <XCircle className="w-3 h-3" />
                            <span>NO PASA</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] text-[var(--text-3)] px-2 py-0.5 rounded bg-[var(--surface-3)] border border-[var(--border)]">
                            <span>SIN DATOS</span>
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
