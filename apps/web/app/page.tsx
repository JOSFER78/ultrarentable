"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface SQXStatus {
  status: string;
  base_url?: string;
  session_id?: string;
  server_info?: { name: string; version: string };
  error?: string;
}

const DEFAULT_SEARCH = {
  project: "Ultra_Auto_Pilot",
  databank: "Results",
  instrument: "BTC-USDT · 1h",
  population: 24,
};

export default function SearchHomePage() {
  const [sqxStatus, setSqxStatus] = useState<SQXStatus | null>(null);
  const [rentable, setRentable] = useState<any[]>([]);
  const [sqxCandidates, setSqxCandidates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchLog, setSearchLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const bgPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [bgState, setBgState] = useState<{ status?: string; percent?: number; done?: number; total?: number; logs?: any[] }>({});
  const [bgRunning, setBgRunning] = useState(false);

  // Search Configurator Form State
  const [cfgMode, setCfgMode] = useState<"ultra" | "fondeo">("ultra");
  const [cfgName, setCfgName] = useState("");
  const [cfgProject, setCfgProject] = useState(DEFAULT_SEARCH.project);
  const [cfgDatabank, setCfgDatabank] = useState(DEFAULT_SEARCH.databank);
  const [cfgSymbol, setCfgSymbol] = useState("BTC-USDT");
  const [cfgInterval, setCfgInterval] = useState("1h");
  const [cfgPopulation, setCfgPopulation] = useState(24);
  const [cfgTargetMultiplier, setCfgTargetMultiplier] = useState(1000);
  const [cfgMaxDrawdownPct, setCfgMaxDrawdownPct] = useState(15);
  const [cfgConsistencyTarget, setCfgConsistencyTarget] = useState(85);
  const [cfgTechniques, setCfgTechniques] = useState("");
  const [savedConfigs, setSavedConfigs] = useState<any[]>([]);
  const [cfgFeedback, setCfgFeedback] = useState<string | null>(null);
  const [cfgLoading, setCfgLoading] = useState(false);

  const pushLog = (line: string) =>
    setSearchLog((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${line}`]);

  const loadBgStatus = useCallback(async () => {
    try {
      const res: any = await fetch("/api/search/background").then((r) => r.json());
      if (res?.status === "ERROR") return;
      setBgState(res);
      setBgRunning(Boolean(res?.status === "QUEUED" || (res?.percent ?? 0) < 100));
    } catch {
      // ignore
    }
  }, []);

  const handleStartBg = async () => {
    try {
      const res: any = await fetch("/api/search/background", { method: "POST" }).then((r) => r.json());
      if (res?.status === "QUEUED" || res?.status === "SUCCESS") {
        setBgRunning(true);
        pushLog("Búsqueda autónoma en segundo plano activada. SQX ejecutando en background.");
      }
      loadBgStatus();
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadBgStatus();
    bgPollRef.current = setInterval(loadBgStatus, 8000);
    return () => {
      if (bgPollRef.current) clearInterval(bgPollRef.current);
    };
  }, [loadBgStatus]);

  const loadSavedConfigs = useCallback(async () => {
    try {
      const list = await api.listSearchConfigs();
      setSavedConfigs(Array.isArray(list) ? list : []);
    } catch {
      setSavedConfigs([]);
    }
  }, []);

  useEffect(() => {
    loadSavedConfigs();
  }, [loadSavedConfigs]);

  const handleSaveConfig = async () => {
    setCfgLoading(true);
    setCfgFeedback(null);
    try {
      const name = cfgName.trim() || `Config ${new Date().toLocaleTimeString()}`;
      const payload: any = {
        name,
        mode: cfgMode,
        project: cfgProject.trim() || DEFAULT_SEARCH.project,
        databank: cfgDatabank.trim() || DEFAULT_SEARCH.databank,
        symbol: cfgSymbol.trim(),
        interval: cfgInterval.trim(),
        population: cfgPopulation,
        techniques: cfgTechniques.trim() ? cfgTechniques.split(",").map((s) => s.trim()).filter(Boolean) : [],
      };
      if (cfgMode === "ultra") {
        payload.target_multiplier = cfgTargetMultiplier;
      } else {
        payload.max_drawdown_pct = cfgMaxDrawdownPct;
        payload.consistency_target = cfgConsistencyTarget;
      }
      const res = await api.createSearchConfig(payload);
      setCfgFeedback(`Configuración guardada exitosamente: ${res.configId ?? res.name ?? name}`);
      await loadSavedConfigs();
    } catch (err: any) {
      setCfgFeedback(`Error al guardar: ${err.message || "Fallo en backend"}`);
    } finally {
      setCfgLoading(false);
    }
  };

  const handleRunSaved = async (configId: string) => {
    setCfgLoading(true);
    setCfgFeedback(null);
    try {
      const res = await api.runSearchConfig(configId);
      setCfgFeedback(`Búsqueda iniciada en SQX: estado ${res.status ?? "QUEUED"} — ID ${configId}`);
      pushLog(`Búsqueda lanzada en SQX con config ${configId}`);
    } catch (err: any) {
      setCfgFeedback(`Error al ejecutar: ${err.message || "Fallo en conexión con SQX"}`);
    } finally {
      setCfgLoading(false);
    }
  };

  const loadInitial = useCallback(async (overrideMode?: "ultra" | "fondeo") => {
    const activeMode = overrideMode || cfgMode;
    setLoading(true);
    try {
      const statusRes = await api.getSQXStatus();
      setSqxStatus(statusRes);
      pushLog(`Estado Servidor SQX MCP: ${statusRes.status || "DESCONOCIDO"}`);

      const rentList = await api.getSQXRentable(20, activeMode);
      setRentable(Array.isArray(rentList) ? rentList : []);

      const candList = await api.getSQXCandidates(activeMode);
      setSqxCandidates(Array.isArray(candList) ? candList : []);

      setError(null);
    } catch (err: any) {
      setError(err.message || "No se pudo conectar con la API de StrategyQuant X");
      pushLog(`Error de conexión: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [cfgMode]);

  useEffect(() => {
    loadInitial();
  }, [loadInitial]);

  const handleModeChange = (mode: "ultra" | "fondeo") => {
    setCfgMode(mode);
    loadInitial(mode);
  };

  return (
    <div className="page-container stagger" style={{ maxWidth: 1280, margin: "0 auto", padding: "24px 16px" }}>
      {/* STEP INDICATOR HEADER */}
      <div className="card animate-in" style={{ padding: 20, marginBottom: 24, background: "var(--bg-2)", border: "1px solid var(--border)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 8, background: "rgba(59, 130, 246, 0.12)", color: "#60a5fa", padding: "4px 10px", borderRadius: 4, fontSize: 11, fontWeight: 800, fontFamily: "monospace", letterSpacing: "0.5px" }}>
              <span>PASO 1 DE 3</span>
              <span>•</span>
              <span>MOTOR DE BÚSQUEDA GENÉTICA SQX</span>
            </div>
            <h1 style={{ fontSize: 24, fontWeight: 800, margin: "10px 0 4px 0", color: "var(--text-primary)", letterSpacing: "-0.5px" }}>
              Buscador Remoto de Estrategias — StrategyQuant X
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: 13, margin: 0, maxWidth: 840 }}>
              Generación y filtrado de candidatos en tiempo real vía conexión directa con la instancia de StrategyQuant X. Todos los resultados provienen exclusivamente de ejecuciones reales sin datos simulados ni hardcodeados.
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <button
              onClick={() => loadInitial()}
              className="btn btn-secondary"
              style={{ fontSize: 12, padding: "8px 14px", fontWeight: 700 }}
            >
              [RECARGAR DATOS]
            </button>
            <Link
              href="/strategyquant"
              className="btn btn-primary"
              style={{ textDecoration: "none", fontSize: 12, padding: "8px 14px", fontWeight: 700 }}
            >
              [VER CONEXIÓN SQX MCP]
            </Link>
          </div>
        </div>

        {/* STATUS BAR */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginTop: 18, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
          <div style={{ padding: 12, borderRadius: 6, background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Estado Servidor SQX</div>
            <div style={{ fontSize: 14, fontWeight: 800, color: sqxStatus?.status === "ONLINE" ? "var(--success)" : "var(--danger)", marginTop: 4, fontFamily: "monospace" }}>
              {sqxStatus?.status === "ONLINE" ? "ONLINE (Puerto 8080)" : "OFFLINE / Desconectado"}
            </div>
          </div>

          <div style={{ padding: 12, borderRadius: 6, background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Búsqueda en Segundo Plano</div>
            <div style={{ fontSize: 14, fontWeight: 800, color: bgRunning ? "var(--warning)" : "var(--text-primary)", marginTop: 4, fontFamily: "monospace" }}>
              {bgRunning ? `EN EJECUCIÓN (${bgState.percent ?? 0}%)` : "INACTIVA / Esperando Lanzamiento"}
            </div>
          </div>

          <div style={{ padding: 12, borderRadius: 6, background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Estrategias Aprobadas (Gates)</div>
            <div style={{ fontSize: 14, fontWeight: 800, color: rentable.length > 0 ? "var(--success)" : "var(--text-muted)", marginTop: 4, fontFamily: "monospace" }}>
              {rentable.length} Estrategias Pasadas ({cfgMode.toUpperCase()})
            </div>
          </div>

          <div style={{ padding: 12, borderRadius: 6, background: "rgba(0,0,0,0.3)", border: "1px solid var(--border)" }}>
            <div style={{ fontSize: 10, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>Candidatos Brutos Ingeridos</div>
            <div style={{ fontSize: 14, fontWeight: 800, color: "var(--text-primary)", marginTop: 4, fontFamily: "monospace" }}>
              {sqxCandidates.length} Candidatos en BD
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div style={{ padding: 14, background: "rgba(239, 68, 68, 0.12)", border: "1px solid var(--danger)", color: "#fca5a5", borderRadius: 6, marginBottom: 24, fontSize: 13 }}>
          <strong>Error de Operación:</strong> {error}
        </div>
      )}

      {/* SEARCH CONFIGURATOR & CONTROL PANEL */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: 24, marginBottom: 24 }}>
        {/* PANEL 1: CONFIGURADOR IA */}
        <div className="card animate-in" style={{ padding: 20, background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8 }}>
          <div style={{ borderBottom: "1px solid var(--border)", paddingBottom: 12, marginBottom: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: "var(--accent)", textTransform: "uppercase", fontFamily: "monospace" }}>CONFIGURADOR ASISTIDO</div>
            <h2 style={{ fontSize: 16, fontWeight: 800, margin: "4px 0 0 0" }}>Parámetros de Búsqueda Genética</h2>
          </div>

          {/* Mode selector */}
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <button
              onClick={() => handleModeChange("ultra")}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: 6,
                border: cfgMode === "ultra" ? "2px solid var(--accent)" : "1px solid var(--border)",
                background: cfgMode === "ultra" ? "var(--accent-dim)" : "transparent",
                color: cfgMode === "ultra" ? "var(--accent)" : "var(--text-muted)",
                fontSize: 12,
                fontWeight: 800,
                cursor: "pointer",
              }}
            >
              MODO ULTRARENTABLE (Capital Propio)
            </button>
            <button
              onClick={() => handleModeChange("fondeo")}
              style={{
                flex: 1,
                padding: "8px 12px",
                borderRadius: 6,
                border: cfgMode === "fondeo" ? "2px solid #60a5fa" : "1px solid var(--border)",
                background: cfgMode === "fondeo" ? "rgba(96, 165, 250, 0.15)" : "transparent",
                color: cfgMode === "fondeo" ? "#60a5fa" : "var(--text-muted)",
                fontSize: 12,
                fontWeight: 800,
                cursor: "pointer",
              }}
            >
              MODO FONDEO (Prop Firms)
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Field label="Nombre Configuración" value={cfgName} onChange={setCfgName} placeholder="ej. Kamikaze BTC H1 2026" />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Field label="Símbolo Activo" value={cfgSymbol} onChange={setCfgSymbol} placeholder="BTC-USDT" />
              <Field label="Timeframe" value={cfgInterval} onChange={setCfgInterval} placeholder="1h" />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Field label="Proyecto SQX" value={cfgProject} onChange={setCfgProject} placeholder="Ultra_Auto_Pilot" />
              <Field label="Databank SQX" value={cfgDatabank} onChange={setCfgDatabank} placeholder="Results" />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Field label="Población por Isla" type="number" value={String(cfgPopulation)} onChange={(v) => setCfgPopulation(Number(v) || 24)} />
              {cfgMode === "ultra" ? (
                <Field label="Target Retorno (% / Mult)" type="number" value={String(cfgTargetMultiplier)} onChange={(v) => setCfgTargetMultiplier(Number(v) || 1000)} />
              ) : (
                <Field label="Máx Drawdown Permitido (%)" type="number" value={String(cfgMaxDrawdownPct)} onChange={(v) => setCfgMaxDrawdownPct(Number(v) || 15)} />
              )}
            </div>

            <Field label="Técnicas SQX (comas)" value={cfgTechniques} onChange={setCfgTechniques} placeholder="Momentum, Breakout, ATR_Filter" />

            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button
                onClick={handleSaveConfig}
                disabled={cfgLoading}
                className="btn btn-secondary"
                style={{ flex: 1, fontSize: 12, fontWeight: 700 }}
              >
                {cfgLoading ? "Guardando..." : "[GUARDAR CONFIG]"}
              </button>
              <button
                onClick={handleStartBg}
                disabled={bgRunning}
                className="btn btn-primary"
                style={{ flex: 1, fontSize: 12, fontWeight: 700 }}
              >
                {bgRunning ? "Buscando..." : "[LANZAR BÚSQUEDA BACKGROUND]"}
              </button>
            </div>

            {cfgFeedback && (
              <div style={{ fontSize: 11, color: "var(--accent)", fontFamily: "monospace", marginTop: 4 }}>
                {cfgFeedback}
              </div>
            )}
          </div>
        </div>

        {/* PANEL 2: TELEMETRÍA Y LOGS EN VIVO */}
        <div className="card animate-in" style={{ padding: 20, background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, display: "flex", flexDirection: "column" }}>
          <div style={{ borderBottom: "1px solid var(--border)", paddingBottom: 12, marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>TELEMETRÍA EN TIEMPO REAL</div>
              <h2 style={{ fontSize: 16, fontWeight: 800, margin: "4px 0 0 0" }}>Registro de Actividad y Progreso</h2>
            </div>
            {bgState.percent !== undefined && (
              <div style={{ fontSize: 12, fontWeight: 800, fontFamily: "monospace", color: "var(--accent)" }}>
                {bgState.percent}% PROGRESO
              </div>
            )}
          </div>

          {/* Progress bar */}
          <div style={{ width: "100%", height: 6, background: "rgba(255,255,255,0.06)", borderRadius: 3, overflow: "hidden", marginBottom: 16 }}>
            <div
              style={{
                width: `${bgState.percent ?? 0}%`,
                height: "100%",
                background: "var(--accent)",
                transition: "width 300ms ease-in-out",
              }}
            />
          </div>

          {/* Log terminal output */}
          <div
            style={{
              flex: 1,
              minHeight: 220,
              maxHeight: 320,
              background: "#080c14",
              border: "1px solid var(--border)",
              borderRadius: 6,
              padding: 12,
              fontFamily: "monospace",
              fontSize: 11,
              color: "#94a3b8",
              overflowY: "auto",
              whiteSpace: "pre-wrap",
            }}
          >
            {searchLog.length > 0 ? (
              searchLog.map((line, idx) => (
                <div key={idx} style={{ marginBottom: 4 }}>
                  {line}
                </div>
              ))
            ) : (
              <div style={{ color: "var(--text-muted)" }}>
                [SISTEMA LISTO] Esperando inicio de búsqueda. Selecciona la configuración y pulsa [LANZAR BÚSQUEDA BACKGROUND].
              </div>
            )}
          </div>

          {/* Saved configs list */}
          {savedConfigs.length > 0 && (
            <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
              <div style={{ fontSize: 10, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 8, fontFamily: "monospace" }}>
                CONFIGURACIONES GUARDADAS ({savedConfigs.length})
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 120, overflowY: "auto" }}>
                {savedConfigs.map((cfg: any, i: number) => (
                  <div key={cfg.id || i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 10px", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 4 }}>
                    <div style={{ fontSize: 11, fontWeight: 700 }}>
                      {cfg.name} <span style={{ color: "var(--text-muted)", fontSize: 10 }}>({cfg.mode})</span>
                    </div>
                    <button
                      onClick={() => handleRunSaved(cfg.id)}
                      style={{ fontSize: 10, fontWeight: 800, padding: "2px 8px", background: "var(--accent-dim)", border: "1px solid var(--accent)", color: "var(--accent)", borderRadius: 3, cursor: "pointer" }}
                    >
                      EJECUTAR
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* REAL STRATEGIES TABLE (ZERO MOCKS) */}
      <div className="card animate-in" style={{ padding: 20, background: "var(--bg-panel)", border: "1px solid var(--border)", borderRadius: 8, marginBottom: 24 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--border)", paddingBottom: 12, marginBottom: 16, flexWrap: "wrap", gap: 12 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>AUDITORÍA DE CANDIDATOS PASADOS</div>
            <h2 style={{ fontSize: 18, fontWeight: 800, margin: "4px 0 0 0" }}>
              Estrategias Aprobadas por Quality Gates (Modo {cfgMode.toUpperCase()})
            </h2>
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "monospace" }}>
            Filtro: {cfgMode === "ultra" ? "Ruina Real (DD >= 100%) descarta" : "DD Intradía <= 15% + Calmar >= 0.5"}
          </div>
        </div>

        {loading ? (
          <div style={{ padding: 24, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
            Cargando estrategias verificadas desde la base de datos sqlite3...
          </div>
        ) : rentable.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, textAlign: "left" }}>
              <thead>
                <tr style={{ background: "var(--bg-2)", borderBottom: "1px solid var(--border)", color: "var(--text-muted)", fontSize: 10, textTransform: "uppercase", fontFamily: "monospace" }}>
                  <th style={{ padding: "10px 12px" }}>Estrategia ID</th>
                  <th style={{ padding: "10px 12px" }}>Símbolo</th>
                  <th style={{ padding: "10px 12px" }}>Retorno IS</th>
                  <th style={{ padding: "10px 12px" }}>Retorno OOS</th>
                  <th style={{ padding: "10px 12px" }}>Max DD IS</th>
                  <th style={{ padding: "10px 12px" }}>Profit Factor</th>
                  <th style={{ padding: "10px 12px" }}>Trades</th>
                  <th style={{ padding: "10px 12px" }}>Estado Gate</th>
                  <th style={{ padding: "10px 12px", textAlign: "right" }}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {rentable.map((s: any, idx: number) => (
                  <tr key={s.strategyId || idx} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 12px", fontWeight: 700, fontFamily: "monospace" }}>{s.name || s.strategyId}</td>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace" }}>{s.symbol || "BTC-USDT"} ({s.interval || "1h"})</td>
                    <td style={{ padding: "10px 12px", color: "var(--success)", fontWeight: 700, fontFamily: "monospace" }}>
                      +{fmt(s.netReturnPct)}%
                    </td>
                    <td style={{ padding: "10px 12px", color: "var(--success)", fontWeight: 700, fontFamily: "monospace" }}>
                      +{fmt(s.netReturnOosPct)}%
                    </td>
                    <td style={{ padding: "10px 12px", color: Number(s.maxDrawdownPct) > 40 ? "var(--warning)" : "var(--text-primary)", fontFamily: "monospace" }}>
                      {fmt(s.maxDrawdownPct)}%
                    </td>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace" }}>{fmt(s.profitFactor)}</td>
                    <td style={{ padding: "10px 12px", fontFamily: "monospace" }}>{s.tradesCount || 0}</td>
                    <td style={{ padding: "10px 12px" }}>
                      <span style={{ fontSize: 10, fontWeight: 800, padding: "2px 6px", borderRadius: 3, background: "rgba(16, 185, 129, 0.15)", color: "var(--success)" }}>
                        APROBADO
                      </span>
                    </td>
                    <td style={{ padding: "10px 12px", textAlign: "right" }}>
                      <Link href={`/strategies?id=${s.strategyId}`} className="btn btn-sm btn-secondary" style={{ textDecoration: "none", fontSize: 11 }}>
                        Ver Ficha
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: 32, textAlign: "center", background: "var(--bg-2)", borderRadius: 6, border: "1px dashed var(--border)" }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
              0 Estrategias Aprobadas en este Momento ({cfgMode.toUpperCase()})
            </div>
            <div style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 640, margin: "0 auto 16px auto" }}>
              Ningún candidato almacenado supera actualmente los criterios estrictos del Quality Gate. La búsqueda en segundo plano en StrategyQuant X está activa generando y evaluando nuevas generaciones genéticas.
            </div>
            <button onClick={handleStartBg} className="btn btn-primary" style={{ fontSize: 12, fontWeight: 700 }}>
              [ACTIVAR MOTOR BÚSQUEDA SEGUNDO PLANO]
            </button>
          </div>
        )}
      </div>

      {/* STEP-BY-STEP PIPELINE BANNER AT BOTTOM */}
      <div className="card animate-in" style={{ padding: 20, background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 8, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 800, color: "var(--text-muted)", textTransform: "uppercase", fontFamily: "monospace" }}>PASO 2: BIFURCACIÓN DE OBJETIVO</div>
          <div style={{ fontSize: 15, fontWeight: 800, color: "var(--text-primary)", marginTop: 2 }}>
            ¿Qué deseas hacer con las estrategias descubiertas?
          </div>
          <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
            Selecciona el canal de despliegue según tu objetivo de capital y tolerancia al riesgo.
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link href="/fondeo" className="btn btn-secondary" style={{ textDecoration: "none", fontSize: 12, fontWeight: 800 }}>
            [PASO 2A] MODO FONDEO (PROP FIRMS) →
          </Link>
          <Link href="/ultra" className="btn btn-primary" style={{ textDecoration: "none", fontSize: 12, fontWeight: 800 }}>
            [PASO 2B] MODO ULTRARENTABLE (BINGX) →
          </Link>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, placeholder, type = "text" }: { label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 800, fontFamily: "monospace" }}>{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          padding: "8px 10px",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border)",
          background: "var(--bg-panel)",
          color: "var(--text-primary)",
          fontSize: 12,
          fontWeight: 600,
          outline: "none",
          fontFamily: "monospace",
        }}
      />
    </label>
  );
}

function fmt(n: number | string | undefined | null): string {
  if (n === null || n === undefined) return "---";
  const num = typeof n === "string" ? parseFloat(n) : n;
  return isNaN(num) ? "---" : num.toFixed(2);
}
