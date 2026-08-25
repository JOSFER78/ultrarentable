/**
 * apps/web/hooks/useTelemetryStream.ts
 * Hook de streaming reactivo SSE para la telemetría en tiempo real de los 8 workers y métricas de supervisor.
 */
"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { WorkerId, WorkerState, SystemMetrics } from "@/types/telemetry";

export interface UseTelemetryStreamResult {
  workers: Record<WorkerId, WorkerState>;
  systemMetrics: SystemMetrics;
  logs: string[];
  reconnect: () => void;
}

const DEFAULT_METRICS: SystemMetrics = {
  sseConnected: false,
  activeWorkersCount: 0,
  totalWorkersCount: 0,
  lastUpdatedUtc: null,
  evaluationsPerSec: 0,
  totalEvaluations: 0,
  engineStatus: "HEALTHY",
  connectionState: "DISCONNECTED",
  sqxBridgeConnected: false,
};

export function useTelemetryStream(): UseTelemetryStreamResult {
  const [workers, setWorkers] = useState<Record<WorkerId, WorkerState>>({});
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>(DEFAULT_METRICS);
  const [logs, setLogs] = useState<string[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const es = new EventSource("/api/v1/telemetry/stream");
      eventSourceRef.current = es;

      es.onopen = () => {
        setSystemMetrics((prev) => ({ ...prev, sseConnected: true, connectionState: "CONNECTED" }));
      };

      es.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.workers) {
            setWorkers(payload.workers);
          }
          if (payload.metrics) {
            setSystemMetrics((prev) => ({
              ...prev,
              ...payload.metrics,
              sseConnected: true,
              connectionState: "CONNECTED",
            }));
          }
          if (payload.logs) {
            setLogs(payload.logs);
          }
        } catch {
          // ignore parse errors on heartbeat lines
        }
      };

      es.onerror = () => {
        setSystemMetrics((prev) => ({ ...prev, sseConnected: false, connectionState: "ERROR" }));
        es.close();
      };
    } catch {
      setSystemMetrics((prev) => ({ ...prev, sseConnected: false, connectionState: "ERROR" }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [connect]);

  return {
    workers,
    systemMetrics,
    logs,
    reconnect: connect,
  };
}
