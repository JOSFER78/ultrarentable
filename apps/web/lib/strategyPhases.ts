// apps/web/lib/strategyPhases.ts
// FUENTE ÚNICA DE VERDAD de las 6 fases del pipeline de estrategias (+ portada/hub).
// Toda página, nav o hub que necesite las fases DEBE consumir este catálogo.
// Prohibido re-declarar fases, badges, rutas o labels en componentes/páginas.
// DOCTRINA ZERO-MOCKS: los labels no contienen métricas hardcodeadas (p.ej. "230 candidatos")
// porque las métricas viven en el backend y cambian; si cambian aquí, se desincronizan.

export const CANONICAL_GATES_COUNT = 10;

export interface StrategyPhase {
  /** 0 = portada/hub global; 1-6 = fases del pipeline */
  id: number;
  key: string;
  /** Nombre largo canónico */
  label: string;
  shortLabel: string;
  description: string;
  icon: string;
  badge: string;
  color: string;
  /** Ruta canónica de la fase (solo fases 1-6) */
  route?: string;
  /** Rutas legadas que representan la misma fase (deben ser redirect/alias, nunca implementación paralela) */
  legacyRoutes?: string[];
}

export const STRATEGY_PHASES: StrategyPhase[] = [
  {
    id: 0,
    key: "portada",
    label: "0. Portada & Panel General de Estrategias",
    shortLabel: "Portada General",
    description: "Visión panorámica global, KPIs consolidados (solo desde telemetría real), embudo de 6 etapas y estado de las 6 fases del sistema.",
    icon: "🗺️",
    badge: "HUB GLOBAL",
    color: "#63e1b4",
  },
  {
    id: 1,
    key: "motor",
    label: "1. Motor Cuantitativo 24/7 en Vivo & Supervisión",
    shortLabel: "1. Motor 24/7",
    description: "Monitoreo en tiempo real de la minería continua (FastEngine 24/7 + SQX Bridge), pool de workers y supervisión de datos.",
    icon: "⚡",
    badge: "24/7",
    color: "#34d399",
    route: "/estrategias/1-motor-en-vivo",
    legacyRoutes: ["/panel", "/sistema"],
  },
  {
    id: 2,
    key: "catalogo",
    label: "2. Catálogo y Explorador Cuantitativo",
    shortLabel: "2. Catálogo",
    description: "Explorador de estrategias con filtros por activo, temporalidad, métricas OOS, Scorecards, DNA y exportador C# / Pine.",
    icon: "📊",
    badge: "CATÁLOGO",
    color: "#38bdf8",
    route: "/estrategias/2-explorador-excel",
    legacyRoutes: ["/strategies"],
  },
  {
    id: 3,
    key: "pipeline",
    label: `3. Pipeline ${CANONICAL_GATES_COUNT} Gates (FSM & Gates Institucionales)`,
    shortLabel: `3. Pipeline ${CANONICAL_GATES_COUNT}-G`,
    description: `Evaluación rigurosa a través de los ${CANONICAL_GATES_COUNT} Gates matemáticos deterministas de control de calidad y robustez.`,
    icon: "🧬",
    badge: `${CANONICAL_GATES_COUNT} GATES`,
    color: "#818cf8",
    route: "/estrategias/3-pipeline-10-gates",
    legacyRoutes: ["/estrategias/3-pipeline-11-gates", "/candidatos", "/pasos"],
  },
  {
    id: 4,
    key: "investigador",
    label: "4. Panel Investigador Semántico (Laboratorio I+D)",
    shortLabel: "4. Lab I+D",
    description: "Análisis semántico de fallos, base de conocimiento de sobreajuste y bucle de mejora continua de estrategias.",
    icon: "🔬",
    badge: "LAB I+D",
    color: "#facc15",
    route: "/estrategias/4-panel-investigador",
    legacyRoutes: ["/research", "/backtest"],
  },
  {
    id: 5,
    key: "aprobadas",
    label: `5. Estrategias Aprobadas (Certificación ${CANONICAL_GATES_COUNT} Gates)`,
    shortLabel: "5. Aprobadas",
    description: `Ranking oficial de estrategias que han superado los ${CANONICAL_GATES_COUNT} Gates con evidencia matemática completa.`,
    icon: "🏆",
    badge: "CERTIFICADAS",
    color: "#10b981",
    route: "/estrategias/5-estrategias-aprobadas",
    legacyRoutes: ["/gates", "/leaderboard"],
  },
  {
    id: 6,
    key: "portfolio",
    label: "6. Meta-Estrategia Ensamblada & Bóveda Ratchet",
    shortLabel: "6. Meta-Estrategia",
    description: "Ensamblaje de portafolios multiactivo no correlacionados, interés compuesto y protección de bóveda.",
    icon: "🧩",
    badge: "PORTFOLIO",
    color: "#ec4899",
    route: "/estrategias/6-meta-estrategia",
    legacyRoutes: ["/portfolio"],
  },
];

export const PIPELINE_PHASES = STRATEGY_PHASES.filter((p) => p.id > 0);
