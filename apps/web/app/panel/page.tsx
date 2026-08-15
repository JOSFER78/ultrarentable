"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface AutopilotStatus {
  status: string;
  runId: string | null;
  mode: string;
  currentSymbol: string | null;
  currentInterval: string | null;
  bestCandidateId: string | null;
  bestFastReturnPct: number;
  bestCanonicalReturnPct: number | null;
  evaluatedStrategiesCount: number;
  exploredSymbolsCount: number;
  createdAt: string | null;
}

interface Decision {
  decisionId: string;
  module: string;
  decision: string;
  reason: string;
  createdAt: string;
}

export default function PanelPage() {
  const [autopilotStatus, setAutopilotStatus] = useState<AutopilotStatus | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dataBlocked = autopilotStatus?.status === "BLOCKED_DATA";
  const activeStatuses = new Set(["QUEUED", "SCANNING", "RUNNING", "PAUSED"]);
  const isActive = activeStatuses.has(autopilotStatus?.status || "");
  const isValidated = autopilotStatus?.status === "VALIDATED_CANDIDATE";

  const fetchAutopilotData = async () => {
    try {
      const [dataStatus, dataDecisions] = await Promise.all([
        api.getAutopilotStatus(),
        api.getAutopilotDecisions(),
      ]);
      setAutopilotStatus(dataStatus);
      setDecisions(dataDecisions);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    fetchAutopilotData();
    const interval = setInterval(fetchAutopilotData, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (action: "start" | "pause" | "resume" | "stop") => {
    setLoading(true);
    try {
      if (action === "start") await api.startAutopilot();
      else if (action === "pause") await api.pauseAutopilot();
      else if (action === "resume") await api.resumeAutopilot();
      else if (action === "stop") await api.stopAutopilot();
      await fetchAutopilotData();
    } catch (err: any) {
      alert(`Error al ejecutar acción: ${(err as any).message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Panel de Control</h1>
        <p className="page-desc">
          Estado global del sistema, seguimiento del proceso y decisiones autónomas.
          Es la vista de operación para quienes quieren controlar el detalle técnico.
        </p>
      </div>

      {/* Atajo a la búsqueda */}
      <div className="card animate-in" style={{ padding: 18, marginBottom: 24, display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", justifyContent: "space-between", background: "var(--bg-2)", border: "1px solid var(--border)" }}>
        <div style={{ fontSize: 13, color: "var(--text-muted)", maxWidth: 640, lineHeight: 1.6 }}>
          Para el usuario no técnico: ve directamente a <strong>Buscar Estrategias</strong> y elige tu camino. Este panel expone el detalle de ingeniería.
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <Link href="/" className="btn btn-primary" style={{ textDecoration: "none" }}>
            Buscar Estrategias
          </Link>
        </div>
      </div>

      {error ? (
        <div className="card animate-in" style={{ borderColor: "var(--danger)", padding: 20, marginBottom: 24 }}>
          <div style={{ color: "var(--danger)", fontWeight: 700, fontSize: 16, marginBottom: 4 }}>
            [ALERTA] SERVICE_UNAVAILABLE
          </div>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            No se pudo conectar con el backend FastAPI en <code>http://127.0.0.1:8000</code>.
          </p>
        </div>
      ) : null}

      {/* AUTOPILOT CONTROL */}
      <div className="card animate-in" style={{ padding: 24, marginBottom: 24, textAlign: "center", background: "var(--bg-2)", border: "1px solid var(--accent)" }}>
        <div style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-muted)", fontWeight: 700, marginBottom: 8 }}>
          Estado del proceso: <span style={{ color: isActive || isValidated ? "var(--success)" : "var(--warning)" }}>{autopilotStatus?.status || "READY"}</span>
        </div>
        <h2 style={{ fontSize: 24, fontWeight: 800, color: "var(--text-primary)", marginBottom: 16 }}>
          {dataBlocked
            ? "Fase 1 detenida: faltan datos históricos verificados"
            : autopilotStatus?.currentSymbol
              ? `Investigando ${autopilotStatus.currentSymbol} (${autopilotStatus.currentInterval})`
              : "Listo para la búsqueda autónoma de 1 clic"}
        </h2>
        <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
          <button onClick={() => handleAction("start")} disabled={loading || isActive} className="btn btn-primary btn-lg">
            {loading ? "[VERIFICANDO...]" : isActive ? "[EN CURSO]" : dataBlocked ? "[REINTENTAR VERIFICACIÓN]" : "[INICIAR PROCESO]"}
          </button>
          <button onClick={() => handleAction("pause")} disabled={loading} className="btn btn-secondary">[PAUSAR]</button>
          <button onClick={() => handleAction("resume")} disabled={loading} className="btn btn-secondary">[REANUDAR]</button>
          <button onClick={() => handleAction("stop")} disabled={loading} className="btn btn-danger">[DETENER AUTOPILOT]</button>
        </div>
      </div>

      {/* STATS */}
      <div className="grid-stats animate-in" style={{ marginBottom: 24 }}>
        <StatCard label="Mejor Retorno Validado" value={`${(autopilotStatus?.bestFastReturnPct ?? 0).toFixed(1)}%`} icon="[BEST]" desc="Solo tras lockbox" color="var(--success)" />
        <StatCard label="Estrategias Evaluadas" value={autopilotStatus?.evaluatedStrategiesCount ?? 0} icon="[EVAL]" desc="Población Autónoma" color="var(--accent)" />
        <StatCard label="Mercados Verificados" value={autopilotStatus?.exploredSymbolsCount ?? 0} icon="[SCAN]" desc="UniverseScanner" color="var(--info)" />
        <StatCard label="Validación Adversarial" value={autopilotStatus?.bestCanonicalReturnPct ? `${autopilotStatus.bestCanonicalReturnPct.toFixed(1)}%` : "PENDIENTE"} icon="[LOCK]" desc="Walk-forward y lockbox" color="var(--warning)" />
      </div>

      {/* DECISIONS LOG */}
      <div className="card animate-in">
        <div className="card-header">
          <h2 className="card-title">Registro de Decisiones Autónomas ({decisions.length})</h2>
        </div>
        {decisions.length === 0 ? (
          <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
            NO_DATA_AVAILABLE — Lanza una búsqueda desde la consola principal.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 350, overflowY: "auto" }}>
            {decisions.map((d) => (
              <div key={d.decisionId} style={{ padding: 12, borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg-2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "var(--accent)" }}>{d.module}</span>
                  <span style={{ fontSize: 10, color: "var(--text-muted)" }}>{new Date(d.createdAt).toLocaleTimeString()}</span>
                </div>
                <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)", marginTop: 4 }}>{d.decision}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>{d.reason}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, desc, color }: { label: string; value: string | number; icon: string; desc: string; color: string }) {
  return (
    <div className="card stat-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <span className="stat-label">{label}</span>
        <span style={{ fontSize: 20 }}>{icon}</span>
      </div>
      <span className="stat-value" style={{ color }}>{value}</span>
      <span className="stat-change neutral">{desc}</span>
    </div>
  );
}
