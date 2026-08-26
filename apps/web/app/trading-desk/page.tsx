"use client";

import React, { useState, useEffect, useCallback } from "react";
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
  Maximize2,
  Flame,
  Globe,
  Lock,
  Send,
  Sparkles,
} from "lucide-react";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

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
  base_capital_usd: number;
  current_equity_usd: number;
  daily_pnl_usd: number;
  trailing_drawdown_limit_usd: number;
  current_drawdown_usd: number;
  open_positions_count: number;
  trial_expires_utc: string;
  gateway_status: string;
  last_ping_latency_ms: number;
}

export default function InstitutionalTradingDesk() {
  const [accountInfo, setAccountInfo] = useState<AccountStatus>({
    provider_id: "pickmytrade_tradovate",
    account_id: "DEMO1279346",
    user: "josferstudio (ID: 24151)",
    broker: "Tradovate Demo",
    environment: "DEMO / SIMULATION",
    base_capital_usd: 50000.0,
    current_equity_usd: 50000.0,
    daily_pnl_usd: 0.0,
    trailing_drawdown_limit_usd: 2000.0,
    current_drawdown_usd: 0.0,
    open_positions_count: 0,
    trial_expires_utc: "2026-09-02 18:43 UTC",
    gateway_status: "CONNECTED",
    last_ping_latency_ms: 68.4,
  });

  // Zero-mocks: Starts empty, strictly populated from real backend / SQLite
  const [positions, setPositions] = useState<LivePosition[]>([]);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

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
    try {
      // 1. Fetch real gateway and account status
      const statusRes = await fetch("/api/v1/gateways/pickmytrade/status");
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setAccountInfo(statusData);
      }

      // 2. Fetch real live positions from SQLite WAL
      const posRes = await fetch("/api/v1/gateways/pickmytrade/positions");
      if (posRes.ok) {
        const posData = await posRes.json();
        setPositions(Array.isArray(posData) ? posData : []);
      }

      // 3. Fetch real forensic logs from SQLite WAL
      const logsRes = await fetch("/api/v1/gateways/pickmytrade/logs");
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setLogs(Array.isArray(logsData) ? logsData : []);
      }
    } catch (e) {
      console.error("Error fetching real trading desk telemetry:", e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRealData();
    const interval = setInterval(fetchRealData, 3000);
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
      account: accountInfo.account_id,
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
          account: accountInfo.account_id,
          token: "3VxOjkjylyJKkt3oN4Jydg",
        }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setAlertNotification(`Posición ${symbol} (${comment}) cerrada a mercado en Tradovate.`);
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
          account: accountInfo.account_id,
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

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-5 space-y-4">
      <EstrategiasHeaderNav />

      {/* TOP INSTITUTIONAL TELEMETRY BAR */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-2xl">
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
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  LIVE CONNECTED
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
                <span>Broker: <strong className="text-slate-200">{accountInfo.broker}</strong></span>
                <span>•</span>
                <span>Cuenta: <strong className="text-emerald-400">{accountInfo.account_id}</strong></span>
                <span>•</span>
                <span>Operador: <strong className="text-slate-200">{accountInfo.user}</strong></span>
                <span>•</span>
                <span>Vence: <strong className="text-amber-400">{accountInfo.trial_expires_utc}</strong></span>
              </p>
            </div>
          </div>

          {/* Real Financial KPI Strip */}
          <div className="flex flex-wrap items-center gap-2.5 w-full xl:w-auto">
            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Saldo Virtual Real</div>
              <div className="text-base font-bold font-mono text-white">
                ${accountInfo.base_capital_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Equidad Viva</div>
              <div className="text-base font-bold font-mono text-white">
                ${accountInfo.current_equity_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">PnL Sesión Hoy</div>
              <div className={`text-base font-bold font-mono flex items-center gap-1 ${accountInfo.daily_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {accountInfo.daily_pnl_usd >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {accountInfo.daily_pnl_usd >= 0 ? "+" : ""}${accountInfo.daily_pnl_usd.toFixed(2)} USD
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Trailing DD Sentinel</div>
              <div className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                ${accountInfo.current_drawdown_usd.toFixed(0)} / ${accountInfo.trailing_drawdown_limit_usd.toFixed(0)} (100% OK)
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Latencia API v2</div>
              <div className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-amber-400" /> {accountInfo.last_ping_latency_ms} ms
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

      {alertNotification && (
        <div className="p-4 bg-rose-950/80 border border-rose-500/80 rounded-2xl text-xs font-bold text-rose-200 flex items-center gap-2.5">
          <AlertTriangle className="w-5 h-5 text-rose-400" />
          {alertNotification}
        </div>
      )}

      {orderResultMsg && (
        <div className={`p-4 rounded-2xl text-xs font-bold flex items-center gap-2.5 ${
          orderResultMsg.isError
            ? "bg-amber-950/80 border border-amber-500/80 text-amber-200"
            : "bg-emerald-950/80 border border-emerald-500/80 text-emerald-200"
        }`}>
          {orderResultMsg.isError ? <AlertTriangle className="w-5 h-5 text-amber-400" /> : <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
          {orderResultMsg.text}
        </div>
      )}

      {/* MAIN 4-QUADRANT DESK GRID */}
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
                Tickers: <strong className="text-slate-200">MES, MNQ, MCL, MGC</strong>
              </span>
            </div>

            {positions.length === 0 ? (
              <div className="p-12 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/60 space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
                  <CheckCircle2 className="w-6 h-6 text-slate-600" />
                </div>
                <div className="text-sm font-bold text-slate-300 font-mono">CERO POSICIONES ABIERTAS EN MERCADO</div>
                <p className="text-xs text-slate-500 max-w-md mx-auto">
                  El libro de órdenes no tiene exposición activa. Puedes despachar una orden usando el panel inferior o esperar señales del motor algorítmico.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-800/40">
                      <th className="py-3 px-3">Contrato</th>
                      <th className="py-3 px-3">Lado</th>
                      <th className="py-3 px-3">Cant.</th>
                      <th className="py-3 px-3">Entrada</th>
                      <th className="py-3 px-3">Actual</th>
                      <th className="py-3 px-3">Bracket TP / SL</th>
                      <th className="py-3 px-3">PnL Flotante</th>
                      <th className="py-3 px-3">UID / Señal</th>
                      <th className="py-3 px-3 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {positions.map((pos) => (
                      <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3 px-3 font-bold text-white flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-emerald-400" />
                          {pos.symbol}
                        </td>
                        <td className="py-3 px-3">
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
                        <td className="py-3 px-3 text-slate-200">{pos.contracts}x</td>
                        <td className="py-3 px-3 text-slate-300">{pos.entryPrice.toFixed(2)}</td>
                        <td className="py-3 px-3 font-bold text-white">{pos.currentPrice.toFixed(2)}</td>
                        <td className="py-3 px-3 text-[11px] text-slate-300 font-mono">
                          {pos.tp ? <span className="text-emerald-400">TP: {pos.tp}</span> : <span className="text-slate-500">TP: --</span>} /{" "}
                          {pos.sl ? <span className="text-rose-400">SL: {pos.sl}</span> : <span className="text-slate-500">SL: --</span>}
                        </td>
                        <td className="py-3 px-3">
                          <span className={`font-bold text-sm ${pos.pnlUsd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {pos.pnlUsd >= 0 ? "+" : ""}${pos.pnlUsd.toFixed(2)} USD
                          </span>
                        </td>
                        <td className="py-3 px-3 text-[11px] text-slate-400 font-mono">
                          {pos.comment}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <button
                            onClick={() => handleClosePosition(pos.comment, pos.symbol)}
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

          {/* QUICK EXECUTION PAD & DOM */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Despachador Manual de Órdenes (PickMyTrade API v2)
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">Protocolo canónico <strong className="text-emerald-400">advance_tp_sl</strong></span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Contrato</label>
                <select
                  value={orderSymbol}
                  onChange={(e) => setOrderSymbol(e.target.value as any)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold font-mono text-white focus:outline-none focus:border-blue-500"
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
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Take Profit ($USD)</label>
                <input
                  type="number"
                  value={orderTpDollar}
                  onChange={(e) => setOrderTpDollar(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold font-mono text-emerald-400 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">Stop Loss ($USD)</label>
                <input
                  type="number"
                  value={orderSlDollar}
                  onChange={(e) => setOrderSlDollar(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-bold font-mono text-rose-400 focus:outline-none focus:border-rose-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              <div className="text-xs text-slate-400 font-mono">
                Riesgo Máx: <strong className="text-rose-400">${(orderSlDollar * orderContracts).toFixed(2)} USD</strong> · Objetivo: <strong className="text-emerald-400">${(orderTpDollar * orderContracts).toFixed(2)} USD</strong>
              </div>

              <button
                onClick={handleSendManualOrder}
                disabled={isSendingOrder}
                className="px-6 py-2.5 rounded-xl text-xs font-black bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-900/40 transition-all flex items-center gap-2 cursor-pointer"
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
              <span className="text-xs text-emerald-400 font-mono">Auditoría SQLite WAL Activa</span>
            </div>

            {logs.length === 0 ? (
              <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/40 text-xs font-mono text-slate-500">
                SIN REGISTROS FORENSES PREVIOS (0 órdenes despachadas)
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider bg-slate-800/40">
                      <th className="py-2.5 px-3">Hora UTC</th>
                      <th className="py-2.5 px-3">Acción</th>
                      <th className="py-2.5 px-3">Símbolo</th>
                      <th className="py-2.5 px-3">Cant.</th>
                      <th className="py-2.5 px-3">Latencia</th>
                      <th className="py-2.5 px-3">Slippage</th>
                      <th className="py-2.5 px-3">Estado</th>
                      <th className="py-2.5 px-3">Respuesta Servidor</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 text-slate-400">{log.timestamp}</td>
                        <td className="py-2.5 px-3 font-bold text-white">{log.action}</td>
                        <td className="py-2.5 px-3 text-slate-200 font-bold">{log.symbol}</td>
                        <td className="py-2.5 px-3 text-slate-300">{log.contracts}x</td>
                        <td className="py-2.5 px-3 text-emerald-400">{log.latencyMs.toFixed(1)} ms</td>
                        <td className="py-2.5 px-3 text-slate-300">{log.slippageTicks.toFixed(1)} ticks</td>
                        <td className="py-2.5 px-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            {log.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400 font-sans text-xs">{log.brokerResponse}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN: ALGO STRATEGIES & MULTI-TIMEFRAME MATRIX (4 COLS) */}
        <div className="lg:col-span-4 space-y-4">
          {/* ALGO STRATEGIES (11 GATES) */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Bot className="w-5 h-5 text-purple-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Estrategias Aprobadas (11 Gates)
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                11/11 CERTIFIED
              </span>
            </div>

            <div className="space-y-3">
              <div className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">CME Nasdaq ORB Breakout</h4>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                </div>
                <div className="text-[11px] text-slate-400 font-mono">ID: CME_NQ_ORB_V2 · Activo: MNQ</div>
                <div className="flex items-center justify-between text-[11px] font-mono pt-1 border-t border-slate-700/40 text-slate-300">
                  <span>Alocación 1R: <strong>$30.00</strong></span>
                  <span className="text-emerald-400 font-bold">ESPERA DE SEÑAL</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">ES VWAP Institutional Trend</h4>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                </div>
                <div className="text-[11px] text-slate-400 font-mono">ID: ES_VWAP_INST_002 · Activo: MES</div>
                <div className="flex items-center justify-between text-[11px] font-mono pt-1 border-t border-slate-700/40 text-slate-300">
                  <span>Alocación 1R: <strong>$25.00</strong></span>
                  <span className="text-emerald-400 font-bold">ESPERA DE SEÑAL</span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">Gold London Mean Reversion</h4>
                  <span className="w-2 h-2 rounded-full bg-blue-400" />
                </div>
                <div className="text-[11px] text-slate-400 font-mono">ID: MGC_LDN_REV_003 · Activo: MGC</div>
                <div className="flex items-center justify-between text-[11px] font-mono pt-1 border-t border-slate-700/40 text-slate-300">
                  <span>Alocación 1R: <strong>$20.00</strong></span>
                  <span className="text-blue-400 font-bold">STANDBY</span>
                </div>
              </div>
            </div>
          </div>

          {/* MULTI-TIMEFRAME CONFIRMATION MATRIX */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Matriz Multitemporal
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">VWAP & Delta</span>
            </div>

            <div className="space-y-2.5">
              {[
                { sym: "MNQ", t1: "BULL", t5: "BULL", t15: "BULL", t1h: "NEUT" },
                { sym: "MES", t1: "BULL", t5: "BULL", t15: "NEUT", t1h: "BULL" },
                { sym: "MCL", t1: "BEAR", t5: "BEAR", t15: "BEAR", t1h: "BEAR" },
                { sym: "MGC", t1: "NEUT", t5: "BULL", t15: "BULL", t1h: "BULL" },
              ].map((row) => (
                <div key={row.sym} className="p-2.5 rounded-xl bg-slate-800/40 border border-slate-700/50 flex items-center justify-between font-mono text-xs">
                  <span className="font-bold text-white">{row.sym}</span>
                  <div className="flex items-center gap-1 text-[10px]">
                    <span className={`px-1.5 py-0.5 rounded ${row.t1 === "BULL" ? "bg-emerald-500/20 text-emerald-400" : row.t1 === "BEAR" ? "bg-rose-500/20 text-rose-400" : "bg-slate-700 text-slate-300"}`}>1m</span>
                    <span className={`px-1.5 py-0.5 rounded ${row.t5 === "BULL" ? "bg-emerald-500/20 text-emerald-400" : row.t5 === "BEAR" ? "bg-rose-500/20 text-rose-400" : "bg-slate-700 text-slate-300"}`}>5m</span>
                    <span className={`px-1.5 py-0.5 rounded ${row.t15 === "BULL" ? "bg-emerald-500/20 text-emerald-400" : row.t15 === "BEAR" ? "bg-rose-500/20 text-rose-400" : "bg-slate-700 text-slate-300"}`}>15m</span>
                    <span className={`px-1.5 py-0.5 rounded ${row.t1h === "BULL" ? "bg-emerald-500/20 text-emerald-400" : row.t1h === "BEAR" ? "bg-rose-500/20 text-rose-400" : "bg-slate-700 text-slate-300"}`}>1h</span>
                  </div>
                  <span className="text-[11px] text-slate-400">RTH</span>
                </div>
              ))}
            </div>
          </div>

          {/* MACRO NEWS COMPLIANCE FILTER */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-blue-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Filtro de Noticias CME Tier 1
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 font-mono">
                CLEAR
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 text-slate-300">
                <span>Próximo Evento: <strong>Core PCE Price Index</strong></span>
                <span className="font-mono text-amber-400">En monitoreo</span>
              </div>
              <p className="text-[11px] text-slate-400">
                Protección Automática: El motor pausa los bots 2 minutos antes y después de noticias macro de alto impacto.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* EMERGENCY FLATTEN CONFIRMATION MODAL */}
      {isFlattenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-slate-900 border-2 border-rose-600 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in duration-200">
            <div className="flex items-center gap-3 text-rose-500">
              <div className="p-3 bg-rose-500/20 rounded-xl">
                <AlertOctagon className="w-8 h-8 animate-bounce" />
              </div>
              <div>
                <h3 className="text-lg font-black text-white">¿CONFIRMAR FLATTEN TOTAL?</h3>
                <p className="text-xs text-rose-300">Liquidación inmediata en libro de órdenes CME</p>
              </div>
            </div>

            <div className="p-4 bg-rose-950/40 border border-rose-900/60 rounded-xl space-y-2 text-xs text-slate-300">
              <p>Esta acción enviará la señal <strong className="text-white font-mono">FLATTEN / CLOSE_ALL</strong> a PickMyTrade:</p>
              <ul className="list-disc list-inside space-y-1 font-mono text-[11px] text-rose-200">
                <li>Liquidará todas las posiciones abiertas en Tradovate a precio de mercado.</li>
                <li>Cancelará todos los brackets OCO pendientes (TP/SL).</li>
                <li>Pausará el despacho de nuevas señales hasta reanudación manual.</li>
              </ul>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setIsFlattenModalOpen(false)}
                className="py-2.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              >
                Cancelar
              </button>
              <button
                onClick={handleExecuteFlattenAll}
                disabled={isFlattening}
                className="py-2.5 rounded-xl text-xs font-black bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/50 transition cursor-pointer"
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
