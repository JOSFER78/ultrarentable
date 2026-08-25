/**
 * apps/web/types/telemetry.ts
 * Definición canónica de tipos de telemetría y supervisor de workers 24/7.
 */

export type WorkerId =
  | "worker_1"
  | "worker_2"
  | "worker_3"
  | "worker_4"
  | "worker_5"
  | "worker_6"
  | "worker_7"
  | "worker_8"
  | string;

export interface WorkerState {
  id: WorkerId;
  name: string;
  status: "ACTIVE" | "IDLE" | "ERROR" | "STOPPED";
  lastHeartbeat: string | null;
  tasksCompleted: number;
  errorCount: number;
  details?: Record<string, unknown>;
}

export interface SystemMetrics {
  sseConnected: boolean;
  activeWorkersCount: number;
  totalWorkersCount: number;
  lastUpdatedUtc: string | null;
  evaluationsPerSec: number;
  totalEvaluations: number;
  engineStatus: "HEALTHY" | "DEGRADED" | "OFFLINE";
}
