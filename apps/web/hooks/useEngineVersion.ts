/**
 * apps/web/hooks/useEngineVersion.ts
 * Hook para la inspección física de versión de motor, git commit y drift criptográfico.
 */
"use client";

import { useState, useEffect, useCallback } from "react";

export interface EngineVersionInfo {
  version: string;
  versionName: string;
  gitCommit: string;
  gitCommitShort: string;
  gitBranch: string;
  gitMessage: string;
  gitAuthor: string;
  codeDrift: boolean;
  codebaseFingerprint: string;
  lastBumpUtc: string;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useEngineVersion(): EngineVersionInfo {
  const [version, setVersion] = useState<string>("5.3.0");
  const [versionName, setVersionName] = useState<string>("Ultrarentable v5.3.0");
  const [gitCommit, setGitCommit] = useState<string>("");
  const [gitCommitShort, setGitCommitShort] = useState<string>("");
  const [gitBranch, setGitBranch] = useState<string>("main");
  const [gitMessage, setGitMessage] = useState<string>("");
  const [gitAuthor, setGitAuthor] = useState<string>("");
  const [codeDrift, setCodeDrift] = useState<boolean>(false);
  const [codebaseFingerprint, setCodebaseFingerprint] = useState<string>("");
  const [lastBumpUtc, setLastBumpUtc] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchVersion = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/v1/versions");
      if (!res.ok) {
        throw new Error(`Fallo al consultar versión del motor (HTTP ${res.status})`);
      }
      const data = await res.json();
      setVersion(data.current_version || data.active_version || "5.3.0");
      setVersionName(data.current_name || data.active_name || "Ultrarentable v5.3.0");
      setGitCommit(data.git_commit || "");
      setGitCommitShort(data.git_commit_short || (data.git_commit ? data.git_commit.slice(0, 7) : ""));
      setGitBranch(data.git_branch || "main");
      setGitMessage(data.git_message || "");
      setGitAuthor(data.git_author || "");
      setCodeDrift(Boolean(data.code_drift_detected));
      setCodebaseFingerprint(data.codebase_fingerprint || "");
      setLastBumpUtc(data.last_bump_utc || "");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al conectar con version router.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVersion();
  }, [fetchVersion]);

  return {
    version,
    versionName,
    gitCommit,
    gitCommitShort,
    gitBranch,
    gitMessage,
    gitAuthor,
    codeDrift,
    codebaseFingerprint,
    lastBumpUtc,
    loading,
    error,
    refetch: fetchVersion,
  };
}
