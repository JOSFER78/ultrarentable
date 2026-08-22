"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

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

const ALL_GATES = [
  { num: 1, slug: "gate-1-data-ingest", name: "1. Data Ingest", icon: "🗄️", badge: "Integridad" },
  { num: 2, slug: "gate-2-cost-backtest", name: "2. Costes & Fricción", icon: "💸", badge: "Costes Reales" },
  { num: 3, slug: "gate-3-trade-significance", name: "3. Muestra Estadística", icon: "📊", badge: "Outliers & N>=20" },
  { num: 4, slug: "gate-4-walk-forward", name: "4. Walk-Forward (WFE)", icon: "🔄", badge: "Anti-Curve Fit" },
  { num: 5, slug: "gate-5-monte-carlo", name: "5. Monte Carlo 1,000x", icon: "🎲", badge: "Ruina 0.0%" },
  { num: 6, slug: "gate-6-stress-slippage", name: "6. Estrés & Slippage", icon: "⚡", badge: "3x Fricción" },
  { num: 7, slug: "gate-7-regime-coverage", name: "7. Cobertura Regímenes", icon: "🌐", badge: "Bull/Bear/Chop" },
  { num: 8, slug: "gate-8-dsr-ratio", name: "8. Deflated Sharpe (DSR)", icon: "📐", badge: "López de Prado" },
  { num: 9, slug: "gate-9-novelty-antifit", name: "9. Novedad & Inoculación", icon: "🧬", badge: "Failure DB" },
  { num: 10, slug: "gate-10-multi-agent-debate", name: "10. Debate 5 Agentes IA", icon: "🤖", badge: "Comité Semántico" },
  { num: 11, slug: "gate-10-nautilus-trader", name: "10. NautilusTrader Core", icon: "⚡", badge: "Event-Driven" },
];

export default function GateDetailPage() {
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
  const [aiChatLog, setAiChatLog] = useState<Array<{ role: "user" | "assistant"; text: string; time: string; syncInfo?: string }>>([
    {
      role: "assistant",
      text: `Hola. Soy el Agente Arquitecto Cuantitativo para este Gate. Puedes darme órdenes en lenguaje natural (ej. "Ajustar para Fondeo estricto", "Aumentar exigencia de estrés a 3x", "Bajar tolerancia de gaps") y reconfiguraré el motor y Firebase al instante.`,
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
      setGate(data);
      
      // Initialize form parameters
      const initial: Record<string, any> = {};
      if (data.params) {
        Object.keys(data.params).forEach((k) => {
          initial[k] = data.params[k].value;
        });
      }
      setCurrentParams(initial);
    } catch (err: any) {
      setError(err.message || "Error al cargar la fase cuantitativa");
    } finally {
      setLoading(false);
    }
  }, [rawSlug]);

  // Load candidate list for Nautilus simulation
  const fetchCandidatesForNautilus = useCallback(async () => {
    if (rawSlug !== "gate-10-nautilus-trader") return;
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
  }, [rawSlug]);

  // Load detailed Nautilus backtest for candidate
  const fetchNautilusBacktest = useCallback(async (cId: string) => {
    if (!cId || rawSlug !== "gate-10-nautilus-trader") return;
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
  }, [rawSlug]);

  useEffect(() => {
    fetchGateData();
    fetchCandidatesForNautilus();
  }, [fetchGateData, fetchCandidatesForNautilus]);

  useEffect(() => {
    if (selectedCandidateId) {
      fetchNautilusBacktest(selectedCandidateId);
    }
  }, [selectedCandidateId, fetchNautilusBacktest]);

  // Save manual configuration
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

  // Submit AI Semantic Mutation
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
      <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "30px", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "var(--font-sans, system-ui)" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "28px", marginBottom: "12px" }}>⚙️</div>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 700 }}>Cargando especificación matemática del Gate...</div>
        </div>
      </div>
    );
  }

  if (error || !gate) {
    return (
      <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "40px", fontFamily: "var(--font-sans, system-ui)" }}>
        <div style={{ maxWidth: "600px", margin: "0 auto", background: "rgba(244, 63, 94, 0.1)", border: "1px solid rgba(244, 63, 94, 0.3)", borderRadius: "12px", padding: "24px" }}>
          <h2 style={{ color: "#fb7185", margin: "0 0 10px" }}>Error al cargar Gate</h2>
          <p style={{ color: "#cbd5e1", fontSize: "13px" }}>{error || "El gate solicitado no existe."}</p>
          <Link href="/candidatos" style={{ display: "inline-block", marginTop: "12px", padding: "8px 14px", background: "#38bdf8", color: "#000", borderRadius: "6px", fontWeight: 800, fontSize: "12px", textDecoration: "none" }}>
            ← Volver a Candidatos & Gates
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#06090e", color: "#f8fafc", padding: "16px 24px", fontFamily: "var(--font-sans, system-ui)", boxSizing: "border-box" }}>
      
      {/* ── BREADCRUMB & BACK LINK ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
          <Link href="/" style={{ color: "#94a3b8", textDecoration: "none" }}>Inicio</Link>
          <span>/</span>
          <Link href="/candidatos" style={{ color: "#94a3b8", textDecoration: "none" }}>10 Gates</Link>
          <span>/</span>
          <span style={{ color: "#38bdf8", fontWeight: 800 }}>{gate.slug}</span>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <Link href="/candidatos" style={{ padding: "5px 12px", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "6px", color: "#cbd5e1", fontSize: "11px", fontWeight: 700, textDecoration: "none" }}>
            ← Ver Matriz 10 Gates
          </Link>
          <Link href="/strategies" style={{ padding: "5px 12px", background: "rgba(56, 189, 248, 0.15)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "6px", color: "#38bdf8", fontSize: "11px", fontWeight: 700, textDecoration: "none" }}>
            Explorador Multiactivo →
          </Link>
        </div>
      </div>

      {/* ── TOP HORIZONTAL GATES SELECTOR (11 SLUGS INDEPENDIENTES) ── */}
      <div style={{ background: "rgba(10, 14, 23, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "8px 10px", marginBottom: "20px" }}>
        <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>
          Navegador de Fases Cuantitativas (Haz clic en cualquier fase para inspeccionar su slug):
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(11, 1fr)", gap: "6px" }}>
          {ALL_GATES.map((g) => {
            const isActive = g.slug === rawSlug;
            return (
              <Link
                key={g.slug}
                href={`/gates/${g.slug}`}
                style={{
                  textDecoration: "none",
                  padding: "8px 6px",
                  borderRadius: "6px",
                  background: isActive ? "linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(99, 102, 241, 0.2))" : "rgba(255, 255, 255, 0.02)",
                  border: isActive ? "1px solid #38bdf8" : "1px solid rgba(255, 255, 255, 0.06)",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  textAlign: "center",
                  transition: "all 0.15s ease",
                }}
              >
                <span style={{ fontSize: "14px", marginBottom: "2px" }}>{g.icon}</span>
                <span style={{ fontSize: "9.5px", fontWeight: 900, color: isActive ? "#38bdf8" : "#cbd5e1", lineHeight: 1.1 }}>
                  Gate {g.num}
                </span>
                <span style={{ fontSize: "7.5px", color: isActive ? "#63e1b4" : "#64748b", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                  {g.badge}
                </span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* ── HERO BANNER DEL GATE SELECCIONADO ── */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(10, 14, 23, 0.95))",
          border: "1px solid rgba(56, 189, 248, 0.2)",
          borderRadius: "12px",
          padding: "20px 24px",
          marginBottom: "22px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <span style={{ fontSize: "28px" }}>{gate.icon}</span>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "10px", fontWeight: 900, color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", padding: "2px 8px", borderRadius: "4px", textTransform: "uppercase" }}>
                  {gate.badge}
                </span>
                <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  Slug Oficial: /gates/{gate.slug}
                </span>
              </div>
              <h1 style={{ margin: "2px 0 0", fontSize: "20px", fontWeight: 900, color: "#ffffff", letterSpacing: "-0.5px" }}>
                Gate {gate.gate_number}: {gate.name}
              </h1>
            </div>
          </div>
          <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "12.5px", maxWidth: "750px", lineHeight: 1.4 }}>
            {gate.description}
          </p>
        </div>

        <div style={{ textAlign: "right" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(52, 211, 153, 0.15)", border: "1px solid rgba(52, 211, 153, 0.3)", padding: "5px 10px", borderRadius: "6px", fontSize: "11px", fontWeight: 800, color: "#34d399", marginBottom: "6px" }}>
            <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#34d399" }}></span>
            {gate.live_telemetry.status}
          </div>
          <div style={{ fontSize: "9.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
            Persistencia: {gate.local_persistence} · {gate.firebase_sync_status}
          </div>
        </div>
      </div>

      {/* ── 2-COLUMN MAIN CONTENT (LEFT: TECHNICAL SPEC & PARAMS, RIGHT: AGENTIC AI SEMANTIC CHAT) ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "20px", marginBottom: "24px" }}>
        
        {/* LEFT COLUMN: FÓRMULAS, TELEMETRÍA Y PARÁMETROS DEL MOTOR */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          
          {/* Fórmulas & Objetivo */}
          <div style={{ background: "#0a0e17", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px 18px" }}>
            <h3 style={{ margin: "0 0 10px", fontSize: "12px", color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 800, display: "flex", alignItems: "center", gap: "6px" }}>
              <span>📐</span> Formulación Matemática & Criterios de Corte
            </h3>
            
            <div style={{ background: "rgba(0, 0, 0, 0.5)", border: "1px solid rgba(56, 189, 248, 0.2)", borderRadius: "6px", padding: "10px 12px", marginBottom: "12px", fontFamily: "var(--font-mono, monospace)", fontSize: "11.5px", color: "#63e1b4" }}>
              {gate.formula}
            </div>

            <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: 1.5, marginBottom: "8px" }}>
              <strong style={{ color: "#ffffff" }}>Objetivo del Gate:</strong> {gate.objective}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "12px", paddingTop: "12px", borderTop: "1px solid rgba(255, 255, 255, 0.06)" }}>
              <div style={{ background: "rgba(244, 63, 94, 0.08)", border: "1px solid rgba(244, 63, 94, 0.2)", borderRadius: "6px", padding: "8px 10px" }}>
                <span style={{ fontSize: "10px", fontWeight: 900, color: "#fb7185" }}>🔥 RUTA ULTRA (BingX 500x)</span>
                <p style={{ margin: "4px 0 0", fontSize: "11px", color: "#fda4af" }}>
                  Admite volatilidad alta si la convexidad R:R compensa y la probabilidad de ruina es 0.0%.
                </p>
              </div>
              <div style={{ background: "rgba(56, 189, 248, 0.08)", border: "1px solid rgba(56, 189, 248, 0.2)", borderRadius: "6px", padding: "8px 10px" }}>
                <span style={{ fontSize: "10px", fontWeight: 900, color: "#38bdf8" }}>🛡️ RUTA FONDEO (Prop Firms)</span>
                <p style={{ margin: "4px 0 0", fontSize: "11px", color: "#bae6fd" }}>
                  Corte tajante si Max Drawdown {">"} 4.0% o si existe vulnerabilidad en días de alta fricción.
                </p>
              </div>
            </div>
          </div>

          {/* Telemetría en Vivo */}
          <div style={{ background: "#0a0e17", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px 18px" }}>
            <h3 style={{ margin: "0 0 12px", fontSize: "12px", color: "#34d399", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 800, display: "flex", alignItems: "center", gap: "6px" }}>
              <span>📡</span> Telemetría del Motor en Tiempo Real
            </h3>
            
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px", marginBottom: "12px" }}>
              <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <div style={{ fontSize: "10px", color: "#64748b" }}>Candidatos Auditados</div>
                <div style={{ fontSize: "16px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                  {gate.live_telemetry.datasets_audited}
                </div>
              </div>
              <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <div style={{ fontSize: "10px", color: "#64748b" }}>Tasa de Aprobación</div>
                <div style={{ fontSize: "16px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                  {gate.live_telemetry.pass_rate_pct}%
                </div>
              </div>
              <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px", borderRadius: "6px", border: "1px solid rgba(255, 255, 255, 0.05)" }}>
                <div style={{ fontSize: "10px", color: "#64748b" }}>Latencia Media</div>
                <div style={{ fontSize: "16px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                  {gate.live_telemetry.avg_latency_ms} ms
                </div>
              </div>
            </div>

            <div style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
              <strong style={{ color: "#cbd5e1" }}>Último Veredicto Registrado:</strong> {gate.live_telemetry.last_verdict}
            </div>
          </div>

          {/* Formulario Manual de Parámetros del Motor */}
          <div style={{ background: "#0a0e17", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px 18px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h3 style={{ margin: 0, fontSize: "12px", color: "#facc15", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 800, display: "flex", alignItems: "center", gap: "6px" }}>
                <span>🎛️</span> Configuración de Umbrales del Motor
              </h3>
              <button
                onClick={handleSaveParams}
                style={{
                  padding: "5px 12px",
                  background: "linear-gradient(135deg, #38bdf8, #6366f1)",
                  color: "#000",
                  border: "none",
                  borderRadius: "5px",
                  fontSize: "11px",
                  fontWeight: 900,
                  cursor: "pointer",
                }}
              >
                Guardar en Motor & Firebase
              </button>
            </div>

            {saveStatus && (
              <div style={{ marginBottom: "12px", padding: "6px 10px", borderRadius: "5px", fontSize: "11px", background: saveStatus.startsWith("✅") ? "rgba(52, 211, 153, 0.15)" : "rgba(56, 189, 248, 0.15)", color: saveStatus.startsWith("✅") ? "#34d399" : "#38bdf8", fontWeight: 700 }}>
                {saveStatus}
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {Object.entries(gate.params || {}).map(([key, p]) => (
                <div key={key} style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "6px", padding: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <span style={{ fontSize: "11.5px", fontWeight: 700, color: "#ffffff" }}>{p.label}</span>
                    <span style={{ fontSize: "12px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                      {currentParams[key] !== undefined ? String(currentParams[key]) : String(p.value)} {p.unit || ""}
                    </span>
                  </div>

                  {p.type === "number" && (
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <input
                        type="range"
                        min={p.min ?? 0}
                        max={p.max ?? 100}
                        step={p.step ?? 1}
                        value={currentParams[key] ?? p.value}
                        onChange={(e) => setCurrentParams({ ...currentParams, [key]: parseFloat(e.target.value) })}
                        style={{ flex: 1, accentColor: "#38bdf8", cursor: "pointer" }}
                      />
                      <input
                        type="number"
                        min={p.min}
                        max={p.max}
                        step={p.step}
                        value={currentParams[key] ?? p.value}
                        onChange={(e) => setCurrentParams({ ...currentParams, [key]: parseFloat(e.target.value) })}
                        style={{ width: "70px", background: "#06090e", border: "1px solid #334155", color: "#fff", borderRadius: "4px", padding: "3px 6px", fontSize: "11px", textAlign: "right" }}
                      />
                    </div>
                  )}

                  {p.type === "boolean" && (
                    <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", marginTop: "4px" }}>
                      <input
                        type="checkbox"
                        checked={currentParams[key] ?? p.value}
                        onChange={(e) => setCurrentParams({ ...currentParams, [key]: e.target.checked })}
                        style={{ accentColor: "#34d399", width: "16px", height: "16px" }}
                      />
                      <span style={{ fontSize: "11px", color: currentParams[key] ? "#34d399" : "#64748b", fontWeight: 700 }}>
                        {currentParams[key] ? "ACTIVADO" : "DESACTIVADO"}
                      </span>
                    </label>
                  )}

                  {p.type === "select" && (
                    <select
                      value={currentParams[key] ?? p.value}
                      onChange={(e) => setCurrentParams({ ...currentParams, [key]: e.target.value })}
                      style={{ width: "100%", background: "#06090e", border: "1px solid #334155", color: "#fff", borderRadius: "4px", padding: "5px 8px", fontSize: "11px", marginTop: "4px" }}
                    >
                      {(p.options || []).map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </select>
                  )}

                  <p style={{ margin: "4px 0 0", fontSize: "10px", color: "#64748b" }}>{p.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: EDITOR SEMÁNTICO AGÉNTICO DE IA & CLOUD SYNC */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          
          <div style={{ background: "#0a0e17", border: "1px solid rgba(99, 102, 241, 0.3)", borderRadius: "10px", padding: "16px 18px", display: "flex", flexDirection: "column", height: "100%", minHeight: "560px" }}>
            
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "18px" }}>🤖</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: "13px", color: "#818cf8", fontWeight: 900 }}>
                    Editor Semántico Agéntico de IA
                  </h3>
                  <div style={{ fontSize: "9.5px", color: "#64748b" }}>
                    Mutación dinámica del motor en lenguaje natural + Firebase Firestore Sync
                  </div>
                </div>
              </div>
              <span style={{ fontSize: "9.5px", color: "#34d399", background: "rgba(52, 211, 153, 0.15)", padding: "2px 6px", borderRadius: "4px", fontWeight: 800 }}>
                CLOUD LIVE
              </span>
            </div>

            {/* Quick Prompt Suggestions */}
            <div style={{ marginBottom: "12px" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontWeight: 700, marginBottom: "5px" }}>Directivas Rápidas Recomendadas:</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                <button
                  onClick={() => handleAiSemanticSubmit("Configurar parámetros con rigor estricto para cuenta de Fondeo 50k")}
                  style={{ background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.25)", color: "#38bdf8", borderRadius: "4px", padding: "4px 8px", fontSize: "10px", cursor: "pointer", fontWeight: 700 }}
                >
                  🛡️ Modo Fondeo Estricto
                </button>
                <button
                  onClick={() => handleAiSemanticSubmit("Ajustar para Ruta ULTRA con máxima convexidad y apalancamiento adaptativo")}
                  style={{ background: "rgba(244, 63, 94, 0.1)", border: "1px solid rgba(244, 63, 94, 0.25)", color: "#fb7185", borderRadius: "4px", padding: "4px 8px", fontSize: "10px", cursor: "pointer", fontWeight: 700 }}
                >
                  🔥 Modo Ultra Convexo
                </button>
                <button
                  onClick={() => handleAiSemanticSubmit("Incrementar el estrés de slippage a 3x y duplicar comisiones")}
                  style={{ background: "rgba(250, 204, 21, 0.1)", border: "1px solid rgba(250, 204, 21, 0.25)", color: "#facc15", borderRadius: "4px", padding: "4px 8px", fontSize: "10px", cursor: "pointer", fontWeight: 700 }}
                >
                  ⚡ Estrés Extremo 3x
                </button>
              </div>
            </div>

            {/* Chat History Box */}
            <div style={{ flex: 1, background: "rgba(0, 0, 0, 0.4)", border: "1px solid rgba(255, 255, 255, 0.05)", borderRadius: "8px", padding: "12px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px", maxHeight: "380px" }}>
              {aiChatLog.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                    maxWidth: "85%",
                    background: msg.role === "user" ? "rgba(56, 189, 248, 0.2)" : "rgba(30, 41, 59, 0.7)",
                    border: msg.role === "user" ? "1px solid rgba(56, 189, 248, 0.4)" : "1px solid rgba(255, 255, 255, 0.08)",
                    borderRadius: "8px",
                    padding: "8px 12px",
                    fontSize: "11.5px",
                    color: "#f8fafc",
                  }}
                >
                  <div style={{ whiteSpace: "pre-line", lineHeight: 1.4 }}>{msg.text}</div>
                  {msg.syncInfo && (
                    <div style={{ marginTop: "6px", fontSize: "9px", color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                      {msg.syncInfo}
                    </div>
                  )}
                  <div style={{ fontSize: "9px", color: "#64748b", textAlign: "right", marginTop: "3px" }}>
                    {msg.time}
                  </div>
                </div>
              ))}
              {aiLoading && (
                <div style={{ alignSelf: "flex-start", background: "rgba(30, 41, 59, 0.7)", borderRadius: "8px", padding: "8px 12px", fontSize: "11px", color: "#818cf8" }}>
                  ⏳ El Agente Semántico está recalculando las matrices del motor y sincronizando en Firebase...
                </div>
              )}
            </div>

            {/* Prompt Input Form */}
            <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
              <input
                type="text"
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAiSemanticSubmit()}
                placeholder="Escribe una instrucción semántica para modificar este Gate..."
                disabled={aiLoading}
                style={{
                  flex: 1,
                  background: "#06090e",
                  border: "1px solid #334155",
                  color: "#ffffff",
                  borderRadius: "6px",
                  padding: "8px 12px",
                  fontSize: "12px",
                  outline: "none",
                }}
              />
              <button
                onClick={() => handleAiSemanticSubmit()}
                disabled={aiLoading || !aiPrompt.trim()}
                style={{
                  background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  padding: "0 16px",
                  fontSize: "12px",
                  fontWeight: 800,
                  cursor: aiLoading || !aiPrompt.trim() ? "not-allowed" : "pointer",
                  opacity: aiLoading || !aiPrompt.trim() ? 0.5 : 1,
                }}
              >
                Enviar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── SECCIÓN ESPECIAL PARA GATE 11 (NAUTILUSTRADER CORE & BACKTEST DETALLADO) ── */}
      {rawSlug === "gate-10-nautilus-trader" && (
        <div style={{ background: "#0a0e17", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "12px", padding: "24px", marginTop: "24px" }}>
          
          {/* Header Nautilus */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "24px" }}>⚡</span>
                <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 900, color: "#ffffff" }}>
                  NautilusTrader Event-Driven Simulation Engine
                </h2>
                <span style={{ fontSize: "10px", fontWeight: 900, background: "#38bdf8", color: "#000", padding: "2px 6px", borderRadius: "4px" }}>
                  RUST / CYTHON CORE
                </span>
              </div>
              <p style={{ margin: "4px 0 0", fontSize: "12px", color: "#94a3b8" }}>
                Auditoría trade a trade de alta resolución con matching engine, comisiones reales y colchón de liquidación.
              </p>
            </div>

            {/* Candidate Selector */}
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 700 }}>Estrategia a Simular:</span>
              <select
                value={selectedCandidateId}
                onChange={(e) => setSelectedCandidateId(e.target.value)}
                style={{
                  background: "#06090e",
                  border: "1px solid #38bdf8",
                  color: "#38bdf8",
                  borderRadius: "6px",
                  padding: "6px 12px",
                  fontSize: "12px",
                  fontWeight: 800,
                  outline: "none",
                }}
              >
                {candidates.map((c) => (
                  <option key={c.candidate_id} value={c.candidate_id}>
                    {c.symbol} ({c.timeframe}) · {c.route} · {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {nautilusLoading ? (
            <div style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
              ⏳ Ejecutando simulación evento-a-evento con NautilusTrader Rust Core...
            </div>
          ) : nautilusReport ? (
            <div>
              {/* Hero KPI Summary */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: "10px", marginBottom: "20px" }}>
                <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>ROI Total</div>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                    +{nautilusReport.performance_summary.total_roi_pct}%
                  </div>
                  <div style={{ fontSize: "9px", color: "#63e1b4" }}>
                    ${nautilusReport.performance_summary.net_profit_usd.toLocaleString()} USD
                  </div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>Profit Factor</div>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                    {nautilusReport.performance_summary.profit_factor}
                  </div>
                  <div style={{ fontSize: "9px", color: "#94a3b8" }}>Win Rate: {nautilusReport.performance_summary.win_rate_pct}%</div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>Max Drawdown</div>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: nautilusReport.performance_summary.max_drawdown_pct <= 4 ? "#34d399" : "#fb7185", fontFamily: "var(--font-mono, monospace)" }}>
                    {nautilusReport.performance_summary.max_drawdown_pct}%
                  </div>
                  <div style={{ fontSize: "9px", color: "#64748b" }}>
                    ${nautilusReport.performance_summary.max_drawdown_usd.toLocaleString()} USD
                  </div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>Sharpe / Sortino</div>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: "#facc15", fontFamily: "var(--font-mono, monospace)" }}>
                    {nautilusReport.performance_summary.sharpe_ratio} / {nautilusReport.performance_summary.sortino_ratio}
                  </div>
                  <div style={{ fontSize: "9px", color: "#64748b" }}>DSR: {nautilusReport.performance_summary.deflated_sharpe_ratio}</div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>Colchón a Liquidación</div>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>
                    {nautilusReport.performance_summary.min_liquidation_distance_pct}%
                  </div>
                  <div style={{ fontSize: "9px", color: "#34d399" }}>0 Margin Calls</div>
                </div>

                <div style={{ background: "rgba(255, 255, 255, 0.02)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "8px", padding: "12px" }}>
                  <div style={{ fontSize: "10px", color: "#64748b" }}>Fricción Pagada</div>
                  <div style={{ fontSize: "18px", fontWeight: 900, color: "#e2e8f0", fontFamily: "var(--font-mono, monospace)" }}>
                    ${(nautilusReport.performance_summary.total_exchange_fees_usd + nautilusReport.performance_summary.total_slippage_cost_usd).toFixed(1)}
                  </div>
                  <div style={{ fontSize: "9px", color: "#64748b" }}>Fees + Slippage</div>
                </div>
              </div>

              {/* Equity Curve Chart Visualizer */}
              <div style={{ background: "rgba(0, 0, 0, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "16px", marginBottom: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase" }}>
                    📈 Curva de Balance & Drawdown Dinámica (Evento a Evento)
                  </span>
                  <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                    Capital Base: ${nautilusReport.performance_summary.initial_capital_usd.toLocaleString()} → Final: ${nautilusReport.performance_summary.ending_equity_usd.toLocaleString()} USD
                  </span>
                </div>

                {/* SVG Polyline Equity Curve */}
                <div style={{ width: "100%", height: "160px", position: "relative" }}>
                  <svg viewBox="0 0 800 150" style={{ width: "100%", height: "100%", overflow: "visible" }}>
                    <defs>
                      <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Grid lines */}
                    <line x1="0" y1="30" x2="800" y2="30" stroke="rgba(255,255,255,0.05)" strokeDasharray="4" />
                    <line x1="0" y1="75" x2="800" y2="75" stroke="rgba(255,255,255,0.05)" strokeDasharray="4" />
                    <line x1="0" y1="120" x2="800" y2="120" stroke="rgba(255,255,255,0.05)" strokeDasharray="4" />

                    {/* Equity Points Path */}
                    {(() => {
                      const pts = nautilusReport.equity_curve || [];
                      if (pts.length < 2) return null;
                      const minEq = Math.min(...pts.map((p: any) => p.equity)) * 0.98;
                      const maxEq = Math.max(...pts.map((p: any) => p.equity)) * 1.02;
                      const range = maxEq - minEq || 1;

                      const coords = pts.map((p: any, idx: number) => {
                        const x = (idx / (pts.length - 1)) * 800;
                        const y = 140 - ((p.equity - minEq) / range) * 130;
                        return `${x},${y}`;
                      });

                      const polylineStr = coords.join(" ");
                      const areaStr = `0,150 ${polylineStr} 800,150`;

                      return (
                        <>
                          <polygon points={areaStr} fill="url(#equityGrad)" />
                          <polyline points={polylineStr} fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeLinecap="round" />
                          {pts.map((p: any, idx: number) => {
                            const x = (idx / (pts.length - 1)) * 800;
                            const y = 140 - ((p.equity - minEq) / range) * 130;
                            return (
                              <circle
                                key={idx}
                                cx={x}
                                cy={y}
                                r={idx === 0 || idx === pts.length - 1 ? 4 : 2}
                                fill={p.is_win ? "#34d399" : "#fb7185"}
                              />
                            );
                          })}
                        </>
                      );
                    })()}
                  </svg>
                </div>
              </div>

              {/* Trade Blotter Table (Registro Exhaustivo Trade a Trade) */}
              <div style={{ background: "rgba(0, 0, 0, 0.4)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "16px", marginBottom: "20px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <span style={{ fontSize: "11px", fontWeight: 800, color: "#63e1b4", textTransform: "uppercase" }}>
                    📋 Registro de Operaciones Event-Driven ({nautilusReport.trade_blotter?.length || 0} Trades Auditados)
                  </span>
                  <span style={{ fontSize: "10px", color: "#64748b" }}>Matching Model: TICK_BY_TICK_QUEUE</span>
                </div>

                <div style={{ overflowX: "auto", maxHeight: "280px" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "11px" }}>
                    <thead>
                      <tr style={{ background: "rgba(255, 255, 255, 0.04)", color: "#64748b", textAlign: "left" }}>
                        <th style={{ padding: "6px 8px" }}>Trade ID</th>
                        <th style={{ padding: "6px 8px" }}>Fecha / Hora</th>
                        <th style={{ padding: "6px 8px" }}>Lado</th>
                        <th style={{ padding: "6px 8px" }}>Tipo Orden</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Precio Entrada</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Precio Salida</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>PnL Neto</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Apalancamiento</th>
                        <th style={{ padding: "6px 8px", textAlign: "right" }}>Colchón Liq.</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(nautilusReport.trade_blotter || []).map((t: any) => (
                        <tr key={t.trade_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.03)" }}>
                          <td style={{ padding: "6px 8px", fontWeight: 800, color: "#cbd5e1", fontFamily: "var(--font-mono, monospace)" }}>{t.trade_id}</td>
                          <td style={{ padding: "6px 8px", color: "#94a3b8" }}>{t.timestamp}</td>
                          <td style={{ padding: "6px 8px" }}>
                            <span style={{ fontSize: "9px", fontWeight: 900, padding: "2px 5px", borderRadius: "3px", background: t.side === "LONG" ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)", color: t.side === "LONG" ? "#34d399" : "#fb7185" }}>
                              {t.side}
                            </span>
                          </td>
                          <td style={{ padding: "6px 8px", color: "#64748b", fontSize: "10px" }}>{t.order_type}</td>
                          <td style={{ padding: "6px 8px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>${t.entry_price}</td>
                          <td style={{ padding: "6px 8px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>${t.exit_price}</td>
                          <td style={{ padding: "6px 8px", textAlign: "right", fontWeight: 800, color: t.net_pnl_usd >= 0 ? "#34d399" : "#fb7185", fontFamily: "var(--font-mono, monospace)" }}>
                            {t.net_pnl_usd >= 0 ? `+$${t.net_pnl_usd}` : `-$${Math.abs(t.net_pnl_usd)}`}
                          </td>
                          <td style={{ padding: "6px 8px", textAlign: "right", color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>{t.effective_leverage}x</td>
                          <td style={{ padding: "6px 8px", textAlign: "right", color: "#34d399", fontFamily: "var(--font-mono, monospace)" }}>{t.liquidation_distance_pct}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Real Logs Visual Feed */}
              <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "14px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{ fontSize: "11px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                      📡 Telemetría y Logs del Gate (VPS 24/7)
                    </span>
                    <span style={{ fontSize: "9px", color: "#34d399", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(52, 211, 153, 0.15)" }}>
                      ● ZERO-MOCKS
                    </span>
                  </div>
                  <span style={{ fontSize: "9.5px", color: "#94a3b8" }}>
                    {nautilusReport.event_log?.length || 0} eventos registrados
                  </span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "6px", maxHeight: "180px", overflowY: "auto" }}>
                  {(nautilusReport.event_log || []).map((line: string, i: number) => {
                    const isErr = line.includes("ERROR") || line.includes("REJECTED") || line.includes("BREACH");
                    const isSuccess = line.includes("PASSED") || line.includes("SUCCESS") || line.includes("Sincronización") || line.includes("Starting");
                    const badgeBg = isErr ? "rgba(248, 113, 113, 0.2)" : isSuccess ? "rgba(52, 211, 153, 0.2)" : "rgba(56, 189, 248, 0.15)";
                    const badgeColor = isErr ? "#f87171" : isSuccess ? "#34d399" : "#38bdf8";

                    return (
                      <div
                        key={i}
                        style={{
                          background: "rgba(5, 8, 14, 0.8)",
                          border: `1px solid ${isErr ? "rgba(248, 113, 113, 0.25)" : isSuccess ? "rgba(52, 211, 153, 0.2)" : "rgba(255, 255, 255, 0.05)"}`,
                          borderRadius: "6px",
                          padding: "8px 10px",
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          fontSize: "11px",
                          gap: "10px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span
                            style={{
                              fontSize: "9px",
                              fontWeight: 900,
                              padding: "1px 5px",
                              borderRadius: "3px",
                              background: badgeBg,
                              color: badgeColor,
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            {isErr ? "❌ FALLO" : isSuccess ? "✓ OK" : "ℹ️ EVENTO"}
                          </span>
                          <span style={{ color: "#f1f5f9" }}>{line}</span>
                        </div>
                        <span style={{ fontSize: "9px", color: "#64748b", fontFamily: "var(--font-mono, monospace)", flexShrink: 0 }}>
                          Evento #{i + 1}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

    </div>
  );
}
