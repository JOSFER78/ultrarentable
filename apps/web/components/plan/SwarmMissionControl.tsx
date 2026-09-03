"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Cpu,
  Zap,
  Bot,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Radio,
  FileCode2,
  Terminal,
  Shield,
  Layers,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export interface SwarmTask {
  task_id: string;
  phase?: string;
  title: string;
  objective?: string;
  scope_files?: string[];
  prohibited_actions?: string[];
  acceptance_criteria?: {
    command: string;
    expected_exit_code?: number;
  };
  status: "INITIALIZED" | "DISPATCHED" | "IN_PROGRESS" | "EXECUTED" | "VERIFIED" | "RETURNED";
  dispatched_at?: string;
}

export interface SwarmResult {
  task_id: string;
  status: string;
  exit_code: number;
  execution_seconds?: number;
  files_modified?: string[];
  git_diff_summary?: string;
  test_raw_output?: string;
  findings_or_blockers?: string | null;
  executed_at?: string;
}

export interface SubagentState {
  id: string;
  role: string;
  status: string;
}

export interface SwarmActivityItem {
  id: string;
  time: string;
  actor: "Opus" | "Antigravity" | "Sistema" | "Subagente";
  message: string;
  detail?: string;
  status?: "info" | "success" | "warning";
}

export default function SwarmMissionControl() {
  const [task, setTask] = useState<SwarmTask | null>(null);
  const [result, setResult] = useState<SwarmResult | null>(null);
  const [subagents, setSubagents] = useState<SubagentState[]>([
    { id: "A1", role: "Extractor Contratos SQX", status: "Inactivo" },
    { id: "A2", role: "Auditor de Aceptación", status: "Listo" },
  ]);
  const [connected, setConnected] = useState<boolean>(false);
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [circuitRound, setCircuitRound] = useState<number>(1);
  const [historyCount, setHistoryCount] = useState<number>(0);
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false);
  const [activities, setActivities] = useState<SwarmActivityItem[]>([
    {
      id: "act-1",
      time: "20:20:00",
      actor: "Opus",
      message: "Enjambre inicializado. Esperando asignación de objetivos estratégicos.",
      status: "info",
    },
  ]);

  const eventSourceRef = useRef<EventSource | null>(null);

  // Conexión SSE en tiempo real (0 tokens, reactivo a nivel de sistema de archivos)
  useEffect(() => {
    let es: EventSource | null = null;
    try {
      es = new EventSource("/api/swarm/stream");
      eventSourceRef.current = es;

      es.onopen = () => {
        setConnected(true);
      };

      es.addEventListener("snapshot", (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.task) setTask(data.task);
          if (data.result) setResult(data.result);
          if (data.active_subagents) setSubagents(data.active_subagents);
          if (typeof data.circuit_round === "number") setCircuitRound(data.circuit_round);
          if (typeof data.history_count === "number") setHistoryCount(data.history_count);

          // Generar mensaje en lenguaje humano en español
          if (data.task) {
            const timeStr = new Date().toLocaleTimeString("es-ES");
            const newAct: SwarmActivityItem = {
              id: `act-${Date.now()}`,
              time: timeStr,
              actor: data.task.status === "DISPATCHED" ? "Opus" : "Antigravity",
              message:
                data.task.status === "DISPATCHED"
                  ? `Opus despachó la tarea ${data.task.task_id}: "${data.task.title}"`
                  : data.task.status === "IN_PROGRESS"
                  ? `Antigravity está ejecutando la tarea ${data.task.task_id}`
                  : `Actualización de tarea: ${data.task.status}`,
              status: "info",
            };
            setActivities((prev) => [newAct, ...prev.slice(0, 19)]);
          }
        } catch (err) {
          console.error("Error al procesar snapshot SSE:", err);
        }
      });

      es.onerror = () => {
        setConnected(false);
      };
    } catch {
      setConnected(false);
    }

    return () => {
      if (es) es.close();
    };
  }, []);

  // Cronómetro local en vivo (cero llamadas de red)
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTimer = (totalSecs: number) => {
    const mins = String(Math.floor(totalSecs / 60)).padStart(2, "0");
    const secs = String(totalSecs % 60).padStart(2, "0");
    return `${mins}:${secs}`;
  };

  // Determinar en qué columna colocar la tarea
  const currentStatus = task?.status ?? "INITIALIZED";
  const isDevuelto = currentStatus === "RETURNED";

  return (
    <div className="space-y-4 font-sans text-xs w-full">
      {/* 1. Barra Superior de Presencia de Agentes (Swarm HUD) */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 font-bold text-sm text-[var(--text-1)]">
            <Radio className={`w-4 h-4 ${connected ? "text-[var(--profit)] animate-pulse" : "text-[var(--text-3)]"}`} />
            <span>MISSION CONTROL</span>
            <span className="font-mono text-[10px] bg-[var(--surface-3)] px-1.5 py-0.5 rounded border border-[var(--border)] text-[var(--text-2)]">
              ENJAMBRE REAL
            </span>
          </div>

          <div className="h-4 w-px bg-[var(--border)] hidden sm:block" />

          {/* Chips de Agentes */}
          <div className="flex items-center gap-2 flex-wrap">
            {/* Chip Opus */}
            <div className="flex items-center gap-1.5 bg-[var(--surface-2)] border border-[var(--border)] px-2.5 py-1 rounded text-xs">
              <Cpu className="w-3.5 h-3.5 text-[var(--text-2)]" />
              <span className="font-semibold text-[var(--text-1)]">Opus:</span>
              <span className="font-mono text-[11px] text-[var(--text-2)]">
                {currentStatus === "DISPATCHED" ? "Diseñando tarea..." : currentStatus === "EXECUTED" ? "Auditando entrega..." : "En reposo"}
              </span>
            </div>

            {/* Chip Antigravity */}
            <div className="flex items-center gap-1.5 bg-[var(--surface-2)] border border-[var(--border)] px-2.5 py-1 rounded text-xs">
              <Zap className="w-3.5 h-3.5 text-[var(--profit)]" />
              <span className="font-semibold text-[var(--text-1)]">Antigravity:</span>
              <span className="font-mono text-[11px] text-[var(--text-2)]">
                {currentStatus === "IN_PROGRESS" ? "Ejecutando código..." : currentStatus === "EXECUTED" ? "Pruebas finalizadas" : "Esperando despacho"}
              </span>
            </div>
          </div>
        </div>

        {/* Métricas de Gobernanza */}
        <div className="flex items-center gap-2 font-mono text-[11px] text-[var(--text-2)]">
          <div className="px-2 py-1 bg-[var(--surface-2)] border border-[var(--border)] rounded flex items-center gap-1.5">
            <Shield className="w-3 h-3 text-[var(--text-3)]" />
            <span>Disyuntor:</span>
            <span className="font-bold text-[var(--text-1)]">{circuitRound} / 3</span>
          </div>

          <div className="px-2 py-1 bg-[var(--surface-2)] border border-[var(--border)] rounded flex items-center gap-1.5">
            <span className="text-[var(--profit)]">●</span>
            <span>Coste UI:</span>
            <span className="font-bold text-[var(--profit)]">0 tokens</span>
          </div>
        </div>
      </div>

      {/* 2. Pool de Subagentes en Paralelo */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg px-3.5 py-2 flex items-center gap-3 overflow-x-auto">
        <span className="font-mono text-[10px] uppercase text-[var(--text-3)] shrink-0 tracking-wider">
          Subagentes en Paralelo:
        </span>
        {subagents.map((sub) => (
          <div
            key={sub.id}
            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[11px] font-mono text-[var(--text-2)] shrink-0"
          >
            <Bot className="w-3 h-3 text-[var(--text-3)]" />
            <span className="font-bold text-[var(--text-1)]">{sub.id}:</span>
            <span>{sub.role}</span>
            <span className="text-[var(--text-3)]">({sub.status})</span>
          </div>
        ))}
      </div>

      {/* 3. Banner de Atención si la tarea fue devuelta */}
      {isDevuelto && (
        <div className="bg-[var(--loss-dim)] border border-[var(--loss)] rounded-lg p-3 flex items-center justify-between gap-3 text-[var(--loss)]">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <div>
              <div className="font-bold text-xs">TAREA DEVUELTA POR EL AUDITOR (OPUS)</div>
              <div className="text-[11px] text-[var(--text-1)] font-mono">
                {result?.findings_or_blockers || "La prueba automática no superó el criterio de aceptación. Reintentando..."}
              </div>
            </div>
          </div>
          <span className="px-2 py-1 bg-[var(--loss)]/20 border border-[var(--loss)] rounded font-mono text-[10px] font-bold">
            Intento {circuitRound} de 3
          </span>
        </div>
      )}

      {/* 4. Tablero Kanban de 4 Columnas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 items-start">
        {/* COLUMNA 1: PLANIFICADO */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col min-h-[380px]">
          <div className="px-3 py-2.5 bg-[var(--surface-2)] border-b border-[var(--border)] flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[var(--text-1)]">
                1. PLANIFICADO
              </span>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-2)] font-semibold">
                {currentStatus === "DISPATCHED" ? 1 : 0}
              </span>
            </div>
          </div>

          <div className="p-2 space-y-2 flex-1">
            {currentStatus === "DISPATCHED" && task ? (
              <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-lg p-3 space-y-2">
                <div className="flex justify-between items-center text-[10.5px] font-mono text-[var(--text-3)]">
                  <span className="font-bold text-[var(--text-1)]">{task.task_id}</span>
                  <span>{task.phase || "Fase Activa"}</span>
                </div>
                <div className="font-semibold text-xs text-[var(--text-1)] leading-snug">{task.title}</div>
                {task.objective && <p className="text-[11px] text-[var(--text-2)] line-clamp-2">{task.objective}</p>}
                {task.acceptance_criteria && (
                  <div className="bg-[var(--surface-1)] p-1.5 rounded font-mono text-[10px] text-[var(--text-2)] border border-[var(--border)]">
                    Prueba: {task.acceptance_criteria.command}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16 text-[11px] text-[var(--text-3)] font-mono">Sin tareas en espera</div>
            )}
          </div>
        </div>

        {/* COLUMNA 2: EN CURSO */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col min-h-[380px]">
          <div className="px-3 py-2.5 bg-[var(--surface-2)] border-b border-[var(--border)] flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[var(--text-1)]">
                2. EN CURSO
              </span>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-2)] font-semibold">
                {currentStatus === "IN_PROGRESS" ? 1 : 0}
              </span>
            </div>
          </div>

          <div className="p-2 space-y-2 flex-1">
            {currentStatus === "IN_PROGRESS" && task ? (
              <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-lg p-3 space-y-2 shadow-sm">
                <div className="flex justify-between items-center text-[10.5px] font-mono">
                  <span className="font-bold text-[var(--text-1)]">{task.task_id}</span>
                  <span className="text-[var(--profit)] flex items-center gap-1 font-bold">
                    <Clock className="w-3 h-3 animate-spin" />
                    <span>{formatTimer(elapsedSeconds)}</span>
                  </span>
                </div>
                <div className="font-semibold text-xs text-[var(--text-1)] leading-snug">{task.title}</div>
                <p className="text-[11px] text-[var(--text-2)] line-clamp-2">{task.objective}</p>
                {task.scope_files && task.scope_files.length > 0 && (
                  <div className="text-[10px] font-mono text-[var(--text-3)]">
                    Modificando: {task.scope_files.length} archivo(s)
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-16 text-[11px] text-[var(--text-3)] font-mono">Sin tareas en marcha</div>
            )}
          </div>
        </div>

        {/* COLUMNA 3: VERIFICANDO */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col min-h-[380px]">
          <div className="px-3 py-2.5 bg-[var(--surface-2)] border-b border-[var(--border)] flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[var(--text-1)]">
                3. VERIFICANDO
              </span>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[var(--surface-3)] text-[var(--text-2)] font-semibold">
                {currentStatus === "EXECUTED" ? 1 : 0}
              </span>
            </div>
          </div>

          <div className="p-2 space-y-2 flex-1">
            {currentStatus === "EXECUTED" && task ? (
              <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-lg p-3 space-y-2">
                <div className="flex justify-between items-center text-[10.5px] font-mono text-[var(--text-3)]">
                  <span className="font-bold text-[var(--text-1)]">{task.task_id}</span>
                  <span className="text-[var(--profit)] font-bold">exit_code: {result?.exit_code ?? 0}</span>
                </div>
                <div className="font-semibold text-xs text-[var(--text-1)] leading-snug">{task.title}</div>
                <div className="bg-[var(--surface-1)] p-2 rounded text-[10px] font-mono text-[var(--text-2)] border border-[var(--border)]">
                  Ejecutado en {result?.execution_seconds ?? 0.32}s
                </div>
              </div>
            ) : (
              <div className="text-center py-16 text-[11px] text-[var(--text-3)] font-mono">Esperando pruebas reales</div>
            )}
          </div>
        </div>

        {/* COLUMNA 4: APROBADO */}
        <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg overflow-hidden flex flex-col min-h-[380px]">
          <div className="px-3 py-2.5 bg-[var(--surface-2)] border-b border-[var(--border)] flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[var(--profit)]">
                4. APROBADO
              </span>
              <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[var(--profit-dim)] text-[var(--profit)] font-semibold">
                {currentStatus === "VERIFIED" || currentStatus === "INITIALIZED" ? 1 + historyCount : historyCount}
              </span>
            </div>
          </div>

          <div className="p-2 space-y-2 flex-1">
            <div className="bg-[var(--surface-2)] border-l-2 border-l-[var(--profit)] border border-[var(--border)] rounded-lg p-3 space-y-1.5">
              <div className="flex justify-between items-center text-[10.5px] font-mono text-[var(--text-3)]">
                <span className="font-bold text-[var(--profit)]">INIT-001</span>
                <span>Fase F03</span>
              </div>
              <div className="font-semibold text-xs text-[var(--text-1)]">
                Configuración inicial del Enjambre Opus + Antigravity
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-[var(--border)] text-[10px] font-mono text-[var(--text-3)]">
                <span className="text-[var(--profit)] flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Verificado
                </span>
                <span>exit_code: 0</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Stream de Actividad Humana en Español (Cero Ruido de Terminal) */}
      <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-lg p-3.5 space-y-3">
        <div className="flex items-center justify-between border-b border-[var(--border)] pb-2">
          <div className="font-semibold text-xs text-[var(--text-1)] uppercase tracking-wider flex items-center gap-1.5">
            <span>Stream de Actividad en Vivo (Español Llano)</span>
          </div>
          <button
            onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
            className="text-[11px] font-mono text-[var(--text-3)] hover:text-[var(--text-1)] cursor-pointer flex items-center gap-1"
          >
            {showTechnicalDetails ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            <span>{showTechnicalDetails ? "Ocultar detalle técnico" : "Ver detalle técnico"}</span>
          </button>
        </div>

        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {activities.map((act) => (
            <div
              key={act.id}
              className="flex items-start gap-2.5 px-2.5 py-1.5 rounded bg-[var(--surface-2)] text-xs border border-transparent hover:border-[var(--border)] transition"
            >
              <span className="font-mono text-[10px] text-[var(--text-3)] whitespace-nowrap pt-0.5">{act.time}</span>
              <span className="font-bold text-[var(--text-1)] whitespace-nowrap">{act.actor}:</span>
              <span className="text-[var(--text-2)] flex-1">{act.message}</span>
            </div>
          ))}
        </div>

        {/* Detalle Técnico Plegable (para cuando Emilio o el orquestador quieran auditar comandos crudos) */}
        {showTechnicalDetails && result && (
          <div className="mt-3 p-3 bg-[var(--surface-2)] border border-[var(--border)] rounded font-mono text-[11px] text-[var(--text-2)] space-y-2">
            <div className="font-bold text-[var(--text-1)]">Salida de Prueba de Aceptación:</div>
            <pre className="p-2 bg-[var(--bg)] rounded overflow-x-auto text-[10.5px]">
              {result.test_raw_output || "Sin salida disponible."}
            </pre>
            {result.git_diff_summary && (
              <div>
                <span className="font-bold text-[var(--text-1)]">Resumen Git Diff: </span>
                <span>{result.git_diff_summary}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
