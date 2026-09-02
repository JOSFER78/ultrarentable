/**
 * apps/web/app/estrategias/api-telemetria/route.ts
 *
 * Lee las telemetrías de embudo que las campañas de M2 (services/improvement)
 * dejan en disco en orchestration/results/telemetria/embudo_*.json y devuelve
 * un resumen ligero por (símbolo, temporalidad, perfil), quedándose con la más
 * reciente de cada combinación. Nunca carga la lista `telemetria` (el detalle
 * operación-a-operación, puede ser miles de filas) en la respuesta: solo los
 * agregados que ya trae cada fichero (`embudo_por_etapa`, `causas_por_etapa`).
 *
 * REAL-ONLY: si la carpeta no existe o no hay ficheros legibles, se responde
 * {status:"NO DATA"} en vez de inventar una campaña.
 */

import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { findRepoRoot } from "@/lib/projectPaths";

export const dynamic = "force-dynamic";

interface CausaEtapaDisco {
  total?: number;
  pocas_operaciones?: number;
  sin_ventaja_bruta?: number;
  sin_ventaja_por_coste?: number;
  por_familia?: Record<
    string,
    { total?: number; pocas_operaciones?: number; sin_ventaja_bruta?: number; sin_ventaja_por_coste?: number }
  >;
}

interface EmbudoDisco {
  generado_utc?: string;
  engine_version?: string;
  contexto?: {
    track?: string;
    symbol?: string;
    timeframe?: string;
    profile?: string;
    configuraciones_evaluadas?: number;
    espacio_total?: number;
    truncado?: boolean;
  };
  embudo_por_etapa?: Record<string, number>;
  causas_por_etapa?: Record<string, CausaEtapaDisco>;
}

interface CampanaResumen {
  track: string;
  symbol: string;
  timeframe: string;
  profile: string;
  generado_utc: string;
  engine_version: string;
  espacio_total: number;
  truncado: boolean;
  evaluadas: number;
  muertas_is: number;
  pasan_is: number;
  sin_ventaja_bruta: number;
  sin_ventaja_por_coste: number;
  pocas_operaciones: number;
  por_familia: Record<string, { total: number; sin_ventaja_bruta: number; sin_ventaja_por_coste: number; pocas_operaciones: number }>;
}

function vacio() {
  return NextResponse.json({ status: "NO DATA", campanas: [] as CampanaResumen[] });
}

export async function GET() {
  const repoRoot = findRepoRoot();
  const dir = path.join(repoRoot, "orchestration", "results", "telemetria");

  if (!fs.existsSync(dir)) return vacio();

  let nombres: string[];
  try {
    nombres = fs.readdirSync(dir).filter((n) => n.startsWith("embudo_") && n.endsWith(".json"));
  } catch {
    return vacio();
  }
  if (nombres.length === 0) return vacio();

  const porClave = new Map<string, CampanaResumen>();

  for (const nombre of nombres) {
    let datos: EmbudoDisco;
    try {
      const texto = fs.readFileSync(path.join(dir, nombre), "utf8");
      datos = JSON.parse(texto) as EmbudoDisco;
    } catch {
      continue; // fichero corrupto o en escritura: se ignora, no se rompe la respuesta
    }

    const ctx = datos.contexto;
    const generadoUtc = datos.generado_utc;
    if (!ctx || !ctx.symbol || !ctx.timeframe || !ctx.profile || !generadoUtc) continue;

    const clave = `${ctx.track ?? "FONDEO"}__${ctx.symbol}__${ctx.timeframe}__${ctx.profile}`;
    const existente = porClave.get(clave);
    if (existente && existente.generado_utc >= generadoUtc) continue; // ya tenemos una más reciente

    const evaluadas = ctx.configuraciones_evaluadas ?? 0;
    const muertasIs = datos.embudo_por_etapa?.IS ?? 0;
    const causasIs = datos.causas_por_etapa?.IS;

    const porFamilia: CampanaResumen["por_familia"] = {};
    for (const [familia, valores] of Object.entries(causasIs?.por_familia ?? {})) {
      porFamilia[familia] = {
        total: valores.total ?? 0,
        sin_ventaja_bruta: valores.sin_ventaja_bruta ?? 0,
        sin_ventaja_por_coste: valores.sin_ventaja_por_coste ?? 0,
        pocas_operaciones: valores.pocas_operaciones ?? 0,
      };
    }

    porClave.set(clave, {
      track: ctx.track ?? "FONDEO",
      symbol: ctx.symbol,
      timeframe: ctx.timeframe,
      profile: ctx.profile,
      generado_utc: generadoUtc,
      engine_version: datos.engine_version ?? "",
      espacio_total: ctx.espacio_total ?? evaluadas,
      truncado: Boolean(ctx.truncado),
      evaluadas,
      muertas_is: muertasIs,
      pasan_is: Math.max(0, evaluadas - muertasIs),
      sin_ventaja_bruta: causasIs?.sin_ventaja_bruta ?? 0,
      sin_ventaja_por_coste: causasIs?.sin_ventaja_por_coste ?? 0,
      pocas_operaciones: causasIs?.pocas_operaciones ?? 0,
      por_familia: porFamilia,
    });
  }

  const campanas = Array.from(porClave.values()).sort((a, b) => (a.generado_utc < b.generado_utc ? 1 : -1));

  return NextResponse.json({ status: campanas.length > 0 ? "OK" : "NO DATA", campanas });
}
