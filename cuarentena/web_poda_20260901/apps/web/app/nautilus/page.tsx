"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Activity,
  Zap,
  Sliders,
  Play,
  ShieldCheck,
  ShieldAlert,
  Server,
  Database,
  CheckCircle2,
  AlertCircle,
  Hash,
  Terminal,
  Cpu,
  Layers,
} from "lucide-react";

interface CandidateItem {
  candidate_id: string;
  name: string;
  symbol: string;
  timeframe: string;
  route: string;
  status: string;
  metrics?: {
    out_of_sample?: {
      profit_factor?: number;
      net_profit_usd?: number;
      max_drawdown_pct?: number;
      trades?: number;
    };
  };
}

function fmtOrSinDatos(
  v: number | null | undefined,
  opts?: { decimals?: number; prefix?: string; suffix?: string }
): string {
  if (v == null) return "SIN DATOS";
  const decimals = opts?.decimals ?? 2;
  return `${opts?.prefix ?? ""}${v.toFixed(decimals)}${opts?.suffix ?? ""}`;
}

export default function NautilusTraderStudioPage() {
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>("");
  const [venue, setVenue] = useState<string>("BINANCE_PERP");
  const [fillModel, setFillModel] = useState<string>("MAKER_TAKER");
  const [latencyMs, setLatencyMs] = useState<number>(15);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<any | null>(null);

  useEffect(() => {
    fetch("/api/v1/candidates?limit=200&include_rejected=true")
      .then((r) => (r.ok ? r.json() : []))
      .then((d) => {
        const list = Array.isArray(d) ? d : (d.candidates || []);
        setCandidates(list);
        if (list.length > 0) {
          setSelectedCandidateId(list[0].candidate_id);
        }
      })
      .catch(() => {});
  }, []);

  const handleRunNautilusSimulation = async () => {
    if (!selectedCandidateId) return;
    setSimulating(true);
    setSimulationResult(null);

    try {
      const res = await fetch(`/api/v1/gates/gate-10-nautilus-trader/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: selectedCandidateId,
          venue: venue,
          fill_model: fillModel,
          latency_ms: latencyMs,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSimulationResult(data);
      } else {
        const errText = await res.text().catch(() => "");
        setSimulationResult({
          status: "ERROR",
          engine: "NautilusTrader Core v1.190.0 (Rust/Cython)",
          venue: venue,
          candidate_id: selectedCandidateId,
          message: `Servicio NautilusTrader no disponible (HTTP ${res.status}): ${errText || "SIN DATOS / NO EVIDENCE"}`,
        });
      }
    } catch (err: any) {
      setSimulationResult({
        status: "ERROR",
        engine: "NautilusTrader Core (Rust/Cython)",
        venue: venue,
        candidate_id: selectedCandidateId,
        message: `Error de conexión con NautilusTrader: ${err?.message || "DESCONECTADO"}`,
      });
    } finally {
      setSimulating(false);
    }
  };

  const selectedCand = candidates.find((c) => c.candidate_id === selectedCandidateId);

  return (
    <div className="space-y-4 font-sans max-w-[1600px] mx-auto">
      {/* HEADER */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-sky-500/10 border border-sky-500/30 rounded-xl text-sky-400">
            <Cpu className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                NautilusTrader Event-Driven Simulation Studio
              </h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-sky-500/20 text-sky-400 border border-sky-500/30">
                GATE 11 · RUST / CYTHON
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Motor de ejecución barra a barra de alta frecuencia para reconciliación exacta de fills y slippage real
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs">
          <Link
            href="/gates"
            className="px-3.5 py-1.5 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-200 border border-white/[0.1] font-bold transition flex items-center gap-1.5"
          >
            ← 11 Evidence Gates
          </Link>
        </div>
      </div>

      {/* SETUP PANEL */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
        {/* COL 1: SELECCIÓN DE ESTRATEGIA */}
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-3 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-sky-400 uppercase font-bold block mb-2">
              1. Estrategia Candidata
            </span>
            <select
              value={selectedCandidateId}
              onChange={(e) => setSelectedCandidateId(e.target.value)}
              disabled={candidates.length === 0}
              className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold mb-3"
            >
              {candidates.length === 0 ? (
                <option value="">(SIN DATOS) 0 Estrategias Candidatas</option>
              ) : (
                candidates.map((c) => (
                  <option key={c.candidate_id} value={c.candidate_id}>
                    {c.symbol} ({c.timeframe}) · {c.name || c.candidate_id} [{c.route}]
                  </option>
                ))
              )}
            </select>
          </div>

          {selectedCand && (
            <div className="p-3 bg-[#050811] rounded-xl border border-white/[0.06] space-y-1.5 text-[11px]">
              <div className="flex justify-between">
                <span className="text-slate-400">Ruta:</span>
                <strong className={selectedCand.route === "ULTRA" ? "text-rose-400" : "text-sky-400"}>
                  {selectedCand.route}
                </strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">PF OOS:</span>
                <strong className="text-emerald-400 tabular-nums">
                  {fmtOrSinDatos(selectedCand.metrics?.out_of_sample?.profit_factor)}
                </strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Max DD:</span>
                <strong className="text-rose-400 tabular-nums">
                  {fmtOrSinDatos(selectedCand.metrics?.out_of_sample?.max_drawdown_pct, { suffix: "%" })}
                </strong>
              </div>
            </div>
          )}
        </div>

        {/* COL 2: VENUE Y MATCHING MODEL */}
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-3">
          <span className="text-[10px] text-amber-400 uppercase font-bold block mb-2">
            2. Venue & Libro de Órdenes
          </span>
          <div>
            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Execution Venue</label>
            <select
              value={venue}
              onChange={(e) => setVenue(e.target.value)}
              className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold mb-3"
            >
              <option value="BINANCE_PERP">Binance Perpetuals (USDT-M)</option>
              <option value="BINGX_PERP">BingX Perpetuals (Hyper-Leverage)</option>
              <option value="CME_GLOBEX">CME Globex (NQ / ES / CL / GC)</option>
              <option value="INTERBANK_FX">Interbank FX (LMAX / Integral)</option>
            </select>
          </div>

          <div>
            <label className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Fill & Matching Model</label>
            <select
              value={fillModel}
              onChange={(e) => setFillModel(e.target.value)}
              className="w-full bg-[#050811] border border-white/[0.1] rounded-xl p-2.5 text-white font-bold"
            >
              <option value="MAKER_TAKER">Maker / Taker Order Book Fill</option>
              <option value="IMMEDIATE_OR_CANCEL">Immediate or Cancel (IOC)</option>
              <option value="BOOK_SLIPPAGE_3X">Estrés de Deslizamiento 3x + Latencia</option>
            </select>
          </div>
        </div>

        {/* COL 3: LATENCIA & DISPARADOR */}
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-emerald-400 uppercase font-bold block mb-2">
              3. Latencia de Red & Simulación
            </span>
            <div className="flex justify-between items-center text-xs mb-2">
              <span className="text-slate-400">Latencia Simulada:</span>
              <strong className="text-sky-400 tabular-nums">{latencyMs} ms</strong>
            </div>
            <input
              type="range"
              min="1"
              max="100"
              value={latencyMs}
              onChange={(e) => setLatencyMs(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <button
            onClick={handleRunNautilusSimulation}
            disabled={simulating || !selectedCandidateId}
            className="w-full py-3 rounded-xl font-black bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-900/40 transition cursor-pointer flex items-center justify-center gap-2 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <Zap className="w-4 h-4" />
            <span>{simulating ? "Simulando Rust/Cython..." : "Ejecutar Simulación Nautilus"}</span>
          </button>
        </div>
      </div>

      {/* RECONCILIATION RESULT */}
      {simulationResult && (
        simulationResult.status === "ERROR" ? (
          <div className="bg-rose-950/40 border border-rose-500/60 rounded-2xl p-5 shadow-xl space-y-2 font-mono text-xs">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-rose-400 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                Error de Reconciliación NautilusTrader
              </h2>
              <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold text-[10px]">
                DESCONECTADO / ERROR
              </span>
            </div>
            <p className="text-slate-300">{simulationResult.message}</p>
            <div className="text-[10px] text-slate-500">
              Motor: {simulationResult.engine} · Venue: {simulationResult.venue} · Estado: NO EVIDENCE
            </div>
          </div>
        ) : (
          <div className="bg-[#090d16]/95 border border-sky-500/40 rounded-2xl p-6 shadow-2xl space-y-4 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div>
                <h2 className="text-base font-bold text-white">
                  Informe de Reconciliación FastEngine vs NautilusTrader
                </h2>
                <div className="text-[10px] text-sky-400 mt-0.5">
                  {simulationResult.engine} · Venue: {simulationResult.venue}
                </div>
              </div>
              <span className={`px-2.5 py-1 rounded-xl text-xs font-bold border ${
                simulationResult.reconciliation?.is_reconciled
                  ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                  : "bg-rose-500/20 text-rose-400 border-rose-500/30"
              }`}>
                {simulationResult.reconciliation?.is_reconciled ? "GATE 11 APROBADO (RECONCILIADO ✓)" : "GATE 11 RECHAZADO"}
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">PnL FastEngine</span>
                <span className="text-base font-bold text-white tabular-nums">
                  {fmtOrSinDatos(simulationResult.reconciliation?.fast_engine_pnl, { prefix: "$" })}
                </span>
              </div>
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">PnL NautilusTrader</span>
                <span className="text-base font-bold text-sky-400 tabular-nums">
                  {fmtOrSinDatos(simulationResult.reconciliation?.nautilus_pnl, { prefix: "$" })}
                </span>
              </div>
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">Discrepancia PnL</span>
                <span className="text-base font-bold text-emerald-400 tabular-nums">
                  {fmtOrSinDatos(simulationResult.reconciliation?.discrepancy_pct, { suffix: "%" })} (≤ 5.0%)
                </span>
              </div>
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.06]">
                <span className="text-[10px] text-slate-400 block">Trades Reconciliados</span>
                <span className="text-base font-bold text-amber-400 tabular-nums">
                  {simulationResult.reconciliation?.trades_executed ?? "SIN DATOS"}
                </span>
              </div>
            </div>

            {simulationResult.logs && (
              <div className="p-4 bg-[#04070c] rounded-xl border border-white/[0.06] space-y-1">
                <span className="text-[10px] text-slate-500 uppercase font-bold block">Logs de Eventos Nautilus:</span>
                {simulationResult.logs.map((l: string, i: number) => (
                  <div key={i} className="text-[11px] text-slate-300">{l}</div>
                ))}
              </div>
            )}
          </div>
        )
      )}
    </div>
  );
}
