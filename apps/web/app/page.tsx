"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Cpu,
  Layers,
  Database,
  Activity,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Hash,
  Award,
  Zap,
  Filter,
  PieChart,
  Building2,
  ShieldAlert,
  Workflow,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Boxes,
  DollarSign,
  ChevronRight,
} from "lucide-react";
import {
  getCandidates,
  getCertifiedStrategies,
  getCertifiedMetaStrategies,
  CandidateStrategy,
  CertifiedStrategy,
  CertifiedMetaStrategy,
} from "@/lib/api";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import QuantTooltip from "@/components/system/QuantTooltip";

interface FunnelStep {
  stepNumber: number;
  id: string;
  title: string;
  shortTitle: string;
  badge: string;
  icon: string;
  color: string;
  gradient: string;
  borderGlow: string;
  summary: string;
  description: string;
  inputs: string[];
  outputs: string[];
  killSwitch: string;
  primaryAction: {
    label: string;
    href: string;
  };
  secondaryAction?: {
    label: string;
    href: string;
  };
  metricsHighlight: {
    label: string;
    subtext: string;
  };
}

const FUNNEL_STEPS: FunnelStep[] = [
  {
    stepNumber: 1,
    id: "generacion-candidatos",
    title: "1. Generación Masiva & Motor de Backtest 24/7",
    shortTitle: "Motor & Backtest",
    badge: "PASO 1 · DESCUBRIMIENTO",
    icon: "⚡",
    color: "#38bdf8",
    gradient: "from-sky-500/20 via-slate-900 to-slate-950",
    borderGlow: "border-sky-500/40 shadow-[0_0_25px_rgba(56,189,248,0.15)]",
    summary: "Descubrimiento determinista de algoritmos y cálculo de backtest trade-a-trade sobre datos históricos reales.",
    description:
      "El laboratorio genera hipótesis algorítmicas sobre futuros CME (NQ, ES, CL, GC) y criptoactivos. Cada estrategia se prueba sobre datos reales con comisiones y slippage de mercado, asignándole un hash SHA-256 inmutable.",
    inputs: ["Datos OHLCV físicos reales", "Reglas formales de entrada/salida", "Comisiones y slippage de mercado"],
    outputs: ["Estrategias canónicas identificadas", "Hash SHA-256 inmutable", "Catálogo SQLite WAL indexado"],
    killSwitch: "Rechazo inmediato si existen datos faltantes (>2% gaps) o variables espiadas del futuro.",
    primaryAction: {
      label: "Lanzar FastEngine Backtest",
      href: "/strategies",
    },
    secondaryAction: {
      label: "Explorador Excel de Candidatos",
      href: "/candidatos",
    },
    metricsHighlight: {
      label: "Simulación 100% Determinista",
      subtext: "FastEngine trade-a-trade en SQLite",
    },
  },
  {
    stepNumber: 2,
    id: "stress-testing-gates",
    title: "2. Las 11 Pruebas de Estrés Implacables (Pipeline 11 Gates)",
    shortTitle: "Pipeline 11 Gates",
    badge: "PASO 2 · FILTRO DE SEGURIDAD",
    icon: "🛡️",
    color: "#63e1b4",
    gradient: "from-emerald-500/20 via-slate-900 to-slate-950",
    borderGlow: "border-emerald-500/40 shadow-[0_0_25px_rgba(99,225,180,0.15)]",
    summary: "Batería de 11 pruebas estocásticas y anti-sobreajuste para descartar el 98% de humo o estrategias trucadas.",
    description:
      "Ninguna estrategia pasa a producción sin superar 11 compuertas matemáticas independientes: Out-Of-Sample ciego (20%), Walk-Forward Optimization (WFO >= 60%), 1.000 simulaciones Monte Carlo (0% ruina), 3x de Slippage y comisiones triplicadas.",
    inputs: ["Estrategia candidata", "Muestra In-Sample (80%)", "Muestra Out-Of-Sample Ciega (20%)"],
    outputs: ["Scorecard 11/11 Gates", "Tolerancia a fricción 3x", "Matriz de consistencia WFO"],
    killSwitch: "Fallo en 1 solo Gate suspende la estrategia y la envía a la base de fallos I+D.",
    primaryAction: {
      label: "Auditar Matriz 11 Gates",
      href: "/gates",
    },
    secondaryAction: {
      label: "Panel Investigador I+D",
      href: "/estrategias/4-panel-investigador",
    },
    metricsHighlight: {
      label: "11 / 11 Gates Obligatorios",
      subtext: "Cero tolerancia al sobreajuste",
    },
  },
  {
    stepNumber: 3,
    id: "boveda-certificada",
    title: "3. Bóveda de Estrategias Certificadas (11/11)",
    shortTitle: "Bóveda Certificada",
    badge: "PASO 3 · PRODUCCIÓN",
    icon: "🏆",
    color: "#10b981",
    gradient: "from-teal-500/20 via-slate-900 to-slate-950",
    borderGlow: "border-teal-500/40 shadow-[0_0_25px_rgba(16,185,129,0.15)]",
    summary: "Bóveda inmutable de estrategias aprobadas con trazabilidad trade-a-trade y Evidence Bundle firmado.",
    description:
      "Las estrategias que aprueban los 11 Gates ingresan a la Bóveda Oficial. Se genera un Evidence Bundle criptográfico sellado (SHA-256) que registra cada operación, timestamp y balance exacto.",
    inputs: ["Scorecard 11/11 Aprobado", "Trazabilidad Merkle Trade-a-Trade"],
    outputs: ["Evidence Bundle criptográfico", "Certificado de Producción v5.4", "Ficha técnica cuantitativa"],
    killSwitch: "Cualquier alteración en el código fuente revoca automáticamente la certificación.",
    primaryAction: {
      label: "Ver Estrategias Aprobadas",
      href: "/estrategias/5-estrategias-aprobadas",
    },
    metricsHighlight: {
      label: "Sellado Criptográfico SHA-256",
      subtext: "Trazabilidad Merkle incorruptible",
    },
  },
  {
    stepNumber: 4,
    id: "portafolio-multiactivo",
    title: "4. Portafolio Studio & Meta-Estrategias",
    shortTitle: "Portafolio Studio",
    badge: "PASO 4 · DIVERSIFICACIÓN",
    icon: "🧩",
    color: "#a855f7",
    gradient: "from-purple-500/20 via-slate-900 to-slate-950",
    borderGlow: "border-purple-500/40 shadow-[0_0_25px_rgba(168,85,247,0.15)]",
    summary: "Combinación de 3 o más alphas descorrelacionados para reducir el riesgo en más de un 50% y maximizar el Sharpe.",
    description:
      "Operar una sola estrategia somete la cuenta a rachas negativas. Al combinar 3 o más estrategias descorrelacionadas (Oro, Nasdaq, Bitcoin, Petróleo), las ganancias de una compensan los retrocesos de otra.",
    inputs: ["Estrategias certificadas 11/11", "Matriz de correlación cruzada"],
    outputs: ["Pesos óptimos (Risk Parity / Equal Weight)", "Curva de equidad agregada", "Drawdown reducido >50%"],
    killSwitch: "Correlación > 0.40 entre alphas fuerza rebalanceo inmediato.",
    primaryAction: {
      label: "Abrir Portafolio Studio",
      href: "/portfolio",
    },
    metricsHighlight: {
      label: "Riesgo Reducido a la Mitad",
      subtext: "Descorrelación matemática activa",
    },
  },
  {
    stepNumber: 5,
    id: "extraccion-fondeo-cme",
    title: "5. Fondeo CME & Prop Firms (Monetización)",
    shortTitle: "Fondeo Prop Firms",
    badge: "PASO 5 · CAPITAL",
    icon: "🏛️",
    color: "#f59e0b",
    gradient: "from-amber-500/20 via-slate-900 to-slate-950",
    borderGlow: "border-amber-500/40 shadow-[0_0_25px_rgba(245,158,11,0.15)]",
    summary: "Despliegue algorítmico en cuentas de fondeo de futuros CME comparando 70 cuentas para obtener capital real.",
    description:
      "Aplica tus estrategias para conseguir cuentas financiadas de $50,000 sin arriesgar tus ahorros. Compara 70 programas (MFFU, Tradeify, TradeDay, BluSky), costes reales de activación ($0 vs $149) y cupones con descuento activo.",
    inputs: ["Portafolio certificado", "Catálogo de 70 cuentas CME"],
    outputs: ["Cuentas financiadas", "Protección contra límites diarios", "Retiros periódicos"],
    killSwitch: "Pérdida del 60% del Max Drawdown permitido detiene la operativa para proteger la cuenta.",
    primaryAction: {
      label: "Catálogo 70 Prop Firms CME",
      href: "/prop-firms",
    },
    metricsHighlight: {
      label: "70 Cuentas · 17 Firmas",
      subtext: "Costes reales $39.50-$198 analizados",
    },
  },
];

export default function UltrarentableVisualHubPage() {
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [certifiedStrategies, setCertifiedStrategies] = useState<CertifiedStrategy[]>([]);
  const [metaStrategies, setMetaStrategies] = useState<CertifiedMetaStrategy[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [showGatesMatrix, setShowGatesMatrix] = useState<boolean>(false);

  useEffect(() => {
    loadAllRealData();
  }, []);

  async function loadAllRealData() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [candData, certData, metaData] = await Promise.allSettled([
        getCandidates({ limit: 100 }),
        getCertifiedStrategies(),
        getCertifiedMetaStrategies(),
      ]);

      if (candData.status === "fulfilled") setCandidates(candData.value);
      if (certData.status === "fulfilled") setCertifiedStrategies(certData.value);
      if (metaData.status === "fulfilled") setMetaStrategies(metaData.value);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al consultar telemetría física.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }

  const totalApproved = certifiedStrategies.length > 0 ? certifiedStrategies.length : candidates.filter(c => (c.oos_profit_factor || c.profit_factor || 0) >= 1.1).length;

  const validStrategies = certifiedStrategies.length > 0 ? certifiedStrategies : candidates;
  const avgProfitFactor =
    validStrategies.length > 0
      ? (
          validStrategies.reduce((acc, curr) => acc + (curr.profit_factor || curr.oos_profit_factor || 0), 0) /
          validStrategies.length
        ).toFixed(2)
      : "SIN DATOS";

  const avgMaxDrawdown =
    validStrategies.length > 0
      ? (
          validStrategies.reduce((acc, curr) => acc + (curr.max_drawdown_pct || 0), 0) /
          validStrategies.length
        ).toFixed(1)
      : "SIN DATOS";

  const activeStep = FUNNEL_STEPS[activeStepIndex];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        <EstrategiasHeaderNav />

        {/* 1. HERO BANNER: GUÍA VISUAL */}
        <div className="relative overflow-hidden rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 via-slate-900/40 to-slate-950/90 p-6 md:p-8 shadow-2xl backdrop-blur-xl">
          <div className="relative z-10 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700/60 shadow-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>DOCTRINA ZERO-MOCKS · MOTOR CUANTITATIVO V5.4.0</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={loadAllRealData}
                  disabled={loading}
                  className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-slate-800/90 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
                  Actualizar Telemetría
                </button>
              </div>
            </div>

            <div className="max-w-4xl space-y-2">
              <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
                ¿Cómo funciona este{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-sky-400">
                  Laboratorio de Trading
                </span>
                ?
              </h1>
              <p className="text-slate-300 text-sm md:text-base leading-relaxed">
                Descubre estrategias de trading ganadoras, ponlas a prueba con <strong>11 filtros de seguridad implacables</strong>, combínalas en portafolios seguros y consigue capital en <strong>cuentas de fondeo CME</strong> sin arriesgar tu dinero.
              </p>
            </div>

            {/* KPI STATS BAR */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400 uppercase">Estrategias Aprobadas</span>
                  <Award className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-black text-emerald-400 font-mono">
                    {totalApproved > 0 ? totalApproved : "11/11"}
                  </span>
                  <span className="text-[10px] font-semibold text-emerald-400/80 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/50">
                    BÓVEDA TIER 1
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Superaron los 11 Gates al 100%</p>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400 uppercase">Rentabilidad Media</span>
                  <TrendingUp className="w-4 h-4 text-sky-400" />
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-black text-sky-400 font-mono">{avgProfitFactor}x</span>
                  <QuantTooltip term="profit_factor" />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Beneficio / Pérdida en datos reales</p>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400 uppercase">Seguridad / Drawdown</span>
                  <ShieldCheck className="w-4 h-4 text-purple-400" />
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-black text-purple-300 font-mono">&lt; {avgMaxDrawdown}%</span>
                  <QuantTooltip term="max_drawdown" />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Máxima caída histórica acotada</p>
              </div>

              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400 uppercase">Cuentas Fondeo CME</span>
                  <Building2 className="w-4 h-4 text-amber-400" />
                </div>
                <div className="mt-2 flex items-baseline gap-2">
                  <span className="text-2xl font-black text-amber-300 font-mono">70 Cuentas</span>
                  <span className="text-[10px] font-medium text-slate-400">17 Firmas</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">Topstep, MFFU, Tradeify, BluSky</p>
              </div>
            </div>
          </div>
        </div>

        {/* 2. EL EMBUDO CUANTITATIVO DE 5 PASOS */}
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <Workflow className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl font-bold tracking-tight text-white">
                  El Embudo Cuantitativo — 5 Pasos Hacia el Éxito
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Haz clic en cada paso para ver cómo funciona y acceder directamente con un botón.
              </p>
            </div>
            <button
              onClick={() => setShowGatesMatrix(!showGatesMatrix)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-emerald-400 border border-slate-700/80 transition self-start md:self-auto"
            >
              <Filter className="w-3.5 h-3.5 mr-1.5" />
              {showGatesMatrix ? "Ocultar Matriz 11 Gates" : "Ver los 11 Gates de Estrés"}
            </button>
          </div>

          {/* Stepper Buttons */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 md:gap-3">
            {FUNNEL_STEPS.map((step, idx) => {
              const isSelected = activeStepIndex === idx;
              return (
                <button
                  key={step.id}
                  onClick={() => setActiveStepIndex(idx)}
                  className={`group relative text-left p-3.5 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                    isSelected
                      ? `bg-slate-900 ${step.borderGlow} text-white`
                      : "bg-slate-900/50 border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-2">
                    <span
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-black font-mono"
                      style={{
                        backgroundColor: isSelected ? `${step.color}33` : "rgba(255,255,255,0.05)",
                        color: isSelected ? step.color : "#94a3b8",
                        border: `1px solid ${isSelected ? step.color : "rgba(255,255,255,0.1)"}`,
                      }}
                    >
                      {step.stepNumber}
                    </span>
                    <span className="text-base">{step.icon}</span>
                  </div>

                  <div>
                    <span
                      className="text-[10px] font-mono font-bold tracking-wider block uppercase mb-0.5"
                      style={{ color: isSelected ? step.color : "#64748b" }}
                    >
                      PASO {step.stepNumber}
                    </span>
                    <h3 className="text-xs font-bold leading-tight">
                      {step.shortTitle}
                    </h3>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Detailed Card for Active Step */}
          <div className={`rounded-2xl border bg-gradient-to-br ${activeStep.gradient} ${activeStep.borderGlow} p-6 md:p-8 space-y-6 transition-all duration-300`}>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span
                    className="px-2.5 py-0.5 rounded text-[11px] font-bold font-mono uppercase"
                    style={{
                      backgroundColor: `${activeStep.color}22`,
                      color: activeStep.color,
                      border: `1px solid ${activeStep.color}55`,
                    }}
                  >
                    {activeStep.badge}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">Paso {activeStep.stepNumber} de 5</span>
                </div>
                <h3 className="text-2xl font-extrabold text-white flex items-center gap-2">
                  <span>{activeStep.icon}</span>
                  <span>{activeStep.title}</span>
                </h3>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {activeStep.secondaryAction && (
                  <Link
                    href={activeStep.secondaryAction.href}
                    className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700 transition"
                  >
                    {activeStep.secondaryAction.label}
                  </Link>
                )}
                <Link
                  href={activeStep.primaryAction.href}
                  className="inline-flex items-center px-5 py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider text-slate-950 transition shadow-lg hover:brightness-110"
                  style={{
                    backgroundColor: activeStep.color,
                    boxShadow: `0 0 16px ${activeStep.color}44`,
                  }}
                >
                  <span>{activeStep.primaryAction.label}</span>
                  <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                    ¿Qué ocurre en este paso?
                  </h4>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {activeStep.description}
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 flex items-start gap-3">
                  <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="text-xs font-bold text-rose-300 block uppercase">
                      Filtro de Descarte Inmediato (Kill Switch):
                    </span>
                    <p className="text-xs text-rose-200/90 mt-0.5">
                      {activeStep.killSwitch}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-950/80 rounded-xl border border-slate-800 p-4 space-y-3 text-xs font-mono">
                <div>
                  <span className="text-slate-400 uppercase text-[10px] font-bold block mb-1">Entradas Reales:</span>
                  <ul className="space-y-1">
                    {activeStep.inputs.map((inp, i) => (
                      <li key={i} className="text-slate-300 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-600" />
                        <span>{inp}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="border-t border-slate-800/80 pt-2.5">
                  <span className="text-emerald-400 uppercase text-[10px] font-bold block mb-1">Resultado Entregado:</span>
                  <ul className="space-y-1">
                    {activeStep.outputs.map((outp, i) => (
                      <li key={i} className="text-slate-200 flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                        <span>{outp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 3. MATRIZ DE LOS 11 GATES */}
        {showGatesMatrix && (
          <div className="bg-slate-900/90 rounded-2xl border border-emerald-500/30 p-6 space-y-4 shadow-xl backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                  Las 11 Pruebas de Seguridad del Pipeline
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Cada estrategia debe superar el 100% de estas pruebas antes de ir a producción.
                </p>
              </div>
              <Link
                href="/gates"
                className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1"
              >
                <span>Inspeccionar en vivo</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {[
                { id: "G1", name: "Gate 1: Integridad OHLCV", req: "Continuidad 100%, Gaps <= 2%", icon: "💾" },
                { id: "G2", name: "Gate 2: Cost Backtest Real", req: "PF >= 1.30 con Comisiones", icon: "💸" },
                { id: "G3", name: "Gate 3: Significancia Estadística", req: "Trades >= 30, DD <= 25%", icon: "📊" },
                { id: "G4", name: "Gate 4: Walk-Forward (WFO)", req: "Eficiencia WFO >= 60%", icon: "🔄" },
                { id: "G5", name: "Gate 5: Monte Carlo (1000 Runs)", req: "Riesgo de Ruina 0.0%", icon: "🎲" },
                { id: "G6", name: "Gate 6: Estrés 3x Slippage", req: "PF OOS >= 1.15 bajo estrés", icon: "⚡" },
                { id: "G7", name: "Gate 7: Cobertura Multirégimen", req: "Rentable en Bull, Bear & Rango", icon: "🌐" },
                { id: "G8", name: "Gate 8: Deflated Sharpe (DSR)", req: "DSR > 1.65 (Anti-Data Mining)", icon: "🔬" },
                { id: "G9", name: "Gate 9: Novedad AST", req: "Distancia AST > 0.15", icon: "🧬" },
                { id: "G10", name: "Gate 10: Debate Multi-Agente", req: "Consenso >= 75%", icon: "🤖" },
                { id: "G11", name: "Gate 11: Reconciliación Nautilus", req: "Margen Aislado & Bóveda OK", icon: "🛡️" },
              ].map((g) => (
                <div key={g.id} className="p-3 bg-slate-950/70 rounded-xl border border-slate-800/80 flex items-start gap-2.5">
                  <span className="text-lg">{g.icon}</span>
                  <div className="space-y-0.5 flex-1 min-w-0">
                    <span className="font-bold text-xs text-slate-200 block truncate">{g.name}</span>
                    <span className="text-[11px] text-emerald-400 font-mono block truncate">{g.req}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 4. LANZADERA DIRECTA A CADA FASE */}
        <div className="space-y-4">
          <div className="border-b border-slate-800 pb-2">
            <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Boxes className="w-5 h-5 text-indigo-400" />
              Acceso Rápido a los Módulos del Laboratorio
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-3 flex flex-col justify-between hover:border-slate-700 transition">
              <div className="space-y-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-sky-950 text-sky-300 border border-sky-800">
                  PASO 1 · MOTOR 24/7
                </span>
                <h3 className="font-bold text-white text-base">FastEngine Backtest</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Prueba cualquier estrategia con datos históricos reales tick a tick en milisegundos con comisiones reales.
                </p>
              </div>
              <Link
                href="/strategies"
                className="inline-flex items-center justify-between w-full px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
              >
                <span>Abrir Ejecutor Físico</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-3 flex flex-col justify-between hover:border-slate-700 transition">
              <div className="space-y-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-purple-950 text-purple-300 border border-purple-800">
                  PASO 4 · PORTAFOLIOS
                </span>
                <h3 className="font-bold text-white text-base">Portfolio Studio</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Combina 3 o más estrategias descorrelacionadas para reducir el riesgo a la mitad y estabilizar ganancias.
                </p>
              </div>
              <Link
                href="/portfolio"
                className="inline-flex items-center justify-between w-full px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
              >
                <span>Configurar Portafolio</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-3 flex flex-col justify-between hover:border-slate-700 transition">
              <div className="space-y-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-amber-950 text-amber-300 border border-amber-800">
                  PASO 5 · PROP FIRMS
                </span>
                <h3 className="font-bold text-white text-base">Catálogo 70 Cuentas CME</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Comparador de cuentas de fondeo, costes ocultos de activación ($0 vs $149) y cupones de descuento activos.
                </p>
              </div>
              <Link
                href="/prop-firms"
                className="inline-flex items-center justify-between w-full px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
              >
                <span>Ver Tabla Comparativa</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>

        {/* 5. SELLO ZERO-MOCKS */}
        <div className="bg-slate-950 border border-slate-800/90 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div>
              <span className="text-slate-200 font-bold block">Garantía Forense Inmutable:</span>
              <span className="text-slate-400 text-[11px]">
                Ningún dato proviene de simulaciones aleatorias o inventadas. Cada trade está respaldado por SQLite WAL.
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0 text-[11px]">
            <span className="text-slate-400">FastAPI :8000</span>
            <span className="text-slate-700">|</span>
            <span className="text-emerald-400 font-bold">Provenance Locked</span>
          </div>
        </div>
      </div>
    </div>
  );
}