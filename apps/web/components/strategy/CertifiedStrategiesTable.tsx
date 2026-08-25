"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";

interface CandidateSummary {
  candidate_id?: string;
  name?: string;
  route?: string;
  symbol?: string;
  timeframe?: string;
  status?: string;
  status_reason?: string;
  profit_factor_is?: number | null;
  profit_factor_oos?: number | null;
  max_dd_oos_pct?: number | null;
  trades_oos?: number | null;
  engine_version?: string | null;
}

interface CandidateDetail {
  candidate_id?: string;
  name?: string;
  route?: string;
  symbol?: string;
  timeframe?: string;
  status?: string;
  strategy_sha256?: string | null;
  bundle_signature_sha256?: string | null;
  dataset_id?: string | null;
  scorecard_json?: string | Record<string, unknown> | null;
  metrics?: {
    out_of_sample?: {
      profit_factor?: number | null;
      max_drawdown_pct?: number | null;
      trades?: number | null;
      win_rate_pct?: number | null;
    };
    anti_overfit?: {
      wfo_pass_pct?: number | null;
      monte_carlo_score?: number | null;
      ratio_oos_is?: number | null;
    };
  };
}

interface EvidenceView {
  explicitGateIds: Set<number>;
  passedGateIds: Set<number>;
  all11Explicit: boolean;
  all11Passed: boolean;
  certificationEligible: boolean;
}

function parseScorecard(raw: CandidateDetail["scorecard_json"]): Record<string, any> {
  if (!raw) return {};
  if (typeof raw === "object") return raw;
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function inspectEvidence(detail: CandidateDetail): EvidenceView {
  const sc = parseScorecard(detail.scorecard_json);
  const ids = new Set<number>();
  const passed = new Set<number>();

  const gates = Array.isArray(sc.gates) ? sc.gates : [];
  for (const gate of gates) {
    const id = Number(gate?.gate_id ?? gate?.id);
    if (Number.isInteger(id) && id >= 1 && id <= 11) {
      ids.add(id);
      if (gate?.passed === true || String(gate?.status).toUpperCase() === "PASSED") {
        passed.add(id);
      }
    }
  }

  const ge = sc.gates_evaluation && typeof sc.gates_evaluation === "object" ? sc.gates_evaluation : {};
  for (let i = 1; i <= 11; i += 1) {
    const key = `gate_${String(i).padStart(2, "0")}`;
    const value = ge[key];
    if (typeof value === "string" || typeof value === "boolean") {
      ids.add(i);
      if (value === true || String(value).toUpperCase() === "PASSED") passed.add(i);
    }
  }

  const explicitGateIds = ids;
  const passedGateIds = passed;
  const all11Explicit = explicitGateIds.size === 11;
  const all11Passed = all11Explicit && passedGateIds.size === 11;

  return {
    explicitGateIds,
    passedGateIds,
    all11Explicit,
    all11Passed,
    certificationEligible: all11Passed,
  };
}

function fmt(value: number | null | undefined, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(digits)}%` : "N/D";
}

function fmtNum(value: number | null | undefined, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(digits) : "N/D";
}

export default function CertifiedStrategiesTable() {
  const [rows, setRows] = useState<CandidateSummary[]>([]);
  const [details, setDetails] = useState<Record<string, CandidateDetail>>({});
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [route, setRoute] = useState<"ALL" | "FONDEO" | "ULTRA">("ALL");
  const [verifiedOnly, setVerifiedOnly] = useState(true);
  const [lastSync, setLastSync] = useState<Date | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/candidates/summary?status=APPROVED&limit=500", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list: CandidateSummary[] = Array.isArray(data) ? data : Array.isArray(data?.candidates) ? data.candidates : [];
      setRows(list);

      const entries = await Promise.all(
        list
          .map((r) => r.candidate_id)
          .filter((id): id is string => Boolean(id))
          .map(async (id) => {
            try {
              const detailRes = await fetch(`/api/v1/candidates/${encodeURIComponent(id)}`, { cache: "no-store" });
              if (!detailRes.ok) return [id, null] as const;
              return [id, (await detailRes.json()) as CandidateDetail] as const;
            } catch {
              return [id, null] as const;
            }
          })
      );
      const map: Record<string, CandidateDetail> = {};
      for (const [id, detail] of entries) {
        if (detail) map[id] = detail;
      }
      setDetails(map);
      setLastSync(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const viewRows = useMemo(() => {
    return rows
      .filter((row) => {
        if (route !== "ALL" && String(row.route).toUpperCase() !== route) return false;
        const text = `${row.candidate_id ?? ""} ${row.name ?? ""} ${row.symbol ?? ""}`.toLowerCase();
        if (query.trim() && !text.includes(query.toLowerCase().trim())) return false;
        const evidence = row.candidate_id ? inspectEvidence(details[row.candidate_id] ?? row as unknown as CandidateDetail) : null;
        if (verifiedOnly && !evidence?.certificationEligible) return false;
        return true;
      })
      .map((row) => {
        const detail = row.candidate_id ? details[row.candidate_id] : undefined;
        const evidence = detail ? inspectEvidence(detail) : inspectEvidence({});
        const oos = detail?.metrics?.out_of_sample ?? {};
        const anti = detail?.metrics?.anti_overfit ?? {};
        return { row, detail, evidence, oos, anti };
      });
  }, [rows, details, route, query, verifiedOnly]);

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 p-6">
      <div className="max-w-[1500px] mx-auto space-y-6">
        <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Estrategias certificadas</h1>
            <p className="text-sm text-neutral-400 mt-1">
              Esta vista sólo declara certificación cuando existe evidencia explícita de los 11 Gates. No calcula ni rellena métricas ausentes.
            </p>
          </div>
          <div className="text-xs text-neutral-500">
            Última sync: {lastSync ? lastSync.toLocaleTimeString("es-ES") : "N/D"}
          </div>
        </header>

        <section className="rounded-xl border border-amber-700/40 bg-amber-950/20 p-4 text-sm text-amber-100">
          <strong>REAL-ONLY:</strong> una estrategia con estado APPROVED en la base no se considera certificada aquí si el scorecard no demuestra explícitamente los Gates 1–11.
          No se muestran CAGR/ROI anualizados inventados a partir de una duración por defecto.
        </section>

        <div className="flex flex-wrap gap-2 items-center">
          {(["ALL", "FONDEO", "ULTRA"] as const).map((r) => (
            <button key={r} onClick={() => setRoute(r)} className={`px-3 py-1.5 rounded-lg border text-sm ${route === r ? "border-blue-500 bg-blue-500/10" : "border-neutral-700"}`}>
              {r === "ALL" ? "TODAS" : r}
            </button>
          ))}
          <button onClick={() => setVerifiedOnly((v) => !v)} className={`px-3 py-1.5 rounded-lg border text-sm ${verifiedOnly ? "border-emerald-500 bg-emerald-500/10" : "border-neutral-700"}`}>
            {verifiedOnly ? "Sólo 11/11 verificado" : "Mostrar también sin evidencia"}
          </button>
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar ID, nombre o activo" className="ml-auto w-full md:w-80 px-3 py-2 rounded-lg bg-neutral-900 border border-neutral-700 outline-none" />
          <button onClick={() => void load()} className="px-3 py-2 rounded-lg border border-neutral-700">Actualizar</button>
        </div>

        {loading ? (
          <div className="p-10 text-center text-neutral-400">Cargando evidencia real…</div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-neutral-800">
            <table className="w-full text-sm">
              <thead className="bg-neutral-900/80 text-neutral-400">
                <tr>
                  <th className="text-left p-3">ID</th>
                  <th className="text-left p-3">Activo / TF / Engine</th>
                  <th className="text-left p-3">Ruta</th>
                  <th className="text-right p-3">Trades OOS</th>
                  <th className="text-right p-3">Win Rate</th>
                  <th className="text-right p-3">PF OOS</th>
                  <th className="text-right p-3">ROI anual</th>
                  <th className="text-right p-3">DD OOS</th>
                  <th className="text-right p-3">WFE</th>
                  <th className="text-left p-3">Certificación</th>
                  <th className="text-left p-3">SHA-256</th>
                </tr>
              </thead>
              <tbody>
                {viewRows.map(({ row, detail, evidence, oos, anti }) => (
                  <tr key={row.candidate_id} className="border-t border-neutral-800 hover:bg-neutral-900/60">
                    <td className="p-3 font-mono text-xs">{row.candidate_id ?? "N/D"}</td>
                    <td className="p-3">{row.symbol ?? "N/D"} · {row.timeframe ?? "N/D"} · {detail ? (detail as any).engine_version ?? "N/D" : row.engine_version ?? "N/D"}</td>
                    <td className="p-3">{row.route ?? "N/D"}</td>
                    <td className="p-3 text-right">{typeof oos.trades === "number" ? oos.trades : typeof row.trades_oos === "number" ? row.trades_oos : "N/D"}</td>
                    <td className="p-3 text-right">{fmt(oos.win_rate_pct)}</td>
                    <td className="p-3 text-right">{fmtNum(oos.profit_factor ?? row.profit_factor_oos)}</td>
                    <td className="p-3 text-right">N/D</td>
                    <td className="p-3 text-right">{fmt(oos.max_drawdown_pct ?? row.max_dd_oos_pct)}</td>
                    <td className="p-3 text-right">{fmt(anti.wfo_pass_pct)}</td>
                    <td className="p-3">
                      {evidence.all11Passed ? (
                        <span className="text-emerald-400">11/11 VERIFICADO</span>
                      ) : (
                        <span className="text-amber-400">NO_EVIDENCE ({evidence.explicitGateIds.size}/11)</span>
                      )}
                    </td>
                    <td className="p-3 font-mono text-[10px] text-neutral-500 break-all">{detail?.strategy_sha256 ?? detail?.bundle_signature_sha256 ?? "N/D"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && viewRows.length === 0 && (
          <div className="rounded-xl border border-neutral-800 p-8 text-center text-neutral-400">
            No hay estrategias con evidencia suficiente para declararlas certificadas bajo la política actual.
          </div>
        )}
      </div>
    </main>
  );
}
