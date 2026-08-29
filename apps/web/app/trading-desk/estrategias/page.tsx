"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Bot,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  ShieldAlert,
  Play,
  Pause,
  AlertOctagon,
  Layers,
  Activity,
  CheckCircle2,
  Lock,
  WifiOff,
  AlertCircle,
  Zap,
} from "lucide-react";

interface ExecutionSession {
  session_id: string;
  route: string;
  environment: string;
  candidate_id: string;
  provider_id: string;
  symbol: string;
  status: string;
  execution_confirmed: boolean;
  current_equity_usd?: number;
  current_pnl_usd: number;
  daily_pnl_usd: number;
  current_drawdown_pct: number;
  peak_equity_usd?: number;
  heartbeat_last_at?: string;
  last_signal: string;
  last_order: string;
  open_positions: any[];
  kill_switch_active: boolean;
  kill_switch_reason?: string;
  created_at?: string;
}

interface GatewayStatus {
  provider_id?: string;
  account_id?: string;
  user?: string;
  broker?: string;
  gateway_status?: string;
  last_ping_latency_ms?: number;
}

interface CandidateItem {
  candidate_id: string;
  name?: string;
  route?: string;
  symbol?: string;
  timeframe?: string;
  profit_factor_oos?: number;
  max_dd_oos_pct?: number;
  status?: string;
  tier_label?: string;
  gates_passed_count?: number;
}

export default function EstrategiasActivasPage() {
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [gatewayData, setGatewayData] = useState<GatewayStatus | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ text: string; isError: boolean } | null>(null);

  const showToast = (text: string, isError = false) => {
    setNotification({ text, isError });
    setTimeout(() => setNotification(null), 5000);
  };

  const fetchRealData = useCallback(async () => {
    setFetchError(null);
    try {
      const [sessRes, candRes, gwRes] = await Promise.all([
        fetch("/api/v1/execution/sessions"),
        fetch("/api/v1/candidates"),
        fetch("/api/v1/gateways/pickmytrade/status"),
      ]);

      if (sessRes.ok) {
        const sessData = await sessRes.json();
        setSessions(Array.isArray(sessData) ? sessData : []);
      } else {
        setSessions([]);
        setFetchError(`Error al consultar sesiones de ejecución (HTTP ${sessRes.status}).`);
      }

      if (candRes.ok) {
        const candData = await candRes.json();
        setCandidates(Array.isArray(candData) ? candData : []);
      } else {
        setCandidates([]);
      }

      if (gwRes.ok) {
        const gwData = await gwRes.json();
        setGatewayData(gwData);
      }
    } catch (e: any) {
      setSessions([]);
      setFetchError(e.message || "Error de red al consultar la API.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRealData();
    const interval = setInterval(fetchRealData, 5000);
    return () => clearInterval(interval);
  }, [fetchRealData]);

  const handleSessionAction = async (sessionId: string, action: "pause" | "resume" | "kill-switch" | "flatten") => {
    setActionLoadingId(`${sessionId}_${action}`);
    try {
      const options: RequestInit = { method: "POST" };
      if (action === "kill-switch") {
        options.headers = { "Content-Type": "application/json" };
        options.body = JSON.stringify({ reason: "MANUAL_OPERATOR_KILL_SWITCH_TRIGGERED" });
      }

      const res = await fetch(`/api/v1/execution/sessions/${sessionId}/${action}`, options);
      const data = await res.json();
      if (res.ok) {
        showToast(`✅ Acción '${action.toUpperCase()}' ejecutada en sesión ${sessionId}.`);
        fetchRealData();
      } else {
        showToast(`⚠️ Error en ${action}: ${data.detail || JSON.stringify(data)}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error de conexión: ${err.message}`, true);
    } finally {
      setActionLoadingId(null);
    }
  };

  const isConnected = gatewayData?.gateway_status === "CONNECTED" || gatewayData?.gateway_status === "IDLE_WAITING";

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl text-purple-400">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-white">Estrategias & Sesiones de Ejecución</h1>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-400 border border-purple-500/30">
                11 GATES & SESSIONS
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Control de Sesiones de Despacho en Tradovate ({gatewayData?.account_id ?? "DEMO1279346"}) · Protocolo Fail-Closed
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold border flex items-center gap-1.5 ${
              isConnected
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-rose-500/20 text-rose-400 border-rose-500/30"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>GATEWAY ACTIVO · {gatewayData?.last_ping_latency_ms != null ? `${gatewayData.last_ping_latency_ms} ms` : "OK"}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>DESCONECTADO</span>
              </>
            )}
          </span>

          <button
            onClick={() => {
              setIsRefreshing(true);
              fetchRealData();
            }}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-mono font-bold transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-emerald-400" : ""}`} />
            <span>{isRefreshing ? "Actualizando..." : "Refrescar"}</span>
          </button>
        </div>
      </div>

      {notification && (
        <div
          className={`p-3.5 rounded-xl text-xs font-bold font-mono flex items-center gap-2.5 shadow-lg ${
            notification.isError
              ? "bg-rose-950/90 border border-rose-500/80 text-rose-200"
              : "bg-emerald-950/90 border border-emerald-500/80 text-emerald-200"
          }`}
        >
          {notification.text}
        </div>
      )}

      {fetchError && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/80 rounded-2xl text-xs font-mono text-rose-200 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>ESTADO: <strong>DESCONECTADO</strong> — {fetchError}</span>
          </div>
          <button
            onClick={fetchRealData}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reintentar
          </button>
        </div>
      )}

      {/* SECTION 1: LIVE EXECUTION SESSIONS */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Sesiones de Ejecución en Vivo ({sessions.length})
            </h2>
          </div>
          <span className="text-xs font-mono text-emerald-400 font-bold">
            API /api/v1/execution/sessions
          </span>
        </div>

        {sessions.length === 0 ? (
          <div className="p-12 bg-slate-950/60 rounded-2xl border border-dashed border-slate-800 text-center space-y-4 font-mono">
            <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto text-slate-500">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
                CERO SESIONES DE EJECUCIÓN ACTIVAS
              </h3>
              <p className="text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
                Bajo la doctrina <strong>ZERO-MOCKS & REAL-ONLY</strong>, ninguna estrategia o sesión se despacha al mercado real sin certificación 11/11 Gates y orden explícita del operador.
              </p>
            </div>
            <div className="pt-1">
              <Link
                href="/gates"
                className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded-xl transition shadow-lg shadow-sky-900/30"
              >
                <ShieldCheck className="w-4 h-4" />
                Ver Candidatos en 11 Evidence Gates
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ) : (
          <div className="space-y-3 font-mono text-xs">
            {sessions.map((sess) => {
              const isKillSwitchActive = sess.kill_switch_active;
              const isPaused = sess.status === "PAUSED";

              return (
                <div
                  key={sess.session_id}
                  className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white">{sess.session_id}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                          {sess.route} · {sess.symbol}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            sess.status === "RUNNING"
                              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                              : isPaused
                              ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                              : isKillSwitchActive
                              ? "bg-rose-500/20 text-rose-400 border-rose-500/30"
                              : "bg-slate-800 text-slate-400 border-slate-700"
                          }`}
                        >
                          {sess.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Candidato: <strong className="text-slate-200">{sess.candidate_id}</strong> · Gateway: <strong className="text-emerald-400">{sess.provider_id}</strong> · Entorno: <strong className="text-slate-300">{sess.environment}</strong>
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {isPaused ? (
                        <button
                          onClick={() => handleSessionAction(sess.session_id, "resume")}
                          disabled={actionLoadingId === `${sess.session_id}_resume`}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 font-bold text-xs flex items-center gap-1 cursor-pointer"
                        >
                          <Play className="w-3.5 h-3.5" /> Reanudar
                        </button>
                      ) : (
                        <button
                          onClick={() => handleSessionAction(sess.session_id, "pause")}
                          disabled={actionLoadingId === `${sess.session_id}_pause`}
                          className="px-3 py-1.5 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/30 font-bold text-xs flex items-center gap-1 cursor-pointer"
                        >
                          <Pause className="w-3.5 h-3.5" /> Pausar
                        </button>
                      )}

                      <button
                        onClick={() => handleSessionAction(sess.session_id, "flatten")}
                        disabled={actionLoadingId === `${sess.session_id}_flatten`}
                        className="px-3 py-1.5 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-400 border border-rose-500/30 font-bold text-xs flex items-center gap-1 cursor-pointer"
                      >
                        <AlertOctagon className="w-3.5 h-3.5" /> Flatten
                      </button>

                      <button
                        onClick={() => handleSessionAction(sess.session_id, "kill-switch")}
                        disabled={actionLoadingId === `${sess.session_id}_kill-switch` || isKillSwitchActive}
                        className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs flex items-center gap-1 cursor-pointer"
                      >
                        <ShieldAlert className="w-3.5 h-3.5" /> Kill-Switch
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                    <div>
                      <span className="text-slate-500 uppercase text-[10px] block">PnL Sesión</span>
                      <span className={`font-bold ${sess.current_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                        ${sess.current_pnl_usd.toFixed(2)} USD
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px] block">Drawdown Actual</span>
                      <span className="font-bold text-slate-300">{sess.current_drawdown_pct.toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px] block">Última Señal</span>
                      <span className="text-slate-300 truncate block">{sess.last_signal || "--"}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 uppercase text-[10px] block">Última Orden</span>
                      <span className="text-slate-300 truncate block">{sess.last_order || "--"}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: CERTIFIED CANDIDATES & VAULT */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Bóveda de Estrategias y Candidatos ({candidates.length})
            </h2>
          </div>
          <Link
            href="/gates"
            className="text-xs font-mono text-sky-400 hover:text-sky-300 flex items-center gap-1 font-bold"
          >
            Auditar en 11 Gates <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {candidates.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/40 text-xs font-mono text-slate-500">
            CERO ESTRATEGIAS REGISTRADAS EN BASE DE DATOS
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
            {candidates.map((cand) => (
              <div
                key={cand.candidate_id}
                className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2.5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">
                      {cand.route} · {cand.symbol} ({cand.timeframe})
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {cand.tier_label || cand.status}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-white truncate">{cand.name || cand.candidate_id}</h3>
                  <p className="text-[10px] text-slate-400 mt-0.5">
                    Gates Superados: <strong className="text-slate-200">{cand.gates_passed_count ?? 0}/11</strong>
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800 text-[10px]">
                  <div>
                    <span className="text-slate-500 block">PF OOS:</span>
                    <span className="font-bold text-slate-200">{cand.profit_factor_oos != null ? cand.profit_factor_oos.toFixed(2) : "NO EVIDENCE"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Max DD OOS:</span>
                    <span className="font-bold text-slate-200">{cand.max_dd_oos_pct != null ? `${cand.max_dd_oos_pct.toFixed(1)}%` : "NO EVIDENCE"}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
