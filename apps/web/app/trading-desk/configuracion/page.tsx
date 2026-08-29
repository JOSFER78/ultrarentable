"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sliders,
  Lock,
  Zap,
  RefreshCw,
  Copy,
  Check,
  ShieldCheck,
  Radio,
  Server,
  AlertCircle,
  Clock,
  User,
  Key,
  ExternalLink,
  ChevronRight,
  Wifi,
  WifiOff,
} from "lucide-react";

interface GatewayStatus {
  provider_id?: string;
  account_id?: string;
  user?: string;
  broker?: string;
  environment?: string;
  base_capital_usd?: number;
  current_equity_usd?: number;
  daily_pnl_usd?: number;
  trailing_drawdown_limit_usd?: number;
  current_drawdown_usd?: number;
  open_positions_count?: number;
  trial_expires_utc?: string;
  gateway_status?: string;
  last_ping_latency_ms?: number;
}

interface GatewayProvider {
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
}

export default function BrokerConfigPage() {
  const [gatewayData, setGatewayData] = useState<GatewayStatus | null>(null);
  const [gatewaysList, setGatewaysList] = useState<GatewayProvider[]>([]);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isPinging, setIsPinging] = useState(false);
  const [isPingingAll, setIsPingingAll] = useState(false);
  const [pingingProviderId, setPingingProviderId] = useState<string | null>(null);
  const [pingLatency, setPingLatency] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ text: string; isError: boolean } | null>(null);

  const showToast = (text: string, isError = false) => {
    setNotification({ text, isError });
    setTimeout(() => setNotification(null), 5000);
  };

  const fetchStatus = useCallback(async () => {
    setFetchError(null);
    try {
      const [statusRes, listRes] = await Promise.all([
        fetch("/api/v1/gateways/pickmytrade/status"),
        fetch("/api/v1/gateways"),
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        setGatewayData(data);
        if (data.last_ping_latency_ms != null) {
          setPingLatency(data.last_ping_latency_ms);
        }
      } else {
        setGatewayData(null);
        setFetchError(`Error ${statusRes.status}: No se pudo obtener el estado del gateway PickMyTrade.`);
      }

      if (listRes.ok) {
        const listData = await listRes.json();
        setGatewaysList(Array.isArray(listData) ? listData : []);
      }
    } catch (e: any) {
      setGatewayData(null);
      setFetchError(e.message || "Error de red al conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2500);
  };

  const handlePingProvider = async (providerId: string) => {
    setPingingProviderId(providerId);
    try {
      const res = await fetch(`/api/v1/gateways/${providerId}/ping`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (providerId === "pickmytrade_tradovate") {
          setPingLatency(data.latency_ms);
        }
        showToast(`✅ Ping a ${providerId}: ${data.latency_ms} ms · Estado: ${data.status}`);
        fetchStatus();
      } else {
        showToast(`⚠️ Ping a ${providerId} devolvió estado ${res.status}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error al ejecutar ping en ${providerId}: ${err.message}`, true);
    } finally {
      setPingingProviderId(null);
    }
  };

  const handlePingAll = async () => {
    setIsPingingAll(true);
    try {
      const res = await fetch("/api/v1/gateways/ping-all", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        showToast(`✅ Diagnóstico global completado: ${data.gateways_count} gateways diagnosticados (Latencia Media: ${data.avg_latency_ms} ms).`);
        fetchStatus();
      } else {
        showToast(`⚠️ Error en ping global: ${res.status}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error al ejecutar ping global: ${err.message}`, true);
    } finally {
      setIsPingingAll(false);
    }
  };

  const isConnected = gatewayData?.gateway_status === "CONNECTED" || gatewayData?.gateway_status === "IDLE_WAITING";

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER BAR */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-white">Conexión Gateway & Brokers CME</h1>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                TRADOVATE / PICKMYTRADE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Puente de Ejecución Institucional · Tradovate Demo ⟷ PickMyTrade API v2
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold border flex items-center gap-2 ${
              isConnected
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-rose-500/20 text-rose-400 border-rose-500/30"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>ONLINE · {pingLatency?.toFixed(1) ?? "--"} ms</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>DESCONECTADO / SIN DATOS</span>
              </>
            )}
          </span>

          <button
            onClick={fetchStatus}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Refrescar estado"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {notification && (
        <div
          className={`p-3.5 rounded-xl text-xs font-bold font-mono flex items-center gap-2.5 shadow-lg ${
            notification.isError
              ? "bg-rose-950/90 border border-rose-500/80 text-rose-200"
              : "bg-emerald-950/90 border border-emerald-500/80 text-emerald-200"
          }`}
        >
          {notification.text}
        </div>
      )}

      {/* ERROR DISCONNECTED BANNER */}
      {fetchError && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/80 rounded-2xl text-xs font-mono text-rose-200 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>ESTADO: <strong>DESCONECTADO</strong> — {fetchError}</span>
          </div>
          <button
            onClick={fetchStatus}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reintentar Conexión
          </button>
        </div>
      )}

      {/* PRIMARY REAL TRADOVATE / PICKMYTRADE CONNECTION CARD */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Gateway Principal: PickMyTrade (Tradovate Demo)
            </h2>
          </div>
          <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
            CONECTOR ACTIVO
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
          {/* Card 1: Account Details */}
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-blue-400" />
              Cuenta & Operador
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Cuenta Tradovate</span>
                <div className="text-sm font-bold text-emerald-400">
                  {gatewayData?.account_id ?? "NO EVIDENCE / SIN DATOS"}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Usuario & ID</span>
                <div className="text-xs text-slate-200">
                  {gatewayData?.user ?? "NO EVIDENCE / SIN DATOS"}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Entorno / Broker</span>
                <div className="text-xs text-slate-300">
                  {gatewayData?.environment ?? "SIN DATOS"} · {gatewayData?.broker ?? "SIN DATOS"}
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Financial Capital & Drawdown */}
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3">
            <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Capital & Guardarraíles
            </div>
            <div className="space-y-2">
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Saldo Base / Equidad</span>
                <div className="text-sm font-bold text-white">
                  {gatewayData?.base_capital_usd != null
                    ? `$${gatewayData.base_capital_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD`
                    : "SIN DATOS"}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Trailing Drawdown Límite</span>
                <div className="text-xs text-emerald-400 font-bold">
                  {gatewayData?.current_drawdown_usd != null && gatewayData?.trailing_drawdown_limit_usd != null
                    ? `$${gatewayData.current_drawdown_usd.toFixed(2)} / $${gatewayData.trailing_drawdown_limit_usd.toFixed(2)} USD (0.0% USADO)`
                    : "SIN DATOS"}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 uppercase">Vencimiento del Trial</span>
                <div className="text-xs text-amber-400 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {gatewayData?.trial_expires_utc ?? "NO EVIDENCE / SIN DATOS"}
                </div>
              </div>
            </div>
          </div>

          {/* Card 3: Physical Latency & Ping */}
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3 flex flex-col justify-between">
            <div>
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Latencia Física & Test RTT
              </div>
              <div className="mt-3 text-center">
                <div className="text-3xl font-black text-emerald-400 font-mono">
                  {pingLatency != null ? `${pingLatency.toFixed(1)} ms` : "-- ms"}
                </div>
                <p className="text-[10px] text-slate-400 mt-1">
                  Latencia de red RTT hacia PickMyTrade / CME
                </p>
              </div>
            </div>

            <button
              onClick={() => handlePingProvider("pickmytrade_tradovate")}
              disabled={pingingProviderId === "pickmytrade_tradovate"}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition flex items-center justify-center gap-2 cursor-pointer mt-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${pingingProviderId === "pickmytrade_tradovate" ? "animate-spin" : ""}`} />
              {pingingProviderId === "pickmytrade_tradovate" ? "Midiendo..." : "Ping Tradovate Bridge"}
            </button>
          </div>
        </div>

        {/* API Endpoint details */}
        <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2 font-mono text-xs">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-purple-400" />
            Endpoint Webhook Tradovate
          </div>
          <div className="flex items-center justify-between bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-slate-300">
            <span className="truncate">https://api.pickmytrade.trade/v2/add-trade-data-latest?t=24151</span>
            <button
              onClick={() => handleCopy("https://api.pickmytrade.trade/v2/add-trade-data-latest?t=24151", "webhook")}
              className="ml-2 p-1 text-slate-400 hover:text-white transition"
              title="Copiar endpoint"
            >
              {copiedField === "webhook" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
      </div>

      {/* SECONDARY REGISTERED GATEWAYS & BRIDGES */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Ecosistema de Gateways Registrados ({gatewaysList.length})
            </h2>
          </div>
          <button
            onClick={handlePingAll}
            disabled={isPingingAll}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPingingAll ? "animate-spin text-emerald-400" : ""}`} />
            {isPingingAll ? "Diagnosticando..." : "Diagnóstico Ping Global"}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
          {gatewaysList.map((gw) => {
            const isGwActive = gw.provider_id === "pickmytrade_tradovate";
            const isGwPinging = pingingProviderId === gw.provider_id;

            return (
              <div
                key={gw.provider_id}
                className={`p-4 rounded-xl border space-y-2.5 flex flex-col justify-between transition-all ${
                  isGwActive
                    ? "bg-slate-950 border-emerald-500/40 ring-1 ring-emerald-500/20"
                    : "bg-slate-950 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                      {gw.category}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${
                        gw.status === "CONNECTED"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : gw.status === "IDLE_WAITING"
                          ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {gw.status}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-white truncate">{gw.name}</h3>
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">
                    ID: <strong className="text-slate-300">{gw.provider_id}</strong>
                  </p>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-slate-800 text-[10px]">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Latencia RTT:</span>
                    <span className="text-emerald-400 font-bold">
                      {gw.latency_ms > 0 ? `${gw.latency_ms.toFixed(1)} ms` : "-- ms"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Token Auth:</span>
                    <span className="text-slate-300 font-mono">{gw.auth_token || "NO_TOKEN"}</span>
                  </div>
                </div>

                <button
                  onClick={() => handlePingProvider(gw.provider_id)}
                  disabled={isGwPinging}
                  className="w-full py-1.5 rounded-lg text-[11px] font-bold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <RefreshCw className={`w-3 h-3 ${isGwPinging ? "animate-spin text-emerald-400" : ""}`} />
                  {isGwPinging ? "Midiendo..." : "Probar Ping"}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
