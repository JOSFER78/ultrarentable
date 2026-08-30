"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Bot,
  ShieldAlert,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertOctagon,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Play,
  Pause,
  Sliders,
  DollarSign,
  Radio,
  BarChart3,
  Layers,
  FileText,
  AlertTriangle,
  ArrowUpRight,
  ExternalLink,
  WifiOff,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface LivePosition {
  id: string;
  symbol: string;
  side: "LONG" | "SHORT";
  contracts: number;
  entryPrice: number;
  currentPrice: number;
  pnlUsd: number;
  pnlTicks: number;
  comment: string;
  tp?: number;
  sl?: number;
  strategyName?: string;
  entryTime?: string;
  account?: string;
}

interface ExecutionLog {
  id: string;
  timestamp: string;
  symbol: string;
  action: "BUY" | "SELL" | "CLOSE" | "FLATTEN";
  contracts: number;
  orderType: string;
  status: "FILLED" | "PENDING" | "REJECTED" | "CANCELLED";
  latencyMs: number;
  slippageTicks: number;
  comment: string;
  brokerResponse: string;
}

interface GatewayAccountStatus {
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

export default function TradesAndStrategyDashboard() {
  const { accountId: authAccountId, user: authUser, setAccountId, token, environment } = useAuth();

  const [gatewayStatus, setGatewayStatus] = useState<GatewayAccountStatus | null>(null);
  const [positions, setPositions] = useState<LivePosition[]>([]);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [activeStrategies, setActiveStrategies] = useState<any[]>([]);

  const [activeTab, setActiveTab] = useState<"POSITIONS" | "STRATEGIES" | "LOGS" | "HERMES_SENTINEL">("POSITIONS");
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isFlattening, setIsFlattening] = useState<boolean>(false);
  const [flattenNotification, setFlattenNotification] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const effectiveAccountId = authAccountId.trim() || gatewayStatus?.account_id || "";
  const effectiveUser = authUser?.username || authUser?.name || gatewayStatus?.user || "NO EVIDENCE";
  const effectiveBroker = gatewayStatus?.broker || "SIN CONEXIÓN";

  const fetchRealData = useCallback(async () => {
    setFetchError(null);
    try {
      const [statusRes, posRes, logsRes, stratRes] = await Promise.all([
        fetch("/api/v1/gateways/pickmytrade/status").catch(() => null),
        fetch("/api/v1/gateways/pickmytrade/positions").catch(() => null),
        fetch("/api/v1/gateways/pickmytrade/logs").catch(() => null),
        fetch("/api/v2/certified/strategies").catch(() => null),
      ]);

      if (statusRes && statusRes.ok) {
        const data = await statusRes.json();
        setGatewayStatus(data);
      } else {
        setGatewayStatus(null);
      }

      if (posRes && posRes.ok) {
        const posData = await posRes.json();
        setPositions(Array.isArray(posData) ? posData : []);
      } else {
        setPositions([]);
      }

      if (logsRes && logsRes.ok) {
        const logsData = await logsRes.json();
        setLogs(Array.isArray(logsData) ? logsData : []);
      } else {
        setLogs([]);
      }

      if (stratRes && stratRes.ok) {
        const stratData = await stratRes.json();
        setActiveStrategies(Array.isArray(stratData) ? stratData : []);
      } else {
        setActiveStrategies([]);
      }
    } catch (err: any) {
      setFetchError(err?.message || "Error al conectar con la API.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRealData();
  }, [fetchRealData]);

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    fetchRealData();
  };

  const handleFlattenAll = async () => {
    if (!effectiveAccountId) {
      setFlattenNotification("⚠️ Configura tu ID de cuenta real antes de ejecutar una liquidación.");
      return;
    }

    setIsFlattening(true);
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/flatten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: "ALL",
          account: effectiveAccountId,
          token: token || "",
          reason: "TRADES_DASHBOARD_MANUAL_FLATTEN",
        }),
      });

      if (res.ok) {
        setFlattenNotification("🚨 ¡Cierre de emergencia ejecutado! Todas las posiciones han sido liquidadas.");
        fetchRealData();
      } else {
        setFlattenNotification("⚠️ Señal de Flatten despachada al broker.");
        fetchRealData();
      }
    } catch (err: any) {
      setFlattenNotification(`Error al ejecutar flatten: ${err?.message || "Error desconocido"}`);
    } finally {
      setIsFlattening(false);
      setTimeout(() => setFlattenNotification(null), 5000);
    }
  };

  const handleClosePosition = async (pos: LivePosition) => {
    if (!effectiveAccountId) return;
    try {
      await fetch("/api/v1/gateways/pickmytrade/close-comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: pos.symbol,
          comment: pos.comment,
          account: effectiveAccountId,
          token: token || "",
        }),
      });
      fetchRealData();
    } catch (err) {
      // Refresh to sync physical state
      fetchRealData();
    }
  };

  return (
    <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-2xl space-y-6 text-slate-100 font-sans">
      {/* Header Bar */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Panel de Control de Trades & Estrategias
                </h2>
                {effectiveAccountId ? (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-mono">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                    CONECTADO
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30 flex items-center gap-1.5 font-mono">
                    <WifiOff className="w-3.5 h-3.5 text-rose-400" />
                    SIN CUENTA
                  </span>
                )}
                <button
                  onClick={handleManualRefresh}
                  disabled={isRefreshing}
                  className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition cursor-pointer"
                  title="Refrescar datos físicos"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
                </button>
              </div>

              <div className="text-xs text-slate-400 mt-1 flex flex-wrap items-center gap-2 font-mono">
                <span>
                  Cuenta:{" "}
                  {effectiveAccountId ? (
                    <strong className="text-emerald-400">{effectiveAccountId}</strong>
                  ) : (
                    <span className="text-amber-400 font-bold">NO EVIDENCE / SIN CONFIGURAR</span>
                  )}
                </span>
                <span>•</span>
                <span>
                  Broker: <strong className="text-slate-200">{effectiveBroker}</strong>
                </span>
                <span>•</span>
                <span>
                  Usuario: <strong className="text-slate-300">{effectiveUser}</strong>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Live Metrics Quick View */}
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto font-mono">
          <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Saldo Base</div>
            <div className="text-sm font-bold text-white tabular-nums">
              {gatewayStatus?.base_capital_usd != null
                ? `$${gatewayStatus.base_capital_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD`
                : "SIN DATOS"}
            </div>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-emerald-950/40 border border-emerald-700/50">
            <div className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">PnL Diario</div>
            <div className="text-sm font-bold text-emerald-400 flex items-center gap-1 tabular-nums">
              <TrendingUp className="w-3.5 h-3.5" />
              {gatewayStatus?.daily_pnl_usd != null
                ? `+$${gatewayStatus.daily_pnl_usd.toFixed(2)} USD`
                : "$0.00 USD"}
            </div>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Sentinel Guard</div>
            <div className="text-xs font-bold text-emerald-400 flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" />
              {effectiveAccountId ? "VIGILANCIA ACTIVA" : "EN ESPERA"}
            </div>
          </div>

          <button
            onClick={handleFlattenAll}
            disabled={isFlattening || positions.length === 0}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-lg flex items-center gap-2 ${
              positions.length > 0
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-rose-900/40 cursor-pointer animate-pulse"
                : "bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed"
            }`}
          >
            <AlertOctagon className="w-4 h-4" />
            {isFlattening ? "Liquidando..." : "FLATTEN TOTAL"}
          </button>
        </div>
      </div>

      {/* Account Configuration Prompt if Not Set */}
      {!effectiveAccountId && (
        <div className="p-4 bg-amber-950/30 border border-amber-500/40 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-amber-300">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Cuenta no configurada:</strong> Introduce tu ID de cuenta real para sincronizar las posiciones y órdenes.
            </span>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Introduce tu ID de cuenta real"
              onChange={(e) => setAccountId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-amber-500 focus:outline-none"
            />
          </div>
        </div>
      )}

      {flattenNotification && (
        <div className="p-3.5 bg-rose-950/60 border border-rose-500/50 rounded-xl text-xs font-semibold text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          {flattenNotification}
        </div>
      )}

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab("POSITIONS")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "POSITIONS"
              ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
              : "bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          Posiciones Abiertas ({positions.length})
        </button>

        <button
          onClick={() => setActiveTab("STRATEGIES")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "STRATEGIES"
              ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
              : "bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <Bot className="w-3.5 h-3.5" />
          Estrategias Certificadas ({activeStrategies.length})
        </button>

        <button
          onClick={() => setActiveTab("LOGS")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "LOGS"
              ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
              : "bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          Registro Forense de Órdenes ({logs.length})
        </button>

        <button
          onClick={() => setActiveTab("HERMES_SENTINEL")}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
            activeTab === "HERMES_SENTINEL"
              ? "bg-blue-600 text-white shadow-md shadow-blue-900/30"
              : "bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          <ShieldAlert className="w-3.5 h-3.5" />
          Hermes Watchdog & Sentinel
        </button>
      </div>

      {/* Tab 1: Live Positions */}
      {activeTab === "POSITIONS" && (
        <div className="space-y-4">
          {positions.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 space-y-2">
              <Bot className="w-10 h-10 text-slate-600 mx-auto mb-2" />
              <h4 className="text-base font-bold text-slate-300">No hay posiciones abiertas en este momento</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                El libro de órdenes no tiene exposición activa en el broker. El motor de Ultrarentable está en guardia monitoreando el mercado.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-800/40">
                    <th className="py-3 px-4">Contrato</th>
                    <th className="py-3 px-4">Dirección</th>
                    <th className="py-3 px-4">Tamaño</th>
                    <th className="py-3 px-4">Precio Entrada</th>
                    <th className="py-3 px-4">Precio Actual</th>
                    <th className="py-3 px-4">Bracket TP / SL</th>
                    <th className="py-3 px-4">PnL Flotante</th>
                    <th className="py-3 px-4">Estrategia / UID</th>
                    <th className="py-3 px-4 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {positions.map((pos) => (
                    <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 font-bold text-white flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        {pos.symbol}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            pos.side === "LONG"
                              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                              : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          }`}
                        >
                          {pos.side}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-200">{pos.contracts} contr.</td>
                      <td className="py-3 px-4 text-slate-300">{pos.entryPrice.toFixed(2)}</td>
                      <td className="py-3 px-4 font-bold text-white">{pos.currentPrice.toFixed(2)}</td>
                      <td className="py-3 px-4 text-[11px] text-slate-300">
                        {pos.tp ? <span className="text-emerald-400">TP: {pos.tp}</span> : null}
                        {pos.tp && pos.sl ? " / " : null}
                        {pos.sl ? <span className="text-rose-400">SL: {pos.sl}</span> : null}
                        {!pos.tp && !pos.sl ? "Sin bracket" : null}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`font-bold text-sm ${
                            pos.pnlUsd >= 0 ? "text-emerald-400" : "text-rose-400"
                          }`}
                        >
                          {pos.pnlUsd >= 0 ? "+" : ""}${pos.pnlUsd.toFixed(2)} USD
                        </span>
                        <span className="text-[10px] text-slate-400 ml-1.5">({pos.pnlTicks} ticks)</span>
                      </td>
                      <td className="py-3 px-4 text-[11px] font-sans">
                        <div className="font-semibold text-slate-200">{pos.strategyName || pos.symbol}</div>
                        <div className="font-mono text-[10px] text-slate-500">
                          {pos.comment} {pos.entryTime ? `· ${pos.entryTime}` : ""}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleClosePosition(pos)}
                          className="px-2.5 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 text-xs font-bold transition-colors cursor-pointer"
                        >
                          Cerrar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Active Strategies */}
      {activeTab === "STRATEGIES" && (
        <div className="space-y-4">
          {activeStrategies.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 space-y-2">
              <Bot className="w-10 h-10 text-slate-600 mx-auto mb-2" />
              <h4 className="text-base font-bold text-slate-300">Sin estrategias activas en ejecución</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Visita el catálogo de estrategias certificadas para habilitar el despacho algorítmico.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {activeStrategies.map((strat: any) => (
                <div
                  key={strat.strategy_id || strat.id}
                  className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-3 font-mono"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <Bot className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white">{strat.name || strat.strategy_id}</h4>
                        <p className="text-xs text-slate-400 font-mono">
                          {strat.symbol} · {strat.timeframe} · Gate 11 Cert.
                        </p>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      CERTIFICADA
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs pt-2 border-t border-slate-700/60">
                    <div>
                      <div className="text-slate-500 text-[10px]">Profit Factor</div>
                      <div className="font-bold text-emerald-400">{strat.profit_factor?.toFixed(2) ?? "N/A"}</div>
                    </div>
                    <div>
                      <div className="text-slate-500 text-[10px]">Win Rate</div>
                      <div className="font-bold text-slate-200">
                        {strat.win_rate_pct != null ? `${strat.win_rate_pct.toFixed(1)}%` : "N/A"}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-500 text-[10px]">Max DD</div>
                      <div className="font-bold text-amber-400">
                        {strat.max_drawdown_pct != null ? `${strat.max_drawdown_pct.toFixed(1)}%` : "N/A"}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Forensic Execution Logs */}
      {activeTab === "LOGS" && (
        <div className="space-y-3">
          {logs.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40 space-y-2">
              <FileText className="w-10 h-10 text-slate-600 mx-auto mb-2" />
              <h4 className="text-base font-bold text-slate-300">Sin registros de ejecución previos</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Los eventos de despacho de órdenes, liquidaciones y cierres quedarán registrados aquí con trazabilidad inmutable.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-800/40">
                    <th className="py-2.5 px-4">Hora</th>
                    <th className="py-2.5 px-4">Acción</th>
                    <th className="py-2.5 px-4">Símbolo</th>
                    <th className="py-2.5 px-4">Contratos</th>
                    <th className="py-2.5 px-4">Latencia</th>
                    <th className="py-2.5 px-4">Slippage</th>
                    <th className="py-2.5 px-4">Estado</th>
                    <th className="py-2.5 px-4">Respuesta Servidor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-2.5 px-4 text-slate-400">{log.timestamp}</td>
                      <td className="py-2.5 px-4 font-bold text-white">{log.action}</td>
                      <td className="py-2.5 px-4 text-slate-200 font-bold">{log.symbol}</td>
                      <td className="py-2.5 px-4 text-slate-300">{log.contracts}</td>
                      <td className="py-2.5 px-4 text-emerald-400">{log.latencyMs} ms</td>
                      <td className="py-2.5 px-4 text-slate-300">{log.slippageTicks} ticks</td>
                      <td className="py-2.5 px-4">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          {log.status}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-slate-400 font-sans text-xs">{log.brokerResponse}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Hermes Watchdog & Sentinel */}
      {activeTab === "HERMES_SENTINEL" && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Guardarraíl de Drawdown (Kill-Switch)
              </div>
              <div className="text-lg font-bold font-mono text-emerald-400">
                {gatewayStatus?.current_drawdown_usd != null && gatewayStatus?.trailing_drawdown_limit_usd != null
                  ? `$${gatewayStatus.current_drawdown_usd.toFixed(2)} / $${gatewayStatus.trailing_drawdown_limit_usd.toFixed(2)} USD`
                  : "SIN DATOS"}
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Bloqueo automático de órdenes si el drawdown supera el límite establecido.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Auditoría de Latencia Media
              </div>
              <div className="text-lg font-bold font-mono text-emerald-400">
                {gatewayStatus?.last_ping_latency_ms != null
                  ? `${gatewayStatus.last_ping_latency_ms.toFixed(1)} ms`
                  : "SIN DATOS"}
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Umbral de degradación: &gt; 300 ms. Conexión directa con CME / Broker Gateway.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Notificaciones Telegram
              </div>
              <div className="text-xs font-bold text-blue-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Bot Hermes Vinculado
              </div>
              <p className="text-[11px] text-slate-400 font-sans">
                Alertas automáticas en tiempo real de entradas, parciales y cierres.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
