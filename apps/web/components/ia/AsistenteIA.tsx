"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Sparkles, Send, Loader2, AlertCircle, Bot, ArrowRight } from "lucide-react";
import {
  getIAProveedor,
  completarIA,
  type IAProveedorConfig,
  type IACompletarRespuesta,
} from "@/lib/api";

export default function AsistenteIA() {
  const [config, setConfig] = useState<IAProveedorConfig | null>(null);
  const [cargandoConfig, setCargandoConfig] = useState<boolean>(true);
  const [prompt, setPrompt] = useState<string>("");
  const [consultando, setConsultando] = useState<boolean>(false);
  const [respuesta, setRespuesta] = useState<IACompletarRespuesta | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargarConfig = useCallback(async () => {
    setCargandoConfig(true);
    try {
      const data = await getIAProveedor();
      setConfig(data);
    } catch {
      setConfig(null);
    } finally {
      setCargandoConfig(false);
    }
  }, []);

  useEffect(() => {
    void cargarConfig();
  }, [cargarConfig]);

  const handleEnviar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || consultando) return;

    setConsultando(true);
    setError(null);
    setRespuesta(null);

    try {
      const res = await completarIA(prompt.trim());
      setRespuesta(res);
    } catch (err: any) {
      setError(err?.message || "Fallo en la llamada al proveedor de IA.");
    } finally {
      setConsultando(false);
    }
  };

  if (cargandoConfig) {
    return (
      <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg text-xs font-mono text-[var(--text-3)] flex items-center gap-2">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--text-3)]" />
        <span>Comprobando configuración del proveedor de IA…</span>
      </div>
    );
  }

  // 3. Si no hay proveedor configurado: línea sobria en gris y enlace al panel
  if (!config || !config.configurado) {
    return (
      <div className="p-4 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono text-[var(--text-2)]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[var(--text-3)] shrink-0" />
          <span>Falta configurar el proveedor de IA en el panel de superadmin.</span>
        </div>
        <a
          href="#config-ia"
          className="inline-flex items-center gap-1 text-[var(--text-1)] hover:underline font-bold"
        >
          <span>Ir a configuración de IA</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </a>
      </div>
    );
  }

  return (
    <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-5 space-y-4 font-mono">
      {/* Cabecera del Asistente */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-[var(--profit)]" />
          <h3 className="text-sm font-bold text-[var(--text-1)]">
            Asistente de IA (Antigravity / Hermes)
          </h3>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-[var(--text-3)]">
          <span>Proveedor: <strong className="text-[var(--text-1)]">{config.nombre || "Personalizado"}</strong></span>
          <span>·</span>
          <span>Modelo: <strong className="text-[var(--text-1)]">{config.modelo || "Automático"}</strong></span>
        </div>
      </div>

      {/* Formulario de Consulta */}
      <form onSubmit={handleEnviar} className="space-y-3">
        <div>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Haz una consulta sobre estrategias, parámetros cuantitativos, manifiesto o reglas..."
            rows={3}
            disabled={consultando}
            className="w-full p-3 bg-[var(--surface-2)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded-lg text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none resize-none font-sans"
          />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-[11px] text-[var(--text-3)]">
            Llamada directa al endpoint configurado en el servidor.
          </span>
          <button
            type="submit"
            disabled={!prompt.trim() || consultando}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border-strong)] text-xs text-[var(--text-1)] font-bold transition cursor-pointer disabled:opacity-50"
          >
            {consultando ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Consultando…</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>Enviar consulta</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Respuesta Real de la IA */}
      {respuesta && (
        <div className="p-4 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg space-y-2">
          <div className="flex items-center justify-between text-[11px] text-[var(--text-3)] border-b border-[var(--border)] pb-1.5">
            <span>Respuesta ({respuesta.modelo} vía {respuesta.proveedor}):</span>
          </div>
          <div className="text-xs text-[var(--text-1)] font-sans whitespace-pre-wrap leading-relaxed">
            {respuesta.respuesta}
          </div>
        </div>
      )}

      {/* Error Real si Falla */}
      {error && (
        <div className="p-3 bg-[var(--loss-dim)] border border-[var(--loss)] rounded-lg text-xs space-y-1 text-[var(--loss)]">
          <div className="flex items-center gap-1.5 font-bold">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Fallo de respuesta del proveedor de IA:</span>
          </div>
          <p className="text-[11px] text-[var(--text-1)] font-mono">{error}</p>
        </div>
      )}
    </div>
  );
}
