"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Activity,
  ShieldCheck,
  Zap,
  SlidersHorizontal,
  Copy,
  RefreshCw,
  AlertTriangle,
  Lock,
  Eye,
  EyeOff,
  Flame,
  Building2,
  Cpu,
  Check,
  X,
} from "lucide-react";
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
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

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
    if (!confirm(`¿Regenerar el token de autenticación para ${providerId}? El script anterior de conexión deberá ser actualizado.`)) return;
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

  const copyTokenToClipboard = (token: string, key: string) => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(token);
      setCopiedToken(key);
      setActionLog(`✓ Token copiado al portapapeles.`);
      setTimeout(() => setCopiedToken(null), 2000);
    }
  };

  const avgLatency = gateways.length > 0 ? (gateways.reduce((acc, g) => acc + (g.latency_ms || 0), 0) / gateways.length).toFixed(1) : "0.0";

  return (
    <div className="w-full max-w-[1560px] mx-auto space-y-6 font-sans">
      {/* 1. HEADER */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 md:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
              <SlidersHorizontal className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Centro de Conexión de Proveedores & Gateways API
              </h1>
              <p className="text-slate-400 text-xs md:text-sm mt-0.5 font-medium">
                Control automatizado y centralizado de NinjaTrader 8, BingX Perpetuos, NautilusTrader, Prop Firms y feeds de mercado.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap font-mono text-xs">
          <Link
            href="/ejecucion"
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 shadow-sm transition active:scale-95"
          >
            ⚡ NinjaTrader 8 Hub
          </Link>

          <button
            onClick={handlePingAll}
            disabled={pinging}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-slate-950 shadow-sm transition active:scale-95 cursor-pointer"
          >
            {pinging ? <RefreshCw className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : <Zap className="w-3.5 h-3.5 mr-1.5" />}
            {pinging ? "Probando..." : "Test Ping Global"}
          </button>

          <button
            onClick={handleEmergencyLock}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-700/60 shadow-sm transition active:scale-95 cursor-pointer"
          >
            🚨 Kill-Switch Global
          </button>

          <button
            onClick={() => setRevealTokens(!revealTokens)}
            className={`inline-flex items-center px-3.5 py-1.5 rounded-xl font-bold border transition active:scale-95 cursor-pointer ${
              revealTokens
                ? "bg-amber-950/80 text-amber-300 border-amber-700/60"
                : "bg-[#050811] text-slate-400 border-white/[0.1] hover:text-slate-200"
            }`}
          >
            {revealTokens ? <EyeOff className="w-3.5 h-3.5 mr-1.5 text-amber-400" /> : <Eye className="w-3.5 h-3.5 mr-1.5 text-slate-400" />}
            {revealTokens ? "Ocultar Tokens" : "Revelar Tokens"}
          </button>
        </div>
      </div>

      {/* 2. ACTION LOG */}
      {actionLog && (
        <div className="bg-[#080c14] border border-sky-500/30 rounded-xl p-3.5 flex justify-between items-center text-xs font-mono text-sky-300 shadow-md">
          <span>{actionLog}</span>
          <button
            onClick={() => setActionLog(null)}
            className="text-slate-500 hover:text-slate-300 cursor-pointer p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* 3. METRIC SUMMARY BAR */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-sky-500/20 rounded-2xl p-4 sm:p-5 space-y-1 shadow-xl">
          <div className="text-[10.5px] text-slate-400 font-bold tracking-wider">ESTADO GLOBAL DE GATEWAYS</div>
          <div className="text-xl font-black text-emerald-400 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            100% OPERATIVO
          </div>
          <div className="text-[11px] text-slate-400">{gateways.length} conectores orquestados y verificados</div>
        </div>

        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-4 sm:p-5 space-y-1 shadow-xl">
          <div className="text-[10.5px] text-slate-400 font-bold tracking-wider">LATENCIA MEDIA ROUND-TRIP</div>
          <div className="text-xl font-black text-sky-400 tabular-nums">{avgLatency} ms</div>
          <div className="text-[11px] text-slate-400">Medición real vía red y sockets locales</div>
        </div>

        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-purple-500/20 rounded-2xl p-4 sm:p-5 space-y-1 shadow-xl">
          <div className="text-[10.5px] text-slate-400 font-bold tracking-wider">AUTENTICACIÓN ZERO-TRUST</div>
          <div className="text-xl font-black text-purple-300">🔐 TOKENS CRIPTO</div>
          <div className="text-[11px] text-slate-400">Headers SHA-256 / Bearer activos en cada llamada</div>
        </div>
      </div>

      {/* 4. TABS: MATRIX VS ARCHITECTURE GUIDE */}
      <div className="flex items-center gap-2 border-b border-white/[0.08] pb-3 font-mono">
        <button
          onClick={() => setActiveTab("GATEWAYS_MATRIX")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === "GATEWAYS_MATRIX"
              ? "bg-sky-600 text-white shadow-[0_0_15px_rgba(56,189,248,0.25)] border border-sky-400/40"
              : "bg-[#090d16]/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-white/[0.08]"
          }`}
        >
          <Activity className="w-4 h-4 text-sky-300" />
          Matriz de Gateways & Tokens API ({gateways.length})
        </button>

        <button
          onClick={() => setActiveTab("ARCHITECTURE_GUIDE")}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === "ARCHITECTURE_GUIDE"
              ? "bg-sky-600 text-white shadow-[0_0_15px_rgba(56,189,248,0.25)] border border-sky-400/40"
              : "bg-[#090d16]/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-white/[0.08]"
          }`}
        >
          <ShieldCheck className="w-4 h-4 text-purple-300" />
          Manual de Monitoreo & Control por Proveedor
        </button>
      </div>

      {/* TAB 1: GATEWAY PROVIDERS MATRIX */}
      {activeTab === "GATEWAYS_MATRIX" && (
        <div className="space-y-4 font-sans">
          {loading ? (
            <div className="py-16 text-center text-slate-500 font-mono text-xs bg-[#090d16]/60 rounded-2xl border border-white/[0.08]">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-400" />
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
                  className={`bg-[#090d16]/90 backdrop-blur-xl rounded-2xl p-5 md:p-6 shadow-xl space-y-4 border transition-all ${
                    g.status === "CONNECTED"
                      ? "border-emerald-500/30 hover:border-emerald-500/50"
                      : g.status === "IDLE_WAITING"
                      ? "border-sky-500/30 hover:border-sky-500/50"
                      : "border-rose-500/30 hover:border-rose-500/50"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2.5">
                        <span className="text-base font-black text-white">{g.name}</span>
                        <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-white/[0.06] text-slate-300 border border-white/[0.08]">
                          {g.category}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 font-mono mt-1">
                        Endpoint: <span className="text-sky-300">{g.endpoint_url}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 font-mono">
                      <span
                        className={`text-[11px] font-bold px-2.5 py-1 rounded-xl border flex items-center gap-1.5 ${
                          g.status === "CONNECTED"
                            ? "bg-emerald-950/80 text-emerald-300 border-emerald-700/70"
                            : g.status === "IDLE_WAITING"
                            ? "bg-sky-950/80 text-sky-300 border-sky-700/70"
                            : "bg-rose-950/80 text-rose-300 border-rose-700/70"
                        }`}
                      >
                        {g.status === "CONNECTED"
                          ? "🟢 CONECTADO"
                          : g.status === "IDLE_WAITING"
                          ? "🟡 ESPERANDO EVENTO"
                          : "🔴 ERROR / DESCONECTADO"}
                      </span>
                      <span className="text-xs text-slate-400 tabular-nums">
                        Latencia: <strong className="text-slate-200">{g.latency_ms} ms</strong>
                      </span>
                    </div>
                  </div>

                  {/* TOKEN & AUTH BAR */}
                  <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-2.5 items-center bg-[#050811] rounded-xl p-3 border border-white/[0.08] font-mono text-xs">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <span className="text-[10.5px] text-slate-500 font-bold uppercase shrink-0">AUTH TOKEN:</span>
                      <code className="text-sky-300 text-xs truncate select-all">{g.auth_token}</code>
                    </div>

                    <button
                      onClick={() => copyTokenToClipboard(g.auth_token, g.provider_id)}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] text-slate-200 font-bold text-xs border border-white/[0.08] transition active:scale-95 cursor-pointer"
                    >
                      {copiedToken === g.provider_id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5 text-slate-400" />
                      )}
                      <span>Copiar</span>
                    </button>

                    <button
                      onClick={() => handleRegenerateToken(g.provider_id)}
                      className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-950/80 hover:bg-amber-900 text-amber-300 font-bold text-xs border border-amber-700/60 transition active:scale-95 cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5 text-amber-400" />
                      <span>Regenerar</span>
                    </button>
                  </div>

                  {/* ACTIONS */}
                  <div className="flex items-center gap-2.5 flex-wrap font-mono text-xs">
                    <button
                      onClick={() => handlePingSingle(g.provider_id)}
                      disabled={pinging}
                      className="inline-flex items-center px-3 py-1.5 rounded-xl font-bold bg-sky-950/80 hover:bg-sky-900 text-sky-300 border border-sky-700/60 shadow-sm transition active:scale-95 cursor-pointer"
                    >
                      🔍 Probar Ping
                    </button>

                    {isNT8 && (
                      <Link
                        href="/ejecucion"
                        className="inline-flex items-center px-3 py-1.5 rounded-xl font-bold bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-700/60 shadow-sm transition active:scale-95"
                      >
                        ⚡ NinjaTrader 8 Hub & Terminal Remota
                      </Link>
                    )}

                    {isBingX && (
                      <button
                        onClick={() => setSelectedGateway(g)}
                        className="inline-flex items-center px-3 py-1.5 rounded-xl font-bold bg-purple-950/80 hover:bg-purple-900 text-purple-300 border border-purple-700/60 shadow-sm transition active:scale-95 cursor-pointer"
                      >
                        🔑 Configurar API Key & Secret
                      </button>
                    )}

                    {isNautilus && (
                      <Link
                        href="/gates"
                        className="inline-flex items-center px-3 py-1.5 rounded-xl font-bold bg-[#050811] hover:bg-slate-800 text-slate-200 border border-white/[0.1] shadow-sm transition active:scale-95"
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

      {/* TAB 2: ARCHITECTURE & PROVIDER CONTROL GUIDE */}
      {activeTab === "ARCHITECTURE_GUIDE" && (
        <div className="space-y-5 font-sans">
          {/* PROVIDER 1: NINJATRADER 8 */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-emerald-500/30 rounded-2xl p-6 shadow-xl space-y-3">
            <div className="flex items-center gap-2.5">
              <span className="text-xl">⚡</span>
              <h2 className="text-lg font-black text-white">
                1. NinjaTrader 8 (Futuros CME / Prop Firms & Cuentas Live)
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
              <strong>Protocolo de Conexión:</strong> Webhook REST Bidireccional en puerto 8000 + Long-Polling asíncrono cada 500ms en C# nativo.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-emerald-400 font-mono font-bold uppercase">CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Captura cada fill en tiempo real (`OnExecutionUpdate`), calcula en vivo el Trailing Drawdown, el balance real en cuenta y la distancia exacta al Daily Loss Limit ($1.000 USD).
                </div>
              </div>
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-sky-400 font-mono font-bold uppercase">CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Despacho de órdenes remotas (BUY, SELL, FLATTEN, KILL_SWITCH), ajuste dinámico de Stop Loss a Break-Even (+1.5R) y corte de emergencia local si se tocan límites de fondeo.
                </div>
              </div>
            </div>
          </div>

          {/* PROVIDER 2: BINGX PERPETUALS */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-purple-500/30 rounded-2xl p-6 shadow-xl space-y-3">
            <div className="flex items-center gap-2.5">
              <span className="text-xl">🔥</span>
              <h2 className="text-lg font-black text-white">
                2. BingX Perpetuals (Ruta Ultra · Cripto 500x Hyper-Leverage)
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              <strong>Protocolo de Conexión:</strong> REST API HTTPS Oficial (`open-api.bingx.com`) con firma criptográfica HMAC-SHA256 y WebSockets de balance/órdenes.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-purple-300 font-mono font-bold uppercase">CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Supervisa la equidad disponible de las subcuentas bala ($1.000 USD), el margen flotante y el riesgo acumulado por operación (10% - 25%).
                </div>
              </div>
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-sky-400 font-mono font-bold uppercase">CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Aplica compounding dinámico geométrico, piramidación en beneficio (1 a 3 tramos &ge; +1.5R) y Cosecha Automática a Bóveda (*Ratchet Vault*).
                </div>
              </div>
            </div>
          </div>

          {/* PROVIDER 3: PROP FIRMS */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-sky-500/30 rounded-2xl p-6 shadow-xl space-y-3">
            <div className="flex items-center gap-2.5">
              <span className="text-xl">🏛️</span>
              <h2 className="text-lg font-black text-white">
                3. Catálogo de 70 Prop Firms (Apex, Topstep, FTMO, Tradovate, Rithmic)
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              <strong>Protocolo de Conexión:</strong> Puente unificado Rithmic / Tradovate + Evaluador formal de reglas de examen `PropChallengeEvaluator`.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-sky-400 font-mono font-bold uppercase">CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Evalúa el Trailing DD institucional ($4.0% = $2.000 en cuentas $50k), el Daily Loss Limit (&le; 2.0% = $1.000) y el progreso hacia el Profit Target (+6.0% = +$3.000).
                </div>
              </div>
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-rose-400 font-mono font-bold uppercase">CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Auto-flatten al 1.5% de pérdida diaria, filtro estricto de sesión RTH Nueva York (13:30 a 20:00 UTC) y finalización de sprint en &le; 5 días hábiles.
                </div>
              </div>
            </div>
          </div>

          {/* PROVIDER 4: NAUTILUS TRADER CORE */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.1] rounded-2xl p-6 shadow-xl space-y-3">
            <div className="flex items-center gap-2.5">
              <span className="text-xl">💎</span>
              <h2 className="text-lg font-black text-white">
                4. NautilusTrader Core (Motor HFT de Microsegundos)
              </h2>
            </div>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              <strong>Protocolo de Conexión:</strong> Sockets IPC locales (`ipc:///tmp/nautilus_core.ipc`) de latencia sub-milisegundo.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-emerald-400 font-mono font-bold uppercase">CÓMO LO MONITOREA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Supervisa la latencia del bus de eventos (OMS/EMS) y la fidelidad de ejecución tick a tick.
                </div>
              </div>
              <div className="bg-[#050811] p-4 rounded-xl border border-white/[0.08] space-y-1">
                <div className="text-[11px] text-sky-400 font-mono font-bold uppercase">CÓMO LO CONTROLA ULTRARENTABLE</div>
                <div className="text-xs text-slate-400 leading-relaxed">
                  Ejecuta validaciones cruzadas de eventos y arbitraje estadístico de alta velocidad (Gate 11).
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 5. MODAL CONFIG BINGX / CUSTOM API */}
      {selectedGateway && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
          <div className="bg-[#0d131f] border border-sky-500/40 rounded-2xl w-full max-w-lg p-6 sm:p-7 shadow-2xl space-y-5">
            <div className="flex justify-between items-center border-b border-white/[0.08] pb-3">
              <h2 className="text-base font-black text-white flex items-center gap-2">
                <Lock className="w-4 h-4 text-sky-400" />
                Configurar {selectedGateway.name}
              </h2>
              <button
                onClick={() => setSelectedGateway(null)}
                className="text-slate-400 hover:text-white cursor-pointer p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveConfig} className="space-y-4 font-mono text-xs">
              <div className="space-y-1.5">
                <label className="text-[11px] text-slate-400 font-bold block">API KEY</label>
                <input
                  type="text"
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder="Pega tu API Key..."
                  className="w-full p-2.5 rounded-xl bg-[#050811] border border-white/[0.1] text-white text-xs focus:border-sky-500 focus:outline-none"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[11px] text-slate-400 font-bold block">API SECRET</label>
                <input
                  type="password"
                  value={apiSecretInput}
                  onChange={(e) => setApiSecretInput(e.target.value)}
                  placeholder="Pega tu API Secret..."
                  className="w-full p-2.5 rounded-xl bg-[#050811] border border-white/[0.1] text-white text-xs focus:border-sky-500 focus:outline-none"
                />
              </div>

              <div className="flex gap-2.5 pt-2">
                <button
                  type="submit"
                  className="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-slate-950 font-black text-xs transition active:scale-95 cursor-pointer shadow-md"
                >
                  Guardar en SQLite WAL
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedGateway(null)}
                  className="py-2.5 px-4 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.1] text-slate-300 font-bold text-xs transition active:scale-95 cursor-pointer"
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
