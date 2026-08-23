// apps/web/lib/strategyPhases.ts

export interface StrategyPhase {
  id: number;
  name: string;
  label?: string;
  shortLabel: string;
  icon: string;
  badge: string;
  color: string;
  description: string;
  routePath: string;
  route?: string;
  legacyRoutes?: string[];
}

export const STRATEGY_PHASES: StrategyPhase[] = [
  {
    id: 0,
    name: "Portada General de Estrategias",
    label: "Portada General",
    shortLabel: "0. Portada",
    icon: "🧬",
    badge: "GLOBAL",
    color: "#63e1b4",
    description: "Centro de mando integral del laboratorio cuantitativo, KPIs consolidados y acceso a las 6 fases.",
    routePath: "/estrategias",
    route: "/estrategias",
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
    description: "Monitorización de los 8 workers en tiempo real, eventos SSE y consola de autosanación.",
    routePath: "/sistema",
    route: "/sistema",
    legacyRoutes: ["/panel"],
  },
  {
    id: 2,
    name: "Fase 2: Catálogo & Familias Cuánticas",
    label: "Fase 2: Catálogo & Familias",
    shortLabel: "2. Catálogo",
    icon: "📊",
    badge: "FAMILIAS",
    color: "#38bdf8",
    description: "Exploración de estrategias generadas, desglose por familias y DSL paramétrico.",
    routePath: "/strategies",
    route: "/strategies",
    legacyRoutes: [],
  },
  {
    id: 3,
    name: "Fase 3: Candidatos & Máquina de Estados (FSM)",
    label: "Fase 3: Candidatos FSM",
    shortLabel: "3. Candidatos",
    icon: "🚦",
    badge: "10 ESTADOS",
    color: "#818cf8",
    description: "Ciclo de vida discreto de candidatos: GENERATED → BACKTESTED → CERTIFIED → LIVE.",
    routePath: "/candidatos",
    route: "/candidatos",
    legacyRoutes: [],
  },
  {
    id: 4,
    name: "Fase 4: Research Semántico & Failure Knowledge",
    label: "Fase 4: Research Lab",
    shortLabel: "4. Research Lab",
    icon: "🔬",
    badge: "AI LOOP",
    color: "#ec4899",
    description: "Base de datos de autopsias de fallos, mutación genética y reparación profunda con agentes.",
    routePath: "/research",
    route: "/research",
    legacyRoutes: [],
  },
  {
    id: 5,
    name: "Fase 5: Quality Gates & Evidence Gate Hub",
    label: "Fase 5: Quality Gates",
    shortLabel: "5. Gates & Auditor",
    icon: "🛡️",
    badge: "EVIDENCE GATE",
    color: "#facc15",
    description: "Auditoría en 11 compuertas matemáticas estrictas, Monte Carlo 5D y WFE.",
    routePath: "/gates",
    route: "/gates",
    legacyRoutes: [],
  },
  {
    id: 6,
    name: "Fase 6: Portfolio Studio & Debate Multi-Agente",
    label: "Fase 6: Portfolio Studio",
    shortLabel: "6. Meta-Portfolio",
    icon: "🌌",
    badge: "MULTI-AGENTE",
    color: "#a855f7",
    description: "Fusión de submáquinas ortogonales, paridad de riesgo ERC, correlación cruzada y debate entre los 5 agentes.",
    routePath: "/portfolio",
    route: "/portfolio",
    legacyRoutes: [],
  },
];

