"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface ApprovedDataset {
  datasetId: string;
  symbol: string;
  interval: string;
  recordCount: number;
  status: string;
}

interface Strategy {
  strategyId: string;
  name: string;
}

interface BacktestResult {
  backtestId: string;
  strategyId: string;
  datasetId: string;
  engineType: string;
  initialCapital: number;
  leverage: number;
  finalEquity: number;
  netReturnPct: number;
  maxDrawdownPct: number;
  winRate: number;
  tradesCount: number;
  profitFactor: number;
  checksum: string;
  status: string;
  createdAt: string;
}

export default function BacktestConsolePage() {
  const [datasets, setDatasets] = useState<ApprovedDataset[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);

  const [selectedDataset, setSelectedDataset] = useState("");
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [capital, setCapital] = useState(10000);
  const [leverage, setLeverage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [activeLedger, setActiveLedger] = useState<any[] | null>(null);
  const [activeBacktestId, setActiveBacktestId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadOptions = async () => {
    try {
      const [allDs, allStrat, allBt] = await Promise.all([
        api.getDatasets(),
        api.getStrategies(),
        api.getBacktests(),
      ]);
      const approvedOnly = allDs.filter((d: any) => d.status === "APPROVED");
      setDatasets(approvedOnly);
      setStrategies(allStrat);
      setBacktests(allBt);

      if (approvedOnly.length > 0 && !selectedDataset) setSelectedDataset(approvedOnly[0].datasetId);
      if (allStrat.length > 0 && !selectedStrategy) setSelectedStrategy(allStrat[0].strategyId);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    loadOptions();
  }, []);

  const handleRunBacktest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDataset || !selectedStrategy) {
      alert("Selecciona un dataset aprobado y una estrategia válida");
      return;
    }
    setLoading(true);
    try {
      await api.runFastBacktest(selectedStrategy, selectedDataset, capital);
      await loadOptions();
    } catch (err: any) {
      alert(`Error en backtest: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewLedger = async (backtestId: string) => {
    try {
      const trades = await api.getBacktestTrades(backtestId);
      setActiveLedger(trades);
      setActiveBacktestId(backtestId);
    } catch (err: any) {
      alert(`No se pudo cargar el ledger: ${err.message}`);
    }
  };

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Consola de Backtesting Real (FastEngine)</h1>
        <p className="page-desc">
          Ejecución estricta de backtests deterministas sobre datasets BingX aprobados y persistencia inmutable en SQLite.
        </p>
      </div>

      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h2 className="card-title">[MOTOR] Ejecutar Nuevo Backtest</h2>
        </div>

        {error ? (
          <div style={{ padding: 16, color: "var(--danger)" }}>SERVICE_UNAVAILABLE: {error}</div>
        ) : datasets.length === 0 ? (
          <div style={{ padding: "24px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            [ADVERTENCIA] No hay datasets aprobados disponibles. Ve a la pantalla <Link href="/data" style={{ color: "var(--accent)" }}>Data Pipeline</Link> para descargar y aprobar un dataset real.
          </div>
        ) : (
          <form onSubmit={handleRunBacktest} style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12, alignItems: "end" }}>
            <div>
              <label style={labelStyle}>Dataset Aprobado</label>
              <select value={selectedDataset} onChange={(e) => setSelectedDataset(e.target.value)} style={inputStyle}>
                {datasets.map((d) => (
                  <option key={d.datasetId} value={d.datasetId}>
                    {d.symbol} ({d.interval}) — {d.recordCount} registros
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Estrategia DSL</label>
              <select value={selectedStrategy} onChange={(e) => setSelectedStrategy(e.target.value)} style={inputStyle}>
                {strategies.map((s) => (
                  <option key={s.strategyId} value={s.strategyId}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Capital Inicial ($)</label>
              <input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))} style={inputStyle} min={100} />
            </div>
            <div>
              <label style={labelStyle}>Apalancamiento (x)</label>
              <input type="number" value={leverage} onChange={(e) => setLeverage(Number(e.target.value))} style={inputStyle} min={1} max={125} />
            </div>
            <div>
              <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%" }}>
                {loading ? "Ejecutando..." : "EJECUTAR BACKTEST REAL"}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Ledger Modal inspection */}
      {activeLedger && (
        <div className="card animate-in" style={{ marginBottom: 24, border: "1px solid var(--accent)" }}>
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 className="card-title">Registro de Trades (Ledger): {activeBacktestId}</h2>
            <button onClick={() => setActiveLedger(null)} className="btn btn-sm btn-danger">Cerrar</button>
          </div>
          <div style={{ maxHeight: 300, overflowY: "auto" }}>
            <pre style={{ background: "var(--bg-1)", padding: 12, borderRadius: "var(--radius-md)", fontSize: 11, fontFamily: "var(--font-mono)" }}>
              {JSON.stringify(activeLedger, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Results History */}
      <div className="card animate-in">
        <div className="card-header">
          <h2 className="card-title">Historial de Resultados en Backend ({backtests.length})</h2>
        </div>

        {backtests.length === 0 ? (
          <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
            NO_DATA_AVAILABLE — Selecciona un dataset y estrategia arriba para ejecutar tu primer backtest.
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID Backtest</th>
                  <th>Motor</th>
                  <th>Capital Inicial</th>
                  <th>Final Equity</th>
                  <th>Retorno Neto</th>
                  <th>Max DD</th>
                  <th>Win Rate</th>
                  <th>Trades</th>
                  <th>Profit Factor</th>
                  <th>Ledger</th>
                </tr>
              </thead>
              <tbody>
                {backtests.map((b) => (
                  <tr key={b.backtestId}>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{b.backtestId}</td>
                    <td>
                      <span className={`badge ${b.engineType === "CANONICAL" ? "badge-success" : "badge-warning"}`}>
                        {b.engineType}
                      </span>
                    </td>
                    <td>${b.initialCapital.toFixed(2)}</td>
                    <td style={{ fontWeight: 700 }}>${b.finalEquity.toFixed(2)}</td>
                    <td style={{ color: b.netReturnPct >= 0 ? "var(--long)" : "var(--short)", fontWeight: 700 }}>
                      {b.netReturnPct >= 0 ? `+${b.netReturnPct.toFixed(2)}%` : `${b.netReturnPct.toFixed(2)}%`}
                    </td>
                    <td style={{ color: "var(--short)" }}>-{b.maxDrawdownPct.toFixed(2)}%</td>
                    <td>{b.winRate.toFixed(1)}%</td>
                    <td>{b.tradesCount}</td>
                    <td>{b.profitFactor.toFixed(2)}</td>
                    <td>
                      <button onClick={() => handleViewLedger(b.backtestId)} className="btn btn-sm" style={{ background: "var(--bg-1)", fontSize: 11 }}>
                        Ver Trades
                      </button>
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

const labelStyle: React.CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: "var(--text-muted)",
  display: "block",
  marginBottom: 4,
  textTransform: "uppercase",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  background: "var(--bg-2)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius-md)",
  padding: "8px 12px",
  color: "var(--text-primary)",
  fontSize: 13,
  outline: "none",
};
