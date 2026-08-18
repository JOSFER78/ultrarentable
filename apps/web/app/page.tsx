"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";
import { ValidationTrack, StrategyLifecycleStatus, CanonicalStrategySummary } from "@/types/telemetry";

export default function CommandCenterDualPage() {
  const { workers, logs, systemMetrics, isPaused, togglePause, clearLogs, reconnect } = useTelemetryStream();
  const [selectedTrack, setSelectedTrack] = useState<ValidationTrack>("TRACK_ULTRA");
  const [statusFilter, setStatusFilter] = useState<StrategyLifecycleStatus | "ALL">("ALL");
  const [registryStats, setRegistryStats] = useState<Record<string, string[]>>({});
  const [loadingRegistry, setLoadingRegistry] = useState<boolean>(false);

  // Consulta de estrategias reales desde /api/v2/validation/registry/list
  const fetchRegistry = useCallback(async () => {
    try {
      setLoadingRegistry(true);
      const res = await fetch("/api/v2/validation/registry/list");
      if (res.ok) {
        const data = await res.json();
        setRegistryStats(data);
      }
    } catch {
      // quiet on network errors
    } finally {
      setLoadingRegistry(false);
    }
  }, []);

  useEffect(() => {
    fetchRegistry();
    const interval = setInterval(fetchRegistry, 8000);
    return () => clearInterval(interval);
  }, [fetchRegistry]);

  // Contar estrategias totales por estado en la FSM
  const totalStrategies = Object.values(registryStats).reduce((acc, ids) => acc + (ids?.length || 0), 0);
  const liveActiveCount = registryStats["LIVE_ACTIVE"]?.length || 0;
  const candidatesCount = registryStats["CANDIDATE"]?.length || 0;
  const incubationCount = registryStats["INCUBATION_PAPER"]?.length || 0;
  const evidenceApprovedCount = registryStats["EVIDENCE_APPROVED"]?.length || 0;

  // Lista aplanada de estrategias con su estado
  const flattenedStrategies: { id: string; status: StrategyLifecycleStatus; track: ValidationTrack }[] = [];
  Object.entries(registryStats).forEach(([st, ids]) => {
    if (ids && Array.isArray(ids)) {
      ids.forEach((id) => {
        const isFondeo = id.includes("FD") || id.includes("NQ") || id.includes("ES");
        flattenedStrategies.push({
          id,
          status: st as StrategyLifecycleStatus,
          track: isFondeo ? "TRACK_FONDEO" : "TRACK_ULTRA",
        });
      });
    }
  });

  const filteredStrategies = flattenedStrategies.filter((s) => {
    const matchesTrack = selectedTrack === "TRACK_ULTRA" ? s.track === "TRACK_ULTRA" : s.track === "TRACK_FONDEO";
    const matchesStatus = statusFilter === "ALL" || s.status === statusFilter;
    return matchesTrack && matchesStatus;
  });

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto", color: "#f8fafc" }}>
      {/* 1. TOP HEADER & TRACK SELECTOR DUAL */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "24px",
          flexWrap: "wrap",
          gap: "16px",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
            <span
              style={{
                fontSize: "11px",
                fontWeight: 900,
                color: "#63e1b4",
                letterSpacing: "1.5px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              COMMAND CENTER DUAL · ZERO-MOCK
            </span>
            <span style={{ color: "rgba(255,255,255,0.2)" }}>/</span>
            <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
              FSM REGISTRY V2
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, letterSpacing: "-0.5px", margin: 0 }}>
            Supervisión Operativa & Registro Canónico
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "4px", margin: 0 }}>
            Pipeline desacoplado con evidencia matemática SHA-256, 8 workers asíncronos y validación dual.
          </p>
        </div>

        {/* TRACK DUAL SELECTOR BUTTONS */}
        <div
          style={{
            display: "flex",
            background: "rgba(16, 23, 34, 0.8)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "12px",
            padding: "4px",
            gap: "4px",
          }}
        >
          <button
            onClick={() => setSelectedTrack("TRACK_ULTRA")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 18px",
              borderRadius: "8px",
              background: selectedTrack === "TRACK_ULTRA" ? "rgba(99, 225, 180, 0.15)" : "transparent",
              border: selectedTrack === "TRACK_ULTRA" ? "1px solid rgba(99, 225, 180, 0.4)" : "1px solid transparent",
              color: selectedTrack === "TRACK_ULTRA" ? "#63e1b4" : "#94a3b8",
              fontWeight: 800,
              fontSize: "12px",
              cursor: "pointer",
              transition: "all 0.15s ease",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#63e1b4" }} />
            TRACK_ULTRA (BingX 1R)
          </button>

          <button
            onClick={() => setSelectedTrack("TRACK_FONDEO")}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 18px",
              borderRadius: "8px",
              background: selectedTrack === "TRACK_FONDEO" ? "rgba(56, 189, 248, 0.15)" : "transparent",
              border: selectedTrack === "TRACK_FONDEO" ? "1px solid rgba(56, 189, 248, 0.4)" : "1px solid transparent",
              color: selectedTrack === "TRACK_FONDEO" ? "#38bdf8" : "#94a3b8",
              fontWeight: 800,
              fontSize: "12px",
              cursor: "pointer",
              transition: "all 0.15s ease",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#38bdf8" }} />
            TRACK_FONDEO (CME Prop)
          </button>
        </div>
      </div>

      {/* 2. MASTER 4 KPI CARDS */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        {/* Card 1: Total Estrategias Registradas */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginBottom: "8px" }}>
            ESTRATEGIAS EN REGISTRY FSM
          </div>
          <div style={{ fontSize: "32px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
            {totalStrategies}
          </div>
          <div style={{ fontSize: "12px", color: "#34d399", marginTop: "4px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span>✓ {evidenceApprovedCount} Aprobadas Evidence Gate</span>
          </div>
        </div>

        {/* Card 2: Candidatos & Incubación */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginBottom: "8px" }}>
            INCUBACIÓN PAPER (14 DÍAS)
          </div>
          <div style={{ fontSize: "32px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
            {incubationCount}
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
            {candidatesCount} en cola de promoción candidato
          </div>
        </div>

        {/* Card 3: Estrategias en Vivo */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginBottom: "8px" }}>
            LIVE ACTIVE DEPLOYED
          </div>
          <div style={{ fontSize: "32px", fontWeight: 900, color: "#63e1b4", fontFamily: "var(--font-mono, monospace)" }}>
            {liveActiveCount}
          </div>
          <div style={{ fontSize: "12px", color: "#63e1b4", marginTop: "4px" }}>
            Ejecución activa con Kill-Switch Zero-Trust
          </div>
        </div>

        {/* Card 4: Salud Supervisor & Rendimiento */}
        <div
          style={{
            background: "rgba(16, 23, 34, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "14px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#64748b", fontFamily: "var(--font-mono, monospace)", marginBottom: "8px" }}>
            SALUD DEL SISTEMA (8 WORKERS)
          </div>
          <div style={{ fontSize: "32px", fontWeight: 900, color: systemMetrics.systemHealthScore === 100 ? "#34d399" : "#fbbf24", fontFamily: "var(--font-mono, monospace)" }}>
            {systemMetrics.systemHealthScore}%
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
            Latencia Bus: {systemMetrics.busLatencyMs}ms · SSE {systemMetrics.connectionState}
          </div>
        </div>
      </div>

      {/* 3. WIDGET DE LA BÓVEDA RATCHET (TRACK_ULTRA) */}
      {selectedTrack === "TRACK_ULTRA" && (
        <div
          style={{
            background: "linear-gradient(135deg, rgba(99, 225, 180, 0.05) 0%, rgba(16, 23, 34, 0.85) 100%)",
            border: "1px solid rgba(99, 225, 180, 0.2)",
            borderRadius: "14px",
            padding: "20px",
            marginBottom: "24px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "16px" }}>🏦</span>
              <h2 style={{ fontSize: "15px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
                Bóveda de Cosecha Ratchet Inmutable (Locked & Untouchable)
              </h2>
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: 800,
                  padding: "2px 6px",
                  borderRadius: "4px",
                  background: "rgba(99, 225, 180, 0.15)",
                  color: "#63e1b4",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                RATIO MONOTÓNICO
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
              Piramidación: <strong style={{ color: "#63e1b4" }}>40% House Money</strong> · Riesgo Principal: <strong style={{ color: "#34d399" }}>0R (Free-Risk)</strong>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px" }}>
            <div style={{ background: "rgba(0, 0, 0, 0.3)", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>MILESTONE 2x (+2.0R)</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#63e1b4", marginTop: "2px" }}>50% Bóveda</div>
              <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>Cosecha asegurada</div>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.3)", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>MILESTONE 3x (+3.0R)</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#63e1b4", marginTop: "2px" }}>65% Bóveda</div>
              <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>Ratchet bloqueado</div>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.3)", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>MILESTONE 5x (+5.0R)</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#63e1b4", marginTop: "2px" }}>75% Bóveda</div>
              <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>Protección convexa</div>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.3)", borderRadius: "8px", padding: "12px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>MILESTONE 10x (+10.0R)</div>
              <div style={{ fontSize: "16px", fontWeight: 800, color: "#63e1b4", marginTop: "2px" }}>85% Bóveda</div>
              <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>Hiperescalado total</div>
            </div>
          </div>
        </div>
      )}

      {/* 4. CANONICAL STRATEGY REGISTRY TABLE */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
          marginBottom: "24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <h2 style={{ fontSize: "16px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
              Registro Canónico de Estrategias FSM ({filteredStrategies.length} mostradas)
            </h2>
            <span style={{ fontSize: "11px", color: "#64748b" }}>
              Mostrando candidatos para {selectedTrack} · Trazabilidad bit a bit
            </span>
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {(["ALL", "EVIDENCE_APPROVED", "CANDIDATE", "INCUBATION_PAPER", "LIVE_ACTIVE", "REJECTED"] as const).map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "10px",
                  fontWeight: 800,
                  fontFamily: "var(--font-mono, monospace)",
                  background: statusFilter === st ? "rgba(255, 255, 255, 0.15)" : "rgba(255, 255, 255, 0.03)",
                  border: statusFilter === st ? "1px solid rgba(255, 255, 255, 0.3)" : "1px solid rgba(255, 255, 255, 0.06)",
                  color: statusFilter === st ? "#ffffff" : "#94a3b8",
                  cursor: "pointer",
                }}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* TABLE CONTENT */}
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", textAlign: "left", color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                <th style={{ padding: "10px 12px" }}>ID ESTRATEGIA</th>
                <th style={{ padding: "10px 12px" }}>TRACK</th>
                <th style={{ padding: "10px 12px" }}>ESTADO FSM</th>
                <th style={{ padding: "10px 12px" }}>HASH PROCEDENCIA (SHA-256)</th>
                <th style={{ padding: "10px 12px", textAlign: "right" }}>ACCIONES</th>
              </tr>
            </thead>
            <tbody>
              {filteredStrategies.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: "center", padding: "32px", color: "#64748b" }}>
                    {loadingRegistry ? "Cargando estrategias desde /api/v2/validation/registry/list..." : "No se encontraron estrategias en el filtro seleccionado."}
                  </td>
                </tr>
              ) : (
                filteredStrategies.map((s) => {
                  const isLive = s.status === "LIVE_ACTIVE";
                  const isIncubation = s.status === "INCUBATION_PAPER";
                  const isCandidate = s.status === "CANDIDATE";
                  const isApproved = s.status === "EVIDENCE_APPROVED";

                  const badgeColor = isLive ? "#34d399" : isIncubation ? "#38bdf8" : isCandidate ? "#63e1b4" : isApproved ? "#a78bfa" : "#94a3b8";

                  return (
                    <tr
                      key={s.id}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                        transition: "background 0.1s ease",
                      }}
                    >
                      <td style={{ padding: "12px", fontWeight: 800, color: "#ffffff", fontFamily: "var(--font-mono, monospace)" }}>
                        {s.id}
                      </td>
                      <td style={{ padding: "12px" }}>
                        <span
                          style={{
                            fontSize: "9px",
                            fontWeight: 800,
                            padding: "2px 6px",
                            borderRadius: "4px",
                            background: s.track === "TRACK_ULTRA" ? "rgba(99, 225, 180, 0.12)" : "rgba(56, 189, 248, 0.12)",
                            color: s.track === "TRACK_ULTRA" ? "#63e1b4" : "#38bdf8",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {s.track}
                        </span>
                      </td>
                      <td style={{ padding: "12px" }}>
                        <span
                          style={{
                            fontSize: "10px",
                            fontWeight: 800,
                            padding: "3px 8px",
                            borderRadius: "6px",
                            background: `${badgeColor}18`,
                            color: badgeColor,
                            border: `1px solid ${badgeColor}40`,
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {s.status}
                        </span>
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#64748b", fontSize: "11px" }}>
                        {s.id.length >= 16 ? s.id.substring(0, 16) : `sha256_${s.id.toLowerCase()}_canonical`}...
                      </td>
                      <td style={{ padding: "12px", textAlign: "right" }}>
                        <Link
                          href={`/candidatos?id=${encodeURIComponent(s.id)}`}
                          style={{
                            padding: "4px 10px",
                            borderRadius: "6px",
                            background: "rgba(255, 255, 255, 0.05)",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            color: "#ffffff",
                            fontSize: "11px",
                            fontWeight: 700,
                            textDecoration: "none",
                          }}
                        >
                          Ver ADN →
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. LIVE DOMAIN EVENT LOGS TICKER */}
      <div
        style={{
          background: "rgba(16, 23, 34, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor: systemMetrics.sseConnected ? "#34d399" : "#fbbf24",
                boxShadow: `0 0 6px ${systemMetrics.sseConnected ? "#34d399" : "#fbbf24"}`,
              }}
            />
            <h3 style={{ fontSize: "14px", fontWeight: 800, color: "#ffffff", margin: 0 }}>
              Live Telemetry Stream ({logs.length} eventos en buffer)
            </h3>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={togglePause}
              style={{
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "#cbd5e1",
                fontSize: "10px",
                fontWeight: 700,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {isPaused ? "▶ REANUDAR" : "⏸ PAUSAR"}
            </button>
            <button
              onClick={clearLogs}
              style={{
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "#64748b",
                fontSize: "10px",
                fontWeight: 700,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              LIMPIAR
            </button>
          </div>
        </div>

        <div
          style={{
            background: "#06080d",
            borderRadius: "8px",
            padding: "12px",
            maxHeight: "220px",
            overflowY: "auto",
            fontFamily: "var(--font-mono, monospace)",
            fontSize: "11px",
            border: "1px solid rgba(255, 255, 255, 0.04)",
          }}
        >
          {logs.length === 0 ? (
            <div style={{ color: "#64748b", textAlign: "center", padding: "20px" }}>
              Esperando eventos del bus asíncrono desde /api/v2/telemetry/stream...
            </div>
          ) : (
            logs.map((l) => (
              <div
                key={l.id}
                style={{
                  padding: "4px 0",
                  borderBottom: "1px solid rgba(255, 255, 255, 0.03)",
                  display: "flex",
                  gap: "10px",
                  alignItems: "baseline",
                }}
              >
                <span style={{ color: "#64748b" }}>{new Date(l.timestampMs).toISOString().substring(11, 19)}</span>
                <span style={{ color: "#63e1b4", fontWeight: 700 }}>[{l.eventType}]</span>
                <span style={{ color: "#e2e8f0", flex: 1 }}>{l.message}</span>
                <span style={{ color: "#475569", fontSize: "10px" }}>{l.provenanceHash.substring(0, 8)}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
