/**
 * apps/web/lib/navigationSequence.ts
 * SSOT para la navegación secuencial (flechas anterior/siguiente) y migas de pan universales
 * de Ultrarentable en escritorio y móvil.
 */

export interface NavRouteItem {
  href: string;
  title: string;
  section?: string;
}

export interface CrumbItem {
  label: string;
  href?: string;
}

export interface NavigationInfo {
  prevHref: string | null;
  prevTitle: string | null;
  nextHref: string | null;
  nextTitle: string | null;
  crumbs: CrumbItem[];
}

export const TRADESFERA_MODULES: NavRouteItem[] = [
  { href: "/tradesfera/01-ecosistema", title: "M01 · Ecosistema & 4 Puertas", section: "Tradesfera" },
  { href: "/tradesfera/02-matematica-bankroll", title: "M02 · Matemática Bankroll", section: "Tradesfera" },
  { href: "/tradesfera/03-teoria-varianza", title: "M03 · Teoría Varianza", section: "Tradesfera" },
  { href: "/tradesfera/04-protocolo-aprobacion", title: "M04 · Protocolo Aprobación", section: "Tradesfera" },
  { href: "/tradesfera/05-sistema-multicuenta", title: "M05 · Sistema Multicuenta", section: "Tradesfera" },
  { href: "/tradesfera/06-ciclo-retiros", title: "M06 · Ciclo Retiros", section: "Tradesfera" },
  { href: "/tradesfera/07-psicologia-fondeo", title: "M07 · Psicología Fondeo", section: "Tradesfera" },
  { href: "/tradesfera/08-comparativa-prop-firms", title: "M08 · Comparativa Prop Firms", section: "Tradesfera" },
  { href: "/tradesfera/09-infraestructura-ninjatrader", title: "M09 · Infra NinjaTrader", section: "Tradesfera" },
  { href: "/tradesfera/10-dossier-maestro", title: "M10 · Dossier Maestro", section: "Tradesfera" },
  { href: "/tradesfera/11-estrategias-horarios", title: "M11 · Estrategias & Horarios", section: "Tradesfera" },
  { href: "/tradesfera/12-maestria-psicologica", title: "M12 · Maestría Psicológica", section: "Tradesfera" },
  { href: "/tradesfera/13-sistema-tactico", title: "M13 · Sistema Táctico", section: "Tradesfera" },
  { href: "/tradesfera/14-hacks-reglas-rapidas", title: "M14 · Hacks & Reglas Rápidas", section: "Tradesfera" },
  { href: "/tradesfera/15-arbitraje-promos-fiscalidad", title: "M15 · Arbitraje & Fiscalidad", section: "Tradesfera" },
  { href: "/tradesfera/16-playbook-diario", title: "M16 · Playbook Diario", section: "Tradesfera" },
];

export const ESTRATEGIAS_SECTIONS: NavRouteItem[] = [
  { href: "/estrategias", title: "Overview & Válidas", section: "Estrategias" },
  { href: "/estrategias/generacion", title: "M1 · Generación SQX", section: "Estrategias" },
  { href: "/estrategias/mejora", title: "M2 · Bucle de Mejora", section: "Estrategias" },
  { href: "/estrategias/valoracion", title: "M3 · Valoración 11 Gates", section: "Estrategias" },
  { href: "/estrategias/candidatos", title: "M4 · Candidatos Estrategias", section: "Estrategias" },
  { href: "/estrategias/meta", title: "M5 · Meta-Estrategias", section: "Estrategias" },
];

export const GATES_SEQUENCE: NavRouteItem[] = [
  { href: "/gates/01-data-leakage", title: "G01 · Cero Fuga Temporal", section: "Gates" },
  { href: "/gates/02-cost-drag", title: "G02 · Fricción Realista", section: "Gates" },
  { href: "/gates/03-sample-size", title: "G03 · Muestra Estadística", section: "Gates" },
  { href: "/gates/04-expectancy", title: "G04 · Esperanza Matemática", section: "Gates" },
  { href: "/gates/05-drawdown", title: "G05 · Límite de Pérdida", section: "Gates" },
  { href: "/gates/06-profit-factor", title: "G06 · Factor de Beneficio", section: "Gates" },
  { href: "/gates/07-time-in-market", title: "G07 · Exposición Temporal", section: "Gates" },
  { href: "/gates/08-tail-risk", title: "G08 · Riesgo de Cola", section: "Gates" },
  { href: "/gates/09-volatility-regime", title: "G09 · Régimen Volatilidad", section: "Gates" },
  { href: "/gates/10-execution-slip", title: "G10 · Deslizamiento Órdenes", section: "Gates" },
  { href: "/gates/11-certification", title: "G11 · Certificación Final", section: "Gates" },
];

export const MAIN_SECTIONS: NavRouteItem[] = [
  { href: "/", title: "Centro de Mando" },
  { href: "/estrategias", title: "Estrategias" },
  { href: "/prop-firms", title: "Prop Firms" },
  { href: "/fondeo", title: "Trading Desk Fondeo" },
  { href: "/tradesfera", title: "Tradesfera" },
  { href: "/gates", title: "Pipeline de Gates" },
  { href: "/candidatos", title: "Candidatos" },
  { href: "/plan", title: "Plan Maestro" },
  { href: "/sistema", title: "Sistema & Telemetría" },
  { href: "/ultra", title: "Trading Desk Ultra" },
];

export function getNavigationInfo(pathname: string): NavigationInfo {
  const normPath = pathname.replace(/\/$/, "") || "/";

  // 1. Tradesfera subpáginas
  const tsIdx = TRADESFERA_MODULES.findIndex(
    (m) => normPath === m.href || normPath.startsWith(m.href + "/")
  );
  if (tsIdx >= 0) {
    const prevHref = tsIdx > 0 ? TRADESFERA_MODULES[tsIdx - 1].href : "/tradesfera";
    const prevTitle = tsIdx > 0 ? TRADESFERA_MODULES[tsIdx - 1].title : "Índice Tradesfera";
    const nextHref = tsIdx < TRADESFERA_MODULES.length - 1 ? TRADESFERA_MODULES[tsIdx + 1].href : null;
    const nextTitle = tsIdx < TRADESFERA_MODULES.length - 1 ? TRADESFERA_MODULES[tsIdx + 1].title : null;

    return {
      prevHref,
      prevTitle,
      nextHref,
      nextTitle,
      crumbs: [
        { label: "Tradesfera", href: "/tradesfera" },
        { label: TRADESFERA_MODULES[tsIdx].title },
      ],
    };
  }

  if (normPath === "/tradesfera") {
    return {
      prevHref: "/fondeo",
      prevTitle: "Trading Desk Fondeo",
      nextHref: TRADESFERA_MODULES[0].href,
      nextTitle: `Módulo 1: ${TRADESFERA_MODULES[0].title}`,
      crumbs: [{ label: "Tradesfera" }],
    };
  }

  // 2. Estrategias subpáginas
  const estIdx = ESTRATEGIAS_SECTIONS.findIndex((s) => normPath === s.href);
  if (estIdx >= 0) {
    const prevHref = estIdx > 0 ? ESTRATEGIAS_SECTIONS[estIdx - 1].href : "/";
    const prevTitle = estIdx > 0 ? ESTRATEGIAS_SECTIONS[estIdx - 1].title : "Centro de Mando";
    const nextHref = estIdx < ESTRATEGIAS_SECTIONS.length - 1 ? ESTRATEGIAS_SECTIONS[estIdx + 1].href : "/prop-firms";
    const nextTitle = estIdx < ESTRATEGIAS_SECTIONS.length - 1 ? ESTRATEGIAS_SECTIONS[estIdx + 1].title : "Prop Firms";

    const crumbs: CrumbItem[] = [{ label: "Estrategias", href: "/estrategias" }];
    if (estIdx > 0) {
      crumbs.push({ label: ESTRATEGIAS_SECTIONS[estIdx].title });
    }

    return { prevHref, prevTitle, nextHref, nextTitle, crumbs };
  }

  // 3. Gates subpáginas
  const gateIdx = GATES_SEQUENCE.findIndex((g) => normPath === g.href || normPath.startsWith(g.href + "/"));
  if (gateIdx >= 0) {
    const prevHref = gateIdx > 0 ? GATES_SEQUENCE[gateIdx - 1].href : "/gates";
    const prevTitle = gateIdx > 0 ? GATES_SEQUENCE[gateIdx - 1].title : "Pipeline de Gates";
    const nextHref = gateIdx < GATES_SEQUENCE.length - 1 ? GATES_SEQUENCE[gateIdx + 1].href : null;
    const nextTitle = gateIdx < GATES_SEQUENCE.length - 1 ? GATES_SEQUENCE[gateIdx + 1].title : null;

    return {
      prevHref,
      prevTitle,
      nextHref,
      nextTitle,
      crumbs: [
        { label: "Gates", href: "/gates" },
        { label: GATES_SEQUENCE[gateIdx].title },
      ],
    };
  }

  // 4. Secciones principales del Sidebar
  const mainIdx = MAIN_SECTIONS.findIndex((s) => s.href === normPath);
  if (mainIdx >= 0) {
    const prevHref = mainIdx > 0 ? MAIN_SECTIONS[mainIdx - 1].href : null;
    const prevTitle = mainIdx > 0 ? MAIN_SECTIONS[mainIdx - 1].title : null;
    const nextHref = mainIdx < MAIN_SECTIONS.length - 1 ? MAIN_SECTIONS[mainIdx + 1].href : null;
    const nextTitle = mainIdx < MAIN_SECTIONS.length - 1 ? MAIN_SECTIONS[mainIdx + 1].title : null;

    return {
      prevHref,
      prevTitle,
      nextHref,
      nextTitle,
      crumbs: mainIdx === 0 ? [{ label: "Centro de Mando" }] : [{ label: MAIN_SECTIONS[mainIdx].title }],
    };
  }

  // Fallback genérico para páginas de cuenta o utilitarias
  if (normPath.startsWith("/perfil")) {
    return {
      prevHref: null,
      prevTitle: null,
      nextHref: null,
      nextTitle: null,
      crumbs: [{ label: "Cuenta", href: "/perfil" }, { label: "Perfil" }],
    };
  }

  const cleanName = normPath.replace(/^\//, "").replace(/-/g, " ");
  const formatted = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);

  return {
    prevHref: null,
    prevTitle: null,
    nextHref: null,
    nextTitle: null,
    crumbs: [{ label: formatted }],
  };
}
