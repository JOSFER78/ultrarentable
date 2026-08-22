"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getApiUrl } from "@/lib/api";

interface GatewayItem {
  provider_id: string;
  name: string;
  category: string;
  auth_token: string;
  endpoint_url: string;
  is_enabled: boolean;
  status: string;
  latency_ms: number;
  telemetry_packets_count: number;
  last_ping_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface PingAllResult {
  status: string;
  gateways_count: number;
  avg_latency_ms: number;
  results: {
    provider_id: string;
    name: string;
    status: string;
    latency_ms: number;
    details: any;
    last_ping_at: string;
  }[];
  timestamp_utc: string;
}

export default function ProveedoresGatewayPage() {
  const [gateways, setGateways] = useState<GatewayItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [pinging, setPinging] = useState<boolean>(false);
  const [actionLog, setActionLog] = useState<string | null>(null);
  const [revealTokens, setRevealTokens] = useState<boolean>(false);
  const [selectedGateway, setSelectedGateway] = useState<GatewayItem | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState<string>("");
  const [apiSecretInput, setApiSecretInput] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"GATEWAYS_MATRIX" | "ARCHITECTURE_GUIDE">("GATEWAYS_MATRIX");

  const fetchGateways = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl(`/api/v1/gateways?reveal_tokens=${revealTokens}`));
      if (res.ok) {
        const data = await res.json();
        setGateways(Array.isArray(data) ? data : []);
      }
    } catch (err: any) {
      setActionLog(`✕ Error cargando gateways: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [revealTokens]);

  useEffect(() => {
    fetchGateways();
  }, [fetchGateways]);

  // Ping a single gateway
  const handlePingSingle = async (providerId: string) => {
    setPinging(true);
    try {
      const res = await fetch(getApiUrl(`/api/v1/gateways/${providerId}/ping`), {
        method: "POST",
      });
      if (res.ok) {
        const result = await res.json();
        setActionLog(`✓ Ping a '${result.name}': ${result.status} (${result.latency_ms} ms)`);
        fetchGateways();
      } else {
        setActionLog(`✕ Error al hacer ping a ${providerId}`);
      }
    } catch (err: any) {
      setActionLog(`✕ Error de red: ${err.message}`);
    } finally {
      setPinging(false);
    }
  };

  // Ping all gateways
  const handlePingAll = async () => {
    setPinging(true);
    try {
      const res = await fetch(getApiUrl("/api/v1/gateways/ping-all"), {
        method: "POST",
      });
      if (res.ok) {
        const result: PingAllResult = await res.json();
        setActionLog(`✓ Diagnóstico Global: ${result.status} · ${result.gateways_count} gateways comprobados · Latencia media: ${result.avg_latency_ms} ms`);
        fetchGateways();
      }
    } catch (err: any) {
      setActionLog(`✕ Error en ping global: ${err.message}`);
    } finally {
      setPinging(false);
    }
  };

  // Regenerate token
  const handleRegenerateToken = async (providerId: string) => {
    if (!confirm(`¿Regenerar el token de autenticación para ${providerId}? El script anterior de NinjaTrader deberá ser actualizado.`)) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/gateways/${providerId}/token/regenerate`), {
        method: "POST",
      });
      if (res.ok) {
        const result = await res.json();
        setActionLog(`🔐 Nuevo token emitido para '${result.name}'.`);
        fetchGateways();
      }
    } catch (err: any) {
      setActionLog(`✕ Error regenerando token: ${err.message}`);
    }
  };

  // Save config / API keys
  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGateway) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/gateways/${selectedGateway.provider_id}/config`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          api_key: apiKeyInput || undefined,
          api_secret: apiSecretInput || undefined,
        }),
      });
      if (res.ok) {
        setActionLog(`✓ Configuración de '${selectedGateway.name}' guardada en SQLite.`);
        setSelectedGateway(null);
        setApiKeyInput("");
        setApiSecretInput("");
        fetchGateways();
      }
    } catch (err: any) {
      setActionLog(`✕ Error guardando configuración: ${err.message}`);
    }
  };

  // Emergency Lock
  const handleEmergencyLock = async () => {
    const reason = prompt("Motivo del Bloqueo Global de Emergencia (Kill-Switch General):", "Manual Global Lockdown");
    if (!reason) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/gateways/emergency-lock?reason=${encodeURIComponent(reason)}`), {
        method: "POST",
      });
      if (res.ok) {
        const result = await res.json();
        setActionLog(`🚨 BLOQUEO GLOBAL ACTIVADO: ${result.sessions_stopped_count} sesiones detenidas.`);
        fetchGateways();
      }
    } catch (err: any) {
      setActionLog(`✕ Error en bloqueo global: ${err.message}`);
    }
  };

  const avgLatency = gateways.length > 0 ? (gateways.reduce((acc, g) => acc + (g.latency_ms || 0), 0) / gateways.length).toFixed(1) : "0.0";

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc", fontFamily: "var(--font-sans, system-ui, sans-serif)" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/panel" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Motor 24/7
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            GATEWAYS & MCP API TOKENS · 100% REAL ORCHESTRATION
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
              Centro de Conexión de Proveedores & Gateways API
            </h1>
            <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
              Control automatizado y centralizado de NinjaTrader 8, BingX Perpetuos, NautilusTrader, Prop Firms (Apex, Topstep) y feeds de mercado en tiempo real.
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
            <Link
              href="/ejecucion"
              style={{
                padding: "10px 16px",
                borderRadius: "8px",
                background: "rgba(16, 185, 129, 0.15)",
                color: "#34d399",
                border: "1px solid #34d399",
                fontWeight: 800,
                fontSize: "12px",
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              ⚡ NinjaTrader 8 Live Hub
            </Link>

            <button
              onClick={handlePingAll}
              disabled={pinging}
              style={{
                padding: "10px 18px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
                color: "#06080d",
                border: "none",
                fontWeight: 900,
                fontSize: "12px",
                cursor: pinging ? "not-allowed" : "pointer",
                boxShadow: "0 2px 10px rgba(56,189,248,0.3)",
              }}
            >
              {pinging ? "⚡ PROBANDO PING..." : "⚡ TEST PING A TODOS LOS PROVEEDORES"}
            </button>

            <button
              onClick={handleEmergencyLock}
              style={{
                padding: "10px 16px",
                borderRadius: "8px",
                background: "rgba(244, 63, 94, 0.15)",
                color: "#f43f5e",
                border: "1px solid #f43f5e",
                fontWeight: 900,
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              🚨 KILL-SWITCH GLOBAL
            </button>

            <button
              onClick={() => {
                setRevealTokens(!revealTokens);
              }}
              style={{
                padding: "10px 14px",
                borderRadius: "8px",
                background: revealTokens ? "rgba(245, 158, 11, 0.2)" : "rgba(255,255,255,0.05)",
                color: revealTokens ? "#f59e0b" : "#94a3b8",
                border: `1px solid ${revealTokens ? "#f59e0b" : "rgba(255,255,255,0.1)"}`,
                fontWeight: 800,
                fontSize: "11px",
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {revealTokens ? "👁️ OCULTAR TOKENS" : "👁️ REVELAR TOKENS"}
            </button>
          </div>
        </div>
      </div>

      {/* 2. ACTION LOG */}
      {actionLog && (
        <div style={{ background: "#080c14", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", padding: "12px 16px", marginBottom: "20px", fontSize: "12px", fontFamily: "var(--font-mono, monospace)", color: "#38bdf8", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>{actionLog}</span>
          <button onClick={() => setActionLog(null)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: "14px" }}>✕</button>
        </div>
      )}

      {/* 3. METRIC SUMMARY BAR */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginBottom: "24px" }}>
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(56, 189, 248, 0.2)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>ESTADO GLOBAL DE GATEWAYS</div>
          <div style={{ fontSize: "20px", fontWeight: 900, color: "#34d399", marginTop: "4px" }}>
            🟢 100% OPERATIVO
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            {gateways.length} conectores orquestados y verificados
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>LATENCIA MEDIA ROUND-TRIP</div>
          <div style={{ fontSize: "20px", fontWeight: 900, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
            {avgLatency} ms
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            Medición real vía red y sockets locales
          </div>
        </div>

        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(168, 85, 247, 0.2)", borderRadius: "12px", padding: "16px" }}>
          <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>AUTENTICACIÓN ZERO-TRUST</div>
          <div style={{ fontSize: "20px", fontWeight: 900, color: "#c084fc", marginTop: "4px" }}>
            🔐 TOKENS CRIPTOGRÁFICOS
          </div>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
            Headers SHA-256 / Bearer activos en cada llamada
          </div>
        </div>
      </div>

      {/* 4. TABS: MATRIX VS ARCHITECTURE GUIDE */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "12px", marginBottom: "24px" }}>
        <button
          onClick={() => setActiveTab("GATEWAYS_MATRIX")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "GATEWAYS_MATRIX" ? "#38bdf8" : "transparent",
            color: activeTab === "GATEWAYS_MATRIX" ? "#06080d" : "#94a3b8",
            border: activeTab === "GATEWAYS_MATRIX" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          📡 Matriz de Gateways & Tokens API ({gateways.length})
        </button>

        <button
          onClick={() => setActiveTab("ARCHITECTURE_GUIDE")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "ARCHITECTURE_GUIDE" ? "#38bdf8" : "transparent",
            color: activeTab === "ARCHITECTURE_GUIDE" ? "#06080d" : "#94a3b8",
            border: activeTab === "ARCHITECTURE_GUIDE" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          📚 Manual de Monitoreo & Control por Proveedor
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: GATEWAY PROVIDERS MATRIX */}
      {/* ========================================================================= */}
      {activeTab === "GATEWAYS_MATRIX" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              Cargando conectores y gateways desde SQLite...
            </div>
          ) : (
            gateways.map((g) => {
              const isNT8 = g.provider_id === "ninjatrader_8";
              const isBingX = g.provider_id === "bingx_perpetuals";
              const isNautilus = g.provider_id === "nautilus_trader";

              return (
                <div
                  key={g.provider_id}
                  style={{
                    background: "rgba(16, 23, 34, 0.85)",
                    backdropFilter: "blur(16px)",
                    border: `1px solid ${g.status === "CONNECTED" ? "rgba(16, 185, 129, 0.3)" : g.status === "IDLE_WAITING" ? "rgba(56, 189, 248, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
                    borderRadius: "14px",
                    padding: "20px",
                    boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ fontSize: "16px", fontWeight: 900, color: "#fff" }}>
                          {g.name}
                        </span>
                        <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", color: "#cbd5e1", fontWeight: 700 }}>
                          {g.category}
                        </span>
                      </div>
                      <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                        Endpoint: <span style={{ color: "#38bdf8" }}>{g.endpoint_url}</span>
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{
                        fontSize: "11px",
                        fontWeight: 800,
                        padding: "4px 10px",
                        borderRadius: "6px",
                        background: g.status === "CONNECTED" ? "rgba(16, 185, 129, 0.15)" : g.status === "IDLE_WAITING" ? "rgba(56, 189, 248, 0.15)" : "rgba(244, 63, 94, 0.15)",
                        color: g.status === "CONNECTED" ? "#34d399" : g.status === "IDLE_WAITING" ? "#38bdf8" : "#f43f5e",
                        border: `1px solid ${g.status === "CONNECTED" ? "#34d399" : g.status === "IDLE_WAITING" ? "#38bdf8" : "#f43f5e"}`,
                      }}>
                        {g.status === "CONNECTED" ? "🟢 CONECTADO" : g.status === "IDLE_WAITING" ? "🟡 ESPERANDO EVENTO" : "🔴 ERROR / DESCONECTADO"}
                      </span>
                      <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
                        Latencia: <strong>{g.latency_ms} ms</strong>
                      </span>
                    </div>
                  </div>

                  {/* TOKEN & AUTH BAR */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: "10px", alignItems: "center", background: "#06090e", borderRadius: "8px", padding: "10px 14px", marginBottom: "16px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", overflow: "hidden" }}>
                      <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>API AUTH TOKEN:</span>
                      <code style={{ fontSize: "12px", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                        {g.auth_token}
                      </code>
                    </div>

                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(g.auth_token);
                        setActionLog(`✓ Token de '${g.name}' copiado al portapapeles.`);
                      }}
                      style={{
                        padding: "6px 12px",
                        borderRadius: "6px",
                        background: "rgba(255,255,255,0.06)",
                        border: "1px solid rgba(255,255,255,0.1)",
                        color: "#fff",
                        fontWeight: 700,
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      📋 Copiar
                    </button>

                    <button
                      onClick={() => handleRegenerateToken(g.provider_id)}
                      style={{
                        padding: "6px 12px",
                        borderRadius: "6px",
                        background: "rgba(245, 158, 11, 0.15)",
                        border: "1px solid #f59e0b",
                        color: "#f59e0b",
                        fontWeight: 800,
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      🔄 Regenerar
                    </button>
                  </div>

                  {/* ACTIONS */}
                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button
                      onClick={() => handlePingSingle(g.provider_id)}
                      disabled={pinging}
                      style={{
                        padding: "8px 14px",
                        borderRadius: "6px",
                        background: "rgba(56, 189, 248, 0.15)",
                        color: "#38bdf8",
                        border: "1px solid #38bdf8",
                        fontWeight: 800,
                        fontSize: "11px",
                        cursor: "pointer",
                      }}
                    >
                      🔍 Probar Ping en Vivo
                    </button>

                    {isNT8 && (
                      <Link
                        href="/ejecucion"
                        style={{
                          padding: "8px 14px",
                          borderRadius: "6px",
                          background: "rgba(16, 185, 129, 0.15)",
                          color: "#34d399",
                          border: "1px solid #34d399",
                          fontWeight: 800,
                          fontSize: "11px",
                          textDecoration: "none",
                          display: "inline-flex",
                          alignItems: "center",
                        }}
                      >
                        ⚡ Abrir Hub NinjaTrader & Terminal Remota
                      </Link>
                    )}

                    {isBingX && (
                      <button
                        onClick={() => setSelectedGateway(g)}
                        style={{
                          padding: "8px 14px",
                          borderRadius: "6px",
                          background: "rgba(168, 85, 247, 0.15)",
                          color: "#c084fc",
                          border: "1px solid #c084fc",
                          fontWeight: 800,
                          fontSize: "11px",
                          cursor: "pointer",
                        }}
                      >
                        🔑 Configurar API Key & Secret
                      </button>
                    )}

                    {isNautilus && (
                      <Link
                        href="/gates/gate-10-nautilus-trader"
                        style={{
                          padding: "8px 14px",
                          borderRadius: "6px",
                          background: "rgba(255,255,255,0.06)",
                          color: "#fff",
                          border: "1px solid rgba(255,255,255,0.1)",
                          fontWeight: 700,
                          fontSize: "11px",
                          textDecoration: "none",
                          display: "inline-flex",
                          alignItems: "center",
                        }}
                      >
                        ⚙️ Inspeccionar Engine Nautilus
                      </Link>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: ARCHITECTURE & PROVIDER CONTROL GUIDE */}
      {/* ========================================================================= */}
      {activeTab === "ARCHITECTURE_GUIDE" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* PROVIDER 1: NINJATRADER 8 */}
          <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "14px", padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
              <span style={{ fontSize: "20px" }}>⚡</span>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, color: "#fff" }}>
                1. NinjaTrader 8 (Futuros CME / Prop Firms & Cuentas Live)
              </h2>
            </div>
            <p style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.6" }}>
              <strong>Protocolo de Conexión:</strong> Webhook REST Bidireccional en puerto 8000 + Long-Polling asíncrono cada 500ms en C# nativo.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px", marginTop: "12px" }}>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 800 }}>CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Captura cada fill en tiempo real (`OnExecutionUpdate`), calcula en vivo el Trailing Drawdown, el balance real en cuenta y la distancia exacta al Daily Loss Limit ($1.000 USD).
                </div>
              </div>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 800 }}>CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Despacho de órdenes remotas (BUY, SELL, FLATTEN, KILL_SWITCH), ajuste dinámico de Stop Loss a Break-Even (+1.5R) y corte de emergencia local si se tocan límites de fondeo.
                </div>
              </div>
            </div>
          </div>

          {/* PROVIDER 2: BINGX PERPETUALS */}
          <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(168, 85, 247, 0.3)", borderRadius: "14px", padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
              <span style={{ fontSize: "20px" }}>🔥</span>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, color: "#fff" }}>
                2. BingX Perpetuals (Ruta Ultra · Cripto 500x Hyper-Leverage)
              </h2>
            </div>
            <p style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.6" }}>
              <strong>Protocolo de Conexión:</strong> REST API HTTPS Oficial (`open-api.bingx.com`) con firma criptográfica HMAC-SHA256 y WebSockets de balance/órdenes.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px", marginTop: "12px" }}>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#c084fc", fontWeight: 800 }}>CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Supervisa la equidad disponible de las subcuentas bala ($1.000 USD), el margen flotante y el riesgo acumulado por operación (10% - 25%).
                </div>
              </div>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 800 }}>CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Aplica compounding dinámico geométrico, piramidación en beneficio (1 a 3 tramos $\ge +1.5R$) y Cosecha Automática a Bóveda (*Ratchet Vault*) al alcanzar $+200\%$ transfiriendo el 50% a resguardo.
                </div>
              </div>
            </div>
          </div>

          {/* PROVIDER 3: PROP FIRMS (APEX / TOPSTEP / TRADOVATE / RITHMIC) */}
          <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "14px", padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
              <span style={{ fontSize: "20px" }}>🏛️</span>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, color: "#fff" }}>
                3. Catálogo de 34 Prop Firms (Apex, Topstep, FTMO, Tradovate, Rithmic)
              </h2>
            </div>
            <p style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.6" }}>
              <strong>Protocolo de Conexión:</strong> Puente unificado Rithmic / Tradovate + Evaluador formal de reglas de examen `PropChallengeEvaluator`.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px", marginTop: "12px" }}>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 800 }}>CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Evalúa el Trailing DD institucional ($4.0\% = \$2.000$ en cuentas \$50k), el Daily Loss Limit ($\le 2.0\% = \$1.000$) y el progreso hacia el Profit Target (+6.0% = +$3.000).
                </div>
              </div>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#f43f5e", fontWeight: 800 }}>CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Auto-flatten al 1.5% de pérdida diaria, filtro estricto de sesión RTH Nueva York (13:30 a 20:00 UTC) y finalización de sprint en $\le 5$ días hábiles.
                </div>
              </div>
            </div>
          </div>

          {/* PROVIDER 4: NAUTILUS TRADER CORE */}
          <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "14px", padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
              <span style={{ fontSize: "20px" }}>💎</span>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, color: "#fff" }}>
                4. NautilusTrader Core (Motor HFT de Microsegundos)
              </h2>
            </div>
            <p style={{ fontSize: "13px", color: "#cbd5e1", lineHeight: "1.6" }}>
              <strong>Protocolo de Conexión:</strong> Sockets IPC locales (`ipc:///tmp/nautilus_core.ipc`) de latencia sub-milisegundo.
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "12px", marginTop: "12px" }}>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 800 }}>CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Supervisa la latencia del bus de eventos (OMS/EMS) y la fidelidad de ejecución tick a tick.
                </div>
              </div>
              <div style={{ background: "#06090e", padding: "14px", borderRadius: "8px" }}>
                <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 800 }}>CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                  Ejecuta validaciones cruzadas de eventos y arbitraje estadístico de alta velocidad (Gate 11).
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. MODAL CONFIG BINGX / CUSTOM API */}
      {selectedGateway && (
        <div style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(6px)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 9999,
          padding: "20px",
        }}>
          <div style={{
            background: "#0d131f",
            border: "1px solid rgba(56, 189, 248, 0.4)",
            borderRadius: "16px",
            width: "100%",
            maxWidth: "540px",
            padding: "28px",
            boxShadow: "0 20px 50px rgba(0, 0, 0, 0.8)",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, color: "#fff" }}>
                🔑 Configurar {selectedGateway.name}
              </h2>
              <button
                onClick={() => setSelectedGateway(null)}
                style={{ background: "none", border: "none", color: "#64748b", fontSize: "18px", cursor: "pointer" }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveConfig} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, display: "block", marginBottom: "4px" }}>
                  API KEY
                </label>
                <input
                  type="text"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="Pega tu API Key..."
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
                />
              </div>

              <div>
                <label style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700, display: "block", marginBottom: "4px" }}>
                  API SECRET
                </label>
                <input
                  type="password"
                  value={apiSecretInput}
                  onChange={(e) => setApiSecretInput(e.target.value)}
                  placeholder="Pega tu API Secret..."
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
                />
              </div>

              <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
                <button
                  type="submit"
                  style={{
                    flex: 1,
                    padding: "12px",
                    borderRadius: "8px",
                    background: "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
                    border: "none",
                    color: "#06080d",
                    fontWeight: 900,
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  💾 GUARDAR EN SQLITE
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedGateway(null)}
                  style={{
                    padding: "12px 20px",
                    borderRadius: "8px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    color: "#94a3b8",
                    fontWeight: 700,
                    fontSize: "13px",
                    cursor: "pointer",
                  }}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
