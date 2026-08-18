/**
 * apps/web/types/telemetry.ts
 * Definición estricta de contratos de telemetría y tipos para Ultrarentable V2 (2026).
 */

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
  | 'DISCONNECTED'
  | 'RUNNING'
  | 'STOPPED'
  | 'ERROR';

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

export type LogLevel = 'INFO' | 'SUCCESS' | 'WARN' | 'ERROR' | 'CRITICAL' | 'AUDIT';

export type TelemetryEventType =
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
  | 'CIRCUIT_BREAKER_TRIPPED'
  | 'CANDIDATE_PROMOTED'
  | 'VALIDATION_COMPLETED'
  | 'VAULT_HARVEST_EXECUTED'
  | 'BULLET_STATE_CHANGED';

export interface WorkerStateRecord {
  state: WorkerStatus;
  processed_tasks: number;
  failed_tasks: number;
  heartbeat_latency_ms: number;
  restart_count: number;
  last_error: string | null;
}

export interface SystemHealthResponse {
  supervisor_active: boolean;
  overall_healthy: boolean;
  total_workers: number;
  workers: Record<WorkerId | string, WorkerStateRecord>;
}

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

export interface TelemetryEventPayload {
  event_type: string;
  event_id: string;
  timestamp_utc_ms: number;
  payload?: Record<string, any>;
}

export interface DomainEventLog {
  id: string;
  timestampMs: number;
  workerId: WorkerId | 'SystemSupervisor' | string;
  eventType: string;
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

export interface CanonicalStrategySummary {
  strategy_id: string;
  symbol: string;
  timeframe: string;
  track: ValidationTrack;
  status: StrategyLifecycleStatus;
  sharpe_ratio: number;
  profit_factor: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
  trades_count: number;
  provenance_hash_sha256: string;
  created_at_utc: string;
}
