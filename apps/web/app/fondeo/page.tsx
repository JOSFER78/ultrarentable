"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldCheck,
  Building2,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingUp,
  Flame,
  Zap,
  Layers,
  Sparkles,
} from "lucide-react";

interface PropFirmChallenge {
  id: string;
  name: string;
  account_size: number;
  profit_target: number;
  max_trailing_dd: number;
  daily_loss_limit: number;
  min_trading_days: number;
  consistency_max_pct: number;
  auto_flatten_time: string;
  drawdown_type: string;
}

const PROP_CATALOG: PropFirmChallenge[] = [
  { id: "mffu_50k", name: "MyFundedFutures 50K Rapid", account_size: 50000, profit_target: 3000, max_trailing_dd: 2000, daily_loss_limit: 1200, min_trading_days: 1, consistency_max_pct: 40, auto_flatten_time: "15:59 CST", drawdown_type: "EOD Trailing" },
  { id: "tradeify_50k", name: "Tradeify 50K Growth", account_size: 50000, profit_target: 2500, max_trailing_dd: 1500, daily_loss_limit: 1000, min_trading_days: 3, consistency_max_pct: 40, auto_flatten_time: "15:59 CST", drawdown_type: "EOD Trailing" },
  { id: "tradeday_50k", name: "TradeDay 50K FastPass", account_size: 50000, profit_target: 3000, max_trailing_dd: 2000, daily_loss_limit: 1000, min_trading_days: 5, consistency_max_pct: 50, auto_flatten_time: "15:59 CST", drawdown_type: "EOD Trailing" },
  { id: "blusky_50k", name: "BluSky 50K Static", account_size: 50000, profit_target: 3000, max_trailing_dd: 1500, daily_loss_limit: 0, min_trading_days: 5, consistency_max_pct: 40, auto_flatten_time: "15:59 CST", drawdown_type: "100% Estático Fijo" },
  { id: "topstep_50k", name: "Topstep 50K Combine", account_size: 50000, profit_target: 3000, max_trailing_dd: 2000, daily_loss_limit: 1000, min_trading_days: 2, consistency_max_pct: 50, auto_flatten_time: "15:59 CST", drawdown_type: "EOD Trailing" },
  { id: "apex_50k", name: "Apex Trader Funding 50K", account_size: 50000, profit_target: 3000, max_trailing_dd: 2500, daily_loss_limit: 0, min_trading_days: 1, consistency_max_pct: 30, auto_flatten_time: "15:59 CST", drawdown_type: "Trailing Intradía" },
];

export default function TrackFondeoCMEPage() {
  const [selectedFirm, setSelectedFirm] = useState<PropFirmChallenge>(PROP_CATALOG[0]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Carga de sesiones reales
  useEffect(() => {
    fetch("/api/v1/execution/sessions?route=FONDEO")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setSessions(Array.isArray(data) ? data : []);
      })
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  const activeSession = sessions.length > 0 ? sessions[0] : null;

  const currentEquity = activeSession ? (selectedFirm.account_size + activeSession.current_pnl_usd) : selectedFirm.account_size;
  const peakEquity = activeSession ? activeSession.peak_equity_usd : selectedFirm.account_size;
  const todayPnl = activeSession ? activeSession.daily_pnl_usd : 0.0;
  const totalProfit = currentEquity - selectedFirm.account_size;
  const targetProgress = Math.min(100, Math.max(0, (totalProfit / selectedFirm.profit_target) * 100));
  const currentDd = Math.max(0, peakEquity - currentEquity);
  const ddBuffer = Math.max(0, selectedFirm.max_trailing_dd - currentDd);
  const ddUsagePct = Math.min(100, (currentDd / selectedFirm.max_trailing_dd) * 100);
  const isDllOk = selectedFirm.daily_loss_limit === 0 || todayPnl > -selectedFirm.daily_loss_limit;

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 pb-24 text-slate-100">
      {/* 1. HEADER */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Link href="/" className="text-xs text-slate-400 hover:text-white transition">
                ← Command Center
              </Link>
              <span className="text-slate-600">/</span>
              <span className="text-xs font-mono font-bold text-sky-400 uppercase tracking-wider">
                TRACK_FONDEO · INSTITUTIONAL CME PROP FIRMS
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Dashboard de Fondeo CME & Compliance Guard
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Supervisión estricta de cuentas de evaluación y fondeadas: Trailing DD intra-trade, Daily Loss Limit y regla de consistencia.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <Link
              href="/prop-firms"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold bg-amber-500 hover:bg-amber-400 text-slate-950 transition shadow-lg shadow-amber-500/20"
            >
              <Building2 className="w-4 h-4" />
              <span>Catálogo 70 Prop Firms</span>
            </Link>
            <Link
              href="/tradesfera"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold bg-sky-950/80 text-sky-300 border border-sky-700/60 hover:bg-sky-900 transition"
            >
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>Tratado Tradesfera M01-M16</span>
            </Link>
          </div>
        </div>
      </div>

      {/* 2. SELECTOR DE EMPRESA DE FONDEO */}
      <div className="space-y-2">
        <span className="text-[11px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
          Seleccionar Programa de Fondeo para Modelar Compliance:
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {PROP_CATALOG.map((firm) => {
            const isSelected = selectedFirm.id === firm.id;
            return (
              <button
                key={firm.id}
                onClick={() => setSelectedFirm(firm)}
                className={`p-3.5 rounded-xl text-left transition-all border backdrop-blur-xl ${
                  isSelected
                    ? "bg-sky-950/40 border-sky-500 shadow-md shadow-sky-500/10 ring-1 ring-sky-500/30"
                    : "bg-[#090d16]/90 border-white/[0.08] hover:border-sky-500/30"
                }`}
              >
                <div className="text-xs font-black text-white truncate">{firm.name}</div>
                <div className="text-[10px] text-slate-400 font-mono mt-1">
                  Target: ${firm.profit_target.toLocaleString()}
                </div>
                <div className="text-[10px] text-sky-400 font-mono">
                  Max DD: ${firm.max_trailing_dd.toLocaleString()}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. MASTER COMPLIANCE METRICS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Equity Actual */}
        <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-5 shadow-xl space-y-1.5">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
            EQUITY REAL DE LA CUENTA
          </span>
          <div className="text-2xl sm:text-3xl font-black text-white font-mono tabular-nums">
            ${currentEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div
            className={`text-xs font-mono font-bold ${
              totalProfit >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            Beneficio: {totalProfit >= 0 ? `+$${totalProfit.toFixed(2)}` : `-$${Math.abs(totalProfit).toFixed(2)}`} USD
          </div>
        </div>

        {/* Trailing Drawdown Buffer */}
        <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-5 shadow-xl space-y-1.5">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
            COLCHÓN TRAILING DRAWDOWN
          </span>
          <div
            className={`text-2xl sm:text-3xl font-black font-mono tabular-nums ${
              ddBuffer > 800 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            ${ddBuffer.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div className="text-xs font-mono text-slate-400">
            Uso: {ddUsagePct.toFixed(1)}% de ${selectedFirm.max_trailing_dd.toLocaleString()}
          </div>
        </div>

        {/* Target Progress */}
        <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-5 shadow-xl space-y-1.5">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
            PROGRESO TARGET (${selectedFirm.profit_target.toLocaleString()})
          </span>
          <div className="text-2xl sm:text-3xl font-black text-sky-400 font-mono tabular-nums">
            {targetProgress.toFixed(1)}%
          </div>
          <div className="text-xs font-mono text-slate-400">
            Faltan: ${Math.max(0, selectedFirm.profit_target - totalProfit).toFixed(2)} USD
          </div>
        </div>

        {/* Daily Loss Limit */}
        <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-5 shadow-xl space-y-1.5">
          <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider block">
            ESTADO DAILY LOSS LIMIT ({selectedFirm.daily_loss_limit > 0 ? `$${selectedFirm.daily_loss_limit}` : "SIN DLL"})
          </span>
          <div
            className={`text-2xl sm:text-3xl font-black font-mono ${
              isDllOk ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {isDllOk ? "DENTRO DE LÍMITE" : "🚨 VIOLACIÓN"}
          </div>
          <div className="text-xs font-mono text-slate-400">
            PnL Hoy: ${todayPnl.toFixed(2)} USD
          </div>
        </div>
      </div>

      {/* 4. CME SESSION TIMER & AUTO-FLATTEN MONITOR */}
      <div className="bg-gradient-to-r from-sky-950/40 via-[#090d16]/90 to-slate-950/90 border border-sky-500/30 backdrop-blur-xl rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-black text-white flex items-center gap-2">
              <span>Temporizador Mandatorio de Auto-Flatten CME ({selectedFirm.auto_flatten_time})</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Cierre automático de posiciones 10 minutos antes del corte diario para evitar sanciones por overnight de las prop firms.
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 text-xs font-mono font-black shrink-0">
          <ShieldCheck className="w-4 h-4" />
          <span>GUARD ACTIVO · 0 OVERNIGHT</span>
        </div>
      </div>

      {/* 5. ACTIVE SESSIONS TABLE */}
      <div className="bg-[#090d16]/90 border border-white/[0.08] backdrop-blur-xl rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-base font-black text-white flex items-center gap-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <span>Sesiones de Fondeo Registradas en SQLite</span>
            </h2>
            <p className="text-xs text-slate-400">
              Telemetría determinista en tiempo real desde la API de ejecución.
            </p>
          </div>
          <Link
            href="/ejecucion"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-sky-950/80 hover:bg-sky-900 text-sky-300 border border-sky-700/60 text-xs font-mono font-bold transition"
          >
            <Zap className="w-3.5 h-3.5 text-sky-400" />
            <span>Centro de Ejecución Live →</span>
          </Link>
        </div>

        {sessions.length === 0 ? (
          <div className="p-8 text-center text-slate-400 text-xs font-mono space-y-2">
            <div>No hay sesiones de fondeo activas en este momento.</div>
            <p className="text-slate-500 text-[11px]">
              Despliega una estrategia validada en <Link href="/ejecucion" className="text-sky-400 underline">Ejecución</Link> o conecta NinjaTrader 8.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-slate-800 text-[11px] text-slate-400 uppercase font-bold tracking-wider">
                  <th className="py-2.5 px-3">Sesión</th>
                  <th className="py-2.5 px-3">Estrategia</th>
                  <th className="py-2.5 px-3">Símbolo</th>
                  <th className="py-2.5 px-3">Estado</th>
                  <th className="py-2.5 px-3 text-right">PnL Hoy</th>
                  <th className="py-2.5 px-3 text-right">Peak Equity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {sessions.map((s) => (
                  <tr key={s.session_id} className="hover:bg-slate-900/40 transition">
                    <td className="py-3 px-3 text-sky-400 font-bold">{s.session_id}</td>
                    <td className="py-3 px-3 text-slate-300 font-sans">{s.candidate_id}</td>
                    <td className="py-3 px-3 font-bold text-white">{s.symbol}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                          s.status === "RUNNING"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        }`}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td className={`py-3 px-3 text-right tabular-nums font-bold ${s.daily_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {s.daily_pnl_usd >= 0 ? `+$${s.daily_pnl_usd.toFixed(2)}` : `-$${Math.abs(s.daily_pnl_usd).toFixed(2)}`}
                    </td>
                    <td className="py-3 px-3 text-right tabular-nums text-slate-300">
                      ${s.peak_equity_usd?.toFixed(2)}
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
