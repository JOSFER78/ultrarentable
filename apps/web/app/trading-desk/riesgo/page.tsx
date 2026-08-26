"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  AlertOctagon,
  AlertTriangle,
  Clock,
  Zap,
  TrendingDown,
  RefreshCw,
} from "lucide-react";

export default function HermesRiskPage() {
  const [account, setAccount] = useState({
    account_id: "DEMO1279346",
    base_capital_usd: 50000.0,
    daily_pnl_usd: 0.0,
    current_drawdown_usd: 0.0,
    trailing_drawdown_limit_usd: 2000.0,
  });

  const fetchStatus = async () => {
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade/status");
      if (res.ok) {
        const data = await res.json();
        setAccount(data);
      }
    } catch {}
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const dailyLossLimitUsd = 1000.0;
  const currentDailyLoss = account.daily_pnl_usd < 0 ? Math.abs(account.daily_pnl_usd) : 0;
  const dailyLossPct = (currentDailyLoss / dailyLossLimitUsd) * 100;
  const ddPct = (account.current_drawdown_usd / account.trailing_drawdown_limit_usd) * 100;

  return (
    <div className="space-y-4 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white">Hermes Risk Sentinel & Drawdown</h1>
            <p className="text-xs text-slate-400 font-mono">Guardarraíl Fail-Closed · Auto-Flatten al 80% · Kill-Switch al 95%</p>
          </div>
        </div>
        <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-bold">
          SENTINEL ARMED
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-300 font-bold">Trailing Drawdown Guard</span>
            <span className="text-emerald-400 font-bold">{ddPct.toFixed(1)}% Usado</span>
          </div>
          <div className="text-2xl font-black text-white">
            ${account.current_drawdown_usd.toFixed(2)} / ${account.trailing_drawdown_limit_usd.toFixed(2)} USD
          </div>
          <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-emerald-500 h-full transition-all" style={{ width: `${Math.max(2, ddPct)}%` }} />
          </div>
          <p className="text-[11px] text-slate-400">Colchón restante: <strong className="text-emerald-400">${(account.trailing_drawdown_limit_usd - account.current_drawdown_usd).toFixed(2)} USD</strong></p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-slate-300 font-bold">Daily Loss Limit (DLL)</span>
            <span className="text-emerald-400 font-bold">{dailyLossPct.toFixed(1)}% Usado</span>
          </div>
          <div className="text-2xl font-black text-white">
            ${currentDailyLoss.toFixed(2)} / ${dailyLossLimitUsd.toFixed(2)} USD
          </div>
          <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-emerald-500 h-full transition-all" style={{ width: `${Math.max(2, dailyLossPct)}%` }} />
          </div>
          <p className="text-[11px] text-slate-400">Colchón diario: <strong className="text-emerald-400">${(dailyLossLimitUsd - currentDailyLoss).toFixed(2)} USD</strong></p>
        </div>
      </div>
    </div>
  );
}
