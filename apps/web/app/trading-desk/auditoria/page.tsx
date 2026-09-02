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
  Hash,
  Binary,
  Layers,
  Sliders,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

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
  const { user, profile, loading: authLoading } = useAuth();

  const [logs, setLogs] = useState<OrderAuditEvent[]>([]);
  const [telemetry, setTelemetry] = useState<TelemetryHealth | null>(null);
  const [gatewayData, setGatewayData] = useState<GatewayStatus | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Derive real credentials from Firestore User Profile
  const linkedAccounts = profile?.trading_accounts || profile?.broker_accounts || {};
  const linkedAccountId =
    linkedAccounts.tradovate_account_id?.trim() ||
    linkedAccounts.ninjatrader_account_id?.trim() ||
    gatewayData?.account_id?.trim() ||
    "";
  const hasLinkedAccount = Boolean(linkedAccountId);

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

  const isConnected = (gatewayData?.gateway_status === "CONNECTED" || gatewayData?.gateway_status === "IDLE_WAITING") && hasLinkedAccount;

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black text-[var(--text-1)] tracking-tight">Auditoría Forense & Telemetría WAL</h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)]">
                SQLITE WAL IMMUTABLE
              </span>
            </div>
            <p className="text-xs text-[var(--text-2)] font-mono mt-1">
              Registro Inmutable de Órdenes Tradovate ({hasLinkedAccount ? linkedAccountId : "SIN CUENTA VINCULADA"}) · Latencias Sub-ms & Slippage
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto font-mono">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-1.5 ${
              isConnected
                ? "bg-[var(--profit-dim)] text-[var(--profit)] border-[var(--profit)]"
                : "bg-[var(--loss-dim)] text-[var(--loss)] border-[var(--loss)]"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-[var(--profit)] animate-ping" />
                <span>WAL LIVE · {gatewayData?.last_ping_latency_ms != null ? `${gatewayData.last_ping_latency_ms} ms` : "ACTIVO"}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>{hasLinkedAccount ? "DESCONECTADO" : "SIN CUENTA VINCULADA"}</span>
              </>
            )}
          </span>

          <button
            onClick={() => {
              setIsRefreshing(true);
              fetchRealData();
            }}
            disabled={isRefreshing}
            className="px-3.5 py-1.5 rounded-xl bg-[var(--bg)] hover:bg-[var(--surface-1)] text-[var(--text-1)] border border-white/[0.1] text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-[var(--text-2)]" : ""}`} />
            Sincronizar WAL
          </button>
        </div>
      </div>

      {fetchError && (
        <div className="p-4 bg-[var(--loss-dim)] border border-[var(--loss)] rounded-2xl text-xs font-mono text-[var(--loss)] flex items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--loss)] flex-shrink-0" />
            <span>ESTADO: <strong>DESCONECTADO</strong> — {fetchError}</span>
          </div>
          <button
            onClick={fetchRealData}
            className="px-3 py-1.5 rounded-lg bg-[var(--surface-3)] hover:bg-[var(--surface-3)] text-[var(--text-1)] font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reintentar
          </button>
        </div>
      )}

      {/* TELEMETRY & AUDIT METRICS STRIP */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-4 bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-[var(--text-2)] uppercase font-bold flex items-center gap-1.5">
            <Server className="w-3.5 h-3.5 text-[var(--text-2)]" />
            Salud del Motor
          </div>
          <div className="text-base font-bold text-[var(--text-1)] flex items-center gap-2 tabular-nums">
            <span className={`w-2 h-2 rounded-full ${telemetry?.overall_status === "HEALTHY" ? "bg-[var(--profit)] animate-ping" : "bg-[var(--surface-3)]"}`} />
            {telemetry?.overall_status ?? "SIN DATOS"} ({telemetry?.healthy_workers ?? 0}/{telemetry?.total_workers ?? 8} Workers)
          </div>
        </div>

        <div className="p-4 bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-[var(--text-2)] uppercase font-bold flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-[var(--text-2)]" />
            Persistencia Fondeo
          </div>
          <div className="text-base font-bold text-[var(--text-2)] tabular-nums">
            SQLite WAL · {logs.length} Órdenes
          </div>
        </div>

        <div className="p-4 bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-[var(--text-2)] uppercase font-bold flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-[var(--text-2)]" />
            Latencia CME RTT
          </div>
          <div className="text-base font-bold text-[var(--profit)] tabular-nums">
            {gatewayData?.last_ping_latency_ms != null ? `${gatewayData.last_ping_latency_ms} ms` : "SIN DATOS"}
          </div>
        </div>

        <div className="p-4 bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-[var(--text-2)] uppercase font-bold flex items-center gap-1.5">
            <Hash className="w-3.5 h-3.5 text-[var(--profit)]" />
            Estado de Cuenta
          </div>
          <div className="text-xs font-bold text-[var(--profit)] tabular-nums truncate">
            {hasLinkedAccount ? `VINCULADA (${linkedAccountId})` : "SIN CUENTA VINCULADA"}
          </div>
        </div>
      </div>

      {/* FORENSIC LOGS TABLE */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-[var(--text-2)]" />
            <h2 className="text-base font-bold text-[var(--text-1)] tracking-tight">
              Eventos Forenses de Microestructura ({filteredLogs.length})
            </h2>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[var(--text-2)] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Buscar por símbolo o ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1.5 bg-[var(--bg)] border border-white/[0.1] rounded-xl text-xs font-mono text-[var(--text-1)] focus:outline-none focus:border-[var(--border)] w-48 sm:w-60"
              />
            </div>
            <span className="text-xs font-mono text-[var(--profit)] font-bold bg-[var(--profit-dim)] px-2.5 py-1 rounded-xl border border-[var(--profit)]">
              100% Zero-Mocks
            </span>
          </div>
        </div>

        {logs.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-white/[0.1] rounded-2xl bg-[var(--bg)] space-y-3 font-mono">
            <CheckCircle2 className="w-8 h-8 text-[var(--text-3)] mx-auto" />
            <div className="text-sm font-bold text-[var(--text-1)] uppercase tracking-wider">
              SIN REGISTROS FORENSES PREVIOS (0 órdenes despachadas)
            </div>
            <p className="text-xs text-[var(--text-2)] max-w-md mx-auto">
              {hasLinkedAccount
                ? "La base de datos SQLite WAL no tiene órdenes ejecutadas en esta sesión. Cada ejecución física registrará su latencia sub-ms y slippage en ticks aquí de forma inmutable."
                : "No hay cuenta vinculada en el Trading Desk. Vincula tu cuenta en Ajustes para despachar y auditar órdenes."}
            </p>
            {!hasLinkedAccount && (
              <Link
                href="/trading-desk/configuracion"
                className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--surface-3)] hover:bg-[var(--surface-3)] text-[var(--text-1)] rounded-xl text-xs font-bold transition mt-2 font-mono"
              >
                <Sliders className="w-3.5 h-3.5" />
                Vincular Cuenta en Ajustes →
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] text-[var(--text-2)] uppercase text-[10px] tracking-wider bg-[var(--bg)]">
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
              <tbody className="divide-y divide-white/[0.05] text-[11px]">
                {filteredLogs.map((l) => (
                  <tr key={l.id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-2.5 px-3 text-[var(--text-2)]">{l.timestamp}</td>
                    <td className="py-2.5 px-3 font-bold text-[var(--text-1)]">{l.symbol}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        l.action?.toUpperCase() === "BUY"
                          ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                          : "bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)]"
                      }`}>
                        {l.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-[var(--text-1)]">{l.contracts}x</td>
                    <td className="py-2.5 px-3 text-[var(--text-2)] tabular-nums">{l.slippageTicks?.toFixed(1) ?? 0}T</td>
                    <td className="py-2.5 px-3 text-[var(--text-2)] tabular-nums">{l.latencyMs?.toFixed(1) ?? 0} ms</td>
                    <td className="py-2.5 px-3 text-[var(--profit)] font-bold">{l.status}</td>
                    <td className="py-2.5 px-3 text-[var(--text-2)] max-w-xs truncate">{l.brokerResponse}</td>
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
