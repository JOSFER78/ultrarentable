"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { getApiUrl } from "@/lib/api";

interface NinjaTraderAccount {
  account_id: string;
  account_name: string;
  account_type: string;
  broker: string;
  base_capital_usd: number;
  current_equity_usd: number;
  daily_pnl_usd: number;
  realized_pnl_usd: number;
  unrealized_pnl_usd: number;
  peak_equity_usd: number;
  max_trailing_dd_limit_usd: number;
  daily_loss_limit_usd: number;
  profit_target_usd: number;
  trailing_drawdown_usd: number;
  trailing_drawdown_pct: number;
  remaining_cushion_usd: number;
  profit_target_progress_pct: number;
  status: string;
  last_sync_at: string | null;
  created_at: string | null;
}

interface ExecutionSession {
  session_id: string;
  route: string;
  environment: string;
  candidate_id: string;
  provider_id: string | null;
  symbol: string;
  status: string;
  current_pnl_usd: number;
  daily_pnl_usd: number;
  current_drawdown_pct: number;
  peak_equity_usd: number;
  heartbeat_last_at: string | null;
  last_signal: string;
  last_order: string;
  open_positions: any[];
  kill_switch_active: boolean;
  kill_switch_reason: string | null;
  created_at: string | null;
}

interface RemoteOrderHistoryItem {
  order_id: string;
  account_name: string;
  symbol: string;
  action: string;
  order_type: string;
  price: number | null;
  quantity: number;
  stop_loss_ticks: number | null;
  take_profit_ticks: number | null;
  strategy_source: string;
  status: string;
  timestamp_utc: string;
}

interface CMEInstrumentSpec {
  symbol: string;
  name: string;
  tickSize: number;
  pointValue: number;
  tickValueUsd: number;
  defaultQty: number;
  defaultSlTicks: number;
  defaultTpTicks: number;
  defaultBeTicks: number;
}

const CME_SPECS: Record<string, CMEInstrumentSpec> = {
  MNQ: {
    symbol: "MNQ",
    name: "Micro E-mini Nasdaq-100",
    tickSize: 0.25,
    pointValue: 2.0,
    tickValueUsd: 0.50,
    defaultQty: 2,
    defaultSlTicks: 40,
    defaultTpTicks: 100,
    defaultBeTicks: 60,
  },
  MES: {
    symbol: "MES",
    name: "Micro E-mini S&P 500",
    tickSize: 0.25,
    pointValue: 5.0,
    tickValueUsd: 1.25,
    defaultQty: 2,
    defaultSlTicks: 16,
    defaultTpTicks: 48,
    defaultBeTicks: 24,
  },
  NQ: {
    symbol: "NQ",
    name: "E-mini Nasdaq-100",
    tickSize: 0.25,
    pointValue: 20.0,
    tickValueUsd: 5.00,
    defaultQty: 1,
    defaultSlTicks: 32,
    defaultTpTicks: 80,
    defaultBeTicks: 48,
  },
  ES: {
    symbol: "ES",
    name: "E-mini S&P 500",
    tickSize: 0.25,
    pointValue: 50.0,
    tickValueUsd: 12.50,
    defaultQty: 1,
    defaultSlTicks: 16,
    defaultTpTicks: 48,
    defaultBeTicks: 24,
  },
  MGC: {
    symbol: "MGC",
    name: "Micro Gold Futures",
    tickSize: 0.10,
    pointValue: 10.0,
    tickValueUsd: 1.00,
    defaultQty: 2,
    defaultSlTicks: 20,
    defaultTpTicks: 60,
    defaultBeTicks: 30,
  },
  GC: {
    symbol: "GC",
    name: "Gold Futures",
    tickSize: 0.10,
    pointValue: 100.0,
    tickValueUsd: 10.00,
    defaultQty: 1,
    defaultSlTicks: 20,
    defaultTpTicks: 60,
    defaultBeTicks: 30,
  },
  MCL: {
    symbol: "MCL",
    name: "Micro Crude Oil",
    tickSize: 0.01,
    pointValue: 100.0,
    tickValueUsd: 1.00,
    defaultQty: 2,
    defaultSlTicks: 25,
    defaultTpTicks: 75,
    defaultBeTicks: 38,
  },
  "6E": {
    symbol: "6E",
    name: "Euro FX Futures",
    tickSize: 0.00005,
    pointValue: 125000.0,
    tickValueUsd: 6.25,
    defaultQty: 1,
    defaultSlTicks: 24,
    defaultTpTicks: 72,
    defaultBeTicks: 36,
  },
};

export default function RealExecutionPage() {
  const [accounts, setAccounts] = useState<NinjaTraderAccount[]>([]);
  const [sessions, setSessions] = useState<ExecutionSession[]>([]);
  const [orderHistory, setOrderHistory] = useState<RemoteOrderHistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);

  // Remote Order Terminal State
  const [remoteAccount, setRemoteAccount] = useState<string>("Sim101");
  const [remoteSymbol, setRemoteSymbol] = useState<string>("MNQ");
  const [remoteQty, setRemoteQty] = useState<number>(2);
  const [sendingOrder, setSendingOrder] = useState<boolean>(false);

  // ATM Calculator State
  const [atmSymbol, setAtmSymbol] = useState<string>("MNQ");
  const [atmQty, setAtmQty] = useState<number>(2);
  const [atmSlTicks, setAtmSlTicks] = useState<number>(40);
  const [atmTpTicks, setAtmTpTicks] = useState<number>(100);
  const [atmDailyLossLimit, setAtmDailyLossLimit] = useState<number>(1000);

  // C# Code Viewer State
  const [exportedCode, setExportedCode] = useState<string | null>(null);
  const [exportedFilename, setExportedFilename] = useState<string>("");
  const [selectedCsSymbol, setSelectedCsSymbol] = useState<string>("MNQ");
  const [loadingCode, setLoadingCode] = useState<boolean>(false);

  // Navigation tab
  const [activeTab, setActiveTab] = useState<"AUTO_CONNECT" | "REMOTE_TERMINAL" | "SESSIONS" | "CS_BOTS" | "ATM_BUILDER">("AUTO_CONNECT");

  const fetchRealData = useCallback(async () => {
    try {
      // 1. Fetch Registered NT8 Accounts
      const resAccs = await fetch(getApiUrl("/api/v1/execution/ninjatrader/accounts"));
      if (resAccs.ok) {
        const dataAccs = await resAccs.json();
        setAccounts(Array.isArray(dataAccs) ? dataAccs : []);
        if (dataAccs.length > 0 && remoteAccount === "Sim101") {
          setRemoteAccount(dataAccs[0].account_id);
        }
      }

      // 2. Fetch Real Sessions from SQLite
      const resSessions = await fetch(getApiUrl("/api/v1/execution/sessions"));
      if (resSessions.ok) {
        const dataSessions = await resSessions.json();
        setSessions(Array.isArray(dataSessions) ? dataSessions : []);
      }

      // 3. Fetch Remote Orders History
      const resOrders = await fetch(getApiUrl("/api/v1/execution/ninjatrader/orders/history"));
      if (resOrders.ok) {
        const dataOrders = await resOrders.json();
        setOrderHistory(Array.isArray(dataOrders) ? dataOrders : []);
      }

      setErrorMsg(null);
    } catch (err: any) {
      setErrorMsg(`Error conectando con la API Backend: ${err?.message}`);
    } finally {
      setLoading(false);
    }
  }, [remoteAccount]);

  useEffect(() => {
    fetchRealData();
  }, [fetchRealData]);

  // Polling loop
  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(() => {
      fetchRealData();
    }, 2500);
    return () => clearInterval(timer);
  }, [autoRefresh, fetchRealData]);

  // Update ATM params when instrument changes
  useEffect(() => {
    const spec = CME_SPECS[atmSymbol] || CME_SPECS.MNQ;
    setAtmQty(spec.defaultQty);
    setAtmSlTicks(spec.defaultSlTicks);
    setAtmTpTicks(spec.defaultTpTicks);
  }, [atmSymbol]);

  // Remote Order Dispatcher
  const handleDispatchRemoteOrder = async (action: "BUY" | "SELL" | "FLATTEN" | "KILL_SWITCH") => {
    setSendingOrder(true);
    try {
      const spec = CME_SPECS[remoteSymbol] || CME_SPECS.MNQ;
      const res = await fetch(getApiUrl("/api/v1/execution/ninjatrader/orders"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          account_name: remoteAccount,
          symbol: remoteSymbol,
          action,
          order_type: "MARKET",
          quantity: action === "FLATTEN" || action === "KILL_SWITCH" ? 0 : remoteQty,
          stop_loss_ticks: spec.defaultSlTicks,
          take_profit_ticks: spec.defaultTpTicks,
          strategy_source: "WEB_REMOTE_TERMINAL",
        }),
      });

      if (res.ok) {
        const result = await res.json();
        setActionLog(`⚡ ORDEN REMOTA ENVIADA A NINJATRADER 8: ${action} ${remoteQty} ${remoteSymbol} (${result.order_id}).`);
        fetchRealData();
      } else {
        setActionLog(`✕ Error enviando orden remota.`);
      }
    } catch (err: any) {
      setActionLog(`✕ Error de conexión: ${err.message}`);
    } finally {
      setSendingOrder(false);
    }
  };

  // Emergency Controls
  const handleKillSwitch = async (sessionId: string) => {
    const reason = prompt("Motivo del Kill-Switch de emergencia (Hard Stop):", "Manual Emergency DLL Guard");
    if (!reason) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/sessions/${sessionId}/kill-switch`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason }),
      });
      if (res.ok) {
        setActionLog(`🚨 KILL-SWITCH ACTIVADO: ${sessionId} detenido inmediatamente.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error activando kill-switch: ${err.message}`);
    }
  };

  const handleFlatten = async (sessionId: string) => {
    if (!confirm(`¿Confirmas cerrar a mercado todas las posiciones abiertas de ${sessionId}?`)) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/sessions/${sessionId}/flatten`), {
        method: "POST",
      });
      if (res.ok) {
        setActionLog(`🛑 POSICIONES APLANADAS: ${sessionId} cerrado a mercado.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error al aplanar posiciones: ${err.message}`);
    }
  };

  const handlePauseResume = async (sessionId: string, currentStatus: string) => {
    const isPaused = currentStatus === "PAUSED";
    const endpoint = isPaused ? "resume" : "pause";
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/sessions/${sessionId}/${endpoint}`), {
        method: "POST",
      });
      if (res.ok) {
        setActionLog(`✓ Sesión ${sessionId} ${isPaused ? "REANUDADA" : "PAUSADA"}.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error modificando estado: ${err.message}`);
    }
  };

  // Load C# code
  const handleLoadCsBridge = async (symbol: string) => {
    setSelectedCsSymbol(symbol);
    setLoadingCode(true);
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/ninjatrader/bridge/script?symbol=${symbol}&account_id=${remoteAccount}`));
      if (res.ok) {
        const data = await res.json();
        setExportedCode(data.code);
        setExportedFilename(data.filename);
      } else {
        setExportedCode(`// Error generando código C# para ${symbol}`);
      }
    } catch (err: any) {
      setExportedCode(`// Error de conexión: ${err.message}`);
    } finally {
      setLoadingCode(false);
    }
  };

  const handleDownloadCsFile = () => {
    if (!exportedCode) return;
    const blob = new Blob([exportedCode], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = exportedFilename || `UR_Bridge_${selectedCsSymbol}.cs`;
    link.click();
    URL.revokeObjectURL(url);
    setActionLog(`✓ Archivo '${link.download}' descargado. Cópialo a Documents/NinjaTrader 8/bin/Custom/Strategies/ y presiona F5 en NinjaTrader.`);
  };

  // Delete account
  const handleDeleteAccount = async (accId: string) => {
    if (!confirm(`¿Eliminar la cuenta ${accId} de SQLite?`)) return;
    try {
      const res = await fetch(getApiUrl(`/api/v1/execution/ninjatrader/accounts/${encodeURIComponent(accId)}`), {
        method: "DELETE",
      });
      if (res.ok) {
        setActionLog(`✓ Cuenta ${accId} eliminada.`);
        fetchRealData();
      }
    } catch (err: any) {
      setActionLog(`✕ Error al eliminar: ${err.message}`);
    }
  };

  // ATM calculations
  const spec = CME_SPECS[atmSymbol] || CME_SPECS.MNQ;
  const slPoints = atmSlTicks * spec.tickSize;
  const tpPoints = atmTpTicks * spec.tickSize;
  const slUsdPerContract = atmSlTicks * spec.tickValueUsd;
  const tpUsdPerContract = atmTpTicks * spec.tickValueUsd;
  const totalRiskUsd = slUsdPerContract * atmQty;
  const totalRewardUsd = tpUsdPerContract * atmQty;
  const rrRatio = slUsdPerContract > 0 ? tpUsdPerContract / slUsdPerContract : 0;
  const beTriggerTicks = Math.round(atmSlTicks * 1.5);
  const beTriggerPoints = beTriggerTicks * spec.tickSize;
  const maxTradesBeforeDll = totalRiskUsd > 0 ? Math.floor(atmDailyLossLimit / totalRiskUsd) : 0;

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc", fontFamily: "var(--font-sans, system-ui, sans-serif)" }}>
      {/* 1. HEADER & CONTROLS */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/panel" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Motor 24/7
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#10b981", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            NINJATRADER 8 REMOTE TRADING BOT & AUTO-CONNECT
          </span>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
              Centro de Trading Remoto & Conexión NinjaTrader 8
            </h1>
            <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
              Control y ejecución remota bidireccional: opera bots en vivo, despacha órdenes de mercado y supervisa telemetría real desde Ultrarentable.
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
            <Link
              href="/proveedores"
              style={{
                padding: "8px 16px",
                borderRadius: "8px",
                background: "rgba(56, 189, 248, 0.15)",
                color: "#38bdf8",
                border: "1px solid #38bdf8",
                fontWeight: 800,
                fontSize: "12px",
                textDecoration: "none",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              📡 Gateways & Tokens API
            </Link>

            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              style={{
                padding: "8px 14px",
                borderRadius: "8px",
                background: autoRefresh ? "rgba(52, 211, 153, 0.15)" : "rgba(255, 255, 255, 0.05)",
                color: autoRefresh ? "#34d399" : "#94a3b8",
                border: `1px solid ${autoRefresh ? "#34d399" : "rgba(255,255,255,0.1)"}`,
                fontWeight: 800,
                fontSize: "11px",
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {autoRefresh ? "🟢 RADAR ACTIVO 2.5s" : "⏸️ PAUSADO"}
            </button>

            <button
              onClick={fetchRealData}
              style={{
                padding: "8px 14px",
                borderRadius: "8px",
                background: "rgba(255,255,255,0.06)",
                color: "#fff",
                border: "1px solid rgba(255,255,255,0.1)",
                fontWeight: 800,
                fontSize: "11px",
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              🔄 ACTUALIZAR
            </button>
          </div>
        </div>
      </div>

      {/* 2. ACTION LOG */}
      {actionLog && (
        <div style={{ background: "#080c14", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", padding: "12px 16px", marginBottom: "20px", fontSize: "12px", fontFamily: "var(--font-mono, monospace)", color: "#38bdf8", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>{actionLog}</span>
          <button onClick={() => setActionLog(null)} style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: "14px" }}>✕</button>
        </div>
      )}

      {errorMsg && (
        <div style={{ background: "rgba(244, 63, 94, 0.1)", border: "1px solid #f43f5e", borderRadius: "8px", padding: "12px 16px", marginBottom: "20px", fontSize: "12px", color: "#f43f5e" }}>
          {errorMsg}
        </div>
      )}

      {/* 3. NAVIGATION TABS */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "12px", marginBottom: "24px", flexWrap: "wrap" }}>
        <button
          onClick={() => setActiveTab("AUTO_CONNECT")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "AUTO_CONNECT" ? "#10b981" : "transparent",
            color: activeTab === "AUTO_CONNECT" ? "#06080d" : "#94a3b8",
            border: activeTab === "AUTO_CONNECT" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          ⚡ Auto-Conexión & Cuentas ({accounts.length})
        </button>

        <button
          onClick={() => setActiveTab("REMOTE_TERMINAL")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "REMOTE_TERMINAL" ? "#38bdf8" : "transparent",
            color: activeTab === "REMOTE_TERMINAL" ? "#06080d" : "#94a3b8",
            border: activeTab === "REMOTE_TERMINAL" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          🎮 Terminal de Trading Remoto
        </button>

        <button
          onClick={() => setActiveTab("SESSIONS")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "SESSIONS" ? "#38bdf8" : "transparent",
            color: activeTab === "SESSIONS" ? "#06080d" : "#94a3b8",
            border: activeTab === "SESSIONS" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          📈 Sesiones de Ejecución ({sessions.length})
        </button>

        <button
          onClick={() => {
            setActiveTab("CS_BOTS");
            if (!exportedCode) handleLoadCsBridge("MNQ");
          }}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "CS_BOTS" ? "#38bdf8" : "transparent",
            color: activeTab === "CS_BOTS" ? "#06080d" : "#94a3b8",
            border: activeTab === "CS_BOTS" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          🤖 Descargar NinjaScript C# (.cs)
        </button>

        <button
          onClick={() => setActiveTab("ATM_BUILDER")}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: activeTab === "ATM_BUILDER" ? "#38bdf8" : "transparent",
            color: activeTab === "ATM_BUILDER" ? "#06080d" : "#94a3b8",
            border: activeTab === "ATM_BUILDER" ? "none" : "1px solid rgba(255,255,255,0.08)",
            fontWeight: 800,
            fontSize: "12px",
            cursor: "pointer",
          }}
        >
          📐 Calculadora ATM & Riesgo CME
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: AUTO-CONNECT RADAR & REAL ACCOUNTS */}
      {/* ========================================================================= */}
      {activeTab === "AUTO_CONNECT" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* RADAR DE ESCUCHA EN VIVO */}
          <div style={{
            background: "linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(56, 189, 248, 0.08) 100%)",
            border: "1px solid rgba(16, 185, 129, 0.35)",
            borderRadius: "16px",
            padding: "24px",
            display: "grid",
            gridTemplateColumns: "1fr auto",
            alignItems: "center",
            gap: "20px",
          }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 12px #10b981" }} />
                <span style={{ fontSize: "14px", fontWeight: 900, color: "#fff", letterSpacing: "0.5px" }}>
                  RADAR DE AUTO-DESCUBRIMIENTO EN TIEMPO REAL ACTIVO
                </span>
                <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "4px", background: "rgba(16,185,129,0.2)", color: "#34d399", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                  PUERTO 8000 ESCUCHANDO
                </span>
              </div>
              <p style={{ color: "#cbd5e1", fontSize: "13px", margin: 0, lineHeight: "1.5" }}>
                Zero formularios manuales. Descarga el script C#, cópialo a NinjaTrader 8 y activa la estrategia en tu gráfico. En cuanto NinjaTrader transmita, <strong>Ultrarentable detectará tu cuenta (Sim101, Apex, Topstep, Tradovate), leerá su balance real y la conectará automáticamente</strong>.
              </p>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <button
                onClick={() => {
                  if (!exportedCode) handleLoadCsBridge("MNQ");
                  setActiveTab("CS_BOTS");
                }}
                style={{
                  padding: "12px 20px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  color: "#06080d",
                  border: "none",
                  fontWeight: 900,
                  fontSize: "13px",
                  cursor: "pointer",
                  boxShadow: "0 4px 15px rgba(16,185,129,0.3)",
                  whiteSpace: "nowrap",
                }}
              >
                ⬇️ DESCARGAR CONECTOR NINJASCRIPT C#
              </button>
            </div>
          </div>

          {/* INSTRUCCIONES DE CONEXIÓN EN 2 PASOS */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
            <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "18px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#38bdf8", marginBottom: "6px" }}>
                1. Guardar el archivo en NinjaTrader 8
              </div>
              <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0, lineHeight: "1.6" }}>
                Guarda el archivo <code>UR_Bridge_MNQ.cs</code> en: <br />
                <code style={{ color: "#38bdf8", background: "rgba(56,189,248,0.1)", padding: "2px 6px", borderRadius: "4px", fontSize: "11px", display: "block", marginTop: "4px" }}>
                  Documents\NinjaTrader 8\bin\Custom\Strategies\
                </code>
              </p>
            </div>

            <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", padding: "18px" }}>
              <div style={{ fontSize: "13px", fontWeight: 800, color: "#10b981", marginBottom: "6px" }}>
                2. Compilar & Habilitar en Gráfico
              </div>
              <p style={{ fontSize: "12px", color: "#94a3b8", margin: 0, lineHeight: "1.6" }}>
                En NinjaTrader 8: Menú <strong>New $\rightarrow$ NinjaScript Editor</strong>, presiona <strong>F5</strong> para compilar. En el gráfico de MNQ, clic derecho $\rightarrow$ <strong>Strategies</strong> $\rightarrow$ selecciona <code>UR_Bridge_MNQ</code> $\rightarrow$ <strong>Enabled = True</strong>.
              </p>
            </div>
          </div>

          {/* LISTA DE CUENTAS DETECTADAS Y CONECTADAS */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: 0, color: "#fff" }}>
                🏛️ Cuentas NinjaTrader 8 Conectadas en Vivo ({accounts.length})
              </h2>
            </div>

            {loading ? (
              <div style={{ padding: "40px", textAlign: "center", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                Escaneando cuentas reales en SQLite...
              </div>
            ) : accounts.length === 0 ? (
              <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px dashed rgba(56, 189, 248, 0.3)", borderRadius: "14px", padding: "40px", textAlign: "center" }}>
                <div style={{ fontSize: "36px", marginBottom: "12px" }}>📡</div>
                <div style={{ fontSize: "17px", fontWeight: 800, color: "#fff" }}>
                  Esperando Primera Conexión desde NinjaTrader 8...
                </div>
                <p style={{ color: "#94a3b8", fontSize: "13px", maxWidth: "600px", margin: "8px auto 16px auto" }}>
                  No hay cuentas manuales inventadas. En cuanto inicies NinjaTrader 8 y habilites la estrategia, tu cuenta aparecerá aquí automáticamente con su saldo real y métricas en vivo.
                </p>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(480px, 1fr))", gap: "20px" }}>
                {accounts.map((acc) => {
                  const isKill = acc.status === "KILL_SWITCH_TRIGGERED";
                  const isPassed = acc.status === "TARGET_PASSED";

                  return (
                    <div
                      key={acc.account_id}
                      style={{
                        background: "rgba(16, 23, 34, 0.85)",
                        backdropFilter: "blur(16px)",
                        border: `1px solid ${isKill ? "#f43f5e" : isPassed ? "#10b981" : "rgba(16, 185, 129, 0.3)"}`,
                        borderRadius: "14px",
                        padding: "20px",
                        boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <span style={{ fontSize: "16px", fontWeight: 900, color: "#fff", fontFamily: "var(--font-mono, monospace)" }}>
                              {acc.account_id}
                            </span>
                            <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "4px", background: "rgba(16, 185, 129, 0.15)", color: "#34d399", fontWeight: 800 }}>
                              {acc.account_type}
                            </span>
                            <span style={{ fontSize: "10px", padding: "2px 8px", borderRadius: "4px", background: "rgba(255,255,255,0.06)", color: "#cbd5e1", fontWeight: 700 }}>
                              {acc.broker}
                            </span>
                          </div>
                          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
                            {acc.account_name} · Sincronizado: {acc.last_sync_at ? new Date(acc.last_sync_at).toLocaleTimeString() : "Ahora"}
                          </div>
                        </div>

                        <div>
                          {isKill ? (
                            <span style={{ fontSize: "11px", fontWeight: 900, background: "rgba(244, 63, 94, 0.2)", color: "#f43f5e", border: "1px solid #f43f5e", padding: "4px 10px", borderRadius: "6px" }}>
                              🚨 LÍMITE ALCANZADO
                            </span>
                          ) : isPassed ? (
                            <span style={{ fontSize: "11px", fontWeight: 900, background: "rgba(16, 185, 129, 0.2)", color: "#10b981", border: "1px solid #10b981", padding: "4px 10px", borderRadius: "6px" }}>
                              🏆 OBJETIVO ALCANZADO
                            </span>
                          ) : (
                            <span style={{ fontSize: "11px", fontWeight: 900, background: "rgba(16, 185, 129, 0.15)", color: "#10b981", border: "1px solid #10b981", padding: "4px 10px", borderRadius: "6px" }}>
                              🟢 CONECTADA EN VIVO
                            </span>
                          )}
                        </div>
                      </div>

                      {/* METRIC GRID */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", padding: "14px", background: "#06090e", borderRadius: "10px", marginBottom: "16px" }}>
                        <div>
                          <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>EQUIDAD REAL RECIBIDA</div>
                          <div style={{ fontSize: "18px", fontWeight: 900, color: "#fff", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                            ${acc.current_equity_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>PNL HOY (USD)</div>
                          <div style={{ fontSize: "18px", fontWeight: 900, color: acc.daily_pnl_usd >= 0 ? "#34d399" : "#f43f5e", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                            {acc.daily_pnl_usd >= 0 ? `+$${acc.daily_pnl_usd.toFixed(2)}` : `-$${Math.abs(acc.daily_pnl_usd).toFixed(2)}`}
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>COLCHÓN TRAILING DD</div>
                          <div style={{ fontSize: "18px", fontWeight: 900, color: acc.remaining_cushion_usd > 1000 ? "#34d399" : acc.remaining_cushion_usd > 500 ? "#f59e0b" : "#f43f5e", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                            ${acc.remaining_cushion_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                          </div>
                        </div>
                      </div>

                      {/* ACTIONS */}
                      <div style={{ display: "flex", gap: "8px" }}>
                        <button
                          onClick={() => {
                            setRemoteAccount(acc.account_id);
                            setActiveTab("REMOTE_TERMINAL");
                          }}
                          style={{
                            flex: 1,
                            padding: "8px 12px",
                            borderRadius: "6px",
                            background: "linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)",
                            color: "#06080d",
                            border: "none",
                            fontWeight: 900,
                            fontSize: "11px",
                            cursor: "pointer",
                          }}
                        >
                          🎮 Operar en Remoto
                        </button>

                        <button
                          onClick={() => {
                            setActiveTab("CS_BOTS");
                            handleLoadCsBridge("MNQ");
                          }}
                          style={{
                            padding: "8px 12px",
                            borderRadius: "6px",
                            background: "rgba(56, 189, 248, 0.15)",
                            color: "#38bdf8",
                            border: "1px solid #38bdf8",
                            fontWeight: 800,
                            fontSize: "11px",
                            cursor: "pointer",
                          }}
                        >
                          ⬇️ C# (.cs)
                        </button>

                        <button
                          onClick={() => handleDeleteAccount(acc.account_id)}
                          style={{
                            padding: "8px 12px",
                            borderRadius: "6px",
                            background: "rgba(244, 63, 94, 0.15)",
                            color: "#f43f5e",
                            border: "1px solid #f43f5e",
                            fontWeight: 800,
                            fontSize: "11px",
                            cursor: "pointer",
                          }}
                        >
                          🗑️ Desconectar
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: REMOTE TRADING TERMINAL */}
      {/* ========================================================================= */}
      {activeTab === "REMOTE_TERMINAL" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* TERMINAL CONTROLS */}
          <div style={{
            background: "rgba(16, 23, 34, 0.85)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            borderRadius: "16px",
            padding: "24px",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 900, margin: "0 0 6px 0", color: "#fff" }}>
                  🎮 Consola de Trading Remoto NinjaTrader 8
                </h2>
                <p style={{ color: "#94a3b8", fontSize: "12px", margin: 0 }}>
                  Despacha órdenes de compra, venta, aplanado y paradas de emergencia directamente a tu NinjaTrader 8 en tiempo real.
                </p>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>CANAL BIDIRECCIONAL:</span>
                <span style={{ fontSize: "11px", padding: "3px 8px", borderRadius: "4px", background: "rgba(16,185,129,0.15)", color: "#34d399", fontWeight: 800 }}>
                  🟢 POLLING & WEBHOOK LISTO
                </span>
              </div>
            </div>

            {/* SELECTION BAR */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px", marginBottom: "24px" }}>
              <div>
                <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>CUENTA OBJETIVO NINJATRADER</label>
                <select
                  value={remoteAccount}
                  onChange={(e) => setRemoteAccount(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
                >
                  {accounts.length === 0 ? (
                    <option value="Sim101">Sim101 (Local Demo)</option>
                  ) : (
                    accounts.map((a) => (
                      <option key={a.account_id} value={a.account_id}>
                        {a.account_id} ({a.account_type} · ${a.current_equity_usd.toLocaleString()})
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>INSTRUMENTO CME</label>
                <select
                  value={remoteSymbol}
                  onChange={(e) => setRemoteSymbol(e.target.value)}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
                >
                  {Object.keys(CME_SPECS).map((k) => (
                    <option key={k} value={k}>
                      {k} — {CME_SPECS[k].name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>CONTRATOS</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={remoteQty}
                  onChange={(e) => setRemoteQty(Number(e.target.value))}
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
                />
              </div>
            </div>

            {/* ACTION BUTTONS */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
              <button
                onClick={() => handleDispatchRemoteOrder("BUY")}
                disabled={sendingOrder}
                style={{
                  padding: "16px",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  color: "#06080d",
                  border: "none",
                  fontWeight: 900,
                  fontSize: "14px",
                  cursor: sendingOrder ? "not-allowed" : "pointer",
                  boxShadow: "0 4px 20px rgba(16, 185, 129, 0.3)",
                }}
              >
                🟢 COMPRAR A MERCADO ({remoteQty} {remoteSymbol})
              </button>

              <button
                onClick={() => handleDispatchRemoteOrder("SELL")}
                disabled={sendingOrder}
                style={{
                  padding: "16px",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #f43f5e 0%, #be123c 100%)",
                  color: "#fff",
                  border: "none",
                  fontWeight: 900,
                  fontSize: "14px",
                  cursor: sendingOrder ? "not-allowed" : "pointer",
                  boxShadow: "0 4px 20px rgba(244, 63, 94, 0.3)",
                }}
              >
                🔴 VENDER A MERCADO ({remoteQty} {remoteSymbol})
              </button>

              <button
                onClick={() => handleDispatchRemoteOrder("FLATTEN")}
                disabled={sendingOrder}
                style={{
                  padding: "16px",
                  borderRadius: "10px",
                  background: "rgba(245, 158, 11, 0.15)",
                  color: "#f59e0b",
                  border: "1px solid #f59e0b",
                  fontWeight: 900,
                  fontSize: "13px",
                  cursor: sendingOrder ? "not-allowed" : "pointer",
                }}
              >
                🛑 APLANAR (FLATTEN {remoteSymbol})
              </button>

              <button
                onClick={() => handleDispatchRemoteOrder("KILL_SWITCH")}
                disabled={sendingOrder}
                style={{
                  padding: "16px",
                  borderRadius: "10px",
                  background: "rgba(244, 63, 94, 0.15)",
                  color: "#f43f5e",
                  border: "1px solid #f43f5e",
                  fontWeight: 900,
                  fontSize: "13px",
                  cursor: sendingOrder ? "not-allowed" : "pointer",
                }}
              >
                🚨 KILL-SWITCH REMOTO
              </button>
            </div>
          </div>

          {/* RECENT ORDERS TABLE */}
          <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 800, margin: "0 0 16px 0", color: "#fff" }}>
              📋 Historial de Órdenes Remotas Enviadas
            </h3>

            {orderHistory.length === 0 ? (
              <div style={{ padding: "30px", textAlign: "center", color: "#64748b", fontSize: "13px" }}>
                Aún no has despachado órdenes remotas en esta sesión.
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", fontFamily: "var(--font-mono, monospace)" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", textAlign: "left", color: "#64748b" }}>
                      <th style={{ padding: "10px" }}>ID DE ORDEN</th>
                      <th style={{ padding: "10px" }}>ACCIDENTE / ACCIÓN</th>
                      <th style={{ padding: "10px" }}>SÍMBOLO</th>
                      <th style={{ padding: "10px" }}>QTY</th>
                      <th style={{ padding: "10px" }}>CUENTA</th>
                      <th style={{ padding: "10px" }}>ESTADO</th>
                      <th style={{ padding: "10px" }}>HORA (UTC)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orderHistory.map((ord) => (
                      <tr key={ord.order_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                        <td style={{ padding: "10px", color: "#38bdf8" }}>{ord.order_id}</td>
                        <td style={{ padding: "10px", fontWeight: 800, color: ord.action === "BUY" ? "#34d399" : ord.action === "SELL" ? "#f43f5e" : "#f59e0b" }}>
                          {ord.action}
                        </td>
                        <td style={{ padding: "10px", color: "#fff" }}>{ord.symbol}</td>
                        <td style={{ padding: "10px", color: "#fff" }}>{ord.quantity}</td>
                        <td style={{ padding: "10px", color: "#94a3b8" }}>{ord.account_name}</td>
                        <td style={{ padding: "10px" }}>
                          <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: ord.status === "DELIVERED" ? "rgba(16,185,129,0.15)" : "rgba(245,158,11,0.15)", color: ord.status === "DELIVERED" ? "#34d399" : "#f59e0b" }}>
                            {ord.status}
                          </span>
                        </td>
                        <td style={{ padding: "10px", color: "#64748b" }}>
                          {new Date(ord.timestamp_utc).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: SESSIONS */}
      {/* ========================================================================= */}
      {activeTab === "SESSIONS" && (
        <div>
          {loading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              Cargando sesiones reales desde SQLite...
            </div>
          ) : sessions.length === 0 ? (
            <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "40px", textAlign: "center" }}>
              <div style={{ fontSize: "36px", marginBottom: "12px" }}>🛡️</div>
              <div style={{ fontSize: "18px", fontWeight: 800, color: "#fff" }}>
                0 Sesiones de Ejecución Activas en SQLite (Zero Mocks)
              </div>
              <p style={{ color: "#94a3b8", fontSize: "13px", maxWidth: "600px", margin: "8px auto 20px auto" }}>
                En cuanto NinjaTrader 8 envíe una orden o fill real a través del Webhook, aparecerá la sesión de trading aquí automáticamente.
              </p>
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(480px, 1fr))", gap: "16px" }}>
              {sessions.map((s) => {
                const isKillActive = s.kill_switch_active || s.status === "KILL_SWITCH_TRIGGERED";
                const isPaused = s.status === "PAUSED";

                return (
                  <div
                    key={s.session_id}
                    style={{
                      background: "rgba(16, 23, 34, 0.85)",
                      backdropFilter: "blur(16px)",
                      border: `1px solid ${isKillActive ? "#f43f5e" : isPaused ? "#f59e0b" : "rgba(255, 255, 255, 0.08)"}`,
                      borderRadius: "14px",
                      padding: "20px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "14px", fontWeight: 800, color: "#fff", fontFamily: "var(--font-mono, monospace)" }}>
                            {s.session_id}
                          </span>
                          <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: s.route === "FONDEO" ? "rgba(56, 189, 248, 0.15)" : "rgba(168, 85, 247, 0.15)", color: s.route === "FONDEO" ? "#38bdf8" : "#c084fc", fontWeight: 800 }}>
                            {s.route}
                          </span>
                        </div>
                        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                          {s.candidate_id} · {s.symbol}
                        </div>
                      </div>

                      <div>
                        {isKillActive ? (
                          <span style={{ fontSize: "10px", fontWeight: 900, background: "rgba(244, 63, 94, 0.2)", color: "#f43f5e", border: "1px solid #f43f5e", padding: "4px 8px", borderRadius: "6px" }}>
                            🚨 KILL-SWITCH
                          </span>
                        ) : isPaused ? (
                          <span style={{ fontSize: "10px", fontWeight: 900, background: "rgba(245, 158, 11, 0.2)", color: "#f59e0b", border: "1px solid #f59e0b", padding: "4px 8px", borderRadius: "6px" }}>
                            ⏸️ PAUSADO
                          </span>
                        ) : (
                          <span style={{ fontSize: "10px", fontWeight: 900, background: "rgba(52, 211, 153, 0.2)", color: "#34d399", border: "1px solid #34d399", padding: "4px 8px", borderRadius: "6px" }}>
                            🟢 ACTIVO
                          </span>
                        )}
                      </div>
                    </div>

                    {/* METRICS */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", padding: "12px", background: "#06090e", borderRadius: "8px", marginBottom: "12px" }}>
                      <div>
                        <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>PNL HOY (USD)</div>
                        <div style={{ fontSize: "16px", fontWeight: 800, color: s.daily_pnl_usd >= 0 ? "#34d399" : "#f43f5e", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                          {s.daily_pnl_usd >= 0 ? `+$${s.daily_pnl_usd.toFixed(2)}` : `-$${Math.abs(s.daily_pnl_usd).toFixed(2)}`}
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>PEAK EQUITY</div>
                        <div style={{ fontSize: "16px", fontWeight: 800, color: "#fff", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                          ${s.peak_equity_usd?.toLocaleString("en-US", { minimumFractionDigits: 2 })}
                        </div>
                      </div>

                      <div>
                        <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700 }}>DRAWDOWN</div>
                        <div style={{ fontSize: "16px", fontWeight: 800, color: s.current_drawdown_pct > 2.0 ? "#f43f5e" : "#f59e0b", marginTop: "2px", fontFamily: "var(--font-mono, monospace)" }}>
                          {s.current_drawdown_pct?.toFixed(2)}%
                        </div>
                      </div>
                    </div>

                    {/* TELEMETRY LOGS */}
                    <div style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)", lineHeight: "1.6", marginBottom: "16px" }}>
                      <div><strong>Señal:</strong> {s.last_signal || "Sin señal reciente"}</div>
                      <div><strong>Orden:</strong> {s.last_order || "Sin orden reciente"}</div>
                    </div>

                    {/* ACTION BUTTONS */}
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        onClick={() => handlePauseResume(s.session_id, s.status)}
                        style={{
                          flex: 1,
                          padding: "6px 12px",
                          borderRadius: "6px",
                          background: isPaused ? "rgba(52, 211, 153, 0.15)" : "rgba(245, 158, 11, 0.15)",
                          color: isPaused ? "#34d399" : "#f59e0b",
                          border: `1px solid ${isPaused ? "#34d399" : "#f59e0b"}`,
                          fontWeight: 800,
                          fontSize: "11px",
                          cursor: "pointer",
                        }}
                      >
                        {isPaused ? "▶️ Reanudar" : "⏸️ Pausar"}
                      </button>

                      <button
                        onClick={() => handleFlatten(s.session_id)}
                        style={{
                          flex: 1,
                          padding: "6px 12px",
                          borderRadius: "6px",
                          background: "rgba(245, 158, 11, 0.15)",
                          color: "#f59e0b",
                          border: "1px solid #f59e0b",
                          fontWeight: 800,
                          fontSize: "11px",
                          cursor: "pointer",
                        }}
                      >
                        🛑 Aplanar (Flatten)
                      </button>

                      <button
                        onClick={() => handleKillSwitch(s.session_id)}
                        disabled={isKillActive}
                        style={{
                          flex: 1,
                          padding: "6px 12px",
                          borderRadius: "6px",
                          background: isKillActive ? "rgba(100, 116, 139, 0.2)" : "rgba(244, 63, 94, 0.2)",
                          color: isKillActive ? "#64748b" : "#f43f5e",
                          border: `1px solid ${isKillActive ? "#64748b" : "#f43f5e"}`,
                          fontWeight: 900,
                          fontSize: "11px",
                          cursor: isKillActive ? "not-allowed" : "pointer",
                        }}
                      >
                        🚨 Kill-Switch
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: C# STRATEGY EXPORTER */}
      {/* ========================================================================= */}
      {activeTab === "CS_BOTS" && (
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
            <div>
              <h2 style={{ fontSize: "18px", fontWeight: 800, margin: "0 0 8px 0", color: "#fff" }}>
                🤖 Generador y Descargador NinjaScript C# (NinjaTrader 8)
              </h2>
              <p style={{ color: "#94a3b8", fontSize: "12px", margin: 0 }}>
                Código C# nativo con puente bidireccional: recibe órdenes remotas desde Ultrarentable, envía telemetría de fills en tiempo real y ejecuta guardas duras de DLL y Trailing DD.
              </p>
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                onClick={handleDownloadCsFile}
                disabled={!exportedCode || loadingCode}
                style={{
                  padding: "10px 18px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
                  color: "#fff",
                  border: "none",
                  fontWeight: 900,
                  fontSize: "12px",
                  cursor: !exportedCode ? "not-allowed" : "pointer",
                  boxShadow: "0 2px 12px rgba(16,185,129,0.3)",
                }}
              >
                ⬇️ DESCARGAR ARCHIVO .CS
              </button>

              {exportedCode && (
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(exportedCode);
                    setActionLog("✓ Código C# copiado al portapapeles.");
                  }}
                  style={{
                    padding: "10px 18px",
                    borderRadius: "8px",
                    background: "#38bdf8",
                    color: "#06080d",
                    border: "none",
                    fontWeight: 800,
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  📋 COPIAR CÓDIGO
                </button>
              )}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 3fr", gap: "20px" }}>
            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#cbd5e1", marginBottom: "8px" }}>
                Selecciona Instrumento CME:
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {Object.keys(CME_SPECS).map((sym) => (
                  <button
                    key={sym}
                    onClick={() => handleLoadCsBridge(sym)}
                    style={{
                      padding: "10px 14px",
                      borderRadius: "8px",
                      background: selectedCsSymbol === sym ? "rgba(56, 189, 248, 0.15)" : "rgba(255,255,255,0.03)",
                      border: `1px solid ${selectedCsSymbol === sym ? "#38bdf8" : "rgba(255,255,255,0.06)"}`,
                      textAlign: "left",
                      color: selectedCsSymbol === sym ? "#38bdf8" : "#fff",
                      cursor: "pointer",
                      fontWeight: selectedCsSymbol === sym ? 800 : 500,
                    }}
                  >
                    <div style={{ fontSize: "13px" }}>{sym} — {CME_SPECS[sym].name}</div>
                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>
                      SL: {CME_SPECS[sym].defaultSlTicks}t · TP: {CME_SPECS[sym].defaultTpTicks}t · BE: +{CME_SPECS[sym].defaultBeTicks}t
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#cbd5e1", marginBottom: "8px" }}>
                Vista Previa del Código C# ({exportedFilename || `UR_Bridge_${selectedCsSymbol}.cs`}):
              </div>

              <pre
                style={{
                  background: "#04070c",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "8px",
                  padding: "16px",
                  fontSize: "11px",
                  fontFamily: "var(--font-mono, monospace)",
                  color: "#38bdf8",
                  height: "460px",
                  overflowY: "auto",
                  margin: 0,
                }}
              >
                {loadingCode ? "// Generando código C# compilable para NinjaTrader 8..." : exportedCode || "// Haz clic en un instrumento a la izquierda para generar el código."}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: ATM CALCULATOR */}
      {/* ========================================================================= */}
      {activeTab === "ATM_BUILDER" && (
        <div style={{ background: "rgba(16, 23, 34, 0.75)", backdropFilter: "blur(16px)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "24px" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 800, margin: "0 0 8px 0", color: "#fff" }}>
            📐 Calculadora Matemática de Parámetros ATM CME
          </h2>
          <p style={{ color: "#94a3b8", fontSize: "12px", margin: "0 0 20px 0" }}>
            Cálculo determinista de riesgo, múltiplos R y disparadores de Break-Even según las especificaciones del exchange CME.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "24px" }}>
            <div>
              <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>INSTRUMENTO CME</label>
              <select
                value={atmSymbol}
                onChange={(e) => setAtmSymbol(e.target.value)}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
              >
                {Object.keys(CME_SPECS).map((k) => (
                  <option key={k} value={k}>
                    {k} — {CME_SPECS[k].name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>CONTRATOS</label>
              <input
                type="number"
                min="1"
                max="20"
                value={atmQty}
                onChange={(e) => setAtmQty(Number(e.target.value))}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>STOP LOSS (TICKS)</label>
              <input
                type="number"
                min="4"
                max="500"
                value={atmSlTicks}
                onChange={(e) => setAtmSlTicks(Number(e.target.value))}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>TAKE PROFIT (TICKS)</label>
              <input
                type="number"
                min="4"
                max="1000"
                value={atmTpTicks}
                onChange={(e) => setAtmTpTicks(Number(e.target.value))}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
              />
            </div>

            <div>
              <label style={{ fontSize: "11px", color: "#64748b", fontWeight: 700, display: "block", marginBottom: "4px" }}>LÍMITE PÉRDIDA DIARIA (USD)</label>
              <input
                type="number"
                value={atmDailyLossLimit}
                onChange={(e) => setAtmDailyLossLimit(Number(e.target.value))}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", background: "#06090e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: "13px" }}
              />
            </div>
          </div>

          {/* CALCULATED RESULTS */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "16px" }}>
            <div style={{ background: "#080c14", border: "1px solid rgba(244, 63, 94, 0.3)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "11px", color: "#f43f5e", fontWeight: 700 }}>RIESGO STOP LOSS</div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#f43f5e", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                ${totalRiskUsd.toFixed(2)} USD
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
                {atmSlTicks} ticks = {slPoints.toFixed(2)} pts (${slUsdPerContract.toFixed(2)}/ctr)
              </div>
            </div>

            <div style={{ background: "#080c14", border: "1px solid rgba(52, 211, 153, 0.3)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 700 }}>BENEFICIO TAKE PROFIT</div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#34d399", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                +${totalRewardUsd.toFixed(2)} USD
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
                {atmTpTicks} ticks = {tpPoints.toFixed(2)} pts (${tpUsdPerContract.toFixed(2)}/ctr) · <strong>Ratio 1:{rrRatio.toFixed(1)}</strong>
              </div>
            </div>

            <div style={{ background: "#080c14", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 700 }}>DISPARADOR BREAK-EVEN (+1.5R)</div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#38bdf8", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                +{beTriggerTicks} Ticks (+{beTriggerPoints.toFixed(2)} pts)
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
                Alcanzado $+{(totalRiskUsd * 1.5).toFixed(2)} flotante $\rightarrow$ SL a Entrada + 2 ticks
              </div>
            </div>

            <div style={{ background: "#080c14", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>COLCHÓN MÁXIMO DE TRADES/DÍA</div>
              <div style={{ fontSize: "20px", fontWeight: 900, color: "#fff", marginTop: "4px", fontFamily: "var(--font-mono, monospace)" }}>
                {maxTradesBeforeDll} Stops Consecutivos
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
                Antes de tocar el límite de pérdida diaria (${atmDailyLossLimit})
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
