/**
 * apps/web/lib/strategyPhases.ts
 * Catálogo Canónico de Fases Cuantitativas (FSM 6 Fases Deterministas)
 * ZERO MOCKS · REAL-ONLY
 */

export interface StrategyPhase {
  id: number;
  name: string;
  label: string;
  shortLabel: string;
  canonicalRoute: string;
  legacyRoutes?: string[];
  icon: string;
  badge: string;
  color: string;
  description?: string;
}

export const STRATEGY_PHASES: StrategyPhase[] = [
  {
    id: 1,
    name: "Motor 24/7 Autónomo",
    label: "1. Motor 24/7 Autónomo",
    shortLabel: "Motor 24/7",
    canonicalRoute: "/strategies",
    legacyRoutes: ["/estrategias/1-motor-en-vivo"],
    icon: "⚡",
    badge: "FASTENGINE",
    color: "#38bdf8",
    description: "Generación autónoma y backtest físico trade-a-trade.",
  },
  {
    id: 2,
    name: "Catálogo de Candidatos",
    label: "2. Catálogo de Candidatos (230)",
    shortLabel: "Candidatos",
    canonicalRoute: "/strategies",
    legacyRoutes: ["/estrategias/2-explorador-excel"],
    icon: "📊",
    badge: "230 CAND",
    color: "#818cf8",
    description: "Exploración de candidatos con métricas en SQLite WAL.",
  },
  {
    id: 3,
    name: "Pipeline 10 Gates",
    label: "3. Pipeline 10 Gates (FSM)",
    shortLabel: "10 Gates",
    canonicalRoute: "/gates",
    legacyRoutes: ["/estrategias/3-pipeline-11-gates"],
    icon: "🧬",
    badge: "10-GATES",
    color: "#63e1b4",
    description: "Matriz de compuertas cuantitativas y pruebas de robustez.",
  },
  {
    id: 4,
    name: "Panel Investigador Semántico",
    label: "4. Panel Investigador Semántico",
    shortLabel: "Lab I+D",
    canonicalRoute: "/strategies",
    legacyRoutes: ["/estrategias/4-panel-investigador"],
    icon: "🔬",
    badge: "LAB I+D",
    color: "#f59e0b",
    description: "Auditoría semántica e investigación de anomalías.",
  },
  {
    id: 5,
    name: "Estrategias Aprobadas (10/10)",
    label: "5. Estrategias Aprobadas (10/10)",
    shortLabel: "Certificadas",
    canonicalRoute: "/gates",
    legacyRoutes: ["/estrategias/5-estrategias-aprobadas"],
    icon: "🏆",
    badge: "CERTIFICADAS",
    color: "#10b981",
    description: "Estrategias certificadas bajo el motor v5.3.0.",
  },
  {
    id: 6,
    name: "Meta-Estrategia Ensamblada",
    label: "6. Meta-Estrategia Ensamblada",
    shortLabel: "Portfolio",
    canonicalRoute: "/portfolio",
    legacyRoutes: ["/estrategias/6-meta-estrategia"],
    icon: "🧩",
    badge: "PORTFOLIO",
    color: "#a855f7",
    description: "Ensamblaje y optimización de meta-portafolios multiactivo.",
  },
];
