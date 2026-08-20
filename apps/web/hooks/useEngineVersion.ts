"use client";

import { useState, useEffect } from "react";

export interface VersionHistoryItem {
  version: string;
  name: string;
  released_at: string;
  status: string;
  status_label: string;
  description: string;
  ruleset_hash: string;
  git_commit?: string;
  changes: string[];
  strategy_count?: number;
}

export interface EngineVersionData {
  current_version: string;
  current_name: string;
  pipeline_version: string;
  codebase_fingerprint?: string;
  code_drift_detected?: boolean;
  history: VersionHistoryItem[];
  version_distribution?: Record<string, number>;
}

export function useEngineVersion() {
  const [data, setData] = useState<EngineVersionData>({
    current_version: "1.03",
    current_name: "Ultrarentable Dual-Engine V1.03 (Master Forensic Architecture & Reconciled Dual-Engine)",
    pipeline_version: "1.03",
    history: [],
    version_distribution: {},
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;

    async function fetchVersion() {
      try {
        const res = await fetch("/api/v1/versions");
        if (res.ok) {
          const json = await res.json();
          if (mounted && json.current_version) {
            setData(json);
          }
        }
      } catch (err) {
        // Keep default fallback
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchVersion();
    const interval = setInterval(fetchVersion, 15000); // Polling every 15s
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return {
    version: data.current_version,
    versionName: data.current_name,
    pipelineVersion: data.pipeline_version,
    history: data.history,
    versionDistribution: data.version_distribution || {},
    codeDrift: data.code_drift_detected,
    loading,
  };
}
