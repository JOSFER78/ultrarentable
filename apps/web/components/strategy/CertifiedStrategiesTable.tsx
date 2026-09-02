"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";

interface CertifiedRow {
  candidate_id: string;
  name?: string;
  route?: string;
  symbol?: string;
  timeframe?: string;
  engine_version?: string | null;
  certification_status?: string;
  explicit_gates?: number;
  passed_gates?: number;
  gates_verified_11?: boolean;
  strategy_sha256?: string | null;
  bundle_signature_sha256?: string | null;
  dataset_id?: string | null;
  metrics?: {
    trades_oos?: number | null;
    win_rate_pct?: number | null;
    profit_factor_is?: number | null;
    profit_factor_oos?: number | null;
    roi_cumulative_pct?: number | null;
    roi_annualized_pct?: number | null;
    roi_monthly_pct?: number | null;
    max_dd_oos_pct?: number | null;
    max_dd_realized_pct?: number | null;
    wfe_pct?: number | null;
    monte_carlo_score?: number | null;
    ratio_oos_is?: number | null;
    oos_months?: number | null;
  };
}

function fmtPct(value: number | null | undefined, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(digits)}%` : "N/D";
}

function fmtNum(value: number | null | undefined, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "N/D";
}

export default function CertifiedStrategiesTable() {
  const [rows, setRows] = useState<CertifiedRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [route, setRoute] = useState<"ALL" | "FONDEO" | "ULTRA">("ALL");
  const [verifiedOnly, setVerifiedOnly] = useState(true);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        verified_only: String(verifiedOnly),
        limit: "500",
      });
      if (route !== "ALL") params.set("route", route);
      const res = await fetch(`/api/v1/certified/summary?${params.toString()}`, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
      setLastSync(new Date());
    } catch (error) {
      console.error("Error loading canonical certification summary:", error);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [route, verifiedOnly]);

  useEffect(() => { void load(); }, [load]);

  const viewRows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return rows.filter((row) => {
      if (!q) return true;
      const text = `${row.candidate_id} ${row.name ?? ""} ${row.symbol ?? ""}`.toLowerCase();
      return text.includes(q);
    });
  }, [rows, query]);

  const countText = verifiedOnly ? `${viewRows.length} verificadas` : `${viewRows.length} resultados`;

  return (
    <main className="min-h-screen bg-[var(--surface-1)] text-[var(--text-1)] p-6">
      <div className="max-w-[1600px] mx-auto space-y-6">
        <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Estrategias certificadas</h1>
            <p className="text-sm text-[var(--text-2)] mt-1">
              Fuente única: API canónica de certificación. La UI no calcula, infiere ni completa métricas.
            </p>
          </div>
          <div className="text-xs text-[var(--text-3)]">Última sync: {lastSync ? lastSync.toLocaleTimeString("es-ES") : "N/D"}</div>
        </header>

        <section className="rounded-xl border border-[var(--border)] bg-[var(--surface-2)] p-4 text-sm text-[var(--text-1)]">
          <strong>REAL-ONLY:</strong> "CERTIFIED_CURRENT" requiere evidencia explícita de los Gates 1–11. Estado APPROVED en la base de datos, PF, DD u otra métrica aislada no equivalen a certificación.
          Los datos ausentes se muestran como N/D.
        </section>

        <div className="flex flex-wrap gap-2 items-center">
          {(["ALL", "FONDEO", "ULTRA"] as const).map((r) => (
            <button key={r} onClick={() => setRoute(r)} className={`px-3 py-1.5 rounded-lg border text-sm ${route === r ? "border-[var(--border)] bg-[var(--surface-2)]" : "border-[var(--border)]"}`}>
              {r === "ALL" ? "TODAS" : r}
            </button>
          ))}
          <button onClick={() => setVerifiedOnly((v) => !v)} className={`px-3 py-1.5 rounded-lg border text-sm ${verifiedOnly ? "border-[var(--profit)] bg-[var(--profit-dim)]" : "border-[var(--border)]"}`}>
            {verifiedOnly ? "Sólo 11/11 verificado" : "Mostrar también sin evidencia"}
          </button>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar ID, nombre o activo" className="ml-auto w-full md:w-80 px-3 py-2 rounded-lg bg-[var(--surface-1)] border border-[var(--border)] outline-none" />
          <button onClick={() => void load()} className="px-3 py-2 rounded-lg border border-[var(--border)]">Actualizar</button>
        </div>

        <div className="text-xs text-[var(--text-3)]">{countText}</div>

        {loading ? (
          <div className="p-10 text-center text-[var(--text-2)]">Cargando evidencia real…</div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-[var(--border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--surface-1)] text-[var(--text-2)]">
                <tr>
                  <th className="text-left p-3">ID candidata</th>
                  <th className="text-left p-3">Activo / TF / Engine</th>
                  <th className="text-left p-3">Ruta</th>
                  <th className="text-right p-3">Trades OOS</th>
                  <th className="text-right p-3">Win Rate</th>
                  <th className="text-right p-3">PF IS / OOS</th>
                  <th className="text-right p-3">ROI mes</th>
                  <th className="text-right p-3">ROI anual</th>
                  <th className="text-right p-3">Max DD</th>
                  <th className="text-right p-3">WFE</th>
                  <th className="text-left p-3">Estado Gate</th>
                  <th className="text-left p-3">SHA-256</th>
                </tr>
              </thead>
              <tbody>
                {viewRows.map((row) => {
                  const m = row.metrics ?? {};
                  return (
                    <tr key={row.candidate_id} className="border-t border-[var(--border)] hover:bg-[var(--surface-1)]">
                      <td className="p-3 font-mono text-xs">{row.candidate_id}</td>
                      <td className="p-3">{row.symbol ?? "N/D"} · {row.timeframe ?? "N/D"} · v{row.engine_version ?? "N/D"}</td>
                      <td className="p-3">{row.route ?? "N/D"}</td>
                      <td className="p-3 text-right">{typeof m.trades_oos === "number" ? m.trades_oos : "N/D"}</td>
                      <td className="p-3 text-right">{fmtPct(m.win_rate_pct)}</td>
                      <td className="p-3 text-right">{fmtNum(m.profit_factor_is)} / {fmtNum(m.profit_factor_oos)}</td>
                      <td className="p-3 text-right">{fmtPct(m.roi_monthly_pct)}</td>
                      <td className="p-3 text-right">{fmtPct(m.roi_annualized_pct)}</td>
                      <td className="p-3 text-right">{fmtPct(m.max_dd_oos_pct)}</td>
                      <td className="p-3 text-right">{fmtPct(m.wfe_pct)}</td>
                      <td className="p-3">
                        {row.gates_verified_11 ? (
                          <span className="text-[var(--profit)]">✓ 11/11 VERIFICADO</span>
                        ) : (
                          <span className="text-[var(--text-2)]">NO_EVIDENCE ({row.passed_gates ?? 0}/{row.explicit_gates ?? 0} explícitos)</span>
                        )}
                      </td>
                      <td className="p-3 font-mono text-[10px] text-[var(--text-3)] break-all">{row.strategy_sha256 ?? row.bundle_signature_sha256 ?? "N/D"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {!loading && viewRows.length === 0 && (
          <div className="rounded-xl border border-[var(--border)] p-8 text-center text-[var(--text-2)]">
            No hay estrategias con evidencia suficiente para declararlas certificadas bajo la política actual.
          </div>
        )}
      </div>
    </main>
  );
}
