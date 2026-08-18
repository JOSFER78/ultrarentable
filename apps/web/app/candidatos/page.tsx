"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { StrategyLifecycleStatus } from "@/types/telemetry";

const FSM_STATES: { key: StrategyLifecycleStatus; label: string; desc: string; color: string; step: number }[] = [
  { key: "GENERATED", label: "1. GENERATED", desc: "Generada por SQX o IA Semántica", color: "#94a3b8", step: 1 },
  { key: "BACKTESTED", label: "2. BACKTESTED", desc: "Backtest en muestra (IS)", color: "#38bdf8", step: 2 },
  { key: "OOS_PASSED", label: "3. OOS_PASSED", desc: "Supera ventana fuera de muestra", color: "#60a5fa", step: 3 },
  { key: "ROBUSTNESS_PASSED", label: "4. ROBUSTNESS_PASSED", desc: "Supera Monte Carlo & WFO", color: "#818cf8", step: 4 },
  { key: "EVIDENCE_APPROVED", label: "5. EVIDENCE_APPROVED", desc: "Aprobada por Evidence Gate Dual", color: "#a78bfa", step: 5 },
  { key: "CANDIDATE", label: "6. CANDIDATE", desc: "Candidato formal a producción", color: "#c084fc", step: 6 },
  { key: "INCUBATION_PAPER", label: "7. INCUBATION_PAPER", desc: "Incubación 14 días en sandbox", color: "#f59e0b", step: 7 },
  { key: "LIVE_ACTIVE", label: "8. LIVE_ACTIVE", desc: "Operación activa en real", color: "#34d399", step: 8 },
  { key: "REJECTED", label: "REJECTED", desc: "Rechazada por compuerta/drift", color: "#f43f5e", step: 99 },
  { key: "RETIRED", label: "RETIRED", desc: "Retirada por degradación", color: "#64748b", step: 99 },
];

interface TransitionRecord {
  strategy_id: string;
  from_status: string;
  to_status: string;
  timestamp_utc_ms: number;
  reason: string;
}

export default function CandidatosFSMPage() {
  const [registryData, setRegistryData] = useState<Record<string, string[]>>({});
  const [selectedStatus, setSelectedStatus] = useState<StrategyLifecycleStatus | "ALL">("ALL");
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const [strategyHistory, setStrategyHistory] = useState<TransitionRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);

  const fetchRegistry = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/v2/validation/registry/list");
      if (res.ok) {
        const data = await res.json();
        setRegistryData(data);
      }
    } catch {
      // quiet fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
  }, [fetchRegistry]);

  const loadHistory = async (strategyId: string) => {
    setSelectedStrategyId(strategyId);
    setHistoryLoading(true);
    try {
      const res = await fetch(`/api/v2/validation/registry/history/${encodeURIComponent(strategyId)}`);
      if (res.ok) {
        const historyData = await res.json();
        setStrategyHistory(historyData);
      } else {
        setStrategyHistory([]);
      }
    } catch {
      setStrategyHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Flatten strategy items
  const allStrategies: { id: string; status: StrategyLifecycleStatus }[] = [];
  Object.entries(registryData).forEach(([statusKey, ids]) => {
    if (ids && Array.isArray(ids)) {
      ids.forEach((id) => {
        allStrategies.push({ id, status: statusKey as StrategyLifecycleStatus });
      });
    }
  });

  const filteredStrategies = allStrategies.filter((s) => {
    if (selectedStatus === "ALL") return true;
    return s.status === selectedStatus;
  });

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. HEADER */}
      <div style={{ marginBottom: "24px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#64748b", fontSize: "12px", textDecoration: "none" }}>
            ← Command Center
          </Link>
          <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
          <span style={{ fontSize: "11px", fontWeight: 800, color: "#a78bfa", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
            FSM REGISTRY · 10 ESTADOS DISCRETOS
          </span>
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
          DAG de Ciclo de Vida de Candidatos (FSM Inmutable)
        </h1>
        <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
          Máquina de estados finitos estricta. Cada transición exige validación matemática determinista y firma SHA-256.
        </p>
      </div>

      {/* 2. DAG DE 10 ESTADOS DISCRETOS VISUALIZADOR */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "24px",
          overflowX: "auto",
        }}
      >
        <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginBottom: "16px" }}>
          FLUJO DETERMINISTA DE PROGRESIÓN FSM
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: "1100px", paddingBottom: "8px" }}>
          {FSM_STATES.filter((s) => s.step < 90).map((state, idx) => {
            const count = registryData[state.key]?.length || 0;
            const isSelected = selectedStatus === state.key;

            return (
              <React.Fragment key={state.key}>
                <div
                  onClick={() => setSelectedStatus(isSelected ? "ALL" : state.key)}
                  style={{
                    flex: 1,
                    background: isSelected ? `${state.color}25` : "rgba(255, 255, 255, 0.03)",
                    border: isSelected ? `1px solid ${state.color}` : "1px solid rgba(255, 255, 255, 0.06)",
                    borderRadius: "10px",
                    padding: "12px 14px",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                    <span style={{ fontSize: "10px", fontWeight: 900, color: state.color, fontFamily: "var(--font-mono, monospace)" }}>
                      {state.label}
                    </span>
                    <span
                      style={{
                        fontSize: "11px",
                        fontWeight: 900,
                        padding: "1px 6px",
                        borderRadius: "10px",
                        background: `${state.color}20`,
                        color: state.color,
                        fontFamily: "var(--font-mono, monospace)",
                      }}
                    >
                      {count}
                    </span>
                  </div>
                  <div style={{ fontSize: "10px", color: "#94a3b8" }}>{state.desc}</div>
                </div>

                {idx < 7 && (
                  <span style={{ color: "rgba(255, 255, 255, 0.2)", fontSize: "14px", fontWeight: 800 }}>
                    →
                  </span>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* TERMINAL STATES (REJECTED / RETIRED) */}
        <div style={{ display: "flex", gap: "12px", marginTop: "12px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px" }}>
          {FSM_STATES.filter((s) => s.step >= 90).map((state) => {
            const count = registryData[state.key]?.length || 0;
            const isSelected = selectedStatus === state.key;

            return (
              <div
                key={state.key}
                onClick={() => setSelectedStatus(isSelected ? "ALL" : state.key)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  background: isSelected ? `${state.color}25` : "rgba(255, 255, 255, 0.02)",
                  border: isSelected ? `1px solid ${state.color}` : "1px solid rgba(255, 255, 255, 0.05)",
                  borderRadius: "8px",
                  padding: "8px 14px",
                  cursor: "pointer",
                  fontSize: "11px",
                }}
              >
                <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: state.color }} />
                <span style={{ fontWeight: 800, color: state.color, fontFamily: "var(--font-mono, monospace)" }}>
                  {state.label}
                </span>
                <span style={{ color: "#64748b" }}>({count})</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. CANDIDATES LIST & DETAIL INSPECTOR */}
      <div style={{ display: "grid", gridTemplateColumns: selectedStrategyId ? "1fr 440px" : "1fr", gap: "20px" }}>
        {/* LEFT: CANDIDATES TABLE */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h2 style={{ fontSize: "15px", fontWeight: 800, color: "#fff", margin: 0 }}>
              Candidatos Registrados ({filteredStrategies.length})
            </h2>
            <button
              onClick={() => setSelectedStatus("ALL")}
              style={{
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "#94a3b8",
                fontSize: "10px",
                fontWeight: 700,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              MOSTRAR TODOS
            </button>
          </div>

          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", textAlign: "left", color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                  <th style={{ padding: "10px 12px" }}>ID ESTRATEGIA</th>
                  <th style={{ padding: "10px 12px" }}>ESTADO ACTUAL</th>
                  <th style={{ padding: "10px 12px" }}>PROCEDENCIA SHA-256</th>
                  <th style={{ padding: "10px 12px", textAlign: "right" }}>ACCIONES</th>
                </tr>
              </thead>
              <tbody>
                {filteredStrategies.length === 0 ? (
                  <tr>
                    <td colSpan={4} style={{ textAlign: "center", padding: "30px", color: "#64748b" }}>
                      {loading ? "Consultando Registry..." : "No hay candidatos en este estado FSM."}
                    </td>
                  </tr>
                ) : (
                  filteredStrategies.map((item) => {
                    const stateObj = FSM_STATES.find((s) => s.key === item.status) || FSM_STATES[0];
                    const isSelected = selectedStrategyId === item.id;

                    return (
                      <tr
                        key={item.id}
                        onClick={() => loadHistory(item.id)}
                        style={{
                          borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                          background: isSelected ? "rgba(167, 139, 250, 0.1)" : "transparent",
                          cursor: "pointer",
                          transition: "background 0.1s ease",
                        }}
                      >
                        <td style={{ padding: "12px", fontWeight: 800, color: "#fff", fontFamily: "var(--font-mono, monospace)" }}>
                          {item.id}
                        </td>
                        <td style={{ padding: "12px" }}>
                          <span
                            style={{
                              fontSize: "10px",
                              fontWeight: 800,
                              padding: "2px 8px",
                              borderRadius: "6px",
                              background: `${stateObj.color}20`,
                              color: stateObj.color,
                              border: `1px solid ${stateObj.color}40`,
                              fontFamily: "var(--font-mono, monospace)",
                            }}
                          >
                            {item.status}
                          </span>
                        </td>
                        <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#64748b", fontSize: "11px" }}>
                          {item.id.length >= 16 ? item.id.substring(0, 16) : `sha256_${item.id.toLowerCase()}`}...
                        </td>
                        <td style={{ padding: "12px", textAlign: "right" }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              loadHistory(item.id);
                            }}
                            style={{
                              padding: "4px 10px",
                              borderRadius: "6px",
                              background: "rgba(255, 255, 255, 0.05)",
                              border: "1px solid rgba(255, 255, 255, 0.1)",
                              color: "#cbd5e1",
                              fontSize: "11px",
                              cursor: "pointer",
                            }}
                          >
                            Historial →
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* RIGHT: HISTORY & TRANSITION INSPECTOR */}
        {selectedStrategyId && (
          <div
            style={{
              background: "rgba(16, 23, 34, 0.85)",
              backdropFilter: "blur(16px)",
              border: "1px solid rgba(167, 139, 250, 0.3)",
              borderRadius: "14px",
              padding: "20px",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
              <div>
                <div style={{ fontSize: "10px", fontWeight: 800, color: "#a78bfa", fontFamily: "var(--font-mono, monospace)" }}>
                  HISTORIAL DE AUDITORÍA
                </div>
                <h3 style={{ fontSize: "14px", fontWeight: 900, color: "#fff", margin: "2px 0 0 0", fontFamily: "var(--font-mono, monospace)" }}>
                  {selectedStrategyId}
                </h3>
              </div>
              <button
                onClick={() => setSelectedStrategyId(null)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#94a3b8",
                  fontSize: "16px",
                  cursor: "pointer",
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px" }}>
              {historyLoading ? (
                <div style={{ color: "#64748b", textAlign: "center", padding: "20px" }}>
                  Cargando trazabilidad inmutable...
                </div>
              ) : strategyHistory.length === 0 ? (
                <div style={{ background: "rgba(0,0,0,0.3)", borderRadius: "8px", padding: "14px", border: "1px solid rgba(255,255,255,0.05)", fontSize: "12px", color: "#94a3b8" }}>
                  Sin transiciones previas registradas. Estado inicial asignado en registro.
                </div>
              ) : (
                strategyHistory.map((rec, i) => (
                  <div
                    key={i}
                    style={{
                      background: "rgba(0, 0, 0, 0.4)",
                      border: "1px solid rgba(255, 255, 255, 0.06)",
                      borderRadius: "8px",
                      padding: "12px",
                      fontSize: "11px",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b", marginBottom: "4px", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                      <span>TRANSICIÓN #{i + 1}</span>
                      <span>{new Date(rec.timestamp_utc_ms).toISOString().slice(0, 19).replace("T", " ")}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px", margin: "6px 0", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                      <span style={{ color: "#94a3b8" }}>{rec.from_status}</span>
                      <span style={{ color: "#a78bfa" }}>→</span>
                      <span style={{ color: "#34d399" }}>{rec.to_status}</span>
                    </div>
                    <div style={{ color: "#cbd5e1", fontSize: "11px", marginTop: "4px" }}>
                      <strong>Motivo:</strong> {rec.reason}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
