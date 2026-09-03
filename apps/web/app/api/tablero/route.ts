/**
 * apps/web/app/api/tablero/route.ts
 *
 * El tablero de orquestación, leído en vivo de `orchestration/tablero/*.md` (un fichero por
 * tarea). Es el único sitio donde vive el estado de una tarea: el orquestador (sesión Claude
 * Code) escribe las tareas y las verifica, los agentes de Antigravity (AGY) las ejecutan y
 * escriben su parte de entrega en el mismo fichero. El protocolo completo está en
 * `orchestration/tablero/README.md`.
 *
 * REAL-ONLY: si la carpeta no existe o no hay tareas legibles, se responde con la lista vacía y
 * el motivo. Nunca se inventa una tarea de ejemplo, y el estado que se publica es exactamente el
 * que pone el fichero: esta ruta no deduce ni corrige estados.
 */

import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { findRepoRoot } from "@/lib/projectPaths";

export const dynamic = "force-dynamic";

/** Estados del ciclo (ver README del tablero). El orden es el del flujo de trabajo. */
export const ESTADOS_TABLERO = [
  // BORRADOR: el orquestador la esta escribiendo. AGY NO puede cogerla aunque la vea entera.
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
  maquina: string;
  ambito: string[];
  depende_de: string[];
  estimado: string;
  creado: string;
  actualizado: string;
  archivo: string;
  /** true cuando el fichero ya trae una parte de entrega escrita por el agente. */
  tiene_parte: boolean;
  /** true cuando el orquestador ya escribió su verificación. */
  tiene_verificacion: boolean;
  /** Primera línea de "Por qué", para la tarjeta. Sin inventar: vacío si no hay. */
  resumen: string;
}

interface TareaIlegible {
  archivo: string;
  error: string;
}

const NOMBRE_TAREA_RE = /^[A-Z]\d{2,3}\.md$/;
const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---/;
const CAMPO_RE = /^([a-zA-Z_][\w]*):\s*(.*)$/;
const ENTRECOMILLADO_RE = /"([^"]*)"/g;

/** Mismo subconjunto de YAML que usa /api/plan: escalares con o sin comillas y arrays en una línea. */
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

/** ¿Tiene contenido real esa sección, o sigue con el marcador "(lo rellena ...)"? */
function seccionRellena(cuerpo: string, titulo: string): boolean {
  const i = cuerpo.indexOf(`## ${titulo}`);
  if (i === -1) return false;
  const desde = cuerpo.slice(i + titulo.length + 3);
  const fin = desde.indexOf("\n## ");
  const bloque = (fin === -1 ? desde : desde.slice(0, fin)).trim();
  if (bloque.length === 0) return false;
  return !/^\(lo rellena/i.test(bloque);
}

/** Primera línea con texto de la sección "Por qué", recortada para la tarjeta. */
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
  };
}

export async function GET() {
  const repoRoot = findRepoRoot();
  const dir = path.join(repoRoot, "orchestration", "tablero");

  if (!fs.existsSync(dir)) {
    return NextResponse.json({
      generatedAt: new Date().toISOString(),
      source: dir,
      estados: ESTADOS_TABLERO,
      total: 0,
      tareas: [],
      por_estado: {},
      ilegibles: [{ archivo: "-", error: `No existe la carpeta ${dir}` }],
    });
  }

  let nombres: string[] = [];
  try {
    nombres = fs.readdirSync(dir).filter((n) => NOMBRE_TAREA_RE.test(n)).sort();
  } catch (error) {
    return NextResponse.json({
      generatedAt: new Date().toISOString(),
      source: dir,
      estados: ESTADOS_TABLERO,
      total: 0,
      tareas: [],
      por_estado: {},
      ilegibles: [{ archivo: "-", error: `No se pudo listar la carpeta: ${String(error)}` }],
    });
  }

  const tareas: TareaTablero[] = [];
  const ilegibles: TareaIlegible[] = [];
  for (const nombre of nombres) {
    const r = leerTarea(path.join(dir, nombre), nombre);
    if ("error" in r) ilegibles.push(r);
    else tareas.push(r);
  }

  const por_estado: Record<string, number> = {};
  for (const t of tareas) por_estado[t.estado] = (por_estado[t.estado] ?? 0) + 1;

  return NextResponse.json({
    generatedAt: new Date().toISOString(),
    source: dir,
    estados: ESTADOS_TABLERO,
    total: tareas.length,
    // Sin verificar = lo que sigue dando trabajo. Lo calcula quien pinta, pero se publica ya hecho
    // para que el contador de la pestaña no tenga que replicar la regla.
    sin_verificar: tareas.filter((t) => t.estado !== "VERIFICADO").length,
    tareas,
    por_estado,
    ilegibles,
  });
}
