/**
 * apps/web/hooks/useTelemetryStream.ts
 * Conexión SSE resiliente con reconexión exponencial y Watchdog
 */
'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  WorkerId, 
  WorkerTelemetry, 
  TelemetryLogEvent, 
  SelfHealingAlert, 
  SystemOverviewMetrics 
} from '../types/telemetry';

const INITIAL_WORKERS: Record<WorkerId, WorkerTelemetry> = {
  DataWorker: { workerId: 'DataWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 40, opsPerSec: 12, tasksCompleted: 1420, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Ingesta de Velas 1m/5m', uptimeSeconds: 3600, version: '2.2.0' },
  SQXWorker: { workerId: 'SQXWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 120, opsPerSec: 45, tasksCompleted: 614280, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Bridge MCP :8081 Activo', uptimeSeconds: 3600, version: '2.2.0' },
  FastBacktestWorker: { workerId: 'FastBacktestWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 60, opsPerSec: 120, tasksCompleted: 85200, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'FastEngine Margen Aislado 1R', uptimeSeconds: 3600, version: '2.2.0' },
  ValidationWorker: { workerId: 'ValidationWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 50, opsPerSec: 25, tasksCompleted: 142, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Evidence Gates QVF Dual', uptimeSeconds: 3600, version: '2.2.0' },
  MonteCarloWorker: { workerId: 'MonteCarloWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 80, opsPerSec: 15, tasksCompleted: 5000, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Bootstrap Permutations (10k)', uptimeSeconds: 3600, version: '2.2.0' },
  SemanticAIWorker: { workerId: 'SemanticAIWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 90, opsPerSec: 8, tasksCompleted: 380, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'FailureKnowledgeDB & 5 Agentes', uptimeSeconds: 3600, version: '2.2.0' },
  PortfolioWorker: { workerId: 'PortfolioWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 45, opsPerSec: 10, tasksCompleted: 64, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'HRP / ERC & Bóveda Ratchet', uptimeSeconds: 3600, version: '2.2.0' },
  PaperTradingWorker: { workerId: 'PaperTradingWorker', status: 'ACTIVE', cpuPercent: 0, memoryMb: 35, opsPerSec: 5, tasksCompleted: 18, tasksFailed: 0, queueDepth: 0, lastHeartbeatMs: Date.now(), currentTaskName: 'Sandbox 14 Días & Latencia 50ms', uptimeSeconds: 3600, version: '2.2.0' },
};

const MAX_LOGS_BUFFER = 300;

export function useTelemetryStream(streamUrl = '/api/v2/telemetry/stream') {
  const [workers, setWorkers] = useState<Record<WorkerId, WorkerTelemetry>>(INITIAL_WORKERS);
  const [logs, setLogs] = useState<TelemetryLogEvent[]>([]);
  const [healingAlerts, setHealingAlerts] = useState<SelfHealingAlert[]>([]);
  const [systemMetrics, setSystemMetrics] = useState<SystemOverviewMetrics>({
    totalOpsPerSec: 280,
    activeWorkersCount: 8,
    totalMemoryMb: 520,
    globalQueueDepth: 0,
    busLatencyMs: 1,
    systemHealthScore: 100,
    sqxBridgeConnected: true,
    sseConnected: true,
    connectionState: 'CONNECTED',
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

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

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
        try {
          const payload = JSON.parse(e.data);
          if (payload) {
            if (payload.event_type === 'CONNECTED_ACK') {
              setSystemMetrics(prev => ({
                ...prev,
                sseConnected: true,
                connectionState: 'CONNECTED',
                lastSyncTimestampMs: Date.now(),
              }));
              return;
            }

            if (!isPausedRef.current && payload.event_type) {
              const eventId = payload.event_id || `evt_${payload.event_type}_${Date.now()}_${logs.length}`;
              const newLog: TelemetryLogEvent = {
                id: eventId,
                timestampMs: payload.timestamp_utc_ms || Date.now(),
                workerId: 'SystemSupervisor',
                eventType: payload.event_type,
                level: 'INFO',
                message: `Evento canónico [${payload.event_type}] procesado en bus asíncrono.`,
                provenanceHash: payload.event_id || 'PROVENANCE_OK',
              };
              setLogs(prev => [newLog, ...prev.slice(0, MAX_LOGS_BUFFER - 1)]);
            }
          }
        } catch (err) {
          // parse error
        }
      };

      es.onerror = () => {
        es.close();
        setSystemMetrics(prev => ({
          ...prev,
          sseConnected: false,
          connectionState: 'RECONNECTING',
        }));

        const baseDelay = Math.min(6000, 1000 * Math.pow(1.3, reconnectAttemptsRef.current));
        reconnectAttemptsRef.current += 1;

        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, baseDelay);
      };
    } catch (err) {
      // Error creating EventSource
    }
  }, [streamUrl]);

  useEffect(() => {
    connect();

    // Polling de respaldo para healthcheck cada 3s
    const healthTimer = setInterval(async () => {
      try {
        const res = await fetch('/api/v2/telemetry/health');
        if (res.ok) {
          const data = await res.json();
          if (data.workers) {
            setWorkers(prev => {
              const next = { ...prev };
              Object.keys(data.workers).forEach((k) => {
                const wKey = k as WorkerId;
                if (next[wKey]) {
                  const state = data.workers[k].state;
                  next[wKey] = {
                    ...next[wKey],
                    status: (state === 'RUNNING' || state === 'ACTIVE') ? 'ACTIVE' : state,
                    tasksCompleted: (data.workers[k].processed_tasks || next[wKey].tasksCompleted),
                    tasksFailed: data.workers[k].failed_tasks || 0,
                    lastHeartbeatMs: Date.now(),
                  };
                }
              });
              return next;
            });
            setSystemMetrics(prev => ({
              ...prev,
              sseConnected: true,
              connectionState: 'CONNECTED',
              systemHealthScore: data.overall_healthy ? 100 : 80,
              lastSyncTimestampMs: Date.now(),
            }));
          }
        }
      } catch (err) {
        // network fetch error
      }
    }, 3000);

    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      clearInterval(healthTimer);
    };
  }, [connect]);

  return {
    workers,
    logs,
    healingAlerts,
    systemMetrics,
    isPaused,
    togglePause,
    clearLogs,
    reconnect: connect,
  };
}
