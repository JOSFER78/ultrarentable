"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Activity,
  Zap,
  Play,
  Database,
  Layers,
  FileText,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sliders,
  ShieldCheck,
  Hash,
} from "lucide-react";

interface ApprovedDataset {
  datasetId: string;
  symbol: string;
  interval: string;
  recordCount: number;
  status: string;
}

interface Strategy {
  strategyId: string;
  name: string;
}

interface BacktestResult {
  backtestId: string;
  strategyId: string;
  datasetId: string;
  engineType: string;
  initialCapital: number;
  leverage: number;
  finalEquity: number;
  netReturnPct: number;
  maxDrawdownPct: number;
  winRate: number;
  tradesCount: number;
  profitFactor: number;
  checksum: string;
  status: string;
  createdAt: string;
}

export default function BacktestConsolePage() {
  const [datasets, setDatasets] = useState<ApprovedDataset[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);

  const [selectedDataset, setSelectedDataset] = useState("");
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [capital, setCapital] = useState(10000);
  const [leverage, setLeverage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [activeLedger, setActiveLedger] = useState<any[] | null>(null);
  const [activeBacktestId, setActiveBacktestId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadOptions = async () => {
    try {
      const [allDs, allStrat, allBt] = await Promise.all([
        api.getDatasets(),
        api.getStrategies(),
        api.getBacktests(),
      ]);
      const approvedOnly = allDs.filter((d: any) => d.status === "APPROVED");
      setDatasets(approvedOnly);
      setStrategies(allStrat);
      setBacktests(allBt);

      if (approvedOnly.length > 0 && !selectedDataset) setSelectedDataset(approvedOnly[0].datasetId);
      if (allStrat.length > 0 && !selectedStrategy) setSelectedStrategy(allStrat[0].strategyId);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    loadOptions();
  }, []);

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset || !selectedStrategy) {
      alert("Selecciona un dataset aprobado y una estrategia válida");
      return;
    }
    setLoading(true);
    try {
      await api.runFastBacktest(selectedStrategy, selectedDataset, capital);
      await loadOptions();
    } catch (err: any) {
      alert(`Error en backtest: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewLedger = async (backtestId: string) => {
    try {
      const trades = await api.getBacktestTrades(backtestId);
      setActiveLedger(trades);
      setActiveBacktestId(backtestId);
    } catch (err: any) {
      alert(`No se pudo cargar el ledger: ${err.message}`);
    }
  };

  return (
    <div className="space-y-4 font-sans max-w-[1600px] mx-auto">
      {/* HEADER */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-400">
            <Zap className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Consola de Backtesting Real (FastEngine)
              </h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-amber-500/20 text-amber-400 border border-amber-500/30">
                DETERMINISTIC SIMULATION
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Ejecución estricta de backtests deterministas sobre datasets aprobados y persistencia inmutable en SQLite
            </p>
          </div>
        </div>

        <button
          onClick={loadOptions}
          className="p-2 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.1] transition cursor-pointer"
          title="Actualizar datos"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* NEW BACKTEST FORM */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 shadow-xl space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-amber-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Ejecutar Nuevo Backtest (FastEngine)
            </h2>
          </div>
          <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 px-2.5 py-0.5 rounded-xl border border-emerald-700/60">
            Zero-Mocks Deterministic
          </span>
        </div>

        {error ? (
          <div className="p-4 bg-rose-950/60 border border-rose-500/80 rounded-xl text-rose-200">
            SERVICE_UNAVAILABLE: {error}
          </div>
        ) : datasets.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-white/[0.1] rounded-xl bg-[#050811]/40 text-slate-400 space-y-2">
            <div>No hay datasets aprobados disponibles en base de datos.</div>
            <Link href="/data" className="text-sky-400 hover:text-sky-300 font-bold inline-block">
              Ir a Data Pipeline para aprobar datasets →
            </Link>
          </div>
        ) : (
          <form onSubmit={handleRunBacktest} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Dataset Aprobado</label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
              >
                {datasets.map((d) => (
                  <option key={d.datasetId} value={d.datasetId}>
                    {d.symbol} ({d.interval}) — {d.recordCount} records
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Estrategia DSL</label>
              <select
                value={selectedStrategy}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
              >
                {strategies.map((s) => (
                  <option key={s.strategyId} value={s.strategyId}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Capital Inicial ($)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                min={100}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
              />
            </div>

            <div>
              <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Apalancamiento (x)</label>
              <input
                type="number"
                value={leverage}
                onChange={(e) => setLeverage(Number(e.target.value))}
                min={1}
                max={125}
                className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-xl font-black bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-900/40 transition cursor-pointer flex items-center justify-center gap-2 active:scale-95"
              >
                <Play className="w-4 h-4" />
                {loading ? "Ejecutando..." : "EJECUTAR BACKTEST"}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* LEDGER MODAL / DRAWER */}
      {activeLedger && (
        <div className="bg-[#090d16]/95 border border-cyan-500/50 rounded-2xl p-5 shadow-2xl space-y-3 font-mono text-xs animate-in fade-in">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-cyan-400" />
              Registro de Trades (Ledger): {activeBacktestId}
            </h3>
            <button
              onClick={() => setActiveLedger(null)}
              className="px-3 py-1 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 font-bold cursor-pointer"
            >
              Cerrar
            </button>
          </div>
          <div className="max-h-64 overflow-y-auto bg-[#04070c] p-3 rounded-xl border border-white/[0.06]">
            <pre className="text-[11px] text-cyan-300">
              {JSON.stringify(activeLedger, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* RESULTS HISTORY */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4 font-mono text-xs">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <h3 className="text-base font-bold text-white">
            Historial de Resultados en Backend ({backtests.length})
          </h3>
          <span className="text-slate-400 text-[11px]">Persistencia SQLite Inmutable</span>
        </div>

        {backtests.length === 0 ? (
          <div className="p-10 text-center border border-dashed border-white/[0.1] rounded-xl bg-[#050811]/40 text-slate-500">
            NO_DATA_AVAILABLE — Selecciona un dataset y estrategia arriba para ejecutar tu primer backtest.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] text-slate-400 uppercase text-[10px] bg-[#050811]">
                  <th className="py-2.5 px-3">ID Backtest</th>
                  <th className="py-2.5 px-3">Motor</th>
                  <th className="py-2.5 px-3">Capital</th>
                  <th className="py-2.5 px-3">Final Equity</th>
                  <th className="py-2.5 px-3">Retorno</th>
                  <th className="py-2.5 px-3">Max DD</th>
                  <th className="py-2.5 px-3">Win Rate</th>
                  <th className="py-2.5 px-3">Trades</th>
                  <th className="py-2.5 px-3">PF</th>
                  <th className="py-2.5 px-3 text-right">Ledger</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05] text-[11px]">
                {backtests.map((b) => (
                  <tr key={b.backtestId} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-2.5 px-3 text-sky-400 font-bold">{b.backtestId}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        b.engineType === "CANONICAL"
                          ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                      }`}>
                        {b.engineType}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 tabular-nums">${b.initialCapital.toFixed(2)}</td>
                    <td className="py-2.5 px-3 font-bold text-white tabular-nums">${b.finalEquity.toFixed(2)}</td>
                    <td className={`py-2.5 px-3 font-bold tabular-nums ${b.netReturnPct >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {b.netReturnPct >= 0 ? "+" : ""}{b.netReturnPct.toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-3 text-rose-400 tabular-nums">-{b.maxDrawdownPct.toFixed(2)}%</td>
                    <td className="py-2.5 px-3 text-slate-300 tabular-nums">{b.winRate.toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-slate-300 tabular-nums">{b.tradesCount}</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold tabular-nums">{b.profitFactor.toFixed(2)}</td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleViewLedger(b.backtestId)}
                        className="px-2 py-1 rounded bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.08] text-[10px] font-bold cursor-pointer"
                      >
                        Ver Trades
                      </button>
                    </td>
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
