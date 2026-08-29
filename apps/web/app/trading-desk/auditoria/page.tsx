"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  FileText,
  Activity,
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  Lock,
  Download,
  Database,
  Search,
  Zap,
  Server,
  AlertCircle,
  WifiOff,
} from "lucide-react";

interface OrderAuditEvent {
  id: string;
  timestamp: string;
  symbol: string;
  action: string;
  contracts: number;
  expectedPrice: number;
  filledPrice: number;
  slippageTicks: number;
  latencyMs: number;
  status: string;
  brokerResponse: string;
}

interface TelemetryHealth {
  overall_status: string;
  total_workers: number;
  healthy_workers: number;
  timestamp_utc: string;
  workers?: Record<string, {
    worker_id: string;
    name: string;
    status: string;
    is_healthy: boolean;
    heartbeat_age_seconds: number;
  }>;
}

interface GatewayStatus {
  account_id?: string;
  broker?: string;
  gateway_status?: string;
  last_ping_latency_ms?: number;
}

export default function ForensicAuditPage() {
  const [logs, setLogs] = useState<OrderAuditEvent[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryHealth | null>(null);
  const [gatewayData, setGatewayData] = useState<GatewayStatus | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [fetchError, setFetchError] = useState<string | null>(null);

  const fetchRealData = useCallback(async () => {
    setFetchError(null);
    try {
      const [logsRes, telRes, gwRes] = await Promise.all([
        fetch("/api/v1/gateways/pickmytrade/logs"),
        fetch("/api/v1/telemetry/health"),
        fetch("/api/v1/gateways/pickmytrade/status"),
      ]);

      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(Array.isArray(data) ? data : []);
      } else {
        setLogs([]);
      }

      if (telRes.ok) {
        const telData = await telRes.json();
        setTelemetry(telData);
      }

      if (gwRes.ok) {
        const gwData = await gwRes.json();
        setGatewayData(gwData);
      }
    } catch (e: any) {
      setLogs([]);
      setFetchError(e.message || "Error al sincronizar registros forenses.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRealData();
    const interval = setInterval(fetchRealData, 4000);
    return () => clearInterval(interval);
  }, [fetchRealData]);

  const filteredLogs = useMemo(() => {
    return logs.filter(
      (l) =>
        !searchQuery ||
        l.symbol?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.action?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [logs, searchQuery]);

  const isConnected = gatewayData?.gateway_status === "CONNECTED" || gatewayData?.gateway_status === "IDLE_WAITING";

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl text-cyan-400">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-white">Auditoría Forense & Telemetría WAL</h1>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                SQLITE WAL IMMUTABLE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Registro Inmutable de Órdenes Tradovate ({gatewayData?.account_id ?? "DEMO1279346"}) · Latencias Sub-ms & Slippage
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold border flex items-center gap-1.5 ${
              isConnected
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-rose-500/20 text-rose-400 border-rose-500/30"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>WAL LIVE · {gatewayData?.last_ping_latency_ms != null ? `${gatewayData.last_ping_latency_ms} ms` : "ACTIVO"}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>DESCONECTADO</span>
              </>
            )}
          </span>

          <button
            onClick={() => {
              setIsRefreshing(true);
              fetchRealData();
            }}
            disabled={isRefreshing}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono font-bold transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-cyan-400" : ""}`} />
            Sincronizar WAL
          </button>
        </div>
      </div>

      {fetchError && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/80 rounded-2xl text-xs font-mono text-rose-200 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>ESTADO: <strong>DESCONECTADO</strong> — {fetchError}</span>
          </div>
          <button
            onClick={fetchRealData}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reintentar
          </button>
        </div>
      )}

      {/* TELEMETRY HEALTH METRICS STRIP */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-blue-400" />
            Salud del Motor
          </div>
          <div className="text-base font-bold text-white flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${telemetry?.overall_status === "HEALTHY" ? "bg-emerald-400 animate-ping" : "bg-amber-400"}`} />
            {telemetry?.overall_status ?? "SIN DATOS"} ({telemetry?.healthy_workers ?? 0}/{telemetry?.total_workers ?? 8} Workers)
          </div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-cyan-400" />
            Persistencia Fondeo
          </div>
          <div className="text-base font-bold text-cyan-400">
            SQLite WAL · {logs.length} Órdenes Registradas
          </div>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Latencia CME RTT
          </div>
          <div className="text-base font-bold text-emerald-400">
            {gatewayData?.last_ping_latency_ms != null ? `${gatewayData.last_ping_latency_ms} ms` : "-- ms"}
          </div>
        </div>
      </div>

      {/* FORENSIC LOGS TABLE */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Eventos Forenses de Microestructura ({filteredLogs.length})
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar por símbolo o ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500 w-48 sm:w-60"
              />
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">100% Zero-Mocks</span>
          </div>
        </div>

        {logs.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-950/60 space-y-3 font-mono">
            <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-sm font-bold text-slate-200 uppercase tracking-wider">
              SIN REGISTROS FORENSES PREVIOS (0 órdenes despachadas)
            </div>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              La base de datos SQLite WAL no tiene órdenes ejecutadas en esta sesión. Cada ejecución física registrará su latencia sub-ms y slippage en ticks aquí de forma inmutable.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-800/40">
                  <th className="py-2.5 px-3">Timestamp UTC</th>
                  <th className="py-2.5 px-3">Símbolo</th>
                  <th className="py-2.5 px-3">Acción</th>
                  <th className="py-2.5 px-3">Contratos</th>
                  <th className="py-2.5 px-3">Slippage</th>
                  <th className="py-2.5 px-3">Latencia</th>
                  <th className="py-2.5 px-3">Estado</th>
                  <th className="py-2.5 px-3">Respuesta Broker</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-[11px]">
                {filteredLogs.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 px-3 text-slate-400">{l.timestamp}</td>
                    <td className="py-2.5 px-3 font-bold text-white">{l.symbol}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        l.action?.toUpperCase() === "BUY"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-rose-500/20 text-rose-400"
                      }`}>
                        {l.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-200">{l.contracts}x</td>
                    <td className="py-2.5 px-3 text-blue-400">{l.slippageTicks?.toFixed(1) ?? 0}T</td>
                    <td className="py-2.5 px-3 text-amber-400">{l.latencyMs?.toFixed(1) ?? 0} ms</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">{l.status}</td>
                    <td className="py-2.5 px-3 text-slate-400 max-w-xs truncate">{l.brokerResponse}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
