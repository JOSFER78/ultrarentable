"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Activity,
  ShieldCheck,
  RotateCcw,
  Cpu,
  Server,
  Zap,
  Terminal,
  CheckCircle2,
  AlertCircle,
  Monitor,
} from "lucide-react";

import { getM1Salud, SaludM1Response, getVigiaLocal, VigiaLocalResponse } from "@/lib/api";

interface WorkerData {
  worker_id: string;
  name: string;
  status: string;
  last_heartbeat_utc: string;
  heartbeat_age_seconds: number;
  restart_count: number;
  jobs_processed: number;
  last_error: string | null;
  is_healthy: boolean;
}

interface TelemetryHealth {
  overall_status: string;
  supervisor_active: boolean;
  total_workers: number;
  healthy_workers: number;
  timestamp_utc: string;
  watchdog: {
    is_running: boolean;
    last_check: string | null;
    failover_active: boolean;
    recent_recoveries_count: number;
  };
  workers: WorkerData[] | Record<string, WorkerData>;
}

export default function SistemaTelemetryPage() {
  // 1. Estado de supervisión M1 del servidor real (/api/v2/m1/salud)
  const [saludM1, setSaludM1] = useState<SaludM1Response | null>(null);
  const [saludM1Loading, setSaludM1Loading] = useState<boolean>(true);
  const [saludM1Error, setSaludM1Error] = useState<string | null>(null);

  // 2. Estado de telemetría del vigía local (este PC) (/api/v2/system/vigia-local)
  const [vigiaLocal, setVigiaLocal] = useState<VigiaLocalResponse | null>(null);
  const [vigiaLocalLoading, setVigiaLocalLoading] = useState<boolean>(true);
  const [vigiaLocalError, setVigiaLocalError] = useState<string | null>(null);

  // 3. Estado de telemetría de workers
  const [telemetry, setTelemetry] = useState<TelemetryHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [logs, setLogs] = useState<Array<{ ts: string; level: string; msg: string }>>([]);
  const [restarting, setRestarting] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchSaludM1 = useCallback(async () => {
    try {
      const json = await getM1Salud();
      setSaludM1(json);
      setSaludM1Error(null);
    } catch (e: any) {
      setSaludM1(null);
      setSaludM1Error(e.message || "El servicio no responde ahora mismo. Se está reintentando solo.");
    } finally {
      setSaludM1Loading(false);
    }
  }, []);

  const fetchVigiaLocal = useCallback(async () => {
    try {
      const data = await getVigiaLocal();
      setVigiaLocal(data);
      setVigiaLocalError(null);
    } catch (err: any) {
      setVigiaLocal(null);
      setVigiaLocalError(err.message || "No se pudo consultar el vigía local");
    } finally {
      setVigiaLocalLoading(false);
    }
  }, []);

  const workerList: WorkerData[] = React.useMemo(() => {
    if (!telemetry?.workers) return [];
    if (Array.isArray(telemetry.workers)) return telemetry.workers;
    const map = new Map<string, WorkerData>();
    Object.values(telemetry.workers).forEach((w) => {
      if (w && typeof w === "object" && "worker_id" in w && w.worker_id) {
        map.set(w.worker_id, w);
      }
    });
    return Array.from(map.values());
  }, [telemetry]);

  async function fetchHealth() {
    try {
      const res = await fetch("/api/v1/telemetry/health");
      if (res.ok) {
        const data: TelemetryHealth = await res.json();
        setTelemetry(data);
        setLastUpdated(new Date().toLocaleTimeString());

        setLogs((prev) => [
          {
            ts: new Date().toLocaleTimeString(),
            level: data.overall_status === "HEALTHY" ? "INFO" : "WARN",
            msg: `Supervisor check: ${data.healthy_workers}/${data.total_workers} workers healthy. HAWatchdog running: ${data.watchdog?.is_running}`,
          },
          ...prev.slice(0, 24),
        ]);
      }
    } catch {
      // Ignored if offline
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchSaludM1();
    void fetchVigiaLocal();
    void fetchHealth();

    const m1Interval = setInterval(fetchSaludM1, 15000);
    const vigiaInterval = setInterval(fetchVigiaLocal, 10000);
    const healthInterval = setInterval(fetchHealth, 3000);

    return () => {
      clearInterval(m1Interval);
      clearInterval(vigiaInterval);
      clearInterval(healthInterval);
    };
  }, [fetchSaludM1, fetchVigiaLocal]);

  async function handleRestartAll() {
    setRestarting(true);
    try {
      await fetch("/api/v1/telemetry/supervisor/restart-all", { method: "POST" });
      await fetchHealth();
    } catch (e) {
      console.error(e);
    } finally {
      setRestarting(false);
    }
  }

  return (
    <div className="w-full space-y-3 font-sans pb-8">
      {/* Header */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)]">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg md:text-xl font-bold text-[var(--text-1)] tracking-tight">
                Telemetría & Pulso Autónomo 24/7 (SystemSupervisor)
              </h1>
              <p className="text-[var(--text-2)] text-xs mt-0.5">
                Supervisión de piezas del servidor M1, workers concurrentes, daemons autónomos y auto-recuperación local.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 font-mono">
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-[var(--surface-2)] text-[var(--profit)] border border-[var(--border)]">
            <span className="w-2 h-2 rounded-full bg-[var(--profit)] mr-2 animate-pulse"></span>
            PULSO ACTIVO {lastUpdated || "24/7"}
          </span>
          <button
            onClick={handleRestartAll}
            disabled={restarting}
            className="inline-flex items-center px-3 py-1 rounded-md text-xs font-semibold bg-[var(--surface-3)] hover:bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border-strong)] transition cursor-pointer"
          >
            <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${restarting ? "animate-spin text-[var(--text-2)]" : "text-[var(--text-2)]"}`} />
            Reiniciar Enjambre
          </button>
        </div>
      </div>

      {/* BLOQUE EXIGIDO: ¿Está todo funcionando? (Medición real de /api/v2/m1/salud) */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-[var(--text-2)]" />
            <h2 className="text-base font-bold text-[var(--text-1)] tracking-tight">
              ¿Está todo funcionando?
            </h2>
            {saludM1 && (
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                  saludM1.todo_en_pie
                    ? "bg-[var(--profit)]/15 text-[var(--profit)] border border-[var(--profit)]/30"
                    : "bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)]"
                }`}
              >
                {saludM1.todo_en_pie ? "TODO EN PIE" : "FALLO EN PIEZAS"}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-3)]">
            {saludM1?.medido && (
              <span>Medido por el supervisor: {saludM1.medido.replace("T", " ").slice(0, 19)} UTC</span>
            )}
            <button
              onClick={() => void fetchSaludM1()}
              disabled={saludM1Loading}
              className="px-2.5 py-1 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer flex items-center gap-1 text-[11px]"
            >
              <RotateCcw className={`w-3 h-3 ${saludM1Loading ? "animate-spin" : ""}`} />
              <span>Refrescar</span>
            </button>
          </div>
        </div>

        {saludM1Loading && !saludM1 && (
          <div className="py-6 text-center text-xs font-mono text-[var(--text-3)]">
            Consultando telemetría del servidor M1 (/api/v2/m1/salud)…
          </div>
        )}

        {saludM1Error && !saludM1 && (
          <div className="px-3.5 py-3 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] text-xs font-mono flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--text-3)] shrink-0 animate-pulse" />
              <span>El endpoint /api/v2/m1/salud no responde ({saludM1Error}). Se está reintentando solo.</span>
            </div>
            <button
              onClick={() => void fetchSaludM1()}
              className="px-2.5 py-1 rounded bg-[var(--surface-3)] hover:bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-1)] text-xs font-semibold cursor-pointer transition"
            >
              Reintentar ahora
            </button>
          </div>
        )}

        {saludM1 && saludM1.piezas && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.entries(saludM1.piezas).map(([key, p]) => (
              <div
                key={key}
                className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/40 space-y-1.5 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs font-bold uppercase text-[var(--text-1)] truncate">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span
                      className={`w-2 h-2 rounded-full shrink-0 ${
                        p.ok ? "bg-[var(--profit)]" : "bg-[var(--loss)]"
                      }`}
                      title={p.ok ? "OK" : "Fallo"}
                    />
                  </div>
                  {p.descripcion && (
                    <p className="text-[11px] text-[var(--text-3)] leading-snug line-clamp-2 mt-1">
                      {p.descripcion}
                    </p>
                  )}
                </div>
                <div className="pt-2 border-t border-[var(--border)]/60 font-mono text-[11px] text-[var(--text-2)] truncate font-semibold">
                  {p.detalle}
                </div>
              </div>
            ))}
          </div>
        )}

        {saludM1?.origen && (
          <div className="text-[10px] font-mono text-[var(--text-3)] flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-[var(--border)]/40">
            <span>Origen telemetría: <code className="text-[var(--text-2)]">{saludM1.origen}</code></span>
            {saludM1.ultimas_acciones && saludM1.ultimas_acciones.length > 0 && (
              <span>
                Última acción: <strong className="text-[var(--text-1)]">{saludM1.ultimas_acciones[0].que}</strong> ({saludM1.ultimas_acciones[0].cuando.replace("T", " ").slice(0, 19)} UTC, rc={saludM1.ultimas_acciones[0].rc})
              </span>
            )}
          </div>
        )}
      </div>

      {/* BLOQUE A30: Instancia local (este PC) */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-4 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
          <div className="flex items-center gap-2">
            <Monitor className="w-5 h-5 text-[var(--text-2)]" />
            <h2 className="text-base font-bold text-[var(--text-1)] tracking-tight">
              Instancia local (este PC)
            </h2>
            {vigiaLocal && vigiaLocal.disponible && (
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-mono font-bold ${
                  vigiaLocal.todo_en_pie &&
                  (!vigiaLocal.medido ||
                    Math.floor((Date.now() - new Date(vigiaLocal.medido).getTime()) / 60000) <= 10)
                    ? "bg-[var(--profit)]/15 text-[var(--profit)] border border-[var(--profit)]/30"
                    : "bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)]"
                }`}
              >
                {vigiaLocal.todo_en_pie &&
                (!vigiaLocal.medido ||
                  Math.floor((Date.now() - new Date(vigiaLocal.medido).getTime()) / 60000) <= 10)
                  ? "TODO EN PIE"
                  : "INCIDENCIA"}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-3)]">
            <span>Medida en vivo del demonio (en el momento)</span>
            <button
              onClick={() => void fetchVigiaLocal()}
              disabled={vigiaLocalLoading}
              className="px-2.5 py-1 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)] transition cursor-pointer flex items-center gap-1 text-[11px]"
            >
              <RotateCcw className={`w-3 h-3 ${vigiaLocalLoading ? "animate-spin" : ""}`} />
              <span>Refrescar</span>
            </button>
          </div>
        </div>

        {vigiaLocalLoading && !vigiaLocal && (
          <div className="py-6 text-center text-xs font-mono text-[var(--text-3)]">
            Consultando estado del demonio local (/api/v2/system/vigia-local)…
          </div>
        )}

        {vigiaLocalError && !vigiaLocal && (
          <div className="px-3.5 py-3 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] text-xs font-mono flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--loss)] shrink-0" />
              <span>No se pudo conectar con el demonio local ({vigiaLocalError}).</span>
            </div>
            <button
              onClick={() => void fetchVigiaLocal()}
              className="px-2.5 py-1 rounded bg-[var(--surface-3)] hover:bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-1)] text-xs font-semibold cursor-pointer transition"
            >
              Reintentar
            </button>
          </div>
        )}

        {vigiaLocal && !vigiaLocal.disponible && (
          <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/40 text-xs font-mono text-[var(--text-2)]">
            Telemetría local no disponible: {vigiaLocal.motivo || "Demonio local no responde"}
          </div>
        )}

        {vigiaLocal && vigiaLocal.disponible && (
          <div className="space-y-3">
            {/* Grid de servicios locales: API, Web y Build */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {/* API 8100 */}
              <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/40 flex flex-col justify-between space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[var(--text-1)]">
                    API FastAPI (:{vigiaLocal.api?.puerto || 8100})
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10.5px] font-mono font-bold ${
                      vigiaLocal.api?.ok
                        ? "bg-[var(--profit)]/15 text-[var(--profit)]"
                        : "bg-[var(--loss-dim)] text-[var(--loss)]"
                    }`}
                  >
                    {vigiaLocal.api?.ok ? "EN PIE" : "CAÍDA"}
                  </span>
                </div>
                <div className="pt-2 border-t border-[var(--border)]/60 flex items-center justify-between font-mono text-[11px] text-[var(--text-2)]">
                  <span>Código HTTP:</span>
                  <span className="font-semibold text-[var(--text-1)]">
                    {vigiaLocal.api?.http ? `HTTP ${vigiaLocal.api.http}` : "Sin respuesta"}
                  </span>
                </div>
              </div>

              {/* Web 3100 */}
              <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/40 flex flex-col justify-between space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[var(--text-1)]">
                    Web Next.js (:{vigiaLocal.web?.puerto || 3100})
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10.5px] font-mono font-bold ${
                      vigiaLocal.web?.ok
                        ? "bg-[var(--profit)]/15 text-[var(--profit)]"
                        : "bg-[var(--loss-dim)] text-[var(--loss)]"
                    }`}
                  >
                    {vigiaLocal.web?.ok ? "EN PIE" : "CAÍDA"}
                  </span>
                </div>
                <div className="pt-2 border-t border-[var(--border)]/60 flex items-center justify-between font-mono text-[11px] text-[var(--text-2)]">
                  <span>Código HTTP:</span>
                  <span className="font-semibold text-[var(--text-1)]">
                    {vigiaLocal.web?.http ? `HTTP ${vigiaLocal.web.http}` : "Sin respuesta"}
                  </span>
                </div>
              </div>

              {/* Build Integro */}
              <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/40 flex flex-col justify-between space-y-2 sm:col-span-2 lg:col-span-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[var(--text-1)]">
                    Build de Producción
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10.5px] font-mono font-bold ${
                      vigiaLocal.build_integro
                        ? "bg-[var(--profit)]/15 text-[var(--profit)]"
                        : "bg-[var(--loss-dim)] text-[var(--loss)]"
                    }`}
                  >
                    {vigiaLocal.build_integro ? "ÍNTEGRO" : "INCOMPLETO"}
                  </span>
                </div>
                <div className="pt-2 border-t border-[var(--border)]/60 text-[11px] text-[var(--text-2)] font-mono">
                  {vigiaLocal.build_integro
                    ? "Manifiestos verificados en disco"
                    : "El build de producción está incompleto"}
                </div>
              </div>
            </div>

            {/* Acciones del vigía */}
            <div className="p-3 rounded-lg border border-[var(--border)] bg-[var(--surface-2)]/20 text-xs">
              <span className="font-mono font-semibold text-[var(--text-2)] mr-2">
                Intervención del vigía:
              </span>
              {vigiaLocal.acciones && vigiaLocal.acciones.length > 0 ? (
                <ul className="mt-1.5 space-y-1">
                  {vigiaLocal.acciones.map((acc, i) => {
                    let desc = `El vigía ejecutó la acción: ${acc}`;
                    if (acc === "arrancar-api") desc = "el vigía tuvo que relanzar la API (:8100)";
                    if (acc === "arrancar-web") desc = "el vigía tuvo que relanzar la web (:3100)";
                    if (acc === "reconstruir-web") desc = "el vigía tuvo que reconstruir el build, estaba a medias";
                    return (
                      <li key={i} className="text-[var(--text-1)] font-mono flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-2)]" />
                        {desc}
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <span className="text-[var(--text-3)] font-mono">
                  no ha hecho falta resucitar nada; todo en pie.
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Tri-Daemon Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {/* Daemon 1 */}
        <div className="p-4 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-2 hover:border-[var(--border-strong)] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-[var(--text-2)] flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              1. CONTINUOUS RESEARCH
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]">
              24/7 ACTIVO
            </span>
          </div>
          <h3 className="text-xs font-bold text-[var(--text-1)]">Laboratorio de Mutación & Debate AST</h3>
          <p className="text-[11px] text-[var(--text-2)] leading-relaxed">
            Escanea candidatos rechazados, ejecuta el debate de 8 roles bajo Blind Scope y sintetiza mutaciones de StrategyDSL.
          </p>
          <div className="text-[10.5px] font-mono text-[var(--text-3)] pt-2 flex justify-between border-t border-[var(--border)]">
            <span>Frecuencia: 30s</span>
            <span className="text-[var(--text-1)] font-semibold">Auto-Reparación ON</span>
          </div>
        </div>

        {/* Daemon 2 */}
        <div className="p-4 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-2 hover:border-[var(--border-strong)] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-[var(--text-2)] flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" />
              2. AUTONOMOUS META DAEMON
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]">
              24/7 ACTIVO
            </span>
          </div>
          <h3 className="text-xs font-bold text-[var(--text-1)]">Ensamblador de Portafolios Multi-Alpha</h3>
          <p className="text-[11px] text-[var(--text-2)] leading-relaxed">
            Barre estrategias 11/11 en SQLite WAL, calcula matrices de correlación y optimiza la paridad de riesgo (DD &lt; 10%).
          </p>
          <div className="text-[10.5px] font-mono text-[var(--text-3)] pt-2 flex justify-between border-t border-[var(--border)]">
            <span>Frecuencia: 60s</span>
            <span className="text-[var(--text-1)] font-semibold">Risk-Parity ON</span>
          </div>
        </div>

        {/* Daemon 3 */}
        <div className="p-4 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-2 hover:border-[var(--border-strong)] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-[var(--profit)] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              3. HIGH AVAILABILITY WATCHDOG
            </span>
            <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]">
              24/7 ACTIVO
            </span>
          </div>
          <h3 className="text-xs font-bold text-[var(--text-1)]">Supervisor de Falla & SQLite Auto-Recovery</h3>
          <p className="text-[11px] text-[var(--text-2)] leading-relaxed">
            Verifica heartbeats cada 2 segundos. Si un worker muere, reinicia su hilo y efectúa rollback de transacciones SQLite.
          </p>
          <div className="text-[10.5px] font-mono text-[var(--text-3)] pt-2 flex justify-between border-t border-[var(--border)]">
            <span>Timeout Heartbeat: 10s</span>
            <span className="text-[var(--text-1)] font-semibold">Self-Healing ON</span>
          </div>
        </div>
      </div>

      {/* Workers Grid */}
      <div className="space-y-2">
        <h2 className="text-xs font-bold text-[var(--text-1)] uppercase tracking-wider font-mono">
          Pool de Workers de Ejecución (SQX + Local Backtesting)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {workerList.length === 0 ? (
            <div className="col-span-4 p-8 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg text-center text-xs font-mono text-[var(--text-3)]">
              Consultando estado de los workers…
            </div>
          ) : (
            workerList.map((w) => (
              <div
                key={w.worker_id}
                className="p-3 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-[var(--text-1)] truncate">
                    {w.name}
                  </span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[10px] font-mono font-bold ${
                      w.is_healthy
                        ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                        : "bg-[var(--loss-dim)] text-[var(--loss)] border border-[var(--loss)]"
                    }`}
                  >
                    {w.status}
                  </span>
                </div>
                <div className="space-y-1 text-[11px] font-mono text-[var(--text-2)]">
                  <div className="flex justify-between">
                    <span>Trabajos:</span>
                    <span className="text-[var(--text-1)] font-bold">{w.jobs_processed}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Reinicios:</span>
                    <span className="text-[var(--text-1)]">{w.restart_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Último latido:</span>
                    <span className="text-[var(--text-3)]">{w.heartbeat_age_seconds}s atrás</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Live Event Log */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-[var(--text-1)] uppercase tracking-wider font-mono flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5" />
            Registro de Eventos del Supervisor en Vivo
          </h2>
          <span className="text-[11px] font-mono text-[var(--text-3)]">Últimos {logs.length} eventos</span>
        </div>
        <div className="p-3 bg-black/40 border border-[var(--border)] rounded-lg font-mono text-[11px] space-y-1 max-h-48 overflow-y-auto">
          {logs.length === 0 ? (
            <div className="text-[var(--text-3)]">Esperando eventos del supervisor…</div>
          ) : (
            logs.map((l, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-[var(--text-3)] shrink-0">{l.ts}</span>
                <span
                  className={`font-bold shrink-0 ${
                    l.level === "INFO" ? "text-[var(--text-1)]" : "text-[var(--text-3)]"
                  }`}
                >
                  [{l.level}]
                </span>
                <span className="text-[var(--text-2)] break-all">{l.msg}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
