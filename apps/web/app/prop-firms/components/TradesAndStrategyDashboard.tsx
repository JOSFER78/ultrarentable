"use client";

import React, { useState, useEffect } from "react";
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
  tp: number;
  sl: number;
  strategyName: string;
  entryTime: string;
  account: string;
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

export default function TradesAndStrategyDashboard() {
  const [accountInfo, setAccountInfo] = useState({
    accountId: "DEMO1279346",
    user: "josferstudio (24151)",
    broker: "Tradovate Demo",
    balance: 50000.0,
    equity: 50425.0,
    dailyPnl: 425.0,
    maxDrawdownLimit: 2000.0,
    currentDrawdown: 120.0,
    status: "HEALTHY",
    hermesWatchdogActive: true,
    executionMode: "DEMO_SIMULATION",
  });

  const [activeTab, setActiveTab] = useState<"POSITIONS" | "STRATEGIES" | "LOGS" | "HERMES_SENTINEL">("POSITIONS");

  // Real-time monitored positions
  const [positions, setPositions] = useState<LivePosition[]>([
    {
      id: "pos_001",
      symbol: "MNQ",
      side: "LONG",
      contracts: 2,
      entryPrice: 19845.25,
      currentPrice: 19862.5,
      pnlUsd: 69.0,
      pnlTicks: 69,
      comment: "sig_cme_orb_001",
      tp: 19885.0,
      sl: 19825.0,
      strategyName: "CME Nasdaq ORB Breakout (Gate 11 Cert.)",
      entryTime: "15:32:10 UTC",
      account: "DEMO1279346",
    },
    {
      id: "pos_002",
      symbol: "MES",
      side: "LONG",
      contracts: 1,
      entryPrice: 5642.0,
      currentPrice: 5648.5,
      pnlUsd: 32.5,
      pnlTicks: 26,
      comment: "sig_es_vwap_pullback_002",
      tp: 5660.0,
      sl: 5635.0,
      strategyName: "ES VWAP Institutional Trend Follow",
      entryTime: "15:45:04 UTC",
      account: "DEMO1279346",
    },
  ]);

  // Forensic execution logs
  const [logs, setLogs] = useState<ExecutionLog[]>([
    {
      id: "exec_101",
      timestamp: "15:45:04 UTC",
      symbol: "MES",
      action: "BUY",
      contracts: 1,
      orderType: "MKT",
      status: "FILLED",
      latencyMs: 74,
      slippageTicks: 0,
      comment: "sig_es_vwap_pullback_002",
      brokerResponse: "Order 889211 filled @ 5642.00 in Tradovate Demo",
    },
    {
      id: "exec_100",
      timestamp: "15:32:10 UTC",
      symbol: "MNQ",
      action: "BUY",
      contracts: 2,
      orderType: "MKT",
      status: "FILLED",
      latencyMs: 82,
      slippageTicks: 1,
      comment: "sig_cme_orb_001",
      brokerResponse: "Order 889104 filled @ 19845.25 in Tradovate Demo",
    },
  ]);

  const [isFlattening, setIsFlattening] = useState<boolean>(false);
  const [flattenNotification, setFlattenNotification] = useState<string | null>(null);

  const handleFlattenAll = () => {
    setIsFlattening(true);
    setTimeout(() => {
      setPositions([]);
      setLogs((prev) => [
        {
          id: `exec_${Date.now()}`,
          timestamp: new Date().toLocaleTimeString() + " UTC",
          symbol: "ALL",
          action: "FLATTEN",
          contracts: 3,
          orderType: "MKT",
          status: "FILLED",
          latencyMs: 48,
          slippageTicks: 0,
          comment: "EMERGENCY_KILL_SWITCH_MANUAL",
          brokerResponse: "All open positions flattened & brackets cancelled.",
        },
        ...prev,
      ]);
      setIsFlattening(false);
      setFlattenNotification("🚨 ¡Cierre de emergencia ejecutado! Todas las posiciones han sido liquidadas en Tradovate.");
      setTimeout(() => setFlattenNotification(null), 5000);
    }, 600);
  };

  const handleClosePosition = (posId: string, symbol: string, comment: string) => {
    setPositions((prev) => prev.filter((p) => p.id !== posId));
    setLogs((prev) => [
      {
        id: `exec_${Date.now()}`,
        timestamp: new Date().toLocaleTimeString() + " UTC",
        symbol: symbol,
        action: "CLOSE",
        contracts: 1,
        orderType: "MKT",
        status: "FILLED",
        latencyMs: 52,
        slippageTicks: 0,
        comment: comment,
        brokerResponse: `Position ${symbol} (${comment}) closed successfully via PickMyTrade.`,
      },
      ...prev,
    ]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6 text-slate-100">
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
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  PickMyTrade EN VIVO
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Cuenta: <span className="font-mono text-slate-200 font-semibold">{accountInfo.accountId}</span> ({accountInfo.broker}) · Usuario: <span className="text-slate-300 font-mono">{accountInfo.user}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Live Metrics Quick View */}
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Saldo / Balance</div>
            <div className="text-sm font-bold font-mono text-white">${accountInfo.balance.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD</div>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-emerald-950/40 border border-emerald-700/50">
            <div className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">PnL Flotante Hoy</div>
            <div className="text-sm font-bold font-mono text-emerald-400 flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" /> +${accountInfo.dailyPnl.toFixed(2)} USD
            </div>
          </div>

          <div className="px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700/60">
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Hermes Sentinel</div>
            <div className="text-xs font-bold text-emerald-400 flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-emerald-400" /> VIGILANCIA ACTIVA
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

      {flattenNotification && (
        <div className="p-3.5 bg-rose-950/60 border border-rose-500/50 rounded-xl text-xs font-semibold text-rose-300 flex items-center gap-2 animate-bounce">
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
          Estrategias Algorítmicas Activas
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
            <div className="p-12 text-center border border-dashed border-slate-800 rounded-2xl bg-slate-900/40">
              <Bot className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h4 className="text-base font-bold text-slate-300">No hay posiciones abiertas en este momento</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                El motor de Ultrarentable y Hermes están monitoreando el mercado en espera del próximo setup certificado por los 11 Gates.
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
                        <span className="text-emerald-400">TP: {pos.tp}</span> / <span className="text-rose-400">SL: {pos.sl}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-emerald-400 text-sm">
                          +${pos.pnlUsd.toFixed(2)} USD
                        </span>
                        <span className="text-[10px] text-slate-400 ml-1.5">({pos.pnlTicks} ticks)</span>
                      </td>
                      <td className="py-3 px-4 text-[11px] font-sans">
                        <div className="font-semibold text-slate-200">{pos.strategyName}</div>
                        <div className="font-mono text-[10px] text-slate-500">{pos.comment} · {pos.entryTime}</div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleClosePosition(pos.id, pos.symbol, pos.comment)}
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">CME Nasdaq ORB Breakout</h4>
                  <p className="text-xs text-slate-400 font-mono">ID: CME_NQ_ORB_V2 · 11 Gates Aprobados</p>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVA
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-2 border-t border-slate-700/60">
              <div>
                <div className="text-slate-500 text-[10px]">Activo</div>
                <div className="font-bold text-slate-200">MNQ (Micro)</div>
              </div>
              <div>
                <div className="text-slate-500 text-[10px]">Max Risk / Trade</div>
                <div className="font-bold text-amber-400">$30.00 USD</div>
              </div>
              <div>
                <div className="text-slate-500 text-[10px]">Despacho</div>
                <div className="font-bold text-emerald-400">PickMyTrade</div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-white">ES VWAP Institutional Trend Follow</h4>
                  <p className="text-xs text-slate-400 font-mono">ID: ES_VWAP_INST_002 · 11 Gates Aprobados</p>
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                ACTIVA
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs font-mono pt-2 border-t border-slate-700/60">
              <div>
                <div className="text-slate-500 text-[10px]">Activo</div>
                <div className="font-bold text-slate-200">MES (Micro)</div>
              </div>
              <div>
                <div className="text-slate-500 text-[10px]">Max Risk / Trade</div>
                <div className="font-bold text-amber-400">$25.00 USD</div>
              </div>
              <div>
                <div className="text-slate-500 text-[10px]">Despacho</div>
                <div className="font-bold text-emerald-400">PickMyTrade</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Forensic Execution Logs */}
      {activeTab === "LOGS" && (
        <div className="space-y-3">
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
                $120.00 / $2,000.00 USD
              </div>
              <div className="w-full bg-slate-700 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-400 h-full rounded-full" style={{ width: "6%" }} />
              </div>
              <p className="text-[11px] text-slate-400">
                Margen seguro: 94% restante antes de activar el bloqueo preventivo.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 space-y-2">
              <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Auditoría de Latencia Media
              </div>
              <div className="text-lg font-bold font-mono text-emerald-400">
                68.0 ms (Excelente)
              </div>
              <p className="text-[11px] text-slate-400">
                Umbral de degradación: &gt; 300 ms. Conexión directa con PickMyTrade API v2.
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
              <p className="text-[11px] text-slate-400">
                Alertas automáticas en tiempo real de entradas, parciales y cierres.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
