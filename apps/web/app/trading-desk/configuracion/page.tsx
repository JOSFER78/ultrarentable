"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Sliders,
  Lock,
  Zap,
  RefreshCw,
  Copy,
  Check,
  ShieldCheck,
  Radio,
  Server,
  AlertCircle,
  Clock,
  User,
  Key,
  ExternalLink,
  ChevronRight,
  Wifi,
  WifiOff,
  Save,
  LogIn,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "@/components/auth/AuthModal";

interface GatewayStatus {
  provider_id?: string;
  account_id?: string;
  user?: string;
  broker?: string;
  environment?: string;
  base_capital_usd?: number | null;
  current_equity_usd?: number | null;
  daily_pnl_usd?: number | null;
  trailing_drawdown_limit_usd?: number | null;
  current_drawdown_usd?: number | null;
  open_positions_count?: number;
  trial_expires_utc?: string | null;
  gateway_status?: string;
  last_ping_latency_ms?: number | null;
}

interface GatewayProvider {
  provider_id: string;
  name: string;
  category: string;
  auth_token: string;
  endpoint_url: string;
  is_enabled: boolean;
  status: string;
  latency_ms: number;
  telemetry_packets_count: number;
  last_ping_at: string | null;
}

export default function BrokerConfigPage() {
  const { user, profile, loading: authLoading, updateUserProfile } = useAuth();

  const [gatewayData, setGatewayData] = useState<GatewayStatus | null>(null);
  const [gatewaysList, setGatewaysList] = useState<GatewayProvider[]>([]);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isPingingAll, setIsPingingAll] = useState(false);
  const [pingingProviderId, setPingingProviderId] = useState<string | null>(null);
  const [pingLatency, setPingLatency] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ text: string; isError: boolean } | null>(null);

  // Form State for Firestore Account Settings
  const [tradovateAccountId, setTradovateAccountId] = useState<string>("");
  const [ninjaTraderAccountId, setNinjaTraderAccountId] = useState<string>("");
  const [pickmytradeToken, setPickmytradeToken] = useState<string>("");
  const [gatewayWebhookToken, setGatewayWebhookToken] = useState<string>("");
  const [broker, setBroker] = useState<string>("Tradovate");
  const [environment, setEnvironment] = useState<"DEMO" | "LIVE">("DEMO");
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  // Auth modal
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  const showToast = (text: string, isError = false) => {
    setNotification({ text, isError });
    setTimeout(() => setNotification(null), 5000);
  };

  // Populate form with real user profile data from Firestore
  useEffect(() => {
    if (profile) {
      const accounts = profile.trading_accounts || profile.broker_accounts || {};
      setTradovateAccountId(accounts.tradovate_account_id || "");
      setNinjaTraderAccountId(accounts.ninjatrader_account_id || "");
      setPickmytradeToken(accounts.pickmytrade_token || "");
      setGatewayWebhookToken(accounts.gateway_webhook_token || "");
      setBroker(accounts.broker || "Tradovate");
      setEnvironment((accounts.environment as "DEMO" | "LIVE") || "DEMO");
    } else if (!user) {
      setTradovateAccountId("");
      setNinjaTraderAccountId("");
      setPickmytradeToken("");
      setGatewayWebhookToken("");
    }
  }, [profile, user]);

  const fetchStatus = useCallback(async () => {
    setFetchError(null);
    try {
      const [statusRes, listRes] = await Promise.all([
        fetch("/api/v1/gateways/pickmytrade/status"),
        fetch("/api/v1/gateways"),
      ]);

      if (statusRes.ok) {
        const data = await statusRes.json();
        setGatewayData(data);
        if (data.last_ping_latency_ms != null) {
          setPingLatency(data.last_ping_latency_ms);
        }
      } else {
        setGatewayData(null);
        setFetchError(`Error ${statusRes.status}: No se pudo obtener el estado del gateway PickMyTrade.`);
      }

      if (listRes.ok) {
        const listData = await listRes.json();
        setGatewaysList(Array.isArray(listData) ? listData : []);
      }
    } catch (e: any) {
      setGatewayData(null);
      setFetchError(e.message || "Error de red al conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2500);
  };

  const handleSaveFirestoreConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setIsAuthModalOpen(true);
      return;
    }

    setIsSaving(true);
    setSaveSuccess(false);

    try {
      const accountsPayload = {
        tradovate_account_id: tradovateAccountId.trim(),
        ninjatrader_account_id: ninjaTraderAccountId.trim(),
        pickmytrade_token: pickmytradeToken.trim(),
        gateway_webhook_token: gatewayWebhookToken.trim(),
        broker: broker,
        environment: environment,
        updated_at: new Date().toISOString(),
      };

      await updateUserProfile({
        trading_accounts: accountsPayload,
        broker_accounts: accountsPayload,
      });

      setSaveSuccess(true);
      showToast("✅ Credenciales de trading guardadas y sincronizadas en Firestore (users/" + user.uid + ")");
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err: any) {
      showToast("❌ Error al guardar en Firestore: " + err.message, true);
    } finally {
      setIsSaving(false);
    }
  };

  const handlePingProvider = async (providerId: string) => {
    setPingingProviderId(providerId);
    try {
      const res = await fetch(`/api/v1/gateways/${providerId}/ping`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (providerId === "pickmytrade_tradovate") {
          setPingLatency(data.latency_ms);
        }
        showToast(`✅ Ping a ${providerId}: ${data.latency_ms} ms · Estado: ${data.status}`);
        fetchStatus();
      } else {
        showToast(`⚠️ Ping a ${providerId} devolvió estado ${res.status}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error al ejecutar ping en ${providerId}: ${err.message}`, true);
    } finally {
      setPingingProviderId(null);
    }
  };

  const handlePingAll = async () => {
    setIsPingingAll(true);
    try {
      const res = await fetch("/api/v1/gateways/ping-all", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        showToast(`✅ Diagnóstico global completado: ${data.gateways_count} gateways diagnosticados (Latencia Media: ${data.avg_latency_ms} ms).`);
        fetchStatus();
      } else {
        showToast(`⚠️ Error en ping global: ${res.status}`, true);
      }
    } catch (err: any) {
      showToast(`❌ Error al ejecutar ping global: ${err.message}`, true);
    } finally {
      setIsPingingAll(false);
    }
  };

  const activeAccountId =
    tradovateAccountId.trim() ||
    ninjaTraderAccountId.trim() ||
    gatewayData?.account_id ||
    "";
  const hasLinkedAccount = Boolean(activeAccountId);
  const isConnected = (gatewayData?.gateway_status === "CONNECTED" || gatewayData?.gateway_status === "IDLE_WAITING") && hasLinkedAccount;

  return (
    <div className="space-y-4 font-sans">
      {/* HEADER BAR */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">Conexión Gateway & Brokers CME</h1>
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
                FIRESTORE REAL-ONLY
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Configuración Cifrada de Cuentas Tradovate, NinjaTrader y PickMyTrade API v2
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 w-full md:w-auto font-mono">
          <span
            className={`px-3 py-1.5 rounded-xl text-xs font-bold border flex items-center gap-2 ${
              isConnected
                ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                : "bg-rose-500/20 text-rose-400 border-rose-500/30"
            }`}
          >
            {isConnected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span className="tabular-nums">ONLINE · {pingLatency != null ? `${pingLatency.toFixed(1)} ms` : "OK"}</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>{hasLinkedAccount ? "GATEWAY DESCONECTADO" : "SIN CUENTA VINCULADA"}</span>
              </>
            )}
          </span>

          <button
            onClick={fetchStatus}
            className="p-2 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-300 border border-white/[0.1] transition cursor-pointer"
            title="Refrescar estado"
          >
            <RefreshCw className="w-4 h-4" />
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
          {notification.isError ? <AlertTriangle className="w-4 h-4 text-rose-400" /> : <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
          {notification.text}
        </div>
      )}

      {/* AUTHENTICATION STATE PROMPT */}
      {!user && !authLoading && (
        <div className="p-4 bg-blue-950/40 border border-blue-500/40 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono text-blue-200 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-blue-500/20 text-blue-400">
              <User className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">Sesión no iniciada</div>
              <p className="text-[11px] text-blue-300/80 font-sans mt-0.5">
                Inicia sesión con tu cuenta para guardar y persistir de forma segura tus Account IDs y tokens en tu documento Firestore.
              </p>
            </div>
          </div>
          <button
            onClick={() => setIsAuthModalOpen(true)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition flex items-center gap-2 cursor-pointer shadow-lg shadow-blue-900/40 shrink-0"
          >
            <LogIn className="w-4 h-4" />
            Acceder / Registro
          </button>
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
            Reintentar Conexión
          </button>
        </div>
      )}

      {/* 2-COLUMN GRID: FIRESTORE INPUTS & LIVE GATEWAY TELEMETRY */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* LEFT COLUMN: REAL FIRESTORE ACCOUNT CONFIGURATION FORM (7 COLS) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <Key className="w-5 h-5 text-emerald-400" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  Credenciales de Cuenta en Firestore
                </h2>
              </div>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                {user ? `UID: ${user.uid.slice(0, 8)}...` : "SIN SESIÓN"}
              </span>
            </div>

            <form onSubmit={handleSaveFirestoreConfig} className="space-y-4 font-mono text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Broker / Plataforma
                  </label>
                  <select
                    value={broker}
                    onChange={(e) => setBroker(e.target.value)}
                    className="w-full bg-[#050811] border border-white/[0.1] rounded-xl px-3 py-2.5 text-white font-bold focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Tradovate">Tradovate (CME Futures)</option>
                    <option value="NinjaTrader">NinjaTrader 8 (CME Futures)</option>
                    <option value="PickMyTrade">PickMyTrade Multi-Gateway</option>
                    <option value="BingX">BingX (Perpetual Swaps)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Entorno de Ejecución
                  </label>
                  <select
                    value={environment}
                    onChange={(e) => setEnvironment(e.target.value as "DEMO" | "LIVE")}
                    className="w-full bg-[#050811] border border-white/[0.1] rounded-xl px-3 py-2.5 text-white font-bold focus:outline-none focus:border-emerald-500"
                  >
                    <option value="DEMO">DEMO / Simulación Real</option>
                    <option value="LIVE">LIVE / Cuenta Real Financiada</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Tradovate Account ID (ej. DEMO1234567 o real)
                </label>
                <input
                  type="text"
                  placeholder="Introduce tu ID de cuenta Tradovate..."
                  value={tradovateAccountId}
                  onChange={(e) => setTradovateAccountId(e.target.value)}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl px-3.5 py-2.5 text-emerald-400 font-bold placeholder:text-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  NinjaTrader 8 Account ID (opcional)
                </label>
                <input
                  type="text"
                  placeholder="ej. Sim101 / NT-Real-..."
                  value={ninjaTraderAccountId}
                  onChange={(e) => setNinjaTraderAccountId(e.target.value)}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl px-3.5 py-2.5 text-slate-200 font-bold placeholder:text-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  PickMyTrade Token / API Key
                </label>
                <input
                  type="text"
                  placeholder="Introduce tu token privado de PickMyTrade API v2..."
                  value={pickmytradeToken}
                  onChange={(e) => setPickmytradeToken(e.target.value)}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl px-3.5 py-2.5 text-cyan-400 font-bold placeholder:text-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Gateway Webhook Token (opcional)
                </label>
                <input
                  type="text"
                  placeholder="Token de autenticación para webhooks entrantes..."
                  value={gatewayWebhookToken}
                  onChange={(e) => setGatewayWebhookToken(e.target.value)}
                  className="w-full bg-[#050811] border border-white/[0.1] rounded-xl px-3.5 py-2.5 text-slate-300 font-bold placeholder:text-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-between border-t border-white/[0.08]">
                <div className="text-[11px] text-slate-400">
                  {saveSuccess && (
                    <span className="text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Sincronizado en Firestore
                    </span>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition flex items-center gap-2 cursor-pointer shadow-lg shadow-emerald-900/40 active:scale-95"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? "Guardando en Firestore..." : "Guardar en Firestore"}
                </button>
              </div>
            </form>
          </div>

          {/* WEBHOOK ENDPOINT INSTRUCTION CARD */}
          <div className="p-4 bg-[#050811] rounded-2xl border border-white/[0.08] space-y-2 font-mono text-xs">
            <div className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
              <Lock className="w-3.5 h-3.5 text-purple-400" />
              Endpoint Webhook Oficial PickMyTrade API v2
            </div>
            <div className="flex items-center justify-between bg-[#090d16] p-2.5 rounded-xl border border-white/[0.08] text-slate-300">
              <span className="truncate font-mono">https://api.pickmytrade.trade/v2/add-trade-data-latest?t=24151</span>
              <button
                onClick={() => handleCopy("https://api.pickmytrade.trade/v2/add-trade-data-latest?t=24151", "webhook")}
                className="ml-2 p-1.5 rounded-lg bg-[#050811] border border-white/[0.08] text-slate-400 hover:text-white transition cursor-pointer"
                title="Copiar endpoint"
              >
                {copiedField === "webhook" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: LIVE STATUS & DIAGNOSTICS (5 COLS) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
              <div className="flex items-center gap-2">
                <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
                <h2 className="text-base font-bold text-white tracking-tight">
                  Estado Real de la Cuenta
                </h2>
              </div>
              <span
                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                  hasLinkedAccount
                    ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                    : "bg-amber-500/20 text-amber-400 border-amber-500/30"
                }`}
              >
                {hasLinkedAccount ? "CUENTA CONFIGURADA" : "SIN CUENTA VINCULADA"}
              </span>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {/* Account ID & User */}
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase">Cuenta Activa:</span>
                  <strong className="text-emerald-400 text-sm">
                    {activeAccountId || "SIN VINCULAR"}
                  </strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase">Operador:</span>
                  <span className="text-slate-200">
                    {user?.email || profile?.displayName || "NO AUTENTICADO"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase">Broker / Entorno:</span>
                  <span className="text-slate-300">
                    {broker} ({environment})
                  </span>
                </div>
              </div>

              {/* Financial Metrics */}
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase">Saldo Base:</span>
                  <span className="font-bold text-white tabular-nums">
                    {gatewayData?.base_capital_usd != null
                      ? `$${gatewayData.base_capital_usd.toLocaleString("en-US", { minimumFractionDigits: 2 })} USD`
                      : "SIN DATOS"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase">Trailing DD Límite:</span>
                  <span className="font-bold text-emerald-400 tabular-nums">
                    {gatewayData?.trailing_drawdown_limit_usd != null
                      ? `$${gatewayData.trailing_drawdown_limit_usd.toFixed(2)} USD`
                      : "SIN DATOS"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-slate-400 uppercase">Vencimiento Trial:</span>
                  <span className="text-amber-400">
                    {gatewayData?.trial_expires_utc ?? "NO EVIDENCE"}
                  </span>
                </div>
              </div>

              {/* Latency & Ping Button */}
              <div className="p-3.5 bg-[#050811] rounded-xl border border-white/[0.08] text-center space-y-2">
                <div className="text-[10px] text-slate-400 uppercase">Latencia Física RTT</div>
                <div className="text-2xl font-black text-emerald-400 font-mono tabular-nums">
                  {pingLatency != null ? `${pingLatency.toFixed(1)} ms` : "SIN DATOS"}
                </div>
                <button
                  onClick={() => handlePingProvider("pickmytrade_tradovate")}
                  disabled={pingingProviderId === "pickmytrade_tradovate"}
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-bold transition flex items-center justify-center gap-2 cursor-pointer active:scale-95"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${pingingProviderId === "pickmytrade_tradovate" ? "animate-spin" : ""}`} />
                  {pingingProviderId === "pickmytrade_tradovate" ? "Probando..." : "Test de Conexión Ping"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECONDARY REGISTERED GATEWAYS & BRIDGES */}
      <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white tracking-tight">
              Ecosistema de Gateways Registrados ({gatewaysList.length})
            </h2>
          </div>
          <button
            onClick={handlePingAll}
            disabled={isPingingAll}
            className="px-3 py-1.5 rounded-xl bg-[#050811] hover:bg-slate-800 text-slate-200 border border-white/[0.1] text-xs font-mono font-bold transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPingingAll ? "animate-spin text-emerald-400" : ""}`} />
            {isPingingAll ? "Diagnosticando..." : "Diagnóstico Ping Global"}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
          {gatewaysList.map((gw) => {
            const isGwActive = gw.provider_id === "pickmytrade_tradovate";
            const isGwPinging = pingingProviderId === gw.provider_id;

            return (
              <div
                key={gw.provider_id}
                className={`p-4 rounded-xl border space-y-2.5 flex flex-col justify-between transition-all ${
                  isGwActive
                    ? "bg-[#050811] border-emerald-500/40 ring-1 ring-emerald-500/20"
                    : "bg-[#050811] border-white/[0.08] hover:border-white/[0.16]"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                      {gw.category}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${
                        gw.status === "CONNECTED"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : gw.status === "IDLE_WAITING"
                          ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                          : "bg-slate-800 text-slate-400 border-white/[0.08]"
                      }`}
                    >
                      {gw.status}
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-white truncate">{gw.name}</h3>
                  <p className="text-[10px] text-slate-400 truncate mt-0.5">
                    ID: <strong className="text-slate-300">{gw.provider_id}</strong>
                  </p>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-white/[0.08] text-[10px]">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Latencia RTT:</span>
                    <span className="text-emerald-400 font-bold tabular-nums">
                      {gw.latency_ms > 0 ? `${gw.latency_ms.toFixed(1)} ms` : "-- ms"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Estado Auth:</span>
                    <span className="text-slate-300 font-mono">
                      {hasLinkedAccount && isGwActive ? "CONFIGURADO" : gw.auth_token ? "PROV_KEY" : "SIN TOKEN"}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handlePingProvider(gw.provider_id)}
                  disabled={isGwPinging}
                  className="w-full py-1.5 rounded-lg text-[11px] font-bold bg-[#090d16] hover:bg-slate-800 text-slate-200 border border-white/[0.08] transition flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                >
                  <RefreshCw className={`w-3 h-3 ${isGwPinging ? "animate-spin text-emerald-400" : ""}`} />
                  {isGwPinging ? "Midiendo..." : "Probar Ping"}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Global Auth Modal if needed */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialTab="login"
      />
    </div>
  );
}
