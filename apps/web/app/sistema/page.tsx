"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface SystemHealthData {
  overall_status: string;
  checked_at: string;
  services: {
    web_frontend: { configured_port: number; url: string; status: string; code?: number; latency_ms: number };
    api_backend: { configured_port: number; url: string; status: string; mode: string };
    sqx_mcp: { detected_port: number; url: string; status: string; message?: string };
    sqx_web_ui: { detected_port: number; url: string; status: string; code?: number; latency_ms: number };
  };
  port_conflicts: {
    port_8080: { occupied: boolean; service: string; impact: string };
  };
  database: {
    db_path: string;
    size_bytes: number;
    wal_active: boolean;
    tables: Record<string, number>;
  };
  market_data: {
    btc_usdt_h1: {
      path: string;
      exists: boolean;
      size_bytes: number;
      bars: number;
      date_range: string;
      cme_futures_data: string;
    };
  };
}

export default function SistemaPage() {
  const [data, setData] = useState<SystemHealthData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = () => {
    fetch("/api/v1/system/health")
      .then((r) => r.json())
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching system health:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHealth();
    const timer = setInterval(fetchHealth, 6000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="page-container animate-in" style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      {/* HEADER */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none" }}>
              ← Control Center
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", fontFamily: "monospace" }}>
              DIAGNÓSTICO DEL SISTEMA
            </span>
          </div>
          <h1 style={{ fontSize: "26px", fontWeight: 900, margin: 0 }}>
            🖥️ Estado de Infraestructura y Servicios Locales
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
            Telemetría real sin mocks. Comprobación directa de puertos, servidores HTTP, SQLite WAL y bridge SQX.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          className="btn btn-secondary"
          style={{ fontSize: "12px", fontWeight: 700 }}
        >
          🔄 Refrescar Diagnóstico
        </button>
      </div>

      {loading && !data ? (
        <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-muted)" }}>
          Cargando telemetría del sistema...
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          
          {/* SERVICIOS HTTP Y PUERTOS */}
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "20px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 800, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              🌐 Servicios de Red y Puertos
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px" }}>
              
              {/* NEXT.JS */}
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>FRONTEND (NEXT.JS)</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: data?.services.web_frontend.status === "ONLINE" ? "#22c55e" : "#ef4444", marginTop: "4px" }}>
                  ● {data?.services.web_frontend.status}
                </div>
                <div style={{ fontSize: "12px", fontFamily: "monospace", color: "var(--text-muted)", marginTop: "4px" }}>
                  Puerto :5000 ({data?.services.web_frontend.latency_ms}ms)
                </div>
              </div>

              {/* FASTAPI */}
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>BACKEND (FASTAPI)</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#22c55e", marginTop: "4px" }}>
                  ● {data?.services.api_backend.status}
                </div>
                <div style={{ fontSize: "12px", fontFamily: "monospace", color: "var(--text-muted)", marginTop: "4px" }}>
                  Puerto :8000 (SQLite WAL)
                </div>
              </div>

              {/* SQX MCP */}
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>STRATEGYQUANT X MCP</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: data?.services.sqx_mcp.status === "ONLINE" ? "#22c55e" : "#ef4444", marginTop: "4px" }}>
                  ● {data?.services.sqx_mcp.status}
                </div>
                <div style={{ fontSize: "12px", fontFamily: "monospace", color: "var(--text-muted)", marginTop: "4px" }}>
                  Puerto :8081 (/mcp activo)
                </div>
              </div>

              {/* CONFLICTO 8080 */}
              <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>CONFLICTO PUERTO :8080</div>
                <div style={{ fontSize: "14px", fontWeight: 800, color: "#f59e0b", marginTop: "4px" }}>
                  {data?.port_conflicts.port_8080.service}
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
                  SQX desplazado a :8081
                </div>
              </div>
            </div>
          </div>

          {/* BASE DE DATOS SQLITE WAL */}
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "20px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 800, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              💾 Base de Datos Local (SQLite WAL)
            </h2>
            <div style={{ fontSize: "12px", fontFamily: "monospace", color: "var(--text-muted)", marginBottom: "12px" }}>
              Ruta: {data?.database.db_path} ({(data?.database.size_bytes ? data.database.size_bytes / 1024 : 0).toFixed(1)} KB) · Modo WAL: {data?.database.wal_active ? "ACTIVO 🟢" : "INACTIVO 🔴"}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "10px" }}>
              {data?.database.tables && Object.entries(data.database.tables).map(([tbl, count]) => (
                <div key={tbl} style={{ background: "rgba(0,0,0,0.2)", padding: "10px", borderRadius: "6px", border: "1px solid var(--border)" }}>
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "monospace" }}>{tbl}</div>
                  <div style={{ fontSize: "16px", fontWeight: 800, color: "var(--text-primary)", marginTop: "2px" }}>{count} filas</div>
                </div>
              ))}
            </div>
          </div>

          {/* HISTORICO DE MERCADO */}
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "10px", padding: "20px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 800, marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
              📊 Datasets en Disco
            </h2>
            <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border)", fontSize: "12px", fontFamily: "monospace", display: "flex", flexDirection: "column", gap: "6px" }}>
              <div><strong>Archivo BTC:</strong> {data?.market_data.btc_usdt_h1.path}</div>
              <div><strong>Total Barras:</strong> {data?.market_data.btc_usdt_h1.bars} barras H1</div>
              <div><strong>Rango Temporal:</strong> {data?.market_data.btc_usdt_h1.date_range}</div>
              <div style={{ color: "#f59e0b" }}><strong>Futuros CME:</strong> {data?.market_data.btc_usdt_h1.cme_futures_data}</div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
