"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertCircle,
  RefreshCw,
  Award,
  Layers,
  Hash,
  FileCheck,
} from "lucide-react";
import { getCertifiedStrategies, CertifiedStrategy, GateVerificationDetail } from "@/lib/api";

interface GateDisplayItem {
  id: string;
  label: string;
  pass: boolean;
  hasEvidence: boolean;
  val: string;
}

export default function GatesPage() {
  const [certifiedList, setCertifiedList] = useState<CertifiedStrategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<CertifiedStrategy | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadCertified();
  }, []);

  async function loadCertified() {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await getCertifiedStrategies();
      setCertifiedList(data);
      if (data.length > 0 && !selectedStrategy) {
        setSelectedStrategy(data[0]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al cargar estrategias certificadas.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  }

  // Resolución forense de compuertas sin hardcodes
  const resolveGateItem = (
    gateId: string,
    defaultLabel: string,
    strategy: CertifiedStrategy,
    fallbackMetric?: () => { pass: boolean; val: string } | null
  ): GateDisplayItem => {
    const gates = strategy.gates || {};
    const num = gateId.replace(/\D/g, "");
    
    // Búsqueda determinista por múltiples claves canónicas posibles
    const gateData: GateVerificationDetail | undefined =
      gates[gateId] ||
      gates[gateId.toLowerCase()] ||
      gates[num] ||
      gates[`gate_${num}`] ||
      gates[`gate_${num.padStart(2, "0")}`] ||
      gates[`gate-${num}`] ||
      gates[`G${num}`] ||
      Object.values(gates).find(
        (g) => g.gate_id === gateId || g.gate_id === num || g.name?.toLowerCase().includes(defaultLabel.toLowerCase())
      );

    if (gateData) {
      const pass = Boolean(gateData.passed);
      const val =
        gateData.observed_value !== undefined && gateData.observed_value !== null && String(gateData.observed_value).trim() !== ""
          ? String(gateData.observed_value)
          : gateData.details || (pass ? "APROBADO" : "RECHAZADO");
      return {
        id: gateId,
        label: gateData.name || defaultLabel,
        pass,
        hasEvidence: true,
        val,
      };
    }

    // Evaluación fallback únicamente con métricas físicas certificadas existentes
    if (fallbackMetric) {
      const res = fallbackMetric();
      if (res !== null) {
        return {
          id: gateId,
          label: defaultLabel,
          pass: res.pass,
          hasEvidence: true,
          val: res.val,
        };
      }
    }

    // ZERO MOCKS: Si no hay evidencia en backend, reportar SIN DATOS / NO EVIDENCE
    return {
      id: gateId,
      label: defaultLabel,
      pass: false,
      hasEvidence: false,
      val: "SIN DATOS / NO EVIDENCE",
    };
  };

  const getGateChecklist = (strategy: CertifiedStrategy): GateDisplayItem[] => {
    return [
      resolveGateItem("G1", "Mínimo de Operaciones (N >= 30)", strategy, () =>
        strategy.total_trades !== undefined && strategy.total_trades !== null
          ? { pass: strategy.total_trades >= 30, val: `${strategy.total_trades} trades` }
          : null
      ),
      resolveGateItem("G2", "Profit Factor In-Sample (PF >= 1.30)", strategy, () =>
        strategy.profit_factor !== undefined && strategy.profit_factor !== null
          ? { pass: strategy.profit_factor >= 1.3, val: `PF ${strategy.profit_factor.toFixed(2)}` }
          : null
      ),
      resolveGateItem("G3", "Max Drawdown Total (DD <= 25%)", strategy, () =>
        strategy.max_drawdown_pct !== undefined && strategy.max_drawdown_pct !== null
          ? { pass: strategy.max_drawdown_pct <= 25, val: `${strategy.max_drawdown_pct.toFixed(1)}%` }
          : null
      ),
      resolveGateItem("G4", "Win Rate Mínimo (WR >= 40%)", strategy, () =>
        strategy.win_rate_pct !== undefined && strategy.win_rate_pct !== null
          ? { pass: strategy.win_rate_pct >= 40, val: `${strategy.win_rate_pct.toFixed(1)}%` }
          : null
      ),
      resolveGateItem("G5", "Sharpe Ratio (SR >= 1.0)", strategy, () =>
        strategy.sharpe_ratio !== undefined && strategy.sharpe_ratio !== null
          ? { pass: strategy.sharpe_ratio >= 1.0, val: `SR ${strategy.sharpe_ratio.toFixed(2)}` }
          : null
      ),
      resolveGateItem("G6", "Consistencia OOS (PF_OOS >= 1.15)", strategy, () =>
        strategy.oos_profit_factor !== undefined && strategy.oos_profit_factor !== null
          ? { pass: strategy.oos_profit_factor >= 1.15, val: `PF ${strategy.oos_profit_factor.toFixed(2)}` }
          : null
      ),
      // G7 a G10: Eliminados todos los pases fijos. Consumo estricto de selectedStrategy.gates
      resolveGateItem("G7", "Monte Carlo 95% Confianza (DD <= 30%)", strategy),
      resolveGateItem("G8", "Matriz de Sensibilidad de Parámetros", strategy),
      resolveGateItem("G9", "Robustez Multi-Mercado", strategy),
      resolveGateItem("G10", "Resistencia a Slippage/Costes (2x)", strategy),
      resolveGateItem("G11", "Bloqueo de Versión de Motor (v5.3.0)", strategy, () =>
        strategy.engine_version
          ? { pass: strategy.engine_version === "5.3.0", val: `v${strategy.engine_version}` }
          : null
      ),
    ];
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header Banner */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Award className="w-7 h-7 text-emerald-400" />
              <h1 className="text-2xl font-bold tracking-tight">Página 5: Pipeline 10 Gates — Estrategias Certificadas (10/10)</h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Registro canónico de estrategias que superan el 100% de compuertas bajo el motor v5.3.0. Evidencia Merkle inmutable.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-300 border border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5 mr-1" />
              APPROVED_CURRENT_ENGINE
            </span>
            <button
              onClick={loadCertified}
              disabled={loading}
              className="inline-flex items-center px-3 py-1.5 rounded-md text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              Actualizar
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-950/70 border border-rose-800 text-rose-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-sm">Error de Carga de Estrategias Certificadas:</p>
              <p className="text-xs text-rose-300 mt-0.5">{errorMsg}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Certified List */}
          <div className="lg:col-span-1 bg-slate-900/80 rounded-xl border border-slate-800 p-4 space-y-4">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Layers className="w-4 h-4 text-emerald-400" />
              Estrategias Certificadas ({certifiedList.length})
            </h2>

            {loading ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-500" />
                Validando certificación física contra SQLite WAL...
              </div>
            ) : certifiedList.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm">
                No hay estrategias certificadas bajo la versión actual (v5.3.0).
              </div>
            ) : (
              <div className="space-y-2 max-h-[650px] overflow-y-auto pr-1">
                {certifiedList.map((st) => {
                  const isSelected = selectedStrategy?.strategy_id === st.strategy_id;
                  return (
                    <button
                      key={st.strategy_id}
                      onClick={() => setSelectedStrategy(st)}
                      className={`w-full text-left p-3 rounded-lg border transition ${
                        isSelected
                          ? "bg-emerald-950/50 border-emerald-500/80 text-white shadow-sm"
                          : "bg-slate-950/50 border-slate-800 hover:border-slate-700 text-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-emerald-300 truncate">{st.name || st.strategy_id}</span>
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                          {st.symbol} · {st.timeframe}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 mt-2 text-xs">
                        <div>
                          <span className="text-slate-500 block">PF Total</span>
                          <span className="font-semibold text-emerald-400">
                            {st.profit_factor ? st.profit_factor.toFixed(2) : "N/A"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">Sharpe</span>
                          <span className="font-semibold text-slate-200">
                            {st.sharpe_ratio ? st.sharpe_ratio.toFixed(2) : "N/A"}
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-500 block">PF OOS</span>
                          <span className="font-semibold text-emerald-400">
                            {st.oos_profit_factor ? st.oos_profit_factor.toFixed(2) : "N/A"}
                          </span>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column: Gate Details & Provenance Certificate */}
          <div className="lg:col-span-2 space-y-6">
            {selectedStrategy ? (
              <>
                {/* Strategy Summary Card */}
                <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <h3 className="font-bold text-slate-100 text-base">{selectedStrategy.name || selectedStrategy.strategy_id}</h3>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Activo: <span className="text-slate-200 font-semibold">{selectedStrategy.symbol}</span> | Temporalidad:{" "}
                        <span className="text-slate-200 font-semibold">{selectedStrategy.timeframe}</span> | Familia:{" "}
                        <span className="text-slate-200 font-semibold">{selectedStrategy.family}</span>
                      </p>
                    </div>
                    <span className="px-2.5 py-1 rounded bg-emerald-950/80 border border-emerald-700 text-emerald-300 text-xs font-mono font-semibold self-start sm:self-auto">
                      {selectedStrategy.status}
                    </span>
                  </div>

                  {/* Certified Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">PF OOS Real</span>
                      <span className="text-lg font-bold text-emerald-400">
                        {selectedStrategy.oos_profit_factor ? selectedStrategy.oos_profit_factor.toFixed(2) : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">Sharpe Ratio</span>
                      <span className="text-lg font-bold text-indigo-300">
                        {selectedStrategy.sharpe_ratio ? selectedStrategy.sharpe_ratio.toFixed(2) : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">Duración OOS Físico</span>
                      <span className="text-lg font-bold text-slate-100 font-mono">
                        {selectedStrategy.oos_months !== null && selectedStrategy.oos_months !== undefined
                          ? `${selectedStrategy.oos_months.toFixed(2)} meses`
                          : "N/A"}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400 block">Retorno Anual Real</span>
                      <span className="text-lg font-bold text-slate-100 font-mono">
                        {selectedStrategy.annual_return !== null && selectedStrategy.annual_return !== undefined
                          ? `${(selectedStrategy.annual_return * 100).toFixed(2)}%`
                          : "N/A"}
                      </span>
                    </div>
                  </div>

                  {/* 11 Gates Checklist Matrix */}
                  <div className="space-y-3 pt-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <FileCheck className="w-4 h-4 text-emerald-400" />
                      Matriz de Validación 11 Gates (Doctrina Forense)
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                      {getGateChecklist(selectedStrategy).map((g) => (
                        <div
                          key={g.id}
                          className={`flex items-center justify-between p-2.5 rounded border transition ${
                            !g.hasEvidence
                              ? "bg-slate-950/40 border-amber-900/40"
                              : g.pass
                              ? "bg-slate-950/60 border-slate-800"
                              : "bg-rose-950/20 border-rose-900/50"
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            {!g.hasEvidence ? (
                              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                            ) : g.pass ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                            ) : (
                              <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                            )}
                            <span className="text-slate-300 font-medium truncate">
                              <span className="text-indigo-400 font-mono font-bold mr-1">[{g.id}]</span>
                              {g.label}
                            </span>
                          </div>
                          <span
                            className={`font-mono text-[11px] ml-2 flex-shrink-0 ${
                              !g.hasEvidence
                                ? "text-amber-400 font-semibold"
                                : g.pass
                                ? "text-slate-400"
                                : "text-rose-400 font-semibold"
                            }`}
                          >
                            {g.val}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Cryptographic Hashes & Ledger Verification */}
                  <div className="p-3.5 bg-slate-950/90 rounded-lg border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                        <Hash className="w-3.5 h-3.5 text-emerald-400" />
                        Certificado Criptográfico & Provenance Lock
                      </span>
                      <span className="text-[11px] text-emerald-400 font-mono flex items-center gap-1">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        Ledger Verificado
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] font-mono text-slate-400">
                      <div className="truncate">
                        <span className="text-slate-500">Strategy Hash: </span>
                        <span className="text-slate-300">{selectedStrategy.strategy_hash || "N/A"}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">Ledger Hash: </span>
                        <span className="text-indigo-300">{selectedStrategy.ledger_hash || "N/A"}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">Dataset Hash: </span>
                        <span className="text-slate-300">{selectedStrategy.dataset_hash || "N/A"}</span>
                      </div>
                      <div className="truncate">
                        <span className="text-slate-500">Evidence Bundle: </span>
                        <span className="text-slate-300">{selectedStrategy.evidence_bundle_hash || "N/A"}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="py-20 text-center text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
                Selecciona una estrategia certificada de la lista para ver su matriz de validación y procedencia forense.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
