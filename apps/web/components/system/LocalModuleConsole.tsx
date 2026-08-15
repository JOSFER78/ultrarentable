"use client";

import { useAPI } from "@/hooks/useAPI";

export type LocalStatus = {
  generatedAt: string;
  mode: string;
  backend: { status: string; base?: string; data?: unknown; error?: string };
  bingx: { status: string; latencyMs?: number; contractsCount?: number; error?: string };
  storage: {
    rawFiles: number;
    datasetManifests: number;
    quarantinedFiles: number;
    strategies: number;
    backtests: number;
    campaigns: number;
    canonicalResults: number;
    researchSources: number;
  };
};

type Props = {
  title: string;
  description: string;
  icon: string;
  countKey: keyof LocalStatus["storage"];
  countLabel: string;
  readyWhen: (status: LocalStatus) => boolean;
  requirements: string[];
  nextAction: string;
};

export default function LocalModuleConsole({
  title,
  description,
  icon,
  countKey,
  countLabel,
  readyWhen,
  requirements,
  nextAction,
}: Props) {
  const { data, loading, error, refetch } = useAPI<LocalStatus>("/api/local/status");
  const ready = data ? readyWhen(data) : false;
  const count = data?.storage[countKey] ?? 0;

  return (
    <div className="stagger">
      <div className="page-header animate-in">
        <h1 className="page-title">{icon} {title}</h1>
        <p className="page-desc">{description}</p>
      </div>

      <div className="grid-stats animate-in" style={{ marginBottom: 20 }}>
        <Metric label={countLabel} value={loading ? "…" : String(count)} />
        <Metric label="API local" value={data?.backend.status ?? (loading ? "…" : "OFFLINE")} />
        <Metric label="BingX" value={data?.bingx.status ?? (loading ? "…" : "UNKNOWN")} />
        <Metric label="Datasets activos" value={loading ? "…" : String(data?.storage.datasetManifests ?? 0)} />
      </div>

      {error && (
        <section className="card animate-in" style={{ padding: 20, borderColor: "var(--danger)", marginBottom: 20 }}>
          <strong style={{ color: "var(--danger)" }}>No se pudo leer el estado local</strong>
          <p style={{ color: "var(--text-muted)", marginTop: 8 }}>{error}</p>
        </section>
      )}

      <div className="grid-2 animate-in">
        <section className="card" style={{ padding: 22 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
            <span className={`badge ${ready ? "badge-success" : "badge-warning"}`}>
              {ready ? "READY" : "NOT_READY"}
            </span>
            <strong>Estado obtenido del sistema local</strong>
          </div>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>
            {ready
              ? "Este módulo ya tiene artefactos reales registrados."
              : "No hay artefactos verificables suficientes para ejecutar esta función todavía."}
          </p>
          <button className="btn btn-secondary" onClick={refetch} style={{ marginTop: 16 }}>
            Actualizar estado
          </button>
        </section>

        <section className="card" style={{ padding: 22 }}>
          <h3 style={{ marginBottom: 12 }}>Siguiente modificación real</h3>
          <p style={{ color: "var(--text-muted)", lineHeight: 1.7 }}>{nextAction}</p>
        </section>
      </div>

      <section className="card animate-in" style={{ padding: 22, marginTop: 20 }}>
        <h3 style={{ marginBottom: 12 }}>Condiciones de activación</h3>
        <ul style={{ display: "grid", gap: 9, paddingLeft: 20, color: "var(--text-secondary)" }}>
          {requirements.map((item) => <li key={item}>{item}</li>)}
        </ul>
        {data?.storage.quarantinedFiles ? (
          <p style={{ marginTop: 18, color: "var(--warning)" }}>
            Hay {data.storage.quarantinedFiles} archivos heredados en cuarentena. No pueden usarse en backtests.
          </p>
        ) : null}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 20 }}>{value}</div>
    </div>
  );
}
