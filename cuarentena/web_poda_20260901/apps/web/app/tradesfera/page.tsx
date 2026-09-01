"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  ShieldCheck,
  TrendingUp,
  Brain,
  Layers,
  Calculator,
  Award,
  ChevronRight,
  ExternalLink,
  Zap,
  Building2,
  DollarSign,
  PieChart,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  FileText,
  Clock,
  Flame,
  Copy,
  Check,
  Target,
  Sparkles,
  X,
} from "lucide-react";

interface ModuleMeta {
  id: string;
  number: string;
  title: string;
  category: "DOCTRINA" | "MATEMÁTICA" | "OPERATIVA" | "PSICOTRADING" | "EJECUCIÓN";
  readTime: string;
  summary: string;
  keyRule: string;
  filePath: string;
  highlights: string[];
}

const TRADESFERA_MODULES: ModuleMeta[] = [
  {
    id: "01",
    number: "M01",
    title: "Ecosistema Tradesfera & Modelo de Negocio",
    category: "DOCTRINA",
    readTime: "12 min",
    summary: "Arquitectura de las 4 Puertas, fundador Vicente Pons, Public Ledger auditado de 167K€ y estructura de partners.",
    keyRule: "Una cuenta de fondeo no es un patrimonio: es un vehículo asimétrico de extracción con vida útil finita.",
    filePath: "docs/tradesfera/01_ECOSISTEMA_TRADESFERA_Y_MODELO_DE_NEGOCIO.md",
    highlights: [
      "Modelo de las 4 Puertas: Descuentos, Ticks, Comunidad y Ledger.",
      "Diferenciación radical: Extracción asimétrica vs inversión tradicional.",
      "Auditoría inmutable de transferencias reales sin sesgo de supervivencia.",
    ],
  },
  {
    id: "02",
    number: "M02",
    title: "Matemática de Bankroll & Capital Munición",
    category: "MATEMÁTICA",
    readTime: "18 min",
    summary: "Formulación de munición (N disparos), Esperanza Matemática Positiva (EV), distribución binomial y regla de cosecha 50/30/20.",
    keyRule: "P(Aprobación >= 1) = 1 - (1 - p)^N. Con 10 balas y p=26.6%, la probabilidad de cobrar supera el 95%.",
    filePath: "docs/tradesfera/02_MATEMATICA_BANKROLL_Y_CAPITAL_MUNICION.md",
    highlights: [
      "Cálculo estocástico de disparos con bankroll finito.",
      "Esperanza matemática neta: EV = P(Éxito) * Payout - Bankroll.",
      "Regla de cosecha 80/20: 80% patrimonio seguro / 20% bóveda de munición.",
    ],
  },
  {
    id: "03",
    number: "M03",
    title: "Teoría de Varianza & Control de Rachas",
    category: "MATEMÁTICA",
    readTime: "15 min",
    summary: "Curvas de drawdown intradía vs EOD, cálculo de Ruina Absoluta y mitigación de rachas negativas consecutivas.",
    keyRule: "El trailing intradía aumenta la probabilidad de quiebra un 340% frente al trailing EOD a cierre de sesión.",
    filePath: "docs/tradesfera/03_TEORIA_VARIANZA_Y_CONTROL_DE_RACHAS.md",
    highlights: [
      "Modelado de drawdown intra-trade vs End-of-Day (EOD).",
      "Matriz de supervivencia frente a rachas de pérdidas de 5 a 10 trades.",
      "Estrategia de amortiguación de varianza mediante microcontratos (MES/MNQ).",
    ],
  },
  {
    id: "04",
    number: "M04",
    title: "Protocolo Inteligente de Aprobación de Cuentas",
    category: "OPERATIVA",
    readTime: "14 min",
    summary: "Fases de evaluación, gestión de microcontratos (MES/MNQ) y timing óptimo para superar el profit target sin sobreexposición.",
    keyRule: "Nunca operar contratos grandes en fase de examen: 2 micros arriesgando $60-$80 por operación garantizan longevidad.",
    filePath: "docs/tradesfera/04_PROTOCOLO_INTELIGENTE_APROBACION_CUENTAS.md",
    highlights: [
      "Dimensionamiento óptimo de micro-lotes para mantener el riesgo < 3% del DD.",
      "Ventanas de alta probabilidad de aprobación en 5 a 10 sesiones.",
      "Evitación de trampas de sobreoperativa en los últimos $300 hacia el target.",
    ],
  },
  {
    id: "05",
    number: "M05",
    title: "Sistema Multicuenta & Copytrading",
    category: "OPERATIVA",
    readTime: "16 min",
    summary: "Topología master-slave con NinjaTrader / Rithmic / Tradovate. Desincronización de milisegundos para evitar flags de copytrading.",
    keyRule: "Diversificar 20 cuentas entre 4 empresas (5 por firma) elimina el riesgo de impago individual de un prop broker.",
    filePath: "docs/tradesfera/05_SISTEMA_MULTICUENTA_Y_COPYTRADING.md",
    highlights: [
      "Topología de replicación 1:N en NinjaTrader y Tradovate.",
      "Control de deslizamiento (slippage) cruzado en contratos múltiples.",
      "Descentralización de brokers para inmunidad ante cambios unilaterales de reglas.",
    ],
  },
  {
    id: "06",
    number: "M06",
    title: "Ciclo Óptimo de Retiros & Payouts",
    category: "OPERATIVA",
    readTime: "14 min",
    summary: "Calendario de transferencias bancarias semanales rotativas entre 4 a 6 firmas complementarias.",
    keyRule: "Regla 80/20: 80% del payout va a patrimonio bancario seguro; 20% a la Caja de Munición para recomprar exámenes.",
    filePath: "docs/tradesfera/06_CICLO_OPTIMO_RETIROS_Y_PAYOUTS.md",
    highlights: [
      "Calendario escalonado de solicitudes de retiro semanales y quincenales.",
      "Mantenimiento del colchón mínimo de seguridad antes de solicitar el payout.",
      "Transición sistemática de ganancias a cuentas bancarias personales.",
    ],
  },
  {
    id: "07",
    number: "M07",
    title: "Psicología del Fondeo & Sesgos Operativos",
    category: "PSICOTRADING",
    readTime: "20 min",
    summary: "Neurobiología del trader, erradicación de la falacia de los $50,000 nominales y protocolos de reseteo del córtex prefrontal.",
    keyRule: "Una cuenta de $50k con drawdown de $2,000 tiene SOLO $2,000 de capital real. Tu apalancamiento real es 25x mayor.",
    filePath: "docs/tradesfera/07_PSICOLOGIA_DEL_FONDEO_Y_SESGOS_OPERATIVOS.md",
    highlights: [
      "Desmitificación del capital nominal: el capital real es el colchón de DD.",
      "Erradicación del sesgo de anclaje y aversión a la pérdida.",
      "Protocolo de respiración y desconexión tras pérdida inesperada.",
    ],
  },
  {
    id: "08",
    number: "M08",
    title: "Comparativa Prop Firms Futuros CME",
    category: "DOCTRINA",
    readTime: "15 min",
    summary: "Análisis forense de MyFundedFutures, Tradeify, TradeDay, BluSky, Lucid, Apex, Topstep, TakeProfitTrader y Bulenox.",
    keyRule: "Priorizar firmas con trailing EOD estricto y sin activación oculta: Tradeify y MyFundedFutures lideran el ranking.",
    filePath: "docs/tradesfera/08_COMPARATIVA_PROP_FIRMS_FUTUROS_CME.md",
    highlights: [
      "Desglose de costes ocultos: cuotas de activación y data feeds.",
      "Evaluación del modelo de negocio de cada prop firm (B-Book vs Real).",
      "Clasificación cuantitativa según idoneidad para bots y algoritmos.",
    ],
  },
  {
    id: "09",
    number: "M09",
    title: "Infraestructura Técnica NinjaTrader Tools",
    category: "EJECUCIÓN",
    readTime: "18 min",
    summary: "VPS de baja latencia en Chicago (CME Aurora), configuración de brackets automáticos y conexión multi-gateway.",
    keyRule: "Configuración obligatoria de Hard Stop Loss en el servidor del broker antes de enviar la orden de mercado.",
    filePath: "docs/tradesfera/09_INFRAESTRUCTURA_TECNICA_NINJATRADER_TOOLS.md",
    highlights: [
      "VPS en Chicago < 2ms de latencia hacia servidores CME Aurora.",
      "ATM Strategies con Brackets OCO incondicionales del lado del servidor.",
      "Puentes de replicación RDL y NinjaTrader Trade Copier.",
    ],
  },
  {
    id: "10",
    number: "M10",
    title: "Dossier Maestro: Tratado Integral Tradesfera",
    category: "DOCTRINA",
    readTime: "30 min",
    summary: "Tratado general que unifica los 16 módulos: microestructura cuantitativa, psicoterapia y marco de ejecución.",
    keyRule: "El sistema cuantitativo Tradesfera eleva la tasa de fondeo de la industria del 2.5% a un 26.6% auditado.",
    filePath: "docs/tradesfera/10_DOSSIER_MAESTRO_TRADESFERA_FONDEO_FUTUROS.md",
    highlights: [
      "Compendio maestro que integra la matemática, psicología y operativa.",
      "Estadísticas agregadas de 1,200+ traders auditados.",
      "Roadmap de principiante a gestor multicuenta de 20 cuentas CME.",
    ],
  },
  {
    id: "11",
    number: "M11",
    title: "Estrategias & Horarios Gerard García",
    category: "EJECUCIÓN",
    readTime: "16 min",
    summary: "Ventanas de liquidez institucional CME (08:30–11:00 EST / 14:30–17:00 CET), aperturas de sesión y patrones de absorción.",
    keyRule: "El 80% del profit se produce en los primeros 45 minutos tras la campana de Wall Street. Prohibido operar fuera de ventana.",
    filePath: "docs/tradesfera/11_ESTRATEGIAS_Y_HORARIOS_GERARD_GARCIA_FUTUROS.md",
    highlights: [
      "Patrón de Apertura ORB (Opening Range Breakout) de 15 minutos en NQ.",
      "Gestión de noticias económicas de alto impacto (NFP, CPI, FOMC).",
      "Filtros de absorción de volumen institucional en niveles clave.",
    ],
  },
  {
    id: "12",
    number: "M12",
    title: "Maestría Psicológica (El Psicólogo del Trading)",
    category: "PSICOTRADING",
    readTime: "22 min",
    summary: "Protocolos clínicos de Víctor Corrales (@Elpsicologodeltrading): parada de pensamiento, desensibilización sistemática y diario de tilt.",
    keyRule: "Ante 2 pérdidas consecutivas en el día: cierre automático de plataforma por 24 horas sin excepción.",
    filePath: "docs/tradesfera/12_MAESTRIA_PSICOLOGICA_Y_PROTOCOLOS_EL_PSICOLOGO_DEL_TRADING.md",
    highlights: [
      "Técnica de parada de pensamiento ante el impulso de revancha (Revenge Trading).",
      "Registro de estado fisiológico y nivel de estrés pre-sesión.",
      "Desconexión física obligatoria tras alcanzar el límite de pérdida diaria.",
    ],
  },
  {
    id: "13",
    number: "M13",
    title: "Sistema Táctico de Máxima Extracción",
    category: "OPERATIVA",
    readTime: "18 min",
    summary: "Secuencia matemática de cobros por niveles, amortización del colchón de seguridad y transición a cuenta live real.",
    keyRule: "Cosechar el primer payout en cuanto se desbloquee el umbral mínimo; nunca dejar acumular capital en un prop broker.",
    filePath: "docs/tradesfera/13_SISTEMA_TACTICO_MAXIMA_EXTRACCION_POR_EMPRESA.md",
    highlights: [
      "Estrategia de amortización del coste de compra en el primer retiro.",
      "Reglas de escalado de contratos según colchón acumulado.",
      "Plan de retiro por etapas (Tier 1 a Tier 4) en cada prop firm.",
    ],
  },
  {
    id: "14",
    number: "M14",
    title: "Hacks, Shorts & Reglas Rápidas de Fondeo",
    category: "EJECUCIÓN",
    readTime: "12 min",
    summary: "Cheat sheet de 25 reglas anti-descalificación: gestión de noticias NFP/FOMC, consistencia del 30% y micro-pips.",
    keyRule: "Comprobar el calendario económico 15 minutos antes de la sesión; cancelar todas las órdenes 2 minutos antes de noticias de alto impacto.",
    filePath: "docs/tradesfera/14_HACKS_SHORTS_Y_REGLAS_RAPIDAS_DE_FONDEO.md",
    highlights: [
      "Checklist de 25 reglas rápidas para evitar la descalificación instantánea.",
      "Regla de consistencia: ningún día puede superar el 30%-40% del profit total.",
      "Gestión de días mínimos obligatorios de trading sin arriesgar el target alcanzado.",
    ],
  },
  {
    id: "15",
    number: "M15",
    title: "Arbitraje de Negocio, Promos & Fiscalidad",
    category: "DOCTRINA",
    readTime: "16 min",
    summary: "Aprovechamiento de cupones del 80%-90%, deducción del coste de exámenes y tributación óptima como facturación de servicios.",
    keyRule: "Los payouts de prop firms se tributan como rendimiento de actividad económica / prestación de servicios, no como ganancia patrimonial directa.",
    filePath: "docs/tradesfera/15_ARBITRAJE_DE_NEGOCIO_PROMOS_Y_FISCALIDAD.md",
    highlights: [
      "Estructuración fiscal de cobros internacionales vía Wise / Deel / Cripto.",
      "Deducción de costes de exámenes, herramientas y datos de mercado.",
      "Aprovechamiento de cupones flash estacionales (Black Friday, New Year).",
    ],
  },
  {
    id: "16",
    number: "M16",
    title: "Playbook Operativo Diario & Checklist",
    category: "EJECUCIÓN",
    readTime: "10 min",
    summary: "Checklist de 7 pasos antes del primer click: conexión ping, sincronización de cuentas esclavas, nivel de drawdown y estado mental.",
    keyRule: "Si el checklist falla en un solo punto, la sesión queda cancelada automáticamente.",
    filePath: "docs/tradesfera/16_PLAYBOOK_OPERATIVO_DIARIO_Y_CHECKLIST_EJECUCION.md",
    highlights: [
      "7 pasos de verificación técnica antes del campanazo de apertura.",
      "Comprobación de conectividad Rithmic / Tradovate / CQG.",
      "Protocolo de cierre formal y registro en el diario de trading.",
    ],
  },
];

export default function TradesferaPortalPage() {
  const [selectedModule, setSelectedModule] = useState<ModuleMeta>(TRADESFERA_MODULES[0]);
  const [activeCategory, setActiveCategory] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [copiedPath, setCopiedPath] = useState<boolean>(false);

  // Bankroll Calculator state
  const [bankroll, setBankroll] = useState<number>(3000);
  const [examCost, setExamCost] = useState<number>(38.5);
  const [passRate, setPassRate] = useState<number>(26.6);
  const [payoutTarget, setPayoutTarget] = useState<number>(2500);

  const numBullets = Math.max(1, Math.floor(bankroll / Math.max(1, examCost)));
  const p = passRate / 100;
  const passProb = 1 - Math.pow(1 - p, numBullets);
  const expectedValue = passProb * payoutTarget - bankroll;

  const filteredModules = activeCategory === "ALL"
    ? TRADESFERA_MODULES
    : TRADESFERA_MODULES.filter((m) => m.category === activeCategory);

  const handleCopyCode = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText("TRADESFERA");
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleCopyPath = (path: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(path);
      setCopiedPath(true);
      setTimeout(() => setCopiedPath(false), 2000);
    }
  };

  const handleOpenModule = (mod: ModuleMeta) => {
    setSelectedModule(mod);
    setIsModalOpen(true);
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-8 pb-24 text-slate-100">
      {/* 1. HERO INSTITUCIONAL TRADESFERA */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-2xl space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-3 py-1 rounded-full text-xs font-mono font-black bg-amber-500/10 border border-amber-500/30 text-amber-400">
                TRATADO MAESTRO V2
              </span>
              <span className="text-xs font-mono text-slate-400">
                FUTUROS CME · METODOLOGÍA CUANTITATIVA TRADESFERA
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                167.000€+ AUDITADOS
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Portal Maestro Tradesfera: Sistema Inteligente de Extracción de Capital
            </h1>

            <p className="text-sm text-slate-300 leading-relaxed">
              Síntesis cuantitativa del tratado integral de 16 módulos: matemática de bankroll munición, varianza y control de drawdown EOD, psicotrading clínico y arquitectura multicuenta de futuros CME.
            </p>
          </div>

          {/* Quick Metrics & Links */}
          <div className="flex flex-wrap sm:flex-nowrap gap-3 shrink-0">
            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 text-center min-w-[130px]">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Tasa Auditada</span>
              <div className="text-2xl font-black text-emerald-400 font-mono tabular-nums">26.6%</div>
              <span className="text-[10px] text-slate-500 block">vs 2.5% industria</span>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 text-center min-w-[130px]">
              <span className="text-[10px] text-slate-400 uppercase font-mono block">Corpus en Disco</span>
              <div className="text-2xl font-black text-sky-400 font-mono tabular-nums">16 Módulos</div>
              <span className="text-[10px] text-slate-500 block">Dossier integral</span>
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-800/80">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/prop-firms"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-lg shadow-amber-500/20"
            >
              <Building2 className="w-4 h-4" />
              <span>Ver Catálogo 70 Prop Firms CME</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <Link
              href="/trading-desk"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 transition shadow-sm"
            >
              <Zap className="w-4 h-4 text-emerald-400" />
              <span>Abrir Trading Desk</span>
            </Link>

            <Link
              href="/ultra"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-pink-950/80 hover:bg-pink-900 text-pink-300 border border-pink-700/60 transition shadow-sm"
            >
              <Flame className="w-4 h-4 text-pink-400" />
              <span>Trading Desk Ultra</span>
            </Link>
          </div>

          {/* Coupon Copy Pill */}
          <div className="flex items-center gap-2 bg-slate-950/90 border border-amber-500/30 rounded-xl px-3 py-1.5">
            <span className="text-[11px] text-slate-400 font-mono">Cupón Oficial Unificado:</span>
            <button
              onClick={handleCopyCode}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 font-mono text-xs font-black border border-amber-500/40 transition"
              title="Copiar cupón TRADESFERA"
            >
              {copiedCode ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-amber-400" />}
              <span>{copiedCode ? "¡Copiado!" : "TRADESFERA"}</span>
            </button>
            <span className="text-[10px] text-emerald-400 font-mono font-bold">(50%-90% OFF)</span>
          </div>
        </div>
      </div>

      {/* 2. LAS 4 PUERTAS DEL ECOSISTEMA TRADESFERA */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-mono font-bold text-slate-400 tracking-wider uppercase">
              ARQUITECTURA DE LAS 4 PUERTAS TRADESFERA
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Infraestructura integral diseñada por Vicente Pons para maximizar la asimetría positiva en futuros regulados.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Puerta 1 */}
          <div className="bg-[#090d16]/90 border border-white/[0.08] hover:border-amber-500/40 backdrop-blur-xl rounded-2xl p-5 shadow-lg transition-all space-y-3 group">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center text-xs font-black font-mono">
                1
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-amber-300 transition">
                Descuentos Centralizados
              </h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Convenio unificado con las mejores prop firms de futuros CME con código <code className="text-amber-300 bg-amber-950/40 px-1 py-0.5 rounded font-mono font-bold">TRADESFERA</code> (50%-90% OFF).
            </p>
            <div className="text-[11px] text-emerald-400 font-mono pt-2 border-t border-slate-800/80">
              Tradeify · MyFundedFutures · TradeDay
            </div>
          </div>

          {/* Puerta 2 */}
          <div className="bg-[#090d16]/90 border border-white/[0.08] hover:border-sky-500/40 backdrop-blur-xl rounded-2xl p-5 shadow-lg transition-all space-y-3 group">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center text-xs font-black font-mono">
                2
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition">
                Sistema de Ticks
              </h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Acumulación de Ticks por cada examen adquirido, canjeables por cuentas gratuitas, reseteos y herramientas operativas en NinjaTrader.
            </p>
            <div className="text-[11px] text-sky-400 font-mono pt-2 border-t border-slate-800/80">
              account.tradesfera.com
            </div>
          </div>

          {/* Puerta 3 */}
          <div className="bg-[#090d16]/90 border border-white/[0.08] hover:border-purple-500/40 backdrop-blur-xl rounded-2xl p-5 shadow-lg transition-all space-y-3 group">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400 flex items-center justify-center text-xs font-black font-mono">
                3
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-purple-300 transition">
                Comunidad Auditada
              </h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Canal privado de Telegram con operativa en directo de Gerard García, análisis de mercado diario y soporte de psicotrading clínico.
            </p>
            <div className="text-[11px] text-purple-400 font-mono pt-2 border-t border-slate-800/80">
              Comunidad de Operadores CME
            </div>
          </div>

          {/* Puerta 4 */}
          <div className="bg-[#090d16]/90 border border-white/[0.08] hover:border-emerald-500/40 backdrop-blur-xl rounded-2xl p-5 shadow-lg transition-all space-y-3 group">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center text-xs font-black font-mono">
                4
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-emerald-300 transition">
                Public Ledger Auditado
              </h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              Libro mayor público con más de 167,000€ en transferencias de retiros reales certificados sin sesgos de supervivencia.
            </p>
            <div className="text-[11px] text-emerald-400 font-mono pt-2 border-t border-slate-800/80">
              167.000€+ Retiros Certificados
            </div>
          </div>
        </div>
      </div>

      {/* 3. CALCULADORA DE BANKROLL DE MUNICIÓN (MATEMÁTICA TRADESFERA M02) */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 md:p-8 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-black text-white tracking-tight">
                Calculadora Cuantitativa de Munición & Esperanza Matemática (M02)
              </h2>
              <p className="text-xs text-slate-400">
                Aplica la distribución binomial estocástica y la regla de cosecha 80/20 para calcular la probabilidad de cobro y EV neto.
              </p>
            </div>
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-bold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Fórmula Canónica M02</span>
          </div>
        </div>

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <label className="text-[11px] font-bold text-slate-400 uppercase font-mono block">
              Bankroll Total de Fondeo ($):
            </label>
            <input
              type="number"
              value={bankroll}
              onChange={(e) => setBankroll(Math.max(10, Number(e.target.value)))}
              className="w-full bg-[#030712] text-white border border-slate-700/80 rounded-lg px-3 py-2 text-sm font-bold font-mono focus:border-sky-500 focus:outline-none"
            />
            <span className="text-[10px] text-slate-500 block font-mono">
              Capital disponible para comprar exámenes
            </span>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <label className="text-[11px] font-bold text-slate-400 uppercase font-mono block">
              Coste Examen con Promo ($):
            </label>
            <input
              type="number"
              step="0.5"
              value={examCost}
              onChange={(e) => setExamCost(Math.max(1, Number(e.target.value)))}
              className="w-full bg-[#030712] text-white border border-slate-700/80 rounded-lg px-3 py-2 text-sm font-bold font-mono focus:border-sky-500 focus:outline-none"
            />
            <span className="text-[10px] text-slate-500 block font-mono">
              ej. MFFU $38.50 o Tradeify $49.00
            </span>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <label className="text-[11px] font-bold text-slate-400 uppercase font-mono block">
              Tasa Aprobación Individual (%):
            </label>
            <input
              type="number"
              step="0.1"
              value={passRate}
              onChange={(e) => setPassRate(Math.min(100, Math.max(0.1, Number(e.target.value))))}
              className="w-full bg-[#030712] text-white border border-slate-700/80 rounded-lg px-3 py-2 text-sm font-bold font-mono focus:border-sky-500 focus:outline-none"
            />
            <span className="text-[10px] text-slate-500 block font-mono">
              Tasa Tradesfera Auditada: 26.6%
            </span>
          </div>

          <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-2">
            <label className="text-[11px] font-bold text-slate-400 uppercase font-mono block">
              Objetivo Payout Neto ($):
            </label>
            <input
              type="number"
              step="100"
              value={payoutTarget}
              onChange={(e) => setPayoutTarget(Math.max(100, Number(e.target.value)))}
              className="w-full bg-[#030712] text-white border border-slate-700/80 rounded-lg px-3 py-2 text-sm font-bold font-mono focus:border-sky-500 focus:outline-none"
            />
            <span className="text-[10px] text-slate-500 block font-mono">
              Retiro proyectado en 1ª fase
            </span>
          </div>
        </div>

        {/* Results Bar */}
        <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Disparos / Balas (N)</span>
            <div className="text-2xl font-black text-white font-mono tabular-nums">
              {numBullets} {numBullets === 1 ? "bala" : "balas"}
            </div>
            <span className="text-[10px] text-slate-500 block font-mono">Intentos garantizados</span>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Prob. Aprobar ≥ 1</span>
            <div
              className={`text-2xl font-black font-mono tabular-nums ${
                passProb >= 0.9 ? "text-emerald-400" : passProb >= 0.7 ? "text-sky-400" : "text-amber-400"
              }`}
            >
              {(passProb * 100).toFixed(1)}%
            </div>
            <span className="text-[10px] text-slate-500 block font-mono">
              {passProb >= 0.95 ? "✓ Certeza estadística" : "Riesgo de varianza"}
            </span>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Esperanza Matemática (EV)</span>
            <div
              className={`text-2xl font-black font-mono tabular-nums ${
                expectedValue > 0 ? "text-emerald-400" : "text-rose-400"
              }`}
            >
              {expectedValue > 0 ? "+" : ""}${expectedValue.toFixed(2)}
            </div>
            <span className="text-[10px] text-slate-500 block font-mono">Retorno neto esperado</span>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-slate-400 uppercase font-mono block">Cosecha Regla 80/20</span>
            <div className="text-base font-bold text-amber-300 font-mono tabular-nums mt-1">
              ${(payoutTarget * 0.8).toFixed(0)} <span className="text-xs text-slate-400 font-normal">Banco</span> / ${(payoutTarget * 0.2).toFixed(0)} <span className="text-xs text-slate-400 font-normal">Caja</span>
            </div>
            <span className="text-[10px] text-slate-500 block font-mono">Preservación de capital</span>
          </div>
        </div>

        {/* Visual Probability Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-mono text-slate-400">
            <span>Barra de Seguridad Estadística (Probabilidad Acumulada):</span>
            <span className="font-bold text-white">{(passProb * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-500 rounded-full ${
                passProb >= 0.9
                  ? "bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-sm shadow-emerald-500/50"
                  : passProb >= 0.7
                  ? "bg-gradient-to-r from-sky-600 to-sky-400"
                  : "bg-gradient-to-r from-amber-600 to-amber-400"
              }`}
              style={{ width: `${Math.min(100, Math.max(2, passProb * 100))}%` }}
            />
          </div>
        </div>
      </div>

      {/* 4. EXPLORADOR INTERACTIVO DE LOS 16 MÓDULOS */}
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-sky-400" />
              <h2 className="text-xl font-black text-white tracking-tight">
                Corpus Documental Especializado (16 Módulos en Disco)
              </h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Haz clic en cualquier módulo para ver su ficha técnica, regla de oro, highlights y ruta de archivo exacta.
            </p>
          </div>

          {/* Category Filter Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 bg-[#090d16]/90 border border-white/[0.08] p-1.5 rounded-xl">
            {["ALL", "DOCTRINA", "MATEMÁTICA", "OPERATIVA", "PSICOTRADING", "EJECUCIÓN"].map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                  activeCategory === cat
                    ? "bg-sky-500 text-slate-950 font-black shadow-md shadow-sky-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredModules.map((mod) => {
            const isSelected = selectedModule.id === mod.id;
            return (
              <div
                key={mod.id}
                onClick={() => handleOpenModule(mod)}
                className={`bg-[#090d16]/90 border backdrop-blur-xl rounded-2xl p-5 shadow-lg transition-all cursor-pointer flex flex-col justify-between space-y-4 group ${
                  isSelected
                    ? "border-sky-500 shadow-sky-500/10 ring-1 ring-sky-500/30"
                    : "border-white/[0.08] hover:border-sky-500/40 hover:shadow-xl hover:shadow-sky-500/5"
                }`}
              >
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded-md bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-bold">
                      {mod.number}
                    </span>
                    <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {mod.readTime}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-white group-hover:text-sky-300 transition-colors leading-snug">
                    {mod.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {mod.summary}
                  </p>
                </div>

                <div className="space-y-3">
                  {/* Key Rule Box */}
                  <div className="bg-slate-950/80 border-l-2 border-amber-400 p-2.5 rounded-r-lg text-xs text-slate-300 italic font-sans leading-tight">
                    &quot;{mod.keyRule}&quot;
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 pt-2 border-t border-slate-800/80">
                    <span className="text-sky-400/80">{mod.category}</span>
                    <span className="group-hover:text-white flex items-center gap-1 transition">
                      <span>Ver Ficha</span>
                      <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 5. MODAL DETALLE DE MÓDULO */}
      {isModalOpen && selectedModule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="bg-[#090d16] border border-sky-500/40 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-6">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-md bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-bold">
                    {selectedModule.number}
                  </span>
                  <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">
                    {selectedModule.category} · {selectedModule.readTime}
                  </span>
                </div>
                <h3 className="text-lg font-black text-white">
                  {selectedModule.title}
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Summary */}
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                Resumen Ejecutivo:
              </h4>
              <p className="text-sm text-slate-200 leading-relaxed">
                {selectedModule.summary}
              </p>
            </div>

            {/* Key Rule */}
            <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl p-4 space-y-1">
              <span className="text-xs font-mono font-black text-amber-400 uppercase tracking-wider block">
                Regla de Oro Inquebrantable:
              </span>
              <p className="text-xs text-amber-200/90 italic font-medium leading-relaxed">
                &quot;{selectedModule.keyRule}&quot;
              </p>
            </div>

            {/* Highlights Checklist */}
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                Conceptos Clave & Protocolos:
              </h4>
              <div className="space-y-1.5">
                {selectedModule.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* File Path Reference */}
            <div className="bg-slate-950 rounded-xl border border-slate-800 p-3.5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-slate-400">Ruta de Documento en Disco:</span>
                <button
                  onClick={() => handleCopyPath(selectedModule.filePath)}
                  className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-sky-400 hover:text-sky-300 transition"
                >
                  {copiedPath ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedPath ? "Copiado" : "Copiar Ruta"}</span>
                </button>
              </div>
              <code className="text-xs text-emerald-400 font-mono block overflow-x-auto p-2 bg-[#030712] rounded border border-slate-800">
                {selectedModule.filePath}
              </code>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-mono font-bold bg-slate-800 hover:bg-slate-700 text-white transition"
              >
                Cerrar Ficha
              </button>
              <Link
                href="/prop-firms"
                className="px-4 py-2 rounded-xl text-xs font-mono font-black bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-lg shadow-amber-500/20 inline-flex items-center gap-1.5"
              >
                <span>Aplicar en Prop Firms</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
