"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface LeaderboardItem {
  rank: number;
  backtestId: string;
  strategyId: string;
  engine: string;
  returnPct: number;
  maxDrawdownPct: number;
  winRate: number;
  tradesCount: number;
  profitFactor: number;
  checksum: string;
  date: string;
}

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardItem[]>([]);
  const [activeLedger, setActiveLedger] = useState<any[] | null>(null);
  const [activeBacktestId, setActiveBacktestId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchLeaderboard = async () => {
    try {
      const data = await api.getLeaderboard();
      setEntries(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const handleViewLedger = async (backtestId: string) => {
    try {
      const trades = await api.getBacktestTrades(backtestId);
      setActiveLedger(trades);
      setActiveBacktestId(backtestId);
    } catch (err: any) {
      alert(`No se pudo cargar el ledger auditado: ${err.message}`);
    }
  };

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Leaderboard Auditado</h1>
        <p className="page-desc">
          Ranking oficial de estrategias supervivientes verificado contra SQLite con artefactos descargables y registro inmutable de trades.
        </p>
      </div>

      {activeLedger && (
        <div className="card animate-in" style={{ marginBottom: 24, border: "1px solid var(--accent)" }}>
          <div className="card-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 className="card-title">[LEDGER] Ledger Auditado Inmutable: {activeBacktestId}</h2>
            <button onClick={() => setActiveLedger(null)} className="btn btn-sm btn-danger">Cerrar</button>
          </div>
          <div style={{ maxHeight: 300, overflowY: "auto" }}>
            <pre style={{ background: "var(--bg-1)", padding: 12, borderRadius: "var(--radius-md)", fontSize: 11, fontFamily: "var(--font-mono)" }}>
              {JSON.stringify(activeLedger, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {error ? (
        <div style={{ padding: 20, color: "var(--danger)" }}>SERVICE_UNAVAILABLE: {error}</div>
      ) : entries.length === 0 ? (
        <div className="card animate-in" style={{ textAlign: "center", padding: "60px 20px" }}>
          <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 12, color: "var(--accent)", fontFamily: "monospace" }}>[LEADERBOARD SIN DATOS]</div>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: "var(--text-primary)", fontFamily: "var(--font-mono)" }}>
            NO_DATA_AVAILABLE
          </h2>
          <p style={{ fontSize: 13, color: "var(--text-muted)", maxWidth: 500, margin: "0 auto 20px auto" }}>
            No existen ejecuciones auditadas registradas en SQLite. Ninguna estrategia ingresa al Leaderboard sin artefactos verificables, checksum SHA-256 e historial de trades real.
          </p>
          <Link href="/backtest" className="btn btn-primary">
            Ir a la Consola de Backtesting
          </Link>
        </div>
      ) : (
        <div className="card animate-in" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>ID Backtest</th>
                  <th>Estrategia ID</th>
                  <th>Motor</th>
                  <th>Return</th>
                  <th>Max DD</th>
                  <th>Win Rate</th>
                  <th>Trades</th>
                  <th>Profit Factor</th>
                  <th>Checksum</th>
                  <th>Ledger</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((item) => (
                  <tr key={item.backtestId}>
                    <td>#{item.rank}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{item.backtestId}</td>
                    <td>{item.strategyId}</td>
                    <td><span className={`badge ${item.engine === "CANONICAL" ? "badge-success" : "badge-warning"}`}>{item.engine}</span></td>
                    <td style={{ color: item.returnPct >= 0 ? "var(--long)" : "var(--short)", fontWeight: 700 }}>+{item.returnPct.toFixed(2)}%</td>
                    <td style={{ color: "var(--short)" }}>-{item.maxDrawdownPct.toFixed(2)}%</td>
                    <td>{item.winRate.toFixed(1)}%</td>
                    <td>{item.tradesCount}</td>
                    <td>{item.profitFactor.toFixed(2)}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{item.checksum.slice(0, 16)}...</td>
                    <td>
                      <button onClick={() => handleViewLedger(item.backtestId)} className="btn btn-sm" style={{ background: "var(--bg-1)", fontSize: 11 }}>
                        Inspeccionar Trades
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
