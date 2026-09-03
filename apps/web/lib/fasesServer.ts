/**
 * apps/web/lib/fasesServer.ts
 *
 * Módulo para cálculo puro y lectura de fases del plan maestro (A40).
 * Separa la lectura de ficheros de la función pura de cálculo de estado y avance.
 */

import fs from "fs";
import path from "path";
import { findRepoRoot } from "@/lib/projectPaths";
import { obtenerTableroData, type TareaTablero } from "@/lib/tableroServer";

export type EstadoFaseCalculado =
  | "con correcciones pendientes"
  | "en marcha"
  | "lista para auditar"
  | "cerrada"
  | "esperando turno";

export interface FaseRaw {
  id: string;
  titulo: string;
  depende_de: string[];
  desbloquea: string[];
  verificacion_global: string;
  cerrada: boolean;
  archivo: string;
}

export interface FaseCalculada {
  id: string;
  titulo: string;
  depende_de: string[];
  desbloquea: string[];
  verificacion_global: string;
  cerrada: boolean;
  total_tareas: number;
  verificadas: number;
  devueltas: number;
  en_curso: number;
  pendientes: number;
  avance_label: string;
  progreso_pct: number;
  estado_calculado: EstadoFaseCalculado;
  es_activa: boolean;
  es_carril_apoyo: boolean;
  tareas: TareaTablero[];
  archivo: string;
}

export interface FasesPlanData {
  generatedAt: string;
  fase_activa: string;
  total_fases: number;
  fases: FaseCalculada[];
}

const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---/;
const BLOQUE_FILENAME_RE = /^F\d{2}_.*\.md$/;
const FIELD_LINE_RE = /^([a-zA-Z_][\w]*):\s*(.*)$/;
const QUOTED_ITEM_RE = /"([^"]*)"/g;

function parseFrontmatterValue(raw: string): string | string[] {
  const trimmed = raw.trim();
  if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
    const items: string[] = [];
    let match: RegExpExecArray | null;
    QUOTED_ITEM_RE.lastIndex = 0;
    while ((match = QUOTED_ITEM_RE.exec(trimmed)) !== null) {
      items.push(match[1]);
    }
    return items;
  }
  if (trimmed.startsWith('"') && trimmed.endsWith('"') && trimmed.length >= 2) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

/**
 * Función PURA que calcula el estado y avance de una fase individual.
 * Sin dependencias de I/O ni red.
 */
export function calcularAvanceFasePura(
  faseRaw: FaseRaw,
  tareas: TareaTablero[],
  fasesCerradas: Set<string>
): FaseCalculada {
  const total = tareas.length;
  let verificadas = 0;
  let devueltas = 0;
  let enCurso = 0;
  let pendientes = 0;

  for (const t of tareas) {
    const st = String(t.estado || "").toUpperCase();
    if (st === "VERIFICADO") verificadas++;
    else if (st === "DEVUELTO") devueltas++;
    else if (st === "EN_CURSO" || st === "ENTREGADO") enCurso++;
    else if (st === "PENDIENTE") pendientes++;
  }

  const avance_label = `${verificadas} de ${total}`;
  const progreso_pct = total > 0 ? Math.round((verificadas / total) * 1000) / 10 : 0.0;

  const depsCerradas = faseRaw.depende_de.every((dep) => fasesCerradas.has(dep));

  let estado_calculado: EstadoFaseCalculado;
  if (faseRaw.cerrada) {
    estado_calculado = "cerrada";
  } else if (devueltas > 0) {
    estado_calculado = "con correcciones pendientes";
  } else if (enCurso > 0) {
    estado_calculado = "en marcha";
  } else if (total > 0 && verificadas === total) {
    estado_calculado = "lista para auditar"; // NUNCA "cerrada" sin auditoría formal
  } else if (!depsCerradas && enCurso === 0 && verificadas === 0) {
    estado_calculado = "esperando turno";
  } else if (pendientes > 0 && depsCerradas) {
    estado_calculado = "en marcha";
  } else if (total === 0 && !depsCerradas) {
    estado_calculado = "esperando turno";
  } else {
    estado_calculado = "en marcha";
  }

  return {
    id: faseRaw.id,
    titulo: faseRaw.titulo,
    depende_de: faseRaw.depende_de,
    desbloquea: faseRaw.desbloquea,
    verificacion_global: faseRaw.verificacion_global,
    cerrada: faseRaw.cerrada,
    total_tareas: total,
    verificadas,
    devueltas,
    en_curso: enCurso,
    pendientes,
    avance_label,
    progreso_pct,
    estado_calculado,
    es_activa: false,
    es_carril_apoyo: faseRaw.id === "F10",
    tareas,
    archivo: faseRaw.archivo,
  };
}

/**
 * Función PURA para procesar todas las fases y determinar la fase activa.
 */
export function procesarFasesCalculadas(
  fasesRaw: FaseRaw[],
  tareasPorFase: Map<string, TareaTablero[]>
): FaseCalculada[] {
  const fasesCerradas = new Set<string>();
  for (const f of fasesRaw) {
    if (f.cerrada) fasesCerradas.add(f.id);
  }

  const resultado: FaseCalculada[] = fasesRaw.map((f) => {
    const tareas = tareasPorFase.get(f.id) || [];
    return calcularAvanceFasePura(f, tareas, fasesCerradas);
  });

  resultado.sort((a, b) => a.id.localeCompare(b.id));

  // Determinar fase activa (hoy es F03 según directiva de A40)
  const faseActivaId = "F03";

  for (const f of resultado) {
    f.es_activa = f.id === faseActivaId;
  }

  return resultado;
}

/**
 * Lectura de ficheros de fases en disco.
 */
export function leerFasesRaw(): FaseRaw[] {
  const repoRoot = findRepoRoot();
  const dir = path.join(repoRoot, "orchestration", "state", "plan", "bloques");
  if (!fs.existsSync(dir)) return [];

  let files: string[] = [];
  try {
    files = fs.readdirSync(dir).filter((f) => BLOQUE_FILENAME_RE.test(f)).sort();
  } catch {
    return [];
  }

  const fases: FaseRaw[] = [];
  for (const filename of files) {
    try {
      const raw = fs.readFileSync(path.join(dir, filename), "utf-8");
      const match = raw.match(FRONTMATTER_RE);
      if (!match) continue;

      const fields: Record<string, string | string[]> = {};
      for (const line of match[1].split(/\r?\n/)) {
        const lineMatch = line.match(FIELD_LINE_RE);
        if (lineMatch) {
          fields[lineMatch[1]] = parseFrontmatterValue(lineMatch[2]);
        }
      }

      const id = String(fields["id"] || "");
      const titulo = String(fields["titulo"] || id);
      const depende_de = Array.isArray(fields["depende_de"])
        ? fields["depende_de"]
        : fields["depende_de"]
        ? [String(fields["depende_de"])]
        : [];
      const desbloquea = Array.isArray(fields["desbloquea"])
        ? fields["desbloquea"]
        : fields["desbloquea"]
        ? [String(fields["desbloquea"])]
        : [];
      const verificacion_global = String(fields["verificacion_global"] || "");
      const cerrada = String(fields["cerrada"] || "").toLowerCase() === "true";

      if (id) {
        fases.push({
          id,
          titulo,
          depende_de,
          desbloquea,
          verificacion_global,
          cerrada,
          archivo: filename,
        });
      }
    } catch {
      // Ignorar errores individuales
    }
  }

  return fases;
}

/**
 * Función orquestadora del servidor para obtener todas las fases calculadas.
 */
export function obtenerFasesPlanData(): FasesPlanData {
  const fasesRaw = leerFasesRaw();
  const tableroData = obtenerTableroData();

  const tareasPorFase = new Map<string, TareaTablero[]>();
  for (const t of tableroData.tareas) {
    const fid = t.fase ? t.fase.toUpperCase() : "";
    if (fid) {
      if (!tareasPorFase.has(fid)) tareasPorFase.set(fid, []);
      tareasPorFase.get(fid)!.push(t);
    }
  }

  const fases = procesarFasesCalculadas(fasesRaw, tareasPorFase);
  const activa = fases.find((f) => f.es_activa)?.id || "F03";

  return {
    generatedAt: new Date().toISOString(),
    fase_activa: activa,
    total_fases: fases.length,
    fases,
  };
}
