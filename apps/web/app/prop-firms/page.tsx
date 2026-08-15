"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";

interface EvalRules {
  target_usd: number;
  target_pct: string;
  max_drawdown_usd: number;
  drawdown_type: string;
  min_trading_days: number;
  consistency_pct: number;
  consistency_rule_desc: string;
  news_allowed: boolean;
  overnight_allowed: boolean;
  bot_sqx_allowed: boolean;
}

interface FundedRules {
  activation_fee_usd: number;
  activation_fee_type: string;
  funded_drawdown_type: string;
  drawdown_lock_at_starting_balance: boolean;
  min_winning_days_before_first_payout: number;
  winning_day_threshold_usd: number;
  buffer_required_usd: number;
  consistency_pct_payout: number;
  payout_frequency: string;
  payout_split_first: string;
  payout_split_subsequent: string;
  max_payout_per_request: string;
  processing_time_hours: string;
}

interface AccountPlan {
  id?: string;
  account_size: string;
  account_size_usd?: number;
  price_usd: number;
  promo_price_usd?: number;
  promo_code?: string;
  activation_fee_usd: number;
  effective_cost_usd?: number;
  cost_per_1k_target?: number;
  cost_per_1k_drawdown?: number;
  target_usd?: number;
  max_drawdown_usd?: number;
  drawdown_type?: string;
  eval_rules?: EvalRules;
  funded_rules?: FundedRules;
  platforms_supported?: string[];
}

interface PropFirm {
  id: string;
  name: string;
  score: number;
  grade: string;
  tier: number;
  website_url: string;
  official_rules_url: string;
  bot_sqx_compatible: boolean;
  bot_policy_summary: string;
  payout_rating: string;
  eod_drawdown_available: boolean;
  activation_fee_summary: string;
  split_pct: string;
  highlights: string[];
  accounts: AccountPlan[];
  last_verified: string;
}

type SortField =
  | "effective_cost"
  | "cost_per_1k_target"
  | "cost_per_1k_dd"
  | "score"
  | "name"
  | "price"
  | "activation";
type SortOrder = "asc" | "desc";

export default function PropFirmsPage() {
  const [firms, setFirms] = useState<PropFirm[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  // Main Mode Tabs: MATRIX vs COMPARATOR vs REPORT
  const [mainViewMode, setMainViewMode] = useState<"MATRIX" | "COMPARATOR" | "REPORT">("MATRIX");
  const [docContent, setDocContent] = useState<string | null>(null);
  const [loadingDoc, setLoadingDoc] = useState<boolean>(false);
  const [reportSubTab, setReportSubTab] = useState<"SUMMARY" | "RAW_MD">("SUMMARY");

  // Side-by-side Selected Firms for Comparator Mode
  const [selectedCompareIds, setSelectedCompareIds] = useState<string[]>(["myfundedfutures", "topstep", "apextraderfunding"]);

  // Modal State for Detailed Inspection
  const [selectedRowDetail, setSelectedRowDetail] = useState<{
    firm: PropFirm;
    account: AccountPlan;
  } | null>(null);
  const [modalTab, setModalTab] = useState<"EVAL" | "FUNDED">("EVAL");

  // Filters
  const [search, setSearch] = useState("");
  const [selectedSize, setSelectedSize] = useState<string>("50K"); // Default 50K Cohort
  const [botFilter, setBotFilter] = useState<string>("ALL");
  const [drawdownFilter, setDrawdownFilter] = useState<string>("ALL");
  const [noActivationOnly, setNoActivationOnly] = useState<boolean>(false);

  // Sorting
  const [sortField, setSortField] = useState<SortField>("cost_per_1k_dd");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

  useEffect(() => {
    fetchFirms();
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const v = params.get("view");
      if (v === "report" || v === "doc" || v === "docs") {
        setMainViewMode("REPORT");
        fetchResearchDoc();
      } else if (v === "comparator") {
        setMainViewMode("COMPARATOR");
      } else if (v === "matrix") {
        setMainViewMode("MATRIX");
      }
    }
  }, []);

  const fetchResearchDoc = async () => {
    if (docContent) return;
    setLoadingDoc(true);
    try {
      const res = await fetch("/api/v1/prop-firms/research-doc");
      if (res.ok) {
        const data = await res.json();
        setDocContent(data.content);
      }
    } catch (err) {
      console.error("Error loading research document:", err);
    } finally {
      setLoadingDoc(false);
    }
  };

  const fetchFirms = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/prop-firms");
      if (!res.ok) throw new Error("Error fetching prop firms");
      const data = await res.json();
      setFirms(data);
    } catch (err) {
      console.error("Error loading prop firms:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLiveRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg("Re-verificando APIs y servidores en tiempo real...");
    try {
      const res = await fetch("/api/v1/prop-firms/refresh-database", {
        method: "POST",
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        setRefreshMsg(`[OK] ${data.message || "Base de datos refrescada"} (${data.refreshed_at || new Date().toISOString()})`);
      } else {
        setRefreshMsg(`[ERROR] ${data.error || "Fallo en la sincronización"}`);
      }
    } catch (err: any) {
      setRefreshMsg("[ERROR] Error de conexión al refrescar datos.");
    } finally {
      setRefreshing(false);
      setTimeout(() => setRefreshMsg(null), 4000);
    }
  };

  const exportCSV = () => {
    if (!comparisonRows.length) return;
    const headers = [
      "Firma", "Score", "Plan", "Precio Eval", "Promo Code", "Drawdown Type", "Target USD",
      "Consistencia Eval", "Cuota Activacion", "SUMA COSTETOTAL", "Coste / $1K DD",
      "Buffer Requerido", "Frecuencia Pago", "SQX Bot Compatible"
    ];
    const csvLines = [
      headers.join(","),
      ...comparisonRows.map((r) => [
        `"${r.firm.name}"`,
        r.firm.score,
        `"${r.account.account_size}"`,
        r.eval_price,
        `"${r.account.promo_code || ""}"`,
        `"${r.drawdown_type}"`,
        r.target_usd,
        `"${r.consistency_pct_eval}%"`,
        r.activation_fee,
        r.effective_cost,
        r.cost_per_1k_dd.toFixed(2),
        r.buffer_required,
        `"${r.payout_freq}"`,
        r.firm.bot_sqx_compatible ? "SI" : "NO"
      ].join(","))
    ].join("\n");

    const blob = new Blob([csvLines], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `prop_firms_database_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportJSON = () => {
    const dataStr = JSON.stringify(firms, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `prop_firms_database_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Flattened & STRICTLY ALIGNED accounts table
  const comparisonRows = useMemo(() => {
    const rows: {
      firm: PropFirm;
      account: AccountPlan;
      eval_price: number;
      activation_fee: number;
      effective_cost: number;
      cost_per_1k_target: number;
      cost_per_1k_dd: number;
      target_usd: number;
      max_drawdown_usd: number;
      drawdown_type: string;
      consistency_pct_eval: number;
      buffer_required: number;
      payout_freq: string;
      consistency_pct_payout: number;
      split_first: string;
    }[] = [];

    if (!Array.isArray(firms)) return rows;

    firms.forEach((firm) => {
      if (!firm || !Array.isArray(firm.accounts)) return;

      if (botFilter === "BOT_ONLY" && !firm.bot_sqx_compatible) return;
      if (botFilter === "NO_BOTS" && firm.bot_sqx_compatible) return;
      if (drawdownFilter === "EOD" && !firm.eod_drawdown_available) return;

      firm.accounts.forEach((acc) => {
        if (!acc) return;
        const accName = (acc.account_size || "").toUpperCase();

        if (selectedSize !== "ALL") {
          if (selectedSize === "25K" && !/\b25K\b/i.test(accName)) return;
          if (selectedSize === "50K" && (/\b150K\b/i.test(accName) || !/\b50K\b/i.test(accName))) return;
          if (selectedSize === "100K" && !/\b100K\b/i.test(accName)) return;
          if (selectedSize === "150K" && !/\b150K\b/i.test(accName)) return;
        }

        const targetUsd = acc.eval_rules?.target_usd ?? acc.target_usd ?? 3000;
        const maxDrawdownUsd = acc.eval_rules?.max_drawdown_usd ?? acc.max_drawdown_usd ?? 2000;
        const drawdownType = acc.eval_rules?.drawdown_type ?? acc.drawdown_type ?? "Trailing";
        const consistencyPctEval = acc.eval_rules?.consistency_pct ?? 50;
        const bufferRequired = acc.funded_rules?.buffer_required_usd ?? 0;
        const payoutFreq = acc.funded_rules?.payout_frequency ?? firm.payout_rating ?? "Semanal";
        const consistencyPctPayout = acc.funded_rules?.consistency_pct_payout ?? 40;
        const splitFirst = acc.funded_rules?.payout_split_first ?? firm.split_pct ?? "90%";

        if (drawdownFilter === "EOD" && !drawdownType.toUpperCase().includes("EOD")) return;
        if (drawdownFilter === "TRAILING" && drawdownType.toUpperCase().includes("EOD")) return;
        if (noActivationOnly && acc.activation_fee_usd > 0) return;

        if (search) {
          const q = search.toLowerCase();
          const match =
            firm.name.toLowerCase().includes(q) ||
            (acc.account_size || "").toLowerCase().includes(q) ||
            (firm.bot_policy_summary || "").toLowerCase().includes(q);
          if (!match) return;
        }

        const evalPrice = acc.promo_price_usd ?? acc.price_usd ?? 0;
        const activationFee = acc.activation_fee_usd ?? 0;
        const effectiveCost = evalPrice + activationFee;
        const targetK = targetUsd > 0 ? targetUsd / 1000 : 1;
        const ddK = maxDrawdownUsd > 0 ? maxDrawdownUsd / 1000 : 1;
        const costPer1kTarget = effectiveCost / targetK;
        const costPer1kDd = effectiveCost / ddK;

        rows.push({
          firm,
          account: acc,
          eval_price: evalPrice,
          activation_fee: activationFee,
          effective_cost: effectiveCost,
          cost_per_1k_target: costPer1kTarget,
          cost_per_1k_dd: costPer1kDd,
          target_usd: targetUsd,
          max_drawdown_usd: maxDrawdownUsd,
          drawdown_type: drawdownType,
          consistency_pct_eval: consistencyPctEval,
          buffer_required: bufferRequired,
          payout_freq: payoutFreq,
          consistency_pct_payout: consistencyPctPayout,
          split_first: splitFirst,
        });
      });
    });

    rows.sort((a, b) => {
      let valA: any;
      let valB: any;

      if (sortField === "effective_cost") {
        valA = a.effective_cost;
        valB = b.effective_cost;
      } else if (sortField === "cost_per_1k_target") {
        valA = a.cost_per_1k_target;
        valB = b.cost_per_1k_target;
      } else if (sortField === "cost_per_1k_dd") {
        valA = a.cost_per_1k_dd;
        valB = b.cost_per_1k_dd;
      } else if (sortField === "score") {
        valA = a.firm.score;
        valB = b.firm.score;
      } else if (sortField === "name") {
        valA = a.firm.name;
        valB = b.firm.name;
      } else if (sortField === "price") {
        valA = a.eval_price;
        valB = b.eval_price;
      } else if (sortField === "activation") {
        valA = a.activation_fee;
        valB = b.activation_fee;
      }

      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });

    return rows;
  }, [
    firms,
    search,
    selectedSize,
    botFilter,
    drawdownFilter,
    noActivationOnly,
    sortField,
    sortOrder,
  ]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  return (
    <div style={{ padding: "16px 24px", width: "100%", maxWidth: "100%", boxSizing: "border-box", fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Header Responsivo 100% Full Width */}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "12px", marginBottom: "14px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "12px", width: "100%" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap", marginBottom: "4px" }}>
            <h1 style={{ fontSize: "22px", fontWeight: "800", color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
              <span></span> Hub de Transparencia de Fondeo: Examen vs Cuenta Financiada
            </h1>
            <span style={{ background: "rgba(59,130,246,0.18)", color: "#93c5fd", border: "1px solid rgba(59,130,246,0.35)", padding: "2px 8px", borderRadius: "12px", fontSize: "11px", fontWeight: "700" }}>
              Verificado: 2 de agosto de 2026
            </span>
          </div>
          <p style={{ color: "#94a3b8", fontSize: "12px", margin: 0 }}>
            100% Ancho de pantalla | Comparativa sin trampas entre el examen de entrada y las reglas reales de cobro de 34 firmas.
          </p>
        </div>

        {/* Mode Toggle Controls & Exports */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "center" }}>
          <button
            onClick={() => setMainViewMode("MATRIX")}
            style={{
              background: mainViewMode === "MATRIX" ? "#2563eb" : "rgba(30, 41, 59, 0.8)",
              color: "#ffffff",
              border: "1px solid rgba(255,255,255,0.1)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            Matriz Completa
          </button>

          <button
            onClick={() => setMainViewMode("COMPARATOR")}
            style={{
              background: mainViewMode === "COMPARATOR" ? "#c084fc" : "rgba(30, 41, 59, 0.8)",
              color: mainViewMode === "COMPARATOR" ? "#000" : "#94a3b8",
              border: "1px solid rgba(255,255,255,0.1)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            Comparador Cara a Cara
          </button>

          <button
            onClick={() => {
              setMainViewMode("REPORT");
              fetchResearchDoc();
            }}
            style={{
              background: mainViewMode === "REPORT" ? "#10b981" : "rgba(30, 41, 59, 0.8)",
              color: "#ffffff",
              border: "1px solid rgba(255,255,255,0.1)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            Informe de Investigación (Doc 2026)
          </button>

          <button
            onClick={exportCSV}
            style={{
              background: "rgba(30, 41, 59, 0.8)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            CSV
          </button>

          <button
            onClick={exportJSON}
            style={{
              background: "rgba(30, 41, 59, 0.8)",
              color: "#fbbf24",
              border: "1px solid rgba(251, 191, 36, 0.3)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: "pointer",
            }}
          >
            JSON
          </button>

          <button
            onClick={handleLiveRefresh}
            disabled={refreshing}
            style={{
              background: refreshing ? "#475569" : "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "#ffffff",
              border: "none",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              cursor: refreshing ? "not-allowed" : "pointer",
            }}
          >
            {refreshing ? "[..] Actualizando..." : "[ ] Actualizar Datos"}
          </button>

          <Link
            href="/fondeo"
            style={{
              background: "rgba(59, 130, 246, 0.15)",
              color: "#60a5fa",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              padding: "6px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              fontWeight: "700",
              textDecoration: "none",
            }}
          >
            Pipeline Fondeo →
          </Link>
        </div>
      </div>

      {/* Live Refresh Banner */}
      {refreshMsg && (
        <div style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)", padding: "6px 12px", borderRadius: "6px", fontWeight: "600", fontSize: "12px", marginBottom: "12px", width: "100%", boxSizing: "border-box" }}>
          {refreshMsg}
        </div>
      )}

      {/* VIEW 1: FULL WIDTH TRANSPARENCY MATRIX */}
      {mainViewMode === "MATRIX" && (
        <>
          {/* Filter Toolbar Full Width */}
          <div style={{ background: "rgba(15, 23, 42, 0.85)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px 14px", marginBottom: "14px", width: "100%", boxSizing: "border-box" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "10px", alignItems: "center", width: "100%" }}>
              {/* Cohort Selector */}
              <div style={{ background: "rgba(37, 99, 235, 0.15)", border: "1px solid rgba(37, 99, 235, 0.4)", padding: "4px 6px", borderRadius: "5px" }}>
                <label style={{ display: "block", color: "#60a5fa", fontSize: "9px", fontWeight: "800", textTransform: "uppercase" }}>
                  [COHORTE] TAMAÑO
                </label>
                <select
                  value={selectedSize}
                  onChange={(e) => setSelectedSize(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(15, 23, 42, 0.95)",
                    border: "1px solid #2563eb",
                    borderRadius: "4px",
                    padding: "5px 6px",
                    color: "#ffffff",
                    fontWeight: "700",
                    fontSize: "12px",
                  }}
                >
                  <option value="50K">Cohorte 50K USD</option>
                  <option value="100K">Cohorte 100K USD</option>
                  <option value="150K">Cohorte 150K USD</option>
                  <option value="ALL">Mostrar Todas las Cuentas</option>
                </select>
              </div>

              {/* Search */}
              <div>
                <label style={{ display: "block", color: "#64748b", fontSize: "9px", fontWeight: "700", textTransform: "uppercase" }}>
                  Buscar Firma / Regla
                </label>
                <input
                  type="text"
                  placeholder="Topstep, MFFU, EOD..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(30, 41, 59, 0.9)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: "4px",
                    padding: "5px 6px",
                    color: "#f8fafc",
                    fontSize: "12px",
                  }}
                />
              </div>

              {/* Bot Compatibility */}
              <div>
                <label style={{ display: "block", color: "#64748b", fontSize: "9px", fontWeight: "700", textTransform: "uppercase" }}>
                  Política Bots / SQX
                </label>
                <select
                  value={botFilter}
                  onChange={(e) => setBotFilter(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(30, 41, 59, 0.9)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: "4px",
                    padding: "5px 6px",
                    color: "#f8fafc",
                    fontSize: "12px",
                  }}
                >
                  <option value="ALL">Todos los Permisos</option>
                  <option value="BOT_ONLY">Solo Bots SQX</option>
                  <option value="NO_BOTS">Solo Manual</option>
                </select>
              </div>

              {/* Drawdown Type */}
              <div>
                <label style={{ display: "block", color: "#64748b", fontSize: "9px", fontWeight: "700", textTransform: "uppercase" }}>
                  Tipo Drawdown
                </label>
                <select
                  value={drawdownFilter}
                  onChange={(e) => setDrawdownFilter(e.target.value)}
                  style={{
                    width: "100%",
                    background: "rgba(30, 41, 59, 0.9)",
                    border: "1px solid rgba(255, 255, 255, 0.15)",
                    borderRadius: "4px",
                    padding: "5px 6px",
                    color: "#f8fafc",
                    fontSize: "12px",
                  }}
                >
                  <option value="ALL">Todos los Drawdowns</option>
                  <option value="EOD">Solo EOD (Cierre)</option>
                  <option value="TRAILING">Solo Trailing</option>
                </select>
              </div>
            </div>
          </div>

          {/* FULL SCREEN WIDTH TABLE WITH TWO DISTINCT VISUAL BLOCKS */}
          {loading ? (
            <div style={{ textAlign: "center", padding: "40px", color: "#94a3b8" }}>Cargando matriz comparativa...</div>
          ) : (
            <div
              style={{
                overflowX: "auto",
                width: "100%",
                background: "rgba(15, 23, 42, 0.95)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
                borderRadius: "8px",
                boxShadow: "0 4px 24px rgba(0,0,0,0.5)",
              }}
            >
              <table style={{ width: "100%", minWidth: "1400px", borderCollapse: "collapse", textAlign: "left", fontSize: "11px" }}>
                <thead>
                  {/* Phase Headers */}
                  <tr style={{ background: "#090d16", borderBottom: "1px solid rgba(255,255,255,0.1)", textTransform: "uppercase", fontSize: "10px", fontWeight: "800" }}>
                    <th colSpan={3} style={{ padding: "6px 10px", color: "#94a3b8" }}>Identificación Firma</th>
                    <th colSpan={4} style={{ padding: "6px 10px", background: "rgba(37, 99, 235, 0.15)", color: "#60a5fa", textAlign: "center", borderLeft: "1px solid #2563eb", borderRight: "1px solid #2563eb" }}>
                      FASE 1: EVALUACIÓN (EXAMEN)
                    </th>
                    <th colSpan={5} style={{ padding: "6px 10px", background: "rgba(168, 85, 247, 0.15)", color: "#c084fc", textAlign: "center" }}>
                      FASE 2: FONDEADO REAL & RETIROS
                    </th>
                  </tr>
                  <tr style={{ background: "rgba(30, 41, 59, 0.98)", borderBottom: "1px solid rgba(255, 255, 255, 0.15)", color: "#94a3b8", fontWeight: "700" }}>
                    <th style={{ padding: "8px 10px", position: "sticky", left: 0, zIndex: 10, background: "#1e293b", minWidth: "140px" }} onClick={() => toggleSort("name")}>
                      Firma
                    </th>
                    <th style={{ padding: "8px 8px" }}>Score</th>
                    <th style={{ padding: "8px 10px" }}>Plan</th>
                    
                    {/* Phase 1: Eval */}
                    <th style={{ padding: "8px 8px" }} onClick={() => toggleSort("price")}>
                      Precio Eval [S]
                    </th>
                    <th style={{ padding: "8px 8px" }}>Drawdown Examen</th>
                    <th style={{ padding: "8px 8px" }}>Target USD</th>
                    <th style={{ padding: "8px 8px" }}>Consistencia Eval</th>

                    {/* Phase 2: Funded */}
                    <th style={{ padding: "8px 8px" }} onClick={() => toggleSort("activation")}>
                      Cuota Activación [S]
                    </th>
                    <th style={{ padding: "8px 10px", background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8" }} onClick={() => toggleSort("effective_cost")}>
                      SUMA TOTAL [S]
                    </th>
                    <th style={{ padding: "8px 10px", background: "rgba(168, 85, 247, 0.15)", color: "#c084fc" }} onClick={() => toggleSort("cost_per_1k_dd")}>
                      Coste / $1K DD [S]
                    </th>
                    <th style={{ padding: "8px 8px" }}>Colchón Mín. (Buffer)</th>
                    <th style={{ padding: "8px 8px" }}>Frecuencia Pago</th>
                    <th style={{ padding: "8px 10px", textAlign: "center" }}>Acción</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map((row, idx) => {
                    const { firm, account, eval_price, activation_fee, effective_cost, cost_per_1k_dd, target_usd, drawdown_type, consistency_pct_eval, buffer_required, payout_freq } = row;

                    return (
                      <tr
                        key={`${firm.id}-${account.account_size}-${idx}`}
                        style={{
                          borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                          background: idx % 2 === 0 ? "rgba(30, 41, 59, 0.35)" : "transparent",
                        }}
                      >
                        {/* Sticky Firm Column */}
                        <td
                          style={{
                            padding: "8px 10px",
                            position: "sticky",
                            left: 0,
                            zIndex: 5,
                            background: idx % 2 === 0 ? "#111827" : "#0f172a",
                            fontWeight: "700",
                            color: "#f8fafc",
                            whiteSpace: "nowrap",
                            borderRight: "1px solid rgba(255,255,255,0.1)",
                          }}
                        >
                          {firm.name}
                        </td>

                        {/* Score */}
                        <td style={{ padding: "8px 8px" }}>
                          <span style={{ background: "rgba(34, 197, 94, 0.2)", color: "#4ade80", padding: "2px 5px", borderRadius: "3px", fontWeight: "700" }}>
                            {firm.score}
                          </span>
                        </td>

                        {/* Plan */}
                        <td style={{ padding: "8px 10px", color: "#e2e8f0", fontWeight: "700", whiteSpace: "nowrap" }}>
                          {account.account_size}
                        </td>

                        {/* Eval Price */}
                        <td style={{ padding: "8px 8px", whiteSpace: "nowrap" }}>
                          <strong style={{ color: "#4ade80" }}>${eval_price.toFixed(2)}</strong>
                        </td>

                        {/* Drawdown Examen */}
                        <td style={{ padding: "8px 8px", whiteSpace: "nowrap" }}>
                          {drawdown_type.includes("EOD") ? (
                            <span style={{ background: "rgba(168, 85, 247, 0.2)", color: "#c084fc", padding: "2px 6px", borderRadius: "3px", fontWeight: "700" }}>
                              EOD
                            </span>
                          ) : (
                            <span style={{ background: "rgba(51, 65, 85, 0.6)", color: "#cbd5e1", padding: "2px 6px", borderRadius: "3px" }}>
                              Trailing
                            </span>
                          )}
                        </td>

                        {/* Target USD */}
                        <td style={{ padding: "8px 8px", color: "#cbd5e1", whiteSpace: "nowrap" }}>
                          ${target_usd}
                        </td>

                        {/* Consistencia Eval */}
                        <td style={{ padding: "8px 8px", whiteSpace: "nowrap" }}>
                          <span style={{ background: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", padding: "2px 6px", borderRadius: "3px", fontWeight: "700" }}>
                            {consistency_pct_eval}% max/día
                          </span>
                        </td>

                        {/* Activation Fee */}
                        <td style={{ padding: "8px 8px", whiteSpace: "nowrap" }}>
                          {activation_fee === 0 ? (
                            <span style={{ color: "#4ade80", fontWeight: "700" }}>$0 (Gratis)</span>
                          ) : (
                            <span style={{ color: "#f87171", fontWeight: "600" }}>${activation_fee.toFixed(2)}</span>
                          )}
                        </td>

                        {/* SUM TOTAL */}
                        <td style={{ padding: "8px 10px", background: "rgba(56, 189, 248, 0.08)", whiteSpace: "nowrap" }}>
                          <strong style={{ color: "#38bdf8", fontSize: "12px" }}>
                            ${effective_cost.toFixed(2)}
                          </strong>
                        </td>

                        {/* Cost / $1K DD */}
                        <td style={{ padding: "8px 10px", background: "rgba(168, 85, 247, 0.08)", whiteSpace: "nowrap" }}>
                          <span style={{ color: "#c084fc", fontWeight: "800" }}>
                            ${cost_per_1k_dd.toFixed(2)}
                          </span>
                        </td>

                        {/* Buffer Required */}
                        <td style={{ padding: "8px 8px", whiteSpace: "nowrap" }}>
                          {buffer_required === 0 ? (
                            <span style={{ color: "#4ade80", fontWeight: "700" }}>$0 (Sin colchón)</span>
                          ) : (
                            <span style={{ color: "#f87171", fontWeight: "700" }}>${buffer_required} retención</span>
                          )}
                        </td>

                        {/* Payout Freq */}
                        <td style={{ padding: "8px 8px", color: "#94a3b8", whiteSpace: "nowrap" }}>
                          {payout_freq}
                        </td>

                        {/* Action Modal Button */}
                        <td style={{ padding: "8px 10px", textAlign: "center", whiteSpace: "nowrap" }}>
                          <button
                            onClick={() => {
                              setSelectedRowDetail({ firm, account });
                              setModalTab("EVAL");
                            }}
                            style={{
                              background: "linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)",
                              color: "#ffffff",
                              border: "none",
                              padding: "5px 10px",
                              borderRadius: "4px",
                              fontSize: "11px",
                              fontWeight: "700",
                              cursor: "pointer",
                            }}
                          >
                            [AUDITAR REGLAS]
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* VIEW 2: SIDE-BY-SIDE EXAM VS FUNDED COMPARATOR CARDS */}
      {mainViewMode === "COMPARATOR" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
          <div style={{ background: "rgba(15, 23, 42, 0.9)", border: "1px solid rgba(192, 132, 252, 0.3)", borderRadius: "8px", padding: "14px 18px" }}>
            <h3 style={{ margin: "0 0 6px 0", color: "#c084fc", fontSize: "15px", fontWeight: "800" }}>
              Comparativa Cara a Cara: La Verdad del Examen vs Fondeado Real
            </h3>
            <p style={{ margin: 0, fontSize: "12px", color: "#cbd5e1" }}>
              Compara directamente las condiciones de entrada contra los requisitos de cobro y retención de capital.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px", width: "100%" }}>
            {firms
              .filter((f) => selectedCompareIds.includes(f.id))
              .map((firm) => {
                const acc50k = firm.accounts.find((a) => a.account_size.includes("50K")) || firm.accounts[0];
                if (!acc50k) return null;

                const evalPrice = acc50k.promo_price_usd ?? acc50k.price_usd;
                const totalCost = evalPrice + acc50k.activation_fee_usd;
                const buffer = acc50k.funded_rules?.buffer_required_usd ?? 0;

                return (
                  <div
                    key={firm.id}
                    style={{
                      background: "rgba(15, 23, 42, 0.95)",
                      border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: "10px",
                      padding: "18px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "14px",
                    }}
                  >
                    {/* Header */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "10px" }}>
                      <div>
                        <h4 style={{ margin: 0, color: "#f8fafc", fontSize: "16px", fontWeight: "800" }}>{firm.name}</h4>
                        <span style={{ fontSize: "11px", color: "#94a3b8" }}>{acc50k.account_size}</span>
                      </div>
                      <span style={{ background: "rgba(34, 197, 94, 0.2)", color: "#4ade80", padding: "3px 8px", borderRadius: "4px", fontWeight: "800", fontSize: "12px" }}>
                        Score {firm.score}
                      </span>
                    </div>

                    {/* Phase 1 Box */}
                    <div style={{ background: "rgba(37, 99, 235, 0.1)", border: "1px solid rgba(37, 99, 235, 0.3)", borderRadius: "6px", padding: "12px" }}>
                      <strong style={{ color: "#60a5fa", fontSize: "12px", display: "block", marginBottom: "6px" }}>FASE 1: EXAMEN / ENTRADA</strong>
                      <div style={{ fontSize: "11px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "4px" }}>
                        <div>• Precio Examen: <strong style={{ color: "#4ade80" }}>${evalPrice.toFixed(2)}</strong></div>
                        <div>• Drawdown Examen: <strong>{acc50k.eval_rules?.drawdown_type ?? acc50k.drawdown_type}</strong></div>
                        <div>• Consistencia Examen: <strong>{acc50k.eval_rules?.consistency_pct ?? 50}% max/día</strong></div>
                        <div>• Días Mínimos: <strong>{acc50k.eval_rules?.min_trading_days ?? 2} d</strong></div>
                      </div>
                    </div>

                    {/* Phase 2 Box */}
                    <div style={{ background: "rgba(168, 85, 247, 0.1)", border: "1px solid rgba(168, 85, 247, 0.3)", borderRadius: "6px", padding: "12px" }}>
                      <strong style={{ color: "#c084fc", fontSize: "12px", display: "block", marginBottom: "6px" }}>FASE 2: REAL & RETIROS</strong>
                      <div style={{ fontSize: "11px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "4px" }}>
                        <div>• Cuota Activación: <strong>${acc50k.activation_fee_usd.toFixed(2)}</strong></div>
                        <div>• SUMA COSTETOTAL: <strong style={{ color: "#38bdf8", fontSize: "13px" }}>${totalCost.toFixed(2)}</strong></div>
                        <div>• Colchón Mínimo Retenido (Buffer): {buffer === 0 ? <strong style={{ color: "#4ade80" }}>$0 (Sin trampa)</strong> : <strong style={{ color: "#f87171" }}>${buffer} retenidos</strong>}</div>
                        <div>• Frecuencia Retiro: <strong>{acc50k.funded_rules?.payout_frequency ?? firm.payout_rating}</strong></div>
                        <div>• Profit Split: <strong>{acc50k.funded_rules?.payout_split_first ?? firm.split_pct}</strong></div>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* VIEW 3: FULL RESEARCH REPORT DOCUMENT */}
      {mainViewMode === "REPORT" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px", width: "100%" }}>
          {/* Sub-tab navigation */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "rgba(15, 23, 42, 0.9)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "8px", padding: "12px 16px" }}>
            <div>
              <h2 style={{ margin: 0, fontSize: "18px", color: "#10b981", fontWeight: 800, display: "flex", alignItems: "center", gap: "8px" }}>
                <span></span> Base de Datos Comparativa de Empresas de Fondeo 2026
              </h2>
              <span style={{ fontSize: "11px", color: "#94a3b8" }}>
                Investigación exhaustiva del 2 de agosto de 2026 · 34 Firmas de Futuros · Reglas SQX / Hermes / VPS
              </span>
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={() => setReportSubTab("SUMMARY")}
                style={{
                  background: reportSubTab === "SUMMARY" ? "#10b981" : "rgba(30, 41, 59, 0.8)",
                  color: reportSubTab === "SUMMARY" ? "#000" : "#94a3b8",
                  border: "none",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontWeight: 700,
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                Resumen Analítico
              </button>
              <button
                onClick={() => {
                  setReportSubTab("RAW_MD");
                  fetchResearchDoc();
                }}
                style={{
                  background: reportSubTab === "RAW_MD" ? "#10b981" : "rgba(30, 41, 59, 0.8)",
                  color: reportSubTab === "RAW_MD" ? "#000" : "#94a3b8",
                  border: "none",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontWeight: 700,
                  fontSize: "12px",
                  cursor: "pointer",
                }}
              >
                Markdown Completo (1.753 Líneas)
              </button>
            </div>
          </div>

          {reportSubTab === "SUMMARY" && (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Executive Summary Cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "14px" }}>
                <div style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "8px", padding: "16px" }}>
                  <h3 style={{ margin: "0 0 8px 0", color: "#34d399", fontSize: "14px", fontWeight: 800 }}>
                    [TOP 5] Proveedores Prioritarios (Nivel 1)
                  </h3>
                  <div style={{ fontSize: "12px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <div>1. <strong>My Funded Futures (MFFU)</strong> — $39.50 (50K Rapid), $0 activación, EOD, EAs OK.</div>
                    <div>2. <strong>Topstep</strong> — $49/m, API oficial ProjectX, split 90/10. <em>No VPS/VPN</em>.</div>
                    <div>3. <strong>TradeDay</strong> — $59/m, $0 activación, EOD fijo, cobro día 1.</div>
                    <div>4. <strong>Tradeify</strong> — $58.20 (Promo TNT), $0 activación en Select, EOD.</div>
                    <div>5. <strong>OneUp Trader</strong> — $75/m, $75 activación, modelo con socio de fondeo.</div>
                  </div>
                </div>

                <div style={{ background: "rgba(59, 130, 246, 0.1)", border: "1px solid rgba(59, 130, 246, 0.3)", borderRadius: "8px", padding: "16px" }}>
                  <h3 style={{ margin: "0 0 8px 0", color: "#60a5fa", fontSize: "14px", fontWeight: "800" }}>
                    [FÓRMULA] Coste Efectivo Real
                  </h3>
                  <p style={{ margin: "0 0 10px 0", fontSize: "11px", color: "#94a3b8" }}>
                    El precio anunciado casi nunca es el coste real. Separa evaluación, mensualidad, activación y colchón.
                  </p>
                  <div style={{ background: "rgba(0,0,0,0.4)", padding: "10px", borderRadius: "6px", fontFamily: "monospace", fontSize: "11px", color: "#38bdf8" }}>
                    Coste Real = Eval + Renovaciones + Activación + Resets - Descuentos
                  </div>
                  <div style={{ marginTop: "10px", fontSize: "11px", color: "#cbd5e1" }}>
                    • MFFU 50K Rapid: $79 × 0.50 (300K) + $0 = <strong>$39.50</strong><br />
                    • Topstep 50K Standard: $49 + $149 = <strong>$198.00</strong><br />
                    • Bulenox 50K: $175 × 0.11 (GUIDE) + $148 = <strong>$167.25</strong>
                  </div>
                </div>

                <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "8px", padding: "16px" }}>
                  <h3 style={{ margin: "0 0 8px 0", color: "#f87171", fontSize: "14px", fontWeight: "800" }}>
                    🚫 Prohibiciones & Restricciones Críticas
                  </h3>
                  <div style={{ fontSize: "12px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <div>• <strong>Apex Trader Funding & Take Profit Trader</strong>: 🚫 BOTS TOTALMENTE PROHIBIDOS. Solo discrecional manual.</div>
                    <div>• <strong>Topstep</strong>: Permite bots pero 🚫 PROHIBIDO VPS, VPN o servidores remotos (tráfico debe ser del PC local).</div>
                    <div>• <strong>Earn2Trade</strong>: Prohíbe copiar operaciones entre cuentas desde 2026.</div>
                    <div>• <strong>FundedNext / MFFU</strong>: Prohibido HFT, abuso de fills simulados y account rolling/stacking.</div>
                  </div>
                </div>
              </div>

              {/* Promo Codes & Coupons Grid */}
              <div style={{ background: "rgba(15, 23, 42, 0.85)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "16px" }}>
                <h3 style={{ margin: "0 0 12px 0", fontSize: "15px", color: "#f8fafc", fontWeight: 800 }}>
                  Códigos Promocionales y Descuentos Observados (2 de Agosto de 2026)
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
                  {[
                    { firm: "Apex Trader Funding", promo: "hasta 90%", code: "SAVENOW", note: "Evaluaciones nuevas (solo manual)" },
                    { firm: "Bulenox", promo: "89% Dto", code: "GUIDE", note: "Option 1 ($148 activación)" },
                    { firm: "DayTraders", promo: "85% Dto", code: "GUIDE", note: "Trail Accounts" },
                    { firm: "TradeDay", promo: "55% Dto + $0 Act", code: "GUIDE", note: "Según producto" },
                    { firm: "FundedNext Futures", promo: "55% Dto", code: "JLFLEX", note: "Plan Flex" },
                    { firm: "My Funded Futures", promo: "50% Dto", code: "300K", note: "Todas las cuentas Rapid ($0 act)" },
                    { firm: "Tradeify", promo: "40% Dto", code: "TNT", note: "Primeras 5 compras ($0 act Select)" },
                    { firm: "Take Profit Trader", promo: "40% Dto + $0 Act", code: "NOFEE40", note: "Tests (solo manual)" },
                  ].map((item) => (
                    <div key={item.firm} style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px", padding: "10px" }}>
                      <div style={{ fontSize: "12px", fontWeight: 700, color: "#60a5fa" }}>{item.firm}</div>
                      <div style={{ fontSize: "14px", fontWeight: 800, color: "#4ade80", marginTop: "2px" }}>{item.promo}</div>
                      <div style={{ fontSize: "11px", color: "#fbbf24", fontFamily: "monospace", marginTop: "4px" }}>Código: {item.code}</div>
                      <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "2px" }}>{item.note}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {reportSubTab === "RAW_MD" && (
            <div style={{ background: "#090d16", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "8px", padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "8px" }}>
                <span style={{ fontSize: "12px", color: "#38bdf8", fontWeight: 700 }}>
                  Documento Original: BASE_DATOS_EMPRESAS_FONDEO_FUTUROS_2026-08-02.md
                </span>
                <button
                  onClick={() => {
                    if (docContent) {
                      navigator.clipboard.writeText(docContent);
                      alert("Documento copiado al portapapeles");
                    }
                  }}
                  style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "#fff", padding: "4px 8px", borderRadius: "4px", fontSize: "11px", cursor: "pointer" }}
                >
                  Copiar Texto
                </button>
              </div>

              {loadingDoc ? (
                <div style={{ padding: "40px", textAlign: "center", color: "#94a3b8", fontSize: "13px" }}>
                  ⏳ Cargando documento de investigación desde el servidor...
                </div>
              ) : (
                <pre
                  style={{
                    margin: 0,
                    padding: "16px",
                    background: "rgba(0,0,0,0.5)",
                    borderRadius: "6px",
                    color: "#e2e8f0",
                    fontSize: "12px",
                    lineHeight: 1.6,
                    fontFamily: "Menlo, Monaco, Consolas, monospace",
                    maxHeight: "700px",
                    overflowY: "auto",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                  }}
                >
                  {docContent || "Presiona 'Cargar Documento' para obtener la investigación original."}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* INTERACTIVE DETAILED INSPECTION MODAL */}
      {selectedRowDetail && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(2, 6, 23, 0.85)",
            backdropFilter: "blur(8px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: "16px",
          }}
        >
          <div
            style={{
              background: "#0f172a",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              borderRadius: "12px",
              width: "100%",
              maxWidth: "750px",
              maxHeight: "90vh",
              overflowY: "auto",
              padding: "24px",
              boxShadow: "0 20px 50px rgba(0,0,0,0.8)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid rgba(255,255,255,0.1)", paddingBottom: "12px" }}>
              <div>
                <h2 style={{ margin: 0, fontSize: "18px", color: "#f8fafc", fontWeight: "800" }}>
                  {selectedRowDetail.firm.name} — {selectedRowDetail.account.account_size}
                </h2>
                <p style={{ margin: "4px 0 0 0", fontSize: "12px", color: "#94a3b8" }}>
                  Auditoría completa de la Fase Evaluativa (Prueba) y Fase Financiada (Live/Retiros).
                </p>
              </div>
              <button
                onClick={() => setSelectedRowDetail(null)}
                style={{ background: "rgba(255,255,255,0.1)", border: "none", color: "#fff", borderRadius: "50%", width: "30px", height: "30px", cursor: "pointer", fontWeight: "700" }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
              <button
                onClick={() => setModalTab("EVAL")}
                style={{
                  flex: 1,
                  padding: "10px",
                  borderRadius: "6px",
                  border: "none",
                  fontWeight: "700",
                  fontSize: "12px",
                  cursor: "pointer",
                  background: modalTab === "EVAL" ? "#2563eb" : "rgba(30, 41, 59, 0.8)",
                  color: modalTab === "EVAL" ? "#fff" : "#94a3b8",
                }}
              >
                FASE 1: EVALUACIÓN (EXAMEN)
              </button>

              <button
                onClick={() => setModalTab("FUNDED")}
                style={{
                  flex: 1,
                  padding: "10px",
                  borderRadius: "6px",
                  border: "none",
                  fontWeight: "700",
                  fontSize: "12px",
                  cursor: "pointer",
                  background: modalTab === "FUNDED" ? "#2563eb" : "rgba(30, 41, 59, 0.8)",
                  color: modalTab === "FUNDED" ? "#fff" : "#94a3b8",
                }}
              >
                FASE 2: FINANCIADA Y RETIROS
              </button>
            </div>

            {modalTab === "EVAL" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ background: "rgba(30, 41, 59, 0.5)", padding: "14px", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#38bdf8", fontSize: "13px" }}>[OBJETIVOS] Límites del Examen</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", color: "#e2e8f0" }}>
                    <div>• <strong>Objetivo de Profit:</strong> ${selectedRowDetail.account.eval_rules?.target_usd ?? selectedRowDetail.account.target_usd ?? 3000} ({selectedRowDetail.account.eval_rules?.target_pct ?? "6%"})</div>
                    <div>• <strong>Límite de Pérdida (Drawdown):</strong> ${selectedRowDetail.account.eval_rules?.max_drawdown_usd ?? selectedRowDetail.account.max_drawdown_usd ?? 2000}</div>
                    <div>• <strong>Tipo de Drawdown:</strong> {selectedRowDetail.account.eval_rules?.drawdown_type ?? selectedRowDetail.account.drawdown_type ?? "Trailing"}</div>
                    <div>• <strong>Días Mínimos:</strong> {selectedRowDetail.account.eval_rules?.min_trading_days ?? 2} días</div>
                  </div>
                </div>

                <div style={{ background: "rgba(30, 41, 59, 0.5)", padding: "14px", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#fbbf24", fontSize: "13px" }}>Regla de Consistencia en el Examen</h4>
                  <p style={{ margin: 0, fontSize: "12px", color: "#cbd5e1" }}>
                    {selectedRowDetail.account.eval_rules?.consistency_rule_desc ?? "Regla de consistencia estándar."} (Máximo {selectedRowDetail.account.eval_rules?.consistency_pct ?? 50}% en un solo día).
                  </p>
                </div>
              </div>
            )}

            {modalTab === "FUNDED" && (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div style={{ background: "rgba(34, 197, 94, 0.1)", padding: "14px", borderRadius: "8px", border: "1px solid rgba(34, 197, 94, 0.3)" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#4ade80", fontSize: "13px" }}>[RETIROS & SPLIT] Cuota de Activación y Reparto de Beneficios</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "12px", color: "#e2e8f0" }}>
                    <div>• <strong>Cuota de Activación al Aprobar:</strong> {selectedRowDetail.account.funded_rules?.activation_fee_type ?? `$${selectedRowDetail.account.activation_fee_usd}`}</div>
                    <div>• <strong>Primer Tramo Profit Split:</strong> {selectedRowDetail.account.funded_rules?.payout_split_first ?? selectedRowDetail.firm.split_pct}</div>
                    <div>• <strong>Tramo Subsecuente Split:</strong> {selectedRowDetail.account.funded_rules?.payout_split_subsequent ?? "90%"}</div>
                  </div>
                </div>

                <div style={{ background: "rgba(30, 41, 59, 0.5)", padding: "14px", borderRadius: "8px" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#c084fc", fontSize: "13px" }}>Drawdown en Cuenta Financiada y Colchón Mínimo</h4>
                  <div style={{ fontSize: "12px", color: "#e2e8f0", display: "flex", flexDirection: "column", gap: "6px" }}>
                    <div>• <strong>Comportamiento del Drawdown:</strong> {selectedRowDetail.account.funded_rules?.funded_drawdown_type ?? "Trailing al balance inicial"}</div>
                    <div>• <strong>Colchón no retirable (Buffer):</strong> ${selectedRowDetail.account.funded_rules?.buffer_required_usd ?? 0}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
