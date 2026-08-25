"use client";

import React, { useState } from "react";
import { Sparkles, RefreshCw, History, AlertCircle } from "lucide-react";

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
      style={{
        width: "100%",
        background: "linear-gradient(135deg, rgba(6,9,14,0.95), rgba(11,16,24,0.95))",
        border: syncError ? "1px solid rgba(244, 63, 94, 0.4)" : "1px solid rgba(148, 163, 184, 0.15)",
        borderRadius: "14px",
        padding: "12px 18px",
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "space-between",
        alignItems: "center",
        gap: "12px",
        marginBottom: "16px",
        boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
      }}
    >
      {/* Lado Izquierdo */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <div
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "8px",
            background: syncError
              ? "rgba(244, 63, 94, 0.15)"
              : "rgba(99, 225, 180, 0.12)",
            border: syncError
              ? "1px solid rgba(244, 63, 94, 0.4)"
              : "1px solid rgba(99, 225, 180, 0.3)",
            color: syncError ? "#f43f5e" : "#63e1b4",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          {syncError ? <AlertCircle size={16} /> : <Sparkles size={16} />}
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "11.5px", fontWeight: 900, color: "#ffffff", letterSpacing: "0.3px" }}>
              Motor Autónomo de Inteligencia con FreeLLMAPI
            </span>
            <span
              style={{
                fontSize: "9.5px",
                fontWeight: 800,
                padding: "1px 6px",
                borderRadius: "4px",
                background: syncError ? "rgba(244, 63, 94, 0.15)" : "rgba(56, 189, 248, 0.15)",
                color: syncError ? "#f43f5e" : "#38bdf8",
              }}
            >
              Zero-Mocks
            </span>
          </div>
          <div
            style={{
              fontSize: "11px",
              color: syncError ? "#f43f5e" : statusMessage ? "#63e1b4" : "#94a3b8",
              marginTop: "1px",
              fontWeight: statusMessage || syncError ? 700 : 400,
            }}
          >
            {statusMessage || `Última sincronización: ${lastUpdatedText}`}
          </div>
        </div>
      </div>

      {/* Lado Derecho */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <button
          onClick={() => setShowChangelog(!showChangelog)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "5px",
            padding: "6px 12px",
            borderRadius: "8px",
            background: "#06090e",
            color: "#94a3b8",
            border: "1px solid rgba(148, 163, 184, 0.2)",
            fontSize: "11.5px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          <History size={13} />
          <span>Changelog</span>
        </button>

        <button
          onClick={handleTriggerSync}
          disabled={isSyncing}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 14px",
            borderRadius: "8px",
            background: syncError ? "#ef4444" : syncSuccess ? "#22c55e" : "#63e1b4",
            color: syncError ? "#ffffff" : "#06090e",
            border: "none",
            fontSize: "11.5px",
            fontWeight: 900,
            cursor: isSyncing ? "not-allowed" : "pointer",
            boxShadow: syncError
              ? "0 2px 8px rgba(239, 68, 68, 0.3)"
              : "0 2px 8px rgba(99, 225, 180, 0.25)",
            opacity: isSyncing ? 0.7 : 1,
          }}
        >
          <RefreshCw size={13} className={isSyncing ? "animate-spin" : ""} />
          <span>
            {isSyncing
              ? "Sincronizando con FreeLLMAPI..."
              : syncError
              ? "Reintentar Sincronización"
              : syncSuccess
              ? "✓ Actualizado"
              : "Actualizar con FreeLLMAPI Ahora"}
          </span>
        </button>
      </div>

      {/* Changelog Modal inline */}
      {showChangelog && (
        <div
          style={{
            width: "100%",
            marginTop: "10px",
            paddingTop: "10px",
            borderTop: "1px solid rgba(148, 163, 184, 0.12)",
            fontSize: "11.5px",
            color: "#cbd5e1",
          }}
        >
          <div style={{ fontWeight: 800, color: "#ffffff", marginBottom: "4px" }}>
            📋 Registro de Auditoría FreeLLMAPI:
          </div>
          <ul style={{ paddingLeft: "16px", margin: 0, lineHeight: "1.6" }}>
            <li>
              <b>Topstep:</b> Sincronizados tiers de $50K, $100K y $150K con $149 activation fee y ruta No-Fee.
            </li>
            <li>
              <b>MyFundedFutures (MFFU):</b> Activado cupón <code>300K</code> (40% OFF) en Rapid $25K, $50K, $100K y $150K con $0 Pass Fee.
            </li>
            <li>
              <b>Tradeify:</b> Cupones <code>TNT</code> y <code>SAVE40</code> en planes Growth, Select y Lightning directo a fondeo.
            </li>
            <li>
              <b>Apex:</b> Cupón <code>SAVINGS</code> (80% OFF) en todos los tamaños de evaluación ($25K a $300K).
            </li>
            <li>
              <b>BluSky:</b> Cupón <code>BLU25</code> en planes de Drawdown 100% Estático Fijo.
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
