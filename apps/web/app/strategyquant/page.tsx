"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface SQXProject {
  name: string;
}

interface SQXStatus {
  status: string;
  base_url?: string;
  session_id?: string;
  server_info?: { name: string; version: string };
  error?: string;
}

export default function StrategyQuantPage() {
  const [sqxStatus, setSqxStatus] = useState<SQXStatus | null>(null);
  const [projects, setProjects] = useState<SQXProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [databanks, setDatabanks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const statusRes = await api.getSQXStatus();
      setSqxStatus(statusRes);
      if (statusRes.status === "ONLINE") {
        const projRes = await api.getSQXProjects();
        setProjects(projRes.projects || []);
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || "Error al conectar con la API local");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectProject = async (name: string) => {
    setSelectedProject(name);
    try {
      const res = await api.getSQXDatabanks(name);
      setDatabanks(res.databanks || []);
    } catch (err: any) {
      setDatabanks([]);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="stagger" style={{ padding: "24px", maxWidth: "1200px", margin: "0 auto" }}>
      <div className="page-header animate-in" style={{ marginBottom: "24px" }}>
        <div style={{ display: "inline-block", background: "rgba(59, 130, 246, 0.15)", color: "#60a5fa", padding: "4px 12px", borderRadius: "9999px", fontSize: "12px", fontWeight: "700", marginBottom: "8px" }}>
          FASE 1: INTEGRACIÓN REAL SQX MCP
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: "800", marginBottom: "8px" }}>StrategyQuant X — Laboratorio MCP</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          Conexión 100% directa en tiempo real con la instancia de StrategyQuant X (`http://localhost:8080/mcp`). Cero mocks.
        </p>
      </div>

      {/* STATUS CARD */}
      <div className="card animate-in" style={{ padding: "20px", marginBottom: "24px", background: "var(--bg-2)", border: "1px solid var(--border)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "700" }}>Estado Servidor MCP SQX</div>
            <div style={{ fontSize: "20px", fontWeight: "800", color: sqxStatus?.status === "ONLINE" ? "#34d399" : "#f87171", marginTop: "4px" }}>
              {sqxStatus?.status === "ONLINE" ? "[ONLINE] — HTTP Stream Activo" : "[OFFLINE] — Abre StrategyQuant X"}
            </div>
            {sqxStatus?.server_info ? (
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "4px" }}>
                Servidor: <strong>{sqxStatus.server_info.name} v{sqxStatus.server_info.version}</strong> | Sesión: <code>{sqxStatus.session_id}</code>
              </div>
            ) : null}
            {sqxStatus?.error ? (
              <div style={{ fontSize: "12px", color: "#f87171", marginTop: "4px" }}>
                Detalle: {sqxStatus.error}
              </div>
            ) : null}
          </div>
          <button onClick={loadData} style={{ background: "#3b82f6", color: "#fff", border: "none", padding: "8px 16px", borderRadius: "6px", cursor: "pointer", fontWeight: "600" }}>
            [RECARGAR CONEXIÓN]
          </button>
        </div>
      </div>

      {/* PROJECTS LIST */}
      <div className="card animate-in" style={{ padding: "24px", marginBottom: "24px" }}>
        <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "16px" }}>
          Proyectos Detectados en StrategyQuant X ({projects.length})
        </h3>

        {loading ? (
          <div style={{ color: "var(--text-muted)", fontSize: "14px" }}>Cargando proyectos desde SQX MCP...</div>
        ) : projects.length > 0 ? (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
            {projects.map((p, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectProject(p.name)}
                style={{
                  padding: "14px 18px",
                  borderRadius: "8px",
                  background: selectedProject === p.name ? "rgba(59, 130, 246, 0.2)" : "var(--bg-3)",
                  border: selectedProject === p.name ? "1px solid #3b82f6" : "1px solid var(--border)",
                  cursor: "pointer",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  transition: "all 0.2s"
                }}
              >
                <span style={{ fontWeight: "600", fontSize: "14px" }}>{p.name}</span>
                <span style={{ fontSize: "11px", background: "rgba(16, 185, 129, 0.2)", color: "#34d399", padding: "2px 8px", borderRadius: "4px" }}>
                  VER DATABANKS
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: "var(--text-muted)", fontSize: "14px" }}>
            No se detectaron proyectos o StrategyQuant X está cerrado. Asegúrate de tener SQX abierto en tu ordenador.
          </div>
        )}
      </div>

      {/* DATABANKS INSPECTOR */}
      {selectedProject ? (
        <div className="card animate-in" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "700", marginBottom: "12px" }}>
            Bancos de Datos (Databanks) en Proyecto: <span style={{ color: "#60a5fa" }}>{selectedProject}</span>
          </h3>
          {databanks.length > 0 ? (
            <ul style={{ paddingLeft: "20px" }}>
              {databanks.map((db, i) => (
                <li key={i} style={{ marginBottom: "8px", fontSize: "14px" }}>
                  <strong>{typeof db === "object" ? db.name || JSON.stringify(db) : db}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
              Selecciona o inspecciona este proyecto para obtener la lista de candidatos guardados en StrategyQuant X.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
