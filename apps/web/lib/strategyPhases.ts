// apps/web/lib/strategyPhases.ts
// SSOT: Catálogo Unificado de Fases de Producto (UX) y Fases del Pipeline Cuantitativo v5.3.0

export interface StrategyPhase {
  id: number;
  name: string;
  label: string;
  shortLabel: string;
  icon: string;
  badge: string;
  color: string;
  description: string;
  canonicalRoute: string;
  legacyRoutes: string[];
}

export interface PipelineStage {
  stageNumber: number;
  key: string;
  name: string;
  description: string;
  evidenceGateRequirement: string;
}

/**
 * PRODUCT_PHASES: Las 6 Vistas Sincronizadas del Frontend (UX / Operativa).
 */
export const PRODUCT_PHASES: StrategyPhase[] = [
  {
    id: 0,
    name: "Portada General de Estrategias",
    label: "Portada General",
    shortLabel: "0. Portada",
    icon: "🧬",
    badge: "GLOBAL",
    color: "#63e1b4",
    description: "Centro de mando integral del laboratorio cuantitativo, KPIs consolidados y acceso a las 6 fases.",
    canonicalRoute: "/estrategias",
    legacyRoutes: [],
  },
  {
    id: 1,
    name: "Fase 1: Supervisor 24/7 & Telemetría",
    label: "Fase 1: Supervisor 24/7",
    shortLabel: "1. Supervisor",
    icon: "⚡",
    badge: "24/7 SSE",
    color: "#10b981",
    description: "Monitorización de los 8 workers en tiempo real, eventos SSE y consola de telemetría física.",
    canonicalRoute: "/estrategias/1-motor-en-vivo",
    legacyRoutes: ["/sistema", "/panel"],
  },
  {
    id: 2,
    name: "Fase 2: Catálogo & Familias Cuánticas",
    label: "Fase 2: Catálogo & Familias",
    shortLabel: "2. Catálogo",
    icon: "📊",
    badge: "FAMILIAS",
    color: "#38bdf8",
    description: "Exploración de estrategias generadas, desglose por familias y ejecución real en FastEngine.",
    canonicalRoute: "/estrategias/2-explorador-excel",
    legacyRoutes: ["/strategies"],
  },
  {
    id: 3,
    name: "Fase 3: Pipeline 11 Quality Gates & FSM",
    label: "Fase 3: Pipeline 11 Gates",
    shortLabel: "3. 11 Gates",
    icon: "🚦",
    badge: "11 GATES",
    color: "#818cf8",
    description: "Auditoría en 11 compuertas matemáticas estrictas, WFE, Monte Carlo y debate de consenso.",
    canonicalRoute: "/estrategias/3-pipeline-11-gates",
    legacyRoutes: ["/gates", "/candidatos"],
  },
  {
    id: 4,
    name: "Fase 4: Research Semántico & Failure Knowledge",
    label: "Fase 4: Research Lab",
    shortLabel: "4. Research Lab",
    icon: "🔬",
    badge: "AI LOOP",
    color: "#ec4899",
    description: "Base de datos de autopsias de fallos, mutación genética y optimización guiada por microestructura.",
    canonicalRoute: "/estrategias/4-panel-investigador",
    legacyRoutes: ["/research"],
  },
  {
    id: 5,
    name: "Fase 5: Estrategias Certificadas (Motor Actual)",
    label: "Fase 5: Aprobadas",
    shortLabel: "5. Aprobadas",
    icon: "🛡️",
    badge: "APPROVED v5.3.0",
    color: "#facc15",
    description: "Exclusivamente estrategias con 11/11 gates aprobados bajo el motor actual y ledger verificado.",
    canonicalRoute: "/estrategias/5-estrategias-aprobadas",
    legacyRoutes: ["/leaderboard"],
  },
  {
    id: 6,
    name: "Fase 6: Meta-Estrategia & Cartera Multi-Activo",
    label: "Fase 6: Portfolio Studio",
    shortLabel: "6. Meta-Portfolio",
    icon: "🌌",
    badge: "MULTI-AGENTE",
    color: "#a855f7",
    description: "Carteras de componentes 100% certificados, aislamiento multi-activo (cero colisión) y ledger propio.",
    canonicalRoute: "/estrategias/6-meta-estrategia",
    legacyRoutes: ["/portfolio"],
  },
];

// Alias para compatibilidad hacia atrás
export const STRATEGY_PHASES = PRODUCT_PHASES;

/**
 * QUANT_PIPELINE_PHASES: Etapas del Pipeline Cuantitativo Interno.
 */
export const QUANT_PIPELINE_PHASES: PipelineStage[] = [
  {
    stageNumber: 1,
    key: "GENERATION",
    name: "1. Generación Cuántica & Discovery",
    description: "Generación de hipótesis y extracción de series de precios.",
    evidenceGateRequirement: "Dataset Ingest & Integrity SHA-256",
  },
  {
    stageNumber: 2,
    key: "NORMALIZATION",
    name: "2. Normalización AST & Compilación Canónica",
    description: "Validación de sintaxis, reglas y asignación de perfil de costes real.",
    evidenceGateRequirement: "Cost Profile & Gate 02 Check",
  },
  {
    stageNumber: 3,
    key: "BACKTEST_IS_OOS",
    name: "3. Backtest Aislado IS / OOS",
    description: "Ejecución sobre Universal Engine con particionado temporal físico sin data-leakage.",
    evidenceGateRequirement: "Canonical Execution Ledger & Merkle Hash",
  },
  {
    stageNumber: 4,
    key: "QUALITY_FABRIC",
    name: "4. Evaluación 11 Quality Gates",
    description: "Evaluación estadística estricta (WFE, Monte Carlo, DSR, Regímenes, Debate).",
    evidenceGateRequirement: "11/11 Gates Pass + EvidenceBundle",
  },
  {
    stageNumber: 5,
    key: "INCUBATION",
    name: "5. Incubación & Paper Forward",
    description: "Verificación en tiempo real sin riesgo financiero.",
    evidenceGateRequirement: "Live Drift < 15% vs OOS Expectation",
  },
  {
    stageNumber: 6,
    key: "LIVE_PORTFOLIO",
    name: "6. Asignación a Cartera Multi-Activo",
    description: "Ponderación por paridad de riesgo y ejecución live con ordenación atómica.",
    evidenceGateRequirement: "Non-overlapping Symbol Portfolio Ledger",
  },
];
