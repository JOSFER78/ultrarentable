"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  RefreshCw,
  ChevronRight,
  ShieldCheck,
  Zap,
  Cpu,
  Bot,
  Sliders,
  Activity,
  Download,
  CheckCircle2,
  AlertTriangle,
  Send,
  Sparkles,
} from "lucide-react";
import QuantTooltip from "@/components/system/QuantTooltip";

interface GateParam {
  label: string;
  value: any;
  unit?: string;
  type: "number" | "boolean" | "select";
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
  desc: string;
}

interface GateDetail {
  gate_number: number;
  slug: string;
  name: string;
  short_title: string;
  category: string;
  badge: string;
  icon: string;
  formula: string;
  objective: string;
  description: string;
  params: Record<string, GateParam>;
  live_telemetry: {
    status: string;
    status_color: string;
    datasets_audited: number;
    candles_verified: number;
    pass_rate_pct: number;
    avg_latency_ms: number;
    last_verdict: string;
  };
  firebase_sync_status: string;
  firebase_path: string;
  local_persistence: string;
}

export const ALL_GATES = [
  { num: 1, slug: "gate-1-data-ingest", name: "1. Data Ingest", icon: "💾", badge: "Integridad" },
  { num: 2, slug: "gate-2-cost-backtest", name: "2. Costes & Fricción", icon: "💸", badge: "Costes Reales" },
  { num: 3, slug: "gate-3-trade-significance", name: "3. Muestra Estadística", icon: "📊", badge: "N >= 20" },
  { num: 4, slug: "gate-4-walk-forward", name: "4. Walk-Forward (WFE)", icon: "🔄", badge: "Anti-Overfit" },
  { num: 5, slug: "gate-5-monte-carlo", name: "5. Monte Carlo 1,000x", icon: "🎲", badge: "Ruina 0.0%" },
  { num: 6, slug: "gate-6-stress-slippage", name: "6. Estrés & Slippage", icon: "⚡", badge: "3x Fricción" },
  { num: 7, slug: "gate-7-regime-coverage", name: "7. Cobertura Regímenes", icon: "🌐", badge: "Multi-Ciclo" },
  { num: 8, slug: "gate-8-dsr-ratio", name: "8. Deflated Sharpe (DSR)", icon: "📐", badge: "López de Prado" },
  { num: 9, slug: "gate-9-novelty-antifit", name: "9. Novedad & AST", icon: "🧬", badge: "DoF >= 10" },
  { num: 10, slug: "gate-10-debate-agentes", name: "10. Debate Multi-Agente", icon: "🤖", badge: "Comité Semántico" },
  { num: 11, slug: "gate-11-nautilus-event", name: "11. NautilusCore Engine", icon: "🛡️", badge: "Event-Driven" },
];

export default function GateDetailClient() {
  const params = useParams();
  const router = useRouter();
  const rawSlug = (params?.slug as string) || "gate-1-data-ingest";

  const [gate, setGate] = useState<GateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentParams, setCurrentParams] = useState<Record<string, any>>({});
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // AI Semantic Agent Chat State
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiChatLog, setAiChatLog] = useState<
    Array<{ role: "user" | "assistant"; text: string; time: string; syncInfo?: string }>
  >([
    {
      role: "assistant",
      text: `Hola. Soy el Agente Arquitecto Cuantitativo para este Gate. Puedes darme directivas en lenguaje natural (ej. "Ajustar para Fondeo estricto", "Aumentar exigencia de estrés a 3x", "Bajar tolerancia de gaps") y reconfiguraré el motor determinista y la persistencia al instante.`,
      time: new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  // Nautilus Backtest View State
  const [candidates, setCandidates] = useState<any[]>([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>("");
  const [nautilusReport, setNautilusReport] = useState<any | null>(null);
  const [nautilusLoading, setNautilusLoading] = useState(false);

  // Load Gate Data
  const fetchGateData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/gates/${rawSlug}`);
      if (!res.ok) throw new Error(`Gate no encontrado: ${rawSlug}`);
      const data = await res.json();

      const paramKeys = Object.keys(data.params || data.default_params || {});
      const normalizedParams: Record<string, GateParam> = {};
      const initialForm: Record<string, any> = {};

      paramKeys.forEach((k) => {
        const rawVal = data.params?.[k] !== undefined ? data.params[k] : data.default_params?.[k] ?? "";
        const isNum = typeof rawVal === "number";
        const isBool = typeof rawVal === "boolean";

        normalizedParams[k] = {
          label: k.replace(/_/g, " ").toUpperCase(),
          value: rawVal,
          type: isBool ? "boolean" : isNum ? "number" : "select",
          desc: `Parámetro de validación: ${k}`,
          min: isNum ? 0 : undefined,
          max: isNum ? Math.max(100, (rawVal as number) * 3) : undefined,
          step: isNum ? ((rawVal as number) < 1 ? 0.05 : 1) : undefined,
        };
        initialForm[k] = rawVal;
      });

      const normalizedGate: GateDetail = {
        gate_number: data.id ?? data.gate_number ?? 1,
        slug: data.slug || rawSlug,
        name: data.name || rawSlug,
        short_title: data.name || rawSlug,
        category: data.category || "Validation Gate",
        badge: data.badge || `GATE ${data.id ?? 1}`,
        icon: data.icon || "🛡️",
        formula: data.formula || "Verificación determinista en motor canónico",
        objective: data.objective || data.description || "Auditoría cuantitativa de evidencia.",
        description: data.description || "Compuerta de validación matemática.",
        params: normalizedParams,
        live_telemetry: data.live_telemetry || {
          status: data.evidence_status || "NO_EVIDENCE",
          status_color: "var(--text-2)",
          datasets_audited: data.datasets_audited ?? 0,
          candles_verified: data.candles_verified ?? 0,
          pass_rate_pct: data.pass_rate_pct ?? 0,
          avg_latency_ms: data.avg_latency_ms ?? 0,
          last_verdict: data.evidence_status === "NO_EVIDENCE" ? "NO EVIDENCE" : data.last_verdict || "NO EVIDENCE",
        },
        firebase_sync_status: data.cloud_sync_status || "NOT_CONFIGURED",
        firebase_path: data.firebase_path || `contracts/gates/${data.slug || rawSlug}`,
        local_persistence: data.local_persistence || "SQLite WAL",
      };

      setGate(normalizedGate);
      setCurrentParams(initialForm);
    } catch (err: any) {
      setError(err.message || "Error al cargar la fase cuantitativa");
    } finally {
      setLoading(false);
    }
  }, [rawSlug]);

  const isNautilusSlug = rawSlug === "gate-11-nautilus-event" || rawSlug === "gate-10-nautilus-trader";

  const fetchCandidatesForNautilus = useCallback(async () => {
    if (!isNautilusSlug) return;
    try {
      const res = await fetch("/api/v1/candidates?limit=100");
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setCandidates(data);
          setSelectedCandidateId(data[0].candidate_id);
        }
      }
    } catch (e) {
      console.error("Error loading candidates for Nautilus:", e);
    }
  }, [isNautilusSlug]);

  const fetchNautilusBacktest = useCallback(
    async (cId: string) => {
      if (!cId || !isNautilusSlug) return;
      try {
        setNautilusLoading(true);
        const res = await fetch(`/api/v1/gates/nautilus/detailed-backtest/${cId}`);
        if (res.ok) {
          const data = await res.json();
          setNautilusReport(data);
        }
      } catch (e) {
        console.error("Error loading Nautilus report:", e);
      } finally {
        setNautilusLoading(false);
      }
    },
    [isNautilusSlug]
  );

  useEffect(() => {
    fetchGateData();
    fetchCandidatesForNautilus();
  }, [fetchGateData, fetchCandidatesForNautilus]);

  useEffect(() => {
    if (selectedCandidateId) {
      fetchNautilusBacktest(selectedCandidateId);
    }
  }, [selectedCandidateId, fetchNautilusBacktest]);

  const handleSaveParams = async () => {
    try {
      setSaveStatus("Guardando en Motor & Firebase...");
      const res = await fetch(`/api/v1/gates/${rawSlug}/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ params: currentParams, source: "UI_MANUAL_SLIDER" }),
      });
      if (!res.ok) throw new Error("Error al guardar parámetros");
      const resData = await res.json();
      setSaveStatus(`✅ Guardado en SQLite WAL y Firebase (${resData.firebase_sync?.project || "pecemi"})`);
      setTimeout(() => setSaveStatus(null), 4000);
      fetchGateData();
    } catch (e: any) {
      setSaveStatus(`❌ Error: ${e.message || e}`);
    }
  };

  const handleAiSemanticSubmit = async (promptToSend?: string) => {
    const text = promptToSend || aiPrompt;
    if (!text.trim() || aiLoading) return;

    const userMsg = {
      role: "user" as const,
      text,
      time: new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }),
    };
    setAiChatLog((prev) => [...prev, userMsg]);
    setAiPrompt("");
    setAiLoading(true);

    try {
      const res = await fetch(`/api/v1/gates/${rawSlug}/ai-semantic-edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg = {
          role: "assistant" as const,
          text: `⚡ ${data.explanation}\n\n⚙️ Parámetros Modificados:\n${Object.entries(data.applied_changes || {})
            .map(([k, v]) => `• ${k}: ${v}`)
            .join("\n")}`,
          time: new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }),
          syncInfo: `☁️ Firebase Synced (${data.firebase_cloud_sync?.project || "pecemi"}) · 💾 SQLite WAL`,
        };
        setAiChatLog((prev) => [...prev, assistantMsg]);
        fetchGateData();
      } else {
        throw new Error("El motor no pudo procesar la directiva");
      }
    } catch (e: any) {
      const errorMsg = {
        role: "assistant" as const,
        text: `⚠️ No se pudo aplicar la mutación: ${e.message || e}`,
        time: new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }),
      };
      setAiChatLog((prev) => [...prev, errorMsg]);
    } finally {
      setAiLoading(false);
    }
  };

  if (loading && !gate) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] p-8 font-sans text-[var(--text-1)]">
        <div className="text-center font-mono">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-[var(--text-2)]" />
          <div className="text-sm font-bold text-[var(--text-2)]">Cargando especificación matemática del Gate...</div>
        </div>
      </div>
    );
  }

  if (error || !gate) {
    return (
      <div className="min-h-screen bg-[var(--bg)] p-8 font-sans text-[var(--text-1)]">
        <div className="mx-auto max-w-xl rounded-2xl border border-[var(--loss)] bg-[var(--loss-dim)] p-6 shadow-2xl">
          <h2 className="mb-2 text-lg font-black text-[var(--loss)]">Error al cargar Gate</h2>
          <p className="text-xs text-[var(--loss)]">{error || "El gate solicitado no existe."}</p>
          <Link
            href="/gates"
            className="mt-4 inline-block rounded-xl bg-[var(--surface-3)] border border-[var(--border-strong)] px-4 py-2 text-xs font-bold text-[var(--text-1)] transition hover:bg-[var(--surface-2)]"
          >
            ← Volver a Matriz 11 Gates
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] p-3 md:p-6 font-sans text-[var(--text-1)]">
      <div className="mx-auto max-w-[1600px] space-y-5">
        {/* BREADCRUMB & TOP LINKS */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3 font-mono text-xs">
          <div className="flex items-center gap-2 text-[var(--text-3)]">
            <Link href="/" className="transition hover:text-[var(--text-1)]">
              Inicio
            </Link>
            <ChevronRight className="w-3 h-3" />
            <Link href="/gates" className="transition hover:text-[var(--text-1)]">
              11 Gates
            </Link>
            <ChevronRight className="w-3 h-3" />
            <span className="font-bold text-[var(--text-2)]">{gate.slug}</span>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href="/gates"
              className="rounded-xl border border-white/[0.08] bg-[var(--surface-1)] px-3 py-1.5 font-bold text-[var(--text-1)] transition hover:border-[var(--border)] hover:bg-[var(--surface-1)]"
            >
              ← Ver Matriz 11 Gates
            </Link>
            <Link
              href="/estrategias/2-explorador-excel"
              className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3 py-1.5 font-bold text-[var(--text-1)] transition hover:bg-[var(--surface-2)]"
            >
              Explorador Excel →
            </Link>
          </div>
        </div>

        {/* SELECTOR HORIZONTAL DE LOS 11 GATES */}
        <div className="rounded-2xl border border-white/[0.08] bg-[var(--surface-1)] p-3 shadow-xl backdrop-blur-xl">
          <div className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-[var(--text-3)] flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--text-2)]" />
            <span>Navegador de Fases Cuantitativas (11 Slugs Independientes):</span>
          </div>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-11 gap-1.5">
            {ALL_GATES.map((g) => {
              const isActive = g.slug === rawSlug;
              return (
                <Link
                  key={g.slug}
                  href={`/gates/${g.slug}`}
                  className={`flex flex-col items-center justify-center rounded-xl p-2 text-center transition-all ${
                    isActive
                      ? "border border-[var(--border)] bg-[var(--surface-1)]   text-[var(--text-1)] shadow-[0_0_15px_rgba(255,255,255,0.06)] ring-1 ring-[var(--border-strong)]"
                      : "border border-white/[0.06] bg-[var(--bg)] text-[var(--text-2)] hover:border-[var(--border)] hover:bg-[var(--surface-1)] hover:text-[var(--text-1)]"
                  }`}
                >
                  <span className="text-base">{g.icon}</span>
                  <span
                    className={`mt-0.5 font-mono text-[10px] font-black leading-tight ${
                      isActive ? "text-[var(--text-1)]" : "text-[var(--text-1)]"
                    }`}
                  >
                    Gate {g.num}
                  </span>
                  <span className="mt-0.5 font-mono text-[8px] text-[var(--text-3)] truncate max-w-full">{g.badge}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* HERO BANNER DEL GATE SELECCIONADO */}
        <div className="relative overflow-hidden rounded-2xl border border-white/[0.08] bg-[var(--surface-1)] from-[var(--surface-1)]   p-5 md:p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <span className="text-3xl">{gate.icon}</span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full border border-[var(--border)] bg-[var(--surface-2)] px-2.5 py-0.5 font-mono text-[10px] font-black uppercase text-[var(--text-1)]">
                      {gate.badge}
                    </span>
                    <span className="font-mono text-[10px] text-[var(--text-3)]">Slug: /gates/{gate.slug}</span>
                  </div>
                  <h1 className="mt-1 text-xl md:text-2xl font-black text-[var(--text-1)] tracking-tight">
                    Gate {gate.gate_number}: {gate.name}
                  </h1>
                </div>
              </div>
              <p className="mt-2 text-xs md:text-sm text-[var(--text-1)] leading-relaxed max-w-3xl">{gate.description}</p>
            </div>

            <div className="text-left md:text-right font-mono flex-shrink-0">
              <div className="inline-flex items-center gap-1.5 rounded-full border border-[var(--profit)] bg-[var(--profit-dim)] px-3 py-1 text-xs font-black text-[var(--profit)] mb-1.5">
                <span className="h-2 w-2 rounded-full bg-[var(--profit)] animate-pulse"></span>
                {gate.live_telemetry.status}
              </div>
              <div className="text-[10px] text-[var(--text-3)]">
                Persistencia: {gate.local_persistence} · {gate.firebase_sync_status}
              </div>
            </div>
          </div>
        </div>

        {/* 2-COLUMN MAIN CONTENT */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* LEFT COLUMN */}
          <div className="lg:col-span-7 space-y-4">
            {/* Fórmulas & Criterios de Corte */}
            <div className="rounded-2xl border border-white/[0.08] bg-[var(--surface-1)] p-5 shadow-xl backdrop-blur-xl space-y-3">
              <h3 className="flex items-center gap-2 font-mono text-xs font-black uppercase tracking-wider text-[var(--text-2)]">
                <span>📐</span> Formulación Matemática & Criterios de Corte
              </h3>

              <div className="rounded-xl border border-[var(--border)] bg-[var(--bg)] p-3 font-mono text-xs text-[var(--profit)] shadow-inner">
                {gate.formula}
              </div>

              <div className="text-xs text-[var(--text-1)] leading-relaxed">
                <strong className="text-[var(--text-1)]">Objetivo del Gate:</strong> {gate.objective}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-white/[0.08]">
                <div className="rounded-xl border border-[var(--loss)] bg-[var(--loss-dim)] p-3">
                  <span className="font-mono text-[10px] font-black uppercase text-[var(--loss)]">
                    🔥 RUTA ULTRA (BingX 500x)
                  </span>
                  <p className="mt-1 text-[11px] text-[var(--loss)] leading-snug">
                    Admite volatilidad alta si la convexidad R:R compensa y la probabilidad de ruina Monte Carlo es 0.0%.
                  </p>
                </div>
                <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-3">
                  <span className="font-mono text-[10px] font-black uppercase text-[var(--text-1)]">
                    🛡️ RUTA FONDEO (Prop Firms)
                  </span>
                  <p className="mt-1 text-[11px] text-[var(--text-1)] leading-snug">
                    Corte tajante si Max Drawdown &gt; 4.0% o si existe vulnerabilidad en días de alta fricción.
                  </p>
                </div>
              </div>
            </div>

            {/* Telemetría en Vivo */}
            <div className="rounded-2xl border border-white/[0.08] bg-[var(--surface-1)] p-5 shadow-xl backdrop-blur-xl space-y-3">
              <h3 className="flex items-center gap-2 font-mono text-xs font-black uppercase tracking-wider text-[var(--profit)]">
                <span>📡</span> Telemetría del Motor en Tiempo Real
              </h3>

              <div className="grid grid-cols-3 gap-2.5 font-mono">
                <div className="rounded-xl border border-white/[0.06] bg-[var(--bg)] p-3">
                  <div className="text-[10px] uppercase text-[var(--text-3)] font-bold">Candidatos Auditados</div>
                  <div className="mt-1 text-lg font-black text-[var(--text-1)] tabular-nums">
                    {gate.live_telemetry.datasets_audited ?? "N/D"}
                  </div>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-[var(--bg)] p-3">
                  <div className="text-[10px] uppercase text-[var(--text-3)] font-bold">Tasa de Aprobación</div>
                  <div className="mt-1 text-lg font-black text-[var(--profit)] tabular-nums">
                    {gate.live_telemetry.pass_rate_pct != null ? `${gate.live_telemetry.pass_rate_pct}%` : "N/D"}
                  </div>
                </div>
                <div className="rounded-xl border border-white/[0.06] bg-[var(--bg)] p-3">
                  <div className="text-[10px] uppercase text-[var(--text-3)] font-bold">Latencia Media</div>
                  <div className="mt-1 text-lg font-black text-[var(--text-2)] tabular-nums">
                    {gate.live_telemetry.avg_latency_ms != null ? `${gate.live_telemetry.avg_latency_ms} ms` : "N/D"}
                  </div>
                </div>
              </div>

              <div className="font-mono text-xs text-[var(--text-2)]">
                <strong className="text-[var(--text-1)]">Último Veredicto Registrado:</strong> {gate.live_telemetry.last_verdict}
              </div>
            </div>

            {/* Formulario Manual de Parámetros del Motor */}
            <div className="rounded-2xl border border-white/[0.08] bg-[var(--surface-1)] p-5 shadow-xl backdrop-blur-xl space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.08] pb-3">
                <h3 className="flex items-center gap-2 font-mono text-xs font-black uppercase tracking-wider text-[var(--text-2)]">
                  <span>🎛️</span> Configuración de Umbrales del Motor
                </h3>
                <button
                  onClick={handleSaveParams}
                  className="rounded-xl bg-[var(--surface-1)]   px-3.5 py-1.5 font-mono text-xs font-black text-[var(--text-1)] shadow-md transition hover: hover: active:scale-95 cursor-pointer"
                >
                  Guardar en Motor & Firebase
                </button>
              </div>

              {saveStatus && (
                <div
                  className={`p-3 rounded-xl font-mono text-xs font-bold ${
                    saveStatus.startsWith("✅")
                      ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                      : "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)]"
                  }`}
                >
                  {saveStatus}
                </div>
              )}

              <div className="space-y-3">
                {Object.entries(gate.params || {}).map(([key, p]) => (
                  <div key={key} className="rounded-xl border border-white/[0.06] bg-[var(--bg)] p-3 space-y-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-[var(--text-1)]">{p.label}</span>
                      <span className="font-mono text-xs font-black text-[var(--text-2)] tabular-nums">
                        {currentParams[key] !== undefined ? String(currentParams[key]) : String(p.value)} {p.unit || ""}
                      </span>
                    </div>

                    {p.type === "number" && (
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min={p.min ?? 0}
                          max={p.max ?? 100}
                          step={p.step ?? 1}
                          value={currentParams[key] ?? p.value}
                          onChange={(e) => setCurrentParams({ ...currentParams, [key]: parseFloat(e.target.value) })}
                          className="flex-1 accent-[var(--text-1)] cursor-pointer"
                        />
                        <input
                          type="number"
                          min={p.min}
                          max={p.max}
                          step={p.step}
                          value={currentParams[key] ?? p.value}
                          onChange={(e) => setCurrentParams({ ...currentParams, [key]: parseFloat(e.target.value) })}
                          className="w-20 rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-2 py-1 font-mono text-xs text-[var(--text-1)] text-right outline-none focus:border-[var(--border)]"
                        />
                      </div>
                    )}

                    {p.type === "boolean" && (
                      <label className="flex items-center gap-2 cursor-pointer pt-1">
                        <input
                          type="checkbox"
                          checked={currentParams[key] ?? p.value}
                          onChange={(e) => setCurrentParams({ ...currentParams, [key]: e.target.checked })}
                          className="w-4 h-4 accent-[var(--text-1)] cursor-pointer"
                        />
                        <span
                          className={`font-mono text-xs font-bold ${
                            currentParams[key] ? "text-[var(--profit)]" : "text-[var(--text-3)]"
                          }`}
                        >
                          {currentParams[key] ? "ACTIVADO" : "DESACTIVADO"}
                        </span>
                      </label>
                    )}

                    {p.type === "select" && (
                      <select
                        value={currentParams[key] ?? p.value}
                        onChange={(e) => setCurrentParams({ ...currentParams, [key]: e.target.value })}
                        className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-1)] px-3 py-1.5 text-xs text-[var(--text-1)] outline-none focus:border-[var(--border)] cursor-pointer"
                      >
                        {(p.options || []).map((opt) => (
                          <option key={opt} value={opt}>
                            {opt}
                          </option>
                        ))}
                      </select>
                    )}

                    <p className="text-[10px] text-[var(--text-3)]">{p.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="lg:col-span-5 flex flex-col space-y-4">
            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface-1)] p-5 shadow-xl backdrop-blur-xl flex flex-col h-full min-h-[580px]">
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 mb-3">
                <div className="flex items-center gap-2.5">
                  <span className="text-xl">🤖</span>
                  <div>
                    <h3 className="font-mono text-xs font-black uppercase text-[var(--text-2)]">
                      Editor Semántico Agéntico de IA
                    </h3>
                    <div className="text-[10px] text-[var(--text-3)]">
                      Mutación dinámica en lenguaje natural + Firestore Sync
                    </div>
                  </div>
                </div>
                <span className="rounded-full border border-[var(--profit)] bg-[var(--profit-dim)] px-2 py-0.5 font-mono text-[9px] font-black text-[var(--profit)]">
                  CLOUD LIVE
                </span>
              </div>

              {/* Directivas Rápidas */}
              <div className="mb-3">
                <div className="font-mono text-[10px] font-bold text-[var(--text-2)] mb-1.5">Directivas Rápidas:</div>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => handleAiSemanticSubmit("Configurar parámetros con rigor estricto para cuenta de Fondeo 50k")}
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-2.5 py-1 font-mono text-[10px] font-bold text-[var(--text-1)] transition hover:bg-[var(--surface-2)] active:scale-95 cursor-pointer"
                  >
                    🛡️ Modo Fondeo Estricto
                  </button>
                  <button
                    onClick={() => handleAiSemanticSubmit("Ajustar para Ruta ULTRA con máxima convexidad y apalancamiento adaptativo")}
                    className="rounded-xl border border-[var(--loss)] bg-[var(--loss-dim)] px-2.5 py-1 font-mono text-[10px] font-bold text-[var(--loss)] transition hover:bg-[var(--loss-dim)] active:scale-95 cursor-pointer"
                  >
                    🔥 Modo Ultra Convexo
                  </button>
                  <button
                    onClick={() => handleAiSemanticSubmit("Incrementar el estrés de slippage a 3x y duplicar comisiones")}
                    className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-2.5 py-1 font-mono text-[10px] font-bold text-[var(--text-1)] transition hover:bg-[var(--surface-2)] active:scale-95 cursor-pointer"
                  >
                    ⚡ Estrés Extremo 3x
                  </button>
                </div>
              </div>

              {/* Chat History */}
              <div className="flex-1 overflow-y-auto rounded-xl border border-white/[0.06] bg-[var(--bg)] p-3 space-y-2.5 max-h-[380px] shadow-inner font-mono text-xs">
                {aiChatLog.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`max-w-[90%] rounded-xl p-3 text-xs leading-relaxed ${
                      msg.role === "user"
                        ? "ml-auto border border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-1)]"
                        : "border border-white/[0.06] bg-[var(--surface-1)] text-[var(--text-1)]"
                    }`}
                  >
                    <div className="whitespace-pre-line">{msg.text}</div>
                    {msg.syncInfo && <div className="mt-1.5 text-[9px] text-[var(--profit)] font-bold">{msg.syncInfo}</div>}
                    <div className="mt-1 text-[9px] text-[var(--text-3)] text-right">{msg.time}</div>
                  </div>
                ))}
                {aiLoading && (
                  <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-3 text-xs text-[var(--text-1)] animate-pulse">
                    ⏳ El Agente Semántico está recalculando matrices del motor y sincronizando en Firebase...
                  </div>
                )}
              </div>

              {/* Prompt Input Form */}
              <div className="mt-3 flex gap-2">
                <input
                  type="text"
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAiSemanticSubmit()}
                  placeholder="Escribe una directiva semántica para modificar este Gate..."
                  disabled={aiLoading}
                  className="flex-1 rounded-xl border border-white/[0.08] bg-[var(--bg)] px-3 py-2 text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none focus:border-[var(--border)] transition"
                />
                <button
                  onClick={() => handleAiSemanticSubmit()}
                  disabled={aiLoading || !aiPrompt.trim()}
                  className="rounded-xl bg-[var(--surface-1)]   px-4 py-2 font-mono text-xs font-bold text-[var(--text-1)] shadow-md transition hover: hover: active:scale-95 disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Enviar</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
