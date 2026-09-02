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
  TrendingUp,
  Award,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

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
  const { user, profile, loading: authLoading } = useAuth();

  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [candidates, setCandidates] = useState<CandidateItem[]>([]);
  const [gatewayData, setGatewayData] = useState<GatewayStatus | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ text: string; isError: boolean } | null>(null);

  // Derive real credentials from Firestore User Profile
  const linkedAccounts = profile?.trading_accounts || profile?.broker_accounts || {};
  const linkedAccountId =
    linkedAccounts.tradovate_account_id?.trim() ||
    linkedAccounts.ninjatrader_account_id?.trim() ||
    gatewayData?.account_id?.trim() ||
    "";
  const hasLinkedAccount = Boolean(linkedAccountId);

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

  const isConnected = (gatewayData?.gateway_status === "CONNECTED" || gatewayData?.gateway_status === "IDLE_WAITING") && hasLinkedAccount;

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black text-[var(--text-1)] tracking-tight">Estrategias & Sesiones de Ejecución</h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)]">
                11 GATES & SESSIONS
              </span>
            </div>
            <p className="text-xs text-[var(--text-2)] font-mono mt-1">
              Control de Sesiones de Despacho en Tradovate ({hasLinkedAccount ? linkedAccountId : "SIN CUENTA VINCULADA"}) · Protocolo Fail-Closed
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto font-mono">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-1.5 ${
              isConnected
                ? "bg-[var(--profit-dim)] text-[var(--profit)] border-[var(--profit)]"
                : "bg-[var(--loss-dim)] text-[var(--loss)] border-[var(--loss)]"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-[var(--profit)] animate-ping" />
                <span className="tabular-nums">GATEWAY ACTIVO · {gatewayData?.last_ping_latency_ms != null ? `${gatewayData.last_ping_latency_ms} ms` : "OK"}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>{hasLinkedAccount ? "DESCONECTADO" : "SIN CUENTA VINCULADA"}</span>
              </>
            )}
          </span>

          <button
            onClick={() => {
              setIsRefreshing(true);
              fetchRealData();
            }}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[var(--bg)] hover:bg-[var(--surface-1)] text-[var(--text-1)] border border-white/[0.1] rounded-xl text-xs font-bold transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-[var(--profit)]" : ""}`} />
            <span>{isRefreshing ? "Actualizando..." : "Refrescar"}</span>
          </button>
        </div>
      </div>

      {notification && (
        <div
          className={`p-3.5 rounded-xl text-xs font-bold font-mono flex items-center gap-2.5 shadow-lg ${
            notification.isError
              ? "bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)]"
              : "bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)]"
          }`}
        >
          {notification.text}
        </div>
      )}

      {fetchError && (
        <div className="p-4 bg-[var(--loss-dim)] border border-[var(--loss)] rounded-2xl text-xs font-mono text-[var(--loss)] flex items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[var(--loss)] flex-shrink-0" />
            <span>ESTADO: <strong>DESCONECTADO</strong> — {fetchError}</span>
          </div>
          <button
            onClick={fetchRealData}
            className="px-3 py-1.5 rounded-lg bg-[var(--surface-3)] hover:bg-[var(--surface-3)] text-[var(--text-1)] font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reintentar
          </button>
        </div>
      )}

      {/* SECTION 1: LIVE EXECUTION SESSIONS */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-[var(--profit)]" />
            <h2 className="text-base font-bold text-[var(--text-1)] tracking-tight">
              Sesiones de Ejecución en Vivo ({sessions.length})
            </h2>
          </div>
          <span className="text-xs font-mono text-[var(--profit)] font-bold bg-[var(--profit-dim)] px-2.5 py-1 rounded-xl border border-[var(--profit)]">
            API /api/v1/execution/sessions
          </span>
        </div>

        {sessions.length === 0 ? (
          <div className="p-12 bg-[var(--bg)] rounded-2xl border border-dashed border-white/[0.1] text-center space-y-4 font-mono">
            <div className="w-12 h-12 rounded-2xl bg-[var(--surface-1)] border border-white/[0.08] flex items-center justify-center mx-auto text-[var(--text-3)]">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-[var(--text-1)] uppercase tracking-wider">
                CERO SESIONES DE EJECUCIÓN ACTIVAS
              </h3>
              <p className="text-xs text-[var(--text-2)] max-w-lg mx-auto leading-relaxed font-sans">
                Bajo la doctrina <strong>ZERO-MOCKS & REAL-ONLY</strong>, ninguna estrategia o sesión se despacha al mercado real sin certificación 11/11 Gates y orden explícita del operador.
              </p>
            </div>
            <div className="pt-1">
              <Link
                href="/gates"
                className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--surface-3)] hover:bg-[var(--surface-3)] text-[var(--text-1)] text-xs font-bold rounded-xl transition shadow-lg "
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
                  className="p-4 bg-[var(--bg)] rounded-xl border border-white/[0.08] space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[var(--text-1)]">{sess.session_id}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)]">
                          {sess.route} · {sess.symbol}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            sess.status === "RUNNING"
                              ? "bg-[var(--profit-dim)] text-[var(--profit)] border-[var(--profit)]"
                              : isPaused
                              ? "bg-[var(--surface-2)] text-[var(--text-2)] border-[var(--border)]"
                              : isKillSwitchActive
                              ? "bg-[var(--loss-dim)] text-[var(--loss)] border-[var(--loss)]"
                              : "bg-[var(--surface-1)] text-[var(--text-2)] border-white/[0.08]"
                          }`}
                        >
                          {sess.status}
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--text-2)] mt-1">
                        Candidato: <strong className="text-[var(--text-1)]">{sess.candidate_id}</strong> · Gateway: <strong className="text-[var(--profit)]">{sess.provider_id}</strong> · Entorno: <strong className="text-[var(--text-1)]">{sess.environment}</strong>
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      {isPaused ? (
                        <button
                          onClick={() => handleSessionAction(sess.session_id, "resume")}
                          disabled={actionLoadingId === `${sess.session_id}_resume`}
                          className="px-3 py-1.5 rounded-lg bg-[var(--profit-dim)] hover:bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)] font-bold text-xs flex items-center gap-1 cursor-pointer"
                        >
                          <Play className="w-3.5 h-3.5" /> Reanudar
                        </button>
                      ) : (
                        <button
                          onClick={() => handleSessionAction(sess.session_id, "pause")}
                          disabled={actionLoadingId === `${sess.session_id}_pause`}
                          className="px-3 py-1.5 rounded-lg bg-[var(--surface-2)] hover:bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)] font-bold text-xs flex items-center gap-1 cursor-pointer"
                        >
                          <Pause className="w-3.5 h-3.5" /> Pausar
                        </button>
                      )}

                      <button
                        onClick={() => handleSessionAction(sess.session_id, "flatten")}
                        disabled={actionLoadingId === `${sess.session_id}_flatten`}
                        className="px-3 py-1.5 rounded-lg bg-[var(--loss-dim)] hover:bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)] font-bold text-xs flex items-center gap-1 cursor-pointer"
                      >
                        <AlertOctagon className="w-3.5 h-3.5" /> Flatten
                      </button>

                      <button
                        onClick={() => handleSessionAction(sess.session_id, "kill-switch")}
                        disabled={actionLoadingId === `${sess.session_id}_kill-switch` || isKillSwitchActive}
                        className="px-3 py-1.5 rounded-lg bg-[var(--surface-3)] hover:bg-[var(--surface-3)] text-[var(--text-1)] font-bold text-xs flex items-center gap-1 cursor-pointer"
                      >
                        <ShieldAlert className="w-3.5 h-3.5" /> Kill-Switch
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-2 border-t border-white/[0.08] text-[11px]">
                    <div>
                      <span className="text-[var(--text-3)] uppercase text-[10px] block">PnL Sesión</span>
                      <span className={`font-bold tabular-nums ${sess.current_pnl_usd >= 0 ? "text-[var(--profit)]" : "text-[var(--loss)]"}`}>
                        ${sess.current_pnl_usd.toFixed(2)} USD
                      </span>
                    </div>
                    <div>
                      <span className="text-[var(--text-3)] uppercase text-[10px] block">Drawdown Actual</span>
                      <span className="font-bold text-[var(--text-1)] tabular-nums">{sess.current_drawdown_pct.toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-[var(--text-3)] uppercase text-[10px] block">Última Señal</span>
                      <span className="text-[var(--text-1)] truncate block">{sess.last_signal || "--"}</span>
                    </div>
                    <div>
                      <span className="text-[var(--text-3)] uppercase text-[10px] block">Última Orden</span>
                      <span className="text-[var(--text-1)] truncate block">{sess.last_order || "--"}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* SECTION 2: CERTIFIED CANDIDATES & VAULT */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-[var(--text-2)]" />
            <h2 className="text-base font-bold text-[var(--text-1)] tracking-tight">
              Bóveda de Estrategias y Candidatos ({candidates.length})
            </h2>
          </div>
          <Link
            href="/gates"
            className="text-xs font-mono text-[var(--text-2)] hover:text-[var(--text-1)] flex items-center gap-1 font-bold"
          >
            Auditar en 11 Gates <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {candidates.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-white/[0.1] rounded-2xl bg-[var(--bg)] text-xs font-mono text-[var(--text-3)]">
            CERO ESTRATEGIAS REGISTRADAS EN BASE DE DATOS
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
            {candidates.map((cand) => (
              <div
                key={cand.candidate_id}
                className="p-4 bg-[var(--bg)] rounded-xl border border-white/[0.08] space-y-2.5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-bold text-[var(--text-2)] uppercase">
                      {cand.route} · {cand.symbol} ({cand.timeframe})
                    </span>
                    <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-[var(--surface-1)] text-[var(--text-1)] border border-white/[0.08]">
                      {cand.tier_label || cand.status}
                    </span>
                  </div>
                  <h3 className="text-xs font-bold text-[var(--text-1)] truncate">{cand.name || cand.candidate_id}</h3>
                  <p className="text-[10px] text-[var(--text-2)] mt-0.5">
                    Gates Superados: <strong className="text-[var(--text-1)]">{cand.gates_passed_count ?? 0}/11</strong>
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/[0.08] text-[10px]">
                  <div>
                    <span className="text-[var(--text-3)] block">PF OOS:</span>
                    <span className="font-bold text-[var(--text-1)] tabular-nums">{cand.profit_factor_oos != null ? cand.profit_factor_oos.toFixed(2) : "NO EVIDENCE"}</span>
                  </div>
                  <div>
                    <span className="text-[var(--text-3)] block">Max DD OOS:</span>
                    <span className="font-bold text-[var(--text-1)] tabular-nums">{cand.max_dd_oos_pct != null ? `${cand.max_dd_oos_pct.toFixed(1)}%` : "NO EVIDENCE"}</span>
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
