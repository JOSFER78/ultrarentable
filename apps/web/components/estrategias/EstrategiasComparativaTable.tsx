"use client";

import React, { useState, useMemo } from "react";
import {
  Download,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Columns,
  CheckSquare,
  Square,
  X,
  FileSpreadsheet,
  Search,
  SlidersHorizontal,
} from "lucide-react";

export interface EstrategiaRow {
  strategy_id: string;
  name: string;
  celda: string;
  simbolo: string;
  timeframe: string;
  periodo_desde: string;
  periodo_hasta: string;
  oos_desde: string;
  periodo_label: string;
  oos_label: string;
  net_profit_oos_usd: number | null;
  annual_return_oos_pct: number | null;
  drawdown_oos_usd: number | null;
  net_profit_usd: number | null;
  annual_return_pct: number | null;
  drawdown_usd: number | null;
  trades_oos: number | null;
  trades_total: number | null;
  profit_factor_oos: number | null;
  profit_factor: number | null;
  sharpe_ratio: number | null;
  stability_oos: number | null;
  ret_dd_oos: number | null;
  avg_win_oos: number | null;
  avg_loss_oos: number | null;
  win_loss_ratio: number | null;
  source_payload?: string | null;
  source_artifact_sha256?: string | null;
  canonical_hash?: string;
  pasa_criterio?: boolean;
  sizing?: {
    metodo: string;
    contratos?: number;
    riesgo_pct?: number;
    capital?: number;
  } | null;
  raw_stats?: Record<string, unknown>;
}

interface Props {
  estrategias: EstrategiaRow[];
  totalDisponibles?: number;
}

type SortField =
  | "name"
  | "simbolo"
  | "timeframe"
  | "periodo_label"
  | "oos_label"
  | "net_profit_oos_usd"
  | "annual_return_oos_pct"
  | "drawdown_oos_usd"
  | "trades_oos"
  | "profit_factor_oos"
  | "ret_dd_oos"
  | "sharpe_ratio"
  | "stability_oos";

function formatMoney(val: number | null): React.ReactNode {
  if (val === null || val === undefined || isNaN(val)) {
    return <span className="text-neutral-600">—</span>;
  }
  const isPos = val > 0;
  const isNeg = val < 0;
  const sign = isPos ? "+" : isNeg ? "-" : "";
  const absVal = Math.abs(val).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <span
      className={`font-mono tabular-nums font-semibold ${
        isPos ? "text-green-500" : isNeg ? "text-red-500" : "text-neutral-400"
      }`}
    >
      {sign}${absVal}
    </span>
  );
}

function formatPct(val: number | null): React.ReactNode {
  if (val === null || val === undefined || isNaN(val)) {
    return <span className="text-neutral-600">—</span>;
  }
  const isPos = val > 0;
  const isNeg = val < 0;
  const sign = isPos ? "+" : isNeg ? "-" : "";
  const absVal = Math.abs(val).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  return (
    <span
      className={`font-mono tabular-nums font-medium ${
        isPos ? "text-green-500" : isNeg ? "text-red-500" : "text-neutral-400"
      }`}
    >
      {sign}
      {absVal}%
    </span>
  );
}

function formatRatio(val: number | null): React.ReactNode {
  if (val === null || val === undefined || isNaN(val)) {
    return <span className="text-neutral-600">—</span>;
  }
  return (
    <span className="font-mono tabular-nums text-neutral-300">
      {val.toFixed(2)}
    </span>
  );
}

function formatTf(tf: string): string {
  const t = tf.toUpperCase();
  if (t === "M240" || t === "H4") return "4h";
  if (t === "M60" || t === "H1") return "1h";
  if (t === "M15") return "15m";
  if (t === "M5") return "5m";
  if (t === "M1") return "1m";
  return tf;
}

export default function EstrategiasComparativaTable({
  estrategias,
  totalDisponibles,
}: Props) {
  const [search, setSearch] = useState("");
  const [filterSimbolo, setFilterSimbolo] = useState("TODOS");
  const [filterTf, setFilterTf] = useState("TODOS");
  const [filterCelda, setFilterCelda] = useState("TODAS");
  const [filterSizing, setFilterSizing] = useState("TODOS");
  const [sortField, setSortField] = useState<SortField>("net_profit_oos_usd");
  const [sortAsc, setSortAsc] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Lista de símbolos y celdas únicas
  const simbolos = useMemo(() => {
    const s = new Set<string>();
    estrategias.forEach((e) => {
      if (e.simbolo) s.add(e.simbolo);
    });
    return Array.from(s).sort();
  }, [estrategias]);

  const timeframes = useMemo(() => {
    const t = new Set<string>();
    estrategias.forEach((e) => {
      if (e.timeframe) t.add(formatTf(e.timeframe));
    });
    return Array.from(t).sort();
  }, [estrategias]);

  const celdas = useMemo(() => {
    const c = new Set<string>();
    estrategias.forEach((e) => {
      if (e.celda) c.add(e.celda);
    });
    return Array.from(c).sort();
  }, [estrategias]);

  // Filtrado
  const filtered = useMemo(() => {
    return estrategias.filter((e) => {
      if (
        filterSimbolo !== "TODOS" &&
        e.simbolo.toUpperCase() !== filterSimbolo.toUpperCase()
      ) {
        return false;
      }
      if (
        filterTf !== "TODOS" &&
        formatTf(e.timeframe).toUpperCase() !== filterTf.toUpperCase()
      ) {
        return false;
      }
      if (filterCelda !== "TODAS" && e.celda !== filterCelda) {
        return false;
      }
      if (filterSizing !== "TODOS") {
        const metodo = e.sizing?.metodo || "FixedSize";
        if (metodo !== filterSizing) return false;
      }
      if (search.trim()) {
        const q = search.toLowerCase();
        const matchesName = e.name.toLowerCase().includes(q);
        const matchesCelda = e.celda.toLowerCase().includes(q);
        const matchesId = e.strategy_id.toLowerCase().includes(q);
        if (!matchesName && !matchesCelda && !matchesId) return false;
      }
      return true;
    });
  }, [estrategias, filterSimbolo, filterTf, filterCelda, filterSizing, search]);

  const hayMezclaSizing = useMemo(() => {
    const metodos = new Set<string>();
    filtered.forEach((e) => {
      metodos.add(e.sizing?.metodo || "FixedSize");
    });
    return metodos.size > 1;
  }, [filtered]);

  // Ordenación
  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      let valA: unknown = a[sortField];
      let valB: unknown = b[sortField];

      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      if (typeof valA === "number" && typeof valB === "number") {
        return sortAsc ? valA - valB : valB - valA;
      }

      const strA = String(valA).toLowerCase();
      const strB = String(valB).toLowerCase();
      if (strA < strB) return sortAsc ? -1 : 1;
      if (strA > strB) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [filtered, sortField, sortAsc]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false); // Por defecto descendente en métricas
    }
  };

  const toggleSelect = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedIds(next);
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === sorted.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(sorted.map((s) => s.strategy_id)));
    }
  };

  // Exportar a CSV
  const handleExportCSV = () => {
    const headers = [
      "Estrategia",
      "Celda",
      "Activo",
      "Marco",
      "Periodo Desde",
      "Periodo Hasta",
      "Periodo Label",
      "OOS Desde",
      "OOS Label",
      "Beneficio Neto OOS ($)",
      "Rentabilidad Anual OOS (%)",
      "Caída Máxima OOS ($)",
      "Beneficio Neto IS ($)",
      "Rentabilidad Anual IS (%)",
      "Caída Máxima IS ($)",
      "Operaciones OOS",
      "Operaciones Totales",
      "Factor Beneficio OOS",
      "Factor Beneficio IS",
      "Ratio Ret/DD OOS",
      "Ratio Sharpe",
      "Estabilidad OOS",
      "Media Ganancia OOS ($)",
      "Media Pérdida OOS ($)",
      "Win/Loss Ratio",
      "Ruta Artefacto",
      "SHA256 Artefacto",
      "Hash Canónico",
    ];

    const rows = sorted.map((e) => [
      `"${e.name.replace(/"/g, '""')}"`,
      `"${e.celda}"`,
      `"${e.simbolo}"`,
      `"${formatTf(e.timeframe)}"`,
      `"${e.periodo_desde}"`,
      `"${e.periodo_hasta}"`,
      `"${e.periodo_label}"`,
      `"${e.oos_desde}"`,
      `"${e.oos_label}"`,
      e.net_profit_oos_usd ?? "",
      e.annual_return_oos_pct ?? "",
      e.drawdown_oos_usd ?? "",
      e.net_profit_usd ?? "",
      e.annual_return_pct ?? "",
      e.drawdown_usd ?? "",
      e.trades_oos ?? "",
      e.trades_total ?? "",
      e.profit_factor_oos ?? "",
      e.profit_factor ?? "",
      e.ret_dd_oos ?? "",
      e.sharpe_ratio ?? "",
      e.stability_oos ?? "",
      e.avg_win_oos ?? "",
      e.avg_loss_oos ?? "",
      e.win_loss_ratio ?? "",
      `"${e.source_payload || ""}"`,
      `"${e.source_artifact_sha256 || ""}"`,
      `"${e.canonical_hash || ""}"`,
    ]);

    const csvContent =
      "\uFEFF" +
      [headers.join(";"), ...rows.map((r) => r.join(";"))].join("\r\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `comparativa_estrategias_fondeo.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const selectedList = useMemo(() => {
    return sorted.filter((e) => selectedIds.has(e.strategy_id));
  }, [sorted, selectedIds]);

  return (
    <div className="w-full space-y-3 font-sans text-neutral-100">
      {/* Barra de control superior */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded bg-neutral-800 border border-neutral-700 flex items-center justify-center text-neutral-300">
              <FileSpreadsheet className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-semibold text-neutral-100 flex items-center gap-2">
                <span>Comparativa Tipo Hoja de Cálculo</span>
                <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 border border-neutral-700">
                  {sorted.length.toLocaleString()}{" "}
                  {totalDisponibles ? `de ${totalDisponibles.toLocaleString()}` : ""}{" "}
                  estrategias
                </span>
              </div>
              <p className="text-xs text-neutral-400">
                Periodo probado, periodo fuera de muestra (OOS) y métricas de dinero en dólares reales.
              </p>
            </div>
          </div>

          {/* Botones de acción */}
          <div className="flex items-center gap-2 self-start md:self-auto">
            {selectedIds.size >= 2 && (
              <button
                type="button"
                onClick={() => setShowCompareModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-neutral-800 hover:bg-neutral-700 border border-neutral-700 text-neutral-100 transition-colors"
              >
                <Columns className="w-3.5 h-3.5" />
                <span>Comparar enfrentadas ({selectedIds.size})</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-neutral-100 hover:bg-neutral-200 text-neutral-900 transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Exportar a CSV</span>
            </button>
          </div>
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2 pt-1 border-t border-neutral-800/80">
          {/* Búsqueda */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-neutral-400" />
            <input
              type="text"
              placeholder="Buscar por nombre o ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded bg-neutral-950 border border-neutral-800 text-xs text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-neutral-600"
            />
          </div>

          {/* Activo */}
          <div className="flex items-center gap-1.5 bg-neutral-950 border border-neutral-800 rounded px-2 py-1">
            <span className="text-xs text-neutral-400">Activo:</span>
            <select
              value={filterSimbolo}
              onChange={(e) => setFilterSimbolo(e.target.value)}
              className="w-full bg-transparent text-xs text-neutral-100 focus:outline-none"
            >
              <option value="TODOS" className="bg-neutral-900">Todos</option>
              {simbolos.map((s) => (
                <option key={s} value={s} className="bg-neutral-900">{s}</option>
              ))}
            </select>
          </div>

          {/* Marco */}
          <div className="flex items-center gap-1.5 bg-neutral-950 border border-neutral-800 rounded px-2 py-1">
            <span className="text-xs text-neutral-400">Marco:</span>
            <select
              value={filterTf}
              onChange={(e) => setFilterTf(e.target.value)}
              className="w-full bg-transparent text-xs text-neutral-100 focus:outline-none"
            >
              <option value="TODOS" className="bg-neutral-900">Todos</option>
              {timeframes.map((t) => (
                <option key={t} value={t} className="bg-neutral-900">{t}</option>
              ))}
            </select>
          </div>

          {/* Celda */}
          <div className="flex items-center gap-1.5 bg-neutral-950 border border-neutral-800 rounded px-2 py-1">
            <span className="text-xs text-neutral-400">Celda:</span>
            <select
              value={filterCelda}
              onChange={(e) => setFilterCelda(e.target.value)}
              className="w-full bg-transparent text-xs text-neutral-100 focus:outline-none truncate"
            >
              <option value="TODAS" className="bg-neutral-900">Todas las celdas</option>
              {celdas.map((c) => (
                <option key={c} value={c} className="bg-neutral-900">{c}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Aviso de mezcla de dimensionamientos (A51) */}
        {hayMezclaSizing && (
          <div className="mt-2.5 p-2.5 rounded bg-neutral-950 border border-neutral-700 text-neutral-300 text-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-neutral-400">⚠️</span>
              <span className="font-sans">Estas filas se midieron con reglas distintas y sus rentabilidades no son comparables.</span>
            </div>
            <div className="flex items-center gap-2 font-mono">
              <span className="text-neutral-400">Filtrar regla:</span>
              <select
                value={filterSizing}
                onChange={(e) => setFilterSizing(e.target.value)}
                className="bg-neutral-900 border border-neutral-700 rounded px-2 py-1 text-xs text-neutral-200 focus:outline-none"
              >
                <option value="TODOS">Todas las reglas</option>
                <option value="FixedSize">1 micro fijo (100k USD)</option>
                <option value="RiskFixedBalancePct">0,5% riesgo (50k USD)</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Tabla con scroll horizontal */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto max-h-[640px] overflow-y-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead className="sticky top-0 bg-neutral-950 text-neutral-400 font-semibold border-b border-neutral-800 z-10 select-none">
              <tr>
                <th className="p-2.5 w-8 text-center">
                  <button
                    type="button"
                    onClick={toggleSelectAll}
                    className="text-neutral-400 hover:text-neutral-200"
                    title="Seleccionar todas"
                  >
                    {selectedIds.size === sorted.length && sorted.length > 0 ? (
                      <CheckSquare className="w-4 h-4 text-neutral-200" />
                    ) : (
                      <Square className="w-4 h-4 text-neutral-500" />
                    )}
                  </button>
                </th>

                {/* 1. Estrategia */}
                <th
                  onClick={() => handleSort("name")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap min-w-[200px]"
                >
                  <div className="flex items-center gap-1">
                    <span>Estrategia</span>
                    {sortField === "name" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 2. Activo y marco */}
                <th
                  onClick={() => handleSort("simbolo")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap min-w-[100px]"
                >
                  <div className="flex items-center gap-1">
                    <span>Activo y marco</span>
                    {sortField === "simbolo" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 3. Periodo probado */}
                <th
                  onClick={() => handleSort("periodo_label")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap min-w-[190px]"
                >
                  <div className="flex items-center gap-1">
                    <span>Periodo probado</span>
                    {sortField === "periodo_label" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 4. Fuera de muestra */}
                <th
                  onClick={() => handleSort("oos_label")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap min-w-[160px]"
                >
                  <div className="flex items-center gap-1">
                    <span>Fuera de muestra</span>
                    {sortField === "oos_label" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 5. Beneficio neto fuera de muestra ($) */}
                <th
                  onClick={() => handleSort("net_profit_oos_usd")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap text-right min-w-[140px]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Beneficio neto (OOS)</span>
                    {sortField === "net_profit_oos_usd" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 6. Rentabilidad anual fuera de muestra (%) */}
                <th
                  onClick={() => handleSort("annual_return_oos_pct")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap text-right min-w-[130px]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Retorno Anual (OOS)</span>
                    {sortField === "annual_return_oos_pct" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 7. Caída máxima fuera de muestra ($) */}
                <th
                  onClick={() => handleSort("drawdown_oos_usd")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap text-right min-w-[130px]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Max Drawdown (OOS)</span>
                    {sortField === "drawdown_oos_usd" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 8. Operaciones (dentro / fuera) */}
                <th
                  onClick={() => handleSort("trades_oos")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap text-right min-w-[130px]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Operaciones (IS / OOS)</span>
                    {sortField === "trades_oos" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 9. Factor de beneficio (dentro / fuera) */}
                <th
                  onClick={() => handleSort("profit_factor_oos")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap text-right min-w-[130px]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Profit Factor (IS / OOS)</span>
                    {sortField === "profit_factor_oos" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>

                {/* 10. Ratios (Ret/DD, Sharpe, Estabilidad) */}
                <th
                  onClick={() => handleSort("sharpe_ratio")}
                  className="p-2.5 cursor-pointer hover:text-neutral-200 whitespace-nowrap text-right min-w-[140px]"
                >
                  <div className="flex items-center justify-end gap-1">
                    <span>Ret/DD · Sharpe · Est.</span>
                    {sortField === "sharpe_ratio" ? (
                      sortAsc ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />
                    ) : (
                      <ArrowUpDown className="w-3 h-3 opacity-40" />
                    )}
                  </div>
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-neutral-800">
              {sorted.length === 0 ? (
                <tr>
                  <td colSpan={11} className="p-8 text-center text-neutral-400">
                    No hay estrategias que coincidan con los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                sorted.map((e) => {
                  const isChecked = selectedIds.has(e.strategy_id);
                  return (
                    <tr
                      key={e.strategy_id}
                      className={`hover:bg-neutral-800/60 transition-colors ${
                        isChecked ? "bg-neutral-800/40" : ""
                      }`}
                    >
                      {/* Checkbox */}
                      <td className="p-2.5 text-center">
                        <button
                          type="button"
                          onClick={() => toggleSelect(e.strategy_id)}
                          className="text-neutral-400 hover:text-neutral-200"
                        >
                          {isChecked ? (
                            <CheckSquare className="w-4 h-4 text-neutral-200" />
                          ) : (
                            <Square className="w-4 h-4 text-neutral-600" />
                          )}
                        </button>
                      </td>

                      {/* Estrategia */}
                      <td className="p-2.5 font-mono">
                        <div className="font-semibold text-neutral-100 hover:underline cursor-pointer">
                          {e.name}
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-neutral-500">
                          {e.pasa_criterio ? (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase bg-neutral-800 text-neutral-200 border border-neutral-700">
                              Candidata
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase text-neutral-500">
                              Banco
                            </span>
                          )}
                          <span>{e.celda}</span>
                          {e.source_artifact_sha256 && (
                            <span
                              title={`SHA256: ${e.source_artifact_sha256}`}
                              className="font-mono text-neutral-400"
                            >
                              · {e.source_artifact_sha256.substring(0, 7)}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Activo y marco */}
                      <td className="p-2.5 font-mono">
                        <span className="font-semibold text-neutral-200">
                          {e.simbolo}
                        </span>{" "}
                        <span className="text-neutral-400">· {formatTf(e.timeframe)}</span>
                      </td>

                      {/* Periodo probado */}
                      <td className="p-2.5 font-mono text-neutral-300">
                        {e.periodo_label || `${e.periodo_desde} → ${e.periodo_hasta}`}
                      </td>

                      {/* Fuera de muestra */}
                      <td className="p-2.5 font-mono text-neutral-300">
                        {e.oos_label || `desde ${e.oos_desde}`}
                      </td>

                      {/* Beneficio neto fuera de muestra ($) */}
                      <td className="p-2.5 text-right">
                        {formatMoney(e.net_profit_oos_usd)}
                      </td>

                      {/* Rentabilidad anual fuera de muestra (%) */}
                      <td className="p-2.5 text-right">
                        {formatPct(e.annual_return_oos_pct)}
                      </td>

                      {/* Caída máxima fuera de muestra ($) */}
                      <td className="p-2.5 text-right font-mono tabular-nums text-neutral-300">
                        {e.drawdown_oos_usd !== null && !isNaN(e.drawdown_oos_usd) ? (
                          `$${Math.abs(e.drawdown_oos_usd).toLocaleString("en-US", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}`
                        ) : (
                          <span className="text-neutral-600">—</span>
                        )}
                      </td>

                      {/* Operaciones (dentro / fuera) */}
                      <td className="p-2.5 text-right font-mono tabular-nums text-neutral-300">
                        {e.trades_total !== null && e.trades_oos !== null ? (
                          <span>
                            {e.trades_total} <span className="text-neutral-500">/</span> {e.trades_oos}
                          </span>
                        ) : (
                          <span className="text-neutral-600">—</span>
                        )}
                      </td>

                      {/* Factor de beneficio (dentro / fuera) */}
                      <td className="p-2.5 text-right font-mono tabular-nums text-neutral-300">
                        {e.profit_factor !== null || e.profit_factor_oos !== null ? (
                          <span>
                            {e.profit_factor?.toFixed(2) ?? "—"}{" "}
                            <span className="text-neutral-500">/</span>{" "}
                            {e.profit_factor_oos?.toFixed(2) ?? "—"}
                          </span>
                        ) : (
                          <span className="text-neutral-600">—</span>
                        )}
                      </td>

                      {/* Ratios (Ret/DD, Sharpe, Estabilidad) */}
                      <td className="p-2.5 text-right font-mono tabular-nums text-neutral-300">
                        <span>
                          {e.ret_dd_oos?.toFixed(2) ?? "—"} ·{" "}
                          {e.sharpe_ratio?.toFixed(2) ?? "—"} ·{" "}
                          {e.stability_oos?.toFixed(2) ?? "—"}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de comparación enfrentada */}
      {showCompareModal && selectedList.length >= 2 && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-neutral-900 border border-neutral-800 rounded-xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl">
            {/* Header modal */}
            <div className="p-4 border-b border-neutral-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Columns className="w-5 h-5 text-neutral-300" />
                <h2 className="text-base font-bold text-neutral-100">
                  Comparativa Enfrentada ({selectedList.length} estrategias)
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setShowCompareModal(false)}
                className="p-1.5 rounded hover:bg-neutral-800 text-neutral-400 hover:text-neutral-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido enfrentado */}
            <div className="p-4 overflow-auto flex-1">
              <table className="w-full text-xs text-left border-collapse">
                <thead>
                  <tr className="border-b border-neutral-800">
                    <th className="p-2.5 text-neutral-400 font-semibold w-48">Métrica / Atributo</th>
                    {selectedList.map((s) => (
                      <th key={s.strategy_id} className="p-2.5 font-mono text-neutral-100 font-bold min-w-[180px]">
                        <div>{s.name}</div>
                        <div className="text-[10px] text-neutral-500 font-normal">{s.celda}</div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-800/70">
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Activo y Marco</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-200 font-semibold">
                        {s.simbolo} · {formatTf(s.timeframe)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Periodo Probado</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {s.periodo_label}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Fuera de Muestra (OOS)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {s.oos_label}
                      </td>
                    ))}
                  </tr>
                  <tr className="bg-neutral-950/40">
                    <td className="p-2.5 text-neutral-200 font-bold">Beneficio Neto OOS ($)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5">
                        {formatMoney(s.net_profit_oos_usd)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Rentabilidad Anual OOS (%)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5">
                        {formatPct(s.annual_return_oos_pct)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Caída Máxima OOS ($)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {s.drawdown_oos_usd !== null ? `$${Math.abs(s.drawdown_oos_usd).toFixed(2)}` : "—"}
                      </td>
                    ))}
                  </tr>
                  <tr className="bg-neutral-950/40">
                    <td className="p-2.5 text-neutral-200 font-bold">Beneficio Neto IS ($)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5">
                        {formatMoney(s.net_profit_usd)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Operaciones (IS / OOS)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {s.trades_total ?? "—"} / {s.trades_oos ?? "—"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Profit Factor (IS / OOS)</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {s.profit_factor?.toFixed(2) ?? "—"} / {s.profit_factor_oos?.toFixed(2) ?? "—"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Ratio Sharpe</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {formatRatio(s.sharpe_ratio)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Estabilidad OOS</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-neutral-300">
                        {formatRatio(s.stability_oos)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Artefacto Físico</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-[10px] text-neutral-400 break-all">
                        {s.source_payload || "—"}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2.5 text-neutral-400 font-medium">Huella SHA-256</td>
                    {selectedList.map((s) => (
                      <td key={s.strategy_id} className="p-2.5 font-mono text-[10px] text-neutral-400 break-all">
                        {s.source_artifact_sha256 || "—"}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Footer modal */}
            <div className="p-4 border-t border-neutral-800 flex justify-end">
              <button
                type="button"
                onClick={() => setShowCompareModal(false)}
                className="px-4 py-2 rounded text-xs font-semibold bg-neutral-800 hover:bg-neutral-700 text-neutral-100 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
