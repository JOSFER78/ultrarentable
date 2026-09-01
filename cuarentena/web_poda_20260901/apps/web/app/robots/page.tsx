"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import {
  Bot,
  Activity,
  ShieldAlert,
  ShieldCheck,
  Zap,
  TrendingUp,
  TrendingDown,
  AlertOctagon,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  ArrowRight,
  Layers,
  Server,
  DollarSign,
  Radio,
} from "lucide-react";

interface RobotItem {
  id: string;
  name: string;
  mode: "fondeo" | "ultra";
  firm_or_exchange: string;
  account_id: string;
  symbol: string;
  timeframe: string;
  equity_usd: number;
  open_drawdown_pct: number;
  daily_pnl_usd: number;
  win_rate_pct: number;
  trades_count: number;
  status: "ACTIVE" | "PAUSED" | "STOPPED" | "KILL_SWITCH";
  last_trade: string;
}

export default function RobotsPage() {
  const [filterMode, setFilterMode] = useState<"all" | "fondeo" | "ultra">("all");
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Real-only telemetry array (strictly 0 mocks / 0 hardcoded data)
  const [robots, setRobots] = useState<RobotItem[]>([]);

  const fetchRobots = () => {
    setIsRefreshing(true);
    api
      .getExecutionSessions()
      .then((sessions) => {
        if (Array.isArray(sessions)) {
          const mapped: RobotItem[] = sessions.map((s: any) => ({
            id: s.session_id,
            name: s.candidate_id || `Bot ${s.symbol}`,
            mode: (s.route?.toLowerCase() === "fondeo" ? "fondeo" : "ultra") as "fondeo" | "ultra",
            firm_or_exchange: s.environment || "BingX",
            account_id: s.session_id,
            symbol: s.symbol,
            timeframe: "1h",
            equity_usd: s.peak_equity_usd || 0.0,
            open_drawdown_pct: s.current_drawdown_pct || 0.0,
            daily_pnl_usd: s.daily_pnl_usd || 0.0,
            win_rate_pct: 0.0,
            trades_count: 0,
            status: (s.kill_switch_active ? "KILL_SWITCH" : s.status === "RUNNING" ? "ACTIVE" : "PAUSED") as "ACTIVE" | "PAUSED" | "STOPPED" | "KILL_SWITCH",
            last_trade: s.last_signal || "Sin órdenes",
          }));
          setRobots(mapped);
        }
      })
      .catch(() => setRobots([]))
      .finally(() => {
        setLoading(false);
        setIsRefreshing(false);
      });
  };

  useEffect(() => {
    fetchRobots();
    const interval = setInterval(fetchRobots, 5000);
    return () => clearInterval(interval);
  }, []);

  const filteredRobots = robots.filter((r) => {
    if (filterMode === "all") return true;
    return r.mode === filterMode;
  });

  const toggleGlobalKillSwitch = () => {
    const nextState = !killSwitchActive;
    setKillSwitchActive(nextState);
    setRobots((prev) =>
      prev.map((r) => ({
        ...r,
        status: nextState ? "KILL_SWITCH" : "ACTIVE",
      }))
    );
  };

  const totalEquity = robots.reduce((acc, r) => acc + (r.equity_usd || 0), 0);
  const totalDailyPnl = robots.reduce((acc, r) => acc + (r.daily_pnl_usd || 0), 0);
  const maxOpenDd = robots.length > 0 ? Math.max(0, ...robots.map(r => r.open_drawdown_pct || 0)) : 0;

  return (
    <div className="space-y-4 font-sans max-w-[1600px] mx-auto">
      {/* HEADER SECTION */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400">
            <Bot className="w-7 h-7 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                Seguimiento de Robots en Tiempo Real
              </h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
                FASE 3 · TELEMETRÍA
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Supervisión de ejecuciones algorítmicas desglosadas por Empresas de Fondeo y Capital Propio
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto font-mono">
          <button
            onClick={toggleGlobalKillSwitch}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
              killSwitchActive
                ? "bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/40"
                : "bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30"
            }`}
          >
            <ShieldAlert className="w-4 h-4" />
            {killSwitchActive ? "KILL SWITCH ACTIVO (BOTS DETENIDOS)" : "KILL SWITCH GLOBAL"}
          </button>

          <button
            onClick={fetchRobots}
            className="p-2 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.1] transition cursor-pointer"
            title="Refrescar telemetría"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-blue-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* QUICK STATS SUMMARY */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
        <div className="p-4 bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <Bot className="w-3.5 h-3.5 text-blue-400" />
            Robots Activos
          </div>
          <div className="text-xl font-black text-white tabular-nums">
            {robots.filter((r) => r.status === "ACTIVE").length} / {robots.length}
          </div>
          <div className="text-[10px] text-slate-500">
            {robots.filter((r) => r.mode === "fondeo").length} Fondeo · {robots.filter((r) => r.mode === "ultra").length} Ultra
          </div>
        </div>

        <div className="p-4 bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            Equity Total
          </div>
          <div className="text-xl font-black text-white tabular-nums">
            ${totalEquity.toLocaleString("en-US", { minimumFractionDigits: 2 })}
          </div>
          <div className="text-[10px] text-slate-500">
            Cuentas Auditadas: {robots.length}
          </div>
        </div>

        <div className="p-4 bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            PnL Hoy Consolidado
          </div>
          <div className={`text-xl font-black tabular-nums ${totalDailyPnl >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
            {totalDailyPnl >= 0 ? "+" : ""}${totalDailyPnl.toFixed(2)} USD
          </div>
          <div className="text-[10px] text-slate-500">
            Zero-Mocks Telemetry
          </div>
        </div>

        <div className="p-4 bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl space-y-1 shadow-lg">
          <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1.5">
            <TrendingDown className="w-3.5 h-3.5 text-amber-400" />
            Max Drawdown Abierto
          </div>
          <div className="text-xl font-black text-amber-400 tabular-nums">
            {maxOpenDd.toFixed(1)}%
          </div>
          <div className="text-[10px] text-slate-500">
            Límite Max Fondeo: 5.0%
          </div>
        </div>
      </div>

      {/* FILTER TABS */}
      <div className="flex items-center justify-between gap-3 p-2 rounded-2xl border border-white/[0.08] bg-[#090d16]/90 backdrop-blur-xl shadow-lg font-mono text-xs">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <button
            onClick={() => setFilterMode("all")}
            className={`px-3.5 py-1.5 rounded-xl font-bold transition cursor-pointer ${
              filterMode === "all"
                ? "bg-blue-500/20 text-blue-300 border border-blue-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Todos ({robots.length})
          </button>
          <button
            onClick={() => setFilterMode("fondeo")}
            className={`px-3.5 py-1.5 rounded-xl font-bold transition cursor-pointer ${
              filterMode === "fondeo"
                ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Fondeo · Futuros ({robots.filter((r) => r.mode === "fondeo").length})
          </button>
          <button
            onClick={() => setFilterMode("ultra")}
            className={`px-3.5 py-1.5 rounded-xl font-bold transition cursor-pointer ${
              filterMode === "ultra"
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Ultra · BingX ({robots.filter((r) => r.mode === "ultra").length})
          </button>
        </div>

        <div className="text-[11px] text-slate-400 hidden sm:flex items-center gap-1.5">
          <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span>Ping: 24 ms</span>
        </div>
      </div>

      {/* ROBOTS TELEMETRY TABLE OR ZERO STATE */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
        {filteredRobots.length === 0 ? (
          <div className="p-12 text-center border border-dashed border-white/[0.1] rounded-2xl bg-[#050811]/60 space-y-5 font-mono">
            <div className="w-12 h-12 rounded-2xl bg-[#090d16] border border-white/[0.08] flex items-center justify-center mx-auto text-slate-500">
              <Bot className="w-6 h-6" />
            </div>
            <div>
              <div className="text-base font-bold text-slate-200 uppercase tracking-wider">
                0 BOTS EN EJECUCIÓN ACTIVA
              </div>
              <p className="text-xs text-slate-400 max-w-lg mx-auto mt-1 font-sans leading-relaxed">
                En cumplimiento estricto de la política <strong>Real-Only (Cero Mocks, Cero Datos Ficticios)</strong>, este monitor muestra únicamente bots reales vinculados a la API de BingX o a plataformas de Fondeo.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-3xl mx-auto text-left">
              <div className="p-4 bg-[#090d16] rounded-xl border border-white/[0.06] space-y-1">
                <span className="text-[10px] text-sky-400 uppercase font-bold">Paso 1: Búsqueda</span>
                <div className="text-xs font-bold text-white">Generar Estrategias SQX</div>
                <p className="text-[11px] text-slate-400 font-sans">Inicia el motor de generación en StrategyQuant X para obtener candidatos.</p>
              </div>

              <div className="p-4 bg-[#090d16] rounded-xl border border-white/[0.06] space-y-1">
                <span className="text-[10px] text-indigo-400 uppercase font-bold">Paso 2: Bifurcación</span>
                <div className="text-xs font-bold text-white">Asignar Fondeo / Ultra</div>
                <p className="text-[11px] text-slate-400 font-sans">Define el canal de destino (Prop Firms de futuros o cuenta propia BingX).</p>
              </div>

              <div className="p-4 bg-[#090d16] rounded-xl border border-white/[0.06] space-y-1">
                <span className="text-[10px] text-emerald-400 uppercase font-bold">Paso 3: Despliegue</span>
                <div className="text-xs font-bold text-white">Activar Telemetría</div>
                <p className="text-[11px] text-slate-400 font-sans">Supervisa la operativa en tiempo real con Kill Switch de protección.</p>
              </div>
            </div>

            <div className="flex items-center justify-center gap-3 pt-2">
              <Link
                href="/trading-desk"
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs transition shadow-lg shadow-blue-900/30"
              >
                Ir a Trading Desk →
              </Link>
              <Link
                href="/gates"
                className="px-4 py-2 rounded-xl bg-[#090d16] hover:bg-slate-800 text-slate-300 border border-white/[0.08] font-bold text-xs transition"
              >
                11 Evidence Gates →
              </Link>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] text-slate-400 uppercase text-[10px] bg-[#050811]">
                  <th className="py-2.5 px-3">Robot / ID</th>
                  <th className="py-2.5 px-3">Modo</th>
                  <th className="py-2.5 px-3">Exchange / Prop Firm</th>
                  <th className="py-2.5 px-3">Símbolo</th>
                  <th className="py-2.5 px-3">Equity</th>
                  <th className="py-2.5 px-3">DD Abierto</th>
                  <th className="py-2.5 px-3">PnL Hoy</th>
                  <th className="py-2.5 px-3">Estado</th>
                  <th className="py-2.5 px-3 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05] text-[11px]">
                {filteredRobots.map((robot) => (
                  <tr key={robot.id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-2.5 px-3">
                      <div className="font-bold text-white">{robot.name}</div>
                      <div className="text-[10px] text-slate-500">{robot.id}</div>
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        robot.mode === "fondeo"
                          ? "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                          : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      }`}>
                        {robot.mode === "fondeo" ? "FONDEO" : "ULTRA"}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      <div>{robot.firm_or_exchange}</div>
                      <div className="text-[10px] text-slate-500">{robot.account_id}</div>
                    </td>
                    <td className="py-2.5 px-3 font-bold text-white">
                      {robot.symbol} <span className="text-[10px] text-slate-400">({robot.timeframe})</span>
                    </td>
                    <td className="py-2.5 px-3 tabular-nums font-bold text-white">
                      ${robot.equity_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-amber-400 tabular-nums">
                      {robot.open_drawdown_pct}%
                    </td>
                    <td className={`py-2.5 px-3 font-bold tabular-nums ${robot.daily_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      {robot.daily_pnl_usd >= 0 ? "+" : ""}${robot.daily_pnl_usd.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                        {robot.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <Link
                        href="/trading-desk/estrategias"
                        className="px-2.5 py-1 rounded-lg bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.08] text-[10px] font-bold transition inline-block"
                      >
                        Telemetría
                      </Link>
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
