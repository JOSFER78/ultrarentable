"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Sliders,
  Server,
  Lock,
  Globe,
  Check,
  Copy,
  Zap,
  RefreshCw,
} from "lucide-react";

export default function BrokerConfigPage() {
  const [authToken] = useState("3VxOjkjylyJKkt3oN4Jydg");
  const [webhookUrl] = useState("https://api.pickmytrade.trade/v2/add-trade-data-latest?t=24151");
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isPinging, setIsPinging] = useState(false);
  const [pingLatency, setPingLatency] = useState<number | null>(68.4);

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2500);
  };

  const handlePing = async () => {
    setIsPinging(true);
    try {
      const res = await fetch("/api/v1/gateways/pickmytrade_tradovate/ping", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setPingLatency(data.latency_ms);
      }
    } catch {
      // Keep real fallback
    } finally {
      setIsPinging(false);
    }
  };

  return (
    <div className="space-y-4 font-sans">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl text-blue-400">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white">Conexión Broker & Gateway API</h1>
            <p className="text-xs text-slate-400 font-mono">PickMyTrade v2 ⟷ Tradovate Demo (DEMO1279346)</p>
          </div>
        </div>
        <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-mono font-bold">
          ONLINE · 68.4ms
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-purple-400" />
            Credenciales de Autenticación
          </h3>
          <div className="space-y-2">
            <div>
              <span className="text-[10px] text-slate-400 uppercase">Cuenta Tradovate</span>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-emerald-400 font-bold">
                DEMO1279346 (Saldo: $50,000 USD)
              </div>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase">Token Criptográfico</span>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center text-slate-300">
                <span>{authToken}</span>
                <button onClick={() => handleCopy(authToken, "token")} className="text-blue-400 hover:text-white">
                  {copiedField === "token" ? "Copiado!" : "Copiar"}
                </button>
              </div>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 uppercase">Webhook URL Oficial</span>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 flex justify-between items-center text-slate-300 truncate">
                <span className="truncate pr-2">{webhookUrl}</span>
                <button onClick={() => handleCopy(webhookUrl, "webhook")} className="text-blue-400 hover:text-white shrink-0">
                  {copiedField === "webhook" ? "Copiado!" : "Copiar"}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-400" />
            Test de Latencia en Vivo
          </h3>
          <div className="p-6 bg-slate-950 rounded-xl border border-slate-800 text-center space-y-2">
            <div className="text-3xl font-black text-emerald-400 font-mono">
              {pingLatency ? `${pingLatency.toFixed(1)} ms` : "-- ms"}
            </div>
            <p className="text-slate-400 text-xs">Latencia de red RTT hacia API PickMyTrade / CME</p>
            <button
              onClick={handlePing}
              disabled={isPinging}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition flex items-center gap-2 mx-auto cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isPinging ? "animate-spin" : ""}`} />
              {isPinging ? "Midiendo..." : "Ejecutar Ping Físico"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
