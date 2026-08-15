"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface Strategy {
  strategyId: string;
  name: string;
  version: string;
  family: string;
  author: string;
  canonicalHash: string;
  dslJson: string;
  validationStatus: string;
  createdAt: string;
}

export default function StrategyInspectorPage() {
  const router = useRouter();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [runningBt, setRunningBt] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStrategies = async () => {
    try {
      const data = await api.getStrategies();
      setStrategies(data);
      if (data.length > 0 && !selectedStrategy) setSelectedStrategy(data[0]);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    fetchStrategies();
  }, []);

  const handleRunBacktestForStrategy = async () => {
    if (!selectedStrategy) return;
    setRunningBt(true);
    try {
      const datasets = await api.getDatasets();
      const approved = datasets.filter((d: any) => d.status === "APPROVED");
      if (approved.length === 0) {
        alert("No hay datasets aprobados. Primero aprueba un dataset en Data Pipeline.");
        router.push("/data");
        return;
      }
      await api.runFastBacktest(selectedStrategy.strategyId, approved[0].datasetId, 10000);
      alert(`¡Backtest ejecutado correctamente en FastEngine! Redirigiendo a la consola...`);
      router.push("/backtest");
    } catch (err: any) {
      alert(`Error al ejecutar backtest: ${err.message}`);
    } finally {
      setRunningBt(false);
    }
  };

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Inspector de Estrategias Generadas (Solo Lectura)</h1>
        <p className="page-desc">
          Inspección de candidatos generados autónomamente por la Fábrica de Estrategias. Árbol AST, versión, linaje y hash canónico SHA-256.
        </p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        {/* Candidate List */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">[CATÁLOGO] Candidatos Generados ({strategies.length})</h2>
          </div>

          {error ? (
            <div style={{ padding: 16, color: "var(--danger)" }}>SERVICE_UNAVAILABLE: {error}</div>
          ) : strategies.length === 0 ? (
            <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
              NO_DATA_AVAILABLE — Pulsa INICIAR AUTOPILOTO ULTRA en el menú principal para generar candidatos.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 450, overflowY: "auto" }}>
              {strategies.map((s) => (
                <div
                  key={s.strategyId}
                  onClick={() => setSelectedStrategy(s)}
                  style={{
                    padding: 12,
                    borderRadius: "var(--radius-md)",
                    border: selectedStrategy?.strategyId === s.strategyId ? "1px solid var(--accent)" : "1px solid var(--border)",
                    background: selectedStrategy?.strategyId === s.strategyId ? "rgba(16,185,129,0.08)" : "var(--bg-2)",
                    cursor: "pointer",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>{s.name}</div>
                    <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: "rgba(16,185,129,0.2)", color: "var(--success)" }}>
                      {s.validationStatus}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    Autor: {s.author} · Familia: {s.family}
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent)", marginTop: 4 }}>
                    ID: {s.strategyId}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Candidate AST/IR Viewer */}
        <div className="card">
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 className="card-title">Detalle de Estructura AST / IR</h2>
            {selectedStrategy && (
              <button
                onClick={handleRunBacktestForStrategy}
                disabled={runningBt}
                className="btn btn-sm btn-primary"
              >
                {runningBt ? "Ejecutando..." : "Probar en Backtest Real"}
              </button>
            )}
          </div>

          {selectedStrategy ? (
            <div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: "var(--text-primary)" }}>{selectedStrategy.name}</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                  Hash Canónico SHA-256: <code>{selectedStrategy.canonicalHash}</code>
                </div>
              </div>

              <div>
                <label style={labelStyle}>Árbol DSL Declarativo (v1.0.0)</label>
                <pre style={{ background: "var(--bg-1)", padding: 12, borderRadius: "var(--radius-md)", border: "1px solid var(--border)", fontSize: 11, fontFamily: "var(--font-mono)", maxHeight: 320, overflowY: "auto" }}>
                  {JSON.stringify(JSON.parse(selectedStrategy.dslJson || "{}"), null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div style={{ padding: "60px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
              Selecciona una estrategia a la izquierda para inspeccionar.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--text-muted)",
  display: "block",
  marginBottom: 4,
  textTransform: "uppercase",
};
