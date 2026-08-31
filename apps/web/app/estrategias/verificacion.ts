/**
 * Capa de verificación de la página de estrategias.
 *
 * Mandato del usuario (2026-08-31): "DEBES ANALIZAR Y REVISAR Y COMPROBAR TODO LO QUE VEAS
 * EN LA WEB, NO DES NADA COMO VÁLIDO".
 *
 * Este módulo NO embellece datos: los audita antes de que lleguen a la pantalla. Un número
 * imposible no se muestra como si fuera un hecho — se marca y se explica por qué se rechaza.
 *
 * Hechos medidos sobre el catálogo real el 2026-08-31 (578 candidatas):
 *   - 6 con beneficio OOS > 10 millones de USD (una llegaba a 9,79e+26)
 *   - 136 con drawdown = 100 % (cuenta liquidada, no una estrategia)
 *   - 99 con profit factor > 50 o NaN
 *   - de las 27 APROBADAS: 0 con cifras imposibles
 */

export type Veredicto = "OK" | "NO_PLAUSIBLE" | "SIN_DATO";

export interface CampoVerificado {
  veredicto: Veredicto;
  valor: number | null;
  motivo?: string;
}

const num = (v: unknown): number | null => {
  if (v === null || v === undefined) return null;
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : null;
};

/** Beneficio neto: coherente con el capital de la ruta, no una cifra astronómica. */
export function verificarBeneficio(valor: unknown, capitalBase: number): CampoVerificado {
  const n = num(valor);
  if (n === null) return { veredicto: "SIN_DATO", valor: null };
  // Ni el sistema más convexo multiplica el capital por 10.000 en un tramo OOS.
  const techo = capitalBase * 10_000;
  if (Math.abs(n) > techo) {
    return {
      veredicto: "NO_PLAUSIBLE",
      valor: n,
      motivo: `${n.toExponential(2)} USD sobre un capital base de ${capitalBase.toLocaleString("es-ES")}. Desbordamiento de composición, no un resultado.`,
    };
  }
  return { veredicto: "OK", valor: n };
}

/** Profit factor: por encima de 50 no es un edge, es un artefacto de cálculo. */
export function verificarProfitFactor(valor: unknown): CampoVerificado {
  const n = num(valor);
  if (n === null) return { veredicto: "SIN_DATO", valor: null };
  if (n < 0) return { veredicto: "NO_PLAUSIBLE", valor: n, motivo: "Un profit factor no puede ser negativo." };
  if (n > 50) {
    return {
      veredicto: "NO_PLAUSIBLE",
      valor: n,
      motivo: `PF ${n.toFixed(1)}: por encima de 50 indica pérdidas brutas ≈ 0, típico de división por cero.`,
    };
  }
  return { veredicto: "OK", valor: n };
}

/** Drawdown: el 100 % significa cuenta liquidada; no es una métrica de calidad. */
export function verificarDrawdown(valor: unknown): CampoVerificado {
  const n = num(valor);
  if (n === null) return { veredicto: "SIN_DATO", valor: null };
  if (n >= 100) {
    return {
      veredicto: "NO_PLAUSIBLE",
      valor: n,
      motivo: "Drawdown del 100 %: la cuenta se liquidó. La estrategia no sobrevivió al tramo.",
    };
  }
  if (n < 0) return { veredicto: "NO_PLAUSIBLE", valor: n, motivo: "Un drawdown no puede ser negativo." };
  return { veredicto: "OK", valor: n };
}

/** Nº de operaciones: bajo esta cifra no hay estadística, hay anécdota. */
export function verificarMuestra(valor: unknown, minimo = 30): CampoVerificado {
  const n = num(valor);
  if (n === null) return { veredicto: "SIN_DATO", valor: null };
  if (n < minimo) {
    return {
      veredicto: "NO_PLAUSIBLE",
      valor: n,
      motivo: `${n} operaciones fuera de muestra: por debajo de ${minimo} el resultado no es significativo.`,
    };
  }
  return { veredicto: "OK", valor: n };
}

export interface AuditoriaCandidata {
  beneficio: CampoVerificado;
  profitFactor: CampoVerificado;
  drawdown: CampoVerificado;
  muestra: CampoVerificado;
  /** true si algún campo es imposible: la fila se marca en la tabla. */
  tieneProblemas: boolean;
  problemas: string[];
}

export function auditarCandidata(c: Record<string, unknown>): AuditoriaCandidata {
  const esUltra = String(c.route ?? "").toUpperCase() === "ULTRA";
  const capitalBase = esUltra ? 1_000 : 50_000;

  const beneficio = verificarBeneficio(c.net_profit_oos, capitalBase);
  const profitFactor = verificarProfitFactor(c.profit_factor_oos);
  const drawdown = verificarDrawdown(c.max_dd_oos_pct);
  const muestra = verificarMuestra(c.trades_oos);

  const problemas = [beneficio, profitFactor, drawdown, muestra]
    .filter((x) => x.veredicto === "NO_PLAUSIBLE" && x.motivo)
    .map((x) => x.motivo as string);

  return { beneficio, profitFactor, drawdown, muestra, tieneProblemas: problemas.length > 0, problemas };
}

/** Presenta un campo verificado. Nunca devuelve un número que no haya pasado la auditoría. */
export function mostrar(campo: CampoVerificado, sufijo = "", decimales = 2): string {
  if (campo.veredicto === "SIN_DATO") return "SIN DATOS";
  if (campo.veredicto === "NO_PLAUSIBLE") return "NO PLAUSIBLE";
  return `${(campo.valor as number).toLocaleString("es-ES", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  })}${sufijo}`;
}
