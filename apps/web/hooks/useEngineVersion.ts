"use client";

import { useState, useEffect } from "react";
import { getApiUrl } from "@/lib/api";

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
  git_commit?: string;
  git_commit_short?: string;
  git_message?: string;
  git_author?: string;
  git_date?: string;
  git_branch?: string;
  git_is_dirty?: boolean;
  history: VersionHistoryItem[];
  version_distribution?: Record<string, number>;
}

export function useEngineVersion() {
  const [data, setData] = useState<EngineVersionData>({
    current_version: "5.4.0",
    current_name: "Ultrarentable V5.4.0 (Multi-Phase Lineage Governance, Zero-Leakage Research Lab, 24/7 Durable Job Queue & Strictly Certified Views 5/6)",
    pipeline_version: "5.4.0",
    git_commit_short: "HEAD",
    git_branch: "main",
    history: [],
    version_distribution: {},
  });
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let mounted = true;

    async function fetchVersion() {
      try {
        const url = typeof window !== "undefined" ? "/api/v1/versions" : getApiUrl("/api/v1/versions");
        const res = await fetch(url, { cache: "no-store" });
        if (res.ok) {
          const json = await res.json();
          if (mounted && json.current_version) {
            setData(json);
          }
        }
      } catch {
        // Keep default fallback v5.4.0
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
    gitCommit: data.git_commit,
    gitCommitShort: data.git_commit_short || (data.git_commit ? data.git_commit.substring(0, 7) : "HEAD"),
    gitBranch: data.git_branch || "main",
    gitMessage: data.git_message || "",
    gitIsDirty: data.git_is_dirty || false,
    history: data.history,
    versionDistribution: data.version_distribution || {},
    codeDrift: data.code_drift_detected,
    loading,
  };
}
