"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Provider {
  provider_id: string;
  name: string;
  provider_name: string;
  market_type: string;
  platform: string;
  allowed_instruments: string;
  account_size: number;
  target_pct: number;
  daily_loss_limit_pct?: number;
  dll_calc_model: string;
  max_trailing_dd_pct: number;
  trailing_dd_type: string;
  consistency_rule_pct: number;
  min_trading_days: number;
  overnight_allowed: boolean;
  news_trading_allowed: boolean;
  ea_bots_allowed: string;
  monthly_cost_usd?: number;
  source_url?: string;
  verified_at?: string;
  verification_status: string;
  notes?: string;
}

export default function PropFirmsCatalogPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [filterMarket, setFilterMarket] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  useEffect(() => {
    fetch("/api/v1/providers")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) setProviders(data);
      })
      .catch((err) => console.error("Error loading providers:", err));
  }, []);

  const filtered = providers.filter((p) => {
    if (filterMarket !== "ALL" && p.market_type !== filterMarket) return false;
    if (filterStatus !== "ALL" && p.verification_status !== filterStatus) return false;
    return true;
  });

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "#60a5fa", textTransform: "uppercase", fontFamily: "monospace" }}>
              CATÁLOGO DE PROP FIRMS
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
            🏛️ Firmas de Fondeo y Reglas de Evaluación
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Base de datos versionada en SQLite con reglas extraídas de fuentes oficiales y estado de verificación explícito.
          </p>
        </div>

        {/* FILTROS */}
        <div style={{ display: "flex", gap: "10px" }}>
          <select
            value={filterMarket}
            onChange={(e) => setFilterMarket(e.target.value)}
            style={{ padding: "8px 12px", background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: "6px", color: "var(--text-primary)", fontSize: "12px", fontWeight: 700 }}
          >
            <option value="ALL">Todos los Mercados</option>
            <option value="FUTURES">Futuros CME</option>
            <option value="CFD">CFDs / FX</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={{ padding: "8px 12px", background: "var(--bg-input)", border: "1px solid var(--border)", borderRadius: "6px", color: "var(--text-primary)", fontSize: "12px", fontWeight: 700 }}
          >
            <option value="ALL">Todos los Estados</option>
            <option value="VERIFIED">VERIFIED (Verificadas)</option>
            <option value="UNVERIFIED">UNVERIFIED (No confirmadas)</option>
          </select>
        </div>
      </div>

      {/* TABLA DE PROVEEDORES */}
      <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "rgba(0,0,0,0.3)", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "11px" }}>
                <th style={{ padding: "12px 16px" }}>FIRMA / CUENTA</th>
                <th style={{ padding: "12px 16px" }}>PLATAFORMA & MERCADO</th>
                <th style={{ padding: "12px 16px" }}>TARGET / DD MÁXIMO</th>
                <th style={{ padding: "12px 16px" }}>PÉRDIDA DIARIA (DLL)</th>
                <th style={{ padding: "12px 16px" }}>CONSISTENCIA</th>
                <th style={{ padding: "12px 16px" }}>POLÍTICA BOTS / EA</th>
                <th style={{ padding: "12px 16px" }}>ESTADO & FUENTE</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.provider_id} style={{ borderBottom: "1px solid var(--border)", transition: "background 0.2s ease" }}>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ fontWeight: 800, fontSize: "13px", color: "var(--text-primary)" }}>{p.name}</div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "2px" }}>
                      Balance: ${p.account_size.toLocaleString()} USD
                    </div>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ fontWeight: 700 }}>{p.platform}</div>
                    <div style={{ fontSize: "11px", color: "#60a5fa", marginTop: "2px" }}>{p.allowed_instruments}</div>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ fontWeight: 700, color: "#22c55e" }}>
                      Target: ${(p.account_size * p.target_pct / 100).toLocaleString()} ({p.target_pct}%)
                    </div>
                    <div style={{ fontSize: "11px", color: "#ef4444", marginTop: "2px" }}>
                      Trailing DD: ≤ ${(p.account_size * p.max_trailing_dd_pct / 100).toLocaleString()} ({p.max_trailing_dd_pct}%) [{p.trailing_dd_type}]
                    </div>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    {p.daily_loss_limit_pct ? (
                      <div>
                        <span style={{ fontWeight: 700, color: "#ef4444" }}>≤ {p.daily_loss_limit_pct}%</span>
                        <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>({p.dll_calc_model})</div>
                      </div>
                    ) : (
                      <span style={{ color: "var(--text-muted)" }}>Sin DLL en evaluación</span>
                    )}
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <span style={{ fontWeight: 700 }}>≤ {p.consistency_rule_pct}%</span>
                    <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>Mín. {p.min_trading_days} días</div>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <span style={{ 
                      fontSize: "11px", 
                      fontWeight: 700, 
                      color: p.ea_bots_allowed.includes("PERMITTED") ? "#22c55e" : "#f59e0b" 
                    }}>
                      {p.ea_bots_allowed}
                    </span>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <span style={{ 
                        fontSize: "10px", 
                        fontWeight: 800, 
                        padding: "2px 6px", 
                        borderRadius: "4px", 
                        background: p.verification_status === "VERIFIED" ? "rgba(34, 197, 94, 0.2)" : "rgba(245, 158, 11, 0.2)",
                        color: p.verification_status === "VERIFIED" ? "#22c55e" : "#f59e0b",
                        alignSelf: "flex-start",
                        fontFamily: "monospace"
                      }}>
                        {p.verification_status} ({p.verified_at ?? "2026"})
                      </span>
                      {p.source_url && (
                        <a href={p.source_url} target="_blank" style={{ fontSize: "11px", color: "#60a5fa", textDecoration: "underline" }}>
                          Fuente Oficial ↗
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
