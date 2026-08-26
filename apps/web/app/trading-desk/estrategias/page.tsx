"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Bot,
  Activity,
  Play,
  Pause,
  AlertOctagon,
  ShieldCheck,
  Zap,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  DollarSign,
  BarChart3,
  Layers,
  FileText,
  AlertTriangle,
  Waves,
  Award,
} from "lucide-react";

interface StrategyNode {
  id: string;
  name: string;
  symbol: string;
  contractName: string;
  timeframe: string;
  sessionWindow: string;
  dispatchState: "DESPACHANDO" | "STANDBY" | "PAUSADA";
  regime: string;
  risk1RUsd: number;
  sharpeRatio: number;
  sortinoRatio: number;
  profitFactorOos: number;
  maxDrawdownPct: number;
  winRatePct: number;
  openPositionsCount: number;
  floatingPnlUsd: number;
  lastExecutionReason: string;
}

const DEFAULT_STRATEGIES: StrategyNode[] = [
  {
    id: "CME_NQ_ORB_V2",
    name: "CME Nasdaq ORB Breakout",
    symbol: "MNQ",
    contractName: "Micro E-mini Nasdaq-100",
    timeframe: "5m / 15m",
    sessionWindow: "09:30 - 11:30 EST (Opening Range)",
    dispatchState: "DESPACHANDO",
    regime: "Expansión RTH (Alta Volatilidad)",
    risk1RUsd: 30.0,
    sharpeRatio: 2.45,
    sortinoRatio: 3.82,
    profitFactorOos: 1.88,
    maxDrawdownPct: 2.8,
    winRatePct: 58.4,
    openPositionsCount: 0,
    floatingPnlUsd: 0.0,
    lastExecutionReason: "Breakout de Rango 15m confirmado con Delta positivo.",
  },
  {
    id: "ES_VWAP_INST_002",
    name: "ES VWAP Institutional Trend",
    symbol: "MES",
    contractName: "Micro E-mini S&P 500",
    timeframe: "15m",
    sessionWindow: "09:30 - 16:00 EST (Trend Follow)",
    dispatchState: "DESPACHANDO",
    regime: "Tendencia Institucional (VWAP Slope)",
    risk1RUsd: 25.0,
    sharpeRatio: 2.18,
    sortinoRatio: 3.24,
    profitFactorOos: 1.64,
    maxDrawdownPct: 2.3,
    winRatePct: 62.1,
    openPositionsCount: 0,
    floatingPnlUsd: 0.0,
    lastExecutionReason: "Pullback al VWAP Diario con absorción institucional.",
  },
  {
    id: "MGC_LDN_REV_003",
    name: "Gold London Mean Reversion",
    symbol: "MGC",
    contractName: "Micro Gold Futures",
    timeframe: "5m",
    sessionWindow: "03:00 - 07:00 EST (London Fix)",
    dispatchState: "STANDBY",
    regime: "Reversión a la Media (Rango Londres)",
    risk1RUsd: 20.0,
    sharpeRatio: 1.95,
    sortinoRatio: 2.88,
    profitFactorOos: 1.52,
    maxDrawdownPct: 3.1,
    winRatePct: 55.7,
    openPositionsCount: 0,
    floatingPnlUsd: 0.0,
    lastExecutionReason: "Contracción de bandas y divergencia RSI en sesión Londres.",
  },
];

export default function EstrategiasExecutionPage() {
  const [strategies, setStrategies] = useState<StrategyNode[]>(DEFAULT_STRATEGIES);
  const [selectedStratId, setSelectedStratId] = useState<string>("CME_NQ_ORB_V2");

  const toggleState = (id: string) => {
    setStrategies((prev) =>
      prev.map((s) => {
        if (s.id === id) {
          const next = s.dispatchState === "PAUSADA" ? "DESPACHANDO" : "PAUSADA";
          return { ...s, dispatchState: next };
        }
        return s;
      })
    );
  };

  const selectedStrat = strategies.find((s) => s.id === selectedStratId) || strategies[0];

  return (
    <div className="space-y-4 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl text-purple-400">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white">Estrategias Cuantitativas en Ejecución</h1>
            <p className="text-xs text-slate-400 font-mono">11 Quality Gates Aprobados · Despacho en tiempo real a Tradovate Demo</p>
          </div>
        </div>
        <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-bold">
          3 BOTS VIVOS
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-5 space-y-3">
          {strategies.map((s) => (
            <div
              key={s.id}
              onClick={() => setSelectedStratId(s.id)}
              className={`p-4 rounded-xl border transition cursor-pointer ${
                selectedStratId === s.id
                  ? "bg-slate-900 border-purple-500 shadow-lg shadow-purple-950/30"
                  : "bg-slate-900/60 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-white font-mono">{s.symbol} · {s.name}</span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded font-mono ${
                    s.dispatchState === "DESPACHANDO" ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"
                  }`}
                >
                  {s.dispatchState}
                </span>
              </div>
              <div className="text-xs text-slate-400 font-mono flex justify-between">
                <span>Régimen: {s.regime}</span>
                <span className="text-amber-400 font-bold">1R: ${s.risk1RUsd}</span>
              </div>
            </div>
          ))}
        </div>

        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-base font-bold text-white">{selectedStrat.name} ({selectedStrat.symbol})</h3>
            <button
              onClick={() => toggleState(selectedStrat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition flex items-center gap-1.5 ${
                selectedStrat.dispatchState === "PAUSADA"
                  ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                  : "bg-amber-600 hover:bg-amber-500 text-white"
              }`}
            >
              {selectedStrat.dispatchState === "PAUSADA" ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
              {selectedStrat.dispatchState === "PAUSADA" ? "REANUDAR" : "PAUSAR BOT"}
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase">Sharpe Ratio</div>
              <div className="text-base font-bold text-emerald-400 mt-0.5">{selectedStrat.sharpeRatio}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase">Profit Factor OOS</div>
              <div className="text-base font-bold text-white mt-0.5">{selectedStrat.profitFactorOos}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase">Win Rate</div>
              <div className="text-base font-bold text-blue-400 mt-0.5">{selectedStrat.winRatePct}%</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase">Max Drawdown</div>
              <div className="text-base font-bold text-rose-400 mt-0.5">-{selectedStrat.maxDrawdownPct}%</div>
            </div>
          </div>

          <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-1 font-mono text-xs text-slate-300">
            <span className="text-slate-500 font-bold uppercase text-[10px]">Última Decisión de Microestructura:</span>
            <p>{selectedStrat.lastExecutionReason}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
