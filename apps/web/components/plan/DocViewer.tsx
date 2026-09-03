"use client";

import React, { useState, useMemo } from "react";
import {
  FileText,
  Copy,
  Check,
  Download,
  X,
} from "lucide-react";

interface DocViewerProps {
  title: string;
  filename: string;
  lastModified?: string;
  sizeBytes?: number;
  content: string;
  onClose?: () => void;
}

// ---------------------------------------------------------------------------
// 1. Parser de Frontmatter
// ---------------------------------------------------------------------------
interface ParsedDoc {
  frontmatter: Record<string, string> | null;
  body: string;
}

function parseFrontmatter(rawContent: string): ParsedDoc {
  const trimmed = rawContent.trimStart();
  if (!trimmed.startsWith("---")) {
    return { frontmatter: null, body: rawContent };
  }
  const endMatch = trimmed.slice(3).indexOf("\n---");
  if (endMatch === -1) {
    return { frontmatter: null, body: rawContent };
  }
  const fmBlock = trimmed.slice(3, 3 + endMatch).trim();
  const rest = trimmed.slice(3 + endMatch + 4).replace(/^\r?\n/, "");

  const fm: Record<string, string> = {};
  for (const line of fmBlock.split(/\r?\n/)) {
    const colonIdx = line.indexOf(":");
    if (colonIdx !== -1) {
      const key = line.slice(0, colonIdx).trim();
      let val = line.slice(colonIdx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      if (key) {
        fm[key] = val;
      }
    }
  }

  return { frontmatter: fm, body: rest };
}

// ---------------------------------------------------------------------------
// 2. Parser & Renderizador de Markdown Inline
// ---------------------------------------------------------------------------
function renderInline(text: string): React.ReactNode[] {
  const tokens: React.ReactNode[] = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      tokens.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith("`") && token.endsWith("`")) {
      tokens.push(
        <code
          key={key++}
          className="px-1.5 py-0.5 mx-0.5 rounded bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)] font-mono text-[11px]"
        >
          {token.slice(1, -1)}
        </code>
      );
    } else if (token.startsWith("**") && token.endsWith("**")) {
      tokens.push(
        <strong key={key++} className="font-semibold text-[var(--text-1)]">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("*") && token.endsWith("*")) {
      tokens.push(
        <em key={key++} className="italic text-[var(--text-2)]">
          {token.slice(1, -1)}
        </em>
      );
    } else if (token.startsWith("[") && token.includes("](")) {
      const closeBracket = token.indexOf("](");
      const linkText = token.slice(1, closeBracket);
      const linkHref = token.slice(closeBracket + 2, -1);
      tokens.push(
        <a
          key={key++}
          href={linkHref}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[var(--text-1)] underline hover:text-[var(--profit)] transition"
        >
          {linkText}
        </a>
      );
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    tokens.push(text.slice(lastIndex));
  }
  return tokens;
}

// ---------------------------------------------------------------------------
// 3. Parser de Bloques Markdown
// ---------------------------------------------------------------------------
type MarkdownBlock =
  | { type: "heading"; level: number; text: string }
  | { type: "code"; lang: string; code: string }
  | { type: "table"; headers: string[]; rows: string[][] }
  | { type: "blockquote"; lines: string[] }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "hr" }
  | { type: "paragraph"; text: string };

function parseMarkdownBlocks(text: string): MarkdownBlock[] {
  const lines = text.split(/\r?\n/);
  const blocks: MarkdownBlock[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Línea vacía
    if (!trimmed) {
      i++;
      continue;
    }

    // Bloque de código ```
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      if (i < lines.length) i++; // saltar cierre ```
      blocks.push({ type: "code", lang, code: codeLines.join("\n") });
      continue;
    }

    // Separador horizontal --- o ***
    if (/^(\-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // Encabezados (#..####)
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length,
        text: headingMatch[2].trim(),
      });
      i++;
      continue;
    }

    // Citas >
    if (trimmed.startsWith(">")) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({ type: "blockquote", lines: quoteLines });
      continue;
    }

    // Tablas | ... |
    if (trimmed.startsWith("|") && trimmed.endsWith("|") && i + 1 < lines.length && lines[i + 1].includes("|") && /\|?\s*[-:]+[-| :]*\|?/.test(lines[i + 1])) {
      const cleanRow = (rowLine: string) =>
        rowLine
          .split("|")
          .slice(1, -1)
          .map((c) => c.trim());

      const headers = cleanRow(line);
      i += 2; // saltar encabezado y separador
      const rows: string[][] = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        rows.push(cleanRow(lines[i]));
        i++;
      }
      blocks.push({ type: "table", headers, rows });
      continue;
    }

    // Listas con viñetas (- o *)
    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    // Listas numeradas (1. 2. etc)
    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    // Párrafo ordinario
    const pLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith("```") &&
      !lines[i].trim().startsWith("#") &&
      !lines[i].trim().startsWith(">") &&
      !(lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) &&
      !/^[-*]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim()) &&
      !/^(\-{3,}|\*{3,}|_{3,})$/.test(lines[i].trim())
    ) {
      pLines.push(lines[i].trim());
      i++;
    }
    blocks.push({ type: "paragraph", text: pLines.join(" ") });
  }

  return blocks;
}

// ---------------------------------------------------------------------------
// 4. Componente Principal DocViewer
// ---------------------------------------------------------------------------
export default function DocViewer({
  title,
  filename,
  lastModified,
  sizeBytes,
  content,
  onClose,
}: DocViewerProps) {
  const [copied, setCopied] = useState(false);

  const { frontmatter, body } = useMemo(() => parseFrontmatter(content), [content]);
  const blocks = useMemo(() => parseMarkdownBlocks(body), [body]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formattedDate = lastModified
    ? new Date(lastModified).toLocaleString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  const sizeKb = sizeBytes ? (sizeBytes / 1024).toFixed(1) : null;

  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col font-sans text-xs">
      {/* Header */}
      <div className="p-3.5 bg-[var(--surface-2)] border-b border-[var(--border)] flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div className="space-y-0.5 min-w-0">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-[var(--profit)] shrink-0" />
            <h2 className="text-sm font-bold text-[var(--text-1)] truncate tracking-tight">{title}</h2>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-[var(--text-3)] font-mono">
            <span>Fichero: <code className="text-[var(--text-2)]">{filename}</code></span>
            {sizeKb && <span>{sizeKb} KB</span>}
            {formattedDate && (
              <span className="hidden sm:inline">Modificado: {formattedDate}</span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 font-mono">
          <button
            onClick={handleCopy}
            className="px-2.5 py-1.5 rounded-md bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-1)] font-medium transition cursor-pointer flex items-center gap-1.5"
            title="Copiar texto completo"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[var(--profit)]" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? "Copiado" : "Copiar"}</span>
          </button>
          <button
            onClick={handleDownload}
            className="px-2.5 py-1.5 rounded-md bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer flex items-center gap-1.5"
            title="Descargar archivo Markdown"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Descargar</span>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-md bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-1)] transition cursor-pointer"
              title="Cerrar visor"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Frontmatter Metadata Bar (etiquetas pequeñas arriba en vez de texto plano) */}
      {frontmatter && Object.keys(frontmatter).length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 px-4 py-2 bg-[var(--surface-2)]/60 border-b border-[var(--border)] font-mono text-[11px]">
          {frontmatter.id && (
            <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-1)] font-semibold border border-[var(--border)]">
              ID: {frontmatter.id}
            </span>
          )}
          {frontmatter.estado && (
            <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-1)] font-semibold border border-[var(--border)]">
              Estado: <span className={frontmatter.estado === "VERIFICADO" ? "text-[var(--profit)]" : frontmatter.estado === "ENTREGADO" ? "text-amber-400" : "text-[var(--text-2)]"}>{frontmatter.estado}</span>
            </span>
          )}
          {frontmatter.prioridad && (
            <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)]">
              Prioridad: {frontmatter.prioridad}
            </span>
          )}
          {frontmatter.agente && (
            <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-2)] border border-[var(--border)]">
              Agente: {frontmatter.agente}
            </span>
          )}
          {frontmatter.actualizado && (
            <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-3)] border border-[var(--border)]">
              Actualizado: {frontmatter.actualizado}
            </span>
          )}
          {frontmatter.estimado && (
            <span className="px-2 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-3)] border border-[var(--border)]">
              Estimado: {frontmatter.estimado}
            </span>
          )}
        </div>
      )}

      {/* Renderizado de Markdown */}
      <div className="p-4 sm:p-6 max-h-[720px] overflow-y-auto space-y-3 bg-[var(--surface-1)] text-[var(--text-2)] leading-relaxed font-sans">
        {blocks.map((block, idx) => {
          switch (block.type) {
            case "heading": {
              if (block.level === 1) {
                return (
                  <h1 key={idx} className="text-lg font-bold text-[var(--text-1)] mt-5 mb-2 pb-1.5 border-b border-[var(--border)] tracking-tight">
                    {renderInline(block.text)}
                  </h1>
                );
              }
              if (block.level === 2) {
                return (
                  <h2 key={idx} className="text-base font-bold text-[var(--text-1)] mt-4 mb-2 pb-1 border-b border-[var(--border)] tracking-tight">
                    {renderInline(block.text)}
                  </h2>
                );
              }
              if (block.level === 3) {
                return (
                  <h3 key={idx} className="text-sm font-semibold text-[var(--text-1)] mt-3 mb-1.5 tracking-tight">
                    {renderInline(block.text)}
                  </h3>
                );
              }
              return (
                <h4 key={idx} className="text-xs font-semibold text-[var(--text-1)] mt-2 mb-1 uppercase tracking-wider">
                  {renderInline(block.text)}
                </h4>
              );
            }

            case "code":
              return (
                <div key={idx} className="my-3 rounded border border-[var(--border)] bg-[var(--surface-2)] overflow-hidden font-mono text-xs">
                  {block.lang && (
                    <div className="px-3 py-1 bg-[var(--surface-3)]/60 border-b border-[var(--border)] text-[10px] text-[var(--text-3)] uppercase tracking-wider font-mono">
                      {block.lang}
                    </div>
                  )}
                  <pre className="p-3 overflow-x-auto text-[var(--text-1)] leading-relaxed whitespace-pre font-mono text-[11px]">
                    <code>{block.code}</code>
                  </pre>
                </div>
              );

            case "table":
              return (
                <div key={idx} className="my-3 overflow-x-auto rounded border border-[var(--border)] bg-[var(--surface-1)] font-mono">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-[var(--surface-2)] border-b border-[var(--border)]">
                        {block.headers.map((th, cIdx) => (
                          <th key={cIdx} className="px-3 py-2 text-[var(--text-1)] font-semibold border-r last:border-r-0 border-[var(--border)]">
                            {renderInline(th)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {block.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="border-b last:border-b-0 border-[var(--border)] hover:bg-[var(--surface-2)]/30 transition">
                          {row.map((cell, cIdx) => (
                            <td key={cIdx} className="px-3 py-2 text-[var(--text-2)] border-r last:border-r-0 border-[var(--border)]">
                              {renderInline(cell)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );

            case "blockquote":
              return (
                <blockquote key={idx} className="my-3 pl-3.5 py-1.5 border-l-2 border-[var(--profit)] text-[var(--text-2)] bg-[var(--surface-2)]/30 rounded-r text-xs leading-relaxed italic">
                  {block.lines.map((l, lIdx) => (
                    <p key={lIdx} className="my-0.5">{renderInline(l)}</p>
                  ))}
                </blockquote>
              );

            case "ul":
              return (
                <ul key={idx} className="my-2 pl-5 list-disc space-y-1 text-xs text-[var(--text-2)]">
                  {block.items.map((item, iIdx) => (
                    <li key={iIdx} className="leading-relaxed">{renderInline(item)}</li>
                  ))}
                </ul>
              );

            case "ol":
              return (
                <ol key={idx} className="my-2 pl-5 list-decimal space-y-1 text-xs text-[var(--text-2)]">
                  {block.items.map((item, iIdx) => (
                    <li key={iIdx} className="leading-relaxed">{renderInline(item)}</li>
                  ))}
                </ol>
              );

            case "hr":
              return <hr key={idx} className="my-4 border-[var(--border)]" />;

            case "paragraph":
            default:
              return (
                <p key={idx} className="my-2 text-xs text-[var(--text-2)] leading-relaxed">
                  {renderInline(block.text)}
                </p>
              );
          }
        })}
      </div>
    </div>
  );
}
