"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface Dataset {
  datasetId: string;
  venue: string;
  symbol: string;
  interval: string;
  startTime: number;
  endTime: number;
  recordCount: number;
  gapCount: number;
  status: "APPROVED" | "QUARANTINED" | "VALIDATING" | "REJECTED";
}

const RESEARCH_DAYS = 160;

export default function DataPipelinePage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [preparing, setPreparing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setDatasets(await api.getDatasets());
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const prepareEth = async () => {
    setPreparing(true);
    setMessage("Descargando ETH de BingX, comprobando continuidad y creando 1m, 5m, 15m y 1h…");
    setError(null);
    try {
      const result = await api.prepareEthResearch(RESEARCH_DAYS);
      setMessage(
        `Datos listos: ${result.datasets.length} datasets aprobados desde ${result.sourcePages} páginas reales de BingX.`,
      );
      await refresh();
    } catch (reason) {
      setMessage(null);
      setError(reason instanceof Error ? reason.message : "ETH_RESEARCH_INGESTION_FAILED");
    } finally {
      setPreparing(false);
    }
  };

  const ethDatasets = datasets.filter((dataset) => dataset.symbol === "ETH-USDT");

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Datos automáticos de Ethereum</h1>
        <p className="page-desc">
          Un solo proceso descarga datos reales de BingX, verifica huecos y checksums, crea todos los
          marcos temporales y los aprueba únicamente si pasan la validación.
        </p>
      </div>

      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <div>
            <h2 className="card-title">ETH-USDT · prueba de investigación</h2>
            <p style={{ marginTop: 8, color: "var(--text-muted)", fontSize: 13 }}>
              Preparará automáticamente {RESEARCH_DAYS} días en 1m, 5m, 15m y 1h. No tienes que elegir
              límites, aprobar archivos ni rellenar parámetros técnicos.
            </p>
          </div>
          <button type="button" className="btn btn-primary" onClick={prepareEth} disabled={preparing}>
            {preparing ? "Preparando datos ETH…" : "Preparar datos ETH"}
          </button>
        </div>
        {message ? (
          <div style={{ marginTop: 16, color: "var(--success)", fontSize: 13 }}>{message}</div>
        ) : null}
        {error ? (
          <div style={{ marginTop: 16, color: "var(--danger)", fontSize: 13 }}>
            No se pudo completar la preparación: {error}
          </div>
        ) : null}
      </div>

      <div className="card animate-in">
        <div className="card-header">
          <h2 className="card-title">Datasets ETH verificados ({ethDatasets.length})</h2>
        </div>
        {ethDatasets.length === 0 ? (
          <div
            style={{
              padding: "40px 0",
              textAlign: "center",
              color: "var(--text-muted)",
              fontSize: 13,
            }}
          >
            Todavía no hay datos aprobados. Pulsa “Preparar datos ETH”.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Intervalo</th>
                  <th>Velas</th>
                  <th>Desde</th>
                  <th>Hasta</th>
                  <th>Huecos</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {ethDatasets.map((dataset) => (
                  <tr key={dataset.datasetId}>
                    <td style={{ fontWeight: 700 }}>{dataset.interval}</td>
                    <td>{dataset.recordCount.toLocaleString("es-ES")}</td>
                    <td>{new Date(dataset.startTime).toLocaleDateString("es-ES")}</td>
                    <td>{new Date(dataset.endTime).toLocaleDateString("es-ES")}</td>
                    <td>{dataset.gapCount}</td>
                    <td>
                      <span
                        className={`badge ${
                          dataset.status === "APPROVED" ? "badge-success" : "badge-danger"
                        }`}
                      >
                        {dataset.status === "APPROVED" ? "VERIFICADO" : dataset.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
