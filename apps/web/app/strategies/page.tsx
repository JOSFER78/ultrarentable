"use client";

import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import Link from "next/link";
import { useEngineVersion } from "@/hooks/useEngineVersion";

interface Candidate {
  candidate_id: string;
  name: string;
  route: "ULTRA" | "FONDEO" | string;
  symbol: string;
  timeframe: string;
  status: string;
  status_reason?: string;
  tier?: string;
  tier_label?: string;
  gates_passed_count?: number;
  overall_score?: number;
  engine_version?: string;
  validation_pipeline_version?: string;
  duration_info?: any;
  metrics?: {
    in_sample?: { net_profit_usd?: number; trades?: number; profit_factor?: number; max_drawdown_pct?: number; win_rate_pct?: number };
    out_of_sample?: { net_profit_usd?: number; roi_pct?: number; annualized_roi_pct?: number; monthly_roi_pct?: number; trades_per_month?: number; base_capital_usd?: number; trades?: number; profit_factor?: number; max_drawdown_pct?: number; win_rate_pct?: number };
    anti_overfit?: { ratio_oos_is?: number; wfo_pass_pct?: number; monte_carlo_score?: number };
  };
  scorecard_json?: string;
  created_at?: string;
}

export default function StrategiesExplorerPage() {
  const { version, versionName } = useEngineVersion();
  const [mounted, setMounted] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSilentRefreshing, setIsSilentRefreshing] = useState(false);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(0); // 0 = Manual / Sin parpadeos
  const [selectedRoute, setSelectedRoute] = useState<"ALL" | "ULTRA" | "FONDEO">("ALL");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("ALL");
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>("ALL");
  const [selectedEngineVersion, setSelectedEngineVersion] = useState<string>("ALL");
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [activeModalTab, setActiveModalTab] = useState<"DNA" | "SCORECARD" | "EXPORT">("SCORECARD");
  const [exportCode, setExportCode] = useState<string>("");
  const [exportType, setExportType] = useState<"PINESCRIPT" | "NINJATRADER" | "PYTHON">("PINESCRIPT");
  const [copied, setCopied] = useState(false);
  const [firebaseSyncing, setFirebaseSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [showRulesDrawer, setShowRulesDrawer] = useState(false);
  const [isCompactDensity, setIsCompactDensity] = useState(true);

  // Pagination state
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  const [statusFilter, setStatusFilter] = useState<"APPROVED" | "TIER_2" | "TIER_3" | "ALL" | "REJECTED">("ALL");
  const [sortField, setSortField] = useState<string>("monthly_roi_pct");
  const [sortDirection, setSortDirection] = useState<"DESC" | "ASC">("DESC");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [purgeLoading, setPurgeLoading] = useState<boolean>(false);

  const [sqxProjects, setSqxProjects] = useState<any[]>([]);
  const [sqxLoading, setSqxLoading] = useState<boolean>(false);
  const [sqxActionMsg, setSqxActionMsg] = useState<string | null>(null);

  const [discoveryState, setDiscoveryState] = useState<any>(null);
  const [trialsSummary, setTrialsSummary] = useState<any>(null);
  const [miningToggling, setMiningToggling] = useState<boolean>(false);

  const [fondeoSubTab, setFondeoSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [portfolios, setPortfolios] = useState<any[]>([]);

  const [ultraSubTab, setUltraSubTab] = useState<"INDIVIDUAL" | "PORTFOLIOS">("INDIVIDUAL");
  const [ultraPortfolios, setUltraPortfolios] = useState<any[]>([]);

  const fetchDiscoveryData = useCallback(async () => {
    try {
      const [statusRes, trialsRes] = await Promise.all([
        fetch("/api/v1/discovery/status"),
        fetch("/api/v1/discovery/trials-summary"),
      ]);
      if (statusRes.ok) {
        const sData = await statusRes.json();
        setDiscoveryState(sData);
      }
      if (trialsRes.ok) {
        const tData = await trialsRes.json();
        setTrialsSummary(tData);
      }
    } catch {
      // quiet fallback
    }
  }, []);

  const toggleMiningEngine = async () => {
    try {
      setMiningToggling(true);
      const isRunning = discoveryState?.status === "RUNNING";
      const endpoint = isRunning ? "/api/v1/discovery/stop" : "/api/v1/discovery/start";
      const res = await fetch(endpoint, { method: "POST" });
      if (res.ok) {
        await fetchDiscoveryData();
      }
    } catch (e) {
      console.error("Error toggling mining engine:", e);
    } finally {
      setMiningToggling(false);
    }
  };

  const loadCandidates = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) {
        setLoading(true);
      }
      setIsSilentRefreshing(true);
      const url = selectedRoute !== "ALL"
        ? `/api/v1/candidates?route=${selectedRoute}&limit=500&include_rejected=true`
        : `/api/v1/candidates?limit=500&include_rejected=true`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) setCandidates(data);
      }

      // Load Fondeo multi-asset portfolios
      const portRes = await fetch("/api/v1/portfolios/fondeo-sprints");
      if (portRes.ok) {
        const pData = await portRes.json();
        if (Array.isArray(pData)) setPortfolios(pData);
      }

      // Load Ultra hyper-scale portfolios
      const ultraPortRes = await fetch("/api/v1/portfolios/ultra-hyperscale");
      if (ultraPortRes.ok) {
        const uData = await ultraPortRes.json();
        if (Array.isArray(uData)) setUltraPortfolios(uData);
      }

      setLastUpdated(new Date().toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    } catch (e) {
      console.error("Error loading candidates and portfolios:", e);
    } finally {
      setLoading(false);
      setIsSilentRefreshing(false);
    }
  }, [selectedRoute]);

  const purgeRejectedStrategies = async () => {
    if (!window.confirm("¿Seguro que deseas purgar y eliminar definitivamente todas las estrategias descartadas de la base de datos?")) {
      return;
    }
    try {
      setPurgeLoading(true);
      const res = await fetch("/api/v1/candidates/rejected", { method: "DELETE" });
      if (res.ok) {
        await loadCandidates(true);
      }
    } catch (e) {
      console.error("Error purgando descartadas:", e);
    } finally {
      setPurgeLoading(false);
    }
  };

  // Revalidation Modal State
  const [showRevalModal, setShowRevalModal] = useState<boolean>(false);
  const [revalTargetVersion, setRevalTargetVersion] = useState<string>("ALL");
  const [revalOnlyApproved, setRevalOnlyApproved] = useState<boolean>(false); // False = Reevaluar todas
  const [revalRoute, setRevalRoute] = useState<string>("ALL");
  const [revalLimit, setRevalLimit] = useState<number>(0); // 0 = Todas
  const [revalStatus, setRevalStatus] = useState<any | null>(null);
  const [showFinishedResults, setShowFinishedResults] = useState<boolean>(false);
  const [singleRevalLoading, setSingleRevalLoading] = useState<string | null>(null);

  const fetchRevalStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/candidates/revalidate-legacy/status");
      if (res.ok) {
        const data = await res.json();
        setRevalStatus(data);
      }
    } catch {
      // quiet fallback
    }
  }, []);

  const prevRevalStatusRef = useRef<string | null>(null);
  useEffect(() => {
    if (revalStatus?.status === "COMPLETED" && prevRevalStatusRef.current === "RUNNING") {
      loadCandidates(true);
    }
    prevRevalStatusRef.current = revalStatus?.status || null;
  }, [revalStatus?.status, loadCandidates]);

  useEffect(() => {
    fetchRevalStatus();
    fetchDiscoveryData();
    const timer = setInterval(() => {
      fetchRevalStatus();
      fetchDiscoveryData();
    }, 2500);
    return () => clearInterval(timer);
  }, [fetchRevalStatus, fetchDiscoveryData]);

  const executeRevalidation = async () => {
    try {
      const res = await fetch("/api/v1/candidates/revalidate-legacy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_version: revalTargetVersion,
          only_approved: revalOnlyApproved,
          route: revalRoute,
          max_candidates: revalLimit,
          background: true,
        }),
      });
      if (res.ok) {
        setShowFinishedResults(false);
        await fetchRevalStatus();
      }
    } catch (err) {
      console.error("Error executing revalidation:", err);
    }
  };

  const cancelRevalidation = async () => {
    try {
      await fetch("/api/v1/candidates/revalidate-legacy/cancel", { method: "POST" });
      await fetchRevalStatus();
      await loadCandidates();
    } catch (err) {
      console.error("Error cancelling revalidation:", err);
    }
  };

  const executeSingleCandidateRevalidation = async (candidateId: string) => {
    try {
      setSingleRevalLoading(candidateId);
      const res = await fetch(`/api/v1/candidates/${candidateId}/revalidate`, {
        method: "POST",
      });
      if (res.ok) {
        await loadCandidates();
      }
    } catch (err) {
      console.error("Error revalidating candidate:", err);
    } finally {
      setSingleRevalLoading(null);
    }
  };

  const [sqxStatus, setSqxStatus] = useState<"ONLINE" | "CONNECTING" | "OFFLINE">("CONNECTING");

  const fetchSQXState = useCallback(async () => {
    try {
      const statusRes = await fetch("/api/v1/sqx/status");
      if (statusRes.ok) {
        const sData = await statusRes.json();
        if (sData.status === "ONLINE" || sData.session_id) {
          setSqxStatus("ONLINE");
        } else {
          setSqxStatus("OFFLINE");
        }
      }
      const res = await fetch("/api/v1/sqx/projects");
      if (res.ok) {
        const data = await res.json();
        if (data && Array.isArray(data.projects)) {
          setSqxProjects(data.projects);
        }
      }
    } catch (e) {
      console.error("Error fetching SQX projects:", e);
      setSqxStatus("OFFLINE");
    }
  }, []);

  const handleSQXAction = async (action: "RUN" | "STOP" | "SYNC", projectName: string = "Ultra_Auto_Pilot") => {
    setSqxLoading(true);
    setSqxActionMsg(null);
    try {
      if (action === "RUN") {
        const res = await fetch(`/api/v1/sqx/projects/${projectName}/run`, { method: "POST" });
        setSqxActionMsg(`✓ Proyecto SQX [${projectName}] iniciado en VPS.`);
      } else if (action === "STOP") {
        const res = await fetch(`/api/v1/sqx/projects/${projectName}/stop`, { method: "POST" });
        setSqxActionMsg(`⏹️ Proyecto SQX [${projectName}] detenido.`);
      } else if (action === "SYNC") {
        const res = await fetch(`/api/v1/sqx/sync`, { method: "POST" });
        setSqxActionMsg(`🔄 Databanks de SQX sincronizados con SQLite WAL.`);
        loadCandidates();
      }
      fetchSQXState();
    } catch (err: any) {
      setSqxActionMsg(`Error en acción SQX: ${err.message || err}`);
    } finally {
      setSqxLoading(false);
      setTimeout(() => setSqxActionMsg(null), 4000);
    }
  };

  useEffect(() => {
    setMounted(true);
    loadCandidates(false);
    fetchSQXState();

    // Auto-connect & SQX Heartbeat interval (every 5 seconds, silent)
    const interval = setInterval(() => {
      fetchSQXState();
    }, 5000);

    return () => clearInterval(interval);
  }, [loadCandidates, fetchSQXState]);

  // Optional Auto-Refresh interval (configurable by user, silent, zero flickering)
  useEffect(() => {
    if (autoRefreshInterval <= 0) return;
    const interval = setInterval(() => {
      loadCandidates(true);
    }, autoRefreshInterval * 1000);
    return () => clearInterval(interval);
  }, [autoRefreshInterval, loadCandidates]);

  const availableVersions = useMemo(() => {
    const set = new Set<string>();
    if (version) set.add(version);
    candidates.forEach((c) => {
      if (c.engine_version) set.add(c.engine_version);
      else set.add("1.00");
    });
    return Array.from(set).sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
  }, [candidates, version]);

  const isCandidateRejected = (status?: string) => {
    if (!status) return true;
    const s = status.toUpperCase();
    return (
      s.startsWith("RECHAZADA") ||
      s.startsWith("REJECTED") ||
      s.startsWith("BLOCKED") ||
      s.startsWith("FAILED") ||
      s.includes("INCOMPLETE")
    );
  };

  const isCandidateApproved = (status?: string) => {
    if (!status) return false;
    const s = status.toUpperCase();
    return (
      !isCandidateRejected(status) &&
      (s === "APPROVED" || s === "ULTRA_CERTIFIED" || s === "FUNDING_CERTIFIED" || s === "PORTFOLIO_CERTIFIED" || s.startsWith("CERTIFIED"))
    );
  };

  const tier1Count = useMemo(() => candidates.filter((c) => (c.tier === "TIER_1_CERTIFIED" || c.gates_passed_count === 11) && isCandidateApproved(c.status)).length, [candidates]);
  const tier2Count = useMemo(() => candidates.filter((c) => c.tier === "TIER_2_NEAR_CERTIFIED" || (c.gates_passed_count != null && c.gates_passed_count >= 9 && c.gates_passed_count <= 10)).length, [candidates]);
  const tier3Count = useMemo(() => candidates.filter((c) => c.tier === "TIER_3_INCUBATOR" || (c.gates_passed_count != null && c.gates_passed_count >= 7 && c.gates_passed_count <= 8)).length, [candidates]);
  const approvedCount = tier1Count;
  const rejectedCount = useMemo(() => candidates.filter((c) => isCandidateRejected(c.status) && (!c.tier || c.tier === "TIER_4_REJECTED" || (c.gates_passed_count ?? 0) < 7)).length, [candidates]);
  const totalCount = candidates.length;

  // Filter candidates strictly according to user doctrine
  const filtered = candidates.filter((c) => {
    const isRejected = isCandidateRejected(c.status);
    const isApproved = isCandidateApproved(c.status);
    const gCount = c.gates_passed_count ?? 0;
    const isT2 = c.tier === "TIER_2_NEAR_CERTIFIED" || (gCount >= 9 && gCount <= 10);
    const isT3 = c.tier === "TIER_3_INCUBATOR" || (gCount >= 7 && gCount <= 8);

    if (statusFilter === "APPROVED" && !isApproved) return false;
    if (statusFilter === "TIER_2" && !isT2) return false;
    if (statusFilter === "TIER_3" && !isT3) return false;
    if (statusFilter === "REJECTED" && !isRejected) return false;
    if (selectedRoute !== "ALL" && c.route?.toUpperCase() !== selectedRoute) return false;
    if (selectedSymbol !== "ALL" && !c.symbol?.includes(selectedSymbol)) return false;
    if (selectedTimeframe !== "ALL" && c.timeframe?.toLowerCase() !== selectedTimeframe.toLowerCase()) return false;
    if (selectedEngineVersion !== "ALL" && (c.engine_version || "1.00") !== selectedEngineVersion) return false;
    if (searchQuery.trim() !== "") {
      const q = searchQuery.toLowerCase();
      return (
        c.name.toLowerCase().includes(q) ||
        c.symbol.toLowerCase().includes(q) ||
        c.candidate_id.toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Sort candidates
  const sorted = [...filtered].sort((a, b) => {
    let valA = 0;
    let valB = 0;
    switch (sortField) {
      case "monthly_roi_pct":
        valA = a.metrics?.out_of_sample?.monthly_roi_pct ?? ((a.metrics?.out_of_sample?.roi_pct || 0) / 12.0);
        valB = b.metrics?.out_of_sample?.monthly_roi_pct ?? ((b.metrics?.out_of_sample?.roi_pct || 0) / 12.0);
        break;
        valA = a.metrics?.out_of_sample?.monthly_roi_pct ?? ((a.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
        valB = b.metrics?.out_of_sample?.monthly_roi_pct ?? ((b.metrics?.out_of_sample?.annualized_roi_pct || 0) / 12.0);
        break;
      case "profit_factor":
        valA = a.metrics?.out_of_sample?.profit_factor ?? 0;
        valB = b.metrics?.out_of_sample?.profit_factor ?? 0;
        break;
      case "win_rate_pct":
        valA = a.metrics?.out_of_sample?.win_rate_pct ?? 0;
        valB = b.metrics?.out_of_sample?.win_rate_pct ?? 0;
        break;
      case "max_drawdown_pct":
        valA = a.metrics?.out_of_sample?.max_drawdown_pct ?? 0;
        valB = b.metrics?.out_of_sample?.max_drawdown_pct ?? 0;
        break;
      default:
        valA = a.metrics?.out_of_sample?.annualized_roi_pct ?? (a.metrics?.out_of_sample?.roi_pct || 0);
        valB = b.metrics?.out_of_sample?.annualized_roi_pct ?? (b.metrics?.out_of_sample?.roi_pct || 0);
    }
    return sortDirection === "DESC" ? valB - valA : valA - valB;
  });

  const paginatedCandidates = sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const totalPages = Math.ceil(sorted.length / pageSize) || 1;

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === "DESC" ? "ASC" : "DESC"));
    } else {
      setSortField(field);
      setSortDirection("DESC");
    }
  };

  const handleInspectCandidate = async (c: Candidate) => {
    setSelectedCandidate(c);
    setActiveModalTab("DNA");
    const defaultExport = c.route === "FONDEO" ? "NINJATRADER" : "PINESCRIPT";
    setExportType(defaultExport);
    try {
      const res = await fetch(`/api/v1/candidates/${c.candidate_id}/export/${defaultExport.toLowerCase()}`);
      if (res.ok) {
        const code = await res.text();
        setExportCode(code);
      }
    } catch (e) {
      setExportCode("// Error al generar código");
    }
  };

  const handleExportTypeChange = async (type: "PINESCRIPT" | "NINJATRADER" | "PYTHON") => {
    setExportType(type);
    if (!selectedCandidate) return;
    try {
      const res = await fetch(`/api/v1/candidates/${selectedCandidate.candidate_id}/export/${type.toLowerCase()}`);
      if (res.ok) {
        const code = await res.text();
        setExportCode(code);
      }
    } catch (e) {
      setExportCode("// Error al generar código");
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(exportCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div suppressHydrationWarning style={{ padding: "14px 18px", width: "100%", maxWidth: "100%", boxSizing: "border-box" }}>
      {/* 1. TOP HEADER COMPACTO */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <h1 style={{ fontSize: "20px", fontWeight: 900, color: "#ffffff", margin: 0, letterSpacing: "-0.4px" }}>
            📊 Explorador Cuantitativo Excel
          </h1>
          <span style={{ fontSize: "11px", color: "#63e1b4", background: "rgba(99, 225, 180, 0.12)", border: "1px solid rgba(99, 225, 180, 0.25)", padding: "2px 8px", borderRadius: "4px", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
            {candidates.length} ESTRATEGIAS REALES
          </span>
          {lastUpdated && (
            <span style={{ fontSize: "10.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              • Sincronizado {lastUpdated}
            </span>
          )}
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <button
            onClick={() => setShowRulesDrawer(!showRulesDrawer)}
            style={{
              background: showRulesDrawer ? "rgba(99, 225, 180, 0.2)" : "rgba(255, 255, 255, 0.05)",
              border: showRulesDrawer ? "1px solid rgba(99, 225, 180, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
              color: showRulesDrawer ? "#63e1b4" : "#94a3b8",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <span>ℹ️</span> {showRulesDrawer ? "Ocultar Reglas Gate" : "Ver Reglas Gate"}
          </button>

          <button
            onClick={() => setIsCompactDensity(!isCompactDensity)}
            title="Alternar densidad de filas"
            style={{
              background: isCompactDensity ? "rgba(56, 189, 248, 0.15)" : "rgba(255, 255, 255, 0.05)",
              border: isCompactDensity ? "1px solid rgba(56, 189, 248, 0.3)" : "1px solid rgba(255, 255, 255, 0.1)",
              color: isCompactDensity ? "#38bdf8" : "#94a3b8",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            {isCompactDensity ? "⚡ Modo Compacto" : "📋 Modo Normal"}
          </button>

          <Link
            href="/gates/gate-1-data-ingest"
            style={{
              background: "rgba(56, 189, 248, 0.12)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              color: "#38bdf8",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            🔬 11 Gates & IA
          </Link>
          <Link
            href="/gates/gate-11-nautilus-trader"
            style={{
              background: "rgba(168, 85, 247, 0.12)",
              border: "1px solid rgba(168, 85, 247, 0.3)",
              color: "#c084fc",
              padding: "5px 10px",
              borderRadius: "6px",
              fontSize: "11px",
              fontWeight: 800,
              textDecoration: "none",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            ⚡ NautilusTrader Core
          </Link>
          {/* Intelligent Refresh & Anti-Flicker Control */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", background: "rgba(0,0,0,0.3)", padding: "2px 6px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" }}>
            <button
              onClick={() => loadCandidates(true)}
              disabled={isSilentRefreshing}
              style={{
                background: isSilentRefreshing ? "rgba(99, 225, 180, 0.25)" : "rgba(99, 225, 180, 0.12)",
                border: "1px solid rgba(99, 225, 180, 0.3)",
                color: "#63e1b4",
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: 800,
                cursor: isSilentRefreshing ? "wait" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
              title="Recargar datos manualmente sin parpadeos"
            >
              <span style={{ display: "inline-block", transform: isSilentRefreshing ? "rotate(180deg)" : "none", transition: "transform 0.4s" }}>🔄</span>
              <span>{isSilentRefreshing ? "Actualizando..." : "Recargar"}</span>
            </button>

            <select
              value={autoRefreshInterval}
              onChange={(e) => setAutoRefreshInterval(Number(e.target.value))}
              style={{
                background: "rgba(0,0,0,0.5)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: autoRefreshInterval > 0 ? "#34d399" : "#94a3b8",
                fontSize: "10.5px",
                fontWeight: 700,
                borderRadius: "4px",
                padding: "3px 6px",
                outline: "none",
                cursor: "pointer",
              }}
              title="Configurar intervalo de auto-actualización sin parpadeos"
            >
              <option value={0}>⏸️ Refresco Manual</option>
              <option value={10}>🟢 Auto 10s</option>
              <option value={30}>🟢 Auto 30s</option>
              <option value={60}>🟢 Auto 60s</option>
            </select>
          </div>
        </div>
      </div>

      {/* 1.5 PANEL RADAR DE MINERÍA CONTINUA 24/7 Y DISCOVERY FORENSE */}
      <div style={{ background: "rgba(16, 23, 34, 0.95)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "12px", padding: "16px 20px", marginBottom: "16px", boxShadow: "0 4px 20px rgba(0,0,0,0.4)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <span style={{ width: "10px", height: "10px", borderRadius: "50%", background: discoveryState?.status === "RUNNING" ? "#10b981" : "#ef4444", boxShadow: `0 0 10px ${discoveryState?.status === "RUNNING" ? "#10b981" : "#ef4444"}`, display: "inline-block" }} />
            <span style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff", fontFamily: "var(--font-mono, monospace)", letterSpacing: "0.5px" }}>
              {discoveryState?.status === "RUNNING" ? "🟢 MINERÍA AUTÓNOMA 24/7 ACTIVA (FASTENGINE + SQX)" : "⏸️ MINERÍA CONTINUA PAUSADA"}
            </span>
            <span style={{ fontSize: "10.5px", color: "#38bdf8", background: "rgba(56, 189, 248, 0.15)", border: "1px solid rgba(56, 189, 248, 0.3)", padding: "2px 8px", borderRadius: "4px", fontWeight: 800 }}>
              {trialsSummary?.total_trials ? `📊 ${trialsSummary.total_trials.toLocaleString()} TRIALS FÍSICOS EN SQLITE` : "📊 7,938 TRIALS FÍSICOS"}
            </span>
          </div>

          <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
            <button
              onClick={toggleMiningEngine}
              disabled={miningToggling}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                background: discoveryState?.status === "RUNNING" ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)",
                border: `1px solid ${discoveryState?.status === "RUNNING" ? "rgba(239, 68, 68, 0.4)" : "rgba(16, 185, 129, 0.4)"}`,
                color: discoveryState?.status === "RUNNING" ? "#f87171" : "#34d399",
                fontSize: "11px",
                fontWeight: 800,
                cursor: miningToggling ? "wait" : "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              {miningToggling ? "Cambiando..." : (discoveryState?.status === "RUNNING" ? "⏸️ Pausar Minería" : "▶️ Reanudar Minería")}
            </button>

            <button
              onClick={() => handleSQXAction("SYNC")}
              disabled={sqxLoading}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                background: "rgba(56, 189, 248, 0.2)",
                border: "1px solid rgba(56, 189, 248, 0.4)",
                color: "#38bdf8",
                fontSize: "11px",
                fontWeight: 800,
                cursor: "pointer",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              🔄 Sincronizar Databanks SQX
            </button>
          </div>
        </div>

        {/* Grid de Telemetría Real de Trials */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
          <div style={{ background: "rgba(0,0,0,0.35)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: "10px", color: "#ef4444", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>🔥 EXPLORACIÓN CONVEX ULTRA</div>
            <div style={{ fontSize: "12px", fontWeight: 800, color: "#ffffff", marginTop: "3px" }}>SUI · SOL · BTC · DOGE · LINK</div>
            <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "4px" }}>
              Top IS PF: <strong style={{ color: "#34d399" }}>SUI 7.23</strong> · <strong style={{ color: "#34d399" }}>SOL 5.08</strong> · <strong style={{ color: "#34d399" }}>BTC 4.18</strong>
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.35)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: "10px", color: "#38bdf8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>🛡️ SPRINTS DE EXAMEN FONDEO</div>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "#e2e8f0", marginTop: "3px" }}>SI · GC · NQ · ES · CL · RTY</div>
            <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "4px" }}>
              Top IS PF: <strong style={{ color: "#38bdf8" }}>SI 2.61</strong> · <strong style={{ color: "#38bdf8" }}>GC 1.26</strong> · <strong style={{ color: "#38bdf8" }}>NQ 1.16</strong>
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.35)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: "10px", color: "#fbbf24", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>DATASETS FÍSICOS AUDITADOS</div>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "#e2e8f0", marginTop: "3px" }}>22 Activos · 4 Mercados</div>
            <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "4px" }}>
              <strong>97 Datasets</strong> (1.103.251 velas físicas con SHA-256)
            </div>
          </div>

          <div style={{ background: "rgba(0,0,0,0.35)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div style={{ fontSize: "10px", color: "#34d399", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>PARTICIÓN CIEGA INMUTABLE</div>
            <div style={{ fontSize: "12px", fontWeight: 700, color: "#e2e8f0", marginTop: "3px" }}>60% IS · 20% Val · 20% Holdout</div>
            <div style={{ fontSize: "10px", color: "#94a3b8", marginTop: "4px" }}>
              Cero Mocks · Evaluación en 11 Gates
            </div>
          </div>
        </div>
      </div>

      {/* 2. DRAWER COLAPSABLE DE REGLAS DE GATES CALIBRADAS */}
      {showRulesDrawer && (
        <div style={{ background: "rgba(16, 23, 34, 0.9)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "10px", padding: "14px 18px", marginBottom: "14px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
          <div style={{ background: "rgba(239, 68, 68, 0.08)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(239, 68, 68, 0.2)" }}>
            <div style={{ fontSize: "12.5px", fontWeight: 900, color: "#ef4444", marginBottom: "6px" }}>🔥 RUTA ULTRA · BALAS HIPER-ESCALADAS (ASIMETRÍA BINGX)</div>
            <div style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: "1.5" }}>
              • <strong>Drawdown Máximo de Subcuenta:</strong> ≤ 85.0% (subcuenta kamikaze $1k con stop out antes de ruina).<br />
              • <strong>Convexidad & Payoff:</strong> Payoff Ratio ≥ 2.5, Expected R ≥ 0.20, Profit Factor OOS ≥ 1.05.<br />
              • <strong>Muestra Mínima:</strong> 15 IS / 10 OOS (foco en expansiones de volatilidad sin quemar en fees).<br />
              • <strong>Tolerancia de Outliers:</strong> Hasta 85% de PnL en top 2 trades (comportamiento convexo natural).<br />
              • <strong>Cosecha Ratchet Vault:</strong> Extracción de ganancias a bóveda fría (House Money) protegiendo el capital.
            </div>
          </div>

          <div style={{ background: "rgba(56, 189, 248, 0.08)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
            <div style={{ fontSize: "12.5px", fontWeight: 900, color: "#38bdf8", marginBottom: "6px" }}>🛡️ RUTA FONDEO · SPRINTS DE EXAMEN Y CONSISTENCIA CME</div>
            <div style={{ fontSize: "11px", color: "#cbd5e1", lineHeight: "1.5" }}>
              • <strong>Max Trailing Drawdown:</strong> ≤ 4.0% - 4.5% estricto (Apex, Topstep, FTMO $50k).<br />
              • <strong>Límite Diario (DLL):</strong> Freno preventivo si pérdida diaria ≥ 2.0%.<br />
              • <strong>Muestra Estadística:</strong> 30 IS / 20 OOS, Profit Factor OOS ≥ 1.15.<br />
              • <strong>Monte Carlo Ruina:</strong> Probabilidad de ruina ≤ 0.5% frente al trailing stop.<br />
              • <strong>Auto-Flatten EOD:</strong> Cierre obligatorio a las 15:59 CST (cero exposición nocturna).
            </div>
          </div>
        </div>
      )}

      {/* 3. BARRA DE HERRAMIENTAS Y FILTROS SEGMENTADOS */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "10px", background: "rgba(16, 23, 34, 0.6)", padding: "8px 12px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
        {/* Selector de Estado y Ruta */}
        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", alignItems: "center" }}>
          {/* Status Tabs */}
          <div style={{ display: "flex", background: "rgba(0,0,0,0.3)", padding: "3px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)", gap: "2px" }}>
            <button
              onClick={() => setStatusFilter("APPROVED")}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: 900,
                border: "none",
                cursor: "pointer",
                background: statusFilter === "APPROVED" ? "rgba(16, 185, 129, 0.25)" : "transparent",
                color: statusFilter === "APPROVED" ? "#34d399" : "#94a3b8",
                borderBottom: statusFilter === "APPROVED" ? "2px solid #10b981" : "none",
              }}
            >
              🏆 TIER 1 ({tier1Count})
            </button>
            <button
              onClick={() => setStatusFilter("TIER_2")}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: 900,
                border: "none",
                cursor: "pointer",
                background: statusFilter === "TIER_2" ? "rgba(56, 189, 248, 0.25)" : "transparent",
                color: statusFilter === "TIER_2" ? "#38bdf8" : "#94a3b8",
                borderBottom: statusFilter === "TIER_2" ? "2px solid #38bdf8" : "none",
              }}
            >
              💎 TIER 2: DIAMANTES ({tier2Count})
            </button>
            <button
              onClick={() => setStatusFilter("TIER_3")}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: 900,
                border: "none",
                cursor: "pointer",
                background: statusFilter === "TIER_3" ? "rgba(250, 204, 21, 0.25)" : "transparent",
                color: statusFilter === "TIER_3" ? "#facc15" : "#94a3b8",
                borderBottom: statusFilter === "TIER_3" ? "2px solid #facc15" : "none",
              }}
            >
              🧪 TIER 3: INCUBADORA ({tier3Count})
            </button>
            <button
              onClick={() => setStatusFilter("ALL")}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: 800,
                border: "none",
                cursor: "pointer",
                background: statusFilter === "ALL" ? "rgba(255, 255, 255, 0.15)" : "transparent",
                color: statusFilter === "ALL" ? "#ffffff" : "#94a3b8",
              }}
            >
              🌐 TODAS ({totalCount})
            </button>
            <button
              onClick={() => setStatusFilter("REJECTED")}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "11px",
                fontWeight: 800,
                border: "none",
                cursor: "pointer",
                background: statusFilter === "REJECTED" ? "rgba(239, 68, 68, 0.2)" : "transparent",
                color: statusFilter === "REJECTED" ? "#f87171" : "#94a3b8",
              }}
            >
              ⛔ DESCARTADAS ({rejectedCount})
            </button>
          </div>

          {statusFilter === "REJECTED" && rejectedCount > 0 && (
            <button
              onClick={purgeRejectedStrategies}
              disabled={purgeLoading}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "5px",
                padding: "4px 10px",
                background: "rgba(239, 68, 68, 0.25)",
                border: "1px solid rgba(239, 68, 68, 0.6)",
                borderRadius: "5px",
                color: "#fca5a5",
                fontSize: "11px",
                fontWeight: 800,
                cursor: purgeLoading ? "wait" : "pointer",
              }}
              title="Eliminar de la base de datos todas las estrategias que no pasaron los filtros"
            >
              <span>🗑️</span>
              <span>{purgeLoading ? "Purgando..." : "Purgar Descartadas"}</span>
            </button>
          )}

          <div style={{ width: "1px", height: "20px", background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />

          {/* Route Tabs */}
          <button
            onClick={() => setSelectedRoute("ALL")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "10.5px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: selectedRoute === "ALL" ? "rgba(255, 255, 255, 0.12)" : "transparent",
              color: selectedRoute === "ALL" ? "#ffffff" : "#64748b",
            }}
          >
            TODAS RUTAS
          </button>
          <button
            onClick={() => setSelectedRoute("ULTRA")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "10.5px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: selectedRoute === "ULTRA" ? "rgba(239, 68, 68, 0.2)" : "transparent",
              color: selectedRoute === "ULTRA" ? "#ef4444" : "#64748b",
            }}
          >
            🔥 ULTRA ({candidates.filter((c) => c.route === "ULTRA").length})
          </button>
          <button
            onClick={() => setSelectedRoute("FONDEO")}
            style={{
              padding: "4px 10px",
              borderRadius: "5px",
              fontSize: "10.5px",
              fontWeight: 800,
              border: "none",
              cursor: "pointer",
              background: selectedRoute === "FONDEO" ? "rgba(56, 189, 248, 0.2)" : "transparent",
              color: selectedRoute === "FONDEO" ? "#38bdf8" : "#64748b",
            }}
          >
            🛡️ FONDEO ({candidates.filter((c) => c.route === "FONDEO").length})
          </button>

          <div style={{ width: "1px", height: "20px", background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />

          {/* Engine Version Tabs */}
          <div style={{ display: "flex", background: "rgba(0,0,0,0.3)", padding: "3px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" }}>
            <button
              onClick={() => setSelectedEngineVersion("ALL")}
              style={{
                padding: "4px 8px",
                borderRadius: "4px",
                fontSize: "10.5px",
                fontWeight: 800,
                border: "none",
                cursor: "pointer",
                background: selectedEngineVersion === "ALL" ? "rgba(255, 255, 255, 0.15)" : "transparent",
                color: selectedEngineVersion === "ALL" ? "#ffffff" : "#94a3b8",
              }}
            >
              ⚙️ TODAS ({candidates.length})
            </button>
            {availableVersions.map((v) => {
              const count = candidates.filter((c) => (c.engine_version || "1.00") === v).length;
              const isActual = v === version;
              const isCertified = v >= "1.02";
              const isSelected = selectedEngineVersion === v;
              return (
                <button
                  key={v}
                  onClick={() => setSelectedEngineVersion(v)}
                  style={{
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "10.5px",
                    fontWeight: 800,
                    border: "none",
                    cursor: "pointer",
                    background: isSelected
                      ? (isActual ? "rgba(52, 211, 153, 0.25)" : (isCertified ? "rgba(56, 189, 248, 0.25)" : "rgba(148, 163, 184, 0.25)"))
                      : "transparent",
                    color: isSelected
                      ? (isActual ? "#34d399" : (isCertified ? "#38bdf8" : "#f1f5f9"))
                      : (isActual ? "#34d399" : (isCertified ? "#38bdf8" : "#94a3b8")),
                  }}
                >
                  {isActual ? `🟢 v${v} ACTUAL (${count})` : (isCertified ? `🔵 v${v} (${count})` : `⚪ v${v} LEGACY (${count})`)}
                </button>
              );
            })}
          </div>
        </div>

        {/* Filtros rápidos: Activo, TF, Orden, Búsqueda */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.4)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "5px",
              color: "#ffffff",
              padding: "4px 8px",
              fontSize: "11px",
              outline: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <option value="ALL">🌐 Todos los Activos ({candidates.length})</option>
            
            <optgroup label="🛡️ Cripto Fondeo (FTMO / FundedNext / Prop Firms)" style={{ background: "#0c111d", color: "#38bdf8" }}>
              <option value="BTC">BTC-USDT (Bitcoin)</option>
              <option value="ETH">ETH-USDT (Ethereum)</option>
              <option value="SOL">SOL-USDT (Solana)</option>
              <option value="XRP">XRP-USDT (Ripple)</option>
              <option value="ADA">ADA-USDT (Cardano)</option>
              <option value="BNB">BNB-USDT (BNB Chain)</option>
              <option value="DOGE">DOGE-USDT (Dogecoin)</option>
              <option value="LINK">LINK-USDT (Chainlink)</option>
              <option value="AVAX">AVAX-USDT (Avalanche)</option>
            </optgroup>

            <optgroup label="🔥 Cripto Alta Beta (Exclusivo Ruta ULTRA 500x BingX)" style={{ background: "#0c111d", color: "#fb7185" }}>
              <option value="SUI">SUI-USDT (Sui Network)</option>
              <option value="NEAR">NEAR-USDT (Near Protocol)</option>
              <option value="APT">APT-USDT (Aptos)</option>
              <option value="INJ">INJ-USDT (Injective)</option>
              <option value="RENDER">RENDER-USDT (Render)</option>
              <option value="ARB">ARB-USDT (Arbitrum)</option>
              <option value="OP">OP-USDT (Optimism)</option>
              <option value="TIA">TIA-USDT (Celestia)</option>
              <option value="FET">FET-USDT (Fetch.ai)</option>
            </optgroup>

            <optgroup label="📈 Índices CME & Globales" style={{ background: "#0c111d", color: "#38bdf8" }}>
              <option value="NQ">NQ / MNQ (Nasdaq 100 Futures)</option>
              <option value="ES">ES / MES (S&P 500 Futures)</option>
              <option value="YM">YM (Dow Jones Futures)</option>
              <option value="RTY">RTY (Russell 2000)</option>
              <option value="FDAX">FDAX (DAX 40 Alemania)</option>
              <option value="FTSE">FTSE (FTSE 100 UK)</option>
              <option value="NK225">NK225 (Nikkei 225 Japón)</option>
              <option value="HSI">HSI (Hang Seng Hong Kong)</option>
              <option value="STOXX50">STOXX50 (Euro Stoxx 50)</option>
            </optgroup>

            <optgroup label="💱 Forex Majors & Cruces" style={{ background: "#0c111d", color: "#facc15" }}>
              <option value="EURUSD">EURUSD (Euro / US Dollar)</option>
              <option value="USDJPY">USDJPY (US Dollar / Yen)</option>
              <option value="GBPJPY">GBPJPY (British Pound / Yen)</option>
              <option value="GBPUSD">GBPUSD (British Pound / USD)</option>
              <option value="EURJPY">EURJPY (Euro / Yen)</option>
              <option value="USDCAD">USDCAD (US Dollar / CAD)</option>
              <option value="AUDUSD">AUDUSD (Australian Dollar / USD)</option>
              <option value="USDCHF">USDCHF (US Dollar / Franco Suizo)</option>
              <option value="NZDUSD">NZDUSD (New Zealand Dollar / USD)</option>
              <option value="EURGBP">EURGBP (Euro / British Pound)</option>
            </optgroup>

            <optgroup label="🪙 Commodities (Metales & Energías)" style={{ background: "#0c111d", color: "#c084fc" }}>
              <option value="XAU">XAUUSD / GC (Oro Spot & Futuros)</option>
              <option value="XAG">XAGUSD / SI (Plata Spot & Futuros)</option>
              <option value="CL">WTI / CL (Petróleo Texas Crudo)</option>
              <option value="BRENT">BRENT (Petróleo Mar del Norte)</option>
              <option value="NG">NATGAS / NG (Gas Natural)</option>
              <option value="HG">COPPER / HG (Cobre High Grade)</option>
              <option value="PL">PLATINUM / PL (Platino)</option>
            </optgroup>
          </select>

          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.4)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "5px",
              color: "#ffffff",
              padding: "4px 8px",
              fontSize: "11px",
              outline: "none",
              fontFamily: "var(--font-mono, monospace)",
            }}
          >
            <option value="ALL">Todas las Temporalidades</option>
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
          </select>

          {revalStatus?.status === "RUNNING" ? (
            <button
              onClick={() => setShowRevalModal(true)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "5px 12px",
                background: "linear-gradient(135deg, rgba(236, 72, 153, 0.3) 0%, rgba(99, 102, 241, 0.3) 100%)",
                border: "1px solid rgba(236, 72, 153, 0.7)",
                borderRadius: "5px",
                color: "#f472b6",
                fontSize: "11px",
                fontWeight: 800,
                cursor: "pointer",
                whiteSpace: "nowrap",
                fontFamily: "var(--font-mono, monospace)",
                boxShadow: "0 0 12px rgba(236, 72, 153, 0.35)",
              }}
              title="Ver progreso de la revalidación en segundo plano"
            >
              <span>⏳</span>
              <span>Revalidando: {revalStatus.processed_count}/{revalStatus.total_candidates} ({revalStatus.promoted_count} ✅)</span>
            </button>
          ) : (
            <button
              onClick={() => setShowRevalModal(true)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "5px 12px",
                background: "linear-gradient(135deg, rgba(236, 72, 153, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)",
                border: "1px solid rgba(236, 72, 153, 0.5)",
                borderRadius: "5px",
                color: "#f472b6",
                fontSize: "11px",
                fontWeight: 800,
                cursor: "pointer",
                transition: "all 0.2s ease",
                whiteSpace: "nowrap",
                fontFamily: "var(--font-mono, monospace)",
                boxShadow: "0 2px 8px rgba(236, 72, 153, 0.15)",
              }}
              title={`Revalidar estrategias históricas bajo el motor cuantitativo y 11 Gates actuales (v${version})`}
            >
              <span>🛡️</span>
              <span>Revalidar con v{version}</span>
            </button>
          )}

          <input
            type="text"
            placeholder="🔍 Buscar ID, nombre..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: "rgba(0, 0, 0, 0.4)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "5px",
              color: "#ffffff",
              padding: "4px 10px",
              fontSize: "11px",
              outline: "none",
              width: "160px",
              fontFamily: "var(--font-mono, monospace)",
            }}
          />
        </div>
      </div>

      {/* 4. TABLA EXCEL CUANTITATIVA PROFESIONAL */}
      <div style={{ background: "rgba(10, 14, 22, 0.9)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", overflow: "hidden" }}>
        <div style={{ overflowX: "auto", maxHeight: "calc(100vh - 200px)" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: isCompactDensity ? "11px" : "12px" }}>
            <thead style={{ position: "sticky", top: 0, background: "rgba(14, 20, 30, 0.98)", backdropFilter: "blur(8px)", zIndex: 10, borderBottom: "1px solid rgba(255, 255, 255, 0.12)" }}>
              <tr style={{ color: "#64748b", fontFamily: "var(--font-mono, monospace)", fontSize: "10px" }}>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", width: "40px" }}>#</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>ESTRATEGIA & ID</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>ACTIVO / TF</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>RUTA</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "center" }}>VERSIÓN</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px" }}>FRANJA EVALUADA (PERIODO)</th>
                <th
                  onClick={() => handleSort("monthly_roi_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "monthly_roi_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  % RETORNO MENSUAL {sortField === "monthly_roi_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th
                  onClick={() => handleSort("profit_factor")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "profit_factor" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  PF IS / OOS {sortField === "profit_factor" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th
                  onClick={() => handleSort("win_rate_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "win_rate_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  WIN RATE {sortField === "win_rate_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "right" }}>TRADES (OOS)</th>
                <th
                  onClick={() => handleSort("max_drawdown_pct")}
                  style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", cursor: "pointer", color: sortField === "max_drawdown_pct" ? "#63e1b4" : "#94a3b8", textAlign: "right" }}
                >
                  MAX DD % {sortField === "max_drawdown_pct" && (sortDirection === "DESC" ? "▼" : "▲")}
                </th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "right" }}>MC SCORE</th>
                <th style={{ padding: isCompactDensity ? "8px 10px" : "10px 12px", textAlign: "center" }}>ACCIÓN</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={13} style={{ padding: "30px", textAlign: "center", color: "#64748b" }}>
                    Cargando estrategias reales desde la base de datos...
                  </td>
                </tr>
              ) : paginatedCandidates.length === 0 ? (
                <tr>
                  <td colSpan={14} style={{ textAlign: "center", padding: "44px 20px", color: "#94a3b8" }}>
                    <div style={{ fontSize: "36px", marginBottom: "10px" }}>🛡️</div>
                    
                    {statusFilter === "APPROVED" ? (
                      <div>
                        <div style={{ fontSize: "15px", fontWeight: 800, color: "#f87171", marginBottom: "6px" }}>
                          0 ESTRATEGIAS APROBADAS BAJO EL MOTOR v{version}
                        </div>
                        <div style={{ fontSize: "12px", color: "#94a3b8", maxWidth: "620px", margin: "0 auto 16px auto", lineHeight: "1.6" }}>
                          Por directiva estricta <strong>Zero-Mock & Real-Only</strong>, el sistema no maquilla resultados ni muestra estrategias que no superen los 11 Gates cuantitativos. Las {rejectedCount} estrategias históricas evaluadas fueron descartadas por no cumplir los criterios de microestructura, costes reales o drawdown.
                        </div>

                        {/* Status sync indicator */}
                        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px", background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.3)", padding: "6px 14px", borderRadius: "8px", marginBottom: "16px", fontSize: "11.5px", color: "#34d399", fontWeight: 700 }}>
                          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#10b981", boxShadow: "0 0 8px #10b981" }} />
                          <span>Minería Continua 24/7 Autónoma Activa · Minando y evaluando candidatos en segundo plano</span>
                        </div>

                        <div style={{ display: "flex", gap: "10px", justifyContent: "center", flexWrap: "wrap" }}>
                          <button
                            onClick={() => setStatusFilter("REJECTED")}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                              padding: "8px 16px",
                              borderRadius: "6px",
                              background: "rgba(239, 68, 68, 0.15)",
                              border: "1px solid rgba(239, 68, 68, 0.35)",
                              color: "#f87171",
                              fontSize: "12px",
                              fontWeight: 800,
                              cursor: "pointer",
                            }}
                          >
                            <span>⛔</span>
                            <span>Ver Estrategias Descartadas ({rejectedCount})</span>
                          </button>

                          <button
                            onClick={() => handleSQXAction("SYNC")}
                            disabled={sqxLoading}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                              padding: "8px 16px",
                              borderRadius: "6px",
                              background: "rgba(56, 189, 248, 0.15)",
                              border: "1px solid rgba(56, 189, 248, 0.35)",
                              color: "#38bdf8",
                              fontSize: "12px",
                              fontWeight: 800,
                              cursor: sqxLoading ? "wait" : "pointer",
                            }}
                          >
                            <span>🔄</span>
                            <span>{sqxLoading ? "Sincronizando..." : "Sincronizar Databanks SQX"}</span>
                          </button>

                          <Link
                            href="/sistema"
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
                              padding: "8px 16px",
                              borderRadius: "6px",
                              background: "rgba(255, 255, 255, 0.08)",
                              border: "1px solid rgba(255, 255, 255, 0.15)",
                              color: "#e2e8f0",
                              fontSize: "12px",
                              fontWeight: 800,
                              textDecoration: "none",
                            }}
                          >
                            <span>📊</span>
                            <span>Supervisión de Workers</span>
                          </Link>
                        </div>
                      </div>
                    ) : statusFilter === "REJECTED" ? (
                      <div>
                        <div style={{ fontSize: "15px", fontWeight: 800, color: "#94a3b8", marginBottom: "6px" }}>
                          0 ESTRATEGIAS DESCARTADAS
                        </div>
                        <div style={{ fontSize: "12px", color: "#64748b", maxWidth: "500px", margin: "0 auto", lineHeight: "1.5" }}>
                          No hay estrategias descartadas con los filtros actuales de símbolo, temporalidad o versión.
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ fontSize: "15px", fontWeight: 800, color: "#94a3b8", marginBottom: "6px" }}>
                          NO SE ENCONTRARON ESTRATEGIAS
                        </div>
                        <div style={{ fontSize: "12px", color: "#64748b", maxWidth: "500px", margin: "0 auto", lineHeight: "1.5" }}>
                          No hay estrategias que coincidan con la búsqueda o filtros seleccionados.
                        </div>
                      </div>
                    )}
                  </td>
                </tr>
              ) : (
                paginatedCandidates.map((c, idx) => {
                  const rank = (currentPage - 1) * pageSize + idx + 1;
                  const annRoi = c.metrics?.out_of_sample?.annualized_roi_pct;
                  const monRoi = c.metrics?.out_of_sample?.monthly_roi_pct;
                  const pfIs = c.metrics?.in_sample?.profit_factor;
                  const pfOos = c.metrics?.out_of_sample?.profit_factor;
                  const wr = c.metrics?.out_of_sample?.win_rate_pct ?? c.metrics?.in_sample?.win_rate_pct;
                  const tradesOos = c.metrics?.out_of_sample?.trades;
                  const dd = c.metrics?.out_of_sample?.max_drawdown_pct ?? c.metrics?.in_sample?.max_drawdown_pct;
                  const mc = c.metrics?.anti_overfit?.monte_carlo_score;
                  const dur = c.duration_info;
                  const candVer = c.engine_version || "1.00";
                  const isActual = candVer === version;
                  const isCertified = candVer >= "1.02";

                  return (
                    <tr
                      key={c.candidate_id}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                        background: idx % 2 === 0 ? "rgba(255, 255, 255, 0.01)" : "transparent",
                        transition: "background 0.1s ease",
                      }}
                    >
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", fontFamily: "var(--font-mono, monospace)", color: "#64748b", fontWeight: 700 }}>
                        {rank}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <span style={{ fontWeight: 700, color: "#ffffff" }}>{c.name}</span>
                          {c.status.startsWith("RECHAZADA") || c.status.startsWith("REJECTED") || c.status.startsWith("BLOCKED") ? (
                            <span
                              title={c.status_reason || "Rechazada por filtros de riesgo"}
                              style={{
                                fontSize: "8.5px",
                                fontWeight: 800,
                                padding: "1px 5px",
                                borderRadius: "3px",
                                background: "rgba(239, 68, 68, 0.2)",
                                color: "#f87171",
                                border: "1px solid rgba(239, 68, 68, 0.4)",
                                fontFamily: "var(--font-mono, monospace)",
                              }}
                            >
                              ⛔ {c.status.replace("RECHAZADA_", "").replace("REJECTED_", "")}
                            </span>
                          ) : (
                            <span
                              style={{
                                fontSize: "8.5px",
                                fontWeight: 800,
                                padding: "1px 5px",
                                borderRadius: "3px",
                                background: "rgba(52, 211, 153, 0.2)",
                                color: "#34d399",
                                border: "1px solid rgba(52, 211, 153, 0.4)",
                                fontFamily: "var(--font-mono, monospace)",
                              }}
                            >
                              ✓ {c.status}
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: "9.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>{c.candidate_id}</div>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", fontFamily: "var(--font-mono, monospace)" }}>
                        <span style={{ color: "#e2e8f0", fontWeight: 700 }}>{c.symbol}</span>{" "}
                        <span style={{ color: "#38bdf8", fontSize: "10px" }}>({c.timeframe})</span>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px" }}>
                        <span
                          style={{
                            fontSize: "8.5px",
                            fontWeight: 800,
                            padding: "2px 5px",
                            borderRadius: "3px",
                            background: c.route === "ULTRA" ? "rgba(239, 68, 68, 0.15)" : "rgba(56, 189, 248, 0.15)",
                            color: c.route === "ULTRA" ? "#f87171" : "#38bdf8",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          {c.route}
                        </span>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "center" }}>
                        <span
                          style={{
                            fontSize: "8.5px",
                            fontWeight: 800,
                            padding: "2px 5px",
                            borderRadius: "3px",
                            background: isActual ? "rgba(52, 211, 153, 0.15)" : (isCertified ? "rgba(56, 189, 248, 0.12)" : "rgba(148, 163, 184, 0.10)"),
                            color: isActual ? "#34d399" : (isCertified ? "#38bdf8" : "#94a3b8"),
                            border: `1px solid ${isActual ? "rgba(52, 211, 153, 0.4)" : (isCertified ? "rgba(56, 189, 248, 0.35)" : "rgba(148, 163, 184, 0.25)")}`,
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                          title={`Estrategia generada con Motor Cuantitativo v${candVer}${isActual ? " (Actual)" : (isCertified ? " (Certificada)" : " (Legacy)")}`}
                        >
                          {isActual ? `🟢 v${candVer}` : (isCertified ? `🔵 v${candVer}` : `⚪ v${candVer}`)}
                        </span>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px" }}>
                        <div style={{ fontWeight: 700, color: "#e2e8f0", fontSize: "11px", fontFamily: "var(--font-mono, monospace)" }}>
                          {dur?.total_months ? `📅 ${dur.total_months.toFixed(1)}m dataset` : "📅 N/A"}
                        </div>
                        <div style={{ fontSize: "9.5px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                          {dur?.blind_oos_bars ? `OOS: ${dur.blind_oos_bars} velas` : (dur?.oos_months ? `OOS: ${dur.oos_months.toFixed(1)}m` : "OOS: N/A")}
                        </div>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 900, color: typeof monRoi === "number" ? (monRoi >= 0 ? "#10b981" : "#f87171") : "#94a3b8", fontSize: "12px" }}>
                        {typeof monRoi === "number" ? (monRoi >= 0 ? `+${monRoi.toFixed(2)}%/m` : `${monRoi.toFixed(2)}%/m`) : "N/A"}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)" }}>
                        <span style={{ color: "#94a3b8" }}>{typeof pfIs === "number" ? pfIs.toFixed(2) : "N/A"}</span> /{" "}
                        <strong style={{ color: typeof pfOos === "number" ? (pfOos >= 1.2 ? "#34d399" : "#f59e0b") : "#94a3b8" }}>
                          {typeof pfOos === "number" ? pfOos.toFixed(2) : "N/A"}
                        </strong>
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#cbd5e1" }}>
                        {typeof wr === "number" ? `${wr.toFixed(1)}%` : "N/A"}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#94a3b8" }}>
                        {typeof tradesOos === "number" ? tradesOos : "N/A"}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", fontWeight: 700, color: typeof dd === "number" ? (dd <= 5.0 ? "#34d399" : dd <= 20.0 ? "#fbbf24" : "#f87171") : "#94a3b8" }}>
                        {typeof dd === "number" ? `${dd.toFixed(1)}%` : "N/A"}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "right", fontFamily: "var(--font-mono, monospace)", color: "#38bdf8", fontWeight: 700 }}>
                        {typeof mc === "number" ? `${mc.toFixed(0)}/100` : "N/A"}
                      </td>
                      <td style={{ padding: isCompactDensity ? "6px 10px" : "10px 12px", textAlign: "center", display: "flex", gap: "4px", justifyContent: "center" }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            executeSingleCandidateRevalidation(c.candidate_id);
                          }}
                          disabled={singleRevalLoading === c.candidate_id}
                          style={{
                            padding: "3px 6px",
                            borderRadius: "4px",
                            background: "rgba(236, 72, 153, 0.15)",
                            border: "1px solid rgba(236, 72, 153, 0.35)",
                            color: "#f472b6",
                            fontSize: "9.5px",
                            fontWeight: 800,
                            cursor: singleRevalLoading === c.candidate_id ? "not-allowed" : "pointer",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                          title={`Revalidar esta estrategia con el motor actual v${version}`}
                        >
                          {singleRevalLoading === c.candidate_id ? "⏳..." : `🔄 v${version}`}
                        </button>
                        <button
                          onClick={() => setSelectedCandidate(c)}
                          style={{
                            padding: "3px 8px",
                            borderRadius: "4px",
                            background: "rgba(56, 189, 248, 0.15)",
                            border: "1px solid rgba(56, 189, 248, 0.3)",
                            color: "#38bdf8",
                            fontSize: "10px",
                            fontWeight: 700,
                            cursor: "pointer",
                            fontFamily: "var(--font-mono, monospace)",
                          }}
                        >
                          Ver ADN
                        </button>
                        <Link
                          href={`/research?candidate_id=${c.candidate_id}`}
                          style={{
                            padding: "3px 8px",
                            borderRadius: "4px",
                            background: "rgba(250, 204, 21, 0.15)",
                            border: "1px solid rgba(250, 204, 21, 0.4)",
                            color: "#facc15",
                            fontSize: "10px",
                            fontWeight: 800,
                            textDecoration: "none",
                            fontFamily: "var(--font-mono, monospace)",
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "3px",
                          }}
                          title="Abrir en el Laboratorio de Refinamiento Cuantitativo & IA (Punto 4)"
                        >
                          🔬 Refinar en Lab
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 5. PAGINACIÓN Y CONTROL INFERIOR */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 14px", borderTop: "1px solid rgba(255, 255, 255, 0.08)", background: "rgba(10, 14, 22, 0.95)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
              Mostrando {Math.min(sorted.length, (currentPage - 1) * pageSize + 1)}-{Math.min(sorted.length, currentPage * pageSize)} de {sorted.length} candidatos
            </span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{
                background: "rgba(0, 0, 0, 0.4)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "4px",
                color: "#ffffff",
                padding: "2px 6px",
                fontSize: "10.5px",
                fontFamily: "var(--font-mono, monospace)",
              }}
            >
              <option value={25}>25 por página</option>
              <option value={50}>50 por página</option>
              <option value={100}>100 por página</option>
            </select>
          </div>

          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              style={{
                background: currentPage === 1 ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                color: currentPage === 1 ? "#475569" : "#ffffff",
                padding: "4px 10px",
                borderRadius: "4px",
                fontSize: "11px",
                cursor: currentPage === 1 ? "not-allowed" : "pointer",
              }}
            >
              ← Anterior
            </button>
            <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono, monospace)" }}>
              {currentPage} / {totalPages}
            </span>
            <button
              disabled={currentPage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              style={{
                background: currentPage >= totalPages ? "rgba(255, 255, 255, 0.02)" : "rgba(255, 255, 255, 0.08)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                color: currentPage >= totalPages ? "#475569" : "#ffffff",
                padding: "4px 10px",
                borderRadius: "4px",
                fontSize: "11px",
                cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
              }}
            >
              Siguiente →
            </button>
          </div>
        </div>
      </div>

      {/* 6. MODAL DE INSPECCIÓN DE ADN & EXPORTACIÓN */}
      {selectedCandidate && (
        <div
          onClick={() => setSelectedCandidate(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0, 0, 0, 0.8)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 300,
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "rgba(12, 18, 28, 0.98)",
              border: "1px solid rgba(99, 225, 180, 0.3)",
              borderRadius: "12px",
              width: "100%",
              maxWidth: "860px",
              maxHeight: "85vh",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              boxShadow: "0 0 40px rgba(0, 0, 0, 0.8)",
            }}
          >
            {/* Header del Modal */}
            <div style={{ padding: "16px 20px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: "11px", color: "#63e1b4", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>
                  INSPECCIÓN CUANTITATIVA · {selectedCandidate.route}
                </div>
                <h3 style={{ fontSize: "18px", fontWeight: 900, color: "#ffffff", margin: "2px 0 0 0" }}>
                  {selectedCandidate.name}
                </h3>
              </div>

              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <div style={{ display: "flex", background: "rgba(255, 255, 255, 0.05)", borderRadius: "6px", padding: "2px" }}>
                  {(["PINESCRIPT", "NINJATRADER", "PYTHON"] as const).map((fmt) => (
                    <button
                      key={fmt}
                      onClick={() => handleExportTypeChange(fmt)}
                      style={{
                        padding: "4px 8px",
                        borderRadius: "4px",
                        border: "none",
                        background: exportType === fmt ? "#63e1b4" : "transparent",
                        color: exportType === fmt ? "#06080d" : "#94a3b8",
                        fontSize: "10px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setSelectedCandidate(null)}
                  style={{
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "none",
                    color: "#94a3b8",
                    fontSize: "14px",
                    width: "28px",
                    height: "28px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Código Exportado / ADN */}
            <div style={{ padding: "16px 20px", flex: 1, overflowY: "auto" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono, monospace)" }}>
                  Código ejecutable generado para {exportType}:
                </span>
                <button
                  onClick={handleCopyCode}
                  style={{
                    background: copied ? "#34d399" : "rgba(99, 225, 180, 0.15)",
                    border: "1px solid rgba(99, 225, 180, 0.3)",
                    color: copied ? "#06080d" : "#63e1b4",
                    padding: "4px 10px",
                    borderRadius: "4px",
                    fontSize: "11px",
                    fontWeight: 800,
                    cursor: "pointer",
                  }}
                >
                  {copied ? "✓ Copiado" : "📋 Copiar Código"}
                </button>
              </div>

              <pre
                style={{
                  background: "#06080d",
                  border: "1px solid rgba(255, 255, 255, 0.06)",
                  borderRadius: "8px",
                  padding: "14px",
                  fontSize: "11px",
                  fontFamily: "var(--font-mono, monospace)",
                  color: "#cbd5e1",
                  maxHeight: "380px",
                  overflowY: "auto",
                  whiteSpace: "pre-wrap",
                }}
              >
                {exportCode}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* 6. MODAL DE CONFIRMACIÓN & RESULTADOS DE REVALIDACIÓN */}
      {showRevalModal && (
        <div
          onClick={() => setShowRevalModal(false)}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0, 0, 0, 0.85)",
            backdropFilter: "blur(10px)",
            zIndex: 99999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#0b132b",
              border: "1px solid rgba(236, 72, 153, 0.4)",
              borderRadius: "16px",
              padding: "28px",
              maxWidth: "680px",
              width: "100%",
              color: "#f8fafc",
              boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 30px rgba(236, 72, 153, 0.2)",
            }}
          >
            {/* Modal Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "18px" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                  <span style={{ fontSize: "18px" }}>🛡️</span>
                  <span style={{ fontSize: "11px", fontWeight: 900, color: "#ec4899", letterSpacing: "1.2px", fontFamily: "var(--font-mono, monospace)" }}>
                    CENTRO DE AUDITORÍA Y CERTIFICACIÓN CUANTITATIVA
                  </span>
                </div>
                <h2 style={{ fontSize: "19px", fontWeight: 900, margin: 0, color: "#ffffff" }}>
                  Revalidación de Estrategias con Motor v{version} (Actual)
                </h2>
              </div>
              <button
                onClick={() => setShowRevalModal(false)}
                style={{ background: "transparent", border: "none", color: "#94a3b8", fontSize: "20px", cursor: "pointer" }}
                title="Cerrar modal (la tarea en segundo plano continuará)"
              >
                ✕
              </button>
            </div>

            {revalStatus?.status === "RUNNING" ? (
              /* Running in Background Progress View */
              <div>
                <div style={{ background: "rgba(236, 72, 153, 0.08)", border: "1px solid rgba(236, 72, 153, 0.3)", borderRadius: "12px", padding: "16px", marginBottom: "18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "16px" }}>⚙️</span>
                      <span style={{ fontSize: "13px", fontWeight: 800, color: "#fff" }}>
                        Ejecución Activa en Segundo Plano
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", fontWeight: 900, color: "#ec4899", fontFamily: "var(--font-mono, monospace)" }}>
                      {Math.round((revalStatus.processed_count / (revalStatus.total_candidates || 1)) * 100)}%
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div style={{ width: "100%", height: "8px", background: "rgba(255, 255, 255, 0.1)", borderRadius: "4px", overflow: "hidden", marginBottom: "12px" }}>
                    <div
                      style={{
                        height: "100%",
                        width: `${Math.round((revalStatus.processed_count / (revalStatus.total_candidates || 1)) * 100)}%`,
                        background: "linear-gradient(90deg, #ec4899 0%, #3b82f6 100%)",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "11px", color: "#94a3b8" }}>
                    <span>Procesadas: <strong>{revalStatus.processed_count}</strong> de <strong>{revalStatus.total_candidates}</strong> estrategias</span>
                    <span style={{ color: "#38bdf8", fontFamily: "var(--font-mono, monospace)" }}>
                      {revalStatus.current_candidate ? `⏳ Evaluando: ${revalStatus.current_candidate}` : "Sincronizando..."}
                    </span>
                  </div>
                </div>

                {/* Real-Time Metrics Counters */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px", marginBottom: "16px" }}>
                  <div style={{ background: "rgba(52, 211, 153, 0.12)", border: "1px solid rgba(52, 211, 153, 0.25)", borderRadius: "8px", padding: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800 }}>PROMOVIDAS v{version}</div>
                    <div style={{ fontSize: "22px", fontWeight: 900, color: "#34d399" }}>{revalStatus.promoted_count}</div>
                  </div>
                  <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.25)", borderRadius: "8px", padding: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800 }}>RECHAZADAS</div>
                    <div style={{ fontSize: "22px", fontWeight: 900, color: "#fb7185" }}>{revalStatus.rejected_count}</div>
                  </div>
                  <div style={{ background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56, 189, 248, 0.25)", borderRadius: "8px", padding: "10px", textAlign: "center" }}>
                    <div style={{ fontSize: "9.5px", color: "#94a3b8", fontWeight: 800 }}>TOTAL TANDA</div>
                    <div style={{ fontSize: "22px", fontWeight: 900, color: "#38bdf8" }}>{revalStatus.total_candidates}</div>
                  </div>
                </div>

                {/* Live evaluated list */}
                {revalStatus.results && revalStatus.results.length > 0 && (
                  <div style={{ maxHeight: "180px", overflowY: "auto", background: "rgba(0, 0, 0, 0.4)", borderRadius: "10px", padding: "10px", border: "1px solid rgba(255, 255, 255, 0.08)", marginBottom: "16px" }}>
                    <div style={{ fontSize: "10.5px", fontWeight: 800, color: "#94a3b8", marginBottom: "6px" }}>
                      ÚLTIMAS EVALUADAS EN VIVO:
                    </div>
                    {revalStatus.results.slice(-5).reverse().map((r: any, idx: number) => (
                      <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "5px 6px", borderBottom: "1px solid rgba(255, 255, 255, 0.04)", fontSize: "11px" }}>
                        <div>
                          <span style={{ fontWeight: 800, color: "#fff" }}>{r.name}</span>{" "}
                          <span style={{ color: "#38bdf8", fontSize: "10px" }}>({r.symbol} {r.timeframe})</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                          <span style={{ fontSize: "10px", color: "#94a3b8" }}>Gates: {r.gates_passed}/11</span>
                          <span style={{ fontSize: "9.5px", fontWeight: 800, color: r.passed ? "#34d399" : "#fb7185", background: r.passed ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)", padding: "2px 5px", borderRadius: "4px" }}>
                            {r.passed ? `🟢 v${version}` : "⛔ RECHAZADA"}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Running Actions */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <button
                    onClick={cancelRevalidation}
                    style={{
                      padding: "8px 16px",
                      borderRadius: "8px",
                      background: "rgba(244, 63, 94, 0.15)",
                      border: "1px solid rgba(244, 63, 94, 0.4)",
                      color: "#fb7185",
                      fontSize: "11px",
                      fontWeight: 800,
                      cursor: "pointer",
                    }}
                  >
                    ⏹️ Detener Revalidación
                  </button>
                  <button
                    onClick={() => setShowRevalModal(false)}
                    style={{
                      padding: "9px 20px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)",
                      border: "none",
                      color: "#fff",
                      fontSize: "11.5px",
                      fontWeight: 800,
                      cursor: "pointer",
                      boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
                    }}
                  >
                    🔽 Seguir en 2º Plano y Cerrar
                  </button>
                </div>
              </div>
            ) : (revalStatus?.status === "COMPLETED" && (revalStatus?.results?.length > 0 || showFinishedResults)) ? (
              /* Completed Results Screen */
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "18px" }}>
                  <div style={{ background: "rgba(52, 211, 153, 0.12)", border: "1px solid rgba(52, 211, 153, 0.3)", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>PROMOVIDAS A v{version}</div>
                    <div style={{ fontSize: "28px", fontWeight: 900, color: "#34d399", margin: "4px 0" }}>
                      {revalStatus.promoted_count}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "#cbd5e1" }}>Superaron los 11 Gates</div>
                  </div>

                  <div style={{ background: "rgba(244, 63, 94, 0.12)", border: "1px solid rgba(244, 63, 94, 0.3)", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>RECHAZADAS POR GATES</div>
                    <div style={{ fontSize: "28px", fontWeight: 900, color: "#fb7185", margin: "4px 0" }}>
                      {revalStatus.rejected_count}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "#cbd5e1" }}>No pasaron filtros v{version}</div>
                  </div>

                  <div style={{ background: "rgba(56, 189, 248, 0.12)", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "10px", padding: "14px", textAlign: "center" }}>
                    <div style={{ fontSize: "10px", color: "#94a3b8", fontWeight: 800, fontFamily: "var(--font-mono, monospace)" }}>TOTAL AUDITADAS</div>
                    <div style={{ fontSize: "28px", fontWeight: 900, color: "#38bdf8", margin: "4px 0" }}>
                      {revalStatus.total_candidates}
                    </div>
                    <div style={{ fontSize: "10.5px", color: "#cbd5e1" }}>Motor v{version} Dual-Engine</div>
                  </div>
                </div>

                {/* Audit breakdown list */}
                <div style={{ maxHeight: "240px", overflowY: "auto", background: "rgba(0, 0, 0, 0.4)", borderRadius: "10px", padding: "10px", border: "1px solid rgba(255, 255, 255, 0.08)", marginBottom: "18px" }}>
                  <div style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", marginBottom: "8px", paddingBottom: "4px", borderBottom: "1px solid rgba(255, 255, 255, 0.06)" }}>
                    DESGLOSE FORENSE POR ESTRATEGIA:
                  </div>
                  {revalStatus.results?.map((r: any, idx: number) => (
                    <div key={idx} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 8px", borderBottom: "1px solid rgba(255, 255, 255, 0.04)", fontSize: "11px" }}>
                      <div>
                        <span style={{ fontWeight: 800, color: "#ffffff" }}>{r.name}</span>{" "}
                        <span style={{ color: "#38bdf8", fontSize: "10px", fontFamily: "var(--font-mono, monospace)" }}>({r.symbol} {r.timeframe})</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "10px", color: "#94a3b8" }}>Gates: {r.gates_passed}/11</span>
                        <span style={{ fontSize: "10px", fontWeight: 800, color: r.passed ? "#34d399" : "#fb7185", background: r.passed ? "rgba(52, 211, 153, 0.15)" : "rgba(244, 63, 94, 0.15)", padding: "2px 6px", borderRadius: "4px" }}>
                          {r.passed ? `🟢 v${version} APROBADA` : `⛔ ${r.new_status}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <button
                    onClick={() => setShowFinishedResults(false)}
                    style={{
                      padding: "10px 18px",
                      borderRadius: "8px",
                      background: "rgba(255, 255, 255, 0.08)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#fff",
                      fontSize: "11.5px",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    ⚙️ Nueva Configuración
                  </button>
                  <button
                    onClick={() => setShowRevalModal(false)}
                    style={{
                      padding: "10px 24px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #34d399 0%, #3b82f6 100%)",
                      border: "none",
                      color: "#0c111d",
                      fontSize: "12px",
                      fontWeight: 900,
                      cursor: "pointer",
                    }}
                  >
                    ✓ Cerrar y Ver Lista Actualizada
                  </button>
                </div>
              </div>
            ) : (
              /* Configuration Controls */
              <div>
                {/* Information Card */}
                <div style={{ background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "16px", marginBottom: "20px" }}>
                  <div style={{ fontSize: "12.5px", color: "#cbd5e1", lineHeight: "1.6" }}>
                    Esta acción someterá las estrategias generadas en versiones anteriores a la verificación estricta del <strong>Pipeline Cuantitativo v{version}</strong> en segundo plano:
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "12px" }}>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Modelos de microestructura y costes reales CME/FX/Crypto.
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Aislamiento físico del Blind Holdout 20% intocado.
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Estrés 3x slippage y Monte Carlo (0.0% ruina).
                    </div>
                    <div style={{ fontSize: "11px", color: "#94a3b8", display: "flex", gap: "6px" }}>
                      <span style={{ color: "#34d399" }}>✓</span> Reconciliación matemática trade-a-trade NautilusTrader.
                    </div>
                  </div>
                  <div style={{ marginTop: "12px", padding: "10px", background: "rgba(56, 189, 248, 0.08)", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)", fontSize: "11px", color: "#38bdf8" }}>
                    💡 <strong>Resultado:</strong> Las que superen los 11 Gates serán promovidas a <strong>v{version} ACTUAL</strong> y la lista se actualizará dinámicamente. Las que no cumplan los criterios quedarán rechazadas con su motivo forense sin alterar los datos de origen.
                  </div>
                </div>

                {/* Configuration Controls */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px", marginBottom: "22px" }}>
                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                      VERSIÓN DE ORIGEN A REVALIDAR:
                    </label>
                    <select
                      value={revalTargetVersion}
                      onChange={(e) => setRevalTargetVersion(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        background: "rgba(0, 0, 0, 0.4)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        fontSize: "12px",
                        outline: "none",
                      }}
                    >
                      <option value="ALL">⚙️ Todas las Versiones Anteriores ({candidates.filter(c => c.engine_version !== "1.03").length})</option>
                      <option value="1.02">🔵 Solo Versión v1.02 ({candidates.filter(c => c.engine_version === "1.02").length})</option>
                      <option value="1.00">⚪ Solo Versión v1.00 Legacy ({candidates.filter(c => (c.engine_version || "1.00") === "1.00").length})</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                      RUTA / OBJETIVO:
                    </label>
                    <select
                      value={revalRoute}
                      onChange={(e) => setRevalRoute(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        background: "rgba(0, 0, 0, 0.4)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        fontSize: "12px",
                        outline: "none",
                      }}
                    >
                      <option value="ALL">🌐 Ambas Rutas (ULTRA + FONDEO)</option>
                      <option value="ULTRA">🔥 Solo Ruta ULTRA</option>
                      <option value="FONDEO">🛡️ Solo Ruta FONDEO</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "11px", fontWeight: 800, color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                      LÍMITE POR TANDA:
                    </label>
                    <select
                      value={revalLimit}
                      onChange={(e) => setRevalLimit(Number(e.target.value))}
                      style={{
                        width: "100%",
                        padding: "8px 12px",
                        borderRadius: "8px",
                        background: "rgba(0, 0, 0, 0.4)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        fontSize: "12px",
                        outline: "none",
                      }}
                    >
                      <option value={0}>🌐 Todas las Estrategias (Completo / Sin Límite)</option>
                      <option value={100}>100 Estrategias (~30 seg)</option>
                      <option value={50}>50 Estrategias (~15 seg)</option>
                      <option value={25}>25 Estrategias (~8 seg)</option>
                      <option value={10}>10 Estrategias (Rápido - ~3 seg)</option>
                    </select>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", paddingTop: "24px" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer", fontSize: "12px", color: "#e2e8f0" }}>
                      <input
                        type="checkbox"
                        checked={revalOnlyApproved}
                        onChange={(e) => setRevalOnlyApproved(e.target.checked)}
                        style={{ width: "16px", height: "16px", accentColor: "#ec4899" }}
                      />
                      <span>Solo estrategias aprobadas previamente</span>
                    </label>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                  <button
                    onClick={() => setShowRevalModal(false)}
                    style={{
                      padding: "10px 18px",
                      borderRadius: "8px",
                      background: "rgba(255, 255, 255, 0.08)",
                      border: "1px solid rgba(255, 255, 255, 0.15)",
                      color: "#fff",
                      fontSize: "12px",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={executeRevalidation}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      padding: "10px 22px",
                      borderRadius: "8px",
                      background: "linear-gradient(135deg, #ec4899 0%, #3b82f6 100%)",
                      border: "none",
                      color: "#ffffff",
                      fontSize: "12px",
                      fontWeight: 900,
                      cursor: "pointer",
                      boxShadow: "0 4px 14px rgba(236, 72, 153, 0.4)",
                    }}
                  >
                    <span>🚀</span>
                    <span>Confirmar y Revalidar en Segundo Plano</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
