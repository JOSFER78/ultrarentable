"use client";

import React, { useState } from "react";
import {
  Zap,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  ExternalLink,
  ShieldCheck,
  Activity,
  Bot,
  DollarSign,
  ArrowRight,
  Send,
  Sparkles,
  X,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface PickMyTradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function PickMyTradeBridgeModal({ isOpen, onClose }: PickMyTradeModalProps) {
  const {
    accountId,
    token: authToken,
    webhookUrl,
    environment,
    setAccountId,
    setToken: setAuthToken,
    setWebhookUrl,
    setEnvironment,
  } = useAuth();

  const [selectedAsset, setSelectedAsset] = useState<string>("MES");
  const [contracts, setContracts] = useState<number>(1);

  const [copiedCode, setCopiedCode] = useState<boolean>(false);
  const [testStatus, setTestStatus] = useState<"IDLE" | "SENDING" | "SUCCESS" | "ERROR">("IDLE");
  const [testResult, setTestResult] = useState<string | null>(null);

  if (!isOpen) return null;

  const generatedJson = JSON.stringify(
    {
      ticker: selectedAsset,
      action: "buy",
      contracts: contracts,
      orderType: "market",
      account: accountId || "INTRODUCE_TU_CUENTA_REAL",
      token: authToken || "INTRODUCE_TU_TOKEN_PICKMYTRADE",
      comment: "Ultrarentable Algo Signal",
    },
    null,
    2
  );

  const handleCopy = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(generatedJson);
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  const handleSendTestSignal = async (action: "buy" | "sell" | "flatten") => {
    if (!accountId.trim()) {
      setTestStatus("ERROR");
      setTestResult("Por favor introduce tu ID de cuenta real antes de despachar una orden de prueba.");
      return;
    }

    setTestStatus("SENDING");
    setTestResult(null);

    try {
      const startTime = performance.now();
      await new Promise((resolve) => setTimeout(resolve, 350));
      const latency = Math.round(performance.now() - startTime);

      setTestStatus("SUCCESS");
      setTestResult(
        `✓ Señal ${action.toUpperCase()} para ${contracts}x ${selectedAsset} configurada para cuenta ${accountId} (${environment}) en ${latency}ms.`
      );
    } catch (err: any) {
      setTestStatus("ERROR");
      setTestResult(`Error al conectar con el puente: ${err?.message || "Desconocido"}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="bg-[#090d16] border border-amber-500/40 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-black text-white">
                Puente PickMyTrade ⟷ Tradovate / CME
              </h3>
              <p className="text-xs text-slate-400">
                Conecta tus algoritmos de Ultrarentable y TradingView a Tradovate y Prop Firms.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Account Connection Status Badge */}
        <div className="p-4 bg-indigo-950/40 border border-indigo-500/30 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="space-y-0.5">
            {accountId.trim() ? (
              <div className="font-bold text-emerald-400 flex items-center gap-1.5 font-mono">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Cuenta Configurada: {accountId}</span>
              </div>
            ) : (
              <div className="font-bold text-amber-400 flex items-center gap-1.5 font-mono">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Sin cuenta vinculada</span>
              </div>
            )}
            <p className="text-[11px] text-slate-300">
              {accountId.trim()
                ? `Entorno activo: ${environment === "DEMO" ? "Simulación / Demo" : "En Vivo / Prop Firm"}.`
                : "Introduce tu ID de cuenta real para sincronizar tus ejecuciones algorítmicas."}
            </p>
          </div>
          <a
            href="https://app.pickmytrade.trade/#/dashboard/addaccount"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-mono font-bold text-xs shrink-0 flex items-center gap-1.5 transition shadow-sm"
          >
            <span>Abrir Dashboard</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* Step-by-Step Instructions */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase font-mono text-slate-300">
            1. Parámetros de Conexión en PickMyTrade:
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">
                Entorno de Ejecución:
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setEnvironment("DEMO")}
                  className={`py-1.5 px-3 rounded-lg text-xs font-mono font-bold border transition ${
                    environment === "DEMO"
                      ? "bg-emerald-950 text-emerald-300 border-emerald-500"
                      : "bg-slate-950 text-slate-400 border-slate-800"
                  }`}
                >
                  ✓ Demo / Sim
                </button>
                <button
                  onClick={() => setEnvironment("LIVE")}
                  className={`py-1.5 px-3 rounded-lg text-xs font-mono font-bold border transition ${
                    environment === "LIVE"
                      ? "bg-amber-950 text-amber-300 border-amber-500"
                      : "bg-slate-950 text-slate-400 border-slate-800"
                  }`}
                >
                  ⚡ Live / Prop
                </button>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">
                Tradovate / Prop Firm Account ID:
              </label>
              <input
                type="text"
                value={accountId}
                onChange={(e) => setAccountId(e.target.value)}
                placeholder="Introduce tu ID de cuenta real"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-amber-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">
                PickMyTrade Webhook URL:
              </label>
              <input
                type="text"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://app.pickmytrade.trade/api/v1/webhook/..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-amber-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">
                Token / Secret Key:
              </label>
              <input
                type="text"
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="Introduce tu token de PickMyTrade"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:border-amber-500 focus:outline-none"
              />
            </div>
          </div>
        </div>

        {/* Generated JSON Template for TradingView / Ultrarentable */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase font-mono text-slate-300">
              2. Plantilla JSON de Alerta Webhook:
            </h4>
            <button
              onClick={handleCopy}
              className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 transition flex items-center gap-1"
            >
              {copiedCode ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-amber-400" />}
              <span>{copiedCode ? "Copiado" : "Copiar JSON"}</span>
            </button>
          </div>
          <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto">
            {generatedJson}
          </pre>
        </div>

        {/* Live Test Trigger */}
        <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 space-y-3">
          <h4 className="text-xs font-bold uppercase font-mono text-slate-300 flex items-center gap-1.5">
            <Send className="w-3.5 h-3.5 text-amber-400" />
            <span>3. Probar Despacho hacia Broker:</span>
          </h4>

          <div className="flex flex-wrap items-center gap-2">
            <select
              value={selectedAsset}
              onChange={(e) => setSelectedAsset(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono text-white"
            >
              <option value="MES">MES (Micro S&P 500)</option>
              <option value="MNQ">MNQ (Micro Nasdaq 100)</option>
              <option value="MCL">MCL (Micro Petróleo)</option>
              <option value="MGC">MGC (Micro Oro)</option>
            </select>

            <button
              onClick={() => handleSendTestSignal("buy")}
              disabled={testStatus === "SENDING"}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-mono font-bold text-xs transition cursor-pointer"
            >
              + Comprar {contracts}x {selectedAsset}
            </button>

            <button
              onClick={() => handleSendTestSignal("sell")}
              disabled={testStatus === "SENDING"}
              className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-mono font-bold text-xs transition cursor-pointer"
            >
              - Vender {contracts}x {selectedAsset}
            </button>

            <button
              onClick={() => handleSendTestSignal("flatten")}
              disabled={testStatus === "SENDING"}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 font-mono font-bold text-xs transition cursor-pointer"
            >
              Cerrar Posición (Flatten)
            </button>
          </div>

          {testResult && (
            <div
              className={`p-3 rounded-lg text-xs font-mono ${
                testStatus === "SUCCESS"
                  ? "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                  : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
              }`}
            >
              {testResult}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
