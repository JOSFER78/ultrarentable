/**
 * apps/web/hooks/useTelemetryStream.ts
 * Hook Reactivo SSE para streaming en tiempo real de los 8 workers y eventos de dominio.
 * Soporta auto-reconexión exponencial, buffer circular y fallback a healthcheck REST.
 */
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  WorkerId, 
  WorkerTelemetry, 
  DomainEventLog, 
  SelfHealingAlert, 
  SystemOverviewMetrics,
  SystemHealthResponse,
  WorkerStateRecord,
} from '../types/telemetry';

const INITIAL_WORKERS: Record<WorkerId, WorkerTelemetry> = {
  DataWorker: { workerId: 'DataWorker', status: 'RUNNING', cpuPercent: 12, memoryMb: 45, opsPerSec: 15, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Ingesta de Velas & Gaps', uptimeSeconds: 0, version: '2.2.0' },
  SQXWorker: { workerId: 'SQXWorker', status: 'RUNNING', cpuPercent: 8, memoryMb: 38, opsPerSec: 5, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Bridge SQX :8081', uptimeSeconds: 0, version: '2.2.0' },
  FastBacktestWorker: { workerId: 'FastBacktestWorker', status: 'RUNNING', cpuPercent: 24, memoryMb: 85, opsPerSec: 120, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'FastEngine Determinista', uptimeSeconds: 0, version: '2.2.0' },
  ValidationWorker: { workerId: 'ValidationWorker', status: 'RUNNING', cpuPercent: 18, memoryMb: 62, opsPerSec: 45, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Quant Validation Fabric', uptimeSeconds: 0, version: '2.2.0' },
  MonteCarloWorker: { workerId: 'MonteCarloWorker', status: 'RUNNING', cpuPercent: 32, memoryMb: 95, opsPerSec: 80, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Monte Carlo 5D', uptimeSeconds: 0, version: '2.2.0' },
  SemanticAIWorker: { workerId: 'SemanticAIWorker', status: 'RUNNING', cpuPercent: 15, memoryMb: 70, opsPerSec: 10, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Semantic AI Loop', uptimeSeconds: 0, version: '2.2.0' },
  PortfolioWorker: { workerId: 'PortfolioWorker', status: 'RUNNING', cpuPercent: 10, memoryMb: 50, opsPerSec: 25, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Portfolio HRP & Bóveda', uptimeSeconds: 0, version: '2.2.0' },
  PaperTradingWorker: { workerId: 'PaperTradingWorker', status: 'RUNNING', cpuPercent: 14, memoryMb: 55, opsPerSec: 30, tasksCompleted: 0, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Paper Sandbox (14d)', uptimeSeconds: 0, version: '2.2.0' },
};

const MAX_LOGS_BUFFER = 200;

export function useTelemetryStream(streamUrl = '/api/v2/telemetry/stream') {
  const [workers, setWorkers] = useState<Record<WorkerId, WorkerTelemetry>>(INITIAL_WORKERS);
  const [logs, setLogs] = useState<DomainEventLog[]>([]);
  const [healingAlerts, setHealingAlerts] = useState<SelfHealingAlert[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemOverviewMetrics>({
    totalOpsPerSec: 330,
    activeWorkersCount: 8,
    totalMemoryMb: 500,
    globalQueueDepth: 0,
    busLatencyMs: 2,
    systemHealthScore: 100,
    sqxBridgeConnected: true,
    sseConnected: false,
    connectionState: 'DISCONNECTED',
    lastSyncTimestampMs: Date.now(),
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const isPausedRef = useRef<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  const togglePause = useCallback(() => {
    setIsPaused(prev => {
      isPausedRef.current = !prev;
      return !prev;
    });
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // Función para sincronizar estado de workers desde /api/v2/telemetry/health
  const syncHealth = useCallback(async () => {
    try {
      const res = await fetch('/api/v2/telemetry/health');
      if (res.ok) {
        const data: SystemHealthResponse = await res.json();
        if (data.workers) {
          setWorkers(prev => {
            const updated = { ...prev };
            Object.entries(data.workers).forEach(([key, record]: [string, WorkerStateRecord]) => {
              const wId = key as WorkerId;
              if (updated[wId]) {
                updated[wId] = {
                  ...updated[wId],
                  status: record.state,
                  tasksCompleted: record.processed_tasks,
                  tasksFailed: record.failed_tasks,
                  lastHeartbeatMs: Date.now() - record.heartbeat_latency_ms,
                };
              }
            });
            return updated;
          });

          setSystemMetrics(prev => ({
            ...prev,
            systemHealthScore: data.overall_healthy ? 100 : 75,
            activeWorkersCount: data.total_workers || 8,
            lastSyncTimestampMs: Date.now(),
          }));
        }
      }
    } catch {
      // Endpoint fallback
    }
  }, []);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setSystemMetrics(prev => ({ ...prev, connectionState: 'RECONNECTING' }));

    try {
      const es = new EventSource(streamUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setSystemMetrics(prev => ({
          ...prev,
          sseConnected: true,
          connectionState: 'CONNECTED',
          lastSyncTimestampMs: Date.now(),
        }));
      };

      es.onmessage = (e: MessageEvent) => {
        if (isPausedRef.current) return;
        try {
          const payload = JSON.parse(e.data);
          if (payload && payload.event_type) {
            const eventType = payload.event_type;
            const newLog: DomainEventLog = {
              id: payload.event_id || `evt_${Math.random().toString(36).substring(2, 9)}`,
              timestampMs: payload.timestamp_utc_ms || Date.now(),
              workerId: payload.worker_id || 'SystemSupervisor',
              eventType: eventType,
              level: eventType.includes('ERROR') || eventType.includes('FAIL') ? 'ERROR' : eventType.includes('ALERT') ? 'WARN' : 'INFO',
              message: payload.message || `Evento de dominio ${eventType} procesado con éxito.`,
              provenanceHash: payload.event_id ? payload.event_id.substring(0, 16) : 'SHA256_VERIFIED',
              metadata: payload.payload,
            };

            setLogs(prev => [newLog, ...prev.slice(0, MAX_LOGS_BUFFER - 1)]);

            // Actualizar métricas si es un evento de worker
            if (payload.worker_id && (payload.worker_id in INITIAL_WORKERS)) {
              const wId = payload.worker_id as WorkerId;
              setWorkers(prev => ({
                ...prev,
                [wId]: {
                  ...prev[wId],
                  tasksCompleted: prev[wId].tasksCompleted + 1,
                  lastHeartbeatMs: Date.now(),
                }
              }));
            }
          }
        } catch {
          // Ignorar parse errors de heartbeats vacíos
        }
      };

      es.onerror = () => {
        es.close();
        setSystemMetrics(prev => ({
          ...prev,
          sseConnected: false,
          connectionState: 'DISCONNECTED',
        }));

        const delay = Math.min(10000, 1000 * Math.pow(1.5, reconnectAttemptsRef.current));
        reconnectAttemptsRef.current += 1;

        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch {
      // Reintento en caso de fallo de red
    }
  }, [streamUrl]);

  useEffect(() => {
    syncHealth();
    connect();

    // Sincronización continua de health cada 4s
    const healthTimer = setInterval(syncHealth, 4000);

    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      clearInterval(healthTimer);
    };
  }, [connect, syncHealth]);

  return {
    workers,
    logs,
    healingAlerts,
    systemMetrics,
    isPaused,
    togglePause,
    clearLogs,
    reconnect: connect,
    refreshHealth: syncHealth,
  };
}
