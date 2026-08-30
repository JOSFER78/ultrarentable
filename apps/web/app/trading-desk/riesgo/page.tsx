"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  AlertOctagon,
  Lock,
  Flame,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  TrendingDown,
  Activity,
  Layers,
  WifiOff,
  AlertCircle,
  Hash,
  Sliders,
  SlidersHorizontal,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface AccountRiskInfo {
  account_id?: string;
  broker?: string;
  environment?: string;
  base_capital_usd?: number | null;
  current_equity_usd?: number | null;
  daily_pnl_usd?: number | null;
  current_drawdown_usd?: number | null;
  trailing_drawdown_limit_usd?: number | null;
  gateway_status?: string;
  last_ping_latency_ms?: number | null;
}

interface ExecutionSession {
  session_id: string;
  route: string;
  symbol: string;
  status: string;
  current_pnl_usd: number;
  current_drawdown_pct: number;
  kill_switch_active: boolean;
}

export default function HermesRiskPage() {
  const { user, profile, loading: authLoading } = useAuth();

  const [account, setAccount] = useState<AccountRiskInfo | null>(null);
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [isFlattenModalOpen, setIsFlattenModalOpen] = useState(false);
  const [isFlattening, setIsFlattening] = useState(false);
  const [isLocking, setIsLocking] = useState(false);
  const [notification, setNotification] = useState<{ text: string; isError: boolean } | null>(null);

  // Derive real credentials from Firestore User Profile
  const linkedAccounts = profile?.trading_accounts || profile?.broker_accounts || {};
  const linkedAccountId =
    linkedAccounts.tradovate_account_id?.trim() ||
    linkedAccounts.ninjatrader_account_id?.trim() ||
    account?.account_id?.trim() ||
    "";
  const linkedToken =
    linkedAccounts.pickmytrade_token?.trim() ||
    linkedAccounts.gateway_webhook_token?.trim() ||
    "";
  const hasLinkedAccount = Boolean(linkedAccountId);

  const showToast = (text: string, isError = false) => {
    setNotification({ text, isError });
    setTimeout(() => setNotification(null), 6000);
  };

  const fetchStatus = useCallback(async () => {
    setFetchError(null);
    try {
      const [gwRes, sessRes] = await Promise.all([
        fetch("/api/v1/gateways/pickmytrade/status"),
        fetch("/api/v1/execution/sessions"),
      ]);

      if (gwRes.ok) {
        const data = await gwRes.json();
        setAccount(data);
      } else {
        setAccount(null);
        setFetchError(`Error al consultar métricas de riesgo (HTTP ${gwRes.status}).`);
      }

      if (sessRes.ok) {
        const sessData = await sessRes.json();
        setSessions(Array.isArray(sessData) ? sessData : []);
      }
    } catch (e: any) {
      setAccount(null);
      setFetchError(e.message || "Error de conexión con el backend.");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleGlobalEmergencyLock = async () => {
    setIsLocking(true);
    try {
      const res = await fetch("/api/v1/gateways/emergency-lock?reason=OPERATOR_MANUAL_RISK_PANEL_TRIGGER", {
        method: "POST",
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`🚨 BLOQUEO GLOBAL ACTIVADO: ${data.sessions_stopped_count ?? 0} sesiones bloqueadas.`, true);
        fetchStatus();
      } else {
        showToast(`⚠️ Error al activar bloqueo: ${JSON.stringify(data)}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error de red: ${err.message}`, true);
    } finally {
      setIsLocking(false);
    }
  };

  const handleExecuteFlattenAll = async () => {
    if (!hasLinkedAccount) {
      showToast("⚠️ Requiere vincular una cuenta real en Configuración", true);
      return;
    }

    setIsFlattening(true);
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/flatten", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker: "ALL",
          account: linkedAccountId,
          token: linkedToken,
          reason: "SENTINEL_RISK_PAGE_EMERGENCY_FLATTEN",
        }),
      });

      const data = await res.json();
      if (res.ok && data.success) {
        showToast("🚨 ¡FLATTEN TOTAL EJECUTADO! Todas las posiciones liquidadas en Tradovate.");
        fetchStatus();
      } else {
        showToast("⚠️ Señal 'flat' despachada al broker.");
      }
    } catch (err: any) {
      showToast(`❌ Error en Flatten: ${err.message}`, true);
    } finally {
      setIsFlattening(false);
      setIsFlattenModalOpen(false);
    }
  };

  const handleSessionKillSwitch = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/v1/execution/sessions/${sessionId}/kill-switch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "SENTINEL_RISK_SESSION_KILL_SWITCH_TRIGGERED" }),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`🚨 Kill-switch activado para sesión ${sessionId}.`);
        fetchStatus();
      } else {
        showToast(`⚠️ Error: ${data.detail || JSON.stringify(data)}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error de conexión: ${err.message}`, true);
    }
  };

  const dailyLossLimitUsd = 1000.0;
  const currentDailyLoss = account?.daily_pnl_usd != null && account.daily_pnl_usd < 0 ? Math.abs(account.daily_pnl_usd) : 0;
  const dailyLossPct = (currentDailyLoss / dailyLossLimitUsd) * 100;
  const trailingLimit = account?.trailing_drawdown_limit_usd;
  const currentDd = account?.current_drawdown_usd ?? 0.0;
  const ddPct = trailingLimit && trailingLimit > 0 ? (currentDd / trailingLimit) * 100 : 0;

  const isConnected = (account?.gateway_status === "CONNECTED" || account?.gateway_status === "IDLE_WAITING") && hasLinkedAccount;

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER BAR */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">Sentinel de Riesgo CME & Kill-Switches</h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30">
                FAIL-CLOSED ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Cuenta: <strong className="text-emerald-400">{hasLinkedAccount ? linkedAccountId : "SIN CUENTA VINCULADA"}</strong> · Auto-Flatten al 80% · Kill-Switch al 95%
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto font-mono">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-1.5 ${
              isConnected
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-rose-500/20 text-rose-400 border-rose-500/30"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>SENTINEL ARMED · ONLINE</span>
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
              fetchStatus();
            }}
            className="p-2 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.1] transition cursor-pointer"
            title="Refrescar estado de riesgo"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin text-emerald-400" : ""}`} />
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

      {/* NO LINKED ACCOUNT WARNING */}
      {!hasLinkedAccount && !authLoading && (
        <div className="p-4 bg-amber-950/40 border border-amber-500/40 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono text-amber-200 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
              <SlidersHorizontal className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">Sin cuenta vinculada para Sentinel de Riesgo</div>
              <p className="text-[11px] text-amber-300/80 font-sans mt-0.5">
                Para monitorear el Trailing Drawdown real y gestionar la liquidación de emergencia en Tradovate, vincula tu cuenta en Ajustes.
              </p>
            </div>
          </div>
          <Link
            href="/trading-desk/configuracion"
            className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs rounded-xl transition flex items-center gap-2 shrink-0 shadow-lg shadow-amber-900/30"
          >
            <Sliders className="w-4 h-4" />
            Vincular Cuenta en Ajustes →
          </Link>
        </div>
      )}

      {fetchError && (
        <div className="p-4 bg-rose-950/60 border border-rose-500/80 rounded-2xl text-xs font-mono text-rose-200 flex items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>ESTADO: <strong>DESCONECTADO</strong> — {fetchError}</span>
          </div>
          <button
            onClick={fetchStatus}
            className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Reintentar
          </button>
        </div>
      )}

      {/* RISK GAUGES (TRAILING DD & DAILY LOSS) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        {/* Trailing Drawdown Card */}
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-300 font-bold flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              Trailing Drawdown Guard
            </span>
            <span className="text-emerald-400 font-bold tabular-nums">
              {trailingLimit != null ? `${ddPct.toFixed(1)}% Usado` : "SIN DATOS"}
            </span>
          </div>
          <div className="text-2xl font-black text-white tabular-nums">
            {trailingLimit != null
              ? `$${currentDd.toFixed(2)} / $${trailingLimit.toFixed(2)} USD`
              : "SIN DATOS / NO VINCULADA"}
          </div>
          <div className="w-full bg-[#050811] h-3 rounded-full overflow-hidden border border-white/[0.08]">
            <div
              className={`h-full transition-all duration-300 ${
                ddPct > 80 ? "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]" : ddPct > 50 ? "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]" : "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
              }`}
              style={{ width: `${Math.max(2, Math.min(100, ddPct))}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Colchón restante:</span>
            <strong className="text-emerald-400 tabular-nums">
              {trailingLimit != null ? `$${(trailingLimit - currentDd).toFixed(2)} USD` : "SIN DATOS"}
            </strong>
          </div>
        </div>

        {/* Daily Loss Limit Card */}
        <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-300 font-bold flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4 text-blue-400" />
              Daily Loss Limit (DLL)
            </span>
            <span className="text-emerald-400 font-bold tabular-nums">
              {account?.daily_pnl_usd != null ? `${dailyLossPct.toFixed(1)}% Usado` : "SIN DATOS"}
            </span>
          </div>
          <div className="text-2xl font-black text-white tabular-nums">
            {account?.daily_pnl_usd != null
              ? `$${currentDailyLoss.toFixed(2)} / $${dailyLossLimitUsd.toFixed(2)} USD`
              : "SIN DATOS / NO VINCULADA"}
          </div>
          <div className="w-full bg-[#050811] h-3 rounded-full overflow-hidden border border-white/[0.08]">
            <div
              className={`h-full transition-all duration-300 ${
                dailyLossPct > 80 ? "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]" : dailyLossPct > 50 ? "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]" : "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
              }`}
              style={{ width: `${Math.max(2, Math.min(100, dailyLossPct))}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Colchón diario restante:</span>
            <strong className="text-emerald-400 tabular-nums">
              {account?.daily_pnl_usd != null ? `$${(dailyLossLimitUsd - currentDailyLoss).toFixed(2)} USD` : "SIN DATOS"}
            </strong>
          </div>
        </div>
      </div>

      {/* EMERGENCY CONTROL ACTIONS PANEL */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Centro de Control de Emergencia & Liquidación Inmediata
            </h2>
          </div>
          <span className="text-xs font-mono text-rose-400 font-bold bg-rose-950/60 px-2.5 py-1 rounded-xl border border-rose-700/60">
            ACCIONES DE ALTO IMPACTO
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          {/* Action 1: Flatten All in Tradovate */}
          <div className="p-5 bg-[#050811] rounded-2xl border border-rose-900/50 space-y-3 flex flex-col justify-between shadow-lg">
            <div>
              <div className="text-sm font-bold text-rose-400 flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4" />
                Liquidación Total Tradovate (Flatten All)
              </div>
              <p className="text-slate-400 text-[11px] mt-1 font-sans">
                Despacha la señal <strong className="text-white">flat</strong> directamente al broker Tradovate ({linkedAccountId || "SIN VINCULAR"}) para liquidar todas las posiciones abiertas al instante.
              </p>
            </div>
            <button
              onClick={() => setIsFlattenModalOpen(true)}
              disabled={!hasLinkedAccount}
              className={`w-full py-2.5 rounded-xl font-bold transition flex items-center justify-center gap-2 mt-2 ${
                hasLinkedAccount
                  ? "bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/40 cursor-pointer active:scale-95"
                  : "bg-slate-800 text-slate-500 border border-white/[0.05] cursor-not-allowed opacity-60"
              }`}
            >
              <AlertOctagon className="w-4 h-4" />
              EJECUTAR FLATTEN TOTAL
            </button>
          </div>

          {/* Action 2: Emergency Lock Global */}
          <div className="p-5 bg-[#050811] rounded-2xl border border-amber-900/50 space-y-3 flex flex-col justify-between shadow-lg">
            <div>
              <div className="text-sm font-bold text-amber-400 flex items-center gap-1.5">
                <Lock className="w-4 h-4" />
                Bloqueo Global de Emergencia (Emergency Lock)
              </div>
              <p className="text-slate-400 text-[11px] mt-1 font-sans">
                Activa el Kill-Switch en todas las sesiones de ejecución activas en base de datos, deteniendo el flujo algorítmico globalmente.
              </p>
            </div>
            <button
              onClick={handleGlobalEmergencyLock}
              disabled={isLocking}
              className="w-full py-2.5 rounded-xl font-bold bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-900/40 transition cursor-pointer flex items-center justify-center gap-2 active:scale-95 mt-2"
            >
              <Lock className="w-4 h-4" />
              {isLocking ? "Activando..." : "BLOQUEAR TODAS LAS SESIONES"}
            </button>
          </div>
        </div>
      </div>

      {/* ACTIVE SESSIONS KILL-SWITCH TABLE */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-400" />
            <h3 className="text-base font-bold text-white tracking-tight">
              Control de Kill-Switch por Sesión ({sessions.length})
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {sessions.filter(s => s.kill_switch_active).length} Bloqueadas
          </span>
        </div>

        {sessions.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-white/[0.1] rounded-2xl bg-[#050811]/40 text-xs font-mono text-slate-500">
            CERO SESIONES DE EJECUCIÓN ACTIVAS (Ningún Kill-Switch pendiente)
          </div>
        ) : (
          <div className="overflow-x-auto font-mono text-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] text-slate-400 uppercase text-[10px] bg-[#050811]">
                  <th className="py-2.5 px-3">Sesión ID</th>
                  <th className="py-2.5 px-3">Símbolo</th>
                  <th className="py-2.5 px-3">Estado</th>
                  <th className="py-2.5 px-3">PnL</th>
                  <th className="py-2.5 px-3">Drawdown</th>
                  <th className="py-2.5 px-3 text-right">Kill-Switch</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05] text-[11px]">
                {sessions.map((s) => (
                  <tr key={s.session_id} className="hover:bg-white/[0.03] transition-colors">
                    <td className="py-2.5 px-3 font-bold text-white">{s.session_id}</td>
                    <td className="py-2.5 px-3 text-slate-300">{s.symbol}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        s.kill_switch_active
                          ? "bg-rose-500/20 text-rose-400 border border-rose-500/30"
                          : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                      }`}>
                        {s.status}
                      </span>
                    </td>
                    <td className={`py-2.5 px-3 font-bold tabular-nums ${s.current_pnl_usd >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                      ${s.current_pnl_usd.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300 tabular-nums">{s.current_drawdown_pct.toFixed(2)}%</td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={() => handleSessionKillSwitch(s.session_id)}
                        disabled={s.kill_switch_active}
                        className="px-2.5 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-[10px] transition cursor-pointer"
                      >
                        {s.kill_switch_active ? "BLOQUEADA" : "ACTIVAR KILL-SWITCH"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* FLATTEN CONFIRMATION MODAL */}
      {isFlattenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150">
          <div className="bg-[#090d16] border-2 border-rose-600 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-[0_0_50px_rgba(244,63,94,0.25)]">
            <div className="flex items-center gap-3 text-rose-500">
              <div className="p-3 bg-rose-500/20 rounded-xl border border-rose-500/30">
                <AlertOctagon className="w-8 h-8 animate-bounce" />
              </div>
              <div>
                <h3 className="text-lg font-black text-white">¿CONFIRMAR FLATTEN TOTAL?</h3>
                <p className="text-xs text-rose-300 font-mono">Liquidación inmediata en Tradovate ({linkedAccountId || "SIN VINCULAR"})</p>
              </div>
            </div>

            <div className="p-4 bg-rose-950/40 border border-rose-900/60 rounded-xl space-y-2 text-xs text-slate-300 font-mono">
              <p>Esta acción enviará la señal <strong className="text-white">flat</strong> a PickMyTrade:</p>
              <ul className="list-disc list-inside space-y-1 text-[11px] text-rose-200">
                <li>Liquidará todas las posiciones abiertas a precio de mercado.</li>
                <li>Cancelará todos los brackets OCO pendientes.</li>
              </ul>
            </div>

            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              <button
                onClick={() => setIsFlattenModalOpen(false)}
                className="py-2.5 rounded-xl font-bold bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.1] transition cursor-pointer"
              >
                Cancelar
              </button>
              <button
                onClick={handleExecuteFlattenAll}
                disabled={isFlattening || !hasLinkedAccount}
                className="py-2.5 rounded-xl font-black bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/50 transition cursor-pointer"
              >
                {isFlattening ? "Liquidando..." : "SÍ, LIQUIDAR TODO"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
