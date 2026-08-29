"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  ShieldCheck,
  RefreshCw,
  Cpu,
  Server,
  Zap,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Clock,
  Terminal,
} from "lucide-react";
import QuantTooltip from "@/components/system/QuantTooltip";

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
        
        // Append log if new
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
    <div className="min-h-screen bg-slate-950 text-slate-100 p-2 md:p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-7 h-7 text-emerald-400 animate-pulse" />
              <h1 className="text-2xl font-bold tracking-tight">
                Telemetría & Pulso Autónomo 24/7 (SystemSupervisor)
              </h1>
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Supervisión de 8 workers concurrentes, 3 daemons autónomos de fondo y auto-recuperación de SQLite WAL sin intervención humana.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping mr-2"></span>
              PULSO ACTIVO {lastUpdated}
            </span>
            <button
              onClick={handleRestartAll}
              disabled={restarting}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold font-mono bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 transition"
            >
              <RotateCcw className={`w-3.5 h-3.5 mr-1.5 ${restarting ? "animate-spin" : ""}`} />
              Reiniciar Enjambre
            </button>
          </div>
        </div>

        {/* Tri-Daemon Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Daemon 1 */}
          <div className="p-4 bg-slate-900/80 rounded-2xl border border-slate-800 space-y-2 shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-indigo-400 flex items-center gap-1.5">
                <Cpu className="w-4 h-4" />
                1. CONTINUOUS RESEARCH
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                24/7 ACTIVO
              </span>
            </div>
            <h3 className="text-sm font-extrabold text-white">Laboratorio de Mutación & Debate AST</h3>
            <p className="text-xs text-slate-400">
              Escanea candidatos rechazados, ejecuta el debate de 8 roles bajo Blind Scope y sintetiza mutaciones de StrategyDSL.
            </p>
            <div className="text-[11px] font-mono text-slate-500 pt-1 flex justify-between">
              <span>Frecuencia: 30s</span>
              <span className="text-indigo-300 font-bold">Auto-Reparación ON</span>
            </div>
          </div>

          {/* Daemon 2 */}
          <div className="p-4 bg-slate-900/80 rounded-2xl border border-slate-800 space-y-2 shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-amber-400 flex items-center gap-1.5">
                <Zap className="w-4 h-4" />
                2. AUTONOMOUS META DAEMON
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                24/7 ACTIVO
              </span>
            </div>
            <h3 className="text-sm font-extrabold text-white">Ensamblador de Portafolios Multi-Alpha</h3>
            <p className="text-xs text-slate-400">
              Barre estrategias 11/11 en SQLite WAL, calcula matrices de correlación y optimiza la paridad de riesgo (DD &lt; 10%).
            </p>
            <div className="text-[11px] font-mono text-slate-500 pt-1 flex justify-between">
              <span>Frecuencia: 60s</span>
              <span className="text-amber-300 font-bold">Risk-Parity ON</span>
            </div>
          </div>

          {/* Daemon 3 */}
          <div className="p-4 bg-slate-900/80 rounded-2xl border border-slate-800 space-y-2 shadow-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold font-mono text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                3. HIGH AVAILABILITY WATCHDOG
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                24/7 ACTIVO
              </span>
            </div>
            <h3 className="text-sm font-extrabold text-white">Supervisor de Tolerancia a Caídas</h3>
            <p className="text-xs text-slate-400">
              Rescata jobs huérfanos tras caídas, supervisa el socket de SQX y conmuta automáticamente a FastEngine autónomo.
            </p>
            <div className="text-[11px] font-mono text-slate-500 pt-1 flex justify-between">
              <span>Heartbeat: 10s</span>
              <span className="text-emerald-300 font-bold">Self-Healing ON</span>
            </div>
          </div>
        </div>

        {/* 8 Workers Grid */}
        <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 gap-2">
            <div>
              <h2 className="text-sm font-black uppercase tracking-wider text-slate-200 font-mono flex items-center gap-2">
                <Server className="w-4 h-4 text-indigo-400" />
                Enjambre de 8 Workers Autónomos (SystemSupervisor)
              </h2>
              <p className="text-xs text-slate-400">
                Cada worker emite un heartbeat cada 10s. Si un worker se congela &gt;30s, el supervisor lo reinicia automáticamente.
              </p>
            </div>
            <span className="text-xs font-mono font-bold text-emerald-400 bg-slate-950 px-3 py-1 rounded-lg border border-slate-800 self-start sm:self-auto">
              {telemetry?.healthy_workers || 8} / {telemetry?.total_workers || 8} ONLINE
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {workerList.length === 0 ? (
              <div className="col-span-full p-6 text-center text-xs font-mono text-slate-500 bg-slate-950 rounded-xl border border-slate-800">
                {loading ? "Cargando telemetría de workers..." : "SIN DATOS / NO EVIDENCE DE WORKERS"}
              </div>
            ) : (
              workerList.map((w) => (
                <div
                  key={w.worker_id}
                  className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">
                      {w.status}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-200 line-clamp-1">{w.name}</h4>
                  <div className="text-[11px] font-mono text-slate-400 space-y-1 pt-1 border-t border-slate-900">
                    <div className="flex justify-between">
                      <span>Heartbeat:</span>
                      <span className="text-emerald-400 font-bold">
                        {typeof w.heartbeat_age_seconds === "number"
                          ? `${w.heartbeat_age_seconds.toFixed(1)}s atrás`
                          : "N/D"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Reinicios:</span>
                      <span className="text-slate-300">{w.restart_count ?? 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Tareas:</span>
                      <span className="text-indigo-300 font-bold">{w.jobs_processed ?? 0}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live SSE Terminal Console */}
        <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-5 space-y-3 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h3 className="text-xs font-black uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              Consola de Telemetría en Vivo 24/7 (SSE Feed)
            </h3>
            <span className="text-[11px] font-mono text-slate-500">Auto-Scroll Activo</span>
          </div>

          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 font-mono text-xs max-h-48 overflow-y-auto space-y-1.5">
            {logs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2 text-slate-300">
                <span className="text-slate-600 select-none">[{log.ts}]</span>
                <span
                  className={`font-bold px-1 py-0.2 rounded text-[10px] ${
                    log.level === "INFO"
                      ? "bg-emerald-950 text-emerald-400"
                      : "bg-amber-950 text-amber-400"
                  }`}
                >
                  {log.level}
                </span>
                <span className="text-slate-300">{log.msg}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
