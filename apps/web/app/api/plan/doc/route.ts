import fs from "fs";
import path from "path";
import { NextRequest, NextResponse } from "next/server";
import { findRepoRoot } from "@/lib/projectPaths";

export const dynamic = "force-dynamic";

const SAFE_DOC_MAP: Record<string, { folder: "state" | "bloques" | "orchestration"; filename: string; title: string }> = {
  current_phase: { folder: "state", filename: "current_phase.md", title: "Seguimiento en Vivo (Current Phase)" },
  especificacion_web: { folder: "state", filename: "ESPECIFICACION_WEB.md", title: "Especificación de la Web" },
  plan_maestro: { folder: "state", filename: "plan_maestro.md", title: "Plan Maestro v4" },
  ventana_emilio: { folder: "state", filename: "VENTANA_EMILIO.md", title: "Ventana de Decisiones (Emilio)" },
  traspaso_vps: { folder: "state", filename: "TRASPASO_2026-09-02_VPS.md", title: "Informe de Traspaso VPS" },
  traspaso_pc: { folder: "state", filename: "TRASPASO_2026-09-02_PC_noche.md", title: "Informe de Traspaso PC Noche" },
  punto_guardado_ultra: { folder: "state", filename: "PUNTO_GUARDADO_ULTRA.md", title: "Punto de Guardado ULTRA" },
  plan_local_fondeo: { folder: "state", filename: "PLAN_LOCAL_FONDEO.md", title: "Plan Local FONDEO" },
  tareas_agy: { folder: "bloques", filename: "F10_operaciones_infra.md", title: "Tareas para AGY — infraestructura" },
  arquitectura_recursos: { folder: "orchestration", filename: "ARQUITECTURA_RECURSOS.md", title: "Arquitectura de recursos (3 máquinas)" },
  runbook_hetzner: { folder: "orchestration", filename: "RUNBOOK_HETZNER_SEGURIDAD.md", title: "Runbook de seguridad del Hetzner" },
};

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const name = searchParams.get("name");

  if (!name) {
    return NextResponse.json({ error: "PARAMETRO_REQUERIDO", message: "Se requiere parámetro ?name=" }, { status: 400 });
  }

  const repoRoot = findRepoRoot();
  const stateDir = path.join(repoRoot, "orchestration", "state");
  const bloquesDir = path.join(stateDir, "plan", "bloques");

  let targetPath = "";
  let title = name;
  let filename = name;

  // 1. Caso documento de estado
  if (SAFE_DOC_MAP[name]) {
    const entry = SAFE_DOC_MAP[name];
    filename = entry.filename;
    title = entry.title;
    const baseDir = entry.folder === "state" ? stateDir : entry.folder === "bloques" ? bloquesDir : path.join(repoRoot, "orchestration");
    targetPath = path.join(baseDir, entry.filename);
  }
  // 2. Caso fase directa por nombre de archivo Fxx_*.md
  else if (/^F\d{2}_.*\.md$/.test(name)) {
    filename = name;
    title = name.replace(/\.md$/, "").replace(/_/g, " ");
    targetPath = path.join(bloquesDir, name);
  }
  // 3. Caso fase por ID (ej. "F03")
  else if (/^F\d{2}$/.test(name)) {
    const files = fs.existsSync(bloquesDir) ? fs.readdirSync(bloquesDir) : [];
    const matched = files.find((f) => f.startsWith(`${name}_`) && f.endsWith(".md"));
    if (matched) {
      filename = matched;
      title = matched.replace(/\.md$/, "").replace(/_/g, " ");
      targetPath = path.join(bloquesDir, matched);
    }
  }

  if (!targetPath || !fs.existsSync(targetPath)) {
    return NextResponse.json(
      { error: "DOCUMENTO_NO_ENCONTRADO", requested: name, resolvedPath: targetPath },
      { status: 404 }
    );
  }

  try {
    const content = fs.readFileSync(targetPath, "utf-8");
    const stat = fs.statSync(targetPath);

    return NextResponse.json({
      id: name,
      title,
      filename,
      lastModified: stat.mtime.toISOString(),
      sizeBytes: stat.size,
      content,
    });
  } catch (err) {
    return NextResponse.json(
      { error: "ERROR_LECTURA", message: err instanceof Error ? err.message : "Error al leer documento" },
      { status: 500 }
    );
  }
}
