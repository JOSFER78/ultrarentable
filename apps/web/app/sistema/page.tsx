"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  ShieldCheck,
  RotateCcw,
  Cpu,
  Server,
  Zap,
  Terminal,
} from "lucide-react";

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
  const [telemetry, setTelemetry] = useState<TelemetryHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [logs, setLogs] = useState<Array<{ ts: string; level: string; msg: string }>>([]);
  const [restarting, setRestarting] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

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

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 3000);
    return () => clearInterval(interval);
  }, []);

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
    <div className="w-full max-w-[1560px] mx-auto space-y-6 font-sans">
      {/* Header */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-5 md:p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)]">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl md:text-2xl font-black text-[var(--text-1)] tracking-tight">
                Telemetría & Pulso Autónomo 24/7 (SystemSupervisor)
              </h1>
              <p className="text-[var(--text-2)] text-xs md:text-sm mt-0.5 font-medium">
                Supervisión de 8 workers concurrentes, 3 daemons autónomos de fondo y auto-recuperación de SQLite WAL.
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 font-mono">
          <span className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)] shadow-sm">
            <span className="w-2 h-2 rounded-full bg-[var(--profit)] animate-ping mr-2"></span>
            PULSO ACTIVO {lastUpdated || "24/7"}
          </span>
          <button
            onClick={handleRestartAll}
            disabled={restarting}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[var(--bg)] hover:bg-[var(--surface-1)] text-[var(--text-1)] border border-white/[0.1] shadow-sm transition active:scale-95 cursor-pointer"
          >
            <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${restarting ? "animate-spin text-[var(--text-2)]" : "text-[var(--text-2)]"}`} />
            Reiniciar Enjambre
          </button>
        </div>
      </div>

      {/* Tri-Daemon Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Daemon 1 */}
        <div className="p-5 bg-[var(--surface-1)] backdrop-blur-xl rounded-2xl border border-white/[0.08] space-y-2.5 shadow-xl hover:border-white/[0.16] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-[var(--text-2)] flex items-center gap-1.5">
              <Cpu className="w-4 h-4" />
              1. CONTINUOUS RESEARCH
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]">
              24/7 ACTIVO
            </span>
          </div>
          <h3 className="text-sm font-black text-[var(--text-1)]">Laboratorio de Mutación & Debate AST</h3>
          <p className="text-xs text-[var(--text-2)] leading-relaxed">
            Escanea candidatos rechazados, ejecuta el debate de 8 roles bajo Blind Scope y sintetiza mutaciones de StrategyDSL.
          </p>
          <div className="text-[11px] font-mono text-[var(--text-3)] pt-2 flex justify-between border-t border-white/[0.06]">
            <span>Frecuencia: 30s</span>
            <span className="text-[var(--text-1)] font-bold">Auto-Reparación ON</span>
          </div>
        </div>

        {/* Daemon 2 */}
        <div className="p-5 bg-[var(--surface-1)] backdrop-blur-xl rounded-2xl border border-white/[0.08] space-y-2.5 shadow-xl hover:border-white/[0.16] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-[var(--text-2)] flex items-center gap-1.5">
              <Zap className="w-4 h-4" />
              2. AUTONOMOUS META DAEMON
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]">
              24/7 ACTIVO
            </span>
          </div>
          <h3 className="text-sm font-black text-[var(--text-1)]">Ensamblador de Portafolios Multi-Alpha</h3>
          <p className="text-xs text-[var(--text-2)] leading-relaxed">
            Barre estrategias 11/11 en SQLite WAL, calcula matrices de correlación y optimiza la paridad de riesgo (DD &lt; 10%).
          </p>
          <div className="text-[11px] font-mono text-[var(--text-3)] pt-2 flex justify-between border-t border-white/[0.06]">
            <span>Frecuencia: 60s</span>
            <span className="text-[var(--text-1)] font-bold">Risk-Parity ON</span>
          </div>
        </div>

        {/* Daemon 3 */}
        <div className="p-5 bg-[var(--surface-1)] backdrop-blur-xl rounded-2xl border border-white/[0.08] space-y-2.5 shadow-xl hover:border-white/[0.16] transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-[var(--profit)] flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" />
              3. HIGH AVAILABILITY WATCHDOG
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]">
              24/7 ACTIVO
            </span>
          </div>
          <h3 className="text-sm font-black text-[var(--text-1)]">Supervisor de Tolerancia a Caídas</h3>
          <p className="text-xs text-[var(--text-2)] leading-relaxed">
            Rescata jobs huérfanos tras caídas, supervisa el socket de SQX y conmuta automáticamente a FastEngine autónomo.
          </p>
          <div className="text-[11px] font-mono text-[var(--text-3)] pt-2 flex justify-between border-t border-white/[0.06]">
            <span>Heartbeat: 10s</span>
            <span className="text-[var(--profit)] font-bold">Self-Healing ON</span>
          </div>
        </div>
      </div>

      {/* 8 Workers Grid */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl rounded-2xl border border-white/[0.08] p-5 md:p-6 space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-white/[0.08] pb-3.5 gap-2">
          <div>
            <h2 className="text-sm font-black uppercase tracking-wider text-[var(--text-1)] font-mono flex items-center gap-2">
              <Server className="w-4 h-4 text-[var(--text-2)]" />
              Enjambre de 8 Workers Autónomos (SystemSupervisor)
            </h2>
            <p className="text-xs text-[var(--text-2)] mt-0.5">
              Cada worker emite un heartbeat cada 10s. Si un worker se congela &gt;30s, el supervisor lo reinicia automáticamente.
            </p>
          </div>
          <span className="text-xs font-mono font-bold text-[var(--profit)] bg-[var(--bg)] px-3 py-1 rounded-xl border border-white/[0.08] self-start sm:self-auto">
            {telemetry?.healthy_workers || 8} / {telemetry?.total_workers || 8} ONLINE
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {workerList.length === 0 ? (
            <div className="col-span-full p-8 text-center text-xs font-mono text-[var(--text-3)] bg-[var(--bg)] rounded-xl border border-white/[0.08]">
              {loading ? "Cargando telemetría de workers..." : "SIN DATOS / NO EVIDENCE DE WORKERS"}
            </div>
          ) : (
            workerList.map((w) => (
              <div
                key={w.worker_id}
                className="p-4 bg-[var(--bg)] rounded-xl border border-white/[0.08] space-y-2 hover:border-white/[0.18] transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="w-2 h-2 rounded-full bg-[var(--profit)] animate-pulse"></span>
                  <span className="text-[10px] font-mono font-bold text-[var(--text-2)] uppercase">
                    {w.status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-[var(--text-1)] line-clamp-1">{w.name}</h4>
                <div className="text-[11px] font-mono text-[var(--text-2)] space-y-1 pt-1.5 border-t border-white/[0.06]">
                  <div className="flex justify-between">
                    <span>Heartbeat:</span>
                    <span className="text-[var(--profit)] font-bold">
                      {typeof w.heartbeat_age_seconds === "number"
                        ? `${w.heartbeat_age_seconds.toFixed(1)}s atrás`
                        : "N/D"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Reinicios:</span>
                    <span className="text-[var(--text-1)]">{w.restart_count ?? 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tareas:</span>
                    <span className="text-[var(--text-1)] font-bold">{w.jobs_processed ?? 0}</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Live SSE Terminal Console */}
      <div className="bg-[var(--surface-1)] backdrop-blur-xl rounded-2xl border border-white/[0.08] p-5 space-y-3 shadow-xl">
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-2.5">
          <h3 className="text-xs font-black uppercase tracking-wider text-[var(--text-1)] font-mono flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[var(--profit)]" />
            Consola de Telemetría en Vivo 24/7 (SSE Feed)
          </h3>
          <span className="text-[11px] font-mono text-[var(--text-3)]">Auto-Scroll Activo</span>
        </div>

        <div className="bg-[var(--bg)] p-3.5 rounded-xl border border-white/[0.08] font-mono text-xs max-h-52 overflow-y-auto space-y-1.5">
          {logs.length === 0 ? (
            <div className="text-[var(--text-3)] text-center py-4">Esperando eventos del supervisor...</div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 text-[var(--text-1)]">
                <span className="text-[var(--text-3)] select-none shrink-0">[{log.ts}]</span>
                <span
                  className={`font-bold px-1.5 py-0.5 rounded text-[9.5px] shrink-0 ${
                    log.level === "INFO"
                      ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                      : "bg-[var(--surface-2)] text-[var(--text-2)] border border-[var(--border)]"
                  }`}
                >
                  {log.level}
                </span>
                <span className="text-[var(--text-1)] leading-relaxed">{log.msg}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
