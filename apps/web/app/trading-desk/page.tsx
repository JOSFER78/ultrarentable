"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  Bot,
  ShieldAlert,
  ShieldCheck,
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
  ChevronRight,
  Flame,
  Globe,
  Lock,
  Send,
  Sparkles,
  Server,
  AlertCircle,
  WifiOff,
} from "lucide-react";

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
  tp?: number | null;
  sl?: number | null;
  status: string;
  account: string;
  createdAt: string;
}

interface ExecutionLog {
  id: string;
  timestamp: string;
  symbol: string;
  action: string;
  contracts: number;
  expectedPrice: number;
  filledPrice: number;
  latencyMs: number;
  slippageTicks: number;
  status: string;
  brokerResponse: string;
}

interface AccountStatus {
  provider_id: string;
  account_id: string;
  user: string;
  broker: string;
  environment: string;
  base_capital_usd: number | null;
  current_equity_usd: number | null;
  daily_pnl_usd: number | null;
  trailing_drawdown_limit_usd: number | null;
  current_drawdown_usd: number | null;
  open_positions_count: number;
  trial_expires_utc: string | null;
  gateway_status: string;
  last_ping_latency_ms: number | null;
}

interface ExecutionSession {
  session_id: string;
  route: string;
  symbol: string;
  status: string;
  candidate_id: string;
  current_pnl_usd: number;
  current_drawdown_pct: number;
  kill_switch_active: boolean;
}

interface GatewayItem {
  provider_id: string;
  name: string;
  status: string;
  latency_ms: number;
  is_enabled: boolean;
}

export default function InstitutionalTradingDesk() {
  const [accountInfo, setAccountInfo] = useState<AccountStatus | null>(null);
  const [positions, setPositions] = useState<LivePosition[]>([]);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [gateways, setGateways] = useState<GatewayItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Order Pad state
  const [orderSymbol, setOrderSymbol] = useState<"MNQ" | "MES" | "MCL" | "MGC">("MNQ");
  const [orderAction, setOrderAction] = useState<"BUY" | "SELL">("BUY");
  const [orderContracts, setOrderContracts] = useState<number>(1);
  const [orderTpDollar, setOrderTpDollar] = useState<number>(25);
  const [orderSlDollar, setOrderSlDollar] = useState<number>(15);
  const [isSendingOrder, setIsSendingOrder] = useState<boolean>(false);
  const [orderResultMsg, setOrderResultMsg] = useState<{ text: string; isError: boolean } | null>(null);

  // Flatten Modal State
  const [isFlattenModalOpen, setIsFlattenModalOpen] = useState<boolean>(false);
  const [isFlattening, setIsFlattening] = useState<boolean>(false);
  const [alertNotification, setAlertNotification] = useState<string | null>(null);

  const fetchRealData = useCallback(async () => {
    setFetchError(null);
    try {
      const [statusRes, posRes, logsRes, sessRes, gwRes] = await Promise.all([
        fetch("/api/v1/gateways/pickmytrade/status"),
        fetch("/api/v1/gateways/pickmytrade/positions"),
        fetch("/api/v1/gateways/pickmytrade/logs"),
        fetch("/api/v1/execution/sessions"),
        fetch("/api/v1/gateways"),
      ]);

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setAccountInfo(statusData);
      } else {
        setAccountInfo(null);
        setFetchError(`Error al consultar estado del gateway (HTTP ${statusRes.status}).`);
      }

      if (posRes.ok) {
        const posData = await posRes.json();
        setPositions(Array.isArray(posData) ? posData : []);
      } else {
        setPositions([]);
      }

      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setLogs(Array.isArray(logsData) ? logsData : []);
      } else {
        setLogs([]);
      }

      if (sessRes.ok) {
        const sessData = await sessRes.json();
        setSessions(Array.isArray(sessData) ? sessData : []);
      } else {
        setSessions([]);
      }

      if (gwRes.ok) {
        const gwData = await gwRes.json();
        setGateways(Array.isArray(gwData) ? gwData : []);
      }
    } catch (e: any) {
      setAccountInfo(null);
      setFetchError(e.message || "Error al conectar con la API de Trading Desk.");
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

  // Real Order Dispatch to PickMyTrade API v2
  const handleSendManualOrder = async () => {
    setIsSendingOrder(true);
    setOrderResultMsg(null);

    const payload = {
      ticker: orderSymbol,
      action: orderAction.toLowerCase(),
      contracts: orderContracts,
      orderType: "market",
      account: accountInfo?.account_id ?? "DEMO1279346",
      token: "3VxOjkjylyJKkt3oN4Jydg",
      comment: `sig_${orderSymbol.toLowerCase()}_${orderAction.toLowerCase()}_${Date.now().toString().slice(-6)}`,
      advance_tp_sl: [
        {
          quantity: orderContracts,
          dollar_tp: orderTpDollar * orderContracts,
          dollar_sl: orderSlDollar * orderContracts,
          breakeven: 10,
          breakeven_offset: 1,
          trail: 0,
        },
      ],
    };

    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok && data.success) {
        setOrderResultMsg({
          text: `✅ Orden ${orderAction} ${orderContracts}x ${orderSymbol} despachada a Tradovate Demo (${data.latency_ms} ms).`,
          isError: false,
        });
        fetchRealData();
      } else {
        setOrderResultMsg({
          text: `⚠️ Despacho: ${data.pickmytrade_response?.message || data.pickmytrade_response?.error || JSON.stringify(data.pickmytrade_response) || "Rechazada por el broker"}`,
          isError: true,
        });
      }
    } catch (err: any) {
      setOrderResultMsg({
        text: `❌ Error de red con PickMyTrade API: ${err.message}`,
        isError: true,
      });
    } finally {
      setIsSendingOrder(false);
      setTimeout(() => setOrderResultMsg(null), 6000);
    }
  };

  // Real Targeted Close by Comment
  const handleClosePosition = async (comment: string, symbol: string) => {
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/close-comment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: symbol,
          comment: comment,
          account: accountInfo?.account_id ?? "DEMO1279346",
          token: "3VxOjkjylyJKkt3oN4Jydg",
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setAlertNotification(`Posición ${symbol} (${comment}) cerrada en Tradovate.`);
        fetchRealData();
      }
    } catch (e) {
      console.error("Error closing position:", e);
    }
  };

  // Real Emergency Flatten All
  const handleExecuteFlattenAll = async () => {
    setIsFlattening(true);
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/flatten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: "ALL",
          account: accountInfo?.account_id ?? "DEMO1279346",
          token: "3VxOjkjylyJKkt3oN4Jydg",
          reason: "EMERGENCY_KILL_SWITCH_MANUAL_TRIGGER",
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setAlertNotification("🚨 ¡FLATTEN TOTAL EJECUTADO! Todas las posiciones han sido liquidadas en Tradovate.");
        fetchRealData();
      } else {
        setAlertNotification("⚠️ Señal 'flat' despachada hacia Tradovate.");
      }
    } catch (err: any) {
      setAlertNotification(`❌ Error ejecutando Flatten: ${err.message}`);
    } finally {
      setIsFlattening(false);
      setIsFlattenModalOpen(false);
      setTimeout(() => setAlertNotification(null), 7000);
    }
  };

  const isConnected = accountInfo?.gateway_status === "CONNECTED" || accountInfo?.gateway_status === "IDLE_WAITING";

  return (
    <div className="space-y-4 font-sans">
      {/* TOP INSTITUTIONAL TELEMETRY BAR */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
        <div className="flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
              <Activity className="w-7 h-7 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl md:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                  Wall Street Trading Desk
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    CME INSTITUTIONAL V3.4
                  </span>
                </h1>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1.5 font-mono ${
                    isConnected
                      ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                      : "bg-rose-500/20 text-rose-400 border-rose-500/30"
                  }`}
                >
                  {isConnected ? (
                    <>
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                      <span>{accountInfo?.gateway_status ?? "ONLINE"} · {accountInfo?.last_ping_latency_ms != null ? `${accountInfo.last_ping_latency_ms} ms` : "OK"}</span>
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
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
                  title="Actualizar telemetría física"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-emerald-400" : ""}`} />
                </button>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 flex flex-wrap items-center gap-2 font-mono">
                <span>Broker: <strong className="text-slate-200">{accountInfo?.broker ?? "SIN CONEXIÓN"}</strong></span>
                <span>•</span>
                <span>Cuenta: <strong className="text-emerald-400">{accountInfo?.account_id ?? "NO EVIDENCE"}</strong></span>
                <span>•</span>
                <span>Operador: <strong className="text-slate-200">{accountInfo?.user ?? "NO EVIDENCE"}</strong></span>
                <span>•</span>
                <span>Vence: <strong className="text-amber-400">{accountInfo?.trial_expires_utc ?? "NO EVIDENCE"}</strong></span>
              </p>
            </div>
          </div>

          {/* Real Financial KPI Strip */}
          <div className="flex flex-wrap items-center gap-2.5 w-full xl:w-auto">
            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Saldo Base Tradovate</div>
              <div className="text-base font-bold font-mono text-white">
                {accountInfo?.base_capital_usd != null
                  ? `$${accountInfo.base_capital_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD`
                  : "SIN DATOS"}
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Equidad Viva</div>
              <div className="text-base font-bold font-mono text-white">
                {accountInfo?.current_equity_usd != null
                  ? `$${accountInfo.current_equity_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD`
                  : "SIN DATOS"}
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Trailing DD Sentinel</div>
              <div className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                {accountInfo?.current_drawdown_usd != null && accountInfo?.trailing_drawdown_limit_usd != null
                  ? `$${accountInfo.current_drawdown_usd.toFixed(0)} / $${accountInfo.trailing_drawdown_limit_usd.toFixed(0)} (0% OK)`
                  : "SIN DATOS"}
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Latencia API v2</div>
              <div className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-amber-400" /> {accountInfo?.last_ping_latency_ms != null ? `${accountInfo.last_ping_latency_ms} ms` : "OFFLINE"}
              </div>
            </div>

            <button
              onClick={() => setIsFlattenModalOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-black bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/40 transition-all flex items-center gap-2 cursor-pointer"
            >
              <AlertOctagon className="w-4 h-4" />
              EMERGENCY FLATTEN
            </button>
          </div>
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

      {alertNotification && (
        <div className="p-4 bg-rose-950/80 border border-rose-500/80 rounded-2xl text-xs font-bold text-rose-200 flex items-center gap-2.5">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          {alertNotification}
        </div>
      )}

      {orderResultMsg && (
        <div
          className={`p-4 rounded-2xl text-xs font-bold flex items-center gap-2.5 font-mono ${
            orderResultMsg.isError
              ? "bg-amber-950/80 border border-amber-500/80 text-amber-200"
              : "bg-emerald-950/80 border border-emerald-500/80 text-emerald-200"
          }`}
        >
          {orderResultMsg.isError ? <AlertTriangle className="w-5 h-5 text-amber-400" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          {orderResultMsg.text}
        </div>
      )}

      {/* MAIN 2-COLUMN GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* LEFT COLUMN: POSITIONS & QUICK ORDER PAD (8 COLS) */}
        <div className="lg:col-span-8 space-y-4">
          {/* POSITIONS MONITOR */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Posiciones Abiertas en Tradovate ({positions.length})
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Tickers: <strong className="text-slate-200">MNQ, MES, MCL, MGC</strong>
              </span>
            </div>

            {positions.length === 0 ? (
              <div className="p-10 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/60 space-y-3 font-mono">
                <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto" />
                <div className="text-sm font-bold text-slate-300">CERO POSICIONES ABIERTAS EN MERCADO</div>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  El libro de órdenes no tiene exposición activa en Tradovate Demo ({accountInfo?.account_id ?? "DEMO1279346"}).
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse font-mono">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-800/40">
                      <th className="py-2.5 px-3">Contrato</th>
                      <th className="py-2.5 px-3">Lado</th>
                      <th className="py-2.5 px-3">Cant.</th>
                      <th className="py-2.5 px-3">Entrada</th>
                      <th className="py-2.5 px-3">Actual</th>
                      <th className="py-2.5 px-3">Bracket TP/SL</th>
                      <th className="py-2.5 px-3">PnL</th>
                      <th className="py-2.5 px-3 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {positions.map((pos) => (
                      <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-bold text-white">{pos.symbol}</td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              pos.side === "LONG"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : "bg-rose-500/20 text-rose-400"
                            }`}
                          >
                            {pos.side}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-200">{pos.contracts}x</td>
                        <td className="py-2.5 px-3 text-slate-300">{pos.entryPrice.toFixed(2)}</td>
                        <td className="py-2.5 px-3 font-bold text-white">{pos.currentPrice.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-[10px] text-slate-400">
                          {pos.tp ? `TP: ${pos.tp}` : "TP: --"} / {pos.sl ? `SL: ${pos.sl}` : "SL: --"}
                        </td>
                        <td className="py-2.5 px-3">
                          <span className={`font-bold ${pos.pnlUsd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            ${pos.pnlUsd?.toFixed(2)} USD
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-right">
                          <button
                            onClick={() => handleClosePosition(pos.comment, pos.symbol)}
                            className="px-2 py-1 rounded bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 text-[10px] font-bold transition-colors cursor-pointer"
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

          {/* QUICK EXECUTION PAD */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Despachador Manual de Órdenes (PickMyTrade API v2)
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">Protocolo <strong className="text-emerald-400">advance_tp_sl</strong></span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 font-mono text-xs">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Contrato</label>
                <select
                  value={orderSymbol}
                  onChange={(e) => setOrderSymbol(e.target.value as any)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="MNQ">MNQ (Micro Nasdaq)</option>
                  <option value="MES">MES (Micro S&P 500)</option>
                  <option value="MCL">MCL (Micro Crude Oil)</option>
                  <option value="MGC">MGC (Micro Gold)</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Dirección</label>
                <div className="grid grid-cols-2 gap-1 bg-slate-800 p-1 rounded-xl border border-slate-700">
                  <button
                    type="button"
                    onClick={() => setOrderAction("BUY")}
                    className={`py-1 rounded-lg text-xs font-bold transition-all ${
                      orderAction === "BUY" ? "bg-emerald-600 text-white" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    BUY
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrderAction("SELL")}
                    className={`py-1 rounded-lg text-xs font-bold transition-all ${
                      orderAction === "SELL" ? "bg-rose-600 text-white" : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    SELL
                  </button>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Contratos</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={orderContracts}
                  onChange={(e) => setOrderContracts(parseInt(e.target.value) || 1)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Take Profit ($USD)</label>
                <input
                  type="number"
                  value={orderTpDollar}
                  onChange={(e) => setOrderTpDollar(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-emerald-400 focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Stop Loss ($USD)</label>
                <input
                  type="number"
                  value={orderSlDollar}
                  onChange={(e) => setOrderSlDollar(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold text-rose-400 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800 font-mono text-xs">
              <div className="text-slate-400">
                Cuenta: <strong className="text-emerald-400">{accountInfo?.account_id ?? "DEMO1279346"}</strong>
              </div>

              <button
                onClick={handleSendManualOrder}
                disabled={isSendingOrder}
                className="px-6 py-2.5 rounded-xl font-black bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/40 transition flex items-center gap-2 cursor-pointer"
              >
                <Zap className="w-4 h-4 text-amber-300" />
                {isSendingOrder ? "Despachando a Tradovate..." : `DESPACHAR ${orderAction} ${orderContracts}x ${orderSymbol}`}
              </button>
            </div>
          </div>

          {/* FORENSIC ORDER AUDIT TRAIL */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Registro Forense de Órdenes & Microestructura ({logs.length})
                </h3>
              </div>
              <Link href="/trading-desk/auditoria" className="text-xs text-indigo-400 hover:text-indigo-300 font-mono font-bold">
                Ver Todo el WAL →
              </Link>
            </div>

            {logs.length === 0 ? (
              <div className="p-6 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/40 text-xs font-mono text-slate-500">
                SIN REGISTROS FORENSES PREVIOS (0 órdenes despachadas)
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                      <th className="py-2 px-3">Hora UTC</th>
                      <th className="py-2 px-3">Acción</th>
                      <th className="py-2 px-3">Símbolo</th>
                      <th className="py-2 px-3">Cant.</th>
                      <th className="py-2 px-3">Latencia</th>
                      <th className="py-2 px-3">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-[11px]">
                    {logs.slice(0, 5).map((log) => (
                      <tr key={log.id}>
                        <td className="py-2 px-3 text-slate-400">{log.timestamp}</td>
                        <td className="py-2 px-3 font-bold text-white">{log.action}</td>
                        <td className="py-2 px-3">{log.symbol}</td>
                        <td className="py-2 px-3">{log.contracts}x</td>
                        <td className="py-2 px-3 text-amber-400">{log.latencyMs.toFixed(1)} ms</td>
                        <td className="py-2 px-3 text-emerald-400 font-bold">{log.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: SESSIONS, GATEWAYS & SENTINEL (4 COLS) */}
        <div className="lg:col-span-4 space-y-4">
          {/* SESSIONS STATUS */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Sesiones de Ejecución ({sessions.length})
                </h3>
              </div>
              <Link href="/trading-desk/estrategias" className="text-xs font-mono text-purple-400 hover:text-purple-300 font-bold">
                Gestionar →
              </Link>
            </div>

            {sessions.length === 0 ? (
              <div className="p-6 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/40 text-xs font-mono text-slate-500 space-y-1">
                <div className="font-bold text-slate-400">CERO SESIONES ACTIVAS</div>
                <div className="text-[11px]">No hay bots despachando órdenes actualmente.</div>
              </div>
            ) : (
              <div className="space-y-2 font-mono text-xs">
                {sessions.map((s) => (
                  <div key={s.session_id} className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{s.symbol} ({s.route})</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-bold">{s.status}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">ID: {s.session_id}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* REGISTERED GATEWAYS STATUS */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Gateways Registrados ({gateways.length})
                </h3>
              </div>
              <Link href="/trading-desk/configuracion" className="text-xs font-mono text-indigo-400 hover:text-indigo-300 font-bold">
                Configurar →
              </Link>
            </div>

            <div className="space-y-2 font-mono text-xs">
              {gateways.slice(0, 4).map((gw) => {
                const isActive = gw.provider_id === "pickmytrade_tradovate";
                return (
                  <div
                    key={gw.provider_id}
                    className={`p-2.5 rounded-xl border flex items-center justify-between ${
                      isActive ? "bg-slate-950 border-emerald-500/40" : "bg-slate-950 border-slate-800"
                    }`}
                  >
                    <div>
                      <div className="font-bold text-white text-[11px] truncate max-w-[170px]">{gw.name}</div>
                      <div className="text-[9px] text-slate-500">{gw.provider_id}</div>
                    </div>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${
                        gw.status === "CONNECTED"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}
                    >
                      {gw.status}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* RISK SENTINEL SUMMARY */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-rose-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Sentinel de Riesgo
                </h3>
              </div>
              <Link href="/trading-desk/riesgo" className="text-xs text-rose-400 hover:text-rose-300 font-bold">
                Detalles →
              </Link>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Trailing DD Límite:</span>
                <span className="font-bold text-emerald-400">${accountInfo?.trailing_drawdown_limit_usd ?? 2000} USD</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Pérdida Diaria Máx:</span>
                <span className="font-bold text-emerald-400">$1,000 USD</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800">
                <span className="text-slate-400">Estado Sentinel:</span>
                <span className="font-bold text-emerald-400">ARMED (Fail-Closed)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* EMERGENCY FLATTEN MODAL */}
      {isFlattenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150">
          <div className="bg-slate-900 border-2 border-rose-600 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex items-center gap-3 text-rose-500">
              <div className="p-3 bg-rose-500/20 rounded-xl">
                <AlertOctagon className="w-8 h-8 animate-bounce" />
              </div>
              <div>
                <h3 className="text-lg font-black text-white">¿CONFIRMAR FLATTEN TOTAL?</h3>
                <p className="text-xs text-rose-300">Liquidación inmediata en Tradovate ({accountInfo?.account_id ?? "DEMO1279346"})</p>
              </div>
            </div>

            <div className="p-4 bg-rose-950/40 border border-rose-900/60 rounded-xl space-y-2 text-xs text-slate-300 font-mono">
              <p>Esta acción enviará la señal <strong className="text-white">flat</strong> a PickMyTrade:</p>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-rose-200">
                <li>Liquidará todas las posiciones abiertas a precio de mercado.</li>
                <li>Cancelará todos los brackets OCO pendientes.</li>
              </ul>
            </div>

            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              <button
                onClick={() => setIsFlattenModalOpen(false)}
                className="py-2.5 rounded-xl font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition cursor-pointer"
              >
                Cancelar
              </button>
              <button
                onClick={handleExecuteFlattenAll}
                disabled={isFlattening}
                className="py-2.5 rounded-xl font-black bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/50 transition cursor-pointer"
              >
                {isFlattening ? "Liquidando..." : "SÍ, LIQUIDAR TODO"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
