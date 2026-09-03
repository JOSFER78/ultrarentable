/**
 * apps/web/app/api/comentarios/route.ts
 *
 * Endpoint para registrar y consultar los comentarios de Emilio directamente en
 * `orchestration/tablero/COMENTARIOS_EMILIO.md`.
 *
 * Permite que las observaciones y anomalías detectadas desde la web se guarden en el
 * repositorio de forma versionada y auditable por el orquestador y los agentes.
 *
 * REAL-ONLY: La ruta del fichero es fija y no se acepta por parámetro. Solo añade (append),
 * nunca sobrescribe comentarios anteriores.
 */

import fs from "fs";
import path from "path";
import { NextRequest, NextResponse } from "next/server";
import { findRepoRoot } from "@/lib/projectPaths";

export const dynamic = "force-dynamic";

function getFilePath(): string {
  const root = findRepoRoot();
  return path.join(root, "orchestration", "tablero", "COMENTARIOS_EMILIO.md");
}

function getUtcTimestamp(): string {
  const d = new Date();
  const yyyy = d.getUTCFullYear();
  const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(d.getUTCDate()).padStart(2, "0");
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const min = String(d.getUTCMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd} ${hh}:${min} UTC`;
}

const CABECERA_INICIAL = `# Comentarios de Emilio

> Registro cronológico de observaciones, dudas y anomalías enviadas por Emilio desde la web (\`/plan\`).
> Formato: fecha UTC, página de origen, texto y estado.
`;

export async function GET() {
  try {
    const filePath = getFilePath();
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({
        ok: true,
        contenido: "",
      });
    }
    const contenido = fs.readFileSync(filePath, "utf-8");
    return NextResponse.json({
      ok: true,
      contenido,
    });
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: `Error al leer comentarios: ${String(error)}` },
      { status: 500 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    let body: { texto?: unknown; pagina?: unknown };
    try {
      body = await req.json();
    } catch {
      return NextResponse.json(
        { error: "Cuerpo de la petición inválido (JSON malformado)." },
        { status: 400 }
      );
    }

    const { texto, pagina } = body;

    if (typeof texto !== "string" || !texto.trim()) {
      return NextResponse.json(
        { error: "El comentario no puede estar vacío." },
        { status: 400 }
      );
    }

    if (texto.length > 4000) {
      return NextResponse.json(
        { error: "El comentario excede el límite máximo de 4.000 caracteres." },
        { status: 400 }
      );
    }

    const paginaValida =
      typeof pagina === "string" && pagina.trim()
        ? pagina.trim()
        : "/plan";

    const filePath = getFilePath();
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const timestamp = getUtcTimestamp();
    const bloque = `\n---\n\n### ${timestamp} · desde ${paginaValida}\n\n${texto.trim()}\n\n**Estado:** SIN ATENDER\n`;

    if (!fs.existsSync(filePath)) {
      fs.writeFileSync(filePath, CABECERA_INICIAL + bloque, "utf-8");
    } else {
      fs.appendFileSync(filePath, bloque, "utf-8");
    }

    return NextResponse.json({
      ok: true,
      mensaje: "Comentario guardado correctamente.",
      timestamp,
      pagina: paginaValida,
    });
  } catch (error) {
    return NextResponse.json(
      { error: `Error del servidor al guardar comentario: ${String(error)}` },
      { status: 500 }
    );
  }
}
