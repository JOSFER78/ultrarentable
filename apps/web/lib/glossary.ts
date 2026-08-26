export interface GlossaryTerm {
  key: string;
  title: string;
  category: "rendimiento" | "riesgo" | "validacion" | "prop_firm" | "cripto_forex";
  whatIs: string;
  benchmark?: string;
  formula?: string;
  colorScheme?: "indigo" | "emerald" | "rose" | "sky" | "amber";
}

export const QUANT_GLOSSARY: Record<string, GlossaryTerm> = {
  sharpe_ratio: {
    key: "sharpe_ratio",
    title: "Sharpe Ratio",
    category: "rendimiento",
    whatIs: "¿Qué es? Mide cuánto ganas por cada unidad de riesgo (volatilidad de la cuenta).",
    benchmark: "Mayor a 1.5 es excelente (> 2.0 es nivel institucional).",
    formula: "Sharpe = (Retorno - Tasa Libre Riesgo) / Volatilidad",
    colorScheme: "indigo",
  },
  profit_factor: {
    key: "profit_factor",
    title: "Profit Factor (Factor de Beneficio)",
    category: "rendimiento",
    whatIs: "¿Qué es? Ratio directo entre los dólares ganados y los dólares perdidos.",
    benchmark: "Mayor a 1.3 es rentable; > 1.6 es muy robusto.",
    formula: "Profit Factor = Ganancias Brutas ($) / Pérdidas Brutas ($)",
    colorScheme: "emerald",
  },
  max_drawdown: {
    key: "max_drawdown",
    title: "Max Drawdown (Caída Máxima)",
    category: "riesgo",
    whatIs: "¿Qué es? La mayor caída temporal de la cuenta desde su punto más alto (pico) hasta su fondo.",
    benchmark: "< 5% ideal para Fondeo CME; < 10% para cuentas personales seguras.",
    formula: "Max DD (%) = ((Pico Máximo - Mínimo Posterior) / Pico) * 100",
    colorScheme: "rose",
  },
  oos: {
    key: "oos",
    title: "OOS (Out of Sample)",
    category: "validacion",
    whatIs: "¿Qué es? Datos del 'futuro' que la estrategia jamás vio durante su diseño para verificar que no esté trucada.",
    benchmark: "Mínimo 20% a 30% del historial reservado como OOS puro.",
    formula: "Validación estadística anti-sobreajuste (Walk-Forward)",
    colorScheme: "sky",
  },
  win_rate: {
    key: "win_rate",
    title: "Win Rate (Tasa de Acierto)",
    category: "rendimiento",
    whatIs: "¿Qué es? Porcentaje de operaciones cerradas en positivo sobre el total.",
    benchmark: "Sistemas tendenciales: 40-50% con grandes ganancias. Reversión: 60-70%.",
    formula: "Win Rate (%) = (Trades Ganadores / Total Trades) * 100",
    colorScheme: "emerald",
  },
  monte_carlo: {
    key: "monte_carlo",
    title: "Monte Carlo (Prueba de Ruina)",
    category: "validacion",
    whatIs: "¿Qué es? Simulación que baraja miles de veces el orden de los trades para ver si la cuenta puede quebrar en el peor escenario.",
    benchmark: "0.0% probabilidad de ruina con 95% de confianza.",
    formula: "Permutaciones Bootstrap de N trades (1,000 ejecuciones)",
    colorScheme: "amber",
  },
  merkle_provenance: {
    key: "merkle_provenance",
    title: "Sellado Criptográfico SHA-256",
    category: "validacion",
    whatIs: "¿Qué es? Firma digital inmutable de cada trade ejecutado en el motor físico (Zero-Mocks).",
    benchmark: "100% Determinista y reproducible en auditoría forense.",
    formula: "Hash = SHA256(Trades + Config + EngineVersion)",
    colorScheme: "sky",
  },
  cagr: {
    key: "cagr",
    title: "CAGR (Crecimiento Anual Compuesto)",
    category: "rendimiento",
    whatIs: "¿Qué es? Tasa de crecimiento anual estimada de la cuenta.",
    benchmark: "> 25% anual con Drawdown < 10% es grado inversión.",
    formula: "CAGR = (Capital Final / Capital Inicial)^(1/Años) - 1",
    colorScheme: "emerald",
  },
};