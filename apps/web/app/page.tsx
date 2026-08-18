/**
 * apps/web/app/page.tsx
 * PANEL MAESTRO DE ESTRATEGIAS APROBADAS & COMBINACIÓN INTELIGENTE DE CARTERA
 * 100% DATOS REALES DIRECTAMENTE DESDE SQLite / FASTAPI (CERO MOCKS)
 */
"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import { useTelemetryStream } from "@/hooks/useTelemetryStream";

interface ApprovedCandidate {
  candidate_id: string;
  name: string;
  route: string;
  symbol: string;
  timeframe: string;
  status: string;
  annual_return_pct: number;
  monthly_return_pct: number;
  net_profit_oos_usd: number;
  profit_factor_is: number;
  profit_factor_oos: number;
  max_dd_pct: number;
  wfe_pct: number;
  mc_robustness_score: number;
  trades_count: number;
  ratio_oos_is: number;
  sha256: string;
}

interface PortfolioCombinationResult {
  strategies_count: number;
  total_capital_usd: number;
  combined_annual_return_pct: number;
  combined_monthly_return_pct: number;
  combined_max_dd_pct: number;
  individual_max_dd_pct: number;
  dd_reduction_pct: number;
  correlation_matrix: number[][];
  allocations: {
    candidate_id: string;
    name: string;
    symbol: string;
    timeframe: string;
    weight: number;
    allocated_capital_usd: number;
    individual_dd_pct: number;
    annual_return_pct: number;
  }[];
}

export default function MasterApprovedStrategiesPage() {
  const { systemMetrics } = useTelemetryStream();
  const [activeTab, setActiveTab] = useState<"FONDEO" | "ULTRA" | "PORTFOLIO">("FONDEO");
  const [candidates, setCandidates] = useState<ApprovedCandidate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filtros interactivos estilo Excel
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [minAnnualReturn, setMinAnnualReturn] = useState<number>(0);
  const [maxDrawdownFilter, setMaxDrawdownFilter] = useState<number>(100);
  const [sortField, setSortField] = useState<keyof ApprovedCandidate>("annual_return_pct");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Selección para combinación inteligente de cartera
  const [selectedForPortfolio, setSelectedForPortfolio] = useState<string[]>([]);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioCombinationResult | null>(null);
  const [combining, setCombining] = useState<boolean>(false);
  const [totalCapital, setTotalCapital] = useState<number>(10000);

  // Carga de candidatos reales aprobados
  const fetchApprovedCandidates = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v2/candidates/approved");
      if (res.ok) {
        const data = await res.json();
        const cands: ApprovedCandidate[] = data.candidates || [];
        setCandidates(cands);

        // Preseleccionar 3 de Ultra para combinación inicial si existen
        const ultraList = cands.filter((c) => c.route === "ULTRA").slice(0, 3).map((c) => c.candidate_id);
        if (ultraList.length > 0 && selectedForPortfolio.length === 0) {
          setSelectedForPortfolio(ultraList);
        }
      }
    } catch (err) {
      // network error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovedCandidates();
  }, []);

  // Recalcular combinación inteligente cuando cambie la selección
  useEffect(() => {
    if (selectedForPortfolio.length === 0) {
      setPortfolioResult(null);
      return;
    }

    const runCombine = async () => {
      setCombining(true);
      try {
        const res = await fetch("/api/v2/portfolio/combine", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            candidate_ids: selectedForPortfolio,
            total_capital_usd: totalCapital,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.status === "SUCCESS") {
            setPortfolioResult(data);
          }
        }
      } catch (e) {
        // error
      } finally {
        setCombining(false);
      }
    };

    runCombine();
  }, [selectedForPortfolio, totalCapital]);

  const toggleSelectStrategy = (id: string) => {
    setSelectedForPortfolio((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  // Filtrado y ordenación
  const filteredData = useMemo(() => {
    let list = candidates.filter((c) => {
      if (activeTab === "FONDEO" && c.route !== "FONDEO") return false;
      if (activeTab === "ULTRA" && c.route !== "ULTRA") return false;
      if (activeTab === "PORTFOLIO" && !selectedForPortfolio.includes(c.candidate_id)) return false;

      if (c.annual_return_pct < minAnnualReturn) return false;
      if (c.max_dd_pct > maxDrawdownFilter) return false;

      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchName = c.name.toLowerCase().includes(q);
        const matchId = c.candidate_id.toLowerCase().includes(q);
        const matchSym = c.symbol.toLowerCase().includes(q);
        if (!matchName && !matchId && !matchSym) return false;
      }

      return true;
    });

    list.sort((a, b) => {
      const valA = a[sortField];
      const valB = b[sortField];
      if (typeof valA === "number" && typeof valB === "number") {
        return sortOrder === "asc" ? valA - valB : valB - valA;
      }
      return sortOrder === "asc"
        ? String(valA).localeCompare(String(valB))
        : String(valB).localeCompare(String(valA));
    });

    return list;
  }, [candidates, activeTab, minAnnualReturn, maxDrawdownFilter, searchQuery, sortField, sortOrder, selectedForPortfolio]);

  const handleSort = (field: keyof ApprovedCandidate) => {
    if (sortField === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  return (
    <div style={{ padding: "24px", maxWidth: "1600px", margin: "0 auto" }}>
      {/* 1. HEADER DEL PANEL MAESTRO */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span style={{ fontSize: "11px", fontWeight: 900, color: "#63e1b4", fontFamily: "var(--font-mono, monospace)", textTransform: "uppercase" }}>
              💎 PANEL MAESTRO DE ESTRATEGIAS VALIDADAS & CARTERA INTELIGENTE
            </span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.5px" }}>
            Catálogo Filtrado & Combinación de Portfolios
          </h1>
          <p style={{ color: "#94a3b8", fontSize: "13px", marginTop: "6px", maxWidth: "1000px" }}>
            El motor cuantitativo procesa de forma 100% asistida y automática las fases de generación genética, backtests, Monte Carlo y debate semántico.
            A continuación se presentan únicamente las <strong>estrategias que han superado todas las compuertas de calidad</strong>, listas para operar individualmente o en cartera descorrelacionada.
          </p>
        </div>
      </div>

      {/* 2. PIPELINE AUTOMATIZADO ASISTIDO (RESUMEN DEL MOTOR) */}
      <div style={{ background: "rgba(16, 23, 34, 0.6)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: "10px", padding: "12px 18px", marginBottom: "24px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", fontFamily: "var(--font-mono, monospace)" }}>
          <span style={{ color: "#64748b" }}>MOTOR ASISTIDO:</span>
          <span style={{ color: "#34d399" }}>1. Genética SQX</span>
          <span style={{ color: "#475569" }}>→</span>
          <span style={{ color: "#34d399" }}>2. FastEngine OOS</span>
          <span style={{ color: "#475569" }}>→</span>
          <span style={{ color: "#34d399" }}>3. Monte Carlo 10k</span>
          <span style={{ color: "#475569" }}>→</span>
          <span style={{ color: "#34d399" }}>4. Debate Semántico IA</span>
          <span style={{ color: "#475569" }}>→</span>
          <strong style={{ color: "#63e1b4" }}>5. Evidence Gate APROBADO ✅</strong>
        </div>
        <div style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
          Total Aprobadas: <strong style={{ color: "#ffffff" }}>{candidates.length} estrategias</strong>
        </div>
      </div>

      {/* 3. PESTAÑAS MAESTRAS: FONDEO vs ULTRA vs COMBINACIÓN DE CARTERA */}
      <div style={{ display: "flex", gap: "8px", marginBottom: "20px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: "12px", flexWrap: "wrap" }}>
        <button
          onClick={() => setActiveTab("FONDEO")}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: 800,
            cursor: "pointer",
            fontFamily: "var(--font-mono, monospace)",
            background: activeTab === "FONDEO" ? "rgba(56, 189, 248, 0.15)" : "transparent",
            color: activeTab === "FONDEO" ? "#38bdf8" : "#64748b",
            border: activeTab === "FONDEO" ? "1px solid rgba(56, 189, 248, 0.4)" : "1px solid transparent",
          }}
        >
          🏛️ FONDEO CME / PROP FIRMS ({candidates.filter((c) => c.route === "FONDEO").length})
        </button>

        <button
          onClick={() => setActiveTab("ULTRA")}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: 800,
            cursor: "pointer",
            fontFamily: "var(--font-mono, monospace)",
            background: activeTab === "ULTRA" ? "rgba(99, 225, 180, 0.15)" : "transparent",
            color: activeTab === "ULTRA" ? "#63e1b4" : "#64748b",
            border: activeTab === "ULTRA" ? "1px solid rgba(99, 225, 180, 0.4)" : "1px solid transparent",
          }}
        >
          ⚡ ULTRA BINGX CONVEXO ({candidates.filter((c) => c.route === "ULTRA").length})
        </button>

        <button
          onClick={() => setActiveTab("PORTFOLIO")}
          style={{
            padding: "10px 20px",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: 800,
            cursor: "pointer",
            fontFamily: "var(--font-mono, monospace)",
            background: activeTab === "PORTFOLIO" ? "rgba(167, 139, 250, 0.2)" : "transparent",
            color: activeTab === "PORTFOLIO" ? "#a78bfa" : "#64748b",
            border: activeTab === "PORTFOLIO" ? "1px solid rgba(167, 139, 250, 0.5)" : "1px solid transparent",
          }}
        >
          💼 COMBINACIÓN INTELIGENTE DE CARTERA ({selectedForPortfolio.length} SELECCIONADAS)
        </button>
      </div>

      {/* 4. MÓDULO DE COMBINACIÓN INTELIGENTE DE ESTRATEGIAS (SI SECCIÓN PORTFOLIO O SELECCIÓN ACTIVA) */}
      {portfolioResult && (
        <div style={{ background: "rgba(16, 23, 34, 0.85)", border: "1px solid rgba(167, 139, 250, 0.3)", borderRadius: "14px", padding: "20px", marginBottom: "28px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <span style={{ fontSize: "10px", fontWeight: 800, color: "#a78bfa", fontFamily: "var(--font-mono, monospace)" }}>
                SISTEMA INTELIGENTE DE COMPENSACIÓN & DESCORRELACIÓN
              </span>
              <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#ffffff", margin: "2px 0 0 0" }}>
                Cartera Combinada ({portfolioResult.strategies_count} Estrategias Interconectadas)
              </h3>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "11px", color: "#64748b" }}>Capital Total:</span>
              <input
                type="number"
                value={totalCapital}
                onChange={(e) => setTotalCapital(Number(e.target.value))}
                style={{
                  background: "rgba(0, 0, 0, 0.4)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "6px",
                  padding: "4px 8px",
                  color: "#ffffff",
                  fontSize: "12px",
                  fontFamily: "var(--font-mono, monospace)",
                  width: "100px",
                }}
              />
            </div>
          </div>

          {/* 4 KPIS DE CARTERA */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px", marginBottom: "18px" }}>
            <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>RENTABILIDAD ANUAL COMBINADA</div>
              <div style={{ fontSize: "22px", fontWeight: 900, color: "#34d399", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                +{portfolioResult.combined_annual_return_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                +{portfolioResult.combined_monthly_return_pct.toFixed(2)}% / mes estimado
              </div>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>MAX DRAWDOWN COMBINADO</div>
              <div style={{ fontSize: "22px", fontWeight: 900, color: "#38bdf8", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                {portfolioResult.combined_max_dd_pct.toFixed(1)}%
              </div>
              <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 700 }}>
                📉 Reducción del {portfolioResult.dd_reduction_pct}% frente a individual
              </div>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>EFECTO COMPENSACIÓN</div>
              <div style={{ fontSize: "22px", fontWeight: 900, color: "#a78bfa", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                ACTIVO
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Tendencias cubren fases laterales
              </div>
            </div>

            <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "14px", borderRadius: "10px", border: "1px solid rgba(255, 255, 255, 0.04)" }}>
              <div style={{ fontSize: "10px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>ESTRUCTURA DE PESOS</div>
              <div style={{ fontSize: "22px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)", marginTop: "2px" }}>
                Inverse Vol / ERC
              </div>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>
                Ponderación por riesgo
              </div>
            </div>
          </div>

          {/* DESGLOSE DE PESOS Y ASIGNACIÓN */}
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", fontFamily: "var(--font-mono, monospace)" }}>
              <thead>
                <tr style={{ background: "rgba(0, 0, 0, 0.4)", color: "#64748b", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px" }}>ESTRATEGIA</th>
                  <th style={{ padding: "8px 12px" }}>ACTIVO / TF</th>
                  <th style={{ padding: "8px 12px" }}>PESO (%)</th>
                  <th style={{ padding: "8px 12px" }}>CAPITAL ASIGNADO</th>
                  <th style={{ padding: "8px 12px" }}>RENT. ANUAL</th>
                  <th style={{ padding: "8px 12px" }}>DD INDIVIDUAL</th>
                </tr>
              </thead>
              <tbody>
                {portfolioResult.allocations.map((a) => (
                  <tr key={a.candidate_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                    <td style={{ padding: "10px 12px", color: "#ffffff", fontWeight: 700 }}>{a.name}</td>
                    <td style={{ padding: "10px 12px", color: "#94a3b8" }}>{a.symbol} ({a.timeframe})</td>
                    <td style={{ padding: "10px 12px", color: "#a78bfa", fontWeight: 800 }}>{(a.weight * 100).toFixed(1)}%</td>
                    <td style={{ padding: "10px 12px", color: "#63e1b4", fontWeight: 800 }}>${a.allocated_capital_usd.toFixed(2)}</td>
                    <td style={{ padding: "10px 12px", color: "#34d399" }}>+{a.annual_return_pct.toFixed(1)}%</td>
                    <td style={{ padding: "10px 12px", color: "#fbbf24" }}>{a.individual_dd_pct.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. BARRA DE FILTROS ESTILO EXCEL */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px", marginBottom: "20px", display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
          {/* BUSCADOR */}
          <div>
            <label style={{ fontSize: "10px", color: "#64748b", display: "block", marginBottom: "4px", fontFamily: "var(--font-mono, monospace)" }}>BUSCAR ESTRATEGIA / PAR</label>
            <input
              type="text"
              placeholder="Filtrar por nombre, ID o activo..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                background: "rgba(0, 0, 0, 0.35)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                padding: "6px 12px",
                color: "#ffffff",
                fontSize: "12px",
                fontFamily: "var(--font-mono, monospace)",
                width: "220px",
              }}
            />
          </div>

          {/* RENTABILIDAD ANUAL MÍNIMA */}
          <div>
            <label style={{ fontSize: "10px", color: "#64748b", display: "block", marginBottom: "4px", fontFamily: "var(--font-mono, monospace)" }}>RENTABILIDAD ANUAL MÍN. (%)</label>
            <input
              type="number"
              value={minAnnualReturn}
              onChange={(e) => setMinAnnualReturn(Number(e.target.value))}
              style={{
                background: "rgba(0, 0, 0, 0.35)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                padding: "6px 10px",
                color: "#ffffff",
                fontSize: "12px",
                fontFamily: "var(--font-mono, monospace)",
                width: "110px",
              }}
            />
          </div>

          {/* MAX DRAWDOWN */}
          <div>
            <label style={{ fontSize: "10px", color: "#64748b", display: "block", marginBottom: "4px", fontFamily: "var(--font-mono, monospace)" }}>MAX DRAWDOWN (%)</label>
            <input
              type="number"
              value={maxDrawdownFilter}
              onChange={(e) => setMaxDrawdownFilter(Number(e.target.value))}
              style={{
                background: "rgba(0, 0, 0, 0.35)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                padding: "6px 10px",
                color: "#ffffff",
                fontSize: "12px",
                fontFamily: "var(--font-mono, monospace)",
                width: "110px",
              }}
            />
          </div>
        </div>

        <div style={{ fontSize: "12px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
          Mostrando <strong style={{ color: "#ffffff" }}>{filteredData.length}</strong> de {candidates.length} estrategias aprobadas
        </div>
      </div>

      {/* 6. TABLA DE EXCEL AVANZADA DE ESTRATEGIAS APROBADAS */}
      <div style={{ background: "rgba(16, 23, 34, 0.75)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "14px", padding: "20px", marginBottom: "28px" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
            <thead>
              <tr style={{ background: "rgba(0, 0, 0, 0.45)", color: "#64748b", textAlign: "left", fontFamily: "var(--font-mono, monospace)" }}>
                <th style={{ padding: "10px 8px", textAlign: "center" }}>CARTERA</th>
                <th onClick={() => handleSort("name")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  ESTRATEGIA & PAR {sortField === "name" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("route")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  TRACK {sortField === "route" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("annual_return_pct")} style={{ padding: "10px 12px", cursor: "pointer", color: "#63e1b4" }}>
                  RENT. ANUAL (%) {sortField === "annual_return_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("monthly_return_pct")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  RENT. MENSUAL {sortField === "monthly_return_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("profit_factor_oos")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  PF OOS {sortField === "profit_factor_oos" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("max_dd_pct")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  MAX DD (%) {sortField === "max_dd_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("wfe_pct")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  WFE (%) {sortField === "wfe_pct" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th onClick={() => handleSort("mc_robustness_score")} style={{ padding: "10px 12px", cursor: "pointer" }}>
                  MC SCORE {sortField === "mc_robustness_score" && (sortOrder === "asc" ? "▲" : "▼")}
                </th>
                <th style={{ padding: "10px 12px" }}>HASH CANÓNICO</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={10} style={{ padding: "30px", textAlign: "center", color: "#64748b" }}>
                    Cargando catálogo de estrategias validadas desde SQLite...
                  </td>
                </tr>
              ) : filteredData.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ padding: "30px", textAlign: "center", color: "#64748b" }}>
                    No hay estrategias que cumplan los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                filteredData.map((c) => {
                  const isSelected = selectedForPortfolio.includes(c.candidate_id);
                  return (
                    <tr
                      key={c.candidate_id}
                      style={{
                        borderBottom: "1px solid rgba(255,255,255,0.04)",
                        background: isSelected ? "rgba(167, 139, 250, 0.08)" : "transparent",
                      }}
                    >
                      <td style={{ padding: "12px 8px", textAlign: "center" }}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleSelectStrategy(c.candidate_id)}
                          style={{ cursor: "pointer", accentColor: "#a78bfa" }}
                        />
                      </td>
                      <td style={{ padding: "12px" }}>
                        <div style={{ fontWeight: 800, color: "#ffffff", fontSize: "13px" }}>{c.name}</div>
                        <div style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                          {c.symbol} · {c.timeframe} · {c.trades_count} trades
                        </div>
                      </td>
                      <td style={{ padding: "12px" }}>
                        <span
                          style={{
                            fontSize: "9px",
                            fontWeight: 900,
                            padding: "3px 6px",
                            borderRadius: "4px",
                            background: c.route === "ULTRA" ? "rgba(99, 225, 180, 0.12)" : "rgba(56, 189, 248, 0.12)",
                            color: c.route === "ULTRA" ? "#63e1b4" : "#38bdf8",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {c.route}
                        </span>
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#34d399", fontWeight: 900, fontSize: "14px" }}>
                        +{c.annual_return_pct.toFixed(1)}%
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#e2e8f0", fontWeight: 700 }}>
                        +{c.monthly_return_pct.toFixed(2)}%
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: c.profit_factor_oos >= 1.2 ? "#34d399" : "#ffffff", fontWeight: 700 }}>
                        {c.profit_factor_oos.toFixed(2)}x
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: c.max_dd_pct <= 5.0 ? "#34d399" : "#fbbf24" }}>
                        {c.max_dd_pct.toFixed(1)}%
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#a78bfa", fontWeight: 800 }}>
                        {c.wfe_pct.toFixed(1)}%
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#38bdf8", fontWeight: 800 }}>
                        {c.mc_robustness_score.toFixed(1)}%
                      </td>
                      <td style={{ padding: "12px", fontFamily: "var(--font-mono, monospace)", color: "#64748b", fontSize: "10px" }}>
                        {c.sha256.substring(0, 12)}...
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
