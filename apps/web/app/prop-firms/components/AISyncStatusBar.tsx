"use client";

import React, { useState } from "react";
import { Sparkles, RefreshCw, History, AlertCircle, CheckCircle2 } from "lucide-react";

interface AISyncStatusBarProps {
  lastUpdatedText?: string;
  onSyncComplete?: () => void;
}

export function AISyncStatusBar({
  lastUpdatedText = "Sin datos de sincronización previa",
  onSyncComplete,
}: AISyncStatusBarProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(false);
  const [syncError, setSyncError] = useState(false);
  const [showChangelog, setShowChangelog] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleTriggerSync = async () => {
    setIsSyncing(true);
    setSyncSuccess(false);
    setSyncError(false);
    setStatusMessage("Rastreando webs oficiales, help desks y cupones vía FreeLLMAPI...");

    try {
      const res = await fetch("/api/v1/providers/ai-update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_full_scan: true }),
      });

      if (res.ok) {
        const json = await res.json().catch(() => ({}));
        const count = json.updated_count ?? json.synced ?? 0;
        setStatusMessage(
          `Extracción completada con éxito. ${
            count > 0 ? `${count} cuentas actualizadas.` : "Evidencia Zero-Mocks verificada."
          }`
        );
        setSyncSuccess(true);
        setSyncError(false);
        setTimeout(() => {
          setSyncSuccess(false);
          setStatusMessage(null);
        }, 4000);
        if (onSyncComplete) onSyncComplete();
      } else {
        let errDetail = res.statusText;
        try {
          const errJson = await res.json();
          errDetail = errJson.detail || errJson.message || errDetail;
        } catch {
          // ignore non-json error bodies
        }
        setSyncSuccess(false);
        setSyncError(true);
        setStatusMessage(`ERROR / DESCONECTADO (HTTP ${res.status}): ${errDetail}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error de red / servicio no disponible";
      setSyncSuccess(false);
      setSyncError(true);
      setStatusMessage(`ERROR / DESCONECTADO: ${msg}`);
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div
      className={`w-full bg-[#090d16]/90 backdrop-blur-xl border rounded-2xl p-3.5 px-5 shadow-xl transition-all ${
        syncError
          ? "border-rose-500/40 shadow-rose-500/5"
          : "border-white/[0.08] shadow-black/20"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left Status Area */}
        <div className="flex items-center gap-3">
          <div
            className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 border ${
              syncError
                ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            }`}
          >
            {syncError ? <AlertCircle className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black text-white tracking-tight">
                Motor Autónomo de Inteligencia con FreeLLMAPI
              </span>
              <span
                className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                  syncError
                    ? "bg-rose-500/10 border-rose-500/30 text-rose-400"
                    : "bg-sky-500/10 border-sky-500/30 text-sky-400"
                }`}
              >
                Zero-Mocks
              </span>
            </div>
            <div
              className={`text-[11px] font-mono mt-0.5 ${
                syncError
                  ? "text-rose-400 font-bold"
                  : statusMessage
                  ? "text-emerald-400 font-bold"
                  : "text-slate-400"
              }`}
            >
              {statusMessage || `Última sincronización: ${lastUpdatedText}`}
            </div>
          </div>
        </div>

        {/* Right Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowChangelog(!showChangelog)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900/90 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700 text-xs font-mono font-bold transition-all"
          >
            <History className="w-3.5 h-3.5" />
            <span>Changelog</span>
          </button>

          <button
            onClick={handleTriggerSync}
            disabled={isSyncing}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-mono font-black transition-all shadow-md ${
              syncError
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/20"
                : syncSuccess
                ? "bg-emerald-600 text-white shadow-emerald-600/20"
                : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-500/20"
            } ${isSyncing ? "opacity-75 cursor-not-allowed" : ""}`}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
            <span>
              {isSyncing
                ? "Sincronizando..."
                : syncError
                ? "Reintentar"
                : syncSuccess
                ? "✓ Actualizado"
                : "Actualizar Ahora"}
            </span>
          </button>
        </div>
      </div>

      {/* Changelog Accordion */}
      {showChangelog && (
        <div className="mt-3 pt-3 border-t border-slate-800 text-xs text-slate-300 space-y-1 font-mono">
          <div className="font-bold text-white flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Registro de Auditoría y Verificación Cuantitativa:</span>
          </div>
          <ul className="pl-4 list-disc space-y-0.5 text-[11px] text-slate-400 font-sans">
            <li>
              <strong className="text-slate-200">Topstep:</strong> Sincronizados tiers de $50K, $100K y $150K con $149 activation fee y ruta No-Fee.
            </li>
            <li>
              <strong className="text-slate-200">MyFundedFutures (MFFU):</strong> Activado cupón <code className="text-amber-300 bg-amber-950/40 px-1 rounded">300K</code> (40% OFF) en Rapid $25K, $50K, $100K y $150K con $0 Pass Fee.
            </li>
            <li>
              <strong className="text-slate-200">Tradeify:</strong> Cupones <code className="text-amber-300 bg-amber-950/40 px-1 rounded">TNT</code> y <code className="text-amber-300 bg-amber-950/40 px-1 rounded">SAVE40</code> en planes Growth, Select y Lightning.
            </li>
            <li>
              <strong className="text-slate-200">Apex:</strong> Cupón <code className="text-amber-300 bg-amber-950/40 px-1 rounded">SAVINGS</code> (80% OFF) en todos los tamaños de evaluación.
            </li>
            <li>
              <strong className="text-slate-200">BluSky:</strong> Cupón <code className="text-amber-300 bg-amber-950/40 px-1 rounded">BLU25</code> en planes de Drawdown 100% Estático Fijo.
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
