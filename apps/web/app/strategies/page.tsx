"use client";

import React, { useState, useEffect } from "react";
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
  Layers,
  Database,
  Activity,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Hash,
} from "lucide-react";
import { executeBacktest, getCandidates, CandidateStrategy, BacktestResult } from "@/lib/api";

export default function StrategiesPage() {
  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<CandidateStrategy | null>(null);
  const [loadingCandidates, setLoadingCandidates] = useState<boolean>(true);
  const [runningBacktest, setRunningBacktest] = useState<boolean>(false);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [symbol, setSymbol] = useState<string>("BTC");
  const [timeframe, setTimeframe] = useState<string>("1h");
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [slippageTicks, setSlippageTicks] = useState<number>(1);

  useEffect(() => {
    loadCandidates();
  }, []);

  async function loadCandidates() {
    setLoadingCandidates(true);
    setErrorMsg(null);
    try {
      const data = await getCandidates({ limit: 50 });
      setCandidates(data);
      if (data.length > 0 && !selectedStrategy) {
        setSelectedStrategy(data[0]);
        setSymbol(data[0].symbol);
        setTimeframe(data[0].timeframe);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar candidatos de estrategias.";
      setErrorMsg(msg);
    } finally {
      setLoadingCandidates(false);
    }
  }

  async function handleRunBacktest() {
    if (!selectedStrategy) return;

    setRunningBacktest(true);
    setErrorMsg(null);
    setBacktestResult(null);

    try {
      // LLAMADA REAL A FASTENGINE BACKTEST SERVICE (ZERO MOCKS, ZERO SETTIMEOUT)
      const result = await executeBacktest({
        strategy_id: selectedStrategy.id,
        symbol: symbol,
        timeframe: timeframe,
        initial_capital: initialCapital,
        slippage_ticks: slippageTicks,
      });

      setBacktestResult(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Fallo en la ejecución física del backtest.";
      setErrorMsg(msg);
    } finally {
      setRunningBacktest(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Cpu className="w-7 h-7 text-indigo-400" />
              <h1 className="text-2xl font-bold tracking-tight">UltraRentable — Motor de Estrategias & Backtest Físico</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Catálogo canónico de estrategias y ejecutor FastEngine determinista. Trazabilidad trade-a-trade con hashes Merkle.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-300 border border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              v5.3.0 Provenance Locked
            </span>
            <button
              onClick={loadCandidates}
              disabled={loadingCandidates}
              className="inline-flex items-center px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loadingCandidates ? "animate-spin" : ""}`} />
              Refrescar Catálogo
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-200 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">Error de Comunicación / Ejecución:</p>
              <p className="text-xs text-rose-300 mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Candidates Catalog */}
          <div className="lg:col-span-1 bg-slate-900/80 rounded-xl border border-slate-800 p-4 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                Candidatos Disponibles ({candidates.length})
              </h2>
            </div>

            {loadingCandidates ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-indigo-500" />
                Cargando estrategias físicas desde SQLite...
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {candidates.map((c) => {
                  const isSelected = selectedStrategy?.id === c.id;
                  return (
                    <button
                      key={c.id}
                      onClick={() => {
                        setSelectedStrategy(c);
                        setSymbol(c.symbol);
                        setTimeframe(c.timeframe);
                      }}
                      className={`w-full text-left p-3 rounded-lg border transition ${
                        isSelected
                          ? "bg-indigo-950/60 border-indigo-500/80 text-white shadow-sm"
                          : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-indigo-300 truncate">{c.name || c.id}</span>
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          {c.symbol} · {c.timeframe}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                        <div>
                          <span className="text-slate-500 block">PF Total</span>
                          <span className="font-semibold text-emerald-400">
                            {c.profit_factor ? c.profit_factor.toFixed(2) : "N/A"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Sharpe</span>
                          <span className="font-semibold text-slate-200">
                            {c.sharpe_ratio ? c.sharpe_ratio.toFixed(2) : "N/A"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Max DD</span>
                          <span className="font-semibold text-rose-400">
                            {c.max_drawdown_pct ? `${c.max_drawdown_pct.toFixed(1)}%` : "N/A"}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Execution Form & Backtest Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Strategy Parameter Execution Card */}
            <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <h3 className="font-bold text-slate-200 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    Ejecutor FastEngine (Real-Only Backtest)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Estrategia seleccionada: <span className="text-indigo-300 font-mono">{selectedStrategy?.id || "Ninguna"}</span>
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Activo</label>
                  <input
                    type="text"
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Temporalidad</label>
                  <select
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                  >
                    <option value="1m">1m</option>
                    <option value="5m">5m</option>
                    <option value="15m">15m</option>
                    <option value="1h">1h</option>
                    <option value="4h">4h</option>
                    <option value="1d">1d</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Capital Inicial ($)</label>
                  <input
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Slippage (ticks)</label>
                  <input
                    type="number"
                    value={slippageTicks}
                    onChange={(e) => setSlippageTicks(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md px-3 py-1.5 text-xs text-slate-100 font-mono focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  id="btn-execute-backtest"
                  onClick={handleRunBacktest}
                  disabled={runningBacktest || !selectedStrategy}
                  className="inline-flex items-center px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white shadow transition"
                >
                  {runningBacktest ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Procesando Backtest Físico...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Ejecutar Backtest Real
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Backtest Results Card */}
            {backtestResult && (
              <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <h3 className="font-bold text-slate-100 text-sm">
                      Resultado Físico Certificado (Run ID: <span className="font-mono text-indigo-300">{backtestResult.run_id}</span>)
                    </h3>
                  </div>
                  <span className="text-xs text-slate-400 font-mono">
                    Tiempo de cálculo: {backtestResult.execution_time_ms} ms
                  </span>
                </div>

                {/* KPI Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-xs text-slate-400 block">Profit Factor</span>
                    <span className="text-lg font-bold text-emerald-400">
                      {backtestResult.profit_factor ? backtestResult.profit_factor.toFixed(2) : "0.00"}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-xs text-slate-400 block">Sharpe Ratio</span>
                    <span className="text-lg font-bold text-indigo-300">
                      {backtestResult.sharpe_ratio ? backtestResult.sharpe_ratio.toFixed(2) : "0.00"}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-xs text-slate-400 block">Max Drawdown</span>
                    <span className="text-lg font-bold text-rose-400">
                      {backtestResult.max_drawdown_pct ? `${backtestResult.max_drawdown_pct.toFixed(2)}%` : "0.00%"}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-xs text-slate-400 block">Win Rate</span>
                    <span className="text-lg font-bold text-slate-100">
                      {backtestResult.win_rate_pct ? `${backtestResult.win_rate_pct.toFixed(1)}%` : "0.0%"}
                    </span>
                  </div>
                </div>

                {/* Additional Metrics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="p-2.5 bg-slate-950/40 rounded border border-slate-800/60">
                    <span className="text-slate-500 block">Total Operaciones</span>
                    <span className="font-semibold text-slate-200">{backtestResult.total_trades}</span>
                  </div>
                  <div className="p-2.5 bg-slate-950/40 rounded border border-slate-800/60">
                    <span className="text-slate-500 block">Net PnL</span>
                    <span className={`font-semibold ${backtestResult.total_net_pnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      ${backtestResult.total_net_pnl?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-950/40 rounded border border-slate-800/60">
                    <span className="text-slate-500 block">Duración OOS (Meses)</span>
                    <span className="font-semibold text-slate-200 font-mono">
                      {backtestResult.oos_months !== null && backtestResult.oos_months !== undefined
                        ? `${backtestResult.oos_months.toFixed(2)} m`
                        : "N/A"}
                    </span>
                  </div>
                  <div className="p-2.5 bg-slate-950/40 rounded border border-slate-800/60">
                    <span className="text-slate-500 block">CAGR Anual</span>
                    <span className="font-semibold text-slate-200 font-mono">
                      {backtestResult.cagr !== null && backtestResult.cagr !== undefined
                        ? `${(backtestResult.cagr * 100).toFixed(2)}%`
                        : "N/A"}
                    </span>
                  </div>
                </div>

                {/* Cryptographic Hashes Provenance */}
                <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800 space-y-1.5">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-indigo-400" />
                    Sellado Criptográfico Merkle (ZERO MOCKS)
                  </span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                    <div className="truncate">
                      <span className="text-slate-500">Strategy Hash: </span>
                      <span className="text-slate-300">{backtestResult.strategy_hash || "N/A"}</span>
                    </div>
                    <div className="truncate">
                      <span className="text-slate-500">Ledger Hash: </span>
                      <span className="text-indigo-300">{backtestResult.ledger_hash || "N/A"}</span>
                    </div>
                    <div className="truncate">
                      <span className="text-slate-500">Dataset Hash: </span>
                      <span className="text-slate-300">{backtestResult.dataset_hash || "N/A"}</span>
                    </div>
                    <div className="truncate">
                      <span className="text-slate-500">Evidence Hash: </span>
                      <span className="text-slate-300">{backtestResult.evidence_bundle_hash || "N/A"}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
