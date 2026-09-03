"use client";

import React, { useState } from "react";
import {
  Layers,
  ShieldCheck,
  Award,
  DollarSign,
  TrendingDown,
  CheckCircle2,
  XCircle,
  ExternalLink,
  ChevronRight,
  Filter,
} from "lucide-react";

interface FirmMetric {
  id: string;
  name: string;
  badge: string;
  cost50k: string;
  drawdownModel: "EOD Trailing" | "Intraday Peak" | "100% Estático";
  ddAmount50k: string;
  activationFee: string;
  payoutSpeed: string;
  botPolicy: "Permitido 100%" | "Manual / No Bots" | "Restringido";
  consistencyRule: string;
  tradesferaRating: number;
}

const TRADESFERA_FIRMS: FirmMetric[] = [
  {
    id: "tradeify",
    name: "Tradeify",
    badge: "RECOMENDADA M08",
    cost50k: "$49 (Cupón)",
    drawdownModel: "EOD Trailing",
    ddAmount50k: "$2,000",
    activationFee: "$0 (Sin cuota)",
    payoutSpeed: "Día 1 / Bajo demanda",
    botPolicy: "Permitido 100%",
    consistencyRule: "Sin regla de consistencia",
    tradesferaRating: 9.8,
  },
  {
    id: "mffu",
    name: "MyFundedFutures (MFFU)",
    badge: "LÍDER RETIROS",
    cost50k: "$38.50 (Promo)",
    drawdownModel: "EOD Trailing",
    ddAmount50k: "$2,000",
    activationFee: "$139 (Starter)",
    payoutSpeed: "Cada 14 días / On demand",
    botPolicy: "Permitido 100%",
    consistencyRule: "Regla 40% en Rapid",
    tradesferaRating: 9.6,
  },
  {
    id: "tradeday",
    name: "TradeDay",
    badge: "FCM REGULADO",
    cost50k: "$99/mes",
    drawdownModel: "EOD Trailing",
    ddAmount50k: "$2,000",
    activationFee: "$0 (Incluida)",
    payoutSpeed: "Mismo día hábil (Dorman)",
    botPolicy: "Permitido 100%",
    consistencyRule: "Libre de consistencia",
    tradesferaRating: 9.5,
  },
  {
    id: "topstep",
    name: "Topstep",
    badge: "INSTITUCIONAL",
    cost50k: "$49/mes",
    drawdownModel: "EOD Trailing",
    ddAmount50k: "$2,000",
    activationFee: "$149",
    payoutSpeed: "Diario tras buffer",
    botPolicy: "Manual / No Bots",
    consistencyRule: "Regla 50% en funded",
    tradesferaRating: 9.2,
  },
  {
    id: "blusky",
    name: "BluSky Trading",
    badge: "DRAWDOWN ESTÁTICO",
    cost50k: "$85/mes",
    drawdownModel: "100% Estático",
    ddAmount50k: "$2,000 Fijo",
    activationFee: "$0",
    payoutSpeed: "Semanal",
    botPolicy: "Permitido 100%",
    consistencyRule: "Sin trailing que persiga",
    tradesferaRating: 9.3,
  },
  {
    id: "apex",
    name: "Apex Trader Funding",
    badge: "VOLUMEN MASIVO",
    cost50k: "$33 (80% OFF)",
    drawdownModel: "Intraday Peak",
    ddAmount50k: "$2,500",
    activationFee: "$85",
    payoutSpeed: "2 veces al mes",
    botPolicy: "Restringido",
    consistencyRule: "Regla 30% estricta",
    tradesferaRating: 8.4,
  },
];

export default function ComparativaPropFirmsPage() {
  const [filterModel, setFilterModel] = useState<string>("TODAS");

  const filtered = TRADESFERA_FIRMS.filter((f) => {
    if (filterModel === "TODAS") return true;
    return f.drawdownModel === filterModel;
  });

  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)] font-sans">
      {/* Header Banner */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--profit)]">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text-1)] flex items-center gap-2">
              <span>Comparativa de Prop Firms de Futuros CME</span>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
                MÓDULO M08
              </span>
            </h1>
            <p className="text-xs text-[var(--text-2)] font-mono">
              Auditoría cuantitativa de modelos de drawdown, costes reales de extracción y políticas de bots (2026).
            </p>
          </div>
        </div>
      </div>

      {/* Filtros de Modelo de Drawdown */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3">
        <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-2)]">
          <Filter className="w-3.5 h-3.5 text-[var(--profit)]" />
          <span>Filtrar por Modelo de Drawdown:</span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-xs">
          {["TODAS", "EOD Trailing", "100% Estático", "Intraday Peak"].map((model) => (
            <button
              key={model}
              onClick={() => setFilterModel(model)}
              className={`px-2.5 py-1 rounded-md border transition cursor-pointer ${
                filterModel === model
                  ? "bg-[var(--surface-2)] border-[var(--profit)] text-[var(--text-1)] font-bold"
                  : "bg-[var(--surface-1)] border-[var(--border)] text-[var(--text-3)] hover:text-[var(--text-2)]"
              }`}
            >
              {model}
            </button>
          ))}
        </div>
      </div>

      {/* Tabla Comparativa Maestra */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden font-mono text-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--surface-2)] border-b border-[var(--border)] text-[11px] text-[var(--text-3)] uppercase">
                <th className="p-3">Firma</th>
                <th className="p-3">Drawdown</th>
                <th className="p-3">Examen 50K</th>
                <th className="p-3">Cuota Activación</th>
                <th className="p-3">Velocidad Pago</th>
                <th className="p-3">Bots / EAs</th>
                <th className="p-3">Consistencia</th>
                <th className="p-3 text-right">Rating M08</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {filtered.map((firm) => (
                <tr key={firm.id} className="hover:bg-[var(--surface-2)] transition">
                  <td className="p-3 font-sans">
                    <div className="font-bold text-[var(--text-1)]">{firm.name}</div>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[var(--profit)] border border-[var(--border)]">
                      {firm.badge}
                    </span>
                  </td>
                  <td className="p-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] ${
                        firm.drawdownModel === "100% Estático"
                          ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                          : firm.drawdownModel === "EOD Trailing"
                          ? "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)]"
                          : "bg-[var(--surface-2)] text-[var(--loss)] border border-[var(--border)]"
                      }`}
                    >
                      {firm.drawdownModel}
                    </span>
                    <div className="text-[10px] text-[var(--text-3)] mt-0.5">{firm.ddAmount50k}</div>
                  </td>
                  <td className="p-3 text-[var(--text-1)] font-bold">{firm.cost50k}</td>
                  <td className="p-3 text-[var(--text-2)]">{firm.activationFee}</td>
                  <td className="p-3 text-[var(--text-1)]">{firm.payoutSpeed}</td>
                  <td className="p-3">
                    <span
                      className={`inline-flex items-center gap-1 ${
                        firm.botPolicy === "Permitido 100%"
                          ? "text-[var(--profit)]"
                          : firm.botPolicy === "Restringido"
                          ? "text-[var(--text-3)]"
                          : "text-[var(--loss)]"
                      }`}
                    >
                      {firm.botPolicy === "Permitido 100%" ? (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5" />
                      )}
                      <span>{firm.botPolicy}</span>
                    </span>
                  </td>
                  <td className="p-3 text-[var(--text-3)]">{firm.consistencyRule}</td>
                  <td className="p-3 text-right">
                    <span className="text-sm font-bold text-[var(--profit)]">{firm.tradesferaRating}</span>
                    <span className="text-[10px] text-[var(--text-3)]">/10</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
