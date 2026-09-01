"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getApiUrl } from "@/lib/api";
import {
  Activity,
  Bot,
  Zap,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  ShieldAlert,
  AlertOctagon,
  RefreshCw,
  Send,
  Terminal,
  Download,
  Copy,
  Check,
  CheckCircle2,
  AlertTriangle,
  Play,
  Pause,
  Sliders,
  Layers,
  Radio,
  WifiOff,
  Server,
  FileCode,
  Calculator,
  Trash2,
} from "lucide-react";

interface NinjaTraderAccount {
  account_id: string;
  account_name: string;
  account_type: string;
  broker: string;
  base_capital_usd: number;
  current_equity_usd: number;
  daily_pnl_usd: number;
  realized_pnl_usd: number;
  unrealized_pnl_usd: number;
  peak_equity_usd: number;
  max_trailing_dd_limit_usd: number;
  daily_loss_limit_usd: number;
  profit_target_usd: number;
  trailing_drawdown_usd: number;
  trailing_drawdown_pct: number;
  remaining_cushion_usd: number;
  profit_target_progress_pct: number;
  status: string;
  last_sync_at: string | null;
  created_at: string | null;
}

interface ExecutionSession {
  session_id: string;
  route: string;
  environment: string;
  candidate_id: string;
  provider_id: string | null;
  symbol: string;
  status: string;
  current_pnl_usd: number;
  daily_pnl_usd: number;
  current_drawdown_pct: number;
  peak_equity_usd: number;
  heartbeat_last_at: string | null;
  last_signal: string;
  last_order: string;
  open_positions: any[];
  kill_switch_active: boolean;
  kill_switch_reason: string | null;
  created_at: string | null;
}

interface RemoteOrderHistoryItem {
  order_id: string;
  account_name: string;
  symbol: string;
  action: string;
  order_type: string;
  price: number | null;
  quantity: number;
  stop_loss_ticks: number | null;
  take_profit_ticks: number | null;
  strategy_source: string;
  status: string;
  timestamp_utc: string;
}

interface CMEInstrumentSpec {
  symbol: string;
  name: string;
  tickSize: number;
  pointValue: number;
  tickValueUsd: number;
  defaultQty: number;
  defaultSlTicks: number;
  defaultTpTicks: number;
  defaultBeTicks: number;
  color: string;
}

const CME_SPECS: Record<string, CMEInstrumentSpec> = {
  MNQ: {
    symbol: "MNQ",
    name: "Micro E-mini Nasdaq-100",
    tickSize: 0.25,
    pointValue: 2.0,
    tickValueUsd: 0.50,
    defaultQty: 2,
    defaultSlTicks: 40,
    defaultTpTicks: 100,
    defaultBeTicks: 60,
    color: "#38bdf8",
  },
  MES: {
    symbol: "MES",
    name: "Micro E-mini S&P 500",
    tickSize: 0.25,
    pointValue: 5.0,
    tickValueUsd: 1.25,
    defaultQty: 2,
    defaultSlTicks: 16,
    defaultTpTicks: 48,
    defaultBeTicks: 24,
    color: "#818cf8",
  },
  NQ: {
    symbol: "NQ",
    name: "E-mini Nasdaq-100",
    tickSize: 0.25,
    pointValue: 20.0,
    tickValueUsd: 5.00,
    defaultQty: 1,
    defaultSlTicks: 32,
    defaultTpTicks: 80,
    defaultBeTicks: 48,
    color: "#38bdf8",
  },
  ES: {
    symbol: "ES",
    name: "E-mini S&P 500",
    tickSize: 0.25,
    pointValue: 50.0,
    tickValueUsd: 12.50,
    defaultQty: 1,
    defaultSlTicks: 16,
    defaultTpTicks: 48,
    defaultBeTicks: 24,
    color: "#818cf8",
  },
  MGC: {
    symbol: "MGC",
    name: "Micro Gold Futures",
    tickSize: 0.10,
    pointValue: 10.0,
    tickValueUsd: 1.00,
    defaultQty: 2,
    defaultSlTicks: 20,
    defaultTpTicks: 60,
    defaultBeTicks: 30,
    color: "#eab308",
  },
  GC: {
    symbol: "GC",
    name: "Gold Futures",
    tickSize: 0.10,
    pointValue: 100.0,
    tickValueUsd: 10.00,
    defaultQty: 1,
    defaultSlTicks: 20,
    defaultTpTicks: 60,
    defaultBeTicks: 30,
    color: "#eab308",
  },
  MCL: {
    symbol: "MCL",
    name: "Micro Crude Oil",
    tickSize: 0.01,
    pointValue: 100.0,
    tickValueUsd: 1.00,
    defaultQty: 2,
    defaultSlTicks: 25,
    defaultTpTicks: 75,
    defaultBeTicks: 38,
    color: "#f59e0b",
  },
  "6E": {
    symbol: "6E",
    name: "Euro FX Futures",
    tickSize: 0.00005,
    pointValue: 125000.0,
    tickValueUsd: 6.25,
    defaultQty: 1,
    defaultSlTicks: 24,
    defaultTpTicks: 72,
    defaultBeTicks: 36,
    color: "#10b981",
  },
};

export default function RealExecutionPage() {
  const [accounts, setAccounts] = useState<NinjaTraderAccount[]>([]);
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [orderHistory, setOrderHistory] = useState<RemoteOrderHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // Remote Order Terminal State
  const [remoteAccount, setRemoteAccount] = useState<string>("Sim101");
  const [remoteSymbol, setRemoteSymbol] = useState<string>("MNQ");
  const [remoteQty, setRemoteQty] = useState<number>(2);
  const [sendingOrder, setSendingOrder] = useState<boolean>(false);

  // ATM Calculator State
  const [atmSymbol, setAtmSymbol] = useState<string>("MNQ");
  const [atmQty, setAtmQty] = useState<number>(2);
  const [atmSlTicks, setAtmSlTicks] = useState<number>(40);
  const [atmTpTicks, setAtmTpTicks] = useState<number>(100);
  const [atmDailyLossLimit, setAtmDailyLossLimit] = useState<number>(1000);

  // C# Code Viewer State
  const [exportedCode, setExportedCode] = useState<string | null>(null);
  const [exportedFilename, setExportedFilename] = useState<string>("");
  const [selectedCsSymbol, setSelectedCsSymbol] = useState<string>("MNQ");
  const [loadingCode, setLoadingCode] = useState<boolean>(false);
  const [copiedCode, setCopiedCode] = useState<boolean>(false);

  // Navigation tab
  const [activeTab, setActiveTab] = useState<"AUTO_CONNECT" | "REMOTE_TERMINAL" | "SESSIONS" | "CS_BOTS" | "ATM_BUILDER">("AUTO_CONNECT");

  const fetchRealData = useCallback(async () => {
    try {
      const [resAccs, resSessions, resOrders] = await Promise.all([
        fetch(getApiUrl("/api/v1/execution/ninjatrader/accounts")),
        fetch(getApiUrl("/api/v1/execution/sessions")),
        fetch(getApiUrl("/api/v1/execution/ninjatrader/orders/history")),
      ]);

      if (resAccs.ok) {
        const dataAccs = await resAccs.json();
        setAccounts(Array.isArray(dataAccs) ? dataAccs : []);
        if (dataAccs.length > 0 && remoteAccount === "Sim101") {
          setRemoteAccount(dataAccs[0].account_id);
        }
      }

      if (resSessions.ok) {
        const dataSessions = await resSessions.json();
        setSessions(Array.isArray(dataSessions) ? dataSessions : []);
      }

      if (resOrders.ok) {
        const dataOrders = await resOrders.json();
        setOrderHistory(Array.isArray(dataOrders) ? dataOrders : []);
      }

      setErrorMsg(null);
    } catch (err: any) {
      setErrorMsg(`Error conectando con la API Backend: ${err?.message}`);
    } finally {
      setLoading(false);
    }
  }, [remoteAccount]);

  useEffect(() => {
    fetchRealData();
  }, [fetchRealData]);

  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(fetchRealData, 2500);
    return () => clearInterval(timer);
  }, [autoRefresh, fetchRealData]);

  useEffect(() => {
    const spec = CME_SPECS[atmSymbol] || CME_SPECS.MNQ;
    setAtmQty(spec.defaultQty);
    setAtmSlTicks(spec.defaultSlTicks);
    setAtmTpTicks(spec.defaultTpTicks);
  }, [atmSymbol]);

  const handleDispatchRemoteOrder = async (action: "BUY" | "SELL" | "FLATTEN" | "KILL_SWITCH") => {
    setSendingOrder(true);
    try {
      const spec = CME_SPECS[remoteSymbol] || CME_SPECS.MNQ;
      const res = await fetch(getApiUrl("/api/v1/execution/ninjatrader/orders"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_name: remoteAccount,
          symbol: remoteSymbol,
          action,
          order_type: "MARKET",
          quantity: action === "FLATTEN" || action === "KILL_SWITCH" ? 0 : remoteQty,
          stop_loss_ticks: spec.defaultSlTicks,
          take_profit_ticks: spec.defaultTpTicks,
          strategy_source: "WEB_REMOTE_TERMINAL",
        }),
      });

      if (res.ok) {
        const result = await res.json();
        setActionLog(`⚡ ORDEN REMOTA ENVIADA A NINJATRADER 8: ${action} ${remoteQty} ${remoteSymbol} (${result.order_id}).`);
        fetchRealData();
      } else {
        setActionLog(`✕ Error enviando orden remota.`);
      }
    } catch (err: any) {
      setActionLog(`✕ Error de conexión: ${err.message}`);
    } finally {
      setSendingOrder(false);
    }
  };

  const handleKillSwitch = async (sessionId: string) => {
    const reason = prompt("Motivo del Kill-Switch de emergencia (Hard Stop):", "Manual Emergency DLL Guard");
    if (!reason) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/sessions/${sessionId}/kill-switch`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      if (res.ok) {
        setActionLog(`🚨 KILL-SWITCH ACTIVADO: ${sessionId} detenido inmediatamente.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error activando kill-switch: ${err.message}`);
    }
  };

  const handleFlatten = async (sessionId: string) => {
    if (!confirm(`¿Confirmas cerrar a mercado todas las posiciones abiertas de ${sessionId}?`)) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/sessions/${sessionId}/flatten`), {
        method: "POST",
      });
      if (res.ok) {
        setActionLog(`🛑 POSICIONES APLANADAS: ${sessionId} cerrado a mercado.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error al aplanar posiciones: ${err.message}`);
    }
  };

  const handlePauseResume = async (sessionId: string, currentStatus: string) => {
    const isPaused = currentStatus === "PAUSED";
    const endpoint = isPaused ? "resume" : "pause";
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/sessions/${sessionId}/${endpoint}`), {
        method: "POST",
      });
      if (res.ok) {
        setActionLog(`✓ Sesión ${sessionId} ${isPaused ? "REANUDADA" : "PAUSADA"}.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error modificando estado: ${err.message}`);
    }
  };

  const handleLoadCsBridge = async (symbol: string) => {
    setSelectedCsSymbol(symbol);
    setLoadingCode(true);
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/ninjatrader/bridge/script?symbol=${symbol}&account_id=${remoteAccount}`));
      if (res.ok) {
        const data = await res.json();
        setExportedCode(data.code);
        setExportedFilename(data.filename);
      } else {
        setExportedCode(`// Error generando código C# para ${symbol}`);
      }
    } catch (err: any) {
      setExportedCode(`// Error de conexión: ${err.message}`);
    } finally {
      setLoadingCode(false);
    }
  };

  const handleDownloadCsFile = () => {
    if (!exportedCode) return;
    const blob = new Blob([exportedCode], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = exportedFilename || `UR_Bridge_${selectedCsSymbol}.cs`;
    link.click();
    URL.revokeObjectURL(url);
    setActionLog(`✓ Archivo '${link.download}' descargado. Cópialo a Documents/NinjaTrader 8/bin/Custom/Strategies/ y presiona F5 en NinjaTrader.`);
  };

  const handleDeleteAccount = async (accId: string) => {
    if (!confirm(`¿Eliminar la cuenta ${accId} de SQLite?`)) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/ninjatrader/accounts/${encodeURIComponent(accId)}`), {
        method: "DELETE",
      });
      if (res.ok) {
        setActionLog(`✓ Cuenta ${accId} eliminada.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error al eliminar: ${err.message}`);
    }
  };

  // ATM calculations
  const spec = CME_SPECS[atmSymbol] || CME_SPECS.MNQ;
  const slPoints = atmSlTicks * spec.tickSize;
  const tpPoints = atmTpTicks * spec.tickSize;
  const slUsdPerContract = atmSlTicks * spec.tickValueUsd;
  const tpUsdPerContract = atmTpTicks * spec.tickValueUsd;
  const totalRiskUsd = slUsdPerContract * atmQty;
  const totalRewardUsd = tpUsdPerContract * atmQty;
  const rrRatio = slUsdPerContract > 0 ? tpUsdPerContract / slUsdPerContract : 0;
  const beTriggerTicks = Math.round(atmSlTicks * 1.5);
  const beTriggerPoints = beTriggerTicks * spec.tickSize;
  const maxTradesBeforeDll = totalRiskUsd > 0 ? Math.floor(atmDailyLossLimit / totalRiskUsd) : 0;

  return (
    <div className="space-y-4 font-sans max-w-[1600px] mx-auto">
      {/* 1. TOP TELEMETRY BAR & HEADER */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
            <Terminal className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Trading Remoto NinjaTrader 8 & Auto-Connect
              </h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                PORT 8000 LIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Telemetría bidireccional en tiempo real · Despacho de órdenes de mercado y control de riesgo CME
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto font-mono">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-1.5 transition cursor-pointer ${
              autoRefresh
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                : "bg-slate-800 text-slate-400 border-white/[0.08]"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${autoRefresh ? "bg-emerald-400 animate-ping" : "bg-slate-500"}`} />
            <span>{autoRefresh ? "RADAR 2.5s" : "PAUSADO"}</span>
          </button>

          <button
            onClick={fetchRealData}
            className="p-2 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.1] transition cursor-pointer"
            title="Refrescar datos"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* ACTION LOG & ERRORS */}
      {actionLog && (
        <div className="p-3.5 bg-sky-950/80 border border-sky-500/60 rounded-xl text-xs font-mono text-sky-200 flex items-center justify-between shadow-lg">
          <span>{actionLog}</span>
          <button onClick={() => setActionLog(null)} className="text-slate-400 hover:text-white cursor-pointer">✕</button>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 bg-rose-950/80 border border-rose-500/60 rounded-xl text-xs font-mono text-rose-200 flex items-center justify-between shadow-lg">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-slate-400 hover:text-white cursor-pointer">✕</button>
        </div>
      )}

      {/* 2. NAVIGATION TABS */}
      <div className="flex items-center gap-1.5 overflow-x-auto p-1.5 rounded-2xl border border-white/[0.08] bg-[#090d16]/90 backdrop-blur-xl shadow-lg font-mono">
        <button
          onClick={() => setActiveTab("AUTO_CONNECT")}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "AUTO_CONNECT"
              ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
          }`}
        >
          <Radio className="w-3.5 h-3.5 text-emerald-400" />
          <span>Auto-Conexión & Cuentas ({accounts.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("REMOTE_TERMINAL")}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "REMOTE_TERMINAL"
              ? "bg-sky-500/15 text-sky-300 border border-sky-500/40 shadow-[0_0_15px_rgba(56,189,248,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
          }`}
        >
          <Send className="w-3.5 h-3.5 text-sky-400" />
          <span>Terminal Remoto</span>
        </button>

        <button
          onClick={() => setActiveTab("SESSIONS")}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "SESSIONS"
              ? "bg-purple-500/15 text-purple-300 border border-purple-500/40 shadow-[0_0_15px_rgba(168,85,247,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
          }`}
        >
          <Layers className="w-3.5 h-3.5 text-purple-400" />
          <span>Sesiones de Ejecución ({sessions.length})</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("CS_BOTS");
            if (!exportedCode) handleLoadCsBridge("MNQ");
          }}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "CS_BOTS"
              ? "bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
          }`}
        >
          <FileCode className="w-3.5 h-3.5 text-cyan-400" />
          <span>NinjaScript C# (.cs)</span>
        </button>

        <button
          onClick={() => setActiveTab("ATM_BUILDER")}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
            activeTab === "ATM_BUILDER"
              ? "bg-amber-500/15 text-amber-300 border border-amber-500/40 shadow-[0_0_15px_rgba(245,158,11,0.15)]"
              : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
          }`}
        >
          <Calculator className="w-3.5 h-3.5 text-amber-400" />
          <span>Calculadora ATM & Riesgo</span>
        </button>
      </div>

      {/* TAB 1: AUTO-CONNECT RADAR & REAL ACCOUNTS */}
      {activeTab === "AUTO_CONNECT" && (
        <div className="space-y-4">
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-emerald-500/30 rounded-2xl p-6 shadow-xl flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  Radar de Auto-Descubrimiento en Tiempo Real Activo
                </h2>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  PUERTO 8000
                </span>
              </div>
              <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
                Zero formularios manuales. Descarga el script C#, cópialo a NinjaTrader 8 y activa la estrategia en tu gráfico. En cuanto NinjaTrader transmita, Ultrarentable detectará tu cuenta (Sim101, Apex, Topstep, Tradovate) y leerá su balance real de forma inmutable.
              </p>
            </div>

            <button
              onClick={() => {
                if (!exportedCode) handleLoadCsBridge("MNQ");
                setActiveTab("CS_BOTS");
              }}
              className="px-5 py-3 rounded-xl font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/40 transition cursor-pointer text-xs font-mono whitespace-nowrap active:scale-95"
            >
              ⬇️ DESCARGAR CONECTOR NINJASCRIPT C#
            </button>
          </div>

          {/* ACCOUNTS GRID */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <Server className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Cuentas NinjaTrader 8 Conectadas en Vivo ({accounts.length})
                </h3>
              </div>
              <span className="text-xs font-mono text-slate-400">Zero-Mocks Certified</span>
            </div>

            {loading ? (
              <div className="p-12 text-center text-xs font-mono text-slate-400">
                Sincronizando cuentas con SQLite...
              </div>
            ) : accounts.length === 0 ? (
              <div className="p-12 text-center border border-dashed border-white/[0.1] rounded-2xl bg-[#050811]/60 space-y-3 font-mono">
                <CheckCircle2 className="w-8 h-8 text-slate-600 mx-auto" />
                <div className="text-sm font-bold text-slate-200">
                  ESPERANDO PRIMERA CONEXIÓN DESDE NINJATRADER 8
                </div>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  En cuanto inicies NinjaTrader 8 y habilites la estrategia C#, tu cuenta aparecerá aquí automáticamente con su saldo real y métricas en vivo.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
                {accounts.map((acc) => (
                  <div
                    key={acc.account_id}
                    className="p-5 bg-[#050811] rounded-2xl border border-white/[0.08] space-y-4 shadow-lg flex flex-col justify-between"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white">{acc.account_id}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            {acc.account_type}
                          </span>
                          <span className="text-[10px] text-slate-400">{acc.broker}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 mt-1">
                          {acc.account_name} · Sinc: {acc.last_sync_at ? new Date(acc.last_sync_at).toLocaleTimeString() : "Ahora"}
                        </div>
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        {acc.status}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2 p-3 bg-[#090d16] rounded-xl border border-white/[0.06]">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">Equidad</span>
                        <span className="text-sm font-bold text-white tabular-nums">
                          ${acc.current_equity_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">PnL Hoy</span>
                        <span className={`text-sm font-bold tabular-nums ${acc.daily_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                          ${acc.daily_pnl_usd.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase block">Colchón DD</span>
                        <span className="text-sm font-bold text-emerald-400 tabular-nums">
                          ${acc.remaining_cushion_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-2 border-t border-white/[0.08]">
                      <button
                        onClick={() => {
                          setRemoteAccount(acc.account_id);
                          setActiveTab("REMOTE_TERMINAL");
                        }}
                        className="flex-1 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition cursor-pointer"
                      >
                        Operar en Remoto
                      </button>
                      <button
                        onClick={() => handleDeleteAccount(acc.account_id)}
                        className="p-2 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 transition cursor-pointer"
                        title="Desconectar cuenta"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: REMOTE TRADING TERMINAL */}
      {activeTab === "REMOTE_TERMINAL" && (
        <div className="space-y-4">
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 shadow-xl space-y-5 font-mono text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-4">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">
                  Consola de Trading Remoto NinjaTrader 8
                </h2>
                <p className="text-xs text-slate-400 font-sans mt-0.5">
                  Despacha órdenes de mercado y paradas de emergencia en tiempo real
                </p>
              </div>
              <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-1 rounded-xl border border-emerald-700/60 self-start sm:self-auto">
                Webhook & Bridge Activo
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Cuenta Objetivo</label>
                <select
                  value={remoteAccount}
                  onChange={(e) => setRemoteAccount(e.target.value)}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
                >
                  {accounts.length === 0 ? (
                    <option value="Sim101">Sim101 (Local Demo)</option>
                  ) : (
                    accounts.map((a) => (
                      <option key={a.account_id} value={a.account_id}>
                        {a.account_id} ({a.account_type})
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Instrumento CME</label>
                <select
                  value={remoteSymbol}
                  onChange={(e) => setRemoteSymbol(e.target.value)}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
                >
                  {Object.keys(CME_SPECS).map((k) => (
                    <option key={k} value={k}>
                      {k} — {CME_SPECS[k].name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Contratos</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={remoteQty}
                  onChange={(e) => setRemoteQty(Number(e.target.value))}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
              <button
                onClick={() => handleDispatchRemoteOrder("BUY")}
                disabled={sendingOrder}
                className="py-3.5 rounded-xl font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/40 transition cursor-pointer active:scale-95"
              >
                COMPRAR {remoteQty}x {remoteSymbol}
              </button>

              <button
                onClick={() => handleDispatchRemoteOrder("SELL")}
                disabled={sendingOrder}
                className="py-3.5 rounded-xl font-black bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/40 transition cursor-pointer active:scale-95"
              >
                VENDER {remoteQty}x {remoteSymbol}
              </button>

              <button
                onClick={() => handleDispatchRemoteOrder("FLATTEN")}
                disabled={sendingOrder}
                className="py-3.5 rounded-xl font-bold bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 transition cursor-pointer active:scale-95"
              >
                FLATTEN {remoteSymbol}
              </button>

              <button
                onClick={() => handleDispatchRemoteOrder("KILL_SWITCH")}
                disabled={sendingOrder}
                className="py-3.5 rounded-xl font-bold bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 transition cursor-pointer active:scale-95"
              >
                KILL-SWITCH REMOTO
              </button>
            </div>
          </div>

          {/* RECENT ORDERS TABLE */}
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <h3 className="text-base font-bold text-white">
                Historial de Órdenes Remotas ({orderHistory.length})
              </h3>
              <span className="text-slate-400 text-[11px]">Sincronización Inmutable</span>
            </div>

            {orderHistory.length === 0 ? (
              <div className="p-8 text-center border border-dashed border-white/[0.1] rounded-xl bg-[#050811]/40 text-slate-500">
                No hay órdenes remotas despachadas en esta sesión.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.08] text-slate-400 uppercase text-[10px] bg-[#050811]">
                      <th className="py-2.5 px-3">ID Orden</th>
                      <th className="py-2.5 px-3">Acción</th>
                      <th className="py-2.5 px-3">Símbolo</th>
                      <th className="py-2.5 px-3">Cant.</th>
                      <th className="py-2.5 px-3">Cuenta</th>
                      <th className="py-2.5 px-3">Estado</th>
                      <th className="py-2.5 px-3">Hora UTC</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.05] text-[11px]">
                    {orderHistory.map((ord) => (
                      <tr key={ord.order_id} className="hover:bg-white/[0.03] transition-colors">
                        <td className="py-2.5 px-3 text-sky-400 font-bold">{ord.order_id}</td>
                        <td className="py-2.5 px-3 font-bold">
                          <span className={ord.action === "BUY" ? "text-emerald-400" : "text-rose-400"}>
                            {ord.action}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-white">{ord.symbol}</td>
                        <td className="py-2.5 px-3 text-slate-300">{ord.quantity}x</td>
                        <td className="py-2.5 px-3 text-slate-400">{ord.account_name}</td>
                        <td className="py-2.5 px-3">
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px]">
                            {ord.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">{new Date(ord.timestamp_utc).toLocaleTimeString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 3: SESSIONS */}
      {activeTab === "SESSIONS" && (
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <h2 className="text-base font-bold text-white">Sesiones de Ejecución Activas ({sessions.length})</h2>
            <span className="text-slate-400 text-[11px]">SQLite Real Telemetry</span>
          </div>

          {sessions.length === 0 ? (
            <div className="p-12 text-center border border-dashed border-white/[0.1] rounded-2xl bg-[#050811]/60 text-slate-400 space-y-2">
              <ShieldAlert className="w-8 h-8 text-slate-600 mx-auto" />
              <div className="font-bold text-slate-300">CERO SESIONES DE EJECUCIÓN ACTIVAS</div>
              <p className="text-xs text-slate-500 font-sans">
                En cuanto NinjaTrader 8 transmita una orden real a través del Webhook, aparecerá la sesión de trading aquí automáticamente.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sessions.map((s) => (
                <div key={s.session_id} className="p-4 bg-[#050811] rounded-xl border border-white/[0.08] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-sm">{s.session_id}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-bold">
                      {s.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 p-2.5 bg-[#090d16] rounded-lg border border-white/[0.06]">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">PnL</span>
                      <span className={`font-bold tabular-nums ${s.daily_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        ${s.daily_pnl_usd.toFixed(2)}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">Peak Equity</span>
                      <span className="font-bold text-white tabular-nums">${s.peak_equity_usd?.toFixed(0)}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase block">Drawdown</span>
                      <span className="font-bold text-amber-400 tabular-nums">{s.current_drawdown_pct.toFixed(2)}%</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-white/[0.08]">
                    <button
                      onClick={() => handlePauseResume(s.session_id, s.status)}
                      className="flex-1 py-1.5 rounded-lg bg-[#090d16] hover:bg-slate-800 text-slate-200 border border-white/[0.08] font-bold text-xs"
                    >
                      {s.status === "PAUSED" ? "Reanudar" : "Pausar"}
                    </button>
                    <button
                      onClick={() => handleFlatten(s.session_id)}
                      className="flex-1 py-1.5 rounded-lg bg-amber-600/20 text-amber-400 border border-amber-500/30 font-bold text-xs"
                    >
                      Flatten
                    </button>
                    <button
                      onClick={() => handleKillSwitch(s.session_id)}
                      className="flex-1 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs"
                    >
                      Kill-Switch
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: C# STRATEGY EXPORTER */}
      {activeTab === "CS_BOTS" && (
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 shadow-xl space-y-4 font-mono text-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
            <div>
              <h2 className="text-base font-bold text-white">Generador y Descargador NinjaScript C#</h2>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Código C# nativo compilable para NinjaTrader 8 con puente HTTP bidireccional y guardas duras
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleDownloadCsFile}
                disabled={!exportedCode || loadingCode}
                className="px-4 py-2 rounded-xl font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 cursor-pointer shadow-lg shadow-emerald-900/30"
              >
                <Download className="w-3.5 h-3.5" />
                Descargar .cs
              </button>
              {exportedCode && (
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(exportedCode);
                    setCopiedCode(true);
                    setTimeout(() => setCopiedCode(false), 2000);
                  }}
                  className="px-4 py-2 rounded-xl font-bold bg-sky-600 hover:bg-sky-500 text-white transition flex items-center gap-1.5 cursor-pointer shadow-lg shadow-sky-900/30"
                >
                  {copiedCode ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  {copiedCode ? "Copiado" : "Copiar"}
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <span className="text-[10px] text-slate-400 uppercase font-bold block">Seleccionar Activo</span>
              {Object.keys(CME_SPECS).map((sym) => (
                <button
                  key={sym}
                  onClick={() => handleLoadCsBridge(sym)}
                  className={`w-full p-2.5 rounded-xl border text-left transition cursor-pointer ${
                    selectedCsSymbol === sym
                      ? "bg-[#050811] border-cyan-500 ring-1 ring-cyan-500/30 text-white font-bold"
                      : "bg-[#050811] border-white/[0.08] text-slate-400 hover:text-white"
                  }`}
                >
                  <div>{sym} — {CME_SPECS[sym].name}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">
                    SL: {CME_SPECS[sym].defaultSlTicks}T · TP: {CME_SPECS[sym].defaultTpTicks}T
                  </div>
                </button>
              ))}
            </div>

            <div className="lg:col-span-3">
              <pre className="p-4 bg-[#04070c] border border-white/[0.08] rounded-xl text-[11px] text-cyan-300 font-mono h-96 overflow-y-auto">
                {loadingCode ? "// Generando código C#..." : exportedCode || "// Selecciona un activo a la izquierda."}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: ATM CALCULATOR */}
      {activeTab === "ATM_BUILDER" && (
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 shadow-xl space-y-4 font-mono text-xs">
          <div className="border-b border-white/[0.08] pb-3">
            <h2 className="text-base font-bold text-white">Calculadora Matemática de Parámetros ATM CME</h2>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Cálculo determinista de riesgo, múltiplos R y disparadores de Break-Even
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Instrumento</label>
              <select
                value={atmSymbol}
                onChange={(e) => setAtmSymbol(e.target.value)}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2 text-white font-bold"
              >
                {Object.keys(CME_SPECS).map((k) => (
                  <option key={k} value={k}>{k} — {CME_SPECS[k].name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Contratos</label>
              <input
                type="number"
                min="1"
                max="20"
                value={atmQty}
                onChange={(e) => setAtmQty(Number(e.target.value))}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2 text-white font-bold"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">SL Ticks</label>
              <input
                type="number"
                value={atmSlTicks}
                onChange={(e) => setAtmSlTicks(Number(e.target.value))}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2 text-rose-400 font-bold"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">TP Ticks</label>
              <input
                type="number"
                value={atmTpTicks}
                onChange={(e) => setAtmTpTicks(Number(e.target.value))}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2 text-emerald-400 font-bold"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Límite Diario ($)</label>
              <input
                type="number"
                value={atmDailyLossLimit}
                onChange={(e) => setAtmDailyLossLimit(Number(e.target.value))}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2 text-amber-400 font-bold"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
            <div className="p-4 bg-[#050811] rounded-xl border border-rose-500/30 space-y-1">
              <span className="text-[10px] text-rose-400 uppercase font-bold">Riesgo Stop Loss</span>
              <div className="text-xl font-bold text-rose-400 tabular-nums">${totalRiskUsd.toFixed(2)} USD</div>
              <div className="text-[10px] text-slate-400">{atmSlTicks} ticks = {slPoints.toFixed(2)} pts</div>
            </div>

            <div className="p-4 bg-[#050811] rounded-xl border border-emerald-500/30 space-y-1">
              <span className="text-[10px] text-emerald-400 uppercase font-bold">Beneficio Take Profit</span>
              <div className="text-xl font-bold text-emerald-400 tabular-nums">+${totalRewardUsd.toFixed(2)} USD</div>
              <div className="text-[10px] text-slate-400">{atmTpTicks} ticks = {tpPoints.toFixed(2)} pts (1:{rrRatio.toFixed(1)} R)</div>
            </div>

            <div className="p-4 bg-[#050811] rounded-xl border border-sky-500/30 space-y-1">
              <span className="text-[10px] text-sky-400 uppercase font-bold">Trigger Break-Even (+1.5R)</span>
              <div className="text-xl font-bold text-sky-400 tabular-nums">+{beTriggerTicks} Ticks</div>
              <div className="text-[10px] text-slate-400">+{beTriggerPoints.toFixed(2)} pts</div>
            </div>

            <div className="p-4 bg-[#050811] rounded-xl border border-amber-500/30 space-y-1">
              <span className="text-[10px] text-amber-400 uppercase font-bold">Stops Máximos / Día</span>
              <div className="text-xl font-bold text-amber-400 tabular-nums">{maxTradesBeforeDll} Stops</div>
              <div className="text-[10px] text-slate-400">Antes del DLL (${atmDailyLossLimit})</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
