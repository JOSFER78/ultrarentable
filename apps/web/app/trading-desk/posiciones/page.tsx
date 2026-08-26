"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  RefreshCw,
  Zap,
  ShieldCheck,
  ShieldAlert,
  TrendingUp,
  TrendingDown,
  Send,
  Target,
  Sliders,
  Percent,
  SlidersHorizontal,
  ChevronRight,
  Info,
  Clock,
  Layers,
  FileText,
  DollarSign,
  Lock,
  ArrowUpRight,
  ArrowDownRight,
  Flame,
  XCircle,
} from "lucide-react";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

interface CmeInstrumentSpec {
  symbol: "MNQ" | "MES" | "MCL" | "MGC";
  name: string;
  exchange: "CME" | "NYMEX" | "COMEX";
  tickSize: number;
  tickValueUsd: number;
  pointValueUsd: number;
  multiplier: string;
  dayMarginUsd: number;
  tradingHours: string;
  color: string;
}

const CME_SPECS: Record<string, CmeInstrumentSpec> = {
  MNQ: {
    symbol: "MNQ",
    name: "Micro E-mini Nasdaq-100",
    exchange: "CME",
    tickSize: 0.25,
    tickValueUsd: 0.5,
    pointValueUsd: 2.0,
    multiplier: "$2.00 × Índice",
    dayMarginUsd: 100,
    tradingHours: "17:00 Dom - 16:00 Vie CT",
    color: "#38bdf8",
  },
  MES: {
    symbol: "MES",
    name: "Micro E-mini S&P 500",
    exchange: "CME",
    tickSize: 0.25,
    tickValueUsd: 1.25,
    pointValueUsd: 5.0,
    multiplier: "$5.00 × Índice",
    dayMarginUsd: 100,
    tradingHours: "17:00 Dom - 16:00 Vie CT",
    color: "#818cf8",
  },
  MCL: {
    symbol: "MCL",
    name: "Micro WTI Crude Oil",
    exchange: "NYMEX",
    tickSize: 0.01,
    tickValueUsd: 1.0,
    pointValueUsd: 100.0,
    multiplier: "100 Barriles",
    dayMarginUsd: 100,
    tradingHours: "17:00 Dom - 16:00 Vie CT",
    color: "#f59e0b",
  },
  MGC: {
    symbol: "MGC",
    name: "Micro Gold",
    exchange: "COMEX",
    tickSize: 0.1,
    tickValueUsd: 1.0,
    pointValueUsd: 10.0,
    multiplier: "10 Troy Oz",
    dayMarginUsd: 100,
    tradingHours: "17:00 Dom - 16:00 Vie CT",
    color: "#eab308",
  },
};

interface AdvanceTpSlBracket {
  quantity: number;
  tp?: number;
  sl?: number;
  dollar_tp?: number;
  dollar_sl?: number;
  percentage_tp?: number;
  percentage_sl?: number;
  breakeven?: number;
  breakeven_offset?: number;
  trail?: number;
  trail_stop?: number;
  trail_trigger?: number;
  trail_freq?: number;
}

interface LivePosition {
  id: string;
  symbol: "MNQ" | "MES" | "MCL" | "MGC" | string;
  side: "LONG" | "SHORT";
  contracts: number;
  entryPrice: number;
  currentPrice: number;
  pnlUsd: number;
  pnlTicks: number;
  comment: string;
  tp?: number | null;
  sl?: number | null;
  advance_tp_sl?: AdvanceTpSlBracket[];
  status: string;
  account: string;
  createdAt: string;
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

export default function PosicionesBracketsPage() {
  const [positions, setPositions] = useState<LivePosition[]>([]);
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

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  const [filterSymbol, setFilterSymbol] = useState<string>("ALL");
  const [filterSide, setFilterSide] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const [notification, setNotification] = useState<{
    text: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const [isFlattenModalOpen, setIsFlattenModalOpen] = useState<boolean>(false);
  const [isFlattening, setIsFlattening] = useState<boolean>(false);
  const [isOrderModalOpen, setIsOrderModalOpen] = useState<boolean>(false);
  const [isSendingOrder, setIsSendingOrder] = useState<boolean>(false);

  const [newOrderSymbol, setNewOrderSymbol] = useState<"MNQ" | "MES" | "MCL" | "MGC">("MNQ");
  const [newOrderAction, setNewOrderAction] = useState<"BUY" | "SELL">("BUY");
  const [newOrderContracts, setNewOrderContracts] = useState<number>(1);
  const [newOrderTpTicks, setNewOrderTpTicks] = useState<number>(20);
  const [newOrderSlTicks, setNewOrderSlTicks] = useState<number>(12);
  const [newOrderBreakevenTicks, setNewOrderBreakevenTicks] = useState<number>(10);
  const [newOrderBreakevenOffset, setNewOrderBreakevenOffset] = useState<number>(1);
  const [newOrderTrailTicks, setNewOrderTrailTicks] = useState<number>(15);
  const [newOrderEnableTrail, setNewOrderEnableTrail] = useState<boolean>(true);

  const showToast = (text: string, type: "success" | "error" | "info" = "info", durationMs = 5000) => {
    setNotification({ text, type });
    setTimeout(() => setNotification(null), durationMs);
  };

  const fetchRealData = useCallback(async () => {
    try {
      const statusRes = await fetch("/api/v1/gateways/pickmytrade/status");
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setAccountInfo(statusData);
      }

      const posRes = await fetch("/api/v1/gateways/pickmytrade/positions");
      if (posRes.ok) {
        const posData = await posRes.json();
        setPositions(Array.isArray(posData) ? posData : []);
      }
    } catch (e) {
      console.error("Error al sincronizar posiciones reales de PickMyTrade:", e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRealData();
    if (!autoRefresh) return;
    const interval = setInterval(fetchRealData, 3000);
    return () => clearInterval(interval);
  }, [fetchRealData, autoRefresh]);

  const handleClosePartial = async (pos: LivePosition, pct: number) => {
    const contractsToClose = Math.max(1, Math.round((pos.contracts * pct) / 100));
    const isFullClose = pct === 100 || contractsToClose >= pos.contracts;

    try {
      if (isFullClose) {
        const res = await fetch("/api/v1/gateways/pickmytrade/close-comment", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ticker: pos.symbol,
            comment: pos.comment,
            account: accountInfo.account_id,
            token: "3VxOjkjylyJKkt3oN4Jydg",
          }),
        });

        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`✅ Posición ${pos.symbol} (UID: ${pos.comment}) cerrada al 100% en Tradovate (${data.latency_ms} ms).`, "success");
          fetchRealData();
        } else {
          showToast(`⚠️ Error al cerrar posición: ${data.response?.message || "Rechazada"}`, "error");
        }
      } else {
        const reverseAction = pos.side === "LONG" ? "sell" : "buy";
        const res = await fetch("/api/v1/gateways/pickmytrade/order", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ticker: pos.symbol,
            action: reverseAction,
            contracts: contractsToClose,
            orderType: "market",
            account: accountInfo.account_id,
            token: "3VxOjkjylyJKkt3oN4Jydg",
            comment: pos.comment,
          }),
        });

        const data = await res.json();
        if (res.ok && data.success) {
          showToast(`✅ Cierre parcial ${pct}% (${contractsToClose}x ${pos.symbol}) ejecutado en Tradovate.`, "success");
          fetchRealData();
        } else {
          showToast(`⚠️ Cierre parcial rechazado: ${JSON.stringify(data.pickmytrade_response)}`, "error");
        }
      }
    } catch (err: any) {
      showToast(`❌ Error de red al ejecutar cierre: ${err.message}`, "error");
    }
  };

  const handleDispatchOrder = async () => {
    setIsSendingOrder(true);
    const spec = CME_SPECS[newOrderSymbol] || CME_SPECS.MNQ;
    const dollarTp = newOrderTpTicks * spec.tickValueUsd * newOrderContracts;
    const dollarSl = newOrderSlTicks * spec.tickValueUsd * newOrderContracts;

    const payload = {
      ticker: newOrderSymbol,
      action: newOrderAction.toLowerCase(),
      contracts: newOrderContracts,
      orderType: "market",
      account: accountInfo.account_id,
      token: "3VxOjkjylyJKkt3oN4Jydg",
      comment: `sig_${newOrderSymbol.toLowerCase()}_${newOrderAction.toLowerCase()}_${Date.now().toString().slice(-6)}`,
      advance_tp_sl: [
        {
          quantity: newOrderContracts,
          dollar_tp: dollarTp,
          dollar_sl: dollarSl,
          breakeven: newOrderBreakevenTicks,
          breakeven_offset: newOrderBreakevenOffset,
          trail: newOrderEnableTrail ? 1 : 0,
          trail_stop: newOrderTrailTicks,
          trail_trigger: newOrderTpTicks * 0.5,
          trail_freq: 1,
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
        showToast(
          `✅ Orden ${newOrderAction} ${newOrderContracts}x ${newOrderSymbol} despachada a Tradovate Demo (${data.latency_ms} ms) con Brackets advance_tp_sl.`,
          "success",
          6000
        );
        setIsOrderModalOpen(false);
        fetchRealData();
      } else {
        showToast(`⚠️ Despacho rechazado: ${data.pickmytrade_response?.message || JSON.stringify(data.pickmytrade_response)}`, "error");
      }
    } catch (err: any) {
      showToast(`❌ Error de conexión con gateway PickMyTrade: ${err.message}`, "error");
    } finally {
      setIsSendingOrder(false);
    }
  };

  const filteredPositions = useMemo(() => {
    return positions.filter((pos) => {
      const matchSymbol = filterSymbol === "ALL" || pos.symbol.toUpperCase() === filterSymbol.toUpperCase();
      const matchSide = filterSide === "ALL" || pos.side.toUpperCase() === filterSide.toUpperCase();
      const matchSearch =
        !searchQuery ||
        pos.comment.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pos.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        pos.id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchSymbol && matchSide && matchSearch;
    });
  }, [positions, filterSymbol, filterSide, searchQuery]);

  const totalFloatingPnlUsd = useMemo(() => {
    return positions.reduce((acc, p) => acc + (p.pnlUsd || 0), 0);
  }, [positions]);

  const totalActiveContracts = useMemo(() => {
    return positions.reduce((acc, p) => acc + (p.contracts || 0), 0);
  }, [positions]);

  return (
    <div className="space-y-4 font-sans">
      {/* TOP TELEMETRY BAR & CME FINANCIAL STRIP */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
        <div className="flex flex-col xl:flex-row items-start xl:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400">
              <BarChart3 className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl md:text-2xl font-black text-white tracking-tight flex items-center gap-2">
                  Monitor de Posiciones & Brackets
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                    CME MICROESTRUCTURA
                  </span>
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  GATEWAY ACTIVO
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 flex flex-wrap items-center gap-2 font-mono">
                <span>Broker: <strong className="text-slate-200">{accountInfo.broker}</strong></span>
                <span>•</span>
                <span>Cuenta: <strong className="text-emerald-400">{accountInfo.account_id}</strong></span>
                <span>•</span>
                <span>Protocolo: <strong className="text-blue-400">advance_tp_sl v2</strong></span>
                <span>•</span>
                <span>Latencia: <strong className="text-amber-400">{accountInfo.last_ping_latency_ms} ms</strong></span>
              </p>
            </div>
          </div>

          {/* Key Metrics Strip */}
          <div className="flex flex-wrap items-center gap-2 w-full xl:w-auto">
            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60 flex-1 min-w-[120px]">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Contratos Activos</div>
              <div className="text-base font-bold font-mono text-white flex items-center gap-1">
                <span>{totalActiveContracts}x</span>
                <span className="text-[10px] font-normal text-slate-400">({positions.length} pos)</span>
              </div>
            </div>

            <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60 flex-1 min-w-[150px]">
              <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">PnL Flotante Total</div>
              <div className={`text-base font-bold font-mono flex items-center gap-1 ${totalFloatingPnlUsd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {totalFloatingPnlUsd >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {totalFloatingPnlUsd >= 0 ? "+" : ""}${totalFloatingPnlUsd.toFixed(2)} USD
              </div>
            </div>

            <button
              onClick={() => setIsOrderModalOpen(true)}
              className="px-3.5 py-2 rounded-xl text-xs font-black bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30 transition flex items-center gap-1.5 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
              Nueva Orden Bracket
            </button>
          </div>
        </div>
      </div>

      {notification && (
        <div className={`p-3.5 rounded-xl text-xs font-bold flex items-center gap-2.5 transition-all shadow-lg ${
          notification.type === "error" ? "bg-rose-950/90 border border-rose-500/80 text-rose-200" : "bg-emerald-950/90 border border-emerald-500/80 text-emerald-200"
        }`}>
          <span>{notification.text}</span>
        </div>
      )}

      {/* CME QUICK CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.values(CME_SPECS).map((spec) => {
          const specCount = positions.filter((p) => p.symbol.toUpperCase() === spec.symbol).length;
          const isFilterActive = filterSymbol === spec.symbol;

          return (
            <div
              key={spec.symbol}
              onClick={() => setFilterSymbol(isFilterActive ? "ALL" : spec.symbol)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                isFilterActive
                  ? "bg-slate-800/90 border-blue-500 ring-1 ring-blue-500 shadow-md"
                  : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: spec.color }} />
                  <strong className="text-sm font-black font-mono text-white">{spec.symbol}</strong>
                </div>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {specCount} abiertas
                </span>
              </div>
              <div className="text-[11px] text-slate-300 font-medium truncate">{spec.name}</div>
              <div className="grid grid-cols-2 gap-1 mt-2 pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-400">
                <div>Tick: <span className="text-slate-200">{spec.tickSize} pts</span></div>
                <div>Valor Tick: <span className="text-emerald-400">${spec.tickValueUsd.toFixed(2)}</span></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* MAIN POSITIONS SECTION */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            Posiciones Abiertas en Mercado ({positions.length})
          </h3>
          <span className="text-xs font-mono text-slate-400">100% Zero-Mocks</span>
        </div>

        {positions.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-950/60 space-y-4">
            <CheckCircle2 className="w-10 h-10 text-slate-600 mx-auto" />
            <div>
              <div className="text-base font-bold text-slate-200 font-mono">
                CERO POSICIONES ABIERTAS EN MERCADO
              </div>
              <p className="text-xs text-slate-400 max-w-lg mx-auto mt-1">
                El libro de órdenes no tiene exposición activa en Tradovate Demo / CME.
              </p>
            </div>
            <button
              onClick={() => setIsOrderModalOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white transition cursor-pointer"
            >
              Despachar Orden de Prueba con Brackets
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredPositions.map((pos) => (
              <div key={pos.id} className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-white font-bold text-sm">{pos.symbol} · {pos.side} {pos.contracts}x</span>
                  <span className={`font-bold ${pos.pnlUsd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                    ${pos.pnlUsd?.toFixed(2)} USD
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-400 text-[11px]">
                  <span>Entrada: {pos.entryPrice} · Actual: {pos.currentPrice}</span>
                  <div className="flex gap-1.5">
                    <button onClick={() => handleClosePartial(pos, 50)} className="px-2 py-0.5 rounded bg-slate-800 text-white">50%</button>
                    <button onClick={() => handleClosePartial(pos, 100)} className="px-2 py-0.5 rounded bg-rose-600 text-white font-bold">100% CERRAR</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ORDER MODAL */}
      {isOrderModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">Nueva Orden con advance_tp_sl</h3>
              <button onClick={() => setIsOrderModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="space-y-3 text-xs font-mono">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Activo</label>
                  <select value={newOrderSymbol} onChange={(e) => setNewOrderSymbol(e.target.value as any)} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white">
                    <option value="MNQ">MNQ (Micro Nasdaq)</option>
                    <option value="MES">MES (Micro S&P)</option>
                    <option value="MCL">MCL (Micro Crude)</option>
                    <option value="MGC">MGC (Micro Gold)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Dirección</label>
                  <select value={newOrderAction} onChange={(e) => setNewOrderAction(e.target.value as any)} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white">
                    <option value="BUY">BUY (Largo)</option>
                    <option value="SELL">SELL (Corto)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Contratos</label>
                <input type="number" min="1" max="10" value={newOrderContracts} onChange={(e) => setNewOrderContracts(parseInt(e.target.value) || 1)} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white" />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-emerald-400 block mb-1">TP Ticks</label>
                  <input type="number" value={newOrderTpTicks} onChange={(e) => setNewOrderTpTicks(parseInt(e.target.value) || 20)} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white" />
                </div>
                <div>
                  <label className="text-[10px] text-rose-400 block mb-1">SL Ticks</label>
                  <input type="number" value={newOrderSlTicks} onChange={(e) => setNewOrderSlTicks(parseInt(e.target.value) || 12)} className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2 text-white" />
                </div>
              </div>

              <button
                onClick={handleDispatchOrder}
                disabled={isSendingOrder}
                className="w-full py-2.5 rounded-xl font-bold bg-blue-600 hover:bg-blue-500 text-white transition flex items-center justify-center gap-2 cursor-pointer"
              >
                {isSendingOrder ? "Despachando..." : `DESPACHAR ${newOrderAction} ${newOrderContracts}x ${newOrderSymbol}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
