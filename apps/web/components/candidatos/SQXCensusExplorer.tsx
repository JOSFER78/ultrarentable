"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import {
  Search,
  Download,
  Copy,
  Check,
  RefreshCw,
  Database,
  ArrowUpDown,
  Filter,
  ShieldAlert,
} from "lucide-react";
import { api } from "@/lib/api";

export interface SQXStrategyItem {
  strategy_id: string;
  name: string;
  strategy_version: string;
  strategy_hash: string;
  validation_status: string;
  source_engine?: string;
  source_project?: string;
  source_databank?: string;
  source_strategy_name?: string;
  symbol?: string;
  timeframe?: string;
  raw_stats?: Record<string, number | null>;
  created_at?: string;
}

interface SQXListResponse {
  status: string;
  count: number;
  strategies: SQXStrategyItem[];
}

type SortKey =
  | "name"
  | "symbol"
  | "timeframe"
  | "source_project"
  | "profit_factor"
  | "profit_factor_oos"
  | "net_profit"
  | "net_profit_oos"
  | "sharpe"
  | "ret_dd"
  | "trades";

export default function SQXCensusExplorer() {
  const [strategies, setStrategies] = useState<SQXStrategyItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [search, setSearch] = useState<string>("");
  const [symbolFilter, setSymbolFilter] = useState<string>("ALL");
  const [sortField, setSortField] = useState<SortKey>("net_profit");
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.get<SQXListResponse>("/api/v2/strategy-lab/strategies?limit=1000");
      if (res?.strategies) {
        setStrategies(res.strategies);
      } else {
        setStrategies([]);
      }
    } catch (err: any) {
      setErrorMsg(err?.message || "No se pudo conectar con el censo de estrategias.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void cargar();
  }, [cargar]);

  const copiar = (txt: string) => {
    void navigator.clipboard.writeText(txt);
    setCopiedId(txt);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Extraer símbolos únicos para filtro
  const symbols = useMemo(() => {
    const s = new Set<string>();
    for (const item of strategies) {
      if (item.symbol) s.add(item.symbol.toUpperCase());
    }
    return Array.from(s).sort();
  }, [strategies]);

  // Filtrado y ordenación
  const filtradas = useMemo(() => {
    let result = strategies.filter((st) => {
      if (symbolFilter !== "ALL" && st.symbol?.toUpperCase() !== symbolFilter) {
        return false;
      }
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchName = st.name.toLowerCase().includes(q);
        const matchId = st.strategy_id.toLowerCase().includes(q);
        const matchProject = (st.source_project || "").toLowerCase().includes(q);
        if (!matchName && !matchId && !matchProject) return false;
      }
      return true;
    });

    result.sort((a, b) => {
      let valA: any = 0;
      let valB: any = 0;

      const statsA = a.raw_stats || {};
      const statsB = b.raw_stats || {};

      switch (sortField) {
        case "name":
          valA = a.name;
          valB = b.name;
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        case "symbol":
          valA = a.symbol || "";
          valB = b.symbol || "";
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        case "timeframe":
          valA = a.timeframe || "";
          valB = b.timeframe || "";
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        case "source_project":
          valA = a.source_project || "";
          valB = b.source_project || "";
          return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
        case "profit_factor":
          valA = statsA.ProfitFactor ?? 0;
          valB = statsB.ProfitFactor ?? 0;
          break;
        case "profit_factor_oos":
          valA = statsA.ProfitFactorOos ?? 0;
          valB = statsB.ProfitFactorOos ?? 0;
          break;
        case "net_profit":
          valA = statsA.NetProfitUsd ?? 0;
          valB = statsB.NetProfitUsd ?? 0;
          break;
        case "net_profit_oos":
          valA = statsA.NetProfitOosUsd ?? 0;
          valB = statsB.NetProfitOosUsd ?? 0;
          break;
        case "sharpe":
          valA = statsA.SharpeRatio ?? 0;
          valB = statsB.SharpeRatio ?? 0;
          break;
        case "ret_dd":
          valA = statsA.RetDD ?? 0;
          valB = statsB.RetDD ?? 0;
          break;
        case "trades":
          valA = statsA.TradesCount ?? 0;
          valB = statsB.TradesCount ?? 0;
          break;
      }

      return sortAsc ? valA - valB : valB - valA;
    });

    return result;
  }, [strategies, symbolFilter, search, sortField, sortAsc]);

  const alternarOrden = (campo: SortKey) => {
    if (sortField === campo) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(campo);
      setSortAsc(false);
    }
  };

  // Exportar a CSV
  const exportarCSV = () => {
    if (!filtradas.length) return;
    const cabecera = [
      "ID",
      "Nombre",
      "Simbolo",
      "Timeframe",
      "Proyecto",
      "Databank",
      "PF_IS",
      "PF_OOS",
      "NetProfit_IS_USD",
      "NetProfit_OOS_USD",
      "MaxDD_IS_USD",
      "MaxDD_OOS_USD",
      "Sharpe",
      "RetDD",
      "Trades_IS",
      "Trades_OOS",
      "Hash_SHA256",
    ];

    const filas = filtradas.map((st) => {
      const s = st.raw_stats || {};
      return [
        `"${st.strategy_id}"`,
        `"${st.name}"`,
        `"${st.symbol || ""}"`,
        `"${st.timeframe || ""}"`,
        `"${st.source_project || ""}"`,
        `"${st.source_databank || ""}"`,
        s.ProfitFactor ?? "",
        s.ProfitFactorOos ?? "",
        s.NetProfitUsd ?? "",
        s.NetProfitOosUsd ?? "",
        s.MaxDrawdownUsd ?? "",
        s.MaxDrawdownOosUsd ?? "",
        s.SharpeRatio ?? "",
        s.RetDD ?? "",
        s.TradesCount ?? "",
        s.TradesOos ?? "",
        `"${st.strategy_hash}"`,
      ].join(",");
    });

    const csvContent = "data:text/csv;charset=utf-8," + [cabecera.join(","), ...filas].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `censo_sqx_m1_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-3 font-mono text-xs">
      {/* Barra de Filtros y Acciones */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-[var(--text-3)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por nombre, celda o ID..."
              className="pl-8 pr-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-xs text-[var(--text-1)] placeholder-[var(--text-3)] min-w-[240px] focus:outline-none focus:border-[var(--border-strong)]"
            />
          </div>

          <div className="flex items-center gap-1.5 pl-2 border-l border-[var(--border)]">
            <Filter className="w-3.5 h-3.5 text-[var(--text-3)]" />
            <select
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value)}
              className="py-1.5 px-2 rounded bg-[var(--surface-2)] border border-[var(--border)] text-xs text-[var(--text-1)] focus:outline-none"
            >
              <option value="ALL">Todos los Activos ({strategies.length})</option>
              {symbols.map((sym) => (
                <option key={sym} value={sym}>
                  {sym}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={exportarCSV}
            disabled={!filtradas.length}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] hover:bg-[var(--surface-3)] transition text-[var(--text-1)] cursor-pointer disabled:opacity-50"
            title="Descargar censo actual en CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Exportar CSV</span>
          </button>

          <button
            onClick={() => void cargar()}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] border border-[var(--border)] hover:bg-[var(--surface-3)] transition text-[var(--text-1)] cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded-lg text-xs text-[var(--loss)] flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Resumen del Censo */}
      <div className="flex items-center justify-between text-[11px] text-[var(--text-3)] px-1">
        <span>
          Mostrando <strong>{filtradas.length}</strong> de <strong>{strategies.length}</strong> estrategias reales extraídas de SQX
        </span>
        <span>Haz clic en los encabezados para ordenar</span>
      </div>

      {/* Tabla de Estrategias */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--surface-2)]/60 text-[11px] uppercase text-[var(--text-2)]">
              <th className="py-2.5 px-3 cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("name")}>
                <div className="flex items-center gap-1">
                  <span>Estrategia / ID</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("symbol")}>
                <div className="flex items-center gap-1">
                  <span>Activo</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("source_project")}>
                <div className="flex items-center gap-1">
                  <span>Celda M1</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("profit_factor")}>
                <div className="flex items-center justify-end gap-1">
                  <span>PF (IS)</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("profit_factor_oos")}>
                <div className="flex items-center justify-end gap-1">
                  <span>PF (OOS)</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("net_profit")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Net Profit (IS)</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("net_profit_oos")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Net Profit (OOS)</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("sharpe")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Sharpe</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("ret_dd")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Ret/DD</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-2 text-right cursor-pointer hover:text-[var(--text-1)]" onClick={() => alternarOrden("trades")}>
                <div className="flex items-center justify-end gap-1">
                  <span>Trades</span>
                  <ArrowUpDown className="w-3 h-3 text-[var(--text-3)]" />
                </div>
              </th>
              <th className="py-2.5 px-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border)]/50">
            {filtradas.length === 0 ? (
              <tr>
                <td colSpan={11} className="py-8 text-center text-[var(--text-3)]">
                  {loading ? "Cargando censo de estrategias..." : "No se encontraron estrategias con los filtros aplicados."}
                </td>
              </tr>
            ) : (
              filtradas.slice(0, 200).map((st) => {
                const s = st.raw_stats || {};
                const pfIs = s.ProfitFactor;
                const pfOos = s.ProfitFactorOos;
                const netIs = s.NetProfitUsd;
                const netOos = s.NetProfitOosUsd;
                const sharpe = s.SharpeRatio;
                const retDd = s.RetDD;
                const trIs = s.TradesCount;
                const trOos = s.TradesOos;

                return (
                  <tr key={st.strategy_id} className="hover:bg-[var(--surface-2)]/30 transition">
                    {/* Nombre y Hash */}
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-[var(--text-1)] truncate max-w-[200px]" title={st.name}>
                          {st.name}
                        </span>
                        <button
                          onClick={() => copiar(st.strategy_id)}
                          className="text-[var(--text-3)] hover:text-[var(--text-1)]"
                          title="Copiar ID de estrategia"
                        >
                          {copiedId === st.strategy_id ? (
                            <Check className="w-3 h-3 text-[var(--profit)]" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                      <span className="text-[10px] text-[var(--text-3)] block font-mono" title={st.strategy_hash}>
                        hash: {st.strategy_hash ? st.strategy_hash.slice(0, 10) + "…" : "n/a"}
                      </span>
                    </td>

                    {/* Activo y TF */}
                    <td className="py-2 px-2">
                      <span className="font-bold text-[var(--text-1)]">{st.symbol || "-"}</span>
                      <span className="text-[10px] text-[var(--text-3)] block">{st.timeframe || "-"}</span>
                    </td>

                    {/* Celda M1 y Databank */}
                    <td className="py-2 px-2">
                      <span className="text-[var(--text-2)] truncate max-w-[130px] block" title={st.source_project || ""}>
                        {st.source_project || "-"}
                      </span>
                      <span className="text-[10px] text-[var(--text-3)] block">{st.source_databank || "-"}</span>
                    </td>

                    {/* PF IS */}
                    <td className="py-2 px-2 text-right">
                      {pfIs !== undefined && pfIs !== null ? (
                        <span className={pfIs >= 1.25 ? "text-[var(--profit)] font-semibold" : "text-[var(--text-2)]"}>
                          {pfIs.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">-</span>
                      )}
                    </td>

                    {/* PF OOS */}
                    <td className="py-2 px-2 text-right">
                      {pfOos !== undefined && pfOos !== null ? (
                        <span className={pfOos >= 1.1 ? "text-[var(--profit)] font-semibold" : pfOos < 1.0 ? "text-[var(--loss)]" : "text-[var(--text-2)]"}>
                          {pfOos.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">-</span>
                      )}
                    </td>

                    {/* Net Profit IS */}
                    <td className="py-2 px-2 text-right">
                      {netIs !== undefined && netIs !== null ? (
                        <span className={netIs > 0 ? "text-[var(--profit)] font-semibold" : "text-[var(--loss)]"}>
                          ${netIs.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">-</span>
                      )}
                    </td>

                    {/* Net Profit OOS */}
                    <td className="py-2 px-2 text-right">
                      {netOos !== undefined && netOos !== null ? (
                        <span className={netOos > 0 ? "text-[var(--profit)] font-semibold" : "text-[var(--loss)]"}>
                          ${netOos.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">-</span>
                      )}
                    </td>

                    {/* Sharpe */}
                    <td className="py-2 px-2 text-right">
                      {sharpe !== undefined && sharpe !== null ? (
                        <span className={sharpe >= 1.0 ? "text-[var(--profit)]" : "text-[var(--text-2)]"}>
                          {sharpe.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-[var(--text-3)]">-</span>
                      )}
                    </td>

                    {/* Ret/DD */}
                    <td className="py-2 px-2 text-right">
                      {retDd !== undefined && retDd !== null ? (
                        <span className="text-[var(--text-2)]">{retDd.toFixed(2)}</span>
                      ) : (
                        <span className="text-[var(--text-3)]">-</span>
                      )}
                    </td>

                    {/* Trades IS / OOS */}
                    <td className="py-2 px-2 text-right text-[var(--text-2)]">
                      <span>{trIs ?? 0}</span>
                      {trOos !== undefined && trOos !== null && (
                        <span className="text-[10px] text-[var(--text-3)] block">OOS: {trOos}</span>
                      )}
                    </td>

                    {/* Estado */}
                    <td className="py-2 px-3 text-center">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-3)]">
                        {st.validation_status}
                      </span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {filtradas.length > 200 && (
        <div className="p-2 text-center text-[11px] text-[var(--text-3)] bg-[var(--surface-1)] border border-[var(--border)] rounded">
          Mostrando los primeros 200 resultados de {filtradas.length} para optimizar el rendimiento. Usa los filtros o exporta a CSV para ver el lote completo.
        </div>
      )}
    </div>
  );
}
