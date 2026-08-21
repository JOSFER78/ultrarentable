"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";

interface Provider {
  provider_id: string;
  name: string;
  provider_name: string;
  market_type: string;
  platform: string;
  allowed_instruments: string;
  account_size: number;
  program_type: string;
  account_tier: string;
  target_usd: number;
  target_pct: number;
  daily_loss_limit_usd?: number;
  daily_loss_limit_pct?: number;
  dll_calc_model: string;
  max_trailing_dd_usd: number;
  max_trailing_dd_pct: number;
  trailing_dd_type: string;
  consistency_rule_pct: number;
  min_trading_days: number;
  overnight_allowed: boolean;
  news_trading_allowed: boolean;
  ea_bots_allowed: string;
  monthly_cost_usd?: number;
  regular_price_usd?: number;
  promo_price_usd?: number;
  discount_code?: string;
  discount_pct?: number;
  activation_fee_usd?: number;
  payout_split_pct?: number;
  payout_frequency?: string;
  payout_buffer_usd?: number;
  funded_trailing_lock?: string;
  contracts_limit?: string;
  trust_score?: number;
  stage_type?: string;
  source_url?: string;
  verified_at?: string;
  verification_status: string;
  notes?: string;
  recommendation_rank?: number;
  calculated_suitability_score?: number;
}

interface SummaryMeta {
  total_firms: number;
  total_accounts: number;
  futures_accounts: number;
  active_promotions_count: number;
  no_activation_fee_accounts: number;
  last_sync_timestamp: string;
  last_verified_date: string;
  status: string;
}

export default function FuturesPropFirmsCatalogPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [meta, setMeta] = useState<SummaryMeta | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  // Filtros exclusivos de Futuros
  const [selectedTier, setSelectedTier] = useState<string>("ALL");
  const [selectedDrawdown, setSelectedDrawdown] = useState<string>("ALL");
  const [selectedBotPolicy, setSelectedBotPolicy] = useState<string>("ALL");
  const [onlyZeroActivation, setOnlyZeroActivation] = useState<boolean>(false);
  const [onlyDayOnePayout, setOnlyDayOnePayout] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("" );

  // Estado de vistas por fila (id -> "EXAMEN" | "FONDEADO" | "PRECIOS")
  const [rowTabs, setRowTabs] = useState<Record<string, "EXAMEN" | "FONDEADO" | "PRECIOS">>({});

  // Comparador Cara a Cara
  const [compareList, setCompareList] = useState<Provider[]>([]);
  const [showCompareModal, setShowCompareModal] = useState<boolean>(false);

  // Asistente Recomendador de Futuros
  const [showRecommender, setShowRecommender] = useState<boolean>(false);
  const [recBudget, setRecBudget] = useState<number>(80);
  const [recBots, setRecBots] = useState<boolean>(true);
  const [recDD, setRecDD] = useState<string>("EOD");
  const [recommendations, setRecommendations] = useState<Provider[]>([]);
  const [isCalculatingRec, setIsCalculatingRec] = useState<boolean>(false);

  const fetchCatalog = () => {
    setIsLoading(true);
    fetch("/api/v1/providers?market_type=FUTURES")
      .then((r) => r.json())
      .then((data) => {
        if (Array.isArray(data)) {
          // Filtrar estrictamente solo FUTURES
          const futuresOnly = data.filter((p) => p.market_type === "FUTURES");
          setProviders(futuresOnly);
        }
      })
      .catch((err) => console.error("Error loading providers:", err))
      .finally(() => setIsLoading(false));

    fetch("/api/v1/providers/meta/summary")
      .then((r) => r.json())
      .then((data) => setMeta(data))
      .catch((err) => console.error("Error loading meta:", err));
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  const handleSyncNow = async () => {
    setIsSyncing(true);
    setSyncMessage("Sincronizando y verificando fuentes oficiales de Futuros CME...");
    try {
      const res = await fetch("/api/v1/providers/sync", { method: "POST" });
      const data = await res.json();
      setSyncMessage(data.message || "Sincronización de futuros completada con éxito.");
      fetchCatalog();
      setTimeout(() => setSyncMessage(null), 4500);
    } catch (e) {
      setSyncMessage("Error al sincronizar con el backend.");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    setTimeout(() => setCopiedCode(null), 2500);
  };

  const handleToggleCompare = (p: Provider) => {
    if (compareList.some((c) => c.provider_id === p.provider_id)) {
      setCompareList(compareList.filter((c) => c.provider_id !== p.provider_id));
    } else {
      if (compareList.length >= 4) {
        alert("Puedes comparar hasta un máximo de 4 cuentas de futuros simultáneas.");
        return;
      }
      setCompareList([...compareList, p]);
    }
  };

  const handleRunRecommender = async () => {
    setIsCalculatingRec(true);
    try {
      const params = new URLSearchParams({
        budget_usd: recBudget.toString(),
        use_bots: recBots.toString(),
        prefer_drawdown: recDD,
        market_pref: "FUTURES",
      });
      const res = await fetch(`/api/v1/providers/recommend?${params.toString()}`);
      const data = await res.json();
      if (Array.isArray(data)) setRecommendations(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsCalculatingRec(false);
    }
  };

  // Filtrado reactivo en cliente (SOLO FUTUROS)
  const filteredProviders = useMemo(() => {
    return providers.filter((p) => {
      // Tier
      if (selectedTier !== "ALL" && p.account_tier !== selectedTier) return false;
      // Drawdown
      if (selectedDrawdown !== "ALL") {
        if (!p.trailing_dd_type.toLowerCase().includes(selectedDrawdown.toLowerCase())) return false;
      }
      // Bots
      if (selectedBotPolicy !== "ALL") {
        if (selectedBotPolicy === "PERMITTED" && !p.ea_bots_allowed.includes("PERMITTED")) return false;
        if (selectedBotPolicy === "PROHIBITED" && p.ea_bots_allowed !== "PROHIBITED") return false;
      }
      // Zero activation
      if (onlyZeroActivation && (p.activation_fee_usd ?? 0) > 0) return false;
      // Payouts Día 1
      if (onlyDayOnePayout && !p.payout_frequency?.toLowerCase().includes("día 1") && !p.payout_frequency?.toLowerCase().includes("mismo día")) return false;
      // Búsqueda
      if (searchQuery.trim() !== "") {
        const q = searchQuery.toLowerCase();
        const matchesName = p.name.toLowerCase().includes(q);
        const matchesProvider = p.provider_name.toLowerCase().includes(q);
        const matchesPlatform = p.platform.toLowerCase().includes(q);
        const matchesInstruments = p.allowed_instruments.toLowerCase().includes(q);
        if (!matchesName && !matchesProvider && !matchesPlatform && !matchesInstruments) return false;
      }
      return true;
    });
  }, [providers, selectedTier, selectedDrawdown, selectedBotPolicy, onlyZeroActivation, onlyDayOnePayout, searchQuery]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-0)", color: "var(--text-primary)", padding: "28px 20px" }}>
      <div style={{ maxWidth: "1520px", margin: "0 auto" }}>
        
        {/* BREADCRUMB & HEADER EXCLUSIVO DE FUTUROS */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px", marginBottom: "20px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
              <Link href="/" style={{ color: "var(--text-muted)", fontSize: "12px", textDecoration: "none", display: "flex", alignItems: "center", gap: "4px" }}>
                <span>←</span> Centro de Control Ultrarentable
              </Link>
              <span style={{ color: "var(--border)" }}>/</span>
              <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--accent)", letterSpacing: "0.08em", textTransform: "uppercase" }}>
                FUTUROS CME · PROP FIRMS
              </span>
            </div>
            <h1 style={{ fontSize: "30px", fontWeight: 900, letterSpacing: "-0.03em", margin: "0 0 6px 0", display: "flex", alignItems: "center", gap: "12px" }}>
              🏛️ Catálogo Maestro de Firmas de Fondeo de Futuros CME
              <span style={{ fontSize: "12px", fontWeight: 800, padding: "3px 10px", borderRadius: "999px", background: "rgba(99, 225, 180, 0.15)", color: "var(--accent)", border: "1px solid var(--accent-dim)" }}>
                SOLO FUTUROS · 2026
              </span>
            </h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px", margin: 0, maxWidth: "880px", lineHeight: "1.5" }}>
              Base de datos viva y versionada de empresas de fondeo para <strong>Futuros CME (MES, MNQ, ES, NQ, YM, RTY, CL, GC)</strong>. Diferenciación estricta entre <strong>Reglas de Examen</strong> y <strong>Reglas de Fondeado</strong>, costes reales con cuota de activación ($0 vs $149), promociones activas y políticas de bots/algoritmos.
            </p>
          </div>

          {/* ACCIONES DEL HEADER */}
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <button
              onClick={() => setShowRecommender(!showRecommender)}
              style={{
                padding: "10px 18px",
                background: "linear-gradient(135deg, rgba(99, 225, 180, 0.2), rgba(59, 130, 246, 0.2))",
                border: "1px solid var(--accent)",
                borderRadius: "var(--radius-md)",
                color: "var(--accent-bright)",
                fontSize: "13px",
                fontWeight: 800,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                boxShadow: "0 4px 14px rgba(99, 225, 180, 0.15)",
                transition: "all 0.2s ease"
              }}
            >
              <span>🧠</span> {showRecommender ? "Ocultar Asistente" : "Asistente: ¿Qué Cuenta de Futuros Comprar?"}
            </button>

            <button
              onClick={handleSyncNow}
              disabled={isSyncing}
              style={{
                padding: "10px 18px",
                background: "var(--bg-panel-2)",
                border: "1px solid var(--border-hover)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-primary)",
                fontSize: "13px",
                fontWeight: 700,
                cursor: isSyncing ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span style={{ display: "inline-block", animation: isSyncing ? "spin 1s linear infinite" : "none" }}>🔄</span>
              {isSyncing ? "Sincronizando..." : "Sincronizar en Vivo"}
            </button>
          </div>
        </div>

        {/* MENSAJE DE SINCRONIZACION */}
        {syncMessage && (
          <div style={{ padding: "12px 16px", borderRadius: "var(--radius-md)", background: "rgba(34, 197, 94, 0.12)", border: "1px solid rgba(34, 197, 94, 0.3)", color: "var(--success)", fontSize: "13px", fontWeight: 700, marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span>✅ {syncMessage}</span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Actualizado en SQLite Remoto</span>
          </div>
        )}

        {/* METRICAS GLOBALES EN VIVO — SOLO FUTUROS */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px", marginBottom: "24px" }}>
          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "16px 20px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Firmas de Futuros Serias</div>
            <div style={{ fontSize: "26px", fontWeight: 900, color: "var(--text-primary)", marginTop: "4px" }}>
              {new Set(providers.map(p => p.provider_name)).size} <span style={{ fontSize: "13px", color: "var(--accent)" }}>Empresas CME</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>Topstep, MFFU, Tradeify, Apex, TradeDay...</div>
          </div>

          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "16px 20px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Cuentas de Futuros</div>
            <div style={{ fontSize: "26px", fontWeight: 900, color: "var(--info)", marginTop: "4px" }}>
              {providers.length} <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Planes</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>Desde $25K hasta $300K</div>
          </div>

          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "16px 20px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Promos del Día Activas</div>
            <div style={{ fontSize: "26px", fontWeight: 900, color: "var(--success)", marginTop: "4px" }}>
              {providers.filter(p => (p.discount_pct ?? 0) > 0).length} <span style={{ fontSize: "13px", color: "var(--success)" }}>Cupones</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>Hasta un 89% con códigos oficiales</div>
          </div>

          <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "16px 20px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Futuros Sin Activación ($0)</div>
            <div style={{ fontSize: "26px", fontWeight: 900, color: "var(--warning)", marginTop: "4px" }}>
              {providers.filter(p => (p.activation_fee_usd ?? 0) === 0).length} <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>Opciones</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>MFFU Rapid, Tradeify Growth, TradeDay, BluSky</div>
          </div>
        </div>

        {/* ASISTENTE RECOMENDADOR DE FUTUROS */}
        {showRecommender && (
          <div style={{ background: "linear-gradient(180deg, rgba(14, 26, 44, 0.95), rgba(9, 15, 26, 0.98))", border: "1px solid var(--accent)", borderRadius: "var(--radius-xl)", padding: "24px", marginBottom: "28px", boxShadow: "0 10px 30px rgba(0,0,0,0.5)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <span style={{ fontSize: "24px" }}>🧠</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: "18px", fontWeight: 900, color: "var(--accent-bright)" }}>Asistente: TOP 3 Cuentas de Futuros CME</h3>
                  <p style={{ margin: 0, fontSize: "12px", color: "var(--text-secondary)" }}>Pondera solvencia de retiros, política de bots en Tradovate/NinjaTrader, tipo de drawdown y coste total.</p>
                </div>
              </div>
              <button onClick={() => setShowRecommender(false)} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "18px", cursor: "pointer" }}>✕</button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "20px" }}>
              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", marginBottom: "6px", textTransform: "uppercase" }}>Presupuesto Máximo Examen ($USD)</label>
                <input
                  type="number"
                  value={recBudget}
                  onChange={(e) => setRecBudget(Number(e.target.value))}
                  style={{ width: "100%", padding: "10px 12px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "#fff", fontSize: "14px", fontWeight: 800 }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", marginBottom: "6px", textTransform: "uppercase" }}>¿Operas con Bots / Algoritmos?</label>
                <select
                  value={recBots ? "YES" : "NO"}
                  onChange={(e) => setRecBots(e.target.value === "YES")}
                  style={{ width: "100%", padding: "10px 12px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "#fff", fontSize: "13px", fontWeight: 700 }}
                >
                  <option value="YES">✅ Sí (Algoritmos / EAs)</option>
                  <option value="NO">👤 No (Manual / Discrecional)</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", marginBottom: "6px", textTransform: "uppercase" }}>Preferencia de Drawdown</label>
                <select
                  value={recDD}
                  onChange={(e) => setRecDD(e.target.value)}
                  style={{ width: "100%", padding: "10px 12px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "#fff", fontSize: "13px", fontWeight: 700 }}
                >
                  <option value="EOD">EOD Trailing (Fin de Día - Recomendado)</option>
                  <option value="STATIC">Estático / Static (Máxima Seguridad)</option>
                  <option value="INTRADAY">Intraday Peak (Cuentas más baratas)</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleRunRecommender}
              disabled={isCalculatingRec}
              style={{
                width: "100%",
                padding: "12px",
                background: "var(--accent)",
                color: "#06090e",
                border: "none",
                borderRadius: "var(--radius-md)",
                fontSize: "14px",
                fontWeight: 900,
                cursor: "pointer",
                letterSpacing: "0.02em"
              }}
            >
              {isCalculatingRec ? "Calculando Idoneidad de Futuros..." : "🔍 Calcular TOP 3 Cuentas de Futuros Óptimas para Hoy"}
            </button>

            {/* RESULTADOS RECOMENDADOS */}
            {recommendations.length > 0 && (
              <div style={{ marginTop: "24px" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 900, color: "var(--accent-bright)", textTransform: "uppercase", marginBottom: "12px" }}>
                  🏆 TOP 3 Cuentas de Futuros Seleccionadas:
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "14px" }}>
                  {recommendations.map((rec) => (
                    <div key={rec.provider_id} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-active)", borderRadius: "var(--radius-lg)", padding: "16px", position: "relative" }}>
                      <div style={{ position: "absolute", top: "12px", right: "12px", background: "var(--accent)", color: "#000", fontSize: "11px", fontWeight: 900, padding: "2px 8px", borderRadius: "999px" }}>
                        #{rec.recommendation_rank} · SCORE {rec.calculated_suitability_score}
                      </div>
                      <div style={{ fontWeight: 800, fontSize: "15px", color: "#fff" }}>{rec.name}</div>
                      <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>{rec.provider_name} · ${rec.account_size.toLocaleString()} USD</div>
                      
                      <div style={{ marginTop: "12px", padding: "10px", background: "rgba(0,0,0,0.3)", borderRadius: "var(--radius-sm)", fontSize: "12px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)" }}>Precio Actual:</span>
                          <span style={{ fontWeight: 800, color: "var(--success)" }}>${rec.promo_price_usd ?? rec.monthly_cost_usd} USD</span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                          <span style={{ color: "var(--text-muted)" }}>Cuota de Activación:</span>
                          <span style={{ fontWeight: 800, color: (rec.activation_fee_usd ?? 0) === 0 ? "var(--accent)" : "var(--danger)" }}>
                            {(rec.activation_fee_usd ?? 0) === 0 ? "$0 (Gratis)" : `$${rec.activation_fee_usd}`}
                          </span>
                        </div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}>
                          <span style={{ color: "var(--text-muted)" }}>Drawdown:</span>
                          <span style={{ fontWeight: 700 }}>{rec.trailing_dd_type}</span>
                        </div>
                      </div>

                      <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
                        {rec.source_url && (
                          <a href={rec.source_url} target="_blank" rel="noreferrer" style={{ flex: 1, padding: "8px", textAlign: "center", background: "var(--accent)", color: "#06090e", borderRadius: "var(--radius-sm)", fontSize: "12px", fontWeight: 800, textDecoration: "none" }}>
                            Web Oficial ↗
                          </a>
                        )}
                        {rec.discount_code && (
                          <button onClick={() => handleCopyCode(rec.discount_code!)} style={{ padding: "8px 12px", background: "var(--bg-3)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "#fff", fontSize: "12px", fontWeight: 700, cursor: "pointer" }}>
                            {copiedCode === rec.discount_code ? "✓ Copiado" : `Cupón: ${rec.discount_code}`}
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* BARRA DE FILTROS DE FUTUROS */}
        <div style={{ background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: "var(--radius-xl)", padding: "18px 20px", marginBottom: "24px" }}>
          
          {/* PÍLDORAS DE TAMAÑO DE CUENTA */}
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "8px", letterSpacing: "0.05em" }}>
              1. Selecciona Tamaño de Cuenta de Futuros:
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {["ALL", "25K", "50K", "100K", "150K", "250K", "300K"].map((tier) => (
                <button
                  key={tier}
                  onClick={() => setSelectedTier(tier)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: "999px",
                    border: selectedTier === tier ? "1px solid var(--accent)" : "1px solid var(--border)",
                    background: selectedTier === tier ? "rgba(99, 225, 180, 0.15)" : "var(--bg-2)",
                    color: selectedTier === tier ? "var(--accent-bright)" : "var(--text-secondary)",
                    fontSize: "12px",
                    fontWeight: 800,
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                >
                  {tier === "ALL" ? "🌐 Todos los Tamaños" : `$${tier}`}
                </button>
              ))}
            </div>
          </div>

          <div style={{ height: "1px", background: "var(--border)", margin: "16px 0" }} />

          {/* FILTROS MULTI-FACETA DE FUTUROS */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", alignItems: "flex-end" }}>
            
            {/* TIPO DE DRAWDOWN */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>TIPO DE DRAWDOWN</label>
              <select
                value={selectedDrawdown}
                onChange={(e) => setSelectedDrawdown(e.target.value)}
                style={{ width: "100%", padding: "8px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: "12px", fontWeight: 700 }}
              >
                <option value="ALL">Cualquier Drawdown</option>
                <option value="EOD">EOD Trailing (Fin de Día)</option>
                <option value="Static">Estático / Static (Fijo)</option>
                <option value="Intraday">Intraday Peak Trailing</option>
              </select>
            </div>

            {/* BOTS / EAS */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>POLÍTICA DE BOTS</label>
              <select
                value={selectedBotPolicy}
                onChange={(e) => setSelectedBotPolicy(e.target.value)}
                style={{ width: "100%", padding: "8px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: "12px", fontWeight: 700 }}
              >
                <option value="ALL">Cualquier Política</option>
                <option value="PERMITTED">Permitidos 100%</option>
                <option value="PROHIBITED">Solo Manual (Sin Bots)</option>
              </select>
            </div>

            {/* CHECKBOX ACTIVACION $0 */}
            <div>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", height: "36px", cursor: "pointer", fontSize: "12px", fontWeight: 700, color: onlyZeroActivation ? "var(--accent)" : "var(--text-secondary)" }}>
                <input
                  type="checkbox"
                  checked={onlyZeroActivation}
                  onChange={(e) => setOnlyZeroActivation(e.target.checked)}
                  style={{ accentColor: "var(--accent)", width: "16px", height: "16px" }}
                />
                Solo $0 Activación
              </label>
            </div>

            {/* CHECKBOX RETIROS DIA 1 */}
            <div>
              <label style={{ display: "flex", alignItems: "center", gap: "8px", height: "36px", cursor: "pointer", fontSize: "12px", fontWeight: 700, color: onlyDayOnePayout ? "var(--accent)" : "var(--text-secondary)" }}>
                <input
                  type="checkbox"
                  checked={onlyDayOnePayout}
                  onChange={(e) => setOnlyDayOnePayout(e.target.checked)}
                  style={{ accentColor: "var(--accent)", width: "16px", height: "16px" }}
                />
                Retiros Día 1 / Mismo Día
              </label>
            </div>

            {/* BUSCADOR */}
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: 700, color: "var(--text-muted)", marginBottom: "4px" }}>BUSCAR FIRMA O PLATAFORMA</label>
              <input
                type="text"
                placeholder="Ej. Topstep, MFFU, Tradovate, NinjaTrader..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ width: "100%", padding: "8px 12px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-primary)", fontSize: "12px" }}
              />
            </div>
          </div>
        </div>

        {/* COMPARADOR FLOTANTE */}
        {compareList.length > 0 && (
          <div style={{ position: "sticky", top: "16px", zIndex: 100, background: "rgba(14, 22, 34, 0.95)", backdropFilter: "blur(12px)", border: "1px solid var(--accent)", borderRadius: "var(--radius-lg)", padding: "12px 20px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center", boxShadow: "0 8px 30px rgba(0,0,0,0.6)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "13px", fontWeight: 800, color: "var(--accent-bright)" }}>
                ⚖️ Modo Comparador de Futuros ({compareList.length}/4 seleccionadas):
              </span>
              <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                {compareList.map((c) => (
                  <span key={c.provider_id} style={{ fontSize: "11px", background: "var(--bg-3)", padding: "4px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "6px" }}>
                    {c.name}
                    <button onClick={() => handleToggleCompare(c)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", padding: 0 }}>✕</button>
                  </span>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              <button
                onClick={() => setCompareList([])}
                style={{ padding: "6px 12px", background: "transparent", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", color: "var(--text-muted)", fontSize: "12px", cursor: "pointer" }}
              >
                Limpiar
              </button>
              <button
                onClick={() => setShowCompareModal(true)}
                style={{ padding: "6px 16px", background: "var(--accent)", border: "none", borderRadius: "var(--radius-sm)", color: "#06090e", fontSize: "12px", fontWeight: 900, cursor: "pointer" }}
              >
                Ver Comparativa Lado a Lado ➔
              </button>
            </div>
          </div>
        )}

        {/* LISTADO DE CUENTAS DE FUTUROS */}
        {isLoading ? (
          <div style={{ textAlign: "center", padding: "60px 0", color: "var(--text-muted)" }}>
            <div style={{ fontSize: "30px", marginBottom: "10px" }}>⏳</div>
            <div style={{ fontSize: "14px", fontWeight: 700 }}>Cargando catálogo de firmas de futuros CME...</div>
          </div>
        ) : filteredProviders.length === 0 ? (
          <div style={{ textAlign: "center", padding: "60px 20px", background: "var(--bg-panel)", borderRadius: "var(--radius-xl)", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: "32px", marginBottom: "12px" }}>🔍</div>
            <h3 style={{ margin: "0 0 6px 0", fontSize: "18px", fontWeight: 800 }}>No se encontraron cuentas de futuros con los filtros actuales</h3>
            <p style={{ color: "var(--text-muted)", fontSize: "13px", margin: "0 0 16px 0" }}>Prueba a seleccionar "Todos los Tamaños" o limpiar el texto de búsqueda.</p>
            <button
              onClick={() => {
                setSelectedTier("ALL");
                setSelectedDrawdown("ALL");
                setSelectedBotPolicy("ALL");
                setOnlyZeroActivation(false);
                setOnlyDayOnePayout(false);
                setSearchQuery("");
              }}
              style={{ padding: "8px 18px", background: "var(--accent)", color: "#06090e", border: "none", borderRadius: "var(--radius-sm)", fontSize: "12px", fontWeight: 800, cursor: "pointer" }}
            >
              Restablecer Filtros
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {filteredProviders.map((p) => {
              const activeTab = rowTabs[p.provider_id] || "EXAMEN";
              const isComparing = compareList.some((c) => c.provider_id === p.provider_id);
              const price = p.promo_price_usd ?? p.monthly_cost_usd ?? p.regular_price_usd ?? 0;

              return (
                <div
                  key={p.provider_id}
                  style={{
                    background: "var(--bg-panel)",
                    border: isComparing ? "1px solid var(--accent)" : "1px solid var(--border)",
                    borderRadius: "var(--radius-lg)",
                    overflow: "hidden",
                    transition: "border 0.2s ease, box-shadow 0.2s ease",
                  }}
                >
                  {/* CABECERA DE LA FILA / CARD */}
                  <div style={{ padding: "18px 20px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", alignItems: "center", borderBottom: "1px solid var(--border)" }}>
                    
                    {/* COL 1: FIRMA Y TAMAÑO */}
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                        <span style={{ fontSize: "10px", fontWeight: 900, padding: "2px 6px", borderRadius: "4px", background: "rgba(96, 165, 250, 0.2)", color: "#60a5fa", fontFamily: "monospace" }}>
                          FUTUROS CME
                        </span>
                        <span style={{ fontSize: "10px", fontWeight: 800, padding: "2px 6px", borderRadius: "4px", background: "rgba(34, 197, 94, 0.15)", color: "var(--success)", fontFamily: "monospace" }}>
                          SCORE {p.trust_score ?? 90}/100
                        </span>
                      </div>
                      <div style={{ fontSize: "16px", fontWeight: 900, color: "#fff" }}>{p.name}</div>
                      <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                        Firma: <strong style={{ color: "var(--text-primary)" }}>{p.provider_name}</strong> · Programa: <strong>{p.program_type}</strong>
                      </div>
                    </div>

                    {/* COL 2: PLATAFORMAS & INSTRUMENTOS */}
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Plataformas Soportadas</div>
                      <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--text-primary)", marginTop: "2px" }}>{p.platform}</div>
                      <div style={{ fontSize: "11px", color: "#60a5fa", marginTop: "2px" }}>{p.allowed_instruments}</div>
                    </div>

                    {/* COL 3: PRECIOS & CUPÓN */}
                    <div>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Coste Examen / Mes</div>
                      <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "2px" }}>
                        <span style={{ fontSize: "20px", fontWeight: 900, color: "var(--success)" }}>
                          ${price.toFixed(2)} USD
                        </span>
                        {p.regular_price_usd && p.regular_price_usd > price && (
                          <span style={{ fontSize: "12px", color: "var(--text-muted)", textDecoration: "line-through" }}>
                            ${p.regular_price_usd.toFixed(2)}
                          </span>
                        )}
                      </div>
                      {p.discount_code && (
                        <div style={{ marginTop: "4px" }}>
                          <button
                            onClick={() => handleCopyCode(p.discount_code!)}
                            style={{
                              padding: "2px 8px",
                              borderRadius: "4px",
                              background: "rgba(99, 225, 180, 0.15)",
                              border: "1px solid var(--accent-dim)",
                              color: "var(--accent-bright)",
                              fontSize: "10px",
                              fontWeight: 800,
                              cursor: "pointer",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            <span>🏷️</span> {copiedCode === p.discount_code ? "✓ Copiado" : `Cupón: ${p.discount_code} (-${p.discount_pct}%)`}
                          </button>
                        </div>
                      )}
                    </div>

                    {/* COL 4: ACCIONES */}
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px", alignItems: "flex-end" }}>
                      <div style={{ display: "flex", gap: "8px", width: "100%", justifyContent: "flex-end" }}>
                        <button
                          onClick={() => handleToggleCompare(p)}
                          style={{
                            padding: "6px 12px",
                            borderRadius: "var(--radius-sm)",
                            border: isComparing ? "1px solid var(--accent)" : "1px solid var(--border)",
                            background: isComparing ? "rgba(99, 225, 180, 0.2)" : "var(--bg-2)",
                            color: isComparing ? "var(--accent-bright)" : "var(--text-secondary)",
                            fontSize: "11px",
                            fontWeight: 800,
                            cursor: "pointer",
                          }}
                        >
                          {isComparing ? "✓ En Comparador" : "+ Comparar"}
                        </button>
                        {p.source_url && (
                          <a
                            href={p.source_url}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                              padding: "6px 12px",
                              borderRadius: "var(--radius-sm)",
                              background: "var(--accent)",
                              color: "#06090e",
                              fontSize: "11px",
                              fontWeight: 900,
                              textDecoration: "none",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                            }}
                          >
                            Web Oficial ↗
                          </a>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* SELECTOR DE PESTAÑAS */}
                  <div style={{ display: "flex", background: "rgba(0,0,0,0.25)", borderBottom: "1px solid var(--border)" }}>
                    <button
                      onClick={() => setRowTabs({ ...rowTabs, [p.provider_id]: "EXAMEN" })}
                      style={{
                        flex: 1,
                        padding: "10px 16px",
                        background: activeTab === "EXAMEN" ? "var(--bg-panel-2)" : "transparent",
                        border: "none",
                        borderBottom: activeTab === "EXAMEN" ? "2px solid var(--accent)" : "2px solid transparent",
                        color: activeTab === "EXAMEN" ? "var(--text-primary)" : "var(--text-muted)",
                        fontSize: "12px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      🎯 1. Reglas de Examen (Fase de Evaluación)
                    </button>

                    <button
                      onClick={() => setRowTabs({ ...rowTabs, [p.provider_id]: "FONDEADO" })}
                      style={{
                        flex: 1,
                        padding: "10px 16px",
                        background: activeTab === "FONDEADO" ? "var(--bg-panel-2)" : "transparent",
                        border: "none",
                        borderBottom: activeTab === "FONDEADO" ? "2px solid #60a5fa" : "2px solid transparent",
                        color: activeTab === "FONDEADO" ? "var(--text-primary)" : "var(--text-muted)",
                        fontSize: "12px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      🏦 2. Reglas de Cuenta Fondeada (Master / Live)
                    </button>

                    <button
                      onClick={() => setRowTabs({ ...rowTabs, [p.provider_id]: "PRECIOS" })}
                      style={{
                        flex: 1,
                        padding: "10px 16px",
                        background: activeTab === "PRECIOS" ? "var(--bg-panel-2)" : "transparent",
                        border: "none",
                        borderBottom: activeTab === "PRECIOS" ? "2px solid var(--warning)" : "2px solid transparent",
                        color: activeTab === "PRECIOS" ? "var(--text-primary)" : "var(--text-muted)",
                        fontSize: "12px",
                        fontWeight: 800,
                        cursor: "pointer",
                      }}
                    >
                      💰 3. Desglose de Coste Real & Retiros Netos
                    </button>
                  </div>

                  {/* CONTENIDO DE LA PESTAÑA */}
                  <div style={{ padding: "16px 20px", background: "var(--bg-panel-2)", fontSize: "12px" }}>
                    
                    {/* VISTA 1: REGLAS DE EXAMEN */}
                    {activeTab === "EXAMEN" && (
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>PROFIT TARGET</div>
                          <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--success)" }}>
                            ${p.target_usd.toLocaleString()} ({p.target_pct}%)
                          </div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>MAX DRAWDOWN (LÍMITE TOTAL)</div>
                          <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--danger)" }}>
                            ${p.max_trailing_dd_usd.toLocaleString()} ({p.max_trailing_dd_pct}%)
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                            Tipo: <strong>{p.trailing_dd_type}</strong>
                          </div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>PÉRDIDA DIARIA MÁX (DLL)</div>
                          <div style={{ fontSize: "14px", fontWeight: 800, color: p.daily_loss_limit_usd ? "var(--danger)" : "var(--text-muted)" }}>
                            {p.daily_loss_limit_usd ? `$${p.daily_loss_limit_usd.toLocaleString()} (${p.daily_loss_limit_pct}%)` : "Sin límite diario"}
                          </div>
                          {p.daily_loss_limit_usd && (
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>Modelo: {p.dll_calc_model}</div>
                          )}
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>REGLA DE CONSISTENCIA</div>
                          <div style={{ fontSize: "14px", fontWeight: 800 }}>
                            {p.consistency_rule_pct >= 100 ? "Sin restricción" : `≤ ${p.consistency_rule_pct}% de ganancias`}
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                            Días Mínimos: <strong>{p.min_trading_days} día(s)</strong>
                          </div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>POLÍTICA DE BOTS / EAS</div>
                          <div style={{ fontSize: "13px", fontWeight: 800, color: p.ea_bots_allowed.includes("PERMITTED") ? "var(--success)" : "var(--danger)" }}>
                            {p.ea_bots_allowed}
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                            Overnight: {p.overnight_allowed ? "✅ Sí" : "❌ No"} · Noticias: {p.news_trading_allowed ? "✅ Sí" : "❌ Restringido"}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* VISTA 2: REGLAS DE FONDEADO */}
                    {activeTab === "FONDEADO" && (
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>CUOTA DE ACTIVACIÓN (PASS FEE)</div>
                          <div style={{ fontSize: "14px", fontWeight: 900, color: (p.activation_fee_usd ?? 0) === 0 ? "var(--accent)" : "var(--danger)" }}>
                            {(p.activation_fee_usd ?? 0) === 0 ? "$0 USD (Gratuita)" : `$${p.activation_fee_usd} USD`}
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>Pago único al aprobar el examen</div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>REPARTO DE BENEFICIOS (PAYOUT SPLIT)</div>
                          <div style={{ fontSize: "14px", fontWeight: 900, color: "var(--success)" }}>
                            {p.payout_split_pct ?? 90}% Trader / {100 - (p.payout_split_pct ?? 90)}% Firma
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>100% de primeros $10K en la mayoría</div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>FRECUENCIA DE RETIRO</div>
                          <div style={{ fontSize: "14px", fontWeight: 800, color: "var(--info)" }}>
                            {p.payout_frequency ?? "Quincenal"}
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                            Colchón / Buffer Mínimo: <strong>${(p.payout_buffer_usd ?? 0).toLocaleString()} USD</strong>
                          </div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>BLOQUEO DE TRAILING EN FONDEO</div>
                          <div style={{ fontSize: "13px", fontWeight: 800, color: "var(--accent-bright)" }}>
                            {p.funded_trailing_lock === "LOCKS_AT_INITIAL_BALANCE" ? "Se congela en Balance Inicial" : p.funded_trailing_lock}
                          </div>
                          <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>No te persigue eternamente</div>
                        </div>

                        <div>
                          <div style={{ color: "var(--text-muted)", fontWeight: 700, marginBottom: "2px" }}>LÍMITE DE CONTRATOS</div>
                          <div style={{ fontSize: "13px", fontWeight: 800 }}>
                            {p.contracts_limit ?? "Según escalado oficial"}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* VISTA 3: PRECIOS & COSTE REAL */}
                    {activeTab === "PRECIOS" && (
                      <div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px", marginBottom: "12px" }}>
                          <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "var(--radius-sm)" }}>
                            <div style={{ color: "var(--text-muted)", fontSize: "11px", fontWeight: 700 }}>COSTE TOTAL PRIMER MES (EXAMEN + ACTIVACIÓN)</div>
                            <div style={{ fontSize: "18px", fontWeight: 900, color: "var(--text-primary)", marginTop: "4px" }}>
                              ${((p.promo_price_usd ?? p.monthly_cost_usd ?? 0) + (p.activation_fee_usd ?? 0)).toFixed(2)} USD
                            </div>
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                              Examen: ${price.toFixed(2)} + Activación: ${(p.activation_fee_usd ?? 0).toFixed(2)}
                            </div>
                          </div>

                          <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "var(--radius-sm)" }}>
                            <div style={{ color: "var(--text-muted)", fontSize: "11px", fontWeight: 700 }}>CÓDIGO DE DESCUENTO ACTIVO</div>
                            <div style={{ fontSize: "16px", fontWeight: 900, color: "var(--accent-bright)", marginTop: "4px" }}>
                              {p.discount_code ? p.discount_code : "Sin cupón requerido"}
                            </div>
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>
                              {p.discount_pct ? `Ahorro del ${p.discount_pct}% directo` : "Precio oficial"}
                            </div>
                          </div>

                          <div style={{ background: "rgba(0,0,0,0.3)", padding: "12px", borderRadius: "var(--radius-sm)" }}>
                            <div style={{ color: "var(--text-muted)", fontSize: "11px", fontWeight: 700 }}>ESTADO DE VERIFICACIÓN</div>
                            <div style={{ fontSize: "14px", fontWeight: 800, color: "var(--success)", marginTop: "4px" }}>
                              {p.verification_status} ({p.verified_at ?? "2026"})
                            </div>
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", marginTop: "2px" }}>Reglas cotejadas con términos oficiales CME</div>
                          </div>
                        </div>

                        {p.notes && (
                          <div style={{ padding: "10px 14px", background: "rgba(245, 158, 11, 0.08)", borderLeft: "3px solid var(--warning)", borderRadius: "4px", color: "var(--text-secondary)", fontSize: "11px" }}>
                            <strong>Condiciones Críticas / Fricción:</strong> {p.notes}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* MODAL COMPARADOR LADO A LADO */}
        {showCompareModal && compareList.length > 0 && (
          <div style={{ position: "fixed", inset: 0, zIndex: 1000, background: "rgba(0,0,0,0.85)", backdropFilter: "blur(8px)", display: "flex", justifyContent: "center", alignItems: "center", padding: "20px" }}>
            <div style={{ background: "var(--bg-1)", border: "1px solid var(--border-hover)", borderRadius: "var(--radius-xl)", width: "100%", maxWidth: "1280px", maxHeight: "90vh", overflowY: "auto", padding: "24px", boxShadow: "0 20px 60px rgba(0,0,0,0.8)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid var(--border)", paddingBottom: "12px" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "20px", fontWeight: 900 }}>⚖️ Comparativa Cara a Cara de Cuentas de Futuros CME</h3>
                  <p style={{ margin: 0, fontSize: "12px", color: "var(--text-muted)" }}>Evaluación side-by-side de métricas de examen, fondeo y coste real de extracción.</p>
                </div>
                <button onClick={() => setShowCompareModal(false)} style={{ background: "var(--bg-3)", border: "1px solid var(--border)", color: "#fff", padding: "6px 12px", borderRadius: "var(--radius-sm)", cursor: "pointer", fontWeight: 800 }}>
                  ✕ Cerrar
                </button>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "2px solid var(--border)" }}>
                      <th style={{ padding: "12px", color: "var(--text-muted)", width: "200px" }}>PARÁMETRO</th>
                      {compareList.map((c) => (
                        <th key={c.provider_id} style={{ padding: "12px", color: "#fff", fontSize: "13px", fontWeight: 900 }}>
                          {c.name}
                          <div style={{ fontSize: "11px", color: "var(--accent)", fontWeight: 700 }}>${c.account_size.toLocaleString()} USD</div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Firma</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", fontWeight: 800 }}>{c.provider_name}</td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Precio Examen Actual</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", color: "var(--success)", fontWeight: 900, fontSize: "14px" }}>
                          ${(c.promo_price_usd ?? c.monthly_cost_usd)?.toFixed(2)} USD
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Cuota de Activación ($)</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", fontWeight: 800, color: (c.activation_fee_usd ?? 0) === 0 ? "var(--accent)" : "var(--danger)" }}>
                          {(c.activation_fee_usd ?? 0) === 0 ? "$0 (Gratis)" : `$${c.activation_fee_usd} USD`}
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Profit Target</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", fontWeight: 800 }}>${c.target_usd.toLocaleString()} ({c.target_pct}%)</td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Max Drawdown & Tipo</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", color: "var(--danger)", fontWeight: 800 }}>
                          ${c.max_trailing_dd_usd.toLocaleString()} ({c.max_trailing_dd_pct}%) [{c.trailing_dd_type}]
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Límite Diario (DLL)</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px" }}>
                          {c.daily_loss_limit_usd ? `$${c.daily_loss_limit_usd.toLocaleString()} (${c.daily_loss_limit_pct}%) [${c.dll_calc_model}]` : "Sin límite diario"}
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Regla de Consistencia</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px" }}>
                          {c.consistency_rule_pct >= 100 ? "Sin restricción" : `≤ ${c.consistency_rule_pct}%`}
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Política Bots / EAs</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", fontWeight: 800, color: c.ea_bots_allowed.includes("PERMITTED") ? "var(--success)" : "var(--danger)" }}>
                          {c.ea_bots_allowed}
                        </td>
                      ))}
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border)" }}>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Frecuencia de Pagos</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px", fontWeight: 800, color: "var(--info)" }}>
                          {c.payout_frequency ?? "Quincenal"} ({c.payout_split_pct ?? 90}% split)
                        </td>
                      ))}
                    </tr>
                    <tr>
                      <td style={{ padding: "10px 12px", color: "var(--text-muted)", fontWeight: 700 }}>Enlace Directo</td>
                      {compareList.map((c) => (
                        <td key={c.provider_id} style={{ padding: "10px 12px" }}>
                          {c.source_url && (
                            <a href={c.source_url} target="_blank" rel="noreferrer" style={{ color: "var(--accent)", fontWeight: 800 }}>
                              Ir a la Web ↗
                            </a>
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
