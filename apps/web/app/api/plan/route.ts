import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { findRepoRoot } from "@/lib/projectPaths";

// El panel de estado (Carril B) corrige el bug de force-static que congelaba
// generatedAt; esta ruta nace ya con force-dynamic para no repetirlo.
export const dynamic = "force-dynamic";

export interface PlanBloque {
  id: string;
  titulo: string;
  estado: string;
  depende_de: string[];
  desbloquea: string[];
  verificacion_global: string;
  actualizado: string;
  aparcado: boolean;
  motivo_aparcado: string;
  archivo: string;
}

interface PlanBloqueError {
  archivo: string;
  error: string;
}

const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---/;
const BLOQUE_FILENAME_RE = /^F\d{2}_.*\.md$/;
const FIELD_LINE_RE = /^([a-zA-Z_][\w]*):\s*(.*)$/;
const QUOTED_ITEM_RE = /"([^"]*)"/g;

/** Parser mínimo del frontmatter YAML de los bloques del plan (claves escalares
 * entre comillas dobles o sin comillas, y arrays de strings en una sola línea:
 * ["F01","F02"] o []). No es un parser YAML general — solo cubre el subconjunto
 * que usan los ficheros orchestration/state/plan/bloques/Fxx_*.md. */
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

function parseBloqueFile(filePath: string, filename: string): PlanBloque | PlanBloqueError {
  let raw: string;
  try {
    raw = fs.readFileSync(filePath, "utf-8");
  } catch (error) {
    return { archivo: filename, error: `No se pudo leer el fichero: ${String(error)}` };
  }

  const match = raw.match(FRONTMATTER_RE);
  if (!match) {
    return { archivo: filename, error: "El fichero no empieza con frontmatter YAML (---...---)" };
  }

  const fields: Record<string, string | string[]> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const lineMatch = line.match(FIELD_LINE_RE);
    if (!lineMatch) continue;
    fields[lineMatch[1]] = parseFrontmatterValue(lineMatch[2]);
  }

  const scalar = (key: string): string | null => {
    const value = fields[key];
    return typeof value === "string" && value.length > 0 ? value : null;
  };
  const array = (key: string): string[] => {
    const value = fields[key];
    return Array.isArray(value) ? value : [];
  };

  const id = scalar("id");
  const titulo = scalar("titulo");
  const estado = scalar("estado");
  if (!id || !titulo || !estado) {
    return {
      archivo: filename,
      error: `Frontmatter incompleto (faltan id/titulo/estado). Claves encontradas: ${
        Object.keys(fields).join(", ") || "ninguna"
      }`,
    };
  }

  return {
    id,
    titulo,
    estado,
    depende_de: array("depende_de"),
    desbloquea: array("desbloquea"),
    verificacion_global: scalar("verificacion_global") ?? "",
    actualizado: scalar("actualizado") ?? "",
    // Una fase aparcada no esta pendiente por falta de trabajo: esta congelada a proposito.
    // Sin este campo la web mostraba F05 y F06 (ULTRA) como simples PENDIENTE, indistinguibles
    // de las fases que si estan en el camino critico de FONDEO.
    aparcado: (scalar("aparcado") ?? "").toLowerCase() === "true",
    motivo_aparcado: scalar("motivo_aparcado") ?? "",
    archivo: filename,
  };
}

export async function GET() {
  const repoRoot = findRepoRoot();
  const bloquesDir = path.join(repoRoot, "orchestration", "state", "plan", "bloques");

  if (!fs.existsSync(bloquesDir)) {
    return NextResponse.json({
      generatedAt: new Date().toISOString(),
      source: bloquesDir,
      count: 0,
      bloques: [],
      errores: [{ archivo: "-", error: `No existe el directorio ${bloquesDir}` }],
    });
  }

  const filenames = fs
    .readdirSync(bloquesDir)
    .filter((name) => BLOQUE_FILENAME_RE.test(name))
    .sort();

  const bloques: PlanBloque[] = [];
  const errores: PlanBloqueError[] = [];

  for (const filename of filenames) {
    const result = parseBloqueFile(path.join(bloquesDir, filename), filename);
    if ("error" in result) errores.push(result);
    else bloques.push(result);
  }

  bloques.sort((a, b) => a.id.localeCompare(b.id));

  return NextResponse.json({
    generatedAt: new Date().toISOString(),
    source: bloquesDir,
    count: bloques.length,
    bloques,
    errores,
  });
}
