/**
 * apps/web/lib/tableroServer.ts
 *
 * Lógica canónica compartida para leer orchestration/tablero/*.md
 * tanto en Server Components como en la ruta de API /api/tablero.
 */

import fs from "fs";
import path from "path";
import { findRepoRoot } from "@/lib/projectPaths";

export const ESTADOS_TABLERO = [
  "BORRADOR",
  "PENDIENTE",
  "EN_CURSO",
  "ENTREGADO",
  "VERIFICADO",
  "DEVUELTO",
  "BLOQUEADO",
] as const;

export type EstadoTablero = (typeof ESTADOS_TABLERO)[number];

export interface TareaTablero {
  id: string;
  titulo: string;
  agente: string;
  estado: EstadoTablero | "DESCONOCIDO";
  prioridad: string;
  fase: string;
  maquina: string;
  ambito: string[];
  depende_de: string[];
  estimado: string;
  creado: string;
  actualizado: string;
  archivo: string;
  tiene_parte: boolean;
  tiene_verificacion: boolean;
  resumen: string;
  motivo_devolucion: string;
}

export interface TareaIlegible {
  archivo: string;
  error: string;
}

export interface TableroData {
  generatedAt: string;
  source: string;
  estados: readonly string[];
  total: number;
  sin_verificar: number;
  tareas: TareaTablero[];
  por_estado: Record<string, number>;
  ilegibles: TareaIlegible[];
}

const NOMBRE_TAREA_RE = /^[A-Z]\d{2,3}\.md$/;
const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---/;
const CAMPO_RE = /^([a-zA-Z_][\w]*):\s*(.*)$/;
const ENTRECOMILLADO_RE = /"([^"]*)"/g;

function valorFrontmatter(bruto: string): string | string[] {
  const t = bruto.trim();
  if (t.startsWith("[") && t.endsWith("]")) {
    const items: string[] = [];
    let m: RegExpExecArray | null;
    ENTRECOMILLADO_RE.lastIndex = 0;
    while ((m = ENTRECOMILLADO_RE.exec(t)) !== null) items.push(m[1]);
    return items;
  }
  if (t.startsWith('"') && t.endsWith('"') && t.length >= 2) return t.slice(1, -1);
  return t;
}

function seccionRellena(cuerpo: string, titulo: string): boolean {
  const i = cuerpo.indexOf(`## ${titulo}`);
  if (i === -1) return false;
  const desde = cuerpo.slice(i + titulo.length + 3);
  const fin = desde.indexOf("\n## ");
  const bloque = (fin === -1 ? desde : desde.slice(0, fin)).trim();
  if (bloque.length === 0) return false;
  return !/^\(lo rellena/i.test(bloque);
}

function resumenDeTarea(cuerpo: string): string {
  const i = cuerpo.indexOf("## Por qué");
  if (i === -1) return "";
  const resto = cuerpo.slice(i + "## Por qué".length);
  for (const linea of resto.split(/\r?\n/)) {
    const t = linea.trim();
    if (t.length > 0 && !t.startsWith("#")) return t.length > 220 ? `${t.slice(0, 217)}…` : t;
  }
  return "";
}

function motivoDevolucion(cuerpo: string): string {
  const i = cuerpo.indexOf("## Verificación del orquestador");
  if (i === -1) return "";
  const resto = cuerpo.slice(i + "## Verificación del orquestador".length);
  const m = resto.match(/\*\*Por qué vuelve[:\*]?\s*([^\n\r]+)/i);
  if (m) {
    const frase = m[1].trim().replace(/\*\*/g, "");
    return frase.length > 220 ? `${frase.slice(0, 217)}…` : frase;
  }
  for (const linea of resto.split(/\r?\n/)) {
    const t = linea.trim();
    if (t.length > 0 && !t.startsWith("#") && !/^\(lo rellena/i.test(t)) {
      const limpia = t.replace(/\*\*/g, "");
      return limpia.length > 220 ? `${limpia.slice(0, 217)}…` : limpia;
    }
  }
  return "";
}

function leerTarea(ruta: string, archivo: string): TareaTablero | TareaIlegible {
  let bruto: string;
  try {
    bruto = fs.readFileSync(ruta, "utf-8");
  } catch (error) {
    return { archivo, error: `No se pudo leer: ${String(error)}` };
  }

  const m = bruto.match(FRONTMATTER_RE);
  if (!m) return { archivo, error: "Sin frontmatter YAML (--- ... ---): no es una tarea del tablero" };

  const campos: Record<string, string | string[]> = {};
  for (const linea of m[1].split(/\r?\n/)) {
    const c = linea.match(CAMPO_RE);
    if (c) campos[c[1]] = valorFrontmatter(c[2]);
  }

  const escalar = (k: string): string => {
    const v = campos[k];
    return typeof v === "string" ? v : "";
  };
  const lista = (k: string): string[] => {
    const v = campos[k];
    return Array.isArray(v) ? v : [];
  };

  const id = escalar("id");
  const titulo = escalar("titulo");
  const estadoBruto = escalar("estado").toUpperCase();
  if (!id || !titulo || !estadoBruto) {
    return { archivo, error: `Frontmatter incompleto: faltan id, titulo o estado (encontrados: ${Object.keys(campos).join(", ") || "ninguno"})` };
  }

  const cuerpo = bruto.slice(m[0].length);
  const estado = (ESTADOS_TABLERO as readonly string[]).includes(estadoBruto)
    ? (estadoBruto as EstadoTablero)
    : "DESCONOCIDO";

  return {
    id,
    titulo,
    agente: escalar("agente") || "sin asignar",
    estado,
    prioridad: escalar("prioridad") || "sin prioridad",
    fase: escalar("fase") || "",
    maquina: escalar("maquina"),
    ambito: lista("ambito"),
    depende_de: lista("depende_de"),
    estimado: escalar("estimado"),
    creado: escalar("creado"),
    actualizado: escalar("actualizado"),
    archivo,
    tiene_parte: seccionRellena(cuerpo, "Parte de entrega"),
    tiene_verificacion: seccionRellena(cuerpo, "Verificación del orquestador"),
    resumen: resumenDeTarea(cuerpo),
    motivo_devolucion: motivoDevolucion(cuerpo),
  };
}

export function obtenerTableroData(): TableroData {
  const repoRoot = findRepoRoot();
  const dir = path.join(repoRoot, "orchestration", "tablero");

  if (!fs.existsSync(dir)) {
    return {
      generatedAt: new Date().toISOString(),
      source: dir,
      estados: ESTADOS_TABLERO,
      total: 0,
      sin_verificar: 0,
      tareas: [],
      por_estado: {},
      ilegibles: [{ archivo: "-", error: `No existe la carpeta ${dir}` }],
    };
  }

  let nombres: string[] = [];
  try {
    nombres = fs.readdirSync(dir).filter((n) => NOMBRE_TAREA_RE.test(n)).sort();
  } catch (error) {
    return {
      generatedAt: new Date().toISOString(),
      source: dir,
      estados: ESTADOS_TABLERO,
      total: 0,
      sin_verificar: 0,
      tareas: [],
      por_estado: {},
      ilegibles: [{ archivo: "-", error: `No se pudo listar la carpeta: ${String(error)}` }],
    };
  }

  const tareas: TareaTablero[] = [];
  const ilegibles: TareaIlegible[] = [];
  for (const nombre of nombres) {
    const r = leerTarea(path.join(dir, nombre), nombre);
    if ("error" in r) ilegibles.push(r);
    else tareas.push(r);
  }

  const por_estado: Record<string, number> = {};
  for (const e of ESTADOS_TABLERO) por_estado[e] = 0;
  for (const t of tareas) {
    por_estado[t.estado] = (por_estado[t.estado] || 0) + 1;
  }

  const sin_verificar = tareas.filter((t) => t.estado !== "VERIFICADO").length;

  return {
    generatedAt: new Date().toISOString(),
    source: dir,
    estados: ESTADOS_TABLERO,
    total: tareas.length,
    sin_verificar,
    tareas,
    por_estado,
    ilegibles,
  };
}
