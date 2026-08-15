"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Campaign {
  campaignId: string;
  name: string;
  symbol: string;
  interval: string;
  populationSize: number;
  generationsCount: number;
  currentGeneration: number;
  seed: number;
  status: string;
  mode?: string;
  targetMultiplier?: number;
  createdAt: string;
}

export default function CampaignsAutopilotPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [symbol, setSymbol] = useState("AUTO");
  const [interval, setTimeframe] = useState("AUTO");
  const [initialCapital, setInitialCapital] = useState(10000);
  const [targetMultiplier, setTargetMultiplier] = useState(11.0);
  const [mode, setMode] = useState("EXPLORE");
  const [populationSize, setPopulationSize] = useState(10);
  const [generationsCount, setGenerationsCount] = useState(3);
  const [loading, setLoading] = useState(false);
  const [activeCampaignResult, setActiveCampaignResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = async () => {
    try {
      const data = await api.getCampaigns();
      setCampaigns(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleStartAutopilot = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setActiveCampaignResult(null);

    try {
      // 1. Create campaign
      const campaignData = await api.createAutonomousCampaign({
        symbol,
        interval,
        initialCapital,
        targetMultiplier,
        mode,
        populationSize,
        generationsCount,
      });
      const campaignId = campaignData.campaignId;

      // 2. Start campaign execution cycle
      const runResult = await api.startCampaign(campaignId);
      setActiveCampaignResult(runResult);
      await fetchCampaigns();
    } catch (err: any) {
      alert(`Error al ejecutar campaña autónoma: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Campaigns Autopilot — Fábrica Autónoma de Estrategias</h1>
        <p className="page-desc">
          Búsqueda autónoma real sin diseño manual. El sistema genera, evalúa, muta y repara estrategias sobre datasets BingX aprobados.
        </p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        {/* Autopilot Launch Card */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Consola Autopilot (Modo Principal)</h2>
          </div>
          <form onSubmit={handleStartAutopilot} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Símbolo BingX</label>
                <select value={symbol} onChange={(e) => setSymbol(e.target.value)} style={inputStyle}>
                  <option value="AUTO">AUTO (ETH-USDT)</option>
                  <option value="ETH-USDT">ETH-USDT</option>
                  <option value="BTC-USDT">BTC-USDT</option>
                  <option value="SOL-USDT">SOL-USDT</option>
                </select>
              </div>
              <div>
                <label style={labelStyle}>Timeframe</label>
                <select value={interval} onChange={(e) => setTimeframe(e.target.value)} style={inputStyle}>
                  <option value="AUTO">AUTO (1h)</option>
                  <option value="1h">1 hora (1h)</option>
                  <option value="15m">15 minutos (15m)</option>
                  <option value="4h">4 horas (4h)</option>
                </select>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Capital Inicial ($)</label>
                <input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(Number(e.target.value))}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Objetivo Neto (Multiplicador)</label>
                <input
                  type="number"
                  step="0.5"
                  value={targetMultiplier}
                  onChange={(e) => setTargetMultiplier(Number(e.target.value))}
                  style={inputStyle}
                />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              <div>
                <label style={labelStyle}>Modo de Búsqueda</label>
                <select value={mode} onChange={(e) => setMode(e.target.value)} style={inputStyle}>
                  <option value="EXPLORE">EXPLORE (Exploración Amplia)</option>
                  <option value="IMPROVE">IMPROVE (Mejorar Ganadores)</option>
                  <option value="REGIME_SEARCH">REGIME_SEARCH (Por Régimen)</option>
                </select>
              </div>
              <div>
                <label style={labelStyle}>Población</label>
                <input
                  type="number"
                  value={populationSize}
                  onChange={(e) => setPopulationSize(Number(e.target.value))}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={labelStyle}>Generaciones</label>
                <input
                  type="number"
                  value={generationsCount}
                  onChange={(e) => setGenerationsCount(Number(e.target.value))}
                  style={inputStyle}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: 8, padding: 12, fontSize: 14 }}>
              {loading ? "Ejecutando Fábrica Autónoma..." : "INICIAR BÚSQUEDA AUTÓNOMA"}
            </button>
          </form>

          {activeCampaignResult && (
            <div style={{ marginTop: 16, padding: 12, borderRadius: "var(--radius-md)", background: "rgba(16,185,129,0.1)", border: "1px solid var(--success)" }}>
              <div style={{ fontWeight: 700, fontSize: 13, color: "var(--success)" }}>
                [OK] Ciclo de Campaña Finalizado
              </div>
              <pre style={{ fontFamily: "var(--font-mono)", fontSize: 10, marginTop: 6, background: "var(--bg-1)", padding: 8, borderRadius: 4, overflowX: "auto" }}>
                {JSON.stringify(activeCampaignResult, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Existing Campaigns & History */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">📚 Registro de Campañas ({campaigns.length})</h2>
          </div>

          {error ? (
            <div style={{ padding: 16, color: "var(--danger)" }}>SERVICE_UNAVAILABLE: {error}</div>
          ) : campaigns.length === 0 ? (
            <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
              NO_DATA_AVAILABLE — Lanza tu primera búsqueda autónoma.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 420, overflowY: "auto" }}>
              {campaigns.map((c) => (
                <div key={c.campaignId} style={{ padding: 12, borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg-2)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>{c.name}</div>
                    <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 4, background: c.status === "COMPLETED" ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)", color: c.status === "COMPLETED" ? "var(--success)" : "var(--warning)" }}>
                      {c.status}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    {c.symbol} · {c.interval} · Generación {c.currentGeneration}/{c.generationsCount} · Modo: {c.mode || "EXPLORE"}
                  </div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--accent)", marginTop: 4 }}>
                    ID: {c.campaignId}
                  </div>
                </div>
              ))}
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
