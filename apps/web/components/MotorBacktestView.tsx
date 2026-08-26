"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Search,
  Sliders,
  TrendingUp,
  ShieldCheck,
  Hash,
  ArrowRight,
  Info,
  DollarSign,
} from "lucide-react";
import {
  executeBacktest,
  getCandidates,
  CandidateStrategy,
  BacktestResult,
} from "@/lib/api";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";
import Link from "next/link";
import QuantTooltip from "@/components/system/QuantTooltip";

const CAPITAL_PRESETS = [
  { label: "$10K", value: 10000, desc: "Micro" },
  { label: "$25K", value: 25000, desc: "Mini" },
  { label: "$50K", value: 50000, desc: "Prop Base" },
  { label: "$100K", value: 100000, desc: "Estándar" },
  { label: "$200K", value: 200000, desc: "Pro" },
];

const SLIPPAGE_PRESETS = [
  { label: "0 Ticks (Cero)", value: 0 },
  { label: "1 Tick (Normal)", value: 1 },
  { label: "2 Ticks (Estrés)", value: 2 },
];

const POPULAR_SYMBOLS = ["TODOS", "BTC", "ETH", "SOL", "EUR", "NQ", "ES", "DOGE"];

export default function MotorBacktestView() {
  const [candidates, setCandidates] = useState<CandidateStrategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<CandidateStrategy | null>(null);
  const [loadingCandidates, setLoadingCandidates] = useState<boolean>(true);
  const [runningBacktest, setRunningBacktest] = useState<boolean>(false);
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedSymbolFilter, setSelectedSymbolFilter] = useState<string>("TODOS");

  const [symbol, setSymbol] = useState<string>("BTC");
  const [timeframe, setTimeframe] = useState<string>("1h");
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [slippageTicks, setSlippageTicks] = useState<number>(1);
  const [showAdvancedHashes, setShowAdvancedHashes] = useState<boolean>(false);

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
        selectStrategy(data[0]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar catálogo.";
      setErrorMsg(msg);
    } finally {
      setLoadingCandidates(false);
    }
  }

  function selectStrategy(strat: CandidateStrategy) {
    setSelectedStrategy(strat);
    setSymbol(strat.symbol || "BTC");
    setTimeframe(strat.timeframe || "1h");
    setBacktestResult(null);
  }

  const filteredCandidates = useMemo(() => {
    return candidates.filter((item) => {
      const matchesSearch =
        searchQuery === "" ||
        item.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesSymbolFilter =
        selectedSymbolFilter === "TODOS" ||
        item.symbol.toUpperCase().includes(selectedSymbolFilter.toUpperCase());

      return matchesSearch && matchesSymbolFilter;
    });
  }, [candidates, searchQuery, selectedSymbolFilter]);

  async function handleRunBacktest() {
    if (!selectedStrategy) return;

    setRunningBacktest(true);
    setErrorMsg(null);
    setBacktestResult(null);

    try {
      const result = await executeBacktest({
        strategy_id: selectedStrategy.id,
        symbol,
        timeframe,
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

  function getTrafficStatus(result: BacktestResult) {
    const pf = result.profit_factor || 0;
    const pnl = result.total_net_pnl || 0;
    const dd = result.max_drawdown_pct || 0;

    if (pf >= 1.4 && pnl > 0 && dd <= 12) {
      return {
        variant: "safe",
        badgeText: "🟢 ESTRATEGIA RENTABLE & SEGURA",
        badgeBg: "bg-emerald-950/80 border-emerald-500 text-emerald-300",
        summaryText: "Comportamiento observado en el backtest real. La clasificación no sustituye a los 11 Gates.",
        canProceed: true,
      };
    } else if (pf >= 1.0 && pnl >= 0 && dd <= 20) {
      return {
        variant: "moderate",
        badgeText: "🟡 RIESGO MODERADO / REVISIÓN",
        badgeBg: "bg-amber-950/80 border-amber-500 text-amber-300",
        summaryText: "El backtest real muestra beneficio con mayor riesgo. Revisar antes de cualquier promoción.",
        canProceed: false,
      };
    }

    return {
      variant: "danger",
      badgeText: "🔴 ESTRATEGIA EN PÉRDIDA O RIESGOSA",
      badgeBg: "bg-rose-950/80 border-rose-500 text-rose-300",
      summaryText: "El backtest real no cumple los umbrales operativos mostrados.",
      canProceed: false,
    };
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <EstrategiasHeaderNav />

        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚡</span>
              <h1 className="text-2xl font-bold tracking-tight">Fase 1: Motor de Estrategias & Backtest Real</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Ejecuta el motor canónico sobre un dataset real. Esta pantalla no fabrica resultados cuando la API falla.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              FastEngine · provenance locked
            </span>
            <button
              onClick={loadCandidates}
              disabled={loadingCandidates}
              className="inline-flex items-center px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loadingCandidates ? "animate-spin" : ""}`} />
              Actualizar Lista
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-200 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold">Ejecución no disponible</div>
              <div className="text-sm mt-1">{errorMsg}</div>
              <div className="text-xs mt-2 text-rose-300/80">No se ha sustituido el resultado por datos sintéticos.</div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold">Estrategias</h2>
                <span className="text-xs text-slate-500">{filteredCandidates.length}</span>
              </div>
              <div className="flex gap-2 mb-3">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar…"
                    className="w-full rounded-md bg-slate-950 border border-slate-800 pl-9 pr-3 py-2 text-sm outline-none"
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-4">
                {POPULAR_SYMBOLS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setSelectedSymbolFilter(item)}
                    className={`px-2 py-1 rounded text-[11px] border ${
                      selectedSymbolFilter === item
                        ? "border-slate-500 bg-slate-800 text-white"
                        : "border-slate-800 bg-slate-950 text-slate-500"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
              <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
                {loadingCandidates ? (
                  <div className="text-sm text-slate-500 py-8 text-center">Cargando estrategias…</div>
                ) : filteredCandidates.length === 0 ? (
                  <div className="text-sm text-slate-500 py-8 text-center">No hay candidatos disponibles.</div>
                ) : (
                  filteredCandidates.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => selectStrategy(item)}
                      className={`w-full text-left rounded-lg border p-3 transition ${
                        selectedStrategy?.id === item.id
                          ? "border-cyan-700 bg-cyan-950/20"
                          : "border-slate-800 bg-slate-950/50 hover:bg-slate-900"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="font-medium text-sm truncate">{item.name}</div>
                        <span className="text-[10px] text-slate-500">{item.engine_version}</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {item.symbol} · {item.timeframe} · PF OOS {item.oos_profit_factor.toFixed(2)}
                      </div>
                    </button>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 space-y-4">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-slate-400" />
                <h2 className="font-semibold">Configuración de ejecución</h2>
              </div>

              <label className="block text-xs text-slate-400">
                Símbolo
                <input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  className="mt-1 w-full rounded-md bg-slate-950 border border-slate-800 px-3 py-2 text-sm"
                />
              </label>

              <label className="block text-xs text-slate-400">
                Timeframe
                <input
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="mt-1 w-full rounded-md bg-slate-950 border border-slate-800 px-3 py-2 text-sm"
                />
              </label>

              <div>
                <div className="text-xs text-slate-400 mb-2">Capital inicial</div>
                <div className="grid grid-cols-2 gap-2">
                  {CAPITAL_PRESETS.map((preset) => (
                    <button
                      key={preset.value}
                      type="button"
                      onClick={() => setInitialCapital(preset.value)}
                      className={`rounded-md border p-2 text-left ${
                        initialCapital === preset.value
                          ? "border-cyan-700 bg-cyan-950/20"
                          : "border-slate-800 bg-slate-950"
                      }`}
                    >
                      <div className="text-sm font-medium">{preset.label}</div>
                      <div className="text-[10px] text-slate-500">{preset.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400 mb-2">Slippage</div>
                <div className="space-y-2">
                  {SLIPPAGE_PRESETS.map((preset) => (
                    <button
                      key={preset.value}
                      type="button"
                      onClick={() => setSlippageTicks(preset.value)}
                      className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                        slippageTicks === preset.value
                          ? "border-cyan-700 bg-cyan-950/20"
                          : "border-slate-800 bg-slate-950"
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={handleRunBacktest}
                disabled={!selectedStrategy || runningBacktest}
                className="w-full inline-flex items-center justify-center gap-2 rounded-md bg-cyan-700 hover:bg-cyan-600 disabled:opacity-50 disabled:cursor-not-allowed px-4 py-2.5 font-semibold"
              >
                <Play className="w-4 h-4" />
                {runningBacktest ? "Ejecutando motor…" : "Ejecutar backtest real"}
              </button>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-5">
              {!selectedStrategy ? (
                <div className="py-20 text-center text-slate-500">Selecciona una estrategia para comenzar.</div>
              ) : !backtestResult ? (
                <div className="py-20 text-center">
                  <DollarSign className="w-10 h-10 mx-auto text-slate-700" />
                  <div className="mt-3 font-semibold">Sin resultado de backtest</div>
                  <div className="mt-1 text-sm text-slate-500">Ejecuta el motor para obtener métricas y evidencia reales.</div>
                </div>
              ) : (
                <>
                  <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                    <div>
                      <div className="text-xs text-slate-500">Resultado real</div>
                      <h2 className="text-xl font-semibold mt-1">{selectedStrategy.name}</h2>
                      <div className="text-sm text-slate-400 mt-1">
                        {backtestResult.strategy_id} · {symbol} · {timeframe} · engine {backtestResult.engine_version}
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border border-emerald-800 bg-emerald-950/40 text-emerald-300">
                      <CheckCircle2 className="w-3.5 h-3.5" /> API REAL
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
                    <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                      <div className="text-xs text-slate-500">Profit Factor</div>
                      <div className="text-lg font-semibold mt-1">{backtestResult.profit_factor.toFixed(2)}</div>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                      <div className="text-xs text-slate-500">Win Rate</div>
                      <div className="text-lg font-semibold mt-1">{backtestResult.win_rate_pct.toFixed(2)}%</div>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                      <div className="text-xs text-slate-500">Net PnL</div>
                      <div className="text-lg font-semibold mt-1">${backtestResult.total_net_pnl.toFixed(2)}</div>
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                      <div className="text-xs text-slate-500">Max Drawdown</div>
                      <div className="text-lg font-semibold mt-1">{backtestResult.max_drawdown_pct.toFixed(2)}%</div>
                    </div>
                  </div>

                  {(() => {
                    const status = getTrafficStatus(backtestResult);
                    return (
                      <div className={`mt-5 rounded-lg border p-4 ${status.badgeBg}`}>
                        <div className="font-semibold text-sm">{status.badgeText}</div>
                        <div className="text-xs mt-1 opacity-80">{status.summaryText}</div>
                      </div>
                    );
                  })()}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
                    <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                      <div className="text-sm font-semibold mb-3">Proveniencia</div>
                      <div className="space-y-2 text-xs text-slate-400">
                        <div className="flex justify-between gap-3"><span>Run ID</span><span className="text-slate-200 break-all">{backtestResult.run_id}</span></div>
                        <div className="flex justify-between gap-3"><span>Dataset hash</span><span className="text-slate-200 break-all">{backtestResult.dataset_hash}</span></div>
                        <div className="flex justify-between gap-3"><span>Ledger hash</span><span className="text-slate-200 break-all">{backtestResult.ledger_hash}</span></div>
                        <div className="flex justify-between gap-3"><span>Evidence bundle</span><span className="text-slate-200 break-all">{backtestResult.evidence_bundle_hash}</span></div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setShowAdvancedHashes((value) => !value)}
                        className="mt-3 text-xs text-cyan-400 hover:text-cyan-300"
                      >
                        {showAdvancedHashes ? "Ocultar hashes" : "Mostrar hashes avanzados"}
                      </button>
                      {showAdvancedHashes && (
                        <div className="mt-3 border-t border-slate-800 pt-3 space-y-2 text-xs text-slate-500">
                          <div>Strategy hash: {backtestResult.strategy_hash}</div>
                          <div>Execution config: {backtestResult.execution_config_hash}</div>
                        </div>
                      )}
                    </div>

                    <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                      <div className="text-sm font-semibold mb-3">OOS</div>
                      <div className="space-y-2 text-xs text-slate-400">
                        <div className="flex justify-between"><span>Trades</span><span className="text-slate-200">{backtestResult.oos_trades}</span></div>
                        <div className="flex justify-between"><span>PF OOS</span><span className="text-slate-200">{backtestResult.oos_profit_factor.toFixed(2)}</span></div>
                        <div className="flex justify-between"><span>OOS meses</span><span className="text-slate-200">{backtestResult.oos_months ?? "—"}</span></div>
                        <div className="flex justify-between"><span>CAGR</span><span className="text-slate-200">{backtestResult.cagr ?? "—"}</span></div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 rounded-lg border border-slate-800 bg-slate-950 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold">Equity curve</div>
                        <div className="text-xs text-slate-500 mt-1">Únicamente los puntos devueltos por el motor.</div>
                      </div>
                      <Link href="/gates" className="text-xs text-cyan-400 hover:text-cyan-300 inline-flex items-center gap-1">
                        Ver gates <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
                    <div className="mt-4 h-56 flex items-center justify-center rounded-md border border-dashed border-slate-800">
                      {backtestResult.equity_curve.length > 0 ? (
                        <div className="w-full h-full p-4 overflow-auto">
                          <pre className="text-[10px] leading-4 text-slate-500 whitespace-pre-wrap">{JSON.stringify(backtestResult.equity_curve, null, 2)}</pre>
                        </div>
                      ) : (
                        <div className="text-xs text-slate-600">NO EVIDENCE: el backtest no devolvió curva.</div>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 flex items-start gap-2 text-xs text-slate-500">
                    <Info className="w-4 h-4 flex-shrink-0" />
                    <div>Este resultado no certifica la estrategia. La promoción depende del pipeline de validación y de sus gates explícitos.</div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
