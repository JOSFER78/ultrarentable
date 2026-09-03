import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const dynamic = "force-dynamic";

interface ModuleSummary {
  id: string;
  slug: string;
  filename: string;
  title: string;
  category: string;
  sizeBytes: number;
}

const MODULE_TITLES: Record<string, { title: string; category: string }> = {
  "01": { title: "Ecosistema Tradesfera & Modelo de Negocio", category: "DOCTRINA" },
  "02": { title: "Matemática de Bankroll & Capital Munición", category: "MATEMÁTICA" },
  "03": { title: "Teoría de Varianza & Control de Rachas", category: "MATEMÁTICA" },
  "04": { title: "Protocolo Inteligente de Aprobación de Cuentas", category: "OPERATIVA" },
  "05": { title: "Sistema Multicuenta & Copytrading", category: "OPERATIVA" },
  "06": { title: "Ciclo Óptimo de Retiros & Payouts", category: "OPERATIVA" },
  "07": { title: "Psicología del Fondeo y Sesgos Operativos", category: "PSICOTRADING" },
  "08": { title: "Comparativa Prop Firms de Futuros CME", category: "ARBITRAJE" },
  "09": { title: "Infraestructura Técnica NinjaTrader Tools", category: "EJECUCIÓN" },
  "10": { title: "Dossier Maestro Tradesfera Fondeo Futuros", category: "DOCTRINA" },
  "11": { title: "Estrategias y Horarios Gerard Garcia Futuros", category: "OPERATIVA" },
  "12": { title: "Maestría Psicológica y Protocolos Psicólogo del Trading", category: "PSICOTRADING" },
  "13": { title: "Sistema Táctico Máxima Extracción por Empresa", category: "ARBITRAJE" },
  "14": { title: "Hacks, Shorts y Reglas Rápidas de Fondeo", category: "OPERATIVA" },
  "15": { title: "Arbitraje de Negocio, Promos y Fiscalidad", category: "ARBITRAJE" },
  "16": { title: "Playbook Operativo Diario y Checklist de Ejecución", category: "EJECUCIÓN" },
};

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const slug = searchParams.get("slug");

  // Localizar carpeta docs/tradesfera en raíz del repo
  const docsDir = path.resolve(process.cwd(), "../../docs/tradesfera");

  if (!fs.existsSync(docsDir)) {
    return NextResponse.json({ error: "CARPETA_NO_ENCONTRADA", path: docsDir }, { status: 404 });
  }

  // Si se pide un slug concreto, devolver su contenido Markdown
  if (slug) {
    const files = fs.readdirSync(docsDir);
    const targetFile = files.find((f) => f.startsWith(`${slug}_`) && f.endsWith(".md"));

    if (!targetFile) {
      return NextResponse.json({ error: "MODULO_NO_ENCONTRADO", slug }, { status: 404 });
    }

    const fullPath = path.join(docsDir, targetFile);
    const content = fs.readFileSync(fullPath, "utf-8");
    const info = MODULE_TITLES[slug] || { title: targetFile, category: "GENERAL" };

    return NextResponse.json({
      id: slug,
      filename: targetFile,
      title: info.title,
      category: info.category,
      content,
    });
  }

  // Si no se pide slug, listar todos los 16 módulos
  const files = fs.readdirSync(docsDir).filter((f) => f.endsWith(".md") && !f.toLowerCase().includes("readme"));
  const modules: ModuleSummary[] = files.map((file) => {
    const prefixMatch = file.match(/^(\d{2})_/);
    const id = prefixMatch ? prefixMatch[1] : "00";
    const info = MODULE_TITLES[id] || {
      title: file.replace(/^\d{2}_/, "").replace(/\.md$/, "").replace(/_/g, " "),
      category: "GENERAL",
    };
    const stat = fs.statSync(path.join(docsDir, file));

    return {
      id,
      slug: id,
      filename: file,
      title: info.title,
      category: info.category,
      sizeBytes: stat.size,
    };
  }).sort((a, b) => a.id.localeCompare(b.id));

  return NextResponse.json({
    total: modules.length,
    modules,
  });
}
