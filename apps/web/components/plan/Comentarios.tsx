"use client";

import React, { useState, useEffect, useCallback } from "react";
import { MessageSquare, Send, CheckCircle2, AlertCircle, RefreshCw, FileText } from "lucide-react";

interface ComentarioItem {
  id: string;
  fecha: string;
  pagina: string;
  texto: string;
  estado: string;
}

function parseComentariosMd(md: string): ComentarioItem[] {
  if (!md) return [];
  const parts = md.split(/^---$/m);
  const items: ComentarioItem[] = [];

  for (let i = 0; i < parts.length; i++) {
    const raw = parts[i].trim();
    if (!raw || raw.startsWith("# Comentarios de Emilio")) continue;

    const headerMatch = raw.match(/###\s+([0-9\-:\sUTC]+)\s+·\s+desde\s+([^\n\r]+)/);
    const estadoMatch = raw.match(/\*\*Estado:\*\*\s+([^\n\r]+)/);

    const fecha = headerMatch ? headerMatch[1].trim() : "Fecha UTC";
    const pagina = headerMatch ? headerMatch[2].trim() : "/plan";
    const estado = estadoMatch ? estadoMatch[1].trim() : "SIN ATENDER";

    let texto = raw;
    if (headerMatch) {
      texto = texto.replace(headerMatch[0], "");
    }
    if (estadoMatch) {
      texto = texto.replace(estadoMatch[0], "");
    }
    texto = texto.trim();

    if (texto) {
      items.push({
        id: `${fecha}-${i}`,
        fecha,
        pagina,
        texto,
        estado,
      });
    }
  }

  // El más nuevo arriba
  return items.reverse();
}

export default function Comentarios() {
  const [texto, setTexto] = useState("");
  const [pagina, setPagina] = useState("/plan");
  const [comentarios, setComentarios] = useState<ComentarioItem[]>([]);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [mensajeExito, setMensajeExito] = useState<string | null>(null);
  const [mensajeError, setMensajeError] = useState<string | null>(null);

  // Inicializar página desde el navegador
  useEffect(() => {
    if (typeof window !== "undefined") {
      setPagina(window.location.pathname || "/plan");
    }
  }, []);

  const cargarComentarios = useCallback(async () => {
    setCargando(true);
    try {
      const res = await fetch("/api/comentarios", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.ok && typeof data.contenido === "string") {
        setComentarios(parseComentariosMd(data.contenido));
      }
    } catch (err) {
      setMensajeError(err instanceof Error ? err.message : "Error al cargar comentarios.");
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void cargarComentarios();
  }, [cargarComentarios]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!texto.trim()) return;

    setGuardando(true);
    setMensajeExito(null);
    setMensajeError(null);

    try {
      const res = await fetch("/api/comentarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          texto: texto.trim(),
          pagina: pagina.trim() || "/plan",
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || `HTTP ${res.status}`);
      }

      setTexto("");
      setMensajeExito("Guardado");
      // Recargar lista inmediatamente
      await cargarComentarios();

      setTimeout(() => {
        setMensajeExito(null);
      }, 4000);
    } catch (err) {
      setMensajeError(err instanceof Error ? err.message : "Error al guardar el comentario.");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto font-sans">
      {/* Cabecera explicativa */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[var(--text-1)] flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-[var(--text-2)]" />
            <span>Comentarios y Observaciones de Emilio</span>
          </h2>
          <span className="text-[11px] font-mono text-[var(--text-3)]">
            orchestration/tablero/COMENTARIOS_EMILIO.md
          </span>
        </div>
        <p className="text-xs text-[var(--text-3)]">
          Cualquier anomalía o duda escrita aquí se guarda en el repositorio y queda registrada de forma visible para el orquestador y los agentes.
        </p>
      </div>

      {/* Formulario de entrada */}
      <form onSubmit={handleSubmit} className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <label htmlFor="comentario-input" className="font-medium text-[var(--text-2)]">
            Nuevo comentario o incidencia:
          </label>
          <div className="flex items-center gap-1.5 font-mono text-[11px] text-[var(--text-3)]">
            <span>Página:</span>
            <input
              type="text"
              value={pagina}
              onChange={(e) => setPagina(e.target.value)}
              className="bg-[var(--surface-2)] border border-[var(--border)] rounded px-1.5 py-0.5 text-[var(--text-2)] text-[11px] w-36 font-mono focus:outline-none focus:border-[var(--border-strong)]"
              title="Página donde viste la anomalía"
            />
          </div>
        </div>

        <textarea
          id="comentario-input"
          rows={4}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Escribe aquí lo que ves raro, lo que falta o cualquier ajuste que deba revisarse…"
          className="w-full bg-[var(--surface-2)] border border-[var(--border)] rounded p-3 text-xs text-[var(--text-1)] font-sans focus:outline-none focus:border-[var(--border-strong)] resize-y placeholder-[var(--text-3)]"
          maxLength={4000}
        />

        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2">
            {mensajeExito && (
              <span className="inline-flex items-center gap-1.5 text-xs text-[var(--profit)] font-mono font-medium">
                <CheckCircle2 className="w-3.5 h-3.5 text-[var(--profit)]" />
                {mensajeExito}
              </span>
            )}
            {mensajeError && (
              <span className="inline-flex items-center gap-1.5 text-xs text-[var(--loss)] font-mono">
                <AlertCircle className="w-3.5 h-3.5 text-[var(--loss)]" />
                {mensajeError}
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={guardando || !texto.trim()}
            className="px-4 py-2 rounded bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border)] text-xs font-medium text-[var(--text-1)] transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {guardando ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Guardando…</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Guardar comentario</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Lista de comentarios anteriores */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-2)] flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-[var(--text-3)]" />
            <span>Historial de Comentarios ({comentarios.length})</span>
          </h3>
          <button
            onClick={() => void cargarComentarios()}
            className="text-[11px] text-[var(--text-3)] hover:text-[var(--text-1)] flex items-center gap-1 transition"
            title="Refrescar comentarios"
          >
            <RefreshCw className={`w-3 h-3 ${cargando ? "animate-spin" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>

        {cargando && comentarios.length === 0 ? (
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-6 text-center text-xs text-[var(--text-3)] font-mono">
            Cargando comentarios…
          </div>
        ) : comentarios.length === 0 ? (
          <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-6 text-center text-xs text-[var(--text-3)]">
            No hay comentarios registrados todavía. Escribe el primero arriba.
          </div>
        ) : (
          <div className="space-y-2.5">
            {comentarios.map((item) => (
              <div
                key={item.id}
                className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[11px] font-semibold text-[var(--text-1)]">
                      {item.fecha}
                    </span>
                    <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-[var(--surface-2)] text-[var(--text-3)] border border-[var(--border)]">
                      desde {item.pagina}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                      item.estado === "ATENDIDO"
                        ? "bg-[var(--surface-2)] text-[var(--profit)] border-[var(--profit)]/30"
                        : "bg-[var(--surface-2)] text-[var(--text-3)] border-[var(--border)]"
                    }`}
                  >
                    {item.estado}
                  </span>
                </div>

                <p className="text-xs text-[var(--text-1)] whitespace-pre-wrap leading-relaxed font-sans">
                  {item.texto}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
