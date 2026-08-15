"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface ResearchSource {
  sourceId: string;
  title: string;
  url: string;
  author: string;
  fetchDate: string;
  sha256Hash: string;
  licenseInfo: string;
  hypothesisText: string;
  associatedBacktestId?: string;
  createdAt: string;
}

export default function ResearchPage() {
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [author, setAuthor] = useState("");
  const [hypothesisText, setHypothesisText] = useState("");
  const [content, setContent] = useState("");
  const [licenseInfo, setLicenseInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = async () => {
    try {
      const data = await api.getResearch();
      setSources(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "SERVICE_UNAVAILABLE");
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !url || !content || !hypothesisText) return alert("Completa título, URL, contenido exacto de la fuente e hipótesis");
    setLoading(true);
    try {
      await api.createResearch({
        title,
        url,
        author: author || "Researcher",
        hypothesisText,
        content,
        licenseInfo,
      });
      setTitle("");
      setUrl("");
      setAuthor("");
      setHypothesisText("");
      setContent("");
      setLicenseInfo("");
      await fetchSources();
    } catch (err: any) {
      alert(`Error al registrar fuente: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">Research & Hypothesis Registry</h1>
        <p className="page-desc">
          Registro manual de fuentes con URL, contenido exacto aportado por el usuario y hash SHA-256. La recuperación automática todavía está pendiente.
        </p>
      </div>

      <div className="grid-2 animate-in" style={{ marginBottom: 24 }}>
        {/* Register Form */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">[REGISTRO] Registrar Nueva Fuente e Hipótesis</h2>
          </div>
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div>
              <label style={labelStyle}>Título de la Hipótesis / Paper</label>
              <input
                type="text"
                placeholder="Ej. High Frequency Breakout on Futures Volatility"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>URL de la Fuente (SSRN / ArXiv / GitHub)</label>
              <input
                type="text"
                placeholder="Ej. https://arxiv.org/abs/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Autor / Investigador</label>
              <input
                type="text"
                placeholder="Ej. Dr. Quant / Equipo"
                value={author}
                onChange={(e) => setAuthor(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Contenido exacto recuperado de la fuente</label>
              <textarea
                placeholder="Pega el texto o fragmento verificable que se va a hashear. No se descargará automáticamente en esta fase."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                style={{ ...inputStyle, minHeight: 90 }}
              />
            </div>
            <div>
              <label style={labelStyle}>Licencia (solo si está confirmada)</label>
              <input
                type="text"
                placeholder="Ej. MIT, Apache-2.0, CC BY 4.0"
                value={licenseInfo}
                onChange={(e) => setLicenseInfo(e.target.value)}
                style={inputStyle}
              />
            </div>
            <div>
              <label style={labelStyle}>Texto de la Hipótesis Observable</label>
              <textarea
                placeholder="Describe la hipótesis cuantificable..."
                value={hypothesisText}
                onChange={(e) => setHypothesisText(e.target.value)}
                style={{ ...inputStyle, minHeight: 90 }}
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "[+] Registrando..." : "[+] Registrar en SQLite"}
            </button>
          </form>
        </div>

        {/* Sources List */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Registro de Fuentes ({sources.length})</h2>
          </div>

          {error ? (
            <div style={{ padding: 16, color: "var(--danger)" }}>SERVICE_UNAVAILABLE: {error}</div>
          ) : sources.length === 0 ? (
            <div style={{ padding: "40px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 13, fontFamily: "var(--font-mono)" }}>
              NO_DATA_AVAILABLE — Registra tu primera fuente e hipótesis.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 380, overflowY: "auto" }}>
              {sources.map((s) => (
                <div key={s.sourceId} style={{ padding: 12, borderRadius: "var(--radius-md)", border: "1px solid var(--border)", background: "var(--bg-2)" }}>
                  <div style={{ fontWeight: 700, fontSize: 13, color: "var(--text-primary)" }}>{s.title}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    Autor: {s.author} · Fecha: {s.fetchDate ? s.fetchDate.slice(0, 10) : "N/A"}
                  </div>
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: "var(--accent)", textDecoration: "underline", marginTop: 4, display: "block" }}>
                      {s.url}
                    </a>
                  ) : null}
                  <div style={{ fontSize: 12, marginTop: 6, color: "var(--text-secondary)" }}>{s.hypothesisText}</div>
                  <div style={{ fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--text-muted)", marginTop: 6 }}>
                    Hash SHA-256: {s.sha256Hash.slice(0, 24)}...
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
