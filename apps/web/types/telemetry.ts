/**
 * apps/web/types/telemetry.ts
 * Definición estricta de contratos de telemetría para Ultrarentable V2
 */

export type ValidationTrack = 'TRACK_FONDEO' | 'TRACK_ULTRA';

export type StrategyLifecycleStatus = 
  | 'GENERATED'
  | 'BACKTESTED'
  | 'OOS_PASSED'
  | 'ROBUSTNESS_PASSED'
  | 'EVIDENCE_APPROVED'
  | 'CANDIDATE'
  | 'INCUBATION_PAPER'
  | 'LIVE_ACTIVE'
  | 'REJECTED'
  | 'RETIRED';

export type WorkerId = 
  | 'DataWorker'
  | 'SQXWorker'
  | 'FastBacktestWorker'
  | 'ValidationWorker'
  | 'MonteCarloWorker'
  | 'SemanticAIWorker'
  | 'PortfolioWorker'
  | 'PaperTradingWorker';

export type WorkerStatus = 
  | 'ACTIVE'
  | 'IDLE'
  | 'BUSY'
  | 'DEGRADED'
  | 'RESTARTING'
  | 'FAILED'
  | 'DISCONNECTED';

export type LogLevel = 'INFO' | 'SUCCESS' | 'WARN' | 'ERROR' | 'CRITICAL' | 'AUDIT';

export type CanonicalEventType =
  | 'DATA_INGESTED'
  | 'SQX_STRATEGY_FOUND'
  | 'BACKTEST_COMPLETED'
  | 'GATE_EVALUATED'
  | 'MONTE_CARLO_SIMULATED'
  | 'AI_ANALYSIS_COMPLETED'
  | 'PORTFOLIO_REBALANCED'
  | 'PAPER_ORDER_FILLED'
  | 'WORKER_HEARTBEAT'
  | 'SELF_HEALING_TRIGGERED'
  | 'SYSTEM_ALERT'
  | 'CIRCUIT_BREAKER_TRIPPED';

export interface WorkerTelemetry {
  workerId: WorkerId;
  status: WorkerStatus;
  cpuPercent: number;
  memoryMb: number;
  opsPerSec: number;
  tasksCompleted: number;
  tasksFailed: number;
  queueDepth: number;
  lastHeartbeatMs: number;
  currentTaskName: string | null;
  uptimeSeconds: number;
  version: string;
}

export interface TelemetryLogEvent {
  id: string;
  timestampMs: number;
  workerId: WorkerId | 'SystemSupervisor';
  eventType: CanonicalEventType;
  level: LogLevel;
  message: string;
  provenanceHash: string;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface SelfHealingAlert {
  id: string;
  timestampMs: number;
  workerId: WorkerId;
  triggerCause: string;
  actionTaken: 'RESTART_WORKER' | 'FLUSH_STALLED_QUEUE' | 'THROTTLE_INGESTION' | 'CIRCUIT_BREAKER_OPEN' | 'FAILOVER_FALLBACK';
  status: 'INVESTIGATING' | 'EXECUTED' | 'RESOLVED' | 'ESCALATED';
  details: string;
  resolvedAtMs: number | null;
}

export interface SystemOverviewMetrics {
  totalOpsPerSec: number;
  activeWorkersCount: number;
  totalMemoryMb: number;
  globalQueueDepth: number;
  busLatencyMs: number;
  systemHealthScore: number;
  sqxBridgeConnected: boolean;
  sseConnected: boolean;
  connectionState: 'CONNECTED' | 'RECONNECTING' | 'DISCONNECTED' | 'STALLED';
  lastSyncTimestampMs: number;
}
